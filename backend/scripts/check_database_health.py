"""
Database Health Check Script
Verifies database schema, migrations, and data integrity
"""

import asyncio
from datetime import datetime
from typing import Any

import asyncpg


class DatabaseHealthChecker:
    """Comprehensive database health checker"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.issues = []
        self.warnings = []
        self.conn = None

    async def connect(self):
        """Connect to database"""
        try:
            self.conn = await asyncpg.connect(self.db_url)
            return True
        except Exception as e:
            self.issues.append(f"[X] Database connection failed: {e}")
            return False

    async def check_all(self) -> dict[str, Any]:
        """Run all health checks"""
        if not await self.connect():
            return self._build_report()

        # Run checks sequentially to avoid connection concurrency issues
        await self.check_tables()
        await self.check_migrations()
        await self.check_indexes()
        await self.check_foreign_keys()
        await self.check_data_integrity()
        await self.check_performance()

        await self.conn.close()

        return self._build_report()

    async def check_tables(self):
        """Check that all required tables exist"""
        print("\n[TABLES] Checking Tables...")
        print("-" * 60)

        required_tables = [
            "kullanicilar",
            "ogrenme_profilleri",
            "sorular",
            "sinavlar",
            "sinav_sonuclari",
            "cozulen_sorular",
            "ogrenme_yollari",
            "icerik_kaynaklari",
            "performans_analizleri",
            "cache_entries",
            "user_sessions",
            "audit_logs",
            "ogrenci_ogretmen",
            "ogrenci_veli",
            "alembic_version",
        ]

        tables = await self.conn.fetch(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname='public'
        """
        )

        existing_tables = [t["tablename"] for t in tables]

        # Check for required tables
        for table in required_tables:
            if table in existing_tables:
                print(f"  [OK] {table}")
            else:
                self.issues.append(f"[X] Missing table: {table}")
                print(f"  [X] {table} - MISSING")

        # Check for unexpected tables
        unexpected = set(existing_tables) - set(required_tables)
        if unexpected:
            self.warnings.append(f"[!] Unexpected tables: {', '.join(unexpected)}")

        print(f"\nTotal tables: {len(existing_tables)}/{len(required_tables)}")

    async def check_migrations(self):
        """Check Alembic migration status"""
        print("\n[MIGRATIONS] Checking Migrations...")
        print("-" * 60)

        try:
            version = await self.conn.fetchrow(
                "SELECT version_num FROM alembic_version"
            )

            if version:
                current_version = version["version_num"]
                print(f"  [OK] Current version: {current_version}")

                # Check if this is the latest known version
                expected_versions = ["60e185cfcca9", "f822e22c28c6"]
                if current_version in expected_versions:
                    print("  [OK] Version is up to date")
                else:
                    self.warnings.append(
                        f"[!] Unknown migration version: {current_version}"
                    )
            else:
                self.issues.append("[X] No migration version found")

        except Exception as e:
            self.issues.append(f"[X] Migration check failed: {e}")

    async def check_indexes(self):
        """Check critical indexes exist"""
        print("\n[INDEXES] Checking Indexes...")
        print("-" * 60)

        critical_indexes = [
            ("kullanicilar", "kullanicilar_pkey"),
            ("sorular", "sorular_pkey"),
            ("sinavlar", "sinavlar_pkey"),
            ("sinav_sonuclari", "sinav_sonuclari_pkey"),
        ]

        for table, index_pattern in critical_indexes:
            indexes = await self.conn.fetch(
                f"""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = '{table}'
                AND indexname LIKE '%{index_pattern}%'
            """
            )

            if indexes:
                print(f"  [OK] {table}: {len(indexes)} indexes")
            else:
                self.warnings.append(f"[!] No primary key index found for {table}")

    async def check_foreign_keys(self):
        """Check foreign key constraints"""
        print("\n[FOREIGN KEYS] Checking Foreign Keys...")
        print("-" * 60)

        fks = await self.conn.fetch(
            """
            SELECT
                tc.table_name,
                tc.constraint_name,
                ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name
        """
        )

        if fks:
            print(f"  [OK] Found {len(fks)} foreign key constraints")

            # Group by table
            fk_by_table = {}
            for fk in fks:
                table = fk["table_name"]
                if table not in fk_by_table:
                    fk_by_table[table] = []
                fk_by_table[table].append(fk)

            for table, constraints in fk_by_table.items():
                print(f"  [OK] {table}: {len(constraints)} FKs")
        else:
            self.warnings.append("[!] No foreign keys found")

    async def check_data_integrity(self):
        """Check basic data integrity"""
        print("\n[DATA INTEGRITY] Checking Data Integrity...")
        print("-" * 60)

        # Check for orphaned records
        checks = [
            {
                "name": "Orphaned exam results",
                "query": """
                    SELECT COUNT(*) FROM sinav_sonuclari sr
                    LEFT JOIN kullanicilar k ON sr.ogrenci_id = k.id
                    WHERE k.id IS NULL
                """,
            },
            {
                "name": "Orphaned solved questions",
                "query": """
                    SELECT COUNT(*) FROM cozulen_sorular cs
                    LEFT JOIN kullanicilar k ON cs.ogrenci_id = k.id
                    WHERE k.id IS NULL
                """,
            },
        ]

        for check in checks:
            try:
                count = await self.conn.fetchval(check["query"])
                if count == 0:
                    print(f"  [OK] {check['name']}: None found")
                else:
                    self.warnings.append(f"[!] {check['name']}: {count} records")
                    print(f"  [!] {check['name']}: {count} records")
            except Exception as e:
                print(f"  [!] {check['name']}: Check failed ({e})")

    async def check_performance(self):
        """Check performance metrics"""
        print("\n[PERFORMANCE] Checking Performance Metrics...")
        print("-" * 60)

        metrics = []

        # Table sizes
        table_sizes = await self.conn.fetch(
            """
            SELECT
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as bytes
            FROM pg_tables
            WHERE schemaname='public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 5
        """
        )

        print("\n  [SIZES] Largest Tables:")
        for table in table_sizes:
            print(f"    {table['tablename']:25} {table['size']:>10}")
            metrics.append({"table": table["tablename"], "size": table["size"]})

        # Row counts
        tables = ["kullanicilar", "sorular", "sinavlar", "sinav_sonuclari"]
        print("\n  [COUNTS] Row Counts:")
        for table in tables:
            try:
                count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                print(f"    {table:25} {count:>10,} rows")
            except Exception as e:
                print(f"    {table:25} Error: {e}")

        # Index usage (if available)
        try:
            unused_indexes = await self.conn.fetch(
                """
                SELECT
                    schemaname || '.' || tablename as table,
                    indexname,
                    idx_scan
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                AND indexname NOT LIKE '%pkey'
                LIMIT 5
            """
            )

            if unused_indexes:
                print("\n  [WARNING] Potentially Unused Indexes:")
                for idx in unused_indexes:
                    print(f"    {idx['table']}: {idx['indexname']}")
                    self.warnings.append(
                        f"[!] Unused index: {idx['indexname']} on {idx['table']}"
                    )
        except Exception:
            pass  # Stats not available

    def _build_report(self) -> dict[str, Any]:
        """Build health check report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy" if not self.issues else "unhealthy",
            "issues": self.issues,
            "warnings": self.warnings,
            "issues_count": len(self.issues),
            "warnings_count": len(self.warnings),
        }

    def print_summary(self, report: dict[str, Any]):
        """Print summary report"""
        print("\n" + "=" * 60)
        print("DATABASE HEALTH CHECK SUMMARY")
        print("=" * 60)

        print(f"\nTimestamp: {report['timestamp']}")
        print(f"Status: {report['status'].upper()}")

        if report["issues"]:
            print(f"\n[ISSUES] CRITICAL ISSUES ({len(report['issues'])}):")
            for issue in report["issues"]:
                print(f"  {issue}")

        if report["warnings"]:
            print(f"\n[WARNINGS] WARNINGS ({len(report['warnings'])}):")
            for warning in report["warnings"]:
                print(f"  {warning}")

        if not report["issues"] and not report["warnings"]:
            print("\n[SUCCESS] All checks passed!")

        print("\n" + "=" * 60)


async def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("KIRO2 Database Health Check")
    print("=" * 60)

    db_url = "postgresql://postgres:postgres@localhost:5434/turkiye_sinav_db"

    checker = DatabaseHealthChecker(db_url)
    report = await checker.check_all()
    checker.print_summary(report)


if __name__ == "__main__":
    asyncio.run(main())
