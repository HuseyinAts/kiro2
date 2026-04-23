"""
Time Planning Strategy Module
Teknofest 2025 - Eğitim Eylemci Projesi

This module implements time-based scheduling and milestone planning.

Responsibilities:
- Create study schedules
- Define learning milestones
- Track learning objectives
- Estimate completion times
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from ..models import LearningPath, LearningResource

logger = logging.getLogger(__name__)


class TimePlanner:
    """Time Planner - Creates schedules and milestones"""

    def __init__(self):
        """Initialize planner"""
        logger.info("TimePlanner initialized")

    def create_schedule(self, path: LearningPath, available_time: int) -> LearningPath:
        """
        Create study schedule for learning path

        Args:
            path: Learning path
            available_time: Daily available time (minutes)

        Returns:
            Path with schedule metadata
        """
        if available_time <= 0:
            raise ValueError("available_time must be positive")

        days_needed = path.total_time // available_time
        if path.total_time % available_time > 0:
            days_needed += 1

        schedule = {
            "start_date": datetime.now().isoformat(),
            "estimated_end_date": (
                datetime.now() + timedelta(days=days_needed)
            ).isoformat(),
            "days_needed": days_needed,
            "minutes_per_day": available_time,
            "daily_plan": self._create_daily_plan(path.resources, available_time),
        }

        path.metadata["schedule"] = schedule
        logger.info(f"Schedule created: {days_needed} days, {available_time} min/day")
        return path

    def create_milestones(
        self, path: LearningPath, milestone_count: int = 5
    ) -> list[dict[str, Any]]:
        """Create learning milestones"""
        if not path.resources:
            return []

        resources_per_milestone = len(path.resources) // milestone_count
        milestones = []

        for i in range(milestone_count):
            start = i * resources_per_milestone
            end = (
                start + resources_per_milestone
                if i < milestone_count - 1
                else len(path.resources)
            )

            milestone = {
                "milestone_number": i + 1,
                "title": f"Milestone {i + 1}",
                "resource_range": [start, end],
                "estimated_time": sum(
                    r.estimated_time for r in path.resources[start:end]
                ),
                "completion_percentage": ((i + 1) / milestone_count) * 100,
            }
            milestones.append(milestone)

        return milestones

    def track_objectives(
        self, path: LearningPath, completed_resource_ids: list[str]
    ) -> dict[str, Any]:
        """Track learning objectives progress"""
        total = len(path.resources)
        completed = sum(
            1 for r in path.resources if r.resource_id in completed_resource_ids
        )

        return {
            "total_objectives": total,
            "completed_objectives": completed,
            "completion_percentage": (completed / total * 100) if total > 0 else 0,
            "remaining_time": path.estimate_remaining_time(completed_resource_ids),
        }

    def _create_daily_plan(
        self, resources: list[LearningResource], daily_time: int
    ) -> list[dict[str, Any]]:
        """Create daily resource allocation"""
        daily_plan = []
        current_day = []
        current_time = 0

        for resource in resources:
            if current_time + resource.estimated_time <= daily_time:
                current_day.append(resource.resource_id)
                current_time += resource.estimated_time
            else:
                if current_day:
                    daily_plan.append(
                        {
                            "day": len(daily_plan) + 1,
                            "resources": current_day,
                            "total_time": current_time,
                        }
                    )
                current_day = [resource.resource_id]
                current_time = resource.estimated_time

        if current_day:
            daily_plan.append(
                {
                    "day": len(daily_plan) + 1,
                    "resources": current_day,
                    "total_time": current_time,
                }
            )

        return daily_plan
