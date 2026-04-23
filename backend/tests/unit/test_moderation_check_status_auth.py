"""F4: moderation check-status — self or admin only."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.moderation_api import check_user_status
from models.enums_db import UserRole


@pytest.mark.asyncio
async def test_check_status_forbidden_for_other_student() -> None:
    user = MagicMock()
    user.id = 1
    user.role = UserRole.STUDENT
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await check_user_status("999", current_user=user, db=db)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_check_status_allowed_for_self() -> None:
    user = MagicMock()
    user.id = 42
    user.role = UserRole.STUDENT
    db = AsyncMock()
    mute_r = MagicMock()
    mute_r.scalar_one_or_none.return_value = None
    ban_r = MagicMock()
    ban_r.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(side_effect=[mute_r, ban_r])

    out = await check_user_status("42", current_user=user, db=db)
    assert out["success"] is True
    assert "data" in out


@pytest.mark.asyncio
async def test_check_status_admin_may_query_other() -> None:
    user = MagicMock()
    user.id = 1
    user.role = UserRole.ADMIN
    db = AsyncMock()
    mute_r = MagicMock()
    mute_r.scalar_one_or_none.return_value = None
    ban_r = MagicMock()
    ban_r.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(side_effect=[mute_r, ban_r])

    out = await check_user_status("999", current_user=user, db=db)
    assert out["success"] is True
