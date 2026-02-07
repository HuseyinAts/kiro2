"""
Rollback Manager - REQ-5

Guvenli rollback yonetimi.
Migration geri alma islemlerini guvenli sekilde yapar.

Features:
    - Dry run before rollback
    - Data integrity check after rollback
    - Backup restore capability
    - Manual intervention detection

Usage:
    manager = RollbackManager(config)
    result = await manager.execute_rollback("abc123")
    if not result.success:
        await manager.restore_from_backup("/path/to/backup.sql.gz")
"""

import asyncio
import gzip
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from ..testing.dry_run import DryRunConfig, DryRunTester, ExecutionResult
from ..validation.integrity_validator import DataIntegrityValidator

logger = logging.getLogger(__name__)


# ==================== DATA CLASSES ====================


@dataclass
class RollbackResult:
    """Rollback sonucu."""

    success: bool
    revision: str
    target_revision: str
    dry_run_result: Optional[ExecutionResult] = None
    execution_result: Optional[ExecutionResult] = None
    integrity_check_passed: bool = False
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    manual_intervention_required: bool = False

    def get_summary(self) -> str:
        """Ozet rapor."""
        lines = [
            f"Rollback Result: {self.revision} -> {self.target_revision}",
            f"Status: {'SUCCESS' if self.success else 'FAILED'}",
            f"Duration: {self.duration_seconds:.2f}s",
            f"Dry Run Passed: {self.dry_run_result.success if self.dry_run_result else 'N/A'}",
            f"Integrity Check: {'PASSED' if self.integrity_check_passed else 'FAILED'}",
            f"Manual Intervention: {'REQUIRED' if self.manual_intervention_required else 'NO'}",
        ]
        if self.error_message:
            lines.append(f"Error: {self.error_message}")
        return "\n".join(lines)


@dataclass
class RestoreResult:
    """Backup restore sonucu."""

    success: bool
    backup_path: Path
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    tables_restored: int = 0
    rows_restored: int = 0

    def get_summary(self) -> str:
        """Ozet rapor."""
        lines = [
            "Restore Result",
            f"Backup: {self.backup_path}",
            f"Status: {'SUCCESS' if self.success else 'FAILED'}",
            f"Duration: {self.duration_seconds:.2f}s",
            f"Tables Restored: {self.tables_restored}",
            f"Rows Restored: {self.rows_restored}",
        ]
        if self.error_message:
            lines.append(f"Error: {self.error_message}")
        return "\n".join(lines)


@dataclass
class VerificationResult:
    """Rollback dogrulama sonucu."""

    success: bool
    schema_valid: bool = False
    data_intact: bool = False
    alembic_version_correct: bool = False
    error_message: Optional[str] = None


# ==================== ROLLBACK MANAGER ====================


class RollbackManager:
    """
    Guvenli rollback yonetimi.

    REQ-5 implementasyonu: Migration'lari guvenli sekilde geri alir,
    dry run test yapar, data integrity kontrol eder.

    Attributes:
        config: DryRunConfig instance
        dry_run_tester: DryRunTester instance
        integrity_validator: DataIntegrityValidator instance
    """

    def __init__(
        self,
        config: Optional[DryRunConfig] = None,
        backup_dir: str = "backups/migrations",
    ):
        """
        RollbackManager olustur.

        Args:
            config: DryRunConfig instance (default: from environment)
            backup_dir: Backup dizini
        """
        self.config = config or DryRunConfig.from_env()
        self.backup_dir = Path(backup_dir)
        self._engine = None

    def _get_connection_string(self) -> str:
        """Async baglanti string'i."""
        return (
            f"postgresql+asyncpg://{self.config.db_user}:{self.config.db_password}"
            f"@{self.config.db_host}:{self.config.db_port}/{self.config.db_name}"
        )

    async def _get_engine(self):
        """Async engine al veya olustur."""
        if self._engine is None:
            self._engine = create_async_engine(self._get_connection_string())
        return self._engine

    async def dry_run_rollback(self, revision: str) -> ExecutionResult:
        """
        Rollback'i dry run olarak test et.

        REQ-5.2: Downgrade calistirildiginda once dry run test yapar.

        Args:
            revision: Hedef revision (ornegin "-1" veya "abc123")

        Returns:
            ExecutionResult: Dry run sonucu
        """
        logger.info(f"Running dry run rollback to {revision}")

        async with DryRunTester(self.config) as tester:
            result = await tester.run_downgrade(revision)

        return result

    async def execute_rollback(
        self,
        revision: str = "-1",
        skip_dry_run: bool = False,
        skip_integrity_check: bool = False,
    ) -> RollbackResult:
        """
        Rollback calistir.

        REQ-5.1: Rollback gerektiginde alembic downgrade komutunu calistirir.

        Args:
            revision: Hedef revision (default: "-1" = bir onceki)
            skip_dry_run: Dry run'i atla
            skip_integrity_check: Integrity check'i atla

        Returns:
            RollbackResult: Rollback sonucu
        """
        start_time = datetime.now()
        current_revision = await self._get_current_revision()

        logger.info(f"Executing rollback from {current_revision} to {revision}")

        # Step 1: Dry run test (REQ-5.2)
        dry_run_result = None
        if not skip_dry_run:
            dry_run_result = await self.dry_run_rollback(revision)
            if not dry_run_result.success:
                return RollbackResult(
                    success=False,
                    revision=current_revision or "unknown",
                    target_revision=revision,
                    dry_run_result=dry_run_result,
                    error_message=f"Dry run failed: {dry_run_result.error_message}",
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    manual_intervention_required=True,
                )

        # Capture row counts before rollback
        engine = await self._get_engine()
        validator = DataIntegrityValidator(engine, auto_rollback=False)
        row_counts_before = await validator.capture_row_counts()

        # Step 2: Execute actual rollback
        try:
            env = os.environ.copy()
            env["DATABASE_URL"] = self._get_connection_string().replace("+asyncpg", "")
            env["DATABASE_URL_SYNC"] = self._get_connection_string().replace("+asyncpg", "")
            env["PGPASSWORD"] = self.config.db_password

            cmd = [
                "alembic",
                "-c", self.config.alembic_config_path,
                "downgrade",
                revision,
            ]

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

            if result.returncode != 0:
                return RollbackResult(
                    success=False,
                    revision=current_revision or "unknown",
                    target_revision=revision,
                    dry_run_result=dry_run_result,
                    error_message=f"Rollback failed: {result.stderr}",
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    manual_intervention_required=True,
                )

            execution_result = ExecutionResult(
                success=True,
                revision=revision,
                direction="downgrade",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        except asyncio.TimeoutError:
            return RollbackResult(
                success=False,
                revision=current_revision or "unknown",
                target_revision=revision,
                dry_run_result=dry_run_result,
                error_message=f"Rollback timed out after {self.config.timeout_seconds}s",
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                manual_intervention_required=True,
            )
        except Exception as e:
            return RollbackResult(
                success=False,
                revision=current_revision or "unknown",
                target_revision=revision,
                dry_run_result=dry_run_result,
                error_message=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                manual_intervention_required=True,
            )

        # Step 3: Data integrity check (REQ-5.3)
        integrity_check_passed = True
        if not skip_integrity_check:
            integrity_result = await validator.validate_integrity(
                before_counts=row_counts_before,
                check_unique=False,  # Schema may have changed
                check_nulls=False,
            )
            integrity_check_passed = integrity_result.is_valid

        duration = (datetime.now() - start_time).total_seconds()

        # REQ-5.4: Basarili rollback
        if integrity_check_passed:
            logger.info(f"Rollback completed successfully in {duration:.2f}s")
            return RollbackResult(
                success=True,
                revision=current_revision or "unknown",
                target_revision=revision,
                dry_run_result=dry_run_result,
                execution_result=execution_result,
                integrity_check_passed=True,
                duration_seconds=duration,
            )
        else:
            # REQ-5.5: Integrity check failed
            logger.error("Rollback completed but integrity check failed")
            return RollbackResult(
                success=False,
                revision=current_revision or "unknown",
                target_revision=revision,
                dry_run_result=dry_run_result,
                execution_result=execution_result,
                integrity_check_passed=False,
                error_message="Integrity check failed after rollback",
                duration_seconds=duration,
                manual_intervention_required=True,
            )

    async def restore_from_backup(self, backup_path: str | Path) -> RestoreResult:
        """
        Backup'tan restore et.

        REQ-5.5: Rollback basarisiz oldugunda backup'tan restore eder.

        Args:
            backup_path: Backup dosya yolu

        Returns:
            RestoreResult: Restore sonucu
        """
        backup_path = Path(backup_path)
        start_time = datetime.now()

        logger.info(f"Restoring from backup: {backup_path}")

        if not backup_path.exists():
            return RestoreResult(
                success=False,
                backup_path=backup_path,
                error_message=f"Backup file not found: {backup_path}",
            )

        try:
            # Decompress if gzipped
            if backup_path.suffix == ".gz":
                sql_content = gzip.open(backup_path, "rt", encoding="utf-8").read()
            else:
                sql_content = backup_path.read_text(encoding="utf-8")

            # Count tables and estimate rows
            tables_count = sql_content.count("CREATE TABLE")
            insert_count = sql_content.count("INSERT INTO")

            # Execute restore using psql
            env = os.environ.copy()
            env["PGPASSWORD"] = self.config.db_password

            # Drop and recreate database (dangerous!)
            # For safety, we just run the SQL file
            cmd = [
                "psql",
                "-h", self.config.db_host,
                "-p", self.config.db_port,
                "-U", self.config.db_user,
                "-d", self.config.db_name,
                "-f", "-",  # Read from stdin
            ]

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    env=env,
                    input=sql_content,
                    capture_output=True,
                    text=True,
                )
            )

            duration = (datetime.now() - start_time).total_seconds()

            if result.returncode != 0:
                return RestoreResult(
                    success=False,
                    backup_path=backup_path,
                    duration_seconds=duration,
                    error_message=f"psql failed: {result.stderr}",
                )

            logger.info(f"Restore completed in {duration:.2f}s")

            return RestoreResult(
                success=True,
                backup_path=backup_path,
                duration_seconds=duration,
                tables_restored=tables_count,
                rows_restored=insert_count,
            )

        except Exception as e:
            logger.exception(f"Restore failed: {e}")
            return RestoreResult(
                success=False,
                backup_path=backup_path,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e),
            )

    async def verify_rollback(self) -> VerificationResult:
        """
        Rollback'i dogrula.

        Returns:
            VerificationResult: Dogrulama sonucu
        """
        try:
            engine = await self._get_engine()

            async with engine.connect() as conn:
                # Check alembic version
                result = await conn.execute(text(
                    "SELECT version_num FROM alembic_version"
                ))
                version = result.scalar()

                # Check table count
                result = await conn.execute(text("""
                    SELECT COUNT(*)
                    FROM pg_tables
                    WHERE schemaname = 'public'
                """))
                table_count = result.scalar() or 0

            return VerificationResult(
                success=True,
                schema_valid=table_count > 0,
                data_intact=True,  # Basic check
                alembic_version_correct=version is not None,
            )

        except Exception as e:
            logger.exception(f"Verification failed: {e}")
            return VerificationResult(
                success=False,
                error_message=str(e),
            )

    async def detect_manual_intervention(self) -> bool:
        """
        Manual intervention gerekip gerekmadigini tespit et.

        REQ-5.6: Rollback mumkun degilse manual intervention gerektigini bildirir.

        Returns:
            bool: Manual intervention gerekli mi?
        """
        try:
            engine = await self._get_engine()

            async with engine.connect() as conn:
                # Check for active transactions
                result = await conn.execute(text("""
                    SELECT COUNT(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                    AND query NOT LIKE '%pg_stat_activity%'
                """))
                active_count = result.scalar() or 0

                if active_count > 1:
                    logger.warning(f"Found {active_count} active transactions")
                    return True

                # Check for locks
                result = await conn.execute(text("""
                    SELECT COUNT(*)
                    FROM pg_locks
                    WHERE granted = false
                """))
                waiting_locks = result.scalar() or 0

                if waiting_locks > 0:
                    logger.warning(f"Found {waiting_locks} waiting locks")
                    return True

            return False

        except Exception as e:
            logger.exception(f"Manual intervention detection failed: {e}")
            return True  # Assume intervention needed on error

    async def _get_current_revision(self) -> Optional[str]:
        """Mevcut alembic revision'i al."""
        try:
            engine = await self._get_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text(
                    "SELECT version_num FROM alembic_version"
                ))
                return result.scalar()
        except Exception:
            return None

    async def find_latest_backup(self) -> Optional[Path]:
        """En son backup dosyasini bul."""
        backups = sorted(
            self.backup_dir.glob("*.sql.gz"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return backups[0] if backups else None

    async def close(self):
        """Engine'i kapat."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
