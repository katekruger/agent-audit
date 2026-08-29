# Crosswalk: Claude Code hooks

Claude Code's hook vocabulary is the richest event model anyone has
shipped for this problem, and it maps onto the three `agent-audit` phases
almost one-to-one:

| Claude Code hook | `agent_audit.action.phase` |
|---|---|
| `PreToolUse` | `proposed` |
| `PermissionRequest` / `PermissionDenied` | `decided` |
| `PostToolUse` / `PostToolUseFailure` | `executed` |

## Field mapping

`PreToolUse` input already carries most of what `agent_audit.proposed`
needs:

| `PreToolUse` input field | `agent_audit.*` attribute |
|---|---|
| `tool_name` | `agent_audit.target.operation` (loosely — see note below) |
| `tool_input` | `agent_audit.target.arguments`, gated by `agent_audit.level` (spec §6.3, §7) |
| `agent_id` | `agent_audit.actor.id` |
| `agent_type` | (no direct equivalent — informs `agent_audit.actor.type`, which is coarser) |
| `session_id` | (not part of the core schema — candidate for a facet, spec §8) |
| `prompt_id` | (not part of the core schema — candidate for a facet) |
| `cwd` | (not part of the core schema — candidate for a facet, or `agent_audit.target.resource` when the action is filesystem-scoped) |
| `permission_mode` | informs `agent_audit.declared.*`/`agent_audit.effective.*` context, not a direct attribute |
| `tool_use_id` | (not part of the core schema — candidate for a facet; distinct from `agent_audit.action.id`, which correlates the phase Records, not the tool-call ID) |

Note: `tool_name` alone does not cleanly split into `agent_audit.target.system`
+ `.resource` + `.operation` (spec §6.3) — a Claude Code emitter will
generally need tool-specific logic (or a per-tool facet) to populate
`target.system` and `target.resource` meaningfully, rather than a single
generic mapping from `tool_name`.

`PermissionRequest`/`PermissionDenied` output carries the decision:

| Claude Code output field | `agent_audit.*` attribute |
|---|---|
| `hookSpecificOutput.permissionDecision` | `agent_audit.decision` — see the enum crosswalk in [`spec/SPECIFICATION.md` §6.5.1](../SPECIFICATION.md#651-the-decision-enum-an-interoperability-layer-not-a-fourth-dialect): `allow → allow`, `deny → deny`, `deferToUser → defer` |
| `permissionDecisionReason` | `agent_audit.decision.reason` |

`PostToolUse`/`PostToolUseFailure` map to `agent_audit.executed`'s
`agent_audit.outcome` (`success` on `PostToolUse`, `failure` on
`PostToolUseFailure`), per spec §6.6.

## The gap: no built-in persistent audit log

Claude Code's own hooks documentation is explicit that there is **no
built-in persistent audit log** — it directly instructs users who want
one to write their own hook, or POST to an external service. That
instruction is, functionally, a ready-made distribution channel for this
specification: HTTP hooks combined with `allowedEnvVars` give a zero-code
install path — pointing an existing Claude Code hook configuration at an
`agent-audit`-conformant receiver requires no changes to the agent's code
at all. See [`integrations/claude-code-hooks/`](../../integrations/claude-code-hooks/)
for the (not yet implemented) reference integration this crosswalk is
building toward.
