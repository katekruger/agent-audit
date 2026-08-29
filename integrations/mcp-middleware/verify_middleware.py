#!/usr/bin/env python3
"""Exercises AgentAuditMiddleware end-to-end against real ServerRequestContext
and ServerMiddleware types from the MCP SDK -- not a mock of the protocol.

Not a pytest suite (this integration has no package of its own to attach
tests to yet -- see README.md); run directly:

    uv run --with mcp --with agent-audit-record python verify_middleware.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from agent_audit_mcp import AgentAuditMiddleware, current_action_id, declare_annotations
from mcp.server.context import HandlerResult, ServerRequestContext
from mcp_types import CallToolResult, TextContent
from opentelemetry.sdk._logs import LoggerProvider, LogRecordProcessor, ReadWriteLogRecord

from agent_audit_record import Cost, Decision, Emitter, PrincipalType


class Capture(LogRecordProcessor):
    def __init__(self) -> None:
        self.records: list[ReadWriteLogRecord] = []

    def on_emit(self, log_record: ReadWriteLogRecord) -> None:
        self.records.append(log_record)

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True

    def shutdown(self) -> None:
        pass

    def attribute_dicts(self) -> list[dict[str, Any]]:
        return [dict(r.log_record.attributes or {}) for r in self.records]

    def event_names(self) -> list[str | None]:
        return [r.log_record.event_name for r in self.records]


def make_ctx(tool_name: str, arguments: dict[str, Any]) -> ServerRequestContext[Any, Any]:
    return ServerRequestContext(
        session=None,  # type: ignore[arg-type]  -- unused by this middleware
        lifespan_context={},
        protocol_version="2026-07-28",
        method="tools/call",
        params={"name": tool_name, "arguments": arguments},
        request_id="req-1",
    )


async def scenario_pattern_a_no_approval_logic(middleware: AgentAuditMiddleware) -> None:
    """A tool with no approval step: proposed + executed, no decided (Pattern A)."""

    async def call_next(ctx: ServerRequestContext[Any, Any]) -> HandlerResult:
        return CallToolResult(content=[TextContent(type="text", text="ok")])

    ctx = make_ctx("read_status", {"id": "123"})
    await middleware(ctx, call_next)


async def scenario_pattern_c_denial(middleware: AgentAuditMiddleware, emitter: Emitter) -> None:
    """A tool with its own approval step that denies: proposed + decided,
    no executed -- the middleware's own executed() attempt must be
    silently swallowed (ExecutionAfterTerminalDecisionError)."""

    async def call_next(ctx: ServerRequestContext[Any, Any]) -> HandlerResult:
        action_id = current_action_id()
        assert action_id is not None
        emitter.decided(
            action_id=action_id,
            decision=Decision.DENY,
            principal_type=PrincipalType.HUMAN,
            reason="blocked by reviewer",
            cost=Cost(wasted=True),
        )
        return CallToolResult(content=[TextContent(type="text", text="denied")], is_error=True)

    ctx = make_ctx("bulk_delete", {"filter": "*"})
    await middleware(ctx, call_next)


async def scenario_declared_annotations(middleware: AgentAuditMiddleware) -> None:
    declare_annotations("read_status", read_only=True, destructive=False)

    async def call_next(ctx: ServerRequestContext[Any, Any]) -> HandlerResult:
        return CallToolResult(content=[TextContent(type="text", text="ok")])

    ctx = make_ctx("read_status", {"id": "456"})
    await middleware(ctx, call_next)


async def main() -> None:
    capture = Capture()
    provider = LoggerProvider()
    provider.add_log_record_processor(capture)
    emitter = Emitter(logger_provider=provider)
    middleware = AgentAuditMiddleware(emitter, target_system="demo-server")

    await scenario_pattern_a_no_approval_logic(middleware)
    await scenario_pattern_c_denial(middleware, emitter)
    await scenario_declared_annotations(middleware)

    names = capture.event_names()
    print("Event sequence:", names)
    assert names == [
        "agent_audit.proposed",
        "agent_audit.executed",  # Pattern A: no decided
        "agent_audit.proposed",
        "agent_audit.decided",  # Pattern C: no executed follows
        "agent_audit.proposed",
        "agent_audit.executed",  # declared-annotations scenario
    ]

    attrs = capture.attribute_dicts()
    assert attrs[1]["agent_audit.outcome"] == "success"
    assert attrs[3]["agent_audit.decision"] == "deny"
    assert attrs[3]["agent_audit.cost.wasted"] is True
    assert attrs[4]["agent_audit.declared.read_only"] is True
    assert attrs[4]["agent_audit.declared.destructive"] is False

    from jsonschema import validate

    schema_path = (
        Path(__file__).resolve().parents[2] / "spec" / "schema" / "v1" / "agent-audit.schema.json"
    )
    schema = json.loads(schema_path.read_text())
    for record in attrs:
        validate(instance=record, schema=schema)

    print(
        f"OK: all {len(attrs)} records validate against the schema; Patterns A and C both correct"
    )


if __name__ == "__main__":
    asyncio.run(main())
