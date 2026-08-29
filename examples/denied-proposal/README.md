# Worked example: a denied proposal

This is the flagship example from the build plan: an agent proposes a
write action, a human denies it, and the record captures the wasted
inference cost — a metric no existing observability platform can produce
today.

> **Status:** placeholder events, matching only the draft schema skeleton
> in `spec/schema/v1/`. Will be filled out once `spec/SPECIFICATION.md`
> (milestone M1) defines the full attribute set — cost fields, decision
> principal, declared-vs-effective annotations, etc.

`events.json` is validated against `spec/schema/v1/agent-audit.schema.json`
in CI on every push.
