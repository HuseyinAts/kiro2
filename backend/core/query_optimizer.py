"""
N+1 Query Optimization Utilities
ARCHITECTURE FIX: Prevent N+1 query problems with eager loading
"""

from typing import Any, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, subqueryload

from .structured_logger import get_logger

logger = get_logger("query_optimizer")

T = TypeVar("T")


class QueryOptimizer:
    """
    Query optimization helper to prevent N+1 queries

    Example:
        # BAD (N+1 query problem):
        users = await session.execute(select(User))
        for user in users.scalars():
            print(user.student_profile)  # Separate query for each user!

        # GOOD (Optimized with eager loading):
        optimizer = QueryOptimizer(session)
        users = await optimizer.select(User).eager_load('student_profile').all()
        for user in users:
            print(user.student_profile)  # Already loaded!
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._query = None
        self._model = None
        self._eager_loads = []
        self._joined_loads = []
        self._subquery_loads = []

    def select(self, model: type[T]) -> "QueryOptimizer":
        """
        Start a new query

        Args:
            model: SQLAlchemy model class

        Returns:
            Self for chaining
        """
        self._model = model
        self._query = select(model)
        return self

    def eager_load(self, *relationships: str) -> "QueryOptimizer":
        """
        Eager load relationships (selectinload - separate query, good for collections)

        Args:
            *relationships: Relationship attribute names

        Returns:
            Self for chaining

        Example:
            optimizer.select(User).eager_load('student_profile', 'exam_sessions')
        """
        self._eager_loads.extend(relationships)
        return self

    def joined_load(self, *relationships: str) -> "QueryOptimizer":
        """
        Joined load (joinedload - single JOIN query, good for single objects)

        Args:
            *relationships: Relationship attribute names

        Returns:
            Self for chaining

        Example:
            optimizer.select(ExamSession).joined_load('student')
        """
        self._joined_loads.extend(relationships)
        return self

    def subquery_load(self, *relationships: str) -> "QueryOptimizer":
        """
        Subquery load (subqueryload - separate subquery, good for large collections)

        Args:
            *relationships: Relationship attribute names

        Returns:
            Self for chaining
        """
        self._subquery_loads.extend(relationships)
        return self

    def filter(self, *conditions) -> "QueryOptimizer":
        """
        Add filter conditions

        Args:
            *conditions: SQLAlchemy filter conditions

        Returns:
            Self for chaining
        """
        self._query = self._query.filter(*conditions)
        return self

    def order_by(self, *columns) -> "QueryOptimizer":
        """
        Add ordering

        Args:
            *columns: Columns to order by

        Returns:
            Self for chaining
        """
        self._query = self._query.order_by(*columns)
        return self

    def limit(self, limit: int) -> "QueryOptimizer":
        """
        Add limit

        Args:
            limit: Number of results

        Returns:
            Self for chaining
        """
        self._query = self._query.limit(limit)
        return self

    def offset(self, offset: int) -> "QueryOptimizer":
        """
        Add offset

        Args:
            offset: Offset value

        Returns:
            Self for chaining
        """
        self._query = self._query.offset(offset)
        return self

    def _build_query(self) -> Select:
        """Build final query with all optimizations"""
        query = self._query

        # Apply eager loads (selectinload)
        for rel in self._eager_loads:
            query = query.options(selectinload(getattr(self._model, rel)))

        # Apply joined loads
        for rel in self._joined_loads:
            query = query.options(joinedload(getattr(self._model, rel)))

        # Apply subquery loads
        for rel in self._subquery_loads:
            query = query.options(subqueryload(getattr(self._model, rel)))

        return query

    async def all(self) -> list[T]:
        """
        Execute query and return all results

        Returns:
            List of model instances
        """
        query = self._build_query()
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def first(self) -> T | None:
        """
        Execute query and return first result

        Returns:
            First model instance or None
        """
        query = self._build_query()
        result = await self.session.execute(query)
        return result.scalars().first()

    async def one(self) -> T:
        """
        Execute query and return exactly one result

        Returns:
            Model instance

        Raises:
            sqlalchemy.exc.NoResultFound: If no result found
            sqlalchemy.exc.MultipleResultsFound: If multiple results found
        """
        query = self._build_query()
        result = await self.session.execute(query)
        return result.scalars().one()

    async def count(self) -> int:
        """
        Count results

        Returns:
            Number of results
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(self._model)
        result = await self.session.execute(query)
        return result.scalar()


# Composite index recommendations
RECOMMENDED_INDEXES = {
    "users": [
        # Composite index for role + active status queries
        ("role", "is_active"),
        # Composite index for email + active status
        ("email", "is_active"),
    ],
    "student_profile": [
        # Composite index for grade + learning style
        ("grade_level", "learning_style"),
        # Composite index for user_id + grade
        ("user_id", "grade_level"),
    ],
    "exam_sessions": [
        # Composite index for student + exam type + status
        ("student_id", "exam_type", "status"),
        # Composite index for created date + exam type
        ("created_at", "exam_type"),
    ],
    "questions": [
        # Composite index for subject + difficulty + exam type
        ("subject_area", "difficulty", "exam_type"),
        # Composite index for irt_difficulty + subject
        ("irt_difficulty", "subject_area"),
    ],
    "exam_answers": [
        # Composite index for session + question (most common query)
        ("exam_session_id", "question_id"),
        # Composite index for student performance analysis
        ("student_id", "is_correct", "created_at"),
    ],
}


def log_query_performance(query_name: str, duration: float, row_count: int):
    """
    Log query performance for monitoring

    Args:
        query_name: Name of the query
        duration: Query duration in seconds
        row_count: Number of rows returned
    """
    if duration > 1.0:
        logger.warning(
            f"Slow query detected: {query_name}",
            extra_data={"duration": duration, "row_count": row_count, "status": "slow"},
        )
    else:
        logger.debug(
            f"Query executed: {query_name}",
            extra_data={"duration": duration, "row_count": row_count},
        )


# ==================== TASK 58.2: ADDITIONAL OPTIMIZATIONS ====================

import functools
import time
from collections.abc import Callable
from contextlib import contextmanager


class QueryStats:
    """Track query execution statistics"""

    def __init__(self):
        self.total_queries = 0
        self.total_time = 0.0
        self.slow_queries = []
        self.slow_threshold = 1.0  # 1 second

    def add_query(self, duration: float, query_name: str):
        """Record a query execution"""
        self.total_queries += 1
        self.total_time += duration

        if duration > self.slow_threshold:
            self.slow_queries.append(
                {"name": query_name, "duration": duration, "timestamp": time.time()}
            )

    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            "total_queries": self.total_queries,
            "total_time": self.total_time,
            "avg_time": self.total_time / max(self.total_queries, 1),
            "slow_query_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-10:],
        }

    def reset(self):
        """Reset statistics"""
        self.total_queries = 0
        self.total_time = 0.0
        self.slow_queries = []


# Global query stats
_query_stats = QueryStats()


def get_query_stats() -> dict:
    """Get global query statistics"""
    return _query_stats.get_stats()


def reset_query_stats():
    """Reset global query statistics"""
    _query_stats.reset()


def timed_query(query_name: str = None):
    """
    Decorator to time query execution

    Example:
        @timed_query("get_active_users")
        async def get_active_users(session: AsyncSession):
            result = await session.execute(select(User).filter(User.is_active == True))
            return result.scalars().all()
    """

    def decorator(func: Callable) -> Callable:
        name = query_name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Count rows if result is a list
                row_count = len(result) if isinstance(result, list) else 1

                # Log performance
                log_query_performance(name, duration, row_count)
                _query_stats.add_query(duration, name)

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Query failed: {name} (duration: {duration:.3f}s)", exc_info=e
                )
                raise

        return wrapper

    return decorator


@contextmanager
def query_counter(description: str = "Query block"):
    """
    Context manager to count queries in a block

    Example:
        with query_counter("User dashboard load"):
            users = await get_users(session)
            posts = await get_posts(session)
        # Logs: "Query block: User dashboard load - 2 queries executed"
    """
    start_count = _query_stats.total_queries
    start_time = time.time()

    yield

    end_count = _query_stats.total_queries
    duration = time.time() - start_time
    queries_executed = end_count - start_count

    logger.info(
        f"{description} - {queries_executed} queries executed in {duration:.3f}s",
        extra_data={"query_count": queries_executed, "duration": duration},
    )


class BatchLoader:
    """
    Batch loader to prevent N+1 queries

    Example:
        loader = BatchLoader(session, User, 'id')
        users = await loader.load_many([1, 2, 3, 4, 5])
    """

    def __init__(self, session: AsyncSession, model: type[T], key_attr: str = "id"):
        self.session = session
        self.model = model
        self.key_attr = key_attr
        self._cache = {}

    async def load(self, key: Any) -> T | None:
        """Load a single item by key"""
        if key not in self._cache:
            await self.load_many([key])
        return self._cache.get(key)

    async def load_many(self, keys: list[Any]) -> list[T]:
        """Load multiple items by keys in a single query"""
        # Find keys not in cache
        missing_keys = [k for k in keys if k not in self._cache]

        if missing_keys:
            # Fetch missing items
            query = select(self.model).filter(
                getattr(self.model, self.key_attr).in_(missing_keys)
            )
            result = await self.session.execute(query)
            items = result.scalars().all()

            # Add to cache
            for item in items:
                key = getattr(item, self.key_attr)
                self._cache[key] = item

            logger.debug(
                f"BatchLoader: Loaded {len(items)} {self.model.__name__} records"
            )

        # Return items in requested order
        return [self._cache.get(k) for k in keys if k in self._cache]


def optimize_pagination(
    query: Select, page: int, per_page: int, max_per_page: int = 100
):
    """
    Optimize pagination with limits

    Args:
        query: SQLAlchemy select query
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum allowed items per page

    Returns:
        Modified query with offset and limit
    """
    # Enforce maximum
    per_page = min(per_page, max_per_page)

    # Calculate offset
    offset = (page - 1) * per_page

    return query.offset(offset).limit(per_page)


# Usage examples in docstring
"""
TASK 58.2 OPTIMIZATION EXAMPLES
================================

1. Timed Query Decorator:
--------------------------
from core.query_optimizer import timed_query

@timed_query("fetch_student_dashboard")
async def get_student_dashboard(session: AsyncSession, student_id: int):
    optimizer = QueryOptimizer(session)
    return await optimizer.select(StudentProfile).filter(
        StudentProfile.user_id == student_id
    ).eager_load('exam_sessions', 'learning_preferences').first()

2. Query Counter Context:
--------------------------
from core.query_optimizer import query_counter

async def load_dashboard(session: AsyncSession, user_id: int):
    with query_counter("Dashboard load"):
        user = await get_user(session, user_id)
        stats = await get_user_stats(session, user_id)
        recent_exams = await get_recent_exams(session, user_id)
    # Logs total queries executed

3. Batch Loader (Prevent N+1):
------------------------------
from core.query_optimizer import BatchLoader

async def get_posts_with_authors(session: AsyncSession, post_ids: List[int]):
    # Load all posts
    posts = await session.execute(select(Post).filter(Post.id.in_(post_ids)))
    posts = posts.scalars().all()

    # Batch load all authors (single query instead of N queries)
    author_ids = [p.author_id for p in posts]
    loader = BatchLoader(session, User, 'id')
    authors = await loader.load_many(author_ids)

    # No N+1 query problem!
    return posts

4. Query Stats Monitoring:
---------------------------
from core.query_optimizer import get_query_stats, reset_query_stats

# Get current stats
stats = get_query_stats()
print(f"Total queries: {stats['total_queries']}")
print(f"Average time: {stats['avg_time']:.3f}s")
print(f"Slow queries: {stats['slow_query_count']}")

# Reset for new measurement period
reset_query_stats()
"""
