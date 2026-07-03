"""
Query Monitoring Configuration
Sprint 1 - Database Optimization

Provides slow query logging, Prometheus metrics, and performance tracking.
"""

import logging
import time
from contextlib import contextmanager

from prometheus_client import Counter, Histogram
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Configure logger
logger = logging.getLogger("query_monitor")

# ============================================================================
# Prometheus Metrics
# ============================================================================


def _metric(cls, name, *args, **kwargs):
    """Idempotent metric factory — çift-import'ta (ör. pytest conftest app'i iki
    kez import ederse) 'Duplicated timeseries in CollectorRegistry' hatasını önler,
    mevcut collector'ı geri döndürür. Tek-import (prod) davranışı değişmez.
    """
    from prometheus_client import REGISTRY

    try:
        return cls(name, *args, **kwargs)
    except ValueError:
        existing = getattr(REGISTRY, "_names_to_collectors", {}).get(name)
        if existing is not None:
            return existing
        raise


# Query execution time histogram
query_duration = _metric(
    Histogram,
    "database_query_duration_seconds",
    "Database query execution time in seconds",
    ["query_type", "table"],
    buckets=(
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
    ),
)

# Slow query counter
slow_queries = _metric(
    Counter,
    "database_slow_queries_total",
    "Total number of slow database queries (>100ms)",
    ["query_type", "table"],
)

# Total queries counter
total_queries = _metric(
    Counter,
    "database_queries_total",
    "Total number of database queries",
    ["query_type"],
)

# N+1 detection counter
n_plus_one_detected = _metric(
    Counter,
    "database_n_plus_one_queries_total",
    "Potential N+1 queries detected",
    ["table"],
)

# ============================================================================
# Configuration
# ============================================================================


class QueryMonitorConfig:
    """Query monitoring configuration"""

    # Slow query threshold in seconds
    SLOW_QUERY_THRESHOLD = 0.1  # 100ms

    # Enable query logging
    ENABLE_QUERY_LOGGING = True

    # Disable N+1 detection for load testing
    ENABLE_N_PLUS_ONE_DETECTION = False

    # Log all queries (set False in production)
    LOG_ALL_QUERIES = False

    # Maximum query log length
    MAX_QUERY_LOG_LENGTH = 500


# ============================================================================
# Query Monitoring Functions
# ============================================================================


def extract_query_info(statement: str) -> tuple[str, str | None]:
    """
    Extract query type and table name from SQL statement

    Returns:
        (query_type, table_name)
        Examples: ("SELECT", "users"), ("INSERT", "questions")
    """
    statement_upper = statement.strip().upper()

    # Extract query type
    query_type = "UNKNOWN"
    if statement_upper.startswith("SELECT"):
        query_type = "SELECT"
    elif statement_upper.startswith("INSERT"):
        query_type = "INSERT"
    elif statement_upper.startswith("UPDATE"):
        query_type = "UPDATE"
    elif statement_upper.startswith("DELETE"):
        query_type = "DELETE"

    # Extract table name (basic parsing)
    table_name = None
    try:
        if "FROM" in statement_upper:
            parts = statement_upper.split("FROM")[1].split()
            if parts:
                table_name = parts[0].strip().lower()
                # Remove schema prefix if present
                if "." in table_name:
                    table_name = table_name.split(".")[-1]
        elif "INTO" in statement_upper:
            parts = statement_upper.split("INTO")[1].split()
            if parts:
                table_name = parts[0].strip().lower()
        elif "UPDATE" in statement_upper:
            parts = statement_upper.split("UPDATE")[1].split()
            if parts:
                table_name = parts[0].strip().lower()
    except (IndexError, AttributeError):
        pass

    return query_type, table_name


def log_query(statement: str, duration: float, is_slow: bool = False):
    """
    Log query execution

    Args:
        statement: SQL statement
        duration: Execution time in seconds
        is_slow: Whether this is a slow query
    """
    if not QueryMonitorConfig.ENABLE_QUERY_LOGGING:
        return

    # Truncate long queries
    if len(statement) > QueryMonitorConfig.MAX_QUERY_LOG_LENGTH:
        statement = statement[: QueryMonitorConfig.MAX_QUERY_LOG_LENGTH] + "..."

    if is_slow:
        logger.warning(f"SLOW QUERY ({duration * 1000:.2f}ms): {statement}")
    elif QueryMonitorConfig.LOG_ALL_QUERIES:
        logger.debug(f"Query ({duration * 1000:.2f}ms): {statement}")


# ============================================================================
# SQLAlchemy Event Listeners
# ============================================================================


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Called before query execution

    Records start time for duration measurement
    """
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Called after query execution

    Measures duration, logs slow queries, updates metrics
    """
    # Calculate duration
    start_time = conn.info["query_start_time"].pop()
    duration = time.time() - start_time

    # Extract query info
    query_type, table_name = extract_query_info(statement)

    # Update total queries counter
    total_queries.labels(query_type=query_type).inc()

    # Record query duration
    if table_name:
        query_duration.labels(query_type=query_type, table=table_name).observe(duration)

    # Log query performance to optimizer
    try:
        from core.database_optimizer import query_optimizer

        query_optimizer.log_query_performance(
            query_name=f"{query_type} {table_name or 'unknown'}",
            execution_time=duration,
            query=statement,
        )
    except Exception as e:
        logger.error(f"Failed to log query performance to optimizer: {e}")

    # Detect slow queries
    is_slow = duration > QueryMonitorConfig.SLOW_QUERY_THRESHOLD
    if is_slow:
        if table_name:
            slow_queries.labels(query_type=query_type, table=table_name).inc()

        log_query(statement, duration, is_slow=True)
    else:
        log_query(statement, duration, is_slow=False)


# ============================================================================
# N+1 Query Detection
# ============================================================================


class N1QueryDetector:
    """
    Detects potential N+1 query patterns

    Tracks sequential similar queries within a short time window
    """

    def __init__(self, threshold: int = 5, window_seconds: float = 1.0):
        """
        Args:
            threshold: Number of similar queries to trigger alert
            window_seconds: Time window for detection
        """
        self.threshold = threshold
        self.window_seconds = window_seconds
        self.recent_queries: list = []

    def check_query(self, statement: str, timestamp: float):
        """
        Check if query is part of N+1 pattern

        Args:
            statement: SQL statement
            timestamp: Query timestamp

        Returns:
            True if N+1 pattern detected
        """
        if not QueryMonitorConfig.ENABLE_N_PLUS_ONE_DETECTION:
            return False

        # Clean old queries outside window
        cutoff_time = timestamp - self.window_seconds
        self.recent_queries = [
            (q, t) for q, t in self.recent_queries if t > cutoff_time
        ]

        # Normalize query (remove parameter values)
        normalized = self._normalize_query(statement)

        # Add current query
        self.recent_queries.append((normalized, timestamp))

        # Count similar queries
        similar_count = sum(1 for q, _ in self.recent_queries if q == normalized)

        # Detect N+1
        if similar_count >= self.threshold:
            query_type, table_name = extract_query_info(statement)
            if table_name:
                n_plus_one_detected.labels(table=table_name).inc()

            logger.warning(
                f"N+1 QUERY PATTERN DETECTED: {similar_count} similar queries to {table_name} "
                f"in {self.window_seconds}s window"
            )
            return True

        return False

    def _normalize_query(self, statement: str) -> str:
        """
        Normalize query by removing parameter values

        Example:
            "SELECT * FROM users WHERE id = 123" -> "SELECT * FROM users WHERE id = ?"
        """
        # Basic normalization - replace numbers with ?
        import re

        normalized = re.sub(r"\b\d+\b", "?", statement)
        return normalized.strip()


# Global N+1 detector instance
n1_detector = N1QueryDetector()


@event.listens_for(Engine, "after_cursor_execute")
def detect_n_plus_one(conn, cursor, statement, parameters, context, executemany):
    """
    Detect N+1 query patterns
    """
    n1_detector.check_query(statement, time.time())


# ============================================================================
# Context Manager for Query Tracking
# ============================================================================


@contextmanager
def track_query_performance(operation_name: str):
    """
    Context manager to track query performance for a specific operation

    Usage:
        with track_query_performance("load_exam_results"):
            # Your database queries here
            results = await get_exam_results()
    """
    start_time = time.time()
    query_count_before = total_queries._value.sum()

    try:
        yield
    finally:
        duration = time.time() - start_time
        query_count_after = total_queries._value.sum()
        query_count = query_count_after - query_count_before

        logger.info(
            f"Operation '{operation_name}': {query_count} queries in {duration * 1000:.2f}ms"
        )

        if query_count > 10:
            logger.warning(
                f"HIGH QUERY COUNT: Operation '{operation_name}' executed {query_count} queries"
            )


# ============================================================================
# Initialization
# ============================================================================


def setup_query_monitoring():
    """
    Initialize query monitoring

    Call this during application startup
    """
    logger.info("Query monitoring initialized")
    logger.info(
        f"Slow query threshold: {QueryMonitorConfig.SLOW_QUERY_THRESHOLD * 1000}ms"
    )
    logger.info(
        f"N+1 detection: {'enabled' if QueryMonitorConfig.ENABLE_N_PLUS_ONE_DETECTION else 'disabled'}"
    )


# Auto-initialize on import
setup_query_monitoring()
