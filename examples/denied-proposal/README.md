# The flagship example: a denied proposal

An agent proposes a CRM bulk delete. A human denies it. The record shows
`proposed` + `decided`, **no `executed`**, and `cost.wasted = true` with
the inference spend that produced the rejected proposal.

Nothing else in the ecosystem can express this. Every observability
platform models cost as tokens × model price for work that ran; none can
say "we spent $X on proposals humans rejected." See
[`docs/cost-of-denied-proposals.md`](../../docs/cost-of-denied-proposals.md).

Per [spec §5.2, Pattern C](../../spec/SPECIFICATION.md#52-completion-patterns--not-every-action-produces-all-three),
calling `executed()` after this denial raises
`ExecutionAfterTerminalDecisionError` — the script doesn't call it, on
purpose, and the emitter would refuse if it tried.

## Run it — one command

```bash
./run.sh
```

This starts a local OTel Collector (`docker compose up`), runs the
example against it, and prints what the collector actually received —
proving the record lands over real OTLP, not just in-process.

## Run it with no backend at all

```bash
uv run --project ../../py --group examples python run.py
```

The script always prints a legible narrative to stdout regardless of
whether an OTLP endpoint is configured — this example is meant to be
readable standing alone, not only through a collector's debug logs:

```
--- agent_audit.proposed ---
  agent proposes: bulk_delete on salesforce:Opportunity/006xx000004TmiQAAS
  actor: agent-crm-assistant on behalf of kate@company.com

--- agent_audit.decided ---
  decision: deny by kate@company.com
  reason: Bulk deletion of closed-won opportunities is outside the agent's authorized policy scope
  >>> cost.wasted = true -- 0.0037 usd of inference spent on a proposal that will never execute <<<

1770 tokens (1450 in / 320 out) were spent proposing an action that a human
then rejected. No executed record exists for this action_id, and none ever
will.
```

## Files

| File | Purpose |
|---|---|
| `run.py` | The example itself — proposes, then denies, using `agent_audit_record.Emitter`. |
| `run.sh` | One-command version: brings up the collector and runs `run.py` against it. |
| `docker-compose.yml`, `collector-config.yaml` | A local OTel Collector with a `debug` exporter, so you can see exactly what an OTLP receiver gets — no backend account or setup required. |
| `events.json` | The static, hand-written version of the same two records, used by CI to validate against the JSON Schema (see [Prompt 1](../../spec/SPECIFICATION.md)). `run.py` produces the same shape dynamically, through the real emitter. |

Stop the collector when you're done:

```bash
docker compose down
```
