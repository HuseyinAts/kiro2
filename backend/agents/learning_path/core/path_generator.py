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
from datetime import datetime, timezone
import uuid

from ..models import (
    StudentProfile,
    LearningResource,
    LearningPath,
    LearningPhase,
    LearningStyle,
    KnowledgeLevel,
)

# KnowledgeLevel to numeric mapping for difficulty comparison
DIFFICULTY_VALUES = {
    KnowledgeLevel.BEGINNER: 0,
    KnowledgeLevel.ELEMENTARY: 1,
    KnowledgeLevel.INTERMEDIATE: 2,
    KnowledgeLevel.ADVANCED: 3,
    KnowledgeLevel.EXPERT: 4,
}

# KnowledgeLevel to IRT difficulty (b parameter) mapping [-4.0, 4.0]
DIFFICULTY_TO_IRT = {
    KnowledgeLevel.BEGINNER: -2.0,
    KnowledgeLevel.ELEMENTARY: -1.0,
    KnowledgeLevel.INTERMEDIATE: 0.0,
    KnowledgeLevel.ADVANCED: 1.5,
    KnowledgeLevel.EXPERT: 3.0,
}

# ZPD (Zone of Proximal Development) constants
ZPD_MIN_PROBABILITY = 0.15
ZPD_MAX_PROBABILITY = 0.85


def get_difficulty_value(level: KnowledgeLevel) -> int:
    """Convert KnowledgeLevel enum to numeric value for comparison."""
    return DIFFICULTY_VALUES.get(level, 2)  # Default to INTERMEDIATE


def get_irt_difficulty(level: KnowledgeLevel) -> float:
    """Convert KnowledgeLevel enum to IRT difficulty (b parameter)."""
    return DIFFICULTY_TO_IRT.get(level, 0.0)  # Default to INTERMEDIATE


def calculate_success_probability(
    theta: float, difficulty: float, discrimination: float = 1.0, guessing: float = 0.0
) -> float:
    """
    Calculate success probability using IRT 3PL model.

    P(θ) = c + (1 - c) / (1 + e^(-a(θ - b)))

    Args:
        theta: Student ability [-4.0, 4.0]
        difficulty: Item difficulty (b parameter) [-4.0, 4.0]
        discrimination: Item discrimination (a parameter) [0.2, 4.0]
        guessing: Guessing parameter (c parameter) [0.0, 0.35]

    Returns:
        Success probability [0.0, 1.0]
    """
    import math

    # Clip exponent to prevent overflow
    exponent = -discrimination * (theta - difficulty)
    exponent = max(-20, min(20, exponent))

    probability = guessing + (1 - guessing) / (1 + math.exp(exponent))
    return max(0.0, min(1.0, probability))


def is_resource_in_zpd(
    resource: LearningResource,
    student_ability: float,
    min_prob: float = ZPD_MIN_PROBABILITY,
    max_prob: float = ZPD_MAX_PROBABILITY,
) -> bool:
    """
    Check if a resource is within student's Zone of Proximal Development.

    ZPD optimal range: 15-85% success probability (CLAUDE.md)

    Args:
        resource: Learning resource to check
        student_ability: Student's current ability (0.0-1.0, converted to theta)
        min_prob: Minimum ZPD probability (default 0.15)
        max_prob: Maximum ZPD probability (default 0.85)

    Returns:
        True if resource is within ZPD
    """
    # Convert student ability (0.0-1.0) to theta scale (-4.0 to 4.0)
    theta = (student_ability - 0.5) * 8  # Maps 0.0-1.0 to -4.0 to 4.0

    # Get resource difficulty as IRT b parameter
    irt_difficulty = get_irt_difficulty(resource.difficulty_level)

    # Calculate success probability
    success_prob = calculate_success_probability(theta, irt_difficulty)

    return min_prob <= success_prob <= max_prob


def filter_resources_by_zpd(
    resources: List[LearningResource],
    student_ability: float,
    min_prob: float = ZPD_MIN_PROBABILITY,
    max_prob: float = ZPD_MAX_PROBABILITY,
) -> List[LearningResource]:
    """
    Filter resources to those within student's ZPD.

    Args:
        resources: List of learning resources
        student_ability: Student's current ability (0.0-1.0)
        min_prob: Minimum ZPD probability (default 0.15)
        max_prob: Maximum ZPD probability (default 0.85)

    Returns:
        List of resources within ZPD, or original list if none match
    """
    if not resources:
        return resources

    zpd_resources = [
        r for r in resources
        if is_resource_in_zpd(r, student_ability, min_prob, max_prob)
    ]

    # If no resources in ZPD, return all (fallback)
    if not zpd_resources:
        logger.warning(
            f"No resources in ZPD for ability {student_ability}. "
            f"Returning all {len(resources)} resources."
        )
        return resources

    logger.info(
        f"ZPD filtering: {len(zpd_resources)}/{len(resources)} resources "
        f"in optimal range for ability {student_ability}"
    )
    return zpd_resources


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

            # Apply ZPD filtering to select optimal difficulty resources
            # Derive student ability from knowledge_level (0.0-1.0 scale)
            knowledge_to_ability = {
                KnowledgeLevel.BEGINNER: 0.15,
                KnowledgeLevel.ELEMENTARY: 0.35,
                KnowledgeLevel.INTERMEDIATE: 0.5,
                KnowledgeLevel.ADVANCED: 0.7,
                KnowledgeLevel.EXPERT: 0.9,
            }
            student_ability = knowledge_to_ability.get(profile.knowledge_level, 0.5)
            zpd_filtered_resources = filter_resources_by_zpd(
                resources, student_ability
            )

            # Create learning phases with ZPD-filtered resources
            phases = self._create_phases(zpd_filtered_resources, profile)

            # Calculate total time from ZPD-filtered resources
            total_time = sum(r.estimated_time for r in zpd_filtered_resources)

            # Generate reasoning with LLM if available
            reasoning = await self._generate_reasoning(
                profile, zpd_filtered_resources, goal
            )

            # Convert phases from dict to LearningPhase objects
            learning_phases = self._convert_phases_to_objects(
                phases, zpd_filtered_resources
            )

            # Create learning path with ZPD-filtered resources
            path = LearningPath(
                path_id=path_id,
                student_id=profile.student_id,
                goal=goal,
                resources=zpd_filtered_resources,
                phases=learning_phases,
                created_at=datetime.now(),
                reasoning=reasoning,
                metadata={
                    "total_time": total_time,
                    "created_by": "PathGenerator",
                    "version": "2.1",
                    "zpd_filtering": {
                        "enabled": True,
                        "student_ability": student_ability,
                        "original_count": len(resources),
                        "filtered_count": len(zpd_filtered_resources),
                        "zpd_range": [ZPD_MIN_PROBABILITY, ZPD_MAX_PROBABILITY],
                    },
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
        profile: Optional[StudentProfile] = None,
        new_resources: Optional[List[LearningResource]] = None,
    ) -> LearningPath:
        """
        Adapt existing path based on performance

        Args:
            current_path: Current learning path
            performance_data: Student performance data
            profile: Student profile (optional, uses metadata if not provided)
            new_resources: New resources to incorporate (optional)

        Returns:
            Adapted LearningPath

        Example:
            >>> performance = {"completed": 5, "avg_score": 75}
            >>> adapted_path = await generator.adapt_path(current_path, performance, profile)
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

            # Get or create student profile for adaptation
            if profile is None:
                # Try to get from metadata or create minimal profile
                profile_data = current_path.metadata.get("profile", {})
                if profile_data:
                    profile = StudentProfile.from_dict(profile_data)
                else:
                    # Create minimal profile from path data
                    profile = StudentProfile(
                        student_id=current_path.student_id,
                        name="Student",
                        grade="12",
                        exam_target="YKS",
                        learning_goal=current_path.goal,
                        learning_style=LearningStyle.MIXED,
                        knowledge_level=KnowledgeLevel.INTERMEDIATE,
                        interests=[],
                        available_time=60,
                    )

            # Calculate base ability from knowledge level
            knowledge_to_ability = {
                KnowledgeLevel.BEGINNER: 0.15,
                KnowledgeLevel.ELEMENTARY: 0.35,
                KnowledgeLevel.INTERMEDIATE: 0.5,
                KnowledgeLevel.ADVANCED: 0.7,
                KnowledgeLevel.EXPERT: 0.9,
            }
            ability = knowledge_to_ability.get(profile.knowledge_level, 0.5)

            # Adjust ability based on performance using ZPD principles
            if avg_score < 60:
                # Student struggling - reduce ability estimate
                adjusted_ability = max(0.0, ability - 0.1)
                logger.info(
                    f"Student struggling (score={avg_score}), "
                    f"adjusting ability {ability:.2f} -> {adjusted_ability:.2f}"
                )
            elif avg_score > 85:
                # Student excelling - increase ability estimate
                adjusted_ability = min(1.0, ability + 0.1)
                logger.info(
                    f"Student excelling (score={avg_score}), "
                    f"adjusting ability {ability:.2f} -> {adjusted_ability:.2f}"
                )
            else:
                adjusted_ability = ability

            # Apply ZPD filtering with adjusted ability
            # This will be done in generate_path(), but we can also
            # pre-filter here for performance-based difficulty adjustment
            current_difficulty_level = int(adjusted_ability * 4)  # Maps 0.0-1.0 to 0-4

            if avg_score < 60:
                # Student struggling, prioritize easier resources
                target_difficulty = max(0, current_difficulty_level - 1)
                easier_resources = [
                    r for r in remaining_resources
                    if get_difficulty_value(r.difficulty_level) <= target_difficulty
                ]
                if easier_resources:
                    remaining_resources = easier_resources + [
                        r for r in remaining_resources if r not in easier_resources
                    ]
            elif avg_score > 85:
                # Student excelling, prioritize harder resources
                target_difficulty = min(4, current_difficulty_level + 1)
                harder_resources = [
                    r for r in remaining_resources
                    if get_difficulty_value(r.difficulty_level) >= target_difficulty
                ]
                if harder_resources:
                    remaining_resources = harder_resources + [
                        r for r in remaining_resources if r not in harder_resources
                    ]

            # Regenerate path with remaining resources (ZPD filtering applied)
            adapted_path = await self.generate_path(
                profile,
                remaining_resources,
                profile.learning_goal,
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

            # Convert to LearningPath object if needed
            if isinstance(path_data, LearningPath):
                logger.info("Structured path created")
                return path_data

            # Convert dict response to LearningPath object
            if isinstance(path_data, dict):
                learning_path = LearningPath(
                    path_id=path_data.get("path_id", str(uuid.uuid4())),
                    student_id=profile.student_id,
                    goal=f"{subject} - {', '.join(topics[:3])}",
                    resources=path_data.get("resources", []),
                    phases=path_data.get("phases", []),
                    created_at=datetime.now(timezone.utc),
                    reasoning=path_data.get("reasoning", "Structured path generated"),
                    metadata={
                        "subject": subject,
                        "topics": topics,
                        "generation_method": "structured",
                        **path_data.get("metadata", {}),
                    },
                )
                logger.info("Structured path created from dict response")
                return learning_path

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

    def _convert_phases_to_objects(
        self,
        phase_dicts: List[Dict[str, Any]],
        resources: List[LearningResource],
    ) -> List[LearningPhase]:
        """
        Convert phase dictionaries to LearningPhase objects.

        Args:
            phase_dicts: List of phase dictionaries from _create_phases()
            resources: List of all resources to map to phases

        Returns:
            List of LearningPhase objects
        """
        if not phase_dicts:
            return []

        # Create resource lookup by ID
        resource_map = {r.resource_id: r for r in resources}

        learning_phases = []
        for i, phase_dict in enumerate(phase_dicts):
            # Get resources for this phase
            phase_resource_ids = phase_dict.get("resource_ids", [])
            phase_resources = [
                resource_map[rid]
                for rid in phase_resource_ids
                if rid in resource_map
            ]

            phase = LearningPhase(
                phase_id=f"phase_{i + 1}",
                name=phase_dict.get("phase_name", f"Phase {i + 1}"),
                description=phase_dict.get("description", ""),
                order=i,
                resources=phase_resources,
                learning_objectives=phase_dict.get("objectives", []),
                metadata={
                    "estimated_time": phase_dict.get("estimated_time", 0),
                },
            )
            learning_phases.append(phase)

        return learning_phases

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
