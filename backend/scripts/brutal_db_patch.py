"""
Database Surgery Script - Brutal DBA Executioner
KIRO2 High-Concurrency SRE & DBA Remediations

This script runs outside SQLAlchemy transactions (isolation_level="AUTOCOMMIT") to:
1. Drop unused user indexes (idx_scan = 0) concurrently.
2. Create indexes for missing Foreign Keys concurrently to prevent Table Locks.
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("brutal_db_patch")

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2"

async def run_surgery():
    logger.info("Initializing DBA Surgery Engine...")

    # Establish asyncpg engine with autocommit to prevent active transaction block on CONCURRENT operations
    engine = create_async_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

    dropped_count = 0
    created_count = 0

    async with engine.connect() as conn:
        # 1. Fetch unused indexes (idx_scan = 0, excluding PKs and unique constraints)
        unused_query = text("""
            SELECT
                schemaname,
                relname as tablename,
                indexrelname as index_name
            FROM pg_stat_user_indexes ui
            JOIN pg_index i ON ui.indexrelid = i.indexrelid
            WHERE ui.idx_scan = 0 
              AND NOT i.indisunique
              AND NOT i.indisprimary
              AND ui.schemaname = 'public';
        """)

        logger.info("Scanning for unused indexes (idx_scan = 0)...")
        unused_results = await conn.execute(unused_query)
        unused_indexes = unused_results.fetchall()
        logger.info(f"Discovered {len(unused_indexes)} unused indexes.")

        # 2. Fetch missing FK indexes
        fk_query = text("""
            SELECT
                c.conrelid::regclass::text AS table_name,
                c.conname::text AS constraint_name,
                g.column_names AS column_names
            FROM pg_constraint c
            CROSS JOIN LATERAL (
                SELECT 
                    array_to_string(array_agg(a.attname), ', ') AS column_names,
                    array_agg(a.attnum) AS attnums
                FROM pg_attribute a
                WHERE a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
            ) g
            WHERE c.contype = 'f'
              AND NOT EXISTS (
                  SELECT 1
                  FROM pg_index i
                  WHERE i.indrelid = c.conrelid
                    AND (i.indkey::int2[])[0:(array_length(c.conkey, 1) - 1)] = c.conkey::int2[]
              )
            ORDER BY table_name, constraint_name;
        """)

        logger.info("Scanning for missing Foreign Key indexes...")
        fk_results = await conn.execute(fk_query)
        missing_fks = fk_results.fetchall()
        logger.info(f"Discovered {len(missing_fks)} missing FK indexes.")

        # 3. Drop unused indexes concurrently
        logger.info("Starting unused index drops (DROP INDEX CONCURRENTLY)...")
        for idx, row in enumerate(unused_indexes):
            schemaname, tablename, index_name = row
            # Strip schema if included in index name
            clean_index_name = index_name.split('.')[-1]
            drop_stmt = f'DROP INDEX CONCURRENTLY IF EXISTS "{clean_index_name}"'
            try:
                logger.info(f"[{idx+1}/{len(unused_indexes)}] Dropping index {clean_index_name} on table {tablename}...")
                await conn.execute(text(drop_stmt))
                dropped_count += 1
            except Exception as e:
                logger.error(f"Failed to drop index {clean_index_name}: {e}")

        # 4. Create missing FK indexes concurrently
        logger.info("Starting missing FK index creation (CREATE INDEX CONCURRENTLY)...")
        for idx, row in enumerate(missing_fks):
            table_name, constraint_name, column_names = row
            # Clean table name
            clean_table = table_name.split('.')[-1].replace('"', '')
            # Clean columns for index name creation
            clean_cols = column_names.replace(', ', '_').replace(' ', '_').replace('"', '')
            index_name = f"idx_fk_{clean_table}_{clean_cols}"

            # Format columns properly for statement: wrap each column in double quotes
            formatted_cols = ", ".join([f'"{c.strip()}"' for c in column_names.split(",")])

            create_stmt = f'CREATE INDEX CONCURRENTLY IF NOT EXISTS "{index_name}" ON "{clean_table}" ({formatted_cols})'
            try:
                logger.info(f"[{idx+1}/{len(missing_fks)}] Creating index {index_name} on table {clean_table}({column_names})...")
                await conn.execute(text(create_stmt))
                created_count += 1
            except Exception as e:
                logger.error(f"Failed to create index {index_name}: {e}")

    logger.info("Surgery completed successfully.")
    logger.info(f"Summary: Dropped {dropped_count} unused indexes. Created {created_count} missing FK indexes.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_surgery())
