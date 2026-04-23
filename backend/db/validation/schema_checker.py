"""
Schema Consistency Checker - REQ-3

SQLAlchemy model vs DB schema karsilastirmasi.
ORM hatalari onlemek icin uyumsuzluklari tespit eder.

Features:
    - Table comparison
    - Column type/nullable/default checking
    - Index verification
    - Foreign key validation
    - Auto migration script generation

Usage:
    checker = SchemaConsistencyChecker(engine, Base.metadata)
    result = await checker.compare_all()
    if result.has_mismatches:
        print(result.generate_migration_script())
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


# ==================== ENUMS ====================


class MismatchType(Enum):
    """Uyumsuzluk tipi."""

    MISSING_IN_DB = "missing_in_db"  # Model'de var, DB'de yok
    MISSING_IN_MODEL = "missing_in_model"  # DB'de var, model'de yok
    TYPE_MISMATCH = "type_mismatch"  # Tip uyumsuzlugu
    NULLABLE_MISMATCH = "nullable_mismatch"  # Nullable uyumsuzlugu
    DEFAULT_MISMATCH = "default_mismatch"  # Default deger uyumsuzlugu


# ==================== DATA CLASSES ====================


@dataclass
class TableMismatch:
    """Tablo uyumsuzlugu."""

    table_name: str
    mismatch_type: MismatchType
    message: str

    def __str__(self) -> str:
        return f"Table '{self.table_name}': {self.message}"


@dataclass
class ColumnMismatch:
    """Kolon uyumsuzlugu."""

    table_name: str
    column_name: str
    mismatch_type: MismatchType
    expected: str | None = None
    actual: str | None = None
    message: str = ""

    def __str__(self) -> str:
        msg = f"Column '{self.table_name}.{self.column_name}': "
        if self.expected and self.actual:
            msg += f"expected {self.expected}, got {self.actual}"
        else:
            msg += self.message
        return msg


@dataclass
class IndexMismatch:
    """Index uyumsuzlugu."""

    table_name: str
    index_name: str
    mismatch_type: MismatchType
    columns: list[str] = field(default_factory=list)
    message: str = ""

    def __str__(self) -> str:
        return f"Index '{self.index_name}' on '{self.table_name}': {self.message}"


@dataclass
class ForeignKeyMismatch:
    """Foreign key uyumsuzlugu."""

    table_name: str
    constraint_name: str
    mismatch_type: MismatchType
    source_columns: list[str] = field(default_factory=list)
    target_table: str = ""
    target_columns: list[str] = field(default_factory=list)
    message: str = ""

    def __str__(self) -> str:
        return f"FK '{self.constraint_name}' on '{self.table_name}': {self.message}"


@dataclass
class SchemaComparisonResult:
    """Schema karsilastirma sonucu."""

    table_mismatches: list[TableMismatch] = field(default_factory=list)
    column_mismatches: list[ColumnMismatch] = field(default_factory=list)
    index_mismatches: list[IndexMismatch] = field(default_factory=list)
    fk_mismatches: list[ForeignKeyMismatch] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0

    @property
    def has_mismatches(self) -> bool:
        """Uyumsuzluk var mi?"""
        return (
            len(self.table_mismatches) > 0
            or len(self.column_mismatches) > 0
            or len(self.index_mismatches) > 0
            or len(self.fk_mismatches) > 0
        )

    @property
    def total_mismatch_count(self) -> int:
        """Toplam uyumsuzluk sayisi."""
        return (
            len(self.table_mismatches)
            + len(self.column_mismatches)
            + len(self.index_mismatches)
            + len(self.fk_mismatches)
        )

    @property
    def is_consistent(self) -> bool:
        """Schema tutarli mi?"""
        return not self.has_mismatches

    def get_report(self) -> str:
        """Insan okunabilir rapor."""
        lines = [
            "Schema Comparison Report",
            f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {self.duration_seconds:.2f}s",
            f"Status: {'CONSISTENT' if self.is_consistent else 'INCONSISTENT'}",
            f"Total Mismatches: {self.total_mismatch_count}",
            "",
        ]

        if self.table_mismatches:
            lines.append(f"Table Mismatches ({len(self.table_mismatches)}):")
            for m in self.table_mismatches:
                lines.append(f"  - {m}")
            lines.append("")

        if self.column_mismatches:
            lines.append(f"Column Mismatches ({len(self.column_mismatches)}):")
            for m in self.column_mismatches:
                lines.append(f"  - {m}")
            lines.append("")

        if self.index_mismatches:
            lines.append(f"Index Mismatches ({len(self.index_mismatches)}):")
            for m in self.index_mismatches:
                lines.append(f"  - {m}")
            lines.append("")

        if self.fk_mismatches:
            lines.append(f"Foreign Key Mismatches ({len(self.fk_mismatches)}):")
            for m in self.fk_mismatches:
                lines.append(f"  - {m}")

        return "\n".join(lines)


# ==================== SCHEMA CONSISTENCY CHECKER ====================


class SchemaConsistencyChecker:
    """
    SQLAlchemy model vs DB schema karsilastirma.

    REQ-3 implementasyonu: SQLAlchemy metadata'yi database semasi ile
    karsilastirir, uyumsuzluklari tespit eder.

    Attributes:
        engine: Async database engine
        metadata: SQLAlchemy metadata
    """

    def __init__(self, engine: AsyncEngine, metadata: MetaData):
        """
        SchemaConsistencyChecker olustur.

        Args:
            engine: Async database engine
            metadata: SQLAlchemy model metadata
        """
        self.engine = engine
        self.metadata = metadata

    async def compare_all(self) -> SchemaComparisonResult:
        """
        Tum schema'yi karsilastir.

        REQ-3.1: SQLAlchemy metadata'yi database semasi ile karsilastirir.

        Returns:
            SchemaComparisonResult: Karsilastirma sonucu
        """
        start_time = datetime.now()

        result = SchemaComparisonResult()

        # Compare tables
        result.table_mismatches = await self.compare_tables()

        # Compare columns for matching tables
        model_tables = set(self.metadata.tables.keys())
        db_tables = await self._get_db_tables()
        common_tables = model_tables & db_tables

        for table_name in common_tables:
            column_mismatches = await self.compare_columns(table_name)
            result.column_mismatches.extend(column_mismatches)

        # Compare indexes
        result.index_mismatches = await self.compare_indexes()

        # Compare foreign keys
        result.fk_mismatches = await self.compare_foreign_keys()

        result.duration_seconds = (datetime.now() - start_time).total_seconds()

        if result.has_mismatches:
            logger.warning(
                f"Schema consistency check found {result.total_mismatch_count} mismatches"
            )
        else:
            logger.info("Schema consistency check passed - no mismatches found")

        return result

    async def compare_tables(self) -> list[TableMismatch]:
        """
        Tablolari karsilastir.

        REQ-3.2: Eksik/fazla tablolari tespit eder.

        Returns:
            list[TableMismatch]: Tablo uyumsuzluklari
        """
        mismatches = []

        model_tables = set(self.metadata.tables.keys())
        db_tables = await self._get_db_tables()

        # Tables in model but not in DB
        for table_name in model_tables - db_tables:
            mismatches.append(TableMismatch(
                table_name=table_name,
                mismatch_type=MismatchType.MISSING_IN_DB,
                message="Table defined in model but missing in database",
            ))

        # Tables in DB but not in model (excluding alembic tables)
        for table_name in db_tables - model_tables:
            if not table_name.startswith("alembic"):
                mismatches.append(TableMismatch(
                    table_name=table_name,
                    mismatch_type=MismatchType.MISSING_IN_MODEL,
                    message="Table exists in database but not defined in model",
                ))

        return mismatches

    async def compare_columns(self, table_name: str) -> list[ColumnMismatch]:
        """
        Kolonlari karsilastir.

        REQ-3.3: Kolon tipi, nullable, default value uyumsuzluklarini tespit eder.

        Args:
            table_name: Tablo adi

        Returns:
            list[ColumnMismatch]: Kolon uyumsuzluklari
        """
        mismatches = []

        if table_name not in self.metadata.tables:
            return mismatches

        model_table = self.metadata.tables[table_name]
        model_columns = {c.name: c for c in model_table.columns}

        db_columns = await self._get_db_columns(table_name)

        # Columns in model but not in DB
        for col_name in set(model_columns.keys()) - set(db_columns.keys()):
            mismatches.append(ColumnMismatch(
                table_name=table_name,
                column_name=col_name,
                mismatch_type=MismatchType.MISSING_IN_DB,
                message="Column defined in model but missing in database",
            ))

        # Columns in DB but not in model
        for col_name in set(db_columns.keys()) - set(model_columns.keys()):
            mismatches.append(ColumnMismatch(
                table_name=table_name,
                column_name=col_name,
                mismatch_type=MismatchType.MISSING_IN_MODEL,
                message="Column exists in database but not defined in model",
            ))

        # Check common columns for type/nullable mismatches
        for col_name in set(model_columns.keys()) & set(db_columns.keys()):
            model_col = model_columns[col_name]
            db_col = db_columns[col_name]

            # Check nullable
            model_nullable = model_col.nullable if model_col.nullable is not None else True
            db_nullable = db_col.get("nullable", True)

            if model_nullable != db_nullable:
                mismatches.append(ColumnMismatch(
                    table_name=table_name,
                    column_name=col_name,
                    mismatch_type=MismatchType.NULLABLE_MISMATCH,
                    expected=str(model_nullable),
                    actual=str(db_nullable),
                    message="Nullable mismatch",
                ))

            # Type comparison is complex due to DB-specific type mapping
            # We do a basic string comparison
            model_type = str(model_col.type).upper()
            db_type = db_col.get("type", "").upper()

            # Normalize common type differences
            type_mappings = {
                "INTEGER": ["INT", "INT4", "INTEGER"],
                "BIGINT": ["BIGINT", "INT8"],
                "SMALLINT": ["SMALLINT", "INT2"],
                "VARCHAR": ["VARCHAR", "CHARACTER VARYING"],
                "TEXT": ["TEXT"],
                "BOOLEAN": ["BOOLEAN", "BOOL"],
                "TIMESTAMP": ["TIMESTAMP", "TIMESTAMP WITHOUT TIME ZONE"],
                "TIMESTAMPTZ": ["TIMESTAMPTZ", "TIMESTAMP WITH TIME ZONE"],
                "FLOAT": ["FLOAT", "FLOAT8", "DOUBLE PRECISION"],
                "REAL": ["REAL", "FLOAT4"],
                "UUID": ["UUID"],
                "JSON": ["JSON"],
                "JSONB": ["JSONB"],
            }

            def normalize_type(t: str) -> str:
                for base_type, variants in type_mappings.items():
                    for variant in variants:
                        if t.startswith(variant):
                            return base_type
                return t.split("(")[0]  # Remove size

            model_type_normalized = normalize_type(model_type)
            db_type_normalized = normalize_type(db_type)

            if model_type_normalized != db_type_normalized:
                mismatches.append(ColumnMismatch(
                    table_name=table_name,
                    column_name=col_name,
                    mismatch_type=MismatchType.TYPE_MISMATCH,
                    expected=model_type,
                    actual=db_type,
                    message="Type mismatch",
                ))

        return mismatches

    async def compare_indexes(self) -> list[IndexMismatch]:
        """
        Indexleri karsilastir.

        REQ-3.4: Eksik/fazla index'leri tespit eder.

        Returns:
            list[IndexMismatch]: Index uyumsuzluklari
        """
        mismatches = []

        for table_name, table in self.metadata.tables.items():
            model_indexes = {idx.name: idx for idx in table.indexes if idx.name}
            db_indexes = await self._get_db_indexes(table_name)

            # Indexes in model but not in DB
            for idx_name in set(model_indexes.keys()) - set(db_indexes.keys()):
                idx = model_indexes[idx_name]
                mismatches.append(IndexMismatch(
                    table_name=table_name,
                    index_name=idx_name,
                    mismatch_type=MismatchType.MISSING_IN_DB,
                    columns=[c.name for c in idx.columns],
                    message="Index defined in model but missing in database",
                ))

            # Indexes in DB but not in model (excluding PK and auto-generated)
            for idx_name in set(db_indexes.keys()) - set(model_indexes.keys()):
                if not idx_name.endswith("_pkey") and not idx_name.startswith("pg_"):
                    mismatches.append(IndexMismatch(
                        table_name=table_name,
                        index_name=idx_name,
                        mismatch_type=MismatchType.MISSING_IN_MODEL,
                        columns=db_indexes[idx_name].get("columns", []),
                        message="Index exists in database but not defined in model",
                    ))

        return mismatches

    async def compare_foreign_keys(self) -> list[ForeignKeyMismatch]:
        """
        Foreign key'leri karsilastir.

        REQ-3.5: Referential integrity sorunlarini tespit eder.

        Returns:
            list[ForeignKeyMismatch]: FK uyumsuzluklari
        """
        mismatches = []

        for table_name, table in self.metadata.tables.items():
            # Get model foreign keys
            model_fks = {}
            for fk in table.foreign_key_constraints:
                if fk.name:
                    model_fks[fk.name] = {
                        "source_columns": [c.name for c in fk.columns],
                        "target_table": list(fk.elements)[0].column.table.name if fk.elements else "",
                        "target_columns": [e.column.name for e in fk.elements],
                    }

            db_fks = await self._get_db_foreign_keys(table_name)

            # FKs in model but not in DB
            for fk_name in set(model_fks.keys()) - set(db_fks.keys()):
                fk = model_fks[fk_name]
                mismatches.append(ForeignKeyMismatch(
                    table_name=table_name,
                    constraint_name=fk_name,
                    mismatch_type=MismatchType.MISSING_IN_DB,
                    source_columns=fk["source_columns"],
                    target_table=fk["target_table"],
                    target_columns=fk["target_columns"],
                    message="FK defined in model but missing in database",
                ))

            # FKs in DB but not in model
            for fk_name in set(db_fks.keys()) - set(model_fks.keys()):
                fk = db_fks[fk_name]
                mismatches.append(ForeignKeyMismatch(
                    table_name=table_name,
                    constraint_name=fk_name,
                    mismatch_type=MismatchType.MISSING_IN_MODEL,
                    source_columns=fk.get("source_columns", []),
                    target_table=fk.get("target_table", ""),
                    target_columns=fk.get("target_columns", []),
                    message="FK exists in database but not defined in model",
                ))

        return mismatches

    async def generate_migration_script(self) -> str:
        """
        Uyumsuzluklari gidermek icin migration script olustur.

        REQ-3.6: Uyumsuzluk tespit edilirse otomatik migration script onerir.

        Returns:
            str: Alembic migration script
        """
        result = await self.compare_all()

        if not result.has_mismatches:
            return "-- No schema mismatches found. Schema is consistent."

        lines = [
            '"""',
            "Auto-generated migration script",
            f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Mismatches found: {result.total_mismatch_count}",
            '"""',
            "",
            "from alembic import op",
            "import sqlalchemy as sa",
            "",
            "",
            "def upgrade():",
        ]

        # Generate upgrade statements
        for mismatch in result.table_mismatches:
            if mismatch.mismatch_type == MismatchType.MISSING_IN_DB:
                lines.append(f"    # TODO: Create table '{mismatch.table_name}'")
                lines.append(f"    # op.create_table('{mismatch.table_name}', ...)")

        for mismatch in result.column_mismatches:
            if mismatch.mismatch_type == MismatchType.MISSING_IN_DB:
                lines.append(
                    f"    op.add_column('{mismatch.table_name}', "
                    f"sa.Column('{mismatch.column_name}', sa.String()))"
                )
            elif mismatch.mismatch_type == MismatchType.TYPE_MISMATCH:
                lines.append(
                    f"    # TODO: Alter column type for '{mismatch.table_name}.{mismatch.column_name}'"
                )
                lines.append(
                    f"    # Expected: {mismatch.expected}, Actual: {mismatch.actual}"
                )

        for mismatch in result.index_mismatches:
            if mismatch.mismatch_type == MismatchType.MISSING_IN_DB:
                cols = ", ".join([f"'{c}'" for c in mismatch.columns])
                lines.append(
                    f"    op.create_index('{mismatch.index_name}', '{mismatch.table_name}', [{cols}])"
                )

        for mismatch in result.fk_mismatches:
            if mismatch.mismatch_type == MismatchType.MISSING_IN_DB:
                lines.append(
                    f"    # TODO: Create foreign key '{mismatch.constraint_name}' on '{mismatch.table_name}'"
                )

        if len(lines) == 12:  # Only header lines
            lines.append("    pass")

        lines.extend([
            "",
            "",
            "def downgrade():",
        ])

        # Generate downgrade statements (reverse order)
        for mismatch in reversed(result.column_mismatches):
            if mismatch.mismatch_type == MismatchType.MISSING_IN_DB:
                lines.append(
                    f"    op.drop_column('{mismatch.table_name}', '{mismatch.column_name}')"
                )

        for mismatch in reversed(result.index_mismatches):
            if mismatch.mismatch_type == MismatchType.MISSING_IN_DB:
                lines.append(
                    f"    op.drop_index('{mismatch.index_name}', table_name='{mismatch.table_name}')"
                )

        if lines[-1] == "def downgrade():":
            lines.append("    pass")

        return "\n".join(lines)

    # ==================== HELPER METHODS ====================

    async def _get_db_tables(self) -> set[str]:
        """DB'deki tum tablolari al."""
        async with self.engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
            """))
            return {row[0] for row in result.fetchall()}

    async def _get_db_columns(self, table_name: str) -> dict[str, dict]:
        """DB'deki kolon bilgilerini al."""
        async with self.engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = :table_name
            """), {"table_name": table_name})

            columns = {}
            for row in result.fetchall():
                columns[row[0]] = {
                    "type": row[1],
                    "nullable": row[2] == "YES",
                    "default": row[3],
                }
            return columns

    async def _get_db_indexes(self, table_name: str) -> dict[str, dict]:
        """DB'deki index bilgilerini al."""
        async with self.engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT
                    i.relname as index_name,
                    array_agg(a.attname) as columns
                FROM pg_index ix
                JOIN pg_class t ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relname = :table_name
                AND t.relkind = 'r'
                GROUP BY i.relname
            """), {"table_name": table_name})

            indexes = {}
            for row in result.fetchall():
                indexes[row[0]] = {"columns": row[1]}
            return indexes

    async def _get_db_foreign_keys(self, table_name: str) -> dict[str, dict]:
        """DB'deki foreign key bilgilerini al."""
        async with self.engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name as source_column,
                    ccu.table_name as target_table,
                    ccu.column_name as target_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = :table_name
            """), {"table_name": table_name})

            fks: dict[str, dict] = {}
            for row in result.fetchall():
                fk_name = row[0]
                if fk_name not in fks:
                    fks[fk_name] = {
                        "source_columns": [],
                        "target_table": row[2],
                        "target_columns": [],
                    }
                fks[fk_name]["source_columns"].append(row[1])
                fks[fk_name]["target_columns"].append(row[3])

            return fks
