"""
KIRO2 Unified Event Bus System
Central event-driven architecture for the Turkish university exam preparation platform
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import asyncio
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from core.application_metrics import MetricType, get_metrics_collector
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config

config = get_unified_config()
logger = get_logger(__name__, LogCategory.EVENTS)


class EventPriority(Enum):
    """Event priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    """System event types for Turkish exam platform"""

    # User Events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PROFILE_UPDATED = "user.profile_updated"
    USER_SETTINGS_CHANGED = "user.settings_changed"

    # Authentication Events
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_EXPIRED = "auth.token_expired"
    AUTH_PASSWORD_RESET = "auth.password_reset"
    TWO_FA_ENABLED = "auth.two_fa_enabled"

    # Educational Events
    LESSON_STARTED = "education.lesson_started"
    LESSON_COMPLETED = "education.lesson_completed"
    QUESTION_ANSWERED = "education.question_answered"
    PRACTICE_TEST_STARTED = "education.practice_test_started"
    PRACTICE_TEST_COMPLETED = "education.practice_test_completed"
    STUDY_SESSION_STARTED = "education.study_session_started"
    STUDY_SESSION_ENDED = "education.study_session_ended"

    # Turkish Exam Events
    YKS_REGISTRATION_OPENED = "exam.yks_registration_opened"
    YKS_REGISTRATION_CLOSED = "exam.yks_registration_closed"
    TYT_SIMULATION_STARTED = "exam.tyt_simulation_started"
    TYT_SIMULATION_COMPLETED = "exam.tyt_simulation_completed"
    AYT_SIMULATION_STARTED = "exam.ayt_simulation_started"
    AYT_SIMULATION_COMPLETED = "exam.ayt_simulation_completed"
    EXAM_RESULTS_PUBLISHED = "exam.results_published"
    RANKING_CALCULATED = "exam.ranking_calculated"

    # Content Events
    CONTENT_CREATED = "content.created"
    CONTENT_UPDATED = "content.updated"
    CONTENT_DELETED = "content.deleted"
    CONTENT_PUBLISHED = "content.published"
    CONTENT_VIEWED = "content.viewed"

    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    CACHE_INVALIDATED = "system.cache_invalidated"
    DATABASE_BACKUP = "system.database_backup"
    PERFORMANCE_ALERT = "system.performance_alert"
    SECURITY_ALERT = "system.security_alert"

    # Notification Events
    EMAIL_SENT = "notification.email_sent"
    SMS_SENT = "notification.sms_sent"
    PUSH_NOTIFICATION_SENT = "notification.push_sent"
    WEBSOCKET_MESSAGE_SENT = "notification.websocket_sent"

    # Analytics Events
    USER_ACTION_TRACKED = "analytics.user_action_tracked"
    PERFORMANCE_METRIC_RECORDED = "analytics.performance_metric_recorded"
    LEARNING_PROGRESS_UPDATED = "analytics.learning_progress_updated"


class EventStatus(Enum):
    """Event processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class Event:
    """Base event class for the event bus system"""

    id: str
    type: EventType
    source: str
    timestamp: datetime
    data: dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: str | None = None
    user_id: int | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    ttl: int | None = None  # Time to live in seconds

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.correlation_id:
            self.correlation_id = self.id

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary"""
        data = asdict(self)
        data["type"] = self.type.value
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create event from dictionary"""
        data = data.copy()
        data["type"] = EventType(data["type"])
        data["priority"] = EventPriority(data["priority"])
        data["status"] = EventStatus(data["status"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def is_expired(self) -> bool:
        """Check if event has expired"""
        if not self.ttl:
            return False
        age = (datetime.now(UTC) - self.timestamp).total_seconds()
        return age > self.ttl

    def should_retry(self) -> bool:
        """Check if event should be retried"""
        return (
            self.status == EventStatus.FAILED
            and self.retry_count < self.max_retries
            and not self.is_expired()
        )


@dataclass
class EventHandler:
    """Event handler registration information"""

    handler_id: str
    event_type: EventType
    callback: Callable
    priority: int = 0
    async_handler: bool = False
    filters: dict[str, Any] = field(default_factory=dict)
    max_concurrent: int = 10
    timeout: float | None = None
    dead_letter_queue: bool = True

    def matches_event(self, event: Event) -> bool:
        """Check if handler matches the event"""
        if self.event_type != event.type:
            return False

        # Apply filters
        for filter_key, filter_value in self.filters.items():
            if filter_key in event.data:
                if event.data[filter_key] != filter_value:
                    return False
            elif filter_key in event.metadata:
                if event.metadata[filter_key] != filter_value:
                    return False

        return True


class EventBusMiddleware:
    """Middleware for event processing pipeline"""

    async def before_publish(self, event: Event) -> Event | None:
        """Called before event is published"""
        return event

    async def after_publish(self, event: Event) -> None:
        """Called after event is published"""

    async def before_handle(self, event: Event, handler: EventHandler) -> Event | None:
        """Called before event is handled"""
        return event

    async def after_handle(
        self, event: Event, handler: EventHandler, result: Any
    ) -> None:
        """Called after event is handled"""

    async def on_error(
        self, event: Event, handler: EventHandler, error: Exception
    ) -> bool:
        """Called when handler raises an exception. Return True to continue, False to stop"""
        return True


class LoggingMiddleware(EventBusMiddleware):
    """Logging middleware for event tracking"""

    async def before_publish(self, event: Event) -> Event | None:
        logger.debug(
            f"Publishing event: {event.type.value} from {event.source}",
            extra={"event_id": event.id, "event_type": event.type.value},
        )
        return event

    async def after_handle(
        self, event: Event, handler: EventHandler, result: Any
    ) -> None:
        logger.debug(
            f"Event handled: {event.type.value} by {handler.handler_id}",
            extra={"event_id": event.id, "handler_id": handler.handler_id},
        )

    async def on_error(
        self, event: Event, handler: EventHandler, error: Exception
    ) -> bool:
        logger.error(
            f"Event handler error: {handler.handler_id} for event {event.type.value}: {error}",
            extra={
                "event_id": event.id,
                "handler_id": handler.handler_id,
                "error": str(error),
            },
        )
        return True


class MetricsMiddleware(EventBusMiddleware):
    """Metrics collection middleware"""

    def __init__(self):
        self.metrics_collector = get_metrics_collector()

    async def after_publish(self, event: Event) -> None:
        self.metrics_collector.record_metric(
            MetricType.EVENT_PUBLISHED,
            1,
            metadata={"event_type": event.type.value, "priority": event.priority.value},
        )

    async def after_handle(
        self, event: Event, handler: EventHandler, result: Any
    ) -> None:
        self.metrics_collector.record_metric(
            MetricType.EVENT_HANDLED,
            1,
            metadata={"event_type": event.type.value, "handler_id": handler.handler_id},
        )

    async def on_error(
        self, event: Event, handler: EventHandler, error: Exception
    ) -> bool:
        self.metrics_collector.record_metric(
            MetricType.EVENT_ERROR,
            1,
            metadata={"event_type": event.type.value, "handler_id": handler.handler_id},
        )
        return True


class EventBus:
    """Central event bus for the Turkish exam platform"""

    def __init__(self):
        self.handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self.middlewares: list[EventBusMiddleware] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.dead_letter_queue: asyncio.Queue = asyncio.Queue()
        self.processing_tasks: set[asyncio.Task] = set()
        self.event_history: deque = deque(maxlen=10000)  # Keep last 10k events
        self.handler_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # Configuration
        self.max_concurrent_events = 100
        self.event_timeout = 30.0  # seconds
        self.retry_delay = 1.0  # seconds
        self.running = False

        # Background tasks
        self.processor_task: asyncio.Task | None = None
        self.dead_letter_processor_task: asyncio.Task | None = None
        self.cleanup_task: asyncio.Task | None = None

        # Add default middlewares
        self.add_middleware(LoggingMiddleware())
        self.add_middleware(MetricsMiddleware())

    def add_middleware(self, middleware: EventBusMiddleware):
        """Add middleware to the event processing pipeline"""
        self.middlewares.append(middleware)
        logger.debug(f"Added middleware: {middleware.__class__.__name__}")

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        priority: int = 0,
        filters: dict[str, Any] | None = None,
        max_concurrent: int = 10,
        timeout: float | None = None,
    ) -> str:
        """Subscribe to events of a specific type"""
        handler_id = f"{handler.__name__}_{uuid.uuid4().hex[:8]}"

        event_handler = EventHandler(
            handler_id=handler_id,
            event_type=event_type,
            callback=handler,
            priority=priority,
            async_handler=asyncio.iscoroutinefunction(handler),
            filters=filters or {},
            max_concurrent=max_concurrent,
            timeout=timeout or self.event_timeout,
        )

        # Insert handler in priority order (higher priority first)
        handlers_list = self.handlers[event_type]
        inserted = False
        for i, existing_handler in enumerate(handlers_list):
            if priority > existing_handler.priority:
                handlers_list.insert(i, event_handler)
                inserted = True
                break

        if not inserted:
            handlers_list.append(event_handler)

        logger.info(
            f"Subscribed handler {handler_id} to {event_type.value}",
            message_tr=f"Olay işleyicisi {handler_id} kaydedildi: {event_type.value}",
        )

        return handler_id

    def unsubscribe(self, handler_id: str) -> bool:
        """Unsubscribe a handler by ID"""
        for event_type, handlers_list in self.handlers.items():
            for handler in handlers_list[
                :
            ]:  # Create a copy to avoid modification during iteration
                if handler.handler_id == handler_id:
                    handlers_list.remove(handler)
                    logger.info(
                        f"Unsubscribed handler {handler_id} from {event_type.value}"
                    )
                    return True
        return False

    async def publish(
        self,
        event_type: EventType,
        data: dict[str, Any],
        source: str = "system",
        priority: EventPriority = EventPriority.NORMAL,
        user_id: int | None = None,
        session_id: str | None = None,
        correlation_id: str | None = None,
        ttl: int | None = None,
    ) -> str:
        """Publish an event to the event bus"""

        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            timestamp=datetime.now(UTC),
            data=data,
            priority=priority,
            correlation_id=correlation_id,
            user_id=user_id,
            session_id=session_id,
            ttl=ttl,
        )

        # Apply middleware before publish
        for middleware in self.middlewares:
            event = await middleware.before_publish(event)
            if event is None:
                logger.warning(
                    f"Event {event_type.value} was filtered out by middleware"
                )
                return ""

        # Add to queue
        await self.event_queue.put(event)

        # Apply middleware after publish
        for middleware in self.middlewares:
            await middleware.after_publish(event)

        logger.debug(f"Published event: {event.type.value} with ID: {event.id}")
        return event.id

    async def start(self):
        """Start the event bus processing"""
        if self.running:
            return

        self.running = True

        # Start background tasks
        self.processor_task = asyncio.create_task(self._process_events())
        self.dead_letter_processor_task = asyncio.create_task(
            self._process_dead_letter_queue()
        )
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("Event Bus started", message_tr="Olay Veriyolu başlatıldı")

    async def stop(self):
        """Stop the event bus processing"""
        if not self.running:
            return

        self.running = False

        # Cancel background tasks
        if self.processor_task:
            self.processor_task.cancel()
        if self.dead_letter_processor_task:
            self.dead_letter_processor_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        # Wait for processing tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)

        logger.info("Event Bus stopped", message_tr="Olay Veriyolu durduruldu")

    async def _process_events(self):
        """Main event processing loop"""
        while self.running:
            try:
                # Limit concurrent processing
                if len(self.processing_tasks) >= self.max_concurrent_events:
                    await asyncio.sleep(0.1)
                    continue

                # Get next event
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                except TimeoutError:
                    continue

                # Check if event is expired
                if event.is_expired():
                    logger.warning(f"Event {event.id} expired, skipping")
                    continue

                # Create processing task
                task = asyncio.create_task(self._handle_event(event))
                self.processing_tasks.add(task)

                # Clean up completed tasks
                task.add_done_callback(self.processing_tasks.discard)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event processing loop error: {e}")
                await asyncio.sleep(1.0)

    async def _handle_event(self, event: Event):
        """Handle a single event"""
        try:
            event.status = EventStatus.PROCESSING
            self.event_history.append(event)

            # Get handlers for this event type
            handlers = self.handlers.get(event.type, [])
            if not handlers:
                logger.debug(
                    f"No handlers registered for event type: {event.type.value}"
                )
                event.status = EventStatus.COMPLETED
                return

            # Process handlers
            for handler in handlers:
                if not handler.matches_event(event):
                    continue

                try:
                    # Apply middleware before handle
                    processed_event = event
                    for middleware in self.middlewares:
                        processed_event = await middleware.before_handle(
                            processed_event, handler
                        )
                        if processed_event is None:
                            break

                    if processed_event is None:
                        continue

                    # Execute handler
                    if handler.async_handler:
                        if handler.timeout:
                            result = await asyncio.wait_for(
                                handler.callback(processed_event),
                                timeout=handler.timeout,
                            )
                        else:
                            result = await handler.callback(processed_event)
                    else:
                        result = handler.callback(processed_event)

                    # Update stats
                    self.handler_stats[handler.handler_id]["success"] += 1

                    # Apply middleware after handle
                    for middleware in self.middlewares:
                        await middleware.after_handle(processed_event, handler, result)

                except Exception as e:
                    # Update stats
                    self.handler_stats[handler.handler_id]["error"] += 1

                    # Apply middleware on error
                    continue_processing = True
                    for middleware in self.middlewares:
                        if not await middleware.on_error(event, handler, e):
                            continue_processing = False
                            break

                    if not continue_processing:
                        break

                    # Check if we should retry
                    if event.should_retry():
                        event.retry_count += 1
                        event.status = EventStatus.RETRYING

                        # Add delay before retry
                        await asyncio.sleep(self.retry_delay * (2**event.retry_count))
                        await self.event_queue.put(event)
                        return
                    # Send to dead letter queue
                    event.status = EventStatus.FAILED
                    await self.dead_letter_queue.put(event)
                    return

            event.status = EventStatus.COMPLETED

        except Exception as e:
            logger.error(f"Event handling error: {e}")
            event.status = EventStatus.FAILED
            await self.dead_letter_queue.put(event)

    async def _process_dead_letter_queue(self):
        """Process dead letter queue"""
        while self.running:
            try:
                try:
                    event = await asyncio.wait_for(
                        self.dead_letter_queue.get(), timeout=5.0
                    )
                except TimeoutError:
                    continue

                logger.warning(
                    f"Dead letter event: {event.type.value} (ID: {event.id})",
                    message_tr=f"İşlenemeyen olay: {event.type.value}",
                )

                # Could implement dead letter processing logic here
                # For now, just log and discard

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Dead letter processing error: {e}")
                await asyncio.sleep(1.0)

    async def _cleanup_loop(self):
        """Periodic cleanup of resources"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Clean up handler stats
                current_time = time.time()
                for handler_id in list(self.handler_stats.keys()):
                    # Remove stats for handlers that no longer exist
                    handler_exists = any(
                        any(h.handler_id == handler_id for h in handlers)
                        for handlers in self.handlers.values()
                    )
                    if not handler_exists:
                        del self.handler_stats[handler_id]

                logger.debug("Event bus cleanup completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event bus cleanup error: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics"""
        return {
            "running": self.running,
            "queue_size": self.event_queue.qsize(),
            "dead_letter_queue_size": self.dead_letter_queue.qsize(),
            "processing_tasks": len(self.processing_tasks),
            "registered_handlers": {
                event_type.value: len(handlers)
                for event_type, handlers in self.handlers.items()
            },
            "handler_stats": dict(self.handler_stats),
            "events_processed": len(self.event_history),
            "middlewares": [
                middleware.__class__.__name__ for middleware in self.middlewares
            ],
        }

    def get_recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent events"""
        return [event.to_dict() for event in list(self.event_history)[-limit:]]

    @asynccontextmanager
    async def event_transaction(self, correlation_id: str):
        """Context manager for event transactions"""
        events_in_transaction = []

        def track_event(event):
            if event.correlation_id == correlation_id:
                events_in_transaction.append(event)

        # Add temporary middleware to track events
        class TransactionMiddleware(EventBusMiddleware):
            async def after_publish(self, event: Event) -> None:
                track_event(event)

        temp_middleware = TransactionMiddleware()
        self.add_middleware(temp_middleware)

        try:
            yield events_in_transaction
        except Exception as e:
            # In case of error, could implement rollback logic
            logger.error(f"Event transaction failed: {correlation_id}: {e}")
            raise
        finally:
            # Remove temporary middleware
            self.middlewares.remove(temp_middleware)


# Global event bus instance
_event_bus: EventBus | None = None


async def get_event_bus() -> EventBus:
    """Get global event bus instance"""
    global _event_bus

    if _event_bus is None:
        _event_bus = EventBus()
        await _event_bus.start()

    return _event_bus


# Decorator for event handlers
def event_handler(
    event_type: EventType,
    priority: int = 0,
    filters: dict[str, Any] | None = None,
    max_concurrent: int = 10,
    timeout: float | None = None,
):
    """Decorator for registering event handlers"""

    def decorator(func):
        async def register_handler():
            bus = await get_event_bus()
            return bus.subscribe(
                event_type=event_type,
                handler=func,
                priority=priority,
                filters=filters,
                max_concurrent=max_concurrent,
                timeout=timeout,
            )

        # Register immediately if possible, otherwise defer
        try:
            asyncio.create_task(register_handler())
        except RuntimeError:
            # No event loop running, will register when bus is accessed
            pass

        return func

    return decorator


# Utility functions
async def publish_event(
    event_type: EventType,
    data: dict[str, Any],
    source: str = "system",
    priority: EventPriority = EventPriority.NORMAL,
    **kwargs,
) -> str:
    """Convenience function to publish events"""
    bus = await get_event_bus()
    return await bus.publish(event_type, data, source, priority, **kwargs)


async def publish_turkish_exam_event(
    exam_type: str,  # 'yks', 'tyt', 'ayt', etc.
    action: str,  # 'started', 'completed', 'registered', etc.
    user_id: int,
    exam_data: dict[str, Any],
    session_id: str | None = None,
) -> str:
    """Convenience function for Turkish exam events"""

    # Map to appropriate event types
    event_type_map = {
        ("tyt", "started"): EventType.TYT_SIMULATION_STARTED,
        ("tyt", "completed"): EventType.TYT_SIMULATION_COMPLETED,
        ("ayt", "started"): EventType.AYT_SIMULATION_STARTED,
        ("ayt", "completed"): EventType.AYT_SIMULATION_COMPLETED,
        ("yks", "registration_opened"): EventType.YKS_REGISTRATION_OPENED,
        ("yks", "registration_closed"): EventType.YKS_REGISTRATION_CLOSED,
    }

    event_type = event_type_map.get((exam_type.lower(), action.lower()))
    if not event_type:
        # Default to a general exam event
        event_type = (
            EventType.PRACTICE_TEST_STARTED
            if "start" in action
            else EventType.PRACTICE_TEST_COMPLETED
        )

    return await publish_event(
        event_type=event_type,
        data={"exam_type": exam_type, "action": action, **exam_data},
        source="exam_system",
        priority=EventPriority.HIGH,
        user_id=user_id,
        session_id=session_id,
    )


# Turkish language event utilities
async def publish_educational_event(
    event_type: str,  # Turkish: 'ders_basladi', 'soru_cevaplandi', etc.
    user_id: int,
    subject: str,  # 'matematik', 'turkce', 'fen_bilimleri', etc.
    content_data: dict[str, Any],
    session_id: str | None = None,
) -> str:
    """Publish educational events with Turkish context"""

    # Map Turkish event types to system events
    turkish_event_map = {
        "ders_basladi": EventType.LESSON_STARTED,
        "ders_tamamlandi": EventType.LESSON_COMPLETED,
        "soru_cevaplandi": EventType.QUESTION_ANSWERED,
        "deneme_basladi": EventType.PRACTICE_TEST_STARTED,
        "deneme_tamamlandi": EventType.PRACTICE_TEST_COMPLETED,
        "calisma_oturumu_basladi": EventType.STUDY_SESSION_STARTED,
        "calisma_oturumu_bitti": EventType.STUDY_SESSION_ENDED,
    }

    mapped_event = turkish_event_map.get(event_type, EventType.USER_ACTION_TRACKED)

    return await publish_event(
        event_type=mapped_event,
        data={
            "turkish_event_type": event_type,
            "subject": subject,
            "subject_tr": subject,  # Turkish subject name
            **content_data,
        },
        source="education_system",
        priority=EventPriority.NORMAL,
        user_id=user_id,
        session_id=session_id,
    )
