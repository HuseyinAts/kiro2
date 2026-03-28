"""
Path Adaptation Service
Teknofest 2025 - Eğitim Eylemci Projesi

Service for dynamically adapting learning paths based on student performance.
Monitors student progress and adjusts difficulty, pacing, and resources
to optimize learning outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .resource_discovery import (
        ResourceDiscoveryService,
    )

import logging

from ..config import get_learning_path_config
from ..models import (
    LearningPath,
    LearningStyle,
    PathNode,
    StudentProfile,
)

logger = logging.getLogger(__name__)


class AdaptationType(Enum):
    """Types of path adaptations."""

    DIFFICULTY_ADJUSTMENT = "difficulty_adjustment"
    PACING_CHANGE = "pacing_change"
    RESOURCE_SWAP = "resource_swap"
    TOPIC_SKIP = "topic_skip"
    TOPIC_ADD = "topic_add"
    STYLE_ADJUSTMENT = "style_adjustment"
    REMEDIATION = "remediation"


@dataclass
class PerformanceMetrics:
    """Student performance metrics for a topic."""

    topic: str
    quiz_score: float | None = None  # 0-100
    completion_time_minutes: int | None = None
    attempts: int = 1
    resources_viewed: int = 0
    notes_taken: bool = False

    @property
    def is_struggling(self) -> bool:
        """Check if student is struggling with topic."""
        if self.quiz_score is not None and self.quiz_score < 60:
            return True
        if self.attempts > 2 and self.quiz_score is not None and self.quiz_score < 70:
            return True
        return False

    @property
    def is_excelling(self) -> bool:
        """Check if student is excelling at topic."""
        if self.quiz_score is not None and self.quiz_score >= 90:
            return True
        return False


@dataclass
class AdaptationRequest:
    """Request for path adaptation."""

    path: LearningPath
    student_profile: StudentProfile
    performance_history: list[PerformanceMetrics] = field(default_factory=list)
    trigger_reason: str | None = None


@dataclass
class AdaptationAction:
    """A single adaptation action."""

    type: AdaptationType
    target_node_id: str | None = None
    description: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def adaptation_type(self) -> AdaptationType:
        """Alias for type — used by learning_path_v2.py."""
        return self.type

    @property
    def reason(self) -> str:
        """Alias for description — used by learning_path_v2.py."""
        return self.description


@dataclass
class AdaptationResult:
    """Result of path adaptation."""

    success: bool
    adapted_path: LearningPath | None = None
    actions_taken: list[AdaptationAction] = field(default_factory=list)
    message: str = ""

    @property
    def new_difficulty(self) -> str | None:
        """Derive difficulty from actions — used by learning_path_v2.py."""
        for action in self.actions_taken:
            if action.type == AdaptationType.DIFFICULTY_ADJUSTMENT:
                adj = action.details.get("adjusted_difficulty")
                if adj is not None:
                    return str(adj)
        return None

    @property
    def next_steps(self) -> list[str]:
        """Compile recommendation strings from actions — used by learning_path_v2.py."""
        return [a.description for a in self.actions_taken if a.description]


class PathAdaptationService:
    """Service for dynamically adapting learning paths based on student performance.

    Monitors student progress and adjusts difficulty, pacing, and resources
    to optimize learning outcomes.
    """

    def __init__(
        self,
        resource_discovery: ResourceDiscoveryService | None = None,
        llm_service: Any | None = None,
    ):
        """Initialize the path adaptation service.

        Args:
            resource_discovery: Optional resource discovery service for finding new resources
            llm_service: Optional LLM service for content generation
        """
        self.config = get_learning_path_config()
        self.resource_discovery = resource_discovery
        self.llm_service = llm_service

        # Adaptation thresholds
        self.struggle_threshold = 60  # Quiz score below this = struggling
        self.excel_threshold = 90  # Quiz score above this = excelling
        self.max_attempts_before_help = 2

    async def adapt_path(self, request: AdaptationRequest) -> AdaptationResult:
        """Adapt the learning path based on student performance.

        Args:
            request: Adaptation request with path and performance data

        Returns:
            AdaptationResult with adapted path and actions taken
        """
        try:
            logger.info(f"Adapting path for student: {request.path.student_id}")

            actions: list[AdaptationAction] = []
            adapted_path = request.path

            # Analyze performance patterns
            struggling_topics = self._find_struggling_topics(
                request.performance_history
            )
            excelling_topics = self._find_excelling_topics(request.performance_history)

            # Apply difficulty adjustments
            if struggling_topics:
                difficulty_actions = await self._handle_struggling(
                    adapted_path, struggling_topics, request.student_profile
                )
                actions.extend(difficulty_actions)

            if excelling_topics:
                excel_actions = self._handle_excelling(adapted_path, excelling_topics)
                actions.extend(excel_actions)

            # Apply learning style adjustments
            style_actions = await self._adjust_for_learning_style(
                adapted_path, request.student_profile
            )
            actions.extend(style_actions)

            # Apply pacing adjustments
            pacing_actions = self._adjust_pacing(
                adapted_path, request.performance_history
            )
            actions.extend(pacing_actions)

            logger.info(f"Adaptation complete: {len(actions)} actions taken")

            return AdaptationResult(
                success=True,
                adapted_path=adapted_path,
                actions_taken=actions,
                message=f"Path adapted with {len(actions)} changes",
            )

        except Exception as e:
            logger.error(f"Path adaptation failed: {e}")
            return AdaptationResult(success=False, message=str(e))

    def _find_struggling_topics(
        self, history: list[PerformanceMetrics]
    ) -> list[PerformanceMetrics]:
        """Find topics where student is struggling."""
        return [m for m in history if m.is_struggling]

    def _find_excelling_topics(
        self, history: list[PerformanceMetrics]
    ) -> list[PerformanceMetrics]:
        """Find topics where student is excelling."""
        return [m for m in history if m.is_excelling]

    async def _handle_struggling(
        self,
        path: LearningPath,
        struggling: list[PerformanceMetrics],
        profile: StudentProfile,
    ) -> list[AdaptationAction]:
        """Handle topics where student is struggling."""
        actions: list[AdaptationAction] = []

        for metric in struggling:
            # Find the node for this topic
            node = self._find_node_by_topic(path, metric.topic)
            if not node:
                continue

            # Add remediation resources
            if self.resource_discovery:
                try:
                    from .resource_discovery import (
                        DiscoveryRequest,
                    )

                    request = DiscoveryRequest(
                        query=f"{metric.topic} temel giriş basit",
                        subject=profile.subjects[0] if profile.subjects else None,  # type: ignore
                        difficulty_range=(-4.0, -1.0),  # Easier content
                        limit=3,
                    )

                    result = await self.resource_discovery.discover(request)

                    if result.resources:
                        # Add easier resources to node
                        for resource in result.resources:
                            node.resources.append(resource)

                        actions.append(
                            AdaptationAction(
                                type=AdaptationType.REMEDIATION,
                                target_node_id=node.node_id,
                                description=f"Added {len(result.resources)} easier resources for '{metric.topic}'",
                                details={
                                    "resources_added": len(result.resources),
                                    "reason": f"Quiz score: {metric.quiz_score}%",
                                },
                            )
                        )
                except Exception as e:
                    logger.warning(f"Failed to find remediation resources: {e}")

            # Adjust difficulty flag
            current_difficulty = getattr(node, "difficulty", 0)
            adjusted_difficulty = max(-4.0, current_difficulty - 1.0)

            actions.append(
                AdaptationAction(
                    type=AdaptationType.DIFFICULTY_ADJUSTMENT,
                    target_node_id=node.node_id,
                    description=f"Lowered difficulty expectation for '{metric.topic}'",
                    details={
                        "original_difficulty": current_difficulty,
                        "adjusted_difficulty": adjusted_difficulty,
                    },
                )
            )

        return actions

    def _handle_excelling(
        self, path: LearningPath, excelling: list[PerformanceMetrics]
    ) -> list[AdaptationAction]:
        """Handle topics where student is excelling."""
        actions: list[AdaptationAction] = []

        for metric in excelling:
            node = self._find_node_by_topic(path, metric.topic)
            if not node:
                continue

            # Suggest skipping or moving faster
            actions.append(
                AdaptationAction(
                    type=AdaptationType.PACING_CHANGE,
                    target_node_id=node.node_id,
                    description=f"Suggested faster pace for '{metric.topic}'",
                    details={
                        "quiz_score": metric.quiz_score,
                        "recommendation": "Can move to advanced content or skip basics",
                    },
                )
            )

        return actions

    async def _adjust_for_learning_style(
        self, path: LearningPath, profile: StudentProfile
    ) -> list[AdaptationAction]:
        """Adjust resources based on learning style preference."""
        actions: list[AdaptationAction] = []
        style = profile.learning_style

        if not style:
            return actions

        # Define resource type preferences by style
        style_preferences = {
            LearningStyle.VISUAL: ["video", "infographic", "animation"],
            LearningStyle.AUDITORY: ["audio", "podcast", "video"],
            LearningStyle.READING: ["document", "article", "book"],
            LearningStyle.KINESTHETIC: ["exercise", "interactive", "simulation"],
        }

        preferred_types = style_preferences.get(style, [])

        # Check if path has nodes attribute (new structure)
        nodes_to_check: list[PathNode] = []
        if hasattr(path, "nodes") and path.nodes:  # type: ignore
            nodes_to_check = path.nodes  # type: ignore

        for node in nodes_to_check:
            if not node.resources:
                continue

            # Count current resource types
            current_types = [
                r.resource_type for r in node.resources if hasattr(r, "resource_type")
            ]
            preferred_count = sum(1 for t in current_types if t in preferred_types)

            if preferred_count < len(node.resources) // 2:
                # Not enough preferred content, flag for adjustment
                actions.append(
                    AdaptationAction(
                        type=AdaptationType.STYLE_ADJUSTMENT,
                        target_node_id=node.node_id,
                        description=f"Recommended more {style.value} content for '{node.topic}'",
                        details={
                            "current_types": current_types,
                            "preferred_types": preferred_types,
                            "learning_style": style.value,
                        },
                    )
                )

        return actions

    def _adjust_pacing(
        self, path: LearningPath, history: list[PerformanceMetrics]
    ) -> list[AdaptationAction]:
        """Adjust pacing based on completion times."""
        actions: list[AdaptationAction] = []

        # Calculate average completion ratio
        completion_ratios: list[float] = []
        for metric in history:
            if metric.completion_time_minutes:
                # Find expected time from path
                node = self._find_node_by_topic(path, metric.topic)
                if node and node.estimated_time > 0:
                    ratio = metric.completion_time_minutes / node.estimated_time
                    completion_ratios.append(ratio)

        if not completion_ratios:
            return actions

        avg_ratio = sum(completion_ratios) / len(completion_ratios)

        if avg_ratio > 1.5:
            # Taking much longer than expected
            actions.append(
                AdaptationAction(
                    type=AdaptationType.PACING_CHANGE,
                    description="Student is taking longer than expected. Consider reducing daily goals.",
                    details={
                        "average_completion_ratio": avg_ratio,
                        "recommendation": "Reduce daily study targets by 20-30%",
                    },
                )
            )
        elif avg_ratio < 0.5:
            # Finishing much faster than expected
            actions.append(
                AdaptationAction(
                    type=AdaptationType.PACING_CHANGE,
                    description="Student is finishing faster than expected. Consider adding more content.",
                    details={
                        "average_completion_ratio": avg_ratio,
                        "recommendation": "Increase daily study targets or add advanced content",
                    },
                )
            )

        return actions

    def _find_node_by_topic(self, path: LearningPath, topic: str) -> PathNode | None:
        """Find a path node by topic name."""
        # Check if path has nodes attribute (new structure)
        if hasattr(path, "nodes"):
            nodes = path.nodes  # type: ignore
            for node in nodes:
                if node.topic.lower() == topic.lower():
                    return node
        return None

    async def get_recommendations(
        self, path: LearningPath, student_profile: StudentProfile
    ) -> list[str]:
        """Get adaptation recommendations without applying them.

        Args:
            path: Current learning path
            student_profile: Student's profile

        Returns:
            List of recommendation strings
        """
        recommendations: list[str] = []

        # Check if path has nodes attribute
        if hasattr(path, "nodes"):
            nodes = path.nodes  # type: ignore
            completed = sum(1 for n in nodes if n.is_completed)
            total = len(nodes)
            progress = (completed / total * 100) if total > 0 else 0

            if progress < 20 and completed == 0:
                recommendations.append(
                    "Başlamak için ilk konuyu açın ve video kaynaklarını izleyin."
                )

            if progress > 50 and progress < 75:
                recommendations.append(
                    "Yarıyı geçtiniz! Devam ederek hedeflerinize ulaşabilirsiniz."
                )

            if progress >= 90:
                recommendations.append(
                    "Neredeyse tamamladınız! Son konuları bitirip sınava hazırlanın."
                )

        # Learning style specific
        if student_profile.learning_style == LearningStyle.VISUAL:
            recommendations.append(
                "Görsel öğrenen olarak video içeriklere öncelik vermenizi öneririz."
            )
        elif student_profile.learning_style == LearningStyle.KINESTHETIC:
            recommendations.append(
                "Pratik yaparak öğrenirsiniz. Her konuda soru çözmeyi unutmayın."
            )

        return recommendations
