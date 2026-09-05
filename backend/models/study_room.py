"""
Task 109: Group Study Rooms Models

Database models for study rooms, members, chat, and file sharing.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from uuid6 import uuid7

from .database import Base

# ============================================================
# Enumerations
# ============================================================


class RoomStatus(str, Enum):
    """Study room status"""

    ACTIVE = "active"  # Room is active
    ARCHIVED = "archived"  # Room archived
    DELETED = "deleted"  # Room deleted


class RoomVisibility(str, Enum):
    """Room visibility/access control"""

    PUBLIC = "public"  # Anyone can join
    PRIVATE = "private"  # Invitation only
    PASSWORD = "password"  # Requires password  # pragma: allowlist secret  # noqa: S105 -- pre-existing, out of scope for SS10.42


class MemberRole(str, Enum):
    """Member role in study room"""

    OWNER = "owner"  # Room creator
    ADMIN = "admin"  # Admin privileges
    MODERATOR = "moderator"  # Can moderate chat/files
    MEMBER = "member"  # Regular member


class MemberStatus(str, Enum):
    """Member status"""

    ACTIVE = "active"  # Active member
    INVITED = "invited"  # Invitation pending
    BANNED = "banned"  # Banned from room


class MessageType(str, Enum):
    """Chat message type"""

    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    LINK = "link"
    SYSTEM = "system"  # System messages


class FileType(str, Enum):
    """Shared file type"""

    DOCUMENT = "document"  # PDF, DOCX, etc.
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"  # ZIP, RAR
    OTHER = "other"


class FileVersionStatus(str, Enum):
    """File version status"""

    CURRENT = "current"  # Current version
    ARCHIVED = "archived"  # Older version


# ============================================================
# Study Room
# ============================================================


class StudyRoom(Base):
    """
    Group study room

    Covers Task 109.1: Room creation and settings
    """

    __tablename__ = "study_rooms"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    topic = Column(String(255))  # Study topic/subject

    # Owner
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Status
    status = Column(SQLEnum(RoomStatus), default=RoomStatus.ACTIVE)

    # Access Control (Task 109.1)
    visibility = Column(SQLEnum(RoomVisibility), default=RoomVisibility.PRIVATE)
    password_hash = Column(String(255))  # For password-protected rooms

    # Settings
    max_members = Column(Integer, default=50)
    current_member_count = Column(Integer, default=1)  # Owner counts as 1

    # Features
    allow_file_sharing = Column(Boolean, default=True)
    allow_member_invites = Column(Boolean, default=True)
    require_approval = Column(Boolean, default=False)  # Approve join requests

    # Moderation
    enable_moderation = Column(Boolean, default=False)
    mute_new_members = Column(Boolean, default=False)

    # Study Schedule
    scheduled_study_times = Column(JSONB, default=list)  # Array of scheduled times

    # Tags
    tags = Column(ARRAY(String), default=list)  # e.g., ["matematik", "TYT", "geometri"]

    # Statistics
    total_messages = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    total_study_hours = Column(Float, default=0.0)

    # Room Image
    room_image_url = Column(String(500))

    # Metadata
    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    members = relationship(  # type: ignore[misc]  # pre-existing, out of scope for SS10.42
        "RoomMember",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    messages = relationship(  # type: ignore[misc]  # pre-existing, out of scope for SS10.42
        "RoomChatMessage",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    files = relationship(  # type: ignore[misc]  # pre-existing, out of scope for SS10.42
        "SharedFile",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    invitations = relationship(  # type: ignore[misc]  # pre-existing, out of scope for SS10.42
        "RoomInvitation",
        back_populates="room",
        cascade="all, delete-orphan",
    )


# ============================================================
# Room Members
# ============================================================


class RoomMember(Base):
    """
    Member of a study room

    Covers Task 109.2: User management and role assignment
    """

    __tablename__ = "room_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    room_id = Column(String, ForeignKey("study_rooms.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Role (Task 109.2)
    role = Column(SQLEnum(MemberRole), default=MemberRole.MEMBER)

    # Status
    status = Column(SQLEnum(MemberStatus), default=MemberStatus.ACTIVE)

    # Permissions (Task 109.2)
    can_send_messages = Column(Boolean, default=True)
    can_share_files = Column(Boolean, default=True)
    can_invite_members = Column(Boolean, default=False)
    can_delete_messages = Column(Boolean, default=False)
    can_delete_files = Column(Boolean, default=False)

    # Joined
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    invited_by = Column(String, ForeignKey("users.id"))

    # Activity
    last_seen_at = Column(DateTime(timezone=True))
    is_online = Column(Boolean, default=False)

    # Notifications
    mute_notifications = Column(Boolean, default=False)

    # Statistics
    messages_sent = Column(Integer, default=0)
    files_shared = Column(Integer, default=0)
    study_hours = Column(Float, default=0.0)

    # Nickname in room
    nickname = Column(String(100))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    room = relationship("StudyRoom", back_populates="members")  # type: ignore[misc]  # pre-existing, out of scope for SS10.42


# ============================================================
# Room Invitations
# ============================================================


class RoomInvitation(Base):
    """
    Room invitation system

    Covers Task 109.2: Member invitation
    """

    __tablename__ = "room_invitations"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    room_id = Column(String, ForeignKey("study_rooms.id"), nullable=False)

    # Inviter & Invitee
    inviter_id = Column(String, ForeignKey("users.id"), nullable=False)
    invitee_id = Column(String, ForeignKey("users.id"))
    invitee_email = Column(String(255))  # For external invitations

    # Invitation Details
    message = Column(Text)

    # Status
    is_accepted = Column(Boolean, default=False)
    is_declined = Column(Boolean, default=False)
    accepted_at = Column(DateTime(timezone=True))
    declined_at = Column(DateTime(timezone=True))

    # Expiration
    expires_at = Column(DateTime(timezone=True))

    # Invitation Link
    invitation_code = Column(String(100), unique=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    room = relationship("StudyRoom", back_populates="invitations")  # type: ignore[misc]  # pre-existing, out of scope for SS10.42


# ============================================================
# Chat Messages
# ============================================================


class RoomChatMessage(Base):
    """
    Chat message in study room

    Covers Task 109.3: Text chat with emoji support
    """

    __tablename__ = "room_chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    room_id = Column(String, ForeignKey("study_rooms.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Message Content (Task 109.3)
    message = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT)

    # Rich Content
    mentions = Column(ARRAY(String), default=list)  # @user mentions
    reactions = Column(JSONB, default=dict)  # Emoji reactions: {emoji: [user_ids]}

    # File Reference (for file messages)
    file_id = Column(String, ForeignKey("shared_files.id"))

    # Reply
    reply_to_id = Column(String, ForeignKey("room_chat_messages.id"))

    # Editing
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime(timezone=True))

    # Deletion
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(String, ForeignKey("users.id"))

    # Pinned
    is_pinned = Column(Boolean, default=False)
    pinned_at = Column(DateTime(timezone=True))
    pinned_by = Column(String, ForeignKey("users.id"))

    # Read Receipts
    read_by = Column(ARRAY(String), default=list)  # User IDs who read the message

    # Metadata
    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    room = relationship("StudyRoom", back_populates="messages")  # type: ignore[misc]  # pre-existing, out of scope for SS10.42


# ============================================================
# Shared Files
# ============================================================


class SharedFile(Base):
    """
    File shared in study room

    Covers Task 109.4: File upload and sharing
    """

    __tablename__ = "shared_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    room_id = Column(String, ForeignKey("study_rooms.id"), nullable=False)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)

    # File Information (Task 109.4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500))  # CDN URL

    # File Details
    file_type = Column(SQLEnum(FileType), nullable=False)
    mime_type = Column(String(100))
    file_size_bytes = Column(Integer, nullable=False)

    # Description
    description = Column(Text)
    tags = Column(ARRAY(String), default=list)

    # Preview
    thumbnail_url = Column(String(500))  # For images/videos
    preview_available = Column(Boolean, default=False)

    # Versioning (Task 109.4)
    version_number = Column(Integer, default=1)
    parent_file_id = Column(
        String, ForeignKey("shared_files.id")
    )  # Original file for versions

    # Download Tracking
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime(timezone=True))

    # Virus Scan
    is_scanned = Column(Boolean, default=False)
    scan_result = Column(String(50))  # clean, infected, pending
    scanned_at = Column(DateTime(timezone=True))

    # Deletion
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(String, ForeignKey("users.id"))

    # Metadata
    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    room = relationship("StudyRoom", back_populates="files")  # type: ignore[misc]  # pre-existing, out of scope for SS10.42
    versions = relationship(  # type: ignore[misc]  # pre-existing, out of scope for SS10.42
        "FileVersion",
        back_populates="file",
        cascade="all, delete-orphan",
    )


# ============================================================
# File Versions
# ============================================================


class FileVersion(Base):
    """
    File version history

    Covers Task 109.4: Version control
    """

    __tablename__ = "file_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    file_id = Column(String, ForeignKey("shared_files.id"), nullable=False)

    # Version Details
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500))
    file_size_bytes = Column(Integer, nullable=False)

    # Uploader
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Status
    status = Column(SQLEnum(FileVersionStatus), default=FileVersionStatus.ARCHIVED)

    # Change Description
    change_description = Column(Text)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    file = relationship("SharedFile", back_populates="versions")  # type: ignore[misc]  # pre-existing, out of scope for SS10.42


# ============================================================
# Study Sessions
# ============================================================


class RoomStudySession(Base):
    """
    Track study sessions in room

    2026-09-04 (docs/guvenlik-borcu.md SS10.42): renamed from `StudySession`
    (tablename "study_sessions") to `RoomStudySession` (tablename
    "room_study_sessions"). This class collided with the unrelated, already
    live `models.learning_path_models.StudySession` (also "study_sessions")
    -- `extend_existing=True` below silently suppressed SQLAlchemy's
    table-redefinition error instead of fixing the actual name clash. The
    live DB (see backend/alembic/baseline/0001_baseline_schema.sql) already
    has a separate `room_study_sessions` table with exactly this class's
    11 columns (id, room_id, user_id, started_at, ended_at,
    duration_minutes, topic, notes, pomodoros_completed, breaks_taken,
    created_at) -- confirmed by an archived pre-squash migration
    (alembic/versions_archive/cff60c64b309_b4_sync_v2.py) that created this
    exact table. Every sibling model in this file already follows the
    `Room*` / `room_*` naming convention (RoomMember/room_members,
    RoomAnalytics/room_analytics, RoomSettings/room_settings, etc.) --
    this class was the sole exception. No migration needed: this fix only
    repoints the ORM at the table that was already there.
    """

    __tablename__ = "room_study_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    room_id = Column(String, ForeignKey("study_rooms.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Session Details
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer, default=0)

    # Topic
    topic = Column(String(255))
    notes = Column(Text)

    # Pomodoro Tracking
    pomodoros_completed = Column(Integer, default=0)
    breaks_taken = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ============================================================
# Room Analytics
# ============================================================


class RoomAnalytics(Base):
    """
    Analytics for study room
    """

    __tablename__ = "room_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    room_id = Column(String, ForeignKey("study_rooms.id"), nullable=False, unique=True)

    # Member Statistics
    total_members = Column(Integer, default=0)
    active_members_today = Column(Integer, default=0)
    active_members_week = Column(Integer, default=0)

    # Activity Statistics
    total_messages = Column(Integer, default=0)
    messages_today = Column(Integer, default=0)
    messages_week = Column(Integer, default=0)

    # File Statistics
    total_files = Column(Integer, default=0)
    total_storage_bytes = Column(Integer, default=0)

    # Study Statistics
    total_study_sessions = Column(Integer, default=0)
    total_study_hours = Column(Float, default=0.0)
    average_session_duration = Column(Float, default=0.0)

    # Engagement
    most_active_day = Column(String(20))
    most_active_hour = Column(Integer)
    average_response_time_minutes = Column(Float, default=0.0)

    # Popular Content
    most_used_tags = Column(JSONB, default=list)
    top_contributors = Column(JSONB, default=list)

    # Detailed Metrics
    metrics = Column(JSONB, default=dict)

    last_calculated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


# ============================================================
# Room Settings
# ============================================================


class RoomSettings(Base):
    """
    Additional room settings and preferences
    """

    __tablename__ = "room_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    room_id = Column(String, ForeignKey("study_rooms.id"), nullable=False, unique=True)

    # Chat Settings
    slow_mode_seconds = Column(Integer, default=0)  # Message cooldown
    link_preview = Column(Boolean, default=True)
    allow_emojis = Column(Boolean, default=True)
    allow_gifs = Column(Boolean, default=True)

    # File Settings
    max_file_size_mb = Column(Integer, default=100)
    allowed_file_types = Column(ARRAY(String), default=list)
    require_file_approval = Column(Boolean, default=False)

    # Notification Settings
    notify_on_mention = Column(Boolean, default=True)
    notify_on_file_upload = Column(Boolean, default=True)
    notify_on_member_join = Column(Boolean, default=True)

    # Study Timer Settings
    default_pomodoro_duration = Column(Integer, default=25)  # minutes
    default_break_duration = Column(Integer, default=5)  # minutes

    # Theme
    theme_color = Column(String(20), default="#3b82f6")

    # Custom Settings
    custom_settings = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
