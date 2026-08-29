"""agent-audit middleware for an arbitrary MCP server.

The unclaimed position this fills (BUILD-PLAN.md §1, §6): Claude Code
hooks are client-side and Anthropic-specific; Microsoft AGT is
enforcement-side. A record an MCP SERVER itself emits, that survives the
client, belongs to neither -- this is that record.

Targets the official MCP Python SDK v2 line (`mcp>=2,<3`; `MCPServer`,
`ServerMiddleware`) and `agent-audit-record`. Neither is bundled as a
dependency of this file's own package -- copy this module into a server
(or install both packages) per README.md.

Design, and why it's shaped this way:

- A `tools/call` with no approval logic of its own produces exactly
  `agent_audit.proposed` + `agent_audit.executed` -- spec Pattern A, the
  minimal legal completion. Most MCP tools have no approval step, and
  this middleware should not invent one.
- A tool that DOES gate on approval (an elicitation round trip, a custom
  approval queue, whatever) calls `emitter.decided(action_id=
  current_action_id(), ...)` from inside its own handler, using the same
  `Emitter` passed to this middleware -- correlating with this
  middleware's `proposed`/`executed` pair via `current_action_id()`.
- If that decision forbids execution (deny/auto_deny/cancel/timeout),
  the tool handler's own return (or raise) still runs `call_next`'s
  remaining chain, so this middleware still attempts its own `executed`
  call afterward. Rather than requiring every tool author to suppress
  that call themselves, this middleware relies on the emitter's own
  invariant: `Emitter.executed()` raises `ExecutionAfterTerminalDecisionError`
  for an action_id already terminally decided. This middleware catches
  exactly that one exception and treats it as confirmation the
  correlated action is already correctly terminal (spec Patterns C/D) --
  never as an error to surface.
- `agent_audit.actor.id` defaults to a constant (`"mcp-client"`): the
  current SDK's `ServerRequestContext` (what middleware receives, as
  opposed to the `Context` handed to tool handlers) does not expose a
  per-connection session or principal identifier without reaching into
  private attributes. Pass a real identity via `actor_id_resolver` if
  your server has one available at the middleware tier (e.g. from
  transport headers via `ctx.headers`) -- see its docstring below.
- MCP `ToolAnnotations` (`readOnlyHint`, etc.) are not exposed to
  middleware by the current SDK -- only `ctx.method`/`ctx.params` are.
  `declare_annotations()` lets a server restate them once, alongside its
  own `@mcp.tool(annotations=...)` registration, so `agent_audit.declared.*`
  (spec §6.4) can be populated without middleware reaching into SDK
  internals. Recorded as untrusted declared input either way, per spec.
- Trace binding needs no code here at all: `agent_audit_record.Emitter`
  already binds `TraceId`/`SpanId` from whatever span is current (spec
  §4). Register the MCP SDK's own `OpenTelemetryMiddleware`
  (`mcp.server._otel`) ahead of this one in `Server.middleware` and every
  `agent_audit.*` Record correlates with that request's span for free.
"""

from __future__ import annotations

import contextlib
import contextvars
import uuid
from typing import Any

from mcp.server.context import CallNext, HandlerResult, ServerMiddleware, ServerRequestContext
from mcp_types import CallToolResult

from agent_audit_record import (
    ActorType,
    Emitter,
    ExecutionAfterTerminalDecisionError,
    Outcome,
)

_current_action_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "agent_audit_current_action_id", default=None
)

_declared_annotations: dict[str, dict[str, bool]] = {}


def declare_annotations(
    tool_name: str,
    *,
    read_only: bool | None = None,
    destructive: bool | None = None,
    idempotent: bool | None = None,
    open_world: bool | None = None,
) -> None:
    """Register one tool's MCP `ToolAnnotations` for `agent_audit.declared.*`.

    Call once per tool, alongside its own `@mcp.tool(annotations=...)`
    registration -- see the module docstring for why this middleware
    can't read them back off the SDK itself. Recorded as **untrusted**
    declared input regardless (spec §6.4): never treat these as the
    basis for a decision.
    """
    _declared_annotations[tool_name] = {
        k: v
        for k, v in {
            "read_only": read_only,
            "destructive": destructive,
            "idempotent": idempotent,
            "open_world": open_world,
        }.items()
        if v is not None
    }


def current_action_id() -> str | None:
    """The `agent_audit.action.id` of the `tools/call` currently in
    flight on this task, or `None` outside one.

    A tool handler that performs its own approval step calls
    `emitter.decided(action_id=current_action_id(), ...)` with this, to
    correlate its decision with this middleware's `proposed`/`executed`
    pair for the same call.
    """
    return _current_action_id.get()


def _default_actor_id(ctx: ServerRequestContext[Any, Any]) -> str:
    del ctx  # unused -- see actor_id_resolver's docstring for why
    return "mcp-client"


class AgentAuditMiddleware(ServerMiddleware[Any]):
    """Wraps every `tools/call` in `agent_audit.proposed` + `agent_audit.executed`."""

    def __init__(
        self,
        emitter: Emitter,
        *,
        target_system: str,
        actor_id_resolver: Any = _default_actor_id,
    ) -> None:
        """`actor_id_resolver(ctx) -> str` resolves `agent_audit.actor.id`.

        Defaults to a constant, since `ServerRequestContext` (what
        middleware receives) has no per-connection identity built in --
        see the module docstring. Pass your own if your server's
        transport exposes one, e.g. from `ctx.headers` on Streamable HTTP.
        """
        self._emitter = emitter
        self._target_system = target_system
        self._actor_id_resolver = actor_id_resolver

    async def __call__(
        self, ctx: ServerRequestContext[Any, Any], call_next: CallNext
    ) -> HandlerResult:
        if ctx.method != "tools/call" or not ctx.params:
            return await call_next(ctx)

        tool_name = ctx.params.get("name")
        if not isinstance(tool_name, str):
            return await call_next(ctx)

        action_id = str(uuid.uuid4())
        token = _current_action_id.set(action_id)
        try:
            declared = _declared_annotations.get(tool_name, {})
            self._emitter.proposed(
                action_id=action_id,
                actor_id=self._actor_id_resolver(ctx),
                actor_type=ActorType.AGENT,
                target_system=self._target_system,
                target_resource=tool_name,
                target_operation="tools/call",
                arguments=ctx.params.get("arguments"),
                declared_read_only=declared.get("read_only"),
                declared_destructive=declared.get("destructive"),
                declared_idempotent=declared.get("idempotent"),
                declared_open_world=declared.get("open_world"),
            )

            try:
                result = await call_next(ctx)
            except Exception:
                self._safe_executed(action_id, Outcome.FAILURE)
                raise

            match result:
                case CallToolResult(is_error=True) | {"isError": True}:
                    self._safe_executed(action_id, Outcome.FAILURE)
                case _:
                    self._safe_executed(action_id, Outcome.SUCCESS)
            return result
        finally:
            _current_action_id.reset(token)

    def _safe_executed(self, action_id: str, outcome: Outcome) -> None:
        # The tool handler may already have recorded a terminal decision via
        # current_action_id() -- spec Patterns C/D correctly forbid an
        # executed Record in that case. Not an error; expected.
        with contextlib.suppress(ExecutionAfterTerminalDecisionError):
            self._emitter.executed(action_id=action_id, outcome=outcome)
