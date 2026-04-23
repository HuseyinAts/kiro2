"""
Learning Path Agent - Main Orchestrator
Teknofest 2025 - Eğitim Eylemci Projesi

This is the main agent that orchestrates all learning path components.
Refactored from monolithic learning_path_agent.py into modular architecture.

Main Responsibilities:
- Coordinate all core components (profiler, assessment, resources, path generation)
- Implement main workflow methods
- Manage agent state and caching
- Provide backward-compatible interface
"""

import logging
from datetime import datetime
from typing import Any

from cachetools import TTLCache

from .core import (
    AssessmentCreator,
    PathGenerator,
    PathOptimizer,
    ResourceFinder,
    StudentProfiler,
)
from .integrations import (
    ChatIntegration,
    FormIntegration,
    KhanIntegration,
    OERIntegration,
    YouTubeIntegration,
)
from .models import (
    KnowledgeLevel,
    LearningPath,
    LearningResource,
    LearningStyle,
    StudentProfile,
)
from .strategies import DifficultyAdapter, LearningStyleStrategy, TimePlanner

logger = logging.getLogger(__name__)


class LearningPathAgent:
    """
    Main Learning Path Agent - Orchestrates all components

    This agent coordinates student profiling, assessment creation, resource discovery,
    and personalized learning path generation for YKS/LGS exam preparation.

    Architecture:
        - Core Components: Student profiling, assessment, resource finding, path generation
        - Strategies: Learning style matching, difficulty adaptation, time planning
        - Integrations: YouTube, Khan Academy, OER, Chat, Forms

    Usage:
        agent = LearningPathAgent(
            llm_service=llm_service,
            assessment_system=assessment_system,
            youtube_service=youtube_service
        )

        # Create personalized learning path
        result = await agent.create_learning_path(
            student_id="student123",
            student_data={"name": "Ahmet", "grade": "12", ...}
        )
    """

    def __init__(
        self,
        llm_service,
        assessment_system,
        youtube_service=None,
        khan_service=None,
        oer_service=None,
        chat_service=None,
        form_service=None,
        resource_ranker=None,
        rag_service=None,
        learning_style_detector=None,
    ):
        """
        Initialize Learning Path Agent with all dependencies

        Args:
            llm_service: LLM service for reasoning and analysis
            assessment_system: Question generation and assessment system
            youtube_service: YouTube API service (optional)
            khan_service: Khan Academy API service (optional)
            oer_service: Open Educational Resources service (optional)
            chat_service: Chat interface service (optional)
            form_service: Form interface service (optional)
            resource_ranker: Resource ranking service (optional)
            rag_service: RAG service for semantic search (optional)
            learning_style_detector: Learning style detection service (optional)
        """
        # Validate required dependencies
        if not llm_service:
            raise ValueError("llm_service is required")
        if not assessment_system:
            raise ValueError("assessment_system is required")

        logger.info("Initializing LearningPathAgent v2.0.0")

        # Store core services
        self.llm = llm_service
        self.assessment_system = assessment_system

        # Initialize core components
        self.student_profiler = StudentProfiler(
            llm_service=llm_service,
            assessment_system=assessment_system,
            learning_style_detector=learning_style_detector,
        )

        self.assessment_creator = AssessmentCreator(
            assessment_system=assessment_system, student_profiler=self.student_profiler
        )

        self.resource_finder = ResourceFinder(
            youtube_service=youtube_service,
            khan_service=khan_service,
            oer_service=oer_service,
            resource_ranker=resource_ranker,
            rag_service=rag_service,
        )

        self.path_generator = PathGenerator(llm_service=llm_service)

        self.path_optimizer = PathOptimizer()

        # Initialize strategies
        self.learning_style_strategy = LearningStyleStrategy()
        self.difficulty_adapter = DifficultyAdapter()
        self.time_planner = TimePlanner()

        # Initialize integrations (if services provided)
        self.youtube_integration = (
            YouTubeIntegration(youtube_service) if youtube_service else None
        )
        self.khan_integration = KhanIntegration(khan_service) if khan_service else None
        self.oer_integration = OERIntegration(oer_service) if oer_service else None
        self.chat_integration = ChatIntegration(chat_service) if chat_service else None
        self.form_integration = FormIntegration(form_service) if form_service else None

        # Agent state with TTLCache to prevent memory leak
        # Max 500 paths, 1 hour TTL
        self.paths_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)
        # Max 1000 sessions, 2 hour TTL
        self.session_data: TTLCache = TTLCache(maxsize=1000, ttl=7200)

        logger.info("LearningPathAgent initialized with TTLCache (paths=500/1h, sessions=1000/2h)")

    async def create_learning_path(
        self, student_id: str, student_data: dict[str, Any], goal: str | None = None
    ) -> dict[str, Any]:
        """
        Main workflow: Create personalized learning path for student

        This is the primary entry point that orchestrates all components:
        1. Analyze student profile
        2. Create diagnostic assessment
        3. Search and rank resources
        4. Generate personalized learning path
        5. Optimize path sequence and difficulty

        Args:
            student_id: Unique student identifier
            student_data: Student information (name, grade, exam_target, etc.)
            goal: Optional specific learning goal

        Returns:
            Dict containing:
                - success: bool
                - student_profile: StudentProfile object
                - learning_path: LearningPath object
                - assessment: Assessment data
                - message: Status message
        """
        try:
            logger.info(f"Creating learning path for student {student_id}")
            start_time = datetime.now()

            # Step 1: Analyze student profile
            profile = await self.student_profiler.analyze_student(
                student_id=student_id, initial_data=student_data
            )
            logger.info(
                f"Student profile created: {profile.learning_style.value}, {profile.knowledge_level.value}"
            )

            # Step 2: Create diagnostic assessment
            assessment = await self.assessment_creator.create_diagnostic_assessment(
                student_id=student_id, subjects=student_data.get("subjects", [])
            )
            logger.info(
                f"Diagnostic assessment created: {len(assessment.get('questions', []))} questions"
            )

            # Step 3: Search resources based on profile
            resources = await self._search_personalized_resources(
                profile=profile, goal=goal or student_data.get("learning_goal", "")
            )
            logger.info(f"Found {len(resources)} personalized resources")

            # Step 4: Generate learning path
            learning_goal = goal or student_data.get(
                "learning_goal", f"{profile.exam_target} hazırlık"
            )
            path = await self.path_generator.generate_path(
                profile=profile, resources=resources, goal=learning_goal
            )
            logger.info(f"Learning path generated: {len(path.phases)} phases")

            # Step 5: Optimize path
            optimized_path = self.path_optimizer.optimize_sequence(path)
            optimized_path = self.path_optimizer.balance_difficulty(optimized_path)
            logger.info("Path optimized for sequence and difficulty")

            # Cache the path
            self.paths_cache[student_id] = optimized_path

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Learning path created in {elapsed:.2f}s")

            return {
                "success": True,
                "student_profile": profile.to_dict(),
                "learning_path": optimized_path.to_dict(),
                "assessment": assessment,
                "execution_time": elapsed,
                "message": f"Kişiselleştirilmiş öğrenme yolu oluşturuldu ({len(resources)} kaynak, {len(path.phases)} aşama)",
            }

        except Exception as e:
            logger.error(f"Error creating learning path: {e!s}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Öğrenme yolu oluşturulurken hata oluştu",
            }

    async def _search_personalized_resources(
        self, profile: StudentProfile, goal: str, max_resources: int = 30
    ) -> list[LearningResource]:
        """
        Search resources personalized for student profile

        Combines multiple strategies:
        - Difficulty matching to knowledge level
        - Learning style preference
        - Multi-platform search (YouTube, Khan, OER)
        """
        # Extract subjects from goal or use defaults
        subjects = profile.interests if profile.interests else ["Matematik", "Türkçe"]

        # Search resources with profile preferences
        resources = await self.resource_finder.search_resources(
            topic=goal,
            subjects=subjects,
            difficulty=profile.knowledge_level,
            learning_style=profile.learning_style,
            count=max_resources,
        )

        # Filter by learning style preference
        filtered_resources = self.learning_style_strategy.filter_by_style(
            resources=resources, learning_style=profile.learning_style
        )

        # Rank by learning style match
        ranked_resources = self.learning_style_strategy.rank_by_style_match(
            resources=filtered_resources, learning_style=profile.learning_style
        )

        return ranked_resources[:max_resources]

    async def update_path_progress(
        self,
        student_id: str,
        completed_resource_ids: list[str],
        performance_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Update student's learning path progress

        Args:
            student_id: Student identifier
            completed_resource_ids: List of completed resource IDs
            performance_data: Optional performance metrics (scores, time spent, etc.)

        Returns:
            Dict with updated path and recommendations
        """
        try:
            # Get current path
            if student_id not in self.paths_cache:
                return {"success": False, "error": "No learning path found for student"}

            current_path = self.paths_cache[student_id]

            # Update completion status
            for resource in current_path.resources:
                if resource.resource_id in completed_resource_ids:
                    resource.metadata["completed"] = True

            # Adapt difficulty if performance data provided
            if performance_data:
                profile = self.student_profiler.get_profile(student_id)
                if profile:
                    new_difficulty, reason = self.difficulty_adapter.adapt_difficulty(
                        current_difficulty=profile.knowledge_level,
                        performance_data=performance_data,
                    )

                    if new_difficulty != profile.knowledge_level:
                        logger.info(
                            f"Difficulty adapted: {profile.knowledge_level.value} -> {new_difficulty.value}"
                        )
                        profile.knowledge_level = new_difficulty
                        # Update profile with dict of changes
                        self.student_profiler.update_profile(
                            student_id, {"knowledge_level": new_difficulty}
                        )

            # Calculate progress
            total_resources = len(current_path.resources)
            completed_count = len(completed_resource_ids)
            progress_percent = (
                (completed_count / total_resources * 100) if total_resources > 0 else 0
            )

            return {
                "success": True,
                "progress_percent": progress_percent,
                "completed_resources": completed_count,
                "total_resources": total_resources,
                "message": f"İlerleme güncellendi: %{progress_percent:.1f}",
            }

        except Exception as e:
            logger.error(f"Error updating path progress: {e!s}")
            return {"success": False, "error": str(e)}

    async def get_next_recommendations(
        self, student_id: str, count: int = 5
    ) -> dict[str, Any]:
        """
        Get next recommended resources for student

        Args:
            student_id: Student identifier
            count: Number of recommendations to return

        Returns:
            Dict with recommended resources
        """
        try:
            # Get current path
            if student_id not in self.paths_cache:
                return {"success": False, "error": "No learning path found for student"}

            path = self.paths_cache[student_id]

            # Find next uncompleted resources
            next_resources = [
                r for r in path.resources if not r.metadata.get("completed", False)
            ][:count]

            return {
                "success": True,
                "recommendations": [r.to_dict() for r in next_resources],
                "count": len(next_resources),
            }

        except Exception as e:
            logger.error(f"Error getting recommendations: {e!s}")
            return {"success": False, "error": str(e)}

    async def create_quick_assessment(
        self,
        student_id: str,
        subject: str,
        topic: str | None = None,
        question_count: int = 5,
    ) -> dict[str, Any]:
        """
        Create quick assessment for specific topic

        Delegates to AssessmentCreator with student profile context
        """
        try:
            result = await self.assessment_creator.create_quick_assessment(
                student_id=student_id,
                subject=subject,
                topic=topic,
                question_count=question_count,
            )
            return result

        except Exception as e:
            logger.error(f"Error creating quick assessment: {e!s}")
            return {"success": False, "error": str(e)}

    async def search_videos(
        self,
        query: str,
        max_results: int = 10,
        language: str = "tr",
        difficulty: KnowledgeLevel | None = None,
    ) -> dict[str, Any]:
        """
        Search YouTube videos with optional difficulty filtering

        Args:
            query: Search query
            max_results: Maximum number of results
            language: Language code (default: "tr")
            difficulty: Optional difficulty level filter

        Returns:
            Dict with video results
        """
        try:
            if not self.youtube_integration:
                return {"success": False, "error": "YouTube service not configured"}

            videos = await self.youtube_integration.search_videos(
                query=query, max_results=max_results, language=language
            )

            # Convert to LearningResource format
            resources = [
                LearningResource(
                    resource_id=f"yt_{i}",
                    title=video.get("title", ""),
                    source="youtube",
                    url=video.get("url", ""),
                    resource_type="video",
                    difficulty_level=difficulty or KnowledgeLevel.INTERMEDIATE,
                    estimated_time=self.youtube_integration.parse_duration(
                        video.get("duration", "")
                    ),
                    language=language,
                    description=video.get("description", ""),
                    tags=video.get("subjects", []) + ["visual", "auditory"],
                    rating=None,
                    metadata=video,
                )
                for i, video in enumerate(videos)
            ]

            # Filter by difficulty if specified
            if difficulty:
                resources = [r for r in resources if r.difficulty_level == difficulty]

            return {
                "success": True,
                "videos": [r.to_dict() for r in resources],
                "count": len(resources),
            }

        except Exception as e:
            logger.error(f"Error searching videos: {e!s}")
            return {"success": False, "error": str(e)}

    async def chat_with_student(
        self, session_id: str, message: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Process chat message from student

        Args:
            session_id: Chat session identifier
            message: Student's message
            context: Optional context (student_id, current_topic, etc.)

        Returns:
            Dict with response and updated context
        """
        try:
            if not self.chat_integration:
                # Fallback to direct LLM if no chat service
                response = await self.llm.generate(
                    prompt=f"Öğrenci sorusu: {message}\n\nLütfen yardımcı ve açıklayıcı bir yanıt ver.",
                    max_tokens=500,
                )
                return {
                    "success": True,
                    "response": response.get("text", ""),
                    "session_id": session_id,
                }

            result = await self.chat_integration.process_message(
                session_id=session_id, message=message, context=context
            )

            return result

        except Exception as e:
            logger.error(f"Error in chat: {e!s}")
            return {"success": False, "error": str(e)}

    def get_student_profile(self, student_id: str) -> StudentProfile | None:
        """Get cached student profile"""
        return self.student_profiler.get_profile(student_id)

    def get_learning_path(self, student_id: str) -> LearningPath | None:
        """Get cached learning path"""
        return self.paths_cache.get(student_id)

    async def regenerate_path(
        self, student_id: str, preferences: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Regenerate learning path with new preferences

        Args:
            student_id: Student identifier
            preferences: Optional preference updates (difficulty, learning_style, etc.)

        Returns:
            Dict with new learning path
        """
        try:
            # Get current profile
            profile = self.student_profiler.get_profile(student_id)
            if not profile:
                return {"success": False, "error": "Student profile not found"}

            # Update profile with new preferences
            if preferences:
                updates = {}
                if "difficulty" in preferences:
                    profile.knowledge_level = KnowledgeLevel(preferences["difficulty"])
                    updates["knowledge_level"] = profile.knowledge_level
                if "learning_style" in preferences:
                    profile.learning_style = LearningStyle(
                        preferences["learning_style"]
                    )
                    updates["learning_style"] = profile.learning_style
                if "available_time" in preferences:
                    profile.available_time = preferences["available_time"]
                    updates["available_time"] = profile.available_time

                self.student_profiler.update_profile(student_id, updates)

            # Search new resources
            resources = await self._search_personalized_resources(
                profile=profile, goal=profile.learning_goal
            )

            # Generate new path
            path = await self.path_generator.generate_path(
                profile=profile, resources=resources, goal=profile.learning_goal
            )

            # Optimize
            optimized_path = self.path_optimizer.optimize_sequence(path)
            optimized_path = self.path_optimizer.balance_difficulty(optimized_path)

            # Update cache
            self.paths_cache[student_id] = optimized_path

            return {
                "success": True,
                "learning_path": optimized_path.to_dict(),
                "message": "Öğrenme yolu yeniden oluşturuldu",
            }

        except Exception as e:
            logger.error(f"Error regenerating path: {e!s}")
            return {"success": False, "error": str(e)}

    async def analyze_learning_gaps(
        self, student_id: str, assessment_results: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze learning gaps from assessment results

        Args:
            student_id: Student identifier
            assessment_results: Assessment results with scores by topic

        Returns:
            Dict with identified gaps and recommendations
        """
        try:
            profile = self.student_profiler.get_profile(student_id)
            if not profile:
                return {"success": False, "error": "Student profile not found"}

            # Analyze weak areas
            weak_topics = [
                topic
                for topic, score in assessment_results.get("topic_scores", {}).items()
                if score < 60
            ]

            # Search targeted resources for weak topics
            gap_resources = []
            for topic in weak_topics:
                resources = await self.resource_finder.search_resources(
                    topic=topic,
                    subjects=[topic],
                    difficulty=KnowledgeLevel.BEGINNER,  # Start from basics for gaps
                    count=5,
                )
                gap_resources.extend(resources)

            return {
                "success": True,
                "weak_topics": weak_topics,
                "recommended_resources": [r.to_dict() for r in gap_resources],
                "message": f"{len(weak_topics)} öğrenme boşluğu tespit edildi",
            }

        except Exception as e:
            logger.error(f"Error analyzing learning gaps: {e!s}")
            return {"success": False, "error": str(e)}

    def get_agent_stats(self) -> dict[str, Any]:
        """Get agent statistics and health metrics"""
        return {
            "version": "2.0.0",
            "cached_profiles": len(self.student_profiler.profiles_cache),
            "cached_paths": len(self.paths_cache),
            "cached_resources": len(self.resource_finder.resource_cache),
            "integrations": {
                "youtube": self.youtube_integration is not None,
                "khan": self.khan_integration is not None,
                "oer": self.oer_integration is not None,
                "chat": self.chat_integration is not None,
                "form": self.form_integration is not None,
            },
            "components": {
                "student_profiler": "active",
                "assessment_creator": "active",
                "resource_finder": "active",
                "path_generator": "active",
                "path_optimizer": "active",
            },
        }

    def clear_cache(self, student_id: str | None = None):
        """Clear cached data for student or all"""
        if student_id:
            self.student_profiler.profiles_cache.pop(student_id, None)
            self.paths_cache.pop(student_id, None)
            logger.info(f"Cleared cache for student {student_id}")
        else:
            self.student_profiler.profiles_cache.clear()
            self.paths_cache.clear()
            self.resource_finder.resource_cache.clear()
            logger.info("Cleared all caches")
