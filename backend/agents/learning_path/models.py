"""
Data Models for Learning Path Agent
Teknofest 2025 - Eğitim Eylemci Projesi

This module contains all data models used by the Learning Path Agent.
Extracted from learning_path_agent.py for better organization and reusability.

Models:
- LearningStyle: Enum for learning styles
- KnowledgeLevel: Enum for knowledge levels
- StudentProfile: Student profile data
- LearningResource: Learning resource data
- LearningPath: Complete learning path data
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class LearningStyle(Enum):
    """
    Learning style categories based on VARK model

    - VISUAL: Visual learners (videos, infographics, diagrams)
    - AUDITORY: Auditory learners (podcasts, lectures, discussions)
    - READING: Reading/writing learners (text, articles, books)
    - KINESTHETIC: Kinesthetic learners (hands-on, projects, practice)
    - MIXED: Mixed/multimodal learners (combination of above)
    """

    VISUAL = "visual"
    AUDITORY = "auditory"
    READING = "reading"
    KINESTHETIC = "kinesthetic"
    MIXED = "mixed"


class KnowledgeLevel(Enum):
    """
    Knowledge level categories

    - BEGINNER: Just starting (0-30% mastery)
    - ELEMENTARY: Basic understanding (30-50% mastery)
    - INTERMEDIATE: Moderate understanding (50-70% mastery)
    - ADVANCED: Advanced understanding (70-90% mastery)
    - EXPERT: Expert level (90-100% mastery)
    """

    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class StudentProfile:
    """
    Student profile containing all relevant information
    for personalized learning path generation.

    Attributes:
        student_id: Unique student identifier
        name: Student name
        grade: Grade/class level (e.g., "10", "11", "12")
        exam_target: Target exam (e.g., "YKS", "LGS")
        learning_goal: Main learning goal/objective
        learning_style: Preferred learning style
        knowledge_level: Current knowledge level
        interests: List of interests/topics
        available_time: Available study time per day (minutes)
        metadata: Additional metadata (analysis, timestamps, etc.)
    """

    student_id: str
    name: str
    grade: str
    exam_target: str
    learning_goal: str
    learning_style: LearningStyle
    knowledge_level: KnowledgeLevel
    interests: List[str]
    available_time: int  # minutes per day
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate after initialization"""
        if not self.student_id:
            raise ValueError("student_id cannot be empty")
        if self.available_time < 0:
            raise ValueError("available_time must be non-negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "grade": self.grade,
            "exam_target": self.exam_target,
            "learning_goal": self.learning_goal,
            "learning_style": self.learning_style.value,
            "knowledge_level": self.knowledge_level.value,
            "interests": self.interests,
            "available_time": self.available_time,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudentProfile":
        """Create from dictionary"""
        return cls(
            student_id=data["student_id"],
            name=data["name"],
            grade=data["grade"],
            exam_target=data["exam_target"],
            learning_goal=data["learning_goal"],
            learning_style=LearningStyle(data["learning_style"]),
            knowledge_level=KnowledgeLevel(data["knowledge_level"]),
            interests=data["interests"],
            available_time=data["available_time"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class LearningResource:
    """
    Learning resource (video, article, course, etc.)

    Attributes:
        resource_id: Unique resource identifier
        title: Resource title
        source: Source platform (YouTube, Khan Academy, Wikipedia, etc.)
        url: Resource URL
        resource_type: Type (video, article, course, quiz, etc.)
        difficulty_level: Difficulty level
        estimated_time: Estimated completion time (minutes)
        language: Content language (e.g., "tr", "en")
        description: Resource description
        tags: Topic/subject tags
        rating: Quality rating (0.0-5.0)
        metadata: Additional metadata (duration, views, author, etc.)
    """

    resource_id: str
    title: str
    source: str
    url: str
    resource_type: str
    difficulty_level: KnowledgeLevel
    estimated_time: int  # minutes
    language: str
    description: str
    tags: List[str]
    rating: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate after initialization"""
        if not self.resource_id:
            raise ValueError("resource_id cannot be empty")
        if not self.url:
            raise ValueError("url cannot be empty")
        if self.estimated_time < 0:
            raise ValueError("estimated_time must be non-negative")
        if self.rating is not None and (self.rating < 0 or self.rating > 5):
            raise ValueError("rating must be between 0 and 5")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "resource_id": self.resource_id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "resource_type": self.resource_type,
            "difficulty_level": self.difficulty_level.value,
            "estimated_time": self.estimated_time,
            "language": self.language,
            "description": self.description,
            "tags": self.tags,
            "rating": self.rating,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningResource":
        """Create from dictionary"""
        return cls(
            resource_id=data["resource_id"],
            title=data["title"],
            source=data["source"],
            url=data["url"],
            resource_type=data["resource_type"],
            difficulty_level=KnowledgeLevel(data["difficulty_level"]),
            estimated_time=data["estimated_time"],
            language=data["language"],
            description=data["description"],
            tags=data["tags"],
            rating=data.get("rating"),
            metadata=data.get("metadata"),
        )

    def matches_style(self, learning_style: LearningStyle) -> bool:
        """Check if resource matches a learning style"""
        style_mappings = {
            LearningStyle.VISUAL: ["video", "infographic", "diagram", "animation"],
            LearningStyle.AUDITORY: ["podcast", "audio", "lecture", "discussion"],
            LearningStyle.READING: ["article", "book", "text", "documentation"],
            LearningStyle.KINESTHETIC: ["practice", "quiz", "project", "interactive"],
        }

        if learning_style == LearningStyle.MIXED:
            return True  # Mixed learners can use any resource

        preferred_types = style_mappings.get(learning_style, [])
        return any(ptype in self.resource_type.lower() for ptype in preferred_types)


@dataclass
class LearningPhase:
    """
    Learning phase/milestone within a learning path

    Attributes:
        phase_id: Unique phase identifier
        name: Phase name
        description: Phase description
        order: Phase order in sequence
        resources: Resources for this phase
        learning_objectives: Learning objectives for this phase
        metadata: Additional metadata
    """

    phase_id: str
    name: str
    description: str
    order: int
    resources: List[LearningResource]
    learning_objectives: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "resources": [r.to_dict() for r in self.resources],
            "learning_objectives": self.learning_objectives,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningPhase":
        """Create from dictionary"""
        return cls(
            phase_id=data["phase_id"],
            name=data["name"],
            description=data["description"],
            order=data["order"],
            resources=[
                LearningResource.from_dict(r) for r in data.get("resources", [])
            ],
            learning_objectives=data.get("learning_objectives", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class LearningPath:
    """
    Complete personalized learning path

    Attributes:
        path_id: Unique path identifier
        student_id: Associated student ID
        goal: Learning goal
        resources: List of learning resources in sequence
        phases: Learning phases/milestones
        created_at: Creation timestamp
        reasoning: Explanation of why this path was created
        metadata: Additional metadata (schedule, checkpoints, etc.)
    """

    path_id: str
    student_id: str
    goal: str
    resources: List[LearningResource]
    phases: List[LearningPhase]
    created_at: datetime
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate after initialization"""
        if not self.path_id:
            raise ValueError("path_id cannot be empty")
        if not self.student_id:
            raise ValueError("student_id cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "path_id": self.path_id,
            "student_id": self.student_id,
            "goal": self.goal,
            "resources": [r.to_dict() for r in self.resources],
            "phases": [p.to_dict() for p in self.phases],
            "created_at": self.created_at.isoformat(),
            "reasoning": self.reasoning,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningPath":
        """Create from dictionary"""
        return cls(
            path_id=data["path_id"],
            student_id=data["student_id"],
            goal=data["goal"],
            resources=[LearningResource.from_dict(r) for r in data["resources"]],
            phases=[LearningPhase.from_dict(p) for p in data.get("phases", [])],
            created_at=datetime.fromisoformat(data["created_at"]),
            reasoning=data["reasoning"],
            metadata=data.get("metadata", {}),
        )

    def get_resources_by_phase(self, phase_index: int) -> List[LearningResource]:
        """Get resources for a specific phase"""
        if phase_index < 0 or phase_index >= len(self.phases):
            raise ValueError(f"Invalid phase_index: {phase_index}")

        return self.phases[phase_index].resources

    def get_completion_percentage(self, completed_resource_ids: List[str]) -> float:
        """Calculate completion percentage"""
        if not self.resources:
            return 0.0

        completed_count = sum(
            1 for r in self.resources if r.resource_id in completed_resource_ids
        )
        return (completed_count / len(self.resources)) * 100

    def estimate_remaining_time(self, completed_resource_ids: List[str]) -> int:
        """Estimate remaining time in minutes"""
        remaining_time = sum(
            r.estimated_time
            for r in self.resources
            if r.resource_id not in completed_resource_ids
        )
        return remaining_time
