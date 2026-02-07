"""
Performance Analyzer - REQ-7

Migration performans analizi.
Migration'in performans etkisini analiz eder ve oneriler sunar.

Features:
    - EXPLAIN ANALYZE execution
    - Lock duration estimation
    - Migration time prediction
    - CONCURRENTLY recommendation
    - Downtime warning

Usage:
    analyzer = PerformanceAnalyzer(engine)
    result = await analyzer.explain_analyze("SELECT * FROM users")
    assessment = await analyzer.check_downtime_risk("abc123")
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


# ==================== DATA CLASSES ====================


@dataclass
class ExplainResult:
    """EXPLAIN ANALYZE sonucu."""

    sql: str
    plan: list[str]
    execution_time_ms: float
    planning_time_ms: float
    total_time_ms: float
    rows_affected: int = 0
    shared_hit_blocks: int = 0
    shared_read_blocks: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def is_efficient(self) -> bool:
        """Sorgu verimli mi?"""
        return self.execution_time_ms < 1000  # Under 1 second

    def get_summary(self) -> str:
        """Ozet rapor."""
        lines = [
            "EXPLAIN ANALYZE Result",
            f"SQL: {self.sql[:50]}...",
            f"Execution Time: {self.execution_time_ms:.2f}ms",
            f"Planning Time: {self.planning_time_ms:.2f}ms",
            f"Total Time: {self.total_time_ms:.2f}ms",
            f"Rows Affected: {self.rows_affected}",
            f"Efficient: {'YES' if self.is_efficient else 'NO'}",
        ]
        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)


@dataclass
class Recommendation:
    """Performans onerisi."""

    severity: str  # "info", "warning", "critical"
    category: str  # "index", "lock", "concurrency", "partitioning"
    message: str
    suggestion: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.category}: {self.message}"


@dataclass
class DowntimeAssessment:
    """Downtime degerlendirmesi."""

    requires_downtime: bool
    estimated_duration: timedelta
    lock_duration: timedelta
    affected_tables: list[str] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    risk_level: str = "low"  # "low", "medium", "high", "critical"

    def get_summary(self) -> str:
        """Ozet rapor."""
        lines = [
            "Downtime Assessment",
            f"Requires Downtime: {'YES' if self.requires_downtime else 'NO'}",
            f"Risk Level: {self.risk_level.upper()}",
            f"Estimated Duration: {self.estimated_duration}",
            f"Lock Duration: {self.lock_duration}",
            f"Affected Tables: {', '.join(self.affected_tables) or 'None'}",
        ]
        if self.recommendations:
            lines.append("Recommendations:")
            for r in self.recommendations:
                lines.append(f"  - {r}")
        return "\n".join(lines)


# ==================== PERFORMANCE ANALYZER ====================


class PerformanceAnalyzer:
    """
    Migration performans analizi.

    REQ-7 implementasyonu: EXPLAIN ANALYZE, lock tahmini,
    migration suresi tahmini, CONCURRENTLY onerisi, downtime uyarisi.

    Attributes:
        engine: Async database engine
    """

    # Size thresholds (rows)
    SMALL_TABLE = 10_000
    MEDIUM_TABLE = 100_000
    LARGE_TABLE = 1_000_000

    # Time thresholds
    DOWNTIME_WARNING_SECONDS = 300  # 5 minutes

    def __init__(self, engine: AsyncEngine):
        """
        PerformanceAnalyzer olustur.

        Args:
            engine: Async database engine
        """
        self.engine = engine

    async def explain_analyze(self, sql: str) -> ExplainResult:
        """
        EXPLAIN ANALYZE calistir.

        REQ-7.1: Migration analiz edildiginde EXPLAIN ANALYZE calistirir.

        Args:
            sql: Analiz edilecek SQL

        Returns:
            ExplainResult: Analiz sonucu
        """
        # Remove any existing EXPLAIN prefix
        clean_sql = sql.strip()
        if clean_sql.upper().startswith("EXPLAIN"):
            clean_sql = re.sub(r"^EXPLAIN\s+(ANALYZE\s+)?", "", clean_sql, flags=re.IGNORECASE)

        warnings = []
        plan = []
        execution_time = 0.0
        planning_time = 0.0
        rows_affected = 0

        try:
            async with self.engine.connect() as conn:
                # Run EXPLAIN ANALYZE
                result = await conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {clean_sql}"))
                rows = result.fetchall()

                for row in rows:
                    line = row[0]
                    plan.append(line)

                    # Parse timing info
                    if "Execution Time:" in line:
                        match = re.search(r"Execution Time:\s+([\d.]+)\s*ms", line)
                        if match:
                            execution_time = float(match.group(1))

                    if "Planning Time:" in line:
                        match = re.search(r"Planning Time:\s+([\d.]+)\s*ms", line)
                        if match:
                            planning_time = float(match.group(1))

                    # Check for warnings
                    if "Seq Scan" in line and "rows=" in line:
                        match = re.search(r"rows=(\d+)", line)
                        if match and int(match.group(1)) > self.LARGE_TABLE:
                            warnings.append("Sequential scan on large table - consider adding index")

                    if "Sort" in line and "external" in line.lower():
                        warnings.append("External sort detected - may need more work_mem")

        except Exception as e:
            logger.warning(f"EXPLAIN ANALYZE failed: {e}")
            # Return basic result for DDL statements
            plan = [f"(EXPLAIN not available for this statement: {e})"]

        return ExplainResult(
            sql=clean_sql,
            plan=plan,
            execution_time_ms=execution_time,
            planning_time_ms=planning_time,
            total_time_ms=execution_time + planning_time,
            rows_affected=rows_affected,
            warnings=warnings,
        )

    async def estimate_lock_duration(self, table_name: str) -> timedelta:
        """
        Lock suresini tahmin et.

        REQ-7.2: Execution plan incelendiginde table lock surelerini tahmin eder.

        Args:
            table_name: Tablo adi

        Returns:
            timedelta: Tahmini lock suresi
        """
        try:
            async with self.engine.connect() as conn:
                # Get table size
                result = await conn.execute(text("""
                    SELECT
                        pg_total_relation_size(:table_name) as total_size,
                        (SELECT reltuples FROM pg_class WHERE relname = :table_name) as row_count
                """), {"table_name": table_name})
                row = result.fetchone()

                if not row:
                    return timedelta(seconds=1)

                total_size = row[0] or 0
                row_count = row[1] or 0

                # Estimate based on size
                # Roughly 1 second per GB for simple operations
                size_gb = total_size / (1024 ** 3)
                base_seconds = max(1, size_gb)

                # Add factor for row count
                if row_count > self.LARGE_TABLE:
                    base_seconds *= 2
                elif row_count > self.MEDIUM_TABLE:
                    base_seconds *= 1.5

                return timedelta(seconds=base_seconds)

        except Exception as e:
            logger.warning(f"Lock duration estimation failed: {e}")
            return timedelta(seconds=10)  # Default estimate

    async def estimate_migration_time(self, revision: str) -> timedelta:
        """
        Migration suresini tahmin et.

        REQ-7.3: Affected rows hesaplandiginda migration suresini tahmin eder.

        Args:
            revision: Migration revision

        Returns:
            timedelta: Tahmini sure
        """
        # Get all table sizes
        total_estimate = timedelta(seconds=0)

        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("""
                    SELECT
                        tablename,
                        pg_total_relation_size(quote_ident(tablename)) as size,
                        (SELECT reltuples FROM pg_class WHERE relname = tablename) as rows
                    FROM pg_tables
                    WHERE schemaname = 'public'
                """))

                for row in result.fetchall():
                    table_name = row[0]
                    size = row[1] or 0
                    rows = row[2] or 0

                    # Estimate 1 second per 100MB
                    size_seconds = size / (100 * 1024 * 1024)
                    total_estimate += timedelta(seconds=max(0.1, size_seconds))

        except Exception as e:
            logger.warning(f"Migration time estimation failed: {e}")
            total_estimate = timedelta(seconds=30)  # Default

        # Add base overhead
        total_estimate += timedelta(seconds=5)

        return total_estimate

    async def check_concurrent_index(self, sql: str) -> list[Recommendation]:
        """
        CONCURRENTLY kullanim kontrolu.

        REQ-7.4: Index olusturuldugunda CONCURRENTLY option kullanimini onerir.

        Args:
            sql: SQL statement

        Returns:
            list[Recommendation]: Oneriler
        """
        recommendations = []
        sql_upper = sql.upper()

        # Check for CREATE INDEX without CONCURRENTLY
        if "CREATE INDEX" in sql_upper and "CONCURRENTLY" not in sql_upper:
            recommendations.append(Recommendation(
                severity="warning",
                category="concurrency",
                message="CREATE INDEX without CONCURRENTLY will lock the table",
                suggestion="Use 'CREATE INDEX CONCURRENTLY' to avoid blocking writes",
            ))

        # Check for DROP INDEX without CONCURRENTLY
        if "DROP INDEX" in sql_upper and "CONCURRENTLY" not in sql_upper:
            recommendations.append(Recommendation(
                severity="info",
                category="concurrency",
                message="DROP INDEX without CONCURRENTLY may block queries",
                suggestion="Consider using 'DROP INDEX CONCURRENTLY' for production",
            ))

        # Check for ALTER TABLE ADD COLUMN with NOT NULL
        if "ALTER TABLE" in sql_upper and "ADD COLUMN" in sql_upper:
            if "NOT NULL" in sql_upper and "DEFAULT" not in sql_upper:
                recommendations.append(Recommendation(
                    severity="critical",
                    category="lock",
                    message="ADD COLUMN NOT NULL without DEFAULT requires table rewrite",
                    suggestion="Add column as NULL first, update values, then add NOT NULL constraint",
                ))
            elif "DEFAULT" in sql_upper:
                recommendations.append(Recommendation(
                    severity="info",
                    category="lock",
                    message="ADD COLUMN with DEFAULT is fast in PostgreSQL 11+",
                    suggestion="Ensure you're using PostgreSQL 11 or later",
                ))

        return recommendations

    async def check_downtime_risk(self, revision: str) -> DowntimeAssessment:
        """
        Downtime riskini degerlendir.

        REQ-7.5 & REQ-7.6: Buyuk tablo degistiginde downtime uyarisi verir,
        5 dakikadan uzun surerse maintenance window onerir.

        Args:
            revision: Migration revision

        Returns:
            DowntimeAssessment: Degerlendirme sonucu
        """
        recommendations = []
        affected_tables = []
        requires_downtime = False
        risk_level = "low"

        # Get large tables
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("""
                    SELECT
                        tablename,
                        pg_total_relation_size(quote_ident(tablename)) as size,
                        (SELECT reltuples FROM pg_class WHERE relname = tablename) as rows
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY size DESC
                    LIMIT 10
                """))

                for row in result.fetchall():
                    table_name = row[0]
                    rows = row[2] or 0

                    if rows > self.LARGE_TABLE:
                        affected_tables.append(table_name)
                        risk_level = "high"
                        recommendations.append(Recommendation(
                            severity="warning",
                            category="partitioning",
                            message=f"Table '{table_name}' has {rows:,.0f} rows",
                            suggestion="Consider partitioning for large table migrations",
                        ))

        except Exception as e:
            logger.warning(f"Table analysis failed: {e}")

        # Estimate total duration
        estimated_duration = await self.estimate_migration_time(revision)

        # Calculate lock duration (simplified)
        lock_duration = timedelta(seconds=5)
        for table in affected_tables:
            lock_duration += await self.estimate_lock_duration(table)

        # REQ-7.6: Check if maintenance window needed
        if estimated_duration.total_seconds() > self.DOWNTIME_WARNING_SECONDS:
            requires_downtime = True
            risk_level = "critical"
            recommendations.append(Recommendation(
                severity="critical",
                category="lock",
                message=f"Migration estimated to take {estimated_duration}",
                suggestion="Schedule maintenance window for this migration",
            ))

        # Add general recommendations
        if affected_tables:
            recommendations.append(Recommendation(
                severity="info",
                category="lock",
                message="Multiple large tables affected",
                suggestion="Consider splitting migration into smaller chunks",
            ))

        return DowntimeAssessment(
            requires_downtime=requires_downtime,
            estimated_duration=estimated_duration,
            lock_duration=lock_duration,
            affected_tables=affected_tables,
            recommendations=recommendations,
            risk_level=risk_level,
        )

    async def get_table_statistics(self, table_name: str) -> dict:
        """Tablo istatistiklerini al."""
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("""
                    SELECT
                        pg_total_relation_size(:table_name) as total_size,
                        pg_table_size(:table_name) as table_size,
                        pg_indexes_size(:table_name) as indexes_size,
                        (SELECT reltuples FROM pg_class WHERE relname = :table_name) as row_count,
                        (SELECT n_live_tup FROM pg_stat_user_tables WHERE relname = :table_name) as live_tuples,
                        (SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname = :table_name) as dead_tuples
                """), {"table_name": table_name})
                row = result.fetchone()

                if row:
                    return {
                        "total_size": row[0],
                        "total_size_mb": (row[0] or 0) / (1024 * 1024),
                        "table_size": row[1],
                        "indexes_size": row[2],
                        "row_count": row[3],
                        "live_tuples": row[4],
                        "dead_tuples": row[5],
                        "bloat_ratio": (row[5] or 0) / max(1, row[4] or 1),
                    }

        except Exception as e:
            logger.warning(f"Failed to get table statistics: {e}")

        return {}

    async def analyze_migration_script(self, script: str) -> list[Recommendation]:
        """Migration script'i analiz et ve oneriler sun."""
        recommendations = []

        # Parse statements
        statements = [s.strip() for s in script.split(";") if s.strip()]

        for stmt in statements:
            stmt_upper = stmt.upper()

            # Check for concurrent index
            if "CREATE INDEX" in stmt_upper:
                recommendations.extend(await self.check_concurrent_index(stmt))

            # Check for ALTER TABLE
            if "ALTER TABLE" in stmt_upper:
                recommendations.extend(await self.check_concurrent_index(stmt))

                # Check for column type change
                if "ALTER COLUMN" in stmt_upper and "TYPE" in stmt_upper:
                    recommendations.append(Recommendation(
                        severity="warning",
                        category="lock",
                        message="ALTER COLUMN TYPE may require table rewrite",
                        suggestion="Test on staging with representative data volume",
                    ))

            # Check for TRUNCATE
            if "TRUNCATE" in stmt_upper:
                recommendations.append(Recommendation(
                    severity="critical",
                    category="data",
                    message="TRUNCATE will delete all data",
                    suggestion="Ensure backup exists before running this migration",
                ))

            # Check for DROP TABLE
            if "DROP TABLE" in stmt_upper:
                recommendations.append(Recommendation(
                    severity="critical",
                    category="data",
                    message="DROP TABLE will permanently delete table and data",
                    suggestion="Verify table is no longer needed and backup exists",
                ))

        return recommendations
