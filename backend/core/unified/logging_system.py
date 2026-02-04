"""
KIRO2 Unified Logging System
Consolidated logging solution combining all logging functionality
"""

import json
import logging
import logging.config
import os
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log level definitions"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log category definitions for KIRO2 platform"""

    API = "api"
    DATABASE = "database"
    AUTH = "auth"
    EXAM = "exam"
    CACHE = "cache"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USER = "user"
    CONTENT = "content"
    ANALYTICS = "analytics"
    SYSTEM = "system"


class LogFormat(Enum):
    """Log format types"""

    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"


class LoggerConfig:
    """Unified logging configuration"""

    def __init__(
        self,
        name: str = "kiro2",
        level: LogLevel = LogLevel.INFO,
        log_dir: str = "logs",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        retention_days: int = 30,
        format_type: LogFormat = LogFormat.JSON,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_rotation: bool = True,
        enable_compression: bool = True,
        turkish_encoding: str = "utf-8",
    ):
        self.name = name
        self.level = level
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.retention_days = retention_days
        self.format_type = format_type
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_rotation = enable_rotation
        self.enable_compression = enable_compression
        self.turkish_encoding = turkish_encoding

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)


class TurkishJSONFormatter(logging.Formatter):
    """Turkish-aware JSON log formatter"""

    def __init__(self, encoding: str = "utf-8"):
        super().__init__()
        self.encoding = encoding

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with Turkish support"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }

        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
                "getMessage",
            ]:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False, separators=(",", ":"))


class StructuredTextFormatter(logging.Formatter):
    """Structured text formatter for console output"""

    def __init__(self, encoding: str = "utf-8"):
        super().__init__()
        self.encoding = encoding

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured text"""
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Basic log message
        message = (
            f"[{timestamp}] [{record.levelname}] {record.name}: {record.getMessage()}"
        )

        # Add location info for DEBUG level
        if record.levelno == logging.DEBUG:
            message += f" ({record.filename}:{record.lineno})"

        # Add exception info if available
        if record.exc_info:
            message += f"\nException: {record.exc_info[1]}"
            if record.levelno >= logging.ERROR:
                message += f"\n{''.join(traceback.format_exception(*record.exc_info))}"

        return message


class LogMetrics:
    """Log metrics collection"""

    def __init__(self):
        self.counts = {level.value: 0 for level in LogLevel}
        self.categories = {cat.value: 0 for cat in LogCategory}
        self.errors = []
        self.start_time = datetime.now()

    def increment(self, level: str, category: str = None):
        """Increment log counters"""
        if level in self.counts:
            self.counts[level] += 1

        if category and category in self.categories:
            self.categories[category] += 1

    def add_error(self, error_info: dict[str, Any]):
        """Add error information"""
        self.errors.append({**error_info, "timestamp": datetime.now().isoformat()})

        # Keep only last 100 errors
        if len(self.errors) > 100:
            self.errors = self.errors[-100:]

    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary"""
        uptime = datetime.now() - self.start_time

        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_logs": sum(self.counts.values()),
            "log_levels": self.counts,
            "categories": self.categories,
            "error_count": len(self.errors),
            "recent_errors": self.errors[-5:] if self.errors else [],
        }


class UnifiedLoggingManager:
    """
    Unified logging manager combining all logging functionality:
    - Structured JSON logging
    - Turkish character support
    - File rotation and retention
    - Multiple output formats
    - Performance monitoring
    - Error tracking
    """

    def __init__(self, config: LoggerConfig | None = None):
        self.config = config or LoggerConfig()
        self.loggers: dict[str, logging.Logger] = {}
        self.metrics = LogMetrics()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize logging system"""
        if self._initialized:
            return

        try:
            # Create root logger
            self._create_logger(self.config.name)

            # Setup default loggers for each category
            for category in LogCategory:
                self._create_logger(f"{self.config.name}.{category.value}")

            self._initialized = True
            logger.info("Unified logging system initialized successfully")

        except Exception as e:
            print(f"Failed to initialize logging system: {e}")
            raise

    def _create_logger(self, name: str) -> logging.Logger:
        """Create and configure a logger"""
        if name in self.loggers:
            return self.loggers[name]

        log = logging.getLogger(name)
        log.setLevel(getattr(logging, self.config.level.value))

        # Clear existing handlers
        log.handlers.clear()

        # Console handler
        if self.config.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.config.level.value))

            if self.config.format_type == LogFormat.JSON:
                console_handler.setFormatter(
                    TurkishJSONFormatter(self.config.turkish_encoding)
                )
            else:
                console_handler.setFormatter(
                    StructuredTextFormatter(self.config.turkish_encoding)
                )

            log.addHandler(console_handler)

        # File handler
        if self.config.enable_file:
            log_file = self.config.log_dir / f"{name}.log"

            if self.config.enable_rotation:
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=self.config.max_file_size,
                    backupCount=self.config.backup_count,
                    encoding=self.config.turkish_encoding,
                )
            else:
                file_handler = logging.FileHandler(
                    log_file, encoding=self.config.turkish_encoding
                )

            file_handler.setLevel(getattr(logging, self.config.level.value))
            file_handler.setFormatter(
                TurkishJSONFormatter(self.config.turkish_encoding)
            )
            log.addHandler(file_handler)

        # Prevent propagation to avoid duplicate logs
        log.propagate = False

        self.loggers[name] = log
        return log

    def get_logger(
        self, name: str = None, category: LogCategory = None
    ) -> logging.Logger:
        """Get logger instance"""
        if not self._initialized:
            self.initialize()

        if category:
            logger_name = f"{self.config.name}.{category.value}"
        elif name:
            logger_name = name
        else:
            logger_name = self.config.name

        if logger_name not in self.loggers:
            return self._create_logger(logger_name)

        return self.loggers[logger_name]

    def log_structured(
        self,
        level: LogLevel,
        message: str,
        category: LogCategory = None,
        extra: dict[str, Any] = None,
        **kwargs,
    ) -> None:
        """Log structured message with metadata"""
        log = self.get_logger(category=category)

        # Prepare extra data
        log_extra = {
            "category": category.value if category else "general",
            "service": "kiro2",
            "environment": os.getenv("ENVIRONMENT", "development"),
            **(extra or {}),
            **kwargs,
        }

        # Update metrics
        self.metrics.increment(level.value, category.value if category else None)

        # Log the message
        log_level = getattr(logging, level.value)
        log.log(log_level, message, extra=log_extra)

        # Track errors
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.metrics.add_error(
                {
                    "level": level.value,
                    "message": message,
                    "category": category.value if category else None,
                    "extra": log_extra,
                }
            )

    def debug(self, message: str, category: LogCategory = None, **kwargs):
        """Log debug message"""
        self.log_structured(LogLevel.DEBUG, message, category, **kwargs)

    def info(self, message: str, category: LogCategory = None, **kwargs):
        """Log info message"""
        self.log_structured(LogLevel.INFO, message, category, **kwargs)

    def warning(self, message: str, category: LogCategory = None, **kwargs):
        """Log warning message"""
        self.log_structured(LogLevel.WARNING, message, category, **kwargs)

    def error(
        self,
        message: str,
        category: LogCategory = None,
        exc_info: bool = True,
        **kwargs,
    ):
        """Log error message"""
        if exc_info:
            kwargs["exc_info"] = True
        self.log_structured(LogLevel.ERROR, message, category, **kwargs)

    def critical(
        self,
        message: str,
        category: LogCategory = None,
        exc_info: bool = True,
        **kwargs,
    ):
        """Log critical message"""
        if exc_info:
            kwargs["exc_info"] = True
        self.log_structured(LogLevel.CRITICAL, message, category, **kwargs)

    @contextmanager
    def log_execution_time(self, operation: str, category: LogCategory = None):
        """Context manager to log execution time"""
        start_time = datetime.now()
        try:
            yield
            duration = (datetime.now() - start_time).total_seconds()
            self.info(
                f"Operation completed: {operation}",
                category=category or LogCategory.PERFORMANCE,
                duration_seconds=duration,
                operation=operation,
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.error(
                f"Operation failed: {operation}",
                category=category or LogCategory.PERFORMANCE,
                duration_seconds=duration,
                operation=operation,
                error=str(e),
            )
            raise

    def cleanup_old_logs(self) -> int:
        """Clean up old log files based on retention policy"""
        if self.config.retention_days <= 0:
            return 0

        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        removed_count = 0

        try:
            for log_file in self.config.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    removed_count += 1

            self.info(
                "Log cleanup completed",
                category=LogCategory.SYSTEM,
                removed_files=removed_count,
                retention_days=self.config.retention_days,
            )

        except Exception as e:
            self.error(f"Log cleanup failed: {e}", category=LogCategory.SYSTEM)

        return removed_count

    def get_metrics(self) -> dict[str, Any]:
        """Get logging metrics"""
        return self.metrics.get_summary()

    def health_check(self) -> dict[str, Any]:
        """Perform logging system health check"""
        status = {
            "initialized": self._initialized,
            "loggers_count": len(self.loggers),
            "log_directory": str(self.config.log_dir),
            "log_directory_exists": self.config.log_dir.exists(),
            "metrics": self.get_metrics(),
            "config": {
                "level": self.config.level.value,
                "format": self.config.format_type.value,
                "console_enabled": self.config.enable_console,
                "file_enabled": self.config.enable_file,
                "rotation_enabled": self.config.enable_rotation,
            },
        }

        # Check log directory permissions
        try:
            test_file = self.config.log_dir / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            status["log_directory_writable"] = True
        except Exception:
            status["log_directory_writable"] = False

        return status


# Global instance
_logging_manager: UnifiedLoggingManager | None = None


def get_logging_manager() -> UnifiedLoggingManager:
    """Get global logging manager instance"""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = UnifiedLoggingManager()
        _logging_manager.initialize()
    return _logging_manager


def get_logger(name: str = None, category: LogCategory = None) -> logging.Logger:
    """Get logger instance - convenience function"""
    return get_logging_manager().get_logger(name, category)


# Backward compatibility aliases
LogConfig = LoggerConfig
StructuredLogger = UnifiedLoggingManager
LoggingConfig = UnifiedLoggingManager
LoggingIntegration = UnifiedLoggingManager
LoggingMiddleware = UnifiedLoggingManager
StructuredLogging = UnifiedLoggingManager
