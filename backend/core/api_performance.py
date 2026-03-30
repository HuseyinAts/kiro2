"""
API Performance Optimization
Middleware and utilities for optimizing API response times
"""

import asyncio
import logging
import re
import time
from collections.abc import Callable
from functools import wraps

from fastapi import Response
from fastapi.responses import JSONResponse

# SQL injection prevention: only allow safe identifiers
_SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_SAFE_FIELD = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_\.]*$")

logger = logging.getLogger(__name__)


class PerformanceMiddleware:
    """Middleware to track and optimize API performance"""

    def __init__(self, app):
        self.app = app
        self.response_times: list[float] = []
        self.slow_endpoints: dict[str, list[float]] = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        path = scope["path"]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                self.response_times.append(process_time)

                # Track slow endpoints (>200ms)
                if process_time > 0.2:
                    if path not in self.slow_endpoints:
                        self.slow_endpoints[path] = []
                    self.slow_endpoints[path].append(process_time)

                    if len(self.slow_endpoints[path]) >= 10:
                        avg_time = sum(self.slow_endpoints[path][-10:]) / 10
                        logger.warning(
                            f"Slow endpoint detected: {path} (avg: {avg_time * 1000:.2f}ms)"
                        )

                # Add performance header
                message["headers"].append(
                    (b"x-process-time-ms", f"{process_time * 1000:.2f}".encode())
                )

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def get_stats(self) -> dict:
        """Get performance statistics"""
        if not self.response_times:
            return {"message": "No requests yet"}

        return {
            "total_requests": len(self.response_times),
            "avg_response_time_ms": round(
                sum(self.response_times) / len(self.response_times) * 1000, 2
            ),
            "p50_response_time_ms": round(
                sorted(self.response_times)[len(self.response_times) // 2] * 1000, 2
            ),
            "p95_response_time_ms": round(
                sorted(self.response_times)[int(len(self.response_times) * 0.95)]
                * 1000,
                2,
            ),
            "p99_response_time_ms": round(
                sorted(self.response_times)[int(len(self.response_times) * 0.99)]
                * 1000,
                2,
            ),
            "slow_endpoints": {k: len(v) for k, v in self.slow_endpoints.items()},
        }


def async_lru_cache(maxsize=128, ttl=300):
    """
    LRU cache decorator for async functions with TTL

    Args:
        maxsize: Maximum cache size
        ttl: Time-to-live in seconds
    """
    import time
    from functools import lru_cache

    def decorator(func):
        # Create cache with timestamp tracking
        cache_times = {}

        @lru_cache(maxsize=maxsize)
        def _cached_func(*args, **kwargs):
            return func(*args, **kwargs)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = str(args) + str(sorted(kwargs.items()))

            # Check if cached and not expired
            if cache_key in cache_times:
                if time.time() - cache_times[cache_key] < ttl:
                    # Cache hit
                    return await _cached_func(*args, **kwargs)
                # Cache expired
                _cached_func.cache_clear()
                del cache_times[cache_key]

            # Cache miss or expired - execute function
            result = await func(*args, **kwargs)

            # Update cache time
            cache_times[cache_key] = time.time()

            return result

        wrapper.cache_clear = _cached_func.cache_clear
        return wrapper

    return decorator


async def batch_database_queries(queries: list[Callable], max_concurrent=10):
    """
    Execute multiple database queries concurrently

    Args:
        queries: List of async callables (queries)
        max_concurrent: Maximum concurrent queries

    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_with_semaphore(query):
        async with semaphore:
            return await query()

    results = await asyncio.gather(*[execute_with_semaphore(q) for q in queries])
    return results


class ResponseCompression:
    """Compress API responses for faster transmission"""

    @staticmethod
    def should_compress(response: Response, min_size: int = 1024) -> bool:
        """Check if response should be compressed"""
        if not hasattr(response, "body"):
            return False

        return len(response.body) > min_size

    @staticmethod
    async def compress_response(response: JSONResponse) -> Response:
        """Compress JSON response using gzip"""
        import gzip

        body = response.body

        if len(body) > 1024:  # Only compress if >1KB
            compressed = gzip.compress(body)

            if len(compressed) < len(body):
                response.body = compressed
                response.headers["Content-Encoding"] = "gzip"
                response.headers["Content-Length"] = str(len(compressed))

        return response


def optimize_query_params(limit: int = 100, offset: int = 0) -> dict:
    """
    Optimize and validate query parameters

    Args:
        limit: Result limit
        offset: Result offset

    Returns:
        Optimized parameters
    """
    # Cap limit to prevent excessive loads
    limit = min(limit, 1000)
    offset = max(offset, 0)

    return {"limit": limit, "offset": offset}


class DatabaseQueryOptimizer:
    """Optimize database queries for performance"""

    @staticmethod
    def add_select_fields(base_query: str, fields: list[str]) -> str:
        """Add only requested fields to SELECT query.

        Validates each field name against a safe identifier pattern to
        prevent SQL injection via crafted field names.
        """
        if not fields:
            return base_query  # Return all fields

        # Validate: only allow alphanumeric, underscore, dot (table.column)
        for field in fields:
            if not _SAFE_FIELD.match(field):
                raise ValueError(f"Invalid field name (SQL injection guard): {field!r}")

        field_str = ", ".join(fields)
        optimized = base_query.replace("SELECT *", f"SELECT {field_str}")
        return optimized

    @staticmethod
    def add_index_hints(query: str, _index_name: str) -> str:
        """Add index hints for PostgreSQL query planner.

        Note: PostgreSQL doesn't support named index hints.
        Uses planner config instead; index_name param kept for API compatibility.
        """
        # index_name is not interpolated into the query — no injection risk
        return f"SET enable_seqscan = off; {query}; SET enable_seqscan = on;"

    @staticmethod
    def optimize_count_query(table: str, where_clause: str = "") -> str:
        """Optimize COUNT queries using approximate counts for large tables.

        Validates table name against a safe identifier pattern to prevent
        SQL injection.
        """
        # Validate table name — must be a plain identifier
        if not _SAFE_IDENTIFIER.match(table):
            raise ValueError(f"Invalid table name (SQL injection guard): {table!r}")

        if where_clause:
            # where_clause must only be used with trusted internal callers
            return f"SELECT COUNT(*) FROM {table} WHERE {where_clause};"
        return f"""
            SELECT CASE
                WHEN c.reltuples < 10000 THEN (SELECT COUNT(*) FROM {table})
                ELSE c.reltuples::bigint
            END as count
            FROM pg_class c
            WHERE c.relname = %(table_name)s;
            """


class APIPerformanceMonitor:
    """Monitor and report API performance metrics"""

    def __init__(self):
        self.request_times: dict[str, list[float]] = {}
        self.error_counts: dict[str, int] = {}

    def record_request(self, endpoint: str, duration_ms: float, success: bool = True):
        """Record request metrics"""
        if endpoint not in self.request_times:
            self.request_times[endpoint] = []

        self.request_times[endpoint].append(duration_ms)

        if not success:
            self.error_counts[endpoint] = self.error_counts.get(endpoint, 0) + 1

    def get_endpoint_stats(self, endpoint: str) -> dict:
        """Get statistics for specific endpoint"""
        if endpoint not in self.request_times:
            return {"message": "No data for endpoint"}

        times = self.request_times[endpoint]
        times_sorted = sorted(times)

        return {
            "endpoint": endpoint,
            "total_requests": len(times),
            "avg_time_ms": round(sum(times) / len(times), 2),
            "min_time_ms": round(min(times), 2),
            "max_time_ms": round(max(times), 2),
            "p50_time_ms": round(times_sorted[len(times) // 2], 2),
            "p95_time_ms": round(times_sorted[int(len(times) * 0.95)], 2),
            "p99_time_ms": round(times_sorted[int(len(times) * 0.99)], 2),
            "error_count": self.error_counts.get(endpoint, 0),
            "error_rate": round(
                self.error_counts.get(endpoint, 0) / len(times) * 100, 2
            ),
        }

    def get_slow_endpoints(self, threshold_ms: float = 200) -> list[dict]:
        """Get endpoints slower than threshold"""
        slow_endpoints = []

        for endpoint, times in self.request_times.items():
            avg_time = sum(times) / len(times)

            if avg_time > threshold_ms:
                slow_endpoints.append(
                    {
                        "endpoint": endpoint,
                        "avg_time_ms": round(avg_time, 2),
                        "request_count": len(times),
                    }
                )

        return sorted(slow_endpoints, key=lambda x: x["avg_time_ms"], reverse=True)

    def get_overall_stats(self) -> dict:
        """Get overall performance statistics"""
        all_times = []
        for times in self.request_times.values():
            all_times.extend(times)

        if not all_times:
            return {"message": "No data yet"}

        all_times_sorted = sorted(all_times)

        return {
            "total_requests": len(all_times),
            "total_endpoints": len(self.request_times),
            "avg_response_time_ms": round(sum(all_times) / len(all_times), 2),
            "p50_response_time_ms": round(all_times_sorted[len(all_times) // 2], 2),
            "p95_response_time_ms": round(
                all_times_sorted[int(len(all_times) * 0.95)], 2
            ),
            "p99_response_time_ms": round(
                all_times_sorted[int(len(all_times) * 0.99)], 2
            ),
            "total_errors": sum(self.error_counts.values()),
            "slow_endpoints_count": len(self.get_slow_endpoints()),
        }


# Global performance monitor
_performance_monitor = APIPerformanceMonitor()


def get_performance_monitor() -> APIPerformanceMonitor:
    """Get global performance monitor instance"""
    return _performance_monitor


# Performance optimization tips
OPTIMIZATION_TIPS = {
    "database": [
        "Use indexes on frequently queried columns",
        "Limit SELECT to only needed columns",
        "Use connection pooling",
        "Cache frequent queries with Redis",
        "Use EXPLAIN ANALYZE to identify slow queries",
    ],
    "api": [
        "Enable response compression for large payloads",
        "Implement pagination for list endpoints",
        "Use async/await for I/O operations",
        "Cache responses with appropriate TTL",
        "Batch database queries when possible",
    ],
    "frontend": [
        "Implement lazy loading for heavy components",
        "Use debouncing for search/filter inputs",
        "Compress images and assets",
        "Use CDN for static files",
        "Implement virtual scrolling for long lists",
    ],
}


if __name__ == "__main__":
    # Example usage
    monitor = get_performance_monitor()

    # Simulate some requests
    monitor.record_request("/api/v2/cat/start", 45.3)
    monitor.record_request("/api/v2/cat/start", 52.1)
    monitor.record_request("/api/v2/cat/submit", 78.4)
    monitor.record_request("/api/v2/knowledge-graph/stats", 320.5)  # Slow
    monitor.record_request("/api/v2/knowledge-graph/stats", 315.2)  # Slow

    # Get stats
    print("Overall Stats:")
    print(monitor.get_overall_stats())
    print("\nSlow Endpoints:")
    for endpoint in monitor.get_slow_endpoints():
        print(f"  {endpoint}")
