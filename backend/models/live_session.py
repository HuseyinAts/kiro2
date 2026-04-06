"""
Task 108: Live Q&A Sessions Models

Database models for video conferencing, screen sharing, whiteboard, and recording.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from enum import Enum

from .database import Base


# ============================================================
# Enumerations
# ============================================================


class SessionStatus(str, Enum):
    """Live session status"""

    SCHEDULED = "scheduled"  # Session scheduled but not started
    LIVE = "live"  # Session currently in progress
    ENDED = "ended"  # Session ended normally
    CANCELLED = "cancelled"  # Session cancelled


class SessionType(str, Enum):
    """Type of live session"""

    ONE_ON_ONE = "one_on_one"  # Private tutoring
    GROUP_SESSION = "group_session"  # Small group
    WEBINAR = "webinar"  # Large audience
    STUDY_GROUP = "study_group"  # Peer study group


class PlatformType(str, Enum):
    """Video conference platform"""

    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    JITSI = "jitsi"  # Open source alternative
    CUSTOM = "custom"  # Custom WebRTC implementation


class ParticipantRole(str, Enum):
    """Participant role in session"""

    HOST = "host"  # Session host (teacher)
    CO_HOST = "co_host"  # Co-host privileges
    PARTICIPANT = "participant"  # Regular participant
    OBSERVER = "observer"  # View-only access


class RecordingStatus(str, Enum):
    """Recording processing status"""

    RECORDING = "recording"  # Currently recording
    PROCESSING = "processing"  # Post-processing
    READY = "ready"  # Ready for playback
    FAILED = "failed"  # Recording failed


class WhiteboardToolType(str, Enum):
    """Whiteboard drawing tools"""

    PEN = "pen"
    ERASER = "eraser"
    TEXT = "text"
    SHAPE = "shape"  # Rectangle, circle, line
    HIGHLIGHTER = "highlighter"
    EQUATION = "equation"  # Math equation tool


class ScreenShareType(str, Enum):
    """Type of screen sharing"""

    ENTIRE_SCREEN = "entire_screen"
    WINDOW = "window"
    APPLICATION = "application"
    WHITEBOARD = "whiteboard"


# ============================================================
# Live Session
# ============================================================


class LiveSession(Base):
    """
    Live Q&A session

    Covers Task 108.1: Video conference integration and session management
    """

    __tablename__ = "live_sessions"

    id = Column(String, primary_key=True, default=uuid4)

    # Basic Information
    title = Column(String(255), nullable=False)
    description = Column(Text)
    session_type = Column(SQLEnum(SessionType), default=SessionType.ONE_ON_ONE)

    # Host
    host_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Optional teacher link
    teacher_id = Column(String, ForeignKey("teacher_profiles.id"))

    # Scheduling
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)

    # Status
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.SCHEDULED)

    # Video Conference Integration (Task 108.1)
    platform = Column(SQLEnum(PlatformType), default=PlatformType.ZOOM)
    meeting_id = Column(String(100))  # Platform meeting ID
    meeting_password = Column(String(100))
    meeting_url = Column(String(500))
    join_url = Column(String(500))
    host_url = Column(String(500))

    # Platform-specific data
    zoom_meeting_data = Column(JSONB, default=dict)  # Zoom API response
    meet_event_data = Column(JSONB, default=dict)  # Google Calendar/Meet data

    # Capacity
    max_participants = Column(Integer, default=50)
    current_participants = Column(Integer, default=0)

    # Features
    allow_screen_share = Column(Boolean, default=True)
    allow_whiteboard = Column(Boolean, default=True)
    allow_recording = Column(Boolean, default=True)
    allow_chat = Column(Boolean, default=True)

    # Recording (Task 108.4)
    is_recorded = Column(Boolean, default=False)
    auto_record = Column(Boolean, default=False)

    # Waiting Room
    enable_waiting_room = Column(Boolean, default=False)

    # Security
    require_password = Column(Boolean, default=True)
    enable_mute_on_join = Column(Boolean, default=True)

    # Subject/Topic
    subject = Column(String(100))  # mathematics, physics, etc.
    topics = Column(ARRAY(String), default=list)  # Specific topics covered

    # Metadata
    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    participants = relationship(
        "SessionParticipant", back_populates="session", cascade="all, delete-orphan"
    )
    recordings = relationship(
        "SessionRecording", back_populates="session", cascade="all, delete-orphan"
    )
    whiteboard_sessions = relationship(
        "WhiteboardSession", back_populates="session", cascade="all, delete-orphan"
    )
    screen_shares = relationship(
        "ScreenShare", back_populates="session", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "SessionChatMessage", back_populates="session", cascade="all, delete-orphan"
    )


# ============================================================
# Session Participants
# ============================================================


class SessionParticipant(Base):
    """
    Participant in a live session
    """

    __tablename__ = "session_participants"

    id = Column(String, primary_key=True, default=uuid4)
    session_id = Column(
        String, ForeignKey("live_sessions.id"), nullable=False
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Role
    role = Column(SQLEnum(ParticipantRole), default=ParticipantRole.PARTICIPANT)

    # Participation
    joined_at = Column(DateTime(timezone=True))
    left_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer, default=0)

    # Status
    is_present = Column(Boolean, default=False)
    is_muted = Column(Boolean, default=False)
    is_video_on = Column(Boolean, default=True)
    is_sharing_screen = Column(Boolean, default=False)

    # Permissions
    can_share_screen = Column(Boolean, default=True)
    can_use_whiteboard = Column(Boolean, default=True)
    can_chat = Column(Boolean, default=True)
    can_unmute_self = Column(Boolean, default=True)

    # Engagement Metrics
    questions_asked = Column(Integer, default=0)
    hands_raised = Column(Integer, default=0)

    # Connection
    connection_quality = Column(String(50))  # good, fair, poor

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    session = relationship("LiveSession", back_populates="participants")


# ============================================================
# Screen Sharing
# ============================================================


class ScreenShare(Base):
    """
    Screen sharing activity tracking

    Covers Task 108.2: Screen sharing functionality
    """

    __tablename__ = "screen_shares"

    id = Column(String, primary_key=True, default=uuid4)
    session_id = Column(
        String, ForeignKey("live_sessions.id"), nullable=False
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Screen Share Details
    share_type = Column(SQLEnum(ScreenShareType), default=ScreenShareType.ENTIRE_SCREEN)

    # Window/Application Info
    window_title = Column(String(255))
    application_name = Column(String(255))

    # Timing
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer, default=0)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    session = relationship("LiveSession", back_populates="screen_shares")


# ============================================================
# Whiteboard
# ============================================================


class WhiteboardSession(Base):
    """
    Whiteboard session within live session

    Covers Task 108.3: Interactive whiteboard
    """

    __tablename__ = "whiteboard_sessions"

    id = Column(String, primary_key=True, default=uuid4)
    session_id = Column(
        String, ForeignKey("live_sessions.id"), nullable=False
    )

    # Whiteboard Info
    name = Column(String(255))
    page_count = Column(Integer, default=1)
    current_page = Column(Integer, default=1)

    # Settings
    background_color = Column(String(20), default="#FFFFFF")
    grid_enabled = Column(Boolean, default=True)

    # State
    is_active = Column(Boolean, default=True)

    # Snapshot
    snapshot_url = Column(String(500))  # Screenshot of final state

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    session = relationship("LiveSession", back_populates="whiteboard_sessions")
    strokes = relationship(
        "WhiteboardStroke", back_populates="whiteboard", cascade="all, delete-orphan"
    )
    equations = relationship(
        "WhiteboardEquation", back_populates="whiteboard", cascade="all, delete-orphan"
    )


class WhiteboardStroke(Base):
    """
    Individual drawing stroke on whiteboard

    Covers Task 108.3: Drawing tools
    """

    __tablename__ = "whiteboard_strokes"

    id = Column(String, primary_key=True, default=uuid4)
    whiteboard_id = Column(
        String, ForeignKey("whiteboard_sessions.id"), nullable=False
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Page
    page_number = Column(Integer, default=1)

    # Tool
    tool_type = Column(SQLEnum(WhiteboardToolType), nullable=False)

    # Stroke Properties
    color = Column(String(20), default="#000000")
    width = Column(Float, default=2.0)
    opacity = Column(Float, default=1.0)

    # Path Data (for pen, highlighter, eraser)
    path_data = Column(JSONB, default=list)  # Array of {x, y} points

    # Shape Data (for shapes)
    shape_type = Column(String(50))  # rectangle, circle, line, arrow
    shape_data = Column(JSONB, default=dict)  # {x, y, width, height, radius, etc}

    # Text Data (for text tool)
    text_content = Column(Text)
    font_size = Column(Integer, default=16)
    font_family = Column(String(100), default="Arial")

    # Z-index for layering
    z_index = Column(Integer, default=0)

    # Deleted (soft delete for undo)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    whiteboard = relationship("WhiteboardSession", back_populates="strokes")


class WhiteboardEquation(Base):
    """
    Math equations on whiteboard

    Covers Task 108.3: Math equation editor
    """

    __tablename__ = "whiteboard_equations"

    id = Column(String, primary_key=True, default=uuid4)
    whiteboard_id = Column(
        String, ForeignKey("whiteboard_sessions.id"), nullable=False
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Page
    page_number = Column(Integer, default=1)

    # Position
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)

    # Equation
    latex_code = Column(Text, nullable=False)  # LaTeX representation
    rendered_svg = Column(Text)  # SVG rendering

    # Styling
    font_size = Column(Integer, default=20)
    color = Column(String(20), default="#000000")

    # Display
    width = Column(Float)
    height = Column(Float)

    # Z-index
    z_index = Column(Integer, default=0)

    # Deleted
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    whiteboard = relationship("WhiteboardSession", back_populates="equations")


# ============================================================
# Session Recording
# ============================================================


class SessionRecording(Base):
    """
    Session recording

    Covers Task 108.4: Session recording and playback
    """

    __tablename__ = "session_recordings"

    id = Column(String, primary_key=True, default=uuid4)
    session_id = Column(
        String, ForeignKey("live_sessions.id"), nullable=False
    )

    # Recording Info
    title = Column(String(255))
    description = Column(Text)

    # File Information
    file_path = Column(String(500))  # Local storage path
    file_url = Column(String(500))  # CDN/cloud storage URL
    file_size_bytes = Column(Integer)

    # Video Details
    duration_seconds = Column(Integer)
    resolution = Column(String(20))  # e.g., "1920x1080"
    format = Column(String(20))  # mp4, webm, etc.

    # Recording Metadata
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))

    # Status
    status = Column(SQLEnum(RecordingStatus), default=RecordingStatus.RECORDING)

    # Platform-specific
    platform_recording_id = Column(String(255))  # Zoom/Meet recording ID
    platform_download_url = Column(String(500))
    platform_passcode = Column(String(100))

    # Processing
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)

    # Thumbnail
    thumbnail_url = Column(String(500))

    # Transcription
    transcript_url = Column(String(500))
    has_transcript = Column(Boolean, default=False)

    # Access Control
    is_public = Column(Boolean, default=False)
    requires_authentication = Column(Boolean, default=True)
    allowed_users = Column(ARRAY(String), default=list)  # User IDs

    # Analytics
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    average_watch_percentage = Column(Float, default=0.0)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    session = relationship("LiveSession", back_populates="recordings")
    views = relationship(
        "RecordingView", back_populates="recording", cascade="all, delete-orphan"
    )
    bookmarks = relationship(
        "RecordingBookmark", back_populates="recording", cascade="all, delete-orphan"
    )


class RecordingView(Base):
    """
    Recording view/watch tracking
    """

    __tablename__ = "recording_views"

    id = Column(String, primary_key=True, default=uuid4)
    recording_id = Column(
        String, ForeignKey("session_recordings.id"), nullable=False
    )
    user_id = Column(String, ForeignKey("users.id"))

    # View Details
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True))

    # Progress
    duration_watched_seconds = Column(Integer, default=0)
    watch_percentage = Column(Float, default=0.0)
    last_position_seconds = Column(Integer, default=0)

    # Completion
    completed = Column(Boolean, default=False)

    # Session
    session_id = Column(String(255))  # Anonymous session tracking

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    recording = relationship("SessionRecording", back_populates="views")


class RecordingBookmark(Base):
    """
    User bookmarks in recordings
    """

    __tablename__ = "recording_bookmarks"

    id = Column(String, primary_key=True, default=uuid4)
    recording_id = Column(
        String, ForeignKey("session_recordings.id"), nullable=False
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Bookmark
    timestamp_seconds = Column(Integer, nullable=False)
    title = Column(String(255))
    note = Column(Text)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    recording = relationship("SessionRecording", back_populates="bookmarks")


# ============================================================
# Session Chat
# ============================================================


class SessionChatMessage(Base):
    """
    Chat messages during live session
    """

    __tablename__ = "session_chat_messages"

    id = Column(String, primary_key=True, default=uuid4)
    session_id = Column(
        String, ForeignKey("live_sessions.id"), nullable=False
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Message
    message = Column(Text, nullable=False)

    # Type
    message_type = Column(String(50), default="text")  # text, file, link

    # Recipient (for private messages)
    recipient_id = Column(String, ForeignKey("users.id"))
    is_private = Column(Boolean, default=False)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Moderation
    is_deleted = Column(Boolean, default=False)
    deleted_by = Column(String, ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    session = relationship("LiveSession", back_populates="chat_messages")


# ============================================================
# Session Analytics
# ============================================================


class SessionAnalytics(Base):
    """
    Analytics for live sessions
    """

    __tablename__ = "session_analytics"

    id = Column(String, primary_key=True, default=uuid4)
    session_id = Column(
        String,
        ForeignKey("live_sessions.id"),
        nullable=False,
        unique=True,
    )

    # Participation
    total_participants = Column(Integer, default=0)
    peak_concurrent_participants = Column(Integer, default=0)
    average_duration_minutes = Column(Float, default=0.0)

    # Engagement
    total_chat_messages = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    total_screen_shares = Column(Integer, default=0)
    whiteboard_used = Column(Boolean, default=False)

    # Quality
    average_connection_quality = Column(String(50))

    # Recording
    recording_duration_seconds = Column(Integer, default=0)
    recording_views = Column(Integer, default=0)

    # Ratings
    average_rating = Column(Float)
    total_ratings = Column(Integer, default=0)

    # Detailed Metrics
    metrics = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
