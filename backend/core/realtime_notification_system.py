"""
KIRO2 Real-Time Notification System
WebSocket-based real-time notifications for Turkish exam platform
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import asyncio
import json
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

try:
    import websockets
    from websockets.exceptions import ConnectionClosed, WebSocketException
    from websockets.server import WebSocketServerProtocol
except ImportError:
    websockets = None
    WebSocketServerProtocol = None
    ConnectionClosed = Exception
    WebSocketException = Exception

from core.application_metrics import MetricType, get_metrics_collector
from core.message_queue_system import get_message_queue
from core.structured_logging import LogCategory, get_logger
from core.unified.auth_system import get_auth_system
from core.unified_config import get_unified_config
from core.unified_event_bus import Event, EventType, get_event_bus

config = get_unified_config()
logger = get_logger(__name__, LogCategory.REALTIME)


class NotificationType(Enum):
    """Real-time notification types"""

    # System notifications
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_UPDATE = "system_update"

    # Exam notifications
    EXAM_STARTED = "exam_started"
    EXAM_COMPLETED = "exam_completed"
    EXAM_TIME_WARNING = "exam_time_warning"
    EXAM_RESULTS_READY = "exam_results_ready"
    EXAM_RANKING_UPDATE = "exam_ranking_update"

    # Learning notifications
    LESSON_PROGRESS = "lesson_progress"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    STUDY_STREAK = "study_streak"
    DAILY_GOAL_ACHIEVED = "daily_goal_achieved"

    # Social notifications
    FRIEND_REQUEST = "friend_request"
    STUDY_GROUP_INVITE = "study_group_invite"
    CHALLENGE_RECEIVED = "challenge_received"

    # Content notifications
    NEW_CONTENT_AVAILABLE = "new_content_available"
    PERSONALIZED_RECOMMENDATION = "personalized_recommendation"

    # Turkish specific
    YKS_ANNOUNCEMENT = "yks_announcement"
    TYT_REMINDER = "tyt_reminder"
    AYT_REMINDER = "ayt_reminder"
    UNIVERSITY_PREFERENCE_REMINDER = "university_preference_reminder"


class NotificationPriority(Enum):
    """Notification priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ConnectionStatus(Enum):
    """WebSocket connection status"""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class NotificationMessage:
    """Real-time notification message"""

    id: str
    type: NotificationType
    title: str
    message: str
    title_tr: str | None = None  # Turkish title
    message_tr: str | None = None  # Turkish message
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    user_id: int | None = None
    session_id: str | None = None
    tags: set[str] = field(default_factory=set)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["type"] = self.type.value
        data["priority"] = self.priority.value
        data["created_at"] = self.created_at.isoformat()
        data["tags"] = list(self.tags)
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        return data

    def is_expired(self) -> bool:
        """Check if notification is expired"""
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at


@dataclass
class WebSocketConnection:
    """WebSocket connection information"""

    id: str
    websocket: Any  # WebSocketServerProtocol when websockets is available
    user_id: int | None
    session_id: str | None
    connected_at: datetime
    last_ping: datetime
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    subscription_filters: dict[str, Any] = field(default_factory=dict)
    message_count: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    async def send_message(self, message: dict[str, Any]) -> bool:
        """Send message to WebSocket connection"""
        try:
            if self.websocket and self.status == ConnectionStatus.CONNECTED:
                await self.websocket.send(json.dumps(message))
                self.message_count += 1
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            self.status = ConnectionStatus.ERROR
            return False

    def matches_filters(self, notification: NotificationMessage) -> bool:
        """Check if notification matches connection filters"""
        # User-specific filter
        if (
            self.user_id
            and notification.user_id
            and self.user_id != notification.user_id
        ):
            return False

        # Session-specific filter
        if (
            self.session_id
            and notification.session_id
            and self.session_id != notification.session_id
        ):
            return False

        # Custom filters
        for filter_key, filter_value in self.subscription_filters.items():
            if filter_key == "notification_types":
                if (
                    isinstance(filter_value, list)
                    and notification.type.value not in filter_value
                ):
                    return False
            elif filter_key == "min_priority":
                priorities = ["low", "normal", "high", "urgent"]
                if priorities.index(notification.priority.value) < priorities.index(
                    filter_value
                ):
                    return False
            elif filter_key == "tags":
                if isinstance(filter_value, list) and not any(
                    tag in notification.tags for tag in filter_value
                ):
                    return False

        return True


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""

    def __init__(self):
        self.connections: dict[str, WebSocketConnection] = {}
        self.user_connections: dict[int, set[str]] = defaultdict(set)
        self.session_connections: dict[str, set[str]] = defaultdict(set)
        self.server = None
        self.running = False
        self.host = getattr(config, "websocket_host", "localhost")
        self.port = getattr(config, "websocket_port", 8765)
        self.ping_interval = 30  # seconds
        self.ping_task = None
        self.metrics_collector = get_metrics_collector()

        # Message history for new connections
        self.message_history: deque = deque(maxlen=1000)

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "uptime_start": datetime.now(UTC),
        }

    async def start_server(self):
        """Start WebSocket server"""
        if not websockets:
            logger.error(
                "WebSockets library not available. Install with: pip install websockets"
            )
            return False

        if self.running:
            return True

        try:
            self.server = await websockets.serve(
                self.handle_connection,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
            )

            self.running = True

            # Start ping task
            self.ping_task = asyncio.create_task(self._ping_loop())

            logger.info(
                f"WebSocket server started on ws://{self.host}:{self.port}",
                message_tr=f"WebSocket sunucusu başlatıldı: ws://{self.host}:{self.port}",
            )

            return True

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False

    async def stop_server(self):
        """Stop WebSocket server"""
        if not self.running:
            return

        self.running = False

        # Cancel ping task
        if self.ping_task:
            self.ping_task.cancel()

        # Close all connections
        await self._close_all_connections()

        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info(
            "WebSocket server stopped", message_tr="WebSocket sunucusu durduruldu"
        )

    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        connection = None

        try:
            # Create connection object
            connection = WebSocketConnection(
                id=connection_id,
                websocket=websocket,
                user_id=None,
                session_id=None,
                connected_at=datetime.now(UTC),
                last_ping=datetime.now(UTC),
            )

            self.connections[connection_id] = connection
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1

            # Send welcome message
            await connection.send_message(
                {
                    "type": "connection_established",
                    "connection_id": connection_id,
                    "message": "WebSocket connection established",
                    "message_tr": "WebSocket bağlantısı kuruldu",
                    "server_time": datetime.now(UTC).isoformat(),
                }
            )

            # Handle messages
            await self._handle_connection_messages(connection)

        except ConnectionClosed:
            logger.debug(f"WebSocket connection {connection_id} closed normally")
        except WebSocketException as e:
            logger.warning(f"WebSocket error for connection {connection_id}: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error in WebSocket connection {connection_id}: {e}"
            )
        finally:
            # Clean up connection
            await self._cleanup_connection(connection_id)

    async def _handle_connection_messages(self, connection: WebSocketConnection):
        """Handle messages from WebSocket connection"""
        async for message in connection.websocket:
            try:
                data = json.loads(message)
                await self._process_client_message(connection, data)
            except json.JSONDecodeError:
                await connection.send_message(
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "message_tr": "Geçersiz JSON formatı",
                    }
                )
            except Exception as e:
                logger.error(f"Error processing client message: {e}")
                await connection.send_message(
                    {
                        "type": "error",
                        "message": "Message processing failed",
                        "message_tr": "Mesaj işleme başarısız",
                    }
                )

    async def _process_client_message(
        self, connection: WebSocketConnection, data: dict[str, Any]
    ):
        """Process message from client"""
        message_type = data.get("type")

        if message_type == "authenticate":
            await self._handle_authentication(connection, data)
        elif message_type == "subscribe":
            await self._handle_subscription(connection, data)
        elif message_type == "unsubscribe":
            await self._handle_unsubscription(connection, data)
        elif message_type == "ping":
            await self._handle_ping(connection, data)
        elif message_type == "get_history":
            await self._handle_history_request(connection, data)
        else:
            await connection.send_message(
                {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "message_tr": f"Bilinmeyen mesaj türü: {message_type}",
                }
            )

    async def _handle_authentication(
        self, connection: WebSocketConnection, data: dict[str, Any]
    ):
        """Handle client authentication with proper token validation"""
        try:
            token = data.get("token")

            # Validate token is provided
            if not token:
                await connection.send_message(
                    {
                        "type": "authentication_error",
                        "message": "Token required for authentication",
                        "message_tr": "Kimlik doğrulama için token gerekli",
                    }
                )
                return

            # Verify token with authentication system
            auth_system = get_auth_system()
            token_payload = auth_system.verify_token(token)

            if not token_payload:
                await connection.send_message(
                    {
                        "type": "authentication_error",
                        "message": "Invalid or expired token",
                        "message_tr": "Geçersiz veya süresi dolmuş token",
                    }
                )
                return

            # Extract user_id from verified token
            user_id = token_payload.get("user_id") or token_payload.get("sub")
            session_id = data.get("session_id") or token_payload.get("session_id")

            if not user_id:
                await connection.send_message(
                    {
                        "type": "authentication_error",
                        "message": "Invalid token payload",
                        "message_tr": "Geçersiz token içeriği",
                    }
                )
                return

            # Update connection with authenticated user
            if user_id:
                # Remove from old user mapping if exists
                if connection.user_id:
                    self.user_connections[connection.user_id].discard(connection.id)

                connection.user_id = user_id
                self.user_connections[user_id].add(connection.id)

            if session_id:
                # Remove from old session mapping if exists
                if connection.session_id:
                    self.session_connections[connection.session_id].discard(
                        connection.id
                    )

                connection.session_id = session_id
                self.session_connections[session_id].add(connection.id)

            await connection.send_message(
                {
                    "type": "authentication_success",
                    "user_id": user_id,
                    "session_id": session_id,
                    "message": "Authentication successful",
                    "message_tr": "Kimlik doğrulama başarılı",
                }
            )

            logger.debug(
                f"WebSocket authenticated: user_id={user_id}, session_id={session_id}"
            )

        except Exception as e:
            await connection.send_message(
                {
                    "type": "authentication_failed",
                    "message": f"Authentication failed: {e}",
                    "message_tr": f"Kimlik doğrulama başarısız: {e}",
                }
            )

    async def _handle_subscription(
        self, connection: WebSocketConnection, data: dict[str, Any]
    ):
        """Handle subscription request"""
        try:
            filters = data.get("filters", {})
            connection.subscription_filters.update(filters)

            await connection.send_message(
                {
                    "type": "subscription_updated",
                    "filters": connection.subscription_filters,
                    "message": "Subscription filters updated",
                    "message_tr": "Abonelik filtreleri güncellendi",
                }
            )

        except Exception as e:
            await connection.send_message(
                {
                    "type": "subscription_failed",
                    "message": f"Subscription failed: {e}",
                    "message_tr": f"Abonelik başarısız: {e}",
                }
            )

    async def _handle_unsubscription(
        self, connection: WebSocketConnection, data: dict[str, Any]
    ):
        """Handle unsubscription request"""
        try:
            filters_to_remove = data.get("filters", [])

            for filter_key in filters_to_remove:
                connection.subscription_filters.pop(filter_key, None)

            await connection.send_message(
                {
                    "type": "unsubscription_success",
                    "remaining_filters": connection.subscription_filters,
                    "message": "Unsubscribed successfully",
                    "message_tr": "Abonelik iptal edildi",
                }
            )

        except Exception as e:
            await connection.send_message(
                {
                    "type": "unsubscription_failed",
                    "message": f"Unsubscription failed: {e}",
                    "message_tr": f"Abonelik iptali başarısız: {e}",
                }
            )

    async def _handle_ping(self, connection: WebSocketConnection, data: dict[str, Any]):
        """Handle ping message"""
        connection.last_ping = datetime.now(UTC)
        await connection.send_message(
            {
                "type": "pong",
                "timestamp": connection.last_ping.isoformat(),
                "message": "pong",
            }
        )

    async def _handle_history_request(
        self, connection: WebSocketConnection, data: dict[str, Any]
    ):
        """Handle request for message history"""
        try:
            limit = min(data.get("limit", 50), 100)  # Max 100 messages

            # Filter history based on connection's filters
            filtered_history = []
            for notification in list(self.message_history)[-limit:]:
                if connection.matches_filters(notification):
                    filtered_history.append(notification.to_dict())

            await connection.send_message(
                {
                    "type": "message_history",
                    "messages": filtered_history,
                    "count": len(filtered_history),
                }
            )

        except Exception as e:
            await connection.send_message(
                {
                    "type": "history_failed",
                    "message": f"History request failed: {e}",
                    "message_tr": f"Geçmiş istek başarısız: {e}",
                }
            )

    async def _ping_loop(self):
        """Send periodic pings to detect dead connections"""
        while self.running:
            try:
                await asyncio.sleep(self.ping_interval)

                current_time = datetime.now(UTC)
                stale_connections = []

                for connection_id, connection in self.connections.items():
                    # Check for stale connections (no ping for 2x ping_interval)
                    if (current_time - connection.last_ping).total_seconds() > (
                        self.ping_interval * 2
                    ):
                        stale_connections.append(connection_id)

                # Remove stale connections
                for connection_id in stale_connections:
                    await self._cleanup_connection(connection_id)
                    logger.debug(f"Removed stale WebSocket connection: {connection_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ping loop error: {e}")

    async def _cleanup_connection(self, connection_id: str):
        """Clean up WebSocket connection"""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return

            # Remove from user mapping
            if connection.user_id:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]

            # Remove from session mapping
            if connection.session_id:
                self.session_connections[connection.session_id].discard(connection_id)
                if not self.session_connections[connection.session_id]:
                    del self.session_connections[connection.session_id]

            # Remove from connections
            del self.connections[connection_id]
            self.stats["active_connections"] -= 1

        except Exception as e:
            logger.error(f"Error cleaning up connection {connection_id}: {e}")

    async def _close_all_connections(self):
        """Close all WebSocket connections"""
        for connection in list(self.connections.values()):
            try:
                await connection.send_message(
                    {
                        "type": "server_shutdown",
                        "message": "Server is shutting down",
                        "message_tr": "Sunucu kapatılıyor",
                    }
                )
                if connection.websocket:
                    await connection.websocket.close()
            except Exception as e:
                logger.error(f"Error closing connection {connection.id}: {e}")

        self.connections.clear()
        self.user_connections.clear()
        self.session_connections.clear()

    async def broadcast_notification(self, notification: NotificationMessage) -> int:
        """Broadcast notification to matching connections"""
        sent_count = 0
        failed_count = 0

        # Add to message history
        self.message_history.append(notification)

        # Send to matching connections
        for connection in list(self.connections.values()):
            try:
                if connection.matches_filters(notification):
                    success = await connection.send_message(
                        {"type": "notification", **notification.to_dict()}
                    )

                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1

            except Exception as e:
                logger.error(
                    f"Error sending notification to connection {connection.id}: {e}"
                )
                failed_count += 1

        # Update statistics
        self.stats["messages_sent"] += sent_count
        self.stats["messages_failed"] += failed_count

        # Record metrics
        self.metrics_collector.record_metric(
            MetricType.WEBSOCKET_MESSAGE_SENT,
            sent_count,
            metadata={"notification_type": notification.type.value},
        )

        if failed_count > 0:
            self.metrics_collector.record_metric(
                MetricType.WEBSOCKET_MESSAGE_FAILED,
                failed_count,
                metadata={"notification_type": notification.type.value},
            )

        return sent_count

    async def send_to_user(
        self, user_id: int, notification: NotificationMessage
    ) -> int:
        """Send notification to specific user"""
        sent_count = 0

        connection_ids = self.user_connections.get(user_id, set())
        for connection_id in connection_ids:
            connection = self.connections.get(connection_id)
            if connection and connection.matches_filters(notification):
                success = await connection.send_message(
                    {"type": "notification", **notification.to_dict()}
                )
                if success:
                    sent_count += 1

        return sent_count

    async def send_to_session(
        self, session_id: str, notification: NotificationMessage
    ) -> int:
        """Send notification to specific session"""
        sent_count = 0

        connection_ids = self.session_connections.get(session_id, set())
        for connection_id in connection_ids:
            connection = self.connections.get(connection_id)
            if connection and connection.matches_filters(notification):
                success = await connection.send_message(
                    {"type": "notification", **notification.to_dict()}
                )
                if success:
                    sent_count += 1

        return sent_count

    def get_stats(self) -> dict[str, Any]:
        """Get WebSocket server statistics"""
        uptime = datetime.now(UTC) - self.stats["uptime_start"]

        return {
            **self.stats,
            "uptime_seconds": uptime.total_seconds(),
            "user_connections_count": len(self.user_connections),
            "session_connections_count": len(self.session_connections),
            "message_history_size": len(self.message_history),
            "running": self.running,
        }


class RealTimeNotificationSystem:
    """Main real-time notification system"""

    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.event_bus = None
        self.message_queue = None
        self.running = False

        # Notification templates for Turkish exam system
        self.notification_templates = self._load_notification_templates()

        # Event handlers
        self.event_handlers = {}

    def _load_notification_templates(self) -> dict[str, dict[str, str]]:
        """Load notification templates for Turkish system"""
        return {
            NotificationType.EXAM_STARTED.value: {
                "title": "Exam Started",
                "title_tr": "Sınav Başladı",
                "message": "Your {exam_type} exam has started. Good luck!",
                "message_tr": "{exam_type} sınavınız başladı. Başarılar!",
            },
            NotificationType.EXAM_TIME_WARNING.value: {
                "title": "Time Warning",
                "title_tr": "Zaman Uyarısı",
                "message": "You have {minutes} minutes left in your {exam_type} exam.",
                "message_tr": "{exam_type} sınavınızda {minutes} dakikanız kaldı.",
            },
            NotificationType.TYT_REMINDER.value: {
                "title": "TYT Exam Reminder",
                "title_tr": "TYT Sınav Hatırlatması",
                "message": "Your TYT exam is scheduled for {exam_date}. Don't forget to prepare!",
                "message_tr": "TYT sınavınız {exam_date} tarihinde. Hazırlanmayı unutmayın!",
            },
            NotificationType.AYT_REMINDER.value: {
                "title": "AYT Exam Reminder",
                "title_tr": "AYT Sınav Hatırlatması",
                "message": "Your AYT exam is scheduled for {exam_date}. Review your subjects!",
                "message_tr": "AYT sınavınız {exam_date} tarihinde. Konularınızı gözden geçirin!",
            },
            NotificationType.ACHIEVEMENT_UNLOCKED.value: {
                "title": "Achievement Unlocked!",
                "title_tr": "Başarı Kazandınız!",
                "message": "Congratulations! You unlocked: {achievement_name}",
                "message_tr": "Tebrikler! Şunu kazandınız: {achievement_name}",
            },
            NotificationType.DAILY_GOAL_ACHIEVED.value: {
                "title": "Daily Goal Achieved",
                "title_tr": "Günlük Hedef Tamamlandı",
                "message": "Well done! You completed your daily study goal.",
                "message_tr": "Aferin! Günlük çalışma hedefinizi tamamladınız.",
            },
        }

    async def initialize(self):
        """Initialize the real-time notification system"""
        try:
            # Get event bus and message queue
            self.event_bus = await get_event_bus()
            self.message_queue = await get_message_queue()

            # Start WebSocket server
            await self.websocket_manager.start_server()

            # Register event handlers
            self._register_event_handlers()

            self.running = True

            logger.info(
                "Real-Time Notification System initialized",
                message_tr="Gerçek Zamanlı Bildirim Sistemi başlatıldı",
            )

        except Exception as e:
            logger.error(f"Real-time notification system initialization failed: {e}")
            raise

    async def shutdown(self):
        """Shutdown the notification system"""
        try:
            self.running = False

            # Stop WebSocket server
            await self.websocket_manager.stop_server()

            logger.info(
                "Real-Time Notification System shut down",
                message_tr="Gerçek Zamanlı Bildirim Sistemi kapatıldı",
            )

        except Exception as e:
            logger.error(f"Notification system shutdown error: {e}")

    def _register_event_handlers(self):
        """Register event handlers for automatic notifications"""

        @self.event_bus.subscribe(EventType.TYT_SIMULATION_STARTED, priority=10)
        async def handle_tyt_started(event: Event):
            await self.send_exam_notification(
                NotificationType.EXAM_STARTED,
                user_id=event.user_id,
                session_id=event.session_id,
                exam_type="TYT",
                **event.data,
            )

        @self.event_bus.subscribe(EventType.AYT_SIMULATION_STARTED, priority=10)
        async def handle_ayt_started(event: Event):
            await self.send_exam_notification(
                NotificationType.EXAM_STARTED,
                user_id=event.user_id,
                session_id=event.session_id,
                exam_type="AYT",
                **event.data,
            )

        @self.event_bus.subscribe(EventType.USER_LOGIN, priority=5)
        async def handle_user_login(event: Event):
            await self.send_notification(
                NotificationType.SYSTEM_ANNOUNCEMENT,
                "Welcome Back!",
                "You have successfully logged in.",
                title_tr="Tekrar Hoşgeldiniz!",
                message_tr="Başarıyla giriş yaptınız.",
                user_id=event.user_id,
                session_id=event.session_id,
                priority=NotificationPriority.LOW,
            )

        logger.debug("Event handlers registered for real-time notifications")

    async def send_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        title_tr: str | None = None,
        message_tr: str | None = None,
        user_id: int | None = None,
        session_id: str | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: dict[str, Any] | None = None,
        tags: set[str] | None = None,
        expires_in_minutes: int | None = None,
    ) -> str:
        """Send a real-time notification"""

        # Create notification
        notification = NotificationMessage(
            id=str(uuid.uuid4()),
            type=notification_type,
            title=title,
            message=message,
            title_tr=title_tr,
            message_tr=message_tr,
            priority=priority,
            data=data or {},
            user_id=user_id,
            session_id=session_id,
            tags=tags or set(),
        )

        # Set expiration
        if expires_in_minutes:
            notification.expires_at = datetime.now(UTC) + timedelta(
                minutes=expires_in_minutes
            )

        # Send notification
        if user_id:
            sent_count = await self.websocket_manager.send_to_user(
                user_id, notification
            )
        elif session_id:
            sent_count = await self.websocket_manager.send_to_session(
                session_id, notification
            )
        else:
            sent_count = await self.websocket_manager.broadcast_notification(
                notification
            )

        logger.debug(f"Sent notification {notification.id} to {sent_count} connections")

        return notification.id

    async def send_exam_notification(
        self,
        notification_type: NotificationType,
        user_id: int,
        exam_type: str,
        session_id: str | None = None,
        **template_vars,
    ) -> str:
        """Send exam-specific notification using templates"""

        template = self.notification_templates.get(notification_type.value, {})
        if not template:
            logger.warning(
                f"No template found for notification type: {notification_type.value}"
            )
            return ""

        # Format template variables
        template_vars.update(
            {
                "exam_type": exam_type.upper(),
                "exam_date": template_vars.get("exam_date", ""),
                "minutes": template_vars.get("minutes_remaining", ""),
                "achievement_name": template_vars.get("achievement", ""),
            }
        )

        title = template["title"].format(**template_vars)
        message = template["message"].format(**template_vars)
        title_tr = template.get("title_tr", "").format(**template_vars)
        message_tr = template.get("message_tr", "").format(**template_vars)

        return await self.send_notification(
            notification_type=notification_type,
            title=title,
            message=message,
            title_tr=title_tr,
            message_tr=message_tr,
            user_id=user_id,
            session_id=session_id,
            priority=NotificationPriority.HIGH,
            data={"exam_type": exam_type, **template_vars},
            tags={f"exam_{exam_type.lower()}", "turkish_exam"},
        )

    async def send_system_announcement(
        self,
        title: str,
        message: str,
        title_tr: str | None = None,
        message_tr: str | None = None,
        priority: NotificationPriority = NotificationPriority.HIGH,
        expires_in_hours: int = 24,
    ) -> str:
        """Send system-wide announcement"""

        return await self.send_notification(
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title=title,
            message=message,
            title_tr=title_tr,
            message_tr=message_tr,
            priority=priority,
            tags={"system", "announcement"},
            expires_in_minutes=expires_in_hours * 60,
        )

    async def send_turkish_exam_reminder(
        self,
        user_id: int,
        exam_type: str,
        exam_date: str,
        reminder_type: str = "24h_before",
    ) -> str:
        """Send Turkish exam reminder"""

        notification_type = (
            NotificationType.TYT_REMINDER
            if exam_type.upper() == "TYT"
            else NotificationType.AYT_REMINDER
        )

        return await self.send_exam_notification(
            notification_type=notification_type,
            user_id=user_id,
            exam_type=exam_type,
            exam_date=exam_date,
            reminder_type=reminder_type,
        )

    def get_connection_stats(self) -> dict[str, Any]:
        """Get real-time connection statistics"""
        return self.websocket_manager.get_stats()

    def get_connected_users(self) -> list[int]:
        """Get list of connected user IDs"""
        return list(self.websocket_manager.user_connections.keys())

    def is_user_connected(self, user_id: int) -> bool:
        """Check if user is connected"""
        return user_id in self.websocket_manager.user_connections

    async def disconnect_user(
        self, user_id: int, reason: str = "admin_disconnect"
    ) -> int:
        """Disconnect all connections for a user"""
        disconnected_count = 0

        connection_ids = list(
            self.websocket_manager.user_connections.get(user_id, set())
        )
        for connection_id in connection_ids:
            connection = self.websocket_manager.connections.get(connection_id)
            if connection:
                try:
                    await connection.send_message(
                        {
                            "type": "forced_disconnect",
                            "reason": reason,
                            "message": "You have been disconnected",
                            "message_tr": "Bağlantınız kesildi",
                        }
                    )
                    if connection.websocket:
                        await connection.websocket.close()
                    disconnected_count += 1
                except Exception as e:
                    logger.error(f"Error disconnecting user {user_id}: {e}")

        return disconnected_count


# Global notification system instance
_notification_system: RealTimeNotificationSystem | None = None


async def get_notification_system() -> RealTimeNotificationSystem:
    """Get global notification system instance"""
    global _notification_system

    if _notification_system is None:
        _notification_system = RealTimeNotificationSystem()
        await _notification_system.initialize()

    return _notification_system


# Utility functions
async def send_realtime_notification(
    notification_type: NotificationType,
    title: str,
    message: str,
    user_id: int | None = None,
    **kwargs,
) -> str:
    """Send a real-time notification"""
    system = await get_notification_system()
    return await system.send_notification(
        notification_type, title, message, user_id=user_id, **kwargs
    )


async def broadcast_system_announcement(
    title: str, message: str, title_tr: str | None = None, message_tr: str | None = None
) -> str:
    """Broadcast system announcement"""
    system = await get_notification_system()
    return await system.send_system_announcement(title, message, title_tr, message_tr)


async def send_exam_reminder(user_id: int, exam_type: str, exam_date: str) -> str:
    """Send exam reminder to user"""
    system = await get_notification_system()
    return await system.send_turkish_exam_reminder(user_id, exam_type, exam_date)


async def notify_exam_started(
    user_id: int, exam_type: str, session_id: str | None = None
) -> str:
    """Notify that exam has started"""
    system = await get_notification_system()
    return await system.send_exam_notification(
        NotificationType.EXAM_STARTED,
        user_id=user_id,
        exam_type=exam_type,
        session_id=session_id,
    )


async def notify_time_warning(
    user_id: int, exam_type: str, minutes_remaining: int, session_id: str | None = None
) -> str:
    """Notify time warning during exam"""
    system = await get_notification_system()
    return await system.send_exam_notification(
        NotificationType.EXAM_TIME_WARNING,
        user_id=user_id,
        exam_type=exam_type,
        session_id=session_id,
        minutes_remaining=minutes_remaining,
    )
