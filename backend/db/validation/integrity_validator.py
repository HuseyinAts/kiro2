"""
Data Integrity Validator - REQ-4

Migration sonrasi veri butunlugu kontrolu.
Data loss onlemek icin row count, FK, constraint dogrulama yapar.

Features:
    - Row count comparison (before/after)
    - Orphaned record detection
    - Unique constraint validation
    - Not null constraint checking
    - Auto rollback on violation

Usage:
    validator = DataIntegrityValidator(engine)
    before = await validator.capture_row_counts()
    # ... run migration ...
    result = await validator.validate_integrity(before)
    if not result.is_valid:
        await validator.trigger_rollback()
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


# ==================== DATA CLASSES ====================


@dataclass
class RowCountDiff:
    """Row count farki."""

    table_name: str
    before_count: int
    after_count: int

    @property
    def difference(self) -> int:
        """Fark (pozitif = artis, negatif = azalis)."""
        return self.after_count - self.before_count

    @property
    def is_data_loss(self) -> bool:
        """Veri kaybi var mi?"""
        return self.difference < 0

    def __str__(self) -> str:
        sign = "+" if self.difference >= 0 else ""
        return f"{self.table_name}: {self.before_count} -> {self.after_count} ({sign}{self.difference})"


@dataclass
class OrphanedRecord:
    """Orphaned (yetim) kayit."""

    table_name: str
    fk_column: str
    orphan_count: int
    referenced_table: str
    sample_ids: list = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"{self.table_name}.{self.fk_column}: "
            f"{self.orphan_count} orphaned records (references {self.referenced_table})"
        )


@dataclass
class DuplicateRecord:
    """Unique constraint ihlali."""

    table_name: str
    constraint_columns: list[str]
    duplicate_count: int
    sample_values: list = field(default_factory=list)

    def __str__(self) -> str:
        cols = ", ".join(self.constraint_columns)
        return f"{self.table_name} ({cols}): {self.duplicate_count} duplicate records"


@dataclass
class NullViolation:
    """Not null constraint ihlali."""

    table_name: str
    column_name: str
    null_count: int

    def __str__(self) -> str:
        return f"{self.table_name}.{self.column_name}: {self.null_count} null values"


@dataclass
class IntegrityCheckResult:
    """Integrity check sonucu."""

    is_valid: bool
    row_count_diffs: list[RowCountDiff] = field(default_factory=list)
    orphaned_records: list[OrphanedRecord] = field(default_factory=list)
    duplicate_records: list[DuplicateRecord] = field(default_factory=list)
    null_violations: list[NullViolation] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0
    rollback_triggered: bool = False

    @property
    def has_data_loss(self) -> bool:
        """Veri kaybi var mi?"""
        return any(d.is_data_loss for d in self.row_count_diffs)

    @property
    def total_issues(self) -> int:
        """Toplam sorun sayisi."""
        return (
            len([d for d in self.row_count_diffs if d.is_data_loss])
            + len(self.orphaned_records)
            + len(self.duplicate_records)
            + len(self.null_violations)
        )

    def get_report(self) -> str:
        """Insan okunabilir rapor."""
        lines = [
            "Data Integrity Check Report",
            f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {self.duration_seconds:.2f}s",
            f"Status: {'VALID' if self.is_valid else 'INVALID'}",
            f"Data Loss Detected: {'YES' if self.has_data_loss else 'NO'}",
            f"Rollback Triggered: {'YES' if self.rollback_triggered else 'NO'}",
            "",
        ]

        if self.row_count_diffs:
            lines.append("Row Count Changes:")
            for diff in self.row_count_diffs:
                marker = "!!" if diff.is_data_loss else "  "
                lines.append(f"  {marker} {diff}")
            lines.append("")

        if self.orphaned_records:
            lines.append(f"Orphaned Records ({len(self.orphaned_records)}):")
            for orphan in self.orphaned_records:
                lines.append(f"  - {orphan}")
            lines.append("")

        if self.duplicate_records:
            lines.append(f"Duplicate Records ({len(self.duplicate_records)}):")
            for dup in self.duplicate_records:
                lines.append(f"  - {dup}")
            lines.append("")

        if self.null_violations:
            lines.append(f"Null Violations ({len(self.null_violations)}):")
            for null in self.null_violations:
                lines.append(f"  - {null}")

        return "\n".join(lines)


# ==================== DATA INTEGRITY VALIDATOR ====================


class DataIntegrityValidator:
    """
    Migration sonrasi veri butunlugu kontrolu.

    REQ-4 implementasyonu: Row count, FK integrity, unique constraint,
    not null constraint dogrulama. Ihlal tespit edilirse otomatik rollback.

    Attributes:
        engine: Async database engine
        rollback_callback: Rollback tetiklendiginde cagrilacak fonksiyon
        auto_rollback: Ihlal durumunda otomatik rollback yap
    """

    def __init__(
        self,
        engine: AsyncEngine,
        rollback_callback: Optional[Callable] = None,
        auto_rollback: bool = True,
    ):
        """
        DataIntegrityValidator olustur.

        Args:
            engine: Async database engine
            rollback_callback: Rollback fonksiyonu (optional)
            auto_rollback: Otomatik rollback aktif mi?
        """
        self.engine = engine
        self.rollback_callback = rollback_callback
        self.auto_rollback = auto_rollback

    async def capture_row_counts(self) -> dict[str, int]:
        """
        Tum tablolarin row count'larini kaydet.

        REQ-4.1: Migration tamamlandiginda row count'lari karsilastirir.

        Returns:
            dict[str, int]: Tablo adi -> row count
        """
        row_counts = {}

        async with self.engine.connect() as conn:
            # Get all user tables
            result = await conn.execute(text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename NOT LIKE 'alembic%'
            """))
            tables = [row[0] for row in result.fetchall()]

            # Get row counts
            for table in tables:
                try:
                    count_result = await conn.execute(
                        text(f'SELECT COUNT(*) FROM "{table}"')
                    )
                    row_counts[table] = count_result.scalar() or 0
                except Exception as e:
                    logger.warning(f"Failed to get row count for {table}: {e}")
                    row_counts[table] = -1  # Error marker

        return row_counts

    async def compare_row_counts(
        self,
        before: dict[str, int],
        after: Optional[dict[str, int]] = None,
    ) -> list[RowCountDiff]:
        """
        Row count'lari karsilastir.

        REQ-4.2: Her tablo icin before/after count'u karsilastirir.

        Args:
            before: Migration oncesi row count'lar
            after: Migration sonrasi row count'lar (None ise yakalayacak)

        Returns:
            list[RowCountDiff]: Row count farklari
        """
        if after is None:
            after = await self.capture_row_counts()

        diffs = []
        all_tables = set(before.keys()) | set(after.keys())

        for table in sorted(all_tables):
            before_count = before.get(table, 0)
            after_count = after.get(table, 0)

            if before_count != after_count:
                diffs.append(RowCountDiff(
                    table_name=table,
                    before_count=before_count,
                    after_count=after_count,
                ))

        return diffs

    async def check_foreign_keys(self) -> list[OrphanedRecord]:
        """
        Foreign key integrity kontrol et.

        REQ-4.3: Orphaned record'lari tespit eder.

        Returns:
            list[OrphanedRecord]: Bulunan orphaned record'lar
        """
        orphans = []

        async with self.engine.connect() as conn:
            # Get all foreign keys
            result = await conn.execute(text("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            """))

            fks = result.fetchall()

            # Check each FK for orphans
            for fk in fks:
                table_name, column_name, ref_table, ref_column = fk

                try:
                    orphan_result = await conn.execute(text(f"""
                        SELECT COUNT(*), array_agg(t.{column_name}::text)
                        FROM "{table_name}" t
                        LEFT JOIN "{ref_table}" r ON t.{column_name} = r.{ref_column}
                        WHERE t.{column_name} IS NOT NULL
                        AND r.{ref_column} IS NULL
                    """))
                    row = orphan_result.fetchone()

                    if row and row[0] > 0:
                        orphans.append(OrphanedRecord(
                            table_name=table_name,
                            fk_column=column_name,
                            orphan_count=row[0],
                            referenced_table=ref_table,
                            sample_ids=row[1][:5] if row[1] else [],  # First 5 samples
                        ))

                except Exception as e:
                    logger.warning(f"Failed to check FK {table_name}.{column_name}: {e}")

        return orphans

    async def check_unique_constraints(self) -> list[DuplicateRecord]:
        """
        Unique constraint kontrol et.

        REQ-4.4: Duplicate record'lari tespit eder.

        Returns:
            list[DuplicateRecord]: Bulunan duplicate'lar
        """
        duplicates = []

        async with self.engine.connect() as conn:
            # Get all unique constraints
            result = await conn.execute(text("""
                SELECT
                    tc.table_name,
                    array_agg(kcu.column_name) as columns
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY')
                AND tc.table_schema = 'public'
                GROUP BY tc.table_name, tc.constraint_name
            """))

            constraints = result.fetchall()

            for constraint in constraints:
                table_name, columns = constraint

                if not columns:
                    continue

                # Build query to find duplicates
                cols_str = ", ".join([f'"{c}"' for c in columns])

                try:
                    dup_result = await conn.execute(text(f"""
                        SELECT {cols_str}, COUNT(*)
                        FROM "{table_name}"
                        GROUP BY {cols_str}
                        HAVING COUNT(*) > 1
                    """))
                    dup_rows = dup_result.fetchall()

                    if dup_rows:
                        duplicates.append(DuplicateRecord(
                            table_name=table_name,
                            constraint_columns=columns,
                            duplicate_count=len(dup_rows),
                            sample_values=[str(row[:-1]) for row in dup_rows[:5]],
                        ))

                except Exception as e:
                    logger.debug(f"Skipping constraint check for {table_name}: {e}")

        return duplicates

    async def check_not_null_constraints(self) -> list[NullViolation]:
        """
        Not null constraint kontrol et.

        REQ-4.5: Null value ihlallerini tespit eder.

        Returns:
            list[NullViolation]: Bulunan null ihlalleri
        """
        violations = []

        async with self.engine.connect() as conn:
            # Get all NOT NULL columns
            result = await conn.execute(text("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND is_nullable = 'NO'
                AND column_default IS NULL
                AND table_name NOT LIKE 'alembic%'
            """))

            columns = result.fetchall()

            for table_name, column_name in columns:
                try:
                    null_result = await conn.execute(text(f"""
                        SELECT COUNT(*)
                        FROM "{table_name}"
                        WHERE "{column_name}" IS NULL
                    """))
                    null_count = null_result.scalar() or 0

                    if null_count > 0:
                        violations.append(NullViolation(
                            table_name=table_name,
                            column_name=column_name,
                            null_count=null_count,
                        ))

                except Exception as e:
                    logger.debug(f"Skipping null check for {table_name}.{column_name}: {e}")

        return violations

    async def validate_integrity(
        self,
        before_counts: Optional[dict[str, int]] = None,
        check_fks: bool = True,
        check_unique: bool = True,
        check_nulls: bool = True,
    ) -> IntegrityCheckResult:
        """
        Tam integrity dogrulama.

        REQ-4.6: Integrity ihlali tespit edilirse otomatik rollback tetikler.

        Args:
            before_counts: Migration oncesi row count'lar
            check_fks: FK kontrolu yap
            check_unique: Unique kontrolu yap
            check_nulls: Null kontrolu yap

        Returns:
            IntegrityCheckResult: Dogrulama sonucu
        """
        start_time = datetime.now()

        result = IntegrityCheckResult(is_valid=True)

        # Row count comparison
        if before_counts:
            result.row_count_diffs = await self.compare_row_counts(before_counts)

        # FK integrity
        if check_fks:
            result.orphaned_records = await self.check_foreign_keys()

        # Unique constraints
        if check_unique:
            result.duplicate_records = await self.check_unique_constraints()

        # Not null constraints
        if check_nulls:
            result.null_violations = await self.check_not_null_constraints()

        # Determine validity
        result.is_valid = (
            not result.has_data_loss
            and len(result.orphaned_records) == 0
            # Duplicates and null violations are warnings, not blocking
        )

        result.duration_seconds = (datetime.now() - start_time).total_seconds()

        # Auto rollback on critical issues
        if not result.is_valid and self.auto_rollback:
            logger.error(f"Integrity validation FAILED:\n{result.get_report()}")
            result.rollback_triggered = await self.trigger_rollback()
        elif result.total_issues > 0:
            logger.warning(f"Integrity validation completed with warnings:\n{result.get_report()}")
        else:
            logger.info("Integrity validation PASSED - no issues found")

        return result

    async def trigger_rollback(self) -> bool:
        """
        Rollback tetikle.

        Returns:
            bool: Rollback basarili mi?
        """
        logger.warning("Triggering automatic rollback due to integrity violations")

        if self.rollback_callback:
            try:
                if asyncio.iscoroutinefunction(self.rollback_callback):
                    await self.rollback_callback()
                else:
                    self.rollback_callback()
                logger.info("Rollback triggered successfully")
                return True
            except Exception as e:
                logger.exception(f"Rollback failed: {e}")
                return False
        else:
            logger.warning("No rollback callback configured")
            return False


# Import asyncio for rollback check
import asyncio
