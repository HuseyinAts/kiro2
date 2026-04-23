"""F4: zpd_maarif /api/v1/zpd-maarif/revolutionary/* student_id IDOR koruması."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import api.zpd_maarif as zpd_mod
from api.zpd_maarif import (
    CulturalAdaptationRequest,
    CulturalPatternAnalysisRequest,
    LearningBalanceRequest,
    RevolutionaryRecommendationRequest,
    RevolutionaryZPDRequest,
    adapt_difficulty_culturally,
    calculate_revolutionary_zpd,
    detect_cultural_context,
    generate_revolutionary_recommendation,
    get_learning_balance,
    monitor_cultural_patterns,
)


def _zpd_range() -> SimpleNamespace:
    cc = SimpleNamespace(
        group_learning_preference=0.1,
        teacher_respect_level=0.2,
        family_involvement=0.3,
        peer_competition=0.4,
    )
    av = SimpleNamespace(value="national")
    ma = SimpleNamespace(
        overall_alignment=0.9,
        national_values_alignment=0.8,
        universal_values_alignment=0.7,
        root_values_alignment=0.6,
        aligned_values=[av],
    )
    return SimpleNamespace(
        student_id="s1",
        subject="mat",
        current_level=5.0,
        lower_bound=4.0,
        upper_bound=7.0,
        optimal_challenge=5.5,
        group_individual_balance=0.5,
        cultural_context=cc,
        maarif_alignment=ma,
        calculated_at=datetime.now(UTC),
    )


def _recommendation():
    mi = SimpleNamespace(value="v1")
    return SimpleNamespace(
        student_id="s1",
        subject="mat",
        recommended_difficulty=5.0,
        learning_mode="mixed",
        content_type="video",
        teacher_guidance_level=0.5,
        peer_support_level=0.5,
        maarif_integration=[mi],
        reasoning="r",
        confidence_score=0.8,
    )


@pytest.mark.asyncio
async def test_revolutionary_calculate_verifies() -> None:
    req = RevolutionaryZPDRequest(
        student_id="stu-zpd-1",
        subject="mat",
        current_level=5.0,
        behavioral_data={},
    )
    user, db = MagicMock(), AsyncMock()
    with patch.object(zpd_mod, "verify_student_access", new_callable=AsyncMock) as v:
        v.return_value = True
        with patch.object(
            zpd_mod.zpd_service,
            "calculate_revolutionary_zpd",
            new_callable=AsyncMock,
        ) as svc:
            svc.return_value = _zpd_range()
            await calculate_revolutionary_zpd(req, user, db)
            v.assert_awaited_once_with("stu-zpd-1", user, db)


@pytest.mark.asyncio
async def test_revolutionary_recommend_verifies() -> None:
    req = RevolutionaryRecommendationRequest(
        student_id="stu-zpd-2",
        subject="mat",
        current_level=5.0,
        behavioral_data={},
        learning_objective="TYT",
        content_description="",
    )
    user, db = MagicMock(), AsyncMock()
    with patch.object(zpd_mod, "verify_student_access", new_callable=AsyncMock) as v:
        v.return_value = True
        with patch.object(
            zpd_mod.zpd_service,
            "generate_revolutionary_recommendation",
            new_callable=AsyncMock,
        ) as svc:
            svc.return_value = _recommendation()
            await generate_revolutionary_recommendation(req, user, db)
            v.assert_awaited_once_with("stu-zpd-2", user, db)


@pytest.mark.asyncio
async def test_revolutionary_cultural_context_verifies() -> None:
    req = LearningBalanceRequest(student_id="stu-zpd-3", behavioral_data={})
    user, db = MagicMock(), AsyncMock()
    with patch.object(zpd_mod, "verify_student_access", new_callable=AsyncMock) as v:
        v.return_value = True
        cc = SimpleNamespace(
            student_id="stu-zpd-3",
            group_learning_preference=0.1,
            teacher_respect_level=0.2,
            family_involvement=0.3,
            peer_competition=0.4,
            authority_acceptance=0.5,
            collective_success=0.5,
            elder_wisdom_value=0.5,
            social_harmony=0.5,
            detected_at=datetime.now(UTC),
        )
        with patch.object(
            zpd_mod.zpd_service,
            "detect_cultural_context_revolutionary",
            new_callable=AsyncMock,
        ) as svc:
            svc.return_value = cc
            await detect_cultural_context(req, user, db)
            v.assert_awaited_once_with("stu-zpd-3", user, db)


@pytest.mark.asyncio
async def test_revolutionary_adapt_difficulty_verifies() -> None:
    req = CulturalAdaptationRequest(
        student_id="stu-zpd-4",
        current_difficulty=5.0,
        student_performance={"a": 0.5},
        behavioral_data={},
    )
    user, db = MagicMock(), AsyncMock()
    with patch.object(zpd_mod, "verify_student_access", new_callable=AsyncMock) as v:
        v.return_value = True
        with patch.object(
            zpd_mod.zpd_service,
            "adapt_difficulty_culturally_revolutionary",
            new_callable=AsyncMock,
        ) as svc:
            svc.return_value = 4.5
            await adapt_difficulty_culturally(req, user, db)
            v.assert_awaited_once_with("stu-zpd-4", user, db)


@pytest.mark.asyncio
async def test_revolutionary_learning_balance_verifies() -> None:
    req = LearningBalanceRequest(student_id="stu-zpd-5", behavioral_data={})
    user, db = MagicMock(), AsyncMock()
    with patch.object(zpd_mod, "verify_student_access", new_callable=AsyncMock) as v:
        v.return_value = True
        with patch.object(
            zpd_mod.zpd_service,
            "get_revolutionary_learning_balance",
            new_callable=AsyncMock,
        ) as svc:
            svc.return_value = {"recommended_mode": "group"}
            await get_learning_balance(req, user, db)
            v.assert_awaited_once_with("stu-zpd-5", user, db)


@pytest.mark.asyncio
async def test_revolutionary_cultural_patterns_verifies() -> None:
    req = CulturalPatternAnalysisRequest(
        student_id="stu-zpd-6",
        learning_sessions=[{"x": 1}],
    )
    user, db = MagicMock(), AsyncMock()
    with patch.object(zpd_mod, "verify_student_access", new_callable=AsyncMock) as v:
        v.return_value = True
        with patch.object(
            zpd_mod.zpd_service,
            "monitor_cultural_learning_patterns_revolutionary",
            new_callable=AsyncMock,
        ) as svc:
            svc.return_value = {"patterns": []}
            await monitor_cultural_patterns(req, user, db)
            v.assert_awaited_once_with("stu-zpd-6", user, db)
