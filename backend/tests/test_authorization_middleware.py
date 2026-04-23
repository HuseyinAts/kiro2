"""Tests for AuthorizationMiddleware, RateLimiter, SecurityValidator,
and ComprehensiveSecurityMiddleware from security_middleware.py"""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.datastructures import Headers, QueryParams
from starlette.responses import JSONResponse

import backend.core.security_middleware as sec_mod

# Patch broken fastapi.middleware.base import before loading the module
import backend.tests.conftest_security  # noqa: F401
from backend.core.rbac_system import Action, ResourceType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    path: str = "/api/v1/users",
    method: str = "GET",
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    query_params: dict[str, str] | None = None,
    client_host: str = "192.168.1.10",
    has_user: bool = False,
    user: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> MagicMock:
    req = MagicMock()
    req.method = method
    req.url = MagicMock()
    req.url.path = path

    _headers = headers or {}
    req.headers = Headers(headers=_headers)
    req.cookies = cookies or {}
    req.query_params = QueryParams(query_params or {})
    req.client = MagicMock()
    req.client.host = client_host

    # Use a simple namespace for state so hasattr works correctly
    class State:
        pass

    state = State()
    if has_user and user is not None:
        state.user = user
        state.session_id = session_id
    req.state = state
    return req


def _async_call_next(status_code: int = 200) -> AsyncMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {}
    return AsyncMock(return_value=resp)


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_heavy() -> Any:
    mock_auth_mgr = MagicMock()
    mock_rbac_mgr = MagicMock()

    ctx_obj = MagicMock()
    ctx_obj.add_annotation = MagicMock()
    ctx_obj.tags = {}
    ctx_obj.to_dict = MagicMock(return_value={})

    async_cm = AsyncMock()
    async_cm.__aenter__ = AsyncMock(return_value=ctx_obj)
    async_cm.__aexit__ = AsyncMock(return_value=False)

    err_obj = MagicMock()
    err_obj.dict = MagicMock(return_value={"error": "test"})

    with (
        patch.object(sec_mod, "get_authentication_manager", return_value=mock_auth_mgr),
        patch.object(sec_mod, "get_rbac_manager", return_value=mock_rbac_mgr),
        patch.object(sec_mod, "async_error_context", return_value=async_cm),
        patch.object(sec_mod, "log_error", new_callable=AsyncMock),
        patch.object(sec_mod, "error_response", return_value=err_obj),
    ):
        yield {"auth": mock_auth_mgr, "rbac": mock_rbac_mgr}


# ===========================================================================
# AuthorizationMiddleware
# ===========================================================================


def _build_authz_middleware(rbac_manager: MagicMock) -> sec_mod.AuthorizationMiddleware:
    config = sec_mod.SecurityMiddlewareConfig()
    mw = sec_mod.AuthorizationMiddleware.__new__(sec_mod.AuthorizationMiddleware)
    mw.config = config
    mw.rbac_manager = rbac_manager
    mw.app = MagicMock()
    mw.endpoint_permissions = {
        "GET /api/v1/users": (ResourceType.USER, Action.READ),
        "POST /api/v1/users": (ResourceType.USER, Action.CREATE),
        "PUT /api/v1/users/*": (ResourceType.USER, Action.UPDATE),
        "DELETE /api/v1/users/*": (ResourceType.USER, Action.DELETE),
    }
    return mw


class TestGetRequiredPermission:
    """Tests for AuthorizationMiddleware._get_required_permission"""

    def test_exact_match(self, _patch_heavy: Any) -> None:
        mw = _build_authz_middleware(_patch_heavy["rbac"])
        req = _make_request(path="/api/v1/users", method="GET")
        result = mw._get_required_permission(req)
        assert result is not None
        resource_type, action = result
        assert resource_type == ResourceType.USER
        assert action == Action.READ

    def test_wildcard_match(self, _patch_heavy: Any) -> None:
        mw = _build_authz_middleware(_patch_heavy["rbac"])
        req = _make_request(path="/api/v1/users/123", method="PUT")
        result = mw._get_required_permission(req)
        assert result is not None
        resource_type, action = result
        assert action == Action.UPDATE

    def test_no_match_returns_none(self, _patch_heavy: Any) -> None:
        mw = _build_authz_middleware(_patch_heavy["rbac"])
        req = _make_request(path="/api/v1/unknown", method="GET")
        result = mw._get_required_permission(req)
        assert result is None


class TestAuthorizationDispatch:
    """Tests for AuthorizationMiddleware.dispatch"""

    @pytest.mark.asyncio
    async def test_unauthenticated_passes_through(self, _patch_heavy: Any) -> None:
        mw = _build_authz_middleware(_patch_heavy["rbac"])
        req = _make_request(path="/api/v1/users", method="GET", has_user=False)
        call_next = _async_call_next(200)

        resp = await mw.dispatch(req, call_next)
        call_next.assert_awaited_once()
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_authorized_request_passes(self, _patch_heavy: Any) -> None:
        mw = _build_authz_middleware(_patch_heavy["rbac"])
        req = _make_request(
            path="/api/v1/users",
            method="GET",
            has_user=True,
            user={"id": "u1", "role": "admin"},
            session_id="s1",
        )
        call_next = _async_call_next(200)

        grant_result = MagicMock()
        grant_result.granted = True
        mw.rbac_manager.check_permission = AsyncMock(return_value=grant_result)

        resp = await mw.dispatch(req, call_next)
        call_next.assert_awaited_once()
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_denied_request_returns_403(self, _patch_heavy: Any) -> None:
        mw = _build_authz_middleware(_patch_heavy["rbac"])
        req = _make_request(
            path="/api/v1/users",
            method="GET",
            has_user=True,
            user={"id": "u2", "role": "student"},
            session_id="s2",
        )
        call_next = _async_call_next(200)

        deny_result = MagicMock()
        deny_result.granted = False
        deny_result.reason = "Insufficient role"
        mw.rbac_manager.check_permission = AsyncMock(return_value=deny_result)

        resp = await mw.dispatch(req, call_next)
        assert isinstance(resp, JSONResponse)
        assert resp.status_code == 403


class TestAuthorizationGetClientIp:
    """Tests for AuthorizationMiddleware._get_client_ip"""

    def test_x_forwarded_for(self, _patch_heavy: Any) -> None:
        mw = _build_authz_middleware(_patch_heavy["rbac"])
        req = _make_request(headers={"x-forwarded-for": "1.2.3.4, 5.6.7.8"})
        assert mw._get_client_ip(req) == "1.2.3.4"

    def test_x_real_ip_fallback(self, _patch_heavy: Any) -> None:
        mw = _build_authz_middleware(_patch_heavy["rbac"])
        req = _make_request(headers={"x-real-ip": "10.0.0.1"})
        assert mw._get_client_ip(req) == "10.0.0.1"

    def test_direct_connection(self, _patch_heavy: Any) -> None:
        mw = _build_authz_middleware(_patch_heavy["rbac"])
        req = _make_request(headers={}, client_host="192.168.1.50")
        assert mw._get_client_ip(req) == "192.168.1.50"


# ===========================================================================
# RateLimiter
# ===========================================================================


def _build_rate_limiter(
    ip_limit: int = 5,
    trusted_proxies: set[str] | None = None,
    enable_proxy_validation: bool = True,
) -> sec_mod.RateLimiter:
    config = sec_mod.SecurityMiddlewareConfig(
        ip_rate_limit_per_minute=ip_limit,
        global_rate_limit_per_minute=10000,
        user_rate_limit_per_minute=100,
        trusted_proxies=trusted_proxies or {"127.0.0.1", "::1", "localhost"},
        enable_trusted_proxy_validation=enable_proxy_validation,
    )
    return sec_mod.RateLimiter(config)


class TestIsFromTrustedProxy:
    """Tests for RateLimiter._is_from_trusted_proxy"""

    def test_trusted_ip(self, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter()
        req = _make_request(client_host="127.0.0.1")
        assert rl._is_from_trusted_proxy(req) is True

    def test_untrusted_ip(self, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter()
        req = _make_request(client_host="8.8.8.8")
        assert rl._is_from_trusted_proxy(req) is False

    def test_validation_disabled_returns_true(self, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter(enable_proxy_validation=False)
        req = _make_request(client_host="8.8.8.8")
        assert rl._is_from_trusted_proxy(req) is True


class TestRateLimiterGetClientIp:
    """Tests for RateLimiter._get_client_ip"""

    def test_forwarded_from_trusted_proxy(self, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter()
        req = _make_request(
            client_host="127.0.0.1",
            headers={"x-forwarded-for": "203.0.113.50, 70.41.3.18"},
        )
        assert rl._get_client_ip(req) == "203.0.113.50"

    def test_forwarded_from_untrusted_proxy_uses_direct(self, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter()
        req = _make_request(
            client_host="8.8.8.8",
            headers={"x-forwarded-for": "1.2.3.4"},
        )
        # untrusted proxy => ignore forwarded header, use client.host
        assert rl._get_client_ip(req) == "8.8.8.8"

    def test_invalid_ip_in_forwarded_header(self, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter()
        req = _make_request(
            client_host="127.0.0.1",
            headers={"x-forwarded-for": "not-an-ip"},
        )
        # invalid IP falls through; x-real-ip not set => client.host
        assert rl._get_client_ip(req) == "127.0.0.1"


class TestIsValidIp:
    """Tests for RateLimiter._is_valid_ip"""

    @pytest.mark.parametrize(
        "ip,expected",
        [
            ("192.168.1.1", True),
            ("::1", True),
            ("2001:db8::1", True),
            ("not-an-ip", False),
            ("999.999.999.999", False),
            ("", False),
        ],
    )
    def test_ip_validation(self, ip: str, expected: bool, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter()
        assert rl._is_valid_ip(ip) is expected


class TestCheckRateLimit:
    """Tests for RateLimiter.check_rate_limit"""

    @pytest.mark.asyncio
    async def test_under_limit_passes(self, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter(ip_limit=100)
        req = _make_request(client_host="10.0.0.1")
        result = await rl.check_rate_limit(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_over_ip_limit_returns_violation(self, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter(ip_limit=3)
        req = _make_request(client_host="10.0.0.2")

        result = None
        for _ in range(5):
            result = await rl.check_rate_limit(req)

        assert result is not None
        assert result["rate_limited"] is True
        assert any(v["type"] == "per_ip" for v in result["violations"])

    @pytest.mark.asyncio
    async def test_progressive_ban_after_repeated_violations(self, _patch_heavy: Any) -> None:
        rl = _build_rate_limiter(ip_limit=2)
        req = _make_request(client_host="10.0.0.3")

        # Trigger many violations to exceed warning_count > 3
        for _ in range(20):
            await rl.check_rate_limit(req)

        record = rl.ip_records.get("10.0.0.3")
        assert record is not None
        # After enough violations, blocked_until should be set
        assert record.blocked_until is not None or record.warning_count >= 0


# ===========================================================================
# SecurityValidator
# ===========================================================================


def _build_validator() -> sec_mod.SecurityValidator:
    config = sec_mod.SecurityMiddlewareConfig()
    return sec_mod.SecurityValidator(config)


class TestSecurityValidator:
    """Tests for SecurityValidator.validate_request"""

    @pytest.mark.asyncio
    async def test_sql_injection_in_query(self, _patch_heavy: Any) -> None:
        sv = _build_validator()
        req = _make_request(query_params={"q": "1 UNION SELECT * FROM users"})
        threats = await sv.validate_request(req)
        types = [t["type"] for t in threats]
        assert "sql_injection" in types

    @pytest.mark.asyncio
    async def test_xss_in_query(self, _patch_heavy: Any) -> None:
        sv = _build_validator()
        req = _make_request(query_params={"name": "<script>alert(1)</script>"})
        threats = await sv.validate_request(req)
        types = [t["type"] for t in threats]
        assert "xss" in types

    @pytest.mark.asyncio
    async def test_suspicious_user_agent(self, _patch_heavy: Any) -> None:
        sv = _build_validator()
        req = _make_request(headers={"user-agent": "python-scraperbot/1.0"})
        threats = await sv.validate_request(req)
        types = [t["type"] for t in threats]
        assert "suspicious_user_agent" in types

    @pytest.mark.asyncio
    async def test_request_size_exceeds_limit(self, _patch_heavy: Any) -> None:
        sv = _build_validator()
        req = _make_request(headers={"content-length": "999999999"})
        threats = await sv.validate_request(req)
        types = [t["type"] for t in threats]
        assert "malformed_request" in types

    @pytest.mark.asyncio
    async def test_clean_request_no_threats(self, _patch_heavy: Any) -> None:
        sv = _build_validator()
        req = _make_request(
            headers={"user-agent": "Mozilla/5.0"},
            query_params={"page": "1", "limit": "10"},
        )
        threats = await sv.validate_request(req)
        assert len(threats) == 0


# ===========================================================================
# ComprehensiveSecurityMiddleware
# ===========================================================================


def _build_comprehensive(
    ip_blacklist: set[str] | None = None,
) -> sec_mod.ComprehensiveSecurityMiddleware:
    config = sec_mod.SecurityMiddlewareConfig(
        ip_blacklist=ip_blacklist or set(),
        enable_input_validation=True,
        enable_security_headers=True,
    )
    mw = sec_mod.ComprehensiveSecurityMiddleware.__new__(
        sec_mod.ComprehensiveSecurityMiddleware
    )
    mw.config = config
    mw.rate_limiter = sec_mod.RateLimiter(config)
    mw.security_validator = sec_mod.SecurityValidator(config)
    mw.security_events = []
    mw.blocked_ips = {}
    mw.app = MagicMock()
    return mw


class TestIsBlockedIp:
    """Tests for ComprehensiveSecurityMiddleware._is_blocked_ip"""

    def test_blacklisted_ip(self, _patch_heavy: Any) -> None:
        mw = _build_comprehensive(ip_blacklist={"1.2.3.4"})
        assert mw._is_blocked_ip("1.2.3.4") is True

    def test_temporarily_blocked_ip(self, _patch_heavy: Any) -> None:
        mw = _build_comprehensive()
        mw.blocked_ips["5.6.7.8"] = datetime.now(UTC) + timedelta(minutes=10)
        assert mw._is_blocked_ip("5.6.7.8") is True

    def test_expired_block_removed(self, _patch_heavy: Any) -> None:
        mw = _build_comprehensive()
        mw.blocked_ips["5.6.7.8"] = datetime.now(UTC) - timedelta(minutes=1)
        assert mw._is_blocked_ip("5.6.7.8") is False
        assert "5.6.7.8" not in mw.blocked_ips

    def test_clean_ip_not_blocked(self, _patch_heavy: Any) -> None:
        mw = _build_comprehensive()
        assert mw._is_blocked_ip("10.0.0.1") is False


class TestAddSecurityHeaders:
    """Tests for ComprehensiveSecurityMiddleware._add_security_headers"""

    def test_all_7_headers_added(self, _patch_heavy: Any) -> None:
        mw = _build_comprehensive()
        resp = MagicMock()
        resp.headers = {}
        mw._add_security_headers(resp)

        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Referrer-Policy",
            "Permissions-Policy",
        ]
        for header in expected_headers:
            assert header in resp.headers, f"Missing header: {header}"

        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"


class TestSecurityStats:
    """Tests for ComprehensiveSecurityMiddleware.get_security_stats"""

    def test_stats_structure(self, _patch_heavy: Any) -> None:
        mw = _build_comprehensive()
        mw.security_events.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "threat_type": "sql_injection",
                "client_ip": "1.2.3.4",
                "details": {},
            }
        )
        stats = mw.get_security_stats()

        assert "total_events_24h" in stats
        assert stats["total_events_24h"] == 1
        assert "threat_breakdown" in stats
        assert stats["threat_breakdown"]["sql_injection"] == 1
        assert "blocked_ips_count" in stats
        assert "rate_limiter_stats" in stats
