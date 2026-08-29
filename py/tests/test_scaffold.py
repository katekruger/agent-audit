"""Scaffold-only tests. Replace once the emitter is implemented (see M3)."""

import pytest

from agent_audit_record import Emitter, Phase


def test_phase_values_match_spec_placeholder() -> None:
    assert {p.value for p in Phase} == {"proposed", "decided", "executed"}


def test_emitter_is_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError):
        Emitter().emit(Phase.PROPOSED)
