"""
Learning Path Repository
P0 Fix: Database persistence layer for Learning Path system

Provides CRUD operations for:
- Student profiles
- Learning paths
- Completion status
- Quiz submissions
- Progress tracking
- Fallback videos
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models.learning_path_models import (
    StudentProfile,
    LearningPath,
    TopicCompletion,
    TopicProgress,
    QuizSubmission,
    FallbackVideo,
)

logger = logging.getLogger(__name__)


class LearningPathRepository:
    """Repository for Learning Path database operations"""

    # ==================== Student Profile Operations ====================

    async def create_student_profile(
        self, session: AsyncSession, profile_data: Dict[str, Any]
    ) -> StudentProfile:
        """Create new student profile"""
        try:
            profile = StudentProfile(**profile_data)
            session.add(profile)
            await session.commit()
            await session.refresh(profile)

            logger.info(f"Created student profile: {profile.student_id}")
            return profile
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Duplicate student profile: {profile_data.get('student_id')}")
            raise ValueError(f"Student profile already exists") from e
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating student profile: {e}")
            raise

    async def get_student_profile(
        self, session: AsyncSession, student_id: str
    ) -> Optional[StudentProfile]:
        """Get student profile by ID"""
        try:
            result = await session.execute(
                select(StudentProfile).where(StudentProfile.student_id == student_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching student profile {student_id}: {e}")
            raise

    async def update_student_profile(
        self, session: AsyncSession, student_id: str, update_data: Dict[str, Any]
    ) -> Optional[StudentProfile]:
        """Update student profile"""
        try:
            update_data["updated_at"] = datetime.now()

            await session.execute(
                update(StudentProfile)
                .where(StudentProfile.student_id == student_id)
                .values(**update_data)
            )
            await session.commit()

            return await self.get_student_profile(session, student_id)
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating student profile {student_id}: {e}")
            raise

    async def delete_student_profile(
        self, session: AsyncSession, student_id: str
    ) -> bool:
        """Delete student profile (cascade deletes related data)"""
        try:
            result = await session.execute(
                delete(StudentProfile).where(StudentProfile.student_id == student_id)
            )
            await session.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted student profile: {student_id}")
            return deleted
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting student profile {student_id}: {e}")
            raise

    # ==================== Learning Path Operations ====================

    async def create_learning_path(
        self, session: AsyncSession, path_data: Dict[str, Any]
    ) -> LearningPath:
        """Create new learning path"""
        try:
            learning_path = LearningPath(**path_data)
            session.add(learning_path)
            await session.commit()
            await session.refresh(learning_path)

            logger.info(
                f"Created learning path: {learning_path.path_id} for student {learning_path.student_id}"
            )
            return learning_path
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Duplicate learning path or invalid student_id")
            raise ValueError(f"Learning path creation failed") from e
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating learning path: {e}")
            raise

    async def get_learning_path(
        self, session: AsyncSession, path_id: str
    ) -> Optional[LearningPath]:
        """Get learning path by ID"""
        try:
            result = await session.execute(
                select(LearningPath).where(LearningPath.path_id == path_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching learning path {path_id}: {e}")
            raise

    async def get_student_learning_paths(
        self, session: AsyncSession, student_id: str, subject: Optional[str] = None
    ) -> List[LearningPath]:
        """Get all learning paths for a student"""
        try:
            query = select(LearningPath).where(LearningPath.student_id == student_id)

            if subject:
                query = query.where(LearningPath.subject == subject)

            query = query.order_by(LearningPath.created_at.desc())

            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching learning paths for student {student_id}: {e}")
            raise

    async def update_learning_path_progress(
        self,
        session: AsyncSession,
        path_id: str,
        completed_modules: int,
        completed_topics: int,
    ) -> Optional[LearningPath]:
        """Update learning path progress"""
        try:
            # Get current path to calculate overall progress
            path = await self.get_learning_path(session, path_id)
            if not path:
                return None

            overall_progress = 0.0
            if path.total_topics > 0:
                overall_progress = (completed_topics / path.total_topics) * 100

            await session.execute(
                update(LearningPath)
                .where(LearningPath.path_id == path_id)
                .values(
                    completed_modules=completed_modules,
                    completed_topics=completed_topics,
                    overall_progress=overall_progress,
                    updated_at=datetime.now(),
                )
            )
            await session.commit()

            return await self.get_learning_path(session, path_id)
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating learning path progress {path_id}: {e}")
            raise

    # ==================== Topic Completion Operations ====================

    async def set_topic_completion(
        self, session: AsyncSession, student_id: str, node_id: str, completed: bool
    ) -> TopicCompletion:
        """Set topic completion status (upsert)"""
        try:
            # Check if exists
            result = await session.execute(
                select(TopicCompletion).where(
                    and_(
                        TopicCompletion.student_id == student_id,
                        TopicCompletion.node_id == node_id,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update
                await session.execute(
                    update(TopicCompletion)
                    .where(
                        and_(
                            TopicCompletion.student_id == student_id,
                            TopicCompletion.node_id == node_id,
                        )
                    )
                    .values(
                        completed=completed,
                        completion_date=datetime.now() if completed else None,
                        updated_at=datetime.now(),
                    )
                )
                await session.commit()
                return await self.get_topic_completion(session, student_id, node_id)
            else:
                # Insert
                completion = TopicCompletion(
                    student_id=student_id,
                    node_id=node_id,
                    completed=completed,
                    completion_date=datetime.now() if completed else None,
                )
                session.add(completion)
                await session.commit()
                await session.refresh(completion)
                return completion
        except Exception as e:
            await session.rollback()
            logger.error(f"Error setting topic completion {student_id}/{node_id}: {e}")
            raise

    async def get_topic_completion(
        self, session: AsyncSession, student_id: str, node_id: str
    ) -> Optional[TopicCompletion]:
        """Get topic completion status"""
        try:
            result = await session.execute(
                select(TopicCompletion).where(
                    and_(
                        TopicCompletion.student_id == student_id,
                        TopicCompletion.node_id == node_id,
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching topic completion: {e}")
            raise

    async def get_student_completions(
        self, session: AsyncSession, student_id: str
    ) -> Dict[str, bool]:
        """Get all topic completions for a student"""
        try:
            result = await session.execute(
                select(TopicCompletion).where(TopicCompletion.student_id == student_id)
            )
            completions = result.scalars().all()

            return {c.node_id: c.completed for c in completions}
        except Exception as e:
            logger.error(f"Error fetching student completions {student_id}: {e}")
            raise

    async def batch_set_completions(
        self, session: AsyncSession, student_id: str, completions: Dict[str, bool]
    ) -> int:
        """Batch set topic completions"""
        try:
            count = 0
            for node_id, completed in completions.items():
                await self.set_topic_completion(session, student_id, node_id, completed)
                count += 1

            logger.info(f"Batch updated {count} completions for student {student_id}")
            return count
        except Exception as e:
            logger.error(f"Error batch setting completions: {e}")
            raise

    # ==================== Topic Progress Operations ====================

    async def update_topic_progress(
        self,
        session: AsyncSession,
        student_id: str,
        node_id: str,
        progress: int,
        time_spent: int,
        completed: bool,
    ) -> TopicProgress:
        """Update topic progress (creates or updates)"""
        try:
            # Check if exists
            result = await session.execute(
                select(TopicProgress).where(
                    and_(
                        TopicProgress.student_id == student_id,
                        TopicProgress.node_id == node_id,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update
                await session.execute(
                    update(TopicProgress)
                    .where(TopicProgress.id == existing.id)
                    .values(
                        progress=progress,
                        time_spent=time_spent,
                        completed=completed,
                        updated_at=datetime.now(),
                    )
                )
                await session.commit()

                result = await session.execute(
                    select(TopicProgress).where(TopicProgress.id == existing.id)
                )
                return result.scalar_one()
            else:
                # Insert
                progress_obj = TopicProgress(
                    student_id=student_id,
                    node_id=node_id,
                    progress=progress,
                    time_spent=time_spent,
                    completed=completed,
                )
                session.add(progress_obj)
                await session.commit()
                await session.refresh(progress_obj)
                return progress_obj
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating topic progress {student_id}/{node_id}: {e}")
            raise

    async def get_student_progress(
        self, session: AsyncSession, student_id: str
    ) -> List[TopicProgress]:
        """Get all progress for a student"""
        try:
            result = await session.execute(
                select(TopicProgress)
                .where(TopicProgress.student_id == student_id)
                .order_by(TopicProgress.updated_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching student progress {student_id}: {e}")
            raise

    # ==================== Quiz Submission Operations ====================

    async def create_quiz_submission(
        self, session: AsyncSession, submission_data: Dict[str, Any]
    ) -> QuizSubmission:
        """Create quiz submission"""
        try:
            submission = QuizSubmission(**submission_data)
            session.add(submission)
            await session.commit()
            await session.refresh(submission)

            logger.info(
                f"Created quiz submission for student {submission.student_id}, quiz {submission.quiz_id}"
            )
            return submission
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating quiz submission: {e}")
            raise

    async def get_student_quiz_submissions(
        self, session: AsyncSession, student_id: str, quiz_id: Optional[str] = None
    ) -> List[QuizSubmission]:
        """Get quiz submissions for a student"""
        try:
            query = select(QuizSubmission).where(
                QuizSubmission.student_id == student_id
            )

            if quiz_id:
                query = query.where(QuizSubmission.quiz_id == quiz_id)

            query = query.order_by(QuizSubmission.submitted_at.desc())

            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching quiz submissions: {e}")
            raise

    # ==================== Fallback Video Operations ====================

    async def create_fallback_video(
        self, session: AsyncSession, video_data: Dict[str, Any]
    ) -> FallbackVideo:
        """Create fallback video"""
        try:
            video = FallbackVideo(**video_data)
            session.add(video)
            await session.commit()
            await session.refresh(video)

            logger.info(f"Created fallback video: {video.video_id}")
            return video
        except IntegrityError as e:
            await session.rollback()
            logger.warning(f"Duplicate fallback video: {video_data.get('video_id')}")
            raise ValueError("Fallback video already exists") from e
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating fallback video: {e}")
            raise

    async def get_fallback_videos(
        self,
        session: AsyncSession,
        subject: str,
        topic: Optional[str] = None,
        limit: int = 10,
    ) -> List[FallbackVideo]:
        """Get fallback videos for subject/topic"""
        try:
            query = select(FallbackVideo).where(
                and_(
                    FallbackVideo.subject == subject,
                    FallbackVideo.is_example == True,
                    FallbackVideo.is_accessible == True,
                )
            )

            if topic:
                query = query.where(FallbackVideo.topic == topic)

            query = query.order_by(FallbackVideo.final_score.desc()).limit(limit)

            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching fallback videos: {e}")
            raise

    async def batch_create_fallback_videos(
        self, session: AsyncSession, videos: List[Dict[str, Any]]
    ) -> int:
        """Batch create fallback videos"""
        try:
            count = 0
            for video_data in videos:
                try:
                    video = FallbackVideo(**video_data)
                    session.add(video)
                    count += 1
                except Exception as e:
                    logger.warning(
                        f"Skipping duplicate video: {video_data.get('video_id')}"
                    )

            await session.commit()
            logger.info(f"Batch created {count} fallback videos")
            return count
        except Exception as e:
            await session.rollback()
            logger.error(f"Error batch creating fallback videos: {e}")
            raise


# Singleton instance
learning_path_repository = LearningPathRepository()
