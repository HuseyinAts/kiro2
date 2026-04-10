"""
Regression: topic_hierarchy.subject_area UPPERCASE'dir (MATEMATIK, TURKCE, FIZIK...).
Orchestrator DAGService'e subject'i .lower() ile göndermemelidir — dag_engine.py:338
`get_subject_topics` exact case-sensitive match yapar, lowercase → 0 eşleşme →
next_topic None → prereq_blocked ASLA True olmaz (silent DAG bypass).

Root cause ref: docs/audits/2026-04-10_feature_health_audit.md Faz C pilot
Bug location: learning_path_orchestrator.py:206 + :463
Pattern: .claude/rules/testing.md Lesson 26 (Case Convention Tutarliligi)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from app.services.learning_path_orchestrator import LearningPathOrchestrator


def _db_execute_dispatch(*args, **kwargs):
    result = MagicMock()
    result.scalars.return_value = []
    result.fetchall.return_value = []
    result.fetchone.return_value = None
    return result


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=_db_execute_dispatch)
    return db


@pytest.fixture
def mock_dag_service():
    svc = AsyncMock()
    svc.get_user_mastery.return_value = {}
    svc.get_next_recommended_topic.return_value = None  # bug tetikleyici değil
    check = MagicMock()
    check.can_proceed = True
    check.blocking_prereqs = []
    check.warning_prereqs = []
    svc.check_can_study_topic.return_value = check
    dag = MagicMock()
    dag.get_topic.return_value = None
    svc.get_dag.return_value = dag
    return svc


@pytest.fixture
def orchestrator(mock_db, mock_dag_service):
    orch = LearningPathOrchestrator(db=mock_db, redis=None)
    orch._dag_service = mock_dag_service
    return orch


@pytest.mark.asyncio
async def test_get_student_subject_statuses_passes_uppercase_to_dag(
    orchestrator, mock_dag_service
):
    """
    get_student_subject_statuses DAGService'e UPPERCASE subject geçmelidir.

    DB'de topic_hierarchy.subject_area UPPERCASE kayıtlıdır
    (MATEMATIK=40, TURKCE=8, FIZIK=8, BIYOLOJI=8, KIMYA=8...).
    dag_engine.py get_subject_topics() exact match yapar — lowercase geçilirse
    0 konu döner ve prereq enforcement sessizce devre dışı kalır.
    """
    await orchestrator.get_student_subject_statuses(
        user_id="test-user-001",
        exam_type="TYT",
    )

    calls = mock_dag_service.get_next_recommended_topic.call_args_list
    assert len(calls) > 0, "DAGService.get_next_recommended_topic hiç çağrılmadı"

    subject_ids = [c.kwargs["subject_id"] for c in calls]
    lowercase_leaks = [s for s in subject_ids if s != s.upper()]
    assert not lowercase_leaks, (
        f"DAG'a lowercase subject_id geçildi: {lowercase_leaks}. "
        f"DB UPPERCASE bekliyor (MATEMATIK, TURKCE vb.) — "
        f"aksi halde get_subject_topics 0 eşleşme döner, prereq bypass olur."
    )


@pytest.mark.asyncio
async def test_get_next_topic_passes_uppercase_to_dag(orchestrator, mock_dag_service):
    """get_next_topic da aynı bug'a sahip — subject .lower() yapmamalı."""
    await orchestrator.get_next_topic(
        user_id="test-user-001",
        subject="MATEMATIK",
    )

    calls = mock_dag_service.get_next_recommended_topic.call_args_list
    assert len(calls) > 0, "DAGService.get_next_recommended_topic hiç çağrılmadı"

    subject_ids = [c.kwargs["subject_id"] for c in calls]
    assert "MATEMATIK" in subject_ids, (
        f"get_next_topic subject'i olduğu gibi iletmedi: {subject_ids}. "
        f"lowercase ('matematik') geçiliyorsa bug mevcut."
    )
