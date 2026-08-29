# Worked example: a denied proposal (Pattern C)

The flagship example from the build plan: an agent proposes a bulk delete,
a human denies it, and the record captures the wasted inference cost — a
metric no existing observability platform can produce today.

Per [spec §5.2, Pattern C](../../spec/SPECIFICATION.md#52-completion-patterns--not-every-action-produces-all-three),
this correlated action consists of exactly two Records — `proposed` and
`decided` — and **no `executed` Record**, because the action never ran.
`agent_audit.cost.wasted` is `true` on the `decided` Record: the schema
requires this whenever `agent_audit.decision` is `deny`, `cancel`, or
`timeout` (see [`spec/schema/v1/agent-audit.schema.json`](../../spec/schema/v1/agent-audit.schema.json)).

`events.json` is validated against the schema in CI on every push.
