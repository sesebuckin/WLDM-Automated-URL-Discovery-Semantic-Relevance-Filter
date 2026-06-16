"""Logging setup and runtime diagnostics for the URL discovery pipeline."""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import Mapping
from typing import Any

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
REDACTION_TEXT = "[已隐藏]"

_SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password|passwd|authorization)=([^\s&;,]+)"
)
_AUTHORIZATION_ASSIGNMENT_PATTERN = re.compile(r"(?i)\bauthorization\s*=\s*bearer\s+[^\s&;,]+")
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+")


def configure_logging(level: int = logging.INFO) -> None:
    """Configure process-wide logging for CLI execution."""
    logging.basicConfig(
        level=level,
        format=DEFAULT_LOG_FORMAT,
        stream=sys.stderr,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger for application modules."""
    return logging.getLogger(name)


def redact_sensitive_text(text: str) -> str:
    """Redact sensitive values before they reach logs or diagnostics."""
    redacted = _AUTHORIZATION_ASSIGNMENT_PATTERN.sub(f"Authorization={REDACTION_TEXT}", text)
    redacted = _SENSITIVE_ASSIGNMENT_PATTERN.sub(
        lambda match: f"{match.group(1)}={REDACTION_TEXT}",
        redacted,
    )
    return _BEARER_PATTERN.sub(f"Bearer {REDACTION_TEXT}", redacted)


def format_runtime_diagnostic(message: str, context: Mapping[str, Any] | None = None) -> str:
    """Format a Simplified Chinese runtime diagnostic with redacted context values."""
    clean_message = redact_sensitive_text(message.strip())
    if not context:
        return clean_message

    parts = []
    for key, value in context.items():
        clean_value = redact_sensitive_text(str(value))
        parts.append(f"{key}={clean_value}")
    return f"{clean_message}；{'；'.join(parts)}"


def log_runtime_diagnostic(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Mapping[str, Any] | None = None,
) -> str:
    """Log a redacted Simplified Chinese diagnostic and return the emitted message."""
    diagnostic = format_runtime_diagnostic(message, context)
    logger.log(level, diagnostic)
    return diagnostic
