"""
KIRO2 Unified Database System
Consolidated database management solution combining all database functionality
"""

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from sqlalchemy import MetaData, event, inspect, text
from sqlalchemy.exc import (
    DisconnectionError,
    OperationalError,
    TimeoutError,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

logger = logging.getLogger(__name__)
T = TypeVar("T")

# Base class for all models
Base = declarative_base()


class DatabaseType(Enum):
    """Database type enumeration"""

    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"


class IsolationLevel(Enum):
    """Transaction isolation levels"""

    READ_UNCOMMITTED = "READ_UNCOMMITTED"
    READ_COMMITTED = "READ_COMMITTED"
    REPEATABLE_READ = "REPEATABLE_READ"
    SERIALIZABLE = "SERIALIZABLE"


class PoolStrategy(Enum):
    """Connection pool strategies"""

    QUEUE_POOL = "queue"
    NULL_POOL = "null"
    STATIC_POOL = "static"


@dataclass
class DatabaseConfig:
    """Unified database configuration"""

    # Connection settings
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kiro2"
    echo: bool = False
    echo_pool: bool = False

    # Connection pool settings
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    pool_strategy: PoolStrategy = PoolStrategy.QUEUE_POOL

    # Query settings
    query_timeout: int = 30
    statement_timeout: int = 60

    # Connection retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True

    # Monitoring settings
    enable_monitoring: bool = True
    slow_query_threshold: float = 1.0  # seconds

    # Turkish optimization
    timezone: str = "Europe/Istanbul"
    charset: str = "utf8"
    locale: str = "tr_TR.UTF-8"


@dataclass
class ConnectionStats:
    """Database connection statistics"""

    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    queries_executed: int = 0
    failed_queries: int = 0
    slow_queries: int = 0
    total_query_time: float = 0.0
    avg_query_time: float = 0.0
    last_error: str | None = None
    uptime: datetime = field(default_factory=datetime.now)

    @property
    def error_rate(self) -> float:
        total = self.queries_executed + self.failed_queries
        return self.failed_queries / total if total > 0 else 0.0


@dataclass
class QueryMetrics:
    """Query execution metrics"""

    query_id: str
    sql: str
    params: dict | None = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration: float | None = None
    success: bool = False
    error: str | None = None
    row_count: int | None = None

    def complete(
        self,
        success: bool = True,
        error: str | None = None,
        row_count: int | None = None,
    ):
        """Mark query as completed"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error = error
        self.row_count = row_count


class DatabaseHealthCheck:
    """Database health monitoring"""

    @staticmethod
    async def check_connection(engine: AsyncEngine) -> dict[str, Any]:
        """Check database connection health"""
        import time

        try:
            # Measure response time
            start_time = time.time()

            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()

                # Get database info
                db_info = await conn.execute(text("SELECT version()"))
                version = db_info.scalar()

                # Calculate response time
                end_time = time.time()
                response_time_ms = round((end_time - start_time) * 1000, 2)

                return {
                    "status": "healthy",
                    "response_time_ms": response_time_ms,
                    "database_version": version,
                    "connection_test": row[0] == 1,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


class UnifiedDatabaseManager:
    """
    Unified database manager combining all database functionality:
    - Advanced connection management and pooling
    - Query optimization and monitoring
    - Transaction management
    - Error handling and recovery
    - Performance monitoring
    - Turkish optimization
    """

    def __init__(self, config: DatabaseConfig | None = None):
        self.config = config or DatabaseConfig()
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker | None = None
        self.stats = ConnectionStats()
        self.query_history: list[QueryMetrics] = []
        self.health_checker = DatabaseHealthCheck()
        self._monitoring_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Initialize database connections"""
        try:
            # Configure connection pool
            pool_class = self._get_pool_class()

            # Create async engine
            self.engine = create_async_engine(
                self.config.database_url,
                echo=self.config.echo,
                echo_pool=self.config.echo_pool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                poolclass=pool_class,
                # Turkish optimization
                connect_args={
                    "server_settings": {
                        "application_name": "KIRO2_Backend",
                        "timezone": self.config.timezone,
                    }
                }
                if "postgresql" in self.config.database_url
                else {},
            )

            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # Set up monitoring
            if self.config.enable_monitoring:
                self._setup_monitoring()

            # Test connection
            health = await self.health_checker.check_connection(self.engine)
            if health["status"] != "healthy":
                raise Exception(f"Database health check failed: {health}")

            logger.info("Database manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise

    def _get_pool_class(self):
        """Get appropriate pool class based on strategy"""
        if self.config.pool_strategy == PoolStrategy.QUEUE_POOL:
            return QueuePool
        if self.config.pool_strategy == PoolStrategy.NULL_POOL:
            return NullPool
        if self.config.pool_strategy == PoolStrategy.STATIC_POOL:
            return StaticPool
        return QueuePool

    def _setup_monitoring(self):
        """Setup database monitoring events"""
        if not self.engine:
            return

        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Track query start time"""
            context._query_start_time = time.time()
            context._query_id = str(uuid.uuid4())

            # Create query metrics
            metrics = QueryMetrics(
                query_id=context._query_id,
                sql=statement,
                params=parameters if not executemany else None,
            )
            self.query_history.append(metrics)

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Track query completion"""
            end_time = time.time()
            duration = end_time - context._query_start_time

            # Update stats
            self.stats.queries_executed += 1
            self.stats.total_query_time += duration
            self.stats.avg_query_time = (
                self.stats.total_query_time / self.stats.queries_executed
            )

            # Check for slow queries
            if duration > self.config.slow_query_threshold:
                self.stats.slow_queries += 1
                logger.warning(
                    f"Slow query detected: {duration:.2f}s - {statement[:100]}..."
                )

            # Update query metrics
            if self.query_history:
                metrics = self.query_history[-1]
                if metrics.query_id == context._query_id:
                    metrics.complete(success=True, row_count=cursor.rowcount)

        @event.listens_for(self.engine.sync_engine, "handle_error")
        def handle_error(exception_context):
            """Track query errors"""
            self.stats.failed_queries += 1
            self.stats.last_error = str(exception_context.original_exception)

            # Update query metrics
            if self.query_history:
                metrics = self.query_history[-1]
                metrics.complete(
                    success=False, error=str(exception_context.original_exception)
                )

            logger.error(f"Database error: {exception_context.original_exception}")

    async def shutdown(self) -> None:
        """Cleanup database connections"""
        if self._monitoring_task:
            self._monitoring_task.cancel()

        if self.engine:
            await self.engine.dispose()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with proper error handling"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")

        retries = 0
        while retries < self.config.max_retries:
            try:
                async with self.session_factory() as session:
                    self.stats.active_connections += 1
                    try:
                        yield session
                        await session.commit()
                    except Exception:
                        await session.rollback()
                        raise
                    finally:
                        self.stats.active_connections -= 1
                    break

            except (DisconnectionError, OperationalError, TimeoutError) as e:
                retries += 1
                if retries >= self.config.max_retries:
                    logger.error(
                        f"Database connection failed after {retries} retries: {e}"
                    )
                    raise

                # Exponential backoff
                delay = self.config.retry_delay
                if self.config.exponential_backoff:
                    delay *= 2 ** (retries - 1)

                logger.warning(
                    f"Database connection retry {retries}/{self.config.max_retries} in {delay}s"
                )
                await asyncio.sleep(delay)

    @asynccontextmanager
    async def get_transaction(
        self, isolation_level: IsolationLevel | None = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with explicit transaction management"""
        async with self.get_session() as session:
            if isolation_level:
                await session.execute(
                    text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level.value}")
                )

            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise

    async def execute_query(self, query: str, params: dict | None = None) -> Any:
        """Execute raw SQL query"""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result

    async def execute_script(self, script: str) -> None:
        """Execute SQL script (multiple statements)"""
        statements = [stmt.strip() for stmt in script.split(";") if stmt.strip()]

        async with self.get_transaction() as session:
            for statement in statements:
                await session.execute(text(statement))

    async def create_tables(self, metadata: MetaData | None = None) -> None:
        """Create all tables from metadata"""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        target_metadata = metadata or Base.metadata

        async with self.engine.begin() as conn:
            await conn.run_sync(target_metadata.create_all)

        logger.info("Database tables created successfully")

    async def drop_tables(self, metadata: MetaData | None = None) -> None:
        """Drop all tables from metadata"""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        target_metadata = metadata or Base.metadata

        async with self.engine.begin() as conn:
            await conn.run_sync(target_metadata.drop_all)

        logger.info("Database tables dropped successfully")

    async def get_table_info(self, table_name: str) -> dict[str, Any]:
        """Get information about a specific table"""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        async with self.engine.connect() as conn:
            # Get table structure
            inspector = inspect(self.engine.sync_engine)
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)

            # Get row count
            count_result = await conn.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            row_count = count_result.scalar()

            return {
                "table_name": table_name,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys,
                "row_count": row_count,
            }

    async def optimize_database(self) -> dict[str, Any]:
        """Perform database optimization tasks"""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        optimization_results = {}

        try:
            async with self.get_session() as session:
                # PostgreSQL specific optimizations
                if "postgresql" in self.config.database_url:
                    # Analyze tables for query planner
                    await session.execute(text("ANALYZE"))
                    optimization_results["analyze"] = "completed"

                    # Vacuum to reclaim space
                    await session.execute(text("VACUUM"))
                    optimization_results["vacuum"] = "completed"

                    # Update statistics
                    await session.execute(
                        text(
                            "UPDATE pg_class SET reltuples = (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public')"
                        )
                    )
                    optimization_results["statistics_update"] = "completed"

                optimization_results["status"] = "success"
                optimization_results["timestamp"] = datetime.now().isoformat()

        except Exception as e:
            optimization_results["status"] = "failed"
            optimization_results["error"] = str(e)

        return optimization_results

    async def get_database_stats(self) -> dict[str, Any]:
        """Get comprehensive database statistics"""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        stats = {
            "connection_stats": {
                "total_connections": self.stats.total_connections,
                "active_connections": self.stats.active_connections,
                "idle_connections": self.stats.idle_connections,
            },
            "query_stats": {
                "queries_executed": self.stats.queries_executed,
                "failed_queries": self.stats.failed_queries,
                "slow_queries": self.stats.slow_queries,
                "avg_query_time": self.stats.avg_query_time,
                "error_rate": self.stats.error_rate,
            },
            "recent_queries": [
                {
                    "query_id": q.query_id,
                    "sql": q.sql[:100] + "..." if len(q.sql) > 100 else q.sql,
                    "duration": q.duration,
                    "success": q.success,
                    "timestamp": q.start_time.isoformat(),
                }
                for q in self.query_history[-10:]  # Last 10 queries
            ],
            "uptime": (datetime.now() - self.stats.uptime).total_seconds(),
            "timestamp": datetime.now().isoformat(),
        }

        # Add database-specific stats
        try:
            async with self.get_session() as session:
                if "postgresql" in self.config.database_url:
                    # PostgreSQL specific stats
                    result = await session.execute(
                        text(
                            """
                        SELECT 
                            count(*) as total_tables,
                            pg_size_pretty(pg_database_size(current_database())) as database_size
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """
                        )
                    )
                    row = result.fetchone()
                    if row:
                        stats["database_info"] = {
                            "total_tables": row[0],
                            "database_size": row[1],
                        }
        except Exception as e:
            stats["database_info_error"] = str(e)

        return stats

    async def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check"""
        if not self.engine:
            return {
                "status": "unhealthy",
                "error": "Database not initialized",
                "timestamp": datetime.now().isoformat(),
            }

        return await self.health_checker.check_connection(self.engine)

    # Migration support
    async def run_migration(self, migration_script: str) -> dict[str, Any]:
        """Run database migration script"""
        try:
            start_time = datetime.now()

            async with self.get_transaction() as session:
                # Split script into individual statements
                statements = [
                    stmt.strip() for stmt in migration_script.split(";") if stmt.strip()
                ]

                for statement in statements:
                    await session.execute(text(statement))

            duration = (datetime.now() - start_time).total_seconds()

            return {
                "status": "success",
                "statements_executed": len(statements),
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# Global instance
_db_manager: UnifiedDatabaseManager | None = None


async def get_db_manager() -> UnifiedDatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = UnifiedDatabaseManager()
        await _db_manager.initialize()
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (FastAPI dependency compatible)"""
    db_manager = await get_db_manager()
    async with db_manager.get_session() as session:
        yield session


# Backward compatibility aliases
DatabaseManager = UnifiedDatabaseManager
EnhancedDatabaseManager = UnifiedDatabaseManager
DatabaseOptimizer = UnifiedDatabaseManager
DatabaseMonitoring = UnifiedDatabaseManager
