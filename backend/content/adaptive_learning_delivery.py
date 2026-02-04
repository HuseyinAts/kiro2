"""
KIRO2 Adaptive Learning Content Delivery System
Intelligent content delivery system that adapts to student learning patterns
Türkiye Üniversite Sınavları Hazırlık Platformu - Uyarlanabilir Öğrenme İçerik Sunumu
"""

import asyncio
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from analytics.unified_analytics_data_model import (
    TurkishExamType,
    TurkishSubject,
)
from content.unified_content_management import (
    ContentItem,
    ContentType,
    DifficultyLevel,
    LearningObjective,
)
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.CONTENT)
config = get_unified_config()


class LearningStyle(Enum):
    """Learning style preferences"""

    VISUAL = "visual"  # Görsel öğrenme
    AUDITORY = "auditory"  # İşitsel öğrenme
    KINESTHETIC = "kinesthetic"  # Bedensel/hareket
    READING_WRITING = "reading_writing"  # Okuma/yazma
    MULTIMODAL = "multimodal"  # Karma öğrenme


class AdaptationStrategy(Enum):
    """Content adaptation strategies"""

    DIFFICULTY_BASED = "difficulty_based"
    PERFORMANCE_BASED = "performance_based"
    LEARNING_STYLE_BASED = "learning_style_based"
    TIME_BASED = "time_based"
    MASTERY_BASED = "mastery_based"
    COLLABORATIVE = "collaborative"


class ContentDeliveryMode(Enum):
    """Content delivery modes"""

    SEQUENTIAL = "sequential"  # Sıralı sunım
    ADAPTIVE = "adaptive"  # Uyarlanabilir
    BRANCHING = "branching"  # Dallanma
    PERSONALIZED = "personalized"  # Kişiselleştirilmiş
    GAMIFIED = "gamified"  # Oyunlaştırılmış


@dataclass
class LearningPathNode:
    """Node in adaptive learning path"""

    node_id: str
    content_item: ContentItem

    # Node properties
    prerequisites: List[str] = field(default_factory=list)
    next_nodes: List[str] = field(default_factory=list)
    alternative_nodes: List[str] = field(default_factory=list)

    # Adaptation parameters
    min_mastery_threshold: float = 0.7
    recommended_study_time_minutes: int = 15
    retry_limit: int = 3

    # Turkish education context
    curriculum_alignment: Dict[str, str] = field(default_factory=dict)
    exam_relevance: Dict[TurkishExamType, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.node_id:
            self.node_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node_id": self.node_id,
            "content_id": self.content_item.content_id,
            "prerequisites": self.prerequisites,
            "next_nodes": self.next_nodes,
            "alternative_nodes": self.alternative_nodes,
            "min_mastery_threshold": self.min_mastery_threshold,
            "recommended_study_time_minutes": self.recommended_study_time_minutes,
            "retry_limit": self.retry_limit,
            "curriculum_alignment": self.curriculum_alignment,
            "exam_relevance": {k.value: v for k, v in self.exam_relevance.items()},
        }


@dataclass
class StudentLearningProfile:
    """Comprehensive student learning profile"""

    student_id: int

    # Learning preferences
    preferred_learning_style: LearningStyle = LearningStyle.MULTIMODAL
    learning_style_scores: Dict[LearningStyle, float] = field(default_factory=dict)

    # Performance patterns
    average_accuracy: float = 0.0
    learning_velocity: float = 1.0  # Relative to average student
    attention_span_minutes: int = 45
    optimal_study_duration: int = 30

    # Subject-specific data
    subject_proficiencies: Dict[TurkishSubject, float] = field(default_factory=dict)
    weak_topics: List[str] = field(default_factory=list)
    strong_topics: List[str] = field(default_factory=list)

    # Engagement patterns
    preferred_content_types: List[ContentType] = field(default_factory=list)
    engagement_patterns: Dict[str, float] = field(default_factory=dict)
    peak_learning_hours: List[int] = field(default_factory=list)

    # Adaptation history
    adaptation_effectiveness: Dict[str, float] = field(default_factory=dict)
    learning_path_completions: int = 0
    mastery_achievements: int = 0

    # Turkish exam specific
    tyt_readiness: float = 0.0
    ayt_readiness: float = 0.0
    target_exam_type: TurkishExamType = TurkishExamType.TYT
    preparation_timeline_days: int = 365

    def calculate_learning_efficiency(self) -> float:
        """Calculate overall learning efficiency score"""
        efficiency_factors = [
            self.average_accuracy * 0.3,
            self.learning_velocity * 0.2,
            (self.mastery_achievements / max(1, self.learning_path_completions)) * 0.3,
            min(
                1.0,
                sum(self.subject_proficiencies.values())
                / len(self.subject_proficiencies),
            )
            * 0.2,
        ]
        return sum(efficiency_factors)

    def get_recommended_difficulty(self, subject: TurkishSubject) -> DifficultyLevel:
        """Get recommended difficulty level for subject"""
        proficiency = self.subject_proficiencies.get(subject, 0.5)

        if proficiency >= 0.85:
            return DifficultyLevel.ADVANCED
        elif proficiency >= 0.7:
            return DifficultyLevel.INTERMEDIATE
        elif proficiency >= 0.5:
            return DifficultyLevel.BASIC
        else:
            return DifficultyLevel.BASIC

    def update_from_interaction(self, interaction_data: Dict[str, Any]) -> None:
        """Update profile based on learning interaction"""
        # Update accuracy
        if "accuracy" in interaction_data:
            new_accuracy = interaction_data["accuracy"]
            self.average_accuracy = (self.average_accuracy * 0.9) + (new_accuracy * 0.1)

        # Update subject proficiency
        if "subject" in interaction_data and "performance" in interaction_data:
            subject = interaction_data["subject"]
            performance = interaction_data["performance"]

            if subject in self.subject_proficiencies:
                self.subject_proficiencies[subject] = (
                    self.subject_proficiencies[subject] * 0.8 + performance * 0.2
                )
            else:
                self.subject_proficiencies[subject] = performance

        # Update learning velocity based on time taken
        if "expected_time" in interaction_data and "actual_time" in interaction_data:
            expected = interaction_data["expected_time"]
            actual = interaction_data["actual_time"]
            if actual > 0:
                velocity_factor = expected / actual
                self.learning_velocity = (self.learning_velocity * 0.9) + (
                    velocity_factor * 0.1
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "student_id": self.student_id,
            "preferred_learning_style": self.preferred_learning_style.value,
            "learning_style_scores": {
                k.value: v for k, v in self.learning_style_scores.items()
            },
            "average_accuracy": self.average_accuracy,
            "learning_velocity": self.learning_velocity,
            "attention_span_minutes": self.attention_span_minutes,
            "optimal_study_duration": self.optimal_study_duration,
            "subject_proficiencies": {
                k.value: v for k, v in self.subject_proficiencies.items()
            },
            "weak_topics": self.weak_topics,
            "strong_topics": self.strong_topics,
            "preferred_content_types": [
                ct.value for ct in self.preferred_content_types
            ],
            "engagement_patterns": self.engagement_patterns,
            "peak_learning_hours": self.peak_learning_hours,
            "learning_efficiency": self.calculate_learning_efficiency(),
            "tyt_readiness": self.tyt_readiness,
            "ayt_readiness": self.ayt_readiness,
            "target_exam_type": self.target_exam_type.value,
            "preparation_timeline_days": self.preparation_timeline_days,
        }


@dataclass
class AdaptiveLearningPath:
    """Adaptive learning path for a student"""

    path_id: str
    student_id: int
    subject: TurkishSubject

    # Path structure
    nodes: List[LearningPathNode] = field(default_factory=list)
    current_node_id: Optional[str] = None
    completed_nodes: Set[str] = field(default_factory=set)

    # Path properties
    learning_objectives: List[LearningObjective] = field(default_factory=list)
    estimated_completion_hours: float = 0.0
    actual_time_spent_hours: float = 0.0

    # Adaptation settings
    adaptation_strategies: List[AdaptationStrategy] = field(default_factory=list)
    delivery_mode: ContentDeliveryMode = ContentDeliveryMode.ADAPTIVE

    # Progress tracking
    mastery_scores: Dict[str, float] = field(default_factory=dict)  # node_id -> mastery
    attempt_counts: Dict[str, int] = field(default_factory=dict)  # node_id -> attempts
    time_spent: Dict[str, float] = field(default_factory=dict)  # node_id -> hours

    # Turkish curriculum alignment
    curriculum_coverage: Dict[str, bool] = field(default_factory=dict)
    exam_preparation_focus: Dict[TurkishExamType, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.path_id:
            self.path_id = str(uuid.uuid4())

    def add_node(self, node: LearningPathNode) -> None:
        """Add node to learning path"""
        self.nodes.append(node)
        if not self.current_node_id and not node.prerequisites:
            self.current_node_id = node.node_id

    def get_current_node(self) -> Optional[LearningPathNode]:
        """Get current learning node"""
        if not self.current_node_id:
            return None

        for node in self.nodes:
            if node.node_id == self.current_node_id:
                return node
        return None

    def get_next_nodes(self) -> List[LearningPathNode]:
        """Get available next nodes"""
        current_node = self.get_current_node()
        if not current_node:
            return []

        next_nodes = []
        for node_id in current_node.next_nodes:
            node = self.get_node_by_id(node_id)
            if node and self.are_prerequisites_met(node):
                next_nodes.append(node)

        return next_nodes

    def get_node_by_id(self, node_id: str) -> Optional[LearningPathNode]:
        """Get node by ID"""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def are_prerequisites_met(self, node: LearningPathNode) -> bool:
        """Check if node prerequisites are met"""
        for prereq_id in node.prerequisites:
            if prereq_id not in self.completed_nodes:
                return False
            if self.mastery_scores.get(prereq_id, 0) < 0.7:  # Minimum mastery threshold
                return False
        return True

    def complete_node(
        self, node_id: str, mastery_score: float, time_spent_minutes: float
    ) -> bool:
        """Complete a learning node"""
        node = self.get_node_by_id(node_id)
        if not node:
            return False

        self.completed_nodes.add(node_id)
        self.mastery_scores[node_id] = mastery_score
        self.time_spent[node_id] = time_spent_minutes / 60.0  # Convert to hours
        self.actual_time_spent_hours += time_spent_minutes / 60.0

        # Move to next node if mastery achieved
        if mastery_score >= node.min_mastery_threshold:
            next_nodes = self.get_next_nodes()
            if next_nodes:
                # Choose best next node based on adaptation strategy
                self.current_node_id = self._select_next_node(next_nodes).node_id
            else:
                self.current_node_id = None  # Path completed

        return True

    def _select_next_node(
        self, available_nodes: List[LearningPathNode]
    ) -> LearningPathNode:
        """Select best next node based on adaptation strategies"""
        if len(available_nodes) == 1:
            return available_nodes[0]

        # For now, simple selection based on difficulty and prerequisites
        # In a full implementation, would use more sophisticated algorithm
        return available_nodes[0]

    def calculate_completion_percentage(self) -> float:
        """Calculate path completion percentage"""
        if not self.nodes:
            return 0.0

        completed_count = len(self.completed_nodes)
        total_count = len(self.nodes)

        return (completed_count / total_count) * 100

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get comprehensive progress summary"""
        total_nodes = len(self.nodes)
        completed_nodes = len(self.completed_nodes)

        # Calculate average mastery
        if self.mastery_scores:
            avg_mastery = sum(self.mastery_scores.values()) / len(self.mastery_scores)
        else:
            avg_mastery = 0.0

        # Calculate time efficiency
        if self.estimated_completion_hours > 0:
            time_efficiency = self.estimated_completion_hours / max(
                0.1, self.actual_time_spent_hours
            )
        else:
            time_efficiency = 1.0

        return {
            "completion_percentage": self.calculate_completion_percentage(),
            "nodes_completed": completed_nodes,
            "total_nodes": total_nodes,
            "average_mastery": avg_mastery,
            "time_spent_hours": self.actual_time_spent_hours,
            "estimated_hours": self.estimated_completion_hours,
            "time_efficiency": time_efficiency,
            "current_node_id": self.current_node_id,
            "subject": self.subject.value,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "path_id": self.path_id,
            "student_id": self.student_id,
            "subject": self.subject.value,
            "nodes": [node.to_dict() for node in self.nodes],
            "current_node_id": self.current_node_id,
            "completed_nodes": list(self.completed_nodes),
            "learning_objectives": [lo.value for lo in self.learning_objectives],
            "estimated_completion_hours": self.estimated_completion_hours,
            "actual_time_spent_hours": self.actual_time_spent_hours,
            "adaptation_strategies": [as_.value for as_ in self.adaptation_strategies],
            "delivery_mode": self.delivery_mode.value,
            "mastery_scores": self.mastery_scores,
            "attempt_counts": self.attempt_counts,
            "time_spent": self.time_spent,
            "progress_summary": self.get_progress_summary(),
            "exam_preparation_focus": {
                k.value: v for k, v in self.exam_preparation_focus.items()
            },
        }


class AdaptationEngine:
    """Engine for making adaptive learning decisions"""

    def __init__(self):
        self.adaptation_algorithms = self._initialize_algorithms()
        self.learning_analytics = defaultdict(list)

    def _initialize_algorithms(self) -> Dict[AdaptationStrategy, callable]:
        """Initialize adaptation algorithms"""
        return {
            AdaptationStrategy.DIFFICULTY_BASED: self._adapt_by_difficulty,
            AdaptationStrategy.PERFORMANCE_BASED: self._adapt_by_performance,
            AdaptationStrategy.LEARNING_STYLE_BASED: self._adapt_by_learning_style,
            AdaptationStrategy.TIME_BASED: self._adapt_by_time,
            AdaptationStrategy.MASTERY_BASED: self._adapt_by_mastery,
        }

    async def adapt_content_selection(
        self,
        student_profile: StudentLearningProfile,
        learning_path: AdaptiveLearningPath,
        available_content: List[ContentItem],
        context: Dict[str, Any] = None,
    ) -> List[ContentItem]:
        """Select and adapt content for student"""
        context = context or {}

        adapted_content = []

        for strategy in learning_path.adaptation_strategies:
            algorithm = self.adaptation_algorithms.get(strategy)
            if algorithm:
                strategy_content = await algorithm(
                    student_profile, learning_path, available_content, context
                )
                adapted_content.extend(strategy_content)

        # Remove duplicates while preserving order
        seen_ids = set()
        unique_content = []
        for content in adapted_content:
            if content.content_id not in seen_ids:
                unique_content.append(content)
                seen_ids.add(content.content_id)

        # Limit to reasonable number
        max_content = context.get("max_content_items", 10)
        return unique_content[:max_content]

    async def _adapt_by_difficulty(
        self,
        student_profile: StudentLearningProfile,
        learning_path: AdaptiveLearningPath,
        available_content: List[ContentItem],
        context: Dict[str, Any],
    ) -> List[ContentItem]:
        """Adapt content based on difficulty level"""
        target_difficulty = student_profile.get_recommended_difficulty(
            learning_path.subject
        )

        # Filter content by appropriate difficulty
        suitable_content = [
            content
            for content in available_content
            if content.metadata.difficulty_level == target_difficulty
        ]

        # If not enough content at target level, include adjacent levels
        if len(suitable_content) < 3:
            if target_difficulty == DifficultyLevel.BASIC:
                adjacent_content = [
                    c
                    for c in available_content
                    if c.metadata.difficulty_level == DifficultyLevel.INTERMEDIATE
                ]
            elif target_difficulty == DifficultyLevel.ADVANCED:
                adjacent_content = [
                    c
                    for c in available_content
                    if c.metadata.difficulty_level == DifficultyLevel.INTERMEDIATE
                ]
            else:  # INTERMEDIATE
                adjacent_content = [
                    c
                    for c in available_content
                    if c.metadata.difficulty_level
                    in [DifficultyLevel.BASIC, DifficultyLevel.ADVANCED]
                ]

            suitable_content.extend(adjacent_content)

        return suitable_content

    async def _adapt_by_performance(
        self,
        student_profile: StudentLearningProfile,
        learning_path: AdaptiveLearningPath,
        available_content: List[ContentItem],
        context: Dict[str, Any],
    ) -> List[ContentItem]:
        """Adapt content based on performance patterns"""
        # Focus on weak topics
        weak_topic_content = []
        for topic in student_profile.weak_topics:
            topic_content = [
                content
                for content in available_content
                if topic.lower() in [t.lower() for t in content.metadata.topics]
            ]
            weak_topic_content.extend(topic_content)

        # Add remedial content if performance is low
        if student_profile.average_accuracy < 0.6:
            remedial_content = [
                content
                for content in available_content
                if content.metadata.difficulty_level == DifficultyLevel.BASIC
                and content.content_type in [ContentType.VIDEO, ContentType.INTERACTIVE]
            ]
            weak_topic_content.extend(remedial_content)

        return weak_topic_content

    async def _adapt_by_learning_style(
        self,
        student_profile: StudentLearningProfile,
        learning_path: AdaptiveLearningPath,
        available_content: List[ContentItem],
        context: Dict[str, Any],
    ) -> List[ContentItem]:
        """Adapt content based on learning style preferences"""
        preferred_style = student_profile.preferred_learning_style

        # Map learning styles to content types
        style_content_mapping = {
            LearningStyle.VISUAL: [
                ContentType.IMAGE,
                ContentType.VIDEO,
                ContentType.INTERACTIVE,
            ],
            LearningStyle.AUDITORY: [ContentType.VIDEO, ContentType.AUDIO],
            LearningStyle.READING_WRITING: [ContentType.DOCUMENT, ContentType.QUESTION],
            LearningStyle.KINESTHETIC: [
                ContentType.INTERACTIVE,
                ContentType.SIMULATION,
            ],
            LearningStyle.MULTIMODAL: list(ContentType),
        }

        preferred_types = style_content_mapping.get(preferred_style, list(ContentType))

        style_adapted_content = [
            content
            for content in available_content
            if content.content_type in preferred_types
        ]

        return style_adapted_content

    async def _adapt_by_time(
        self,
        student_profile: StudentLearningProfile,
        learning_path: AdaptiveLearningPath,
        available_content: List[ContentItem],
        context: Dict[str, Any],
    ) -> List[ContentItem]:
        """Adapt content based on available time and attention span"""
        available_minutes = context.get(
            "available_time_minutes", student_profile.optimal_study_duration
        )

        # Filter content that fits within time constraints
        time_appropriate_content = [
            content
            for content in available_content
            if content.metadata.estimated_duration_minutes <= available_minutes
        ]

        # Prioritize shorter content if attention span is limited
        if student_profile.attention_span_minutes < 30:
            time_appropriate_content = [
                content
                for content in time_appropriate_content
                if content.metadata.estimated_duration_minutes <= 15
            ]

        return time_appropriate_content

    async def _adapt_by_mastery(
        self,
        student_profile: StudentLearningProfile,
        learning_path: AdaptiveLearningPath,
        available_content: List[ContentItem],
        context: Dict[str, Any],
    ) -> List[ContentItem]:
        """Adapt content based on mastery levels"""
        # Find topics that need reinforcement
        low_mastery_topics = []

        for node_id, mastery in learning_path.mastery_scores.items():
            if mastery < 0.8:  # Below mastery threshold
                node = learning_path.get_node_by_id(node_id)
                if node:
                    low_mastery_topics.extend(node.content_item.metadata.topics)

        # Select content for reinforcement
        reinforcement_content = [
            content
            for content in available_content
            if any(topic in content.metadata.topics for topic in low_mastery_topics)
        ]

        return reinforcement_content

    def analyze_adaptation_effectiveness(
        self, student_id: int, adaptation_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Analyze effectiveness of different adaptation strategies"""
        strategy_effectiveness = defaultdict(list)

        for result in adaptation_results:
            strategy = result.get("strategy")
            effectiveness = result.get("effectiveness_score", 0.0)

            if strategy:
                strategy_effectiveness[strategy].append(effectiveness)

        # Calculate average effectiveness for each strategy
        avg_effectiveness = {}
        for strategy, scores in strategy_effectiveness.items():
            avg_effectiveness[strategy] = sum(scores) / len(scores) if scores else 0.0

        return avg_effectiveness


class ContentDeliveryService:
    """Service for adaptive content delivery"""

    def __init__(self):
        self.adaptation_engine = AdaptationEngine()
        self.student_profiles: Dict[int, StudentLearningProfile] = {}
        self.learning_paths: Dict[str, AdaptiveLearningPath] = {}
        self.content_repository = {}  # Would be injected in real implementation

        # Delivery settings
        self.max_concurrent_content = config.get_setting(
            "content.max_concurrent_delivery", 5
        )
        self.adaptation_interval_minutes = config.get_setting(
            "content.adaptation_interval", 15
        )

    async def initialize_student_profile(
        self, student_id: int, initial_assessment: Dict[str, Any] = None
    ) -> StudentLearningProfile:
        """Initialize or update student learning profile"""
        if student_id in self.student_profiles:
            profile = self.student_profiles[student_id]
        else:
            profile = StudentLearningProfile(student_id=student_id)

        # Update profile with assessment data
        if initial_assessment:
            self._update_profile_from_assessment(profile, initial_assessment)

        self.student_profiles[student_id] = profile
        logger.info(f"Initialized learning profile for student {student_id}")

        return profile

    def _update_profile_from_assessment(
        self, profile: StudentLearningProfile, assessment: Dict[str, Any]
    ) -> None:
        """Update profile based on initial assessment"""
        # Learning style assessment
        if "learning_style_scores" in assessment:
            for style_str, score in assessment["learning_style_scores"].items():
                try:
                    style = LearningStyle(style_str)
                    profile.learning_style_scores[style] = score
                except ValueError:
                    continue

            # Set preferred style
            if profile.learning_style_scores:
                max_style = max(
                    profile.learning_style_scores.items(), key=lambda x: x[1]
                )
                profile.preferred_learning_style = max_style[0]

        # Subject proficiencies
        if "subject_scores" in assessment:
            for subject_str, score in assessment["subject_scores"].items():
                try:
                    subject = TurkishSubject(subject_str)
                    profile.subject_proficiencies[subject] = (
                        score / 100.0
                    )  # Normalize to 0-1
                except ValueError:
                    continue

        # Learning preferences
        if "preferred_content_types" in assessment:
            profile.preferred_content_types = [
                ContentType(ct)
                for ct in assessment["preferred_content_types"]
                if ct in [c.value for c in ContentType]
            ]

        # Time preferences
        if "optimal_study_duration" in assessment:
            profile.optimal_study_duration = assessment["optimal_study_duration"]

        if "attention_span" in assessment:
            profile.attention_span_minutes = assessment["attention_span"]

        # Exam preparation
        if "target_exam" in assessment:
            try:
                profile.target_exam_type = TurkishExamType(assessment["target_exam"])
            except ValueError:
                pass

        if "preparation_timeline" in assessment:
            profile.preparation_timeline_days = assessment["preparation_timeline"]

    async def create_adaptive_learning_path(
        self,
        student_id: int,
        subject: TurkishSubject,
        learning_objectives: List[LearningObjective],
        available_content: List[ContentItem],
        path_config: Dict[str, Any] = None,
    ) -> AdaptiveLearningPath:
        """Create adaptive learning path for student"""
        path_config = path_config or {}

        # Get student profile
        profile = self.student_profiles.get(student_id)
        if not profile:
            profile = await self.initialize_student_profile(student_id)

        # Create learning path
        learning_path = AdaptiveLearningPath(
            path_id=str(uuid.uuid4()),
            student_id=student_id,
            subject=subject,
            learning_objectives=learning_objectives,
        )

        # Set adaptation strategies
        learning_path.adaptation_strategies = path_config.get(
            "strategies",
            [
                AdaptationStrategy.DIFFICULTY_BASED,
                AdaptationStrategy.PERFORMANCE_BASED,
                AdaptationStrategy.LEARNING_STYLE_BASED,
            ],
        )

        # Set delivery mode
        learning_path.delivery_mode = ContentDeliveryMode(
            path_config.get("delivery_mode", "adaptive")
        )

        # Build path structure
        await self._build_learning_path_structure(
            learning_path, available_content, profile
        )

        # Store path
        self.learning_paths[learning_path.path_id] = learning_path

        logger.info(
            f"Created adaptive learning path {learning_path.path_id} for student {student_id}"
        )
        return learning_path

    async def _build_learning_path_structure(
        self,
        learning_path: AdaptiveLearningPath,
        available_content: List[ContentItem],
        profile: StudentLearningProfile,
    ) -> None:
        """Build the structure of the learning path"""
        # Filter content by subject
        subject_content = [
            content
            for content in available_content
            if content.metadata.subject == learning_path.subject
        ]

        # Group content by topics and difficulty
        topic_content = defaultdict(lambda: defaultdict(list))
        for content in subject_content:
            for topic in content.metadata.topics:
                difficulty = content.metadata.difficulty_level
                topic_content[topic][difficulty].append(content)

        # Create learning nodes for each topic/difficulty combination
        topic_order = self._determine_topic_order(
            list(topic_content.keys()), learning_path.subject
        )

        previous_nodes = []
        for i, topic in enumerate(topic_order):
            difficulty_order = [
                DifficultyLevel.BASIC,
                DifficultyLevel.INTERMEDIATE,
                DifficultyLevel.ADVANCED,
            ]

            topic_nodes = []
            for difficulty in difficulty_order:
                if difficulty in topic_content[topic]:
                    # Select best content for this topic/difficulty
                    best_content = self._select_best_content(
                        topic_content[topic][difficulty], profile
                    )

                    if best_content:
                        node = LearningPathNode(
                            node_id=str(uuid.uuid4()),
                            content_item=best_content,
                            prerequisites=[node.node_id for node in previous_nodes],
                            min_mastery_threshold=0.7,
                            recommended_study_time_minutes=best_content.metadata.estimated_duration_minutes,
                        )

                        # Set exam relevance
                        if learning_path.subject in [
                            TurkishSubject.MATEMATIK,
                            TurkishSubject.FIZIK,
                            TurkishSubject.KIMYA,
                            TurkishSubject.BIYOLOJI,
                        ]:
                            node.exam_relevance[TurkishExamType.TYT] = 0.8
                            node.exam_relevance[TurkishExamType.AYT] = 0.9
                        else:
                            node.exam_relevance[TurkishExamType.TYT] = 0.9
                            node.exam_relevance[TurkishExamType.AYT] = 0.5

                        learning_path.add_node(node)
                        topic_nodes.append(node)

            # Update next_nodes for previous topic nodes
            if previous_nodes and topic_nodes:
                for prev_node in previous_nodes:
                    prev_node.next_nodes.extend([node.node_id for node in topic_nodes])

            previous_nodes = topic_nodes

        # Calculate estimated completion time
        total_time = sum(
            node.recommended_study_time_minutes for node in learning_path.nodes
        )
        learning_path.estimated_completion_hours = total_time / 60.0

    def _determine_topic_order(
        self, topics: List[str], subject: TurkishSubject
    ) -> List[str]:
        """Determine optimal order for topics based on subject"""
        # This would contain curriculum-based topic ordering
        # For now, simple alphabetical order
        topic_order_mapping = {
            TurkishSubject.MATEMATIK: [
                "Sayılar",
                "Cebir",
                "Geometri",
                "Fonksiyonlar",
                "Türev",
                "İntegral",
                "Olasılık",
            ],
            TurkishSubject.FIZIK: [
                "Hareket",
                "Kuvvet",
                "Enerji",
                "İmpuls",
                "Elektrik",
                "Manyetizma",
                "Dalga",
            ],
            TurkishSubject.KIMYA: [
                "Atom",
                "Molekül",
                "Reaksiyonlar",
                "Asit-Baz",
                "Elektrokimya",
                "Organik Kimya",
            ],
        }

        default_order = topic_order_mapping.get(subject, topics)

        # Filter to only include available topics
        ordered_topics = [topic for topic in default_order if topic in topics]

        # Add any missing topics at the end
        missing_topics = [topic for topic in topics if topic not in ordered_topics]
        ordered_topics.extend(sorted(missing_topics))

        return ordered_topics

    def _select_best_content(
        self, content_list: List[ContentItem], profile: StudentLearningProfile
    ) -> Optional[ContentItem]:
        """Select best content based on student profile"""
        if not content_list:
            return None

        # Score each content item
        content_scores = []
        for content in content_list:
            score = 0.0

            # Prefer content types matching learning style
            if content.content_type in profile.preferred_content_types:
                score += 2.0

            # Prefer appropriate duration
            if (
                content.metadata.estimated_duration_minutes
                <= profile.optimal_study_duration
            ):
                score += 1.0

            # Prefer higher quality content
            score += content.engagement_score / 100.0

            # Prefer content with good ratings
            if content.rating > 0:
                score += content.rating / 5.0

            content_scores.append((content, score))

        # Return highest scoring content
        best_content = max(content_scores, key=lambda x: x[1])[0]
        return best_content

    async def get_next_content(
        self, student_id: int, path_id: str, context: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Get next adaptive content for student"""
        learning_path = self.learning_paths.get(path_id)
        profile = self.student_profiles.get(student_id)

        if not learning_path or not profile:
            return None

        current_node = learning_path.get_current_node()
        if not current_node:
            # Path completed or no current node
            return {
                "status": "completed",
                "message": "Öğrenme yolu tamamlandı!",
                "progress": learning_path.get_progress_summary(),
            }

        # Get adapted content based on current context
        available_content = [current_node.content_item]

        # Add alternative content if available
        for alt_node_id in current_node.alternative_nodes:
            alt_node = learning_path.get_node_by_id(alt_node_id)
            if alt_node:
                available_content.append(alt_node.content_item)

        # Apply adaptation strategies
        adapted_content = await self.adaptation_engine.adapt_content_selection(
            profile, learning_path, available_content, context
        )

        if not adapted_content:
            return None

        primary_content = adapted_content[0]

        # Prepare delivery response
        delivery_response = {
            "content_id": primary_content.content_id,
            "content_type": primary_content.content_type.value,
            "title": primary_content.metadata.title,
            "title_tr": primary_content.title_tr,
            "description": primary_content.metadata.description,
            "description_tr": primary_content.description_tr,
            "estimated_duration_minutes": primary_content.metadata.estimated_duration_minutes,
            "difficulty_level": primary_content.metadata.difficulty_level.value,
            "learning_objectives": [
                lo.value for lo in primary_content.metadata.learning_objectives
            ],
            "node_id": current_node.node_id,
            "progress": learning_path.get_progress_summary(),
            "adaptation_info": {
                "strategies_applied": [
                    s.value for s in learning_path.adaptation_strategies
                ],
                "learning_style_match": primary_content.content_type
                in profile.preferred_content_types,
                "difficulty_appropriate": True,  # Would calculate based on profile
            },
            "alternative_content": [
                {
                    "content_id": alt.content_id,
                    "title": alt.metadata.title,
                    "content_type": alt.content_type.value,
                }
                for alt in adapted_content[1:3]  # Include up to 2 alternatives
            ],
        }

        return delivery_response

    async def record_learning_interaction(
        self,
        student_id: int,
        path_id: str,
        node_id: str,
        interaction_data: Dict[str, Any],
    ) -> bool:
        """Record student interaction with learning content"""
        learning_path = self.learning_paths.get(path_id)
        profile = self.student_profiles.get(student_id)

        if not learning_path or not profile:
            return False

        # Update attempt count
        learning_path.attempt_counts[node_id] = (
            learning_path.attempt_counts.get(node_id, 0) + 1
        )

        # Extract interaction metrics
        time_spent_minutes = interaction_data.get("time_spent_minutes", 0)
        accuracy = interaction_data.get("accuracy", 0.0)
        completed = interaction_data.get("completed", False)

        # Calculate mastery score
        mastery_score = self._calculate_mastery_score(interaction_data)

        # Update learning path
        if completed:
            learning_path.complete_node(node_id, mastery_score, time_spent_minutes)

        # Update student profile
        profile.update_from_interaction(
            {
                "accuracy": accuracy,
                "subject": learning_path.subject,
                "performance": mastery_score,
                "expected_time": learning_path.get_node_by_id(
                    node_id
                ).recommended_study_time_minutes
                if learning_path.get_node_by_id(node_id)
                else 15,
                "actual_time": time_spent_minutes,
            }
        )

        # Log interaction for analytics
        logger.info(
            f"Recorded learning interaction for student {student_id}, mastery: {mastery_score:.2f}"
        )

        return True

    def _calculate_mastery_score(self, interaction_data: Dict[str, Any]) -> float:
        """Calculate mastery score from interaction data"""
        # Base score from accuracy
        accuracy = interaction_data.get("accuracy", 0.0)
        base_score = accuracy

        # Time bonus (completed faster than expected)
        time_spent = interaction_data.get("time_spent_minutes", 0)
        expected_time = interaction_data.get("expected_time_minutes", time_spent)

        if expected_time > 0 and time_spent > 0:
            time_efficiency = expected_time / time_spent
            if time_efficiency > 1.0:  # Completed faster than expected
                base_score *= min(1.2, time_efficiency)  # Up to 20% bonus

        # Completion bonus
        if interaction_data.get("completed", False):
            base_score += 0.1

        # Effort bonus (number of attempts)
        attempts = interaction_data.get("attempts", 1)
        if attempts == 1:
            base_score += 0.05  # First-try bonus

        return min(1.0, base_score)

    async def get_learning_analytics(self, student_id: int) -> Dict[str, Any]:
        """Get comprehensive learning analytics for student"""
        profile = self.student_profiles.get(student_id)
        if not profile:
            return {}

        # Get all paths for student
        student_paths = [
            path
            for path in self.learning_paths.values()
            if path.student_id == student_id
        ]

        # Calculate analytics
        analytics = {
            "student_id": student_id,
            "profile_summary": profile.to_dict(),
            "learning_efficiency": profile.calculate_learning_efficiency(),
            "paths": [path.get_progress_summary() for path in student_paths],
            "overall_progress": {
                "total_paths": len(student_paths),
                "completed_paths": len(
                    [
                        p
                        for p in student_paths
                        if p.calculate_completion_percentage() == 100
                    ]
                ),
                "total_study_hours": sum(
                    p.actual_time_spent_hours for p in student_paths
                ),
                "average_mastery": sum(
                    sum(p.mastery_scores.values()) for p in student_paths
                )
                / max(1, sum(len(p.mastery_scores) for p in student_paths)),
            },
            "recommendations": self._generate_learning_recommendations(
                profile, student_paths
            ),
        }

        return analytics

    def _generate_learning_recommendations(
        self, profile: StudentLearningProfile, paths: List[AdaptiveLearningPath]
    ) -> List[Dict[str, str]]:
        """Generate personalized learning recommendations"""
        recommendations = []

        # Study time recommendations
        if profile.learning_velocity < 0.8:
            recommendations.append(
                {
                    "type": "study_pattern",
                    "title": "Çalışma Hızını Artırın",
                    "message": "Daha kısa süreli ama sık çalışma seansları deneyin",
                    "action": "shorter_sessions",
                }
            )

        # Subject focus recommendations
        weak_subjects = [
            subject
            for subject, score in profile.subject_proficiencies.items()
            if score < 0.6
        ]

        if weak_subjects:
            subject_names = [subject.value for subject in weak_subjects[:2]]
            recommendations.append(
                {
                    "type": "subject_focus",
                    "title": "Zayıf Konulara Odaklanın",
                    "message": f"{', '.join(subject_names)} konularında ekstra çalışma yapın",
                    "action": "focus_weak_subjects",
                }
            )

        # Learning style recommendations
        if profile.preferred_learning_style != LearningStyle.MULTIMODAL:
            recommendations.append(
                {
                    "type": "learning_style",
                    "title": "Öğrenme Stilinizi Geliştirin",
                    "message": f"{profile.preferred_learning_style.value} stilini destekleyen içerikleri tercih edin",
                    "action": "optimize_content_type",
                }
            )

        # Time management recommendations
        if profile.optimal_study_duration > profile.attention_span_minutes:
            recommendations.append(
                {
                    "type": "time_management",
                    "title": "Çalışma Sürelerini Ayarlayın",
                    "message": "Dikkat sürenize uygun daha kısa bloklar halinde çalışın",
                    "action": "adjust_study_duration",
                }
            )

        return recommendations


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Adaptive Learning Content Delivery System")
    print("=" * 50)

    async def test_adaptive_system():
        """Test adaptive learning system"""
        service = ContentDeliveryService()

        # Initialize student profile
        initial_assessment = {
            "learning_style_scores": {
                "visual": 0.8,
                "auditory": 0.6,
                "reading_writing": 0.4,
                "kinesthetic": 0.3,
            },
            "subject_scores": {"matematik": 75, "fizik": 65, "kimya": 55},
            "preferred_content_types": ["video", "interactive"],
            "optimal_study_duration": 30,
            "attention_span": 25,
            "target_exam": "tyt",
            "preparation_timeline": 180,
        }

        profile = await service.initialize_student_profile(
            student_id=12345, initial_assessment=initial_assessment
        )

        print(f"Initialized profile for student {profile.student_id}")
        print(f"Learning efficiency: {profile.calculate_learning_efficiency():.2f}")
        print(f"Preferred learning style: {profile.preferred_learning_style.value}")

        # Create sample content (would come from content repository)
        from content.unified_content_management import ContentMetadata

        sample_metadata = ContentMetadata(
            title="Türev Alma Kuralları",
            description="Temel türev alma kuralları",
            subject=TurkishSubject.MATEMATIK,
            exam_types=[TurkishExamType.TYT, TurkishExamType.AYT],
            grade_levels=[11, 12],
            topics=["Kalkülüs", "Türev"],
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            learning_objectives=[
                LearningObjective.COMPREHENSION,
                LearningObjective.APPLICATION,
            ],
            estimated_duration_minutes=20,
        )

        sample_content = ContentItem(
            content_id=str(uuid.uuid4()),
            content_type=ContentType.VIDEO,
            metadata=sample_metadata,
        )

        # Create adaptive learning path
        learning_path = await service.create_adaptive_learning_path(
            student_id=12345,
            subject=TurkishSubject.MATEMATIK,
            learning_objectives=[
                LearningObjective.COMPREHENSION,
                LearningObjective.APPLICATION,
            ],
            available_content=[sample_content],
        )

        print(f"Created learning path: {learning_path.path_id}")
        print(f"Path has {len(learning_path.nodes)} nodes")
        print(
            f"Estimated completion: {learning_path.estimated_completion_hours:.1f} hours"
        )

        # Get next content
        next_content = await service.get_next_content(
            student_id=12345, path_id=learning_path.path_id
        )

        if next_content:
            print(f"Next content: {next_content['title']}")
            print(f"Duration: {next_content['estimated_duration_minutes']} minutes")
            print(f"Progress: {next_content['progress']['completion_percentage']:.1f}%")

        # Simulate learning interaction
        interaction_data = {
            "time_spent_minutes": 18,
            "accuracy": 0.85,
            "completed": True,
            "attempts": 1,
        }

        success = await service.record_learning_interaction(
            student_id=12345,
            path_id=learning_path.path_id,
            node_id=learning_path.current_node_id,
            interaction_data=interaction_data,
        )

        print(f"Recorded interaction: {success}")

        # Get learning analytics
        analytics = await service.get_learning_analytics(12345)
        print(f"Overall progress: {analytics['overall_progress']}")
        print(f"Recommendations: {len(analytics['recommendations'])}")

    # Run test
    asyncio.run(test_adaptive_system())
