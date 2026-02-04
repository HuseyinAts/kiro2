#!/usr/bin/env python3
"""
Database Optimization Script
Performance optimization ve index yönetimi
"""

import asyncio
import logging
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from core.database import db_manager, get_db_session_context

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization sınıfı"""

    def __init__(self):
        self.optimization_results = {
            "indexes_analyzed": 0,
            "queries_optimized": 0,
            "performance_improvements": [],
        }

    async def analyze_database_performance(self):
        """Database performansını analiz et"""
        logger.info("[MAG] Database performans analizi başlatılıyor...")

        try:
            await db_manager.initialize()

            # Index analizi
            await self._analyze_indexes()

            # Query performance analizi
            await self._analyze_query_performance()

            # Table statistics
            await self._analyze_table_statistics()

            # Optimization önerileri
            await self._generate_optimization_recommendations()

            # Sonuçları raporla
            await self._print_optimization_report()

            logger.info("[CHECK] Database performans analizi tamamlandı!")
            return True

        except Exception as e:
            logger.error(f"[X] Performans analizi hatası: {str(e)}")
            return False
        finally:
            await db_manager.close()

    async def _analyze_indexes(self):
        """Index analizi"""
        logger.info("[CHART] Index analizi yapılıyor...")

        async with get_db_session_context() as session:
            try:
                # SQLite için index bilgilerini al
                result = await session.execute(
                    text(
                        "SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
                    )
                )
                indexes = result.fetchall()

                self.optimization_results["indexes_analyzed"] = len(indexes)

                logger.info(f"[TRENDING_UP] {len(indexes)} index bulundu")
                for index in indexes:
                    logger.info(f"   - {index[0]}")

            except SQLAlchemyError as e:
                logger.error(f"Index analizi hatası: {str(e)}")

    async def _analyze_query_performance(self):
        """Query performance analizi"""
        logger.info("[LIGHTNING] Query performance analizi yapılıyor...")

        # Kritik query'leri test et
        test_queries = [
            {
                "name": "User lookup by email",
                "query": "SELECT * FROM users WHERE email = ?",
                "params": ("admin@turkiyesinav.com",),
            },
            {
                "name": "Questions by subject",
                "query": "SELECT * FROM questions WHERE subject_area = ?",
                "params": ("MATEMATIK",),
            },
            {
                "name": "Student profile lookup",
                "query": "SELECT * FROM student_profiles WHERE grade_level = ?",
                "params": (12,),
            },
            {
                "name": "Exam sessions by student",
                "query": "SELECT * FROM exam_sessions WHERE student_id = ? ORDER BY created_at DESC",
                "params": ("test-student-id",),
            },
        ]

        async with get_db_session_context() as session:
            for query_test in test_queries:
                try:
                    # Query execution time ölçümü
                    import time

                    start_time = time.time()

                    result = await session.execute(
                        text(query_test["query"]), query_test["params"]
                    )
                    rows = result.fetchall()

                    end_time = time.time()
                    execution_time = (end_time - start_time) * 1000  # ms

                    logger.info(
                        f"   {query_test['name']}: {execution_time:.2f}ms ({len(rows)} rows)"
                    )

                    if execution_time > 100:  # 100ms üzeri yavaş
                        self.optimization_results["performance_improvements"].append(
                            {
                                "query": query_test["name"],
                                "execution_time": execution_time,
                                "recommendation": "Index optimization needed",
                            }
                        )

                except SQLAlchemyError as e:
                    logger.warning(
                        f"Query test hatası ({query_test['name']}): {str(e)}"
                    )

        self.optimization_results["queries_optimized"] = len(test_queries)

    async def _analyze_table_statistics(self):
        """Tablo istatistikleri"""
        logger.info("[CLIPBOARD] Tablo istatistikleri analiz ediliyor...")

        tables = [
            "users",
            "student_profiles",
            "teacher_profiles",
            "parent_profiles",
            "questions",
            "exam_sessions",
            "exam_questions",
            "student_answers",
            "educational_contents",
            "learning_analytics",
            "classrooms",
            "system_configurations",
            "audit_logs",
        ]

        async with get_db_session_context() as session:
            for table in tables:
                try:
                    # Validate table name to prevent SQL injection
                    if not re.match(r"^[a-zA-Z0-9_]+$", table):
                        logger.warning(f"Skipping invalid table name: {table}")
                        continue

                    # SQL identifier validation performed above
                    result = await session.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    )
                    count = result.scalar()
                    logger.info(f"   {table}: {count} kayıt")

                except SQLAlchemyError as e:
                    logger.warning(f"Tablo istatistik hatası ({table}): {str(e)}")

    async def _generate_optimization_recommendations(self):
        """Optimization önerileri oluştur"""
        logger.info("[BULB] Optimization önerileri oluşturuluyor...")

        recommendations = [
            {
                "category": "Index Optimization",
                "recommendations": [
                    "Email arama için composite index ekle: (email, is_active)",
                    "Sınav sorguları için composite index: (student_id, created_at)",
                    "Soru filtreleme için composite index: (subject_area, difficulty, exam_type)",
                ],
            },
            {
                "category": "Query Optimization",
                "recommendations": [
                    "Pagination için LIMIT/OFFSET yerine cursor-based pagination kullan",
                    "N+1 query problemini önlemek için eager loading kullan",
                    "Büyük result set'ler için streaming kullan",
                ],
            },
            {
                "category": "Schema Optimization",
                "recommendations": [
                    "JSON alanları için functional index'ler ekle",
                    "Sık kullanılan computed field'lar için materialized view'lar oluştur",
                    "Archive stratejisi ile eski verileri ayrı tablolara taşı",
                ],
            },
            {
                "category": "Connection Optimization",
                "recommendations": [
                    "Connection pool size'ı workload'a göre ayarla",
                    "Connection timeout değerlerini optimize et",
                    "Read replica kullanımını değerlendir",
                ],
            },
        ]

        self.optimization_results["recommendations"] = recommendations

    async def _print_optimization_report(self):
        """Optimization raporu yazdır"""
        logger.info("\n" + "=" * 60)
        logger.info("[ROCKET] DATABASE OPTIMIZATION RAPORU")
        logger.info("=" * 60)

        logger.info(
            f"[CHART] Analiz Edilen Index Sayısı: {self.optimization_results['indexes_analyzed']}"
        )
        logger.info(
            f"[LIGHTNING] Test Edilen Query Sayısı: {self.optimization_results['queries_optimized']}"
        )
        logger.info(
            f"⚠️ Performance İyileştirme Gereken: {len(self.optimization_results['performance_improvements'])}"
        )

        if self.optimization_results["performance_improvements"]:
            logger.info("\n🐌 YAVAŞ QUERY'LER:")
            for improvement in self.optimization_results["performance_improvements"]:
                logger.info(
                    f"   - {improvement['query']}: {improvement['execution_time']:.2f}ms"
                )
                logger.info(f"     Öneri: {improvement['recommendation']}")

        if "recommendations" in self.optimization_results:
            logger.info("\n[BULB] OPTİMİZASYON ÖNERİLERİ:")
            for category in self.optimization_results["recommendations"]:
                logger.info(f"\n[CLIPBOARD] {category['category']}:")
                for rec in category["recommendations"]:
                    logger.info(f"   • {rec}")

        logger.info("=" * 60)

    async def apply_basic_optimizations(self):
        """Temel optimizasyonları uygula"""
        logger.info("[TOOL] Temel optimizasyonlar uygulanıyor...")

        try:
            await db_manager.initialize()

            async with get_db_session_context() as session:
                # SQLite için temel optimizasyonlar
                optimizations = [
                    "PRAGMA journal_mode = WAL;",  # Write-Ahead Logging
                    "PRAGMA synchronous = NORMAL;",  # Sync mode
                    "PRAGMA cache_size = 10000;",  # Cache size
                    "PRAGMA temp_store = MEMORY;",  # Temp storage
                    "PRAGMA mmap_size = 268435456;",  # Memory mapping (256MB)
                ]

                for optimization in optimizations:
                    try:
                        await session.execute(text(optimization))
                        logger.info(f"[CHECK] Uygulandı: {optimization}")
                    except SQLAlchemyError as e:
                        logger.warning(
                            f"⚠️ Optimization hatası: {optimization} - {str(e)}"
                        )

                await session.commit()

            logger.info("[CHECK] Temel optimizasyonlar tamamlandı!")
            return True

        except Exception as e:
            logger.error(f"[X] Optimization uygulama hatası: {str(e)}")
            return False
        finally:
            await db_manager.close()

    async def vacuum_database(self):
        """Database vacuum işlemi"""
        logger.info("🧹 Database vacuum işlemi başlatılıyor...")

        try:
            await db_manager.initialize()

            async with get_db_session_context() as session:
                # SQLite VACUUM
                await session.execute(text("VACUUM;"))
                logger.info("[CHECK] VACUUM tamamlandı")

                # ANALYZE statistics
                await session.execute(text("ANALYZE;"))
                logger.info("[CHECK] ANALYZE tamamlandı")

                await session.commit()

            logger.info("[CHECK] Database vacuum işlemi tamamlandı!")
            return True

        except Exception as e:
            logger.error(f"[X] Vacuum işlemi hatası: {str(e)}")
            return False
        finally:
            await db_manager.close()


async def main():
    """Ana fonksiyon"""
    import argparse

    parser = argparse.ArgumentParser(description="Database Optimization Tool")
    parser.add_argument(
        "action", choices=["analyze", "optimize", "vacuum"], help="Yapılacak işlem"
    )

    args = parser.parse_args()

    optimizer = DatabaseOptimizer()

    if args.action == "analyze":
        success = await optimizer.analyze_database_performance()
    elif args.action == "optimize":
        success = await optimizer.apply_basic_optimizations()
    elif args.action == "vacuum":
        success = await optimizer.vacuum_database()
    else:
        parser.print_help()
        return

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
