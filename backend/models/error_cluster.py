"""
Error Clustering Models — F15
Tables for collaborative filtering of error patterns.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class ErrorCluster(Base):
    """A cluster of students who make similar error patterns."""

    __tablename__ = "error_clusters"
    __table_args__ = (
        Index("idx_error_cluster_subject", "subject"),
        Index("idx_error_cluster_updated", "updated_at"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    topic_ids: Mapped[dict] = mapped_column(JSONB, default=list)
    error_pattern: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g. "kavram_hatasi:turev"
    student_count: Mapped[int] = mapped_column(Integer, default=0)
    recommended_remediation: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PeerRecommendation(Base):
    """Collaborative filtering recommendation from error clusters."""

    __tablename__ = "peer_recommendations"
    __table_args__ = (
        Index("idx_peer_rec_cluster", "cluster_id"),
        Index("idx_peer_rec_source", "source_topic"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    cluster_id: Mapped[str] = mapped_column(String, nullable=False)
    source_topic: Mapped[str] = mapped_column(String(200), nullable=False)
    target_topic: Mapped[str] = mapped_column(String(200), nullable=False)
    improvement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
