# Crosswalk: draft-sharif-agent-audit-trail-01

`draft-sharif-agent-audit-trail-01` (IETF individual submission, published
2026-08-19 — nine days before this project's build plan, no working group,
expires 2027-02-19) is motivated by EU AI Act Article 12's automatic-recording
requirement and covers substantial overlap with `agent-audit`'s scope. This
document exists to align field names wherever that is possible without
breaking OTel semantic convention style, and to state precisely which parts
of `agent-audit`'s scope the draft does not cover.

This crosswalk is cited in the README regardless of whether the draft's
author responds to outreach about it — see
[`docs/plans/going-public-checklist.md`](../../docs/plans/going-public-checklist.md),
which currently records that outreach as deliberately not yet done.

## Field-by-field crosswalk

| draft-sharif field | Type / values | `agent-audit` equivalent | Notes |
|---|---|---|---|
| `record_id` | string | `agent_audit.action.id` | Both correlate related records for one logical action. |
| `timestamp` | string | (implicit — OTel LogRecord `Timestamp`) | `agent-audit` relies on the OTel Log Data Model's own timestamp field rather than defining a redundant attribute; see [ADR-0003](../../docs/decisions/0003-otel-log-data-model-as-carrier.md). |
| `agent_id` | string | `agent_audit.actor.id` | Direct equivalent. |
| `session_id` | string | (not in core schema) | Candidate for a facet (spec §8), not currently a core attribute. |
| `action_type` | string | `agent_audit.target.operation` | Direct equivalent, though `agent-audit` additionally splits `target.system` and `target.resource` out separately (spec §6.3), which the draft does not. |
| `outcome` | `success \| failure \| timeout \| denied \| escalated` | Split across two attributes: `agent_audit.outcome` (`success \| failure \| timeout \| not_executed`, spec §6.6) and `agent_audit.decision` (`allow \| deny \| defer \| cancel \| timeout \| auto_allow \| auto_deny`, spec §6.5) | **`outcome: denied \| escalated` is exactly `agent-audit`'s approval axis** — `denied` → `agent_audit.decision = deny`, `escalated` → `agent_audit.decision = defer`. The draft conflates the approval axis and the execution-result axis into one `outcome` field; `agent-audit` keeps them as two attributes on two different phase Records, because a denial and an execution failure are different events with different implications (see the `record_phase` row below). |
| `record_phase` | `pre_execution \| post_execution \| concurrent` | `agent_audit.action.phase` (`proposed \| decided \| executed`, spec §6.1) | **This is exactly `agent-audit`'s proposed-vs-executed axis**, and it is the single largest point of alignment between the two efforts. The draft's two-value pre/post split (plus `concurrent`) does not distinguish "proposed" from "decided" the way `agent-audit` does — a `pre_execution` record in the draft could correspond to either an `agent_audit.proposed` or an `agent_audit.decided` Record depending on context, because the draft has no separate concept for the decision itself. |
| `parent_record_id` | string | (not in core schema) | `agent-audit` uses one shared `agent_audit.action.id` across all Records for one action rather than a parent/child pointer; the correlation model differs even though the intent (linking related records) is the same. |
| `prev_hash` | string | (not in core schema — deferred) | See "What we deliberately do not adopt" below. |
| `signature` (optional) | string | (not in core schema — deferred) | See below. |
| `input_hash` (optional) | string | (not in core schema) | No current equivalent; would be a facet candidate if a real user needs input-integrity verification. |
| `output_hash` (optional) | string | (not in core schema) | Same as `input_hash`. |
| `risk_score` (optional) | number | (not in core schema) | No equivalent — `agent-audit` records what was decided and what it cost, not a risk assessment; a risk-scoring facet is plausible future work but is not core. |
| `model_id` (optional) | string | (not in core schema) | `agent-audit` expects this to be reused from `gen_ai.request.model` where the actor is a GenAI agent, rather than restated — see [`spec/mappings/otel-genai.md`](otel-genai.md). |
| `latency_ms` (optional) | integer | `agent_audit.decision.latency_ms` (spec §6.5) | Direct equivalent, though the draft's `latency_ms` is not explicitly scoped to the decision step the way `agent-audit`'s is. |
| `deny_reasons` (optional) | array of string | `agent_audit.decision.reason` (spec §6.5) | `agent-audit` uses a single string rather than an array; a multi-reason facet is possible future work if a real use case needs it. |

## What draft-sharif has that agent-audit does not adopt

**Cryptographic signing and hash-chaining (`prev_hash`, `signature`,
`input_hash`, `output_hash`).** Deliberately deferred — see the build
plan's open questions and [ADR-0004](../../docs/decisions/0004-record-not-enforcer.md)'s
known limitation. Tamper-evidence is a real gap for high-assurance
compliance use cases, but adding it in v1 would make the schema look more
serious and the emitter harder to adopt than the current evidence
justifies. It gets added if and when a real user needs it, not
speculatively.

## agent-audit's three openings — what this specification has that the draft does not

1. **Cost accounting.** The draft has no cost model of any kind — not for
   executed actions, and certainly not for the cost of a proposal that
   was denied before it ran. `agent_audit.cost.*` (spec §6.7), and
   specifically `agent_audit.cost.wasted`, has no equivalent anywhere in
   the draft.
2. **Approver identity.** The draft's `agent_id` identifies the *agent*,
   not who decided. There is no field anywhere in the draft for the
   identity of the human, policy, or system that reached a `denied` or
   `escalated` outcome — `agent_audit.decision.principal.id` and
   `.principal.type` (spec §6.5) have no equivalent. `agent_audit.actor.on_behalf_of`
   (spec §6.2) — the on-behalf-of relationship borrowed from Kubernetes'
   `impersonatedUser` — is absent from the draft entirely.
3. **An MCP binding.** The draft is protocol-agnostic and does not
   reference MCP, its Tasks extension, its elicitation flow, or its tool
   annotations anywhere. `agent-audit`'s MCP crosswalk
   ([`spec/mappings/mcp.md`](mcp.md)) has no counterpart in the draft.
