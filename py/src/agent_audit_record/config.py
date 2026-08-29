"""Env-driven configuration, with sane no-op defaults.

Per AGENTS.md, the emitter must never crash its host: a malformed
environment variable here falls back to the safest default (logged once,
never raised) rather than propagating.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from agent_audit_record.phases import Level

_LOG = logging.getLogger("agent_audit_record")

_SCHEMA_URL_ENV = "AGENT_AUDIT_SCHEMA_URL"
_LEVEL_ENV = "AGENT_AUDIT_LEVEL"

DEFAULT_SCHEMA_URL = (
    "https://raw.githubusercontent.com/katekruger/agent-audit/main/"
    "spec/schema/v1/agent-audit.schema.json"
)


@dataclass(frozen=True, slots=True)
class Config:
    """Emitter configuration.

    `default_level` defaults to the most conservative value (`METADATA`)
    so that installing this library never leaks request/response bodies
    by default — a caller must opt in to a more verbose level, per spec §7.
    """

    schema_url: str = DEFAULT_SCHEMA_URL
    default_level: Level = Level.METADATA

    @classmethod
    def from_env(cls) -> Config:
        schema_url = os.environ.get(_SCHEMA_URL_ENV, DEFAULT_SCHEMA_URL)
        return cls(schema_url=schema_url, default_level=_parse_level(os.environ.get(_LEVEL_ENV)))


def _parse_level(raw: str | None) -> Level:
    if raw is None:
        return Level.METADATA
    try:
        return Level(raw)
    except ValueError:
        _LOG.warning("agent-audit: invalid %s=%r; falling back to level=metadata", _LEVEL_ENV, raw)
        return Level.METADATA
