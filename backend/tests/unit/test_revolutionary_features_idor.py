"""F4 Dalga B: revolutionary-features ZPD / öneri / kültür uçlarında verify_student_access."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.revolutionary_features import (
    BehavioralDataRequest,
    CulturalContextRequest,
    RecommendationRequest,
    ZPDCalculationRequest,
    calculate_revolutionary_zpd,
    detect_cultural_context,
    generate_revolutionary_recommendation,
)


def _behavioral() -> BehavioralDataRequest:
    return BehavioralDataRequest()


@pytest.mark.asyncio
async def test_calculate_zpd_calls_verify_student_access() -> None:
    req = ZPDCalculationRequest(
        student_id="stu-test-1",
        subject="matematik",
        current_level=0.5,
        behavioral_data=_behavioral(),
    )
    user = MagicMock()
    db = AsyncMock()
    with patch(
        "api.revolutionary_features.verify_student_access", new_callable=AsyncMock
    ) as verify:
        verify.return_value = True
        with patch(
            "api.revolutionary_features.revolutionary_features_service.calculate_revolutionary_zpd",
            new_callable=AsyncMock,
        ) as svc:
            svc.return_value = SimpleNamespace(z_min=0.1)
            await calculate_revolutionary_zpd(req, user, db)
            verify.assert_awaited_once_with("stu-test-1", user, db)


@pytest.mark.asyncio
async def test_generate_recommendation_calls_verify_student_access() -> None:
    req = RecommendationRequest(
        student_id="stu-test-2",
        subject="fizik",
        current_level=0.4,
        behavioral_data=_behavioral(),
        learning_objective="TYT",
        content_description="",
    )
    user = MagicMock()
    db = AsyncMock()
    with patch(
        "api.revolutionary_features.verify_student_access", new_callable=AsyncMock
    ) as verify:
        verify.return_value = True
        with patch(
            "api.revolutionary_features.revolutionary_features_service.generate_revolutionary_recommendation",
            new_callable=AsyncMock,
        ) as svc:
            svc.return_value = SimpleNamespace(tip="x")
            await generate_revolutionary_recommendation(req, user, db)
            verify.assert_awaited_once_with("stu-test-2", user, db)


@pytest.mark.asyncio
async def test_detect_cultural_context_calls_verify_student_access() -> None:
    req = CulturalContextRequest(
        student_id="stu-test-3",
        behavioral_data=_behavioral(),
    )
    user = MagicMock()
    db = AsyncMock()
    with patch(
        "api.revolutionary_features.verify_student_access", new_callable=AsyncMock
    ) as verify:
        verify.return_value = True
        with patch(
            "api.revolutionary_features.revolutionary_features_service.detect_cultural_context",
            new_callable=AsyncMock,
        ) as svc:
            svc.return_value = SimpleNamespace(ctx=1)
            await detect_cultural_context(req, user, db)
            verify.assert_awaited_once_with("stu-test-3", user, db)
