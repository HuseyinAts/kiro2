"""
Run Migration 012: Add visual_content column for visual questions
"""
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def run_migration():
    """Run migration 012"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL not found in .env")
        return False

    # Fix asyncpg URL format (remove +asyncpg)
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    print("\n" + "=" * 60)
    print("Migration 012: Add Visual Content Support")
    print("=" * 60 + "\n")

    try:
        # Connect to database
        print("[1/3] Connecting to database...")
        conn = await asyncpg.connect(database_url)
        print("      [OK] Connected\n")

        # Read migration file
        print("[2/3] Reading migration file...")
        migration_path = os.path.join(
            os.path.dirname(__file__), "migrations", "012_add_visual_content_column.sql"
        )
        with open(migration_path, encoding="utf-8") as f:
            migration_sql = f.read()
        print("      [OK] Migration file loaded\n")

        # Execute migration
        print("[3/3] Executing migration...")
        await conn.execute(migration_sql)
        print("      [OK] Migration executed successfully\n")

        # Verify columns added
        print("Verifying changes...")

        # Check questions table
        questions_has_visual = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'questions'
                AND column_name = 'visual_content'
            )
            """
        )

        # Check sorular table
        sorular_has_visual = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sorular'
                AND column_name = 'visual_content'
            )
            """
        )

        print(
            f"  - questions.visual_content: {'[OK] Added' if questions_has_visual else '[FAIL] Failed'}"
        )
        print(
            f"  - sorular.visual_content: {'[OK] Added' if sorular_has_visual else '[FAIL] Failed'}"
        )

        # Check indexes
        indexes = await conn.fetch(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE tablename IN ('questions', 'sorular')
            AND indexname LIKE '%visual%'
            ORDER BY indexname
            """
        )

        print(f"\n  Indexes created: {len(indexes)}")
        for idx in indexes:
            print(f"    - {idx['indexname']}")

        await conn.close()

        print("\n" + "=" * 60)
        print("[SUCCESS] Migration 012 completed successfully!")
        print("=" * 60 + "\n")
        print("Next steps:")
        print("  1. Update models (add visual_content field)")
        print("  2. Update generator templates")
        print("  3. Create table parser/renderer")
        print("  4. Update frontend for table rendering")
        print("\n")

        return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e!s}\n")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    exit(0 if success else 1)
