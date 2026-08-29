"""Typed models mirroring spec/schema/v1/agent-audit.schema.json.

Normative definitions live in spec/SPECIFICATION.md. Keep this module and
the schema in sync — see AGENTS.md.
"""

from enum import StrEnum


class Phase(StrEnum):
    """`agent_audit.action.phase` — spec §5.1, §6.1."""

    PROPOSED = "proposed"
    DECIDED = "decided"
    EXECUTED = "executed"


class Level(StrEnum):
    """`agent_audit.level` — spec §7."""

    METADATA = "metadata"
    REQUEST = "request"
    REQUEST_RESPONSE = "request_response"


class ActorType(StrEnum):
    """`agent_audit.actor.type` — spec §6.2."""

    AGENT = "agent"
    HUMAN = "human"
    POLICY = "policy"
    SYSTEM = "system"


class Decision(StrEnum):
    """`agent_audit.decision` — spec §6.5.1."""

    ALLOW = "allow"
    DENY = "deny"
    DEFER = "defer"
    CANCEL = "cancel"
    TIMEOUT = "timeout"
    AUTO_ALLOW = "auto_allow"
    AUTO_DENY = "auto_deny"

    @property
    def forbids_execution(self) -> bool:
        """True for decisions after which spec Patterns C/D forbid an executed Record.

        AUTO_DENY is included alongside DENY: an automatic denial forbids
        execution exactly as a human one does, differing only in
        `decision.principal.type` -- not in whether cost was wasted.
        """
        return self in (Decision.DENY, Decision.AUTO_DENY, Decision.CANCEL, Decision.TIMEOUT)


class PrincipalType(StrEnum):
    """`agent_audit.decision.principal.type` — spec §6.5."""

    HUMAN = "human"
    POLICY = "policy"
    TIMEOUT = "timeout"
    DEFAULT = "default"


class Outcome(StrEnum):
    """`agent_audit.outcome` — spec §6.6."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    NOT_EXECUTED = "not_executed"


class NotExecutedReason(StrEnum):
    """`agent_audit.not_executed_reason` — spec §6.6."""

    DENIED = "denied"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class CostUnit(StrEnum):
    """`agent_audit.cost.unit` — spec §6.7."""

    USD = "usd"
    API_CALLS = "api_calls"
    CREDITS = "credits"
    SEAT_HOURS = "seat_hours"
    QUOTA = "quota"


class CostComponent(StrEnum):
    """`agent_audit.cost.component` — spec §6.7."""

    INFERENCE = "inference"
    ACTION = "action"
    TOTAL = "total"
