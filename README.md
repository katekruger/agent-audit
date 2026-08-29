# agent-audit

**A portable record binding what an agent proposed, what a human decided,
what executed, and what it cost.**

An OpenTelemetry semantic convention plus a thin reference emitter. The
record, not the enforcer.

> **Status:** early scaffold. The specification is not yet written — see
> [`BUILD-PLAN.md`](BUILD-PLAN.md) for the plan and
> [`docs/plans/going-public-checklist.md`](docs/plans/going-public-checklist.md)
> for what has to be true before this repo goes public.

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

## License

Apache-2.0 — see [`LICENSE`](LICENSE).
