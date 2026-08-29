# vs. Microsoft Agent Governance Toolkit

- Status: placeholder — see [ADR-0004](decisions/0004-record-not-enforcer.md)
  for the accepted decision this document will expand into full prose.

`microsoft/agent-governance-toolkit` (AGT) is MIT-licensed, has 6.1k GitHub
stars, ships in five languages, and has roughly 992 conformance tests. It
is a governance **platform**: a policy engine, `require_approval` gates, a
Merkle audit log, and a "Decision BOM."

`agent-audit` is not a competitor to AGT. It is a schema plus a
~200-line emitter, with no policy engine, no enforcement, and no storage
of its own. AGT should be able to emit `agent-audit` records as part of
its own decision pipeline — that composability is the design target,
stated as a test in ADR-0004.

| | AGT | agent-audit |
|---|---|---|
| Shape | Platform | Schema + thin emitter |
| Requires | Adopting a policy engine and runtime | Nothing |
| Enforces | Yes | Never |
| Storage | Its own | Any OTLP sink you already run |
| Answers | "Should this be allowed?" | "What happened, and what did it cost?" |

TODO: expand with real usage examples once the reference implementation
and an AGT interop adapter exist (build plan feature #19, targeted v0.3).
