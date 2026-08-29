# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
for the JSON Schema and the Python package independently.

## [Unreleased]

### Added

- Repository scaffold: spec/, py/ reference implementation skeleton,
  integrations/, examples/, docs/ with initial ADRs.
- `spec/SPECIFICATION.md` v1 (draft): the three-phase event model, the four
  completion patterns (including the proposed+decided-with-no-executed
  asymmetry that makes denied-proposal cost computable), the full
  attribute table, the declared-vs-effective trust boundary for MCP tool
  annotations, the decision enum crosswalk, the `level` dial, and the cost
  model.
- `spec/schema/v1/agent-audit.schema.json`: normative JSON Schema with
  per-phase conditional requirements.
- Worked examples for all four completion patterns: auto-allowed read,
  human-approved write, denied proposal, decision timeout — each validated
  against the schema in CI.
- Spec additions needed by the reference emitter's edge cases: Pattern E
  (superseded before a decision), batch fan-out (§5.4, one decision many
  executions), retry linkage via `agent_audit.action.parent_id` (§5.5),
  and the decision-latency non-negativity rule (§6.5).
- `py/src/agent_audit_record/`: the reference Python emitter
  (`emitter.py`, `phases.py`, `cost.py`, `config.py`). Emits OTel
  LogRecord Events; never crashes its host on exporter/config failure;
  enforces the `level=metadata` argument-redaction boundary; refuses to
  emit an `executed` record after a denial/cancel/timeout decision.
  100% test coverage, every emitted record validated against the JSON
  Schema in CI.
