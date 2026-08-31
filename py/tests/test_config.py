import logging
import random
import string

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


def test_from_env_never_crashes_on_arbitrary_garbage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Generative counterpart to test_from_env_falls_back_on_malformed_level.

    That test only proves one hand-picked bad string is handled. AGENTS.md's
    "the emitter must never crash its host" is a claim about *any* malformed
    env value, not the one example the author happened to think of -- so this
    throws a wide net of adversarial inputs (empty, whitespace, unicode,
    near-miss values that are substrings/superstrings/case-variants of real
    enum members, null bytes, very long strings) and asserts the fallback
    path is always taken rather than raising.
    """
    valid_values = {level.value for level in Level}
    near_misses: set[str] = set()
    for value in valid_values:
        near_misses.add(value.upper())
        near_misses.add(value[:-1])
        near_misses.add(value + "x")
        near_misses.add(f" {value} ")

    rng = random.Random(0)
    random_strings = [
        "".join(rng.choices(string.printable, k=rng.randint(0, 200))) for _ in range(200)
    ]

    # Note: os.environ cannot hold a null byte (ValueError at the OS layer),
    # so unlike the other candidates, embedded-null strings are not a
    # reachable input here and are intentionally excluded.
    candidates = [
        "",
        *sorted(near_misses),
        "null",
        "None",
        "🙂",
        "a" * 10_000,
        *random_strings,
    ]

    for raw in candidates:
        if raw in valid_values:
            continue
        monkeypatch.setenv("AGENT_AUDIT_LEVEL", raw)
        config = Config.from_env()  # must not raise for any input
        assert config.default_level is Level.METADATA, f"unexpected fallback for {raw!r}"
