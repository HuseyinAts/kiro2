"""
Learning Path Optimization Module
Teknofest 2025 - Eğitim Eylemci Projesi

Extracted from LearningPathAgent (lines 3203-3278)

This module handles:
- Resource sequence optimization
- Difficulty balancing
- Time optimization
- Learning efficiency improvement

Responsibilities:
- Optimize resource order for maximum learning efficiency
- Balance difficulty progression
- Minimize cognitive load
- Maximize retention
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from ..models import LearningPath, LearningResource, KnowledgeLevel

logger = logging.getLogger(__name__)


class PathOptimizer:
    """
    Path Optimizer - Optimizes learning path structure

    This class optimizes the order and structure of learning paths
    to maximize learning efficiency and student engagement.
    """

    def __init__(self):
        """Initialize PathOptimizer"""
        logger.info("PathOptimizer initialized")

    def optimize_sequence(self, path: LearningPath) -> LearningPath:
        """
        Optimize resource sequence in learning path

        Reorders resources for optimal learning progression.

        Args:
            path: Learning path to optimize

        Returns:
            Optimized LearningPath

        Example:
            >>> optimizer = PathOptimizer()
            >>> optimized = optimizer.optimize_sequence(path)
        """
        if not path or not path.resources:
            return path

        try:
            logger.info(f"Optimizing sequence for path: {path.path_id}")

            # Get optimized order
            optimized_resources = self._optimize_resource_order(path.resources)

            # Create optimized path
            optimized_path = LearningPath(
                path_id=path.path_id,
                student_profile=path.student_profile,
                resources=optimized_resources,
                total_time=path.total_time,
                phases=self._recreate_phases(optimized_resources, path.phases),
                created_at=path.created_at,
                reasoning=path.reasoning + " (Optimized for learning efficiency)",
                metadata={
                    **path.metadata,
                    "optimized_at": datetime.now().isoformat(),
                    "optimization_version": "1.0",
                },
            )

            logger.info(
                f"Sequence optimized: {len(optimized_resources)} resources reordered"
            )
            return optimized_path

        except Exception as e:
            logger.error(f"Optimize sequence error: {str(e)}")
            return path  # Return original on error

    def balance_difficulty(self, path: LearningPath) -> LearningPath:
        """
        Balance difficulty progression in path

        Ensures smooth difficulty curve without sudden jumps.

        Args:
            path: Learning path to balance

        Returns:
            Balanced LearningPath
        """
        if not path or not path.resources:
            return path

        try:
            logger.info(f"Balancing difficulty for path: {path.path_id}")

            # Sort by difficulty
            balanced_resources = self._balance_difficulty_order(path.resources)

            # Create balanced path
            balanced_path = LearningPath(
                path_id=path.path_id,
                student_profile=path.student_profile,
                resources=balanced_resources,
                total_time=path.total_time,
                phases=self._recreate_phases(balanced_resources, path.phases),
                created_at=path.created_at,
                reasoning=path.reasoning + " (Balanced for difficulty progression)",
                metadata={**path.metadata, "balanced_at": datetime.now().isoformat()},
            )

            logger.info("Difficulty balanced successfully")
            return balanced_path

        except Exception as e:
            logger.error(f"Balance difficulty error: {str(e)}")
            return path

    def optimize_time(self, path: LearningPath, target_time: int) -> LearningPath:
        """
        Optimize path to fit target time constraint

        Args:
            path: Learning path to optimize
            target_time: Target total time in minutes

        Returns:
            Time-optimized LearningPath
        """
        if not path or not path.resources:
            return path

        if target_time <= 0:
            raise ValueError("target_time must be positive")

        try:
            logger.info(
                f"Optimizing time: current={path.total_time}min, "
                f"target={target_time}min"
            )

            # If current time is within acceptable range, no optimization needed
            if abs(path.total_time - target_time) < target_time * 0.1:  # 10% tolerance
                logger.info("Time already optimal")
                return path

            # Select resources to fit time
            optimized_resources = self._select_resources_for_time(
                path.resources, target_time
            )

            # Create time-optimized path
            optimized_path = LearningPath(
                path_id=path.path_id,
                student_profile=path.student_profile,
                resources=optimized_resources,
                total_time=sum(r.estimated_time for r in optimized_resources),
                phases=self._recreate_phases(optimized_resources, path.phases),
                created_at=path.created_at,
                reasoning=path.reasoning + f" (Optimized for {target_time} minutes)",
                metadata={
                    **path.metadata,
                    "time_optimized_at": datetime.now().isoformat(),
                    "target_time": target_time,
                },
            )

            logger.info(
                f"Time optimized: {path.total_time}min → {optimized_path.total_time}min"
            )
            return optimized_path

        except Exception as e:
            logger.error(f"Optimize time error: {str(e)}")
            return path

    # Private optimization methods

    def _optimize_resource_order(
        self, resources: List[LearningResource]
    ) -> List[LearningResource]:
        """
        Optimize resource order for learning efficiency

        Strategy:
        1. Start with easier resources (build confidence)
        2. Progress to harder resources (challenge)
        3. Mix different types (avoid monotony)
        4. End with practice/application (consolidation)
        """
        # Sort by difficulty first
        difficulty_order = [
            KnowledgeLevel.BEGINNER,
            KnowledgeLevel.ELEMENTARY,
            KnowledgeLevel.INTERMEDIATE,
            KnowledgeLevel.ADVANCED,
            KnowledgeLevel.EXPERT,
        ]

        sorted_resources = sorted(
            resources, key=lambda r: difficulty_order.index(r.difficulty_level)
        )

        # Group by type
        videos = [r for r in sorted_resources if "video" in r.resource_type.lower()]
        articles = [r for r in sorted_resources if "article" in r.resource_type.lower()]
        practice = [
            r
            for r in sorted_resources
            if "quiz" in r.resource_type.lower()
            or "practice" in r.resource_type.lower()
        ]
        others = [r for r in sorted_resources if r not in videos + articles + practice]

        # Interleave types for variety
        optimized = []
        max_len = max(len(videos), len(articles), len(practice), len(others))

        for i in range(max_len):
            if i < len(videos):
                optimized.append(videos[i])
            if i < len(articles):
                optimized.append(articles[i])
            if i < len(practice):
                optimized.append(practice[i])
            if i < len(others):
                optimized.append(others[i])

        return optimized

    def _balance_difficulty_order(
        self, resources: List[LearningResource]
    ) -> List[LearningResource]:
        """
        Balance difficulty progression

        Creates smooth difficulty curve without sudden jumps.
        """
        difficulty_order = [
            KnowledgeLevel.BEGINNER,
            KnowledgeLevel.ELEMENTARY,
            KnowledgeLevel.INTERMEDIATE,
            KnowledgeLevel.ADVANCED,
            KnowledgeLevel.EXPERT,
        ]

        # Sort by difficulty
        sorted_resources = sorted(
            resources, key=lambda r: difficulty_order.index(r.difficulty_level)
        )

        return sorted_resources

    def _select_resources_for_time(
        self, resources: List[LearningResource], target_time: int
    ) -> List[LearningResource]:
        """
        Select subset of resources that fit target time

        Strategy: Prioritize high-quality, essential resources
        """
        # Sort by quality (rating) and difficulty balance
        scored_resources = []
        for r in resources:
            score = (r.rating or 3.0) * 2  # Base score from rating

            # Prefer intermediate difficulty (more useful for most learners)
            if r.difficulty_level == KnowledgeLevel.INTERMEDIATE:
                score += 2
            elif r.difficulty_level in [
                KnowledgeLevel.ELEMENTARY,
                KnowledgeLevel.ADVANCED,
            ]:
                score += 1

            scored_resources.append((r, score))

        # Sort by score descending
        scored_resources.sort(key=lambda x: x[1], reverse=True)

        # Select resources until we hit target time
        selected = []
        current_time = 0

        for resource, _ in scored_resources:
            if current_time + resource.estimated_time <= target_time:
                selected.append(resource)
                current_time += resource.estimated_time

            if current_time >= target_time:
                break

        # Ensure we have at least some resources
        if not selected and resources:
            selected = [resources[0]]  # At least include the best one

        return selected

    def _recreate_phases(
        self, resources: List[LearningResource], original_phases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Recreate phases with new resource order

        Maintains phase structure but updates resource assignments.
        """
        if not resources:
            return []

        # Simple approach: redistribute resources across original number of phases
        num_phases = len(original_phases) if original_phases else 3
        resources_per_phase = len(resources) // num_phases

        new_phases = []
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
                "phase_name": original_phases[i]["phase_name"]
                if i < len(original_phases)
                else f"Phase {i + 1}",
                "resource_ids": [r.resource_id for r in phase_resources],
                "estimated_time": sum(r.estimated_time for r in phase_resources),
                "description": original_phases[i].get("description", "")
                if i < len(original_phases)
                else "",
                "objectives": original_phases[i].get("objectives", [])
                if i < len(original_phases)
                else [],
            }

            new_phases.append(phase)

        return new_phases
