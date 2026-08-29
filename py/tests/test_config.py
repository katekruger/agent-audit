import logging

import pytest

from agent_audit_record import Level
from agent_audit_record.config import DEFAULT_SCHEMA_URL, Config


def test_defaults_are_the_safest_no_op() -> None:
    config = Config()
    assert config.default_level is Level.METADATA
    assert config.schema_url == DEFAULT_SCHEMA_URL


def test_from_env_reads_schema_url_and_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_AUDIT_SCHEMA_URL", "https://example.com/schema.json")
    monkeypatch.setenv("AGENT_AUDIT_LEVEL", "request_response")
    config = Config.from_env()
    assert config.schema_url == "https://example.com/schema.json"
    assert config.default_level is Level.REQUEST_RESPONSE


def test_from_env_falls_back_on_malformed_level(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("AGENT_AUDIT_LEVEL", "not-a-real-level")
    with caplog.at_level(logging.WARNING, logger="agent_audit_record"):
        config = Config.from_env()
    assert config.default_level is Level.METADATA
    assert any("invalid" in r.message for r in caplog.records)


def test_from_env_defaults_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENT_AUDIT_LEVEL", raising=False)
    monkeypatch.delenv("AGENT_AUDIT_SCHEMA_URL", raising=False)
    config = Config.from_env()
    assert config.default_level is Level.METADATA
    assert config.schema_url == DEFAULT_SCHEMA_URL
