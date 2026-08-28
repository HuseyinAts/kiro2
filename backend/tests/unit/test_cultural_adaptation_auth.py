"""F4: cultural_adaptation_api öğrenci path yetkisi (staff + self)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

import api.cultural_adaptation_api as cult_mod
from api.cultural_adaptation_api import (
    BehavioralUpdateRequest,
    get_student_cultural_adaptation,
    update_student_behavioral_data,
)
from core.dependencies import AuthenticatedUser, UserRole


@pytest.mark.asyncio
async def test_get_cultural_super_admin_can_read_any_student() -> None:
    user = AuthenticatedUser(
        id=1, username="sa", role=UserRole.SUPER_ADMIN, email=None
    )
    with patch.object(
        cult_mod.cultural_service,
        "get_student_cultural_adaptation",
        new_callable=AsyncMock,
        return_value={"profile": "x"},
    ):
        out = await get_student_cultural_adaptation("stu-9", False, user)
        assert out.success is True


@pytest.mark.asyncio
async def test_get_cultural_student_denied_other_path_id() -> None:
    user = AuthenticatedUser(
        id=50, username="s", role=UserRole.STUDENT, email=None
    )
    with pytest.raises(HTTPException) as ei:
        await get_student_cultural_adaptation("999", False, user)
    assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_behavioral_update_teacher_allowed() -> None:
    user = AuthenticatedUser(
        id=2, username="t", role=UserRole.TEACHER, email=None
    )
    body = BehavioralUpdateRequest(group_study_sessions=3)
    with patch.object(
        cult_mod.cultural_service,
        "update_cultural_context",
        new_callable=AsyncMock,
        return_value={"ok": True},
    ):
        out = await update_student_behavioral_data("any-id", body, user)
        assert out.success is True


@pytest.mark.asyncio
async def test_test_adaptation_requires_admin_or_super() -> None:
    from api.cultural_adaptation_api import test_cultural_adaptation

    user = AuthenticatedUser(
        id=3, username="s", role=UserRole.STUDENT, email=None
    )
    with pytest.raises(HTTPException) as ei:
        await test_cultural_adaptation(
            {
                "student_id": "x",
                "age": 15,
                "region": "tr",
                "cultural_factors": [],
            },
            user,
        )
    assert ei.value.status_code == 403
