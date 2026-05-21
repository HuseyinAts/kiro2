"""
Structured Logging Module
Provides categorized logging with structured output.

@deprecated S179 fix (B-P1-25): KIRO2 has two parallel logger modules —
this one and `core.structured_logger`. The audit (Session 179) counted
86 importers of `structured_logger` vs 10 of `structured_logging`.
New code SHOULD use `core.structured_logger.get_logger(...)`. This
module is kept for backward compatibility only; do not extend.
"""

import logging
from enum import Enum


class LogCategory(str, Enum):
    """Log categories for structured logging"""

    TESTING = "testing"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    GENERAL = "general"
    EVENTS = "events"
    QUEUE = "queue"
    CACHE = "cache"
    AUTH = "auth"
    EXAM = "exam"
    USER = "user"
    CONTENT = "content"
    ANALYTICS = "analytics"
    SYSTEM = "system"
    JOBS = "jobs"
    REALTIME = "realtime"


def get_logger(
    name: str, category: LogCategory = LogCategory.GENERAL
) -> logging.Logger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (usually __name__)
        category: Log category for filtering/organization

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"{category.value}.{name}")
    return logger
