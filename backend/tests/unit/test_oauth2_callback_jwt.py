"""
Regression test: OAuth2 callback (api/enhanced_auth_api.py) must issue a
real signed JWT, not a random string.

Bug: oauth2_callback() called secrets.token_urlsafe(32) for both
access_token and refresh_token instead of using jwt_manager — a user who
logs in via "Google ile giriş" received tokens that fail JWT validation
on every subsequent request to a protected endpoint.
"""

import sys

sys.path.insert(0, "C:/Users/husey/kiro2/backend")

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import jwt
import pytest

from api.enhanced_auth_api import oauth2_callback
from core.config import get_settings
from models.enums_db import UserRole


def _fake_oauth2_service(fake_user: SimpleNamespace) -> AsyncMock:
    service = AsyncMock()
    service.exchange_code.return_value = {"access_token": "provider-access-token"}
    service.get_user_info.return_value = SimpleNamespace(email=fake_user.email)
    service.link_or_create_user.return_value = fake_user
    return service


@pytest.mark.asyncio
async def test_oauth2_callback_returns_real_decodable_jwt() -> None:
    fake_user = SimpleNamespace(
        id="user-123",
        email="ogrenci@example.com",
        first_name="Ali",
        last_name="Veli",
        role=UserRole.STUDENT,
        is_active=True,
    )

    with patch(
        "api.enhanced_auth_api.get_oauth2_service",
        return_value=_fake_oauth2_service(fake_user),
    ):
        result = await oauth2_callback(
            provider="google",
            code="auth-code",
            state="state-value",
            db=AsyncMock(),
        )

    from core.jwt_auth import get_jwt_manager

    jwt_mgr = get_jwt_manager()
    payload = jwt.decode(
        result["token"], jwt_mgr.secret_key, algorithms=[jwt_mgr.algorithm]
    )
    assert payload["sub"] == fake_user.id
    assert payload["email"] == fake_user.email
    assert payload["type"] == "access"

    refresh_payload = jwt.decode(
        result["refreshToken"],
        jwt_mgr.secret_key,
        algorithms=[jwt_mgr.algorithm],
    )
    assert refresh_payload["sub"] == fake_user.id
    assert refresh_payload["type"] == "refresh"
