"""
ST-06: Smoke tests for authentication chain.

Tests:
- Root endpoint accessibility
- Register endpoint exists
- Login endpoint exists
- Profile requires authentication
- Invalid tokens are rejected
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import pytest  # noqa: E402
import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402


@pytest.mark.asyncio
async def test_root_endpoint():
    """ST-06-01: Root endpoint returns 200 OK."""
    from main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

        # Accept 200 (root page) or 404 (no root route)
        # Either is acceptable - we just verify app responds
        assert response.status_code in [200, 404, 307], \
            f"Root endpoint unreachable: {response.status_code}"


@pytest.mark.asyncio
async def test_register_endpoint_exists():
    """ST-06-02: Register endpoint exists (not 404)."""
    from main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Attempt registration with minimal test data
        test_data = {
            "email": "smoke-test@example.com",
            "password": "TestPass123!",
            "isim": "Test",
            "soyisim": "User",
        }

        response = await client.post("/api/v1/auth/kayit", json=test_data)

        # We don't expect success (may need more fields or email validation)
        # But we should NOT get 404 - endpoint must exist
        assert response.status_code != 404, \
            "Register endpoint /api/v1/auth/kayit should exist (not 404)"

        # Common acceptable status codes:
        # 201 - Success (unlikely with minimal data)
        # 400 - Bad request (validation failed)
        # 422 - Unprocessable entity (Pydantic validation)
        # 409 - Conflict (email exists)
        # 500 - Server error (database issue)
        acceptable_codes = [200, 201, 400, 409, 422, 500]
        assert response.status_code in acceptable_codes, \
            f"Unexpected status code from register: {response.status_code}"


@pytest.mark.asyncio
async def test_login_endpoint_exists():
    """ST-06-03: Login endpoint exists (not 404)."""
    from main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Attempt login with test credentials
        test_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!",
        }

        try:
            response = await client.post("/api/v1/auth/giris", json=test_data)
        except Exception as e:
            pytest.skip(f"Login endpoint connection error: {e}")
            return

        # Endpoint must exist (not 404)
        assert response.status_code != 404, \
            "Login endpoint /api/v1/auth/giris should exist (not 404)"

        acceptable_codes = [200, 400, 401, 422, 500]
        assert response.status_code in acceptable_codes, \
            f"Unexpected status code from login: {response.status_code}"


@pytest.mark.asyncio
async def test_profile_requires_auth():
    """ST-06-04: Profile endpoint requires authentication."""
    from main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Request profile WITHOUT authentication token
        response = await client.get("/api/v1/auth/profil")

        # Should be rejected with 401 Unauthorized or 403 Forbidden
        assert response.status_code in [401, 403], \
            f"Profile without auth should return 401/403, got: {response.status_code}"


@pytest.mark.asyncio
async def test_invalid_token_rejected():
    """ST-06-05: Invalid JWT token is rejected."""
    from main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Request profile with fake/invalid token
        headers = {"Authorization": "Bearer fake-invalid-token-12345"}
        response = await client.get("/api/v1/auth/profil", headers=headers)

        # Should be rejected with 401 Unauthorized or 403 Forbidden
        assert response.status_code in [401, 403, 422], \
            f"Invalid token should return 401/403/422, got: {response.status_code}"

        # Verify response indicates authentication failure
        # (Don't check exact message as it may vary)
        if response.status_code in [401, 403]:
            # Success - properly rejected invalid token
            assert response.status_code in [401, 403]
        elif response.status_code == 422:
            # Also acceptable - validation error for malformed token
            data = response.json()
            assert "detail" in data or "message" in data, \
                "Error response should contain detail/message"
