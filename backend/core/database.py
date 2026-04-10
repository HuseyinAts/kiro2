"""
PostgreSQL Database Connection ve Session Yönetimi
Async SQLAlchemy + asyncpg driver ile optimized connection pooling

OPTIMIZATION: asyncpg driver kullanımı ile performans artışı
- psycopg2 yerine asyncpg (3-5x daha hızlı)
- Connection pooling: pool_size=50, max_overflow=100 (100K+ users)
- Health checks: pool_pre_ping=True
- Connection recycling: 3600s (1 saat)

Requirements: REQ-1.2
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from .config import settings

# SPRINT 1: Enable query monitoring (slow query logging, Prometheus metrics, N+1 detection)
try:
    from .query_monitor_config import setup_query_monitoring
    # Query monitoring auto-initializes via SQLAlchemy event listeners
except ImportError:
    logging.warning("Query monitoring module not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Base from models to avoid circular imports
try:
    from models.base import Base
except ImportError:
    # Fallback for when models package is not available
    Base = declarative_base()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session generator
    SECURITY FIX: Real database session (removed mock implementation)

    TESTING MODE: Returns mock session when TESTING=true
    """
    import os

    # Initialize database manager if not already done
    if not db_manager._initialized:
        await db_manager.initialize()

    # TESTING MODE: Return mock session
    if os.environ.get("TESTING") == "true" and db_manager.async_session_maker is None:
        from unittest.mock import AsyncMock

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        yield mock_session
        return

    # Use real database session
    # NOTE: Session lifecycle (commit/rollback/close) is managed by
    # db_manager.get_session() context manager. Do NOT add commit/close here
    # to avoid double-commit on an already-closed session.
    async with db_manager.get_session() as session:
        yield session


class DatabaseManager:
    """Database connection ve session yöneticisi."""

    def __init__(self) -> None:
        """Initialize database manager."""
        self.engine: AsyncEngine | None = None
        self.async_session_maker: async_sessionmaker[AsyncSession] | None = None
        self._initialized: bool = False

    async def initialize(self) -> None:
        """
        Database bağlantısını başlat.

        OPTIMIZATION: asyncpg driver configuration (FIX: Updated for 100K+ users)
        - pool_size=50: Base connection pool size (from settings.db_pool_size)
        - max_overflow=100: Additional connections during peak load (from settings.db_max_overflow)
        - pool_pre_ping=True: Health check before each connection use
        - pool_recycle=3600: Recycle connections after 1 hour
        - pool_timeout=30: Wait up to 30s for connection

        Requirements: REQ-1.2
        """
        if self._initialized:
            logger.warning("Database already initialized")
            return

        # TESTING MODE: Skip initialization if TESTING=true (smoke tests)
        import os

        if os.environ.get("TESTING") == "true":
            logger.info("⚠️  TESTING mode: Skipping database initialization")
            self._initialized = True
            return

        try:
            # Ensure asyncpg driver is used for PostgreSQL
            database_url = settings.database_url
            if "postgresql://" in database_url:
                # Replace psycopg2 with asyncpg driver
                database_url = database_url.replace(
                    "postgresql://", "postgresql+asyncpg://"
                )
                logger.info("Using asyncpg driver for PostgreSQL")
            elif "postgresql+psycopg2://" in database_url:
                database_url = database_url.replace(
                    "postgresql+psycopg2://", "postgresql+asyncpg://"
                )
                logger.info("Replaced psycopg2 with asyncpg driver")

            # Engine oluştur
            connect_args = {}
            if "postgresql" in database_url:
                connect_args = {
                    "server_settings": {
                        "application_name": "turkiye_sinav_platform",
                        "client_encoding": "utf8",
                    },
                    # asyncpg specific settings
                    "command_timeout": 60.0,  # Command timeout (seconds)
                    "timeout": 30.0,  # Connection timeout (seconds)
                }

            # Pool settings only for PostgreSQL (SQLite doesn't support pooling)
            engine_args = {
                "echo": settings.database_echo,
                "connect_args": connect_args,
            }

            if "postgresql" in database_url:
                # PERFORMANCE OPTIMIZED: Pool settings for high concurrency (100K+ users)
                # FIX: Updated defaults to match config.py - pool_size=50, max_overflow=100
                pool_size = getattr(
                    settings, "db_pool_size", 50
                )  # Use config or default (50)
                max_overflow = getattr(
                    settings, "db_max_overflow", 100
                )  # Use config or default (100)

                engine_args.update(
                    {
                        "poolclass": AsyncAdaptedQueuePool,  # Async-compatible pool for async engine
                        "pool_pre_ping": True,  # Connection health check before each use
                        "pool_size": pool_size,  # Base pool size
                        "max_overflow": max_overflow,  # Additional connections during peak
                        "pool_recycle": 600,  # Recycle at PostgreSQL default idle timeout (600s)
                        # 300s was < PostgreSQL idle timeout → "server closed connection" errors
                        "pool_timeout": 30,  # Wait up to 30s for connection from pool
                    }
                )
                logger.info(
                    f"PostgreSQL asyncpg pool configured: size={pool_size}, overflow={max_overflow}"
                )
            else:
                # SQLite: Use NullPool (no pooling for file-based DB)
                engine_args["poolclass"] = NullPool

            self.engine = create_async_engine(database_url, **engine_args)

            # Add connection event listeners for monitoring
            @event.listens_for(self.engine.sync_engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                """Log new connections"""
                logger.debug("New database connection established")

            @event.listens_for(self.engine.sync_engine, "close")
            def receive_close(dbapi_conn, connection_record):
                """Log connection closures"""
                logger.debug("Database connection closed")

            # Session maker oluştur
            self.async_session_maker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )

            # Connection test (skip in testing mode if no engine)
            if self.engine is not None:
                await self._test_connection()

            self._initialized = True
            logger.info("Database connection initialized successfully with asyncpg")

        except Exception as e:
            logger.error(f"Database initialization failed: {e!s}")
            raise

    async def _test_connection(self) -> None:
        """Database bağlantısını test et"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
                logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e!s}")
            raise

    async def close(self) -> None:
        """Database bağlantısını kapat"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
        self._initialized = False

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Async context manager ile session al"""
        if not self._initialized:
            await self.initialize()

        # TESTING MODE: Return mock session if no session maker
        import os

        if os.environ.get("TESTING") == "true" and self.async_session_maker is None:
            # Create a minimal mock session for testing
            from unittest.mock import AsyncMock

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            yield mock_session
            return

        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e!s}")
                raise
            finally:
                await session.close()

    async def get_session_direct(self) -> AsyncSession:
        """Direct session al (manuel yönetim için)"""
        if not self._initialized:
            await self.initialize()

        return self.async_session_maker()

    async def create_tables(self) -> None:
        """Tüm tabloları oluştur"""
        if not self._initialized:
            await self.initialize()

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Table creation failed: {e!s}")
            raise

    async def drop_tables(self) -> None:
        """Tüm tabloları sil (dikkatli kullan!)"""
        if not self._initialized:
            await self.initialize()

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Table drop failed: {e!s}")
            raise

    async def health_check(self) -> dict:
        """Database sağlık kontrolü"""
        try:
            if not self._initialized:
                return {"status": "not_initialized", "healthy": False}

            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    return {
                        "status": "healthy",
                        "healthy": True,
                        "pool_size": getattr(self.engine.pool, "size", lambda: "N/A")(),
                        "checked_out": getattr(
                            self.engine.pool, "checkedout", lambda: "N/A"
                        )(),
                        "overflow": getattr(
                            self.engine.pool, "overflow", lambda: "N/A"
                        )(),
                        "checked_in": getattr(
                            self.engine.pool, "checkedin", lambda: "N/A"
                        )(),
                    }
                return {"status": "unhealthy", "healthy": False}

        except Exception as e:
            logger.error(f"Database health check failed: {e!s}")
            return {"status": "error", "healthy": False, "error": str(e)}


# Global database manager instance
db_manager = DatabaseManager()

# Connection event listeners will be added after engine creation


# Dependency injection için session getter
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency injection için session getter"""
    async with db_manager.get_session() as session:
        yield session


# Repository base class
class BaseRepository:
    """Tüm repository'ler için base class"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self):
        """Transaction commit"""
        try:
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Repository commit failed: {e!s}")
            raise

    async def rollback(self):
        """Transaction rollback"""
        await self.session.rollback()

    async def refresh(self, instance):
        """Instance'ı refresh et"""
        await self.session.refresh(instance)

    async def flush(self):
        """Session flush"""
        await self.session.flush()


# Utility functions
async def init_database():
    """Database'i başlat"""
    await db_manager.initialize()


async def close_database():
    """Database'i kapat"""
    await db_manager.close()


async def create_all_tables():
    """Tüm tabloları oluştur"""
    await db_manager.create_tables()


async def get_database_health():
    """Database sağlık durumunu al"""
    return await db_manager.health_check()


# Context manager for manual session management
@asynccontextmanager
async def get_db_session_context():
    """Manuel session yönetimi için context manager"""
    async with db_manager.get_session() as session:
        yield session


# Sync version for compatibility
#
# DEPRECATED — DO NOT USE IN NEW CODE.
#
# This yields a synchronous sqlalchemy.orm.Session. FastAPI's DI resolver
# does NOT type-check the annotation against what the dependency yields,
# so a handler declared as `db: AsyncSession = Depends(get_db)` silently
# gets a sync Session injected. Any subsequent `await db.execute(...)`
# raises sqlalchemy.exc.MissingGreenlet at runtime — a 100% 500 factory.
#
# Correct imports:
#   - Async handlers: `from core.database import get_async_session`
#     and `db: AsyncSession = Depends(get_async_session)`
#   - Manual session blocks: `async with get_db_session_context() as s:`
#
# Session 137 AST linter (`backend/scripts/audit_db_dependency.py`)
# blocks new regressions at CI. The 98 remaining MEDIUM type-lie call
# sites (diary_api, university_info_routes, department_info_routes,
# preference_simulation_routes, sequential_reasoning_api) still work
# today because none of them `await db.*`, but they are a latent hazard.
# See `docs/audits/2026-04-10_db-dependency-baseline.md`.
def get_db():
    """Sync compatibility shim — DEPRECATED, use get_async_session instead.

    Emits a DeprecationWarning on every call so new usages surface in
    test runs without breaking the 98 existing legacy call sites.
    """
    import warnings

    warnings.warn(
        "core.database.get_db is a sync shim that yields a sync "
        "sqlalchemy.orm.Session. Any `db: AsyncSession = Depends(get_db)` "
        "with an `await db.*` call will raise MissingGreenlet. Use "
        "`get_async_session` for FastAPI handlers or "
        "`get_db_session_context()` for manual session blocks.",
        DeprecationWarning,
        stacklevel=2,
    )

    from sqlalchemy.orm import sessionmaker

    if db_manager.engine is None:
        raise RuntimeError(
            "Database not initialized — call db_manager.initialize() first"
        )
    sync_engine = db_manager.engine.sync_engine
    SyncSession = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = SyncSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Redis client dependency for FastAPI
async def get_redis_client():
    """FastAPI dependency injection for Redis client"""
    from core.cache import cache_manager

    # Ensure cache manager is initialized
    if not cache_manager._initialized:
        await cache_manager.initialize()

    # Return the Redis client (can be None if Redis is not available)
    return cache_manager.redis
