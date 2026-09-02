# agent-audit

**A portable record binding what an agent proposed, what a human decided,
what executed, and what it cost.**

An OpenTelemetry semantic convention plus a thin reference emitter. The
record, not the enforcer.

> **Status:** draft specification. See
> [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md) for the normative
> definition, [`BUILD-PLAN.md`](BUILD-PLAN.md) for the plan, and
> [`docs/plans/going-public-checklist.md`](docs/plans/going-public-checklist.md)
> for what has to be true before this repo goes public.

An agent proposes a CRM bulk delete. A human denies it. The record shows
`proposed` + `decided`, no `executed`, and `cost.wasted = true` with the
inference spend that produced the rejected proposal — the thing no
existing observability convention can say. This is the real, unedited
output of [`examples/denied-proposal/run.py`](examples/denied-proposal/):

![A terminal recording of the denied-proposal example: an agent proposes a Salesforce bulk delete, a human denies it, and the printed record shows cost.wasted = true with no executed event ever appearing.](docs/media/denied-proposal.gif)

## What this is

This repository ships a **specification**, not a library. The Python
package under [`py/`](py/) is a reference implementation, not the
deliverable.

The most widely-deployed human-in-the-loop gate in the agent ecosystem
today records the decision but not the decider. `agent-audit` defines a
three-phase event model — `proposed` → `decided` → `executed` — that binds
those events together with a correlation ID, records approver identity as
a first-class field, and models the cost of both executed actions and
proposals a human rejected before they ran.

`agent-audit` also does not let a server's self-reported claims stand in
for a decision's justification. MCP tool annotations like `readOnlyHint`
are, per the MCP spec itself, hints — not guaranteed to be faithful, and
not a safe basis for a client's decision. **CloudTrail records `readOnly`
as fact. MCP's `readOnlyHint` is a claim.** `agent-audit` records both,
under separate attribute names (`agent_audit.declared.*` vs.
`agent_audit.effective.*`), and a decision's recorded reason must reflect
the effective conclusion, never the declared claim — see
[spec §6.4](spec/SPECIFICATION.md#64-declared-vs-effective-annotations).

The PyPI distribution name for the Python package is `agent-audit-record`,
not `agent-audit` — that name is already taken by an unrelated static
security analyzer for AI agents, one of whose rules, `AGENT-037`, flags
"Missing Human-in-the-Loop." That other tool flags the absence of a human
in the loop; this one records the decision at one.

## How this relates to what already exists

| Layer | Owner | `agent-audit`'s relationship |
|---|---|---|
| Policy & enforcement | [Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) | **Emits into** `agent-audit` |
| Gate mechanics | MCP Tasks, LangGraph, Temporal | **Rides on** — never competes |
| Ask-a-human | MCP elicitation | **Records the outcome of** |
| Transport | OpenTelemetry | **Is a convention over** |
| Backends | Langfuse, Phoenix, Braintrust, any OTLP sink | **Lands in**, unchanged |

See [`docs/vs-agent-governance-toolkit.md`](docs/vs-agent-governance-toolkit.md)
for the detailed positioning and [`docs/why-not-a-protocol.md`](docs/why-not-a-protocol.md)
for why this is a semantic convention and not a wire protocol.

This project is also not the only recent attempt at this vocabulary —
`draft-sharif-agent-audit-trail-01` was published nine days before this
plan and covers much of the same ground. See
[`spec/mappings/ietf-draft-sharif.md`](spec/mappings/ietf-draft-sharif.md)
for the field-by-field crosswalk.

## Repository layout

```
spec/            the specification — the actual deliverable
py/              reference implementation (Python)
integrations/    Claude Code hooks, MCP middleware
examples/        worked examples, validated against the schema in CI
docs/            positioning docs and architecture decision records
```

## See also

Every project here shares one idea: a GTM system should refuse to act on data it cannot verify.

[n8n-operator](https://github.com/katekruger/n8n-operator) — the same human gate, enforced in a running system rather than described in a schema. Every workflow run passes an approval before it executes.

[instantly-mcp](https://github.com/katekruger/instantly-mcp) — code-enforced autonomy tiers over a live commercial API. The decision boundary this convention records is the one that project already draws.

## License

Apache-2.0 — see [`LICENSE`](LICENSE).
