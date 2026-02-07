"""
Enhanced Database Pattern Consolidation
Unified database connection management, query patterns, and transaction handling

Bu dosya mevcut database.py'yi genişleterek kapsamlı database pattern consolidation sağlar:
- Gelişmiş connection management ve pooling
- Query builder ve ORM patterns
- Transaction management sistemi
- Database migration framework
- Connection pooling optimizasyonu
- Performance monitoring
- Error handling ve recovery
"""

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import event, text
from sqlalchemy.exc import DisconnectionError, OperationalError, TimeoutError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from .config import settings
from .error_context import async_error_context
from .error_monitoring import log_error
from .exceptions import DatabaseError, ErrorSeverity

# Type variables for generic repository patterns
T = TypeVar("T")
PK = TypeVar("PK")

# Configure logging
logger = logging.getLogger(__name__)

# Base class for all models (enhanced version)
Base = declarative_base()


# ==================== DATABASE CONNECTION MANAGEMENT ====================


class ConnectionPoolConfig:
    """Enhanced connection pool configuration"""

    def __init__(
        self,
        pool_size: int = 30,
        max_overflow: int = 50,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        pool_reset_on_return: str = "commit",
        echo: bool = False,
        echo_pool: bool = False,
    ):
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.pool_reset_on_return = pool_reset_on_return
        self.echo = echo
        self.echo_pool = echo_pool


class DatabaseMetrics:
    """Database performance and health metrics"""

    def __init__(self):
        self.connections_created = 0
        self.connections_closed = 0
        self.queries_executed = 0
        self.transactions_started = 0
        self.transactions_committed = 0
        self.transactions_rolled_back = 0
        self.slow_queries: list[dict[str, Any]] = []
        self.connection_errors: list[dict[str, Any]] = []
        self.query_times: list[float] = []
        self.last_reset = datetime.now()

    def record_query(self, query: str, duration: float, success: bool = True):
        """Record query execution metrics"""
        self.queries_executed += 1
        self.query_times.append(duration)

        # Keep only last 1000 query times for memory efficiency
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]

        # Record slow queries (over 1 second)
        if duration > 1.0:
            self.slow_queries.append(
                {
                    "query": query[:200] + "..." if len(query) > 200 else query,
                    "duration": duration,
                    "timestamp": datetime.now(),
                    "success": success,
                }
            )

            # Keep only last 100 slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]

    def record_connection_error(self, error: Exception, context: str):
        """Record connection error"""
        self.connection_errors.append(
            {
                "error": str(error),
                "error_type": type(error).__name__,
                "context": context,
                "timestamp": datetime.now(),
            }
        )

        # Keep only last 100 errors
        if len(self.connection_errors) > 100:
            self.connection_errors = self.connection_errors[-100:]

    def get_average_query_time(self) -> float:
        """Get average query execution time"""
        if not self.query_times:
            return 0.0
        return sum(self.query_times) / len(self.query_times)

    def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive health status"""
        now = datetime.now()
        uptime = (now - self.last_reset).total_seconds()

        return {
            "uptime_seconds": uptime,
            "connections_created": self.connections_created,
            "connections_closed": self.connections_closed,
            "active_connections": self.connections_created - self.connections_closed,
            "queries_executed": self.queries_executed,
            "average_query_time": self.get_average_query_time(),
            "slow_queries_count": len(self.slow_queries),
            "connection_errors_count": len(self.connection_errors),
            "transactions_started": self.transactions_started,
            "transactions_committed": self.transactions_committed,
            "transactions_rolled_back": self.transactions_rolled_back,
            "transaction_success_rate": (
                self.transactions_committed / self.transactions_started
                if self.transactions_started > 0
                else 1.0
            ),
        }


class EnhancedDatabaseManager:
    """Enhanced database manager with comprehensive features"""

    def __init__(self, config: ConnectionPoolConfig | None = None):
        self.config = config or ConnectionPoolConfig()
        self.engine: AsyncEngine | None = None
        self.async_session_maker: async_sessionmaker | None = None
        self.sync_session_maker: sessionmaker | None = None
        self._initialized = False
        self.metrics = DatabaseMetrics()
        self._connection_callbacks: list[Callable] = []
        self._query_callbacks: list[Callable] = []
        self._health_check_interval = 300  # 5 minutes
        self._last_health_check = datetime.now()

        # Migration tracking
        self._migration_history: list[dict[str, Any]] = []

        # Connection pooling optimization
        self._pool_optimization_enabled = True
        self._adaptive_pool_sizing = True

    async def initialize(self, database_url: str | None = None) -> None:
        """Enhanced database initialization with comprehensive setup"""

        if self._initialized:
            logger.warning("Enhanced database manager already initialized")
            return

        db_url = database_url or settings.database_url

        async with async_error_context(
            operation_name="initialize_enhanced_database",
            entity_type="database",
            business_operation="database_initialization",
        ) as ctx:
            try:
                ctx.add_annotation("Starting enhanced database initialization")

                # Create enhanced engine with optimized settings
                connect_args = {}
                if "postgresql" in db_url:
                    connect_args = {
                        "server_settings": {
                            "application_name": "turkiye_sinav_platform_enhanced",
                            "client_encoding": "utf8",
                            "timezone": "UTC",
                            "statement_timeout": "300000",  # 5 minutes
                            "idle_in_transaction_session_timeout": "600000",  # 10 minutes
                        },
                        "command_timeout": 60,
                    }

                # Configure connection pooling
                poolclass = QueuePool if self.config.pool_size > 0 else NullPool

                self.engine = create_async_engine(
                    db_url,
                    echo=self.config.echo,
                    echo_pool=self.config.echo_pool,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=self.config.pool_recycle,
                    pool_pre_ping=self.config.pool_pre_ping,
                    pool_reset_on_return=self.config.pool_reset_on_return,
                    poolclass=poolclass,
                    connect_args=connect_args,
                    # Enhanced execution options
                    execution_options={
                        "isolation_level": "READ_COMMITTED",
                        "autocommit": False,
                    },
                )

                # Create session makers
                self.async_session_maker = async_sessionmaker(
                    bind=self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=True,
                    autocommit=False,
                )

                # Setup event listeners for monitoring
                self._setup_event_listeners()

                # Test connection
                await self._comprehensive_connection_test()

                # Initialize migration tracking
                await self._initialize_migration_tracking()

                self._initialized = True
                ctx.add_annotation(
                    "Enhanced database initialization completed successfully"
                )
                logger.info("Enhanced database manager initialized successfully")

            except Exception as e:
                ctx.add_annotation(f"Database initialization failed: {e!s}")
                self.metrics.record_connection_error(e, "initialization")
                logger.error(f"Enhanced database initialization failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.CRITICAL)
                raise DatabaseError(
                    message="Enhanced database initialization failed",
                    operation="initialize",
                    details={"original_error": str(e)},
                )

    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring"""

        @event.listens_for(self.engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Handle new database connections"""
            self.metrics.connections_created += 1
            logger.debug("Database connection established")

            # Execute connection callbacks
            for callback in self._connection_callbacks:
                try:
                    callback(dbapi_connection, connection_record)
                except Exception as e:
                    logger.error(f"Connection callback error: {e}")

        @event.listens_for(self.engine.sync_engine, "close")
        def on_close(dbapi_connection, connection_record):
            """Handle connection closures"""
            self.metrics.connections_closed += 1
            logger.debug("Database connection closed")

        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Track query start time"""
            context._query_start_time = time.time()

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Track query completion and metrics"""
            if hasattr(context, "_query_start_time"):
                duration = time.time() - context._query_start_time
                self.metrics.record_query(statement, duration, True)

                # Execute query callbacks
                for callback in self._query_callbacks:
                    try:
                        callback(statement, parameters, duration, True)
                    except Exception as e:
                        logger.error(f"Query callback error: {e}")

    async def _comprehensive_connection_test(self) -> None:
        """Comprehensive connection testing"""

        async with async_error_context(
            operation_name="database_connection_test",
            business_operation="connection_test",
        ) as ctx:
            try:
                # Basic connectivity test
                async with self.engine.begin() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    assert result.scalar() == 1
                    ctx.add_annotation("Basic connectivity test passed")

                # Database version and features test
                async with self.engine.begin() as conn:
                    # Get database version
                    version_result = await conn.execute(text("SELECT version()"))
                    version = version_result.scalar()
                    ctx.add_annotation(f"Database version: {version[:100]}...")

                    # Test transaction support
                    await conn.execute(text("BEGIN"))
                    await conn.execute(text("SELECT 1"))
                    await conn.execute(text("COMMIT"))
                    ctx.add_annotation("Transaction support test passed")

                # Connection pool test
                pool_status = self._get_pool_status()
                ctx.add_annotation(f"Connection pool status: {pool_status}")

                logger.info("Comprehensive connection test successful")

            except Exception as e:
                ctx.add_annotation(f"Connection test failed: {e!s}")
                self.metrics.record_connection_error(e, "connection_test")
                logger.error(f"Database connection test failed: {e!s}")
                raise

    async def _initialize_migration_tracking(self):
        """Initialize database migration tracking"""

        async with async_error_context(
            operation_name="initialize_migration_tracking",
            business_operation="migration_setup",
        ) as ctx:
            try:
                async with self.engine.begin() as conn:
                    # Create migrations table if it doesn't exist
                    await conn.execute(
                        text(
                            """
                        CREATE TABLE IF NOT EXISTS alembic_version_enhanced (
                            version_num VARCHAR(32) NOT NULL,
                            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            applied_by VARCHAR(100),
                            description TEXT,
                            CONSTRAINT pk_alembic_version_enhanced PRIMARY KEY (version_num)
                        )
                    """
                        )
                    )

                    # Check current migration status
                    result = await conn.execute(
                        text("SELECT COUNT(*) FROM alembic_version_enhanced")
                    )
                    migration_count = result.scalar()

                    ctx.add_annotation(
                        f"Migration tracking initialized. Current migrations: {migration_count}"
                    )
                    logger.info(
                        f"Migration tracking initialized with {migration_count} migrations"
                    )

            except Exception as e:
                ctx.add_annotation(f"Migration tracking initialization failed: {e!s}")
                logger.error(f"Migration tracking initialization failed: {e!s}")
                # Don't raise - this is not critical for basic operation

    def _get_pool_status(self) -> dict[str, Any]:
        """Get detailed connection pool status"""

        if not self.engine or not hasattr(self.engine, "pool"):
            return {"status": "no_pool"}

        pool = self.engine.pool

        return {
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
            "invalid": getattr(pool, "invalid", 0),
            "pool_class": type(pool).__name__,
        }

    @asynccontextmanager
    async def get_session(
        self, read_only: bool = False, isolation_level: str | None = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """Enhanced session context manager with advanced options"""

        if not self._initialized:
            await self.initialize()

        session_id = str(uuid.uuid4())[:8]

        async with async_error_context(
            operation_name="database_session",
            entity_id=session_id,
            business_operation="session_management",
        ) as ctx:
            ctx.add_annotation(f"Creating database session {session_id}")
            ctx.tags.update(
                {
                    "session_id": session_id,
                    "read_only": str(read_only),
                    "isolation_level": isolation_level or "default",
                }
            )

            session = self.async_session_maker()

            try:
                # Configure session options
                if isolation_level:
                    await session.execute(
                        text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
                    )

                if read_only:
                    await session.execute(text("SET TRANSACTION READ ONLY"))

                start_time = time.time()
                yield session

                # Auto-commit unless read-only
                if not read_only:
                    await session.commit()
                    self.metrics.transactions_committed += 1

                duration = time.time() - start_time
                ctx.add_annotation(
                    f"Session {session_id} completed successfully in {duration:.3f}s"
                )

            except Exception as e:
                duration = time.time() - start_time
                ctx.add_annotation(
                    f"Session {session_id} failed after {duration:.3f}s: {e!s}"
                )

                try:
                    await session.rollback()
                    self.metrics.transactions_rolled_back += 1
                except Exception as rollback_error:
                    logger.error(f"Session rollback failed: {rollback_error}")

                # Log the error with session context
                await log_error(e, ctx.to_dict(), ErrorSeverity.MEDIUM)
                raise DatabaseError(
                    message=f"Database session {session_id} failed",
                    operation="session_management",
                    details={
                        "session_id": session_id,
                        "duration": duration,
                        "original_error": str(e),
                    },
                )

            finally:
                await session.close()
                ctx.add_annotation(f"Session {session_id} closed")

    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        **kwargs,
    ) -> Any:
        """Execute database operation with retry logic"""

        async with async_error_context(
            operation_name="database_operation_with_retry",
            business_operation="retry_execution",
        ) as ctx:
            ctx.tags.update(
                {
                    "max_retries": str(max_retries),
                    "operation": operation.__name__
                    if hasattr(operation, "__name__")
                    else str(operation),
                }
            )

            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    ctx.add_annotation(f"Attempt {attempt + 1}/{max_retries + 1}")

                    result = await operation(*args, **kwargs)

                    if attempt > 0:
                        ctx.add_annotation(
                            f"Operation succeeded on attempt {attempt + 1}"
                        )

                    return result

                except (DisconnectionError, OperationalError, TimeoutError) as e:
                    last_error = e
                    self.metrics.record_connection_error(
                        e, f"retry_attempt_{attempt + 1}"
                    )

                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (2**attempt), max_delay)

                        ctx.add_annotation(
                            f"Retryable error on attempt {attempt + 1}, waiting {delay}s"
                        )
                        logger.warning(
                            f"Database operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}"
                        )

                        await asyncio.sleep(delay)
                    else:
                        ctx.add_annotation("All retry attempts failed")
                        break

                except Exception as e:
                    # Non-retryable error
                    ctx.add_annotation(f"Non-retryable error: {type(e).__name__}")
                    await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                    raise

            # All retries exhausted
            ctx.add_annotation(f"All {max_retries + 1} attempts failed")
            await log_error(last_error, ctx.to_dict(), ErrorSeverity.HIGH)

            raise DatabaseError(
                message="Database operation failed after all retry attempts",
                operation="retry_execution",
                details={"attempts": max_retries + 1, "last_error": str(last_error)},
            )

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check"""

        try:
            # Basic connectivity
            async with self.get_session(read_only=True) as session:
                await session.execute(text("SELECT 1"))

            # Get metrics and pool status
            metrics = self.metrics.get_health_status()
            pool_status = self._get_pool_status()

            return {
                "status": "healthy",
                "healthy": True,
                "timestamp": datetime.now(),
                "metrics": metrics,
                "pool_status": pool_status,
                "configuration": {
                    "pool_size": self.config.pool_size,
                    "max_overflow": self.config.max_overflow,
                    "pool_timeout": self.config.pool_timeout,
                },
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.metrics.record_connection_error(e, "health_check")

            return {
                "status": "unhealthy",
                "healthy": False,
                "timestamp": datetime.now(),
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def close(self) -> None:
        """Enhanced cleanup and connection closing"""

        if self.engine:
            logger.info("Closing enhanced database connections...")

            # Log final metrics
            final_metrics = self.metrics.get_health_status()
            logger.info(f"Final database metrics: {final_metrics}")

            await self.engine.dispose()
            logger.info("Enhanced database connections closed successfully")

        self._initialized = False


# Global enhanced database manager instance
enhanced_db_manager = EnhancedDatabaseManager()


# ==================== UTILITY FUNCTIONS ====================


async def init_enhanced_database(database_url: str | None = None):
    """Initialize enhanced database manager"""
    await enhanced_db_manager.initialize(database_url)


async def close_enhanced_database():
    """Close enhanced database manager"""
    await enhanced_db_manager.close()


async def get_enhanced_db_session(**kwargs):
    """Get enhanced database session"""
    async with enhanced_db_manager.get_session(**kwargs) as session:
        yield session


def get_enhanced_database_health():
    """Get enhanced database health status"""
    return enhanced_db_manager.health_check()


# FastAPI dependency for enhanced database sessions
async def get_enhanced_db_dependency(
    read_only: bool = False, isolation_level: str | None = None
) -> AsyncGenerator[AsyncSession, None]:
    """Enhanced FastAPI dependency for database sessions"""
    async with enhanced_db_manager.get_session(
        read_only=read_only, isolation_level=isolation_level
    ) as session:
        yield session
