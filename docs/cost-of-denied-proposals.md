# The cost of denied proposals

- Status: placeholder — see `BUILD-PLAN.md` §0 point 6 and §10 point 2.

No observability platform today models the cost of a proposal a human
rejected before it ran. Every platform models cost as tokens × model
price for actions that executed; none can answer "how much did we spend on
inference for things a human then said no to?"

`agent_audit.cost.wasted` (set `true` when `agent_audit.decision` is
`deny`, `cancel`, or `timeout` and no `executed` event follows) is designed
to make that number computable directly from existing telemetry, without a
new backend.

TODO: once the reference emitter and an example backend integration exist
(build plan feature #17, the `cost-of-denied-proposals` reporter, targeted
v0.3), replace this placeholder with the actual worked number and the
query used to produce it — this is intended as launch collateral, per the
build plan's distribution section.
