"""
Migration History Tracker - REQ-6

Migration gecmisi takibi.
Tum migration'larin detayli gecmisini ve metriklerini kaydeder.

Features:
    - Revision tracking with metadata
    - Execution metrics collection
    - Error logging
    - Dependency graph visualization
    - Audit reporting for compliance

Usage:
    tracker = MigrationHistoryTracker(engine)
    await tracker.record_migration(info, execution)
    history = await tracker.get_history()
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


# ==================== DATA CLASSES ====================


@dataclass
class MigrationRecord:
    """Migration kaydi."""

    id: int
    revision: str
    direction: str  # "upgrade" or "downgrade"
    status: str  # "completed", "failed", "rolled_back"
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    author: Optional[str] = None
    description: Optional[str] = None
    error_message: Optional[str] = None
    affected_tables: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Dictionary'ye donustur."""
        return {
            "id": self.id,
            "revision": self.revision,
            "direction": self.direction,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "author": self.author,
            "description": self.description,
            "error_message": self.error_message,
            "affected_tables": self.affected_tables,
            "metadata": self.metadata,
        }


@dataclass
class AuditReport:
    """Audit raporu."""

    generated_at: datetime
    total_migrations: int
    successful_migrations: int
    failed_migrations: int
    rolled_back_migrations: int
    total_duration_ms: float
    average_duration_ms: float
    records: list[MigrationRecord] = field(default_factory=list)
    summary_by_month: dict = field(default_factory=dict)

    def to_json(self) -> str:
        """JSON'a donustur."""
        return json.dumps({
            "generated_at": self.generated_at.isoformat(),
            "total_migrations": self.total_migrations,
            "successful_migrations": self.successful_migrations,
            "failed_migrations": self.failed_migrations,
            "rolled_back_migrations": self.rolled_back_migrations,
            "total_duration_ms": self.total_duration_ms,
            "average_duration_ms": self.average_duration_ms,
            "summary_by_month": self.summary_by_month,
            "records": [r.to_dict() for r in self.records],
        }, indent=2)


# ==================== MIGRATION HISTORY TRACKER ====================


class MigrationHistoryTracker:
    """
    Migration gecmisi takibi.

    REQ-6 implementasyonu: Migration detaylarini kaydeder,
    filtreleme/arama destekler, dependency graph ve audit raporu olusturur.

    Attributes:
        engine: Async database engine
    """

    TABLE_NAME = "migration_history"

    def __init__(self, engine: AsyncEngine):
        """
        MigrationHistoryTracker olustur.

        Args:
            engine: Async database engine
        """
        self.engine = engine

    async def initialize(self):
        """History tablosunu olustur."""
        async with self.engine.begin() as conn:
            await conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    revision VARCHAR(255) NOT NULL,
                    direction VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    duration_ms FLOAT DEFAULT 0,
                    author VARCHAR(255),
                    description TEXT,
                    error_message TEXT,
                    affected_tables TEXT,
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))

            # Create indexes
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_revision
                ON {self.TABLE_NAME}(revision)
            """))
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_status
                ON {self.TABLE_NAME}(status)
            """))
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_started_at
                ON {self.TABLE_NAME}(started_at)
            """))

        logger.info(f"Migration history table '{self.TABLE_NAME}' initialized")

    async def record_migration(
        self,
        revision: str,
        direction: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        duration_ms: float = 0.0,
        author: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None,
        affected_tables: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> int:
        """
        Migration kaydini ekle.

        REQ-6.1: Migration calistirildiginda migration detaylarini kaydeder.
        REQ-6.2: revision, timestamp, author, description, execution time kaydeder.

        Args:
            revision: Migration revision
            direction: "upgrade" or "downgrade"
            status: "completed", "failed", "rolled_back"
            started_at: Baslangic zamani
            completed_at: Bitis zamani
            duration_ms: Sure (milisaniye)
            author: Yapan kisi
            description: Aciklama
            error_message: Hata mesaji (varsa)
            affected_tables: Etkilenen tablolar
            metadata: Ek metadata

        Returns:
            int: Eklenen kaydin ID'si
        """
        async with self.engine.begin() as conn:
            result = await conn.execute(text(f"""
                INSERT INTO {self.TABLE_NAME}
                (revision, direction, status, started_at, completed_at,
                 duration_ms, author, description, error_message,
                 affected_tables, metadata)
                VALUES
                (:revision, :direction, :status, :started_at, :completed_at,
                 :duration_ms, :author, :description, :error_message,
                 :affected_tables, :metadata)
                RETURNING id
            """), {
                "revision": revision,
                "direction": direction,
                "status": status,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_ms": duration_ms,
                "author": author,
                "description": description,
                "error_message": error_message,
                "affected_tables": ",".join(affected_tables) if affected_tables else None,
                "metadata": json.dumps(metadata or {}),
            })

            record_id = result.scalar()

        # REQ-6.3: Basarisiz migration loglama
        if status == "failed":
            logger.error(
                f"Migration {revision} failed: {error_message}",
                extra={"revision": revision, "direction": direction},
            )
        else:
            logger.info(
                f"Migration {revision} {direction} {status} in {duration_ms:.0f}ms",
                extra={"revision": revision, "direction": direction},
            )

        return record_id

    async def get_history(
        self,
        revision: Optional[str] = None,
        status: Optional[str] = None,
        direction: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MigrationRecord]:
        """
        Migration gecmisini sorgula.

        REQ-6.4: History sorgulandiginda filtreleme ve arama destekler.

        Args:
            revision: Revision filtresi
            status: Status filtresi
            direction: Direction filtresi
            start_date: Baslangic tarihi
            end_date: Bitis tarihi
            limit: Maksimum kayit sayisi
            offset: Atlama sayisi

        Returns:
            list[MigrationRecord]: Migration kayitlari
        """
        conditions = ["1=1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if revision:
            conditions.append("revision = :revision")
            params["revision"] = revision

        if status:
            conditions.append("status = :status")
            params["status"] = status

        if direction:
            conditions.append("direction = :direction")
            params["direction"] = direction

        if start_date:
            conditions.append("started_at >= :start_date")
            params["start_date"] = start_date

        if end_date:
            conditions.append("started_at <= :end_date")
            params["end_date"] = end_date

        where_clause = " AND ".join(conditions)

        async with self.engine.connect() as conn:
            result = await conn.execute(text(f"""
                SELECT id, revision, direction, status, started_at, completed_at,
                       duration_ms, author, description, error_message,
                       affected_tables, metadata
                FROM {self.TABLE_NAME}
                WHERE {where_clause}
                ORDER BY started_at DESC
                LIMIT :limit OFFSET :offset
            """), params)

            records = []
            for row in result.fetchall():
                records.append(MigrationRecord(
                    id=row[0],
                    revision=row[1],
                    direction=row[2],
                    status=row[3],
                    started_at=row[4],
                    completed_at=row[5],
                    duration_ms=row[6] or 0.0,
                    author=row[7],
                    description=row[8],
                    error_message=row[9],
                    affected_tables=row[10].split(",") if row[10] else [],
                    metadata=json.loads(row[11]) if row[11] else {},
                ))

            return records

    async def get_dependency_graph(self) -> dict:
        """
        Migration dependency graph'i olustur.

        REQ-6.5: Migration chain goruntuleme.

        Returns:
            dict: Dependency graph {revision: [dependencies]}
        """
        async with self.engine.connect() as conn:
            # Get all unique revisions
            result = await conn.execute(text(f"""
                SELECT DISTINCT revision
                FROM {self.TABLE_NAME}
                WHERE direction = 'upgrade'
                AND status = 'completed'
                ORDER BY revision
            """))

            revisions = [row[0] for row in result.fetchall()]

            # Build simple linear dependency graph
            graph = {}
            for i, rev in enumerate(revisions):
                if i == 0:
                    graph[rev] = []  # First revision has no dependencies
                else:
                    graph[rev] = [revisions[i - 1]]  # Depends on previous

            return graph

    async def generate_audit_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AuditReport:
        """
        Audit raporu olustur.

        REQ-6.6: Compliance icin detayli log saglar.

        Args:
            start_date: Rapor baslangic tarihi
            end_date: Rapor bitis tarihi

        Returns:
            AuditReport: Audit raporu
        """
        # Get all records in date range
        records = await self.get_history(
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )

        # Calculate statistics
        total = len(records)
        successful = len([r for r in records if r.status == "completed"])
        failed = len([r for r in records if r.status == "failed"])
        rolled_back = len([r for r in records if r.status == "rolled_back"])

        total_duration = sum(r.duration_ms for r in records)
        avg_duration = total_duration / total if total > 0 else 0

        # Summary by month
        monthly_summary: dict[str, dict] = {}
        for record in records:
            month_key = record.started_at.strftime("%Y-%m")
            if month_key not in monthly_summary:
                monthly_summary[month_key] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                }
            monthly_summary[month_key]["total"] += 1
            if record.status == "completed":
                monthly_summary[month_key]["successful"] += 1
            elif record.status == "failed":
                monthly_summary[month_key]["failed"] += 1

        return AuditReport(
            generated_at=datetime.now(),
            total_migrations=total,
            successful_migrations=successful,
            failed_migrations=failed,
            rolled_back_migrations=rolled_back,
            total_duration_ms=total_duration,
            average_duration_ms=avg_duration,
            records=records,
            summary_by_month=monthly_summary,
        )

    async def get_latest_revision(self) -> Optional[str]:
        """En son basarili revision'i al."""
        async with self.engine.connect() as conn:
            result = await conn.execute(text(f"""
                SELECT revision
                FROM {self.TABLE_NAME}
                WHERE status = 'completed' AND direction = 'upgrade'
                ORDER BY completed_at DESC
                LIMIT 1
            """))
            row = result.fetchone()
            return row[0] if row else None

    async def get_migration_count(self) -> dict[str, int]:
        """Migration sayilarini al."""
        async with self.engine.connect() as conn:
            result = await conn.execute(text(f"""
                SELECT status, COUNT(*)
                FROM {self.TABLE_NAME}
                GROUP BY status
            """))

            counts = {"total": 0, "completed": 0, "failed": 0, "rolled_back": 0}
            for row in result.fetchall():
                counts[row[0]] = row[1]
                counts["total"] += row[1]

            return counts
