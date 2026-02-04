"""
Run Migration 010: Question Bank v2.0 Upgrade
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def run_migration():
    """Execute migration 010"""
    # Connect to database
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL not found in .env")
        return

    # Convert SQLAlchemy URL to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    print("Connecting to database...")
    conn = await asyncpg.connect(db_url)

    try:
        # Read migration file
        migration_path = "migrations/010_upgrade_question_bank_v2.sql"
        print(f"Reading migration file: {migration_path}")

        with open(migration_path, "r", encoding="utf-8") as f:
            migration_sql = f.read()

        # Execute migration
        print("Executing migration...")
        print("=" * 60)

        await conn.execute(migration_sql)

        print("=" * 60)
        print("[SUCCESS] Migration 010 completed!")

        # Verify new tables
        print("\nVerifying new tables...")
        tables = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN (
                'cat_sessions',
                'cat_responses',
                'expert_review_tasks',
                'expert_profiles',
                'knowledge_graph_relationships'
            )
            ORDER BY table_name
        """
        )

        print(f"New tables created: {len(tables)}")
        for table in tables:
            print(f"  - {table['table_name']}")

        # Verify new columns in sorular
        print("\nVerifying new columns in 'sorular' table...")
        columns = await conn.fetch(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'sorular'
            AND column_name IN (
                'irt_discrimination',
                'irt_guessing',
                'plagiarism_score',
                'knowledge_graph_id',
                'bloom_level',
                'status'
            )
            ORDER BY column_name
        """
        )

        print(f"New columns added: {len(columns)}")
        for col in columns:
            print(f"  - {col['column_name']} ({col['data_type']})")

        # Check indexes
        print("\nVerifying indexes...")
        indexes = await conn.fetch(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'sorular'
            AND indexname LIKE 'idx_sorular_%'
            ORDER BY indexname
        """
        )

        print(f"Indexes on sorular: {len(indexes)}")
        for idx in indexes[:5]:  # Show first 5
            print(f"  - {idx['indexname']}")
        if len(indexes) > 5:
            print(f"  ... and {len(indexes) - 5} more")

        # Check views
        print("\nVerifying views...")
        views = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            AND table_name LIKE 'vw_%'
            ORDER BY table_name
        """
        )

        print(f"Views created: {len(views)}")
        for view in views:
            print(f"  - {view['table_name']}")

        print("\n" + "=" * 60)
        print("[SUCCESS] All v2.0 features ready!")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await conn.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    asyncio.run(run_migration())
