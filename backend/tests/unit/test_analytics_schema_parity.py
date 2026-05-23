"""Schema parity tests for S196 Day 4 Tier-1 analytics endpoints.

Asserts ``_real`` and ``_mock`` variants emit the same response shape
so flipping ``analytics.*`` flags in ``mock_endpoint_flags.json`` cannot
break the frontend contract.

Stubs DB session — no live PostgreSQL needed.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_class_students_real_shape_matches_mock():
    """``_get_class_students_real`` returns the same dict shape as mock.

    Stubs the DB result with 2 rows; asserts keys + types match mock.
    """
    from api.analytics import (
        _get_class_students_mock,
        _get_class_students_real,
    )

    mock_result = await _get_class_students_mock("any-class-id")
    assert mock_result and isinstance(mock_result, list)
    assert set(mock_result[0].keys()) == {"id", "name"}

    fake_rows = [
        SimpleNamespace(id="u-1", first_name="Test", last_name="Student"),
        SimpleNamespace(id="u-2", first_name="Another", last_name="One"),
    ]
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value=iter(fake_rows))

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    # Use a valid UUID string so the UUID() cast succeeds.
    with patch("api.analytics.get_db_session_context", new=_fake_ctx):
        real_result = await _get_class_students_real(
            "11111111-1111-1111-1111-111111111111"
        )

    assert isinstance(real_result, list)
    assert len(real_result) == 2
    for item in real_result:
        assert set(item.keys()) == {"id", "name"}, (
            f"class_students shape drift: {item.keys()}"
        )


@pytest.mark.asyncio
async def test_class_students_invalid_uuid_returns_empty():
    """Invalid UUID class_id → empty list (no crash, no DB call)."""
    from api.analytics import _get_class_students_real

    # Patch DB so we can assert it is NEVER called.
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock()

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    with patch("api.analytics.get_db_session_context", new=_fake_ctx):
        result = await _get_class_students_real("not-a-uuid")

    assert result == []
    fake_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_exam_statistics_real_keys_match_mock():
    """``_get_exam_statistics_real`` emits the 4 top-level keys mock does."""
    from api.analytics import (
        _get_exam_statistics_mock,
        _get_exam_statistics_real,
    )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 12, 31, tzinfo=UTC)

    mock_result = await _get_exam_statistics_mock(start, end)

    fake_rows = [
        SimpleNamespace(
            etype="TYT", completed_count=30, avg_score=72.5, attempted_count=40
        ),
        SimpleNamespace(
            etype="AYT", completed_count=20, avg_score=68.0, attempted_count=25
        ),
    ]
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value=SimpleNamespace(all=lambda: fake_rows))

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    with patch("api.analytics.get_db_session_context", new=_fake_ctx):
        real_result = await _get_exam_statistics_real(start, end)

    assert set(real_result.keys()) == set(mock_result.keys()), (
        f"exam_statistics top-level drift: "
        f"real={set(real_result.keys())}, mock={set(mock_result.keys())}"
    )
    # Numeric shape — total_exams_taken is integer sum, averages floats per type.
    assert real_result["total_exams_taken"] == 50  # 30 + 20
    assert real_result["exam_types"] == {"TYT": 30, "AYT": 20}
    assert real_result["completion_rates"]["TYT"] == 0.75  # 30/40
    assert real_result["completion_rates"]["AYT"] == 0.8  # 20/25


@pytest.mark.asyncio
async def test_exam_statistics_empty_window_returns_zeros():
    """No rows in window → zeros, not empty dict (schema parity)."""
    from api.analytics import _get_exam_statistics_real

    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value=SimpleNamespace(all=list))

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    with patch("api.analytics.get_db_session_context", new=_fake_ctx):
        now = datetime.now(tz=UTC)
        result = await _get_exam_statistics_real(now - timedelta(days=7), now)

    assert result["total_exams_taken"] == 0
    assert result["exam_types"] == {}
    assert result["average_scores"] == {}
    assert result["completion_rates"] == {}


@pytest.mark.asyncio
async def test_user_statistics_real_keys_match_mock():
    """``_get_user_statistics_real`` matches mock top-level + nested keys."""
    from api.analytics import (
        _get_user_statistics_mock,
        _get_user_statistics_real,
    )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 12, 31, tzinfo=UTC)
    mock_result = await _get_user_statistics_mock(start, end)

    roles_rows = [
        SimpleNamespace(role="STUDENT", cnt=71),
        SimpleNamespace(role="TEACHER", cnt=1),
        SimpleNamespace(role="PARENT", cnt=2),
        SimpleNamespace(role="ADMIN", cnt=1),
    ]
    counters = iter([roles_rows, 5, 60])  # rows + new_reg + active

    async def _exec(*_args, **_kw):
        nxt = next(counters)
        if isinstance(nxt, list):
            return iter(nxt)
        return SimpleNamespace(scalar=lambda v=nxt: v)

    fake_db = AsyncMock()
    fake_db.execute = _exec

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    with patch("api.analytics.get_db_session_context", new=_fake_ctx):
        real_result = await _get_user_statistics_real(start, end)

    assert set(real_result.keys()) == set(mock_result.keys())
    assert set(real_result["user_types"].keys()) == set(
        mock_result["user_types"].keys()
    )
    assert real_result["total_users"] == 75
    assert real_result["user_types"]["students"] == 71


@pytest.mark.asyncio
async def test_student_performance_real_keys_match_mock():
    """``_calculate_student_performance_metrics_real`` matches mock shape."""
    from api.analytics import (
        _calculate_student_performance_metrics_mock,
        _calculate_student_performance_metrics_real,
    )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 12, 31, tzinfo=UTC)
    mock_result = await _calculate_student_performance_metrics_mock(
        "sid", start, end, None
    )

    call_outputs = [
        SimpleNamespace(one=lambda: SimpleNamespace(total_q=100, correct_q=72)),
        SimpleNamespace(
            one=lambda: SimpleNamespace(avg_dur=28.5, total_secs=3600 * 12)
        ),
        SimpleNamespace(
            all=lambda: [
                SimpleNamespace(subject="MATEMATIK", n=30, acc=0.45),
                SimpleNamespace(subject="TURKCE", n=20, acc=0.85),
                SimpleNamespace(subject="FIZIK", n=25, acc=0.50),
            ]
        ),
    ]
    output_iter = iter(call_outputs)
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(side_effect=lambda *a, **kw: next(output_iter))

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    with patch("api.analytics.get_db_session_context", new=_fake_ctx):
        real_result = await _calculate_student_performance_metrics_real(
            "sid", start, end, None
        )

    assert set(real_result.keys()) == set(mock_result.keys())
    assert real_result["total_questions_solved"] == 100
    assert real_result["correct_answers"] == 72
    assert real_result["accuracy_rate"] == 0.72
    assert "MATEMATIK" in real_result["weak_subjects"]
    assert "TURKCE" in real_result["strong_subjects"]


@pytest.mark.asyncio
async def test_class_metrics_real_aggregates_students():
    """``_calculate_class_metrics_real`` matches mock shape + aggregates."""
    from api.analytics import (
        _calculate_class_metrics_mock,
        _calculate_class_metrics_real,
    )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 12, 31, tzinfo=UTC)
    mock_result = await _calculate_class_metrics_mock("c1", [], start, end, None)

    fake_metrics = {
        "total_study_time_hours": 10.0,
        "total_questions_solved": 50,
        "correct_answers": 35,
        "accuracy_rate": 0.7,
        "average_session_duration_minutes": 20.0,
        "improvement_trend": "insufficient_data",
        "weak_subjects": [],
        "strong_subjects": [],
        "study_consistency_score": 0.0,
    }
    with patch(
        "api.analytics._calculate_student_performance_metrics_real",
        new=AsyncMock(return_value=fake_metrics),
    ):
        real_result = await _calculate_class_metrics_real(
            "c1",
            [{"id": "s1"}, {"id": "s2"}, {"id": "s3"}],
            start,
            end,
            None,
        )

    assert set(real_result.keys()) == set(mock_result.keys())
    assert real_result["total_questions_solved"] == 150  # 3 students × 50
    assert real_result["class_accuracy_rate"] == 0.7  # 105/150
    assert real_result["active_students_percentage"] == 1.0


@pytest.mark.asyncio
async def test_exam_performance_analysis_real_keys_match_mock():
    """``_get_exam_performance_analysis_real`` matches mock top-level + nested keys."""
    from api.analytics import (
        _get_exam_performance_analysis_mock,
        _get_exam_performance_analysis_real,
    )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 12, 31, tzinfo=UTC)
    mock_result = await _get_exam_performance_analysis_mock("sid", start, end)

    call_outputs = [
        # per-type rows
        iter(
            [
                SimpleNamespace(
                    etype="TYT", completed_n=8, attempted_n=10, avg_score=76.2
                ),
                SimpleNamespace(
                    etype="AYT", completed_n=3, attempted_n=4, avg_score=82.1
                ),
            ]
        ),
        # overall aggregate
        SimpleNamespace(
            one=lambda: SimpleNamespace(
                min_s=65, max_s=92, avg_s=78.5, attempted=14, completed=11
            )
        ),
        # avg response time
        SimpleNamespace(scalar=lambda: 45.2),
    ]
    output_iter = iter(call_outputs)
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(side_effect=lambda *a, **kw: next(output_iter))

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    with patch("api.analytics.get_db_session_context", new=_fake_ctx):
        real_result = await _get_exam_performance_analysis_real("sid", start, end)

    assert set(real_result.keys()) == set(mock_result.keys())
    assert set(real_result["exam_types"].keys()) == {"TYT", "AYT"}
    assert real_result["total_exams"] == 11  # 8 + 3
    assert real_result["best_score"] == 92
    assert real_result["worst_score"] == 65
    assert set(real_result["time_management"].keys()) == set(
        mock_result["time_management"].keys()
    )


@pytest.mark.asyncio
async def test_subject_performance_analysis_real_keys_match_mock():
    """``_get_subject_performance_analysis_real`` matches mock shape."""
    from api.analytics import (
        _get_subject_performance_analysis_mock,
        _get_subject_performance_analysis_real,
    )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 12, 31, tzinfo=UTC)
    mock_result = await _get_subject_performance_analysis_mock("sid", start, end)

    fake_rows = [
        SimpleNamespace(subject="MATEMATIK", n=245, acc=0.68, total_seconds=45000),
        SimpleNamespace(subject="TURKCE", n=189, acc=0.82, total_seconds=29500),
    ]
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value=iter(fake_rows))

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    with patch("api.analytics.get_db_session_context", new=_fake_ctx):
        real_result = await _get_subject_performance_analysis_real("sid", start, end)

    assert set(real_result.keys()) == set(mock_result.keys())
    assert "subjects" in real_result
    # Per-subject nested key parity (using one mock subject as reference).
    mock_subject_keys = set(next(iter(mock_result["subjects"].values())).keys())
    if real_result["subjects"]:
        real_subject_keys = set(next(iter(real_result["subjects"].values())).keys())
        assert real_subject_keys == mock_subject_keys, (
            f"subject-level drift: {real_subject_keys ^ mock_subject_keys}"
        )
    assert "MATEMATIK" in real_result["subjects"]


@pytest.mark.asyncio
async def test_content_usage_statistics_real_keys_match_mock():
    """``_get_content_usage_statistics_real`` matches mock top-level + nested keys."""
    from api.analytics import (
        _get_content_usage_statistics_mock,
        _get_content_usage_statistics_real,
    )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 12, 31, tzinfo=UTC)
    mock_result = await _get_content_usage_statistics_mock(start, end)

    fake_rows = [
        SimpleNamespace(
            src="youtube",
            view_n=1000,
            avg_completion=0.65,
            avg_duration_seconds=480.0,
            completed_n=650,
            bounced_n=200,
        ),
    ]
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value=iter(fake_rows))

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    with patch("api.analytics.get_db_session_context", new=_fake_ctx):
        real_result = await _get_content_usage_statistics_real(start, end)

    assert set(real_result.keys()) == set(mock_result.keys())
    assert set(real_result["content_types"].keys()) == set(
        mock_result["content_types"].keys()
    )
    assert set(real_result["engagement_metrics"].keys()) == set(
        mock_result["engagement_metrics"].keys()
    )
    assert real_result["total_content_views"] == 1000
    assert real_result["content_types"]["videos"] == 1000
    assert real_result["engagement_metrics"]["completion_rate"] == 0.65
    assert real_result["engagement_metrics"]["bounce_rate"] == 0.2
