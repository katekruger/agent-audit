# Agent instructions for this repository

## What this project is

This project ships a **specification**: a portable record binding what an
agent proposed, what a human decided, what executed, and what it cost. It is
an OpenTelemetry semantic convention plus a thin reference emitter — not a
library, not an enforcer, not a protocol.

## House rules

- **The spec is the deliverable.** Code changes that are not reflected in
  [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md) are incomplete. If you
  change an attribute name, a required field, or an enum value in the
  reference emitter, update the specification and the JSON Schema in the
  same change.
- **Reuse before you define.** `gen_ai.*` and `llm.cost.*` already exist as
  semantic conventions. Restating an attribute someone else owns is a bug,
  not a feature. Check [`spec/mappings/otel-genai.md`](spec/mappings/otel-genai.md)
  before adding a new attribute.
- **We never enforce.** If a change makes this library able to *block* an
  action — a policy engine, a gate, a runtime decision — it is out of scope.
  This project records; something else decides. See
  [ADR-0004](docs/decisions/0004-record-not-enforcer.md).
- **The emitter must never crash its host.** No OTLP endpoint configured,
  network down, malformed config — degrade silently, log once, continue.
  A host application's crash is never an acceptable side effect of adding
  observability.
- **Every schema version gets an immutable URL. Never edit a published
  schema.** Once `spec/schema/v1/` is tagged and released, changes go into
  `spec/schema/v2/`. See [ADR-0003](docs/decisions/0003-otel-log-data-model-as-carrier.md).

## Working in this repo

- Python code lives under `py/`, not at the repo root — the root is the
  specification.
- Use `uv` for all Python dependency and environment management. Commit
  `uv.lock`.
- Run `ruff check`, `ruff format --check`, `pyright`, and `pytest` before
  proposing a change to `py/`.
- Every example under `examples/` must validate against the current JSON
  Schema — this is enforced in CI, not just convention.
- Record architectural decisions that are expensive to reverse or
  non-obvious later as an ADR in `docs/decisions/`, using
  [the template](docs/decisions/0000-template.md).
