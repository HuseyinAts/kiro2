"""
Phase 2: API Optimizer Comprehensive Tests
Target: 0% → 40%+ coverage for core/api_optimizer.py (642 lines)
Focus: Rate limiting, compression, caching, performance optimization
"""

import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAPIOptimizerConfigs:
    """Test API Optimizer configuration classes"""

    def test_rate_limit_config_creation(self):
        """Test RateLimitConfig creation with defaults"""
        try:
            from core.api_optimizer import RateLimitConfig

            config = RateLimitConfig()

            assert config.requests_per_minute == 100
            assert config.requests_per_hour == 1000
            assert config.requests_per_day == 10000
            assert config.burst_limit == 20
            assert config.enabled is True

        except ImportError:
            pytest.skip("RateLimitConfig not available")

    def test_rate_limit_config_custom_values(self):
        """Test RateLimitConfig with custom values"""
        try:
            from core.api_optimizer import RateLimitConfig

            config = RateLimitConfig(
                requests_per_minute=200,
                requests_per_hour=2000,
                requests_per_day=20000,
                burst_limit=50,
                enabled=False,
            )

            assert config.requests_per_minute == 200
            assert config.requests_per_hour == 2000
            assert config.requests_per_day == 20000
            assert config.burst_limit == 50
            assert config.enabled is False

        except ImportError:
            pytest.skip("RateLimitConfig not available")

    def test_compression_config_creation(self):
        """Test CompressionConfig creation with defaults"""
        try:
            from core.api_optimizer import CompressionConfig

            config = CompressionConfig()

            assert config.enabled is True
            assert config.min_size == 1024
            assert config.compression_level == 6
            assert "application/json" in config.mime_types
            assert "text/html" in config.mime_types
            assert "text/css" in config.mime_types

        except ImportError:
            pytest.skip("CompressionConfig not available")

    def test_compression_config_custom_values(self):
        """Test CompressionConfig with custom values"""
        try:
            from core.api_optimizer import CompressionConfig

            config = CompressionConfig(
                enabled=False,
                min_size=512,
                compression_level=9,
                mime_types=["application/json", "text/plain"],
            )

            assert config.enabled is False
            assert config.min_size == 512
            assert config.compression_level == 9
            assert len(config.mime_types) == 2
            assert "application/json" in config.mime_types
            assert "text/plain" in config.mime_types

        except ImportError:
            pytest.skip("CompressionConfig not available")

    def test_cache_config_creation(self):
        """Test CacheConfig creation with defaults"""
        try:
            from core.api_optimizer import CacheConfig

            config = CacheConfig()

            assert config.enabled is True
            assert config.default_ttl == 300
            assert config.redis_url == "redis://localhost:6379/1"
            assert config.cache_headers is True

        except ImportError:
            pytest.skip("CacheConfig not available")

    def test_cache_config_custom_values(self):
        """Test CacheConfig with custom values"""
        try:
            from core.api_optimizer import CacheConfig

            config = CacheConfig(
                enabled=False,
                default_ttl=600,
                redis_url="redis://test-server:6379/2",
                cache_headers=False,
            )

            assert config.enabled is False
            assert config.default_ttl == 600
            assert config.redis_url == "redis://test-server:6379/2"
            assert config.cache_headers is False

        except ImportError:
            pytest.skip("CacheConfig not available")


class TestAPIOptimizerCore:
    """Test APIOptimizer main class"""

    def test_api_optimizer_creation(self):
        """Test APIOptimizer instantiation"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                RateLimitConfig,
            )

            rate_config = RateLimitConfig()
            compression_config = CompressionConfig()
            cache_config = CacheConfig()

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            assert optimizer.rate_limit_config == rate_config
            assert optimizer.compression_config == compression_config
            assert optimizer.cache_config == cache_config
            assert optimizer.redis_client is None
            assert isinstance(optimizer.stats, dict)

        except ImportError:
            pytest.skip("APIOptimizer not available")

    def test_api_optimizer_stats_initialization(self):
        """Test APIOptimizer stats are properly initialized"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                RateLimitConfig,
            )

            rate_config = RateLimitConfig()
            compression_config = CompressionConfig()
            cache_config = CacheConfig()

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            expected_stats = [
                "total_requests",
                "rate_limited",
                "compressed_responses",
                "cache_hits",
                "cache_misses",
                "average_response_time",
            ]

            for stat in expected_stats:
                assert stat in optimizer.stats
                assert isinstance(optimizer.stats[stat], (int, float))

            assert optimizer.stats["total_requests"] == 0
            assert optimizer.stats["rate_limited"] == 0
            assert optimizer.stats["average_response_time"] == 0.0

        except ImportError:
            pytest.skip("APIOptimizer not available")

    @pytest.mark.asyncio
    async def test_api_optimizer_initialization_no_redis(self):
        """Test APIOptimizer initialization without Redis"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                RateLimitConfig,
            )

            rate_config = RateLimitConfig()
            compression_config = CompressionConfig()
            cache_config = CacheConfig(enabled=False)

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            # Should not fail even without Redis
            await optimizer.initialize()
            assert optimizer.redis_client is None

        except ImportError:
            pytest.skip("APIOptimizer not available")

    @pytest.mark.asyncio
    async def test_api_optimizer_close(self):
        """Test APIOptimizer close method"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                RateLimitConfig,
            )

            rate_config = RateLimitConfig()
            compression_config = CompressionConfig()
            cache_config = CacheConfig(enabled=False)

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            # Mock Redis client
            mock_redis = AsyncMock()
            optimizer.redis_client = mock_redis

            await optimizer.close()
            mock_redis.close.assert_called_once()

        except ImportError:
            pytest.skip("APIOptimizer not available")


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware functionality"""

    def test_rate_limit_middleware_creation(self):
        """Test RateLimitMiddleware instantiation"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                RateLimitConfig,
                RateLimitMiddleware,
            )

            rate_config = RateLimitConfig()
            compression_config = CompressionConfig()
            cache_config = CacheConfig()

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            app = Mock()
            middleware = RateLimitMiddleware(app, optimizer)

            assert middleware.optimizer == optimizer
            assert middleware.config == rate_config
            assert middleware.app == app

        except ImportError:
            pytest.skip("RateLimitMiddleware not available")

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_disabled(self):
        """Test RateLimitMiddleware when disabled"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                RateLimitConfig,
                RateLimitMiddleware,
            )

            rate_config = RateLimitConfig(enabled=False)
            compression_config = CompressionConfig()
            cache_config = CacheConfig()

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            app = Mock()
            middleware = RateLimitMiddleware(app, optimizer)

            # Mock request and call_next
            mock_request = Mock()
            mock_response = Mock()
            mock_call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, mock_call_next)

            assert result == mock_response
            mock_call_next.assert_called_once_with(mock_request)

        except ImportError:
            pytest.skip("RateLimitMiddleware not available")

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_client_key_generation(self):
        """Test rate limit client key generation"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                RateLimitConfig,
                RateLimitMiddleware,
            )

            rate_config = RateLimitConfig(enabled=True)
            compression_config = CompressionConfig()
            cache_config = CacheConfig()

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            app = Mock()
            middleware = RateLimitMiddleware(app, optimizer)

            # Mock request with client info
            mock_request = Mock()
            mock_request.client.host = "192.168.1.100"
            mock_request.headers = {"X-User-ID": "user123"}

            # Mock _is_rate_limited to return False
            middleware._is_rate_limited = AsyncMock(return_value=False)
            middleware._update_rate_limit = AsyncMock()

            mock_response = Mock()
            mock_call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, mock_call_next)

            # Check that client key was generated correctly
            expected_key = "rate_limit:192.168.1.100:user123"
            middleware._is_rate_limited.assert_called_once_with(expected_key)
            middleware._update_rate_limit.assert_called_once_with(expected_key)

        except ImportError:
            pytest.skip("RateLimitMiddleware not available")


class TestCompressionMiddleware:
    """Test CompressionMiddleware functionality"""

    def test_compression_middleware_creation(self):
        """Test CompressionMiddleware instantiation"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                CompressionMiddleware,
                RateLimitConfig,
            )

            rate_config = RateLimitConfig()
            compression_config = CompressionConfig()
            cache_config = CacheConfig()

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            app = Mock()
            middleware = CompressionMiddleware(app, optimizer)

            assert middleware.optimizer == optimizer
            assert middleware.config == compression_config
            assert middleware.app == app

        except ImportError:
            pytest.skip("CompressionMiddleware not available")

    @pytest.mark.asyncio
    async def test_compression_middleware_disabled(self):
        """Test CompressionMiddleware when disabled"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                CompressionMiddleware,
                RateLimitConfig,
            )

            rate_config = RateLimitConfig()
            compression_config = CompressionConfig(enabled=False)
            cache_config = CacheConfig()

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            app = Mock()
            middleware = CompressionMiddleware(app, optimizer)

            mock_request = Mock()
            mock_response = Mock()
            mock_call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, mock_call_next)

            assert result == mock_response
            mock_call_next.assert_called_once_with(mock_request)

        except ImportError:
            pytest.skip("CompressionMiddleware not available")

    @pytest.mark.asyncio
    async def test_compression_middleware_no_gzip_support(self):
        """Test CompressionMiddleware when client doesn't support gzip"""
        try:
            from core.api_optimizer import (
                APIOptimizer,
                CacheConfig,
                CompressionConfig,
                CompressionMiddleware,
                RateLimitConfig,
            )

            rate_config = RateLimitConfig()
            compression_config = CompressionConfig(enabled=True)
            cache_config = CacheConfig()

            optimizer = APIOptimizer(
                rate_limit_config=rate_config,
                compression_config=compression_config,
                cache_config=cache_config,
            )

            app = Mock()
            middleware = CompressionMiddleware(app, optimizer)

            # Mock request without gzip support
            mock_request = Mock()
            mock_request.headers = {"Accept-Encoding": "deflate, br"}

            mock_response = Mock()
            mock_call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, mock_call_next)

            assert result == mock_response

        except ImportError:
            pytest.skip("CompressionMiddleware not available")


class TestPaginationUtilities:
    """Test pagination utility classes"""

    def test_pagination_params_creation(self):
        """Test PaginationParams creation with defaults"""
        try:
            from core.api_optimizer import PaginationParams

            params = PaginationParams()

            assert params.page == 1
            assert params.size == 20
            assert params.max_size == 100
            assert params.offset == 0

        except ImportError:
            pytest.skip("PaginationParams not available")

    def test_pagination_params_custom_values(self):
        """Test PaginationParams with custom values"""
        try:
            from core.api_optimizer import PaginationParams

            params = PaginationParams(page=3, size=50, max_size=200)

            assert params.page == 3
            assert params.size == 50
            assert params.max_size == 200
            assert params.offset == 100  # (3-1) * 50

        except ImportError:
            pytest.skip("PaginationParams not available")

    def test_pagination_params_validation(self):
        """Test PaginationParams value validation"""
        try:
            from core.api_optimizer import PaginationParams

            # Test minimum values
            params = PaginationParams(page=0, size=0)
            assert params.page >= 1
            assert params.size >= 1

            # Test maximum size enforcement
            params = PaginationParams(size=150, max_size=100)
            assert params.size <= params.max_size

        except ImportError:
            pytest.skip("PaginationParams not available")

    def test_paginated_response_creation(self):
        """Test PaginatedResponse creation"""
        try:
            from core.api_optimizer import PaginatedResponse, PaginationParams

            items = [{"id": 1}, {"id": 2}, {"id": 3}]
            total = 25
            pagination = PaginationParams(page=2, size=10)

            response = PaginatedResponse.create(items, total, pagination)

            assert response.items == items
            assert response.total == 25
            assert response.page == 2
            assert response.size == 10
            assert response.pages == 3  # ceil(25/10)
            assert response.has_next is True  # page 2 < 3 pages
            assert response.has_previous is True  # page 2 > 1

        except ImportError:
            pytest.skip("PaginatedResponse not available")

    def test_paginated_response_edge_cases(self):
        """Test PaginatedResponse edge cases"""
        try:
            from core.api_optimizer import PaginatedResponse, PaginationParams

            # First page
            items = [{"id": 1}]
            pagination = PaginationParams(page=1, size=10)
            response = PaginatedResponse.create(items, 5, pagination)

            assert response.has_previous is False
            assert response.has_next is False
            assert response.pages == 1

            # Last page
            pagination = PaginationParams(page=3, size=10)
            response = PaginatedResponse.create(items, 25, pagination)

            assert response.has_previous is True
            assert response.has_next is False

        except ImportError:
            pytest.skip("PaginatedResponse not available")


class TestTurkishContentOptimizer:
    """Test Turkish content optimization utilities"""

    def test_turkish_content_optimizer_search_results(self):
        """Test Turkish search results optimization"""
        try:
            from core.api_optimizer import TurkishContentOptimizer

            results = [
                {"title": "Türkçe Ders", "content": "Matematik konuları"},
                {"title": "English Lesson", "content": "Turkish language study"},
                {"title": "Geometri", "content": "Üçgen hesaplamaları"},
            ]

            query = "türkçe"
            optimized = TurkishContentOptimizer.optimize_search_results(results, query)

            # Should return results sorted by relevance
            assert len(optimized) == 3
            assert isinstance(optimized, list)

            # First result should be the most relevant (contains "Türkçe" in title)
            assert (
                "Türkçe" in optimized[0]["title"] or "türkçe" in optimized[0]["title"]
            )

        except ImportError:
            pytest.skip("TurkishContentOptimizer not available")

    def test_turkish_content_optimizer_empty_results(self):
        """Test Turkish content optimizer with empty results"""
        try:
            from core.api_optimizer import TurkishContentOptimizer

            results = []
            query = "test"
            optimized = TurkishContentOptimizer.optimize_search_results(results, query)

            assert optimized == []

            # Test with None query
            results = [{"title": "Test"}]
            optimized = TurkishContentOptimizer.optimize_search_results(results, "")

            assert optimized == results

        except ImportError:
            pytest.skip("TurkishContentOptimizer not available")

    def test_turkish_content_optimizer_response_format(self):
        """Test Turkish content response format optimization"""
        try:
            from core.api_optimizer import TurkishContentOptimizer

            # Test string optimization
            text = "Türkçe içerik öğrenci çalışması"
            optimized = TurkishContentOptimizer.optimize_response_format(text)
            assert isinstance(optimized, str)
            assert "Türkçe" in optimized

            # Test dict optimization
            data = {"title": "Türkçe Ders", "content": "Öğrenci çalışması", "count": 42}
            optimized = TurkishContentOptimizer.optimize_response_format(data)

            assert isinstance(optimized, dict)
            assert "title" in optimized
            assert "Türkçe" in optimized["title"]
            assert optimized["count"] == 42

            # Test list optimization
            data_list = [{"name": "Öğrenci"}, {"name": "Öğretmen"}]
            optimized = TurkishContentOptimizer.optimize_response_format(data_list)

            assert isinstance(optimized, list)
            assert len(optimized) == 2

        except ImportError:
            pytest.skip("TurkishContentOptimizer not available")


class TestPerformanceDecorators:
    """Test performance optimization decorators"""

    def test_cache_response_decorator_import(self):
        """Test cache_response decorator can be imported"""
        try:
            from core.api_optimizer import cache_response

            assert callable(cache_response)

            # Test decorator creation
            decorator = cache_response(ttl=600, key_prefix="test")
            assert callable(decorator)

        except ImportError:
            pytest.skip("cache_response decorator not available")

    def test_optimize_query_decorator_import(self):
        """Test optimize_query decorator can be imported"""
        try:
            from core.api_optimizer import optimize_query

            assert callable(optimize_query)

            # Test decorator creation
            decorator = optimize_query(enable_pagination=True)
            assert callable(decorator)

        except ImportError:
            pytest.skip("optimize_query decorator not available")

    @pytest.mark.asyncio
    async def test_optimize_query_decorator_functionality(self):
        """Test optimize_query decorator basic functionality"""
        try:
            from core.api_optimizer import optimize_query

            @optimize_query(enable_pagination=True)
            async def test_function():
                return {"result": "success"}

            result = await test_function()
            assert result == {"result": "success"}

        except ImportError:
            pytest.skip("optimize_query decorator not available")


class TestGlobalAPIOptimizer:
    """Test global API optimizer functionality"""

    @pytest.mark.asyncio
    async def test_get_api_optimizer_function(self):
        """Test get_api_optimizer global function"""
        try:
            # Mock Redis to avoid connection issues
            with patch("redis.asyncio.from_url") as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.ping = AsyncMock()

                from core.api_optimizer import get_api_optimizer

                optimizer = await get_api_optimizer()

                assert optimizer is not None
                assert hasattr(optimizer, "rate_limit_config")
                assert hasattr(optimizer, "compression_config")
                assert hasattr(optimizer, "cache_config")
                assert hasattr(optimizer, "stats")

        except ImportError:
            pytest.skip("get_api_optimizer not available")


class TestExampleUsages:
    """Test example usage functions"""

    @pytest.mark.asyncio
    async def test_get_exam_questions_example(self):
        """Test get_exam_questions example function"""
        try:
            # Mock the global optimizer to avoid Redis dependency
            with patch("core.api_optimizer.get_api_optimizer") as mock_get_optimizer:
                mock_optimizer = Mock()
                mock_optimizer.redis_client = None
                mock_get_optimizer.return_value = mock_optimizer

                from core.api_optimizer import get_exam_questions

                result = await get_exam_questions(exam_id=1, subject="matematik")

                assert isinstance(result, list)
                assert len(result) >= 0

        except ImportError:
            pytest.skip("get_exam_questions example not available")

    @pytest.mark.asyncio
    async def test_search_content_example(self):
        """Test search_content example function"""
        try:
            from core.api_optimizer import PaginationParams, search_content

            pagination = PaginationParams(page=1, size=10)
            result = await search_content(query="türkçe", pagination=pagination)

            assert hasattr(result, "items")
            assert hasattr(result, "total")
            assert hasattr(result, "page")
            assert hasattr(result, "size")

        except ImportError:
            pytest.skip("search_content example not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
