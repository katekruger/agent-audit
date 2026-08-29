# Crosswalk: Model Context Protocol (MCP)

Protocol revision referenced throughout: `2026-07-28` (verified against
[`schema.ts`](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/schema/2026-07-28/schema.ts)
line 30).

## Elicitation → decision

MCP's elicitation result is the closest thing anywhere in MCP to an
approval record:

| `ElicitResult.action` | `agent_audit.decision` |
|---|---|
| `accept` | `allow` |
| `decline` | `deny` |
| `cancel` | `cancel` |

**What `ElicitResult` lacks, stated precisely:** no approver identity, no
timestamp, and no durable record. It is an ephemeral RPC result, scoped to
one request/response exchange — once the response is consumed, nothing
about who decided, when, or under what authority survives anywhere. That
absence is not incidental; it is the gap this specification exists to
fill. `agent_audit.decided` records carry `agent_audit.decision.principal.id`,
`agent_audit.decision.principal.type`, and `agent_audit.decision.latency_ms`
(spec §6.5) — an approver identity and a timestamp-equivalent, attached to
a Record that outlives the RPC call that produced the decision.

### Elicitation is now a Multi Round-Trip Request (MRTR)

As of `2026-07-28`, MCP made elicitation stateless: the server returns
`resultType: "input_required"` instead of blocking on the client, and the
client retries the call with `inputResponses` once it has an answer.
Two modes exist: `form` (structured fields) and `url` (the client is
handed a URL to complete out-of-band — added specifically to keep
sensitive input, e.g. payment details or credentials, out of the model's
context window).

This statelessness does not change the mapping above — `agent_audit.decision`
is still populated from the eventual `ElicitResult.action` once the round
trip resolves — but it does mean an `agent-audit` emitter sitting on top
of elicitation cannot assume a single synchronous call/response pair. The
`agent_audit.proposed` Record SHOULD be emitted when the elicitation is
first initiated, not when it resolves, so that `agent_audit.decision.latency_ms`
(spec §6.5) correctly reflects the full round-trip time, including any
`input_required` retries.

## Tool annotations → declared attributes

MCP's `ToolAnnotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`,
`openWorldHint`) map to `agent_audit.declared.*` (spec §6.4), recorded
verbatim as **untrusted input** — never as the basis for a decision. The
MCP specification states, more than once, that these are hints, not
guaranteed to be faithful, and that a client should never make decisions
based on annotations from an untrusted server. `agent-audit` treats that
warning as load-bearing: `agent_audit.effective.read_only` (spec §6.4)
records what a policy or authorization layer actually concluded,
independently of whatever the server claimed.

## Tasks extension → the transport for the pause, not the record of the decision

MCP's Tasks extension (negotiated as `io.modelcontextprotocol/tasks`) has
a lifecycle of `working` → `input_required` → `completed | failed | cancelled`.
`CreateTaskResult` is durably created **before** the response is sent to
the caller, and the MCP docs name human approval gates explicitly as a
Tasks use case.

**The division of labor is deliberate and explicit: Tasks is the
transport for the pause. It is not the record of the decision.** A task
is TTL-bounded and disposable by design — it exists to let a long-running
or human-gated operation survive a disconnect, not to serve as a
compliance record. An audit record must outlive the task that carried the
pause; once a task expires or is garbage-collected, whatever decision it
carried should already be durable somewhere else. `agent-audit` rides on
top of Tasks for the pause mechanics and never attempts to replace or
duplicate them — see [ADR-0003](../../docs/decisions/0003-otel-log-data-model-as-carrier.md)
and [ADR-0004](../../docs/decisions/0004-record-not-enforcer.md) for the
same non-competition posture applied elsewhere.

## Why not an `audit/*` JSON-RPC method (SEP-2577)

MCP's SEP-2577 (status: Final, revision `2026-07-28`) deprecates Roots,
Sampling, and Logging, and its stated rationale names OpenTelemetry
explicitly as the correct alternative to an application-protocol logging
channel. A proposed `audit/*` JSON-RPC method for `agent-audit` records
would be rejected on exactly the grounds SEP-2577 already articulated —
MCP has told the ecosystem, in effect, that logging is not this
protocol's job. See [ADR-0003](../../docs/decisions/0003-otel-log-data-model-as-carrier.md)
and [`docs/why-not-a-protocol.md`](../../docs/why-not-a-protocol.md) for
the full reasoning.

## Field reference

| MCP concept | `agent-audit` equivalent | Gap this specification fills |
|---|---|---|
| `ElicitResult.action` | `agent_audit.decision` | Approver identity, timestamp, durability beyond the RPC call. |
| `ToolAnnotations.*Hint` | `agent_audit.declared.*` | A trust boundary — the hint is never the decision's justification. |
| (none) | `agent_audit.effective.read_only` | MCP has no concept of a policy's *evaluated* conclusion, only the server's self-reported hint. |
| MCP Tasks lifecycle | (not mapped — different concern) | Tasks is the pause mechanism; `agent-audit` is the durable record of what was decided during the pause. |
| `mcp.method.name`, `mcp.protocol.version`, `mcp.resource.uri`, `mcp.session.id` (OTel `mcp.*` semconv) | `agent_audit.target.system` / `.resource` / `.operation` (loosely, when the target is an MCP server) | See [`spec/mappings/otel-genai.md`](otel-genai.md) for the current state of OTel's `mcp.*` coverage and where it lags the spec. |
