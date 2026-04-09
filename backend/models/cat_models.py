"""
CAT (Computerized Adaptive Testing) ORM Models

Tables: kiro2_cat_sessions, kiro2_learning_events, topic_prerequisites
These tables were previously only accessed via raw SQL (text("INSERT INTO ...")).
ORM models enable alembic --autogenerate drift detection.
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)

from .base import Base


class CatSession(Base):
    """CAT oturumu — adaptif test session kaydı."""

    __tablename__ = "kiro2_cat_sessions"

    id = Column(
        String,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id = Column(String, nullable=False)
    subject_id = Column(Text, nullable=False)
    theta_final = Column(Numeric, nullable=False, server_default="0.0")
    se_final = Column(Numeric, nullable=False, server_default="1.0")
    n_questions = Column(SmallInteger, nullable=False, server_default="0")
    started_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    state = Column(Text, nullable=False, server_default="active")
    termination_reason = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index(
            "idx_kiro2_cat_sessions_user_state", "user_id", "state", completed_at.desc()
        ),
        Index("idx_kiro2_cat_sessions_user_subject", "user_id", "subject_id"),
    )


class LearningEvent(Base):
    """Öğrenme olayı — CAT cevabı, quiz cevabı vb."""

    __tablename__ = "kiro2_learning_events"

    id = Column(
        String,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id = Column(String, nullable=False)
    question_id = Column(Text, nullable=False)
    session_id = Column(String, nullable=True)
    event_type = Column(Text, nullable=False, server_default="cat_answer")
    is_correct = Column(Boolean, nullable=True)
    theta_after = Column(Numeric, nullable=True)
    response_ms = Column(Integer, nullable=True)
    occurred_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_learning_events_user", "user_id", occurred_at.desc()),
        Index("idx_learning_events_session", "session_id"),
    )


class TopicPrerequisite(Base):
    """Konu ön koşulu — DAG yapısı için bağımlılık tanımı."""

    __tablename__ = "topic_prerequisites"

    id = Column(
        String,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    topic_id = Column(Text, ForeignKey("topic_hierarchy.id"), nullable=False)
    prereq_id = Column(Text, ForeignKey("topic_hierarchy.id"), nullable=False)
    prereq_type = Column(Text, nullable=False, server_default="hard")
    strength = Column(Numeric, nullable=False, server_default="1.0")
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_topic_prereqs_topic", "topic_id"),
        Index(
            "idx_topic_prereqs_active",
            "is_active",
            postgresql_where=(is_active == True),  # noqa: E712
        ),
    )


class UserTheta(Base):
    """User subject ability — IRT θ tahmini (per user × subject_area).

    Tablo DB'de migrations/005_learning_path.sql ile yaratıldı.
    Alembic EXCLUDE listesinde (env.py) — autogenerate etkilenmez.
    """

    __tablename__ = "user_theta"

    user_id = Column(String(255), nullable=False, primary_key=True)
    subject_area = Column(String(50), nullable=False, primary_key=True)
    theta_estimate = Column(Float, nullable=False, server_default="0.0")
    theta_se = Column(Float, nullable=False, server_default="0.5")
    response_count = Column(Integer, nullable=False, server_default="0")
    last_updated = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_user_theta_user", "user_id"),
        {"extend_existing": True},
    )
