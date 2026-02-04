"""
Database Connection and Session Management
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from models.base import Base

logger = logging.getLogger(__name__)

# Database URL'lerini environment'tan al
if os.getenv("TESTING") == "true":
    # Test environment - use SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./test_db.sqlite"
    SYNC_DATABASE_URL = "sqlite:///./test_db.sqlite"
else:
    # Production environment - use PostgreSQL
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://teknofest:[REDACTED_DB_PASSWORD]@localhost:5432/teknofest_db",
    )
    SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Async Engine (Ana uygulama için)
if os.getenv("TESTING") == "true" or "sqlite" in DATABASE_URL:
    # SQLite doesn't support pool_size and max_overflow
    async_engine = create_async_engine(
        DATABASE_URL,
        echo=False,
    )
else:
    # PostgreSQL with connection pooling
    async_engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # SQL loglarını görmek için True yapabilirsiniz
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,  # 1 saat
    )

# Sync Engine (Migration ve admin işlemleri için)
if os.getenv("TESTING") == "true" or "sqlite" in SYNC_DATABASE_URL:
    # SQLite doesn't support pool_size and max_overflow
    sync_engine = create_engine(
        SYNC_DATABASE_URL,
        echo=False,
    )
else:
    # PostgreSQL with connection pooling
    sync_engine = create_engine(
        SYNC_DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Session makers
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


class DatabaseManager:
    """Database yönetim sınıfı"""

    def __init__(self):
        self.async_engine = async_engine
        self.sync_engine = sync_engine
        self.async_session_factory = AsyncSessionLocal
        self.sync_session_factory = SessionLocal

    async def create_tables(self):
        """Tüm tabloları oluştur"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("[CHECK] Database tabloları başarıyla oluşturuldu")
        except Exception as e:
            logger.error(f"[X] Database tablo oluşturma hatası: {str(e)}")
            raise

    async def drop_tables(self):
        """Tüm tabloları sil (dikkatli kullanın!)"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("⚠️ Database tabloları silindi")
        except Exception as e:
            logger.error(f"[X] Database tablo silme hatası: {str(e)}")
            raise

    def create_tables_sync(self):
        """Sync olarak tabloları oluştur (migration için)"""
        try:
            Base.metadata.create_all(bind=self.sync_engine)
            logger.info("[CHECK] Database tabloları (sync) başarıyla oluşturuldu")
        except Exception as e:
            logger.error(f"[X] Database tablo oluşturma (sync) hatası: {str(e)}")
            raise

    async def check_connection(self) -> bool:
        """Database bağlantısını kontrol et"""
        try:
            from sqlalchemy import text

            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("[CHECK] Database bağlantısı başarılı")
            return True
        except Exception as e:
            logger.error(f"[X] Database bağlantı hatası: {str(e)}")
            return False

    async def get_table_info(self) -> dict:
        """Tablo bilgilerini getir"""
        try:
            from sqlalchemy import text

            async with self.async_engine.begin() as conn:
                # Tablo sayısını al
                result = await conn.execute(
                    text(
                        """
                    SELECT COUNT(*) as table_count 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                    )
                )
                table_count = result.scalar()

                # Tablo isimlerini al
                result = await conn.execute(
                    text(
                        """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """
                    )
                )
                table_names = [row[0] for row in result.fetchall()]

                return {
                    "table_count": table_count,
                    "table_names": table_names,
                    "status": "connected",
                }
        except Exception as e:
            logger.error(f"[X] Tablo bilgisi alma hatası: {str(e)}")
            return {
                "table_count": 0,
                "table_names": [],
                "status": "error",
                "error": str(e),
            }


# Global database manager instance
db_manager = DatabaseManager()


# Dependency injection için async session getter
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency injection için async session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"[X] Database session hatası: {str(e)}")
            raise
        finally:
            await session.close()


# Context manager için async session
@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager ile async session kullanımı"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"[X] Database session context hatası: {str(e)}")
            raise
        finally:
            await session.close()


# Sync session getter (migration ve admin işlemleri için)
def get_sync_session() -> Session:
    """Sync session oluştur"""
    return SessionLocal()


# Context manager için sync session
@asynccontextmanager
async def get_sync_session_context() -> Session:
    """Context manager ile sync session kullanımı"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"[X] Sync database session context hatası: {str(e)}")
        raise
    finally:
        session.close()


# Database initialization
async def init_database():
    """Database'i başlat ve tabloları oluştur"""
    logger.info("[ROCKET] Database başlatılıyor...")

    # Bağlantıyı kontrol et
    if not await db_manager.check_connection():
        raise Exception("Database bağlantısı kurulamadı")

    # Tabloları oluştur
    await db_manager.create_tables()

    # Tablo bilgilerini logla
    table_info = await db_manager.get_table_info()
    logger.info(
        f"[CHART] Database hazır: {table_info['table_count']} tablo oluşturuldu"
    )
    logger.info(f"[CLIPBOARD] Tablolar: {', '.join(table_info['table_names'])}")


# Database cleanup
async def cleanup_database():
    """Database bağlantılarını temizle"""
    logger.info("🧹 Database bağlantıları temizleniyor...")

    try:
        await async_engine.dispose()
        sync_engine.dispose()
        logger.info("[CHECK] Database bağlantıları temizlendi")
    except Exception as e:
        logger.error(f"[X] Database temizleme hatası: {str(e)}")


# Health check
async def database_health_check() -> dict:
    """Database sağlık kontrolü"""
    try:
        connection_ok = await db_manager.check_connection()
        table_info = await db_manager.get_table_info()

        return {
            "status": "healthy" if connection_ok else "unhealthy",
            "connection": connection_ok,
            "tables": table_info["table_count"],
            "engine": "PostgreSQL + AsyncPG",
            "pool_size": async_engine.pool.size()
            if hasattr(async_engine.pool, "size")
            else 0,
            "checked_out": async_engine.pool.checkedout()
            if hasattr(async_engine.pool, "checkedout")
            else 0,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connection": False,
            "error": str(e),
            "engine": "PostgreSQL + AsyncPG",
        }
