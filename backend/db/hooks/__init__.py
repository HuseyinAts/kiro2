"""
Migration Hooks Module

PreMigration ve PostMigration hook'lari saglar.
Migration oncesi dogrulama, backup ve syntax kontrolu yapar.
"""

from .pre_migration import (
    BackupResult,
    DependencyError,
    PreMigrationHook,
    SyntaxError,
    ValidationResult,
)

__all__ = [
    "BackupResult",
    "DependencyError",
    "PreMigrationHook",
    "SyntaxError",
    "ValidationResult",
]
