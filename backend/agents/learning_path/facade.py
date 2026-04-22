"""
Learning Path Facade - Unified interface for the learning path system.

This facade coordinates all learning path services and provides a simple,
high-level API for the rest of the application. It replaces the monolithic
agent.py (God Class) with a clean, maintainable architecture.

Usage:
    facade = LearningPathFacade()

    # Create path
    result = await facade.create_path_for_student(student_id, subject="matematik")

    # Search resources
    resources = await facade.search_resources("türev", limit=10)

    # Process chat
    response = await facade.process_chat(student_id, "İlerleme durumum nedir?")

Teknofest 2025 - Eğitim Eylemci Projesi
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .integrations.chat_integration import (
        ChatIntegrationService,
    )
    from .integrations.form_integration import (
        FormIntegrationService,
    )
    from .services.path_adaptation import (
        PathAdaptationService,
    )
    from .services.path_generation import (
        PathGenerationService,
    )
    from .services.resource_discovery import (
        ResourceDiscoveryService,
    )

from .config import get_learning_path_config
from .integrations.chat_integration import (
    ChatMessage,
    ChatResponse,
)
from .integrations.form_integration import (
    FormDefinition,
    FormSubmission,
    FormSubmissionResult,
)
from .models import (
    KnowledgeLevel,
    LearningPath,
    LearningResource,
    LearningStyle,
    StudentProfile,
)
from .services.path_adaptation import (
    AdaptationRequest,
    AdaptationResult,
    PerformanceMetrics,
)
from .services.path_generation import (
    PathGenerationRequest,
    PathGenerationResult,
)
from .services.resource_discovery import (
    DiscoveryRequest,
)
from .facade_persistence import (
    load_student_path_from_db,
    load_student_profile_from_db,
    persist_student_path,
)

logger = logging.getLogger(__name__)


@dataclass
class FacadeConfig:
    """Configuration for the facade."""

    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    max_resources_per_search: int = 20
    default_difficulty_range: tuple = (-4.0, 4.0)


class LearningPathFacade:
    """
    Unified facade for the Learning Path system.

    This class provides a simplified interface to the learning path subsystem,
    coordinating multiple services:
    - PathGenerationService: Creates personalized learning paths
    - ResourceDiscoveryService: Finds educational resources
    - PathAdaptationService: Adapts paths based on performance
    - ChatIntegrationService: Handles chat interactions
    - FormIntegrationService: Manages forms and profiles

    The facade implements the Facade design pattern, hiding the complexity
    of the subsystem and providing a clean API for external consumers.

    Example:
        >>> facade = LearningPathFacade()
        >>> path = await facade.create_path_for_student("student-123", "matematik")
        >>> resources = await facade.search_resources("türev", limit=5)
    """

    def __init__(
        self,
        path_generation: PathGenerationService | None = None,
        resource_discovery: ResourceDiscoveryService | None = None,
        path_adaptation: PathAdaptationService | None = None,
        chat_integration: ChatIntegrationService | None = None,
        form_integration: FormIntegrationService | None = None,
        config: FacadeConfig | None = None,
    ):
        """
        Initialize the facade with optional service dependencies.

        Args:
            path_generation: Service for generating learning paths
            resource_discovery: Service for discovering resources
            path_adaptation: Service for adapting paths
            chat_integration: Service for chat interactions
            form_integration: Service for form handling
            config: Facade configuration
        """
        self.config = config or FacadeConfig()
        self._app_config = get_learning_path_config()

        # Lazy-initialized services
        self._path_generation = path_generation
        self._resource_discovery = resource_discovery
        self._path_adaptation = path_adaptation
        self._chat_integration = chat_integration
        self._form_integration = form_integration

        # In-memory cache for active paths (could be Redis in production)
        self._paths_cache: dict[str, LearningPath] = {}
        self._profiles_cache: dict[str, StudentProfile] = {}

        logger.info("LearningPathFacade initialized")

    # =====================
    # Service Properties (Lazy Init)
    # =====================

    @property
    def path_generation(self) -> PathGenerationService:
        """Get or create PathGenerationService."""
        if self._path_generation is None:
            from .services.path_generation import PathGenerationService

            self._path_generation = PathGenerationService(
                resource_finder=self.resource_discovery
            )
        return self._path_generation

    @property
    def resource_discovery(self) -> ResourceDiscoveryService:
        """Get or create ResourceDiscoveryService."""
        if self._resource_discovery is None:
            from .services.resource_discovery import ResourceDiscoveryService

            self._resource_discovery = ResourceDiscoveryService()
        return self._resource_discovery

    @property
    def path_adaptation(self) -> PathAdaptationService:
        """Get or create PathAdaptationService."""
        if self._path_adaptation is None:
            from .services.path_adaptation import PathAdaptationService

            self._path_adaptation = PathAdaptationService(
                resource_discovery=self.resource_discovery
            )
        return self._path_adaptation

    @property
    def chat_integration(self) -> ChatIntegrationService:
        """Get or create ChatIntegrationService."""
        if self._chat_integration is None:
            from .integrations.chat_integration import ChatIntegrationService

            self._chat_integration = ChatIntegrationService(
                resource_finder=self.resource_discovery
            )
        return self._chat_integration

    @property
    def form_integration(self) -> FormIntegrationService:
        """Get or create FormIntegrationService."""
        if self._form_integration is None:
            from .integrations.form_integration import FormIntegrationService

            self._form_integration = FormIntegrationService()
        return self._form_integration

    # =====================
    # Path Operations
    # =====================

    async def create_path_for_student(
        self,
        student_id: str,
        subject: str,
        topics: list[str] | None = None,
        target_level: KnowledgeLevel = KnowledgeLevel.INTERMEDIATE,
        max_duration_hours: int = 20,
    ) -> PathGenerationResult:
        """
        Create a personalized learning path for a student.

        Args:
            student_id: Unique student identifier
            subject: Subject to study (matematik, fizik, etc.)
            topics: Optional specific topics to include
            target_level: Target knowledge level
            max_duration_hours: Maximum path duration in hours

        Returns:
            PathGenerationResult with the created path
        """
        logger.info(f"Creating path for student {student_id}, subject: {subject}")

        # Get or create student profile
        profile = await self._get_or_create_profile(student_id)

        # Create generation request
        request = PathGenerationRequest(
            student_profile=profile,
            target_subject=subject,
            target_topics=topics,
            target_level=target_level,
            max_duration_hours=max_duration_hours,
        )

        # Generate path
        result = await self.path_generation.generate_path(request)

        # Cache the path
        if result.success and result.path:
            self._paths_cache[student_id] = result.path
            await persist_student_path(
                result.path, subject, profile
            )

        return result

    async def get_student_path(self, student_id: str) -> LearningPath | None:
        """
        Get the current learning path for a student.

        Args:
            student_id: Student identifier

        Returns:
            LearningPath if exists, None otherwise
        """
        # Check cache first
        if student_id in self._paths_cache:
            return self._paths_cache[student_id]

        loaded = await load_student_path_from_db(student_id)
        if loaded is not None:
            self._paths_cache[student_id] = loaded
            return loaded
        return None

    async def adapt_student_path(
        self,
        student_id: str,
        performance: list[PerformanceMetrics],
    ) -> AdaptationResult:
        """
        Adapt a student's learning path based on performance.

        Args:
            student_id: Student identifier
            performance: List of performance metrics

        Returns:
            AdaptationResult with adaptation details
        """
        logger.info(f"Adapting path for student {student_id}")

        # Get current path
        path = await self.get_student_path(student_id)
        if not path:
            return AdaptationResult(
                success=False, message="No active path found for student"
            )

        # Get profile
        profile = await self._get_or_create_profile(student_id)

        # Create adaptation request
        request = AdaptationRequest(
            path=path,
            student_profile=profile,
            performance_history=performance,
        )

        # Adapt
        result = await self.path_adaptation.adapt_path(request)

        # Update cache
        if result.success and result.adapted_path:
            self._paths_cache[student_id] = result.adapted_path
            subj = (result.adapted_path.metadata or {}).get("subject", "genel")
            prof = await self._get_or_create_profile(student_id)
            await persist_student_path(result.adapted_path, str(subj), prof)

        return result

    # =====================
    # Resource Operations
    # =====================

    async def search_resources(
        self,
        query: str,
        subject: str | None = None,
        difficulty: str | None = None,
        difficulty_range: tuple | None = None,
        limit: int = 10,
        platforms: list[str] | None = None,
    ) -> list[LearningResource]:
        """
        Search for learning resources across all platforms.

        Args:
            query: Search query
            subject: Optional subject filter
            difficulty: Human-readable difficulty (başlangıç/orta/ileri)
            difficulty_range: IRT difficulty range (min, max)
            limit: Maximum results
            platforms: Optional list of platforms to search

        Returns:
            List of matching LearningResource objects
        """
        logger.debug(f"Searching resources: {query}")

        request = DiscoveryRequest(
            query=query,
            subject=subject,
            difficulty=difficulty,
            difficulty_range=difficulty_range or self.config.default_difficulty_range,
            limit=min(limit, self.config.max_resources_per_search),
            preferred_platforms=platforms or [],
        )

        result = await self.resource_discovery.discover(request)
        return result.resources

    async def find_similar_resources(
        self,
        resource: LearningResource,
        limit: int = 5,
    ) -> list[LearningResource]:
        """
        Find resources similar to a given resource.

        Args:
            resource: Reference resource
            limit: Maximum similar resources

        Returns:
            List of similar resources
        """
        return await self.resource_discovery.find_similar(resource, limit)

    # =====================
    # Chat Operations
    # =====================

    async def process_chat(
        self,
        student_id: str,
        message: str,
        session_id: str | None = None,
    ) -> ChatResponse:
        """
        Process a chat message from a student.

        Args:
            student_id: Student identifier
            message: Chat message text
            session_id: Optional session identifier

        Returns:
            ChatResponse with reply and suggestions
        """
        logger.debug(f"Processing chat from {student_id}: {message[:50]}...")

        # Get context
        current_path = await self.get_student_path(student_id)
        profile = await self._get_or_create_profile(student_id)

        # Create message
        chat_message = ChatMessage(
            text=message,
            student_id=student_id,
            session_id=session_id,
        )

        # Process
        return await self.chat_integration.process_message(
            message=chat_message,
            current_path=current_path,
            student_profile=profile,
        )

    # =====================
    # Form Operations
    # =====================

    def get_profile_form(self) -> FormDefinition:
        """Get the student profile creation form."""
        return self.form_integration.get_profile_creation_form()

    def get_learning_style_form(self) -> FormDefinition:
        """Get the learning style questionnaire form."""
        return self.form_integration.get_learning_style_form()

    def get_goal_setting_form(self) -> FormDefinition:
        """Get the goal setting form."""
        return self.form_integration.get_goal_setting_form()

    async def submit_profile_form(
        self,
        student_id: str,
        form_data: dict[str, Any],
    ) -> FormSubmissionResult:
        """
        Submit a profile creation form.

        Args:
            student_id: Student identifier
            form_data: Form field values

        Returns:
            FormSubmissionResult with created profile
        """
        submission = FormSubmission(
            form_id="profile_creation",
            student_id=student_id,
            data=form_data,
        )

        result = await self.form_integration.submit_profile_form(submission)

        # Cache profile
        if result.success and result.profile:
            self._profiles_cache[student_id] = result.profile

        return result

    async def submit_learning_style_form(
        self,
        student_id: str,
        form_data: dict[str, Any],
    ) -> FormSubmissionResult:
        """
        Submit a learning style questionnaire.

        Args:
            student_id: Student identifier
            form_data: Questionnaire answers

        Returns:
            FormSubmissionResult with determined style
        """
        submission = FormSubmission(
            form_id="learning_style",
            student_id=student_id,
            data=form_data,
        )

        return await self.form_integration.submit_learning_style_form(submission)

    # =====================
    # Progress Operations
    # =====================

    async def get_progress(
        self,
        student_id: str,
    ) -> dict[str, Any]:
        """
        Get progress summary for a student.

        Args:
            student_id: Student identifier

        Returns:
            Progress summary dict
        """
        path = await self.get_student_path(student_id)

        if not path:
            return {
                "has_path": False,
                "message": "No active learning path",
            }

        # Calculate from resources
        total_resources = len(path.resources)
        # Note: completed resources would need to be tracked separately
        # For now, return basic info

        return {
            "has_path": True,
            "path_id": path.path_id,
            "goal": path.goal,
            "total_resources": total_resources,
            "phases_count": len(path.phases),
            "created_at": path.created_at.isoformat(),
        }

    async def mark_resource_complete(
        self,
        student_id: str,
        resource_id: str,
    ) -> bool:
        """
        Mark a resource as completed.

        Args:
            student_id: Student identifier
            resource_id: Resource ID to mark complete

        Returns:
            True if successful
        """
        path = await self.get_student_path(student_id)
        if not path:
            return False

        # TODO: Implement completion tracking
        # This would need to be stored in metadata or a separate tracking system
        logger.info(f"Marked resource '{resource_id}' complete for {student_id}")
        return True

    # =====================
    # Private Helpers
    # =====================

    async def _get_or_create_profile(
        self,
        student_id: str,
    ) -> StudentProfile:
        """Get or create a student profile."""
        # Check cache
        if student_id in self._profiles_cache:
            return self._profiles_cache[student_id]

        loaded = await load_student_profile_from_db(student_id)
        if loaded is not None:
            self._profiles_cache[student_id] = loaded
            return loaded

        # Create default profile
        profile = StudentProfile(
            student_id=student_id,
            name="",
            grade="12",
            exam_target="YKS-TYT",
            learning_goal="",
            learning_style=LearningStyle.MIXED,
            knowledge_level=KnowledgeLevel.INTERMEDIATE,
            interests=[],
            available_time=240,  # 4 hours in minutes
        )

        self._profiles_cache[student_id] = profile
        return profile

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._paths_cache.clear()
        self._profiles_cache.clear()
        logger.info("Facade cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get facade statistics."""
        return {
            "cached_paths": len(self._paths_cache),
            "cached_profiles": len(self._profiles_cache),
            "services_initialized": {
                "path_generation": self._path_generation is not None,
                "resource_discovery": self._resource_discovery is not None,
                "path_adaptation": self._path_adaptation is not None,
                "chat_integration": self._chat_integration is not None,
                "form_integration": self._form_integration is not None,
            },
        }


# Convenience function for getting a facade instance
_facade_instance: LearningPathFacade | None = None


def get_learning_path_facade() -> LearningPathFacade:
    """
    Get the singleton LearningPathFacade instance.

    Returns:
        Shared LearningPathFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = LearningPathFacade()
    return _facade_instance
