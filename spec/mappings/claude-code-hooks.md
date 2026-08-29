# Crosswalk: Claude Code hooks

- Status: placeholder — see `BUILD-PLAN.md` milestone M2.

| Hook | `agent-audit` phase |
|---|---|
| `PreToolUse` | `proposed` |
| `PermissionRequest` / `PermissionDenied` | `decided` |
| `PostToolUse` / `PostToolUseFailure` | `executed` |

TODO: full field mapping from `PreToolUse` input (`session_id`,
`prompt_id`, `cwd`, `permission_mode`, `agent_id`, `agent_type`,
`tool_name`, `tool_input`, `tool_use_id`) and
`hookSpecificOutput.permissionDecision` (`allow` / `deny` / `deferToUser`)
to the corresponding `agent_audit.*` attributes. See
[`integrations/claude-code-hooks/`](../../integrations/claude-code-hooks/)
for the reference implementation.
