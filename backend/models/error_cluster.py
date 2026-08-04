"""
Error Cluster Models

ErrorCluster ve PeerRecommendation modelleri — ortak hata kume analizi.
"""

import uuid
from uuid6 import uuid7
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class ErrorCluster(Base):
    """Benzer hatalar yapan ogrencilerin olusturdugu kume."""

    __tablename__ = "error_clusters"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    subject: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    topic_ids: Mapped[list] = mapped_column(JSONB, default=list, deferred=True)
    error_pattern: Mapped[str] = mapped_column(String(100), nullable=False)
    student_count: Mapped[int] = mapped_column(Integer, default=0)
    recommended_remediation: Mapped[dict] = mapped_column(JSONB, default=dict, deferred=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<ErrorCluster id={self.id} subject={self.subject}"
            f" pattern={self.error_pattern}>"
        )


class PeerRecommendation(Base):
    """Akran tabanli konu oneri — hangi konudan sonra hangi konu calisilmali."""

    __tablename__ = "peer_recommendations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    cluster_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_topic: Mapped[str] = mapped_column(String(200), nullable=False)
    target_topic: Mapped[str] = mapped_column(String(200), nullable=False)
    improvement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, deferred=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<PeerRecommendation id={self.id} cluster={self.cluster_id}"
            f" {self.source_topic} -> {self.target_topic}>"
        )
