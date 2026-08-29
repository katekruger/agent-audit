# agent-audit Specification

- Version: `v1` (draft)
- Status: Draft
- Schema: [`spec/schema/v1/agent-audit.schema.json`](schema/v1/agent-audit.schema.json)

## 1. Introduction

`agent-audit` is a semantic convention over the [OpenTelemetry Log Data
Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/) that
binds together what an autonomous agent **proposed**, what a human or
policy **decided**, what **executed**, and what it **cost**, as one
correlated unit.

It is a specification, not a protocol and not a library. It defines
attribute names, required and optional fields, enumerations, and a JSON
Schema. It does not define a wire format, a transport, or a server — those
are OpenTelemetry's job. See
[ADR-0003](../docs/decisions/0003-otel-log-data-model-as-carrier.md).

It does not decide whether an action is allowed, gate an action, or
enforce a policy. It records what a decision-maker — human or automated —
already decided. See [ADR-0004](../docs/decisions/0004-record-not-enforcer.md).

## 2. Conformance language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## 3. Terminology

| Term | Meaning |
|---|---|
| **Action** | A single unit of agent behavior that may require authorization: a tool call, an API invocation, a write. |
| **Actor** | The entity that proposed the action — typically an agent, but the attribute model also admits a human, a policy, or a system proposing on its own behalf. |
| **Principal** | The entity whose decision resolves the `decided` phase — a human, a policy engine, or a timeout. |
| **Record** | One OTel LogRecord Event conforming to this specification — i.e., one `agent_audit.proposed`, `agent_audit.decided`, or `agent_audit.executed` event. |
| **Correlated action** | The set of one, two, or three Records sharing one `agent_audit.action.id`. |

## 4. Carrier

Each Record MUST be emitted as an OpenTelemetry LogRecord Event, per the
[OTel Log Data Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/):
a LogRecord whose `EventName` is non-empty. Implementations MUST set
`EventName` to one of `agent_audit.proposed`, `agent_audit.decided`, or
`agent_audit.executed`, matching the record's `agent_audit.action.phase`
attribute (§6.1).

A Record SHOULD carry `TraceId` and `SpanId` identifying the span that
authorized or performed the underlying operation, so the record binds to
the exact unit of work it describes. When no ambient span exists,
implementations MAY emit the LogRecord without trace context; the record
remains valid, but loses span-level correlation.

## 5. The event model

### 5.1 The three phases

A correlated action is described by up to three Records, distinguished by
`agent_audit.action.phase`:

| Phase | `EventName` | Emitted when | RFC 2119 |
|---|---|---|---|
| `proposed` | `agent_audit.proposed` | An agent has determined an action and is about to seek (or bypass) authorization for it. | An implementation conforming to this specification MUST emit `proposed` before the corresponding `decided` or `executed` record for the same `agent_audit.action.id`. |
| `decided` | `agent_audit.decided` | A decision was reached — by a human, a policy engine, or a timeout. | MUST be emitted before any `executed` record for the same `agent_audit.action.id`, if a `decided` record is emitted at all (§5.2). |
| `executed` | `agent_audit.executed` | The action ran to completion or failure, or was definitively abandoned without running. | MUST be the last record for a given `agent_audit.action.id`, if emitted at all. |

All Records for one correlated action MUST share the same
`agent_audit.action.id`.

### 5.2 Completion patterns — not every action produces all three

**This asymmetry is the central design feature of this specification, not
an edge case.** An implementation MUST NOT assume that a correlated action
always consists of exactly three Records. Four patterns are defined:

#### Pattern A — auto-decided

The action required no human or policy deliberation (e.g. an
auto-allowed read). The correlated action consists of `proposed` +
`executed`; a `decided` record MAY be omitted entirely.

An implementation MAY instead emit an explicit `decided` record with
`agent_audit.decision` of `auto_allow` or `auto_deny` (§6.5) to record the
automatic decision's provenance (e.g. which policy auto-allowed it, and
how long that evaluation took). Both forms — two records or three — are
conformant; omitting the `decided` record is the minimal legal form.

#### Pattern B — deliberated approval

A human or policy engine deliberated and allowed the action. The
correlated action consists of `proposed` + `decided` (`agent_audit.decision`
= `allow`) + `executed`.

#### Pattern C — denial (no execution)

**A denial produces `proposed` + `decided` and MUST NOT be followed by an
`executed` record.** The action never ran; there is nothing to execute,
and emitting an `executed` record for a denied action is a specification
violation. `agent_audit.decision` MUST be `deny` for this pattern.

This is precisely what makes the cost of a denied proposal computable: the
absence of an `executed` record, combined with `agent_audit.cost.wasted`
= `true` on the `decided` record (§6.7), is the signal that inference (or
other) cost was spent on a proposal that produced no business outcome. No
existing observability convention expresses this.

#### Pattern D — decision timeout (no execution)

The approval request itself expired before a principal responded — the
decider never said yes or no. The correlated action consists of
`proposed` + `decided` (`agent_audit.decision` = `timeout`), and MUST NOT
be followed by an `executed` record, for the same reason as Pattern C: the
action never ran.

This is distinct from an *execution* timeout (§6.6, `agent_audit.outcome`
= `timeout`), which describes an action that WAS approved, attempted, and
then failed to complete in time. Implementations MUST distinguish these:
a decision-phase timeout is Pattern D (no `executed` record); an
execution-phase timeout is Pattern B or C's `executed` record carrying
`agent_audit.outcome` = `timeout`.

### 5.3 Correlation

`agent_audit.action.id` (§6.1) is the sole correlation key across a
correlated action's Records. Implementations MUST generate a new
`agent_audit.action.id` per action (RECOMMENDED: UUIDv4) and MUST reuse
the same value across all Records describing that one action's lifecycle.

## 6. Attributes

Attribute names follow OpenTelemetry semantic convention style: flat,
dot-namespaced string keys on the LogRecord's attribute map — not nested
JSON objects. For example, `agent_audit.actor.id` is one attribute key,
exactly as `gen_ai.usage.input_tokens` is one attribute key in the GenAI
conventions this specification reuses.

Attribute requirement levels below (Required / Recommended / Optional)
follow OTel semantic convention terminology: **Required** attributes MUST
be present; **Recommended** attributes SHOULD be present when the
information is available to the emitter; **Optional** attributes MAY be
present.

### 6.1 Core attributes

Present on every Record, regardless of phase.

| Attribute | Type | Requirement | Description |
|---|---|---|---|
| `agent_audit.action.id` | string | **Required** | Correlates the Records for one action (§5.3). RECOMMENDED format: UUIDv4. |
| `agent_audit.action.phase` | string | **Required** | One of `proposed`, `decided`, `executed` (§5.1). MUST match the Record's `EventName`. |
| `agent_audit.schema_url` | string (URI) | **Recommended** | The immutable, versioned URL of the JSON Schema this Record conforms to (§9). |
| `agent_audit.level` | string | **Recommended** | One of `metadata`, `request`, `request_response` (§7). Governs how much of `agent_audit.target.arguments` (§6.3) this Record may legally carry. |

### 6.2 Actor attributes

Who proposed the action. Present on `proposed` Records; MAY be repeated on
`decided` and `executed` Records for convenience, but `agent_audit.action.id`
correlation (§5.3) is the authoritative link, not attribute repetition.

| Attribute | Type | Requirement | Description |
|---|---|---|---|
| `agent_audit.actor.id` | string | **Required** on `proposed` | Identifier of the proposing actor. Implementations SHOULD reuse `gen_ai.agent.id` (see [`spec/mappings/otel-genai.md`](mappings/otel-genai.md)) where the actor is a GenAI agent already carrying that attribute, rather than defining a second identifier for the same entity. |
| `agent_audit.actor.type` | string | **Required** on `proposed` | One of `agent`, `human`, `policy`, `system`. |
| `agent_audit.actor.on_behalf_of` | string | **Recommended** | The human or service principal the actor is acting for, when applicable. Modeled on Kubernetes audit's `impersonatedUser`. This is frequently the first question an auditor asks and is not captured by MCP, the IETF draft, or OTel's existing conventions — see [ADR context in BUILD-PLAN.md §1](../BUILD-PLAN.md). |

### 6.3 Target attributes

What the action acts on. Present on `proposed` Records.

| Attribute | Type | Requirement | Description |
|---|---|---|---|
| `agent_audit.target.system` | string | **Required** on `proposed` | The system being acted on, e.g. `salesforce`, `n8n`, `gmail`. |
| `agent_audit.target.resource` | string | **Required** on `proposed` | The specific resource within that system. |
| `agent_audit.target.operation` | string | **Required** on `proposed` | The operation being performed on the resource. |
| `agent_audit.target.arguments` | any | **Optional**, gated by `agent_audit.level` | The operation's arguments. An implementation MUST NOT populate this attribute with request or response bodies when `agent_audit.level` is `metadata`; MAY populate it with request arguments (not response bodies) when `agent_audit.level` is `request`; MAY populate it fully when `agent_audit.level` is `request_response` (§7). |

### 6.4 Declared vs. effective annotations

This is a trust boundary, not a convenience pairing, and implementations
MUST treat it as one.

The [MCP specification](https://modelcontextprotocol.io/specification/2026-07-28)
states, in more than one place, that `ToolAnnotations` (`readOnlyHint`,
`destructiveHint`, `idempotentHint`, `openWorldHint`) are **hints**, are
**not guaranteed to be faithful or accurate**, and that clients **should
never make decisions based on annotations from an untrusted server**. The
spec additionally defaults `destructiveHint` and `openWorldHint` to
`true` when absent — a server that says nothing is treated as
destructive and open-world until proven otherwise.

`agent-audit` therefore records the claim and the conclusion as two
separate, independently-typed attribute groups:

| Attribute | Type | Requirement | Description |
|---|---|---|---|
| `agent_audit.declared.read_only` | boolean | **Optional** | MCP `readOnlyHint`, recorded verbatim as **untrusted input**. |
| `agent_audit.declared.destructive` | boolean | **Optional** | MCP `destructiveHint`, recorded verbatim as **untrusted input**. Spec default when the source hint is absent: `true`. |
| `agent_audit.declared.idempotent` | boolean | **Optional** | MCP `idempotentHint`, recorded verbatim as **untrusted input**. |
| `agent_audit.declared.open_world` | boolean | **Optional** | MCP `openWorldHint`, recorded verbatim as **untrusted input**. Spec default when the source hint is absent: `true`. |
| `agent_audit.effective.read_only` | boolean | **Recommended** when a policy or authorization layer evaluated the action | What the policy or authorization layer actually concluded about read-only-ness, independent of what the server claimed. |

An implementation MUST NOT use any `agent_audit.declared.*` value as the
sole justification recorded for a `decided` Record's decision. If a
decision's justification is recorded (`agent_audit.decision.reason`,
§6.5), it MUST reflect the effective, evaluated conclusion — not the
declared hint. Put plainly, and stated for documentation purposes
(see `README.md`): **CloudTrail's `readOnly` is recorded as fact.
MCP's `readOnlyHint` is a claim.** `agent-audit` keeps that distinction
visible in the record rather than collapsing it.

### 6.5 Decision attributes

Present on `decided` Records.

| Attribute | Type | Requirement | Description |
|---|---|---|---|
| `agent_audit.decision` | string | **Required** on `decided` | One of `allow`, `deny`, `defer`, `cancel`, `timeout`, `auto_allow`, `auto_deny` (§6.5.1). |
| `agent_audit.decision.reason` | string | **Recommended** | Human-readable justification. MUST reflect the effective conclusion, not a declared hint (§6.4). |
| `agent_audit.decision.principal.id` | string | **Recommended** | Identifier of the human, policy, or system that reached the decision. |
| `agent_audit.decision.principal.type` | string | **Required** on `decided` | One of `human`, `policy`, `timeout`, `default`. |
| `agent_audit.decision.policy.id` | string | **Optional** | Identifier of the policy in force, when `principal.type` is `policy`. |
| `agent_audit.decision.policy.version` | string | **Optional** | Version of the policy in force, when `principal.type` is `policy`. |
| `agent_audit.decision.latency_ms` | integer | **Optional** | Milliseconds between the `proposed` Record and this `decided` Record. |

#### 6.5.1 The decision enum: an interoperability layer, not a fourth dialect

`agent_audit.decision` MUST use exactly one of the seven values below.
This enum is deliberately a superset that can losslessly represent the
decision vocabularies already in use by MCP, Claude Code, and
`draft-sharif-agent-audit-trail-01`, so that an emitter sitting on top of
any of those systems can map into it without inventing new meaning:

| `agent_audit.decision` | MCP `ElicitResult.action` | Claude Code `permissionDecision` | IETF draft `outcome` |
|---|---|---|---|
| `allow` | `accept` | `allow` | — |
| `deny` | `decline` | `deny` | `denied` |
| `defer` | — | `deferToUser` | `escalated` |
| `cancel` | `cancel` | — | — |
| `timeout` | — | — | — |
| `auto_allow` | — | — | — |
| `auto_deny` | — | — | — |

`timeout`, `auto_allow`, and `auto_deny` have no equivalent in the three
upstream vocabularies surveyed; they exist because none of those systems
distinguishes an unanswered approval request from an explicit denial, or
an automatic decision from a deliberated one. A full field-by-field
crosswalk, including fields these vocabularies define that `agent-audit`
does not map, lives in [`spec/mappings/`](mappings/).

### 6.6 Execution attributes

Present on `executed` Records.

| Attribute | Type | Requirement | Description |
|---|---|---|---|
| `agent_audit.outcome` | string | **Required** on `executed` | One of `success`, `failure`, `timeout`, `not_executed`. |
| `agent_audit.not_executed_reason` | string | **Required** when `agent_audit.outcome` is `not_executed`; otherwise MUST NOT be present | One of `denied`, `cancelled`, `expired`, `superseded`. |
| `agent_audit.effect.records_changed` | integer | **Optional** | Count of records or resources changed by the action. |
| `agent_audit.effect.reversible` | boolean | **Optional** | Whether the effect can be undone. |
| `agent_audit.effect.undo_token` | string | **Optional** | An opaque token usable to reverse the effect, when `agent_audit.effect.reversible` is `true` and the target system supports it. |

An `executed` Record with `agent_audit.outcome` = `timeout` describes an
action that was authorized and attempted, but did not complete within an
expected window — this is distinct from Pattern D (§5.2), where the
*decision itself* timed out and no `executed` Record exists at all.

### 6.7 Cost attributes

The genuinely novel part of this specification: no existing convention
models the cost of an action a human rejected before it ran.

| Attribute | Type | Requirement | Description |
|---|---|---|---|
| `agent_audit.cost.amount` | double | **Optional** | The cost quantity, in whatever unit `agent_audit.cost.unit` specifies. |
| `agent_audit.cost.currency` | string | **Optional** | ISO 4217 currency code, or absent/null for a non-monetary unit. |
| `agent_audit.cost.unit` | string | **Optional** | One of `usd`, `api_calls`, `credits`, `seat_hours`, `quota`. |
| `agent_audit.cost.component` | string | **Optional** | One of `inference`, `action`, `total`. |
| `agent_audit.cost.wasted` | boolean | **Required** on `decided` Records where `agent_audit.decision` is `deny`, `cancel`, or `timeout`; **Optional** elsewhere | `true` when the cost recorded on this Record was spent on a proposal that produced no executed outcome. Absent is equivalent to `false`. |

Per [ADR AGENTS.md "reuse before you define"](../AGENTS.md), implementations
MUST NOT restate token counts or inference cost using new attribute names
when reusing an existing convention is possible:

- Token counts MUST be recorded using `gen_ai.usage.input_tokens` and
  `gen_ai.usage.output_tokens`, not a new `agent_audit.*` token attribute.
- Inference cost MUST be recorded using OpenInference's `llm.cost.total`,
  `llm.cost.prompt`, and `llm.cost.completion` (Apache-2.0; freely
  reusable — see [`spec/mappings/otel-genai.md`](mappings/otel-genai.md)),
  not a new `agent_audit.*` inference-cost attribute.

`agent_audit.cost.currency` exists specifically because OpenInference's
`llm.cost.*` fields are USD-implicit and carry no currency attribute of
their own; `agent_audit.cost.*` fills that one gap rather than
duplicating the fields it sits alongside.

**The launch metric this specification exists to make computable:** for
any Pattern C or Pattern D correlated action (§5.2), the `decided`
Record's `agent_audit.cost.amount` (typically the `inference` component,
reusing `llm.cost.total` where present) with `agent_audit.cost.wasted` =
`true` is directly summable across a time window to answer "how much did
we spend on proposals that were rejected or never decided?" — a query no
existing observability platform can express, because no existing
convention records cost on a record that has no corresponding execution.

## 7. The `level` dial

`agent_audit.level` (§6.1) takes one of three values, borrowed from
[Kubernetes audit policy](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/):

| Value | Meaning |
|---|---|
| `metadata` | Record that the action happened; MUST NOT record request or response bodies in `agent_audit.target.arguments`. |
| `request` | MAY additionally record the request arguments; MUST NOT record response bodies. |
| `request_response` | MAY additionally record both request arguments and response/effect data. |

Whether a deployment records full request and response bodies or only
metadata is a compliance and data-handling decision. This specification
treats it as **policy, not a hardcoded schema choice**: `agent_audit.level`
is an attribute an implementation sets per-deployment or per-action
according to its own compliance requirements, not a constant baked into
this specification or into any one emitter. Kubernetes made this a policy
knob in 2017; this specification adopts the same posture rather than
picking a single fixed verbosity for every deployment.

## 8. Facets

Extensions beyond the core attributes in §6 MUST be namespaced under
`agent_audit.facet.<namespace>.*` and MUST NOT be added to the core
schema (§9). See [`spec/facets/`](facets/).

## 9. JSON Schema and versioning

The normative machine-readable schema for `v1` is
[`spec/schema/v1/agent-audit.schema.json`](schema/v1/agent-audit.schema.json),
published at the immutable URL:

```
https://raw.githubusercontent.com/katekruger/agent-audit/main/spec/schema/v1/agent-audit.schema.json
```

Once a schema version is published, it MUST NOT be edited. A
backward-incompatible or additive normative change MUST be published as a
new version (`spec/schema/v2/`, etc.) with its own immutable URL. A Record
SHOULD carry `agent_audit.schema_url` identifying the exact schema version
it conforms to, so a consumer can validate correctly even as multiple
schema versions coexist across a fleet during a migration.

## 10. Examples

Worked examples for each completion pattern in §5.2 live under
[`examples/`](../examples/) and are validated against the current schema
in CI on every push:

| Example | Pattern | Directory |
|---|---|---|
| Auto-allowed read | A (`proposed` + `executed`, no `decided`) | [`examples/auto-allowed-read/`](../examples/auto-allowed-read/) |
| Human-approved write | B (`proposed` + `decided[allow]` + `executed`) | [`examples/human-approved-write/`](../examples/human-approved-write/) |
| Denied proposal | C (`proposed` + `decided[deny]`, no `executed`) | [`examples/denied-proposal/`](../examples/denied-proposal/) |
| Decision timeout | D (`proposed` + `decided[timeout]`, no `executed`) | [`examples/decision-timeout/`](../examples/decision-timeout/) |
