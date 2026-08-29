# agent-audit-record

Reference Python emitter for the [`agent-audit`](https://github.com/katekruger/agent-audit)
OpenTelemetry semantic convention — a portable record binding what an agent
proposed, what a human decided, what executed, and what it cost.

This package is the reference implementation, not the specification. The
normative definition lives in [`spec/SPECIFICATION.md`](../spec/SPECIFICATION.md)
at the repository root.

> **Status:** scaffold. The emitter is not yet implemented — see
> [`BUILD-PLAN.md`](../BUILD-PLAN.md) milestone M3.

## Install

```bash
pip install agent-audit-record
```

> Distribution name is provisional — see
> [ADR-0002](../docs/decisions/0002-python-distribution-name.md).

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run pyright
```
