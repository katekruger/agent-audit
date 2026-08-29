from __future__ import annotations

import json
from pathlib import Path

import pytest
from opentelemetry.sdk._logs import LoggerProvider, LogRecordProcessor, ReadWriteLogRecord

from agent_audit_record import Emitter

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "spec" / "schema" / "v1" / "agent-audit.schema.json"
)


class CapturingProcessor(LogRecordProcessor):
    """Collects every emitted Record in-process, for assertions."""

    def __init__(self) -> None:
        self.records: list[ReadWriteLogRecord] = []

    def on_emit(self, log_record: ReadWriteLogRecord) -> None:
        self.records.append(log_record)

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True

    def shutdown(self) -> None:
        pass

    def attribute_dicts(self) -> list[dict[str, object]]:
        return [dict(r.log_record.attributes or {}) for r in self.records]

    def event_names(self) -> list[str | None]:
        return [r.log_record.event_name for r in self.records]


class RaisingProcessor(LogRecordProcessor):
    """Simulates a misbehaving exporter/processor that raises synchronously."""

    def on_emit(self, log_record: ReadWriteLogRecord) -> None:
        raise RuntimeError("simulated exporter failure")

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True

    def shutdown(self) -> None:
        pass


@pytest.fixture
def capture() -> CapturingProcessor:
    return CapturingProcessor()


@pytest.fixture
def emitter(capture: CapturingProcessor) -> Emitter:
    provider = LoggerProvider()
    provider.add_log_record_processor(capture)
    return Emitter(logger_provider=provider)


@pytest.fixture(scope="session")
def schema() -> dict[str, object]:
    return json.loads(SCHEMA_PATH.read_text())
