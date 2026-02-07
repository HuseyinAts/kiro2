"""
Assessment Creation Module
Teknofest 2025 - Eğitim Eylemci Projesi

Extracted from LearningPathAgent (lines 261-501, 1334-1459)

This module handles:
- Quick assessment creation
- Self-assessment creation
- Interactive questionnaires
- Guided self-assessments
- Learning style questionnaires
- Response analysis

Responsibilities:
- Generate adaptive assessments based on student profile
- Create various types of assessments
- Analyze assessment responses
- Determine difficulty levels dynamically
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models import KnowledgeLevel

logger = logging.getLogger(__name__)


class AssessmentCreator:
    """
    Assessment Creator - Creates various types of assessments

    This class is responsible for generating different types of
    assessments tailored to student profiles and learning goals.

    Uses dependency injection for external services.
    """

    def __init__(self, assessment_system, student_profiler=None):
        """
        Initialize AssessmentCreator with injected dependencies

        Args:
            assessment_system: Assessment system for question generation
            student_profiler: Student profiler for profile access (optional)
        """
        if not assessment_system:
            raise ValueError("assessment_system is required")

        self.assessment = assessment_system
        self.profiler = student_profiler

        logger.info("AssessmentCreator initialized")

    async def create_diagnostic_assessment(
        self, student_id: str, subjects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create comprehensive diagnostic assessment

        Args:
            student_id: Student identifier
            subjects: List of subjects to assess (optional)

        Returns:
            Diagnostic assessment data with questions across subjects
        """
        # Get student profile if available
        profile = None
        if self.profiler:
            profile = self.profiler.get_profile(student_id)

        # Default subjects if not provided
        if not subjects:
            subjects = ["Matematik", "Türkçe"]

        # Create assessments for each subject
        all_questions = []
        for subject in subjects:
            result = await self.create_quick_assessment(
                student_id=student_id, subject=subject, question_count=5
            )
            if result.get("success"):
                all_questions.extend(result.get("questions", []))

        return {
            "success": True,
            "assessment_id": f"diag_{student_id}_{len(all_questions)}",
            "type": "diagnostic",
            "subjects": subjects,
            "questions": all_questions,
            "metadata": {
                "student_id": student_id,
                "total_questions": len(all_questions),
            },
        }

    async def create_quick_assessment(
        self,
        student_id: str,
        subject: str,
        topic: Optional[str] = None,
        question_count: int = 5,
    ) -> Dict[str, Any]:
        """
        Create quick assessment with dynamic question selection

        Adapts difficulty based on student profile if available.

        Args:
            student_id: Student identifier
            subject: Subject/course (e.g., "Matematik", "Türkçe")
            topic: Specific topic (optional)
            question_count: Number of questions (5-10)

        Returns:
            Assessment data dictionary with questions and metadata

        Raises:
            ValueError: If inputs are invalid
            Exception: If assessment generation fails

        Example:
            >>> creator = AssessmentCreator(assessment_system, profiler)
            >>> assessment = await creator.create_quick_assessment(
            ...     "student123",
            ...     "Matematik",
            ...     "Türev",
            ...     question_count=5
            ... )
        """
        # Validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")
        if not subject or not isinstance(subject, str):
            raise ValueError("subject must be a non-empty string")
        if question_count < 1 or question_count > 20:
            raise ValueError("question_count must be between 1 and 20")

        try:
            # Get student profile and determine difficulty
            difficulty = None
            profile = None

            if self.profiler:
                profile = self.profiler.get_profile(student_id)
                if profile:
                    difficulty = self._map_knowledge_to_difficulty(
                        profile.knowledge_level
                    )

            # Generate questions
            logger.info(
                f"Creating quick assessment: {student_id} - {subject} "
                f"(difficulty={difficulty.value if hasattr(difficulty, 'value') else difficulty or 'default'})"
            )

            questions = await self.assessment.generate_quick_test(
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                question_count=question_count,
            )

            # Build assessment data
            assessment_data = {
                "assessment_id": f"quick_{student_id}_{int(datetime.now().timestamp())}",
                "student_id": student_id,
                "assessment_type": "quick_test",
                "subject": subject,
                "topic": topic,
                "difficulty_level": difficulty.value if difficulty else "medium",
                "questions": [self._format_question(q) for q in questions],
                "total_questions": len(questions),
                "estimated_time_minutes": sum(
                    getattr(q, "time_limit_seconds", 120) for q in questions
                )
                // 60,
                "created_at": datetime.now().isoformat(),
                "adaptive_features": {
                    "difficulty_adjusted": difficulty is not None,
                    "profile_based": profile is not None,
                    "subject_context": True,
                },
            }

            logger.info(
                f"Quick assessment created: {len(questions)} questions "
                f"(difficulty: {difficulty.value if difficulty else 'medium'})"
            )

            return assessment_data

        except Exception as e:
            logger.error(f"Create quick assessment error: {str(e)}")
            raise

    async def create_self_assessment(
        self, student_id: str, subjects: List[str]
    ) -> Dict[str, Any]:
        """
        Create self-assessment for multiple subjects

        Self-assessment allows students to evaluate their own
        understanding and identify knowledge gaps.

        Args:
            student_id: Student identifier
            subjects: List of subjects to assess

        Returns:
            Self-assessment data dictionary

        Raises:
            ValueError: If inputs are invalid
        """
        # Validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")
        if not subjects or not isinstance(subjects, list):
            raise ValueError("subjects must be a non-empty list")

        try:
            logger.info(f"Creating self-assessment: {student_id} - {subjects}")

            # Generate self-assessment questions
            questions = await self.assessment.create_self_assessment(
                student_id=student_id, subjects=subjects
            )

            assessment_data = {
                "assessment_id": f"self_{student_id}_{int(datetime.now().timestamp())}",
                "student_id": student_id,
                "assessment_type": "self_assessment",
                "subjects": subjects,
                "questions": [self._format_question(q) for q in questions],
                "total_questions": len(questions),
                "estimated_time_minutes": len(questions) * 2,  # 2 minutes per question
                "created_at": datetime.now().isoformat(),
            }

            logger.info(f"Self-assessment created: {len(questions)} questions")
            return assessment_data

        except Exception as e:
            logger.error(f"Create self-assessment error: {str(e)}")
            raise

    async def create_interactive_questionnaire(
        self, student_id: str, goal: str, subjects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create interactive questionnaire with dynamic questions

        Interactive questionnaires adapt based on previous responses.

        Args:
            student_id: Student identifier
            goal: Learning goal
            subjects: Related subjects (optional)

        Returns:
            Interactive questionnaire data

        Example:
            >>> questionnaire = await creator.create_interactive_questionnaire(
            ...     "student123",
            ...     "YKS Matematik hazırlığı"
            ... )
        """
        # Validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")
        if not goal or not isinstance(goal, str):
            raise ValueError("goal must be a non-empty string")

        try:
            # Get current knowledge if profiler available
            current_knowledge = None
            if self.profiler:
                profile = self.profiler.get_profile(student_id)
                if profile:
                    current_knowledge = {
                        "learning_style": profile.learning_style.value,
                        "knowledge_level": profile.knowledge_level.value,
                        "interests": profile.interests,
                        "grade": profile.grade,
                    }

            logger.info(f"Creating interactive questionnaire: {student_id} - {goal}")

            # Generate questionnaire
            questions = await self.assessment.generate_interactive_questionnaire(
                student_id=student_id,
                goal=goal,
                subjects=subjects or ["Genel"],
                current_knowledge=current_knowledge,
            )

            assessment_data = {
                "assessment_id": f"interactive_{student_id}_{int(datetime.now().timestamp())}",
                "student_id": student_id,
                "assessment_type": "interactive_questionnaire",
                "goal": goal,
                "subjects": subjects or ["Genel"],
                "questions": [self._format_question(q) for q in questions],
                "total_questions": len(questions),
                "estimated_time_minutes": sum(
                    getattr(q, "time_limit_seconds", 120) for q in questions
                )
                // 60,
                "created_at": datetime.now().isoformat(),
                "adaptive_features": {
                    "profile_based": current_knowledge is not None,
                    "dynamic_selection": True,
                    "context_aware": current_knowledge is not None,
                    "goal_oriented": True,
                },
            }

            logger.info(
                f"Interactive questionnaire created: {len(questions)} questions"
            )
            return assessment_data

        except Exception as e:
            logger.error(f"Create interactive questionnaire error: {str(e)}")
            raise

    async def create_guided_self_assessment(
        self, student_id: str, subjects: List[str], learning_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Create guided self-assessment flow

        Guided self-assessment provides step-by-step evaluation
        with feedback and recommendations.

        Args:
            student_id: Student identifier
            subjects: Subjects to assess
            learning_goals: Learning goals

        Returns:
            Guided self-assessment flow data
        """
        # Validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")
        if not subjects or not isinstance(subjects, list):
            raise ValueError("subjects must be a non-empty list")
        if not learning_goals or not isinstance(learning_goals, list):
            raise ValueError("learning_goals must be a non-empty list")

        try:
            logger.info(
                f"Creating guided self-assessment: {student_id} - "
                f"{len(subjects)} subjects, {len(learning_goals)} goals"
            )

            flow_data = await self.assessment.create_guided_self_assessment_flow(
                student_id=student_id, subjects=subjects, learning_goals=learning_goals
            )

            logger.info(
                f"Guided self-assessment created: {flow_data.get('total_steps', 0)} steps"
            )
            return flow_data

        except Exception as e:
            logger.error(f"Create guided self-assessment error: {str(e)}")
            raise

    async def create_learning_style_questionnaire(
        self, student_id: str
    ) -> Dict[str, Any]:
        """
        Create questionnaire to detect learning style

        Uses VARK model questions to identify learning preferences.

        Args:
            student_id: Student identifier

        Returns:
            Learning style questionnaire data
        """
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")

        try:
            logger.info(f"Creating learning style questionnaire: {student_id}")

            # VARK-based questions
            questions = [
                {
                    "question_id": "style_q1",
                    "question_text": "Yeni bir konuyu öğrenirken hangi yöntem size daha uygun?",
                    "options": [
                        "Videolar ve görseller izlemek",
                        "Sesli anlatımları dinlemek",
                        "Metin ve makaleler okumak",
                        "Pratik yaparak öğrenmek",
                    ],
                    "style_mapping": ["visual", "auditory", "reading", "kinesthetic"],
                },
                {
                    "question_id": "style_q2",
                    "question_text": "Bir problemi çözerken nasıl yaklaşırsınız?",
                    "options": [
                        "Şemalar ve diyagramlar çizerim",
                        "Kendime sesli açıklarım",
                        "Adım adım yazılı notlar alırım",
                        "Deneme yanılma ile pratik yaparım",
                    ],
                    "style_mapping": ["visual", "auditory", "reading", "kinesthetic"],
                },
                {
                    "question_id": "style_q3",
                    "question_text": "Bilgiyi en iyi nasıl hatırlarsınız?",
                    "options": [
                        "Görsel imgeler olarak",
                        "Sesler ve melodiler olarak",
                        "Kelimeler ve metinler olarak",
                        "Fiziksel hareketlerle",
                    ],
                    "style_mapping": ["visual", "auditory", "reading", "kinesthetic"],
                },
            ]

            assessment_data = {
                "assessment_id": f"style_{student_id}_{int(datetime.now().timestamp())}",
                "student_id": student_id,
                "assessment_type": "learning_style_questionnaire",
                "questions": questions,
                "total_questions": len(questions),
                "estimated_time_minutes": 5,
                "created_at": datetime.now().isoformat(),
            }

            logger.info("Learning style questionnaire created")
            return assessment_data

        except Exception as e:
            logger.error(f"Create learning style questionnaire error: {str(e)}")
            raise

    def analyze_learning_style_responses(
        self, student_id: str, responses: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Analyze learning style questionnaire responses

        Args:
            student_id: Student identifier
            responses: Question ID -> selected option index mapping

        Returns:
            Analysis results with detected learning style

        Example:
            >>> responses = {"style_q1": 0, "style_q2": 0, "style_q3": 0}
            >>> result = creator.analyze_learning_style_responses("student123", responses)
            >>> print(result["detected_style"])  # "visual"
        """
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")
        if not responses or not isinstance(responses, dict):
            raise ValueError("responses must be a non-empty dictionary")

        try:
            # Count style preferences
            style_counts = {"visual": 0, "auditory": 0, "reading": 0, "kinesthetic": 0}

            style_mappings = {
                "style_q1": ["visual", "auditory", "reading", "kinesthetic"],
                "style_q2": ["visual", "auditory", "reading", "kinesthetic"],
                "style_q3": ["visual", "auditory", "reading", "kinesthetic"],
            }

            for question_id, option_index in responses.items():
                if question_id in style_mappings:
                    mapping = style_mappings[question_id]
                    if 0 <= option_index < len(mapping):
                        style = mapping[option_index]
                        style_counts[style] += 1

            # Determine dominant style
            max_count = max(style_counts.values())
            dominant_styles = [
                style for style, count in style_counts.items() if count == max_count
            ]

            # If multiple styles have same count, it's mixed
            detected_style = "mixed" if len(dominant_styles) > 1 else dominant_styles[0]

            analysis = {
                "student_id": student_id,
                "detected_style": detected_style,
                "style_counts": style_counts,
                "confidence": max_count / len(responses) if responses else 0,
                "is_mixed": len(dominant_styles) > 1,
                "analyzed_at": datetime.now().isoformat(),
            }

            logger.info(
                f"Learning style analyzed: {student_id} -> {detected_style} "
                f"(confidence: {analysis['confidence']:.2f})"
            )

            return analysis

        except Exception as e:
            logger.error(f"Analyze learning style error: {str(e)}")
            raise

    # Private helper methods

    def _map_knowledge_to_difficulty(self, knowledge_level: KnowledgeLevel):
        """Map knowledge level to assessment difficulty"""
        mapping = {
            KnowledgeLevel.BEGINNER: "EASY",
            KnowledgeLevel.ELEMENTARY: "EASY",
            KnowledgeLevel.INTERMEDIATE: "MEDIUM",
            KnowledgeLevel.ADVANCED: "HARD",
            KnowledgeLevel.EXPERT: "VERY_HARD",
        }

        difficulty_str = mapping.get(knowledge_level, "MEDIUM")

        # Return difficulty enum if assessment system has DifficultyLevel
        if hasattr(self.assessment, "DifficultyLevel"):
            return getattr(self.assessment.DifficultyLevel, difficulty_str)

        # Otherwise return string
        return difficulty_str

    def _format_question(self, question) -> Dict[str, Any]:
        """Format question object to dictionary"""
        return {
            "question_id": getattr(question, "question_id", ""),
            "question_text": getattr(question, "question_text", ""),
            "question_type": getattr(question, "question_type", "").value
            if hasattr(getattr(question, "question_type", ""), "value")
            else str(getattr(question, "question_type", "")),
            "subject": getattr(question, "subject", ""),
            "topic": getattr(question, "topic", ""),
            "difficulty": getattr(question, "difficulty", "").value
            if hasattr(getattr(question, "difficulty", ""), "value")
            else str(getattr(question, "difficulty", "")),
            "options": getattr(question, "options", []),
            "time_limit_seconds": getattr(question, "time_limit_seconds", 120),
            "points": getattr(question, "points", 1),
            "explanation": getattr(question, "explanation", ""),
            "metadata": getattr(question, "metadata", {}),
        }
