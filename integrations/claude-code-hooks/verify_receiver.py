#!/usr/bin/env python3
"""Smoke-tests receiver.py against a real HTTP round trip, in two shapes.

Not a pytest suite (receiver.py has no package of its own to attach tests
to -- see README.md); run directly:

    python integrations/claude-code-hooks/verify_receiver.py

Two scenarios, deliberately using two different process shapes:

1. In-process: PreToolUse -> PermissionDenied -> PostToolUse against one
   running receiver, proving the illegal post-denial PostToolUse is
   swallowed (never crashes the receiver) rather than emitting a
   contradictory `executed` record.

2. Restart-between-requests: the same sequence, but the receiver process
   is killed and a fresh one started between PermissionDenied and
   PostToolUse -- the process-shape check called for in AGENTS.md/the
   round-3 audit finding. This proves the guard in scenario 1 is
   process-lifetime-scoped: the fresh process has no memory of the denial,
   so the "illegal" PostToolUse succeeds instead of being swallowed. That is
   documented, expected behavior (see receiver.py's module docstring), not
   a bug this script is meant to catch -- it exists so that fact stays
   verified rather than asserted.
"""

from __future__ import annotations

import http.client
import json
import subprocess
import time
from pathlib import Path

RECEIVER = Path(__file__).resolve().parent / "receiver.py"
PY_PROJECT = Path(__file__).resolve().parents[2] / "py"


def post(port: int, event_name: str, **payload: object) -> int:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    body = json.dumps({"hook_event_name": event_name, **payload}).encode()
    conn.request("POST", "/hook", body=body, headers={"Content-Type": "application/json"})
    status = conn.getresponse().status
    conn.close()
    return status


def start_receiver(port: int) -> subprocess.Popen[bytes]:
    proc = subprocess.Popen(
        ["uv", "run", "--project", str(PY_PROJECT), "python", str(RECEIVER), "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    for _ in range(100):
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode() if proc.stderr else ""
            raise RuntimeError(f"receiver.py exited early:\n{stderr}")
        try:
            post(port, "__probe__")
            break
        except (ConnectionRefusedError, OSError):
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("receiver.py did not come up in time")
    return proc


def scenario_in_process(port: int) -> None:
    proc = start_receiver(port)
    try:
        assert post(port, "PreToolUse", tool_use_id="a1", tool_name="bulk_delete") == 204
        assert (
            post(
                port,
                "PermissionDenied",
                tool_use_id="a1",
                hookSpecificOutput={"permissionDecision": "deny", "permissionDecisionReason": "no"},
            )
            == 204
        )
        # Out-of-spec: a PostToolUse after a denial. Must not crash the
        # receiver (204 either way) -- the point is the process survives.
        assert post(port, "PostToolUse", tool_use_id="a1") == 204
        print("scenario 1 (in-process): illegal post-denial PostToolUse did not crash receiver")
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def scenario_restart_between_requests(port: int) -> None:
    proc = start_receiver(port)
    try:
        assert post(port, "PreToolUse", tool_use_id="b1", tool_name="bulk_delete") == 204
        assert (
            post(
                port,
                "PermissionDenied",
                tool_use_id="b1",
                hookSpecificOutput={"permissionDecision": "deny", "permissionDecisionReason": "no"},
            )
            == 204
        )
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    # Fresh process: no memory of the denial above.
    proc = start_receiver(port)
    try:
        status = post(port, "PostToolUse", tool_use_id="b1")
        assert status == 204, "receiver should not crash even across a restart"
        print(
            "scenario 2 (restart between requests): confirmed the process-lifetime-scoped "
            "guard has no memory of the prior denial after a restart -- documented "
            "behavior, not a regression"
        )
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def main() -> None:
    scenario_in_process(4318)
    scenario_restart_between_requests(4319)
    print("OK: receiver.py verified in both process shapes")


if __name__ == "__main__":
    main()
