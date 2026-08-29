# agent-audit-record

Reference Python emitter for the [`agent-audit`](https://github.com/katekruger/agent-audit)
OpenTelemetry semantic convention — a portable record binding what an agent
proposed, what a human decided, what executed, and what it cost.

This package is the reference implementation, not the specification. The
normative definition lives in [`spec/SPECIFICATION.md`](../spec/SPECIFICATION.md)
at the repository root.

> **Status:** v1 reference emitter implemented (milestone M3). Claude Code
> hooks and MCP middleware integrations (M4, M7) are not yet built — see
> [`BUILD-PLAN.md`](../BUILD-PLAN.md).

## Install

```bash
pip install agent-audit-record
```

## Usage

```python
from agent_audit_record import ActorType, Cost, Decision, Emitter, Outcome, PrincipalType

emitter = Emitter()  # no-op until a host configures an OTel LoggerProvider

emitter.proposed(
    action_id="7c1e9a3b-4d2f-4a6e-9b1c-2d3e4f5a6b7c",
    actor_id="agent-crm-assistant",
    actor_type=ActorType.AGENT,
    target_system="salesforce",
    target_resource="Opportunity/006xx000004TmiQAAS",
    target_operation="bulk_delete",
)
emitter.decided(
    action_id="7c1e9a3b-4d2f-4a6e-9b1c-2d3e4f5a6b7c",
    decision=Decision.DENY,
    principal_type=PrincipalType.HUMAN,
    cost=Cost(amount=0.0037, currency="usd", wasted=True),
)
# No executed() call follows: spec §5.2 Pattern C forbids one after a denial.
```

See [`spec/SPECIFICATION.md`](../spec/SPECIFICATION.md) for the full event
model and [`../examples/`](../examples/) for worked examples of every
completion pattern.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run pyright
```
