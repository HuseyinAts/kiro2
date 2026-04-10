"""
Regression: GET /dag/topics?subject_id=matematik boş liste dönmemeli.

topic_hierarchy.subject_area UPPERCASE ("MATEMATIK"). Frontend lowercase
gönderirse dag_engine.get_subject_topics exact match 0 döner → boş liste.
app/api/dag.py:91 defansif .upper() eklenmeli.

Pattern ref: .claude/rules/case-convention.md
Root cause ref: Session 134 mikroskopik audit
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from app.services.dag_engine import PrerequisiteDAG


def test_dag_subject_topics_uppercase_match():
    """dag_engine.get_subject_topics exact match — UPPERCASE node/query."""
    dag = PrerequisiteDAG()
    dag.add_topic("t1", "Fonksiyonlar", "MATEMATIK")
    dag.add_topic("t2", "Paragraf", "TURKCE")

    assert len(dag.get_subject_topics("MATEMATIK")) == 1
    assert len(dag.get_subject_topics("matematik")) == 0  # exact match bug


def test_dag_subject_topics_lowercase_miss_documented():
    """Lowercase subject_id exact match bug'ını dokümante eder."""
    dag = PrerequisiteDAG()
    dag.add_topic("t1", "Fonksiyonlar", "MATEMATIK")
    # Lowercase = 0 eşleşme. list_topics endpoint'inin .upper() eklemesi gerekir.
    assert dag.get_subject_topics("matematik") == []


@pytest.mark.asyncio
async def test_list_topics_endpoint_uppercases_subject_id():
    """
    app/api/dag.py list_topics endpoint lowercase subject_id'yi
    defansif olarak UPPERCASE'e çevirmeli.

    DB'de topic_hierarchy.subject_area UPPERCASE kayıtlı (MATEMATIK, TURKCE...).
    DAG node'ları bu UPPERCASE değerlerle yüklendiği için endpoint lowercase
    subject_id aldığında exact match 0 döner ve frontend boş liste görür.
    """
    from app.api.dag import list_topics

    dag_mock = MagicMock()
    dag_mock.get_subject_topics = MagicMock(return_value=[])
    dag_mock.get_all_topics = MagicMock(return_value=[])

    svc_mock = AsyncMock()
    svc_mock.get_dag = AsyncMock(return_value=dag_mock)

    user_mock = MagicMock()
    user_mock.id = "test-user"

    await list_topics(
        subject_id="matematik",
        current_user=user_mock,
        svc=svc_mock,
    )

    call_args = dag_mock.get_subject_topics.call_args
    passed_subject = call_args[0][0]
    assert passed_subject == "MATEMATIK", (
        f"Endpoint lowercase '{passed_subject}' geçti. "
        f"topic_hierarchy.subject_area UPPERCASE → sessiz boş yanıt."
    )
