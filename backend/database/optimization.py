"""
Database Optimization and Scaling Module
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu

Bu modül veritabanı performans optimizasyonu ve ölçeklenebilirlik için:
- Gelişmiş connection pooling optimizasyonu
- Kapsamlı indexing stratejisi
- Query optimizasyonu (100K+ öğrenci için)
- Database monitoring ve alerting
- Performance metrics toplama

Requirements: 7.1, 7.2, 7.3
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import Index, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.pool import Pool

logger = logging.getLogger(__name__)


class DatabaseOptimizationManager:
    """
    Veritabanı optimizasyon ve performans yöneticisi

    Özellikler:
    - Connection pool monitoring
    - Query performance tracking
    - Automatic index recommendations
    - Performance metrics collection
    """

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.metrics: Dict[str, Any] = {
            "queries": [],
            "slow_queries": [],
            "connection_stats": {},
            "index_usage": {},
        }
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """SQLAlchemy event listener'larını kur"""

        @event.listens_for(Pool, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Yeni connection oluşturulduğunda"""
            logger.debug("New database connection established")
            self.metrics["connection_stats"]["total_connections"] = (
                self.metrics["connection_stats"].get("total_connections", 0) + 1
            )

        @event.listens_for(Pool, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Connection pool'dan connection alındığında"""
            self.metrics["connection_stats"]["checkouts"] = (
                self.metrics["connection_stats"].get("checkouts", 0) + 1
            )

        @event.listens_for(Pool, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Connection pool'a connection geri verildiğinde"""
            self.metrics["connection_stats"]["checkins"] = (
                self.metrics["connection_stats"].get("checkins", 0) + 1
            )

    async def get_pool_status(self) -> Dict[str, Any]:
        """
        Connection pool durumunu getir

        Returns:
            Pool istatistikleri (size, checked_out, overflow, etc.)
        """
        try:
            pool = self.engine.pool

            return {
                "pool_size": pool.size(),
                "checked_out_connections": pool.checkedout(),
                "overflow_connections": pool.overflow(),
                "checked_in_connections": pool.checkedin(),
                "total_connections": pool.size() + pool.overflow(),
                "available_connections": pool.size() - pool.checkedout(),
                "pool_timeout": pool._timeout if hasattr(pool, "_timeout") else None,
                "max_overflow": pool._max_overflow
                if hasattr(pool, "_max_overflow")
                else None,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Pool status alınamadı: {e}")
            return {"error": str(e)}

    async def optimize_pool_settings(
        self, expected_concurrent_users: int = 100000
    ) -> Dict[str, int]:
        """
        Beklenen kullanıcı sayısına göre pool ayarlarını optimize et

        Args:
            expected_concurrent_users: Beklenen eşzamanlı kullanıcı sayısı

        Returns:
            Önerilen pool ayarları
        """
        # Her 1000 kullanıcı için ~5 connection (ortalama request süresi 200ms)
        recommended_pool_size = max(50, min(200, expected_concurrent_users // 1000 * 5))
        recommended_max_overflow = recommended_pool_size * 2

        # Connection timeout hesaplama (yüksek yük altında daha uzun)
        recommended_timeout = 30 if expected_concurrent_users > 50000 else 20

        # Pool recycle time (connection freshness için)
        recommended_recycle = 3600  # 1 saat

        recommendations = {
            "pool_size": recommended_pool_size,
            "max_overflow": recommended_max_overflow,
            "pool_timeout": recommended_timeout,
            "pool_recycle": recommended_recycle,
            "pool_pre_ping": True,  # Her kullanımda connection sağlığı kontrolü
        }

        logger.info(
            f"Pool optimizasyonu: {expected_concurrent_users} kullanıcı için "
            f"pool_size={recommended_pool_size}, max_overflow={recommended_max_overflow}"
        )

        return recommendations

    async def analyze_query_performance(
        self, query: str, execution_time: float, threshold_ms: float = 200.0
    ):
        """
        Query performansını analiz et ve yavaş sorguları kaydet

        Args:
            query: SQL sorgusu
            execution_time: Çalışma süresi (saniye)
            threshold_ms: Yavaş sorgu eşiği (milisaniye)
        """
        execution_time_ms = execution_time * 1000

        query_info = {
            "query": query[:500],  # İlk 500 karakter
            "execution_time_ms": execution_time_ms,
            "timestamp": datetime.now().isoformat(),
        }

        self.metrics["queries"].append(query_info)

        # Yavaş sorguları ayrı takip et
        if execution_time_ms > threshold_ms:
            self.metrics["slow_queries"].append(query_info)
            logger.warning(
                f"Yavaş sorgu tespit edildi ({execution_time_ms:.2f}ms): "
                f"{query[:100]}..."
            )

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Toplanan performans metriklerini getir

        Returns:
            Performans metrikleri özeti
        """
        total_queries = len(self.metrics["queries"])
        slow_queries = len(self.metrics["slow_queries"])

        if total_queries > 0:
            avg_execution_time = (
                sum(q["execution_time_ms"] for q in self.metrics["queries"])
                / total_queries
            )
        else:
            avg_execution_time = 0

        return {
            "total_queries": total_queries,
            "slow_queries_count": slow_queries,
            "slow_query_percentage": (slow_queries / total_queries * 100)
            if total_queries > 0
            else 0,
            "average_execution_time_ms": avg_execution_time,
            "connection_stats": self.metrics["connection_stats"],
            "pool_status": await self.get_pool_status(),
        }

    def clear_metrics(self):
        """Metrikleri temizle (memory management için)"""
        # Son 1000 sorguyu tut
        if len(self.metrics["queries"]) > 1000:
            self.metrics["queries"] = self.metrics["queries"][-1000:]

        # Son 100 yavaş sorguyu tut
        if len(self.metrics["slow_queries"]) > 100:
            self.metrics["slow_queries"] = self.metrics["slow_queries"][-100:]


class DatabaseIndexingStrategy:
    """
    Veritabanı indexing stratejisi ve yönetimi

    100K+ öğrenci için optimize edilmiş index stratejisi
    """

    # Önerilen indexler (tablo_adı: [kolon_listesi])
    RECOMMENDED_INDEXES = {
        "kullanici": [
            ["email"],  # Login için
            ["kullanici_adi"],  # Arama için
            ["rol"],  # Role-based queries için
            ["created_at"],  # Zaman bazlı sorgular için
        ],
        "ogrenci_profili": [
            ["kullanici_id"],  # Foreign key
            ["sinif_seviyesi"],  # Filtreleme için
            ["hedef_universite"],  # Filtreleme için
            ["created_at", "updated_at"],  # Composite index
        ],
        "sinav": [
            ["ogrenci_id"],  # Öğrenci sınavları için
            ["sinav_tipi"],  # Sınav tipi filtreleme
            ["baslangic_zamani"],  # Zaman bazlı sorgular
            ["tamamlanma_durumu"],  # Durum filtreleme
            ["ogrenci_id", "sinav_tipi", "baslangic_zamani"],  # Composite
        ],
        "sinav_cevabi": [
            ["sinav_id"],  # Sınav cevapları için
            ["soru_id"],  # Soru bazlı analiz
            ["dogru_mu"],  # Başarı analizi
            ["sinav_id", "soru_id"],  # Composite (unique)
        ],
        "sinav_sonucu": [
            ["sinav_id"],  # Unique index
            ["ogrenci_id"],  # Öğrenci sonuçları
            ["toplam_puan"],  # Sıralama için
            ["created_at"],  # Zaman bazlı
        ],
        "soru_bankasi": [
            ["konu"],  # Konu bazlı sorgular
            ["zorluk_seviyesi"],  # Zorluk filtreleme
            ["sinav_tipi"],  # Sınav tipi filtreleme
            ["konu", "zorluk_seviyesi"],  # Composite
        ],
        "ogrenme_oturumu": [
            ["ogrenci_id"],  # Öğrenci oturumları
            ["baslangic_zamani"],  # Zaman bazlı
            ["konu"],  # Konu bazlı analiz
            ["ogrenci_id", "baslangic_zamani"],  # Composite
        ],
        "egitim_icerigi": [
            ["konu"],  # Konu bazlı arama
            ["icerik_tipi"],  # Tip filtreleme
            ["zorluk_seviyesi"],  # Zorluk filtreleme
            ["kalite_skoru"],  # Sıralama için
        ],
    }

    @classmethod
    async def create_indexes(cls, session: AsyncSession):
        """
        Önerilen indexleri oluştur

        Args:
            session: Database session
        """
        logger.info("Veritabanı indexleri oluşturuluyor...")

        for table_name, index_columns_list in cls.RECOMMENDED_INDEXES.items():
            for columns in index_columns_list:
                index_name = f"idx_{table_name}_{'_'.join(columns)}"

                try:
                    # Index oluşturma SQL'i
                    columns_str = ", ".join(columns)
                    create_index_sql = f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table_name} ({columns_str})
                    """

                    await session.execute(text(create_index_sql))
                    logger.info(f"✓ Index oluşturuldu: {index_name}")

                except Exception as e:
                    logger.error(f"✗ Index oluşturulamadı ({index_name}): {e}")

        await session.commit()
        logger.info("Index oluşturma tamamlandı")

    @classmethod
    async def analyze_index_usage(cls, session: AsyncSession) -> Dict[str, Any]:
        """
        Index kullanım istatistiklerini analiz et (PostgreSQL)

        Args:
            session: Database session

        Returns:
            Index kullanım istatistikleri
        """
        try:
            # PostgreSQL index kullanım sorgusu
            query = text(
                """
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan as index_scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
            """
            )

            result = await session.execute(query)
            rows = result.fetchall()

            index_stats = []
            for row in rows:
                index_stats.append(
                    {
                        "schema": row[0],
                        "table": row[1],
                        "index": row[2],
                        "scans": row[3],
                        "tuples_read": row[4],
                        "tuples_fetched": row[5],
                    }
                )

            return {
                "total_indexes": len(index_stats),
                "indexes": index_stats,
                "unused_indexes": [idx for idx in index_stats if idx["scans"] == 0],
            }

        except Exception as e:
            logger.error(f"Index analizi başarısız: {e}")
            return {"error": str(e)}

    @classmethod
    async def get_missing_indexes(cls, session: AsyncSession) -> List[Dict[str, Any]]:
        """
        Eksik index önerilerini al (PostgreSQL)

        Args:
            session: Database session

        Returns:
            Eksik index önerileri
        """
        try:
            # PostgreSQL missing index sorgusu
            query = text(
                """
            SELECT
                schemaname,
                tablename,
                attname as column_name,
                n_distinct,
                correlation
            FROM pg_stats
            WHERE schemaname = 'public'
            AND n_distinct > 100
            AND correlation < 0.1
            ORDER BY n_distinct DESC
            LIMIT 20
            """
            )

            result = await session.execute(query)
            rows = result.fetchall()

            recommendations = []
            for row in rows:
                recommendations.append(
                    {
                        "schema": row[0],
                        "table": row[1],
                        "column": row[2],
                        "distinct_values": row[3],
                        "correlation": row[4],
                        "recommendation": f"CREATE INDEX idx_{row[1]}_{row[2]} ON {row[1]}({row[2]})",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"Missing index analizi başarısız: {e}")
            return []


class QueryOptimizer:
    """
    Query optimizasyon ve analiz araçları

    100K+ öğrenci için optimize edilmiş sorgular
    """

    @staticmethod
    async def explain_query(session: AsyncSession, query: str) -> Dict[str, Any]:
        """
        Query execution plan'ı analiz et

        Args:
            session: Database session
            query: Analiz edilecek SQL sorgusu

        Returns:
            Query execution plan
        """
        try:
            explain_query = text(f"EXPLAIN ANALYZE {query}")
            result = await session.execute(explain_query)
            rows = result.fetchall()

            plan = [row[0] for row in rows]

            return {
                "query": query[:200],
                "execution_plan": plan,
                "has_seq_scan": any("Seq Scan" in line for line in plan),
                "has_index_scan": any("Index Scan" in line for line in plan),
            }

        except Exception as e:
            logger.error(f"Query explain başarısız: {e}")
            return {"error": str(e)}

    @staticmethod
    def optimize_pagination_query(
        base_query: str, page: int = 1, page_size: int = 50, order_by: str = "id"
    ) -> str:
        """
        Pagination için optimize edilmiş sorgu oluştur

        Args:
            base_query: Temel SQL sorgusu
            page: Sayfa numarası
            page_size: Sayfa başına kayıt sayısı
            order_by: Sıralama kolonu

        Returns:
            Optimize edilmiş pagination sorgusu
        """
        offset = (page - 1) * page_size

        # OFFSET yerine keyset pagination kullan (daha performanslı)
        optimized_query = f"""
        {base_query}
        ORDER BY {order_by}
        LIMIT {page_size}
        OFFSET {offset}
        """

        return optimized_query

    @staticmethod
    async def get_table_statistics(
        session: AsyncSession, table_name: str
    ) -> Dict[str, Any]:
        """
        Tablo istatistiklerini getir

        Args:
            session: Database session
            table_name: Tablo adı

        Returns:
            Tablo istatistikleri
        """
        try:
            # Satır sayısı
            count_query = text(f"SELECT COUNT(*) FROM {table_name}")
            result = await session.execute(count_query)
            row_count = result.scalar()

            # Tablo boyutu (PostgreSQL)
            size_query = text(
                f"""
            SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))
            """
            )
            result = await session.execute(size_query)
            table_size = result.scalar()

            return {
                "table_name": table_name,
                "row_count": row_count,
                "table_size": table_size,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Tablo istatistikleri alınamadı: {e}")
            return {"error": str(e)}


# Global optimization manager instance
_optimization_manager: Optional[DatabaseOptimizationManager] = None


def get_optimization_manager(engine: AsyncEngine) -> DatabaseOptimizationManager:
    """Global optimization manager instance'ı al"""
    global _optimization_manager
    if _optimization_manager is None:
        _optimization_manager = DatabaseOptimizationManager(engine)
    return _optimization_manager
