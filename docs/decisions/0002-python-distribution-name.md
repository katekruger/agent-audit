# 0002. Python distribution name

- Status: proposed — PLACEHOLDER, pending owner confirmation
- Date: 2026-08-29

## Context

The GitHub repository and the specification are named `agent-audit`. That
name is already taken on PyPI: `agent-audit` v0.19.2 (MIT license) is an
actively-versioned static security analyzer for AI agents — a different
purpose, in the same ecosystem, which makes the collision confusing rather
than merely inconvenient. Shipping a package under that name is not
possible, and shipping under a deceptively similar name would be worse.

The `agent-audit` name is free on npm; only the PyPI/Python distribution
name needs to differ from the repository and specification name.

## Decision

**Provisional pending owner confirmation:** the Python distribution and
import package are named `agent-audit-record` / `agent_audit_record`,
following the build plan's top-ranked candidate — it names the project's
actual role ("the record, not the enforcer") rather than the transport
(`agentaudit-otel`) or a generic rebrand (`openagentaudit`).

**This choice was not confirmed by the project owner before scaffolding.**
Do not treat this ADR as settled. Before the first PyPI publish:

1. Re-check name availability on PyPI for the candidate.
2. Confirm the owner is comfortable with the repo name (`agent-audit`)
   differing from the distribution name (`agent-audit-record`) — this ADR
   assumes that mismatch is less confusing than a forced rename of the
   GitHub repository, but that has not been validated with the owner.
3. Update this ADR's status to `accepted` once confirmed, or supersede it
   with the actual chosen name.

## Consequences

The repository name (`agent-audit`) and the PyPI package name
(`agent-audit-record`) will differ permanently. Documentation, install
instructions (`pip install agent-audit-record`), and the `py/pyproject.toml`
`[project].name` field must all use the distribution name, not the repo
name. The import package name is `agent_audit_record` (underscores, PEP 8).

## Assumption this relies on

That a Python distribution name distinct from the repository name is
acceptable to the project owner, and that `agent-audit-record` in
particular is not itself already taken or reserved on PyPI at publish time.

## Known limitation

Renaming a published PyPI package is effectively impossible — a new name
requires a new project and abandoning the old one. This decision must be
finalized and locked before `v0.1.0` is published, not after.
