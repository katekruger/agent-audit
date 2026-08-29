# The cost of denied proposals

> "We spent $4,100 last quarter on proposals humans rejected."

That's the sentence a finance team has never been able to say, because
nothing they already run can produce the number behind it. Every
observability platform available today prices an agent's activity the
same way: tokens × model price, for the work that ran. None of them can
answer "how much did we spend proposing things a human then said no to?"
— because none of them record a cost on an action that never executed.

**The $4,100 figure above is illustrative**, not an audited claim about
any real deployment — nobody could produce it before now, which is
exactly the point. The rest of this document shows the mechanism that
makes a real version of that number computable from your own telemetry,
with no new backend, no new dashboard, and no change to how you already
export OTLP.

## Why this number doesn't exist anywhere else

Every cost model in the ecosystem — `gen_ai.usage.*` token counts,
OpenInference's `llm.cost.*`, every vendor's per-seat or per-call
pricing — is scoped to work that happened. A proposal an agent generated
and a human then rejected still burned real inference: the tokens to
reason about the action, draft it, and justify it. That spend is real
whether or not the action executed, and today it is invisible — folded
into "successful" inference cost with no way to separate it back out, or
simply never recorded at all if the emitting system only logs completed
actions.

`agent_audit.cost.wasted` (spec §6.7) exists to close exactly that gap.
It is `true` on any `decided` Record whose decision is `deny`, `cancel`,
or `timeout` — precisely the Records that spec §5.2's Patterns C and D say
are never followed by an `executed` Record. The absence of that
`executed` Record, combined with `cost.wasted = true`, is the signal: real
cost, zero business outcome.

## The mechanism, worked through the flagship example

[`examples/denied-proposal/`](../examples/denied-proposal/) emits exactly
one denied proposal:

```
agent_audit.decision = deny
agent_audit.cost.amount = 0.0037
agent_audit.cost.currency = usd
agent_audit.cost.component = inference
agent_audit.cost.wasted = true
```

Run it (`./examples/denied-proposal/run.sh`) and the record lands, over
real OTLP, in whatever collector or backend you already point OTel at —
see [`docs/backend-compatibility.md`](backend-compatibility.md) for what
we verified lands unmodified in Langfuse and Phoenix specifically.

## The query

Once records like this are flowing, "how much did we spend on denied
proposals last quarter" is one filter and one sum over data you already
have — no new instrumentation, no new export path:

```sql
-- Illustrative: adjust table/column names to your backend's OTLP log schema.
SELECT
    SUM(attributes['agent_audit.cost.amount']) AS wasted_spend,
    attributes['agent_audit.cost.currency']    AS currency,
    COUNT(*)                                   AS denied_proposals
FROM   otel_logs
WHERE  attributes['agent_audit.action.phase'] = 'decided'
  AND  attributes['agent_audit.cost.wasted']  = true
  AND  timestamp >= now() - INTERVAL '90' DAY
GROUP  BY currency;
```

Run against a Langfuse or Phoenix instance already ingesting
`agent-audit` records (again, see
[`docs/backend-compatibility.md`](backend-compatibility.md) for the exact
query surface each one exposes), this returns a real, defensible number —
the first one that has ever existed for this question.

## Why this is the launch metric, not just a nice-to-have

- **It's legible to a non-technical audience.** A finance team doesn't
  need to understand OpenTelemetry, semantic conventions, or agent
  architecture to understand a dollar figure with "rejected" next to it.
- **It's a number every organization running agentic tooling already has
  an answer to — they just can't currently compute it.** That's a much
  stronger adoption argument than a technical one: it's not "here's a
  better schema," it's "here's a number you're already paying for and
  can't see."
- **It composes with existing FinOps practice.** Most organizations
  already track LLM spend by token cost. `cost.wasted` is a filter on
  data they're already collecting, not a new cost center to justify.
