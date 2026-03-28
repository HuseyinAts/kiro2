"""
Database Query Optimization Script v2 - Week 3
Analyzes and optimizes PostgreSQL database for KIRO platform
"""

import asyncio
import os

import asyncpg


class DatabaseOptimizerV2:
    """Optimize PostgreSQL database for performance"""

    def __init__(self):
        """Initialize database connection"""
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise RuntimeError("DATABASE_URL env var required")
        self.conn = None

    async def connect(self):
        """Connect to database"""
        try:
            self.conn = await asyncpg.connect(self.db_url)
            print("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e!s}")
            return False

    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()

    async def analyze_table_stats(self) -> list[dict]:
        """Analyze table statistics"""
        query = """
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            n_live_tup AS row_count,
            n_dead_tup AS dead_rows
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 20;
        """

        rows = await self.conn.fetch(query)
        stats = [dict(row) for row in rows]

        print("\n📊 TABLE STATISTICS (Top 20 by size)")
        print("=" * 100)

        for stat in stats:
            print(
                f"{stat['tablename']:<30} Size:{stat['size']:<15} Rows:{stat['row_count']:<15}"
            )

        return stats

    async def create_missing_indexes(self):
        """Create recommended indexes for KIRO platform"""
        print("\n🔧 CREATING RECOMMENDED INDEXES")
        print("=" * 80)

        indexes = [
            {
                "name": "idx_sorular_cat_selection_v2",
                "table": "sorular",
                "columns": "(konu, irt_difficulty, aktif, status)",
                "condition": "WHERE aktif = TRUE AND status = 'approved'",
                "description": "CAT question selection optimization",
            },
        ]

        created_count = 0

        for idx in indexes:
            try:
                create_sql = f"""
                CREATE INDEX IF NOT EXISTS {idx["name"]}
                ON {idx["table"]} {idx["columns"]}
                {idx["condition"]};
                """

                await self.conn.execute(create_sql)
                print(f"✅ Created: {idx['name']}")
                created_count += 1

            except Exception as e:
                print(f"⏭️  Skipped: {idx['name']} ({str(e)[:50]})")

        print(f"\n📊 Index Creation Summary: {created_count} created")

    async def run_full_optimization(self):
        """Run complete database optimization"""
        print("=" * 80)
        print("DATABASE OPTIMIZATION V2 - KIRO PLATFORM")
        print("=" * 80)

        if not await self.connect():
            return

        try:
            await self.analyze_table_stats()
            await self.create_missing_indexes()

            print("\n✅ OPTIMIZATION COMPLETE!")

        finally:
            await self.close()


async def main():
    """Main entry point"""
    optimizer = DatabaseOptimizerV2()
    await optimizer.run_full_optimization()


if __name__ == "__main__":
    asyncio.run(main())
