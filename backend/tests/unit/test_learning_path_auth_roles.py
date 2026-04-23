"""verify_student_access: ORM User / string role vs UserRole enum (F4)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from core.learning_path_auth import assert_can_access_body_student_id, verify_student_access


@pytest.mark.asyncio
async def test_privileged_access_string_teacher_role() -> None:
    user = MagicMock()
    user.role = "teacher"
    user.id = 1
    db = AsyncMock()
    ok = await verify_student_access("STU_any", user, db)
    assert ok is True


@pytest.mark.asyncio
async def test_privileged_access_super_admin_slug() -> None:
    user = MagicMock()
    user.role = "super_admin"
    user.id = 1
    db = AsyncMock()
    ok = await verify_student_access("STU_x", user, db)
    assert ok is True


@pytest.mark.asyncio
async def test_student_must_own_profile() -> None:
    user = MagicMock()
    user.role = "student"
    user.id = 42
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)
    with pytest.raises(HTTPException) as exc:
        await verify_student_access("STU_other", user, db)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_assert_body_student_id_matches_user_no_db() -> None:
    user = MagicMock()
    user.role = "student"
    user.id = 42
    db = AsyncMock()
    await assert_can_access_body_student_id("42", user, db)
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_assert_body_student_id_peer_invokes_verify() -> None:
    user = MagicMock()
    user.role = "student"
    user.id = 42
    db = AsyncMock()
    with patch(
        "core.learning_path_auth.verify_student_access", new_callable=AsyncMock
    ) as v:
        await assert_can_access_body_student_id("STU_peer", user, db)
        v.assert_awaited_once()
