# Crosswalk: OTel GenAI semantic conventions

Per [AGENTS.md](../../AGENTS.md)'s "reuse before you define" rule: this
document is scrupulous about what `agent-audit` reuses versus what it
defines, because restating an attribute another semantic convention
already owns is the fastest way for a contribution to be ignored — or
rejected — by the standards body that owns it.

## State of play

- **All 72 `gen_ai.*` attributes are `Development` status**, not `Stable`.
  `agent-audit` builds on the OTel Log Data Model instead — which is
  `Stable` — specifically to avoid inheriting that instability at its
  foundation. See [ADR-0003](../../docs/decisions/0003-otel-log-data-model-as-carrier.md).
- **The `mcp.*` namespace has only four attributes**
  (`mcp.method.name`, `mcp.protocol.version`, `mcp.resource.uri`,
  `mcp.session.id`) and **lags the current MCP spec by two revisions** —
  its documented example value for `mcp.protocol.version` is `2025-06-18`,
  while this specification (and MCP itself) is already on `2026-07-28`.
  Contributing updated coverage here is low-hanging fruit relative to the
  size of the gap, and doing so before proposing anything larger to
  `open-telemetry/semantic-conventions-genai` buys standing with that
  project ahead of a bigger ask (see `BUILD-PLAN.md` §6 milestone M9).

## What we reuse

| We reuse | Instead of defining | Why |
|---|---|---|
| `gen_ai.agent.id` | `agent_audit.actor.id` as a new identifier | Where the actor is already a GenAI agent carrying this attribute, restating it under a new name would just create two identifiers for one entity. `agent_audit.actor.id` (spec §6.2) is populated from `gen_ai.agent.id` when present, and only independently defined when the actor is not a GenAI agent (e.g. `actor.type = human` or `policy`). |
| `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` | A new `agent_audit.*` token-count attribute | Token counts are squarely `gen_ai.*`'s domain. `agent-audit`'s cost model (spec §6.7) references these directly rather than restating them. |
| OpenInference's `llm.cost.total`, `llm.cost.prompt`, `llm.cost.completion` | A new `agent_audit.*` inference-cost attribute | OpenInference is Apache-2.0, so this vocabulary is freely reusable (unlike Phoenix itself, which is Elastic License 2.0). These three fields already express inference cost; `agent-audit` does not duplicate them. |
| `gen_ai.request.model` | A new `agent_audit.*` model-identifier attribute | Candidate reuse target for any facet or crosswalk (e.g. `draft-sharif`'s `model_id`, see [`spec/mappings/ietf-draft-sharif.md`](ietf-draft-sharif.md)) that needs to identify which model proposed an action. |

## What we define, and why nothing upstream already covers it

| `agent-audit` defines | Why no existing OTel convention covers it |
|---|---|
| `agent_audit.cost.currency`, `.unit`, `.wasted` | OTel has **no cost attribute of any kind** outside the GenAI-specific `gen_ai.usage.*` token counts, and OpenInference's `llm.cost.*` fields are USD-implicit with no currency field at all. Nothing anywhere models a non-monetary cost unit (`api_calls`, `credits`, `seat_hours`, `quota`), and nothing anywhere models the cost of a proposal that was never executed — `agent_audit.cost.wasted` (spec §6.7) has no analog in any surveyed convention. |
| `agent_audit.decision`, `.decision.principal.*`, `.decision.policy.*` | OTel has **no concept of human approval** at all — no attribute anywhere in the GenAI or general semantic conventions represents a human or policy decision gating an action, let alone the identity of who made it. |
| `agent_audit.actor.on_behalf_of` | No OTel convention has an approver- or actor-impersonation concept analogous to Kubernetes audit's `impersonatedUser`. |
| `agent_audit.action.phase` and the three-phase event model itself | OTel has **no proposed-vs-executed distinction**. Spans and GenAI attributes describe what an agent *did*; nothing describes what an agent *proposed to do but was stopped from doing*. This is the specification's central contribution (spec §5). |
| `agent_audit.declared.*` / `.effective.*` | No OTel convention encodes a trust boundary between a self-reported capability claim and an independently-evaluated conclusion about the same fact. |

## The evaluation family: a deliberately rejected reuse candidate

OTel's `gen_ai.evaluation.*` namespace is the closest existing thing to
"a human or system judged this agent's behavior," and it is tempting to
overload it for approval decisions rather than defining `agent_audit.decision`
independently. **This specification deliberately does not do that.**

`gen_ai.evaluation.*` is designed for **post-hoc quality scoring** —
grading an output after the fact, typically for offline analysis or
online quality monitoring (e.g. "was this response helpful?", "did this
response hallucinate?"). `agent_audit.decision` records a **pre-execution
authorization decision** — whether an action was allowed to happen at
all, made by a human, a policy, or a timeout, before or concurrent with
execution.

These are semantically different acts with different legal weight: an
evaluation score answers "was this good?"; an `agent-audit` decision
answers "was this allowed?" Conflating the two into a single attribute
family would erase exactly the distinction that matters for compliance —
a low evaluation score is feedback; a `deny` decision is the gate that
prevented an action from executing at all. `agent-audit` therefore treats
`gen_ai.evaluation.*` as an adjacent, non-overlapping convention, not a
reuse target.
