"""The three-phase event model.

Normative definition lives in spec/SPECIFICATION.md. This module is a
scaffold — the enum values below are placeholders until the specification
(Prompt 1 of the build plan) is written and this is implemented against it.
"""

from enum import StrEnum


class Phase(StrEnum):
    """`agent_audit.action.phase` — see spec/SPECIFICATION.md."""

    PROPOSED = "proposed"
    DECIDED = "decided"
    EXECUTED = "executed"
