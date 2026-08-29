# Backend compatibility

What actually happens when an `agent-audit` record — an OTel **Log**
Data Model Event — is sent over OTLP to a real backend, as opposed to a
generic collector. Verified locally against a specific version of each
backend; versions are pinned below so this table doesn't quietly go
stale.

**Headline finding: neither backend tested accepts OTLP logs ingestion at
all, as of the versions tested.** Both are trace/span-centric LLM
observability products. This is a stronger and more important finding
than "mangles a field" — it means `agent-audit` records currently cannot
reach either product directly over OTLP, full stop, regardless of shape.
This is exactly the kind of dependency this document exists to surface
honestly rather than paper over.

## What was tested and how

For each backend: start it locally via Docker, obtain (or auto-provision)
an ingestion endpoint and credentials, and send the same request an
`agent-audit` emitter sends — an OTLP `ExportLogsServiceRequest`, over
both gRPC and HTTP where applicable — and observe the response.

## Arize Phoenix

- **Version tested:** `arizephoenix/phoenix:version-20.4.0` (Docker Hub)
- **OTLP surface:** gRPC on `:4317`, HTTP on `:6006/v1/traces`

| Signal | Result |
|---|---|
| Traces (`POST /v1/traces`) | `200 OK` |
| Logs, HTTP (`POST /v1/logs`) | **`405 Method Not Allowed`** — the route exists for other methods but does not accept log export. |
| Logs, gRPC (`LogsService/Export` on `:4317`) | **`UNIMPLEMENTED`** — `Method not found!`, confirmed directly against the gRPC channel. |

**Conclusion:** Phoenix does not implement the OTLP Logs signal in this
version. It is built around traces (spans) as the unit of observability;
`agent-audit` records, being Log Events rather than spans, have no
ingestion path into Phoenix over OTLP today.

## Langfuse

- **Version tested:** `docker.langfuse.com/langfuse/langfuse:4` (resolved
  to `4.24.0` at test time), self-hosted via Langfuse's own published
  `docker-compose.yml` (Postgres + ClickHouse + Redis + MinIO + web +
  worker).
- **License / ownership note:** Langfuse is MIT-licensed. Its copyright
  header now reads **ClickHouse, Inc.**, following ClickHouse's
  acquisition of Langfuse in January 2026 — worth knowing if you're
  evaluating vendor risk, though it doesn't change what was tested here.
- **OTLP surface:** confirmed directly from the compiled server, not
  guessed — `/app/web/.next/server/pages/api/public/otel/v1/` inside the
  running container contains exactly two routes: `traces.js` and
  `metrics.js`. There is no `logs.js`.

| Signal | Result |
|---|---|
| Traces (`POST /api/public/otel/v1/traces`, Basic auth) | `200 OK` |
| Metrics (`POST /api/public/otel/v1/metrics`) | Route exists (not exercised further — out of scope for this record type). |
| Logs (`POST /api/public/otel/v1/logs`) | **`404 Not Found`** — the route does not exist in the built server at all. |
| Legacy Ingestion API (`POST /api/public/ingestion`) | `400 Bad Request` on an empty/OTLP body — reachable, but it is Langfuse's proprietary pre-OTLP format, not what `agent-audit` emits. **This is also the format [ADR context] explicitly avoided**: Langfuse's legacy Ingestion API sunsets on Langfuse Cloud on 2026-11-16 in favor of OTLP/HTTP, so conforming to it now would mean building against a format already on a published deprecation timer. |

**Conclusion:** Langfuse implements OTLP ingestion for traces and metrics
only. Like Phoenix, it has no Logs-signal ingestion path yet, despite
strong general OTel-native positioning.

## What this means for `agent-audit`

[ADR-0003](decisions/0003-otel-log-data-model-as-carrier.md) chose the
OTel Log Data Model because it is the **Stable** part of the OTel spec,
and because building on it means getting "every existing OTel exporter
and backend for free." That claim holds at the **protocol and collector**
level — a generic collector (`otel/opentelemetry-collector-contrib`,
verified working in
[`examples/denied-proposal/`](../examples/denied-proposal/)) receives,
processes, and can route `agent-audit` records with zero special
handling, exactly as promised.

It does **not** yet hold at the level of AI-observability **product**
backends specifically. Phoenix and Langfuse are both, today, trace-only
consumers of OTLP — the Log Data Model being Stable in the OTel spec has
not yet translated into these products implementing that signal. This is
a real, current gap in the ecosystem, not a flaw in the Log Data Model
choice: routing `agent-audit` records into either product today requires
an intermediate step this project does not build (e.g. a collector-side
transform mapping Log Events onto synthetic spans), which is out of scope
here because it would mean the records no longer land *unmodified* — the
thing this document set out to verify in the first place.

**Practical takeaway for an adopter today:** point `agent-audit` at a
generic OTel Collector (as the flagship example does) and export from
there to whatever your organization already uses for storage and
querying — a data warehouse, ClickHouse directly, or a logs-specific
backend that does implement the OTLP Logs signal. Don't expect Phoenix or
Langfuse to ingest `agent-audit` records directly yet.

## Revisit this

This table reflects specific pinned versions tested on 2026-08-29. Both
projects ship frequently; check for Logs-signal support before assuming
this finding still holds, and update this document (not just the ADR)
when it changes.
