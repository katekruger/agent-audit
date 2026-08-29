# Worked example: an auto-allowed read (Pattern A)

Per [spec §5.2, Pattern A](../../spec/SPECIFICATION.md#52-completion-patterns--not-every-action-produces-all-three),
a read that required no human or policy deliberation produces exactly two
Records — `proposed` and `executed` — with **no `decided` Record**. This
is the minimal legal completion pattern; an implementation MAY instead
emit an explicit `decided` Record with `agent_audit.decision` of
`auto_allow` to record the automatic decision's provenance, but is not
required to.

`events.json` is validated against the schema in CI on every push.
