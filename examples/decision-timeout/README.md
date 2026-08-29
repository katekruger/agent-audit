# Worked example: a decision timeout (Pattern D)

Per [spec §5.2, Pattern D](../../spec/SPECIFICATION.md#52-completion-patterns--not-every-action-produces-all-three),
an approval request that expired before any principal responded produces
`proposed` + `decided` (`agent_audit.decision` = `timeout`,
`agent_audit.decision.principal.type` = `timeout`), and **no `executed`
Record** — the action never ran, exactly as in a denial.

This is distinct from an *execution* timeout, where the action was
approved and attempted but failed to complete — that case would appear on
an `executed` Record with `agent_audit.outcome` = `timeout` instead (see
spec §6.6).

`events.json` is validated against the schema in CI on every push.
