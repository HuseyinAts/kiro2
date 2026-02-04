"""
Mock data and fixtures for testing
"""
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock


class MockResponses:
    """Centralized mock responses for consistent testing"""

    # Database mock responses
    DB_USER = {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com",
        "role": "student",
        "created_at": datetime.now(),
        "is_active": True,
    }

    DB_EXAM = {
        "id": 1,
        "title": "Test Exam",
        "description": "Test exam description",
        "duration": 120,
        "created_at": datetime.now(),
        "is_active": True,
    }

    # API mock responses
    LLM_RESPONSE = {
        "generated_text": "This is a mock LLM response for testing.",
        "confidence": 0.95,
        "tokens_used": 50,
    }

    YOUTUBE_API_RESPONSE = {
        "items": [
            {
                "id": {"videoId": "test_video_id"},
                "snippet": {
                    "title": "Test Video Title",
                    "description": "Test video description",
                    "publishedAt": "2024-01-01T00:00:00Z",
                },
            }
        ],
        "pageInfo": {"totalResults": 1},
    }

    ELASTICSEARCH_RESPONSE = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_source": {
                        "title": "Test Document",
                        "content": "Test document content",
                        "created_at": "2024-01-01T00:00:00Z",
                    }
                }
            ],
        }
    }


class MockServices:
    """Mock service implementations"""

    @staticmethod
    def mock_database_session():
        """Create a mock database session"""
        session = AsyncMock()
        session.execute.return_value = AsyncMock()
        session.commit.return_value = None
        session.rollback.return_value = None
        session.close.return_value = None
        return session

    @staticmethod
    def mock_llm_service():
        """Create a mock LLM service"""
        service = AsyncMock()
        service.generate_text.return_value = MockResponses.LLM_RESPONSE
        service.chat_completion.return_value = MockResponses.LLM_RESPONSE
        return service

    @staticmethod
    def mock_youtube_service():
        """Create a mock YouTube service"""
        service = AsyncMock()
        service.search_videos.return_value = MockResponses.YOUTUBE_API_RESPONSE
        service.get_video_details.return_value = MockResponses.YOUTUBE_API_RESPONSE[
            "items"
        ][0]
        return service

    @staticmethod
    def mock_elasticsearch_client():
        """Create a mock Elasticsearch client"""
        client = AsyncMock()
        client.search.return_value = MockResponses.ELASTICSEARCH_RESPONSE
        client.index.return_value = {"_id": "test_id", "result": "created"}
        return client


class MockEnvironment:
    """Mock environment variables and settings"""

    TEST_ENV = {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "USE_MOCK_RESPONSES": "true",
        "HF_ENDPOINT_URL": "https://mock.endpoint.com",
        "HF_API_KEY": "mock_api_key",
        "YOUTUBE_API_KEY": "mock_youtube_key",
        "ELASTICSEARCH_URL": "http://localhost:9200",
        "REDIS_URL": "redis://localhost:6379/0",
        "LLM_TIMEOUT": "5",
        "MAX_RETRIES": "2",
        "TEST_MODE": "true",
    }

    @classmethod
    def apply(cls):
        """Apply mock environment variables"""
        import os

        for key, value in cls.TEST_ENV.items():
            os.environ[key] = value


def create_mock_settings():
    """Create mock settings object"""
    from unittest.mock import MagicMock

    settings = MagicMock()
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    settings.hf_endpoint_url = "https://mock.endpoint.com"
    settings.hf_api_key = "mock_api_key"
    settings.youtube_api_key = "mock_youtube_key"
    settings.elasticsearch_url = "http://localhost:9200"
    settings.redis_url = "redis://localhost:6379/0"
    settings.llm_timeout = 5
    settings.max_retries = 2
    settings.test_mode = True

    return settings
