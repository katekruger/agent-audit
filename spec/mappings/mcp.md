# Crosswalk: Model Context Protocol (MCP)

- Status: placeholder — see `BUILD-PLAN.md` milestone M2.

Purpose: document how `agent-audit` relates to MCP elicitation, Tasks, and
tool annotations, without duplicating any of them.

TODO:
- `ElicitResult.action` (`accept` / `decline` / `cancel`) → maps to
  `agent_audit.decision` (`allow` / `deny` / `cancel`).
- MCP Tasks (`working` → `input_required` → `completed|failed|cancelled`)
  is the transport for the pause; `agent-audit` is the durable record of
  the decision reached during that pause. Tasks is TTL-bounded and
  disposable — the audit record must outlive it.
- `ToolAnnotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`,
  `openWorldHint`) → recorded as `agent_audit.declared.*`, explicitly as
  **untrusted input**, never as the basis for a decision. See
  `agent_audit.effective.*` for the policy's actual conclusion.
- Track `mcp.method.name`, `mcp.protocol.version`, `mcp.resource.uri`,
  `mcp.session.id` from OTel's existing `mcp.*` semantic convention, and
  where it lags the current MCP spec revision.
