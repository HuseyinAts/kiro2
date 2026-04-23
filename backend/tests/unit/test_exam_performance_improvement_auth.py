"""F4: exam_performance gelişim trendi — staff + self."""

import pytest
from fastapi import HTTPException

from api.exam_performance import get_student_improvement_trends
from core.dependencies import AuthenticatedUser, UserRole
from models.database import ExamType


@pytest.mark.asyncio
async def test_improvement_trends_denies_student_peer() -> None:
    user = AuthenticatedUser(
        id=1, username="s", role=UserRole.STUDENT, email=None
    )
    with pytest.raises(HTTPException) as ei:
        await get_student_improvement_trends("999", ExamType.TYT, user)
    assert ei.value.status_code == 403
