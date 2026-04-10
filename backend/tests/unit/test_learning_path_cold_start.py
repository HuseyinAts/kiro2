"""
Cold-Start testi: theta_map == {} olduğunda daily plan üretimini doğrular.

Senaryo: Yeni kayıtlı öğrenci — hiç soru çözmemiş, DB'de StudentAbility yok.
Beklenti: plan.blocks > 0 (boş plan üretilmemeli, CAT blokları gelmeli)

Bu test silent failure'ı engeller: theta_map boş olduğunda orchestrator sessizce
boş blok listesi döndürürdü — öğrenci ilk oturumda hiçbir şey görmezdi.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Path ayarı — tests/unit'ten backend/ köküne ulaş
sys.path.insert(0, str(Path(__file__).parents[2]))

from app.services.learning_path_orchestrator import (
    DailyPlan,
    LearningPathOrchestrator,
    StudyBlock,
)

# ─── Fixture'lar ──────────────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    """Async DB session mock — hiçbir StudentAbility verisi yok (cold start)."""
    db = AsyncMock()
    # _fetch_thetas_with_se → boş scalars (yeni öğrenci, theta yok)
    empty_result = MagicMock()
    empty_result.scalars.return_value = []
    # _fetch_fsrs_due_counts → boş (hiç kart yok)
    empty_fsrs = MagicMock()
    empty_fsrs.fetchall.return_value = []
    # execute çağrılarını sırayla ver: 1. theta, 2. fsrs, 3. DAG sorguları
    db.execute = AsyncMock(side_effect=_db_execute_dispatch)
    return db


def _db_execute_dispatch(*args, **kwargs):
    """Hangi sorgu olduğuna bağımsız olarak boş sonuç döndür."""
    result = MagicMock()
    result.scalars.return_value = []
    result.fetchall.return_value = []
    result.fetchone.return_value = None
    return result


@pytest.fixture
def mock_dag_service():
    """DAGService mock — önkoşul yok, her ders için geçerli konu öner."""
    svc = AsyncMock()
    svc.get_user_mastery.return_value = {}
    svc.get_next_recommended_topic.return_value = "topic-001"
    check = MagicMock()
    check.can_proceed = True
    check.blocking_prereqs = []
    svc.check_can_study_topic.return_value = check
    dag = MagicMock()
    topic_node = MagicMock()
    topic_node.name = "Test Konusu"
    dag.get_topic.return_value = topic_node
    svc.get_dag.return_value = dag
    return svc


@pytest.fixture
def orchestrator(mock_db, mock_dag_service):
    """LearningPathOrchestrator — gerçek mantık, mock DB + DAG."""
    orch = LearningPathOrchestrator(db=mock_db, redis=None)
    orch._dag_service = mock_dag_service
    return orch


# ─── Testler ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cold_start_produces_blocks(orchestrator):
    """
    KRITIK: theta_map == {} → plan.blocks > 0 olmalı.
    Yeni öğrenci ilk girişinde boş plan görmemeli.
    """
    plan = await orchestrator.generate_daily_plan(
        user_id="new-user-001",
        available_minutes=120,
        exam_date=date.today() + timedelta(days=180),
        exam_type="TYT",
    )

    assert isinstance(plan, DailyPlan)
    assert len(plan.blocks) > 0, (
        "Cold-start öğrenci için boş plan üretildi — "
        "theta_map={} olduğunda en az 1 blok gelmeli"
    )


@pytest.mark.asyncio
async def test_cold_start_has_cat_blocks(orchestrator):
    """
    Cold-start'ta CAT blokları gelmeli: theta bilinmiyorsa adaptif test başlatılır.
    """
    plan = await orchestrator.generate_daily_plan(
        user_id="new-user-001",
        available_minutes=120,
        exam_date=date.today() + timedelta(days=180),
        exam_type="TYT",
    )

    cat_blocks = [b for b in plan.blocks if b.activity_type == "cat"]
    assert len(cat_blocks) > 0, (
        "Cold-start'ta CAT bloğu yok — theta bilinmeyen dersler için CAT başlatılmalı"
    )


@pytest.mark.asyncio
async def test_cold_start_total_minutes_positive(orchestrator):
    """Plan toplam süre > 0 olmalı (boş plan değil)."""
    plan = await orchestrator.generate_daily_plan(
        user_id="new-user-001",
        available_minutes=60,
        exam_date=date.today() + timedelta(days=90),
        exam_type="TYT",
    )

    assert plan.total_minutes > 0, (
        "Cold-start planı toplam_süre=0 döndürdü — içerik üretilmedi"
    )


@pytest.mark.asyncio
async def test_cold_start_weak_strong_none(orchestrator):
    """
    Tüm theta'lar eşit (hepsi 0.0) → weak/strong None olmalı.
    Orchestrator bu durumu algılayıp weak/strong göstermiyor.
    """
    plan = await orchestrator.generate_daily_plan(
        user_id="new-user-001",
        available_minutes=120,
        exam_date=date.today() + timedelta(days=180),
        exam_type="TYT",
    )

    assert plan.weak_subject is None, (
        f"Cold-start'ta weak_subject='{plan.weak_subject}' — "
        "tüm theta'lar eşit olduğunda None olmalı"
    )
    assert plan.strong_subject is None, (
        f"Cold-start'ta strong_subject='{plan.strong_subject}' — "
        "tüm theta'lar eşit olduğunda None olmalı"
    )


@pytest.mark.asyncio
async def test_cold_start_exam_crunch_still_produces_blocks(orchestrator):
    """
    Sınava < 30 gün kaldığında bile cold-start öğrenci blok görmeli.
    Bu köşe durumu: hem theta yok hem exam_crunch=True.
    """
    plan = await orchestrator.generate_daily_plan(
        user_id="new-user-001",
        available_minutes=120,
        exam_date=date.today() + timedelta(days=15),  # exam crunch!
        exam_type="TYT",
    )

    assert len(plan.blocks) > 0, (
        "Sınav kıyısında + cold-start kombinasyonunda boş plan üretildi"
    )


@pytest.mark.asyncio
async def test_cold_start_blocks_have_valid_structure(orchestrator):
    """Her bloğun zorunlu alanları dolu olmalı."""
    plan = await orchestrator.generate_daily_plan(
        user_id="new-user-001",
        available_minutes=120,
        exam_date=date.today() + timedelta(days=180),
        exam_type="TYT",
    )

    for block in plan.blocks:
        assert isinstance(block, StudyBlock)
        assert block.subject, f"Bloğun subject alanı boş: {block}"
        assert block.activity_type in ("cat", "fsrs_review", "practice", "prereq"), (
            f"Geçersiz activity_type: {block.activity_type}"
        )
        assert block.duration_minutes >= 0, f"Negatif süre: {block.duration_minutes}"
