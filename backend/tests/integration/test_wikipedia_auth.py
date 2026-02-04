"""
Comprehensive tests for Wikipedia service with various authentication methods
Tests Bearer Token, Query Parameter, Header, and Cookie authentication
"""

from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from integrations.wikipedia_service_with_auth import (
    AuthMethod,
    WikipediaServiceWithAuth,
)


class TestWikipediaAuthMethods:
    """Test all Wikipedia API authentication methods"""

    @pytest.mark.asyncio
    async def test_no_authentication(self):
        """Test Wikipedia service without authentication (standard public API)"""
        service = WikipediaServiceWithAuth(auth_method=AuthMethod.NONE)

        with patch("aiohttp.ClientSession") as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "query": {
                        "search": [
                            {
                                "pageid": 12345,
                                "title": "Mathematics",
                                "snippet": "Mathematics is the study of...",
                                "wordcount": 5000,
                            }
                        ]
                    }
                }
            )

            mock_session = AsyncMock()
            # Create async context manager for get method
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test search without auth
            results = await service.search_articles("mathematics")

            # Verify no auth headers/params were sent
            call_args = mock_session.get.call_args
            headers = call_args.kwargs.get("headers", {})
            params = call_args.kwargs.get("params", {})
            cookies = call_args.kwargs.get("cookies", {})

            assert "Authorization" not in headers
            assert "X-API-Key" not in headers
            assert "api_key" not in params
            assert "X-API-KEY" not in cookies
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_bearer_token_authentication(self):
        """Test Wikipedia service with Bearer token (JWT) authentication"""
        api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        service = WikipediaServiceWithAuth(
            api_key=api_key, auth_method=AuthMethod.BEARER_TOKEN
        )

        with patch("aiohttp.ClientSession") as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "query": {
                        "search": [
                            {
                                "pageid": 67890,
                                "title": "Physics",
                                "snippet": "Physics is the natural science...",
                                "wordcount": 8000,
                            }
                        ]
                    }
                }
            )

            mock_session = AsyncMock()
            # Create async context manager for get method
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test search with Bearer token
            results = await service.search_articles("physics")

            # Verify Bearer token was sent in Authorization header
            call_args = mock_session.get.call_args
            headers = call_args.kwargs.get("headers", {})

            assert "Authorization" in headers
            assert headers["Authorization"] == f"Bearer {api_key}"
            assert len(results) > 0
            assert results[0].title == "Physics"

    @pytest.mark.asyncio
    async def test_query_parameter_authentication(self):
        """Test Wikipedia service with API key as query parameter"""
        api_key = "abcdef12345"
        service = WikipediaServiceWithAuth(
            api_key=api_key, auth_method=AuthMethod.QUERY_PARAM
        )

        with patch("aiohttp.ClientSession") as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "query": {
                        "search": [
                            {
                                "pageid": 11111,
                                "title": "Chemistry",
                                "snippet": "Chemistry is the scientific study...",
                                "wordcount": 6000,
                            }
                        ]
                    }
                }
            )

            mock_session = AsyncMock()
            # Create async context manager for get method
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test search with query parameter auth
            results = await service.search_articles("chemistry")

            # Verify API key was sent as query parameter
            call_args = mock_session.get.call_args
            params = call_args.kwargs.get("params", {})

            assert "api_key" in params
            assert params["api_key"] == api_key
            assert len(results) > 0
            assert results[0].title == "Chemistry"

    @pytest.mark.asyncio
    async def test_header_authentication(self):
        """Test Wikipedia service with API key as custom header"""
        api_key = "xyz789secret"
        service = WikipediaServiceWithAuth(
            api_key=api_key, auth_method=AuthMethod.HEADER
        )

        with patch("aiohttp.ClientSession") as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "query": {
                        "search": [
                            {
                                "pageid": 22222,
                                "title": "Biology",
                                "snippet": "Biology is the scientific study of life...",
                                "wordcount": 7000,
                            }
                        ]
                    }
                }
            )

            mock_session = AsyncMock()
            # Create async context manager for get method
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test search with header auth
            results = await service.search_articles("biology")

            # Verify API key was sent as X-API-Key header
            call_args = mock_session.get.call_args
            headers = call_args.kwargs.get("headers", {})

            assert "X-API-Key" in headers
            assert headers["X-API-Key"] == api_key
            assert len(results) > 0
            assert results[0].title == "Biology"

    @pytest.mark.asyncio
    async def test_cookie_authentication(self):
        """Test Wikipedia service with API key as cookie"""
        api_key = "cookie_secret_123"
        service = WikipediaServiceWithAuth(
            api_key=api_key, auth_method=AuthMethod.COOKIE
        )

        with patch("aiohttp.ClientSession") as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "query": {
                        "search": [
                            {
                                "pageid": 33333,
                                "title": "History",
                                "snippet": "History is the study of past events...",
                                "wordcount": 9000,
                            }
                        ]
                    }
                }
            )

            mock_session = AsyncMock()
            # Create async context manager for get method
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test search with cookie auth
            results = await service.search_articles("history")

            # Verify API key was sent as cookie
            call_args = mock_session.get.call_args
            cookies = call_args.kwargs.get("cookies", {})

            assert "X-API-KEY" in cookies
            assert cookies["X-API-KEY"] == api_key
            assert len(results) > 0
            assert results[0].title == "History"

    @pytest.mark.asyncio
    async def test_authentication_failure_401(self):
        """Test handling of 401 Unauthorized response"""
        service = WikipediaServiceWithAuth(
            api_key="invalid_key", auth_method=AuthMethod.BEARER_TOKEN
        )

        with patch("aiohttp.ClientSession") as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 401  # Unauthorized
            mock_response.json = AsyncMock(return_value={"error": "Invalid API key"})

            mock_session = AsyncMock()
            # Create async context manager for get method
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test search with invalid auth
            results = await service.search_articles("test")

            # Should return empty list on auth failure
            assert results == []

    @pytest.mark.asyncio
    async def test_authentication_failure_403(self):
        """Test handling of 403 Forbidden response"""
        service = WikipediaServiceWithAuth(
            api_key="valid_but_insufficient", auth_method=AuthMethod.HEADER
        )

        with patch("aiohttp.ClientSession") as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 403  # Forbidden
            mock_response.json = AsyncMock(
                return_value={"error": "Insufficient permissions"}
            )

            mock_session = AsyncMock()
            # Create async context manager for get method
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test search with insufficient permissions
            results = await service.search_articles("test")

            # Should return empty list on authorization failure
            assert results == []

    @pytest.mark.asyncio
    async def test_custom_proxy_url_with_auth(self):
        """Test using custom proxy URL that requires authentication"""
        api_key = "proxy_api_key_789"
        custom_url = "https://wiki-proxy.example.com"

        service = WikipediaServiceWithAuth(
            api_key=api_key,
            auth_method=AuthMethod.BEARER_TOKEN,
            custom_base_url=custom_url,
        )

        # Verify custom URL is set
        assert service.api_endpoint == f"{custom_url}/{{lang}}/api"
        assert service.base_urls["en"] == f"{custom_url}/en"
        assert service.base_urls["tr"] == f"{custom_url}/tr"

        with patch("aiohttp.ClientSession") as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "query": {
                        "search": [
                            {
                                "pageid": 44444,
                                "title": "Geography",
                                "snippet": "Geography is the study of places...",
                                "wordcount": 5500,
                            }
                        ]
                    }
                }
            )

            mock_session = AsyncMock()
            # Create async context manager for get method
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test search through proxy
            results = await service.search_articles("geography")

            # Verify request was made to proxy URL with auth
            call_args = mock_session.get.call_args
            url = call_args.args[0]
            headers = call_args.kwargs.get("headers", {})

            assert custom_url in url
            assert headers["Authorization"] == f"Bearer {api_key}"
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_environment_variable_api_key(self):
        """Test loading API key from environment variable"""
        env_api_key = "env_secret_key_456"

        with patch.dict("os.environ", {"WIKIPEDIA_API_KEY": env_api_key}):
            service = WikipediaServiceWithAuth(auth_method=AuthMethod.QUERY_PARAM)

            # Verify API key was loaded from environment
            assert service.api_key == env_api_key

            with patch("aiohttp.ClientSession") as MockSession:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(
                    return_value={
                        "query": {
                            "search": [
                                {
                                    "pageid": 55555,
                                    "title": "Literature",
                                    "snippet": "Literature is written work...",
                                    "wordcount": 4500,
                                }
                            ]
                        }
                    }
                )

                mock_session = AsyncMock()
                # Create async context manager for get method
                mock_get_cm = AsyncMock()
                mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
                mock_get_cm.__aexit__ = AsyncMock(return_value=None)
                mock_session.get = Mock(return_value=mock_get_cm)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                MockSession.return_value = mock_session

                # Test search with env API key
                results = await service.search_articles("literature")

                # Verify env API key was used
                call_args = mock_session.get.call_args
                params = call_args.kwargs.get("params", {})

                assert params["api_key"] == env_api_key
                assert len(results) > 0

    @pytest.mark.asyncio
    async def test_get_article_with_authentication(self):
        """Test fetching full article with authentication"""
        api_key = "article_key_999"
        service = WikipediaServiceWithAuth(
            api_key=api_key, auth_method=AuthMethod.HEADER
        )

        with patch("aiohttp.ClientSession") as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "parse": {
                        "pageid": 66666,
                        "title": "Quantum Physics",
                        "text": {
                            "*": "<p>Quantum physics is a fundamental theory...</p>"
                        },
                        "categories": [{"*": "Physics"}, {"*": "Quantum mechanics"}],
                        "images": ["quantum.png", "schrodinger.jpg"],
                        "externallinks": ["https://example.com/quantum"],
                    }
                }
            )

            mock_session = AsyncMock()
            # Create async context manager for get method
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test getting article with auth
            article = await service.get_article("Quantum Physics")

            # Verify auth was sent
            call_args = mock_session.get.call_args
            headers = call_args.kwargs.get("headers", {})

            assert headers["X-API-Key"] == api_key
            assert article is not None
            assert article.title == "Quantum Physics"
            assert len(article.categories) == 2
            assert "Physics" in article.categories[0]

    @pytest.mark.asyncio
    async def test_multiple_auth_methods_switching(self):
        """Test switching between different authentication methods"""
        api_key = "multi_method_key"

        # Test with Bearer token
        service_bearer = WikipediaServiceWithAuth(
            api_key=api_key, auth_method=AuthMethod.BEARER_TOKEN
        )
        headers_bearer = service_bearer._prepare_auth_headers()
        assert headers_bearer["Authorization"] == f"Bearer {api_key}"

        # Test with Header
        service_header = WikipediaServiceWithAuth(
            api_key=api_key, auth_method=AuthMethod.HEADER
        )
        headers_header = service_header._prepare_auth_headers()
        assert headers_header["X-API-Key"] == api_key

        # Test with Query param
        service_query = WikipediaServiceWithAuth(
            api_key=api_key, auth_method=AuthMethod.QUERY_PARAM
        )
        params = service_query._prepare_auth_params({"test": "value"})
        assert params["api_key"] == api_key

        # Test with Cookie
        service_cookie = WikipediaServiceWithAuth(
            api_key=api_key, auth_method=AuthMethod.COOKIE
        )
        cookies = service_cookie._prepare_auth_cookies()
        assert cookies["X-API-KEY"] == api_key

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors during API calls"""
        service = WikipediaServiceWithAuth(
            api_key="test_key", auth_method=AuthMethod.BEARER_TOKEN
        )

        with patch("aiohttp.ClientSession") as MockSession:
            # Simulate network error
            mock_session = AsyncMock()
            # Create async context manager that raises error
            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__ = AsyncMock(
                side_effect=aiohttp.ClientError("Network timeout")
            )
            mock_get_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_get_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = mock_session

            # Test search with network error
            results = await service.search_articles("test")

            # Should return empty list on network error
            assert results == []

    @pytest.mark.asyncio
    async def test_educational_relevance_calculation(self):
        """Test educational relevance scoring with auth"""
        service = WikipediaServiceWithAuth(auth_method=AuthMethod.NONE)

        # Test educational relevance calculation
        educational_result = {"title": "Mathematics Formula Theory", "wordcount": 6000}
        score = service._calculate_educational_relevance(educational_result)
        assert score > 0.7  # Should have high score

        # Test non-educational content
        non_educational_result = {"title": "Celebrity Gossip", "wordcount": 500}
        score = service._calculate_educational_relevance(non_educational_result)
        assert score < 0.6  # Should have low score


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
