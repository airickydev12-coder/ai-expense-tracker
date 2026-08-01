"""
Centralized logging configuration for the Financial Core application.

Call configure_logging() once at application startup (CLI entry point
or API startup). Every other module should call get_logger(__name__)
to obtain a logger rather than configuring logging itself.
"""

import logging
import sys

from src.core.config import LOG_DIR

LOG_FILE = LOG_DIR / "app.log"

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging(
    *,
    file_level: int = logging.DEBUG,
    console_level: int = logging.WARNING,
) -> None:
    """
    Configure application-wide logging.

    File logging captures everything at file_level and above for later
    review. Console logging defaults to warnings and above so normal
    CLI output isn't cluttered; callers such as the API can raise
    console_level to make request-handling activity visible.

    Safe to call more than once; only the first call takes effect.
    """
    global _configured

    if _configured:
        return

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    formatter = logging.Formatter(
        _LOG_FORMAT,
        datefmt=_DATE_FORMAT,
    )

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger("src")
    root_logger.setLevel(min(file_level, console_level))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.propagate = False

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name."""
    return logging.getLogger(name)
