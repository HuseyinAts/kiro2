from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from services.offline_sync_service import process_sync_results


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value
        
    def scalars(self):
        return self
        
    def all(self):
        return [self._value] if self._value is not None else []


class _MappingsResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row


@pytest.mark.asyncio
async def test_sync_results_s1_happy_path_accepts_package():
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _MappingsResult({"student_id": "stu-1", "consumed_at": None}),
            _ScalarResult(SimpleNamespace(id="q1")),
            _ScalarResult(None),
            _ScalarResult(None),
        ]
    )

    result = await process_sync_results(
        db=db,
        student_id="stu-1",
        package_id="pkg-1",
        results=[
            {
                "question_id": "q1",
                "selected_answer": "A",
                "is_correct": True,
                "time_seconds": 4.0,
            }
        ],
        completed_at="2026-04-20T09:00:00Z",
    )

    assert result["synced_count"] == 1
    assert result["failed_count"] == 0
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_results_s2_happy_path_invalid_answer_counted_as_failed():
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _MappingsResult({"student_id": "stu-1", "consumed_at": None}),
            _ScalarResult(SimpleNamespace(id="q1")),
            _ScalarResult(None),
            _ScalarResult(None),
        ]
    )

    result = await process_sync_results(
        db=db,
        student_id="stu-1",
        package_id="pkg-2",
        results=[
            {
                "question_id": "q1",
                "selected_answer": "Z",
                "is_correct": False,
                "time_seconds": 5.0,
            }
        ],
        completed_at="2026-04-20T09:00:00Z",
    )

    assert result["synced_count"] == 0
    assert result["failed_count"] == 1
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_results_s3_happy_path_unknown_question_counted_as_failed():
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _MappingsResult({"student_id": "stu-1", "consumed_at": None}),
            _ScalarResult(None),
            _ScalarResult(None),
            _ScalarResult(None),
        ]
    )

    result = await process_sync_results(
        db=db,
        student_id="stu-1",
        package_id="pkg-3",
        results=[
            {
                "question_id": "missing-q",
                "selected_answer": "A",
                "is_correct": False,
                "time_seconds": 5.0,
            }
        ],
        completed_at="2026-04-20T09:00:00Z",
    )

    assert result["synced_count"] == 0
    assert result["failed_count"] == 1
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_results_s4_replay_rejected_as_batch():
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=_MappingsResult(
            {"student_id": "stu-1", "consumed_at": "2026-04-20T08:00:00Z"}
        )
    )

    result = await process_sync_results(
        db=db,
        student_id="stu-1",
        package_id="pkg-replay",
        results=[{"question_id": "q1", "selected_answer": "A", "is_correct": True}],
        completed_at="2026-04-20T09:00:00Z",
    )

    assert result["synced_count"] == 0
    assert result["failed_count"] == 1
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_sync_results_s5_unknown_package_rejected_as_batch():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_MappingsResult(None))

    result = await process_sync_results(
        db=db,
        student_id="stu-1",
        package_id="pkg-missing",
        results=[{"question_id": "q1", "selected_answer": "A", "is_correct": True}],
        completed_at="2026-04-20T09:00:00Z",
    )

    assert result["synced_count"] == 0
    assert result["failed_count"] == 1
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_sync_results_s6_ownership_rejected_with_error_log():
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=_MappingsResult({"student_id": "other-student", "consumed_at": None})
    )

    with patch("services.offline_sync_service.logger.error") as error_log:
        result = await process_sync_results(
            db=db,
            student_id="stu-1",
            package_id="pkg-owned-by-other",
            results=[{"question_id": "q1", "selected_answer": "A", "is_correct": True}],
            completed_at="2026-04-20T09:00:00Z",
        )

    assert result["synced_count"] == 0
    assert result["failed_count"] == 1
    error_log.assert_called_once()
    db.commit.assert_not_awaited()
