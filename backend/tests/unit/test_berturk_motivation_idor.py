"""F4: BERTurk POST /motivation/assess hedef öğrenci yetkisi (staff + self)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import api.berturk_api as berturk_mod
from api.berturk_api import MotivationAssessmentRequest, assess_student_motivation
from core.dependencies import AuthenticatedUser, UserRole


def _assessment_mock(student_id: str = "42") -> MagicMock:
    m = MagicMock()
    m.student_id = student_id
    m.motivation_level = 0.5
    m.engagement_score = 0.6
    m.frustration_level = 0.2
    m.confidence_level = 0.7
    m.learning_enthusiasm = 0.55
    m.support_needed = False
    m.recommendations = []
    m.analysis_timestamp = datetime.now(UTC)
    return m


@pytest.mark.asyncio
async def test_motivation_super_admin_can_assess_other_student() -> None:
    req = MotivationAssessmentRequest(
        student_id="999", recent_texts=["merhaba"], time_window_hours=24
    )
    user = AuthenticatedUser(
        id=1, username="sa", role=UserRole.SUPER_ADMIN, email=None
    )
    mock_svc = MagicMock()
    mock_svc.assess_student_motivation = AsyncMock(
        return_value=_assessment_mock("999")
    )
    with patch.object(berturk_mod, "berturk_service", mock_svc):
        out = await assess_student_motivation(req, user)
        assert out.success is True
        mock_svc.assess_student_motivation.assert_awaited_once()


@pytest.mark.asyncio
async def test_motivation_student_cannot_assess_peer() -> None:
    req = MotivationAssessmentRequest(
        student_id="other-user", recent_texts=["x"], time_window_hours=24
    )
    user = AuthenticatedUser(
        id=100, username="stu", role=UserRole.STUDENT, email=None
    )
    with pytest.raises(HTTPException) as ei:
        await assess_student_motivation(req, user)
    assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_motivation_student_can_assess_self_by_user_id() -> None:
    req = MotivationAssessmentRequest(
        student_id="100", recent_texts=["x"], time_window_hours=24
    )
    user = AuthenticatedUser(
        id=100, username="stu", role=UserRole.STUDENT, email=None
    )
    mock_svc = MagicMock()
    mock_svc.assess_student_motivation = AsyncMock(
        return_value=_assessment_mock("100")
    )
    with patch.object(berturk_mod, "berturk_service", mock_svc):
        out = await assess_student_motivation(req, user)
        assert out.success is True
