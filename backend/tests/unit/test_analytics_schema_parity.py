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
