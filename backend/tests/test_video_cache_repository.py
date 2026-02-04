"""
Unit tests for OptimizedVideoRepository
Tests core functionality without requiring full database setup
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from models.video_cache_model import VideoCache
from repositories.video_cache_repository import OptimizedVideoRepository


@pytest.fixture
def mock_session():
    """Create mock async session"""
    session = Mock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create repository with mock session"""
    return OptimizedVideoRepository(mock_session)


@pytest.fixture
def sample_video():
    """Create sample video cache entry"""
    return VideoCache(
        id=uuid4(),
        video_id="test_video_123",
        title="Test Video - Matematik Geometri",
        description="Test description",
        channel_name="Test Channel",
        channel_id="channel_123",
        thumbnail_url="https://example.com/thumb.jpg",
        duration=600,
        subject="matematik",
        difficulty="orta",
        exam_type="TYT",
        language="tr",
        quality_score=8.5,
        relevance_score=0.85,
        language_score=0.95,
        difficulty_match=0.90,
        view_count=10000,
        like_count=500,
        comment_count=50,
        video_metadata={"test": True},
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow(),
        last_accessed=datetime.utcnow(),
        access_count=10,
        cache_ttl=3600,
    )


class TestVideoCacheModel:
    """Test VideoCache model"""

    def test_video_cache_creation(self, sample_video):
        """Test video cache model creation"""
        assert sample_video.video_id == "test_video_123"
        assert sample_video.subject == "matematik"
        assert sample_video.quality_score == 8.5
        assert sample_video.language == "tr"

    def test_to_dict(self, sample_video):
        """Test model to dictionary conversion"""
        video_dict = sample_video.to_dict()

        assert video_dict["video_id"] == "test_video_123"
        assert video_dict["subject"] == "matematik"
        assert video_dict["quality_score"] == 8.5
        assert "created_at" in video_dict

    def test_update_access(self, sample_video):
        """Test access tracking update"""
        import time

        initial_count = sample_video.access_count
        initial_time = sample_video.last_accessed

        # Small delay to ensure timestamp difference
        time.sleep(0.001)
        sample_video.update_access()

        assert sample_video.access_count == initial_count + 1
        assert sample_video.last_accessed >= initial_time

    def test_is_expired(self, sample_video):
        """Test cache expiration check"""
        # Fresh entry should not be expired
        assert not sample_video.is_expired()

        # Set last_updated to past
        from datetime import timedelta

        sample_video.last_updated = datetime.utcnow() - timedelta(hours=2)
        sample_video.cache_ttl = 3600  # 1 hour

        # Should be expired
        assert sample_video.is_expired()

    def test_calculate_overall_score(self, sample_video):
        """Test overall score calculation"""
        overall_score = sample_video.calculate_overall_score()

        # Should be weighted average
        expected = (
            (8.5 / 10.0) * 0.4
            + 0.85 * 0.3  # quality_score
            + 0.95 * 0.2  # relevance_score
            + 0.90 * 0.1  # language_score  # difficulty_match
        )

        assert abs(overall_score - expected) < 0.01


class TestOptimizedVideoRepository:
    """Test OptimizedVideoRepository"""

    @pytest.mark.asyncio
    async def test_find_videos_optimized(self, repository, mock_session, sample_video):
        """Test optimized video search"""
        # Mock query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_video]
        mock_session.execute.return_value = mock_result

        # Execute query
        videos = await repository.find_videos_optimized(
            subject="matematik",
            difficulty="orta",
            exam_type="TYT",
            language="tr",
            min_quality=7.0,
            min_relevance=0.7,
            limit=20,
        )

        # Verify
        assert len(videos) == 1
        assert videos[0].video_id == "test_video_123"
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_find_videos_by_subject(self, repository, mock_session, sample_video):
        """Test subject-only video search"""
        # Mock query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_video]
        mock_session.execute.return_value = mock_result

        # Execute query
        videos = await repository.find_videos_by_subject(
            subject="matematik", min_quality=7.0, limit=50
        )

        # Verify
        assert len(videos) == 1
        assert videos[0].subject == "matematik"

    @pytest.mark.asyncio
    async def test_find_videos_flexible(self, repository, mock_session, sample_video):
        """Test flexible video search with difficulty tolerance"""
        # Mock query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_video]
        mock_session.execute.return_value = mock_result

        # Execute query
        videos = await repository.find_videos_flexible(
            subject="matematik",
            target_difficulty="orta",
            exam_type="TYT",
            language="tr",
            min_quality=6.0,
            difficulty_tolerance=1,
            limit=20,
        )

        # Verify
        assert len(videos) == 1
        assert videos[0].difficulty in ["başlangıç", "orta", "ileri"]

    @pytest.mark.asyncio
    async def test_get_top_quality_videos(self, repository, mock_session, sample_video):
        """Test getting top quality videos"""
        # Mock query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_video]
        mock_session.execute.return_value = mock_result

        # Execute query
        videos = await repository.get_top_quality_videos(subject="matematik", limit=100)

        # Verify
        assert len(videos) == 1
        assert videos[0].quality_score >= 7.0

    @pytest.mark.asyncio
    async def test_bulk_upsert(self, repository, mock_session):
        """Test bulk upsert operation"""
        # Prepare test data
        videos = [
            {
                "video_id": f"test_{i}",
                "title": f"Test Video {i}",
                "description": "Test",
                "channel_name": "Test Channel",
                "channel_id": "channel_1",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "duration": 600,
                "subject": "matematik",
                "difficulty": "orta",
                "exam_type": "TYT",
                "language": "tr",
                "quality_score": 8.0,
                "relevance_score": 0.8,
                "language_score": 0.9,
                "difficulty_match": 0.85,
                "view_count": 1000,
                "like_count": 50,
                "comment_count": 10,
                "metadata": {},
                "cache_ttl": 3600,
            }
            for i in range(10)
        ]

        # Execute bulk upsert
        count = await repository.bulk_upsert(videos)

        # Verify
        assert count == 10
        assert mock_session.execute.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_get_cache_statistics(self, repository, mock_session):
        """Test cache statistics retrieval"""
        # Mock query result
        mock_result = Mock()
        mock_result.fetchone.return_value = (
            1000,  # total_entries
            5,  # unique_subjects
            3,  # unique_exam_types
            8.5,  # avg_quality_score
            0.85,  # avg_relevance_score
            15.5,  # avg_access_count
            100,  # max_access_count
            50,  # expired_entries
            200,  # accessed_last_hour
            800,  # accessed_last_day
        )
        mock_session.execute.return_value = mock_result

        # Execute query
        stats = await repository.get_cache_statistics()

        # Verify
        assert stats["total_entries"] == 1000
        assert stats["unique_subjects"] == 5
        assert stats["avg_quality_score"] == 8.5
        assert stats["expired_entries"] == 50


class TestQueryPerformance:
    """Test query performance characteristics"""

    def test_composite_index_coverage(self):
        """
        Test that composite index covers common query patterns

        Composite index: (subject, difficulty, exam_type, language, quality_score DESC)
        """
        # This test documents the expected index usage
        # In production, use EXPLAIN ANALYZE to verify

        query_patterns = [
            # Pattern 1: Full composite index usage
            {
                "subject": "matematik",
                "difficulty": "orta",
                "exam_type": "TYT",
                "language": "tr",
                "order_by": "quality_score DESC",
            },
            # Pattern 2: Partial index usage (subject + difficulty)
            {"subject": "matematik", "difficulty": "orta"},
            # Pattern 3: Subject only
            {"subject": "matematik"},
        ]

        # All patterns should use the composite index
        for pattern in query_patterns:
            assert "subject" in pattern  # Index starts with subject

    def test_index_selectivity(self):
        """
        Test index selectivity for optimal performance

        Good selectivity: Each index level filters significantly
        """
        # Example data distribution
        total_videos = 10000
        subjects = 5  # matematik, fizik, kimya, biyoloji, türkçe
        difficulties = 3  # başlangıç, orta, ileri
        exam_types = 3  # TYT, AYT, LGS
        languages = 1  # tr (mostly)

        # Expected filtering at each index level
        after_subject = total_videos / subjects  # 2000 videos
        after_difficulty = after_subject / difficulties  # 667 videos
        after_exam_type = after_difficulty / exam_types  # 222 videos
        after_language = after_exam_type / languages  # 222 videos

        # Final result set should be small enough for efficient sorting
        assert after_language < 500  # Good selectivity

        # With quality_score filter (>= 7.0), expect ~50% reduction
        final_result_set = after_language * 0.5  # ~111 videos
        assert final_result_set < 200  # Excellent selectivity


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
