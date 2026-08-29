"""Thin reference emitter over the OpenTelemetry SDK.

Implements spec/SPECIFICATION.md v1: three correlated LogRecord Events
(`agent_audit.proposed` / `.decided` / `.executed`) per `agent_audit.action.id`.

Per AGENTS.md, this emitter must never crash its host: any exporter or
configuration failure is caught in `_emit`, logged once at WARNING, and
swallowed. The one exception is a caller contract violation this module
can detect before touching OpenTelemetry at all -- e.g. emitting
`executed` after a denial, or omitting `cost.wasted` on one. Those raise
immediately: they are bugs in the caller, not telemetry failures, and the
schema would reject the resulting record anyway (spec §5.2, §6.7).
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from opentelemetry import trace
from opentelemetry._logs import Logger, LoggerProvider, get_logger
from opentelemetry.util.types import AnyValue

from agent_audit_record.config import Config
from agent_audit_record.cost import Cost
from agent_audit_record.phases import (
    ActorType,
    Decision,
    Level,
    NotExecutedReason,
    Outcome,
    Phase,
    PrincipalType,
)

_LOG = logging.getLogger("agent_audit_record")

_EVENT_NAME: dict[Phase, str] = {
    Phase.PROPOSED: "agent_audit.proposed",
    Phase.DECIDED: "agent_audit.decided",
    Phase.EXECUTED: "agent_audit.executed",
}


class ExecutionAfterTerminalDecisionError(RuntimeError):
    """`executed()` was called for an action whose `decided` Record already
    forbade execution (spec Patterns C/D: deny, auto_deny, cancel, or timeout).
    """


class Emitter:
    """Emits `agent_audit.*` LogRecord Events for one or more actions.

    Safe to construct with no arguments: with no OTel LoggerProvider
    configured by the host, every emitted Record is a documented no-op --
    OpenTelemetry's own default behavior, not something this class
    special-cases (spec §4).
    """

    def __init__(
        self,
        config: Config | None = None,
        logger_provider: LoggerProvider | None = None,
    ) -> None:
        self._config = config or Config.from_env()
        self._logger: Logger = get_logger("agent_audit_record", logger_provider=logger_provider)
        self._warned = False
        self._terminal_decisions: dict[str, Decision] = {}

    def proposed(
        self,
        *,
        action_id: str,
        actor_id: str,
        actor_type: ActorType,
        target_system: str,
        target_resource: str,
        target_operation: str,
        level: Level | None = None,
        arguments: Any = None,
        on_behalf_of: str | None = None,
        parent_id: str | None = None,
        declared_read_only: bool | None = None,
        declared_destructive: bool | None = None,
        declared_idempotent: bool | None = None,
        declared_open_world: bool | None = None,
    ) -> None:
        """Emit `agent_audit.proposed` (spec §6.2, §6.3, §6.4).

        `arguments` is only attached when `level` (or the configured
        default) is not `METADATA` -- spec §7's gate is enforced here, not
        left to the caller to remember.
        """
        level = level or self._config.default_level
        attrs: dict[str, AnyValue] = {
            "agent_audit.level": level.value,
            "agent_audit.actor.id": actor_id,
            "agent_audit.actor.type": actor_type.value,
            "agent_audit.target.system": target_system,
            "agent_audit.target.resource": target_resource,
            "agent_audit.target.operation": target_operation,
        }
        if on_behalf_of is not None:
            attrs["agent_audit.actor.on_behalf_of"] = on_behalf_of
        if parent_id is not None:
            attrs["agent_audit.action.parent_id"] = parent_id
        if level is not Level.METADATA and arguments is not None:
            attrs["agent_audit.target.arguments"] = _serialize_arguments(arguments)
        _set_optional(attrs, "agent_audit.declared.read_only", declared_read_only)
        _set_optional(attrs, "agent_audit.declared.destructive", declared_destructive)
        _set_optional(attrs, "agent_audit.declared.idempotent", declared_idempotent)
        _set_optional(attrs, "agent_audit.declared.open_world", declared_open_world)
        self._emit(Phase.PROPOSED, action_id, attrs)

    def decided(
        self,
        *,
        action_id: str,
        decision: Decision,
        principal_type: PrincipalType,
        principal_id: str | None = None,
        reason: str | None = None,
        policy_id: str | None = None,
        policy_version: str | None = None,
        latency_ms: int | None = None,
        effective_read_only: bool | None = None,
        cost: Cost | None = None,
    ) -> None:
        """Emit `agent_audit.decided` (spec §6.5).

        Raises `ValueError` if `decision.forbids_execution` (deny,
        auto_deny, cancel, or timeout) and `cost` is missing or
        `cost.wasted` is not True -- spec §6.7 requires it, and the
        schema would reject the record.
        """
        if decision.forbids_execution and (cost is None or not cost.wasted):
            raise ValueError(
                f"decision={decision.value!r} forbids execution (spec Patterns C/D); "
                "cost.wasted must be True (spec §6.7)"
            )
        attrs: dict[str, AnyValue] = {
            "agent_audit.decision": decision.value,
            "agent_audit.decision.principal.type": principal_type.value,
        }
        _set_optional(attrs, "agent_audit.decision.reason", reason)
        _set_optional(attrs, "agent_audit.decision.principal.id", principal_id)
        _set_optional(attrs, "agent_audit.decision.policy.id", policy_id)
        _set_optional(attrs, "agent_audit.decision.policy.version", policy_version)
        _set_optional(attrs, "agent_audit.effective.read_only", effective_read_only)
        if latency_ms is not None:
            if latency_ms < 0:
                _LOG.warning(
                    "agent-audit: negative decision.latency_ms=%d for action_id=%r "
                    "(clock skew?); omitting per spec §6.5",
                    latency_ms,
                    action_id,
                )
            else:
                attrs["agent_audit.decision.latency_ms"] = latency_ms
        if cost is not None:
            attrs.update(cost.to_attributes())

        if decision.forbids_execution:
            self._terminal_decisions[action_id] = decision
        self._emit(Phase.DECIDED, action_id, attrs)

    def executed(
        self,
        *,
        action_id: str,
        outcome: Outcome,
        not_executed_reason: NotExecutedReason | None = None,
        records_changed: int | None = None,
        reversible: bool | None = None,
        undo_token: str | None = None,
        batch_item_index: int | None = None,
        batch_size: int | None = None,
        cost: Cost | None = None,
    ) -> None:
        """Emit `agent_audit.executed` (spec §6.6).

        Raises `ExecutionAfterTerminalDecisionError` if a prior `decided()`
        call for this `action_id` forbade execution (spec Patterns C/D).
        Multiple `executed()` calls for one `action_id` are permitted --
        that is the batch fan-out case, spec §5.4 -- as long as no prior
        decision forbids execution.
        """
        terminal = self._terminal_decisions.get(action_id)
        if terminal is not None:
            raise ExecutionAfterTerminalDecisionError(
                f"action_id={action_id!r} was decided {terminal.value!r}, which spec "
                "Patterns C/D forbid following with an executed Record"
            )
        if outcome is Outcome.NOT_EXECUTED and not_executed_reason is None:
            raise ValueError(
                "not_executed_reason is required when outcome=not_executed (spec §6.6)"
            )
        if outcome is not Outcome.NOT_EXECUTED and not_executed_reason is not None:
            raise ValueError(
                "not_executed_reason MUST NOT be set unless outcome=not_executed (spec §6.6)"
            )

        attrs: dict[str, AnyValue] = {"agent_audit.outcome": outcome.value}
        if not_executed_reason is not None:
            attrs["agent_audit.not_executed_reason"] = not_executed_reason.value
        _set_optional(attrs, "agent_audit.effect.records_changed", records_changed)
        _set_optional(attrs, "agent_audit.effect.reversible", reversible)
        _set_optional(attrs, "agent_audit.effect.undo_token", undo_token)
        _set_optional(attrs, "agent_audit.batch.item_index", batch_item_index)
        _set_optional(attrs, "agent_audit.batch.size", batch_size)
        if cost is not None:
            attrs.update(cost.to_attributes())
        self._emit(Phase.EXECUTED, action_id, attrs)

    def _emit(self, phase: Phase, action_id: str, attrs: dict[str, AnyValue]) -> None:
        attrs["agent_audit.action.id"] = action_id
        attrs["agent_audit.action.phase"] = phase.value
        attrs["agent_audit.schema_url"] = self._config.schema_url

        context = None
        span = trace.get_current_span()
        if span.get_span_context().is_valid:
            context = trace.set_span_in_context(span)

        try:
            self._logger.emit(
                event_name=_EVENT_NAME[phase],
                attributes=attrs,
                context=context,
                timestamp=time.time_ns(),
            )
        except Exception:
            if not self._warned:
                _LOG.warning(
                    "agent-audit: failed to emit telemetry; this warning will not repeat "
                    "for the lifetime of this Emitter",
                    exc_info=True,
                )
                self._warned = True


def _set_optional(attrs: dict[str, AnyValue], key: str, value: AnyValue | None) -> None:
    if value is not None:
        attrs[key] = value


def _serialize_arguments(arguments: Any) -> AnyValue:
    if isinstance(arguments, str | int | float | bool):
        return arguments
    return json.dumps(arguments, default=str)
