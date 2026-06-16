"""Unit tests for Simplified Chinese diagnostics and redaction."""

import logging

import pytest

from wldm_url_filter.logging_config import (
    REDACTION_TEXT,
    format_runtime_diagnostic,
    log_runtime_diagnostic,
    redact_sensitive_text,
)


def test_redact_sensitive_text_removes_tokens_and_passwords() -> None:
    text = redact_sensitive_text(
        "token=abc123 password=swordfish Authorization=Bearer secret-token"
    )

    assert "abc123" not in text
    assert "swordfish" not in text
    assert "secret-token" not in text
    assert text.count(REDACTION_TEXT) == 3


def test_format_runtime_diagnostic_keeps_chinese_message_and_redacts_context() -> None:
    diagnostic = format_runtime_diagnostic(
        "访问目标网址失败",
        {"url": "https://example.com?api_key=secret", "reason": "timeout"},
    )

    assert diagnostic.startswith("访问目标网址失败")
    assert "secret" not in diagnostic
    assert REDACTION_TEXT in diagnostic


def test_log_runtime_diagnostic_emits_redacted_message(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("wldm_url_filter.test")

    with caplog.at_level(logging.WARNING):
        emitted = log_runtime_diagnostic(
            logger,
            logging.WARNING,
            "读取输入失败",
            {"token": "token=abc"},
        )

    assert emitted in caplog.text
    assert "abc" not in caplog.text
