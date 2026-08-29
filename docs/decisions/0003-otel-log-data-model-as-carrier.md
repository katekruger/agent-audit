# 0003. OTel Log Data Model as carrier, not a new wire protocol

- Status: accepted
- Date: 2026-08-29

## Context

A record binding "proposed → decided → executed" needs some way to travel
from the point it is generated to wherever it is consumed. The obvious
naive design is a new application-protocol method — e.g. an `audit/*`
JSON-RPC method on MCP — that agents and servers call directly.

Two pieces of evidence rule that out:

1. **MCP's SEP-2577** (status: Final, revision `2026-07-28`) deprecates
   Roots, Sampling, and Logging. Its stated rationale names OpenTelemetry
   explicitly as the correct alternative to an application-protocol logging
   channel. A proposed `audit/*` JSON-RPC method would be rejected on
   exactly the grounds SEP-2577 already articulated — MCP has told the
   ecosystem, in effect, "logging is not this protocol's job."
2. **The OpenTelemetry Log Data Model is Stable.** Every `gen_ai.*` span
   attribute — all 72 of them — is still `Development`. Building on the
   least stable part of the ecosystem we could have chosen would be a
   strange way to ask for adoption.

A LogRecord with a non-empty `EventName` is an OTel Event. It carries
`TraceId`/`SpanId`, which lets a record bind to the exact span that
authorized it, and it gets every existing OTel exporter and backend for
free — no new client, no new server, no new protocol negotiation.

## Decision

We define `agent-audit` as a semantic convention over the OpenTelemetry Log
Data Model — three correlated Events (`agent_audit.proposed`,
`agent_audit.decided`, `agent_audit.executed`) — rather than as a wire
protocol, an RPC method, or a bespoke transport.

## Consequences

Any system that already emits OTLP can adopt this convention without a new
integration surface. The reference emitter is a thin layer over the
existing OTel SDK (target: ~200 lines), not a client library with its own
transport, retry logic, or serialization format. This also means we inherit
whatever OTel already does well or poorly — exporter configuration, backend
compatibility, sampling behavior — for free, in both directions.

## Assumption this relies on

That OpenTelemetry's Log Data Model remains the de facto neutral carrier
for this kind of event in the AI agent ecosystem, and that MCP's stated
preference for OTel over protocol-level logging (SEP-2577) reflects a
durable position rather than a transitional one.

## Known limitation

We inherit OTel's ecosystem assumptions: a collector or exporter must be
configured for records to go anywhere, OTLP's semantics around sampling and
batching apply to audit records the same as any other telemetry (which is
not obviously correct for records that may need compliance-grade delivery
guarantees), and adoption is gated on an organization already having, or
being willing to stand up, OTel infrastructure.

**Verified 2026-08-29, and worse than the paragraph above assumed:** "gets
every existing OTel exporter and backend for free" holds at the protocol
and collector level (confirmed against `otel/opentelemetry-collector-contrib`
in [`examples/denied-proposal/`](../../examples/denied-proposal/)), but
**not yet at the level of AI-observability product backends**. Both Arize
Phoenix (`version-20.4.0`) and Langfuse (`4.24.0`) implement OTLP ingestion
for traces only (Langfuse also metrics) — neither has a Logs-signal
ingestion route at all. See
[`docs/backend-compatibility.md`](../backend-compatibility.md) for the
full verification. The Log Data Model being Stable in the OTel spec has
not yet translated into these specific products supporting that signal.
This doesn't change the decision — the alternative (building on spans, or
on a bespoke protocol) is still worse — but it means today's adopters need
a generic collector between `agent-audit` and their storage of choice,
not a direct line into these particular products.
