# Claude Code hooks integration

A drop-in hook config plus a small HTTP receiver. Zero code changes to
your Claude Code setup: you add hook entries to `.claude/settings.json`
and set one environment variable.

See [`spec/mappings/claude-code-hooks.md`](../../spec/mappings/claude-code-hooks.md)
for the full field-by-field mapping this implements.

## Hook → phase mapping

| Claude Code hook | `agent_audit.action.phase` |
|---|---|
| `PreToolUse` | `proposed` |
| `PermissionRequest` / `PermissionDenied` | `decided` |
| `PostToolUse` / `PostToolUseFailure` | `executed` |

**A denied action never gets a `PostToolUse` call — this is the normal
denial path (spec §5.2 Pattern C), not an error the receiver waits for or
times out on.** Each hook fires as its own independent HTTP request; the
receiver has no state machine expecting a follow-up event that a denial
will never produce. It emits exactly what it's told, when it's told.

## Install (no code changes)

1. Start the receiver (requires `pip install agent-audit-record`, or run
   from a checkout of this repo as below):

   ```bash
   python integrations/claude-code-hooks/receiver.py --port 4317
   ```

2. Merge the `hooks` block from [`settings.snippet.json`](settings.snippet.json)
   into your `.claude/settings.json`.

3. Point Claude Code at the receiver before starting it:

   ```bash
   export AGENT_AUDIT_RECEIVER_URL=http://127.0.0.1:4317/hook
   ```

That's the whole install. Each hook pipes its JSON payload to `curl` on
stdin, which POSTs it to the receiver; nothing runs inside Claude Code's
own process, and a receiver that isn't running (or is slow) never blocks
a tool call — the hook command has a 2-second timeout and always exits 0
(`|| true`), per the same "never crash the host" principle the emitter
itself follows (`AGENTS.md`).

To point the emitter at a real OTLP backend instead of the console/no-op
default, configure the standard OTel environment variables (e.g.
`OTEL_EXPORTER_OTLP_ENDPOINT`) before starting the receiver — the receiver
uses `agent_audit_record.Emitter()` with no arguments, which follows
whatever OTel `LoggerProvider` the process has configured, exactly like
any other OTel instrumentation.

## Known simplifications

- **Correlation.** `agent_audit.action.id` is populated from Claude Code's
  own `tool_use_id`. This is pragmatic for a zero-code receiver, though
  `tool_use_id` and `agent_audit.action.id` are conceptually distinct in
  the spec (§5.3) — a fuller integration might mint its own ID and record
  `tool_use_id` as a facet instead.
- **No cost data.** Claude Code's hook payloads don't carry token or
  inference cost. `agent_audit.cost.wasted` is still set correctly on a
  `deny`/`defer` decision (required by spec §6.7 and enforced by the
  emitter itself), but `agent_audit.cost.amount` is omitted rather than
  guessed. A fuller integration could correlate hook events against a
  session transcript to recover real cost — out of scope for this
  reference receiver.
- **`target.system`/`target.resource`** are set to constants
  (`"claude-code"` and the working directory) rather than something
  tool-specific, since a general mapping from arbitrary `tool_name` values
  to a system/resource pair isn't possible without per-tool logic. See
  [`spec/mappings/claude-code-hooks.md`](../../spec/mappings/claude-code-hooks.md).
