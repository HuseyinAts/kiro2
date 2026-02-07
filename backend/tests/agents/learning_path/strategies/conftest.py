"""Fixtures for strategy tests.

This module provides shared fixtures for testing learning path strategies.
All fixtures return properly structured mock API responses.
"""
import pytest
from typing import Dict, Any


@pytest.fixture
def mock_youtube_response() -> Dict[str, Any]:
    """Mock YouTube API video details response.

    Returns:
        Dict containing snippet, contentDetails, and statistics.
    """
    return {
        "id": "video123",
        "snippet": {
            "title": "Türev Konu Anlatımı",
            "description": "Temel türev kavramları ve uygulamaları",
            "channelTitle": "Matematik Kanalı",
            "channelId": "channel123",
            "thumbnails": {
                "high": {"url": "https://i.ytimg.com/vi/video123/hqdefault.jpg"},
                "medium": {"url": "https://i.ytimg.com/vi/video123/mqdefault.jpg"}
            },
            "publishedAt": "2024-01-15T10:00:00Z"
        },
        "contentDetails": {
            "duration": "PT15M30S",  # ISO 8601 duration: 15 minutes 30 seconds
            "definition": "hd"
        },
        "statistics": {
            "viewCount": "12345",
            "likeCount": "987"
        }
    }


@pytest.fixture
def mock_youtube_search_response() -> Dict[str, Any]:
    """Mock YouTube API search response (list of video IDs).

    Returns:
        Dict with items array containing video IDs.
    """
    return {
        "items": [
            {
                "id": {"videoId": "video123"},
                "snippet": {
                    "title": "Türev Konu Anlatımı",
                    "description": "Temel türev kavramları"
                }
            },
            {
                "id": {"videoId": "video456"},
                "snippet": {
                    "title": "İntegral Hesaplama",
                    "description": "İntegral teknikleri"
                }
            }
        ]
    }


@pytest.fixture
def mock_khan_response() -> Dict[str, Any]:
    """Mock Khan Academy API response.

    Returns:
        Dict containing Khan Academy content metadata.
    """
    return {
        "kind": "Video",
        "slug": "algebra-basics",
        "id": "algebra-basics",
        "title": "Algebra Basics",
        "translated_title": "Cebir Temelleri",
        "description": "Introduction to algebraic concepts",
        "translated_description": "Cebirsel kavramlara giriş",
        "duration": 900,  # seconds
        "video_seconds": 900,
        "mastery_model": {"level": 2},
        "domain_slug": "math",
        "subject_slug": "algebra",
        "topic_slug": "algebra-foundations",
        "ka_url": "https://tr.khanacademy.org/video/algebra-basics",
        "image_url": "https://cdn.kastatic.org/image.jpg",
        "is_turkish": True,
        "prerequisites": ["basic-math"]
    }


@pytest.fixture
def mock_oer_response() -> Dict[str, Any]:
    """Mock OER Commons API response.

    Returns:
        Dict containing OER Commons resource metadata.
    """
    return {
        "id": "oer-123",
        "title": "Introduction to Calculus",
        "abstract": "A comprehensive guide to calculus concepts.",
        "description": "Detailed calculus tutorial covering derivatives and integrals.",
        "url": "https://oercommons.org/courses/calculus-intro",
        "link": "https://oercommons.org/courses/calculus-intro",
        "media_type": "document",
        "grade_level": ["9", "10", "11"],
        "license": "CC-BY",
        "rating": 4.5,
        "avg_rating": 4.5,
        "author": "Dr. Math Teacher",
        "creator": "Dr. Math Teacher",
        "subjects": ["Mathematics", "Calculus"],
        "subject_areas": ["Mathematics"],
        "keywords": ["calculus", "derivatives", "integrals"],
        "tags": ["math", "advanced"],
        "language": "en",
        "word_count": 5000
    }


@pytest.fixture
def mock_rag_response() -> Dict[str, Any]:
    """Mock RAG/ChromaDB response.

    Returns:
        Dict containing RAG search result metadata.
    """
    return {
        "id": "question_123",
        "title": "Trigonometri Soru Bankası",
        "content": "Sinüs, kosinüs ve tanjant ile ilgili çözümlü sorular...",
        "description": "Trigonometri soruları ve çözümleri",
        "url": "/questions/question_123",
        "difficulty": 0.5,  # IRT difficulty
        "topics": ["trigonometri", "matematik"],
        "resource_type": "question",
        "language": "tr",
        "duration": 10,
        "rating": 4.2,
        "metadata": {
            "subject": "matematik",
            "question_count": 25
        }
    }


@pytest.fixture
def mock_youtube_turkish_response() -> Dict[str, Any]:
    """Mock YouTube response with Turkish characters.

    Returns:
        Dict with Turkish content for character encoding tests.
    """
    return {
        "id": "vid-turkish",
        "snippet": {
            "title": "İntegral Hesaplama - Üst Düzey Çözümler",
            "description": "Türkçe karakterler: İ ı Ğ ğ Ü ü Ş ş Ö ö Ç ç",
            "channelTitle": "Öğretmen Kanalı",
            "channelId": "channel-tr",
            "thumbnails": {
                "high": {"url": "https://example.com/thumb.jpg"}
            },
            "publishedAt": "2024-01-20T12:00:00Z"
        },
        "contentDetails": {
            "duration": "PT10M",
            "definition": "sd"
        },
        "statistics": {
            "viewCount": "5000",
            "likeCount": "450"
        }
    }


@pytest.fixture
def mock_khan_turkish_response() -> Dict[str, Any]:
    """Mock Khan Academy Turkish content response.

    Returns:
        Dict with Turkish Khan Academy content.
    """
    return {
        "kind": "Exercise",
        "slug": "turev-alisirma",
        "id": "turev-alisirma",
        "title": "Derivative Exercises",
        "translated_title": "Türev Alıştırmaları",
        "description": "Practice derivative problems",
        "translated_description": "Türev problemleri pratiği",
        "duration": 1800,
        "mastery_model": {"level": 3},
        "domain_slug": "matematik",
        "subject_slug": "turev",
        "topic_slug": "temel-turev",
        "ka_url": "https://tr.khanacademy.org/exercise/turev-alisirma",
        "image_url": "https://cdn.kastatic.org/image-tr.jpg",
        "is_turkish": True,
        "prerequisites": ["fonksiyonlar", "limit"]
    }


@pytest.fixture
def mock_oer_multilevel_response() -> Dict[str, Any]:
    """Mock OER response with multiple grade levels.

    Returns:
        Dict with various grade levels for difficulty estimation tests.
    """
    return {
        "id": "oer-multilevel",
        "title": "Advanced Physics Concepts",
        "abstract": "Complex physics topics for high school students",
        "url": "https://oercommons.org/courses/physics-advanced",
        "media_type": "video",
        "grade_level": ["11", "12", "Higher Education"],
        "license": "CC-BY-SA",
        "rating": 4.8,
        "subjects": ["Physics", "Science"],
        "keywords": ["physics", "mechanics", "waves"],
        "language": "en",
        "duration": 1800,  # 30 minutes in seconds
        "author": "Prof. Physics"
    }
