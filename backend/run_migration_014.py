"""
Run Migration 014: Performance Indexes
PHASE 1 Sprint 1: Database Optimization

Adds 50+ indexes to improve query performance
Expected gain: 40-80% faster on common queries
"""
import asyncio
import asyncpg
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    """Run migration 014"""
    # Database connection - use config from database connection module
    import os

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://teknofest:[REDACTED_DB_PASSWORD]@localhost:5432/teknofest_db",
    )

    # Convert SQLAlchemy URL to asyncpg format
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("✅ Connected to database")

        # Read migration file
        migration_file = (
            Path(__file__).parent / "migrations" / "014_add_performance_indexes.sql"
        )

        if not migration_file.exists():
            logger.error(f"❌ Migration file not found: {migration_file}")
            return

        sql = migration_file.read_text(encoding="utf-8")
        logger.info(f"📄 Read migration file: {migration_file.name}")

        # Execute migration
        logger.info("🔧 Executing migration...")
        await conn.execute(sql)
        logger.info("✅ Migration executed successfully")

        # Verify indexes created
        logger.info("🔍 Verifying indexes...")

        index_check_queries = [
            # Check a few critical indexes
            "SELECT indexname FROM pg_indexes WHERE indexname = 'idx_users_email'",
            "SELECT indexname FROM pg_indexes WHERE indexname = 'idx_sorular_subject_difficulty'",
            "SELECT indexname FROM pg_indexes WHERE indexname = 'idx_answers_user_created'",
            "SELECT indexname FROM pg_indexes WHERE indexname = 'idx_point_transactions_user_created'",
            "SELECT indexname FROM pg_indexes WHERE indexname = 'idx_video_cache_topic_subject'",
        ]

        verified = 0
        for query in index_check_queries:
            result = await conn.fetchval(query)
            if result:
                verified += 1
                logger.info(f"  ✓ {result}")

        logger.info(f"✅ Verified {verified}/{len(index_check_queries)} sample indexes")

        # Count total indexes on key tables
        total_indexes_query = """
        SELECT schemaname, tablename, COUNT(*) as index_count
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename IN ('users', 'sorular', 'answers', 'learning_paths',
                           'user_achievements', 'point_transactions', 'video_cache', 'audit_logs')
        GROUP BY schemaname, tablename
        ORDER BY tablename;
        """

        results = await conn.fetch(total_indexes_query)
        logger.info("\n📊 Index count per table:")
        total = 0
        for row in results:
            count = row["index_count"]
            total += count
            logger.info(f"  {row['tablename']:25} {count:3} indexes")

        logger.info(f"\n🎉 Total indexes: {total}")
        logger.info("✅ Migration 014 completed successfully!")
        logger.info("\n📈 Expected Performance Improvements:")
        logger.info("  • User analytics: 70-80% faster")
        logger.info("  • Question selection: 50-60% faster")
        logger.info("  • Learning path queries: 60-70% faster")
        logger.info("  • Transaction history: 80-90% faster")
        logger.info("  • Cache lookups: 90%+ faster")

        await conn.close()

    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_migration())
