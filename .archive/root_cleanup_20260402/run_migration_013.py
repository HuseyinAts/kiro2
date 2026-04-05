#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run migration 013: Create sorular table
"""
import sys
import os
import asyncio
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

def log(msg):
    print(msg, flush=True)

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def run_migration():
    """Run migration 013 to create sorular table"""
    log("="*80)
    log("MIGRATION 013: CREATE SORULAR TABLE")
    log("="*80)
    log("")

    try:
        from core.database import db_manager

        await db_manager.initialize()
        log("[✓] Database connection established")
        log("")

        # Read migration SQL
        migration_file = "backend/migrations/013_create_sorular_table.sql"
        if not os.path.exists(migration_file):
            log(f"[HATA] Migration file not found: {migration_file}")
            return

        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        log("[✓] Migration SQL loaded")
        log("")

        # Execute migration
        async with db_manager.get_session() as session:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

            log(f"[→] Executing {len(statements)} SQL statements...")
            log("")

            for idx, statement in enumerate(statements, 1):
                try:
                    # Skip comments and empty lines
                    if not statement or statement.startswith('--'):
                        continue

                    log(f"[{idx}/{len(statements)}] Executing statement...")

                    from sqlalchemy import text
                    await session.execute(text(statement))
                    await session.commit()

                    # Show what was created
                    if 'CREATE TABLE' in statement.upper():
                        log("  [✓] Table created: sorular")
                    elif 'CREATE INDEX' in statement.upper():
                        log("  [✓] Index created")
                    elif 'CREATE TRIGGER' in statement.upper():
                        log("  [✓] Trigger created")
                    elif 'CREATE OR REPLACE FUNCTION' in statement.upper():
                        log("  [✓] Function created")
                    elif 'COMMENT ON' in statement.upper():
                        pass  # Don't log every comment
                    else:
                        log("  [✓] Statement executed")

                except Exception as e:
                    error_msg = str(e)
                    # Ignore "already exists" errors
                    if 'already exists' in error_msg.lower():
                        log(f"  [→] Already exists, skipping")
                    else:
                        log(f"  [!] Warning: {error_msg[:100]}")

            log("")
            log("="*80)
            log("MIGRATION COMPLETE")
            log("="*80)
            log("")

            # Verify table was created
            result = await session.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'sorular'
                    )
                """)
            )
            table_exists = result.scalar()

            if table_exists:
                log("[✓✓✓] SUCCESS: 'sorular' table created and verified!")
                log("")

                # Get column count
                result = await session.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM information_schema.columns
                        WHERE table_name = 'sorular'
                    """)
                )
                column_count = result.scalar()
                log(f"[INFO] Table has {column_count} columns")

                # Get index count
                result = await session.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM pg_indexes
                        WHERE tablename = 'sorular'
                    """)
                )
                index_count = result.scalar()
                log(f"[INFO] Table has {index_count} indexes")

                # Get row count
                result = await session.execute(text("SELECT COUNT(*) FROM sorular"))
                row_count = result.scalar()
                log(f"[INFO] Table has {row_count} rows (expected: 0)")
                log("")
            else:
                log("[HATA] Table was not created!")

        await db_manager.close()

    except Exception as e:
        log(f"[HATA] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_migration())
