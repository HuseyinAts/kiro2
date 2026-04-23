"""Tests for AuthenticationMiddleware from security_middleware.py"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.datastructures import Headers, QueryParams
from starlette.responses import JSONResponse

import backend.core.security_middleware as sec_mod

# Patch broken fastapi.middleware.base import before loading the module
import backend.tests.conftest_security  # noqa: F401

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    path: str = "/api/v1/resource",
    method: str = "GET",
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    query_params: dict[str, str] | None = None,
    client_host: str = "127.0.0.1",
) -> MagicMock:
    """Build a mock Starlette Request."""
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

    state = MagicMock()
    req.state = state
    return req


def _async_call_next(status_code: int = 200) -> AsyncMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {}
    return AsyncMock(return_value=resp)


# ---------------------------------------------------------------------------
# Fixture: patch heavy deps via patch.object on the already-imported module
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_imports() -> Any:
    mock_auth_mgr = MagicMock()
    mock_auth_mgr.token_manager = MagicMock()
    mock_auth_mgr.session_manager = MagicMock()

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
        patch.object(sec_mod, "async_error_context", return_value=async_cm),
        patch.object(sec_mod, "log_error", new_callable=AsyncMock),
        patch.object(sec_mod, "error_response", return_value=err_obj),
    ):
        yield mock_auth_mgr


def _build_middleware(
    auth_manager: MagicMock,
    enable_authentication: bool = True,
    exempt_paths: list[str] | None = None,
    required_paths: list[str] | None = None,
) -> sec_mod.AuthenticationMiddleware:
    """Instantiate AuthenticationMiddleware with patched deps."""
    config = sec_mod.SecurityMiddlewareConfig(
        enable_authentication=enable_authentication,
        authentication_exempt_paths=exempt_paths or ["/health", "/docs"],
        authentication_required_paths=required_paths or ["/api/"],
    )
    app = MagicMock()
    mw = sec_mod.AuthenticationMiddleware.__new__(sec_mod.AuthenticationMiddleware)
    mw.config = config
    mw.auth_manager = auth_manager
    mw.security_bearer = MagicMock()
    mw.app = app
    return mw


# ===========================================================================
# _is_exempt_path
# ===========================================================================


class TestIsExemptPath:
    """Tests for AuthenticationMiddleware._is_exempt_path"""

    def test_health_is_exempt(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        assert mw._is_exempt_path("/health") is True

    def test_docs_is_exempt(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        assert mw._is_exempt_path("/docs") is True

    def test_docs_subpath_is_exempt(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        assert mw._is_exempt_path("/docs/openapi.json") is True

    def test_api_path_not_exempt(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        assert mw._is_exempt_path("/api/v1/users") is False

    def test_random_path_not_exempt(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        assert mw._is_exempt_path("/admin") is False


# ===========================================================================
# _requires_authentication
# ===========================================================================


class TestRequiresAuthentication:
    """Tests for AuthenticationMiddleware._requires_authentication"""

    def test_api_path_requires_auth(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        assert mw._requires_authentication("/api/v1/users") is True

    def test_non_api_path_does_not_require_auth(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        assert mw._requires_authentication("/static/main.js") is False

    def test_disabled_auth_returns_false(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports, enable_authentication=False)
        assert mw._requires_authentication("/api/v1/users") is False


# ===========================================================================
# _authenticate_jwt
# ===========================================================================


class TestAuthenticateJwt:
    """Tests for AuthenticationMiddleware._authenticate_jwt"""

    @pytest.mark.asyncio
    async def test_valid_bearer_token(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)

        payload = MagicMock()
        payload.user_id = "user-1"
        payload.username = "test"
        payload.email = "test@example.com"
        payload.role = "student"
        payload.permissions = ["read"]
        payload.session_id = None

        mw.auth_manager.token_manager.verify_token.return_value = payload

        req = _make_request(headers={"authorization": "Bearer valid-token-123"})
        result = await mw._authenticate_jwt(req)

        assert result["success"] is True
        assert result["user"]["id"] == "user-1"
        assert result["user"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_missing_auth_header(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        req = _make_request(headers={})
        result = await mw._authenticate_jwt(req)

        assert result["success"] is False
        assert "No bearer token" in result["reason"]

    @pytest.mark.asyncio
    async def test_malformed_header_basic_scheme(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        req = _make_request(headers={"authorization": "Basic dXNlcjpwYXNz"})
        result = await mw._authenticate_jwt(req)

        assert result["success"] is False
        assert "No bearer token" in result["reason"]

    @pytest.mark.asyncio
    async def test_expired_token(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        mw.auth_manager.token_manager.verify_token.return_value = None

        req = _make_request(headers={"authorization": "Bearer expired-token"})
        result = await mw._authenticate_jwt(req)

        assert result["success"] is False
        assert "Invalid or expired" in result["reason"]


# ===========================================================================
# _authenticate_api_key
# ===========================================================================


class TestAuthenticateApiKey:
    """Tests for AuthenticationMiddleware._authenticate_api_key"""

    @pytest.mark.asyncio
    async def test_missing_api_key(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        req = _make_request(headers={})
        result = await mw._authenticate_api_key(req)

        assert result["success"] is False
        assert "No API key" in result["reason"]


# ===========================================================================
# _authenticate_session
# ===========================================================================


class TestAuthenticateSession:
    """Tests for AuthenticationMiddleware._authenticate_session"""

    @pytest.mark.asyncio
    async def test_missing_session_cookie(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        req = _make_request(cookies={})
        result = await mw._authenticate_session(req)

        assert result["success"] is False
        assert "No session cookie" in result["reason"]


# ===========================================================================
# _authenticate_request (fallback chain)
# ===========================================================================


class TestAuthenticateRequest:
    """Tests for AuthenticationMiddleware._authenticate_request fallback chain"""

    @pytest.mark.asyncio
    async def test_all_methods_fail(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        mw.auth_manager.token_manager.verify_token.return_value = None

        req = _make_request(headers={}, cookies={})
        result = await mw._authenticate_request(req)

        assert result["success"] is False
        assert "No valid authentication" in result["reason"]

    @pytest.mark.asyncio
    async def test_jwt_succeeds_skips_others(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)

        payload = MagicMock()
        payload.user_id = "u1"
        payload.username = "u"
        payload.email = "u@e.com"
        payload.role = "admin"
        payload.permissions = []
        payload.session_id = None

        mw.auth_manager.token_manager.verify_token.return_value = payload

        req = _make_request(headers={"authorization": "Bearer good"})
        result = await mw._authenticate_request(req)

        assert result["success"] is True
        assert result["user"]["id"] == "u1"


# ===========================================================================
# dispatch
# ===========================================================================


class TestAuthMiddlewareDispatch:
    """Tests for AuthenticationMiddleware.dispatch"""

    @pytest.mark.asyncio
    async def test_exempt_path_passes_through(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        req = _make_request(path="/health")
        call_next = _async_call_next(200)

        resp = await mw.dispatch(req, call_next)

        call_next.assert_awaited_once_with(req)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_authenticated_request_passes(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)

        payload = MagicMock()
        payload.user_id = "u1"
        payload.username = "u"
        payload.email = "u@e.com"
        payload.role = "student"
        payload.permissions = []
        payload.session_id = None

        mw.auth_manager.token_manager.verify_token.return_value = payload

        req = _make_request(path="/api/v1/data", headers={"authorization": "Bearer tok"})
        call_next = _async_call_next(200)

        resp = await mw.dispatch(req, call_next)

        call_next.assert_awaited_once()
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_api_returns_401(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        mw.auth_manager.token_manager.verify_token.return_value = None

        req = _make_request(path="/api/v1/data", headers={}, cookies={})
        call_next = _async_call_next(200)

        resp = await mw.dispatch(req, call_next)

        assert isinstance(resp, JSONResponse)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_non_api_path_skips_auth(self, _patch_imports: Any) -> None:
        mw = _build_middleware(_patch_imports)
        req = _make_request(path="/static/logo.png")
        call_next = _async_call_next(200)

        resp = await mw.dispatch(req, call_next)

        call_next.assert_awaited_once_with(req)
        assert resp.status_code == 200
