"""F4: enhanced_user_management_api require_admin / require_admin_or_self."""

import pytest

from api.enhanced_user_management_api import require_admin, require_admin_or_self
from core.dependencies import AuthenticatedUser, UserRole
from core.exceptions import AuthorizationError, EnhancedServiceError


@pytest.mark.asyncio
async def test_require_admin_accepts_super_admin() -> None:
    u = AuthenticatedUser(
        id=1, username="a", role=UserRole.SUPER_ADMIN, email="a@x.com"
    )
    assert await require_admin(u) is u


@pytest.mark.asyncio
async def test_require_admin_rejects_teacher() -> None:
    u = AuthenticatedUser(
        id=2, username="t", role=UserRole.TEACHER, email="t@x.com"
    )
    with pytest.raises(AuthorizationError):
        await require_admin(u)


@pytest.mark.asyncio
async def test_require_admin_or_self_allows_self_numeric_string_id() -> None:
    u = AuthenticatedUser(
        id=42, username="s", role=UserRole.STUDENT, email="s@x.com"
    )
    assert await require_admin_or_self("42", u) is u


@pytest.mark.asyncio
async def test_require_admin_or_self_rejects_peer() -> None:
    u = AuthenticatedUser(
        id=42, username="s", role=UserRole.STUDENT, email="s@x.com"
    )
    with pytest.raises(EnhancedServiceError):
        await require_admin_or_self("999", u)
