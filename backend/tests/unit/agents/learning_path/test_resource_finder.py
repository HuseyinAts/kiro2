"""
Unit Tests for ResourceFinder
Coverage Target: 90%+
"""

import pytest
from unittest.mock import Mock, AsyncMock

import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
)

from backend.agents.learning_path.core.resource_finder import ResourceFinder
from backend.agents.learning_path.models import (
    LearningResource,
    KnowledgeLevel,
    LearningStyle,
)


@pytest.fixture
def mock_youtube():
    """Mock YouTube service"""
    mock = Mock()
    mock.search = AsyncMock(
        return_value=[
            {
                "id": "vid1",
                "title": "Test Video",
                "url": "https://youtube.com/watch?v=test",
                "duration": "PT10M",
                "description": "Test description",
                "views": 1000,
                "likes": 100,
                "channel": "Test Channel",
                "published_at": "2024-01-01",
            }
        ]
    )
    return mock


@pytest.fixture
def mock_khan():
    """Mock Khan Academy service"""
    mock = Mock()
    mock.search = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def resource_finder(mock_youtube, mock_khan):
    """ResourceFinder instance"""
    return ResourceFinder(youtube_service=mock_youtube, khan_service=mock_khan)


@pytest.mark.asyncio
class TestResourceFinder:
    """Test suite for ResourceFinder"""

    async def test_search_resources_success(self, resource_finder, mock_youtube):
        """Test successful resource search"""
        results = await resource_finder.search_resources("Matematik", count=5)

        assert len(results) > 0
        assert isinstance(results[0], LearningResource)
        mock_youtube.search.assert_called_once()

    async def test_search_resources_invalid_inputs(self, resource_finder):
        """Test with invalid inputs"""
        with pytest.raises(ValueError):
            await resource_finder.search_resources("", count=5)

        with pytest.raises(ValueError):
            await resource_finder.search_resources("Math", count=0)

        with pytest.raises(ValueError):
            await resource_finder.search_resources("Math", count=100)

    async def test_search_by_topic(self, resource_finder):
        """Test simple topic search"""
        results = await resource_finder.search_by_topic("Math")
        assert isinstance(results, list)

    async def test_search_by_difficulty(self, resource_finder):
        """Test difficulty-based search"""
        results = await resource_finder.search_by_difficulty(
            "Math", KnowledgeLevel.INTERMEDIATE
        )
        assert isinstance(results, list)

    async def test_search_by_style(self, resource_finder):
        """Test style-based search"""
        results = await resource_finder.search_by_style("Math", LearningStyle.VISUAL)
        assert isinstance(results, list)

    def test_get_style_recommendations(self, resource_finder):
        """Test style recommendations"""
        resources = [
            LearningResource(
                resource_id="r1",
                title="Test",
                source="YouTube",
                url="http://test.com",
                resource_type="video",
                difficulty_level=KnowledgeLevel.INTERMEDIATE,
                estimated_time=10,
                language="tr",
                description="Test",
                tags=[],
            )
        ]

        recommendations = resource_finder.get_style_recommendations(
            resources, LearningStyle.VISUAL
        )

        assert len(recommendations) > 0
        assert "match_score" in recommendations[0]

    async def test_caching(self, resource_finder):
        """Test result caching"""
        # First call
        results1 = await resource_finder.search_resources("Math", count=5)

        # Second call (should use cache)
        results2 = await resource_finder.search_resources("Math", count=5)

        assert results1 == results2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
