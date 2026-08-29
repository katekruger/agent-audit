"""Non-negotiable behaviors (spec-adjacent contract tests) and the four
completion patterns, per BUILD-PLAN Prompt 3's definition of done.
"""

from __future__ import annotations

import logging

import pytest
from jsonschema import validate
from opentelemetry.sdk._logs import LoggerProvider

from agent_audit_record import (
    ActorType,
    Cost,
    CostComponent,
    CostUnit,
    Decision,
    Emitter,
    ExecutionAfterTerminalDecisionError,
    Level,
    NotExecutedReason,
    Outcome,
    PrincipalType,
)
from tests.conftest import CapturingProcessor, RaisingProcessor


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


class TestNeverCrashTheHost:
    """Non-negotiable behavior #1."""

    def test_raising_processor_does_not_propagate(self) -> None:
        provider = LoggerProvider()
        provider.add_log_record_processor(RaisingProcessor())
        emitter = Emitter(logger_provider=provider)

        _propose(emitter, "a1")  # must not raise

    def test_raising_processor_warns_once(self, caplog: pytest.LogCaptureFixture) -> None:
        provider = LoggerProvider()
        provider.add_log_record_processor(RaisingProcessor())
        emitter = Emitter(logger_provider=provider)

        with caplog.at_level(logging.WARNING, logger="agent_audit_record"):
            _propose(emitter, "a1")
            _propose(emitter, "a2")

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1

    def test_no_logger_provider_configured_is_a_noop(self) -> None:
        emitter = Emitter()  # no logger_provider passed: proxies to the global no-op
        _propose(emitter, "a1")  # must not raise


class TestLevelMetadataDoesNotLeak:
    """Non-negotiable behavior #2: adversarial secret-leak test."""

    def test_secret_omitted_at_level_metadata(
        self, emitter: Emitter, capture: CapturingProcessor
    ) -> None:
        secret = "sk-live-do-not-leak-this-token"
        _propose(
            emitter,
            "a1",
            level=Level.METADATA,
            arguments={"api_key": secret},
        )
        serialized = repr(capture.attribute_dicts())
        assert secret not in serialized
        assert "agent_audit.target.arguments" not in capture.attribute_dicts()[0]

    def test_arguments_present_at_level_request(
        self, emitter: Emitter, capture: CapturingProcessor
    ) -> None:
        _propose(emitter, "a1", level=Level.REQUEST, arguments={"StageName": "Closed Won"})
        assert "agent_audit.target.arguments" in capture.attribute_dicts()[0]

    def test_arguments_present_at_level_request_response(
        self, emitter: Emitter, capture: CapturingProcessor
    ) -> None:
        _propose(emitter, "a1", level=Level.REQUEST_RESPONSE, arguments="raw-body")
        assert capture.attribute_dicts()[0]["agent_audit.target.arguments"] == "raw-body"

    def test_default_level_from_config_is_metadata(
        self, emitter: Emitter, capture: CapturingProcessor
    ) -> None:
        _propose(emitter, "a1", level=None, arguments={"secret": "x"})
        assert "agent_audit.target.arguments" not in capture.attribute_dicts()[0]

    def test_non_primitive_arguments_are_json_serialized(
        self, emitter: Emitter, capture: CapturingProcessor
    ) -> None:
        _propose(emitter, "a1", level=Level.REQUEST, arguments={"a": 1, "b": [1, 2]})
        value = capture.attribute_dicts()[0]["agent_audit.target.arguments"]
        assert isinstance(value, str)
        assert '"a": 1' in value


class TestDenialEmitsNoExecuted:
    """Non-negotiable behavior #3."""

    def test_executed_after_denial_raises(self, emitter: Emitter) -> None:
        _propose(emitter, "a1")
        emitter.decided(
            action_id="a1",
            decision=Decision.DENY,
            principal_type=PrincipalType.HUMAN,
            cost=Cost(wasted=True),
        )
        with pytest.raises(ExecutionAfterTerminalDecisionError):
            emitter.executed(action_id="a1", outcome=Outcome.SUCCESS)

    def test_decided_deny_without_cost_wasted_raises(self, emitter: Emitter) -> None:
        with pytest.raises(ValueError, match=r"cost\.wasted"):
            emitter.decided(
                action_id="a1",
                decision=Decision.DENY,
                principal_type=PrincipalType.HUMAN,
            )

    def test_decided_deny_with_cost_wasted_false_raises(self, emitter: Emitter) -> None:
        with pytest.raises(ValueError, match=r"cost\.wasted"):
            emitter.decided(
                action_id="a1",
                decision=Decision.DENY,
                principal_type=PrincipalType.HUMAN,
                cost=Cost(wasted=False),
            )


class TestCompletionPatterns:
    """Spec §5.2 Patterns A-D, each validated against the JSON Schema."""

    def test_pattern_a_auto_allowed_read(
        self, emitter: Emitter, capture: CapturingProcessor, schema: dict[str, object]
    ) -> None:
        _propose(emitter, "a1")
        emitter.executed(action_id="a1", outcome=Outcome.SUCCESS)

        assert capture.event_names() == ["agent_audit.proposed", "agent_audit.executed"]
        for record in capture.attribute_dicts():
            validate(instance=record, schema=schema)

    def test_pattern_b_human_approved_write(
        self, emitter: Emitter, capture: CapturingProcessor, schema: dict[str, object]
    ) -> None:
        _propose(emitter, "a1")
        emitter.decided(action_id="a1", decision=Decision.ALLOW, principal_type=PrincipalType.HUMAN)
        emitter.executed(action_id="a1", outcome=Outcome.SUCCESS, records_changed=1)

        assert capture.event_names() == [
            "agent_audit.proposed",
            "agent_audit.decided",
            "agent_audit.executed",
        ]
        for record in capture.attribute_dicts():
            validate(instance=record, schema=schema)

    def test_pattern_c_denial(
        self, emitter: Emitter, capture: CapturingProcessor, schema: dict[str, object]
    ) -> None:
        _propose(emitter, "a1")
        emitter.decided(
            action_id="a1",
            decision=Decision.DENY,
            principal_type=PrincipalType.HUMAN,
            cost=Cost(amount=0.004, currency="usd", component=CostComponent.INFERENCE, wasted=True),
        )

        assert capture.event_names() == ["agent_audit.proposed", "agent_audit.decided"]
        decided = capture.attribute_dicts()[1]
        assert decided["agent_audit.cost.wasted"] is True
        for record in capture.attribute_dicts():
            validate(instance=record, schema=schema)

    def test_pattern_d_decision_timeout(
        self, emitter: Emitter, capture: CapturingProcessor, schema: dict[str, object]
    ) -> None:
        _propose(emitter, "a1")
        emitter.decided(
            action_id="a1",
            decision=Decision.TIMEOUT,
            principal_type=PrincipalType.TIMEOUT,
            cost=Cost(wasted=True),
        )

        assert capture.event_names() == ["agent_audit.proposed", "agent_audit.decided"]
        for record in capture.attribute_dicts():
            validate(instance=record, schema=schema)
        with pytest.raises(ExecutionAfterTerminalDecisionError):
            emitter.executed(action_id="a1", outcome=Outcome.SUCCESS)

    def test_cancel_decision_also_forbids_execution(self, emitter: Emitter) -> None:
        _propose(emitter, "a1")
        emitter.decided(
            action_id="a1",
            decision=Decision.CANCEL,
            principal_type=PrincipalType.HUMAN,
            cost=Cost(wasted=True),
        )
        with pytest.raises(ExecutionAfterTerminalDecisionError):
            emitter.executed(action_id="a1", outcome=Outcome.SUCCESS)

    def test_auto_deny_also_forbids_execution_and_requires_cost_wasted(
        self, emitter: Emitter
    ) -> None:
        """Found while dogfooding agent-audit in n8n-operator: an automatic
        denial forbids execution exactly as a human one does, differing
        only in principal.type -- not in whether cost was wasted.
        """
        with pytest.raises(ValueError, match=r"cost\.wasted"):
            emitter.decided(
                action_id="a1",
                decision=Decision.AUTO_DENY,
                principal_type=PrincipalType.POLICY,
            )

        _propose(emitter, "a2")
        emitter.decided(
            action_id="a2",
            decision=Decision.AUTO_DENY,
            principal_type=PrincipalType.POLICY,
            cost=Cost(wasted=True),
        )
        with pytest.raises(ExecutionAfterTerminalDecisionError):
            emitter.executed(action_id="a2", outcome=Outcome.SUCCESS)


class TestExecutedValidation:
    def test_not_executed_requires_reason(self, emitter: Emitter) -> None:
        with pytest.raises(ValueError, match="not_executed_reason"):
            emitter.executed(action_id="a1", outcome=Outcome.NOT_EXECUTED)

    def test_reason_forbidden_unless_not_executed(self, emitter: Emitter) -> None:
        with pytest.raises(ValueError, match="not_executed_reason"):
            emitter.executed(
                action_id="a1",
                outcome=Outcome.SUCCESS,
                not_executed_reason=NotExecutedReason.CANCELLED,
            )

    def test_executed_cost_attached(self, emitter: Emitter, capture: CapturingProcessor) -> None:
        _propose(emitter, "a1")
        emitter.executed(
            action_id="a1",
            outcome=Outcome.SUCCESS,
            cost=Cost(amount=1.0, unit=CostUnit.USD, component=CostComponent.TOTAL),
        )
        assert capture.attribute_dicts()[1]["agent_audit.cost.amount"] == 1.0
