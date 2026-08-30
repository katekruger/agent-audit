# 0006. IETF draft author outreach is deferred, against the build plan's own recommendation

- Status: accepted
- Date: 2026-08-30

## Context

`draft-sharif-agent-audit-trail-01` was published nine days before this
project's build plan, and covers substantially the same ground: an
event model binding an agent's proposal to a human decision and its
execution. [BUILD-PLAN.md's M0 milestone](../../BUILD-PLAN.md#9-milestones)
explicitly pairs the Python distribution name decision with "email sent
to the draft author," and [§10](../../BUILD-PLAN.md#10-distribution)
does not list this as optional. [`spec/mappings/ietf-draft-sharif.md`](../../spec/mappings/ietf-draft-sharif.md)
already does the field-by-field crosswalk work this outreach would be
grounded in.

Going public with a competing vocabulary before reaching out to that
author is, in the build plan's own words, the single worst available
move: it reads as either not having done the homework to notice the
overlap, or having noticed and chosen not to engage.

## Decision

The project owner has deliberately chosen not to send that outreach
yet, and this repository stays **private** until that changes — see
[docs/plans/going-public-checklist.md](../plans/going-public-checklist.md),
which lists it as an open, unchecked item rather than treating the
private status as a substitute for actually resolving it.

This ADR exists so the deferral is a recorded, visible decision rather
than a silently-skipped step that a later reader (or a future audit)
would otherwise have to reconstruct from the going-public checklist
alone.

## Consequences

Easier: nothing about repo-internal work is blocked by outreach that
hasn't happened yet — the spec, emitter, and integrations can all be
built and tested without it.

Harder: this repository cannot go public under the going-public
checklist's own gates until the outreach happens, or until the project
owner explicitly revises this decision and the checklist together. Any
future session working on "go public" tasks must not skip past this
gate by treating repo-completeness as sufficient — it explicitly is
not, per the build plan's own competitive-posture reasoning in
[§7](../../BUILD-PLAN.md#7-competitive-posture).

## Assumption this relies on

That the cost of going public later, once outreach has happened, is
lower than the cost of the reputational risk the build plan identifies
in going public first. If the draft author publishes a revision, gets
significant traction, or the IETF draft expires (build plan cites a
February expiry) before outreach happens, this tradeoff should be
revisited.

## Known limitation

This ADR records that the decision was deliberate; it does not resolve
it. The outreach itself — drafting and sending the email — remains an
action only the project owner can take, since it is a message sent on
their behalf to a third party.
