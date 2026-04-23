"""
Migration Rollback Module

Guvenli rollback yonetimi saglar.
Dry run before rollback, backup restore, manual intervention detection.
"""

from .manager import (
    RestoreResult,
    RollbackManager,
    RollbackResult,
    VerificationResult,
)

__all__ = [
    "RestoreResult",
    "RollbackManager",
    "RollbackResult",
    "VerificationResult",
]
