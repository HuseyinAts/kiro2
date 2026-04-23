#!/usr/bin/env python3
"""
Run migration 013: Create sorular table
"""
import asyncio
import logging
from pathlib import Path

import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration():
    """Run the sorular table creation migration"""
    # Database connection params - TEK KAYNAK: teknofest_db (Port 5434)
    db_params = {
        "host": "localhost",
        "port": 5434,
        "user": "teknofest",
        "password": "TeknoFest2025SecurePass",
        "database": "teknofest_db"
    }

    try:
        # Connect to database
        conn = await asyncpg.connect(**db_params)
        logger.info("✅ Connected to database")

        # Read SQL file
        sql_file = Path("migrations/013_create_sorular_table.sql")
        sql = sql_file.read_text(encoding="utf-8")
        logger.info(f"📄 Read migration file: {sql_file.name}")

        # Execute migration
        logger.info("🔧 Executing migration...")
        await conn.execute(sql)
        logger.info("✅ Migration completed successfully!")

        # Verify table was created
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'sorular'
            )
        """)

        if exists:
            logger.info("✅ Table 'sorular' created successfully!")

            # Count any existing rows
            count = await conn.fetchval("SELECT COUNT(*) FROM sorular")
            logger.info(f"📊 Current row count: {count}")
        else:
            logger.error("❌ Table 'sorular' was not created!")

        await conn.close()

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())
