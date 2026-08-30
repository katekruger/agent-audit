# vs. Microsoft Agent Governance Toolkit

- Status: accepted — see [ADR-0004](decisions/0004-record-not-enforcer.md)
  for the underlying decision this document expands into prose.

## What AGT is

[`microsoft/agent-governance-toolkit`](https://github.com/microsoft/agent-governance-toolkit)
(AGT) is MIT-licensed, has 6.1k GitHub stars, ships in five languages,
and has roughly 992 conformance tests. It is a governance **platform**:
a policy engine (YAML/OPA/Cedar), `require_approval` gates, sandboxing
and privilege rings, kill switches, an MCP Security Gateway, a
Merkle-chained tamper-evident audit log, and a "Decision BOM." It
already covers a large fraction of what a complete human-in-the-loop
agent governance story needs, and this document says that plainly
rather than manufacturing daylight that isn't there.

## What `agent-audit` is

`agent-audit` is not a competing governance platform. It is a schema
plus a reference emitter — [`py/src/agent_audit_record/`](../py/src/agent_audit_record/)
is four files and, as of this writing, has 100% test coverage at under
200 statements. It has no policy engine, makes no allow/deny decisions,
and owns no storage of its own; it emits OTel LogRecord Events into
whatever OTLP sink you already run. [ADR-0004](decisions/0004-record-not-enforcer.md)
makes this a structural constraint, not just a current-scope note: a
change that would let this library gate or evaluate policy on an action
is out of scope regardless of how useful it looks in isolation.

| | AGT | `agent-audit` |
|---|---|---|
| Shape | Platform | Schema + ~200-line emitter |
| Requires | Adopting a policy engine and runtime | Nothing |
| Enforces | Yes | Never |
| Storage | Its own (Merkle-chained audit log) | Any OTLP sink you already run |
| Lock-in | Real | None |
| Answers | "Should this be allowed?" | "What happened, and what did it cost?" |

## The test we hold every design decision to

AGT should be able to emit `agent-audit` records as part of its own
decision pipeline. If a design choice in this project would make that
awkward or impossible, the design choice is wrong — not AGT. Nothing in
`agent-audit`'s schema or emitter API assumes it is the only thing
deciding, recording, or storing anything; every call takes the decision
as a given.

## What that composability looks like, concretely

There is no AGT integration shipped in this repository yet — build
plan feature #19 (an AGT interop doc plus an emitter adapter) is
targeted at v0.3, not built. What follows is not a claim that this
exists today; it's what the seam looks like using the real, current
[`Emitter`](../py/src/agent_audit_record/emitter.py) API, to make the
composability claim checkable rather than aspirational.

A `require_approval` gate in AGT's policy engine already produces
exactly the two facts `agent-audit` needs to record a decision: who
decided, and what they decided. Wrapping that gate's outcome costs
three calls, not a rewrite of either project:

```python
from agent_audit_record import ActorType, Decision, Emitter, PrincipalType

emitter = Emitter()  # wherever AGT's host process already configures OTel

# 1. Before AGT evaluates the gate, the agent's proposed action is
#    already known -- record it.
emitter.proposed(
    action_id=action_id,
    actor_id=agent_id,
    actor_type=ActorType.AGENT,
    target_system=target_system,
    target_resource=target_resource,
    target_operation=operation,
)

# 2. AGT's policy engine runs -- this call is unchanged, this is AGT's
#    code, doing AGT's job.
agt_decision = policy_engine.evaluate(action_id)

# 3. Record what AGT decided, in agent-audit's vocabulary. The
#    Decision enum crosswalks AGT/MCP/Claude Code/IETF-draft vocabularies
#    (spec/SPECIFICATION.md sec.6.2) so this mapping is a lookup, not
#    a judgment call each integrator makes differently.
emitter.decided(
    action_id=action_id,
    decision=Decision.ALLOW if agt_decision.approved else Decision.DENY,
    principal_type=PrincipalType.HUMAN if agt_decision.approver else PrincipalType.POLICY,
    principal_id=agt_decision.approver or "agt-policy-engine",
    reason=agt_decision.reason,
)
```

AGT keeps its own Merkle-chained log for tamper-evidence — that's a
capability `agent-audit` deliberately does not have yet (see
[ADR-0005](decisions/0005-hash-chaining-deferred.md)) and doesn't
compete to replace. The `agent-audit` record is the portable,
vendor-neutral copy that lands in whatever observability backend the
host organization already runs, independent of whether that
organization ever adopts AGT specifically.
