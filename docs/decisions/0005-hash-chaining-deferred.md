# 0005. Hash chaining and signing are deferred, not designed out

- Status: accepted
- Date: 2026-08-30

## Context

`draft-sharif-agent-audit-trail-01` includes a hash chain (`prev_hash`)
and ECDSA P-256 signing over each record, giving tamper-evidence: a
gap or edit in the chain is detectable without trusting the storage
backend. `agent-audit` currently emits plain OTel LogRecord Events with
no chaining or signing field.

Adding a `prev_hash`-style field to v1 would require: a canonical
serialization order for hashing (attribute ordering is not otherwise
meaningful in OTel), a place to persist "the last hash" across process
restarts and across concurrent emitters sharing one `service.name`, and
a signing key management story this project has no opinion on. None of
that is free, and all of it is the kind of feature that makes a schema
*look* more serious without making it easier to adopt — [BUILD-PLAN.md
§11](../../BUILD-PLAN.md#11-open-questions-to-resolve-before-m1) calls
this out directly as a trap: "the kind of feature that makes a schema
look serious and makes an emitter hard to adopt."

## Decision

v1 of the schema and the reference emitter ship with no hash chain and
no signing. The three-phase event model is designed so that adding a
`prev_hash`-shaped attribute later is additive (a new optional
attribute under `agent_audit.integrity.*`), not a breaking schema
change — but nothing is built or reserved for it now.

We will build it when a real user asks for it, not speculatively.

## Consequences

Easier: adoption cost stays at "point an existing OTLP exporter at this
schema" — no key management, no persistence-of-last-hash problem, no
canonicalization spec to get right before v1 ships.

Harder: `agent-audit` records are exactly as tamper-evident as whatever
backend stores them and nothing more. A record can be edited or deleted
after the fact by anyone with write access to the sink, and nothing in
the schema itself would reveal that. For a compliance regime that
specifically requires tamper-evidence (rather than just "a record
exists"), this schema alone is not sufficient today.

## Assumption this relies on

That most early adopters need "a record exists and lands in our OTLP
sink" far more urgently than they need "the record is cryptographically
tamper-evident" — i.e., that hash-chaining is a v2 feature for a
smaller, more demanding subset of users, not a v1 blocker for everyone.

## Known limitation

If EU AI Act Article 12 or a similar compliance regime is eventually
read to require tamper-evidence specifically (not just record
existence), this decision would need revisiting before this project
could be used to satisfy that reading. No such reading is confirmed as
of this ADR's date.
