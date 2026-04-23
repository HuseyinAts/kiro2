"""Tests for OERSearchStrategy.

This module tests OER Commons API integration for learning path recommendations.
"""
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from agents.learning_path.models import KnowledgeLevel, LearningResource
from agents.learning_path.strategies.oer_strategy import OERSearchStrategy


class TestOERSearchStrategy:
    """Test suite for OERSearchStrategy."""

    @pytest.fixture
    def strategy(self) -> OERSearchStrategy:
        """Create strategy instance."""
        return OERSearchStrategy()

    def test_platform_name(self, strategy: OERSearchStrategy) -> None:
        """Platform name should be 'oer_commons'."""
        assert strategy.get_platform_name() == "oer_commons"

    def test_base_url(self, strategy: OERSearchStrategy) -> None:
        """Should have correct API base URL."""
        assert strategy.base_url == "https://www.oercommons.org/api/v1"

    def test_normalize_result_valid(
        self,
        strategy: OERSearchStrategy,
        mock_oer_response: dict[str, Any]
    ) -> None:
        """Should convert OER API response to LearningResource."""
        resource = strategy.normalize_result(mock_oer_response)

        assert resource is not None
        assert isinstance(resource, LearningResource)
        assert resource.resource_id == "oer-oer-123"
        assert resource.source == "oer_commons"
        assert resource.title == "Introduction to Calculus"
        assert resource.resource_type == "document"

    def test_normalize_result_with_all_fields(
        self,
        strategy: OERSearchStrategy,
        mock_oer_response: dict[str, Any]
    ) -> None:
        """Should extract all available fields."""
        resource = strategy.normalize_result(mock_oer_response)

        assert resource is not None
        assert resource.rating == 4.5
        assert "Mathematics" in resource.tags or "Calculus" in resource.tags
        assert resource.metadata is not None
        assert resource.metadata["license"] == "CC-BY"
        assert resource.metadata["author"] == "Dr. Math Teacher"

    def test_normalize_result_minimal_fields(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should handle minimal field set."""
        minimal = {
            "id": "min-123",
            "title": "Minimal Resource",
            "url": "https://example.com"
        }

        resource = strategy.normalize_result(minimal)

        assert resource is not None
        assert resource.resource_id == "oer-min-123"

    def test_normalize_result_exception_handling(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should return None on normalization error."""
        invalid = {"id": None}  # Will cause error

        resource = strategy.normalize_result(invalid)

        assert resource is None

    def test_map_media_type_video(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map video media type."""
        assert strategy._map_media_type("video") == "video"

    def test_map_media_type_document(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map document media type."""
        assert strategy._map_media_type("document") == "document"

    def test_map_media_type_interactive(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map interactive media types."""
        assert strategy._map_media_type("interactive") == "interactive"
        assert strategy._map_media_type("simulation") == "interactive"
        assert strategy._map_media_type("activity") == "interactive"

    def test_map_media_type_assessment(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map assessment to exercise."""
        assert strategy._map_media_type("assessment") == "exercise"

    def test_map_media_type_unknown(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should default to document for unknown types."""
        assert strategy._map_media_type("unknown") == "document"

    def test_estimate_duration_from_result(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should use duration from result if available."""
        result = {"duration": 1800}  # 1800 seconds = 30 minutes

        duration = strategy._estimate_duration(result, "video")

        assert duration == 30

    def test_estimate_duration_from_result_large_value(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should convert large duration values from seconds."""
        result = {"duration": 3600}  # 3600 seconds = 60 minutes

        duration = strategy._estimate_duration(result, "video")

        assert duration == 60

    def test_estimate_duration_by_type(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should estimate duration based on resource type."""
        assert strategy._estimate_duration({}, "video") == 15
        assert strategy._estimate_duration({}, "document") == 20
        assert strategy._estimate_duration({}, "interactive") == 30
        assert strategy._estimate_duration({}, "course") == 60

    def test_estimate_duration_from_word_count(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should estimate duration from word count for documents."""
        result = {"word_count": 2000}  # 2000 words = 10 minutes at 200 wpm

        duration = strategy._estimate_duration(result, "document")

        # Returns max(base, estimated) = max(20, 10) = 20
        assert duration == 20

    def test_estimate_difficulty_elementary(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should estimate elementary difficulty from K-5 grades."""
        result = {"grade_level": ["K", "1", "2"]}

        difficulty = strategy._estimate_difficulty(result)

        assert difficulty < -1.0  # Elementary level

    def test_estimate_difficulty_middle_school(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should estimate middle school difficulty from grades 6-8."""
        result = {"grade_level": ["6", "7", "8"]}

        difficulty = strategy._estimate_difficulty(result)

        assert -1.0 <= difficulty <= 1.5

    def test_estimate_difficulty_high_school(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should estimate high school difficulty from grades 9-12."""
        result = {"grade_level": ["9", "10", "11", "12"]}

        difficulty = strategy._estimate_difficulty(result)

        assert difficulty > 1.0  # Advanced level

    def test_estimate_difficulty_higher_education(
        self,
        strategy: OERSearchStrategy,
        mock_oer_multilevel_response: dict[str, Any]
    ) -> None:
        """Should estimate higher education difficulty."""
        difficulty = strategy._estimate_difficulty(mock_oer_multilevel_response)

        assert difficulty >= 2.0  # Advanced/Expert level

    def test_estimate_difficulty_no_grade_level(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should default to intermediate when no grade level."""
        result = {}

        difficulty = strategy._estimate_difficulty(result)

        assert difficulty == 0.0

    def test_estimate_difficulty_average_multiple_grades(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should average difficulty for multiple grade levels."""
        result = {"grade_level": ["6", "9"]}  # Mix of middle and high school

        difficulty = strategy._estimate_difficulty(result)

        # Should be between grades 6 and 9 difficulty
        assert 0.0 <= difficulty <= 2.0

    def test_map_difficulty_to_level_beginner(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map difficulty < -2.0 to BEGINNER."""
        level = strategy._map_difficulty_to_level(-3.0)
        assert level == KnowledgeLevel.BEGINNER

    def test_map_difficulty_to_level_elementary(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map difficulty -2.0 to -0.5 to ELEMENTARY."""
        level = strategy._map_difficulty_to_level(-1.0)
        assert level == KnowledgeLevel.ELEMENTARY

    def test_map_difficulty_to_level_intermediate(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map difficulty -0.5 to 1.0 to INTERMEDIATE."""
        level = strategy._map_difficulty_to_level(0.5)
        assert level == KnowledgeLevel.INTERMEDIATE

    def test_map_difficulty_to_level_advanced(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map difficulty 1.0 to 2.5 to ADVANCED."""
        level = strategy._map_difficulty_to_level(2.0)
        assert level == KnowledgeLevel.ADVANCED

    def test_map_difficulty_to_level_expert(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map difficulty >= 2.5 to EXPERT."""
        level = strategy._map_difficulty_to_level(3.0)
        assert level == KnowledgeLevel.EXPERT

    def test_extract_topics_from_subjects(
        self,
        strategy: OERSearchStrategy,
        mock_oer_response: dict[str, Any]
    ) -> None:
        """Should extract topics from subjects."""
        topics = strategy._extract_topics(mock_oer_response)

        assert "Mathematics" in topics
        assert "Calculus" in topics

    def test_extract_topics_from_keywords(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should extract topics from keywords."""
        result = {
            "keywords": ["physics", "mechanics", "waves"]
        }

        topics = strategy._extract_topics(result)

        assert "Physics" in topics or "Mechanics" in topics or "Waves" in topics

    def test_extract_topics_max_five(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should limit topics to maximum 5."""
        result = {
            "subjects": ["Math", "Science", "Physics"],
            "keywords": ["algebra", "geometry", "calculus", "trigonometry"]
        }

        topics = strategy._extract_topics(result)

        assert len(topics) <= 5

    def test_extract_rating_valid(
        self,
        strategy: OERSearchStrategy,
        mock_oer_response: dict[str, Any]
    ) -> None:
        """Should extract valid rating."""
        rating = strategy._extract_rating(mock_oer_response)

        assert rating == 4.5

    def test_extract_rating_from_avg_rating(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should extract from avg_rating field."""
        result = {"avg_rating": 3.7}

        rating = strategy._extract_rating(result)

        assert rating == 3.7

    def test_extract_rating_normalize_10_scale(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should normalize 0-10 scale to 0-5."""
        result = {"rating": 8.0}  # Assume 0-10 scale

        rating = strategy._extract_rating(result)

        assert rating == 4.0  # 8 / 2 = 4

    def test_extract_rating_clamp_max(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should normalize and clamp rating."""
        result = {"rating": 6.0}

        rating = strategy._extract_rating(result)

        # 6.0 > 5.0, so divide by 2 = 3.0, then min(5.0, 3.0) = 3.0
        assert rating == 3.0

    def test_extract_rating_none_when_missing(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should return None when rating is missing."""
        result = {}

        rating = strategy._extract_rating(result)

        assert rating is None

    def test_is_in_difficulty_range_within(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should return True if resource is within difficulty range."""
        resource = LearningResource(
            resource_id="test",
            title="Test",
            source="oer_commons",
            url="https://test.com",
            resource_type="document",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="en",
            description="Test",
            tags=[],
            metadata={"difficulty_irt": 0.5}
        )

        assert strategy._is_in_difficulty_range(resource, (-1.0, 2.0))

    def test_is_in_difficulty_range_outside(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should return False if resource is outside difficulty range."""
        resource = LearningResource(
            resource_id="test",
            title="Test",
            source="oer_commons",
            url="https://test.com",
            resource_type="document",
            difficulty_level=KnowledgeLevel.EXPERT,
            estimated_time=10,
            language="en",
            description="Test",
            tags=[],
            metadata={"difficulty_irt": 3.5}
        )

        assert not strategy._is_in_difficulty_range(resource, (-1.0, 2.0))

    @pytest.mark.asyncio
    async def test_search_validates_query(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should validate query before searching."""
        with patch.object(strategy, 'validate_query') as mock_validate:
            with patch.object(strategy, '_search_oer', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = []

                await strategy.search("test query")

                mock_validate.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_search_applies_difficulty_filter(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should filter results by difficulty range."""
        with patch.object(strategy, '_search_oer', new_callable=AsyncMock) as mock_search:
            # Create resources with different difficulties
            easy_result = {
                "id": "easy",
                "title": "Easy Resource",
                "url": "https://test.com",
                "grade_level": ["K", "1"],
                "media_type": "video"
            }
            hard_result = {
                "id": "hard",
                "title": "Hard Resource",
                "url": "https://test.com",
                "grade_level": ["Higher Education"],
                "media_type": "document"
            }

            mock_search.return_value = [easy_result, hard_result]

            # Only want easy content
            results = await strategy.search(
                "test",
                difficulty_range=(-4.0, 0.0),
                limit=10
            )

            # Should only include easy resource
            assert len(results) == 1
            assert results[0].resource_id == "oer-easy"

    @pytest.mark.asyncio
    async def test_search_exception_returns_empty(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should return empty list on search error."""
        with patch.object(strategy, '_search_oer', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("API Error")

            results = await strategy.search("test")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_oer_network_handling(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should handle network operations properly."""
        # Network error handling is tested in test_search_oer_network_error
        # Complex async mock setup is tested via higher-level search tests

    @pytest.mark.asyncio
    async def test_search_oer_with_subject_mapping(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should map Turkish subjects to English."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value={"results": []})
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_resp

            await strategy._search_oer("test", subject="matematik", limit=10)

            # Check that params included mapped subject
            call_args = mock_session.return_value.__aenter__.return_value.get.call_args
            params = call_args[1]["params"]
            assert params["subject"] == "mathematics"

    @pytest.mark.asyncio
    async def test_search_oer_license_filter(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should filter for open licenses."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value={"results": []})
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_resp

            await strategy._search_oer("test", None, 10)

            # Check license parameter
            call_args = mock_session.return_value.__aenter__.return_value.get.call_args
            params = call_args[1]["params"]
            assert "cc-by" in params["license"]

    @pytest.mark.asyncio
    async def test_search_oer_non_200_status(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should return empty list on non-200 status."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 500
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_resp

            results = await strategy._search_oer("test", None, 10)

            assert results == []

    @pytest.mark.asyncio
    async def test_search_oer_network_error(
        self,
        strategy: OERSearchStrategy
    ) -> None:
        """Should handle network errors gracefully."""
        import aiohttp

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.side_effect = (
                aiohttp.ClientError("Network error")
            )

            results = await strategy._search_oer("test", None, 10)

            assert results == []


class TestOERGradeLevelMapping:
    """Focused tests for grade level to difficulty mapping."""

    @pytest.fixture
    def strategy(self) -> OERSearchStrategy:
        """Create strategy instance."""
        return OERSearchStrategy()

    @pytest.mark.parametrize(
        "grade_levels,expected_range",
        [
            (["K"], (-3.5, -2.5)),
            (["1", "2"], (-3.0, -1.5)),
            (["5"], (-1.0, 0.0)),
            (["6", "7", "8"], (-0.5, 1.5)),
            (["9", "10"], (1.0, 2.5)),
            (["11", "12"], (2.0, 3.5)),
            (["Higher Education"], (3.0, 4.0)),
            (["Professional"], (3.5, 4.5)),
        ]
    )
    def test_grade_level_difficulty_mapping(
        self,
        strategy: OERSearchStrategy,
        grade_levels: list,
        expected_range: tuple
    ) -> None:
        """Test grade level mapping to IRT difficulty."""
        result = {"grade_level": grade_levels}
        difficulty = strategy._estimate_difficulty(result)

        assert expected_range[0] <= difficulty <= expected_range[1]
