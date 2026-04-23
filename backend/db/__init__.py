"""
Database Migration Validation Module - KIRO2

Boris Cherny verification feedback loops prensibi ile
migration hatalarini %95 azaltma hedefleyen dogulama sistemi.

Modules:
    hooks: Migration oncesi/sonrasi hook'lar
    testing: Dry run test altyapisi
    validation: Schema ve data integrity kontrolu
    rollback: Guvenli geri alma yonetimi
    history: Migration gecmisi takibi
    analysis: Performans analizi
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .analysis.performance import PerformanceAnalyzer
    from .history.tracker import MigrationHistoryTracker
    from .hooks.pre_migration import PreMigrationHook
    from .rollback.manager import RollbackManager
    from .testing.dry_run import DryRunTester
    from .validation.integrity_validator import DataIntegrityValidator
    from .validation.schema_checker import SchemaConsistencyChecker

__all__ = [
    "DataIntegrityValidator",
    "DryRunTester",
    "MigrationHistoryTracker",
    "PerformanceAnalyzer",
    "PreMigrationHook",
    "RollbackManager",
    "SchemaConsistencyChecker",
]
