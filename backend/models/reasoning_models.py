"""
Sequential Thinking / Reasoning Database Models
Stores reasoning sessions, steps, and sub-problems

Author: KIRO AI Team
Date: 2026-01-16
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from .database import Base


class ReasoningStepTypeEnum(str, PyEnum):
    """Types of reasoning steps"""

    UNDERSTANDING = "understanding"
    DECOMPOSITION = "decomposition"
    CALCULATION = "calculation"
    INFERENCE = "inference"
    VERIFICATION = "verification"
    CONCLUSION = "conclusion"


class ReasoningSessionStatus(str, PyEnum):
    """Status of reasoning session"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class LLMProviderEnum(str, PyEnum):
    """LLM Provider types"""

    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    QWEN = "qwen"
    ENSEMBLE = "ensemble"


class ReasoningSession(Base):
    """
    Reasoning session - tracks a complete reasoning process

    Stores metadata about the reasoning session including
    the original problem, provider used, and final result.
    """

    __tablename__ = "reasoning_sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Problem and context
    problem = Column(Text, nullable=False, comment="Original problem text")
    problem_type = Column(
        String(50), nullable=True, comment="Problem type: math, logic, etc."
    )
    problem_embedding = Column(Vector(768), nullable=True, comment="Embedding of the problem text")
    context = Column(Text, nullable=True, comment="Additional context")

    # Provider info
    provider = Column(
        Enum(LLMProviderEnum),
        default=LLMProviderEnum.GEMINI,
        comment="LLM provider used",
    )
    model_name = Column(String(100), nullable=True, comment="Specific model used")
    use_ensemble = Column(Boolean, default=False, comment="Whether ensemble was used")

    # Session status
    status = Column(
        Enum(ReasoningSessionStatus),
        default=ReasoningSessionStatus.PENDING,
        comment="Session status",
    )

    # Results
    understanding = Column(Text, nullable=True, comment="Problem understanding")
    final_answer = Column(Text, nullable=True, comment="Final answer")
    verification = Column(Text, nullable=True, comment="Verification result")
    confidence = Column(Float, default=0.0, comment="Confidence score 0-1")

    # Metrics
    total_steps = Column(Integer, default=0, comment="Total reasoning steps")
    latency_ms = Column(Float, default=0.0, comment="Total latency in ms")
    tokens_used = Column(Integer, default=0, comment="Total tokens used")
    cost_usd = Column(Float, default=0.0, comment="Total cost in USD")

    # Ensemble voting info (if ensemble used)
    ensemble_scores = Column(JSON, nullable=True, comment="Scores from each provider")
    winning_provider = Column(
        String(50), nullable=True, comment="Winning provider in ensemble"
    )

    # User association
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who initiated the session",
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    steps = relationship(
        "ReasoningStep",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ReasoningStep.step_number",
    )
    sub_problems = relationship(
        "SubProblem",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SubProblem.order_index",
    )

    # Indexes
    __table_args__ = (
        Index(
            "ix_rs_problem_embedding_hnsw",
            "problem_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"problem_embedding": "vector_cosine_ops"}
        ),
        Index("idx_reasoning_sessions_user", "user_id"),
        Index("idx_reasoning_sessions_status", "status"),
        Index("idx_reasoning_sessions_provider", "provider"),
        Index("idx_reasoning_sessions_created", "created_at"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "problem": self.problem,
            "problem_type": self.problem_type,
            "provider": self.provider.value if self.provider else None,
            "model_name": self.model_name,
            "use_ensemble": self.use_ensemble,
            "status": self.status.value if self.status else None,
            "understanding": self.understanding,
            "final_answer": self.final_answer,
            "verification": self.verification,
            "confidence": self.confidence,
            "total_steps": self.total_steps,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "ensemble_scores": self.ensemble_scores,
            "winning_provider": self.winning_provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "steps": [s.to_dict() for s in self.steps] if self.steps else [],
        }


class ReasoningStep(Base):
    """
    Individual reasoning step within a session

    Represents a single step in the reasoning process
    with its description, reasoning, and result.
    """

    __tablename__ = "reasoning_steps"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Session reference
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reasoning_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Step metadata
    step_number = Column(Integer, nullable=False, comment="Step order (1, 2, 3...)")
    step_type = Column(
        Enum(ReasoningStepTypeEnum),
        default=ReasoningStepTypeEnum.INFERENCE,
        comment="Type of reasoning step",
    )

    # Step content
    description = Column(Text, nullable=False, comment="What this step does")
    reasoning = Column(Text, nullable=True, comment="Why this step is needed")
    result = Column(Text, nullable=True, comment="Result of this step")

    # Parent step for hierarchical numbering (1.1, 1.2, etc.)
    parent_step_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reasoning_steps.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Quality metrics
    confidence = Column(Float, default=1.0, comment="Confidence 0-1")
    is_verified = Column(Boolean, default=False, comment="Has been verified")
    verification_result = Column(Text, nullable=True)

    # Timing
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    latency_ms = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ReasoningSession", back_populates="steps")
    sub_steps = relationship(
        "ReasoningStep",
        remote_side=[id],
        backref="parent_step",
    )

    # Indexes
    __table_args__ = (
        Index("idx_reasoning_steps_session", "session_id"),
        Index("idx_reasoning_steps_number", "session_id", "step_number"),
        Index("idx_reasoning_steps_type", "step_type"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "step_number": self.step_number,
            "step_type": self.step_type.value if self.step_type else None,
            "description": self.description,
            "reasoning": self.reasoning,
            "result": self.result,
            "confidence": self.confidence,
            "is_verified": self.is_verified,
            "verification_result": self.verification_result,
            "latency_ms": self.latency_ms,
            "parent_step_id": str(self.parent_step_id) if self.parent_step_id else None,
        }


class SubProblem(Base):
    """
    Sub-problem from problem decomposition

    Represents a decomposed sub-problem with its
    dependencies and solution status.
    """

    __tablename__ = "sub_problems"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Session reference
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reasoning_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Sub-problem metadata
    order_index = Column(Integer, nullable=False, comment="Order in solving sequence")
    title = Column(String(255), nullable=False, comment="Sub-problem title")
    description = Column(Text, nullable=False, comment="Detailed description")

    # Dependencies (IDs of other sub-problems that must be solved first)
    dependencies = Column(
        ARRAY(String),
        default=[],
        comment="IDs of dependent sub-problems",
    )

    # Difficulty and estimation
    difficulty = Column(Float, default=0.5, comment="Difficulty 0-1")
    estimated_steps = Column(Integer, default=3)

    # Solution
    is_solved = Column(Boolean, default=False)
    solution = Column(Text, nullable=True)
    solution_steps = Column(JSON, nullable=True, comment="Steps used to solve")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    solved_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("ReasoningSession", back_populates="sub_problems")

    # Indexes
    __table_args__ = (
        Index("idx_sub_problems_session", "session_id"),
        Index("idx_sub_problems_order", "session_id", "order_index"),
        Index("idx_sub_problems_solved", "is_solved"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "order_index": self.order_index,
            "title": self.title,
            "description": self.description,
            "dependencies": [str(d) for d in (self.dependencies or [])],
            "difficulty": self.difficulty,
            "estimated_steps": self.estimated_steps,
            "is_solved": self.is_solved,
            "solution": self.solution,
            "solution_steps": self.solution_steps,
        }


class ReasoningCache(Base):
    """
    Cache for reasoning paths

    Stores completed reasoning paths for similar problems
    to speed up future requests.
    """

    __tablename__ = "reasoning_cache"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Problem embedding key
    problem_hash = Column(String(64), unique=True, nullable=False, index=True)
    problem_embedding = Column(Vector(1536), nullable=True)

    # Cached data
    problem_text = Column(Text, nullable=False)
    reasoning_data = Column(JSON, nullable=False, comment="Full reasoning result")
    provider = Column(String(50), nullable=True)

    # Cache metadata
    hit_count = Column(Integer, default=0, comment="Number of cache hits")
    last_hit = Column(DateTime, nullable=True)

    # Quality metrics (for cache invalidation decisions)
    confidence = Column(Float, default=0.0)
    was_verified = Column(Boolean, default=False)

    # TTL (7 days default as per spec)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index(
            "ix_rc_problem_embedding_hnsw",
            "problem_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"problem_embedding": "vector_cosine_ops"}
        ),
        Index("idx_reasoning_cache_hash", "problem_hash"),
        Index("idx_reasoning_cache_expires", "expires_at"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "problem_hash": self.problem_hash,
            "problem_text": self.problem_text,
            "reasoning_data": self.reasoning_data,
            "provider": self.provider,
            "hit_count": self.hit_count,
            "confidence": self.confidence,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
