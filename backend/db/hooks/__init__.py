"""
Migration Hooks Module

PreMigration ve PostMigration hook'lari saglar.
Migration oncesi dogrulama, backup ve syntax kontrolu yapar.
"""

from .pre_migration import (
    PreMigrationHook,
    ValidationResult,
    BackupResult,
    SyntaxError,
    DependencyError,
)

__all__ = [
    "PreMigrationHook",
    "ValidationResult",
    "BackupResult",
    "SyntaxError",
    "DependencyError",
]
