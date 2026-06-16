"""Logging setup for the URL discovery pipeline."""

from __future__ import annotations

import logging
import sys

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


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
