"""
Context Management System for AI Agents
Handles stateful conversations, session management, and progress tracking
SECURITY FIX: JSON serialization (replaced pickle to prevent RCE)
"""

import json
import logging
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# import redis.asyncio as redis  # Disabled due to Python 3.11 compatibility issues

# Import RoomStudySession from models for history tracking
# 2026-09-04 (docs/guvenlik-borcu.md SS10.42): renamed from StudySession,
# which collided with the unrelated models.learning_path_models.StudySession
try:
    from models.study_room import RoomStudySession
except ImportError:
    # Fallback if model is not available
    RoomStudySession = None

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session states"""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"


@dataclass
class StudentProfile:
    """Student profile with learning preferences and history"""

    student_id: str
    name: str
    grade: int
    learning_style: str  # visual, auditory, kinesthetic
    preferred_language: str = "tr"
    difficulty_level: str = "medium"
    subjects_of_interest: list[str] = field(default_factory=list)
    weak_topics: list[str] = field(default_factory=list)
    strong_topics: list[str] = field(default_factory=list)
    total_study_time: int = 0  # minutes
    last_active: datetime | None = None
    achievements: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """Single conversation turn with metadata"""

    turn_id: str
    timestamp: datetime
    agent_name: str
    user_message: str
    agent_response: str
    intent: str | None = None
    entities: dict | None = None
    sentiment: str | None = None
    confidence: float = 1.0
    processing_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionContext:
    """Complete session context with conversation history"""

    session_id: str
    student_id: str
    created_at: datetime
    last_updated: datetime
    status: SessionStatus
    conversation_history: list[ConversationTurn] = field(default_factory=list)
    current_topic: str | None = None
    current_learning_path: str | None = None
    progress: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)  # Session variables
    goals: list[str] = field(default_factory=list)
    achievements_in_session: list[str] = field(default_factory=list)

    def add_turn(self, turn: ConversationTurn):
        """Add conversation turn to history"""
        self.conversation_history.append(turn)
        self.last_updated = datetime.now()

        # Keep only last 50 turns for memory efficiency
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

    def get_context_window(self, window_size: int = 5) -> list[ConversationTurn]:
        """Get recent conversation context"""
        return (
            self.conversation_history[-window_size:]
            if self.conversation_history
            else []
        )

    def get_summary(self) -> str:
        """Generate conversation summary"""
        if not self.conversation_history:
            return "No conversation history"

        summary = []
        for turn in self.conversation_history[-3:]:
            summary.append(f"User: {turn.user_message[:100]}")
            summary.append(f"Agent: {turn.agent_response[:100]}")

        return "\\n".join(summary)


class ProgressTracker:
    """Track student progress across sessions"""

    def __init__(self):
        self.progress_data = defaultdict(dict)  # type: ignore[var-annotated]  # pre-existing, out of scope for SS10.42
        self.milestones = defaultdict(list)

    def update_progress(self, student_id: str, metric: str, value: Any):
        """Update progress metric"""
        if student_id not in self.progress_data:
            self.progress_data[student_id] = {
                "total_sessions": 0,
                "total_questions_answered": 0,
                "correct_answers": 0,
                "topics_covered": set(),
                "skills_acquired": [],
                "current_streak": 0,
                "best_streak": 0,
                "total_points": 0,
                "level": 1,
                "experience": 0,
            }

        progress = self.progress_data[student_id]

        if metric == "question_answered":
            progress["total_questions_answered"] += 1
            if value.get("correct", False):
                progress["correct_answers"] += 1
                progress["current_streak"] += 1
                progress["best_streak"] = max(
                    progress["best_streak"], progress["current_streak"]
                )
            else:
                progress["current_streak"] = 0

        elif metric == "topic_completed":
            progress["topics_covered"].add(value)
            progress["experience"] += 100
            self._check_level_up(student_id)

        elif metric == "skill_acquired":
            if value not in progress["skills_acquired"]:
                progress["skills_acquired"].append(value)
                progress["experience"] += 50

        elif metric == "session_completed":
            progress["total_sessions"] += 1
            progress["experience"] += 25

        # Check for milestones
        self._check_milestones(student_id)

    def _check_level_up(self, student_id: str):
        """Check if student should level up"""
        progress = self.progress_data[student_id]
        required_exp = progress["level"] * 500

        if progress["experience"] >= required_exp:
            progress["level"] += 1
            progress["experience"] -= required_exp
            self.milestones[student_id].append(
                {
                    "type": "level_up",
                    "level": progress["level"],
                    "timestamp": datetime.now(),
                }
            )

    def _check_milestones(self, student_id: str):
        """Check for achievement milestones"""
        progress = self.progress_data[student_id]

        milestones_config = [
            (10, "total_questions_answered", "First 10 Questions"),
            (50, "total_questions_answered", "Question Master"),
            (5, "current_streak", "5 in a Row"),
            (10, "current_streak", "Perfect 10"),
            (5, "topics_covered", "Explorer"),
            (10, "topics_covered", "Knowledge Seeker"),
        ]

        for threshold, metric, achievement in milestones_config:
            value = progress.get(metric, 0)
            if isinstance(value, set):
                value = len(value)

            if value >= threshold:
                milestone_id = f"{achievement}_{threshold}"
                existing = [
                    m
                    for m in self.milestones[student_id]
                    if m.get("id") == milestone_id
                ]
                if not existing:
                    self.milestones[student_id].append(
                        {
                            "id": milestone_id,
                            "type": "achievement",
                            "name": achievement,
                            "timestamp": datetime.now(),
                        }
                    )

    def get_progress_report(self, student_id: str) -> dict:
        """Get detailed progress report"""
        if student_id not in self.progress_data:
            return {"error": "No progress data found"}

        progress = self.progress_data[student_id]
        accuracy = 0
        if progress["total_questions_answered"] > 0:
            accuracy = (
                progress["correct_answers"] / progress["total_questions_answered"]
            ) * 100

        return {
            "student_id": student_id,
            "statistics": {
                "total_sessions": progress["total_sessions"],
                "questions_answered": progress["total_questions_answered"],
                "accuracy": round(accuracy, 2),
                "topics_mastered": list(progress["topics_covered"]),
                "current_streak": progress["current_streak"],
                "best_streak": progress["best_streak"],
            },
            "gamification": {
                "level": progress["level"],
                "experience": progress["experience"],
                "next_level_exp": progress["level"] * 500,
                "total_points": progress["total_points"],
                "achievements": self.milestones.get(student_id, []),
            },
            "skills": progress["skills_acquired"],
            "recommendations": self._generate_recommendations(student_id),
        }

    def _generate_recommendations(self, student_id: str) -> list[str]:
        """Generate personalized recommendations"""
        progress = self.progress_data[student_id]
        recommendations = []

        accuracy = 0
        if progress["total_questions_answered"] > 0:
            accuracy = (
                progress["correct_answers"] / progress["total_questions_answered"]
            ) * 100

        if accuracy < 60:
            recommendations.append("Consider reviewing fundamental concepts")
            recommendations.append("Try easier questions to build confidence")
        elif accuracy > 85:
            recommendations.append("Challenge yourself with harder topics")
            recommendations.append("Explore advanced concepts")

        if progress["current_streak"] == 0 and progress["best_streak"] > 5:
            recommendations.append("You had a great streak before! Keep practicing")

        if len(progress["topics_covered"]) < 3:
            recommendations.append("Explore more topics to broaden knowledge")

        return recommendations


class ContextManager:
    """Main context management system"""

    def __init__(self, redis_url: str = None):  # noqa: RUF013 -- pre-existing, out of scope for SS10.42
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_client = None
        self.sessions: dict[str, SessionContext] = {}
        self.student_profiles: dict[str, StudentProfile] = {}
        self.progress_tracker = ProgressTracker()
        self.session_ttl = timedelta(hours=2)  # Session timeout

    async def initialize(self):
        """Initialize Redis connection for persistence"""
        try:
            # Disabled aioredis due to Python 3.11 compatibility issues
            # self.redis_client = await redis.from_url(
            #     self.redis_url,
            #     minsize=5,
            #     maxsize=10
            # )
            logger.info(
                "Using in-memory storage for context management (Redis disabled)"
            )
            self.redis_client = None
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory storage: {e}")
            self.redis_client = None

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()
            await self.redis_client.wait_closed()

    async def create_session(
        self, student_id: str, initial_context: dict | None = None
    ) -> SessionContext:
        """Create new session for student"""
        session_id = str(uuid.uuid4())

        session = SessionContext(
            session_id=session_id,
            student_id=student_id,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            status=SessionStatus.ACTIVE,
            variables=initial_context or {},
        )

        # Store in memory
        self.sessions[session_id] = session

        # Persist to Redis if available
        await self._persist_session(session)

        logger.info(f"Created session {session_id} for student {student_id}")
        return session

    async def get_session(self, session_id: str) -> SessionContext | None:
        """Get session by ID"""
        # Check memory first
        if session_id in self.sessions:
            session = self.sessions[session_id]

            # Check if expired
            if datetime.now() - session.last_updated > self.session_ttl:
                session.status = SessionStatus.EXPIRED
                await self._persist_session(session)
                return None

            return session

        # Try Redis
        session = await self._load_session(session_id)
        if session:
            # Cache in memory
            self.sessions[session_id] = session

            # Check expiry
            if datetime.now() - session.last_updated > self.session_ttl:
                session.status = SessionStatus.EXPIRED
                await self._persist_session(session)
                return None

        return session

    async def update_session(
        self,
        session_id: str,
        turn: ConversationTurn | None = None,
        variables: dict | None = None,
        progress: dict | None = None,
    ) -> bool:
        """Update session with new information"""
        session = await self.get_session(session_id)
        if not session:
            return False

        if turn:
            session.add_turn(turn)

        if variables:
            session.variables.update(variables)

        if progress:
            session.progress.update(progress)
            # Update progress tracker
            for key, value in progress.items():
                self.progress_tracker.update_progress(session.student_id, key, value)

        session.last_updated = datetime.now()

        # Persist changes
        await self._persist_session(session)

        return True

    async def get_or_create_student_profile(
        self, student_id: str, **kwargs
    ) -> StudentProfile:
        """Get existing or create new student profile"""
        if student_id in self.student_profiles:
            return self.student_profiles[student_id]

        # Try loading from Redis
        profile = await self._load_profile(student_id)

        if not profile:
            # Create new profile
            profile = StudentProfile(
                student_id=student_id,
                name=kwargs.get("name", f"Student_{student_id[:8]}"),
                grade=kwargs.get("grade", 8),
                learning_style=kwargs.get("learning_style", "visual"),
                preferred_language=kwargs.get("preferred_language", "tr"),
                difficulty_level=kwargs.get("difficulty_level", "medium"),
            )
            await self._persist_profile(profile)

        # Cache in memory
        self.student_profiles[student_id] = profile
        return profile

    async def update_student_profile(
        self, student_id: str, updates: dict[str, Any]
    ) -> bool:
        """Update student profile"""
        profile = await self.get_or_create_student_profile(student_id)

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.last_active = datetime.now()

        # Persist changes
        await self._persist_profile(profile)

        return True

    async def get_active_sessions(self) -> list[SessionContext]:
        """Get all active sessions"""
        active = []
        for session in self.sessions.values():
            if session.status == SessionStatus.ACTIVE:  # noqa: SIM102 -- pre-existing, out of scope for SS10.42
                if datetime.now() - session.last_updated <= self.session_ttl:
                    active.append(session)
        return active

    async def end_session(self, session_id: str) -> bool:
        """End a session"""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.status = SessionStatus.COMPLETED
        session.last_updated = datetime.now()

        # Update progress
        self.progress_tracker.update_progress(
            session.student_id,
            "session_completed",
            {"duration": (session.last_updated - session.created_at).total_seconds()},
        )

        await self._persist_session(session)

        # Remove from memory cache after persistence
        if session_id in self.sessions:
            del self.sessions[session_id]

        return True

    async def get_student_history(
        self, student_id: str, limit: int = 10
    ) -> list[SessionContext]:
        """Get student's session history"""
        history = []

        # Get from Redis if available
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(f"session:*:{student_id}")
                for key in keys[-limit:]:
                    session_data = await self.redis_client.get(key)
                    if session_data:
                        # SECURITY FIX: JSON deserialization
                        session_dict = json.loads(session_data)
                        session = RoomStudySession(**session_dict)
                        history.append(session)
            except Exception as e:
                logger.error(f"Error loading history: {e}")

        # Also check memory
        for session in self.sessions.values():
            if session.student_id == student_id and session not in history:
                history.append(session)

        # Sort by creation time
        history.sort(key=lambda s: s.created_at, reverse=True)

        return history[:limit]

    # Private methods for Redis operations
    async def _persist_session(self, session: SessionContext):
        """Persist session to Redis"""
        if not self.redis_client:
            return

        try:
            key = f"session:{session.session_id}:{session.student_id}"
            # SECURITY FIX: JSON serialization
            session_dict = (
                asdict(session)
                if hasattr(session, "__dataclass_fields__")
                else session.__dict__
            )
            # Convert datetime to ISO format
            if "start_time" in session_dict and isinstance(
                session_dict["start_time"], datetime
            ):
                session_dict["start_time"] = session_dict["start_time"].isoformat()
            if "last_activity" in session_dict and isinstance(
                session_dict["last_activity"], datetime
            ):
                session_dict["last_activity"] = session_dict[
                    "last_activity"
                ].isoformat()
            value = json.dumps(session_dict, ensure_ascii=False, default=str)
            await self.redis_client.setex(
                key, int(self.session_ttl.total_seconds()), value
            )
        except Exception as e:
            logger.error(f"Error persisting session: {e}")

    async def _load_session(self, session_id: str) -> SessionContext | None:
        """Load session from Redis"""
        if not self.redis_client:
            return None

        try:
            keys = await self.redis_client.keys(f"session:{session_id}:*")
            if keys:
                data = await self.redis_client.get(keys[0])
                if data:
                    # SECURITY FIX: JSON deserialization
                    profile_dict = json.loads(data)
                    return StudentProfile(**profile_dict)
        except Exception as e:
            logger.error(f"Error loading session: {e}")

        return None

    async def _persist_profile(self, profile: StudentProfile):
        """Persist student profile to Redis"""
        if not self.redis_client:
            return

        try:
            key = f"profile:{profile.student_id}"
            # SECURITY FIX: JSON serialization
            profile_dict = (
                asdict(profile)
                if hasattr(profile, "__dataclass_fields__")
                else profile.__dict__
            )
            # Convert datetime to ISO format
            if "last_active" in profile_dict and isinstance(
                profile_dict["last_active"], datetime
            ):
                profile_dict["last_active"] = profile_dict["last_active"].isoformat()
            value = json.dumps(profile_dict, ensure_ascii=False, default=str)
            await self.redis_client.set(key, value)
        except Exception as e:
            logger.error(f"Error persisting profile: {e}")

    async def _load_profile(self, student_id: str) -> StudentProfile | None:
        """Load student profile from Redis"""
        if not self.redis_client:
            return None

        try:
            key = f"profile:{student_id}"
            data = await self.redis_client.get(key)
            if data:
                # SECURITY FIX: JSON deserialization
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error loading profile: {e}")

        return None

    def get_progress_tracker(self) -> ProgressTracker:
        """Get progress tracker instance"""
        return self.progress_tracker


# Singleton instance
_context_manager = None


async def get_context_manager() -> ContextManager:
    """Get or create singleton context manager"""
    global _context_manager  # noqa: PLW0603 -- pre-existing, out of scope for SS10.42

    if _context_manager is None:
        _context_manager = ContextManager()
        await _context_manager.initialize()

    return _context_manager


# Cleanup function for graceful shutdown
async def cleanup_context_manager():
    """Cleanup context manager resources"""
    global _context_manager  # noqa: PLW0603 -- pre-existing, out of scope for SS10.42

    if _context_manager:
        await _context_manager.close()
        _context_manager = None
