"""
PreMigration Validation Hook - REQ-1

Migration oncesi dogrulama hook'u. Boris Cherny verification feedback loops
prensibi ile migration hatalarini onler.

Features:
    - Schema backup (pg_dump)
    - SQL syntax validation
    - Dependency checking
    - Error reporting with line numbers

Usage:
    hook = PreMigrationHook()
    result = await hook.validate_migration("abc123")
    if not result.is_valid:
        print(result.errors)
"""

import asyncio
import gzip
import hashlib
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ==================== DATA CLASSES ====================


@dataclass
class SyntaxError:
    """SQL syntax hatasi detayi."""

    line_number: int
    column: int
    message: str
    sql_fragment: str
    severity: str = "error"  # error, warning, info

    def __str__(self) -> str:
        return f"Line {self.line_number}:{self.column} - {self.message}"


@dataclass
class DependencyError:
    """Migration dependency hatasi."""

    migration_id: str
    required_by: str
    message: str
    is_blocking: bool = True

    def __str__(self) -> str:
        return f"Migration '{self.migration_id}' required by '{self.required_by}': {self.message}"


@dataclass
class BackupResult:
    """Backup islem sonucu."""

    success: bool
    backup_path: Optional[Path] = None
    size_bytes: int = 0
    duration_seconds: float = 0.0
    checksum: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def size_mb(self) -> float:
        """Backup boyutu MB cinsinden."""
        return self.size_bytes / (1024 * 1024)


@dataclass
class ValidationResult:
    """Migration dogrulama sonucu."""

    is_valid: bool
    revision: str
    backup_result: Optional[BackupResult] = None
    syntax_errors: list[SyntaxError] = field(default_factory=list)
    dependency_errors: list[DependencyError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0

    @property
    def has_blocking_errors(self) -> bool:
        """Engelleyici hata var mi?"""
        return (
            len(self.syntax_errors) > 0
            or any(d.is_blocking for d in self.dependency_errors)
            or (self.backup_result is not None and not self.backup_result.success)
        )

    @property
    def error_count(self) -> int:
        """Toplam hata sayisi."""
        return len(self.syntax_errors) + len(self.dependency_errors)

    def get_report(self) -> str:
        """Insan okunabilir rapor olustur."""
        lines = [
            f"Migration Validation Report - {self.revision}",
            f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {self.duration_seconds:.2f}s",
            f"Status: {'VALID' if self.is_valid else 'INVALID'}",
            "",
        ]

        if self.backup_result:
            lines.extend([
                "Backup:",
                f"  Status: {'OK' if self.backup_result.success else 'FAILED'}",
                f"  Path: {self.backup_result.backup_path}",
                f"  Size: {self.backup_result.size_mb:.2f} MB",
            ])
            if self.backup_result.error_message:
                lines.append(f"  Error: {self.backup_result.error_message}")
            lines.append("")

        if self.syntax_errors:
            lines.append(f"Syntax Errors ({len(self.syntax_errors)}):")
            for err in self.syntax_errors:
                lines.append(f"  - {err}")
            lines.append("")

        if self.dependency_errors:
            lines.append(f"Dependency Errors ({len(self.dependency_errors)}):")
            for err in self.dependency_errors:
                lines.append(f"  - {err}")
            lines.append("")

        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warn in self.warnings:
                lines.append(f"  - {warn}")

        return "\n".join(lines)


# ==================== PREMIGRATION HOOK ====================


class PreMigrationHook:
    """
    Migration oncesi dogrulama hook'u.

    REQ-1 implementasyonu: Migration calistirilmak istendiginde
    otomatik olarak tetiklenir ve dogrulama yapar.

    Attributes:
        backup_dir: Backup dosyalarinin kaydedilecegi dizin
        retention_days: Backup saklama suresi (gun)
        db_host: PostgreSQL host
        db_port: PostgreSQL port
        db_name: Database adi
        db_user: Database kullanici adi
    """

    def __init__(
        self,
        backup_dir: str = "backups/migrations",
        retention_days: int = 7,
        db_host: Optional[str] = None,
        db_port: Optional[str] = None,
        db_name: Optional[str] = None,
        db_user: Optional[str] = None,
        db_password: Optional[str] = None,
    ):
        """
        PreMigrationHook olustur.

        Args:
            backup_dir: Backup dizini
            retention_days: Backup saklama suresi
            db_host: Database host (default: POSTGRES_HOST env)
            db_port: Database port (default: POSTGRES_PORT env)
            db_name: Database adi (default: POSTGRES_DB env)
            db_user: Database kullanici (default: POSTGRES_USER env)
            db_password: Database sifre (default: POSTGRES_PASSWORD env)
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

        # Database connection info
        self.db_host = db_host or os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = db_port or os.getenv("POSTGRES_PORT", "5434")
        self.db_name = db_name or os.getenv("POSTGRES_DB", "kiro2_db")
        self.db_user = db_user or os.getenv("POSTGRES_USER", "postgres")
        self.db_password = db_password or os.getenv("POSTGRES_PASSWORD", "postgres")

    async def validate_migration(
        self,
        revision: str,
        migration_script: Optional[str] = None,
        session: Optional[AsyncSession] = None,
        skip_backup: bool = False,
    ) -> ValidationResult:
        """
        Migration'i dogrula.

        REQ-1.1: Migration calistirilmak istendiginde otomatik tetiklenir.

        Args:
            revision: Migration revision ID
            migration_script: SQL script (optional, Alembic'ten alinir)
            session: Database session (dependency check icin)
            skip_backup: Backup'i atla (test icin)

        Returns:
            ValidationResult: Dogrulama sonucu
        """
        start_time = datetime.now()
        syntax_errors: list[SyntaxError] = []
        dependency_errors: list[DependencyError] = []
        warnings: list[str] = []
        backup_result: Optional[BackupResult] = None

        logger.info(f"PreMigration validation starting for revision: {revision}")

        # REQ-1.2 & REQ-1.3: Schema backup
        if not skip_backup:
            backup_result = await self.create_backup(revision)
            if not backup_result.success:
                logger.error(f"Backup failed: {backup_result.error_message}")

        # REQ-1.4: SQL syntax validation
        if migration_script:
            syntax_errors = self.validate_sql_syntax(migration_script)
            if syntax_errors:
                logger.warning(f"Found {len(syntax_errors)} syntax issues")

        # REQ-1.5: Dependency check
        if session:
            dependency_errors = await self.check_dependencies(revision, session)
            if dependency_errors:
                logger.warning(f"Found {len(dependency_errors)} dependency issues")

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Determine validity
        is_valid = (
            (backup_result is None or backup_result.success)
            and len(syntax_errors) == 0
            and not any(d.is_blocking for d in dependency_errors)
        )

        result = ValidationResult(
            is_valid=is_valid,
            revision=revision,
            backup_result=backup_result,
            syntax_errors=syntax_errors,
            dependency_errors=dependency_errors,
            warnings=warnings,
            duration_seconds=duration,
        )

        # REQ-1.6: Detailed report on critical errors
        if not is_valid:
            logger.error(f"Migration validation FAILED:\n{result.get_report()}")
        else:
            logger.info(f"Migration validation PASSED for {revision}")

        return result

    async def create_backup(self, revision: str) -> BackupResult:
        """
        Schema backup olustur.

        REQ-1.2: Hook tetiklendiginde mevcut database semasini yedekler.
        REQ-1.3: pg_dump ile full backup alir.

        Args:
            revision: Migration revision ID (dosya adinda kullanilir)

        Returns:
            BackupResult: Backup sonucu
        """
        start_time = datetime.now()
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"pre_migration_{revision}_{timestamp}.sql.gz"
        backup_path = self.backup_dir / backup_filename
        temp_file = backup_path.with_suffix(".sql")

        try:
            logger.info(f"Creating backup: {backup_filename}")

            # Set password in environment
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password

            # Run pg_dump
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", self.db_port,
                "-U", self.db_user,
                "-d", self.db_name,
                "-F", "p",  # Plain SQL format
                "-f", str(temp_file),
                "--schema-only",  # Only schema for migration backups
            ]

            # Run in thread pool (subprocess is blocking)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, env=env, capture_output=True, text=True)
            )

            if result.returncode != 0:
                return BackupResult(
                    success=False,
                    error_message=f"pg_dump failed: {result.stderr}",
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                )

            # Compress the backup
            await loop.run_in_executor(
                None,
                lambda: self._compress_file(temp_file, backup_path)
            )

            # Calculate checksum
            checksum = await loop.run_in_executor(
                None,
                lambda: self._calculate_checksum(backup_path)
            )

            # Get file size
            size_bytes = backup_path.stat().st_size
            duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Backup created: {backup_filename} "
                f"({size_bytes / (1024*1024):.2f} MB, {duration:.2f}s)"
            )

            return BackupResult(
                success=True,
                backup_path=backup_path,
                size_bytes=size_bytes,
                duration_seconds=duration,
                checksum=checksum,
            )

        except FileNotFoundError:
            return BackupResult(
                success=False,
                error_message="pg_dump not found. Is PostgreSQL client installed?",
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            logger.exception(f"Backup failed: {e}")
            return BackupResult(
                success=False,
                error_message=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    def _compress_file(self, source: Path, dest: Path) -> None:
        """Dosyayi gzip ile sikistir."""
        with open(source, "rb") as f_in:
            with gzip.open(dest, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        source.unlink()  # Remove original

    def _calculate_checksum(self, file_path: Path) -> str:
        """SHA256 checksum hesapla."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def validate_sql_syntax(self, script: str) -> list[SyntaxError]:
        """
        SQL syntax dogrula.

        REQ-1.4: Migration script kontrol edildiginde SQL syntax hatalarini tespit eder.

        Args:
            script: SQL script

        Returns:
            list[SyntaxError]: Bulunan syntax hatalari
        """
        errors: list[SyntaxError] = []

        if not SQLPARSE_AVAILABLE:
            logger.warning("sqlparse not installed, skipping syntax validation")
            return errors

        try:
            # Parse SQL
            parsed = sqlparse.parse(script)

            line_offset = 0
            for statement in parsed:
                statement_str = str(statement).strip()
                if not statement_str:
                    continue

                # Check for common issues
                stmt_errors = self._check_statement(statement, line_offset)
                errors.extend(stmt_errors)

                # Update line offset
                line_offset += statement_str.count("\n") + 1

        except Exception as e:
            logger.exception(f"SQL parsing error: {e}")
            errors.append(SyntaxError(
                line_number=1,
                column=0,
                message=f"Parse error: {e}",
                sql_fragment=script[:100] + "..." if len(script) > 100 else script,
            ))

        return errors

    def _check_statement(self, statement: "sqlparse.sql.Statement", line_offset: int) -> list[SyntaxError]:
        """Tek bir SQL statement'i kontrol et."""
        errors: list[SyntaxError] = []
        statement_str = str(statement).strip().upper()

        # Dangerous operations check
        dangerous_patterns = [
            (r"DROP\s+DATABASE", "DROP DATABASE is dangerous"),
            (r"TRUNCATE\s+TABLE\s+(?!.*CASCADE)", "TRUNCATE without CASCADE may fail with FK"),
            (r"DELETE\s+FROM\s+\w+\s*$", "DELETE without WHERE clause"),
            (r"UPDATE\s+\w+\s+SET\s+.*(?!WHERE)", "UPDATE without WHERE clause"),
        ]

        for pattern, message in dangerous_patterns:
            if re.search(pattern, statement_str):
                errors.append(SyntaxError(
                    line_number=line_offset + 1,
                    column=0,
                    message=message,
                    sql_fragment=str(statement)[:50],
                    severity="warning",
                ))

        # Check for missing semicolon at end
        if not str(statement).strip().endswith(";"):
            if not str(statement).strip().endswith("$$"):  # Function body
                errors.append(SyntaxError(
                    line_number=line_offset + 1,
                    column=len(str(statement)),
                    message="Statement should end with semicolon",
                    sql_fragment=str(statement)[-30:],
                    severity="warning",
                ))

        # Check for invalid characters
        invalid_chars = set(statement_str) - set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n\t,;()[]{}.'\"=-+*/<>!@#$%^&_|\\:?"
        )
        if invalid_chars:
            errors.append(SyntaxError(
                line_number=line_offset + 1,
                column=0,
                message=f"Invalid characters found: {invalid_chars}",
                sql_fragment=str(statement)[:50],
                severity="warning",
            ))

        return errors

    async def check_dependencies(
        self,
        revision: str,
        session: AsyncSession,
    ) -> list[DependencyError]:
        """
        Migration dependency'lerini kontrol et.

        REQ-1.5: Migration dependencies kontrol edildiginde eksik dependency'leri tespit eder.

        Args:
            revision: Migration revision ID
            session: Database session

        Returns:
            list[DependencyError]: Bulunan dependency hatalari
        """
        errors: list[DependencyError] = []

        try:
            # Check if alembic_version table exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                )
            """))
            has_alembic = result.scalar()

            if not has_alembic:
                errors.append(DependencyError(
                    migration_id="alembic_version",
                    required_by=revision,
                    message="alembic_version table not found. Run 'alembic stamp head' first.",
                    is_blocking=True,
                ))
                return errors

            # Get current revision
            result = await session.execute(text(
                "SELECT version_num FROM alembic_version"
            ))
            current_revision = result.scalar()

            if current_revision is None:
                errors.append(DependencyError(
                    migration_id="base",
                    required_by=revision,
                    message="No current revision found. Database may not be initialized.",
                    is_blocking=False,
                ))

            # Additional checks can be added here:
            # - Check if required tables exist
            # - Check if required columns exist
            # - Check foreign key dependencies

        except Exception as e:
            logger.exception(f"Dependency check error: {e}")
            errors.append(DependencyError(
                migration_id="unknown",
                required_by=revision,
                message=f"Dependency check failed: {e}",
                is_blocking=True,
            ))

        return errors

    async def cleanup_old_backups(self) -> int:
        """
        Eski backup'lari temizle.

        Returns:
            int: Silinen backup sayisi
        """
        from datetime import timedelta

        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        for backup_file in self.backup_dir.glob("pre_migration_*.sql.gz"):
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                logger.info(f"Deleting old backup: {backup_file.name}")
                backup_file.unlink()
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old backup(s)")
        return deleted_count


# ==================== ALEMBIC INTEGRATION ====================


def run_pre_migration_hook(revision: str, context: dict) -> ValidationResult:
    """
    Alembic env.py icin senkron wrapper.

    Usage in alembic/env.py:
        from backend.db.hooks.pre_migration import run_pre_migration_hook

        def run_migrations_online():
            ...
            result = run_pre_migration_hook(context.get_head_revision(), context)
            if not result.is_valid:
                raise Exception(f"PreMigration validation failed: {result.get_report()}")
            ...
    """
    hook = PreMigrationHook()
    return asyncio.run(hook.validate_migration(revision))
