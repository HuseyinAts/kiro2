"""Tests for RAGSearchStrategy.

This module tests RAG/ChromaDB semantic search strategy for learning path recommendations.
"""
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.learning_path.models import KnowledgeLevel, LearningResource
from agents.learning_path.strategies.rag_strategy import RAGSearchStrategy


class TestRAGSearchStrategy:
    """Test suite for RAGSearchStrategy."""

    @pytest.fixture
    def mock_rag_service(self) -> MagicMock:
        """Create mock RAG search service."""
        service = MagicMock()
        service.search = AsyncMock(return_value=[])
        service.find_similar = AsyncMock(return_value=[])
        service.add_resource = AsyncMock(return_value=True)
        return service

    @pytest.fixture
    def strategy(self, mock_rag_service: MagicMock) -> RAGSearchStrategy:
        """Create strategy instance with mock service."""
        return RAGSearchStrategy(rag_service=mock_rag_service)

    @pytest.fixture
    def strategy_no_service(self) -> RAGSearchStrategy:
        """Create strategy without pre-injected service."""
        return RAGSearchStrategy()

    def test_platform_name(self, strategy: RAGSearchStrategy) -> None:
        """Platform name should be 'rag'."""
        assert strategy.get_platform_name() == "rag"

    def test_priority(self, strategy: RAGSearchStrategy) -> None:
        """RAG should have higher priority for semantic search."""
        assert strategy.get_priority() == -1

    def test_lazy_initialization(
        self,
        strategy_no_service: RAGSearchStrategy
    ) -> None:
        """Should lazily initialize RAGSearchService."""
        assert strategy_no_service._rag_service is None

        # Accessing property should initialize
        service = strategy_no_service.rag_service

        assert service is not None
        assert strategy_no_service._rag_service is not None

    def test_normalize_dict_result(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_response: dict[str, Any]
    ) -> None:
        """Should convert dict to LearningResource."""
        resource = strategy.normalize_result(mock_rag_response)

        assert resource is not None
        assert isinstance(resource, LearningResource)
        assert resource.resource_id == "question_123"
        assert resource.source == "rag"
        assert resource.title == "Trigonometri Soru Bankası"
        assert resource.resource_type == "question"

    def test_normalize_learning_resource_passthrough(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should pass through existing LearningResource."""
        existing = LearningResource(
            resource_id="test-123",
            title="Test Resource",
            source="rag",
            url="https://test.com",
            resource_type="question",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="Test description",
            tags=["test"]
        )

        result = strategy.normalize_result(existing)

        assert result is existing

    def test_normalize_result_with_minimal_fields(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should handle minimal fields in dict."""
        minimal = {
            "id": "min-123",
            "title": "Minimal Question",
            "content": "Question text here"
        }

        resource = strategy.normalize_result(minimal)

        assert resource is not None
        assert resource.resource_id == "min-123"
        assert resource.source == "rag"

    def test_normalize_result_generates_url(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should generate URL if not provided."""
        result_without_url = {
            "id": "q-456",
            "title": "Question",
            "content": "Content"
        }

        resource = strategy.normalize_result(result_without_url)

        assert resource is not None
        assert resource.url == "/questions/q-456"

    def test_normalize_result_uses_provided_url(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_response: dict[str, Any]
    ) -> None:
        """Should use provided URL if available."""
        resource = strategy.normalize_result(mock_rag_response)

        assert resource is not None
        assert resource.url == "/questions/question_123"

    def test_normalize_result_exception_handling(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should handle missing fields gracefully with defaults."""
        minimal = {"content": "Some content"}  # Minimal valid

        resource = strategy.normalize_result(minimal)

        # Should create resource with defaults, not return None
        assert resource is not None
        assert resource.source == "rag"

    def test_map_difficulty_to_level_beginner(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should map difficulty < -2.0 to BEGINNER."""
        level = strategy._map_difficulty_to_level(-3.0)
        assert level == KnowledgeLevel.BEGINNER

    def test_map_difficulty_to_level_elementary(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should map difficulty -2.0 to -0.5 to ELEMENTARY."""
        level = strategy._map_difficulty_to_level(-1.5)
        assert level == KnowledgeLevel.ELEMENTARY

    def test_map_difficulty_to_level_intermediate(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should map difficulty -0.5 to 0.5 to INTERMEDIATE."""
        level = strategy._map_difficulty_to_level(0.0)
        assert level == KnowledgeLevel.INTERMEDIATE

    def test_map_difficulty_to_level_advanced(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should map difficulty 0.5 to 2.0 to ADVANCED."""
        level = strategy._map_difficulty_to_level(1.0)
        assert level == KnowledgeLevel.ADVANCED

    def test_map_difficulty_to_level_expert(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should map difficulty >= 2.0 to EXPERT."""
        level = strategy._map_difficulty_to_level(2.5)
        assert level == KnowledgeLevel.EXPERT

    @pytest.mark.asyncio
    async def test_search_delegates_to_service(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Search should delegate to RAGSearchService."""
        await strategy.search("test query", subject="matematik", limit=10)

        mock_rag_service.search.assert_called_once_with(
            query="test query",
            subject="matematik",
            difficulty_range=(-4.0, 4.0),
            limit=10
        )

    @pytest.mark.asyncio
    async def test_search_validates_query(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should validate query before searching."""
        # Empty query should raise ValueError
        with pytest.raises(ValueError):
            await strategy.search("")

    @pytest.mark.asyncio
    async def test_search_swaps_invalid_difficulty_range(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should swap difficulty range if min > max."""
        await strategy.search(
            "test",
            difficulty_range=(2.0, -2.0),  # Invalid order
            limit=10
        )

        # Should swap to (-2.0, 2.0)
        call_args = mock_rag_service.search.call_args
        difficulty_range = call_args[1]["difficulty_range"]
        assert difficulty_range == (-2.0, 2.0)

    @pytest.mark.asyncio
    async def test_search_returns_resources(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should return resources from service."""
        mock_resource = LearningResource(
            resource_id="test",
            title="Test",
            source="rag",
            url="https://test.com",
            resource_type="question",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="Test",
            tags=[]
        )
        mock_rag_service.search.return_value = [mock_resource]

        results = await strategy.search("test")

        assert len(results) == 1
        assert results[0].resource_id == "test"

    @pytest.mark.asyncio
    async def test_search_exception_returns_empty(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should return empty list on search error."""
        mock_rag_service.search.side_effect = Exception("Search failed")

        results = await strategy.search("test")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_similar_delegates_to_service(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should delegate similar search to service."""
        await strategy.search_similar("question_123", limit=5)

        mock_rag_service.find_similar.assert_called_once_with("question_123", 5)

    @pytest.mark.asyncio
    async def test_search_similar_returns_resources(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should return similar resources from service."""
        mock_resource = LearningResource(
            resource_id="similar",
            title="Similar",
            source="rag",
            url="https://test.com",
            resource_type="question",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="Similar",
            tags=[]
        )
        mock_rag_service.find_similar.return_value = [mock_resource]

        results = await strategy.search_similar("ref_123")

        assert len(results) == 1
        assert results[0].resource_id == "similar"

    @pytest.mark.asyncio
    async def test_search_similar_not_supported(
        self,
        strategy_no_service: RAGSearchStrategy
    ) -> None:
        """Should return empty if similar search not supported."""
        # Create service without find_similar method
        service = MagicMock()
        service.search = AsyncMock(return_value=[])
        # No find_similar attribute
        del service.find_similar
        strategy_no_service._rag_service = service

        results = await strategy_no_service.search_similar("test")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_similar_exception_returns_empty(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should return empty list on similar search error."""
        mock_rag_service.find_similar.side_effect = Exception("Find similar failed")

        results = await strategy.search_similar("test")

        assert results == []

    @pytest.mark.asyncio
    async def test_add_resource_delegates_to_service(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should delegate add resource to service."""
        resource = LearningResource(
            resource_id="new",
            title="New Resource",
            source="rag",
            url="https://test.com",
            resource_type="question",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="New",
            tags=[]
        )

        await strategy.add_resource(resource)

        mock_rag_service.add_resource.assert_called_once_with(resource)

    @pytest.mark.asyncio
    async def test_add_resource_returns_success(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should return True on successful add."""
        resource = LearningResource(
            resource_id="new",
            title="New",
            source="rag",
            url="https://test.com",
            resource_type="question",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="New",
            tags=[]
        )
        mock_rag_service.add_resource.return_value = True

        success = await strategy.add_resource(resource)

        assert success is True

    @pytest.mark.asyncio
    async def test_add_resource_not_supported(
        self,
        strategy_no_service: RAGSearchStrategy
    ) -> None:
        """Should return False if add resource not supported."""
        # Create service without add_resource method
        service = MagicMock()
        service.search = AsyncMock(return_value=[])
        del service.add_resource
        strategy_no_service._rag_service = service

        resource = LearningResource(
            resource_id="new",
            title="New",
            source="rag",
            url="https://test.com",
            resource_type="question",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="New",
            tags=[]
        )

        success = await strategy_no_service.add_resource(resource)

        assert success is False

    @pytest.mark.asyncio
    async def test_add_resource_exception_returns_false(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_service: MagicMock
    ) -> None:
        """Should return False on add resource error."""
        mock_rag_service.add_resource.side_effect = Exception("Add failed")

        resource = LearningResource(
            resource_id="new",
            title="New",
            source="rag",
            url="https://test.com",
            resource_type="question",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="New",
            tags=[]
        )

        success = await strategy.add_resource(resource)

        assert success is False

    def test_normalize_extracts_topics(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_response: dict[str, Any]
    ) -> None:
        """Should extract topics from result."""
        resource = strategy.normalize_result(mock_rag_response)

        assert resource is not None
        assert "trigonometri" in resource.tags
        assert "matematik" in resource.tags

    def test_normalize_handles_non_list_topics(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should handle non-list topics gracefully."""
        result = {
            "id": "test",
            "title": "Test",
            "content": "Content",
            "topics": "single_topic"  # Not a list
        }

        resource = strategy.normalize_result(result)

        assert resource is not None
        assert resource.tags == []  # Should be empty, not error

    def test_normalize_uses_metadata(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_response: dict[str, Any]
    ) -> None:
        """Should extract and use metadata."""
        resource = strategy.normalize_result(mock_rag_response)

        assert resource is not None
        assert resource.metadata is not None
        assert resource.metadata["subject"] == "matematik"
        assert resource.metadata["question_count"] == 25

    def test_normalize_description_truncation(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should truncate description to 500 characters."""
        long_content = "A" * 1000
        result = {
            "id": "test",
            "title": "Test",
            "content": long_content
        }

        resource = strategy.normalize_result(result)

        assert resource is not None
        assert len(resource.description) <= 500


class TestRAGDifficultyMapping:
    """Focused tests for difficulty mapping."""

    @pytest.fixture
    def strategy(self) -> RAGSearchStrategy:
        """Create strategy instance."""
        return RAGSearchStrategy()

    @pytest.mark.parametrize(
        "irt_difficulty,expected_level",
        [
            (-3.0, KnowledgeLevel.BEGINNER),
            (-2.5, KnowledgeLevel.BEGINNER),
            (-2.0, KnowledgeLevel.ELEMENTARY),
            (-1.0, KnowledgeLevel.ELEMENTARY),
            (-0.5, KnowledgeLevel.ELEMENTARY),
            (0.0, KnowledgeLevel.INTERMEDIATE),
            (0.4, KnowledgeLevel.INTERMEDIATE),
            (0.5, KnowledgeLevel.ADVANCED),
            (1.5, KnowledgeLevel.ADVANCED),
            (2.0, KnowledgeLevel.EXPERT),
            (3.0, KnowledgeLevel.EXPERT),
        ]
    )
    def test_irt_to_knowledge_level_mapping(
        self,
        strategy: RAGSearchStrategy,
        irt_difficulty: float,
        expected_level: KnowledgeLevel
    ) -> None:
        """Test IRT difficulty to KnowledgeLevel mapping."""
        level = strategy._map_difficulty_to_level(irt_difficulty)
        assert level == expected_level


class TestRAGResourceNormalization:
    """Focused tests for resource normalization edge cases."""

    @pytest.fixture
    def strategy(self) -> RAGSearchStrategy:
        """Create strategy instance."""
        return RAGSearchStrategy()

    def test_normalize_with_hash_fallback(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should generate resource_id from content hash if missing."""
        result = {
            "title": "No ID Resource",
            "content": "Some content"
        }

        resource = strategy.normalize_result(result)

        assert resource is not None
        assert resource.resource_id.startswith("rag_")

    def test_normalize_default_resource_type(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should default to 'question' resource type."""
        result = {
            "id": "test",
            "title": "Test",
            "content": "Content"
        }

        resource = strategy.normalize_result(result)

        assert resource is not None
        assert resource.resource_type == "question"

    def test_normalize_default_language(
        self,
        strategy: RAGSearchStrategy
    ) -> None:
        """Should default to Turkish language."""
        result = {
            "id": "test",
            "title": "Test",
            "content": "Content"
        }

        resource = strategy.normalize_result(result)

        assert resource is not None
        assert resource.language == "tr"

    def test_normalize_uses_rating(
        self,
        strategy: RAGSearchStrategy,
        mock_rag_response: dict[str, Any]
    ) -> None:
        """Should extract rating from result."""
        resource = strategy.normalize_result(mock_rag_response)

        assert resource is not None
        assert resource.rating == 4.2
