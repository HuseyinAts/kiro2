"""Dungeon Learning Path ORM Models."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)

from .base import Base


class DungeonProgress(Base):
    """Per-user per-topic dungeon progress — attempts, scores, completion."""

    __tablename__ = "dungeon_progress"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    topic_id = Column(String, ForeignKey("topic_hierarchy.id"), primary_key=True)
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    attempt_count = Column(Integer, nullable=False, server_default="0")
    best_score = Column(Integer, nullable=False, server_default="0")
    last_score = Column(Integer, nullable=False, server_default="0")
    completed = Column(Boolean, nullable=False, server_default="false")
    first_attempt = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_attempt = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("idx_dungeon_progress_user", "user_id"),)
