"""Reference emitter for the agent-audit semantic convention.

See spec/SPECIFICATION.md in the repository root for the normative
definition of the three-phase event model this package emits.
"""

from agent_audit_record.config import Config
from agent_audit_record.cost import Cost
from agent_audit_record.emitter import Emitter, ExecutionAfterTerminalDecisionError
from agent_audit_record.phases import (
    ActorType,
    CostComponent,
    CostUnit,
    Decision,
    Level,
    NotExecutedReason,
    Outcome,
    Phase,
    PrincipalType,
)

__all__ = [
    "ActorType",
    "Config",
    "Cost",
    "CostComponent",
    "CostUnit",
    "Decision",
    "Emitter",
    "ExecutionAfterTerminalDecisionError",
    "Level",
    "NotExecutedReason",
    "Outcome",
    "Phase",
    "PrincipalType",
]
