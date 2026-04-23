"""
Unit tests for LearningJournalService (REQ-4)

Knowledge tracking, spaced repetition, and knowledge graph tests.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from api.schemas.diary import LearningEntryCreate


class TestLearningJournalServiceEntryCreation:
    """Test REQ-4.1: Knowledge Entry Creation"""

    @pytest.mark.asyncio
    async def test_create_entry(self):
        """Test creating a learning entry"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = LearningJournalService(mock_db)

        data = LearningEntryCreate(
            title="Async Patterns in Python",
            content="Today I learned about async/await patterns in Python and how they work with FastAPI.",
            tags=["python", "async", "fastapi"],
            domain="backend",
            importance=4,
        )

        await service.create_entry(uuid4(), data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_entry_auto_summary(self):
        """Test auto-summary generation for long content"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = LearningJournalService(mock_db)

        long_content = "A" * 200  # Long content without summary
        data = LearningEntryCreate(
            title="Test Entry",
            content=long_content,
        )

        await service.create_entry(uuid4(), data)

        # Entry should have been created with auto-summary
        mock_db.add.assert_called_once()


class TestLearningJournalServiceTagging:
    """Test REQ-4.2: Categorization with Tags"""

    def test_auto_tag_backend_content(self):
        """Test auto-tagging for backend content"""
        from services.learning_journal_service import LearningJournalService

        mock_db = MagicMock()
        service = LearningJournalService(mock_db)

        tags = service.auto_tag(
            content="FastAPI REST API development with PostgreSQL database",
            title="API Development"
        )

        assert isinstance(tags, list)
        assert "backend" in tags or "database" in tags

    def test_auto_tag_frontend_content(self):
        """Test auto-tagging for frontend content"""
        from services.learning_journal_service import LearningJournalService

        mock_db = MagicMock()
        service = LearningJournalService(mock_db)

        tags = service.auto_tag(
            content="React component with TypeScript and CSS styling",
            title="UI Component"
        )

        assert isinstance(tags, list)
        assert "frontend" in tags

    def test_auto_tag_testing_content(self):
        """Test auto-tagging for testing content"""
        from services.learning_journal_service import LearningJournalService

        mock_db = MagicMock()
        service = LearningJournalService(mock_db)

        tags = service.auto_tag(
            content="pytest unit tests with mock objects and coverage",
            title="Testing"
        )

        assert isinstance(tags, list)
        assert "testing" in tags

    def test_auto_tag_max_tags(self):
        """Test that auto-tagging returns max 10 tags"""
        from services.learning_journal_service import LearningJournalService

        mock_db = MagicMock()
        service = LearningJournalService(mock_db)

        # Content with many keywords
        content = "api server database sql rest fastapi django react vue angular css html javascript typescript docker kubernetes ci/cd pytest unittest coverage"
        tags = service.auto_tag(content=content, title="Full Stack")

        assert len(tags) <= 10

    @pytest.mark.asyncio
    async def test_update_tags(self):
        """Test updating tags for an entry"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()

        # Mock entry lookup
        mock_entry = MagicMock()
        mock_entry.tags = ["old_tag"]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = LearningJournalService(mock_db)

        result = await service.update_tags(uuid4(), uuid4(), ["new_tag", "python"])

        assert result is not None
        assert result.tags == ["new_tag", "python"]


class TestLearningJournalServiceConceptLinking:
    """Test REQ-4.3: Concept Linking / Knowledge Graph"""

    @pytest.mark.asyncio
    async def test_link_concepts(self):
        """Test linking concepts to an entry"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.related_concepts = []
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = LearningJournalService(mock_db)

        result = await service.link_concepts(
            uuid4(), uuid4(),
            concepts=["async", "await", "coroutine"]
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_link_concepts_not_found(self):
        """Test linking concepts to non-existent entry"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = LearningJournalService(mock_db)

        result = await service.link_concepts(uuid4(), uuid4(), ["concept"])

        assert result is None


class TestLearningJournalServiceSpacedRepetition:
    """Test REQ-4.4: Spaced Repetition Scheduling"""

    def test_intervals_defined(self):
        """Test that INTERVALS are properly defined"""
        from services.learning_journal_service import LearningJournalService

        assert LearningJournalService.INTERVALS == [1, 3, 7, 14, 30, 60, 120]

    def test_default_ease_factor(self):
        """Test default ease factor value"""
        from services.learning_journal_service import LearningJournalService

        assert LearningJournalService.DEFAULT_EASE == 2.5

    @pytest.mark.asyncio
    async def test_get_due_reviews(self):
        """Test getting entries due for review"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = LearningJournalService(mock_db)

        entries = await service.get_due_reviews(uuid4())

        assert isinstance(entries, list)
        mock_db.execute.assert_called_once()


class TestLearningJournalServiceGapDetection:
    """Test REQ-4.5: Gap Detection"""

    @pytest.mark.asyncio
    async def test_detect_gaps_empty(self):
        """Test gap detection with no entries"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = LearningJournalService(mock_db)

        gaps = await service.detect_gaps(uuid4())

        assert isinstance(gaps, list)


class TestLearningJournalServiceKnowledgeGraph:
    """Test REQ-4.6: Knowledge Graph Visualization"""

    @pytest.mark.asyncio
    async def test_get_knowledge_graph(self):
        """Test getting knowledge graph"""
        import networkx as nx

        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()

        # Create mock entries with all required attributes
        entry1 = MagicMock()
        entry1.id = uuid4()
        entry1.title = "Python Basics"
        entry1.domain = "backend"
        entry1.importance = 3
        entry1.related_concepts = ["variables", "loops"]
        entry1.tags = ["python"]
        entry1.mastery_level = 0.8

        entry2 = MagicMock()
        entry2.id = uuid4()
        entry2.title = "FastAPI"
        entry2.domain = "backend"
        entry2.importance = 4
        entry2.related_concepts = ["api", "python"]
        entry2.tags = ["backend", "python"]
        entry2.mastery_level = 0.6

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [entry1, entry2]
        mock_db.execute.return_value = mock_result

        service = LearningJournalService(mock_db)

        graph = await service.get_knowledge_graph(uuid4())

        assert isinstance(graph, nx.Graph)


class TestLearningJournalServiceCRUD:
    """Test CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_entries(self):
        """Test getting learning entries with filters"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = LearningJournalService(mock_db)

        entries = await service.get_entries(
            user_id=uuid4(),
            domain=None,
            tag=None,
            limit=20
        )

        assert isinstance(entries, list)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_entry_by_id(self):
        """Test getting entry by ID"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = LearningJournalService(mock_db)

        entry = await service.get_entry_by_id(uuid4(), uuid4())

        assert entry is None

    @pytest.mark.asyncio
    async def test_delete_entry_not_found(self):
        """Test deleting non-existent entry"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = LearningJournalService(mock_db)

        result = await service.delete_entry(uuid4(), uuid4())

        assert result is False


class TestLearningJournalServiceDomains:
    """Test domain constants"""

    def test_domains_list(self):
        """Test that DOMAINS contains expected values"""
        from services.learning_journal_service import LearningJournalService

        domains = LearningJournalService.DOMAINS

        assert "backend" in domains
        assert "frontend" in domains
        assert "devops" in domains
        assert "database" in domains
        assert "security" in domains
        assert "ai_ml" in domains
        assert "testing" in domains


class TestLearningJournalServiceReview:
    """Test review functionality"""

    @pytest.mark.asyncio
    async def test_record_review(self):
        """Test recording a review for an entry"""
        from api.schemas.diary import LearningReviewRequest
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.id = uuid4()
        mock_entry.review_count = 0
        mock_entry.interval_days = 1
        mock_entry.ease_factor = 2.5
        mock_entry.retention_score = 0.8
        mock_entry.mastery_level = 0.5
        mock_entry.next_review = datetime.now()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = LearningJournalService(mock_db)

        # record_review takes user_id and LearningReviewRequest
        review_data = LearningReviewRequest(
            entry_id=mock_entry.id,
            remembered=True,
            quality=4
        )

        result = await service.record_review(uuid4(), review_data)

        assert result is not None


class TestLearningJournalServiceSearch:
    """Test search functionality"""

    @pytest.mark.asyncio
    async def test_search_entries(self):
        """Test searching learning entries"""
        from services.learning_journal_service import LearningJournalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = LearningJournalService(mock_db)

        entries = await service.search_entries(
            user_id=uuid4(),
            query="python async"
        )

        assert isinstance(entries, list)
