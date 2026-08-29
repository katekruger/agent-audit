"""Thin reference emitter over the OpenTelemetry SDK.

Scaffold only. Implementation follows once spec/SPECIFICATION.md (Prompt 1
of the build plan) defines the required and optional attributes for each
phase. Per AGENTS.md, this emitter must never crash its host: any failure
to configure or reach an OTLP endpoint degrades silently and logs once.
"""

from __future__ import annotations

from agent_audit_record.phases import Phase


class Emitter:
    """Emits `agent_audit.*` LogRecord Events for one action.

    Not yet implemented — see spec/SPECIFICATION.md and
    docs/decisions/0003-otel-log-data-model-as-carrier.md for the design
    this will implement against.
    """

    def emit(self, phase: Phase, **attributes: object) -> None:
        raise NotImplementedError(
            "Emitter.emit is a scaffold pending spec/SPECIFICATION.md (see BUILD-PLAN.md M1)"
        )
