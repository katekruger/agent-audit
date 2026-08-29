#!/usr/bin/env python3
"""The flagship agent-audit example: a denied proposal.

An agent proposes a CRM bulk delete. A human denies it. The record shows
proposed + decided, no executed, and cost.wasted = true with the
inference spend that produced the rejected proposal.

No existing observability convention can express this: every platform
models cost as tokens x model price for actions that ran; none can say
"we spent $X on proposals humans rejected." See
docs/cost-of-denied-proposals.md.

Runs standalone -- prints a legible narrative to stdout with no backend
required. Set OTEL_EXPORTER_OTLP_ENDPOINT (e.g. after `docker compose up`
in this directory) to additionally send real OTLP to a local collector;
see README.md for the one-command version.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "py" / "src"))

from opentelemetry.sdk._logs import LoggerProvider, LogRecordProcessor, ReadWriteLogRecord
from opentelemetry.sdk.resources import Resource

from agent_audit_record import ActorType, Cost, CostComponent, Decision, Emitter, PrincipalType

ACTION_ID = "7c1e9a3b-4d2f-4a6e-9b1c-2d3e4f5a6b7c"

# Illustrative numbers for one proposal-review round trip -- not live
# billing data. See docs/cost-of-denied-proposals.md for how a real
# deployment computes its own figure from records like this one.
INFERENCE_INPUT_TOKENS = 1_450
INFERENCE_OUTPUT_TOKENS = 320
INFERENCE_COST_USD = 0.0037


class NarrativePrinter(LogRecordProcessor):
    """Prints each Record as a legible narrative line -- works with zero
    backend configured, which is the point: this example must be legible
    without one.
    """

    def on_emit(self, log_record: ReadWriteLogRecord) -> None:
        r = log_record.log_record
        attrs = dict(r.attributes or {})
        phase = attrs.get("agent_audit.action.phase")
        print(f"\n--- {r.event_name} ---")
        if phase == "proposed":
            print(f"  agent proposes: {attrs['agent_audit.target.operation']} on "
                  f"{attrs['agent_audit.target.system']}:{attrs['agent_audit.target.resource']}")
            print(f"  actor: {attrs['agent_audit.actor.id']} on behalf of "
                  f"{attrs.get('agent_audit.actor.on_behalf_of', '(unspecified)')}")
        elif phase == "decided":
            print(f"  decision: {attrs['agent_audit.decision']} by "
                  f"{attrs.get('agent_audit.decision.principal.id', '(unknown)')}")
            print(f"  reason: {attrs.get('agent_audit.decision.reason', '(none given)')}")
            if attrs.get("agent_audit.cost.wasted"):
                amount = attrs.get("agent_audit.cost.amount")
                currency = attrs.get("agent_audit.cost.currency", "")
                print(f"  >>> cost.wasted = true -- {amount} {currency} of inference spent on a "
                      f"proposal that will never execute <<<")
        elif phase == "executed":
            print(f"  outcome: {attrs['agent_audit.outcome']}")

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True

    def shutdown(self) -> None:
        pass


def build_emitter() -> Emitter:
    provider = LoggerProvider(resource=Resource.create({"service.name": "agent-audit-example"}))
    provider.add_log_record_processor(NarrativePrinter())

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

        exporter = OTLPLogExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/logs")
        provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        print(f"OTLP export enabled -> {otlp_endpoint} (see `docker compose logs collector`)")
    else:
        print("No OTEL_EXPORTER_OTLP_ENDPOINT set -- printing narrative only. "
              "See README.md to also send real OTLP to a local collector.")

    return Emitter(logger_provider=provider)


def main() -> None:
    emitter = build_emitter()

    emitter.proposed(
        action_id=ACTION_ID,
        actor_id="agent-crm-assistant",
        actor_type=ActorType.AGENT,
        on_behalf_of="kate@company.com",
        target_system="salesforce",
        target_resource="Opportunity/006xx000004TmiQAAS",
        target_operation="bulk_delete",
        declared_destructive=True,
        declared_read_only=False,
    )

    emitter.decided(
        action_id=ACTION_ID,
        decision=Decision.DENY,
        principal_type=PrincipalType.HUMAN,
        principal_id="kate@company.com",
        reason="Bulk deletion of closed-won opportunities is outside the agent's authorized policy scope",
        latency_ms=12_040,
        cost=Cost(
            amount=INFERENCE_COST_USD,
            currency="usd",
            component=CostComponent.INFERENCE,
            wasted=True,
        ),
    )

    # No executed() call: spec §5.2 Pattern C forbids one after a denial.
    # Calling it here would raise ExecutionAfterTerminalDecisionError.

    print(f"\n{INFERENCE_INPUT_TOKENS + INFERENCE_OUTPUT_TOKENS} tokens "
          f"({INFERENCE_INPUT_TOKENS} in / {INFERENCE_OUTPUT_TOKENS} out) were spent proposing "
          f"an action that a human then rejected. No executed record exists for this action_id, "
          f"and none ever will.")


if __name__ == "__main__":
    main()
