# agent-audit Specification

- Status: **draft skeleton — not yet written**
- Version: unreleased (targeting `v1`)

> This file is a placeholder. The normative specification is scoped as
> milestone M1 in [`BUILD-PLAN.md`](../BUILD-PLAN.md) and is the subject of
> a dedicated follow-up pass, not this scaffolding commit. Do not treat
> anything below as normative yet.

## 1. Overview

`agent-audit` defines a semantic convention over the OpenTelemetry Log Data
Model: three correlated Events — `agent_audit.proposed`,
`agent_audit.decided`, `agent_audit.executed` — binding what an agent
proposed, what a human (or policy) decided, and what executed, including
its cost. See [ADR-0003](../docs/decisions/0003-otel-log-data-model-as-carrier.md)
for why this is a convention and not a protocol.

## 2. Conformance language

This specification will use RFC 2119 keywords (MUST, SHOULD, MAY) once
written. Not yet present in this skeleton.

## 3. The event model

TODO (M1): Event names, phases, and the full attribute table currently
sketched in `BUILD-PLAN.md` §4 — action/actor/target attributes, the
declared-vs-effective annotation split, the decision enum crosswalk, the
cost model, and the `level` dial.

## 4. Schema

The normative machine-readable schema lives at
[`spec/schema/v1/agent-audit.schema.json`](schema/v1/agent-audit.schema.json).
Once `v1` is published, it is immutable — see AGENTS.md.

## 5. Facets

Extension mechanism for namespaced, independently-versioned additions
without forking the core schema. See [`spec/facets/`](facets/).

## 6. Crosswalks

- [`mappings/mcp.md`](mappings/mcp.md)
- [`mappings/claude-code-hooks.md`](mappings/claude-code-hooks.md)
- [`mappings/ietf-draft-sharif.md`](mappings/ietf-draft-sharif.md)
- [`mappings/otel-genai.md`](mappings/otel-genai.md)
