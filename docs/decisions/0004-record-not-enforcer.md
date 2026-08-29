# 0004. Record, not enforcer

- Status: accepted
- Date: 2026-08-29

## Context

`microsoft/agent-governance-toolkit` (AGT) is MIT-licensed, has 6.1k GitHub
stars, ships in five languages, and has roughly 992 conformance tests. It
already implements a policy engine, `require_approval` gates, a Merkle
audit log, and a "Decision BOM." It covers a large fraction of what a
human-in-the-loop agent governance story needs.

Building a competing enforcement platform would mean re-implementing
policy evaluation, gate mechanics, and audit storage that AGT already has,
tested, in production, at scale. That is not a two-week project, and
duplicating it would not obviously make anyone's life better — it would
just be a second choice in a space that already has a credible first one.

## Decision

`agent-audit` records what happened; it never decides what is allowed to
happen. If a proposed change would let this library block, gate, or
evaluate policy on an action, that change is out of scope, full stop —
regardless of how small or how clearly beneficial it looks in isolation.

**The test we hold every design decision to:** AGT should be able to emit
`agent-audit` records as part of its own decision pipeline. If a design
choice makes that impossible or awkward, the design choice is wrong — not
AGT.

## Consequences

`agent-audit` and AGT are complementary, not competitive: AGT can decide
and then emit an `agent-audit` record of what it decided and why. This
keeps the project small (schema + ~200-line emitter) and keeps its adoption
cost near zero — using it never requires adopting a policy engine, a
runtime, or new storage. It also means we give up owning the harder,
higher-value part of the problem (actually deciding what's allowed) in
exchange for owning a smaller piece cleanly.

## Assumption this relies on

That there is durable value in a vendor-neutral, enforcement-agnostic
record format that both AGT-style platforms and simpler point solutions
(a single MCP server, a Claude Code hook) can emit into — i.e., that the
market wants a record its governance tools output, not a fourth
governance tool.

## Known limitation

A record-only design cannot by itself guarantee that recording actually
happened — a misbehaving or compromised agent could simply not call the
emitter. Tamper-evidence and completeness guarantees (e.g. hash chains, as
in `draft-sharif-agent-audit-trail-01`) are explicitly deferred; see the
build plan's open questions. This is a real gap for high-assurance
compliance use cases, accepted deliberately in exchange for staying small.
