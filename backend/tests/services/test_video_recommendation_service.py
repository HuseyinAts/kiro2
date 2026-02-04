"""
Unit Tests - VideoRecommendationService
Learning Path Video Yükleme Sorunu Çözümü - Task 19

Comprehensive unit tests for VideoRecommendationService
Requirements: 11.1, 11.2
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import List
import json

from services.video_recommendation_service import (
    VideoRecommendationService,
    StudentProfile,
    VideoRecommendation,
)
from services.advanced_youtube_search import TurkishEducationVideo
from services.turkish_content_filter import TurkishValidationResult


class TestVideoRecommendationService:
    """VideoRecommendationService unit tests - %80+ coverage hedefi"""

    @pytest.fixture
    def mock_cache(self):
        """Mock MultiLayerCache"""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.get_stats = Mock(
            return_value={
                "memory": {"hits": 10, "misses": 5, "size": 15},
                "redis": {"hits": 20, "misses": 10, "size": 30},
            }
        )
        return cache

    @pytest.fixture
    def mock_advanced_search(self):
        """Mock AdvancedYouTubeSearch"""
        search = AsyncMock()
        search.search_videos_with_filters = AsyncMock(return_value=[])
        return search

    @pytest.fixture
    def mock_semantic_search(self):
        """Mock SemanticYouTubeSearch"""
        search = AsyncMock()
        search.semantic_search_videos = AsyncMock(return_value=[])
        return search

    @pytest.fixture
    def mock_content_filter(self):
        """Mock TurkishContentFilter"""
        filter_service = AsyncMock()
        filter_service.validate_turkish_content = AsyncMock(
            return_value=TurkishValidationResult(
                is_turkish=True,
                confidence_score=0.9,
                detected_language="tr",
                turkish_indicators=["turkish_chars", "turkish_words"],
            )
        )
        return filter_service

    @pytest.fixture
    def video_service(
        self,
        mock_cache,
        mock_advanced_search,
        mock_semantic_search,
        mock_content_filter,
    ):
        """VideoRecommendationService instance"""
        return VideoRecommendationService(
            cache=mock_cache,
            advanced_search=mock_advanced_search,
            semantic_search=mock_semantic_search,
            content_filter=mock_content_filter,
        )

    @pytest.fixture
    def sample_student_profile(self):
        """Sample student profile"""
        return StudentProfile(
            goals=["TYT Matematik", "AYT Fizik"],
            currentLevel={"matematik": 60, "fizik": 50},
            learningStyle="görsel",
        )

    @pytest.fixture
    def sample_video(self):
        """Sample TurkishEducationVideo"""
        return TurkishEducationVideo(
            video_id="test123",
            title="Matematik Konu Anlatımı",
            channel="Tonguç Akademi",
            channel_id="UC123",
            duration="10:30",
            view_count=10000,
            upload_date="2024-01-01",
            thumbnail="https://example.com/thumb.jpg",
            description="Test açıklama",
            quality_score=8.5,
            subject="matematik",
            difficulty="orta",
            exam_type="TYT",
            language_score=9.0,
            education_relevance=8.0,
            url="https://youtube.com/watch?v=test123",
        )

    # ==================== Cache Tests ====================

    @pytest.mark.asyncio
    async def test_cache_hit(self, video_service, mock_cache, sample_student_profile):
        """Test cache hit scenario - Req 11.1"""
        # Arrange
        cached_data = {
            "recommendations": [
                {
                    "subject_exam": "Matematik TYT",
                    "videos": [],
                    "total_count": 0,
                    "cache_hit": True,
                    "response_time_ms": 5,
                }
            ]
        }
        mock_cache.get = AsyncMock(return_value=cached_data)

        # Act
        result = await video_service.get_recommendations(
            sample_student_profile, "test-request-123"
        )

        # Assert
        assert len(result) > 0
        assert result[0].cache_hit is True
        assert video_service.cache_hits == 1
        assert video_service.cache_misses == 0
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss(self, video_service, mock_cache, sample_student_profile):
        """Test cache miss scenario - Req 11.1"""
        # Arrange
        mock_cache.get = AsyncMock(return_value=None)

        # Act
        result = await video_service.get_recommendations(
            sample_student_profile, "test-request-123"
        )

        # Assert
        assert video_service.cache_hits == 0
        assert video_service.cache_misses == 1
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()

    # ==================== Parallel Discovery Tests ====================

    @pytest.mark.asyncio
    async def test_parallel_discovery(
        self,
        video_service,
        mock_advanced_search,
        mock_semantic_search,
        sample_student_profile,
        sample_video,
    ):
        """Test parallel video discovery - Req 11.2"""
        # Arrange
        mock_advanced_search.search_videos_with_filters = AsyncMock(
            return_value=[sample_video]
        )
        mock_semantic_search.semantic_search_videos = AsyncMock(return_value=[])

        # Act
        result = await video_service._discover_videos(
            sample_student_profile, "test-123"
        )

        # Assert
        # Max 3 goals processed
        assert len(result) <= 3
        # Verify parallel execution (both searches called)
        assert mock_advanced_search.search_videos_with_filters.called
        assert mock_semantic_search.semantic_search_videos.called

    # ==================== Subject Extraction Tests ====================

    @pytest.mark.asyncio
    async def test_extract_subject_matematik(self, video_service):
        """Test matematik subject extraction"""
        assert video_service._extract_subject("TYT Matematik") == "matematik"
        assert video_service._extract_subject("Geometri Konu Anlatımı") == "matematik"
        assert video_service._extract_subject("Algebra") == "matematik"

    @pytest.mark.asyncio
    async def test_extract_subject_fizik(self, video_service):
        """Test fizik subject extraction - Req 11.1"""
        assert video_service._extract_subject("AYT Fizik") == "fizik"
        assert video_service._extract_subject("Mekanik Dersi") == "fizik"

    @pytest.mark.asyncio
    async def test_extract_subject_default(self, video_service):
        """Test default subject extraction - Req 11.1"""
        assert video_service._extract_subject("Bilinmeyen Ders") == "matematik"

    # ==================== Exam Type Extraction Tests ====================

    @pytest.mark.asyncio
    async def test_extract_exam_type_tyt(self, video_service):
        """Test TYT exam type extraction"""
        assert video_service._extract_exam_type("TYT Matematik") == "TYT"

    @pytest.mark.asyncio
    async def test_extract_exam_type_ayt(self, video_service):
        """Test AYT exam type extraction - Req 11.1"""
        assert video_service._extract_exam_type("AYT Fizik") == "AYT"

    @pytest.mark.asyncio
    async def test_extract_exam_type_lgs(self, video_service):
        """Test LGS exam type extraction - Req 11.1"""
        assert video_service._extract_exam_type("LGS Matematik") == "LGS"

    @pytest.mark.asyncio
    async def test_extract_exam_type_default(self, video_service):
        """Test default exam type extraction - Req 11.1"""
        assert video_service._extract_exam_type("Matematik Dersi") == "TYT"

    # ==================== Difficulty Determination Tests ====================

    @pytest.mark.asyncio
    async def test_difficulty_baslangiç(self, video_service):
        """Test başlangıç difficulty when subject level < 30"""
        current_level = {"matematik": 20}
        assert (
            video_service._determine_difficulty("matematik", current_level)
            == "başlangıç"
        )

    @pytest.mark.asyncio
    async def test_difficulty_orta(self, video_service):
        """Test orta difficulty determination - Req 11.1"""
        current_level = {"matematik": 50}
        assert video_service._determine_difficulty("matematik", current_level) == "orta"

    @pytest.mark.asyncio
    async def test_difficulty_ileri(self, video_service):
        """Test ileri difficulty determination - Req 11.1"""
        current_level = {"matematik": 80}
        assert (
            video_service._determine_difficulty("matematik", current_level) == "ileri"
        )

    @pytest.mark.asyncio
    async def test_difficulty_default_when_subject_not_in_current_level(
        self, video_service
    ):
        """Test default difficulty when subject not in current level - Req 11.1"""
        current_level = {"fizik": 60}
        assert video_service._determine_difficulty("matematik", current_level) == "orta"

    # ==================== Video Merging Tests ====================

    @pytest.mark.asyncio
    async def test_merge_videos_deduplication(self, video_service, sample_video):
        """Test video merging and deduplication - Req 11.2"""
        # Arrange
        video1 = sample_video
        video2 = TurkishEducationVideo(
            video_id="test123",  # Same ID
            title="Duplicate Video",
            channel="Test",
            channel_id="UC456",
            duration="5:00",
            view_count=5000,
            upload_date="2024-01-02",
            thumbnail="https://example.com/thumb2.jpg",
            description="Duplicate",
            quality_score=7.0,
            subject="matematik",
            difficulty="orta",
            exam_type="TYT",
            language_score=8.0,
            education_relevance=7.0,
            url="https://youtube.com/watch?v=test123",
        )

        # Act
        merged = video_service._merge_videos([video1], [video2])

        # Assert
        # Verify deduplication (same video_id)
        assert len(merged) == 1  # Deduplicated
        assert merged[0].video_id == "test123"

    # ==================== Metrics Collection Tests ====================

    @pytest.mark.asyncio
    async def test_get_metrics(self, video_service):
        """Test metrics collection - Req 11.1"""
        # Arrange
        video_service.total_requests = 10
        video_service.cache_hits = 7
        video_service.cache_misses = 3
        video_service.total_response_time = 1000.0

        # Act
        metrics = video_service.get_metrics()

        # Assert
        assert metrics["service"]["total_requests"] == 10
        assert metrics["service"]["cache_hits"] == 7
        assert metrics["service"]["cache_misses"] == 3
        assert "70.0%" in metrics["service"]["cache_hit_rate"]
        assert "cache" in metrics

    # ==================== Error Handling Tests ====================

    @pytest.mark.asyncio
    async def test_error_handling_returns_empty_list(
        self, video_service, mock_cache, sample_student_profile
    ):
        """Test error handling returns empty list - Req 11.2"""
        # Arrange
        mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))

        # Act
        result = await video_service.get_recommendations(
            sample_student_profile, "test-request-123"
        )

        # Assert
        assert result == []

    # ==================== Serialization Tests ====================

    @pytest.mark.asyncio
    async def test_serialize_recommendations(self, video_service, sample_video):
        """Test recommendation serialization - Req 11.1"""
        # Arrange
        recommendation = VideoRecommendation(
            subject_exam="Matematik TYT",
            videos=[sample_video],
            total_count=1,
            cache_hit=False,
            response_time_ms=100,
        )

        # Act
        serialized = video_service._serialize_recommendations([recommendation])

        # Assert
        assert "recommendations" in serialized
        assert len(serialized["recommendations"]) == 1
        assert serialized["recommendations"][0]["subject_exam"] == "Matematik TYT"
        assert len(serialized["recommendations"][0]["videos"]) == 1

    @pytest.mark.asyncio
    async def test_deserialize_recommendations(self, video_service, sample_video):
        """Test recommendation deserialization - Req 11.1"""
        # Arrange
        recommendation = VideoRecommendation(
            subject_exam="Matematik TYT",
            videos=[sample_video],
            total_count=1,
            cache_hit=False,
            response_time_ms=100,
        )
        serialized = video_service._serialize_recommendations([recommendation])

        # Act
        deserialized = video_service._deserialize_recommendations(serialized)

        # Assert
        assert len(deserialized) == 1
        assert deserialized[0].subject_exam == "Matematik TYT"
        assert len(deserialized[0].videos) == 1
        assert deserialized[0].videos[0].video_id == "test123"

    # ==================== Cache Key Generation Tests ====================

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, video_service, sample_student_profile):
        """Test cache key generation - Req 11.1"""
        # Act
        key1 = video_service._generate_cache_key(sample_student_profile)
        key2 = video_service._generate_cache_key(sample_student_profile)

        # Assert
        # Same profile = same key
        assert key1 == key2
        assert key1.startswith("video_rec:")
        assert len(key1) > 10

    @pytest.mark.asyncio
    async def test_cache_key_different_profiles(self, video_service):
        """Test different profiles generate different keys - Req 11.1"""
        # Arrange
        profile1 = StudentProfile(
            goals=["TYT Matematik"],
            currentLevel={"matematik": 60},
            learningStyle="görsel",
        )
        profile2 = StudentProfile(
            goals=["AYT Fizik"], currentLevel={"fizik": 50}, learningStyle="işitsel"
        )

        # Act
        key1 = video_service._generate_cache_key(profile1)
        key2 = video_service._generate_cache_key(profile2)

        # Assert
        assert key1 != key2

    # ==================== Turkish Content Filtering Tests ====================

    @pytest.mark.asyncio
    async def test_filter_turkish_content(
        self, video_service, mock_content_filter, sample_video
    ):
        """Test Turkish content filtering - Req 11.2"""
        # Arrange
        mock_content_filter.validate_turkish_content = AsyncMock(
            return_value=TurkishValidationResult(
                is_turkish=True,
                confidence_score=0.9,
                detected_language="tr",
                turkish_indicators=["turkish_chars"],
            )
        )

        # Act
        filtered = await video_service._filter_turkish_content(
            [sample_video], "test-123"
        )

        # Assert
        assert len(filtered) == 1
        assert filtered[0].video_id == "test123"

    @pytest.mark.asyncio
    async def test_filter_non_turkish_content(
        self, video_service, mock_content_filter, sample_video
    ):
        """Test non-Turkish content filtering - Req 11.2"""
        # Arrange
        mock_content_filter.validate_turkish_content = AsyncMock(
            return_value=TurkishValidationResult(
                is_turkish=False,
                confidence_score=0.3,
                detected_language="en",
                turkish_indicators=[],
            )
        )

        # Act
        filtered = await video_service._filter_turkish_content(
            [sample_video], "test-123"
        )

        # Assert
        assert len(filtered) == 0  # Non-Turkish video filtered out

    # ==================== Integration Tests ====================

    @pytest.mark.asyncio
    async def test_full_recommendation_flow(
        self,
        video_service,
        mock_cache,
        mock_advanced_search,
        mock_semantic_search,
        sample_student_profile,
        sample_video,
    ):
        """Test full recommendation flow - Req 11.2"""
        # Arrange
        mock_cache.get = AsyncMock(return_value=None)  # Cache miss
        mock_advanced_search.search_videos_with_filters = AsyncMock(
            return_value=[sample_video]
        )
        mock_semantic_search.semantic_search_videos = AsyncMock(return_value=[])

        # Act
        result = await video_service.get_recommendations(
            sample_student_profile, "test-request-123"
        )

        # Assert
        assert len(result) > 0
        assert video_service.total_requests == 1
        assert video_service.cache_misses == 1
        mock_cache.set.assert_called_once()


# ==================== Additional Edge Case Tests ====================


class TestVideoRecommendationServiceEdgeCases:
    """Edge case tests for VideoRecommendationService"""

    @pytest.mark.asyncio
    async def test_empty_goals(self):
        """Test handling of empty goals"""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.get_stats = Mock(return_value={})

        service = VideoRecommendationService(
            cache=cache,
            advanced_search=AsyncMock(),
            semantic_search=AsyncMock(),
            content_filter=AsyncMock(),
        )

        profile = StudentProfile(goals=[], currentLevel={}, learningStyle="görsel")

        result = await service.get_recommendations(profile, "test-123")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_many_goals_limits_to_three(self):
        """Test that only first 3 goals are processed"""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.get_stats = Mock(return_value={})

        advanced_search = AsyncMock()
        advanced_search.search_videos_with_filters = AsyncMock(return_value=[])

        semantic_search = AsyncMock()
        semantic_search.semantic_search_videos = AsyncMock(return_value=[])

        content_filter = AsyncMock()

        service = VideoRecommendationService(
            cache=cache,
            advanced_search=advanced_search,
            semantic_search=semantic_search,
            content_filter=content_filter,
        )

        profile = StudentProfile(
            goals=["Goal1", "Goal2", "Goal3", "Goal4", "Goal5"],
            currentLevel={},
            learningStyle="görsel",
        )

        result = await service._discover_videos(profile, "test-123")
        # Should process max 3 goals
        assert len(result) <= 3
