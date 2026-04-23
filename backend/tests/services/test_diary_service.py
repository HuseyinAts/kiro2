"""
Unit tests for DiaryService (REQ-1)

Daily diary entry creation and management tests.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


class TestDiaryServiceTaskAggregation:
    """Test REQ-1.1: Task Aggregation"""

    def test_aggregate_tasks(self):
        """Test task aggregation calculations"""
        from api.schemas.diary import TaskSummary
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        tasks = [
            TaskSummary(title="Task 1", status="success", duration_minutes=60),
            TaskSummary(title="Task 2", status="success", duration_minutes=30),
            TaskSummary(title="Task 3", status="failure", duration_minutes=45),
        ]

        aggregation = service.aggregate_tasks(tasks)

        assert aggregation["total_tasks"] == 3
        assert aggregation["success_count"] == 2
        assert aggregation["failure_count"] == 1
        assert aggregation["total_duration_minutes"] == 135

    def test_aggregate_tasks_empty(self):
        """Test task aggregation with no tasks"""
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        aggregation = service.aggregate_tasks([])

        assert aggregation["total_tasks"] == 0
        assert aggregation["success_count"] == 0
        assert aggregation["total_duration_minutes"] == 0

    def test_aggregate_tasks_with_partial(self):
        """Test task aggregation with partial tasks"""
        from api.schemas.diary import TaskSummary
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        tasks = [
            TaskSummary(title="Task 1", status="success", duration_minutes=60),
            TaskSummary(title="Task 2", status="partial", duration_minutes=30),
        ]

        aggregation = service.aggregate_tasks(tasks)

        assert aggregation["partial_count"] == 1
        assert aggregation["success_rate"] == 50.0


class TestDiaryServiceLearningsExtraction:
    """Test REQ-1.2: Key Learnings Extraction"""

    def test_extract_learnings_from_tasks(self):
        """Test learning extraction from successful tasks"""
        from api.schemas.diary import TaskSummary
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        tasks = [
            TaskSummary(
                title="API Implementation",
                status="success",
                duration_minutes=60,
                notes="Learned about async patterns and how to properly handle exceptions in FastAPI"
            ),
            TaskSummary(
                title="Failed Task",
                status="failure",
                duration_minutes=30,
                notes="Need to understand better"
            ),
        ]

        learnings = service.extract_learnings(tasks, max_learnings=3)

        assert isinstance(learnings, list)
        assert len(learnings) <= 3

    def test_extract_learnings_empty_tasks(self):
        """Test learning extraction with empty task list"""
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        learnings = service.extract_learnings([])

        assert learnings == []


class TestDiaryServiceHighlightsSelection:
    """Test REQ-1.3: Highlights Selection"""

    def test_select_highlights_from_tasks(self):
        """Test highlight selection from tasks"""
        from api.schemas.diary import TaskSummary
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        tasks = [
            TaskSummary(
                title="Completed major feature",
                status="success",
                duration_minutes=120,
                notes="Finally finished the authentication system"
            ),
            TaskSummary(
                title="Minor fix",
                status="success",
                duration_minutes=15,
            ),
        ]

        highlights = service.select_highlights(tasks, max_highlights=3)

        assert isinstance(highlights, list)
        assert len(highlights) <= 3

    def test_select_highlights_empty(self):
        """Test highlight selection with no tasks"""
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        highlights = service.select_highlights([])

        assert highlights == []


class TestDiaryServiceChallengesExtraction:
    """Test REQ-1.4: Challenges Extraction"""

    def test_extract_challenges_from_failures(self):
        """Test challenge extraction from failed tasks"""
        from api.schemas.diary import TaskSummary
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        tasks = [
            TaskSummary(
                title="Bug Fix",
                status="failure",
                duration_minutes=60,
                notes="Couldn't figure out the async issue"
            ),
            TaskSummary(
                title="Success Task",
                status="success",
                duration_minutes=30,
            ),
        ]

        challenges = service.extract_challenges(tasks)

        assert isinstance(challenges, list)

    def test_extract_challenges_no_failures(self):
        """Test challenge extraction with no failed tasks"""
        from api.schemas.diary import TaskSummary
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        tasks = [
            TaskSummary(title="Success", status="success", duration_minutes=30),
        ]

        challenges = service.extract_challenges(tasks)

        assert isinstance(challenges, list)


class TestDiaryServiceMarkdownGeneration:
    """Test REQ-1.5: Markdown Generation"""

    def test_format_markdown(self):
        """Test markdown format generation"""
        from api.schemas.diary import TaskSummary
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        entry_date = date.today()
        tasks = [
            TaskSummary(title="Task 1", status="success", duration_minutes=60),
        ]
        stats = service.aggregate_tasks(tasks)
        learnings = ["Learned about async"]
        highlights = ["Completed feature"]
        challenges = ["Debugging was hard"]

        markdown = service.format_markdown(
            entry_date=entry_date,
            stats=stats,
            highlights=highlights,
            learnings=learnings,
            challenges=challenges,
            tasks=tasks,
        )

        assert isinstance(markdown, str)
        assert "##" in markdown  # Has headers

    def test_format_markdown_minimal(self):
        """Test markdown format with minimal data"""
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        markdown = service.format_markdown(
            entry_date=date.today(),
            stats={"total_tasks": 0, "success_count": 0, "failure_count": 0, "partial_count": 0, "total_duration_minutes": 0, "success_rate": 0},
            highlights=[],
            learnings=[],
            challenges=[],
            tasks=[],
        )

        assert isinstance(markdown, str)


class TestDiaryServiceCRUD:
    """Test CRUD operations"""

    @pytest.mark.asyncio
    async def test_generate_summary(self):
        """Test generating a diary summary"""
        from api.schemas.diary import TaskSummary
        from services.diary_service import DiaryService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock no existing entry
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = DiaryService(mock_db)

        tasks = [
            TaskSummary(title="Task 1", status="success", duration_minutes=60),
        ]

        summary = await service.generate_summary(
            user_id=uuid4(),
            entry_date=date.today(),
            tasks=tasks,
        )

        assert summary is not None

    @pytest.mark.asyncio
    async def test_get_summary(self):
        """Test getting a summary by user_id and date"""
        from services.diary_service import DiaryService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = DiaryService(mock_db)

        summary = await service.get_summary(uuid4(), date.today())

        assert summary is None

    @pytest.mark.asyncio
    async def test_get_summaries(self):
        """Test getting summaries list"""
        from services.diary_service import DiaryService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = DiaryService(mock_db)

        summaries = await service.get_summaries(
            user_id=uuid4(),
            limit=20
        )

        assert isinstance(summaries, list)

    @pytest.mark.asyncio
    async def test_get_today_summary(self):
        """Test getting today's summary"""
        from services.diary_service import DiaryService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = DiaryService(mock_db)

        summary = await service.get_today_summary(uuid4())

        assert summary is None

    @pytest.mark.asyncio
    async def test_update_summary(self):
        """Test updating a summary"""
        from api.schemas.diary import DiaryEntryUpdate
        from services.diary_service import DiaryService

        mock_db = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.id = uuid4()
        mock_entry.user_id = uuid4()
        mock_entry.notes = "Old notes"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = DiaryService(mock_db)

        update = DiaryEntryUpdate(notes="New notes")

        result = await service.update_summary(mock_entry.id, update)

        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_summary(self):
        """Test deleting a summary"""
        from services.diary_service import DiaryService

        mock_db = AsyncMock()

        mock_entry = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        service = DiaryService(mock_db)

        result = await service.delete_summary(uuid4())

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_summary_not_found(self):
        """Test deleting non-existent summary"""
        from services.diary_service import DiaryService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = DiaryService(mock_db)

        result = await service.delete_summary(uuid4())

        assert result is False


class TestDiaryServiceWeeklyStats:
    """Test weekly statistics"""

    @pytest.mark.asyncio
    async def test_get_weekly_stats(self):
        """Test getting weekly statistics"""
        from services.diary_service import DiaryService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = DiaryService(mock_db)

        # week_start is a required parameter
        week_start = date.today() - timedelta(days=date.today().weekday())
        stats = await service.get_weekly_stats(uuid4(), week_start)

        assert isinstance(stats, dict)


class TestDiaryServiceFilePath:
    """Test file path generation"""

    def test_get_file_path(self):
        """Test file path generation for entries"""
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        entry_date = date(2026, 1, 15)
        path = service.get_file_path(entry_date)

        assert isinstance(path, str)
        assert "2026" in path or "01" in path or "15" in path


class TestDiaryServiceTurkishDayName:
    """Test Turkish day name generation"""

    def test_get_turkish_day_name(self):
        """Test Turkish day name for dates"""
        from services.diary_service import DiaryService

        mock_db = MagicMock()
        service = DiaryService(mock_db)

        test_date = date(2026, 1, 20)  # Tuesday
        day_name = service._get_turkish_day_name(test_date)

        assert isinstance(day_name, str)
        # Implementation uses ASCII characters
        assert day_name in ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]
