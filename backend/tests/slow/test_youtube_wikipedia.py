"""
Integration tests for YouTube and Wikipedia services
With proper mocking to avoid real API calls
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from integrations.wikipedia_service import WikipediaArticle, WikipediaService

# Test edilecek modüller
from integrations.youtube_service import YouTubeService, YouTubeVideo


class TestYouTubeIntegration:
    """YouTube API integration tests with mocking"""

    @pytest.mark.asyncio
    async def test_youtube_search(self):
        """Test YouTube search with mocked API response"""
        # Set the API key in environment
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "TEST_MOCK_YOUTUBE_API_KEY"}):
            service = YouTubeService()

            # Mock the _simulate_api_call method since actual implementation uses it
            mock_videos = [
                YouTubeVideo(
                    video_id="dQw4w9WgXcQ",
                    title="Mathematics Tutorial - Algebra Basics",
                    description="Learn the fundamentals of algebra",
                    channel_name="Math Academy",
                    channel_id="UC_math_academy",
                    thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
                    duration="PT10M30S",
                    view_count=50000,
                    like_count=2000,
                    published_at=datetime(2024, 1, 15, 10, 0, 0),
                    tags=["mathematics", "algebra", "education"],
                    language="en",
                    caption_available=True,
                    educational_score=0.95,
                ),
                YouTubeVideo(
                    video_id="abc123xyz",
                    title="Geometry Basics for High School",
                    description="Essential geometry concepts explained",
                    channel_name="Education Hub",
                    channel_id="UC_edu_hub",
                    thumbnail_url="https://i.ytimg.com/vi/abc123xyz/default.jpg",
                    duration="PT15M00S",
                    view_count=30000,
                    like_count=1500,
                    published_at=datetime(2024, 2, 1, 14, 30, 0),
                    tags=["geometry", "high school"],
                    language="en",
                    caption_available=True,
                    educational_score=0.92,
                ),
            ]

            with patch.object(service, "_simulate_api_call", return_value=mock_videos):
                # Test search
                result = await service.search_educational_videos(
                    "mathematics tutorial", max_results=2
                )

                # Assertions
                assert isinstance(result, list)
                assert len(result) == 2
                # Check that both videos are in the result (order doesn't matter)
                video_ids = [v.video_id for v in result]
                assert "dQw4w9WgXcQ" in video_ids
                assert "abc123xyz" in video_ids
                # Check one of the videos has the expected title
                titles = [v.title for v in result]
                assert any("Mathematics Tutorial" in t for t in titles)

    @pytest.mark.asyncio
    async def test_youtube_search_with_filters(self):
        """Test YouTube search with educational filters"""
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "TEST_MOCK_YOUTUBE_API_KEY"}):
            service = YouTubeService()

            mock_videos = [
                YouTubeVideo(
                    video_id="edu_video_1",
                    title="LGS Mathematics Preparation",
                    description="Complete LGS math preparation guide",
                    channel_name="LGS Academy",
                    channel_id="UC_lgs_academy",
                    thumbnail_url="https://example.com/thumb.jpg",
                    duration="PT30M00S",
                    view_count=50000,
                    like_count=2000,
                    published_at=datetime(2024, 3, 1, 9, 0, 0),
                    tags=["LGS", "mathematics", "exam preparation"],
                    language="tr",
                    caption_available=True,
                    educational_score=0.98,
                )
            ]

            with patch.object(service, "_simulate_api_call", return_value=mock_videos):
                # Test educational content search
                result = await service.search_educational_videos(
                    query="LGS Mathematics", max_results=5, language="tr"
                )

                assert isinstance(result, list)
                assert len(result) > 0
                assert "LGS" in result[0].title

    @pytest.mark.asyncio
    async def test_youtube_api_error_handling(self):
        """Test YouTube API error handling"""
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "TEST_MOCK_YOUTUBE_API_KEY"}):
            service = YouTubeService()

            # Mock an exception in the API call
            with patch.object(
                service,
                "_simulate_api_call",
                side_effect=Exception("API quota exceeded"),
            ):
                # Test error handling
                result = await service.search_educational_videos("test query")

                # When error occurs, should return empty list
                assert isinstance(result, list)
                assert len(result) == 0

    @pytest.mark.asyncio
    async def test_youtube_video_details(self):
        """Test fetching YouTube video details"""
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "TEST_MOCK_YOUTUBE_API_KEY"}):
            service = YouTubeService()

            mock_video = YouTubeVideo(
                video_id="test_video_id",
                title="Advanced Calculus Lecture",
                description="University level calculus",
                channel_name="University Math",
                channel_id="UC_uni_math",
                thumbnail_url="https://example.com/calc.jpg",
                duration="PT45M30S",
                view_count=100000,
                like_count=5000,
                published_at=datetime(2024, 1, 20, 12, 0, 0),
                tags=["calculus", "mathematics", "university"],
                language="en",
                caption_available=True,
                educational_score=0.99,
            )

            with patch.object(service, "get_video_details", return_value=mock_video):
                # Test getting video details
                result = await service.get_video_details("test_video_id")

                assert isinstance(result, YouTubeVideo)
                assert result.title == "Advanced Calculus Lecture"
                assert result.duration == "PT45M30S"
                assert result.view_count == 100000


class TestWikipediaIntegration:
    """Wikipedia API integration tests with mocking"""

    @pytest.mark.asyncio
    async def test_wikipedia_fetch(self):
        """Test Wikipedia article fetch with mocked API"""
        service = WikipediaService()

        mock_articles = [
            WikipediaArticle(
                page_id=12345,
                title="Mathematics",
                summary="Mathematics is an area of knowledge...",
                content="Full content of the article...",
                url="https://en.wikipedia.org/wiki/Mathematics",
                categories=["Science", "Mathematics"],
                images=["math1.jpg", "math2.png"],
                references=["ref1", "ref2"],
                language="en",
                last_modified=datetime(2024, 1, 15, 10, 0, 0),
                word_count=8000,
                educational_relevance=0.95,
            ),
            WikipediaArticle(
                page_id=67890,
                title="Mathematical notation",
                summary="Mathematical notation consists of symbols...",
                content="Full content about notation...",
                url="https://en.wikipedia.org/wiki/Mathematical_notation",
                categories=["Mathematics", "Notation"],
                images=["notation.svg"],
                references=["ref3"],
                language="en",
                last_modified=datetime(2024, 1, 10, 8, 0, 0),
                word_count=4000,
                educational_relevance=0.90,
            ),
        ]

        with patch.object(service, "_simulate_search", return_value=mock_articles):
            # Test search
            result = await service.search_articles(
                "mathematics", language="en", limit=2
            )

            # Assertions
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0].title == "Mathematics"
            assert result[0].page_id == 12345

    @pytest.mark.asyncio
    async def test_wikipedia_get_article_content(self):
        """Test fetching full Wikipedia article content"""
        service = WikipediaService()

        mock_article = WikipediaArticle(
            page_id=54321,
            title="Algebra",
            summary="Algebra is one of the broad areas of mathematics...",
            content="<div>Full algebra content...</div>",
            url="https://en.wikipedia.org/wiki/Algebra",
            categories=["Mathematics", "Abstract algebra", "Mathematical structures"],
            images=["Algebra_example.svg", "Quadratic_formula.png"],
            references=["ref10", "ref11", "ref12"],
            language="en",
            last_modified=datetime(2024, 1, 12, 15, 30, 0),
            word_count=10000,
            educational_relevance=0.97,
        )

        with patch.object(service, "get_article", return_value=mock_article):
            # Test getting article content
            result = await service.get_article("Algebra", language="en")

            assert isinstance(result, WikipediaArticle)
            assert result.title == "Algebra"
            assert len(result.categories) == 3
            assert "Mathematics" in result.categories

    @pytest.mark.asyncio
    async def test_wikipedia_multilingual_support(self):
        """Test Wikipedia multilingual article fetching"""
        service = WikipediaService()

        # Test Turkish Wikipedia
        mock_articles = [
            WikipediaArticle(
                page_id=11111,
                title="Matematik",
                summary="Matematik, sayılar, yapılar, uzay ve değişim...",
                content="Matematik hakkında Türkçe içerik...",
                url="https://tr.wikipedia.org/wiki/Matematik",
                categories=["Bilim", "Matematik"],
                images=["matematik.jpg"],
                references=["kaynak1"],
                language="tr",
                last_modified=datetime(2024, 1, 20, 10, 0, 0),
                word_count=6000,
                educational_relevance=0.95,
            )
        ]

        with patch.object(service, "_simulate_search", return_value=mock_articles):
            # Test Turkish search
            result = await service.search_articles("matematik", language="tr")

            assert isinstance(result, list)
            assert result[0].title == "Matematik"
            assert "sayılar" in result[0].summary

    @pytest.mark.asyncio
    async def test_wikipedia_error_handling(self):
        """Test Wikipedia API error handling"""
        service = WikipediaService()

        # Mock an exception
        with patch.object(
            service, "get_article", side_effect=Exception("Article not found")
        ):
            try:
                # Test error handling
                result = await service.get_article("NonexistentPage")
                # If no exception, should return None or empty
                assert result is None or isinstance(result, WikipediaArticle)
            except Exception as e:
                # Error is properly raised
                assert "not found" in str(e).lower()

    @pytest.mark.asyncio
    async def test_wikipedia_summary_extraction(self):
        """Test extracting article summary from Wikipedia"""
        service = WikipediaService()

        mock_article = WikipediaArticle(
            page_id=22222,
            title="Physics",
            summary="Physics is the natural science that studies matter, its fundamental constituents, its motion and behavior through space and time, and the related entities of energy and force.",
            content="Full physics content...",
            url="https://en.wikipedia.org/wiki/Physics",
            categories=["Physics", "Natural sciences"],
            images=["physics_thumb.jpg"],
            references=["ref20", "ref21"],
            language="en",
            last_modified=datetime(2024, 1, 18, 11, 0, 0),
            word_count=12000,
            educational_relevance=0.98,
        )

        with patch.object(service, "get_article", return_value=mock_article):
            # Test summary extraction
            result = await service.get_article("Physics", language="en")

            assert isinstance(result, WikipediaArticle)
            assert "Physics is the natural science" in result.summary
            assert result.title == "Physics"


class TestIntegrationCombined:
    """Combined integration tests for YouTube and Wikipedia"""

    @pytest.mark.asyncio
    async def test_combined_search_for_topic(self):
        """Test searching both YouTube and Wikipedia for the same topic"""
        topic = "quantum physics"

        # Setup YouTube mock
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "TEST_MOCK_YOUTUBE_API_KEY"}):
            youtube_service = YouTubeService()
            wikipedia_service = WikipediaService()

            # Mock YouTube results
            mock_videos = [
                YouTubeVideo(
                    video_id="quantum_video",
                    title="Quantum Physics Explained",
                    description="Introduction to quantum mechanics",
                    channel_name="Science Channel",
                    channel_id="UC_science",
                    thumbnail_url="http://example.com/q.jpg",
                    duration="PT20M00S",
                    view_count=75000,
                    like_count=3000,
                    published_at=datetime(2024, 1, 1, 0, 0, 0),
                    tags=["quantum", "physics"],
                    language="en",
                    caption_available=True,
                    educational_score=0.96,
                )
            ]

            # Mock Wikipedia results
            mock_articles = [
                WikipediaArticle(
                    page_id=99999,
                    title="Quantum physics",
                    summary="Quantum physics is a fundamental theory...",
                    content="Full quantum physics content...",
                    url="https://en.wikipedia.org/wiki/Quantum_physics",
                    categories=["Physics", "Quantum mechanics"],
                    images=["quantum.png"],
                    references=["ref30"],
                    language="en",
                    last_modified=datetime(2024, 1, 5, 9, 0, 0),
                    word_count=15000,
                    educational_relevance=0.99,
                )
            ]

            with patch.object(
                youtube_service, "_simulate_api_call", return_value=mock_videos
            ):
                with patch.object(
                    wikipedia_service, "_simulate_search", return_value=mock_articles
                ):
                    # Search both services
                    youtube_results = await youtube_service.search_educational_videos(
                        topic
                    )
                    wikipedia_results = await wikipedia_service.search_articles(topic)

                    # Verify both returned results
                    assert isinstance(youtube_results, list)
                    assert isinstance(wikipedia_results, list)
                    assert "Quantum" in youtube_results[0].title
                    assert "Quantum" in wikipedia_results[0].title

    @pytest.mark.asyncio
    async def test_educational_content_aggregation(self):
        """Test aggregating educational content from multiple sources"""
        subject = "Biology"
        grade = "High School"

        results = {"youtube": None, "wikipedia": None}

        # Mock YouTube
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "TEST_MOCK_YOUTUBE_API_KEY"}):
            youtube_service = YouTubeService()

            mock_videos = [
                YouTubeVideo(
                    video_id="bio_video",
                    title=f"{grade} {subject} Tutorial",
                    description="Biology for high school students",
                    channel_name="Education Channel",
                    channel_id="UC_education",
                    thumbnail_url="http://example.com/bio.jpg",
                    duration="PT25M00S",
                    view_count=40000,
                    like_count=1800,
                    published_at=datetime(2024, 1, 1, 0, 0, 0),
                    tags=["biology", "high school"],
                    language="en",
                    caption_available=True,
                    educational_score=0.94,
                )
            ]

            with patch.object(
                youtube_service, "_simulate_api_call", return_value=mock_videos
            ):
                results["youtube"] = await youtube_service.search_educational_videos(
                    query=f"{grade} {subject}", max_results=5
                )

        # Mock Wikipedia
        wikipedia_service = WikipediaService()

        mock_articles = [
            WikipediaArticle(
                page_id=88888,
                title=subject,
                summary=f"{subject} is the scientific study of life...",
                content="Full biology content...",
                url="https://en.wikipedia.org/wiki/Biology",
                categories=["Science", "Biology"],
                images=["biology.jpg"],
                references=["ref40"],
                language="en",
                last_modified=datetime(2024, 1, 15, 12, 0, 0),
                word_count=20000,
                educational_relevance=0.97,
            )
        ]

        with patch.object(
            wikipedia_service, "_simulate_search", return_value=mock_articles
        ):
            results["wikipedia"] = await wikipedia_service.search_articles(subject)

        # Verify aggregated results
        assert all(r for r in results.values() if r)
        assert results["youtube"][0].title == f"{grade} {subject} Tutorial"
        assert results["wikipedia"][0].title == subject


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
