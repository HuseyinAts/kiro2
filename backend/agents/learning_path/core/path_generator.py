"""
Learning Path Generation Module
Teknofest 2025 - Eğitim Eylemci Projesi

Extracted from LearningPathAgent (lines 1109-1249, 2885-2982)

This module handles:
- Learning path generation
- Path adaptation based on performance
- Structured path creation with phases
- Resource sequencing
- Milestone creation

Responsibilities:
- Generate personalized learning paths
- Create learning phases and milestones
- Adapt paths based on student progress
- Sequence resources logically
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from ..models import StudentProfile, LearningResource, LearningPath, KnowledgeLevel

logger = logging.getLogger(__name__)


class PathGenerator:
    """
    Path Generator - Creates personalized learning paths

    This class generates structured learning paths based on
    student profiles, learning goals, and available resources.

    Uses dependency injection for external services.
    """

    def __init__(self, llm_service=None, structured_path_generator=None):
        """
        Initialize PathGenerator

        Args:
            llm_service: LLM service for AI-powered path generation (optional)
            structured_path_generator: Structured path generator service (optional)
        """
        self.llm = llm_service
        self.structured_generator = structured_path_generator

        logger.info("PathGenerator initialized")

    async def generate_path(
        self, profile: StudentProfile, resources: List[LearningResource], goal: str
    ) -> LearningPath:
        """
        Generate complete learning path

        Args:
            profile: Student profile
            resources: Available learning resources
            goal: Learning goal

        Returns:
            LearningPath object

        Example:
            >>> generator = PathGenerator(llm_service)
            >>> path = await generator.generate_path(profile, resources, "Learn calculus")
        """
        if not profile:
            raise ValueError("profile is required")
        if not resources:
            raise ValueError("resources cannot be empty")
        if not goal:
            raise ValueError("goal is required")

        try:
            logger.info(
                f"Generating path: student={profile.student_id}, "
                f"resources={len(resources)}, goal='{goal}'"
            )

            # Generate path ID
            path_id = f"path_{profile.student_id}_{uuid.uuid4().hex[:8]}"

            # Create learning phases
            phases = self._create_phases(resources, profile)

            # Calculate total time
            total_time = sum(r.estimated_time for r in resources)

            # Generate reasoning with LLM if available
            reasoning = await self._generate_reasoning(profile, resources, goal)

            # Create learning path
            path = LearningPath(
                path_id=path_id,
                student_profile=profile,
                resources=resources,
                total_time=total_time,
                phases=phases,
                created_at=datetime.now(),
                reasoning=reasoning,
                metadata={
                    "goal": goal,
                    "created_by": "PathGenerator",
                    "version": "2.0",
                },
            )

            logger.info(
                f"Path generated: {path_id} ({len(phases)} phases, {total_time} min)"
            )
            return path

        except Exception as e:
            logger.error(f"Generate path error: {str(e)}")
            raise

    async def adapt_path(
        self,
        current_path: LearningPath,
        performance_data: Dict[str, Any],
        new_resources: Optional[List[LearningResource]] = None,
    ) -> LearningPath:
        """
        Adapt existing path based on performance

        Args:
            current_path: Current learning path
            performance_data: Student performance data
            new_resources: New resources to incorporate (optional)

        Returns:
            Adapted LearningPath

        Example:
            >>> performance = {"completed": 5, "avg_score": 75}
            >>> adapted_path = await generator.adapt_path(current_path, performance)
        """
        if not current_path:
            raise ValueError("current_path is required")
        if not performance_data:
            raise ValueError("performance_data is required")

        try:
            logger.info(f"Adapting path: {current_path.path_id}")

            # Analyze performance
            completed_resources = performance_data.get("completed_resource_ids", [])
            avg_score = performance_data.get("avg_score", 0)

            # Filter out completed resources
            remaining_resources = [
                r
                for r in current_path.resources
                if r.resource_id not in completed_resources
            ]

            # Add new resources if provided
            if new_resources:
                remaining_resources.extend(new_resources)

            # Adjust difficulty if needed
            if avg_score < 60:
                # Student struggling, add easier resources
                logger.info("Student struggling, adjusting difficulty down")
                # TODO: Add easier resources
            elif avg_score > 85:
                # Student excelling, add harder resources
                logger.info("Student excelling, adjusting difficulty up")
                # TODO: Add harder resources

            # Regenerate path with remaining resources
            adapted_path = await self.generate_path(
                current_path.student_profile,
                remaining_resources,
                current_path.student_profile.learning_goal,
            )

            # Preserve original path ID with version
            adapted_path.path_id = f"{current_path.path_id}_v2"
            adapted_path.metadata["adapted_from"] = current_path.path_id
            adapted_path.metadata["adaptation_reason"] = "performance_adjustment"

            logger.info(f"Path adapted: {adapted_path.path_id}")
            return adapted_path

        except Exception as e:
            logger.error(f"Adapt path error: {str(e)}")
            raise

    async def create_structured_path(
        self, profile: StudentProfile, subject: str, topics: List[str]
    ) -> LearningPath:
        """
        Create structured learning path with predefined progression

        Args:
            profile: Student profile
            subject: Subject (e.g., "Matematik")
            topics: List of topics in learning order

        Returns:
            Structured LearningPath
        """
        if not self.structured_generator:
            raise ValueError("Structured path generator not available")

        try:
            logger.info(
                f"Creating structured path: student={profile.student_id}, "
                f"subject={subject}, topics={topics}"
            )

            # Use structured path generator service
            path_data = await self.structured_generator.generate_structured_path(
                student_profile=profile, subject=subject, topics=topics
            )

            # Convert to LearningPath object
            # TODO: Implement conversion from service response

            logger.info("Structured path created")
            return path_data

        except Exception as e:
            logger.error(f"Create structured path error: {str(e)}")
            raise

    # Private methods

    def _create_phases(
        self, resources: List[LearningResource], profile: StudentProfile
    ) -> List[Dict[str, Any]]:
        """
        Create learning phases from resources

        Divides resources into logical phases based on:
        - Difficulty progression
        - Topic clustering
        - Time constraints
        """
        if not resources:
            return []

        # Simple implementation: divide into 3-5 phases
        num_phases = min(5, max(3, len(resources) // 3))

        phases = []
        resources_per_phase = len(resources) // num_phases

        for i in range(num_phases):
            start_idx = i * resources_per_phase
            end_idx = (
                start_idx + resources_per_phase
                if i < num_phases - 1
                else len(resources)
            )

            phase_resources = resources[start_idx:end_idx]

            phase = {
                "phase_number": i + 1,
                "phase_name": self._get_phase_name(i + 1, num_phases),
                "resource_ids": [r.resource_id for r in phase_resources],
                "estimated_time": sum(r.estimated_time for r in phase_resources),
                "description": self._get_phase_description(i + 1, num_phases),
                "objectives": self._get_phase_objectives(i + 1, num_phases),
            }

            phases.append(phase)

        return phases

    def _get_phase_name(self, phase_number: int, total_phases: int) -> str:
        """Get name for learning phase"""
        if phase_number == 1:
            return "Temel Kavramlar"
        elif phase_number == total_phases:
            return "İleri Düzey ve Uygulama"
        elif phase_number == total_phases // 2:
            return "Orta Seviye"
        else:
            return f"Faz {phase_number}"

    def _get_phase_description(self, phase_number: int, total_phases: int) -> str:
        """Get description for learning phase"""
        if phase_number == 1:
            return "Konunun temel kavramlarını öğrenme"
        elif phase_number == total_phases:
            return "İleri düzey konuları anlama ve uygulama"
        else:
            return f"Faz {phase_number} - Devam eden öğrenme"

    def _get_phase_objectives(self, phase_number: int, total_phases: int) -> List[str]:
        """Get objectives for learning phase"""
        if phase_number == 1:
            return [
                "Temel kavramları anlama",
                "Konuya giriş yapma",
                "Ön bilgileri pekiştirme",
            ]
        elif phase_number == total_phases:
            return [
                "İleri düzey problemleri çözme",
                "Gerçek hayat uygulamaları",
                "Konuda uzmanlaşma",
            ]
        else:
            return [
                f"Faz {phase_number} hedeflerini tamamlama",
                "Bilgiyi pekiştirme",
                "Bir sonraki faza hazırlanma",
            ]

    async def _generate_reasoning(
        self, profile: StudentProfile, resources: List[LearningResource], goal: str
    ) -> str:
        """
        Generate reasoning for why this path was created

        Uses LLM if available, otherwise returns generic reasoning.
        """
        if not self.llm:
            return self._get_generic_reasoning(profile, resources, goal)

        try:
            prompt = f"""
Öğrenci profili:
- İsim: {profile.name}
- Seviye: {profile.knowledge_level.value}
- Öğrenme stili: {profile.learning_style.value}
- Hedef: {goal}

Bu öğrenci için {len(resources)} kaynaklı bir öğrenme yolu oluşturuldu.

Neden bu kaynaklar seçildi ve nasıl sıralandı? Kısa ve net açıkla (2-3 cümle).
"""

            result = await self.llm.generate(prompt=prompt, temperature=0.7)

            if result.get("success"):
                return result["text"]
            else:
                return self._get_generic_reasoning(profile, resources, goal)

        except Exception as e:
            logger.warning(f"LLM reasoning failed: {str(e)}")
            return self._get_generic_reasoning(profile, resources, goal)

    def _get_generic_reasoning(
        self, profile: StudentProfile, resources: List[LearningResource], goal: str
    ) -> str:
        """Get generic reasoning without LLM"""
        return (
            f"Bu öğrenme yolu {profile.name} için {profile.knowledge_level.value} seviyesinde "
            f"ve {profile.learning_style.value} öğrenme stiline uygun olarak oluşturulmuştur. "
            f"{len(resources)} kaynak, '{goal}' hedefine ulaşmak için seçilmiş ve sıralanmıştır."
        )
