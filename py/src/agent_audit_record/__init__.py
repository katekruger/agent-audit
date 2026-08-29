"""Reference emitter for the agent-audit semantic convention.

See spec/SPECIFICATION.md in the repository root for the normative
definition of the three-phase event model this package emits.
"""

from agent_audit_record.emitter import Emitter
from agent_audit_record.phases import Phase

__all__ = ["Emitter", "Phase"]
