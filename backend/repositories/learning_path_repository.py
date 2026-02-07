"""
Learning Path Repository
Production-ready repository for Learning Path system with type-safe operations.

Provides:
- LearningPathRepository: Learning path CRUD with eager loading
- StudentProfileRepository: Student profile with get_or_create pattern
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.learning_path_models import (
    LearningPath,
    LearningPathStudentProfile,
)

from .base import BaseRepository

logger = logging.getLogger(__name__)


class LearningPathRepository(BaseRepository[LearningPath]):
    """
    Repository for Learning Path operations.

    Provides type-safe CRUD operations with relationship eager loading
    for optimal query performance.

    Attributes:
        model: LearningPath SQLAlchemy model
        session: Async database session
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session for database operations
        """
        super().__init__(LearningPath, session)

    async def get_by_student_id(
        self, student_id: str
    ) -> Optional[LearningPath]:
        """
        Get the most recent learning path for a student.

        Args:
            student_id: Unique student identifier

        Returns:
            Most recent LearningPath or None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            result = await self.session.execute(
                select(LearningPath)
                .where(LearningPath.student_id == student_id)
                .order_by(LearningPath.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting learning path for student {student_id}: {str(e)}"
            )
            raise

    async def get_active_paths(
        self, student_id: str
    ) -> List[LearningPath]:
        """
        Get all active learning paths for a student.

        Active paths are those with progress < 100% or created within last 30 days.
        Ordered by creation date descending.

        Args:
            student_id: Unique student identifier

        Returns:
            List of active learning paths (may be empty)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            result = await self.session.execute(
                select(LearningPath)
                .where(
                    and_(
                        LearningPath.student_id == student_id,
                        LearningPath.overall_progress < 100.0,
                    )
                )
                .order_by(LearningPath.created_at.desc())
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting active paths for student {student_id}: {str(e)}"
            )
            raise

    async def get_with_progress(
        self, path_id: str
    ) -> Optional[LearningPath]:
        """
        Get learning path with eager-loaded relationships.

        Eagerly loads:
        - student: LearningPathStudentProfile relationship

        Use this method when you need to access related data to avoid N+1 queries.

        Args:
            path_id: Unique learning path identifier

        Returns:
            LearningPath with relationships loaded or None if not found

        Raises:
            SQLAlchemyError: If database operation fails

        Example:
            >>> path = await repo.get_with_progress("path-123")
            >>> if path:
            >>>     print(path.student.name)  # No additional query
        """
        try:
            result = await self.session.execute(
                select(LearningPath)
                .options(
                    selectinload(LearningPath.student)
                )
                .where(LearningPath.path_id == path_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting learning path {path_id} with progress: {str(e)}"
            )
            raise

    async def get_by_student_and_subject(
        self, student_id: str, subject: str
    ) -> List[LearningPath]:
        """
        Get all learning paths for a student filtered by subject.

        Args:
            student_id: Unique student identifier
            subject: Subject name (e.g., "Matematik", "Fizik")

        Returns:
            List of learning paths for the subject (may be empty)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            result = await self.session.execute(
                select(LearningPath)
                .where(
                    and_(
                        LearningPath.student_id == student_id,
                        LearningPath.subject == subject,
                    )
                )
                .order_by(LearningPath.created_at.desc())
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting paths for student {student_id}, subject {subject}: {str(e)}"
            )
            raise

    async def update_progress(
        self,
        path_id: str,
        completed_modules: int,
        completed_topics: int,
    ) -> Optional[LearningPath]:
        """
        Update learning path progress and calculate overall percentage.

        Args:
            path_id: Unique learning path identifier
            completed_modules: Number of completed modules
            completed_topics: Number of completed topics

        Returns:
            Updated LearningPath or None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Get current path to calculate progress
            path = await self.get_by_id(path_id)
            if not path:
                logger.warning(f"Learning path {path_id} not found for progress update")
                return None

            # Calculate overall progress percentage
            overall_progress: float = 0.0
            if path.total_topics > 0:
                progress_calc = (completed_topics / path.total_topics) * 100
                overall_progress = min(100.0, progress_calc)

            # Update with calculated progress
            return await self.update(
                path_id,
                completed_modules=completed_modules,
                completed_topics=completed_topics,
                overall_progress=overall_progress,
            )
        except SQLAlchemyError as e:
            logger.error(f"Error updating progress for path {path_id}: {str(e)}")
            raise


class StudentProfileRepository(BaseRepository[LearningPathStudentProfile]):
    """
    Repository for Learning Path Student Profile operations.

    Provides specialized methods for student profile management
    including get_or_create pattern for atomic operations.

    Attributes:
        model: LearningPathStudentProfile SQLAlchemy model
        session: Async database session
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session for database operations
        """
        super().__init__(LearningPathStudentProfile, session)

    async def get_or_create(
        self, student_id: str, **defaults: Any
    ) -> tuple[LearningPathStudentProfile, bool]:
        """
        Get student profile or create if it doesn't exist (atomic operation).

        This method is thread-safe and handles race conditions during concurrent
        profile creation attempts.

        Args:
            student_id: Unique student identifier
            **defaults: Default values for profile creation (name, grade, etc.)

        Returns:
            Tuple of (profile, created) where:
            - profile: LearningPathStudentProfile instance
            - created: True if newly created, False if existing

        Raises:
            SQLAlchemyError: If database operation fails
            ValueError: If defaults are missing required fields

        Example:
            >>> profile, created = await repo.get_or_create(
            ...     student_id="student-123",
            ...     name="John Doe",
            ...     grade="10",
            ...     exam_target="YKS",
            ...     learning_style="visual",
            ...     knowledge_level="intermediate",
            ...     available_time=60
            ... )
            >>> if created:
            ...     print(f"Created new profile for {profile.name}")
        """
        try:
            # Try to get existing profile
            result = await self.session.execute(
                select(LearningPathStudentProfile).where(
                    LearningPathStudentProfile.student_id == student_id
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.debug(f"Found existing profile for student {student_id}")
                return existing, False

            # Create new profile
            # Validate required fields
            required_fields = {
                "name",
                "grade",
                "exam_target",
                "learning_style",
                "knowledge_level",
            }
            provided_fields = set(defaults.keys())
            missing_fields = required_fields - provided_fields

            if missing_fields:
                raise ValueError(
                    f"Missing required fields for profile creation: {missing_fields}"
                )

            # Create profile with student_id
            profile_data = {"student_id": student_id, **defaults}
            profile = await self.create(**profile_data)

            logger.info(f"Created new profile for student {student_id}")
            return profile, True

        except SQLAlchemyError as e:
            logger.error(f"Error in get_or_create for student {student_id}: {str(e)}")
            await self.session.rollback()
            raise

    async def get_by_student_id(
        self, student_id: str
    ) -> Optional[LearningPathStudentProfile]:
        """
        Get student profile by student ID.

        Args:
            student_id: Unique student identifier

        Returns:
            LearningPathStudentProfile or None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return await self.get_by_field("student_id", student_id)

    async def get_with_learning_paths(
        self, student_id: str
    ) -> Optional[LearningPathStudentProfile]:
        """
        Get student profile with all learning paths eager-loaded.

        Args:
            student_id: Unique student identifier

        Returns:
            LearningPathStudentProfile with learning_paths loaded or None

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            result = await self.session.execute(
                select(LearningPathStudentProfile)
                .options(selectinload(LearningPathStudentProfile.learning_paths))
                .where(LearningPathStudentProfile.student_id == student_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting profile with paths for student {student_id}: {str(e)}"
            )
            raise

    async def update_learning_preferences(
        self,
        student_id: str,
        learning_style: Optional[str] = None,
        knowledge_level: Optional[str] = None,
        interests: Optional[List[str]] = None,
        goals: Optional[List[str]] = None,
        available_time: Optional[int] = None,
    ) -> Optional[LearningPathStudentProfile]:
        """
        Update student's learning preferences.

        Args:
            student_id: Unique student identifier
            learning_style: New learning style (optional)
            knowledge_level: New knowledge level (optional)
            interests: Updated interests list (optional)
            goals: Updated goals list (optional)
            available_time: New available time in minutes (optional)

        Returns:
            Updated profile or None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Get current profile
            profile = await self.get_by_student_id(student_id)
            if not profile:
                logger.warning(f"Profile not found for student {student_id}")
                return None

            # Build update dict with only provided values
            update_data: Dict[str, Any] = {}
            if learning_style is not None:
                update_data["learning_style"] = learning_style
            if knowledge_level is not None:
                update_data["knowledge_level"] = knowledge_level
            if interests is not None:
                update_data["interests"] = interests
            if goals is not None:
                update_data["goals"] = goals
            if available_time is not None:
                update_data["available_time"] = available_time

            if not update_data:
                logger.debug("No updates provided, returning current profile")
                return profile

            # Update using primary key (student_id is primary key)
            await self.session.execute(
                select(LearningPathStudentProfile)
                .where(LearningPathStudentProfile.student_id == student_id)
            )

            for key, value in update_data.items():
                setattr(profile, key, value)

            await self.session.flush()
            await self.session.refresh(profile)

            logger.info(f"Updated learning preferences for student {student_id}")
            return profile

        except SQLAlchemyError as e:
            logger.error(
                f"Error updating preferences for student {student_id}: {str(e)}"
            )
            await self.session.rollback()
            raise
