# MCP server middleware

The unclaimed position (`BUILD-PLAN.md` §1, §6): Claude Code hooks are
client-side and Anthropic-specific; Microsoft AGT is enforcement-side. A
record an MCP **server** itself emits, that survives the client, belongs
to neither — this is that record.

`agent_audit_mcp.py` provides `AgentAuditMiddleware`, a
[`ServerMiddleware`](https://github.com/modelcontextprotocol/python-sdk)
for the official MCP Python SDK (v2 line, `mcp>=2,<3`) that wraps every
`tools/call` in `agent_audit.proposed` + `agent_audit.executed` — the
minimal legal completion, spec Pattern A — with no code change to the
tools themselves.

## Install

Requires `mcp>=2,<3` and `agent-audit-record` (both currently unpublished
— see the main [README](../../README.md)). This module has no package of
its own yet; copy `agent_audit_mcp.py` into your server, or vendor it,
until this integration ships as a proper distribution.

## Usage

```python
from mcp.server.mcpserver import MCPServer
from agent_audit_record import Emitter

from agent_audit_mcp import AgentAuditMiddleware, current_action_id, declare_annotations

emitter = Emitter()  # no-op until the host configures an OTel LoggerProvider

server = MCPServer(
    "my-server",
    middleware=[AgentAuditMiddleware(emitter, target_system="my-server")],
)

# Optional: restate a tool's ToolAnnotations so agent_audit.declared.*
# gets populated -- the SDK doesn't expose them to middleware (see
# agent_audit_mcp.py's docstring for why).
declare_annotations("bulk_delete", read_only=False, destructive=True)


@server.tool(name="bulk_delete")
async def bulk_delete(filter: str) -> str:
    # A tool with its own approval step correlates its decision with the
    # middleware's proposed/executed pair via current_action_id():
    from agent_audit_record import Cost, Decision, PrincipalType

    approved = await ask_a_human(filter)
    if not approved:
        emitter.decided(
            action_id=current_action_id(),
            decision=Decision.DENY,
            principal_type=PrincipalType.HUMAN,
            cost=Cost(wasted=True),
        )
        raise PermissionError("denied")
    ...
```

## What this does and doesn't decide

Per [ADR-0004](../../docs/decisions/0004-record-not-enforcer.md): this
middleware **records**, it never gates. A tool with no approval logic of
its own is fine — most are — and produces `proposed` + `executed` with no
`decided` Record at all (spec Pattern A). A tool that implements its own
approval step (elicitation, a custom queue, whatever) records that
decision itself, using `current_action_id()` to correlate it with this
middleware's pair. If that decision forbade execution
(`deny`/`auto_deny`/`cancel`/`timeout`), this middleware's own attempt to
record `executed` afterward is caught and silently skipped —
`agent_audit_record.Emitter` itself raises
`ExecutionAfterTerminalDecisionError` in exactly that case, and this
middleware treats that as confirmation the correlated action is already
correctly terminal (spec Patterns C/D), never as a bug.

## Verifying this works

`verify_middleware.py` exercises the middleware against real
`ServerRequestContext`/`ServerMiddleware` types from the MCP SDK — not a
mock of the protocol — covering both the no-approval path (Pattern A) and
the denial path (Pattern C), and validates every emitted record against
the JSON Schema:

```bash
PYTHONPATH=../../py/src uv run --with mcp --with jsonschema --with opentelemetry-sdk python verify_middleware.py
```

## Known limitations

- **Actor identity defaults to a constant** (`"mcp-client"`). The current
  SDK's `ServerRequestContext` (what middleware receives) has no
  per-connection principal identifier without reaching into private
  attributes. Pass `actor_id_resolver=...` to `AgentAuditMiddleware` if
  your transport exposes one (e.g. via `ctx.headers` on Streamable HTTP).
- **`target.system`/`target.resource`** map generically to the server's
  configured name and the tool name — a server with a richer resource
  model (e.g. n8n-operator's workflow IDs) should pass its own values
  rather than relying on the tool name alone.
- **Declared annotations require restating them** via `declare_annotations()`
  rather than being read automatically from `@mcp.tool(annotations=...)` —
  see `agent_audit_mcp.py`'s docstring.
