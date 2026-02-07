"""
Structured Logging Module
Provides categorized logging with structured output
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
