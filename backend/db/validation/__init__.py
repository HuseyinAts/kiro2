"""
Migration Validation Module

Schema consistency ve data integrity dogrulama saglar.
SQLAlchemy model vs DB schema karsilastirmasi yapar.
"""

from .schema_checker import (
    SchemaConsistencyChecker,
    TableMismatch,
    ColumnMismatch,
    IndexMismatch,
    ForeignKeyMismatch,
    SchemaComparisonResult,
)
from .integrity_validator import (
    DataIntegrityValidator,
    RowCountDiff,
    OrphanedRecord,
    DuplicateRecord,
    NullViolation,
    IntegrityCheckResult,
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
