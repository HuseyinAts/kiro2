"""
KIRO2 Database Optimization Module
PostgreSQL performance optimization for Turkish content
"""

import logging
import re
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Veritabanı sorgu optimizasyon yöneticisi"""

    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 saniye

    def log_query_performance(self, query_name: str, execution_time: float, query: str):
        """Sorgu performansını logla"""
        if query_name not in self.query_stats:
            self.query_stats[query_name] = {
                "total_executions": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "max_time": 0.0,
                "slow_queries": 0,
            }

        stats = self.query_stats[query_name]
        stats["total_executions"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["total_executions"]
        stats["max_time"] = max(stats["max_time"], execution_time)

        if execution_time > self.slow_query_threshold:
            stats["slow_queries"] += 1
            logger.warning(
                f"Yavaş sorgu tespit edildi: {query_name} - {execution_time:.3f}s\n"
                f"Query: {query[:200]}..."
            )

        logger.debug(f"Query performance: {query_name} - {execution_time:.3f}s")

    def get_performance_stats(self) -> dict[str, Any]:
        """Performans istatistiklerini al"""
        return self.query_stats.copy()


# Global optimizer instance
query_optimizer = QueryOptimizer()


def monitor_query_performance(query_name: str):
    """Sorgu performansını izleyen decorator"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Query string'i almaya çalış
                query_str = str(kwargs.get("query", "Unknown query"))

                query_optimizer.log_query_performance(
                    query_name, execution_time, query_str
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Query error in {query_name}: {e!s} (took {execution_time:.3f}s)"
                )
                raise

        return wrapper

    return decorator


class OptimizedRepository:
    """Optimize edilmiş repository base class"""

    def __init__(self, session: AsyncSession):
        self.session = session

    @monitor_query_performance("bulk_insert")
    async def bulk_insert(self, model_class, data_list: list[dict[str, Any]]) -> bool:
        """Toplu veri ekleme - performans optimizasyonu"""
        try:
            # SQLAlchemy bulk insert
            await self.session.execute(model_class.__table__.insert(), data_list)
            await self.session.commit()
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Bulk insert hatası: {e!s}")
            return False

    @monitor_query_performance("bulk_update")
    async def bulk_update(
        self, model_class, filter_criteria: dict[str, Any], update_data: dict[str, Any]
    ) -> int:
        """Toplu güncelleme - performans optimizasyonu"""
        try:
            result = await self.session.execute(
                model_class.__table__.update()
                .where(
                    *[getattr(model_class, k) == v for k, v in filter_criteria.items()]
                )
                .values(**update_data)
            )
            await self.session.commit()
            return result.rowcount

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Bulk update hatası: {e!s}")
            return 0

    @monitor_query_performance("paginated_query")
    async def get_paginated(
        self, query, page: int = 1, per_page: int = 20, max_per_page: int = 100
    ) -> dict[str, Any]:
        """Sayfalanmış sorgu - performans optimizasyonu"""
        try:
            # Güvenlik kontrolü
            per_page = min(per_page, max_per_page)
            offset = (page - 1) * per_page

            # Toplam sayı sorgusu (optimize edilmiş)
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.session.execute(count_query)
            total = total_result.scalar()

            # Veri sorgusu
            data_query = query.offset(offset).limit(per_page)
            data_result = await self.session.execute(data_query)
            items = data_result.scalars().all()

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
                "has_next": page * per_page < total,
                "has_prev": page > 1,
            }

        except Exception as e:
            logger.error(f"Paginated query hatası: {e!s}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "pages": 0,
                "has_next": False,
                "has_prev": False,
            }

    @monitor_query_performance("eager_loading")
    async def get_with_relations(
        self, model_class, filter_criteria: dict[str, Any], relations: list[str]
    ) -> list[Any]:
        """İlişkili verileri eager loading ile al"""
        try:
            query = select(model_class)

            # Filter criteria ekle
            for key, value in filter_criteria.items():
                query = query.where(getattr(model_class, key) == value)

            # Eager loading ekle
            for relation in relations:
                if hasattr(model_class, relation):
                    query = query.options(selectinload(getattr(model_class, relation)))

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Eager loading hatası: {e!s}")
            return []

    @monitor_query_performance("batch_processing")
    async def process_in_batches(
        self, query, batch_size: int = 1000, processor: Callable = None
    ) -> int:
        """Büyük veri setlerini batch'ler halinde işle"""
        try:
            processed_count = 0
            offset = 0

            while True:
                # Batch al
                batch_query = query.offset(offset).limit(batch_size)
                batch_result = await self.session.execute(batch_query)
                batch_items = batch_result.scalars().all()

                if not batch_items:
                    break

                # Batch'i işle
                if processor:
                    await processor(batch_items)

                processed_count += len(batch_items)
                offset += batch_size

                # Memory temizliği
                await self.session.expunge_all()

            return processed_count

        except Exception as e:
            logger.error(f"Batch processing hatası: {e!s}")
            return 0


class ConnectionPoolManager:
    """Veritabanı bağlantı havuzu yöneticisi"""

    def __init__(self):
        self.pool_stats = {
            "active_connections": 0,
            "idle_connections": 0,
            "total_connections": 0,
            "connection_errors": 0,
        }

    async def get_pool_status(self, engine) -> dict[str, Any]:
        """Bağlantı havuzu durumunu al"""
        try:
            pool = engine.pool

            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }

        except Exception as e:
            logger.error(f"Pool status hatası: {e!s}")
            return {}

    @asynccontextmanager
    async def get_optimized_session(self, session_factory):
        """Optimize edilmiş session context manager"""
        session = session_factory()

        try:
            # Session konfigürasyonu
            await session.execute(text("SET SESSION query_cache_type = ON"))
            await session.execute(text("SET SESSION query_cache_size = 1048576"))  # 1MB

            yield session

        except Exception as e:
            await session.rollback()
            logger.error(f"Session hatası: {e!s}")
            raise

        finally:
            await session.close()


# Index önerileri
INDEX_RECOMMENDATIONS = {
    "users": [
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
    ],
    "exams": [
        "CREATE INDEX IF NOT EXISTS idx_exams_student_id ON exams(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_exams_exam_type ON exams(exam_type)",
        "CREATE INDEX IF NOT EXISTS idx_exams_created_at ON exams(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_exams_status ON exams(status)",
    ],
    "questions": [
        "CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject)",
        "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)",
        "CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic)",
        "CREATE INDEX IF NOT EXISTS idx_questions_exam_type ON questions(exam_type)",
    ],
    "learning_styles": [
        "CREATE INDEX IF NOT EXISTS idx_learning_styles_student_id ON learning_styles(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_learning_styles_profile_type ON learning_styles(profile_type)",
    ],
}


async def create_performance_indexes(session: AsyncSession):
    """Performans için gerekli index'leri oluştur"""
    try:
        for table, indexes in INDEX_RECOMMENDATIONS.items():
            for index_sql in indexes:
                try:
                    await session.execute(text(index_sql))
                    logger.info(f"Index oluşturuldu: {index_sql}")
                except Exception as e:
                    logger.warning(f"Index oluşturma hatası: {index_sql} - {e!s}")

        await session.commit()
        logger.info("Tüm performans index'leri kontrol edildi")

    except Exception as e:
        logger.error(f"Index oluşturma genel hatası: {e!s}")
        await session.rollback()


# Query optimization utilities
class QueryBuilder:
    """Optimize edilmiş sorgu oluşturucu"""

    @staticmethod
    def build_search_query(
        model_class,
        search_term: str,
        search_fields: list[str],
        filters: dict[str, Any] | None = None,
    ):
        """Arama sorgusu oluştur"""
        query = select(model_class)

        # Arama koşulları
        if search_term and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(model_class, field):
                    search_conditions.append(
                        getattr(model_class, field).ilike(f"%{search_term}%")
                    )

            if search_conditions:
                from sqlalchemy import or_

                query = query.where(or_(*search_conditions))

        # Filtreler
        if filters:
            for key, value in filters.items():
                if hasattr(model_class, key) and value is not None:
                    query = query.where(getattr(model_class, key) == value)

        return query

    @staticmethod
    def build_analytics_query(
        model_class,
        date_field: str,
        start_date: str | None = None,
        end_date: str | None = None,
        group_by: str | None = None,
    ):
        """Analitik sorgusu oluştur"""
        query = select(model_class)

        # Tarih filtreleri
        if start_date and hasattr(model_class, date_field):
            query = query.where(getattr(model_class, date_field) >= start_date)

        if end_date and hasattr(model_class, date_field):
            query = query.where(getattr(model_class, date_field) <= end_date)

        # Gruplama
        if group_by and hasattr(model_class, group_by):
            query = query.group_by(getattr(model_class, group_by))

        return query


class DatabaseOptimizer:
    """
    Advanced database optimization manager for KIRO2
    Handles connection pooling, query optimization, and Turkish text indexing
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: AsyncEngine | None = None
        self.session_factory = None
        self.stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "connection_pool_size": 0,
            "active_connections": 0,
        }

    async def initialize(self):
        """Initialize optimized database engine"""
        try:
            # Create engine with optimized settings
            self.engine = create_async_engine(
                self.database_url,
                # Connection pool settings
                poolclass=QueuePool,
                pool_size=20,  # Base connections
                max_overflow=30,  # Additional connections under load
                pool_timeout=30,  # Wait time for connection
                pool_recycle=3600,  # Recreate connections every hour
                pool_pre_ping=True,  # Validate connections before use
                # Performance settings
                connect_args={
                    "command_timeout": 60,
                    "server_settings": {
                        # Turkish locale settings
                        "lc_collate": "tr_TR.UTF-8",
                        "lc_ctype": "tr_TR.UTF-8",
                        "timezone": "Europe/Istanbul",
                        # Performance settings
                        "shared_preload_libraries": "pg_stat_statements",
                        "log_min_duration_statement": "1000",  # Log slow queries
                        "log_checkpoints": "on",
                        "log_connections": "on",
                        "log_disconnections": "on",
                        "log_statement": "mod",  # Log modifications
                        # Memory settings
                        "work_mem": "8MB",
                        "maintenance_work_mem": "128MB",
                        "effective_cache_size": "1GB",
                        "shared_buffers": "256MB",
                        # Turkish full-text search
                        "default_text_search_config": "turkish",
                    },
                },
                # Logging and debugging
                echo=False,  # Disable in production
                echo_pool=False,
            )

            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # Test connection
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                logger.info("Database optimizer initialized successfully")

            # Setup monitoring
            await self._setup_monitoring()

        except Exception as e:
            logger.error(f"Failed to initialize database optimizer: {e}")
            raise

    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database optimizer closed")

    async def _setup_monitoring(self):
        """Setup database monitoring"""
        try:
            async with self.engine.begin() as conn:
                # Enable pg_stat_statements if available
                await conn.execute(
                    text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
                )

                # Create Turkish text search configuration if not exists
                await conn.execute(
                    text(
                        """
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_ts_config WHERE cfgname = 'turkish_kiro2'
                        ) THEN
                            CREATE TEXT SEARCH CONFIGURATION turkish_kiro2 (COPY = turkish);
                        END IF;
                    END $$;
                """
                    )
                )

                logger.info("Database monitoring setup completed")

        except Exception as e:
            logger.warning(f"Failed to setup database monitoring: {e}")

    async def get_session(self) -> AsyncSession:
        """Get database session from pool"""
        if not self.session_factory:
            raise RuntimeError("Database optimizer not initialized")

        return self.session_factory()

    async def create_turkish_indexes(self):
        """Create optimized indexes for Turkish content"""
        try:
            async with self.engine.begin() as conn:
                # Turkish text search indexes
                indexes = [
                    # User table indexes
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower 
                       ON users (lower(email))""",
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_gin 
                       ON users USING gin(to_tsvector('turkish', username))""",
                    # Question content indexes
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_content_gin 
                       ON questions USING gin(to_tsvector('turkish', content))""",
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_subject_difficulty 
                       ON questions (subject, difficulty_level)""",
                    # Exam session indexes
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_exam_sessions_user_created 
                       ON exam_sessions (user_id, created_at DESC)""",
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_exam_sessions_status_updated 
                       ON exam_sessions (status, updated_at DESC)""",
                    # Learning style indexes
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_styles_user_updated 
                       ON learning_style_profiles (user_id, updated_at DESC)""",
                    # Content indexes
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_title_gin 
                       ON content USING gin(to_tsvector('turkish', title))""",
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_body_gin 
                       ON content USING gin(to_tsvector('turkish', body))""",
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_subject_type 
                       ON content (subject, content_type, is_published)""",
                    # Performance tracking indexes
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_performance_user_subject 
                       ON user_performance (user_id, subject, created_at DESC)""",
                    # Notification indexes
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_user_read 
                       ON notifications (user_id, is_read, created_at DESC)""",
                ]

                for index_sql in indexes:
                    try:
                        await conn.execute(text(index_sql))
                        logger.info(
                            f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}"
                        )
                    except Exception as e:
                        logger.warning(f"Index creation warning: {e}")

                logger.info("Turkish content indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create Turkish indexes: {e}")
            raise

    async def optimize_tables(self, tables: list[str] | None = None):
        """Optimize database tables"""
        try:
            async with self.engine.begin() as conn:
                if tables is None:
                    # Get all user tables
                    result = await conn.execute(
                        text(
                            """
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public'
                        AND tablename NOT LIKE 'pg_%'
                        AND tablename NOT LIKE 'sql_%'
                    """
                        )
                    )
                    tables = [row[0] for row in result]

                for table in tables:
                    # Validate table name to prevent SQL injection (defense in depth)
                    if not re.match(r"^[a-zA-Z0-9_]+$", table):
                        logger.warning(f"Skipping invalid table name: {table}")
                        continue

                    logger.info(f"Optimizing table: {table}")

                    # SQL identifier validation performed above
                    # Analyze table statistics
                    await conn.execute(text(f"ANALYZE {table}"))

                    # Vacuum table (reclaim space)
                    await conn.execute(text(f"VACUUM ANALYZE {table}"))

                logger.info(f"Optimized {len(tables)} tables")

        except Exception as e:
            logger.error(f"Table optimization failed: {e}")
            raise

    async def get_performance_metrics(self) -> dict[str, Any]:
        """Get comprehensive performance metrics"""
        try:
            async with self.engine.begin() as conn:
                # Database size
                db_size_result = await conn.execute(
                    text(
                        """
                    SELECT pg_size_pretty(pg_database_size(current_database())) as database_size
                """
                    )
                )

                # Active connections
                connections_result = await conn.execute(
                    text(
                        """
                    SELECT count(*) as active_connections
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """
                    )
                )

                # Cache hit ratio
                cache_result = await conn.execute(
                    text(
                        """
                    SELECT 
                        sum(heap_blks_hit) as heap_hit,
                        sum(heap_blks_read) as heap_read,
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as cache_hit_ratio
                    FROM pg_statio_user_tables
                """
                    )
                )

                # Long running queries
                long_queries_result = await conn.execute(
                    text(
                        """
                    SELECT count(*) as long_queries
                    FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND now() - query_start > interval '1 minute'
                """
                    )
                )

                db_size_row = db_size_result.fetchone()
                connections_row = connections_result.fetchone()
                cache_row = cache_result.fetchone()
                long_queries_row = long_queries_result.fetchone()

                return {
                    "database_size": db_size_row[0] if db_size_row else "Unknown",
                    "active_connections": connections_row[0] if connections_row else 0,
                    "cache_hit_ratio": round(cache_row[2] or 0, 2) if cache_row else 0,
                    "long_running_queries": long_queries_row[0]
                    if long_queries_row
                    else 0,
                    "connection_pool": await self.get_connection_stats(),
                }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}

    async def get_connection_stats(self) -> dict[str, Any]:
        """Get connection pool statistics"""
        if not self.engine:
            return {}

        pool = self.engine.pool

        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }


# Query optimization utilities for Turkish content
class TurkishQueryOptimizer:
    """Query optimization utilities for Turkish content"""

    @staticmethod
    def optimize_search_query(search_term: str, columns: list[str], table: str) -> str:
        """Generate optimized Turkish search query"""
        # Clean and prepare search term
        cleaned_term = search_term.strip().lower()

        # Create full-text search conditions
        fts_conditions = []
        for column in columns:
            fts_conditions.append(
                f"to_tsvector('turkish', {column}) @@ plainto_tsquery('turkish', :search_term)"
            )

        # Create trigram search conditions for fuzzy matching
        trigram_conditions = []
        for column in columns:
            trigram_conditions.append(f"{column} % :search_term")

        query = f"""
        SELECT *, 
               CASE 
                   WHEN {' OR '.join(fts_conditions)} THEN 1
                   WHEN {' OR '.join(trigram_conditions)} THEN 0.5
                   ELSE 0
               END as relevance_score
        FROM {table}
        WHERE ({' OR '.join(fts_conditions + trigram_conditions)})
        ORDER BY relevance_score DESC, id
        """

        return query

    @staticmethod
    def paginate_query(base_query: str, page: int = 1, page_size: int = 20) -> str:
        """Add optimized pagination to query"""
        offset = (page - 1) * page_size
        return f"{base_query} LIMIT {page_size} OFFSET {offset}"


# Global instances
connection_pool_manager = ConnectionPoolManager()
query_builder = QueryBuilder()
db_optimizer: DatabaseOptimizer | None = None


async def get_db_optimizer() -> DatabaseOptimizer:
    """Get global database optimizer instance"""
    global db_optimizer

    if db_optimizer is None:
        database_url = "postgresql+asyncpg://user:pass@localhost/db"  # Load from config
        db_optimizer = DatabaseOptimizer(database_url)
        await db_optimizer.initialize()

    return db_optimizer
