"""
Social Safety Models — Guvenli Sosyal Ortam Altyapisi

Tablolar:
- content_reports: Icerik raporlama
- moderation_actions: Moderator aksiyonlari (uyari/mute/ban)
- blocked_users: Kullanici engelleme
- parent_social_settings: Veli sosyal kontrolleri
- message_audit_log: Mesaj denetim logu
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ContentType(str, enum.Enum):
    CHAT_MESSAGE = "chat_message"
    STUDY_ROOM_MESSAGE = "study_room_message"
    DUEL_CHAT = "duel_chat"
    FORUM_POST = "forum_post"
    FORUM_SOLUTION = "forum_solution"
    PROFILE_BIO = "profile_bio"
    MENTOR_MESSAGE = "mentor_message"


class ReportReason(str, enum.Enum):
    HARASSMENT = "harassment"
    INAPPROPRIATE = "inappropriate"
    SPAM = "spam"
    PERSONAL_INFO = "personal_info"
    FLIRTING = "flirting"
    BULLYING = "bullying"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationActionType(str, enum.Enum):
    WARNING = "warning"
    CONTENT_REMOVED = "content_removed"
    MUTED_1H = "muted_1h"
    MUTED_24H = "muted_24h"
    BANNED_7D = "banned_7d"
    BANNED_PERMANENT = "banned_permanent"
    UNBAN = "unban"


class VisibilityLevel(str, enum.Enum):
    FULL = "full"
    SUMMARY = "summary"
    NONE = "none"


class FlagReason(str, enum.Enum):
    CLEAN = "clean"
    BLACKLIST = "blacklist"
    FLIRT = "flirt"
    PERSONAL_INFO = "personal_info"
    EMOJI_ABUSE = "emoji_abuse"
    SPAM = "spam"
    AI_FLAGGED = "ai_flagged"
    LENGTH = "length"


# ---------------------------------------------------------------------------
# Table 1: content_reports
# ---------------------------------------------------------------------------


class ContentReport(Base):
    """Kullanici tarafindan raporlanan icerikler."""

    __tablename__ = "content_reports"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    reporter_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    reported_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    reported_content_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Table 2: moderation_actions
# ---------------------------------------------------------------------------


class ModerationAction(Base):
    """Moderator/sistem tarafindan alinan aksiyonlar."""

    __tablename__ = "moderation_actions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    moderator_id: Mapped[str | None] = mapped_column(String, nullable=True)
    target_user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content_id: Mapped[str | None] = mapped_column(String, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    report_id: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Table 3: blocked_users
# ---------------------------------------------------------------------------


class BlockedUser(Base):
    """Kullanici engelleme kayitlari."""

    __tablename__ = "blocked_users"
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_block_pair"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    blocker_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    blocked_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Table 4: parent_social_settings
# ---------------------------------------------------------------------------


class ParentSocialSettings(Base):
    """Veli tarafindan ayarlanan sosyal ortam kontrolleri."""

    __tablename__ = "parent_social_settings"
    __table_args__ = (
        UniqueConstraint("parent_id", "student_id", name="uq_parent_student_settings"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    parent_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    social_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    chat_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    study_rooms_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    duels_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    forum_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    visibility_level: Mapped[str] = mapped_column(String(20), default="full")
    max_daily_messages: Mapped[int] = mapped_column(Integer, default=200)
    allowed_hours_start: Mapped[int] = mapped_column(Integer, default=6)
    allowed_hours_end: Mapped[int] = mapped_column(Integer, default=23)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# Table 5: message_audit_log
# ---------------------------------------------------------------------------


class MessageAuditLog(Base):
    """Mesaj denetim logu — icerik hash'i saklar, ham metin DEGIL."""

    __tablename__ = "message_audit_log"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    sender_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_length: Mapped[int] = mapped_column(Integer, nullable=False)
    flagged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    flag_reason: Mapped[str] = mapped_column(String(20), default="clean")
    flag_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pipeline_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
