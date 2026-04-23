"""
Migration Validation Module

Schema consistency ve data integrity dogrulama saglar.
SQLAlchemy model vs DB schema karsilastirmasi yapar.
"""

from .integrity_validator import (
    DataIntegrityValidator,
    DuplicateRecord,
    IntegrityCheckResult,
    NullViolation,
    OrphanedRecord,
    RowCountDiff,
)
from .schema_checker import (
    ColumnMismatch,
    ForeignKeyMismatch,
    IndexMismatch,
    SchemaComparisonResult,
    SchemaConsistencyChecker,
    TableMismatch,
)

__all__ = [
    # Schema Checker
    "SchemaConsistencyChecker",
    "TableMismatch",
    "ColumnMismatch",
    "IndexMismatch",
    "ForeignKeyMismatch",
    "SchemaComparisonResult",
    # Integrity Validator
    "DataIntegrityValidator",
    "RowCountDiff",
    "OrphanedRecord",
    "DuplicateRecord",
    "NullViolation",
    "IntegrityCheckResult",
]
