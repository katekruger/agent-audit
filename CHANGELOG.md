# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
for the JSON Schema and the Python package independently.

## [Unreleased]

### Added

- `docs/plans/pypi-trusted-publishing-setup.md`: precise step-by-step
  for configuring PyPI/TestPyPI Trusted Publishing, since that
  configuration lives in external accounts this repo can't touch
  directly.
- M9 prep (not opened): a draft PR branch at
  `katekruger/semantic-conventions-genai@mcp-2026-07-28-attribute-coverage`
  catching up the OTel `mcp.*` namespace to the MCP 2026-07-28 protocol
  revision — five methods deprecated for having been fully removed
  from the wire schema (`initialize`, `notifications/initialized`,
  `ping`, `resources/subscribe`, `resources/unsubscribe`), four more
  deprecated per SEP-2577, three new methods added, and
  `mcp.session.id`'s description corrected (it linked to a
  `#session-management` anchor that no longer exists, since
  protocol-level sessions were removed in this revision). Verified
  against the real upstream `schema.ts` and transports spec, not just
  BUILD-PLAN.md's claims; validated with the upstream repo's own
  `make check-policies` and `make generate-all`.
- `docs/decisions/0005-hash-chaining-deferred.md`,
  `docs/decisions/0006-ietf-outreach-deferred-before-public.md`: ADRs
  for the two deferred decisions that were previously only implicit in
  `BUILD-PLAN.md`'s open questions and the going-public checklist.
- `docs/why-not-a-protocol.md`, `docs/vs-agent-governance-toolkit.md`:
  expanded from placeholders into full posts. The AGT comparison
  includes a real, signature-checked code sample against the actual
  `Emitter` API rather than a hypothetical one.

## [0.1.0] - 2026-08-30

M6 of [`BUILD-PLAN.md`](BUILD-PLAN.md): the specification, the reference
emitter, the flagship human-in-the-loop example, and the GIF showing it.
The Python package remains `0.1.0.dev0`-versioned separately until it is
actually published — see
[docs/plans/going-public-checklist.md](docs/plans/going-public-checklist.md)
for what's still required before that happens.

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
- `integrations/claude-code-hooks/`: zero-code hooks receiver mapping
  PreToolUse/PermissionRequest/PermissionDenied/PostToolUse to the
  three-phase model.
- `examples/denied-proposal/`: the flagship example is now runnable
  (`run.py`, `run.sh`), verified end-to-end against a real local OTel
  Collector.
- `docs/cost-of-denied-proposals.md`, `docs/backend-compatibility.md`:
  the launch metric writeup, and honest verification results against
  real local Arize Phoenix and Langfuse instances (neither currently
  implements OTLP log ingestion — traces/metrics only).
- `integrations/mcp-middleware/`: `AgentAuditMiddleware` for the
  official MCP Python SDK (v2 line) — wraps every `tools/call` in
  `proposed`/`executed`, with `current_action_id()` letting a tool's own
  approval logic correlate a `decided` call into the same pair.
- Fixed a spec gap surfaced by dogfooding: `auto_deny` now forbids
  execution and requires `cost.wasted=true`, exactly like `deny`.
- `.github/workflows/zizmor.yml`: GitHub Actions workflow security scanning
  via zizmor (not CodeQL, per house standard), gated on `zizmor.yml`
  config; SARIF/Advanced-Security upload is deferred until the repo goes
  public (private repos need a GHAS license), so findings currently fail
  the job via plain annotations instead.
- `.github/workflows/release.yml`: tag-triggered release pipeline — full
  CI must pass, then build with `uv build`, publish to TestPyPI via OIDC
  Trusted Publishing as a dry run gate, then (real tag pushes only)
  publish to PyPI with PEP 740 Sigstore attestations
  (`pypa/gh-action-pypi-publish`) plus GitHub build provenance
  attestations. The `pypi` and `testpypi` GitHub Environments and their
  Trusted Publisher configuration on PyPI/TestPyPI still need to be set
  up out-of-band by the project owner — see
  [docs/plans/going-public-checklist.md](docs/plans/going-public-checklist.md).
- `docs/media/denied-proposal.gif`: the flagship GIF (M6) — a real,
  unedited terminal recording of `examples/denied-proposal/run.py`,
  generated via the VHS tape at `docs/media/denied-proposal.tape` (not a
  mockup or narrated screen capture), embedded at the top of
  [`README.md`](README.md).
