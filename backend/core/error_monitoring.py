"""
Error Logging and Monitoring System
Comprehensive error logging, monitoring, alerting, and analytics
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .exceptions import EnhancedServiceError, ErrorSeverity
from .unified_config import get_unified_config

# ==================== ERROR LOG MODELS ====================


class LogLevel(str, Enum):
    """Log severity levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ErrorLogEntry:
    """Structured error log entry"""

    id: str
    timestamp: datetime
    level: LogLevel
    error_code: str
    error_type: str
    message: str
    user_message: str
    severity: ErrorSeverity

    # Context information
    request_id: str | None = None
    correlation_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    endpoint: str | None = None
    method: str | None = None

    # Technical details
    stack_trace: str | None = None
    source_location: dict[str, Any] | None = None
    exception_details: dict[str, Any] | None = None

    # Performance metrics
    processing_time_ms: float | None = None
    memory_usage_mb: float | None = None
    cpu_usage_percent: float | None = None

    # Environment context
    environment: str | None = None
    service_version: str | None = None
    host_name: str | None = None

    # Additional metadata
    tags: dict[str, str] = field(default_factory=dict)
    custom_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["level"] = self.level.value
        data["severity"] = self.severity.value
        return data


@dataclass
class ErrorMetrics:
    """Error metrics for monitoring"""

    total_errors: int = 0
    errors_by_type: dict[str, int] = field(default_factory=dict)
    errors_by_severity: dict[str, int] = field(default_factory=dict)
    errors_by_endpoint: dict[str, int] = field(default_factory=dict)
    errors_by_user: dict[str, int] = field(default_factory=dict)
    errors_per_minute: deque = field(default_factory=lambda: deque(maxlen=60))
    errors_per_hour: deque = field(default_factory=lambda: deque(maxlen=24))

    # Performance metrics
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float("inf")

    # System health indicators
    error_rate_threshold_breached: bool = False
    critical_error_count_last_hour: int = 0
    consecutive_errors: int = 0
    last_error_time: datetime | None = None

    def update_metrics(self, log_entry: ErrorLogEntry):
        """Update metrics with new error log entry"""
        self.total_errors += 1

        # Update by type
        error_type = log_entry.error_type
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

        # Update by severity
        severity = log_entry.severity.value
        self.errors_by_severity[severity] = self.errors_by_severity.get(severity, 0) + 1

        # Update by endpoint
        if log_entry.endpoint:
            self.errors_by_endpoint[log_entry.endpoint] = (
                self.errors_by_endpoint.get(log_entry.endpoint, 0) + 1
            )

        # Update by user
        if log_entry.user_id:
            self.errors_by_user[log_entry.user_id] = (
                self.errors_by_user.get(log_entry.user_id, 0) + 1
            )

        # Update time-based metrics
        current_time = datetime.now()
        self.errors_per_minute.append(current_time)
        self.errors_per_hour.append(current_time)

        # Update performance metrics
        if log_entry.processing_time_ms:
            self.avg_response_time = (
                self.avg_response_time + log_entry.processing_time_ms
            ) / 2
            self.max_response_time = max(
                self.max_response_time, log_entry.processing_time_ms
            )
            self.min_response_time = min(
                self.min_response_time, log_entry.processing_time_ms
            )

        # Update health indicators
        if log_entry.severity == ErrorSeverity.CRITICAL:
            self.critical_error_count_last_hour += 1

        self.last_error_time = current_time
        self.consecutive_errors += 1

    def get_error_rate_per_minute(self) -> float:
        """Get current error rate per minute"""
        cutoff_time = datetime.now() - timedelta(minutes=1)
        recent_errors = [t for t in self.errors_per_minute if t > cutoff_time]
        return len(recent_errors)

    def get_error_rate_per_hour(self) -> float:
        """Get current error rate per hour"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_errors = [t for t in self.errors_per_hour if t > cutoff_time]
        return len(recent_errors)

    def reset_consecutive_errors(self):
        """Reset consecutive error counter on successful request"""
        self.consecutive_errors = 0


# ==================== LOG PROCESSORS ====================


class LogProcessor:
    """Base class for log processors"""

    async def process(self, log_entry: ErrorLogEntry) -> bool:
        """Process log entry. Return True if processing should continue."""
        raise NotImplementedError


class ConsoleLogProcessor(LogProcessor):
    """Console output log processor"""

    def __init__(self, colored_output: bool = True):
        self.colored_output = colored_output
        self.colors = {
            LogLevel.DEBUG: "\033[36m",  # Cyan
            LogLevel.INFO: "\033[32m",  # Green
            LogLevel.WARNING: "\033[33m",  # Yellow
            LogLevel.ERROR: "\033[31m",  # Red
            LogLevel.CRITICAL: "\033[35m",  # Magenta
        }
        self.reset_color = "\033[0m"

    async def process(self, log_entry: ErrorLogEntry) -> bool:
        """Process log entry to console"""

        timestamp_str = log_entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Format message
        if self.colored_output:
            color = self.colors.get(log_entry.level, "")
            message = f"{color}[{timestamp_str}] {log_entry.level.value} {log_entry.error_code}: {log_entry.message}{self.reset_color}"
        else:
            message = f"[{timestamp_str}] {log_entry.level.value} {log_entry.error_code}: {log_entry.message}"

        # Add context information
        if log_entry.request_id:
            message += f" (Request: {log_entry.request_id})"

        if log_entry.user_id:
            message += f" (User: {log_entry.user_id})"

        print(message)

        # Print stack trace for errors
        if (
            log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]
            and log_entry.stack_trace
        ):
            print(f"Stack trace:\n{log_entry.stack_trace}")

        return True


class FileLogProcessor(LogProcessor):
    """File-based log processor"""

    def __init__(
        self,
        log_file_path: str,
        max_file_size_mb: int = 100,
        backup_count: int = 5,
        json_format: bool = True,
    ):
        self.log_file_path = Path(log_file_path)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.backup_count = backup_count
        self.json_format = json_format
        self.lock = threading.Lock()

        # Ensure directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    async def process(self, log_entry: ErrorLogEntry) -> bool:
        """Process log entry to file"""

        with self.lock:
            # Check if file rotation is needed
            if (
                self.log_file_path.exists()
                and self.log_file_path.stat().st_size > self.max_file_size_bytes
            ):
                self._rotate_files()

            # Write log entry
            mode = "a" if self.log_file_path.exists() else "w"
            with open(self.log_file_path, mode, encoding="utf-8") as f:
                if self.json_format:
                    json.dump(log_entry.to_dict(), f, ensure_ascii=False)
                    f.write("\n")
                else:
                    timestamp_str = log_entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(
                        f"[{timestamp_str}] {log_entry.level.value} {log_entry.error_code}: {log_entry.message}\n"
                    )

                    if log_entry.stack_trace:
                        f.write(f"Stack trace:\n{log_entry.stack_trace}\n")
                    f.write("---\n")

        return True

    def _rotate_files(self):
        """Rotate log files"""
        for i in range(self.backup_count - 1, 0, -1):
            old_file = self.log_file_path.with_suffix(f".{i}")
            new_file = self.log_file_path.with_suffix(f".{i + 1}")

            if old_file.exists():
                if new_file.exists():
                    new_file.unlink()
                old_file.rename(new_file)

        # Move current log to .1
        if self.log_file_path.exists():
            backup_file = self.log_file_path.with_suffix(".1")
            if backup_file.exists():
                backup_file.unlink()
            self.log_file_path.rename(backup_file)


class DatabaseLogProcessor(LogProcessor):
    """Database-based log processor"""

    def __init__(self, connection_string: str, table_name: str = "error_logs"):
        self.connection_string = connection_string
        self.table_name = table_name
        self.batch_size = 10
        self.batch = []
        self.last_flush = time.time()
        self.flush_interval = 30  # seconds

    async def process(self, log_entry: ErrorLogEntry) -> bool:
        """Process log entry to database"""

        self.batch.append(log_entry)

        # Flush batch if it's full or enough time has passed
        if (
            len(self.batch) >= self.batch_size
            or time.time() - self.last_flush > self.flush_interval
        ):
            await self._flush_batch()

        return True

    async def _flush_batch(self):
        """Flush batch of log entries to database"""
        if not self.batch:
            return

        try:
            # This would be implemented based on your database choice
            # For now, we'll just simulate the operation
            await asyncio.sleep(0.1)  # Simulate database write

            self.batch.clear()
            self.last_flush = time.time()

        except Exception as e:
            # Log the error but don't fail the entire logging system
            print(f"Failed to write to database: {e}")


# ==================== ALERT SYSTEM ====================


class AlertRule:
    """Alert rule configuration"""

    def __init__(
        self,
        name: str,
        condition: Callable[[ErrorMetrics], bool],
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        cooldown_minutes: int = 5,
        message_template: str = "Alert triggered: {name}",
    ):
        self.name = name
        self.condition = condition
        self.severity = severity
        self.cooldown_minutes = cooldown_minutes
        self.message_template = message_template
        self.last_triggered: datetime | None = None

    def should_trigger(self, metrics: ErrorMetrics) -> bool:
        """Check if alert should be triggered"""

        # Check cooldown period
        if self.last_triggered:
            cooldown_end = self.last_triggered + timedelta(
                minutes=self.cooldown_minutes
            )
            if datetime.now() < cooldown_end:
                return False

        # Check condition
        return self.condition(metrics)

    def trigger(self, metrics: ErrorMetrics) -> str:
        """Trigger alert and return message"""
        self.last_triggered = datetime.now()
        return self.message_template.format(
            name=self.name, metrics=metrics, timestamp=self.last_triggered.isoformat()
        )


class AlertManager:
    """Manage error alerts and notifications"""

    def __init__(self):
        self.rules: list[AlertRule] = []
        self.notification_handlers: list[Callable] = []
        self._setup_default_rules()

    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules.append(rule)

    def add_notification_handler(self, handler: Callable):
        """Add notification handler"""
        self.notification_handlers.append(handler)

    async def check_alerts(self, metrics: ErrorMetrics):
        """Check all alert rules and trigger notifications"""

        for rule in self.rules:
            if rule.should_trigger(metrics):
                alert_message = rule.trigger(metrics)
                await self._send_notifications(alert_message, rule.severity)

    async def _send_notifications(self, message: str, severity: ErrorSeverity):
        """Send notifications to all handlers"""

        notification_data = {
            "message": message,
            "severity": severity.value,
            "timestamp": datetime.now().isoformat(),
        }

        for handler in self.notification_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(notification_data)
                else:
                    handler(notification_data)
            except Exception as e:
                print(f"Notification handler failed: {e}")

    def _setup_default_rules(self):
        """Setup default alert rules"""

        # High error rate alert
        self.add_rule(
            AlertRule(
                name="High Error Rate",
                condition=lambda m: m.get_error_rate_per_minute() > 10,
                severity=ErrorSeverity.HIGH,
                message_template="High error rate detected: {metrics.get_error_rate_per_minute():.1f} errors/minute",
            )
        )

        # Critical error alert
        self.add_rule(
            AlertRule(
                name="Critical Error",
                condition=lambda m: m.critical_error_count_last_hour > 0,
                severity=ErrorSeverity.CRITICAL,
                message_template="Critical error detected in the last hour",
            )
        )

        # Consecutive errors alert
        self.add_rule(
            AlertRule(
                name="Consecutive Errors",
                condition=lambda m: m.consecutive_errors > 5,
                severity=ErrorSeverity.HIGH,
                message_template="Multiple consecutive errors: {metrics.consecutive_errors}",
            )
        )


# ==================== MAIN ERROR MONITOR ====================


class ErrorMonitor:
    """Central error monitoring system"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.processors: list[LogProcessor] = []
        self.metrics = ErrorMetrics()
        self.alert_manager = AlertManager()
        self.logger = logging.getLogger("error_monitor")
        self.app_config = get_unified_config()

        # Setup default processors
        self._setup_default_processors()

        # Setup default alert handlers
        self._setup_default_alert_handlers()

        # Background task for periodic checks
        self._monitoring_task: asyncio.Task | None = None
        self._running = False

    def _setup_default_processors(self):
        """Setup default log processors"""

        # Console processor (always enabled in debug mode)
        if self.app_config.debug:
            self.add_processor(ConsoleLogProcessor(colored_output=True))

        # File processor
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        self.add_processor(
            FileLogProcessor(
                log_file_path=str(log_dir / "errors.log"), json_format=True
            )
        )

        # Database processor (if configured)
        if self.config.get("database_logging_enabled"):
            db_config = self.config.get("database_config", {})
            if db_config:
                self.add_processor(
                    DatabaseLogProcessor(
                        connection_string=db_config["connection_string"]
                    )
                )

    def _setup_default_alert_handlers(self):
        """Setup default alert notification handlers"""

        async def console_alert_handler(notification_data: dict[str, Any]):
            """Simple console alert handler"""
            severity = notification_data["severity"]
            message = notification_data["message"]
            timestamp = notification_data["timestamp"]

            color = (
                "\033[31m" if severity == "critical" else "\033[33m"
            )  # Red for critical, yellow for others
            reset = "\033[0m"

            print(f"\n{color}[ALERT] ALERT [{severity.upper()}] {timestamp}{reset}")
            print(f"{color}{message}{reset}\n")

        self.alert_manager.add_notification_handler(console_alert_handler)

    def add_processor(self, processor: LogProcessor):
        """Add log processor"""
        self.processors.append(processor)

    def remove_processor(self, processor: LogProcessor):
        """Remove log processor"""
        if processor in self.processors:
            self.processors.remove(processor)

    async def log_error(
        self,
        exception: Exception,
        context: dict[str, Any],
        severity: ErrorSeverity | None = None,
    ):
        """Log error with full context"""

        # Determine severity
        if severity is None:
            severity = self._determine_severity(exception)

        # Create log entry
        log_entry = ErrorLogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level=self._get_log_level(severity),
            error_code=getattr(exception, "error_code", type(exception).__name__),
            error_type=type(exception).__name__,
            message=str(exception),
            user_message=getattr(exception, "user_message", str(exception)),
            severity=severity,
            # Extract context
            request_id=context.get("request_id"),
            correlation_id=context.get("correlation_id"),
            user_id=context.get("user_id"),
            session_id=context.get("session_id"),
            endpoint=context.get("endpoint"),
            method=context.get("method"),
            # Technical details
            stack_trace=context.get("stack_trace"),
            source_location=getattr(exception, "source_location", None),
            exception_details=getattr(exception, "details", {}),
            # Performance metrics
            processing_time_ms=context.get("processing_time_ms"),
            memory_usage_mb=context.get("memory_usage_mb"),
            # Environment
            environment=self.app_config.environment.value,
            service_version=self.app_config.app_version,
            host_name=context.get("host_name"),
            # Custom fields
            tags=context.get("tags", {}),
            custom_fields=context.get("custom_fields", {}),
        )

        # Update metrics
        self.metrics.update_metrics(log_entry)

        # Process through all processors
        for processor in self.processors:
            try:
                should_continue = await processor.process(log_entry)
                if not should_continue:
                    break
            except Exception as e:
                # Don't let processor failures break the logging system
                self.logger.error(f"Log processor failed: {e}")

        # Check alerts
        await self.alert_manager.check_alerts(self.metrics)

    def _determine_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type"""

        if isinstance(exception, EnhancedServiceError):
            return exception.severity

        # Map exception types to severities
        severity_mapping = {
            ValueError: ErrorSeverity.LOW,
            KeyError: ErrorSeverity.LOW,
            AttributeError: ErrorSeverity.MEDIUM,
            TypeError: ErrorSeverity.MEDIUM,
            ConnectionError: ErrorSeverity.HIGH,
            TimeoutError: ErrorSeverity.HIGH,
            MemoryError: ErrorSeverity.CRITICAL,
            SystemError: ErrorSeverity.CRITICAL,
        }

        for exc_type, severity in severity_mapping.items():
            if isinstance(exception, exc_type):
                return severity

        return ErrorSeverity.MEDIUM

    def _get_log_level(self, severity: ErrorSeverity) -> LogLevel:
        """Get log level from error severity"""
        mapping = {
            ErrorSeverity.LOW: LogLevel.WARNING,
            ErrorSeverity.MEDIUM: LogLevel.ERROR,
            ErrorSeverity.HIGH: LogLevel.ERROR,
            ErrorSeverity.CRITICAL: LogLevel.CRITICAL,
        }
        return mapping.get(severity, LogLevel.ERROR)

    async def start_monitoring(self):
        """Start background monitoring"""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop background monitoring"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                # Periodic checks
                await self.alert_manager.check_alerts(self.metrics)

                # Clean up old metrics
                self._cleanup_old_metrics()

                # Wait for next check
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)

    def _cleanup_old_metrics(self):
        """Clean up old metrics data"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Clean up time-based metrics
        self.metrics.errors_per_minute = deque(
            [t for t in self.metrics.errors_per_minute if t > cutoff_time], maxlen=60
        )

        self.metrics.errors_per_hour = deque(
            [t for t in self.metrics.errors_per_hour if t > cutoff_time], maxlen=24
        )

        # Reset hourly critical error count
        cutoff_hour = datetime.now() - timedelta(hours=1)
        if self.metrics.last_error_time and self.metrics.last_error_time < cutoff_hour:
            self.metrics.critical_error_count_last_hour = 0

    def get_health_status(self) -> dict[str, Any]:
        """Get current system health status"""
        return {
            "status": "healthy" if self.metrics.consecutive_errors < 3 else "unhealthy",
            "total_errors": self.metrics.total_errors,
            "error_rate_per_minute": self.metrics.get_error_rate_per_minute(),
            "error_rate_per_hour": self.metrics.get_error_rate_per_hour(),
            "critical_errors_last_hour": self.metrics.critical_error_count_last_hour,
            "consecutive_errors": self.metrics.consecutive_errors,
            "last_error_time": self.metrics.last_error_time.isoformat()
            if self.metrics.last_error_time
            else None,
            "avg_response_time": self.metrics.avg_response_time,
            "max_response_time": self.metrics.max_response_time,
            "errors_by_type": dict(self.metrics.errors_by_type),
            "errors_by_severity": dict(self.metrics.errors_by_severity),
        }

    def reset_consecutive_errors(self):
        """Reset consecutive error counter (call on successful requests)"""
        self.metrics.reset_consecutive_errors()


# ==================== GLOBAL INSTANCE ====================

# Global error monitor instance
_global_error_monitor: ErrorMonitor | None = None


def get_error_monitor() -> ErrorMonitor:
    """Get global error monitor instance"""
    global _global_error_monitor
    if _global_error_monitor is None:
        _global_error_monitor = ErrorMonitor()
    return _global_error_monitor


def setup_error_monitoring(config: dict[str, Any] | None = None) -> ErrorMonitor:
    """Setup global error monitoring"""
    global _global_error_monitor
    _global_error_monitor = ErrorMonitor(config)
    return _global_error_monitor


# ==================== CONVENIENCE FUNCTIONS ====================


async def log_error(
    exception: Exception,
    context: dict[str, Any] | None = None,
    severity: ErrorSeverity | None = None,
):
    """Convenience function to log error"""
    monitor = get_error_monitor()
    await monitor.log_error(exception, context or {}, severity)


def reset_consecutive_errors():
    """Reset consecutive error counter"""
    monitor = get_error_monitor()
    monitor.reset_consecutive_errors()


async def start_monitoring():
    """Start error monitoring"""
    monitor = get_error_monitor()
    await monitor.start_monitoring()


async def stop_monitoring():
    """Stop error monitoring"""
    monitor = get_error_monitor()
    await monitor.stop_monitoring()


def get_health_status() -> dict[str, Any]:
    """Get system health status"""
    monitor = get_error_monitor()
    return monitor.get_health_status()
