"""
Migration Rollback Module

Guvenli rollback yonetimi saglar.
Dry run before rollback, backup restore, manual intervention detection.
"""

from .manager import (
    RollbackManager,
    RollbackResult,
    RestoreResult,
    VerificationResult,
)

__all__ = [
    "RollbackManager",
    "RollbackResult",
    "RestoreResult",
    "VerificationResult",
]
