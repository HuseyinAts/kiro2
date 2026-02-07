"""Elasticsearch logging wrapper module."""
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, Enum):
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    GENERAL = "general"
    AUTH = "auth"
    SYSTEM = "system"
    JOBS = "jobs"


class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: LogLevel = LogLevel.INFO
    category: LogCategory = LogCategory.GENERAL
    message: str = ""
    metadata: dict[str, Any] = {}
    source: str = ""
    user_id: Optional[str] = None
    request_id: Optional[str] = None


class ElasticsearchLogger:
    """Logger that formats entries for Elasticsearch-compatible output."""

    def __init__(self, index_prefix: str = "kiro2-logs", enabled: bool = True) -> None:
        self.index_prefix = index_prefix
        self.enabled = enabled
        self._logger = logging.getLogger("elasticsearch_logger")
        self._entries: list[LogEntry] = []

    async def log(self, entry: LogEntry) -> None:
        if not self.enabled:
            return
        self._entries.append(entry)
        self._logger.log(
            getattr(logging, entry.level.value.upper(), logging.INFO),
            f"[{entry.category.value}] {entry.message}",
        )

    async def info(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs: Any) -> None:
        await self.log(LogEntry(level=LogLevel.INFO, category=category, message=message, metadata=kwargs))

    async def error(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs: Any) -> None:
        await self.log(LogEntry(level=LogLevel.ERROR, category=category, message=message, metadata=kwargs))

    async def warning(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs: Any) -> None:
        await self.log(LogEntry(level=LogLevel.WARNING, category=category, message=message, metadata=kwargs))

    async def get_entries(self, limit: int = 100) -> list[LogEntry]:
        return self._entries[-limit:]

    async def clear(self) -> None:
        self._entries.clear()


class ElasticsearchLoggingMiddleware:
    """ASGI middleware for request/response logging."""

    def __init__(self, app: Any, logger: Optional[ElasticsearchLogger] = None) -> None:
        self.app = app
        self.logger = logger or ElasticsearchLogger()

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        await self.app(scope, receive, send)


_logger_instance: Optional[ElasticsearchLogger] = None


def get_elasticsearch_logger() -> ElasticsearchLogger:
    """Get or create global Elasticsearch logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ElasticsearchLogger()
    return _logger_instance
