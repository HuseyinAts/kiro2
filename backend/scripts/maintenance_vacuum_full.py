"""
Nightly Database Maintenance Script - Heavyweight VACUUM FULL
KIRO2 SRE & DBA Maintenance Operations

This script runs sequentially outside transactions (AUTOCOMMIT mode)
to perform a complete tablespace reclamation via VACUUM FULL ANALYZE.
Must only be scheduled during off-peak maintenance hours (nightly).
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("maintenance_vacuum")

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2"

async def run_maintenance():
    logger.info("Initializing Nightly DBA VACUUM Maintenance Engine...")
    engine = create_async_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

    reclaimed_tables = 0

    async with engine.connect() as conn:
        # Retrieve all public tables
        tables_query = text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)

        logger.info("Fetching public tables list...")
        result = await conn.execute(tables_query)
        tables = result.fetchall()
        logger.info(f"Discovered {len(tables)} tables to vacuum.")

        for idx, row in enumerate(tables):
            table_name = row[0]
            # Strip quotes or schema prefixes
            clean_table = table_name.split('.')[-1].replace('"', '')
            vacuum_stmt = f'VACUUM FULL ANALYZE "{clean_table}"'
            try:
                logger.info(f"[{idx+1}/{len(tables)}] Reclaiming space on table {clean_table}...")
                await conn.execute(text(vacuum_stmt))
                reclaimed_tables += 1
            except Exception as e:
                logger.error(f"Failed to VACUUM FULL table {clean_table}: {e}")

    logger.info("Nightly DBA maintenance completed successfully.")
    logger.info(f"Summary: Reclaimed and analyzed {reclaimed_tables} tables.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_maintenance())
