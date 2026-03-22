"""
Database Query Monitoring & Performance Tracking
PERFORMANCE FIX: Real-time query performance monitoring
"""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession

from .structured_logger import get_logger

logger = get_logger("query_monitor")


class QueryMonitor:
    """
    Real-time database query monitoring

    Features:
    - Query execution time tracking
    - N+1 query detection
    - Slow query logging
    - Query count per request
    """

    def __init__(self):
        self.queries_executed = 0
        self.total_duration = 0.0
        self.slow_query_threshold = 1.0  # 1 second
        self.n_plus_one_threshold = 10  # 10+ queries indicates potential N+1
        self.query_log = []

    def reset(self):
        """Reset counters for new request"""
        self.queries_executed = 0
        self.total_duration = 0.0
        self.query_log = []

    # Sorgular bu patterndeyse N+1 sayacina dahil edilmez
    _HEALTH_QUERY_PATTERNS = (
        "information_schema",
        "SELECT 1",
        "select 1",
        "pg_stat",
        "pg_database",
    )

    def record_query(
        self, statement: str, duration: float, row_count: Optional[int] = None
    ):
        """Record a query execution"""
        # Health-check ve sistem sorgularini N+1 sayacindan hariç tut
        if any(p in statement for p in self._HEALTH_QUERY_PATTERNS):
            return  # Sayaca katma, log'a yazma

        self.queries_executed += 1
        self.total_duration += duration

        query_info = {
            "statement": statement[:200],  # Truncate long queries
            "duration": duration,
            "row_count": row_count,
            "timestamp": time.time(),
        }
        self.query_log.append(query_info)

        # Log slow queries
        if duration > self.slow_query_threshold:
            logger.warning(
                f"Slow query detected ({duration:.2f}s)",
                extra_data={
                    "duration": duration,
                    "statement": statement[:500],
                    "row_count": row_count,
                },
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get query statistics for current request"""
        return {
            "total_queries": self.queries_executed,
            "total_duration": round(self.total_duration, 3),
            "average_duration": round(
                self.total_duration / max(self.queries_executed, 1), 3
            ),
            "slow_queries": len(
                [q for q in self.query_log if q["duration"] > self.slow_query_threshold]
            ),
            "potential_n_plus_one": self.queries_executed > self.n_plus_one_threshold,
        }

    def detect_n_plus_one(self) -> bool:
        """
        Detect potential N+1 query patterns

        Heuristic: If we see many similar queries in a short time window,
        it's likely an N+1 problem
        """
        if self.queries_executed < self.n_plus_one_threshold:
            return False

        # Check for similar queries (same structure, different parameters)
        query_patterns = {}
        for query in self.query_log:
            # Normalize query (remove literals)
            normalized = self._normalize_query(query["statement"])
            query_patterns[normalized] = query_patterns.get(normalized, 0) + 1

        # If any pattern repeats 5+ times, it's likely N+1
        for pattern, count in query_patterns.items():
            if count >= 5:
                logger.error(
                    f"N+1 query detected: {count} similar queries",
                    extra_data={
                        "pattern": pattern,
                        "count": count,
                        "total_queries": self.queries_executed,
                    },
                )
                return True

        return False

    @staticmethod
    def _normalize_query(query: str) -> str:
        """Normalize query for pattern detection"""
        import re

        # Remove numbers and quoted strings
        normalized = re.sub(r"\d+", "?", query)
        normalized = re.sub(r"'[^']*'", "?", normalized)
        normalized = re.sub(r'"[^"]*"', "?", normalized)
        return normalized


# Global query monitor instance
query_monitor = QueryMonitor()


@asynccontextmanager
async def monitor_queries(session: AsyncSession, operation_name: str = "unknown"):
    """
    Context manager for monitoring queries in an operation

    Usage:
        async with monitor_queries(session, "get_user_dashboard"):
            # Your queries here
            users = await optimizer.select(User).all()
    """
    query_monitor.reset()
    start_time = time.time()

    try:
        yield query_monitor
    finally:
        duration = time.time() - start_time
        stats = query_monitor.get_stats()

        # Check for N+1
        is_n_plus_one = query_monitor.detect_n_plus_one()

        # Log operation summary
        log_level = (
            logger.warning
            if (stats["slow_queries"] > 0 or is_n_plus_one)
            else logger.info
        )
        log_level(
            f"Query monitoring: {operation_name}",
            extra_data={
                "operation": operation_name,
                "total_duration": duration,
                "db_queries": stats["total_queries"],
                "db_duration": stats["total_duration"],
                "slow_queries": stats["slow_queries"],
                "n_plus_one_detected": is_n_plus_one,
            },
        )


def setup_query_event_listeners(engine: Engine):
    """
    Set up SQLAlchemy event listeners for query monitoring

    Call this during app startup:
        from core.database import engine
        setup_query_event_listeners(engine)
    """

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        query_start_times = conn.info.get("query_start_time", [])
        if query_start_times:
            start_time = query_start_times.pop()
            duration = time.time() - start_time
            row_count = cursor.rowcount if hasattr(cursor, "rowcount") else None
            query_monitor.record_query(statement, duration, row_count)


# Middleware for automatic query monitoring per HTTP request
class QueryMonitoringMiddleware:
    """
    FastAPI middleware for automatic query monitoring

    Add to FastAPI app:
        app.add_middleware(QueryMonitoringMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Reset monitor for each request
        query_monitor.reset()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add query stats to response headers
                stats = query_monitor.get_stats()
                headers = list(message.get("headers", []))
                headers.append((b"x-db-queries", str(stats["total_queries"]).encode()))
                headers.append(
                    (b"x-db-duration", str(stats["total_duration"]).encode())
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
