from __future__ import annotations

import logging
import logging.config
import sys

from pythonjsonlogger.json import JsonFormatter

from app.core.config import settings


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%H:%M:%S")
        return (
            f"{timestamp} "
            f"[{record.levelname:<8}] "
            f"{record.name}: "
            f"{record.getMessage()}"
        )


def configure_logging() -> None:
    """
    Configure application logging.
    """

    root = logging.getLogger()

    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)

    if settings.environment.lower() == "development":
        handler.setFormatter(ConsoleFormatter())
    else:
        handler.setFormatter(
            JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s"
            )
        )

    root.setLevel(settings.log_level.upper())
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").handlers = []
