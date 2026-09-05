"""
Structured Logging Module for FraudLens
Provides standardized console & file log formatting with contextual metadata.
"""

import logging
import sys
from datetime import datetime, timezone
from app.core.config import settings


class FraudLensFormatter(logging.Formatter):
    """Custom formatter with ISO timestamps and clean module tagging."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        level = record.levelname.ljust(8)
        message = record.getMessage()
        location = f"{record.name}:{record.lineno}"
        return f"[{timestamp}] [{level}] [{location}] {message}"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("fraudlens")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Avoid duplicate handlers if reloaded
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(FraudLensFormatter())
        logger.addHandler(handler)

    # Configure uvicorn loggers to match
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        u_logger = logging.getLogger(uvicorn_logger_name)
        u_logger.handlers = logger.handlers

    return logger


logger = setup_logging()
