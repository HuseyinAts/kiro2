"""
Core Database Patch Script - Brutal Core Executioner
KIRO2 SRE & DBA Remediations

This script runs outside SQLAlchemy transactions (isolation_level="AUTOCOMMIT") to:
1. Concurrently drop any INVALID indexes in pg_index.
2. Concurrently create GIN indexes for JSONB columns lacking them to prevent table locks and full scans.
"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("brutal_db_core_patch")

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2"

async def run_surgery():
    logger.info("Initializing Core DBA Surgery Engine...")
    engine = create_async_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    
    dropped_count = 0
    created_count = 0
    
    async with engine.connect() as conn:
        # 1. Fetch broken/invalid indexes
        invalid_idx_query = text("""
            SELECT
                c.relname as index_name,
                t.relname as table_name
            FROM pg_index i
            JOIN pg_class c ON c.oid = i.indexrelid
            JOIN pg_class t ON t.oid = i.indrelid
            WHERE i.indisvalid = false
            LIMIT 50;
        """)
        
        logger.info("Scanning for broken/invalid indexes (indisvalid = false)...")
        invalid_results = await conn.execute(invalid_idx_query)
        invalid_indexes = invalid_results.fetchall()
        logger.info(f"Discovered {len(invalid_indexes)} invalid indexes.")
        
        # Drop invalid indexes
        for idx, row in enumerate(invalid_indexes):
            index_name = row[0]
            tablename = row[1]
            clean_index_name = index_name.split('.')[-1]
            drop_stmt = f'DROP INDEX CONCURRENTLY IF EXISTS "{clean_index_name}"'
            try:
                logger.info(f"[{idx+1}/{len(invalid_indexes)}] Dropping invalid index {clean_index_name} on table {tablename}...")
                await conn.execute(text(drop_stmt))
                dropped_count += 1
            except Exception as e:
                logger.error(f"Failed to drop invalid index {clean_index_name}: {e}")
                
        # 2. Fetch JSONB columns
        jsonb_cols_query = text("""
            SELECT 
                table_name, 
                column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND udt_name = 'jsonb'
            LIMIT 50;
        """)
        logger.info("Scanning for all JSONB columns...")
        jsonb_results = await conn.execute(jsonb_cols_query)
        jsonb_cols = jsonb_results.fetchall()
        
        # 3. Fetch existing GIN indexes
        gin_idx_query = text("""
            SELECT 
                t.relname as table_name,
                i.relname as index_name,
                a.attname as column_name
            FROM pg_class t
            JOIN pg_index idx ON t.oid = idx.indrelid
            JOIN pg_class i ON i.oid = idx.indexrelid
            JOIN pg_am am ON i.relam = am.oid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(idx.indkey)
            WHERE am.amname = 'gin' AND t.relnamespace = 'public'::regnamespace
            LIMIT 50;
        """)
        gin_results = await conn.execute(gin_idx_query)
        gin_rows = gin_results.fetchall()
        gin_indexed_cols = {(r[0], r[2]) for r in gin_rows}
        
        # Determine missing GIN indexes
        missing_gin_indexes = []
        for col in jsonb_cols:
            tbl = col[0]
            clm = col[1]
            if (tbl, clm) not in gin_indexed_cols:
                missing_gin_indexes.append((tbl, clm))
                
        logger.info(f"Discovered {len(missing_gin_indexes)} JSONB columns lacking GIN indexes.")
        
        # Create missing GIN indexes concurrently
        for idx, (table_name, column_name) in enumerate(missing_gin_indexes):
            clean_table = table_name.split('.')[-1].replace('"', '')
            clean_col = column_name.replace('"', '')
            
            # Construct GIN index name (PG max 63 bytes)
            index_name = f"idx_gin_{clean_table}_{clean_col}"
            if len(index_name) > 63:
                index_name = index_name[:63]
                
            create_stmt = f'CREATE INDEX CONCURRENTLY IF NOT EXISTS "{index_name}" ON "{clean_table}" USING gin ("{clean_col}")'
            try:
                logger.info(f"[{idx+1}/{len(missing_gin_indexes)}] Creating GIN index {index_name} on table {clean_table}({clean_col})...")
                await conn.execute(text(create_stmt))
                created_count += 1
            except Exception as e:
                logger.error(f"Failed to create GIN index {index_name} on {clean_table}: {e}")
                
    logger.info("Core DBA patch surgery completed successfully.")
    logger.info(f"Summary: Dropped {dropped_count} invalid indexes. Created {created_count} GIN indexes.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_surgery())
