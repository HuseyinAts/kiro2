"""
KIRO2 API Performance Optimization Module
FastAPI response optimization, rate limiting, and compression
"""

import gzip
import json
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import Any

import redis.asyncio as redis
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""

    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 20
    enabled: bool = True


class CompressionConfig(BaseModel):
    """Response compression configuration"""

    enabled: bool = True
    min_size: int = 1024  # Minimum response size to compress (bytes)
    compression_level: int = 6  # 1-9, higher = better compression, slower
    mime_types: list[str] = [
        "application/json",
        "application/javascript",
        "text/css",
        "text/html",
        "text/plain",
        "text/xml",
        "application/xml",
    ]


class CacheConfig(BaseModel):
    """Response caching configuration"""

    enabled: bool = True
    default_ttl: int = 300  # 5 minutes
    redis_url: str = "redis://localhost:6379/1"
    cache_headers: bool = True


class APIOptimizer:
    """
    API performance optimizer for KIRO2
    Handles rate limiting, compression, caching, and pagination
    """

    def __init__(
        self,
        rate_limit_config: RateLimitConfig,
        compression_config: CompressionConfig,
        cache_config: CacheConfig,
    ):
        self.rate_limit_config = rate_limit_config
        self.compression_config = compression_config
        self.cache_config = cache_config
        self.redis_client: redis.Redis | None = None
        self.stats = {
            "total_requests": 0,
            "rate_limited": 0,
            "compressed_responses": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0.0,
        }

    async def initialize(self):
        """Initialize API optimizer"""
        try:
            if self.cache_config.enabled:
                self.redis_client = redis.from_url(
                    self.cache_config.redis_url, encoding="utf-8", decode_responses=True
                )
                await self.redis_client.ping()

            logger.info("API optimizer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize API optimizer: {e}")
            raise

    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("API optimizer closed")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, app, optimizer: APIOptimizer):
        super().__init__(app)
        self.optimizer = optimizer
        self.config = optimizer.rate_limit_config

    async def dispatch(self, request: Request, call_next):
        """Process rate limiting"""
        if not self.config.enabled:
            return await call_next(request)

        # Get client identifier (IP + user if available)
        client_ip = request.client.host
        user_id = request.headers.get("X-User-ID", "anonymous")
        client_key = f"rate_limit:{client_ip}:{user_id}"

        try:
            # Check rate limits
            if await self._is_rate_limited(client_key):
                self.optimizer.stats["rate_limited"] += 1
                # Middleware MUST return a Response, not raise HTTPException.
                # Raising here escapes the middleware stack and surfaces as a
                # generic 500 (see .claude/rules/middleware.md / GF99).
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Çok fazla istek gönderiyorsunuz. Lütfen bir süre bekleyin.",
                        "retry_after": 60,
                    },
                    headers={"Retry-After": "60"},
                )

            # Process request
            start_time = time.time()
            response = await call_next(request)
            response_time = time.time() - start_time

            # Update stats
            self.optimizer.stats["total_requests"] += 1
            self.optimizer.stats["average_response_time"] = (
                self.optimizer.stats["average_response_time"]
                * (self.optimizer.stats["total_requests"] - 1)
                + response_time
            ) / self.optimizer.stats["total_requests"]

            # Update rate limit counters
            await self._update_rate_limit(client_key)

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            return await call_next(request)

    async def _is_rate_limited(self, client_key: str) -> bool:
        """Check if client is rate limited"""
        if not self.optimizer.redis_client:
            return False

        try:
            current_minute = int(time.time() / 60)
            current_hour = int(time.time() / 3600)
            current_day = int(time.time() / 86400)

            # Check minute limit
            minute_key = f"{client_key}:minute:{current_minute}"
            minute_count = await self.optimizer.redis_client.get(minute_key) or 0

            if int(minute_count) >= self.config.requests_per_minute:
                return True

            # Check hour limit
            hour_key = f"{client_key}:hour:{current_hour}"
            hour_count = await self.optimizer.redis_client.get(hour_key) or 0

            if int(hour_count) >= self.config.requests_per_hour:
                return True

            # Check day limit
            day_key = f"{client_key}:day:{current_day}"
            day_count = await self.optimizer.redis_client.get(day_key) or 0

            if int(day_count) >= self.config.requests_per_day:
                return True

            return False

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False

    async def _update_rate_limit(self, client_key: str):
        """Update rate limit counters"""
        if not self.optimizer.redis_client:
            return

        try:
            current_minute = int(time.time() / 60)
            current_hour = int(time.time() / 3600)
            current_day = int(time.time() / 86400)

            # Update counters with expiration
            pipe = self.optimizer.redis_client.pipeline()

            minute_key = f"{client_key}:minute:{current_minute}"
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)  # 2 minutes

            hour_key = f"{client_key}:hour:{current_hour}"
            pipe.incr(hour_key)
            pipe.expire(hour_key, 7200)  # 2 hours

            day_key = f"{client_key}:day:{current_day}"
            pipe.incr(day_key)
            pipe.expire(day_key, 172800)  # 2 days

            await pipe.execute()

        except Exception as e:
            logger.error(f"Rate limit update error: {e}")


class CompressionMiddleware(BaseHTTPMiddleware):
    """Response compression middleware"""

    def __init__(self, app, optimizer: APIOptimizer):
        super().__init__(app)
        self.optimizer = optimizer
        self.config = optimizer.compression_config

    async def dispatch(self, request: Request, call_next):
        """Process response compression"""
        response = await call_next(request)

        if not self.config.enabled:
            return response

        # Check if client accepts gzip
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response

        # Check content type
        content_type = response.headers.get("Content-Type", "").lower()
        should_compress = any(
            mime_type in content_type for mime_type in self.config.mime_types
        )

        if not should_compress:
            return response

        # Get response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Check minimum size
        if len(response_body) < self.config.min_size:
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=content_type,
            )

        # Compress response
        try:
            compressed_body = gzip.compress(
                response_body, compresslevel=self.config.compression_level
            )

            # Only use compression if it actually reduces size
            if len(compressed_body) < len(response_body):
                self.optimizer.stats["compressed_responses"] += 1

                headers = dict(response.headers)
                headers["Content-Encoding"] = "gzip"
                headers["Content-Length"] = str(len(compressed_body))
                headers["Vary"] = "Accept-Encoding"

                return Response(
                    content=compressed_body,
                    status_code=response.status_code,
                    headers=headers,
                    media_type=content_type,
                )

        except Exception as e:
            logger.error(f"Compression error: {e}")

        # Return original response if compression fails or doesn't help
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=content_type,
        )


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """Response caching middleware"""

    def __init__(self, app, optimizer: APIOptimizer):
        super().__init__(app)
        self.optimizer = optimizer
        self.config = optimizer.cache_config

    async def dispatch(self, request: Request, call_next):
        """Process response caching"""
        if not self.config.enabled or request.method != "GET":
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get from cache
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            self.optimizer.stats["cache_hits"] += 1
            return JSONResponse(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response.get("headers", {}),
            )

        # Process request
        response = await call_next(request)

        # Cache successful responses
        if response.status_code == 200:
            await self._cache_response(cache_key, response)

        self.optimizer.stats["cache_misses"] += 1
        return response

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        # Include path, query parameters, and user context
        user_id = request.headers.get("X-User-ID", "anonymous")
        query_string = str(request.query_params)

        cache_key = f"api_cache:{request.url.path}:{query_string}:{user_id}"
        return cache_key

    async def _get_cached_response(self, cache_key: str) -> dict | None:
        """Get cached response"""
        if not self.optimizer.redis_client:
            return None

        try:
            cached_data = await self.optimizer.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")

        return None

    async def _cache_response(self, cache_key: str, response: StarletteResponse):
        """Cache response"""
        if not self.optimizer.redis_client:
            return

        try:
            # Get response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Parse JSON response
            try:
                content = json.loads(response_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                return  # Don't cache non-JSON responses

            cache_data = {
                "content": content,
                "status_code": response.status_code,
                "headers": {
                    "Content-Type": response.headers.get(
                        "Content-Type", "application/json"
                    )
                },
                "cached_at": datetime.now(UTC).isoformat(),
            }

            await self.optimizer.redis_client.setex(
                cache_key,
                self.config.default_ttl,
                json.dumps(cache_data, ensure_ascii=False),
            )

        except Exception as e:
            logger.error(f"Cache set error: {e}")


# Pagination utilities
class PaginationParams(BaseModel):
    """Pagination parameters"""

    page: int = 1
    size: int = 20
    max_size: int = 100

    def __post_init__(self):
        self.page = max(1, self.page)
        self.size = min(max(1, self.size), self.max_size)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel):
    """Paginated response model"""

    items: list[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def create(cls, items: list[Any], total: int, pagination: PaginationParams):
        """Create paginated response"""
        pages = (total + pagination.size - 1) // pagination.size

        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages,
            has_next=pagination.page < pages,
            has_previous=pagination.page > 1,
        )


# Performance decorators
def cache_response(ttl: int = 300, key_prefix: str = "api"):
    """Decorator to cache API responses"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and parameters
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get API optimizer instance
            try:
                from .api_optimizer import get_api_optimizer

                optimizer = await get_api_optimizer()

                if optimizer.redis_client:
                    # Try cache first
                    cached_result = await optimizer.redis_client.get(cache_key)
                    if cached_result:
                        optimizer.stats["cache_hits"] += 1
                        return json.loads(cached_result)
            except (
                redis.ConnectionError,
                redis.TimeoutError,
                redis.RedisError,
                json.JSONDecodeError,
                ImportError,
            ):
                pass

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            try:
                if optimizer.redis_client:
                    await optimizer.redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, ensure_ascii=False, default=str),
                    )
                    optimizer.stats["cache_misses"] += 1
            except (
                redis.ConnectionError,
                redis.TimeoutError,
                redis.RedisError,
                TypeError,
                ValueError,
            ):
                pass

            return result

        return wrapper

    return decorator


def optimize_query(_: bool = True):
    """Decorator to optimize database queries"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # Log performance
                execution_time = time.time() - start_time
                if execution_time > 1.0:  # Log slow queries
                    logger.warning(
                        f"Slow query in {func.__name__}: {execution_time:.3f}s"
                    )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Query error in {func.__name__}: {e} (took {execution_time:.3f}s)"
                )
                raise

        return wrapper

    return decorator


# Turkish content optimization
class TurkishContentOptimizer:
    """Optimize responses for Turkish content"""

    @staticmethod
    def optimize_search_results(results: list[dict], query: str) -> list[dict]:
        """Optimize search results for Turkish query"""
        if not query or not results:
            return results

        # Turkish character normalization for relevance scoring
        turkish_chars = {
            "ç": "c",
            "ğ": "g",
            "ı": "i",
            "İ": "I",
            "ö": "o",
            "ş": "s",
            "ü": "u",
            "Ç": "C",
            "Ğ": "G",
            "Ö": "O",
            "Ş": "S",
            "Ü": "U",
        }

        normalized_query = query.lower()
        for tr_char, en_char in turkish_chars.items():
            normalized_query = normalized_query.replace(tr_char.lower(), en_char)

        # Add relevance scores
        for item in results:
            relevance_score = 0

            # Check title relevance
            if item.get("title"):
                title_normalized = item["title"].lower()
                for tr_char, en_char in turkish_chars.items():
                    title_normalized = title_normalized.replace(
                        tr_char.lower(), en_char
                    )

                if normalized_query in title_normalized:
                    relevance_score += 10

            # Check content relevance
            if item.get("content"):
                content_normalized = item["content"].lower()
                for tr_char, en_char in turkish_chars.items():
                    content_normalized = content_normalized.replace(
                        tr_char.lower(), en_char
                    )

                if normalized_query in content_normalized:
                    relevance_score += 5

            item["_relevance_score"] = relevance_score

        # Sort by relevance
        results.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)

        # Remove relevance score from response
        for item in results:
            item.pop("_relevance_score", None)

        return results

    @staticmethod
    def optimize_response_format(data: Any) -> Any:
        """Optimize response format for Turkish content"""
        if isinstance(data, dict):
            optimized = {}
            for key, value in data.items():
                # Ensure Turkish characters are properly encoded
                if isinstance(value, str):
                    optimized[key] = value.encode("utf-8").decode("utf-8")
                else:
                    optimized[key] = TurkishContentOptimizer.optimize_response_format(
                        value
                    )
            return optimized

        if isinstance(data, list):
            return [
                TurkishContentOptimizer.optimize_response_format(item) for item in data
            ]

        if isinstance(data, str):
            return data.encode("utf-8").decode("utf-8")

        return data


# Global API optimizer instance
api_optimizer: APIOptimizer | None = None


async def get_api_optimizer() -> APIOptimizer:
    """Get global API optimizer instance"""
    global api_optimizer

    if api_optimizer is None:
        rate_limit_config = RateLimitConfig()
        compression_config = CompressionConfig()
        cache_config = CacheConfig()

        api_optimizer = APIOptimizer(
            rate_limit_config=rate_limit_config,
            compression_config=compression_config,
            cache_config=cache_config,
        )

        await api_optimizer.initialize()

    return api_optimizer


# Usage examples
@cache_response(ttl=600, key_prefix="exam_questions")
async def get_exam_questions(exam_id: int, subject: str):
    """Cached exam questions endpoint"""
    # Simulated database query
    questions = [
        {"id": 1, "content": "Matematik sorusu", "subject": subject},
        {"id": 2, "content": "Geometri sorusu", "subject": subject},
    ]

    return TurkishContentOptimizer.optimize_response_format(questions)


@optimize_query(True)
async def search_content(query: str, pagination: PaginationParams):
    """Optimized content search"""
    # Simulated search results
    results = [
        {"title": "Türkçe İçerik", "content": "Türkiye Üniversite Sınavları"},
        {"title": "Matematik Dersi", "content": "Calculus ve Türev Konuları"},
    ]

    # Optimize for Turkish content
    optimized_results = TurkishContentOptimizer.optimize_search_results(results, query)

    total = len(optimized_results)
    items = optimized_results[pagination.offset : pagination.offset + pagination.size]

    return PaginatedResponse.create(items, total, pagination)
