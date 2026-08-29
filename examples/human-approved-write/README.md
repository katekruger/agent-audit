# Worked example: a human-approved write (Pattern B)

Per [spec §5.2, Pattern B](../../spec/SPECIFICATION.md#52-completion-patterns--not-every-action-produces-all-three),
a deliberated approval produces all three Records: `proposed`, `decided`
(`agent_audit.decision` = `allow`), and `executed`. `agent_audit.decision.latency_ms`
on the `decided` Record captures how long the human took to respond.

`events.json` is validated against the schema in CI on every push.
