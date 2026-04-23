"""
Student Profile Creation and Analysis
Teknofest 2025 - Eğitim Eylemci Projesi

Extracted from LearningPathAgent (lines 112-727, 1460-1596)

This module handles:
- Student analysis and profile creation
- Knowledge level assessment
- Learning style detection
- Behavioral analysis
- Performance tracking

Responsibilities:
- Create student profiles using LLM analysis
- Assess knowledge levels from test results
- Detect learning styles from behavioral indicators
- Track learning behaviors
- Analyze performance trends
"""

import json
import logging
from datetime import datetime
from typing import Any

from cachetools import TTLCache

from ..models import KnowledgeLevel, LearningStyle, StudentProfile

logger = logging.getLogger(__name__)


class StudentProfiler:
    """
    Student Profiler - Creates and manages student profiles

    This class is responsible for analyzing student data and creating
    personalized profiles that guide learning path generation.

    Uses dependency injection for external services to improve
    testability and maintainability.
    """

    def __init__(
        self, llm_service, assessment_system=None, learning_style_detector=None
    ):
        """
        Initialize StudentProfiler with injected dependencies

        Args:
            llm_service: LLM service for AI-powered analysis
            assessment_system: Assessment system for tests (optional)
            learning_style_detector: Learning style detection service (optional)
        """
        if not llm_service:
            raise ValueError("llm_service is required")

        self.llm = llm_service
        self.assessment = assessment_system
        self.style_detector = learning_style_detector

        # In-memory cache for profiles with TTL and max size
        # Max 1000 profiles, 30 minute TTL to prevent memory leak
        self.profiles_cache: TTLCache = TTLCache(maxsize=1000, ttl=1800)

        # Behavior history cache - stores list of behaviors per student
        # Max 5000 entries (500 students * ~10 behaviors average), 2 hour TTL
        self.behavior_cache: TTLCache = TTLCache(maxsize=5000, ttl=7200)

        # Performance score history for trend analysis
        # Max 1000 students, each with list of scores, 24 hour TTL
        self.score_history_cache: TTLCache = TTLCache(maxsize=1000, ttl=86400)

        logger.info(
            "StudentProfiler initialized with TTLCache (profiles=1000, behaviors=5000)"
        )

    async def analyze_student(
        self, student_id: str, initial_data: dict[str, Any]
    ) -> StudentProfile:
        """
        Analyze student data and create profile

        This is the main method for profile creation. It uses LLM
        to analyze student data and extract key information.

        Args:
            student_id: Unique student identifier
            initial_data: Initial data (survey, test results, preferences, etc.)
                Expected keys:
                - name: Student name (optional, default: "Student")
                - grade: Grade level (optional, default: "")
                - exam_target: Target exam (optional, default: "")
                - goal: Learning goal (required)
                - available_time: Daily study time in minutes (optional, default: 60)

        Returns:
            StudentProfile: Created student profile

        Raises:
            ValueError: If student_id or initial_data is invalid
            Exception: If LLM analysis fails

        Example:
            >>> profiler = StudentProfiler(llm_service)
            >>> data = {
            ...     "name": "Ali Veli",
            ...     "grade": "10",
            ...     "exam_target": "YKS",
            ...     "goal": "Matematik konusunda gelişmek",
            ...     "available_time": 90
            ... }
            >>> profile = await profiler.analyze_student("student123", data)
        """
        # Input validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")

        if not initial_data or not isinstance(initial_data, dict):
            raise ValueError("initial_data must be a non-empty dictionary")

        if "goal" not in initial_data:
            raise ValueError("initial_data must contain 'goal'")

        try:
            # LLM analysis
            logger.info(f"Analyzing student: {student_id}")
            analysis = await self._llm_analyze(initial_data)

            # Create profile
            profile = self._create_profile(student_id, initial_data, analysis)

            # Cache profile
            self.profiles_cache[student_id] = profile

            logger.info(
                f"Student profile created: {student_id} "
                f"(style={profile.learning_style.value}, "
                f"level={profile.knowledge_level.value})"
            )

            return profile

        except Exception as e:
            logger.error(f"Student analysis error for {student_id}: {e!s}")
            raise

    async def assess_knowledge_level(
        self,
        student_id: str,
        subject: str,
        test_results: dict[str, Any] | None = None,
    ) -> KnowledgeLevel:
        """
        Assess student's knowledge level for a subject

        Can assess from test results or from cached profile.

        Args:
            student_id: Student identifier
            subject: Subject/topic to assess
            test_results: Test results (optional)
                Expected keys:
                - score: Score achieved
                - total: Total possible score

        Returns:
            KnowledgeLevel: Assessed knowledge level

        Raises:
            ValueError: If inputs are invalid
        """
        # Validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")

        if not subject or not isinstance(subject, str):
            raise ValueError("subject must be a non-empty string")

        try:
            if test_results:
                # Calculate from test results
                logger.info(f"Assessing knowledge from test: {student_id} - {subject}")
                return self._calculate_level_from_test(test_results)
            # Get from cached profile
            profile = self.get_profile(student_id)
            if profile:
                logger.info(
                    f"Knowledge level from profile: {student_id} - {profile.knowledge_level.value}"
                )
                return profile.knowledge_level
            logger.warning(
                f"No profile found for {student_id}, defaulting to BEGINNER"
            )
            return KnowledgeLevel.BEGINNER

        except Exception as e:
            logger.error(f"Knowledge assessment error: {e!s}")
            raise

    async def analyze_behavioral_learning_style(
        self, student_id: str, behaviors: list[dict[str, Any]]
    ) -> LearningStyle:
        """
        Analyze learning style from behavioral indicators

        Uses learning style detector service if available.

        Args:
            student_id: Student identifier
            behaviors: List of behavioral indicators
                Each behavior dict should contain:
                - action: Action type (e.g., "watched_video", "read_article")
                - duration: Duration in seconds
                - engagement: Engagement score (0-100)

        Returns:
            LearningStyle: Detected learning style

        Raises:
            Exception: If analysis fails
        """
        try:
            if not self.style_detector:
                logger.warning("Learning style detector not available, using default")
                return LearningStyle.MIXED

            logger.info(
                f"Analyzing behavioral learning style: {student_id} ({len(behaviors)} behaviors)"
            )

            # Use learning style detector
            detected_style = await self.style_detector.analyze_behaviors(
                student_id=student_id, behaviors=behaviors
            )

            # Update cached profile if exists
            profile = self.get_profile(student_id)
            if profile:
                profile.learning_style = LearningStyle(detected_style)
                self.profiles_cache[student_id] = profile
                logger.info(
                    f"Updated profile learning style: {student_id} -> {detected_style}"
                )

            return LearningStyle(detected_style)

        except Exception as e:
            logger.error(f"Behavioral analysis error: {e!s}")
            raise

    def record_learning_behavior(
        self,
        student_id: str,
        action: str,
        context: dict[str, Any],
        duration: int | None = None,
    ) -> bool:
        """
        Record a learning behavior for future analysis

        Args:
            student_id: Student identifier
            action: Action type (e.g., "watched_video", "completed_quiz")
            context: Context data (resource_id, subject, difficulty, etc.)
            duration: Duration in seconds (optional)

        Returns:
            bool: Success status

        Example:
            >>> profiler.record_learning_behavior(
            ...     student_id="student123",
            ...     action="watched_video",
            ...     context={"video_id": "vid123", "subject": "math"},
            ...     duration=600
            ... )
        """
        try:
            behavior = {
                "student_id": student_id,
                "action": action,
                "context": context,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
            }

            # Store behavior in cache
            cache_key = f"behaviors_{student_id}"
            if cache_key in self.behavior_cache:
                behaviors = self.behavior_cache[cache_key]
                # Keep only last 100 behaviors per student
                if len(behaviors) >= 100:
                    behaviors = behaviors[-99:]
                behaviors.append(behavior)
                self.behavior_cache[cache_key] = behaviors
            else:
                self.behavior_cache[cache_key] = [behavior]

            logger.info(
                f"Behavior recorded: {student_id} - {action} (duration={duration}s)"
            )

            return True

        except Exception as e:
            logger.error(f"Record behavior error: {e!s}")
            return False

    def get_behavior_history(
        self, student_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get student's behavior history

        Args:
            student_id: Student identifier
            limit: Maximum number of behaviors to return

        Returns:
            List of behavior records, most recent first
        """
        cache_key = f"behaviors_{student_id}"
        behaviors = self.behavior_cache.get(cache_key, [])
        return behaviors[-limit:][::-1]  # Return most recent first

    def analyze_performance_trend(self, student_id: str, current_score: float) -> str:
        """
        Analyze performance trend from score using historical tracking

        Args:
            student_id: Student identifier
            current_score: Current assessment score (0-100)

        Returns:
            str: Trend description with additional detail:
                - "improving_rapidly": Score increasing >10 points average
                - "improving": Score increasing 5-10 points average
                - "stable_excellent": Score stable at 80+
                - "stable_good": Score stable at 60-79
                - "stable_average": Score stable at 40-59
                - "declining": Score decreasing
                - "needs_improvement": Score below 40
        """
        # Store current score in history
        cache_key = f"scores_{student_id}"
        if cache_key in self.score_history_cache:
            scores = self.score_history_cache[cache_key]
            # Keep last 20 scores for trend analysis
            if len(scores) >= 20:
                scores = scores[-19:]
            scores.append({
                "score": current_score,
                "timestamp": datetime.now().isoformat(),
            })
            self.score_history_cache[cache_key] = scores
        else:
            self.score_history_cache[cache_key] = [{
                "score": current_score,
                "timestamp": datetime.now().isoformat(),
            }]

        # Get score history for analysis
        scores = self.score_history_cache.get(cache_key, [])

        # Need at least 3 scores for trend analysis
        if len(scores) < 3:
            # Fall back to simple thresholds
            if current_score >= 80:
                return "stable_excellent"
            if current_score >= 60:
                return "stable_good"
            if current_score >= 40:
                return "stable_average"
            return "needs_improvement"

        # Calculate trend from recent scores
        recent_scores = [s["score"] for s in scores[-5:]]
        older_scores = [s["score"] for s in scores[:-5]] if len(scores) > 5 else []

        avg_recent = sum(recent_scores) / len(recent_scores)
        avg_older = sum(older_scores) / len(older_scores) if older_scores else avg_recent

        improvement = avg_recent - avg_older

        # Determine trend
        if improvement > 10:
            return "improving_rapidly"
        if improvement > 5:
            return "improving"
        if improvement < -5:
            return "declining"
        if current_score >= 80:
            return "stable_excellent"
        if current_score >= 60:
            return "stable_good"
        if current_score >= 40:
            return "stable_average"
        return "needs_improvement"

    def get_score_history(
        self, student_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get student's score history

        Args:
            student_id: Student identifier
            limit: Maximum number of scores to return

        Returns:
            List of score records, most recent first
        """
        cache_key = f"scores_{student_id}"
        scores = self.score_history_cache.get(cache_key, [])
        return scores[-limit:][::-1]  # Return most recent first

    def get_profile(self, student_id: str) -> StudentProfile | None:
        """
        Get student profile from cache

        Args:
            student_id: Student identifier

        Returns:
            StudentProfile if found, None otherwise
        """
        return self.profiles_cache.get(student_id)

    def update_profile(
        self, student_id: str, updates: dict[str, Any]
    ) -> StudentProfile | None:
        """
        Update student profile

        Args:
            student_id: Student identifier
            updates: Dictionary of fields to update

        Returns:
            Updated StudentProfile if found, None otherwise

        Example:
            >>> profiler.update_profile(
            ...     "student123",
            ...     {"knowledge_level": KnowledgeLevel.ADVANCED}
            ... )
        """
        profile = self.get_profile(student_id)
        if not profile:
            logger.warning(f"Profile not found for update: {student_id}")
            return None

        # Update allowed fields
        allowed_updates = {
            "learning_style",
            "knowledge_level",
            "interests",
            "available_time",
            "metadata",
        }

        for key, value in updates.items():
            if key in allowed_updates and hasattr(profile, key):
                setattr(profile, key, value)
                logger.info(f"Updated profile field: {student_id}.{key}")

        # Update cache
        self.profiles_cache[student_id] = profile

        return profile

    # Private helper methods

    async def _llm_analyze(self, initial_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze student data using LLM

        Args:
            initial_data: Student data to analyze

        Returns:
            Dictionary with analysis results
        """
        prompt = f"""
Öğrenci verisini analiz et ve profil oluştur:

Veri: {json.dumps(initial_data, ensure_ascii=False)}

Şunları belirle:
1. Öğrenme stili (visual/auditory/reading/kinesthetic/mixed)
2. Bilgi seviyesi (beginner/elementary/intermediate/advanced/expert)
3. İlgi alanları (liste olarak)
4. Öğrenme hedefi özeti

JSON formatında yanıtla:
{{
    "learning_style": "...",
    "knowledge_level": "...",
    "interests": [...],
    "goal_summary": "..."
}}
"""

        try:
            result = await self.llm.generate(prompt=prompt, temperature=0.3)

            if result.get("success"):
                try:
                    analysis = json.loads(result["text"])
                    logger.debug(f"LLM analysis successful: {analysis}")
                    return analysis
                except json.JSONDecodeError:
                    logger.warning("LLM response not valid JSON, using defaults")
                    return self._default_analysis(initial_data)
            else:
                logger.warning(f"LLM generation failed: {result.get('error')}")
                return self._default_analysis(initial_data)

        except Exception as e:
            logger.error(f"LLM analysis error: {e!s}")
            return self._default_analysis(initial_data)

    def _default_analysis(self, initial_data: dict[str, Any]) -> dict[str, Any]:
        """
        Fallback analysis when LLM fails

        Args:
            initial_data: Original student data

        Returns:
            Default analysis
        """
        return {
            "learning_style": "mixed",
            "knowledge_level": "beginner",
            "interests": [],
            "goal_summary": initial_data.get("goal", "Genel öğrenme"),
        }

    def _create_profile(
        self, student_id: str, initial_data: dict[str, Any], analysis: dict[str, Any]
    ) -> StudentProfile:
        """
        Create StudentProfile from analysis

        Args:
            student_id: Student identifier
            initial_data: Original data
            analysis: LLM analysis results

        Returns:
            StudentProfile instance
        """
        return StudentProfile(
            student_id=student_id,
            name=initial_data.get("name", "Öğrenci"),
            grade=initial_data.get("grade", ""),
            exam_target=initial_data.get("exam_target", ""),
            learning_goal=initial_data.get("goal", ""),
            learning_style=LearningStyle(analysis["learning_style"]),
            knowledge_level=KnowledgeLevel(analysis["knowledge_level"]),
            interests=analysis.get("interests", []),
            available_time=initial_data.get("available_time", 60),
            metadata={
                "analysis": analysis,
                "initial_data": initial_data,
                "created_at": datetime.now().isoformat(),
            },
        )

    def _calculate_level_from_test(
        self, test_results: dict[str, Any]
    ) -> KnowledgeLevel:
        """
        Calculate knowledge level from test results

        Args:
            test_results: Test results with 'score' and 'total'

        Returns:
            KnowledgeLevel based on percentage
        """
        score = test_results.get("score", 0)
        total = test_results.get("total", 100)

        if total == 0:
            return KnowledgeLevel.BEGINNER

        percentage = (score / total) * 100

        # Knowledge level thresholds
        if percentage < 30:
            return KnowledgeLevel.BEGINNER
        if percentage < 50:
            return KnowledgeLevel.ELEMENTARY
        if percentage < 70:
            return KnowledgeLevel.INTERMEDIATE
        if percentage < 90:
            return KnowledgeLevel.ADVANCED
        return KnowledgeLevel.EXPERT
