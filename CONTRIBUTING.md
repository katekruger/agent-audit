# Contributing

Thanks for considering a contribution to `agent-audit`. Read
[`AGENTS.md`](AGENTS.md) first — it has the house rules that apply to every
change, human or AI-assisted.

## Setup

```bash
git clone https://github.com/katekruger/agent-audit.git
cd agent-audit/py
uv sync
uv run pre-commit install --config ../.pre-commit-config.yaml
```

Run the checks locally before opening a PR:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

If you're changing anything under `spec/`, validate examples against the
schema — CI does this automatically, but it's faster to catch locally:

```bash
uv run python -m jsonschema -i ../examples/denied-proposal/*.json ../spec/schema/v1/agent-audit.schema.json
```

## Use of AI

AI-assisted contributions are welcome. If a tool generated or substantially
drafted your change, say so in the PR description — not as a disclaimer,
but because reviewers weigh a contribution differently depending on whether
a human independently verified the reasoning behind it. A PR that changes
`spec/SPECIFICATION.md` needs a human who understands *why* the change is
correct, not just that a tool produced text that looks plausible.

## What gets rejected

- Anything that gives this library the ability to block, gate, or evaluate
  policy on an action. See [ADR-0004](docs/decisions/0004-record-not-enforcer.md) —
  this project records; it does not enforce, no matter how small or
  reasonable the enforcement hook looks in isolation.
- New attributes that restate something `gen_ai.*` or `llm.cost.*` already
  owns. Check [`spec/mappings/otel-genai.md`](spec/mappings/otel-genai.md)
  first.
- Edits to a schema version that has already been published under an
  immutable URL. New fields go in a new schema version.
- A code change to `py/` that isn't reflected in `spec/SPECIFICATION.md`,
  or vice versa. The spec and the reference implementation must not drift.
- Cryptographic signing or hash-chaining features in v1, absent a
  concrete, named use case that needs it. See the build plan's open
  questions for the reasoning.
