"""
Mock decorators for consistent API mocking
"""
import functools
from unittest.mock import AsyncMock, MagicMock, patch
from .mock_data import MockServices, MockResponses, MockEnvironment


def mock_database(func):
    """Decorator to mock database operations"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with patch("core.database.get_async_session") as mock_get_session:
            mock_get_session.return_value = MockServices.mock_database_session()
            return await func(*args, **kwargs)

    return wrapper


def mock_llm_calls(func):
    """Decorator to mock LLM API calls"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        patches = [
            patch(
                "httpx.AsyncClient.post",
                new_callable=AsyncMock,
                return_value=AsyncMock(
                    json=AsyncMock(return_value=MockResponses.LLM_RESPONSE),
                    status_code=200,
                ),
            ),
            patch(
                "core.llm_service.LLMService.generate_text",
                new_callable=AsyncMock,
                return_value=MockResponses.LLM_RESPONSE,
            ),
            patch(
                "agents.base_agent.BaseAgent.call_llm",
                new_callable=AsyncMock,
                return_value=MockResponses.LLM_RESPONSE,
            ),
        ]

        for p in patches:
            p.start()

        try:
            return await func(*args, **kwargs)
        finally:
            for p in patches:
                p.stop()

    return wrapper


def mock_youtube_api(func):
    """Decorator to mock YouTube API calls"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with patch(
            "services.youtube_service.YouTubeService.search_videos"
        ) as mock_search:
            mock_search.return_value = MockResponses.YOUTUBE_API_RESPONSE
            return await func(*args, **kwargs)

    return wrapper


def mock_elasticsearch(func):
    """Decorator to mock Elasticsearch calls"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with patch("elasticsearch.AsyncElasticsearch") as mock_es:
            mock_es.return_value = MockServices.mock_elasticsearch_client()
            return await func(*args, **kwargs)

    return wrapper


def mock_all_external_apis(func):
    """Decorator to mock all external API calls"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Apply mock environment
        MockEnvironment.apply()

        patches = [
            # HTTP clients
            patch(
                "httpx.AsyncClient.post",
                new_callable=AsyncMock,
                return_value=AsyncMock(
                    json=AsyncMock(return_value=MockResponses.LLM_RESPONSE),
                    status_code=200,
                ),
            ),
            patch(
                "httpx.AsyncClient.get",
                new_callable=AsyncMock,
                return_value=AsyncMock(
                    json=AsyncMock(return_value=MockResponses.YOUTUBE_API_RESPONSE),
                    status_code=200,
                ),
            ),
            # Database
            patch(
                "core.database.get_async_session",
                return_value=MockServices.mock_database_session(),
            ),
            # Services (with error handling for non-existent modules)
            # patch('services.llm_service.LLMService', return_value=MockServices.mock_llm_service()),
            # patch('services.youtube_service.YouTubeService', return_value=MockServices.mock_youtube_service()),
            # Elasticsearch
            patch(
                "elasticsearch.AsyncElasticsearch",
                return_value=MockServices.mock_elasticsearch_client(),
            ),
            # Redis
            patch("redis.asyncio.Redis", return_value=AsyncMock()),
        ]

        for p in patches:
            p.start()

        try:
            return await func(*args, **kwargs)
        finally:
            for p in patches:
                p.stop()

    return wrapper


def mock_settings(func):
    """Decorator to mock settings/configuration"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from .mock_data import create_mock_settings

        with patch("core.config.settings", create_mock_settings()):
            with patch("core.config.get_settings", return_value=create_mock_settings()):
                return func(*args, **kwargs)

    return wrapper
