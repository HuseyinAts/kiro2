"""F4: IRT morfoloji POST /recommend-questions student_id yetkisi."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.irt_morfoloji import (
    StudentQuestionRecommendationRequest,
    recommend_questions_for_student,
)
from core.dependencies import AuthenticatedUser, UserRole


@pytest.mark.asyncio
async def test_recommend_questions_teacher_skips_verify() -> None:
    req = StudentQuestionRecommendationRequest(
        student_id="999", subject="MATEMATIK", target_success_rate=0.7
    )
    user = AuthenticatedUser(
        id=1, username="t", role=UserRole.TEACHER, email=None
    )
    db = AsyncMock()
    with patch(
        "core.learning_path_auth.verify_student_access", new_callable=AsyncMock
    ) as v:
        with patch(
            "services.irt_morfoloji_service.IRTMorfolojiService",
        ) as Svc:
            inst = MagicMock()
            inst.ogrenci_uyumlu_soru_onerisi = AsyncMock(return_value=[])
            Svc.return_value = inst
            out = await recommend_questions_for_student(req, user, db)
            v.assert_not_called()
            assert out["success"] is True


@pytest.mark.asyncio
async def test_recommend_questions_student_other_id_invokes_verify() -> None:
    req = StudentQuestionRecommendationRequest(
        student_id="STU_PEER", subject="MATEMATIK", target_success_rate=0.7
    )
    user = AuthenticatedUser(
        id=50, username="s", role=UserRole.STUDENT, email=None
    )
    db = AsyncMock()
    with patch(
        "core.learning_path_auth.verify_student_access", new_callable=AsyncMock
    ) as v:
        v.side_effect = HTTPException(status_code=403, detail="no")
        with pytest.raises(HTTPException) as ei:
            await recommend_questions_for_student(req, user, db)
        assert ei.value.status_code == 403
        v.assert_awaited_once()
