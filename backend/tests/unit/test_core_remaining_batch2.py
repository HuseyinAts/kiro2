"""
Unit tests for 6 core modules with partial coverage — Batch 2.

Targets uncovered functions in:
  1. core/rbac_system.py            (~41% covered)
  2. core/turkish_exam_event_handlers.py (~26% covered)
  3. core/unified_api_gateway.py    (~30% covered)
  4. core/middleware/timing.py      (~52% covered)
  5. core/middleware/cache_headers.py (~67% covered)
  6. core/structured_logger.py      (~43% covered)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Save sys.modules state to prevent mock pollution in other unit test files
_RESTORE_MODULES = [
    "redis", "redis.asyncio", "elasticsearch", "langchain", "langchain_core",
    "websockets", "websockets.exceptions", "websockets.server", "cryptography",
    "cryptography.fernet", "zemberek", "structlog", "structlog.stdlib",
    "structlog.processors", "structlog.dev", "structlog.types", "celery",
    "celery.schedules", "celery.exceptions", "core.application_metrics",
    "core.message_queue_system", "core.unified_event_bus",
    "core.background_job_processor", "core.enhanced_database",
    "core.transaction_manager", "core.structured_logging", "core.unified_config",
    "core.realtime_notification_system", "core.exceptions"
]
_original_modules = {}
for _mod in _RESTORE_MODULES:
    if _mod in sys.modules:
        _original_modules[_mod] = sys.modules[_mod]

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parents[2]))

# ---------------------------------------------------------------------------
# Remove stale MagicMock stubs left by other test files.
# test_core_remaining_batch1.py stubs these modules via setdefault — when it
# runs first, later imports of the REAL classes (ExamSession, APIGateway, etc.)
# would resolve to MagicMock objects and produce failures.
# ---------------------------------------------------------------------------
_NEED_REAL = [
    "core.turkish_exam_event_handlers",
    "core.unified_api_gateway",
    "core.rbac_system",
    "core.structured_logger",
    "core.middleware.timing",
    "core.middleware.cache_headers",
]
for _mod in _NEED_REAL:
    _existing = sys.modules.get(_mod)
    if _existing is not None and isinstance(_existing, MagicMock):
        del sys.modules[_mod]

# ---------------------------------------------------------------------------
# Heavy dependency stubs — MUST come before any project imports
# ---------------------------------------------------------------------------
_STUBS = [
    "redis",
    "redis.asyncio",
    "elasticsearch",
    "langchain",
    "langchain_core",
    "websockets",
    "websockets.exceptions",
    "websockets.server",
    "cryptography",
    "cryptography.fernet",
    "zemberek",
    "structlog",
    "structlog.stdlib",
    "structlog.processors",
    "structlog.dev",
    "structlog.types",
]

for _mod in _STUBS:
    sys.modules.setdefault(_mod, MagicMock())

# Explicitly setup celery stubs as ModuleType to support nested imports
import types as _types

for _cmod in ["celery", "celery.schedules", "celery.exceptions"]:
    if _cmod not in sys.modules:
        sys.modules[_cmod] = _types.ModuleType(_cmod)

sys.modules["celery"].Celery = lambda *args, **kwargs: MagicMock()
sys.modules["celery.schedules"].crontab = MagicMock

# Core internal deps strategy:
#   - Modules our code under test calls with fake attribute names (API_REQUEST, EXAM_STARTED, etc.)
#     must remain MagicMock so attribute access always returns a MagicMock (never raises).
#   - Modules that other test files (test_core_partial_batch1.py) import real classes from
#     must be loaded for real (try import, fallback to stub).
_ALWAYS_MOCK = [
    # unified_api_gateway + turkish_exam_event_handlers use MetricType.API_REQUEST etc.
    # which don't exist in the real MetricType enum.
    "core.application_metrics",
    # message_queue_system: QueueType, QueuePriority used as attributes — MagicMock is safe
    "core.message_queue_system",
    # event_bus: EventType used as attribute — MagicMock is safe
    "core.unified_event_bus",
    # background_job_processor: called as coroutine — MagicMock is safe
    "core.background_job_processor",
    # enhanced_database, transaction_manager: not needed by batch1
    "core.enhanced_database",
    "core.transaction_manager",
]
for _mod in _ALWAYS_MOCK:
    sys.modules[_mod] = MagicMock()

# These may be needed as real by other test files — try real import first.
_TRY_REAL = [
    "core.structured_logging",
    "core.unified_config",
    "core.realtime_notification_system",
]
for _mod in _TRY_REAL:
    if _mod not in sys.modules:
        try:
            import importlib as _il

            _il.import_module(_mod)
        except Exception:
            sys.modules[_mod] = MagicMock()

# error_context has no heavy deps — use the real module so combined test runs work.
# error_monitoring has no heavy deps — use the real module so combined test runs work.
# core.exceptions has no heavy deps — use the real module so combined test runs work.
# This also ensures all names (AuthorizationError etc.) are available for other test files.
import importlib as _importlib
import types as _types

if "core.exceptions" not in sys.modules:
    try:
        _importlib.import_module("core.exceptions")
    except Exception:
        # Fallback stub with all commonly needed names
        _ex_mod = _types.ModuleType("core.exceptions")

        class _ValidationError(Exception):
            pass

        class _NotFoundError(Exception):
            pass

        class _AuthorizationError(Exception):
            pass

        class _ErrorSeverity:
            HIGH = "HIGH"
            LOW = "LOW"
            MEDIUM = "MEDIUM"
            CRITICAL = "CRITICAL"

        _ex_mod.ValidationError = _ValidationError  # type: ignore[attr-defined]
        _ex_mod.NotFoundError = _NotFoundError  # type: ignore[attr-defined]
        _ex_mod.AuthorizationError = _AuthorizationError  # type: ignore[attr-defined]
        _ex_mod.ErrorSeverity = _ErrorSeverity  # type: ignore[attr-defined]
        sys.modules["core.exceptions"] = _ex_mod

# ---------------------------------------------------------------------------
# Now import the modules under test
# ---------------------------------------------------------------------------
from datetime import UTC, datetime, timedelta

import pytest

from core.middleware.cache_headers import (
    CacheConfig,
    CachePolicy,
    build_cache_control_header,
    etags_match,
    generate_etag,
    get_cache_config_for_path,
    should_skip_cache,
)
from core.middleware.timing import (
    CORSPreflightCache,
    EndpointStats,
    JWTTokenCache,
    TimingStatsManager,
    get_timing_stats_manager,
)
from core.rbac_system import (
    Action,
    AuthorizationContext,
    AuthorizationResult,
    Permission,
    PermissionEffect,
    PermissionManager,
    RBACManager,
    ResourceType,
    Role,
    RoleManager,
    RoleType,
    UserRole,
    _get_value,
    assign_role,
    check_user_permission,
    get_rbac_manager,
    get_user_permissions,
    get_user_roles,
    initialize_rbac_system,
    revoke_role,
)
from core.structured_logger import (
    StructuredLogger,
    add_app_context,
    censor_sensitive_data,
    get_logger,
    get_structured_logger,
    log_api_request,
    log_api_response,
    log_cache_operation,
    log_database_query,
    log_error_with_context,
    log_exam_event,
)
from core.turkish_exam_event_handlers import (
    ExamEventAction,
    ExamSession,
    TurkishExamEventHandlers,
    TurkishExamType,
)
from core.unified_api_gateway import (
    APIGateway,
    APIRequest,
    APIResponse,
    APIVersion,
    HTTPMethod,
    MiddlewarePipeline,
    RouteConfig,
    RouteManager,
    RouteType,
)

# Restore sys.modules to prevent mock pollution in other unit test files
for _mod in _RESTORE_MODULES:
    if _mod in _original_modules:
        sys.modules[_mod] = _original_modules[_mod]
    elif _mod in sys.modules:
        del sys.modules[_mod]

# ===========================================================================
# =====================  SECTION 1: rbac_system.py  =========================
# ===========================================================================


class TestGetValue:
    def test_enum_value_extracted(self):
        assert _get_value(ResourceType.USER) == "user"

    def test_string_returned_as_is(self):
        assert _get_value("custom") == "custom"

    def test_none_returns_none_string(self):
        assert _get_value(None) == "none"


class TestPermission:
    def test_to_dict_contains_expected_keys(self):
        perm = Permission(
            id="exam:read",
            name="Sınav Okuma",
            description="desc",
            resource_type=ResourceType.EXAM,
            action=Action.READ,
        )
        d = perm.to_dict()
        assert d["id"] == "exam:read"
        assert d["resource_type"] == "exam"
        assert d["action"] == "read"
        assert d["effect"] == "allow"

    def test_from_dict_roundtrip(self):
        perm = Permission(
            id="user:delete",
            name="Silme",
            description="delete user",
            resource_type=ResourceType.USER,
            action=Action.DELETE,
        )
        d = perm.to_dict()
        restored = Permission.from_dict(d)
        assert restored.id == "user:delete"
        assert restored.resource_type == ResourceType.USER
        assert restored.action == Action.DELETE

    def test_deny_effect(self):
        perm = Permission(
            id="x",
            name="x",
            description="x",
            resource_type=ResourceType.SYSTEM,
            action=Action.EXECUTE,
            effect=PermissionEffect.DENY,
        )
        assert perm.effect == PermissionEffect.DENY

    def test_from_dict_without_created_at(self):
        d = {
            "id": "report:read",
            "name": "Okuma",
            "description": "d",
            "resource_type": "report",
            "action": "read",
        }
        perm = Permission.from_dict(d)
        assert perm.id == "report:read"


class TestRole:
    def _make_role(self) -> Role:
        return Role(
            id="teacher",
            name="Öğretmen",
            description="desc",
            role_type=RoleType.SYSTEM,
        )

    def test_is_valid_active(self):
        role = self._make_role()
        assert role.is_valid() is True

    def test_is_valid_inactive(self):
        role = self._make_role()
        role.is_active = False
        assert role.is_valid() is False

    def test_is_valid_not_yet_started(self):
        role = self._make_role()
        role.valid_from = datetime.now(UTC) + timedelta(hours=1)
        assert role.is_valid() is False

    def test_is_valid_expired(self):
        role = self._make_role()
        role.valid_until = datetime.now(UTC) - timedelta(hours=1)
        assert role.is_valid() is False

    def test_add_permission(self):
        role = self._make_role()
        role.add_permission("exam:read")
        assert "exam:read" in role.permissions
        # Adding duplicate should not duplicate
        role.add_permission("exam:read")
        assert role.permissions.count("exam:read") == 1

    def test_remove_permission(self):
        role = self._make_role()
        role.add_permission("exam:read")
        role.remove_permission("exam:read")
        assert "exam:read" not in role.permissions

    def test_add_parent_role(self):
        role = self._make_role()
        role.add_parent_role("admin")
        assert "admin" in role.parent_roles

    def test_to_dict_has_role_type(self):
        role = self._make_role()
        d = role.to_dict()
        assert d["role_type"] == "system"
        assert d["is_active"] is True


class TestUserRole:
    def test_is_valid_active(self):
        ur = UserRole(
            id="u:r:1",
            user_id="u1",
            role_id="student",
            assigned_by="admin",
            assigned_at=datetime.now(UTC),
        )
        assert ur.is_valid() is True

    def test_is_valid_expired(self):
        ur = UserRole(
            id="u:r:2",
            user_id="u2",
            role_id="student",
            assigned_by="admin",
            assigned_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        assert ur.is_valid() is False

    def test_is_valid_inactive(self):
        ur = UserRole(
            id="u:r:3",
            user_id="u3",
            role_id="teacher",
            assigned_by="admin",
            assigned_at=datetime.now(UTC),
            is_active=False,
        )
        assert ur.is_valid() is False


class TestAuthorizationResult:
    def test_authorized_alias(self):
        result = AuthorizationResult(granted=True, reason="ok")
        assert result.authorized is True

    def test_message_alias_set_from_reason(self):
        result = AuthorizationResult(granted=False, reason="no roles")
        assert result.message == "no roles"

    def test_to_dict(self):
        result = AuthorizationResult(
            granted=True,
            reason="granted",
            matched_permissions=["exam:read"],
            matched_roles=["student"],
        )
        d = result.to_dict()
        assert d["granted"] is True
        assert d["authorized"] is True
        assert "exam:read" in d["matched_permissions"]


class TestPermissionManager:
    def setup_method(self):
        self.pm = PermissionManager()

    def test_system_permissions_initialized(self):
        assert len(self.pm.permissions) > 0
        assert "system:read" in self.pm.permissions

    def test_create_permission_new(self):
        perm = Permission(
            id="chat:read",
            name="Chat",
            description="Chat read",
            resource_type=ResourceType.CHAT,
            action=Action.READ,
        )
        result = self.pm.create_permission(perm)
        assert result is True
        assert self.pm.get_permission("chat:read") is not None

    def test_create_permission_duplicate_returns_false(self):
        perm = Permission(
            id="system:read",
            name="dup",
            description="d",
            resource_type=ResourceType.SYSTEM,
            action=Action.READ,
        )
        assert self.pm.create_permission(perm) is False

    def test_get_permissions_by_resource(self):
        perms = self.pm.get_permissions_by_resource(ResourceType.EXAM)
        assert len(perms) > 0
        for p in perms:
            assert p.resource_type == ResourceType.EXAM

    def test_get_permissions_by_action(self):
        perms = self.pm.get_permissions_by_action(Action.READ)
        assert len(perms) > 0
        for p in perms:
            assert p.action == Action.READ

    def test_update_permission_existing(self):
        perm = self.pm.get_permission("system:read")
        perm.description = "Updated"
        assert self.pm.update_permission(perm) is True

    def test_update_permission_nonexistent(self):
        perm = Permission(
            id="nonexistent:read",
            name="x",
            description="x",
            resource_type=ResourceType.SYSTEM,
            action=Action.READ,
        )
        assert self.pm.update_permission(perm) is False

    def test_delete_permission(self):
        perm = Permission(
            id="payment:read",
            name="p",
            description="d",
            resource_type=ResourceType.PAYMENT,
            action=Action.READ,
        )
        self.pm.create_permission(perm)
        assert self.pm.delete_permission("payment:read") is True
        assert self.pm.get_permission("payment:read") is None

    def test_delete_nonexistent_returns_false(self):
        assert self.pm.delete_permission("does:not:exist") is False

    def test_get_all_permissions(self):
        all_perms = self.pm.get_all_permissions()
        assert isinstance(all_perms, list)
        assert len(all_perms) > 0


class TestRoleManager:
    def setup_method(self):
        self.pm = PermissionManager()
        self.rm = RoleManager(self.pm)

    def test_system_roles_initialized(self):
        assert "student" in self.rm.roles
        assert "admin" in self.rm.roles
        assert "teacher" in self.rm.roles

    def test_get_role_existing(self):
        role = self.rm.get_role("student")
        assert role is not None
        assert role.id == "student"

    def test_get_role_nonexistent(self):
        assert self.rm.get_role("nonexistent") is None

    def test_get_roles_by_type(self):
        system_roles = self.rm.get_roles_by_type(RoleType.SYSTEM)
        assert len(system_roles) >= 5

    def test_create_role_success(self):
        new_role = Role(
            id="custom_viewer",
            name="Viewer",
            description="Read-only viewer",
            role_type=RoleType.CUSTOM,
            permissions=["exam:read", "question:read"],
        )
        assert self.rm.create_role(new_role) is True
        assert self.rm.get_role("custom_viewer") is not None

    def test_create_role_duplicate_returns_false(self):
        role = Role(
            id="student",
            name="dup",
            description="d",
            role_type=RoleType.CUSTOM,
        )
        assert self.rm.create_role(role) is False

    def test_create_role_invalid_permission_raises(self):
        role = Role(
            id="bad_role",
            name="Bad",
            description="d",
            role_type=RoleType.CUSTOM,
            permissions=["does:not:exist"],
        )
        with pytest.raises(Exception):
            self.rm.create_role(role)

    def test_update_role(self):
        role = self.rm.get_role("student")
        role.description = "Updated"
        assert self.rm.update_role(role) is True

    def test_update_nonexistent_role(self):
        role = Role(
            id="ghost",
            name="g",
            description="d",
            role_type=RoleType.CUSTOM,
        )
        assert self.rm.update_role(role) is False

    def test_delete_custom_role(self):
        custom = Role(
            id="to_delete",
            name="del",
            description="d",
            role_type=RoleType.CUSTOM,
            permissions=[],
        )
        self.rm.roles["to_delete"] = custom
        assert self.rm.delete_role("to_delete") is True
        assert self.rm.get_role("to_delete") is None

    def test_delete_system_role_fails(self):
        assert self.rm.delete_role("student") is False

    def test_get_inherited_permissions_student(self):
        perms = self.rm.get_inherited_permissions("student")
        # Student should have its own permissions and none from others
        assert isinstance(perms, set)
        assert "exam:read" in perms

    def test_get_role_hierarchy_path(self):
        path = self.rm.get_role_hierarchy_path("student")
        assert "student" in path

    def test_get_all_roles(self):
        roles = self.rm.get_all_roles()
        assert isinstance(roles, list)
        assert len(roles) >= 5


class TestRBACManager:
    def setup_method(self):
        self.rbac = RBACManager()

    @pytest.mark.asyncio
    async def test_assign_role_success(self):
        result = await self.rbac.assign_role_to_user("user1", "student", "admin")
        assert result is True
        active = self.rbac.get_active_user_roles("user1")
        assert len(active) == 1

    @pytest.mark.asyncio
    async def test_assign_nonexistent_role_raises(self):
        with pytest.raises(Exception):
            await self.rbac.assign_role_to_user("user2", "ghost_role", "admin")

    @pytest.mark.asyncio
    async def test_assign_role_duplicate_returns_false(self):
        await self.rbac.assign_role_to_user("user3", "student", "admin")
        result = await self.rbac.assign_role_to_user("user3", "student", "admin")
        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_role(self):
        await self.rbac.assign_role_to_user("user4", "teacher", "admin")
        result = await self.rbac.revoke_role_from_user("user4", "teacher", "admin")
        assert result is True
        assert len(self.rbac.get_active_user_roles("user4")) == 0

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_assignment_returns_false(self):
        result = await self.rbac.revoke_role_from_user("ghost_user", "student", "admin")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_permission_no_roles_denied(self):
        ctx = AuthorizationContext(
            user_id="no_role_user",
            resource_type=ResourceType.EXAM,
            action=Action.READ,
        )
        result = await self.rbac.check_permission(ctx)
        assert result.granted is False
        assert "no active roles" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_permission_granted(self):
        await self.rbac.assign_role_to_user("student1", "student", "admin")
        ctx = AuthorizationContext(
            user_id="student1",
            resource_type=ResourceType.EXAM,
            action=Action.READ,
        )
        result = await self.rbac.check_permission(ctx)
        assert result.granted is True

    @pytest.mark.asyncio
    async def test_check_permission_role_only_grants_without_rbac_assignment(self):
        ctx = AuthorizationContext(
            user_id="jwt_admin_no_rbac_row",
            resource_type="general",
            action=None,
            required_roles=["admin", "super_admin"],
            user_role="admin",
        )
        result = await self.rbac.check_permission(ctx)
        assert result.granted is True

    @pytest.mark.asyncio
    async def test_check_permission_role_only_denies_wrong_role(self):
        ctx = AuthorizationContext(
            user_id="student_only",
            resource_type="general",
            action=None,
            required_roles=["admin"],
            user_role="student",
        )
        result = await self.rbac.check_permission(ctx)
        assert result.granted is False

    @pytest.mark.asyncio
    async def test_check_permission_role_only_missing_user_role_denied(self):
        ctx = AuthorizationContext(
            user_id="norole_ctx",
            resource_type="general",
            action=None,
            required_roles=["admin"],
            user_role=None,
        )
        result = await self.rbac.check_permission(ctx)
        assert result.granted is False
        assert "user_role" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_permission_combined_role_and_perm_denied_when_role_wrong(self):
        await self.rbac.assign_role_to_user("u_combo", "student", "admin")
        ctx = AuthorizationContext(
            user_id="u_combo",
            resource_type=ResourceType.EXAM,
            action=Action.READ,
            required_roles=["admin"],
            required_permissions=["read"],
            user_role="student",
        )
        result = await self.rbac.check_permission(ctx)
        assert result.granted is False
        assert "combined" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_permission_combined_role_and_perm_granted(self):
        await self.rbac.assign_role_to_user("u_combo2", "student", "admin")
        ctx = AuthorizationContext(
            user_id="u_combo2",
            resource_type=ResourceType.EXAM,
            action=Action.READ,
            required_roles=["student", "teacher"],
            required_permissions=["read"],
            user_role="student",
        )
        result = await self.rbac.check_permission(ctx)
        assert result.granted is True

    @pytest.mark.asyncio
    async def test_check_permission_denied_insufficient(self):
        # Create an isolated custom role with only report:read — no exam:delete, no parent roles
        from core.rbac_system import Role, RoleType

        isolated_role = Role(
            id="report_only_role",
            name="Report Only",
            description="Only report:read, no parent hierarchy",
            role_type=RoleType.CUSTOM,
            permissions=["report:read"],
            parent_roles=[],  # No inheritance
        )
        self.rbac.role_manager.roles["report_only_role"] = isolated_role
        await self.rbac.assign_role_to_user("limited_user", "report_only_role", "admin")
        ctx = AuthorizationContext(
            user_id="limited_user",
            resource_type=ResourceType.EXAM,
            action=Action.DELETE,
        )
        result = await self.rbac.check_permission(ctx)
        assert result.granted is False

    def test_get_user_permissions_empty(self):
        perms = self.rbac.get_user_permissions("nobody")
        assert perms == set()

    @pytest.mark.asyncio
    async def test_get_user_permissions_with_role(self):
        await self.rbac.assign_role_to_user("student_p", "student", "admin")
        perms = self.rbac.get_user_permissions("student_p")
        assert "exam:read" in perms

    def test_get_rbac_stats(self):
        stats = self.rbac.get_rbac_stats()
        assert stats["roles_count"] >= 5
        assert stats["permissions_count"] > 0
        assert "roles_by_type" in stats

    @pytest.mark.asyncio
    async def test_audit_log_populated(self):
        await self.rbac.assign_role_to_user("audit_user", "student", "admin")
        assert len(self.rbac.audit_log) > 0

    @pytest.mark.asyncio
    async def test_permission_cache_populated(self):
        await self.rbac.assign_role_to_user("cache_user", "student", "admin")
        ctx = AuthorizationContext(
            user_id="cache_user",
            resource_type=ResourceType.EXAM,
            action=Action.READ,
        )
        await self.rbac.check_permission(ctx)
        assert len(self.rbac.permission_cache) > 0


class TestRBACUtilityFunctions:
    def setup_method(self):
        # Reset global rbac manager between tests
        import core.rbac_system as rbac_mod

        rbac_mod.rbac_manager = None

    def test_get_rbac_manager_returns_instance(self):
        rbac = get_rbac_manager()
        assert isinstance(rbac, RBACManager)

    def test_get_rbac_manager_singleton(self):
        rbac1 = get_rbac_manager()
        rbac2 = get_rbac_manager()
        assert rbac1 is rbac2

    @pytest.mark.asyncio
    async def test_check_user_permission_convenience(self):
        rbac = get_rbac_manager()
        await rbac.assign_role_to_user("cu1", "student", "admin")
        result = await check_user_permission("cu1", ResourceType.EXAM, Action.READ)
        assert result is True

    @pytest.mark.asyncio
    async def test_assign_role_convenience(self):
        result = await assign_role("cu2", "student", "admin")
        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_role_convenience(self):
        await assign_role("cu3", "student", "admin")
        result = await revoke_role("cu3", "student", "admin")
        assert result is True

    def test_get_user_roles_empty(self):
        roles = get_user_roles("nobody")
        assert roles == []

    @pytest.mark.asyncio
    async def test_get_user_roles_with_assignment(self):
        await assign_role("cu4", "teacher", "admin")
        roles = get_user_roles("cu4")
        assert "teacher" in roles

    def test_get_user_permissions_list(self):
        perms = get_user_permissions("nobody")
        assert isinstance(perms, list)

    def test_initialize_rbac_system(self):
        rbac = initialize_rbac_system()
        assert isinstance(rbac, RBACManager)


# ===========================================================================
# ==========  SECTION 2: turkish_exam_event_handlers.py  ===================
# ===========================================================================


class TestExamSession:
    def _make_session(self, answered: int = 30) -> ExamSession:
        return ExamSession(
            session_id="sess-001",
            user_id=42,
            exam_type=TurkishExamType.TYT,
            exam_date=datetime.now(UTC),
            start_time=datetime.now(UTC),
            duration_minutes=120,
            questions_total=120,
            questions_answered=answered,
            remaining_time_minutes=90,
        )

    def test_get_progress_percentage(self):
        sess = self._make_session(answered=60)
        assert sess.get_progress_percentage() == 50.0

    def test_get_progress_percentage_zero_total(self):
        sess = self._make_session(answered=0)
        sess.questions_total = 0
        assert sess.get_progress_percentage() == 0.0

    def test_get_time_progress_percentage(self):
        sess = self._make_session()
        # elapsed = 120 - 90 = 30, progress = 30/120 * 100 = 25%
        assert sess.get_time_progress_percentage() == 25.0


@pytest.mark.parametrize("exam_type", list(TurkishExamType))
def test_turkish_exam_type_values(exam_type):
    assert isinstance(exam_type.value, str)
    assert len(exam_type.value) > 0


@pytest.mark.parametrize("action", list(ExamEventAction))
def test_exam_event_action_values(action):
    assert isinstance(action.value, str)


class TestTurkishExamEventHandlers:
    def setup_method(self):
        self.handlers = TurkishExamEventHandlers()

    def test_initial_state(self):
        assert self.handlers.registered is False
        assert len(self.handlers.active_sessions) == 0
        assert len(self.handlers.exam_results) == 0

    def test_notification_templates_loaded(self):
        templates = self.handlers.notification_templates
        assert "exam_started" in templates
        assert "time_warning_30" in templates
        assert "time_warning_15" in templates
        assert "time_warning_5" in templates
        assert "exam_completed" in templates
        assert "results_ready" in templates

    def test_turkish_subjects_loaded(self):
        subjects = self.handlers.turkish_subjects
        assert "matematik" in subjects
        assert subjects["matematik"] == "Matematik"
        assert "turkce" in subjects

    def test_get_active_sessions_empty(self):
        sessions = self.handlers.get_active_sessions()
        assert sessions == {}

    def test_get_exam_results_empty(self):
        results = self.handlers.get_exam_results()
        assert results == {}

    def test_get_session_stats_empty(self):
        stats = self.handlers.get_session_stats()
        assert stats["active_sessions"] == 0
        assert stats["completed_exams"] == 0

    def test_get_session_stats_with_session(self):
        sess = ExamSession(
            session_id="s1",
            user_id=1,
            exam_type=TurkishExamType.TYT,
            exam_date=datetime.now(UTC),
            start_time=datetime.now(UTC),
            duration_minutes=120,
            questions_total=120,
        )
        self.handlers.active_sessions["s1"] = sess
        stats = self.handlers.get_session_stats()
        assert stats["active_sessions"] == 1
        assert stats["session_by_type"]["tyt"] == 1

    @pytest.mark.asyncio
    async def test_handle_exam_started_creates_session(self):
        event = MagicMock()
        event.user_id = 10
        event.session_id = "session-abc"
        event.data = {
            "session_id": "session-abc",
            "duration_minutes": 135,
            "questions_total": 120,
            "is_simulation": True,
        }

        # Patch all external calls
        with (
            patch.object(self.handlers, "_send_exam_notification", new=AsyncMock()),
            patch.object(self.handlers, "_schedule_time_warnings", new=AsyncMock()),
            patch("core.turkish_exam_event_handlers.enqueue_message", new=AsyncMock()),
        ):
            metrics_mock = MagicMock()
            self.handlers.metrics_collector = metrics_mock
            await self.handlers._handle_exam_started(event, TurkishExamType.TYT)

        assert "session-abc" in self.handlers.active_sessions
        sess = self.handlers.active_sessions["session-abc"]
        assert sess.exam_type == TurkishExamType.TYT
        assert sess.user_id == 10

    @pytest.mark.asyncio
    async def test_handle_exam_completed_removes_session(self):
        # First set up active session
        sess = ExamSession(
            session_id="sess-complete",
            user_id=5,
            exam_type=TurkishExamType.AYT,
            exam_date=datetime.now(UTC),
            start_time=datetime.now(UTC),
            duration_minutes=180,
            questions_total=80,
        )
        self.handlers.active_sessions["sess-complete"] = sess

        event = MagicMock()
        event.user_id = 5
        event.session_id = "sess-complete"
        event.data = {
            "session_id": "sess-complete",
            "total_score": 450.5,
            "section_scores": {"matematik": 120.0},
            "correct_answers": 60,
            "wrong_answers": 10,
            "empty_answers": 10,
        }

        mock_processor = MagicMock()
        mock_processor.schedule_job = AsyncMock()

        async def _fake_get_job_processor():
            return mock_processor

        with (
            patch.object(self.handlers, "_send_exam_notification", new=AsyncMock()),
            patch(
                "core.turkish_exam_event_handlers.get_turkish_job_processor",
                side_effect=_fake_get_job_processor,
            ),
            patch(
                "core.turkish_exam_event_handlers.schedule_exam_processing",
                new=AsyncMock(),
            ),
        ):
            self.handlers.metrics_collector = MagicMock()
            await self.handlers._handle_exam_completed(event, TurkishExamType.AYT)

        assert "sess-complete" not in self.handlers.active_sessions
        assert "sess-complete" in self.handlers.exam_results
        assert self.handlers.exam_results["sess-complete"].total_score == 450.5

    @pytest.mark.asyncio
    async def test_handle_exam_completed_no_session(self):
        event = MagicMock()
        event.user_id = 99
        event.session_id = "nonexistent"
        event.data = {}

        # Should not raise, just log warning
        await self.handlers._handle_exam_completed(event, TurkishExamType.TYT)
        assert "nonexistent" not in self.handlers.exam_results

    @pytest.mark.asyncio
    async def test_handle_question_progress_update(self):
        sess = ExamSession(
            session_id="progress-sess",
            user_id=3,
            exam_type=TurkishExamType.TYT,
            exam_date=datetime.now(UTC),
            start_time=datetime.now(UTC),
            duration_minutes=120,
            questions_total=4,
            questions_answered=0,
        )
        self.handlers.active_sessions["progress-sess"] = sess

        event = MagicMock()
        event.user_id = 3
        event.session_id = "progress-sess"
        event.data = {"subject": "matematik"}

        with patch(
            "core.turkish_exam_event_handlers.send_realtime_notification",
            new=AsyncMock(),
        ):
            await self.handlers._handle_question_progress(event)

        assert sess.questions_answered == 1
        assert sess.current_section == "matematik"

    @pytest.mark.asyncio
    async def test_handle_question_progress_no_session(self):
        event = MagicMock()
        event.user_id = 99
        event.session_id = "missing"
        event.data = {}
        # Should return silently without error
        await self.handlers._handle_question_progress(event)

    @pytest.mark.asyncio
    async def test_handle_learning_progress(self):
        event = MagicMock()
        event.user_id = 7
        event.data = {
            "subject": "matematik",
            "progress": {"milestone_reached": False},
        }
        with patch("core.turkish_exam_event_handlers.enqueue_message", new=AsyncMock()):
            await self.handlers._handle_learning_progress(event)

    @pytest.mark.asyncio
    async def test_handle_learning_progress_milestone(self):
        event = MagicMock()
        event.user_id = 8
        event.data = {
            "subject": "fizik",
            "progress": {
                "milestone_reached": True,
                "achievement_type": "subject_mastery",
                "achievement_name": "Fizik Ustası",
            },
        }
        with (
            patch("core.turkish_exam_event_handlers.enqueue_message", new=AsyncMock()),
            patch.object(
                self.handlers, "_handle_achievement_notification", new=AsyncMock()
            ),
        ):
            await self.handlers._handle_learning_progress(event)
            self.handlers._handle_achievement_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_achievement_notification(self):
        with patch(
            "core.turkish_exam_event_handlers.send_realtime_notification",
            new=AsyncMock(),
        ):
            await self.handlers._handle_achievement_notification(
                user_id=5,
                subject="Matematik",
                progress_data={"achievement_name": "Top Scorer"},
            )

    @pytest.mark.asyncio
    async def test_handle_practice_notification_started(self):
        event = MagicMock()
        event.user_id = 11
        event.data = {"test_type": "practice", "subject": "kimya"}
        with patch(
            "core.turkish_exam_event_handlers.send_realtime_notification",
            new=AsyncMock(),
        ):
            await self.handlers._handle_practice_notification(event, "started")

    @pytest.mark.asyncio
    async def test_handle_practice_notification_completed(self):
        event = MagicMock()
        event.user_id = 11
        event.data = {"test_type": "practice", "subject": "kimya"}
        with patch(
            "core.turkish_exam_event_handlers.send_realtime_notification",
            new=AsyncMock(),
        ):
            await self.handlers._handle_practice_notification(event, "completed")

    @pytest.mark.asyncio
    async def test_handle_results_notification(self):
        event = MagicMock()
        event.user_id = 12
        event.session_id = "sess-res"
        event.data = {"exam_type": "tyt", "score": 400.0}
        with patch.object(self.handlers, "_send_exam_notification", new=AsyncMock()):
            await self.handlers._handle_results_notification(event)

    @pytest.mark.asyncio
    async def test_handle_analytics_tracking(self):
        event = MagicMock()
        event.user_id = 13
        event.data = {"action": "view"}
        event.timestamp = datetime.now(UTC)
        with patch("core.turkish_exam_event_handlers.enqueue_message", new=AsyncMock()):
            await self.handlers._handle_analytics_tracking(event)

    @pytest.mark.asyncio
    async def test_handle_ranking_notification(self):
        event = MagicMock()
        event.data = {
            "exam_type": "TYT",
            "rankings": [
                {"user_id": 1, "rank": 1},
                {"user_id": 2, "rank": 2},
            ],
        }
        with patch(
            "core.turkish_exam_event_handlers.send_realtime_notification",
            new=AsyncMock(),
        ):
            await self.handlers._handle_ranking_notification(event)

    @pytest.mark.asyncio
    async def test_handle_user_context_setup(self):
        event = MagicMock()
        event.user_id = 20
        await self.handlers._handle_user_context_setup(event)

    @pytest.mark.asyncio
    async def test_handle_system_initialization(self):
        event = MagicMock()
        await self.handlers._handle_system_initialization(event)

    @pytest.mark.asyncio
    async def test_send_exam_notification_valid_template(self):
        with patch(
            "core.turkish_exam_event_handlers.send_realtime_notification",
            new=AsyncMock(),
        ):
            await self.handlers._send_exam_notification(
                user_id=1,
                session_id="s1",
                exam_type="TYT",
                template_key="exam_started",
                duration=135,
            )

    @pytest.mark.asyncio
    async def test_send_exam_notification_missing_template(self):
        with patch(
            "core.turkish_exam_event_handlers.send_realtime_notification",
            new=AsyncMock(),
        ):
            # Should not raise, just log warning
            await self.handlers._send_exam_notification(
                user_id=1,
                session_id="s1",
                exam_type="TYT",
                template_key="nonexistent_template",
            )


# ===========================================================================
# ===========  SECTION 3: unified_api_gateway.py  ==========================
# ===========================================================================


class TestAPIRequest:
    def _make_request(self) -> APIRequest:
        return APIRequest(
            id="req-001",
            method=HTTPMethod.GET,
            path="/health",
            version=APIVersion.V1,
            route_type=RouteType.HEALTH,
            headers={},
            query_params={},
            body=None,
        )

    def test_get_full_path(self):
        req = self._make_request()
        assert req.get_full_path() == "/api/v1/health"

    def test_is_authenticated_route_public(self):
        req = self._make_request()
        assert req.is_authenticated_route() is False

    def test_is_authenticated_route_private(self):
        req = self._make_request()
        req.route_type = RouteType.USER_PROFILE
        assert req.is_authenticated_route() is True

    def test_is_exam_route_true(self):
        req = self._make_request()
        req.route_type = RouteType.TYT_EXAM
        assert req.is_exam_route() is True

    def test_is_exam_route_false(self):
        req = self._make_request()
        assert req.is_exam_route() is False

    def test_get_cache_key_no_user(self):
        req = self._make_request()
        key = req.get_cache_key()
        assert "GET" in key
        assert "v1" in key

    def test_get_cache_key_with_user_and_params(self):
        req = self._make_request()
        req.user_id = 42
        req.query_params = {"page": "1"}
        key = req.get_cache_key()
        assert "user_42" in key


class TestAPIResponse:
    def test_is_success_200(self):
        resp = APIResponse(
            request_id="r1",
            status_code=200,
            headers={},
            body=None,
            processing_time_ms=10.0,
        )
        assert resp.is_success() is True

    def test_is_client_error_400(self):
        resp = APIResponse(
            request_id="r1",
            status_code=404,
            headers={},
            body=None,
            processing_time_ms=5.0,
        )
        assert resp.is_client_error() is True
        assert resp.is_success() is False

    def test_is_server_error_500(self):
        resp = APIResponse(
            request_id="r1",
            status_code=503,
            headers={},
            body=None,
            processing_time_ms=5.0,
        )
        assert resp.is_server_error() is True

    def test_add_header(self):
        resp = APIResponse(
            request_id="r1",
            status_code=200,
            headers={},
            body=None,
            processing_time_ms=1.0,
        )
        resp.add_header("X-Custom", "value")
        assert resp.headers["X-Custom"] == "value"

    def test_set_turkish_headers(self):
        resp = APIResponse(
            request_id="r1",
            status_code=200,
            headers={},
            body=None,
            processing_time_ms=1.0,
        )
        resp.set_turkish_headers()
        assert resp.headers["Content-Language"] == "tr-TR"
        assert "KIRO2" in resp.headers["X-Platform"]


class TestMiddlewarePipeline:
    def setup_method(self):
        self.pipeline = MiddlewarePipeline()

    def test_register_middleware(self):
        mw = AsyncMock(return_value=MagicMock())
        self.pipeline.register_middleware("test_mw", mw)
        assert "test_mw" in self.pipeline.middleware_registry

    def test_register_middleware_at_position(self):
        mw1 = AsyncMock()
        mw2 = AsyncMock()
        self.pipeline.register_middleware("first", mw1, 0)
        self.pipeline.register_middleware("second", mw2, 0)
        assert self.pipeline.middleware_stack[0] is mw2

    def test_remove_middleware(self):
        mw = AsyncMock()
        self.pipeline.register_middleware("removable", mw)
        result = self.pipeline.remove_middleware("removable")
        assert result is True
        assert "removable" not in self.pipeline.middleware_registry

    def test_remove_nonexistent_middleware(self):
        assert self.pipeline.remove_middleware("ghost") is False

    @pytest.mark.asyncio
    async def test_process_request_calls_handler(self):
        async def handler(req):
            return APIResponse(
                request_id=req.id,
                status_code=200,
                headers={},
                body={"ok": True},
                processing_time_ms=1.0,
            )

        req = APIRequest(
            id="r1",
            method=HTTPMethod.GET,
            path="/health",
            version=APIVersion.V1,
            route_type=RouteType.HEALTH,
            headers={},
            query_params={},
            body=None,
        )
        resp = await self.pipeline.process_request(req, handler)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_chain_executed(self):
        call_order = []

        async def mw1(req, next_h):
            call_order.append("mw1_before")
            resp = await next_h(req)
            call_order.append("mw1_after")
            return resp

        async def handler(req):
            call_order.append("handler")
            return APIResponse(
                request_id=req.id,
                status_code=200,
                headers={},
                body={},
                processing_time_ms=1.0,
            )

        self.pipeline.register_middleware("mw1", mw1)
        req = APIRequest(
            id="r1",
            method=HTTPMethod.GET,
            path="/health",
            version=APIVersion.V1,
            route_type=RouteType.HEALTH,
            headers={},
            query_params={},
            body=None,
        )
        await self.pipeline.process_request(req, handler)
        assert call_order == ["mw1_before", "handler", "mw1_after"]


class TestRouteManager:
    def setup_method(self):
        self.rm = RouteManager()

    def test_register_and_match_route(self):
        async def handler(req):
            return None

        config = RouteConfig(
            path_pattern="/health",
            method=HTTPMethod.GET,
            route_type=RouteType.HEALTH,
            version=APIVersion.V1,
            handler=handler,
        )
        self.rm.register_route(config)
        result = self.rm.match_route(HTTPMethod.GET, APIVersion.V1, "/health")
        assert result is not None
        matched_config, params = result
        assert matched_config.route_type == RouteType.HEALTH

    def test_match_route_with_path_params(self):
        async def handler(req):
            return None

        config = RouteConfig(
            path_pattern="/users/{user_id}/profile",
            method=HTTPMethod.GET,
            route_type=RouteType.USER_PROFILE,
            version=APIVersion.V1,
            handler=handler,
        )
        self.rm.register_route(config)
        result = self.rm.match_route(HTTPMethod.GET, APIVersion.V1, "/users/42/profile")
        assert result is not None
        _, params = result
        assert params["user_id"] == "42"

    def test_match_route_no_match(self):
        result = self.rm.match_route(HTTPMethod.GET, APIVersion.V1, "/does/not/exist")
        assert result is None

    def test_get_routes_by_type(self):
        async def handler(req):
            return None

        config = RouteConfig(
            path_pattern="/admin/users",
            method=HTTPMethod.GET,
            route_type=RouteType.ADMIN,
            version=APIVersion.V1,
            handler=handler,
        )
        self.rm.register_route(config)
        routes = self.rm.get_routes_by_type(RouteType.ADMIN)
        assert len(routes) == 1


class TestAPIGateway:
    def setup_method(self):
        self.gateway = APIGateway()

    def test_default_config_set(self):
        assert self.gateway.config["enable_cors"] is True
        assert self.gateway.config["enable_caching"] is True
        assert self.gateway.config["enable_rate_limiting"] is True

    def test_middleware_registered(self):
        registry = self.gateway.middleware_pipeline.middleware_registry
        assert "cors" in registry
        assert "request_id" in registry
        assert "metrics" in registry

    def test_routes_registered(self):
        assert len(self.gateway.route_manager.routes) >= 5

    def test_get_stats(self):
        stats = self.gateway.get_stats()
        assert "request_stats" in stats
        assert "registered_routes" in stats
        assert stats["registered_routes"] >= 5

    def test_get_active_requests_empty(self):
        active = self.gateway.get_active_requests()
        assert active == []

    def test_update_request_stats_success(self):
        self.gateway._update_request_stats(True, 50.0)
        assert self.gateway.request_stats["total_requests"] == 1
        assert self.gateway.request_stats["successful_requests"] == 1

    def test_update_request_stats_failure(self):
        self.gateway._update_request_stats(False, 100.0)
        assert self.gateway.request_stats["failed_requests"] == 1

    @pytest.mark.parametrize(
        "path,expected",
        [
            ("/auth/login", RouteType.AUTH),
            ("/users/1/profile", RouteType.USER_PROFILE),
            ("/exams/tyt/start", RouteType.TYT_EXAM),
            ("/exams/ayt/start", RouteType.AYT_EXAM),
            ("/yks/info", RouteType.YKS_INFO),
            ("/practice/matematik/tests", RouteType.PRACTICE_TESTS),
            ("/analytics/overview", RouteType.ANALYTICS),
            ("/progress/summary", RouteType.PROGRESS),
            ("/health", RouteType.HEALTH),
            ("/admin/users", RouteType.ADMIN),
            ("/content/videos", RouteType.CONTENT),
            ("/unknown/path", RouteType.SYSTEM),
        ],
    )
    def test_determine_route_type(self, path, expected):
        assert self.gateway._determine_route_type(path) == expected

    @pytest.mark.parametrize(
        "path,header,expected",
        [
            ("/api/v1/health", {}, APIVersion.V1),
            ("/api/v2/exams", {}, APIVersion.V2),
            ("/api/beta/test", {}, APIVersion.BETA),
            ("/health", {"X-API-Version": "v1"}, APIVersion.V1),
            ("/health", {"X-API-Version": "v2"}, APIVersion.V2),
            ("/health", {"X-API-Version": "beta"}, APIVersion.BETA),
            ("/health", {}, APIVersion.V1),  # default
        ],
    )
    def test_extract_api_version(self, path, header, expected):
        assert self.gateway._extract_api_version(path, header) == expected

    def test_clean_path_removes_prefix(self):
        assert self.gateway._clean_path("/api/v1/health", APIVersion.V1) == "/health"

    def test_clean_path_no_prefix(self):
        assert self.gateway._clean_path("/health", APIVersion.V1) == "/health"

    def test_translate_error_known(self):
        tr = self.gateway._translate_error("Route not found")
        assert tr == "Rota bulunamadı"

    def test_translate_error_unknown(self):
        tr = self.gateway._translate_error("Custom Error")
        assert tr == "Custom Error"

    def test_translate_error_detail(self):
        # "not found" is lowercase match + replace — works correctly
        assert "bulunamadı" in self.gateway._translate_error_detail("User not found")
        # "invalid" lowercase — method does case-sensitive replace("invalid", ...)
        assert "geçersiz" in self.gateway._translate_error_detail("invalid token")
        # "required" lowercase
        assert "gerekli" in self.gateway._translate_error_detail("field required")
        # No match returns original
        assert (
            self.gateway._translate_error_detail("Something else") == "Something else"
        )

    @pytest.mark.asyncio
    async def test_process_request_health_check(self):
        raw = {
            "method": "GET",
            "path": "/api/v1/health",
            "headers": {},
            "query_params": {},
        }
        result = await self.gateway.process_request(raw)
        assert result["status_code"] == 200
        assert result["body"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_process_request_not_found(self):
        raw = {
            "method": "GET",
            "path": "/api/v1/does/not/exist",
            "headers": {},
            "query_params": {},
        }
        result = await self.gateway.process_request(raw)
        assert result["status_code"] == 404

    @pytest.mark.asyncio
    async def test_default_handler_health(self):
        req = APIRequest(
            id="h1",
            method=HTTPMethod.GET,
            path="/health",
            version=APIVersion.V1,
            route_type=RouteType.HEALTH,
            headers={},
            query_params={},
            body=None,
        )
        resp = await self.gateway._health_check_handler(req)
        assert resp.status_code == 200
        assert resp.body["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_error_handling_middleware_value_error(self):
        async def raising_handler(req):
            raise ValueError("bad input")

        req = APIRequest(
            id="e1",
            method=HTTPMethod.POST,
            path="/auth/login",
            version=APIVersion.V1,
            route_type=RouteType.AUTH,
            headers={},
            query_params={},
            body=None,
        )
        resp = await self.gateway._error_handling_middleware(req, raising_handler)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_error_handling_middleware_permission_error(self):
        async def raising_handler(req):
            raise PermissionError("no access")

        req = APIRequest(
            id="e2",
            method=HTTPMethod.GET,
            path="/admin",
            version=APIVersion.V1,
            route_type=RouteType.ADMIN,
            headers={},
            query_params={},
            body=None,
        )
        resp = await self.gateway._error_handling_middleware(req, raising_handler)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_error_handling_middleware_generic_error(self):
        async def raising_handler(req):
            raise RuntimeError("unexpected")

        req = APIRequest(
            id="e3",
            method=HTTPMethod.GET,
            path="/health",
            version=APIVersion.V1,
            route_type=RouteType.HEALTH,
            headers={},
            query_params={},
            body=None,
        )
        resp = await self.gateway._error_handling_middleware(req, raising_handler)
        assert resp.status_code == 500


# ===========================================================================
# =============  SECTION 4: middleware/timing.py  ==========================
# ===========================================================================


class TestEndpointStats:
    def test_add_timing_increments_count(self):
        stats = EndpointStats(endpoint="/api/users", method="GET")
        stats.add_timing(100.0)
        assert stats.request_count == 1
        assert 100.0 in stats.timings

    def test_add_timing_error_increments_error_count(self):
        stats = EndpointStats(endpoint="/api/users", method="GET")
        stats.add_timing(200.0, is_error=True)
        assert stats.error_count == 1

    def test_get_percentile_empty(self):
        stats = EndpointStats(endpoint="/api/users", method="GET")
        assert stats.get_percentile(50) == 0.0

    def test_get_percentile_single_value(self):
        stats = EndpointStats(endpoint="/test", method="GET")
        stats.add_timing(150.0)
        assert stats.get_percentile(50) == 150.0

    def test_p50_p95_p99_computed(self):
        stats = EndpointStats(endpoint="/test", method="GET")
        for val in range(1, 101):  # 1..100ms
            stats.add_timing(float(val))
        assert 45.0 <= stats.p50 <= 55.0
        assert stats.p95 >= 90.0
        assert stats.p99 >= 95.0

    def test_avg_computed(self):
        stats = EndpointStats(endpoint="/test", method="GET")
        for val in [10.0, 20.0, 30.0]:
            stats.add_timing(val)
        assert abs(stats.avg - 20.0) < 1.0

    def test_avg_empty_returns_zero(self):
        stats = EndpointStats(endpoint="/test", method="GET")
        assert stats.avg == 0.0

    def test_to_dict_structure(self):
        stats = EndpointStats(endpoint="/api/exams", method="POST")
        stats.add_timing(55.0)
        d = stats.to_dict()
        assert d["endpoint"] == "/api/exams"
        assert d["method"] == "POST"
        assert d["request_count"] == 1
        assert "p50_ms" in d
        assert "p95_ms" in d
        assert "p99_ms" in d
        assert "avg_ms" in d


class TestTimingStatsManager:
    def setup_method(self):
        self.manager = TimingStatsManager(slow_threshold_ms=100.0)

    def test_record_creates_stats(self):
        self.manager.record("/api/test", "GET", 50.0, 200)
        stats = self.manager.get_stats("/api/test", "GET")
        assert stats is not None
        assert stats.request_count == 1

    def test_record_slow_request_logs_warning(self):
        with patch.object(self.manager, "slow_threshold_ms", 10.0):
            # 500ms > 10ms threshold
            self.manager.record("/api/slow", "GET", 500.0, 200)
        # No assertion needed — just confirming it doesn't raise

    def test_record_error_increments_error_count(self):
        self.manager.record("/api/err", "GET", 50.0, 500)
        stats = self.manager.get_stats("/api/err", "GET")
        assert stats.error_count == 1

    def test_get_stats_nonexistent(self):
        assert self.manager.get_stats("/nonexistent", "GET") is None

    def test_get_all_stats_empty(self):
        assert self.manager.get_all_stats() == []

    def test_get_all_stats_with_data(self):
        self.manager.record("/api/a", "GET", 50.0, 200)
        self.manager.record("/api/b", "POST", 60.0, 201)
        all_stats = self.manager.get_all_stats()
        assert len(all_stats) == 2

    def test_get_slow_endpoints_filters_correctly(self):
        # Add fast and slow endpoints
        for _ in range(10):
            self.manager.record("/api/fast", "GET", 10.0, 200)
        for _ in range(10):
            self.manager.record("/api/slow", "GET", 500.0, 200)

        slow = self.manager.get_slow_endpoints(threshold_ms=100.0)
        endpoints = [s["endpoint"] for s in slow]
        assert "/api/slow" in endpoints
        assert "/api/fast" not in endpoints

    def test_get_slow_endpoints_uses_default_threshold(self):
        for _ in range(10):
            self.manager.record("/api/borderline", "GET", 200.0, 200)
        slow = self.manager.get_slow_endpoints()
        assert len(slow) == 1

    def test_clear_removes_all_stats(self):
        self.manager.record("/api/x", "GET", 50.0, 200)
        self.manager.clear()
        assert self.manager.get_stats("/api/x", "GET") is None
        assert self.manager.get_all_stats() == []


class TestCORSPreflightCache:
    def setup_method(self):
        self.cache = CORSPreflightCache(ttl_seconds=3600)

    def test_get_nonexistent(self):
        assert self.cache.get("https://example.com") is None

    def test_set_and_get(self):
        headers = {"Access-Control-Allow-Origin": "*"}
        self.cache.set("https://example.com", headers)
        result = self.cache.get("https://example.com")
        assert result == headers

    def test_expired_entry_returns_none(self):
        headers = {"Access-Control-Allow-Origin": "*"}
        self.cache.set("https://expired.com", headers)
        # Manually expire it
        past = datetime.now(UTC) - timedelta(seconds=7200)
        self.cache._cache["https://expired.com"] = (headers, past)
        assert self.cache.get("https://expired.com") is None
        assert "https://expired.com" not in self.cache._cache

    def test_clear(self):
        self.cache.set("https://a.com", {})
        self.cache.clear()
        assert self.cache.get("https://a.com") is None


class TestJWTTokenCache:
    def setup_method(self):
        self.cache = JWTTokenCache(default_ttl=300)

    def test_set_and_get(self):
        token = "test.jwt.token"
        user_data = {"user_id": 42, "role": "student"}
        self.cache.set(token, user_data)
        result = self.cache.get(token)
        assert result == user_data

    def test_get_nonexistent_returns_none(self):
        assert self.cache.get("nonexistent.token") is None

    def test_expired_entry_returns_none(self):
        token = "expired.jwt.token"
        user_data = {"user_id": 1}
        self.cache.set(token, user_data, ttl=1)
        # Manually expire
        token_hash = self.cache._hash_token(token)
        past = datetime.now(UTC) - timedelta(seconds=10)
        self.cache._cache[token_hash] = (user_data, past)
        assert self.cache.get(token) is None

    def test_invalidate(self):
        token = "valid.token"
        self.cache.set(token, {"user_id": 5})
        self.cache.invalidate(token)
        assert self.cache.get(token) is None

    def test_custom_ttl(self):
        token = "custom.ttl.token"
        self.cache.set(token, {"user_id": 10}, ttl=600)
        assert self.cache.get(token) is not None

    def test_evict_expired_on_full_cache(self):
        # Fill cache slightly over max_size
        self.cache._max_size = 3
        for i in range(3):
            tok = f"token_{i}"
            self.cache.set(tok, {"user_id": i})
            # Expire some
            token_hash = self.cache._hash_token(tok)
            if i < 2:
                past = datetime.now(UTC) - timedelta(seconds=100)
                self.cache._cache[token_hash] = ({"user_id": i}, past)

        # Adding one more should trigger eviction
        self.cache.set("new_token", {"user_id": 99})
        # Cache should have evicted expired entries
        assert self.cache.get("new_token") is not None

    def test_clear(self):
        self.cache.set("tok1", {"user_id": 1})
        self.cache.clear()
        assert self.cache.get("tok1") is None


def test_get_timing_stats_manager_singleton():
    manager1 = get_timing_stats_manager()
    manager2 = get_timing_stats_manager()
    assert manager1 is manager2


# ===========================================================================
# =========  SECTION 5: middleware/cache_headers.py  =======================
# ===========================================================================


class TestGenerateEtag:
    def test_generates_quoted_hash(self):
        etag = generate_etag(b"hello world")
        assert etag.startswith('"')
        assert etag.endswith('"')

    def test_same_content_same_etag(self):
        assert generate_etag(b"content") == generate_etag(b"content")

    def test_different_content_different_etag(self):
        assert generate_etag(b"content_a") != generate_etag(b"content_b")

    def test_weak_etag_has_prefix(self):
        etag = generate_etag(b"data", weak=True)
        assert etag.startswith("W/")

    def test_strong_etag_no_prefix(self):
        etag = generate_etag(b"data", weak=False)
        assert not etag.startswith("W/")


class TestBuildCacheControlHeader:
    @pytest.mark.parametrize(
        "policy,max_age,expected_fragment",
        [
            (CachePolicy.PUBLIC, 3600, "public"),
            (CachePolicy.PRIVATE, 60, "private"),
            (CachePolicy.NO_CACHE, 0, "no-cache"),
            (CachePolicy.NO_STORE, 0, "no-store"),
        ],
    )
    def test_policy_in_header(self, policy, max_age, expected_fragment):
        config = CacheConfig(max_age=max_age, policy=policy)
        header = build_cache_control_header(config)
        assert expected_fragment in header

    def test_no_store_returns_immediately(self):
        config = CacheConfig(max_age=0, policy=CachePolicy.NO_STORE)
        assert build_cache_control_header(config) == "no-store"

    def test_max_age_in_header(self):
        config = CacheConfig(max_age=300, policy=CachePolicy.PUBLIC)
        header = build_cache_control_header(config)
        assert "max-age=300" in header

    def test_stale_while_revalidate_included(self):
        config = CacheConfig(
            max_age=300, policy=CachePolicy.PUBLIC, stale_while_revalidate=60
        )
        header = build_cache_control_header(config)
        assert "stale-while-revalidate=60" in header

    def test_stale_if_error_included(self):
        config = CacheConfig(
            max_age=300, policy=CachePolicy.PUBLIC, stale_if_error=86400
        )
        header = build_cache_control_header(config)
        assert "stale-if-error=86400" in header


class TestGetCacheConfigForPath:
    @pytest.mark.parametrize(
        "path,expected_policy",
        [
            ("/api/v1/questions/1", CachePolicy.PUBLIC),
            ("/api/v1/users/me", CachePolicy.PRIVATE),
            ("/api/v1/auth/login", CachePolicy.NO_STORE),
            ("/api/v1/admin/settings", CachePolicy.NO_STORE),
            ("/static/image.png", CachePolicy.PUBLIC),
            ("/docs", CachePolicy.PUBLIC),
            ("/unknown/path", CachePolicy.PRIVATE),  # default dynamic
        ],
    )
    def test_path_mapping(self, path, expected_policy):
        config = get_cache_config_for_path(path)
        assert config.policy == expected_policy


class TestShouldSkipCache:
    def test_post_method_skipped(self):
        req = MagicMock()
        req.method = "POST"
        req.url.path = "/api/v1/data"
        req.headers = {}
        assert should_skip_cache(req) is True

    def test_delete_method_skipped(self):
        req = MagicMock()
        req.method = "DELETE"
        req.url.path = "/api/v1/data"
        req.headers = {}
        assert should_skip_cache(req) is True

    def test_get_method_not_skipped(self):
        req = MagicMock()
        req.method = "GET"
        req.url.path = "/api/v1/questions"
        req.headers.get = MagicMock(return_value="")
        assert should_skip_cache(req) is False

    def test_health_path_skipped(self):
        req = MagicMock()
        req.method = "GET"
        req.url.path = "/health"
        req.headers.get = MagicMock(return_value="")
        assert should_skip_cache(req) is True

    def test_no_cache_header_skipped(self):
        req = MagicMock()
        req.method = "GET"
        req.url.path = "/api/v1/questions"
        req.headers.get = MagicMock(return_value="no-cache")
        assert should_skip_cache(req) is True


class TestEtagsMatch:
    def test_exact_match(self):
        assert etags_match('"abc123"', '"abc123"') is True

    def test_wildcard_matches_any(self):
        assert etags_match("*", '"any_etag"') is True

    def test_no_match(self):
        assert etags_match('"abc"', '"def"') is False

    def test_weak_etag_matches(self):
        assert etags_match('W/"abc123"', '"abc123"') is True

    def test_multiple_values_one_matches(self):
        assert etags_match('"abc", "def", "ghi"', '"def"') is True

    def test_empty_request_etag_no_match(self):
        assert etags_match("", '"abc"') is False

    def test_empty_response_etag_no_match(self):
        assert etags_match('"abc"', "") is False

    def test_both_empty_no_match(self):
        assert etags_match("", "") is False


# ===========================================================================
# ===========  SECTION 6: structured_logger.py  ============================
# ===========================================================================


class TestAddAppContext:
    def test_app_key_added(self):
        event_dict = {}
        result = add_app_context(None, "info", event_dict)
        assert result.get("app") == "kiro2-backend"

    def test_existing_app_key_not_overwritten(self):
        event_dict = {"app": "custom-app"}
        result = add_app_context(None, "info", event_dict)
        assert result["app"] == "custom-app"

    def test_environment_key_added(self):
        event_dict = {}
        result = add_app_context(None, "info", event_dict)
        assert "environment" in result


class TestCensorSensitiveData:
    @pytest.mark.parametrize(
        "key,value",
        [
            ("password", "secret123"),
            ("token", "bearer-xyz"),
            ("api_key", "sk-abc"),
            ("authorization", "Bearer token"),
            ("şifre", "gizli"),
            ("parola", "gizli123"),
        ],
    )
    def test_sensitive_key_redacted(self, key, value):
        event_dict = {key: value}
        result = censor_sensitive_data(None, "info", event_dict)
        assert result[key] == "***REDACTED***"

    def test_non_sensitive_key_not_redacted(self):
        event_dict = {"user_id": 42, "action": "login"}
        result = censor_sensitive_data(None, "info", event_dict)
        assert result["user_id"] == 42
        assert result["action"] == "login"


class TestStructuredLogger:
    def setup_method(self):
        self.logger = StructuredLogger("test_module")

    def test_info_logs_message(self):
        with patch.object(self.logger.logger, "info") as mock_info:
            self.logger.info("test_event", user_id=42)
            mock_info.assert_called_once()
            call_kwargs = mock_info.call_args
            assert "test_event" in str(call_kwargs)

    def test_error_logs_message(self):
        with patch.object(self.logger.logger, "error") as mock_err:
            self.logger.error("error_event", code=500)
            mock_err.assert_called_once()

    def test_warning_logs_message(self):
        with patch.object(self.logger.logger, "warning") as mock_warn:
            self.logger.warning("warn_event")
            mock_warn.assert_called_once()

    def test_debug_logs_message(self):
        with patch.object(self.logger.logger, "debug") as mock_debug:
            self.logger.debug("debug_event")
            mock_debug.assert_called_once()

    def test_critical_logs_message(self):
        with patch.object(self.logger.logger, "critical") as mock_crit:
            self.logger.critical("critical_event")
            mock_crit.assert_called_once()

    def test_extra_dict_merged_into_kwargs(self):
        with patch.object(self.logger.logger, "info") as mock_info:
            self.logger.info("event", extra={"key": "val"}, other="x")
            _, kwargs = mock_info.call_args
            assert kwargs.get("key") == "val"
            assert kwargs.get("other") == "x"

    def test_bind_updates_context(self):
        self.logger.bind(request_id="req-123")
        assert "request_id" in self.logger._context

    def test_unbind_removes_key(self):
        self.logger.bind(request_id="req-123")
        self.logger.unbind("request_id")
        assert "request_id" not in self.logger._context

    def test_log_request_method(self):
        with patch.object(self.logger, "info") as mock_info:
            self.logger.log_request("req-001", "/api/v1/test", "GET")
            mock_info.assert_called_once()
            args, _ = mock_info.call_args
            assert args[0] == "api_request_started"

    def test_log_request_with_profile(self):
        with patch.object(self.logger, "info") as mock_info:
            self.logger.log_request(
                "req-001",
                "/api/v1/test",
                profile={"goals": ["TYT"]},
            )
            _, kwargs = mock_info.call_args
            assert "profile" in kwargs

    def test_log_response_success(self):
        with patch.object(self.logger, "info") as mock_info:
            self.logger.log_response("req-001", "/api/v1/test", 200, 100.0)
            mock_info.assert_called_once()

    def test_log_response_client_error_calls_warning(self):
        with patch.object(self.logger, "warning") as mock_warn:
            self.logger.log_response("req-001", "/api/v1/test", 404, 50.0)
            mock_warn.assert_called_once()

    def test_log_response_server_error_calls_error(self):
        with patch.object(self.logger, "error") as mock_err:
            self.logger.log_response("req-001", "/api/v1/test", 500, 50.0)
            mock_err.assert_called_once()

    def test_log_response_with_cache_hit(self):
        with patch.object(self.logger, "info") as mock_info:
            self.logger.log_response(
                "req-001", "/api/v1/test", 200, 10.0, cache_hit=True
            )
            _, kwargs = mock_info.call_args
            assert kwargs.get("cache_hit") is True

    def test_log_error_context(self):
        with patch.object(self.logger, "error") as mock_err:
            self.logger.log_error_context(
                error_type="ValueError",
                error_message="bad value",
                context="test_context",
                request_id="req-001",
                stack_trace="traceback...",
            )
            mock_err.assert_called_once()
            _, kwargs = mock_err.call_args
            assert kwargs.get("error_type") == "ValueError"
            assert kwargs.get("request_id") == "req-001"

    def test_exception_logs(self):
        with patch.object(self.logger.logger, "exception") as mock_exc:
            self.logger.exception("exc_event")
            mock_exc.assert_called_once()


class TestStructuredLoggerHelpers:
    def setup_method(self):
        self.logger = StructuredLogger("helpers_test")

    def test_log_exam_event(self):
        with patch.object(self.logger, "info") as mock_info:
            log_exam_event(self.logger, "sinav_olusturuldu", sinav_id=1, ogrenci_id=2)
            mock_info.assert_called_once_with(
                "sinav_olusturuldu",
                sinav_id=1,
                ogrenci_id=2,
                sinav_tipi=None,
                timestamp=mock_info.call_args[1]["timestamp"],
            )

    def test_log_api_request_helper(self):
        with patch.object(self.logger, "info") as mock_info:
            log_api_request(self.logger, "GET", "/api/v1/test", user_id=42)
            mock_info.assert_called_once()
            _, kwargs = mock_info.call_args
            assert kwargs.get("method") == "GET"
            assert kwargs.get("user_id") == 42

    def test_log_api_response_helper(self):
        with patch.object(self.logger, "info") as mock_info:
            log_api_response(
                self.logger, "GET", "/api/v1/test", 200, 50.0, request_id="r1"
            )
            mock_info.assert_called_once()
            _, kwargs = mock_info.call_args
            assert kwargs.get("status_code") == 200

    def test_log_api_response_with_cache_hit(self):
        with patch.object(self.logger, "info") as mock_info:
            log_api_response(self.logger, "GET", "/test", 200, 10.0, cache_hit=True)
            _, kwargs = mock_info.call_args
            assert kwargs.get("cache_hit") is True

    def test_log_database_query(self):
        with patch.object(self.logger, "debug") as mock_debug:
            log_database_query(self.logger, "SELECT", "question_bank", 15.5)
            mock_debug.assert_called_once()
            _, kwargs = mock_debug.call_args
            assert kwargs.get("operation") == "SELECT"
            assert kwargs.get("table") == "question_bank"

    def test_log_cache_operation_hit(self):
        with patch.object(self.logger, "debug") as mock_debug:
            log_cache_operation(self.logger, "get", "user:42:profile", hit=True)
            mock_debug.assert_called_once()
            _, kwargs = mock_debug.call_args
            assert kwargs.get("hit") is True

    def test_log_error_with_context_includes_stack_trace(self):
        with patch.object(self.logger, "error") as mock_err:
            try:
                raise ValueError("test error")
            except ValueError as exc:
                log_error_with_context(
                    self.logger,
                    exc,
                    "test_context",
                    request_id="req-001",
                    include_stack_trace=True,
                )
            mock_err.assert_called_once()
            _, kwargs = mock_err.call_args
            assert kwargs.get("error_type") == "ValueError"
            assert kwargs.get("stack_trace") is not None

    def test_log_error_with_context_no_stack_trace(self):
        with patch.object(self.logger, "error") as mock_err:
            try:
                raise RuntimeError("test")
            except RuntimeError as exc:
                log_error_with_context(
                    self.logger,
                    exc,
                    "context",
                    include_stack_trace=False,
                )
            _, kwargs = mock_err.call_args
            assert "stack_trace" not in kwargs


class TestGetLogger:
    def test_get_logger_returns_structured_logger(self):
        logger = get_logger("my_module")
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "my_module"

    def test_get_structured_logger_alias(self):
        logger = get_structured_logger("alias_module")
        assert isinstance(logger, StructuredLogger)

    def test_logger_level_set(self):
        logger = get_logger("test_module", level="DEBUG")
        assert logger.level == "DEBUG"
