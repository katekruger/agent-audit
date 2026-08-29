# Crosswalk: draft-sharif-agent-audit-trail-01

- Status: placeholder — see `BUILD-PLAN.md` milestone M2 and §7.

`draft-sharif-agent-audit-trail-01` (IETF individual submission, published
2026-08-19, expires 2027-02-19) covers much of the same ground as this
project. This document exists so we align field names rather than ship a
fourth competing vocabulary — see the note in
[`BUILD-PLAN.md`](../../BUILD-PLAN.md) §0 and §7 about contacting the
author before, not after, this spec is written.

| draft-sharif field | `agent-audit` equivalent |
|---|---|
| `record_phase: pre_execution\|post_execution\|concurrent` | `agent_audit.action.phase: proposed\|decided\|executed` (not a 1:1 mapping — TODO) |
| `outcome: denied\|escalated` | `agent_audit.decision: deny\|defer` |
| `record_id` | `agent_audit.action.id` |
| `agent_id` | `agent_audit.actor.id` |
| `prev_hash` / `signature` | out of scope for `agent-audit` v1 — see the build plan's open questions |

TODO: complete the full field-by-field crosswalk once M1 is done and once
the author has been contacted (build plan milestone M0).
