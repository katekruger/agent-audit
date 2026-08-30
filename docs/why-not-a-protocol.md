# Why not a protocol?

- Status: accepted — see [ADR-0003](decisions/0003-otel-log-data-model-as-carrier.md)
  for the underlying decision this document expands into prose.

## The obvious design that doesn't survive contact with the MCP spec

The natural first instinct for "record what an agent proposed, what a
human decided, and what executed" is to add it to the protocol the
agent and the tool are already speaking. For MCP, that would mean a new
JSON-RPC method — something like `audit/record`, sitting alongside
`tools/call` and `elicitation/create` — that a server or client calls
to durably log a decision as it happens.

That design is dead on arrival, and MCP's own spec says so.

## SEP-2577 already answered this question

MCP's SEP-2577 (status: **Final**, revision `2026-07-28`) deprecates
three existing protocol features — Roots, Sampling, and Logging — and
its stated rationale names OpenTelemetry explicitly as the correct
mechanism for the kind of concern Logging used to carry. MCP is not
silent on where observability data should live; it has an opinion, and
the opinion is "not in this protocol."

A proposed `audit/*` JSON-RPC method for `agent-audit` records would be
rejected on exactly the grounds SEP-2577 already articulated for
`logging/*`. There is no principled distinction between "logging" and
"audit logging" that would let one back in through the front door after
the other was shown out. If anything, an audit record is a stricter
case: it needs to survive the death of the MCP session, the death of
the client process, and — per [MCP Tasks](spec/mappings/mcp.md) — the
expiry of whatever ephemeral task carried the human-in-the-loop pause.
A record that only exists inside an active JSON-RPC connection is
already a worse fit for that job than SEP-2577's own rejected `Logging`
capability was.

**MCP has, in effect, told the ecosystem to stop logging over the
protocol.** That's a stronger and more specific claim than "MCP doesn't
have an audit feature" — it's that MCP had one, in a related form
(`Logging`), used it, and removed it, on the record, citing OpenTelemetry
by name as the replacement. Most of the ecosystem building
observability or governance tooling on top of MCP has not internalized
this yet; several designs proposed in adjacent projects still assume a
protocol-level logging or audit channel is the natural extension point.

## What this means for `agent-audit`

`agent-audit` is a **semantic convention** — a schema and vocabulary for
attributes and event shapes carried over OpenTelemetry's existing Log
Data Model (itself Stable; see [ADR-0003](decisions/0003-otel-log-data-model-as-carrier.md))
— not a wire protocol, and not an extension to MCP's wire protocol.
Concretely, that means:

- No new JSON-RPC methods, capabilities, or MCP extension namespaces.
  `agent-audit` never needs MCP's consent to exist, and MCP never needs
  to allocate anything for it.
- Any transport that can carry an OTel LogRecord — an OTLP exporter, a
  vendor SDK, a file sink — can carry an `agent-audit` record. The
  record is decoupled from whatever caused it (an MCP tool call, a
  Claude Code hook, a LangGraph `interrupt()`), by design.
- MCP Tasks and MCP elicitation remain exactly what they are: pause and
  ask-a-human mechanics. `agent-audit` records the *outcome* of a pause
  or an elicitation; it never tries to become the pause mechanism
  itself. See [`spec/mappings/mcp.md`](mappings/mcp.md) for the
  field-by-field mapping.

This is also why `agent-audit` has no interest in [SEP-1763
(Interceptors)](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1763)
succeeding as a place to attach audit logging, even though its proposal
text mentions "log all MCP operations for compliance" as a motivating
use case. If SEP-1763 lands, it would be a fine place to *call* an
`agent-audit` emitter from — a hook point, not a storage or transport
mechanism. It would not change anything about where the record itself
lives or how it's shaped. As of this writing SEP-1763 is open, Draft,
and has no sponsor; nothing here depends on its outcome either way.
