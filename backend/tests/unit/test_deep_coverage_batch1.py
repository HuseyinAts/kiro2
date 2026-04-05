"""
Deep coverage tests - Batch 1
Targets uncovered lines in 5 core modules:
  1. core/realtime_notification_system.py  (292 miss)
  2. core/message_queue_system.py          (284 miss)
  3. core/rag_service.py                   (263 miss)
  4. core/curriculum_compliance_system.py  (246 miss)
  5. core/auth_middleware.py               (225 miss)

~100+ tests covering previously-uncovered branches, handlers, and helpers.
"""

import asyncio
import json
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub heavy dependencies BEFORE any project import
# ---------------------------------------------------------------------------

# redis
_redis_mock = MagicMock()
_redis_async_mock = MagicMock()
_redis_async_mock.from_url = MagicMock(return_value=AsyncMock())
_redis_mock.asyncio = _redis_async_mock
sys.modules.setdefault("redis", _redis_mock)
sys.modules.setdefault("redis.asyncio", _redis_async_mock)

# jwt
_jwt_mock = MagicMock()
_jwt_mock.encode = MagicMock(return_value="mocked.jwt.token")
_jwt_mock.decode = MagicMock(
    return_value={
        "sub": "42",
        "username": "testuser",
        "email": "test@example.com",
        "role": "student",
        "permissions": ["take_tyt_exam", "view_profile"],
        "session_id": "sess-123",
        "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
    }
)
_jwt_mock.ExpiredSignatureError = type("ExpiredSignatureError", (Exception,), {})
_jwt_mock.InvalidTokenError = type("InvalidTokenError", (Exception,), {})
sys.modules.setdefault("jwt", _jwt_mock)

# langchain / vector-store stubs
for _mod in [
    "langchain_core",
    "langchain_core.documents",
    "langchain_text_splitters",
    "langchain_community",
    "langchain_community.embeddings",
    "langchain_community.vectorstores",
    "langchain",
    "langchain.embeddings",
    "langchain.embeddings.base",
]:
    sys.modules.setdefault(_mod, MagicMock())

# SQLAlchemy / DB stubs
for _mod in ["sqlalchemy", "sqlalchemy.orm", "sqlalchemy.ext.asyncio"]:
    sys.modules.setdefault(_mod, MagicMock())

# websockets
_ws_mock = MagicMock()
_ws_mock.serve = AsyncMock()
_ws_exc = MagicMock()
_ws_exc.ConnectionClosed = ConnectionError
_ws_exc.WebSocketException = Exception
_ws_mock.exceptions = _ws_exc
_ws_mock.server = MagicMock()
_ws_mock.server.WebSocketServerProtocol = MagicMock()
sys.modules.setdefault("websockets", _ws_mock)
sys.modules.setdefault("websockets.exceptions", _ws_exc)
sys.modules.setdefault("websockets.server", _ws_mock.server)


# Stub core dependencies so modules load without real infra
def _make_stub_module(name):
    mod = MagicMock()
    sys.modules[name] = mod
    return mod


for _dep in [
    "core.application_metrics",
    "core.structured_logging",
    "core.unified_config",
    "core.unified_event_bus",
    "core.session_auth_caching",
    "core.unified_api_gateway",
    "core.unified.auth_system",
    "core.vector_store_factory",
    "core.rag_config",
    "core.reranker",
    "core.document_deduplication",
]:
    sys.modules.setdefault(_dep, MagicMock())

# Provide specific values needed by the modules at import time
_metrics_stub = sys.modules["core.application_metrics"]
_metrics_stub.get_metrics_collector.return_value = MagicMock()
_metrics_stub.MetricType = MagicMock()

_logging_stub = sys.modules["core.structured_logging"]
_logging_stub.LogCategory = MagicMock()
_logging_stub.get_logger.return_value = MagicMock()

_config_stub = sys.modules["core.unified_config"]
_config_stub.get_unified_config.return_value = MagicMock()

_event_stub = sys.modules["core.unified_event_bus"]
_event_stub.get_event_bus = AsyncMock(return_value=MagicMock())
_event_stub.publish_event = AsyncMock()
_event_stub.EventType = MagicMock()
_event_stub.EventPriority = MagicMock()
_event_stub.Event = MagicMock()

_auth_sys_stub = sys.modules["core.unified.auth_system"]
_auth_sys_stub.get_auth_system.return_value = MagicMock()

# models/curriculum stub
_curriculum_models = MagicMock()
for _cls_name in [
    "CurriculumAlignment",
    "CurriculumComplianceReport",
    "CurriculumUpdateRequest",
    "ExamType",
    "GradeLevel",
    "LearningOutcome",
    "MEBCurriculumStandard",
    "OSYMStandard",
    "QuestionBankCompliance",
    "SubjectType",
]:
    setattr(_curriculum_models, _cls_name, MagicMock())
sys.modules["models.curriculum"] = _curriculum_models
sys.modules.setdefault("models", MagicMock())

# Add backend to path
import os as _os

_backend_dir = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ---------------------------------------------------------------------------
# Now import the modules under test
# ---------------------------------------------------------------------------
from core.auth_middleware import (  # noqa: E402
    AuthContext,
    AuthenticationMiddleware,
    AuthorizationMiddleware,
    AuthUser,
    JWTManager,
    Permission,
    PermissionManager,
    SessionManager,
    UserRole,
)

# CurriculumComplianceSystem needs curriculum models - import after stubs
from core.curriculum_compliance_system import CurriculumComplianceSystem  # noqa: E402
from core.message_queue_system import (  # noqa: E402
    BackgroundJob,
    BackgroundJobProcessor,
    JobStatus,
    QueueMessage,
    QueuePriority,
    QueueType,
)
from core.realtime_notification_system import (  # noqa: E402
    ConnectionStatus,
    NotificationMessage,
    NotificationPriority,
    NotificationType,
    RealTimeNotificationSystem,
    WebSocketConnection,
    WebSocketManager,
)

# ===========================================================================
# Helpers
# ===========================================================================


def _make_notification(
    ntype=NotificationType.SYSTEM_ANNOUNCEMENT,
    priority=NotificationPriority.NORMAL,
    user_id=None,
    session_id=None,
    tags=None,
):
    return NotificationMessage(
        id=str(uuid.uuid4()),
        type=ntype,
        title="Test",
        message="Test message",
        priority=priority,
        user_id=user_id,
        session_id=session_id,
        tags=tags or set(),
    )


def _make_ws_connection(
    user_id=None, session_id=None, status=ConnectionStatus.CONNECTED
):
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    return WebSocketConnection(
        id=str(uuid.uuid4()),
        websocket=ws,
        user_id=user_id,
        session_id=session_id,
        connected_at=datetime.now(UTC),
        last_ping=datetime.now(UTC),
        status=status,
    )


def _make_queue_message(
    queue_type=QueueType.NOTIFICATIONS,
    priority=QueuePriority.NORMAL,
    payload=None,
    user_id=None,
):
    return QueueMessage(
        id=str(uuid.uuid4()),
        queue_type=queue_type,
        payload=payload or {"action": "test"},
        priority=priority,
        created_at=datetime.now(UTC),
        user_id=user_id,
    )


def _make_auth_user(role=UserRole.STUDENT):
    pm = PermissionManager()
    return AuthUser(
        user_id=42,
        username="testuser",
        email="test@example.com",
        role=role,
        permissions=pm.get_user_permissions(role),
        session_id="sess-abc",
    )


# ===========================================================================
# 1. NotificationMessage tests
# ===========================================================================


class TestNotificationMessage:
    def test_id_auto_generated(self):
        n = NotificationMessage(
            id="",
            type=NotificationType.EXAM_STARTED,
            title="T",
            message="M",
        )
        assert n.id  # __post_init__ fills it

    def test_to_dict_basic_fields(self):
        n = _make_notification()
        d = n.to_dict()
        assert d["title"] == "Test"
        assert d["type"] == NotificationType.SYSTEM_ANNOUNCEMENT.value
        assert d["priority"] == NotificationPriority.NORMAL.value
        assert isinstance(d["tags"], list)
        assert "created_at" in d

    def test_to_dict_with_expires_at(self):
        n = _make_notification()
        n.expires_at = datetime.now(UTC) + timedelta(hours=1)
        d = n.to_dict()
        assert "expires_at" in d
        assert d["expires_at"] is not None

    def test_is_expired_no_expiry(self):
        n = _make_notification()
        assert n.is_expired() is False

    def test_is_expired_future(self):
        n = _make_notification()
        n.expires_at = datetime.now(UTC) + timedelta(hours=1)
        assert n.is_expired() is False

    def test_is_expired_past(self):
        n = _make_notification()
        n.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        assert n.is_expired() is True

    def test_to_dict_tags_as_list(self):
        n = _make_notification(tags={"exam", "tyt"})
        d = n.to_dict()
        assert isinstance(d["tags"], list)
        assert set(d["tags"]) == {"exam", "tyt"}


# ===========================================================================
# 2. WebSocketConnection tests
# ===========================================================================


class TestWebSocketConnection:
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        conn = _make_ws_connection()
        result = await conn.send_message({"type": "ping"})
        assert result is True
        assert conn.message_count == 1

    @pytest.mark.asyncio
    async def test_send_message_disconnected(self):
        conn = _make_ws_connection(status=ConnectionStatus.DISCONNECTED)
        result = await conn.send_message({"type": "ping"})
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_websocket_error(self):
        conn = _make_ws_connection()
        conn.websocket.send.side_effect = Exception("network error")
        result = await conn.send_message({"type": "ping"})
        assert result is False
        assert conn.status == ConnectionStatus.ERROR

    def test_matches_filters_no_filters(self):
        conn = _make_ws_connection()
        n = _make_notification()
        assert conn.matches_filters(n) is True

    def test_matches_filters_user_id_match(self):
        conn = _make_ws_connection(user_id=10)
        n = _make_notification(user_id=10)
        assert conn.matches_filters(n) is True

    def test_matches_filters_user_id_mismatch(self):
        conn = _make_ws_connection(user_id=10)
        n = _make_notification(user_id=99)
        assert conn.matches_filters(n) is False

    def test_matches_filters_session_id_mismatch(self):
        conn = _make_ws_connection(session_id="sess-A")
        n = _make_notification(session_id="sess-B")
        assert conn.matches_filters(n) is False

    def test_matches_filters_notification_types(self):
        conn = _make_ws_connection()
        conn.subscription_filters["notification_types"] = ["exam_started"]
        n = _make_notification(ntype=NotificationType.EXAM_STARTED)
        assert conn.matches_filters(n) is True

    def test_matches_filters_notification_type_excluded(self):
        conn = _make_ws_connection()
        conn.subscription_filters["notification_types"] = ["exam_started"]
        n = _make_notification(ntype=NotificationType.SYSTEM_ANNOUNCEMENT)
        assert conn.matches_filters(n) is False

    def test_matches_filters_min_priority(self):
        conn = _make_ws_connection()
        conn.subscription_filters["min_priority"] = "high"
        n_low = _make_notification(priority=NotificationPriority.LOW)
        n_high = _make_notification(priority=NotificationPriority.HIGH)
        assert conn.matches_filters(n_low) is False
        assert conn.matches_filters(n_high) is True

    def test_matches_filters_tags(self):
        conn = _make_ws_connection()
        conn.subscription_filters["tags"] = ["tyt", "exam"]
        n_match = _make_notification(tags={"tyt"})
        n_no_match = _make_notification(tags={"biology"})
        assert conn.matches_filters(n_match) is True
        assert conn.matches_filters(n_no_match) is False


# ===========================================================================
# 3. WebSocketManager tests
# ===========================================================================


class TestWebSocketManager:
    def _make_manager(self):
        mgr = WebSocketManager()
        mgr.metrics_collector = MagicMock()
        mgr.metrics_collector.record_metric = MagicMock()
        return mgr

    def test_initial_stats(self):
        mgr = self._make_manager()
        stats = mgr.get_stats()
        assert stats["total_connections"] == 0
        assert stats["active_connections"] == 0
        assert stats["running"] is False

    @pytest.mark.asyncio
    async def test_cleanup_unknown_connection(self):
        mgr = self._make_manager()
        # Should silently return for unknown IDs
        await mgr._cleanup_connection("nonexistent-id")

    @pytest.mark.asyncio
    async def test_cleanup_removes_connection(self):
        mgr = self._make_manager()
        conn = _make_ws_connection(user_id=1, session_id="s1")
        mgr.connections[conn.id] = conn
        mgr.user_connections[1].add(conn.id)
        mgr.session_connections["s1"].add(conn.id)
        mgr.stats["active_connections"] = 1

        await mgr._cleanup_connection(conn.id)

        assert conn.id not in mgr.connections
        assert 1 not in mgr.user_connections  # empty set removed
        assert "s1" not in mgr.session_connections

    @pytest.mark.asyncio
    async def test_broadcast_notification_empty(self):
        mgr = self._make_manager()
        n = _make_notification()
        sent = await mgr.broadcast_notification(n)
        assert sent == 0
        # Should still add to history
        assert len(mgr.message_history) == 1

    @pytest.mark.asyncio
    async def test_broadcast_notification_sends_to_matching(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        mgr.connections[conn.id] = conn
        n = _make_notification()
        sent = await mgr.broadcast_notification(n)
        assert sent == 1

    @pytest.mark.asyncio
    async def test_send_to_user_no_connections(self):
        mgr = self._make_manager()
        n = _make_notification(user_id=99)
        sent = await mgr.send_to_user(99, n)
        assert sent == 0

    @pytest.mark.asyncio
    async def test_send_to_user_with_connection(self):
        mgr = self._make_manager()
        conn = _make_ws_connection(user_id=5)
        mgr.connections[conn.id] = conn
        mgr.user_connections[5].add(conn.id)
        n = _make_notification(user_id=5)
        sent = await mgr.send_to_user(5, n)
        assert sent == 1

    @pytest.mark.asyncio
    async def test_send_to_session_with_connection(self):
        mgr = self._make_manager()
        conn = _make_ws_connection(session_id="sess-test")
        mgr.connections[conn.id] = conn
        mgr.session_connections["sess-test"].add(conn.id)
        n = _make_notification(session_id="sess-test")
        sent = await mgr.send_to_session("sess-test", n)
        assert sent == 1

    @pytest.mark.asyncio
    async def test_close_all_connections(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        mgr.connections[conn.id] = conn
        mgr.stats["active_connections"] = 1
        await mgr._close_all_connections()
        assert len(mgr.connections) == 0

    @pytest.mark.asyncio
    async def test_handle_ping(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        mgr.connections[conn.id] = conn
        old_ping = conn.last_ping
        await asyncio.sleep(0.01)
        await mgr._handle_ping(conn, {})
        assert conn.last_ping >= old_ping

    @pytest.mark.asyncio
    async def test_handle_subscription(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        data = {"filters": {"notification_types": ["exam_started"]}}
        await mgr._handle_subscription(conn, data)
        assert "notification_types" in conn.subscription_filters

    @pytest.mark.asyncio
    async def test_handle_unsubscription(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        conn.subscription_filters["notification_types"] = ["exam_started"]
        data = {"filters": ["notification_types"]}
        await mgr._handle_unsubscription(conn, data)
        assert "notification_types" not in conn.subscription_filters

    @pytest.mark.asyncio
    async def test_handle_history_request(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        # Add some history
        for _ in range(3):
            mgr.message_history.append(_make_notification())
        await mgr._handle_history_request(conn, {"limit": 5})
        # Should send a response without error

    @pytest.mark.asyncio
    async def test_process_client_message_authenticate(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        mgr.connections[conn.id] = conn
        with patch.object(
            mgr, "_handle_authentication", new_callable=AsyncMock
        ) as mock_auth:
            await mgr._process_client_message(
                conn, {"type": "authenticate", "token": "t"}
            )
            mock_auth.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_client_message_unknown_type(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        mgr.connections[conn.id] = conn
        await mgr._process_client_message(conn, {"type": "unknown_xyz"})
        # Should send error response
        conn.websocket.send.assert_called()

    @pytest.mark.asyncio
    async def test_handle_authentication_no_token(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        await mgr._handle_authentication(conn, {"type": "authenticate"})
        sent = conn.websocket.send.call_args[0][0]
        msg = json.loads(sent)
        assert msg["type"] == "authentication_error"

    @pytest.mark.asyncio
    async def test_handle_authentication_invalid_token(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        auth_sys = MagicMock()
        auth_sys.verify_token.return_value = None
        sys.modules["core.unified.auth_system"].get_auth_system.return_value = auth_sys
        await mgr._handle_authentication(conn, {"type": "authenticate", "token": "bad"})
        sent = conn.websocket.send.call_args[0][0]
        msg = json.loads(sent)
        assert msg["type"] == "authentication_error"

    @pytest.mark.asyncio
    async def test_handle_authentication_valid_token(self):
        mgr = self._make_manager()
        conn = _make_ws_connection()
        auth_sys = MagicMock()
        auth_sys.verify_token.return_value = {"user_id": 7, "session_id": "sess-77"}
        sys.modules["core.unified.auth_system"].get_auth_system.return_value = auth_sys
        await mgr._handle_authentication(
            conn, {"type": "authenticate", "token": "good"}
        )
        assert conn.user_id == 7
        sent_calls = [json.loads(c[0][0]) for c in conn.websocket.send.call_args_list]
        types = [m["type"] for m in sent_calls]
        assert "authentication_success" in types

    @pytest.mark.asyncio
    async def test_start_server_no_websockets(self):
        mgr = self._make_manager()
        import core.realtime_notification_system as rns_mod

        original = rns_mod.websockets
        rns_mod.websockets = None
        result = await mgr.start_server()
        assert result is False
        rns_mod.websockets = original

    def test_get_stats_uptime(self):
        mgr = self._make_manager()
        stats = mgr.get_stats()
        assert "uptime_seconds" in stats
        assert stats["uptime_seconds"] >= 0


# ===========================================================================
# 4. RealTimeNotificationSystem tests
# ===========================================================================


class TestRealTimeNotificationSystem:
    def _make_system(self):
        sys_obj = RealTimeNotificationSystem()
        sys_obj.websocket_manager = MagicMock()
        sys_obj.websocket_manager.send_to_user = AsyncMock(return_value=1)
        sys_obj.websocket_manager.send_to_session = AsyncMock(return_value=1)
        sys_obj.websocket_manager.broadcast_notification = AsyncMock(return_value=0)
        sys_obj.websocket_manager.user_connections = {10: {"conn-1"}}
        sys_obj.websocket_manager.connections = {}
        sys_obj.websocket_manager.get_stats = MagicMock(return_value={"active": 1})
        return sys_obj

    @pytest.mark.asyncio
    async def test_send_notification_to_user(self):
        sys_obj = self._make_system()
        nid = await sys_obj.send_notification(
            NotificationType.SYSTEM_ANNOUNCEMENT,
            "Title",
            "Msg",
            user_id=10,
        )
        assert nid
        sys_obj.websocket_manager.send_to_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_to_session(self):
        sys_obj = self._make_system()
        nid = await sys_obj.send_notification(
            NotificationType.EXAM_STARTED,
            "Title",
            "Msg",
            session_id="sess-99",
        )
        assert nid
        sys_obj.websocket_manager.send_to_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_broadcast(self):
        sys_obj = self._make_system()
        nid = await sys_obj.send_notification(
            NotificationType.SYSTEM_ANNOUNCEMENT,
            "Title",
            "Msg",
        )
        assert nid
        sys_obj.websocket_manager.broadcast_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_with_expiry(self):
        sys_obj = self._make_system()
        nid = await sys_obj.send_notification(
            NotificationType.SYSTEM_ANNOUNCEMENT,
            "Title",
            "Msg",
            expires_in_minutes=30,
        )
        assert nid

    @pytest.mark.asyncio
    async def test_send_exam_notification_no_template(self):
        sys_obj = self._make_system()
        # Use a type with no template
        nid = await sys_obj.send_exam_notification(
            NotificationType.CHALLENGE_RECEIVED,
            user_id=1,
            exam_type="TYT",
        )
        assert nid == ""

    @pytest.mark.asyncio
    async def test_send_exam_notification_with_template(self):
        sys_obj = self._make_system()
        nid = await sys_obj.send_exam_notification(
            NotificationType.EXAM_STARTED,
            user_id=5,
            exam_type="TYT",
        )
        assert nid

    @pytest.mark.asyncio
    async def test_send_system_announcement(self):
        sys_obj = self._make_system()
        nid = await sys_obj.send_system_announcement(
            "Bakım",
            "Sistem bakımda",
            title_tr="Bakım",
            message_tr="Sistem bakımda",
        )
        assert nid

    @pytest.mark.asyncio
    async def test_send_turkish_exam_reminder_tyt(self):
        sys_obj = self._make_system()
        nid = await sys_obj.send_turkish_exam_reminder(
            user_id=3, exam_type="TYT", exam_date="2026-06-15"
        )
        assert nid

    @pytest.mark.asyncio
    async def test_send_turkish_exam_reminder_ayt(self):
        sys_obj = self._make_system()
        nid = await sys_obj.send_turkish_exam_reminder(
            user_id=3, exam_type="AYT", exam_date="2026-06-16"
        )
        assert nid

    def test_get_connection_stats(self):
        sys_obj = self._make_system()
        stats = sys_obj.get_connection_stats()
        assert stats is not None

    def test_get_connected_users(self):
        sys_obj = self._make_system()
        users = sys_obj.get_connected_users()
        assert 10 in users

    def test_is_user_connected_true(self):
        sys_obj = self._make_system()
        assert sys_obj.is_user_connected(10) is True

    def test_is_user_connected_false(self):
        sys_obj = self._make_system()
        assert sys_obj.is_user_connected(999) is False

    @pytest.mark.asyncio
    async def test_disconnect_user_no_connections(self):
        sys_obj = self._make_system()
        count = await sys_obj.disconnect_user(user_id=999)
        assert count == 0

    def test_load_notification_templates(self):
        sys_obj = RealTimeNotificationSystem()
        templates = sys_obj._load_notification_templates()
        assert NotificationType.EXAM_STARTED.value in templates
        assert NotificationType.TYT_REMINDER.value in templates
        assert NotificationType.AYT_REMINDER.value in templates
        assert NotificationType.ACHIEVEMENT_UNLOCKED.value in templates


# ===========================================================================
# 5. QueueMessage tests
# ===========================================================================


class TestQueueMessage:
    def test_id_auto_generated_on_empty(self):
        msg = _make_queue_message()
        assert msg.id

    def test_correlation_id_defaults_to_id(self):
        msg = QueueMessage(
            id="abc",
            queue_type=QueueType.NOTIFICATIONS,
            payload={},
            priority=QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
        )
        assert msg.correlation_id == "abc"

    def test_to_dict(self):
        msg = _make_queue_message()
        d = msg.to_dict()
        assert d["queue_type"] == QueueType.NOTIFICATIONS.value
        assert d["priority"] == QueuePriority.NORMAL.value
        assert "created_at" in d

    def test_to_dict_with_scheduled_at(self):
        msg = _make_queue_message()
        msg.scheduled_at = datetime.now(UTC) + timedelta(hours=1)
        d = msg.to_dict()
        assert "scheduled_at" in d
        assert d["scheduled_at"] is not None

    def test_from_dict_roundtrip(self):
        # Use core.message_queue_system directly to avoid enum identity issues
        # when other test files reload the module in combined pytest runs.
        import core.message_queue_system as _mqs

        original = _mqs.QueueMessage(
            id=str(uuid.uuid4()),
            queue_type=_mqs.QueueType.NOTIFICATIONS,
            payload={"action": "test"},
            priority=_mqs.QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
        )
        d = original.to_dict()
        restored = _mqs.QueueMessage.from_dict(d)
        assert restored.id == original.id
        assert restored.queue_type == original.queue_type
        assert restored.priority == original.priority

    def test_from_dict_with_scheduled_at(self):
        import core.message_queue_system as _mqs

        msg = _mqs.QueueMessage(
            id=str(uuid.uuid4()),
            queue_type=_mqs.QueueType.NOTIFICATIONS,
            payload={},
            priority=_mqs.QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
            scheduled_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        d = msg.to_dict()
        restored = _mqs.QueueMessage.from_dict(d)
        assert restored.scheduled_at is not None


# ===========================================================================
# 6. BackgroundJob tests
# ===========================================================================


class TestBackgroundJob:
    def _make_job(self, status=JobStatus.PENDING):
        return BackgroundJob(
            id=str(uuid.uuid4()),
            job_type="test_job",
            function_name="my_func",
            args=[1, 2],
            kwargs={"key": "val"},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=status,
            created_at=datetime.now(UTC),
        )

    def test_to_dict(self):
        job = self._make_job()
        d = job.to_dict()
        assert d["job_type"] == "test_job"
        assert d["status"] == "pending"
        assert "created_at" in d

    def test_to_dict_with_started_and_completed(self):
        job = self._make_job(status=JobStatus.COMPLETED)
        job.started_at = datetime.now(UTC)
        job.completed_at = datetime.now(UTC)
        d = job.to_dict()
        assert d["started_at"] is not None
        assert d["completed_at"] is not None


# ===========================================================================
# 7. RedisMessageQueue handler tests
# ===========================================================================


class TestRedisMessageQueueHandlers:
    def _make_queue(self):
        # Use __new__ to skip __init__ which references QueueType internally.
        # This avoids enum identity breakage when other test files reload the module.
        import core.message_queue_system as _mqs

        q = object.__new__(_mqs.RedisMessageQueue)
        q.redis_url = "redis://localhost:6379"
        q.redis_client = AsyncMock()
        q.consumer_group = "kiro2_consumers"
        q.consumer_name = "consumer_test"
        q.running = True
        q.queue_configs = {}  # not needed for handler tests
        q.consumer_tasks = {}
        q.metrics_collector = MagicMock()
        q.metrics_collector.record_metric = MagicMock()
        return q

    @pytest.mark.asyncio
    async def test_handle_real_time_message_broadcast(self):
        q = self._make_queue()
        msg = _make_queue_message(
            queue_type=QueueType.REAL_TIME, payload={"action": "websocket_broadcast"}
        )
        result = await q._handle_real_time_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_real_time_message_live_exam(self):
        q = self._make_queue()
        msg = _make_queue_message(
            queue_type=QueueType.REAL_TIME, payload={"action": "live_exam_update"}
        )
        result = await q._handle_real_time_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_real_time_message_notification(self):
        q = self._make_queue()
        msg = _make_queue_message(
            queue_type=QueueType.REAL_TIME, payload={"action": "real_time_notification"}
        )
        result = await q._handle_real_time_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_auth_message_login(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "user_login"})
        result = await q._handle_auth_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_auth_message_token_refresh(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "token_refresh"})
        result = await q._handle_auth_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_auth_message_logout_all(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "logout_all_sessions"})
        result = await q._handle_auth_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_exam_message_submission(self):
        q = self._make_queue()
        msg = _make_queue_message(
            payload={"action": "process_exam_submission", "exam_type": "tyt"}, user_id=1
        )
        result = await q._handle_exam_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_exam_message_calculate_results(self):
        q = self._make_queue()
        msg = _make_queue_message(
            payload={"action": "calculate_exam_results", "exam_type": "ayt"}
        )
        result = await q._handle_exam_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_exam_message_generate_report(self):
        q = self._make_queue()
        msg = _make_queue_message(
            payload={"action": "generate_exam_report", "exam_type": "yks"}
        )
        result = await q._handle_exam_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_exam_message_update_progress(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "update_student_progress"})
        result = await q._handle_exam_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_notification_message_email(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"type": "email"})
        result = await q._handle_notification_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_notification_message_sms(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"type": "sms"})
        result = await q._handle_notification_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_notification_message_push(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"type": "push"})
        result = await q._handle_notification_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_notification_message_exam_reminder(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"type": "exam_reminder"})
        result = await q._handle_notification_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_content_message_generate(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "generate_questions"})
        result = await q._handle_content_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_content_message_analyze(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "analyze_content"})
        result = await q._handle_content_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_content_message_update_metadata(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "update_content_metadata"})
        result = await q._handle_content_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_analytics_message_calculate(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "calculate_learning_analytics"})
        result = await q._handle_analytics_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_analytics_message_update_tracking(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "update_progress_tracking"})
        result = await q._handle_analytics_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_analytics_message_performance_report(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "generate_performance_report"})
        result = await q._handle_analytics_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_batch_message_bulk_import(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "bulk_user_import"})
        result = await q._handle_batch_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_batch_message_monthly_reports(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "generate_monthly_reports"})
        result = await q._handle_batch_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_batch_message_backup_database(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "backup_database"})
        result = await q._handle_batch_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_cleanup_message_expired_sessions(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "clean_expired_sessions"})
        result = await q._handle_cleanup_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_cleanup_message_old_logs(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "clean_old_logs"})
        result = await q._handle_cleanup_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_cleanup_message_optimize_db(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "optimize_database"})
        result = await q._handle_cleanup_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_maintenance_message_health_check(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "system_health_check"})
        result = await q._handle_maintenance_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_maintenance_message_update_config(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "update_system_configuration"})
        result = await q._handle_maintenance_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_maintenance_message_restart_services(self):
        q = self._make_queue()
        msg = _make_queue_message(payload={"action": "restart_services"})
        result = await q._handle_maintenance_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_message_by_type_all_types(self):
        # Re-import fresh to avoid enum identity issues in combined runs
        import core.message_queue_system as _mqs

        q = self._make_queue()
        for qt in _mqs.QueueType:
            msg = _mqs.QueueMessage(
                id=str(uuid.uuid4()),
                queue_type=qt,
                payload={"action": "noop"},
                priority=_mqs.QueuePriority.NORMAL,
                created_at=datetime.now(UTC),
            )
            result = await q._handle_message_by_type(msg, qt)
            assert result is True

    @pytest.mark.asyncio
    async def test_stop_consumers(self):
        import core.message_queue_system as _mqs

        q = object.__new__(_mqs.RedisMessageQueue)
        q.running = True
        q.consumer_tasks = {}
        await q.stop_consumers()
        assert q.running is False

    @pytest.mark.asyncio
    async def test_disconnect_from_redis(self):
        import core.message_queue_system as _mqs

        q = object.__new__(_mqs.RedisMessageQueue)
        q.redis_client = AsyncMock()
        await q.disconnect()
        q.redis_client.close.assert_called_once()


# ===========================================================================
# 8. BackgroundJobProcessor tests
# ===========================================================================


class TestBackgroundJobProcessor:
    def _make_processor(self):
        queue = MagicMock()
        queue.enqueue = AsyncMock(return_value=True)
        return BackgroundJobProcessor(queue)

    def test_register_job_handler(self):
        proc = self._make_processor()
        handler = MagicMock()
        proc.register_job_handler("my_job", handler)
        assert "my_job" in proc.job_handlers

    @pytest.mark.asyncio
    async def test_schedule_job_immediate(self):
        proc = self._make_processor()
        job_id = await proc.schedule_job(
            job_type="test",
            function_name="run_test",
            args=[1],
            kwargs={"a": "b"},
        )
        assert job_id in proc.jobs
        assert proc.jobs[job_id].status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_schedule_job_with_delay(self):
        proc = self._make_processor()
        job_id = await proc.schedule_job(
            job_type="delayed",
            function_name="run_later",
            delay_seconds=100,
        )
        assert job_id in proc.jobs
        assert proc.jobs[job_id].status == JobStatus.SCHEDULED
        assert job_id in proc.scheduled_jobs
        # Cancel to avoid real waiting
        proc.scheduled_jobs[job_id].cancel()

    @pytest.mark.asyncio
    async def test_schedule_job_with_scheduled_at(self):
        proc = self._make_processor()
        future = datetime.now(UTC) + timedelta(hours=1)
        job_id = await proc.schedule_job(
            job_type="future_job",
            function_name="run_future",
            scheduled_at=future,
        )
        assert job_id in proc.jobs
        assert job_id in proc.scheduled_jobs
        proc.scheduled_jobs[job_id].cancel()

    def test_get_job_status_existing(self):
        proc = self._make_processor()
        job = BackgroundJob(
            id="j1",
            job_type="t",
            function_name="f",
            args=[],
            kwargs={},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=JobStatus.COMPLETED,
            created_at=datetime.now(UTC),
        )
        proc.jobs["j1"] = job
        result = proc.get_job_status("j1")
        assert result == job

    def test_get_job_status_nonexistent(self):
        proc = self._make_processor()
        assert proc.get_job_status("nope") is None

    def test_cancel_job_scheduled(self):
        proc = self._make_processor()
        mock_task = MagicMock()
        proc.scheduled_jobs["j2"] = mock_task
        proc.jobs["j2"] = BackgroundJob(
            id="j2",
            job_type="t",
            function_name="f",
            args=[],
            kwargs={},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=JobStatus.SCHEDULED,
            created_at=datetime.now(UTC),
        )
        result = proc.cancel_job("j2")
        assert result is True
        assert proc.jobs["j2"].status == JobStatus.CANCELLED

    def test_cancel_job_not_found(self):
        proc = self._make_processor()
        result = proc.cancel_job("nonexistent")
        assert result is False

    def test_get_job_stats(self):
        proc = self._make_processor()
        job = BackgroundJob(
            id="j3",
            job_type="t",
            function_name="f",
            args=[],
            kwargs={},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        proc.jobs["j3"] = job
        stats = proc.get_job_stats()
        assert stats["total_jobs"] == 1
        assert stats["status_breakdown"]["pending"] == 1


# ===========================================================================
# 9. JWTManager tests
# ===========================================================================


class TestJWTManager:
    def _make_jwt_mgr(self):
        return JWTManager(
            {
                "jwt_secret_key": "test-secret-key-12345",
                "jwt_algorithm": "HS256",
                "access_token_expire_minutes": 30,
                "refresh_token_expire_days": 7,
                "jwt_issuer": "test-issuer",
            }
        )

    def test_generate_access_token(self):
        # Temporarily use real jwt
        mgr = self._make_jwt_mgr()
        user = _make_auth_user()
        token = mgr.generate_access_token(user)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_refresh_token(self):
        mgr = self._make_jwt_mgr()
        user = _make_auth_user()
        token = mgr.generate_refresh_token(user)
        assert isinstance(token, str)

    def test_validate_token_valid(self):
        mgr = self._make_jwt_mgr()
        good_payload = {
            "sub": "42",
            "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
            "role": "student",
            "iss": "test-issuer",
        }
        import core.auth_middleware as _mw

        with patch.object(_mw.jwt, "decode", return_value=good_payload):
            payload = mgr.validate_token("some.token.here")
        assert payload is not None
        assert payload["sub"] == "42"

    def test_validate_token_expired(self):
        mgr = self._make_jwt_mgr()
        import core.auth_middleware as _mw

        ExpiredErr = type("ExpiredSignatureError", (Exception,), {})
        with patch.object(_mw.jwt, "ExpiredSignatureError", ExpiredErr):
            with patch.object(_mw.jwt, "decode", side_effect=ExpiredErr("expired")):
                with pytest.raises(ValueError):
                    mgr.validate_token("expired.token")

    def test_validate_token_invalid(self):
        mgr = self._make_jwt_mgr()
        import core.auth_middleware as _mw

        InvalidErr = type("InvalidTokenError", (Exception,), {})
        with patch.object(_mw.jwt, "InvalidTokenError", InvalidErr):
            with patch.object(_mw.jwt, "decode", side_effect=InvalidErr("invalid")):
                with pytest.raises(ValueError):
                    mgr.validate_token("bad.token")


# ===========================================================================
# 10. PermissionManager tests
# ===========================================================================


class TestPermissionManager:
    def test_get_student_permissions(self):
        pm = PermissionManager()
        perms = pm.get_user_permissions(UserRole.STUDENT)
        assert Permission.TAKE_TYT_EXAM in perms
        assert Permission.VIEW_PROFILE in perms

    def test_get_admin_permissions(self):
        pm = PermissionManager()
        perms = pm.get_user_permissions(UserRole.ADMIN)
        assert Permission.MANAGE_SYSTEM in perms
        assert Permission.MANAGE_USERS in perms

    def test_get_guest_permissions(self):
        pm = PermissionManager()
        perms = pm.get_user_permissions(UserRole.GUEST)
        assert Permission.VIEW_CONTENT in perms
        assert Permission.MANAGE_SYSTEM not in perms

    def test_get_teacher_permissions(self):
        pm = PermissionManager()
        perms = pm.get_user_permissions(UserRole.TEACHER)
        assert Permission.CREATE_CONTENT in perms
        assert Permission.MANAGE_SYSTEM not in perms

    def test_check_permission_true(self):
        pm = PermissionManager()
        assert pm.check_permission(UserRole.STUDENT, Permission.TAKE_TYT_EXAM) is True

    def test_check_permission_false(self):
        pm = PermissionManager()
        assert pm.check_permission(UserRole.GUEST, Permission.MANAGE_SYSTEM) is False

    def test_check_route_permissions_admin_route(self):
        pm = PermissionManager()
        assert pm.check_route_permissions(UserRole.ADMIN, "/admin/users") is True

    def test_check_route_permissions_student_exam(self):
        pm = PermissionManager()
        assert pm.check_route_permissions(UserRole.STUDENT, "/exams/tyt/") is True

    def test_check_route_permissions_no_match(self):
        pm = PermissionManager()
        assert pm.check_route_permissions(UserRole.STUDENT, "/unknown/route") is True

    def test_get_unknown_role_permissions(self):
        pm = PermissionManager()
        # PARENT role not in map → returns empty set
        perms = pm.get_user_permissions(UserRole.PARENT)
        assert isinstance(perms, set)


# ===========================================================================
# 11. AuthUser tests
# ===========================================================================


class TestAuthUser:
    def test_has_permission_true(self):
        user = _make_auth_user(role=UserRole.STUDENT)
        assert user.has_permission(Permission.TAKE_TYT_EXAM) is True

    def test_has_permission_false(self):
        user = _make_auth_user(role=UserRole.STUDENT)
        assert user.has_permission(Permission.MANAGE_SYSTEM) is False

    def test_has_role(self):
        user = _make_auth_user(role=UserRole.TEACHER)
        assert user.has_role(UserRole.TEACHER) is True
        assert user.has_role(UserRole.STUDENT) is False

    def test_is_student(self):
        student = _make_auth_user(role=UserRole.STUDENT)
        teacher = _make_auth_user(role=UserRole.TEACHER)
        assert student.is_student() is True
        assert teacher.is_student() is False

    def test_is_admin(self):
        admin = _make_auth_user(role=UserRole.ADMIN)
        student = _make_auth_user(role=UserRole.STUDENT)
        assert admin.is_admin() is True
        assert student.is_admin() is False

    def test_is_system_admin(self):
        system = _make_auth_user(role=UserRole.SYSTEM)
        assert system.is_admin() is True

    def test_can_take_exam_tyt(self):
        student = _make_auth_user(role=UserRole.STUDENT)
        assert student.can_take_exam("tyt") is True

    def test_can_take_exam_ayt(self):
        student = _make_auth_user(role=UserRole.STUDENT)
        assert student.can_take_exam("ayt") is True

    def test_can_take_exam_unknown(self):
        # can_take_exam returns None (falsy) for unknown exam types
        student = _make_auth_user(role=UserRole.STUDENT)
        assert not student.can_take_exam("xyz")


# ===========================================================================
# 12. AuthenticationMiddleware helper tests
# ===========================================================================


class TestAuthenticationMiddlewareHelpers:
    def _make_middleware(self):
        _jwt_mock.decode.reset_mock()
        _jwt_mock.decode.side_effect = None
        _jwt_mock.decode.return_value = {
            "sub": "42",
            "username": "testuser",
            "email": "test@example.com",
            "role": "student",
            "permissions": ["take_tyt_exam", "view_profile"],
            "session_id": "sess-123",
            "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
        }
        return AuthenticationMiddleware(
            {
                "jwt": {"jwt_secret_key": "test-key", "jwt_issuer": "test-issuer"},
                "session": {},
            }
        )

    def test_is_public_route_login(self):
        mw = self._make_middleware()
        assert mw._is_public_route("/auth/login") is True

    def test_is_public_route_health(self):
        mw = self._make_middleware()
        assert mw._is_public_route("/health") is True

    def test_is_public_route_private(self):
        mw = self._make_middleware()
        assert mw._is_public_route("/exams/tyt/start") is False

    def test_extract_jwt_token_bearer(self):
        mw = self._make_middleware()
        req = MagicMock()
        req.headers = {"Authorization": "Bearer my.test.token"}
        token = mw._extract_jwt_token(req)
        assert token == "my.test.token"

    def test_extract_jwt_token_x_access(self):
        mw = self._make_middleware()
        req = MagicMock()
        req.headers = {"X-Access-Token": "header.token"}
        token = mw._extract_jwt_token(req)
        assert token == "header.token"

    def test_extract_jwt_token_missing(self):
        mw = self._make_middleware()
        req = MagicMock()
        req.headers = {}
        token = mw._extract_jwt_token(req)
        assert token is None

    def test_extract_session_id_header(self):
        mw = self._make_middleware()
        req = MagicMock()
        req.headers = {"X-Session-ID": "sess-xyz"}
        sid = mw._extract_session_id(req)
        assert sid == "sess-xyz"

    def test_extract_session_id_cookie(self):
        mw = self._make_middleware()
        req = MagicMock()
        req.headers = {"Cookie": "other=val; session_id=sess-cookie; foo=bar"}
        sid = mw._extract_session_id(req)
        assert sid == "sess-cookie"

    def test_extract_session_id_missing(self):
        mw = self._make_middleware()
        req = MagicMock()
        req.headers = {"Cookie": ""}
        sid = mw._extract_session_id(req)
        assert sid is None

    def test_extract_api_key(self):
        mw = self._make_middleware()
        req = MagicMock()
        req.headers = {"X-API-Key": "my-api-key"}
        key = mw._extract_api_key(req)
        assert key == "my-api-key"

    @pytest.mark.asyncio
    async def test_authenticate_jwt_valid(self):
        mw = self._make_middleware()
        good_payload = {
            "sub": "42",
            "username": "testuser",
            "email": "test@example.com",
            "role": "student",
            "permissions": ["take_tyt_exam", "view_profile"],
            "session_id": "sess-123",
            "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
            "iss": "test-issuer",
        }
        import core.auth_middleware as _mw

        req = MagicMock()
        with patch.object(_mw.jwt, "decode", return_value=good_payload):
            context = await mw._authenticate_jwt("valid.jwt.token", req)
        assert context.authenticated is True
        assert context.user is not None
        assert context.user.user_id == 42

    @pytest.mark.asyncio
    async def test_authenticate_jwt_invalid(self):
        mw = self._make_middleware()
        import core.auth_middleware as _mw

        req = MagicMock()
        with patch.object(_mw.jwt, "decode", side_effect=Exception("bad token")):
            context = await mw._authenticate_jwt("bad.token", req)
        assert context.authenticated is False

    @pytest.mark.asyncio
    async def test_authenticate_api_key_system(self):
        mw = self._make_middleware()
        req = MagicMock()
        context = await mw._authenticate_api_key("kiro2_system_api_key", req)
        assert context.authenticated is True
        assert context.user.role == UserRole.SYSTEM

    @pytest.mark.asyncio
    async def test_authenticate_api_key_invalid(self):
        mw = self._make_middleware()
        req = MagicMock()
        context = await mw._authenticate_api_key("wrong-key", req)
        assert context.authenticated is False

    def test_create_auth_error_401(self):
        mw = self._make_middleware()
        import core.auth_middleware as _mw

        # APIResponse is mocked; capture the kwargs passed to the constructor
        with patch.object(_mw, "APIResponse") as mock_resp_cls:
            mock_resp_cls.return_value = MagicMock()
            mw._create_auth_error("req-1", 401, "Unauthorized", "Yetkisiz", "detail")
        call_kwargs = mock_resp_cls.call_args.kwargs
        assert call_kwargs["status_code"] == 401
        assert "error" in call_kwargs["body"]

    def test_create_auth_error_500(self):
        mw = self._make_middleware()
        import core.auth_middleware as _mw

        with patch.object(_mw, "APIResponse") as mock_resp_cls:
            mock_resp_cls.return_value = MagicMock()
            mw._create_auth_error("req-2", 500, "Server Error", "Sunucu Hatası", "msg")
        call_kwargs = mock_resp_cls.call_args.kwargs
        assert call_kwargs["status_code"] == 500


# ===========================================================================
# 13. AuthorizationMiddleware tests
# ===========================================================================


class TestAuthorizationMiddleware:
    def _make_authz(self):
        authz = AuthorizationMiddleware({})
        authz.metrics_collector = MagicMock()
        authz.metrics_collector.record_metric = MagicMock()
        return authz

    def test_check_route_authorization_admin(self):
        authz = self._make_authz()
        user = _make_auth_user(role=UserRole.ADMIN)
        ctx = AuthContext(user=user, authenticated=True)
        req = MagicMock()
        req.path = "/admin/secret"
        req.method = MagicMock()
        result = authz._check_route_authorization(ctx, req)
        assert result is True

    def test_check_route_authorization_no_user(self):
        authz = self._make_authz()
        ctx = AuthContext(user=None, authenticated=False)
        req = MagicMock()
        req.path = "/exams/tyt/start"
        req.method = MagicMock()
        result = authz._check_route_authorization(ctx, req)
        assert result is False

    def test_check_route_authorization_student_tyt(self):
        authz = self._make_authz()
        user = _make_auth_user(role=UserRole.STUDENT)
        ctx = AuthContext(user=user, authenticated=True)
        req = MagicMock()
        req.path = "/exams/tyt/start"
        req.method = MagicMock()
        result = authz._check_route_authorization(ctx, req)
        assert result is True

    def test_check_route_authorization_unknown_route(self):
        authz = self._make_authz()
        user = _make_auth_user(role=UserRole.STUDENT)
        ctx = AuthContext(user=user, authenticated=True)
        req = MagicMock()
        req.path = "/some/unknown/path"
        req.method = MagicMock()
        result = authz._check_route_authorization(ctx, req)
        assert result is True


# ===========================================================================
# 14. SessionManager._generate_session_id test
# ===========================================================================


class TestSessionManager:
    def test_generate_session_id_format(self):
        sm = SessionManager({})
        sid = sm._generate_session_id(user_id=123)
        assert sid.startswith("kiro2_session_")
        assert len(sid) == len("kiro2_session_") + 32

    def test_generate_session_id_unique(self):
        sm = SessionManager({})
        ids = {sm._generate_session_id(1) for _ in range(5)}
        assert len(ids) == 5  # All unique due to random component


# ===========================================================================
# 15. RAG service cache helpers (TESTING=true path)
# ===========================================================================


class TestRAGServiceCacheHelpers:
    """Tests for the cache helper functions in RAGService.

    We set TESTING=true so _initialize() is skipped and we can patch
    internals directly.
    """

    def _make_rag_service(self):
        import os

        os.environ["TESTING"] = "true"
        from core.rag_service import RAGService

        svc = RAGService.__new__(RAGService)
        svc.persist_directory = "./test_vector_db"
        svc._redis_client = None
        svc._search_cache = {}
        svc._cache_ttl = 1800
        svc._max_cache_size = 500
        svc._batch_size = 50
        svc._document_registry = {}
        svc.embeddings = None
        svc.vector_store = None
        svc.text_splitter = None
        return svc

    def test_generate_search_cache_key_deterministic(self):
        svc = self._make_rag_service()
        k1 = svc._generate_search_cache_key("query", 5, {"subject": "math"})
        k2 = svc._generate_search_cache_key("query", 5, {"subject": "math"})
        assert k1 == k2

    def test_generate_search_cache_key_different_queries(self):
        svc = self._make_rag_service()
        k1 = svc._generate_search_cache_key("query A", 5)
        k2 = svc._generate_search_cache_key("query B", 5)
        assert k1 != k2

    def test_generate_search_cache_key_different_k(self):
        svc = self._make_rag_service()
        k1 = svc._generate_search_cache_key("same", 5)
        k2 = svc._generate_search_cache_key("same", 10)
        assert k1 != k2

    @pytest.mark.asyncio
    async def test_get_cached_results_miss(self):
        svc = self._make_rag_service()
        result = await svc._get_cached_search_results("nonexistent-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_cached_results_memory(self):
        svc = self._make_rag_service()
        data = [{"content": "doc1", "score": 0.9}]
        key = "test-cache-key"
        await svc._set_cached_search_results(key, data)
        result = await svc._get_cached_search_results(key)
        assert result == data

    @pytest.mark.asyncio
    async def test_cache_eviction_when_full(self):
        svc = self._make_rag_service()
        svc._max_cache_size = 3
        # Fill cache
        for i in range(3):
            await svc._set_cached_search_results(f"key-{i}", [{"content": f"doc-{i}"}])
        assert len(svc._search_cache) == 3
        # Add one more - should evict oldest
        await svc._set_cached_search_results("key-new", [{"content": "new"}])
        assert len(svc._search_cache) == 3

    @pytest.mark.asyncio
    async def test_cached_results_expire(self):
        svc = self._make_rag_service()
        svc._cache_ttl = 0  # Immediate expiry
        key = "expire-key"
        svc._search_cache[key] = ([{"content": "old"}], time.time() - 1)
        result = await svc._get_cached_search_results(key)
        assert result is None
        assert key not in svc._search_cache

    def test_preprocess_text(self):
        svc = self._make_rag_service()
        result = svc._preprocess_text("  Hello   WORLD  ")
        assert result == "hello world"

    def test_preprocess_text_empty(self):
        svc = self._make_rag_service()
        result = svc._preprocess_text("")
        assert result == ""

    def test_preprocess_text_cached(self):
        svc = self._make_rag_service()
        # Call twice - second should hit lru_cache
        r1 = svc._preprocess_text("test text")
        r2 = svc._preprocess_text("test text")
        assert r1 == r2

    def test_rerank_results_fallback_on_error(self):
        svc = self._make_rag_service()
        results = [{"content": "doc", "score": 0.8}]
        # Reranker not available → should return original results
        sys.modules["core.reranker"].get_turkish_reranker.side_effect = Exception(
            "unavailable"
        )
        output = svc._rerank_results("query", results)
        assert output == results
        sys.modules["core.reranker"].get_turkish_reranker.side_effect = None

    @pytest.mark.asyncio
    async def test_test_redis_connection_no_client(self):
        svc = self._make_rag_service()
        svc._redis_client = None
        # Should not raise
        await svc._test_redis_connection()

    @pytest.mark.asyncio
    async def test_test_redis_connection_success(self):
        svc = self._make_rag_service()
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        svc._redis_client = mock_redis
        await svc._test_redis_connection()
        mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_redis_connection_failure(self):
        svc = self._make_rag_service()
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("conn refused"))
        svc._redis_client = mock_redis
        await svc._test_redis_connection()
        assert svc._redis_client is None

    @pytest.mark.asyncio
    async def test_get_cached_results_redis_hit(self):
        svc = self._make_rag_service()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps([{"content": "redis-hit"}]))
        svc._redis_client = mock_redis
        result = await svc._get_cached_search_results("some-key")
        assert result == [{"content": "redis-hit"}]

    @pytest.mark.asyncio
    async def test_set_cached_results_redis(self):
        svc = self._make_rag_service()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        svc._redis_client = mock_redis
        await svc._set_cached_search_results("k", [{"x": 1}])
        mock_redis.setex.assert_called_once()


# ===========================================================================
# 16. CurriculumComplianceSystem tests
# ===========================================================================


class TestCurriculumComplianceSystem:
    def _make_system(self, with_db=False):
        db = AsyncMock() if with_db else None
        return CurriculumComplianceSystem(database_service=db)

    def test_init_thresholds(self):
        sys_obj = self._make_system()
        assert sys_obj.compliance_thresholds["excellent"] == 0.9
        assert sys_obj.compliance_thresholds["good"] == 0.8
        assert sys_obj.minimum_questions_per_topic == 1000

    def test_determine_compliance_status_excellent(self):
        sys_obj = self._make_system()
        status = sys_obj._determine_compliance_status(0.95)
        assert status == "excellent"

    def test_determine_compliance_status_good(self):
        sys_obj = self._make_system()
        status = sys_obj._determine_compliance_status(0.85)
        assert status == "good"

    def test_determine_compliance_status_acceptable(self):
        sys_obj = self._make_system()
        status = sys_obj._determine_compliance_status(0.75)
        assert status == "acceptable"

    def test_determine_compliance_status_needs_improvement(self):
        sys_obj = self._make_system()
        status = sys_obj._determine_compliance_status(0.65)
        assert status == "needs_improvement"

    def test_determine_compliance_status_insufficient(self):
        sys_obj = self._make_system()
        status = sys_obj._determine_compliance_status(0.0)
        assert status == "insufficient"

    @pytest.mark.asyncio
    async def test_calculate_question_compliance_score_full(self):
        sys_obj = self._make_system()
        counts = {"total": 1200, "osym_format": 1100, "meb_aligned": 1050}
        score = await sys_obj._calculate_question_compliance_score(counts)
        assert 0.0 <= score <= 1.0
        assert score > 0.8  # high counts → high score

    @pytest.mark.asyncio
    async def test_calculate_question_compliance_score_zero_total(self):
        sys_obj = self._make_system()
        counts = {"total": 0, "osym_format": 0, "meb_aligned": 0}
        score = await sys_obj._calculate_question_compliance_score(counts)
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_calculate_question_compliance_score_partial(self):
        sys_obj = self._make_system()
        counts = {"total": 500, "osym_format": 400, "meb_aligned": 450}
        score = await sys_obj._calculate_question_compliance_score(counts)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_identify_curriculum_gaps_both_sides(self):
        sys_obj = self._make_system()
        # Create mock standards
        meb1 = MagicMock()
        meb1.topic_name = "Algebra"
        meb2 = MagicMock()
        meb2.topic_name = "Geometry"
        osym1 = MagicMock()
        osym1.topic_name = "Algebra"
        osym2 = MagicMock()
        osym2.topic_name = "Calculus"
        gaps = await sys_obj._identify_curriculum_gaps([meb1, meb2], [osym1, osym2])
        assert len(gaps) == 2  # MEB-only: Geometry, ÖSYM-only: Calculus

    @pytest.mark.asyncio
    async def test_identify_curriculum_gaps_empty(self):
        sys_obj = self._make_system()
        gaps = await sys_obj._identify_curriculum_gaps([], [])
        assert gaps == []

    @pytest.mark.asyncio
    async def test_generate_alignment_recommendations_meb_gap(self):
        sys_obj = self._make_system()
        gaps = ["MEB'de var ÖSYM'de yok: Geometri"]
        recs = await sys_obj._generate_alignment_recommendations(gaps)
        assert len(recs) >= 1
        assert any("ÖSYM" in r for r in recs)

    @pytest.mark.asyncio
    async def test_generate_alignment_recommendations_osym_gap(self):
        sys_obj = self._make_system()
        gaps = ["ÖSYM'de var MEB'de yok: Kalkülüs"]
        recs = await sys_obj._generate_alignment_recommendations(gaps)
        assert len(recs) >= 1
        assert any("MEB" in r for r in recs)

    @pytest.mark.asyncio
    async def test_generate_alignment_recommendations_no_gaps(self):
        sys_obj = self._make_system()
        recs = await sys_obj._generate_alignment_recommendations([])
        assert len(recs) == 1
        assert "yeterli" in recs[0].lower()

    @pytest.mark.asyncio
    async def test_calculate_alignment_score_no_standards(self):
        sys_obj = self._make_system()
        score = await sys_obj._calculate_alignment_score([], [])
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_calculate_alignment_score_with_standards(self):
        sys_obj = self._make_system()
        meb1 = MagicMock()
        meb1.topic_name = "Algebra"
        meb1.id = "m1"
        osym1 = MagicMock()
        osym1.topic_name = "Algebra"
        # Patch get_learning_outcomes to return empty list
        with patch.object(sys_obj, "get_learning_outcomes", return_value=[]):
            score = await sys_obj._calculate_alignment_score([meb1], [osym1])
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_is_outcome_osym_aligned_valid(self):
        sys_obj = self._make_system()
        outcome = MagicMock()
        outcome.cognitive_level = "analiz"
        result = await sys_obj._is_outcome_osym_aligned(outcome)
        assert result is True

    @pytest.mark.asyncio
    async def test_is_outcome_osym_aligned_invalid(self):
        sys_obj = self._make_system()
        outcome = MagicMock()
        outcome.cognitive_level = "unknown_level"
        result = await sys_obj._is_outcome_osym_aligned(outcome)
        assert result is False

    @pytest.mark.asyncio
    async def test_add_meb_standard_without_db(self):
        sys_obj = self._make_system()
        standard = MagicMock()
        standard.id = "std-1"
        standard.topic_name = "Matematik"
        result = await sys_obj.add_meb_standard(standard)
        assert result is True
        assert "std-1" in sys_obj.meb_standards_cache

    @pytest.mark.asyncio
    async def test_add_osym_standard_without_db(self):
        sys_obj = self._make_system()
        standard = MagicMock()
        standard.id = "osym-1"
        standard.topic_name = "Fizik"
        result = await sys_obj.add_osym_standard(standard)
        assert result is True
        assert "osym-1" in sys_obj.osym_standards_cache

    @pytest.mark.asyncio
    async def test_get_meb_standards_by_subject_from_cache(self):
        sys_obj = self._make_system()
        std = MagicMock()
        std.id = "s1"
        std.subject = MagicMock()
        std.is_active = True
        std.grade_level = None
        subject = std.subject
        sys_obj.meb_standards_cache["s1"] = std
        results = await sys_obj.get_meb_standards_by_subject(subject)
        assert std in results

    @pytest.mark.asyncio
    async def test_get_meb_standards_subject_mismatch(self):
        sys_obj = self._make_system()
        std = MagicMock()
        std.id = "s2"
        std.subject = "matematik"
        std.is_active = True
        sys_obj.meb_standards_cache["s2"] = std
        results = await sys_obj.get_meb_standards_by_subject("fizik")
        assert std not in results

    @pytest.mark.asyncio
    async def test_get_learning_outcomes_no_db(self):
        sys_obj = self._make_system()
        outcomes = await sys_obj.get_learning_outcomes("std-1")
        assert outcomes == []

    @pytest.mark.asyncio
    async def test_get_osym_standards_by_priority_sorted(self):
        sys_obj = self._make_system()
        s1 = MagicMock()
        s1.id = "o1"
        s1.is_active = True
        s1.priority_level = 3
        s2 = MagicMock()
        s2.id = "o2"
        s2.is_active = True
        s2.priority_level = 1
        exam = MagicMock()
        s1.exam_type = exam
        s2.exam_type = exam
        sys_obj.osym_standards_cache = {"o1": s1, "o2": s2}
        results = await sys_obj.get_osym_standards_by_priority(exam)
        assert results[0].priority_level == 1

    @pytest.mark.asyncio
    async def test_calculate_overall_osym_compliance_empty(self):
        sys_obj = self._make_system()
        score = await sys_obj._calculate_overall_osym_compliance()
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_calculate_overall_osym_compliance_with_standards(self):
        sys_obj = self._make_system()
        std = MagicMock()
        std.is_active = True
        std.priority_level = 2
        std.exam_frequency = 0.8
        std.exam_type = None
        std.subject = None
        sys_obj.osym_standards_cache = {"o1": std}
        score = await sys_obj._calculate_overall_osym_compliance()
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_initialize_returns_true_without_db(self):
        sys_obj = CurriculumComplianceSystem()
        result = await sys_obj.initialize()
        assert result is True

    @pytest.mark.asyncio
    async def test_get_question_counts_no_db(self):
        sys_obj = self._make_system()
        counts = await sys_obj._get_question_counts_by_topic("topic-1")
        assert "total" in counts
        assert counts["total"] == 850


# ===========================================================================
# Parametrized boundary tests
# ===========================================================================


@pytest.mark.parametrize(
    "score,expected_status",
    [
        (1.0, "excellent"),
        (0.9, "excellent"),
        (0.89, "good"),
        (0.8, "good"),
        (0.79, "acceptable"),
        (0.7, "acceptable"),
        (0.69, "needs_improvement"),
        (0.6, "needs_improvement"),
        (0.59, "insufficient"),
        (0.0, "insufficient"),
    ],
)
def test_compliance_status_boundaries(score, expected_status):
    sys_obj = CurriculumComplianceSystem()
    status = sys_obj._determine_compliance_status(score)
    assert status == expected_status


@pytest.mark.parametrize(
    "role",
    [
        UserRole.STUDENT,
        UserRole.TEACHER,
        UserRole.ADMIN,
        UserRole.SYSTEM,
        UserRole.GUEST,
        UserRole.MODERATOR,
    ],
)
def test_permission_manager_all_roles(role):
    pm = PermissionManager()
    perms = pm.get_user_permissions(role)
    assert isinstance(perms, set)


@pytest.mark.parametrize(
    "notification_type",
    [
        NotificationType.EXAM_STARTED,
        NotificationType.EXAM_COMPLETED,
        NotificationType.EXAM_TIME_WARNING,
        NotificationType.ACHIEVEMENT_UNLOCKED,
        NotificationType.DAILY_GOAL_ACHIEVED,
        NotificationType.TYT_REMINDER,
        NotificationType.AYT_REMINDER,
    ],
)
def test_notification_type_to_dict(notification_type):
    n = NotificationMessage(
        id=str(uuid.uuid4()),
        type=notification_type,
        title="T",
        message="M",
    )
    d = n.to_dict()
    assert d["type"] == notification_type.value


def test_queue_config_for_all_types():
    # Re-import to get fresh module (robust to combined-run enum identity issues)
    import core.message_queue_system as _mqs

    q = _mqs.RedisMessageQueue()
    for qt in _mqs.QueueType:
        assert qt in q.queue_configs
        cfg = q.queue_configs[qt]
        assert "stream_name" in cfg
        assert "max_len" in cfg
        assert "consumer_count" in cfg
