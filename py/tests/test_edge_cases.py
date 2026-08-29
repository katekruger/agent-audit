"""Edge cases enumerated in BUILD-PLAN Prompt 3, one test class each."""

from __future__ import annotations

import uuid

from jsonschema import validate
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk.trace import TracerProvider

from agent_audit_record import (
    ActorType,
    Decision,
    Emitter,
    NotExecutedReason,
    Outcome,
    PrincipalType,
)
from tests.conftest import CapturingProcessor


def _propose(emitter: Emitter, action_id: str, **overrides: object) -> None:
    kwargs: dict[str, object] = dict(
        action_id=action_id,
        actor_id="agent-1",
        actor_type=ActorType.AGENT,
        target_system="salesforce",
        target_resource="Account/1",
        target_operation="read",
    )
    kwargs.update(overrides)
    emitter.proposed(**kwargs)  # type: ignore[arg-type]


def test_proposed_then_superseded_before_a_decision(
    emitter: Emitter, capture: CapturingProcessor, schema: dict[str, object]
) -> None:
    """Pattern E: proposed + executed(not_executed/superseded), no decided."""
    _propose(emitter, "a1")
    emitter.executed(
        action_id="a1",
        outcome=Outcome.NOT_EXECUTED,
        not_executed_reason=NotExecutedReason.SUPERSEDED,
    )

    assert capture.event_names() == ["agent_audit.proposed", "agent_audit.executed"]
    for record in capture.attribute_dicts():
        validate(instance=record, schema=schema)


def test_approved_execution_then_fails_approval_still_recorded(
    emitter: Emitter, capture: CapturingProcessor, schema: dict[str, object]
) -> None:
    _propose(emitter, "a1")
    emitter.decided(action_id="a1", decision=Decision.ALLOW, principal_type=PrincipalType.HUMAN)
    emitter.executed(action_id="a1", outcome=Outcome.FAILURE)

    decided, executed = capture.attribute_dicts()[1], capture.attribute_dicts()[2]
    assert decided["agent_audit.decision"] == "allow"
    assert executed["agent_audit.outcome"] == "failure"
    for record in capture.attribute_dicts():
        validate(instance=record, schema=schema)


def test_approved_then_cancelled_before_execution(
    emitter: Emitter, capture: CapturingProcessor, schema: dict[str, object]
) -> None:
    _propose(emitter, "a1")
    emitter.decided(action_id="a1", decision=Decision.ALLOW, principal_type=PrincipalType.HUMAN)
    emitter.executed(
        action_id="a1",
        outcome=Outcome.NOT_EXECUTED,
        not_executed_reason=NotExecutedReason.CANCELLED,
    )

    executed = capture.attribute_dicts()[2]
    assert executed["agent_audit.outcome"] == "not_executed"
    assert executed["agent_audit.not_executed_reason"] == "cancelled"
    for record in capture.attribute_dicts():
        validate(instance=record, schema=schema)


def test_retry_after_failure_uses_new_action_id_linked_via_parent(
    emitter: Emitter, capture: CapturingProcessor, schema: dict[str, object]
) -> None:
    first_id = str(uuid.uuid4())
    _propose(emitter, first_id)
    emitter.executed(action_id=first_id, outcome=Outcome.FAILURE)

    retry_id = str(uuid.uuid4())
    assert retry_id != first_id
    _propose(emitter, retry_id, parent_id=first_id)
    emitter.executed(action_id=retry_id, outcome=Outcome.SUCCESS)

    retry_proposed = capture.attribute_dicts()[2]
    assert retry_proposed["agent_audit.action.id"] == retry_id
    assert retry_proposed["agent_audit.action.parent_id"] == first_id
    for record in capture.attribute_dicts():
        validate(instance=record, schema=schema)


def test_batch_one_decided_many_executed_share_action_id(
    emitter: Emitter, capture: CapturingProcessor, schema: dict[str, object]
) -> None:
    _propose(emitter, "batch-1")
    emitter.decided(
        action_id="batch-1", decision=Decision.ALLOW, principal_type=PrincipalType.HUMAN
    )
    for i in range(3):
        emitter.executed(
            action_id="batch-1",
            outcome=Outcome.SUCCESS,
            batch_item_index=i,
            batch_size=3,
        )

    records = capture.attribute_dicts()
    assert capture.event_names() == [
        "agent_audit.proposed",
        "agent_audit.decided",
        "agent_audit.executed",
        "agent_audit.executed",
        "agent_audit.executed",
    ]
    assert all(r["agent_audit.action.id"] == "batch-1" for r in records)
    executed_records = records[2:]
    assert [r["agent_audit.batch.item_index"] for r in executed_records] == [0, 1, 2]
    assert all(r["agent_audit.batch.size"] == 3 for r in executed_records)
    for record in records:
        validate(instance=record, schema=schema)


def test_no_trace_context_emits_without_fabricating_one(
    emitter: Emitter, capture: CapturingProcessor
) -> None:
    """Standalone CLI case: no active span anywhere."""
    _propose(emitter, "a1")

    record = capture.records[0].log_record
    assert record.trace_id == 0
    assert record.span_id == 0


def test_trace_context_bound_when_a_span_is_active(capture: CapturingProcessor) -> None:
    provider = LoggerProvider()
    provider.add_log_record_processor(capture)
    emitter = Emitter(logger_provider=provider)

    tracer = TracerProvider().get_tracer(__name__)
    with tracer.start_as_current_span("do-the-thing") as span:
        _propose(emitter, "a1")
        expected_trace_id = span.get_span_context().trace_id

    record = capture.records[0].log_record
    assert record.trace_id == expected_trace_id
    assert record.trace_id != 0


def test_clock_skew_negative_latency_is_omitted_not_negative(
    emitter: Emitter, capture: CapturingProcessor
) -> None:
    _propose(emitter, "a1")
    emitter.decided(
        action_id="a1",
        decision=Decision.ALLOW,
        principal_type=PrincipalType.HUMAN,
        latency_ms=-50,
    )

    decided = capture.attribute_dicts()[1]
    assert "agent_audit.decision.latency_ms" not in decided


def test_positive_latency_is_recorded(emitter: Emitter, capture: CapturingProcessor) -> None:
    _propose(emitter, "a1")
    emitter.decided(
        action_id="a1",
        decision=Decision.ALLOW,
        principal_type=PrincipalType.HUMAN,
        latency_ms=1500,
    )
    assert capture.attribute_dicts()[1]["agent_audit.decision.latency_ms"] == 1500


def test_on_behalf_of_records_the_impersonated_principal(
    emitter: Emitter, capture: CapturingProcessor
) -> None:
    _propose(emitter, "a1", on_behalf_of="kate@company.com")
    assert capture.attribute_dicts()[0]["agent_audit.actor.on_behalf_of"] == "kate@company.com"


def test_declared_and_effective_disagreement_both_recorded_never_collapsed(
    emitter: Emitter, capture: CapturingProcessor
) -> None:
    _propose(emitter, "a1", declared_read_only=True)
    emitter.decided(
        action_id="a1",
        decision=Decision.ALLOW,
        principal_type=PrincipalType.HUMAN,
        effective_read_only=False,
    )

    proposed, decided = capture.attribute_dicts()
    assert proposed["agent_audit.declared.read_only"] is True
    assert decided["agent_audit.effective.read_only"] is False
