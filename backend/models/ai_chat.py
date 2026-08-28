"""
Task 106: AI Chat Assistant Models

Database models for enhanced chat system with image upload and OCR
"""

from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from uuid6 import uuid7

from .database import Base

# ============================================================
# Enumerations
# ============================================================


class MessageRole(str, Enum):
    """Role of message sender"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionStatus(str, Enum):
    """Status of chat session"""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SubjectType(str, Enum):
    """Subject type for chat context"""

    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    TURKISH = "turkish"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    ENGLISH = "english"
    GENERAL = "general"


class ImageProcessingStatus(str, Enum):
    """Status of image processing"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================
# Task 106.1: Enhanced Chat Session
# ============================================================


class ChatSession(Base):
    """
    Chat session model

    Stores chat sessions with context and metadata
    """

    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Session info
    title = Column(String(255))
    # DB columns are VARCHAR; use native_enum=False so SQLAlchemy does NOT
    # emit ::sessionstatus / ::subjecttype casts (the live_sessions feature
    # owns a conflicting "sessionstatus" native enum with different values).
    subject_type = Column(
        SQLEnum(SubjectType, native_enum=False, length=50),
        default=SubjectType.GENERAL,
    )
    status = Column(
        SQLEnum(SessionStatus, native_enum=False, length=50),
        default=SessionStatus.ACTIVE,
    )

    # Context and metadata
    context = Column(JSONB, default=dict)  # Conversation context for AI
    meta_data = Column(JSONB, default=dict)  # Additional metadata

    # AI model info
    model_name = Column(String(100), default="gpt-4")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)

    # Session statistics
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_message_at = Column(DateTime(timezone=True))

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    images = relationship(
        "ImageUpload",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_chat_sessions_user", "user_id"),
        Index("idx_chat_sessions_status", "status"),
        Index("idx_chat_sessions_subject", "subject_type"),
        Index("idx_chat_sessions_created", "created_at"),
    )


# ============================================================
# Task 106.1: Chat Messages
# ============================================================


class ChatMessage(Base):
    """
    Chat message model

    Stores individual messages in chat sessions
    """

    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    session_id = Column(
        String,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Message content
    role = Column(SQLEnum(MessageRole, native_enum=False, length=50), nullable=False)
    content = Column(Text, nullable=False)

    # Image reference (if message contains image)
    image_id = Column(String, ForeignKey("image_uploads.id", ondelete="SET NULL"))

    # AI response metadata
    model = Column(String(100))
    tokens_used = Column(Integer)
    cost = Column(Float)
    response_time_ms = Column(Integer)  # Response time in milliseconds

    # Quality metrics
    confidence_score = Column(Float)  # AI confidence in response (0.0 - 1.0)
    relevance_score = Column(Float)  # Relevance to question (0.0 - 1.0)

    # Feedback
    user_rating = Column(Integer)  # 1-5 stars
    is_helpful = Column(Boolean)
    feedback_comment = Column(Text)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    session = relationship("ChatSession", back_populates="messages")
    image = relationship("ImageUpload")

    # Indexes
    __table_args__ = (
        Index("idx_chat_messages_session", "session_id"),
        Index("idx_chat_messages_role", "role"),
        Index("idx_chat_messages_created", "created_at"),
    )


# ============================================================
# Task 106.2 & 106.3: Image Upload and OCR
# ============================================================


class ImageUpload(Base):
    """
    Image upload model

    Stores uploaded images with OCR results
    """

    __tablename__ = "image_uploads"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    session_id = Column(
        String,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Image file info
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String(100))
    width = Column(Integer)
    height = Column(Integer)

    # Image URL (if stored in cloud)
    image_url = Column(String(512))
    thumbnail_url = Column(String(512))

    # OCR processing
    processing_status = Column(
        SQLEnum(ImageProcessingStatus), default=ImageProcessingStatus.PENDING
    )
    ocr_text = Column(Text)  # Extracted text
    ocr_confidence = Column(Float)  # OCR confidence score (0.0 - 1.0)

    # Math formula recognition
    contains_math = Column(Boolean, default=False)
    math_latex = Column(Text)  # LaTeX representation of math formulas
    math_confidence = Column(Float)

    # Handwriting recognition
    is_handwritten = Column(Boolean, default=False)
    handwriting_quality = Column(String(50))  # "good", "fair", "poor"

    # Processing metadata
    processing_time_ms = Column(Integer)
    ocr_engine = Column(String(100))  # "tesseract", "google_vision", etc.
    error_message = Column(Text)

    # AI analysis
    image_description = Column(Text)  # AI-generated description of image
    detected_objects = Column(JSONB, default=list)  # Objects detected in image
    suggested_subjects = Column(JSONB, default=list)  # Suggested subject areas

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    # Relationship
    session = relationship("ChatSession", back_populates="images")

    # Indexes
    __table_args__ = (
        Index("idx_image_uploads_session", "session_id"),
        Index("idx_image_uploads_user", "user_id"),
        Index("idx_image_uploads_status", "processing_status"),
        Index("idx_image_uploads_created", "created_at"),
    )


# ============================================================
# Task 106.4: Solution Steps
# ============================================================


class SolutionStep(Base):
    """
    Solution step model

    Stores step-by-step solutions for problems
    """

    __tablename__ = "solution_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    message_id = Column(
        String,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Step info
    step_number = Column(Integer, nullable=False)
    title = Column(String(255))
    content = Column(Text, nullable=False)

    # Step type
    step_type = Column(
        String(50)
    )  # "explanation", "calculation", "formula", "diagram", "conclusion"

    # Mathematical content
    latex_formula = Column(Text)  # LaTeX representation
    calculation_result = Column(String(255))

    # Alternative methods
    is_alternative_method = Column(Boolean, default=False)
    alternative_method_name = Column(String(100))

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_solution_steps_message", "message_id"),
        Index("idx_solution_steps_number", "step_number"),
    )


# ============================================================
# Chat Analytics
# ============================================================


class ChatAnalytics(Base):
    """
    Chat analytics model

    Stores analytics about chat usage
    """

    __tablename__ = "chat_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))

    # Time period
    date = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), default="daily")  # "daily", "weekly", "monthly"

    # Session statistics
    total_sessions = Column(Integer, default=0)
    active_sessions = Column(Integer, default=0)
    completed_sessions = Column(Integer, default=0)

    # Message statistics
    total_messages = Column(Integer, default=0)
    user_messages = Column(Integer, default=0)
    assistant_messages = Column(Integer, default=0)

    # Image statistics
    total_images = Column(Integer, default=0)
    images_with_math = Column(Integer, default=0)
    images_handwritten = Column(Integer, default=0)

    # Subject distribution
    subject_distribution = Column(
        JSONB, default=dict
    )  # {"mathematics": 10, "physics": 5, ...}

    # Quality metrics
    avg_response_time_ms = Column(Float)
    avg_confidence_score = Column(Float)
    avg_user_rating = Column(Float)
    helpful_responses = Column(Integer, default=0)

    # Token and cost
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    # Metadata
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_chat_analytics_user", "user_id"),
        Index("idx_chat_analytics_date", "date"),
        Index("idx_chat_analytics_period", "period_type"),
    )
