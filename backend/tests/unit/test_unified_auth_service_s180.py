"""S180 smoke tests for core/unified_auth_service.py (was 0% coverage).

Targets enum + dataclass surface + factory `get_auth_service()`. Real
JWT/2FA flows need integration tests with DB; this file just ensures
the module is loaded and basic invariants hold. Without this, the
audit-detected 0% coverage masks any future regression in the
397-LOC service.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.unified_auth_service import (
    AuthEvent,
    Permission,
    TokenPair,
    TokenPayload,
    TokenType,
    UserRole,
    get_auth_service,
)

# ---- Enums ----


def test_userrole_enum_has_canonical_roles():
    # KIRO2 has 4+ roles per CLAUDE.md mapping (STUDENT↔ogrenci dict)
    values = {r.value for r in UserRole}
    assert "student" in values or "STUDENT" in values
    assert len(values) >= 3, f"Expected ≥3 roles, got {values}"


def test_tokentype_enum_has_access_refresh():
    values = {t.value for t in TokenType}
    # Pre-condition: access + refresh tokens supported
    assert any("access" in v.lower() for v in values), values
    assert any("refresh" in v.lower() for v in values), values


def test_permission_enum_nonempty():
    perms = list(Permission)
    assert len(perms) > 0, "Permission enum must define at least one value"


def test_authevent_enum_has_login_events():
    values = {e.value for e in AuthEvent}
    assert "login_success" in values
    assert "login_failed" in values
    assert "logout" in values
    assert "token_refresh" in values
    # 2FA observability
    assert "2fa_verified" in values
    assert "2fa_failed" in values


# ---- Dataclasses ----


def test_tokenpayload_can_be_constructed():
    """TokenPayload is the core JWT body — must be instantiable."""
    now = datetime.now(UTC)
    payload = TokenPayload(
        sub="user-123",
        email="test@example.com",
        role=next(iter(UserRole)),
        exp=now + timedelta(minutes=15),
        iat=now,
        type=next(iter(TokenType)),
        jti="jti-test",
    )
    assert payload.sub == "user-123"
    assert payload.email == "test@example.com"
    assert payload.jti == "jti-test"
    # Defaults
    assert payload.permissions == []
    assert payload.device_id is None
    assert payload.session_id is None


def test_tokenpair_dataclass_smoke():
    """TokenPair is the public return of issue_tokens() — must instantiate."""
    # TokenPair fields vary; just ensure the class exists and is a dataclass
    import dataclasses

    assert dataclasses.is_dataclass(TokenPair), "TokenPair must be a dataclass"


# ---- Factory ----


def test_get_auth_service_returns_instance():
    """The module-level factory must produce a usable singleton."""
    svc = get_auth_service()
    assert svc is not None
    # Re-call should return the same instance (singleton invariant)
    svc2 = get_auth_service()
    assert svc is svc2, "get_auth_service() must be idempotent (singleton)"


def test_get_auth_service_has_core_methods():
    """The UnifiedAuthService class must expose the documented surface."""
    svc = get_auth_service()
    # Smoke-check method presence (don't call — need DB)
    expected_attrs = ["pwd_context"]  # passlib context for bcrypt
    for attr in expected_attrs:
        assert hasattr(svc, attr), f"UnifiedAuthService missing {attr}"


# ---- Anti-regression: passlib import ----


def test_passlib_cryptcontext_imported():
    """auth.py reverted from a passlib-shim back to passlib.context.CryptContext
    in S179. This test guards against re-introduction of the shim.
    """
    from passlib.context import CryptContext

    import core.unified_auth_service as m

    # The module must import CryptContext from passlib.context (real lib).
    assert m.CryptContext is CryptContext, (
        "unified_auth_service must use passlib.context.CryptContext, "
        "not a custom shim (see S179 revert)."
    )
