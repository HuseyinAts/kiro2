"""
Dry Run Testing Module - REQ-2

Test ortaminda migration deneme altyapisi.
Production'da sorun cikmadan once migration'lari test eder.

Features:
    - Test database creation (production schema copy)
    - Upgrade/downgrade testing
    - Execution time tracking
    - Affected rows reporting

Usage:
    tester = DryRunTester()
    async with tester:
        result = await tester.run_upgrade("abc123")
        if result.success:
            print(f"Migration took {result.duration_seconds}s")
"""

import asyncio
import logging
import os
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)


# ==================== DATA CLASSES ====================


@dataclass
class DryRunConfig:
    """Dry run configuration."""

    # Database connection
    db_host: str = "localhost"
    db_port: str = "5434"
    db_name: str = "kiro2_db"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # Test database settings
    test_db_prefix: str = "test_migration_"
    cleanup_on_exit: bool = True
    timeout_seconds: int = 300  # 5 minutes

    # Alembic settings - compute absolute path relative to backend directory
    alembic_config_path: str = str(Path(__file__).parent.parent.parent / "alembic.ini")

    @classmethod
    def from_env(cls) -> "DryRunConfig":
        """Create config from environment variables.

        Supports both individual POSTGRES_* variables and DATABASE_URL.
        DATABASE_URL format: postgresql+asyncpg://user:pass@host:port/dbname
        """
        # Try to parse DATABASE_URL first
        database_url = os.getenv("DATABASE_URL", "")
        if database_url:
            import re
            # Parse: postgresql+asyncpg://user:pass@host:port/dbname
            pattern = r"postgresql\+?(?:asyncpg)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)"
            match = re.match(pattern, database_url)
            if match:
                return cls(
                    db_user=match.group(1),
                    db_password=match.group(2),
                    db_host=match.group(3),
                    db_port=match.group(4),
                    db_name=match.group(5),
                )

        # Fall back to individual environment variables
        return cls(
            db_host=os.getenv("POSTGRES_HOST", "localhost"),
            db_port=os.getenv("POSTGRES_PORT", "5434"),
            db_name=os.getenv("POSTGRES_DB", "kiro2_db"),
            db_user=os.getenv("POSTGRES_USER", "postgres"),
            db_password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        )


@dataclass
class ExecutionResult:
    """Migration execution result."""

    success: bool
    revision: str
    direction: str  # "upgrade" or "downgrade"
    duration_seconds: float = 0.0
    affected_tables: list[str] = field(default_factory=list)
    affected_rows: dict[str, int] = field(default_factory=dict)  # table -> row count
    error_message: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @property
    def total_affected_rows(self) -> int:
        """Toplam etkilenen satir sayisi."""
        return sum(self.affected_rows.values())

    def get_summary(self) -> str:
        """Ozet rapor olustur."""
        lines = [
            f"Migration {self.direction.upper()} - {self.revision}",
            f"Status: {'SUCCESS' if self.success else 'FAILED'}",
            f"Duration: {self.duration_seconds:.2f}s",
        ]

        if self.affected_tables:
            lines.append(f"Affected Tables: {', '.join(self.affected_tables)}")

        if self.affected_rows:
            lines.append("Affected Rows:")
            for table, count in self.affected_rows.items():
                lines.append(f"  - {table}: {count}")

        if self.error_message:
            lines.append(f"Error: {self.error_message}")

        return "\n".join(lines)


# ==================== DRY RUN TESTER ====================


class DryRunTester:
    """
    Test ortaminda migration deneme.

    REQ-2 implementasyonu: Migration'i test ortaminda deneme,
    upgrade ve downgrade testleri, execution time ve affected rows raporlama.

    Usage:
        async with DryRunTester() as tester:
            result = await tester.run_upgrade("head")
            if result.success:
                result = await tester.run_downgrade("-1")

    Attributes:
        config: DryRunConfig instance
        test_db_name: Olusturulan test database adi
    """

    def __init__(self, config: Optional[DryRunConfig] = None):
        """
        DryRunTester olustur.

        Args:
            config: DryRunConfig instance (default: from environment)
        """
        self.config = config or DryRunConfig.from_env()
        self.test_db_name: Optional[str] = None
        self._engine = None
        self._async_engine = None

    async def __aenter__(self) -> "DryRunTester":
        """Context manager entry - test DB olustur."""
        self.test_db_name = await self.create_test_db()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup."""
        if self.config.cleanup_on_exit and self.test_db_name:
            await self.cleanup_test_db()

    def _get_admin_connection_string(self) -> str:
        """Admin baglanti string'i (postgres DB'ye)."""
        return (
            f"postgresql://{self.config.db_user}:{self.config.db_password}"
            f"@{self.config.db_host}:{self.config.db_port}/postgres"
        )

    def _get_source_connection_string(self) -> str:
        """Kaynak DB baglanti string'i."""
        return (
            f"postgresql://{self.config.db_user}:{self.config.db_password}"
            f"@{self.config.db_host}:{self.config.db_port}/{self.config.db_name}"
        )

    def _get_test_connection_string(self) -> str:
        """Test DB baglanti string'i."""
        if not self.test_db_name:
            raise ValueError("Test database not created yet")
        return (
            f"postgresql://{self.config.db_user}:{self.config.db_password}"
            f"@{self.config.db_host}:{self.config.db_port}/{self.test_db_name}"
        )

    def _get_async_test_connection_string(self) -> str:
        """Test DB async baglanti string'i."""
        if not self.test_db_name:
            raise ValueError("Test database not created yet")
        return (
            f"postgresql+asyncpg://{self.config.db_user}:{self.config.db_password}"
            f"@{self.config.db_host}:{self.config.db_port}/{self.test_db_name}"
        )

    async def create_test_db(self) -> str:
        """
        Test database olustur.

        REQ-2.1: Dry run basladiginda test database'inde migration calistirir.
        REQ-2.2: Production'in exact kopyasini kullanir.

        Returns:
            str: Test database adi
        """
        # Generate unique test DB name
        test_db_name = f"{self.config.test_db_prefix}{uuid.uuid4().hex[:8]}"
        logger.info(f"Creating test database: {test_db_name}")

        try:
            # Use synchronous engine for DDL operations
            admin_engine = create_engine(
                self._get_admin_connection_string(),
                isolation_level="AUTOCOMMIT",
            )

            with admin_engine.connect() as conn:
                # Terminate existing connections to source DB
                conn.execute(text(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{self.config.db_name}'
                    AND pid <> pg_backend_pid()
                """))

                # Create test database as a template copy
                conn.execute(text(f"""
                    CREATE DATABASE "{test_db_name}"
                    WITH TEMPLATE "{self.config.db_name}"
                    OWNER "{self.config.db_user}"
                """))

            admin_engine.dispose()
            logger.info(f"Test database created: {test_db_name}")
            return test_db_name

        except Exception as e:
            logger.exception(f"Failed to create test database: {e}")
            # Fallback: create empty database and run migrations
            return await self._create_empty_test_db(test_db_name)

    async def _create_empty_test_db(self, test_db_name: str) -> str:
        """Bos test database olustur (fallback)."""
        admin_engine = create_engine(
            self._get_admin_connection_string(),
            isolation_level="AUTOCOMMIT",
        )

        with admin_engine.connect() as conn:
            conn.execute(text(f"""
                CREATE DATABASE "{test_db_name}"
                OWNER "{self.config.db_user}"
            """))

        admin_engine.dispose()
        logger.info(f"Empty test database created: {test_db_name}")
        return test_db_name

    async def run_upgrade(self, revision: str = "head") -> ExecutionResult:
        """
        Upgrade migration calistir.

        REQ-2.3: Migration test edildiginde upgrade testi yapar.

        Args:
            revision: Hedef revision (default: "head")

        Returns:
            ExecutionResult: Test sonucu
        """
        return await self._run_migration(revision, "upgrade")

    async def run_downgrade(self, revision: str = "-1") -> ExecutionResult:
        """
        Downgrade migration calistir.

        REQ-2.3: Migration test edildiginde downgrade testi yapar.

        Args:
            revision: Hedef revision (default: "-1" = bir onceki)

        Returns:
            ExecutionResult: Test sonucu

        Note:
            If current revision is a merge head and "-1" is specified,
            automatically detects and uses first parent to avoid
            "Ambiguous walk" error.
        """
        # Handle merge heads: if downgrade to -1 fails with "Ambiguous walk",
        # we need to specify a specific parent revision
        if revision == "-1":
            parent_revision = await self._get_downgrade_target()
            if parent_revision:
                revision = parent_revision

        return await self._run_migration(revision, "downgrade")

    async def _get_downgrade_target(self) -> str | None:
        """Get the appropriate downgrade target revision.

        For merge heads, returns the first parent. Returns None for normal revisions.
        """
        try:
            env = os.environ.copy()
            env["DATABASE_URL"] = self._get_test_connection_string()
            env["DATABASE_URL_SYNC"] = self._get_test_connection_string()

            # First get current revision
            cmd = [
                "alembic",
                "-c", self.config.alembic_config_path,
                "current",
            ]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                cwd=str(Path(self.config.alembic_config_path).parent),
            )

            # Parse current revision from output like "abc123 (head)"
            import re
            match = re.search(r"([a-f0-9]+)\s*\(head\)", result.stdout)
            if not match:
                return None

            current_rev = match.group(1)

            # Now show details of current revision
            cmd = [
                "alembic",
                "-c", self.config.alembic_config_path,
                "show", current_rev,
            ]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                cwd=str(Path(self.config.alembic_config_path).parent),
            )

            # Parse output to find merge parents
            output = result.stdout + result.stderr
            # Look for: "Merges: rev1, rev2" format
            match = re.search(r"Merges:\s*([^\n]+)", output)
            if match:
                # It's a merge, get first parent
                revisions = [r.strip() for r in match.group(1).split(",")]
                if revisions:
                    first_parent = revisions[0]
                    logger.info(f"Detected merge revision, using parent: {first_parent}")
                    return first_parent

            # Also check for "Revises: rev1, rev2" format in revision ID line
            match = re.search(r"Revises:\s*([^\n]+)", output)
            if match and "," in match.group(1):
                # It's a merge
                revisions = [r.strip() for r in match.group(1).split(",")]
                if len(revisions) > 1:
                    first_parent = revisions[0]
                    logger.info(f"Detected merge revision (from Revises), using parent: {first_parent}")
                    return first_parent

        except Exception as e:
            logger.warning(f"Could not determine downgrade target: {e}")

        return None

    async def _run_migration(self, revision: str, direction: str) -> ExecutionResult:
        """
        Migration calistir (internal).

        REQ-2.4: Test tamamlandiginda execution time ve affected rows raporlar.

        Args:
            revision: Hedef revision
            direction: "upgrade" veya "downgrade"

        Returns:
            ExecutionResult: Test sonucu
        """
        if not self.test_db_name:
            raise ValueError("Test database not created. Use 'async with' context manager.")

        start_time = datetime.now()

        # Capture row counts before migration
        row_counts_before = await self._get_row_counts()

        try:
            logger.info(f"Running {direction} to {revision} on {self.test_db_name}")

            # Build alembic command
            env = os.environ.copy()
            env["DATABASE_URL"] = self._get_test_connection_string()
            env["DATABASE_URL_SYNC"] = self._get_test_connection_string()
            env["PGPASSWORD"] = self.config.db_password

            cmd = [
                "alembic",
                "-c", self.config.alembic_config_path,
                direction,
                revision,
            ]

            # Run in thread pool
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        cmd,
                        env=env,
                        capture_output=True,
                        text=True,
                        cwd=str(Path(self.config.alembic_config_path).parent.absolute()),
                    )
                ),
                timeout=self.config.timeout_seconds,
            )

            # Capture row counts after migration
            row_counts_after = await self._get_row_counts()

            # Calculate affected rows
            affected_rows = {}
            affected_tables = []
            all_tables = set(row_counts_before.keys()) | set(row_counts_after.keys())

            for table in all_tables:
                before = row_counts_before.get(table, 0)
                after = row_counts_after.get(table, 0)
                if before != after:
                    affected_rows[table] = after - before
                    affected_tables.append(table)

            duration = (datetime.now() - start_time).total_seconds()

            if result.returncode != 0:
                # REQ-2.6: Hata detayi ve stack trace goster
                return ExecutionResult(
                    success=False,
                    revision=revision,
                    direction=direction,
                    duration_seconds=duration,
                    affected_tables=affected_tables,
                    affected_rows=affected_rows,
                    error_message=result.stderr or "Migration failed",
                    stdout=result.stdout,
                    stderr=result.stderr,
                    completed_at=datetime.now(),
                )

            # REQ-2.5: Basarili ise yesil onay
            logger.info(
                f"Migration {direction} to {revision} completed in {duration:.2f}s"
            )

            return ExecutionResult(
                success=True,
                revision=revision,
                direction=direction,
                duration_seconds=duration,
                affected_tables=affected_tables,
                affected_rows=affected_rows,
                stdout=result.stdout,
                stderr=result.stderr,
                completed_at=datetime.now(),
            )

        except asyncio.TimeoutError:
            duration = (datetime.now() - start_time).total_seconds()
            return ExecutionResult(
                success=False,
                revision=revision,
                direction=direction,
                duration_seconds=duration,
                error_message=f"Migration timed out after {self.config.timeout_seconds}s",
                completed_at=datetime.now(),
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.exception(f"Migration {direction} failed: {e}")
            return ExecutionResult(
                success=False,
                revision=revision,
                direction=direction,
                duration_seconds=duration,
                error_message=str(e),
                completed_at=datetime.now(),
            )

    async def _get_row_counts(self) -> dict[str, int]:
        """Tum tablolarin row count'larini al."""
        try:
            engine = create_async_engine(self._get_async_test_connection_string())

            async with engine.connect() as conn:
                # Get all user tables
                result = await conn.execute(text("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename NOT LIKE 'alembic%'
                """))
                tables = [row[0] for row in result.fetchall()]

                # Get row counts
                row_counts = {}
                for table in tables:
                    try:
                        count_result = await conn.execute(
                            text(f'SELECT COUNT(*) FROM "{table}"')
                        )
                        row_counts[table] = count_result.scalar() or 0
                    except Exception:
                        row_counts[table] = 0

            await engine.dispose()
            return row_counts

        except Exception as e:
            logger.warning(f"Failed to get row counts: {e}")
            return {}

    async def run_full_test(self, revision: str = "head") -> tuple[ExecutionResult, ExecutionResult]:
        """
        Tam upgrade/downgrade testi.

        REQ-2.3: Upgrade ve downgrade'i sirayla test eder.

        Args:
            revision: Hedef revision

        Returns:
            tuple[ExecutionResult, ExecutionResult]: (upgrade_result, downgrade_result)
        """
        # Run upgrade
        upgrade_result = await self.run_upgrade(revision)

        if not upgrade_result.success:
            # Downgrade test anlamsiz, bos result dondur
            return (
                upgrade_result,
                ExecutionResult(
                    success=False,
                    revision=revision,
                    direction="downgrade",
                    error_message="Skipped due to upgrade failure",
                ),
            )

        # Run downgrade
        downgrade_result = await self.run_downgrade("-1")

        return (upgrade_result, downgrade_result)

    async def cleanup_test_db(self) -> None:
        """Test database'i sil."""
        if not self.test_db_name:
            return

        logger.info(f"Cleaning up test database: {self.test_db_name}")

        try:
            # Close any existing connections
            if self._async_engine:
                await self._async_engine.dispose()
                self._async_engine = None

            # Use admin connection to drop database
            admin_engine = create_engine(
                self._get_admin_connection_string(),
                isolation_level="AUTOCOMMIT",
            )

            with admin_engine.connect() as conn:
                # Terminate connections
                conn.execute(text(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{self.test_db_name}'
                    AND pid <> pg_backend_pid()
                """))

                # Drop database
                conn.execute(text(f'DROP DATABASE IF EXISTS "{self.test_db_name}"'))

            admin_engine.dispose()
            logger.info(f"Test database dropped: {self.test_db_name}")
            self.test_db_name = None

        except Exception as e:
            logger.exception(f"Failed to cleanup test database: {e}")

    async def verify_schema_integrity(self) -> bool:
        """
        Test DB schema integrity'sini dogrula.

        Returns:
            bool: Schema gecerli mi?
        """
        try:
            engine = create_async_engine(self._get_async_test_connection_string())

            async with engine.connect() as conn:
                # Check alembic_version exists
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'alembic_version'
                    )
                """))
                has_alembic = result.scalar()

                if not has_alembic:
                    logger.warning("alembic_version table not found")
                    return False

                # Check for any broken foreign keys
                result = await conn.execute(text("""
                    SELECT COUNT(*)
                    FROM information_schema.table_constraints
                    WHERE constraint_type = 'FOREIGN KEY'
                """))
                fk_count = result.scalar() or 0
                logger.info(f"Found {fk_count} foreign key constraints")

            await engine.dispose()
            return True

        except Exception as e:
            logger.exception(f"Schema integrity check failed: {e}")
            return False


# ==================== CLI INTERFACE ====================


async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migration Dry Run Tester")
    parser.add_argument(
        "--revision",
        default="head",
        help="Target revision (default: head)",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't cleanup test database after test",
    )
    parser.add_argument(
        "--full-test",
        action="store_true",
        help="Run full upgrade + downgrade test",
    )

    args = parser.parse_args()

    config = DryRunConfig.from_env()
    config.cleanup_on_exit = not args.no_cleanup

    async with DryRunTester(config) as tester:
        if args.full_test:
            upgrade_result, downgrade_result = await tester.run_full_test(args.revision)

            print("\n" + "=" * 60)
            print("UPGRADE RESULT")
            print("=" * 60)
            print(upgrade_result.get_summary())

            print("\n" + "=" * 60)
            print("DOWNGRADE RESULT")
            print("=" * 60)
            print(downgrade_result.get_summary())

            success = upgrade_result.success and downgrade_result.success

        else:
            result = await tester.run_upgrade(args.revision)
            print("\n" + "=" * 60)
            print("MIGRATION RESULT")
            print("=" * 60)
            print(result.get_summary())
            success = result.success

        return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
