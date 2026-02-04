"""
PostgreSQL Database Connection ve Session Yönetimi
Async SQLAlchemy ile optimized connection pooling
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

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
    """
    # Initialize database manager if not already done
    if not db_manager._initialized:
        await db_manager.initialize()

    # Use real database session
    async with db_manager.get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


class DatabaseManager:
    """Database connection ve session yöneticisi"""

    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.async_session_maker: async_sessionmaker | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Database bağlantısını başlat"""
        if self._initialized:
            logger.warning("Database already initialized")
            return

        try:
            # Engine oluştur
            connect_args = {}
            if "postgresql" in settings.database_url:
                connect_args = {
                    "server_settings": {
                        "application_name": "turkiye_sinav_platform",
                        "client_encoding": "utf8",
                    }
                }

            # Pool settings only for PostgreSQL (SQLite doesn't support pooling)
            engine_args = {
                "echo": settings.database_echo,
                "connect_args": connect_args,
            }

            if "postgresql" in settings.database_url:
                # PERFORMANCE OPTIMIZED: Pool settings for high concurrency (fixes 74x slowdown issue)
                pool_size = (
                    int(settings.db_pool_size)
                    if hasattr(settings, "db_pool_size")
                    else 50
                )
                max_overflow = (
                    int(settings.db_max_overflow)
                    if hasattr(settings, "db_max_overflow")
                    else 100
                )

                engine_args.update(
                    {
                        "pool_pre_ping": True,  # Connection health check before each use
                        "pool_size": pool_size,  # Base pool size (default: 50 for concurrent load)
                        "max_overflow": max_overflow,  # Additional connections during peak (default: 100)
                        "pool_recycle": 3600,  # Recycle connections after 1 hour (prevents stale connections)
                        "pool_timeout": 30,  # Wait up to 30s for connection from pool
                    }
                )
                logger.info(
                    f"PostgreSQL pool configured: size={pool_size}, overflow={max_overflow}"
                )

            self.engine = create_async_engine(settings.database_url, **engine_args)

            # Session maker oluştur
            self.async_session_maker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )

            # Connection test
            await self._test_connection()

            self._initialized = True
            logger.info("Database connection initialized successfully")

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
                        "pool_size": self.engine.pool.size(),
                        "checked_out": self.engine.pool.checkedout(),
                        "overflow": self.engine.pool.overflow(),
                        "checked_in": self.engine.pool.checkedin(),
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
def get_db():
    """Sync compatibility function"""
    return db_manager


# Redis client dependency for FastAPI
async def get_redis_client():
    """FastAPI dependency injection for Redis client"""
    from core.cache import cache_manager

    # Ensure cache manager is initialized
    if not cache_manager._initialized:
        await cache_manager.initialize()

    # Return the Redis client (can be None if Redis is not available)
    return cache_manager.redis
