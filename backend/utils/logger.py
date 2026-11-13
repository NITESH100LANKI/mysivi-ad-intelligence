"""Structured logging utility with secret masking."""
import logging
import re
import sys
from typing import Optional


class SecretMaskingFilter(logging.Filter):
    """Filter that masks tokens and API keys matching common patterns."""

    PATTERNS = [
        re.compile(r"(AIza[0-9A-Za-z-_]{35})"),  # Google API key
        re.compile(r"(apify_api_[0-9A-Za-z]{32,})"),  # Apify token
        re.compile(r"([A-Za-z0-9_-]{20,}:[A-Za-z0-9_-]{20,})"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            masked = record.msg
            for pattern in self.PATTERNS:
                masked = pattern.sub(lambda m: m.group(0)[:4] + "****" + m.group(0)[-4:], masked)
            record.msg = masked
        return True


def setup_logger(name: str = "MySiviAdIntelligence", level: int = logging.INFO) -> logging.Logger:
    """Set up and return a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SecretMaskingFilter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger

