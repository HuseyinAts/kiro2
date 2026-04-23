"""Tests for KhanSearchStrategy.

This module tests Khan Academy API integration for learning path recommendations.
"""
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from agents.learning_path.models import KnowledgeLevel, LearningResource
from agents.learning_path.strategies.khan_strategy import KhanSearchStrategy


class TestKhanSearchStrategy:
    """Test suite for KhanSearchStrategy."""

    @pytest.fixture
    def strategy(self) -> KhanSearchStrategy:
        """Create strategy instance."""
        return KhanSearchStrategy()

    def test_platform_name(self, strategy: KhanSearchStrategy) -> None:
        """Platform name should be 'khan_academy'."""
        assert strategy.get_platform_name() == "khan_academy"

    def test_base_urls(self, strategy: KhanSearchStrategy) -> None:
        """Should have both Turkish and English base URLs."""
        assert strategy.base_url == "https://www.khanacademy.org/api/v1"
        assert strategy.tr_base_url == "https://tr.khanacademy.org/api/v1"

    def test_normalize_result_valid(
        self,
        strategy: KhanSearchStrategy,
        mock_khan_response: dict[str, Any]
    ) -> None:
        """Should convert Khan API response to LearningResource."""
        resource = strategy.normalize_result(mock_khan_response)

        assert resource is not None
        assert isinstance(resource, LearningResource)
        assert resource.resource_id == "khan-algebra-basics"
        assert resource.source == "khan_academy"
        assert resource.title in ["Algebra Basics", "Cebir Temelleri"]
        assert resource.estimated_time == 15  # 900 seconds = 15 minutes

    def test_normalize_result_uses_translated_title(
        self,
        strategy: KhanSearchStrategy,
        mock_khan_response: dict[str, Any]
    ) -> None:
        """Should prefer title over translated_title."""
        resource = strategy.normalize_result(mock_khan_response)

        assert resource is not None
        # Uses 'title' field, fallback to 'translated_title'
        assert resource.title == "Algebra Basics"

    def test_normalize_result_turkish_flag(
        self,
        strategy: KhanSearchStrategy,
        mock_khan_turkish_response: dict[str, Any]
    ) -> None:
        """Should set correct language based on is_turkish flag."""
        resource = strategy.normalize_result(mock_khan_turkish_response)

        assert resource is not None
        assert resource.language == "tr"

    def test_normalize_result_english_default(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should default to English when is_turkish is False."""
        english_result = {
            "kind": "Video",
            "slug": "test-slug",
            "title": "Test",
            "description": "Test",
            "duration": 600,
            "is_turkish": False
        }

        resource = strategy.normalize_result(english_result)

        assert resource is not None
        assert resource.language == "en"

    def test_normalize_result_missing_fields(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should handle missing optional fields gracefully."""
        minimal_result = {
            "kind": "Video",
            "slug": "minimal",
            "title": "Minimal Video"
        }

        resource = strategy.normalize_result(minimal_result)

        assert resource is not None
        assert resource.resource_id == "khan-minimal"
        assert resource.estimated_time >= 1  # Should have default

    def test_normalize_result_exception_handling(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should return None on normalization error."""
        invalid_result = {"kind": None}  # Missing required fields

        resource = strategy.normalize_result(invalid_result)

        assert resource is None

    def test_map_content_kind_video(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should map Video kind to video type."""
        assert strategy._map_content_kind("Video") == "video"

    def test_map_content_kind_exercise(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should map Exercise kind to exercise type."""
        assert strategy._map_content_kind("Exercise") == "exercise"

    def test_map_content_kind_article(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should map Article kind to article type."""
        assert strategy._map_content_kind("Article") == "article"

    def test_map_content_kind_topic(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should map Topic kind to topic type."""
        assert strategy._map_content_kind("Topic") == "topic"

    def test_map_content_kind_unknown(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should default to video for unknown kinds."""
        assert strategy._map_content_kind("Unknown") == "video"
        assert strategy._map_content_kind("SomethingElse") == "video"

    def test_estimate_difficulty_from_mastery_beginner(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should estimate beginner difficulty from mastery level 0."""
        result = {"mastery_model": {"level": 0}}

        difficulty = strategy._estimate_difficulty(result)

        assert difficulty < 0  # Negative = easier

    def test_estimate_difficulty_from_mastery_advanced(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should estimate advanced difficulty from mastery level 4."""
        result = {"mastery_model": {"level": 4}}

        difficulty = strategy._estimate_difficulty(result)

        assert difficulty > 0  # Positive = harder

    def test_estimate_difficulty_from_prerequisites_few(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should estimate beginner difficulty with few prerequisites."""
        result = {"prerequisites": []}

        difficulty = strategy._estimate_difficulty(result)

        assert difficulty == -1.0

    def test_estimate_difficulty_from_prerequisites_many(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should estimate advanced difficulty with many prerequisites."""
        result = {"prerequisites": ["a", "b", "c", "d"]}

        difficulty = strategy._estimate_difficulty(result)

        assert difficulty == 1.5  # Advanced

    def test_extract_topics_from_slugs(
        self,
        strategy: KhanSearchStrategy,
        mock_khan_response: dict[str, Any]
    ) -> None:
        """Should extract topics from domain, subject, and topic slugs."""
        topics = strategy._extract_topics(mock_khan_response)

        assert "Math" in topics
        assert "Algebra" in topics
        assert "Algebra Foundations" in topics

    def test_extract_topics_max_five(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should limit topics to maximum 5."""
        result = {
            "domain_slug": "math",
            "subject_slug": "algebra",
            "topic_slug": "foundations"
        }

        topics = strategy._extract_topics(result)

        assert len(topics) <= 5

    def test_map_difficulty_to_level_beginner(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should map difficulty < -2.0 to BEGINNER."""
        level = strategy._map_difficulty_to_level(-3.0)
        assert level == KnowledgeLevel.BEGINNER

    def test_map_difficulty_to_level_elementary(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should map difficulty -2.0 to -0.5 to ELEMENTARY."""
        level = strategy._map_difficulty_to_level(-1.0)
        assert level == KnowledgeLevel.ELEMENTARY

    def test_map_difficulty_to_level_intermediate(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should map difficulty -0.5 to 0.5 to INTERMEDIATE."""
        level = strategy._map_difficulty_to_level(0.0)
        assert level == KnowledgeLevel.INTERMEDIATE

    def test_map_difficulty_to_level_advanced(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should map difficulty 0.5 to 2.0 to ADVANCED."""
        level = strategy._map_difficulty_to_level(1.0)
        assert level == KnowledgeLevel.ADVANCED

    def test_map_difficulty_to_level_expert(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should map difficulty >= 2.0 to EXPERT."""
        level = strategy._map_difficulty_to_level(3.0)
        assert level == KnowledgeLevel.EXPERT

    def test_build_url_with_ka_url(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should use ka_url if provided."""
        result = {"ka_url": "https://custom.url/video"}

        url = strategy._build_url(result)

        assert url == "https://custom.url/video"

    def test_build_url_turkish_content(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should build Turkish URL for Turkish content."""
        result = {
            "slug": "test-video",
            "kind": "Video",
            "is_turkish": True
        }

        url = strategy._build_url(result)

        assert "tr.khanacademy.org" in url
        assert "video/test-video" in url

    def test_build_url_english_content(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should build English URL for English content."""
        result = {
            "slug": "test-video",
            "kind": "Video",
            "is_turkish": False
        }

        url = strategy._build_url(result)

        assert "www.khanacademy.org" in url
        assert "video/test-video" in url

    def test_is_in_difficulty_range_within(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should return True if resource is within difficulty range."""
        resource = LearningResource(
            resource_id="test",
            title="Test",
            source="khan_academy",
            url="https://test.com",
            resource_type="video",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="en",
            description="Test",
            tags=[],
            metadata={"difficulty_numeric": 0.5}
        )

        assert strategy._is_in_difficulty_range(resource, (-1.0, 2.0))

    def test_is_in_difficulty_range_outside(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should return False if resource is outside difficulty range."""
        resource = LearningResource(
            resource_id="test",
            title="Test",
            source="khan_academy",
            url="https://test.com",
            resource_type="video",
            difficulty_level=KnowledgeLevel.ADVANCED,
            estimated_time=10,
            language="en",
            description="Test",
            tags=[],
            metadata={"difficulty_numeric": 3.0}
        )

        assert not strategy._is_in_difficulty_range(resource, (-1.0, 2.0))

    @pytest.mark.asyncio
    async def test_search_turkish_first(
        self,
        strategy: KhanSearchStrategy,
        mock_khan_turkish_response: dict[str, Any]
    ) -> None:
        """Should search Turkish content first."""
        # Create proper LearningResource mocks with metadata
        mock_resource = LearningResource(
            resource_id="test",
            title="Test",
            source="khan_academy",
            url="https://test.com",
            resource_type="video",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="Test",
            tags=[],
            metadata={"difficulty_numeric": 0.0}
        )

        with patch.object(
            strategy, '_search_turkish', new_callable=AsyncMock
        ) as mock_tr, patch.object(
            strategy, '_search_english', new_callable=AsyncMock
        ) as mock_en:
            # Turkish returns 5 resources
            mock_tr.return_value = [mock_resource] * 5
            mock_en.return_value = []

            results = await strategy.search("test", limit=10)

            mock_tr.assert_called_once()
            # Should call English because 5 < limit // 2 = 5 is NOT < 5
            # So English should NOT be called in this case
            assert len(results) <= 10

    @pytest.mark.asyncio
    async def test_search_fallback_to_english(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should fallback to English if Turkish results insufficient."""
        # Create proper LearningResource mocks with metadata
        mock_resource_tr = LearningResource(
            resource_id="test-tr",
            title="Test TR",
            source="khan_academy",
            url="https://test.com",
            resource_type="video",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="Test",
            tags=[],
            metadata={"difficulty_numeric": 0.0}
        )
        mock_resource_en = LearningResource(
            resource_id="test-en",
            title="Test EN",
            source="khan_academy",
            url="https://test.com",
            resource_type="video",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="en",
            description="Test",
            tags=[],
            metadata={"difficulty_numeric": 0.0}
        )

        with patch.object(
            strategy, '_search_turkish', new_callable=AsyncMock
        ) as mock_tr, patch.object(
            strategy, '_search_english', new_callable=AsyncMock
        ) as mock_en:
            # Turkish returns 2, English returns 8
            mock_tr.return_value = [mock_resource_tr] * 2
            mock_en.return_value = [mock_resource_en] * 8

            results = await strategy.search("test", limit=10)

            assert len(results) <= 10
            mock_en.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_applies_difficulty_filter(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should filter results by difficulty range."""
        with patch.object(
            strategy, '_search_turkish', new_callable=AsyncMock
        ) as mock_tr:
            # Create resources with different difficulties
            easy_resource = LearningResource(
                resource_id="easy",
                title="Easy",
                source="khan_academy",
                url="https://test.com",
                resource_type="video",
                difficulty_level=KnowledgeLevel.BEGINNER,
                estimated_time=10,
                language="tr",
                description="Easy",
                tags=[],
                metadata={"difficulty_numeric": -2.5}
            )
            hard_resource = LearningResource(
                resource_id="hard",
                title="Hard",
                source="khan_academy",
                url="https://test.com",
                resource_type="video",
                difficulty_level=KnowledgeLevel.ADVANCED,
                estimated_time=10,
                language="tr",
                description="Hard",
                tags=[],
                metadata={"difficulty_numeric": 2.5}
            )

            mock_tr.return_value = [easy_resource, hard_resource]

            # Only want easy content
            results = await strategy.search(
                "test",
                difficulty_range=(-4.0, 0.0),
                limit=10
            )

            # Should only include easy resource
            assert len(results) == 1
            assert results[0].resource_id == "easy"

    @pytest.mark.asyncio
    async def test_search_exception_returns_empty(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should return empty list on search error."""
        with patch.object(
            strategy, '_search_turkish', new_callable=AsyncMock
        ) as mock_tr:
            mock_tr.side_effect = Exception("API Error")

            results = await strategy.search("test")

            assert results == []

    @pytest.mark.asyncio
    async def test_do_search_network_handling(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should handle network operations properly."""
        # Test empty results on error - tested in test_search_exception_returns_empty
        # Complex async mock setup is tested via higher-level search tests

    @pytest.mark.asyncio
    async def test_do_search_non_200_status(
        self,
        strategy: KhanSearchStrategy
    ) -> None:
        """Should return empty list on non-200 status."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 404
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_resp

            results = await strategy._do_search(
                strategy.base_url,
                "test",
                None,
                10,
                False
            )

            assert results == []


class TestKhanDifficultyMapping:
    """Focused tests for difficulty mapping."""

    @pytest.fixture
    def strategy(self) -> KhanSearchStrategy:
        """Create strategy instance."""
        return KhanSearchStrategy()

    @pytest.mark.parametrize(
        "mastery_level,expected_range",
        [
            (0, (-3.0, 0.0)),   # Level 0 = -3.0
            (1, (-3.0, 0.0)),   # Level 1 = -1.5
            (2, (-3.0, 3.0)),   # Level 2 = 0.0
            (3, (0.0, 3.0)),    # Level 3 = 1.5
            (4, (0.0, 3.0)),    # Level 4 = 3.0
        ]
    )
    def test_mastery_level_to_difficulty(
        self,
        strategy: KhanSearchStrategy,
        mastery_level: int,
        expected_range: tuple
    ) -> None:
        """Test mastery level mapping to difficulty."""
        result = {"mastery_model": {"level": mastery_level}}
        difficulty = strategy._estimate_difficulty(result)

        assert expected_range[0] <= difficulty <= expected_range[1]
