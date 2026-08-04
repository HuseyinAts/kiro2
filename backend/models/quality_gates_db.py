"""
SQLAlchemy ORM Quality Gates Models
===================================

Database models for persisting quality gates pipeline results.
Supports trend analysis, historical comparison, and audit logging.

Models:
- QualityGatesRun: Pipeline execution record
- GateResultRecord: Individual gate results
- OverrideAuditLog: Override history
"""

import uuid
from uuid6 import uuid7
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    pass


class QualityGatesRun(Base):
    """
    Pipeline execution record.

    Stores summary of each quality gates pipeline run including
    overall status, execution time, and git context.
    """

    __tablename__ = "quality_gates_runs"
    __table_args__ = (
        Index("idx_qg_run_status", "status"),
        Index("idx_qg_run_commit", "commit_hash"),
        Index("idx_qg_run_branch", "branch"),
        Index("idx_qg_run_started", "started_at"),
        Index("idx_qg_run_triggered_by", "triggered_by"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Pipeline info
    pipeline_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # pass, warning, fail, error

    # Scores
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    passed_gates: Mapped[int] = mapped_column(Integer, default=0)
    failed_gates: Mapped[int] = mapped_column(Integer, default=0)
    skipped_gates: Mapped[int] = mapped_column(Integer, default=0)

    # Execution
    total_execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    parallel_execution_used: Mapped[bool] = mapped_column(Boolean, default=False)
    fail_fast_mode: Mapped[bool] = mapped_column(Boolean, default=False)

    # Git context
    commit_hash: Mapped[str | None] = mapped_column(String(40), index=True)
    branch: Mapped[str | None] = mapped_column(String(200), index=True)
    repository: Mapped[str | None] = mapped_column(String(500))

    # Trigger info
    triggered_by: Mapped[str | None] = mapped_column(String(255), index=True)
    trigger_type: Mapped[str | None] = mapped_column(
        String(50)
    )  # manual, push, pr, schedule

    # Override info
    overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    override_reason: Mapped[str | None] = mapped_column(Text, deferred=True)
    override_approver: Mapped[str | None] = mapped_column(String(255))

    # Configuration used
    config_snapshot: Mapped[dict | None] = mapped_column(JSON, deferred=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    gate_results: Mapped[list["GateResultRecord"]] = relationship(
        "GateResultRecord",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin")


class GateResultRecord(Base):
    """
    Individual gate execution result.

    Stores detailed results for each gate in a pipeline run including
    score, issues, and metrics.
    """

    __tablename__ = "quality_gate_results"
    __table_args__ = (
        Index("idx_qg_result_run", "run_id"),
        Index("idx_qg_result_gate", "gate_name"),
        Index("idx_qg_result_status", "status"),
        Index("idx_qg_result_run_gate", "run_id", "gate_name"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    run_id: Mapped[str] = mapped_column(String, ForeignKey("quality_gates_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Gate info
    gate_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # pass, warning, fail, skipped, timeout, error

    # Scores
    score: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    blocking: Mapped[bool] = mapped_column(Boolean, default=True)

    # Result
    message: Mapped[str] = mapped_column(Text, nullable=False, deferred=True)
    issues_count: Mapped[int] = mapped_column(Integer, default=0)
    auto_fixed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Detailed data stored as JSON
    issues: Mapped[list | None] = mapped_column(JSON, deferred=True)  # List of issue objects
    metrics: Mapped[dict | None] = mapped_column(JSON, deferred=True)  # Gate-specific metrics
    details: Mapped[dict | None] = mapped_column(JSON, deferred=True)  # Additional details

    # Execution
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    run: Mapped["QualityGatesRun"] = relationship(
        "QualityGatesRun", back_populates="gate_results"
    , lazy="selectin")


class OverrideAuditLog(Base):
    """
    Override request and approval audit log.

    Tracks all override requests and their approvals for compliance
    and audit purposes.
    """

    __tablename__ = "quality_gates_override_audit"
    __table_args__ = (
        Index("idx_qg_override_gate", "gate_name"),
        Index("idx_qg_override_requestor", "requestor"),
        Index("idx_qg_override_status", "status"),
        Index("idx_qg_override_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Request info
    gate_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    run_id: Mapped[str | None] = mapped_column(String, ForeignKey("quality_gates_runs.id", ondelete="SET NULL"),
    )

    # Requestor
    requestor: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, deferred=True)
    ticket_id: Mapped[str | None] = mapped_column(String(100))

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, approved, denied, expired

    # Approval
    approver: Mapped[str | None] = mapped_column(String(255))
    approver_comments: Mapped[str | None] = mapped_column(Text, deferred=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
