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
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models import StudentProfile, LearningStyle, KnowledgeLevel

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

        # In-memory cache for profiles
        # TODO: Consider using Redis for distributed caching
        self.profiles_cache: Dict[str, StudentProfile] = {}

        logger.info("StudentProfiler initialized")

    async def analyze_student(
        self, student_id: str, initial_data: Dict[str, Any]
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
            logger.error(f"Student analysis error for {student_id}: {str(e)}")
            raise

    async def assess_knowledge_level(
        self,
        student_id: str,
        subject: str,
        test_results: Optional[Dict[str, Any]] = None,
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
            else:
                # Get from cached profile
                profile = self.get_profile(student_id)
                if profile:
                    logger.info(
                        f"Knowledge level from profile: {student_id} - {profile.knowledge_level.value}"
                    )
                    return profile.knowledge_level
                else:
                    logger.warning(
                        f"No profile found for {student_id}, defaulting to BEGINNER"
                    )
                    return KnowledgeLevel.BEGINNER

        except Exception as e:
            logger.error(f"Knowledge assessment error: {str(e)}")
            raise

    async def analyze_behavioral_learning_style(
        self, student_id: str, behaviors: List[Dict[str, Any]]
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
            logger.error(f"Behavioral analysis error: {str(e)}")
            raise

    def record_learning_behavior(
        self,
        student_id: str,
        action: str,
        context: Dict[str, Any],
        duration: Optional[int] = None,
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

            # TODO: Store in database or send to analytics service
            # For now, just log
            logger.info(
                f"Behavior recorded: {student_id} - {action} " f"(duration={duration}s)"
            )

            return True

        except Exception as e:
            logger.error(f"Record behavior error: {str(e)}")
            return False

    def analyze_performance_trend(self, student_id: str, current_score: float) -> str:
        """
        Analyze performance trend from score

        Args:
            student_id: Student identifier
            current_score: Current assessment score (0-100)

        Returns:
            str: Trend description ("excellent", "good", "average", "needs_improvement")

        Note:
            This is a simple implementation. In production, this should
            track historical scores and calculate actual trends.
        """
        # TODO: Implement historical tracking
        # For now, simple thresholds
        if current_score >= 80:
            return "excellent"
        elif current_score >= 60:
            return "good"
        elif current_score >= 40:
            return "average"
        else:
            return "needs_improvement"

    def get_profile(self, student_id: str) -> Optional[StudentProfile]:
        """
        Get student profile from cache

        Args:
            student_id: Student identifier

        Returns:
            StudentProfile if found, None otherwise
        """
        return self.profiles_cache.get(student_id)

    def update_profile(
        self, student_id: str, updates: Dict[str, Any]
    ) -> Optional[StudentProfile]:
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

    async def _llm_analyze(self, initial_data: Dict[str, Any]) -> Dict[str, Any]:
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
            logger.error(f"LLM analysis error: {str(e)}")
            return self._default_analysis(initial_data)

    def _default_analysis(self, initial_data: Dict[str, Any]) -> Dict[str, Any]:
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
        self, student_id: str, initial_data: Dict[str, Any], analysis: Dict[str, Any]
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
        self, test_results: Dict[str, Any]
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
        elif percentage < 50:
            return KnowledgeLevel.ELEMENTARY
        elif percentage < 70:
            return KnowledgeLevel.INTERMEDIATE
        elif percentage < 90:
            return KnowledgeLevel.ADVANCED
        else:
            return KnowledgeLevel.EXPERT
