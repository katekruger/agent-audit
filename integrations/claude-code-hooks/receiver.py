#!/usr/bin/env python3
"""Zero-code Claude Code hooks receiver for agent-audit.

Requires `agent-audit-record` on PYTHONPATH (either `pip install
agent-audit-record`, or run this from a repo checkout with `py/src` on
PYTHONPATH). No dependencies beyond the Python standard library and
agent-audit-record itself -- deliberately small, per spec/mappings/claude-code-hooks.md.

Usage:
    python integrations/claude-code-hooks/receiver.py [--port 4317]

Then merge settings.snippet.json's "hooks" block into .claude/settings.json
and set AGENT_AUDIT_RECEIVER_URL=http://127.0.0.1:4317/hook before starting
Claude Code. See README.md for the full install path.

Hook -> phase mapping (spec/mappings/claude-code-hooks.md):
    PreToolUse                           -> agent_audit.proposed
    PermissionRequest / PermissionDenied -> agent_audit.decided
    PostToolUse / PostToolUseFailure      -> agent_audit.executed

A denied action never gets a PostToolUse -- that is the normal denial
path (spec §5.2 Pattern C), not a missing event this receiver waits for.
Each hook invocation is handled independently and statelessly; there is no
correlation-timeout logic here because there is nothing to time out.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "py" / "src"))

from agent_audit_record import (
    ActorType,
    Cost,
    Decision,
    Emitter,
    Outcome,
    PrincipalType,
)

_LOG = logging.getLogger("agent_audit_record.claude_code_hooks")

_DECISION_MAP = {
    "allow": Decision.ALLOW,
    "deny": Decision.DENY,
    "deferToUser": Decision.DEFER,
}

_emitter = Emitter()


def handle_pre_tool_use(payload: dict[str, Any]) -> None:
    _emitter.proposed(
        action_id=str(payload.get("tool_use_id", "")),
        actor_id=str(payload.get("agent_id", "claude-code")),
        actor_type=ActorType.AGENT,
        target_system="claude-code",
        target_resource=str(payload.get("cwd", "unknown")),
        target_operation=str(payload.get("tool_name", "unknown")),
        arguments=payload.get("tool_input"),
    )


def handle_permission_event(payload: dict[str, Any]) -> None:
    hook_output = payload.get("hookSpecificOutput") or {}
    raw_decision = str(hook_output.get("permissionDecision", "deny"))
    decision = _DECISION_MAP.get(raw_decision, Decision.DENY)
    reason = hook_output.get("permissionDecisionReason")

    cost = Cost(wasted=True) if decision.forbids_execution else None
    _emitter.decided(
        action_id=str(payload.get("tool_use_id", "")),
        decision=decision,
        principal_type=PrincipalType.HUMAN,
        reason=str(reason) if reason is not None else None,
        cost=cost,
    )


def handle_post_tool_use(payload: dict[str, Any], *, failed: bool) -> None:
    _emitter.executed(
        action_id=str(payload.get("tool_use_id", "")),
        outcome=Outcome.FAILURE if failed else Outcome.SUCCESS,
    )


_HANDLERS = {
    "PreToolUse": handle_pre_tool_use,
    "PermissionRequest": handle_permission_event,
    "PermissionDenied": handle_permission_event,
    "PostToolUse": lambda p: handle_post_tool_use(p, failed=False),
    "PostToolUseFailure": lambda p: handle_post_tool_use(p, failed=True),
}


class HookRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        _LOG.debug(fmt, *args)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"

        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError:
            _LOG.warning("agent-audit: dropping malformed hook payload (invalid JSON)")
            self._respond(400)
            return

        event_name = str(payload.get("hook_event_name", ""))
        handler = _HANDLERS.get(event_name)
        if handler is None:
            _LOG.debug("agent-audit: ignoring unmapped hook event %r", event_name)
            self._respond(204)
            return

        # Never let a malformed or unexpected payload crash the receiver --
        # this receiver's whole job is to not be the thing that breaks Claude
        # Code's tool-use flow.
        try:
            handler(payload)
        except Exception:
            _LOG.warning(
                "agent-audit: failed to process %r hook payload", event_name, exc_info=True
            )
        self._respond(204)

    def _respond(self, status: int) -> None:
        self.send_response(status)
        self.end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4317)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    server = ThreadingHTTPServer((args.host, args.port), HookRequestHandler)
    _LOG.info(
        "agent-audit Claude Code hooks receiver listening on http://%s:%d/hook",
        args.host,
        args.port,
    )
    with contextlib.suppress(KeyboardInterrupt):
        server.serve_forever()


if __name__ == "__main__":
    main()
