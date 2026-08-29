# Crosswalk: OTel GenAI semantic conventions

- Status: placeholder — see `BUILD-PLAN.md` milestone M2.

Purpose: document exactly which attributes `agent-audit` reuses from
`gen_ai.*` and OpenInference's `llm.cost.*` rather than restating, per
AGENTS.md's "reuse before you define" rule.

TODO:
- `gen_ai.agent.id` → reused for `agent_audit.actor.id` where present.
- `gen_ai.usage.input_tokens` / `.output_tokens` → reused for the inference
  cost component.
- `llm.cost.total` / `.prompt` / `.completion` (OpenInference, Apache-2.0)
  → reused; `agent_audit.cost.currency` fills OpenInference's missing
  currency field.
- Full table of what `gen_ai.*` attributes remain `Development` status vs.
  the Stable OTel Log Data Model this project builds on.
