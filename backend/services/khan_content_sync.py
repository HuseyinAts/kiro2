"""
Task 98.2 & 98.3: Khan Academy Content & Progress Synchronization
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from services.khan_academy_client import (
    KhanAcademyClient,
    get_khan_client,
    KhanContentMetadata,
    KhanUserProgress,
    KhanSubject,
    KhanContentType,
)

logger = logging.getLogger(__name__)


class KhanContentSyncService:
    """
    Task 98.2: Turkish Content Synchronization

    - Fetch Turkish content from Khan Academy
    - Filter and validate content
    - Store in local database
    - Schedule regular updates
    """

    def __init__(self, db: AsyncSession, use_mock: bool = False):
        self.db = db
        self.khan_client = get_khan_client(use_mock=use_mock)

    async def sync_turkish_content(
        self, subjects: Optional[List[KhanSubject]] = None
    ) -> Dict[str, int]:
        """
        Task 98.2: Sync Turkish content from Khan Academy

        Fetches all Turkish content and stores locally
        """
        from models.khan_content import KhanContent

        stats = {
            "total_fetched": 0,
            "new_content": 0,
            "updated_content": 0,
            "errors": 0,
        }

        # Default: sync all subjects
        if subjects is None:
            subjects = list(KhanSubject)

        logger.info(
            f"[KHAN SYNC] Starting Turkish content sync for {len(subjects)} subjects..."
        )

        for subject in subjects:
            try:
                # Fetch videos
                videos = await self.khan_client.get_turkish_content(
                    subject=subject, content_type=KhanContentType.VIDEO, limit=100
                )

                # FIX N+1: Batch save all videos without committing
                for video in videos:
                    try:
                        is_new = await self._save_content(video, commit=False)
                        stats["total_fetched"] += 1

                        if is_new:
                            stats["new_content"] += 1
                        else:
                            stats["updated_content"] += 1

                    except Exception as e:
                        logger.warning(
                            f"Failed to save content {video.content_id}: {e}"
                        )
                        stats["errors"] += 1
                        continue

                # Fetch exercises
                exercises = await self.khan_client.get_turkish_content(
                    subject=subject, content_type=KhanContentType.EXERCISE, limit=100
                )

                # FIX N+1: Batch save all exercises without committing
                for exercise in exercises:
                    try:
                        is_new = await self._save_content(exercise, commit=False)
                        stats["total_fetched"] += 1

                        if is_new:
                            stats["new_content"] += 1
                        else:
                            stats["updated_content"] += 1

                    except Exception as e:
                        logger.warning(
                            f"Failed to save content {exercise.content_id}: {e}"
                        )
                        stats["errors"] += 1
                        continue

                # FIX N+1: Single commit per subject instead of per item
                await self.db.commit()

                logger.info(
                    f"[KHAN SYNC] Completed {subject.value}: fetched {len(videos)} videos, {len(exercises)} exercises"
                )

            except Exception as e:
                logger.error(f"[KHAN SYNC] Failed to sync {subject.value}: {e}")
                stats["errors"] += 1
                # Rollback on error to avoid partial commits
                await self.db.rollback()
                continue

        logger.info(f"[KHAN SYNC] Completed. Stats: {stats}")
        return stats

    async def _save_content(self, content: KhanContentMetadata, commit: bool = True) -> bool:
        """
        Save content to database

        Args:
            content: Content metadata to save
            commit: Whether to commit immediately (default True for backwards compatibility)

        Returns:
            True if new content, False if updated existing
        """
        from models.khan_content import KhanContent

        # Check if exists
        stmt = select(KhanContent).where(
            KhanContent.khan_content_id == content.content_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.title = content.title
            existing.description = content.description
            existing.video_url = content.video_url
            existing.duration_seconds = content.duration_seconds
            existing.thumbnail_url = content.thumbnail_url
            existing.exercise_url = content.exercise_url
            existing.problem_count = content.problem_count
            existing.difficulty_level = content.difficulty_level
            existing.last_synced_at = datetime.now()

            if commit:
                await self.db.commit()
            return False

        else:
            # Create new
            new_content = KhanContent(
                khan_content_id=content.content_id,
                title=content.title,
                description=content.description,
                content_type=content.content_type.value,
                subject=content.subject.value,
                topic=content.topic,
                video_url=content.video_url,
                duration_seconds=content.duration_seconds,
                thumbnail_url=content.thumbnail_url,
                exercise_url=content.exercise_url,
                problem_count=content.problem_count,
                language="tr",
                difficulty_level=content.difficulty_level,
                last_synced_at=datetime.now(),
            )

            self.db.add(new_content)
            if commit:
                await self.db.commit()
            return True

    async def sync_incremental(self, since_days: int = 7) -> Dict[str, int]:
        """
        Incremental sync: Only recently updated content

        For daily scheduled sync
        """
        logger.info(f"[KHAN SYNC] Starting incremental sync (last {since_days} days)")

        # Khan Academy doesn't have "updated_since" filter in API
        # So we do full sync for all subjects (smaller dataset than EBA)
        return await self.sync_turkish_content()

    async def close(self):
        """Close Khan client"""
        await self.khan_client.close()


class KhanProgressSyncService:
    """
    Task 98.3: Progress Synchronization

    Bidirectional sync between Kiro and Khan Academy:
    - Pull user progress from Khan Academy
    - Push local progress to Khan Academy
    - Merge conflicts intelligently
    """

    def __init__(self, db: AsyncSession, use_mock: bool = False):
        self.db = db
        self.khan_client = get_khan_client(use_mock=use_mock)

    async def pull_user_progress(
        self, user_id: str, khan_user_id: str
    ) -> Dict[str, int]:
        """
        Task 98.3: Pull progress from Khan Academy to Kiro

        Fetches user's Khan Academy progress and stores locally
        """
        from models.khan_content import KhanUserProgress as KhanUserProgressModel

        stats = {
            "total_items": 0,
            "new_progress": 0,
            "updated_progress": 0,
            "conflicts": 0,
        }

        try:
            # Fetch progress from Khan Academy
            progress_list = await self.khan_client.get_user_progress(khan_user_id)

            # OPTIMIZATION: Fetch all local progress in one query instead of N queries
            # Before: N database queries (one per progress item)
            # After: 1 database query
            stmt = select(KhanUserProgressModel).where(
                KhanUserProgressModel.user_id == user_id
            )
            result = await self.db.execute(stmt)
            local_progress_dict = {
                p.khan_content_id: p for p in result.scalars().all()
            }

            for progress in progress_list:
                try:
                    # Check if we have local progress (from pre-fetched dict)
                    local_progress = local_progress_dict.get(progress.content_id)

                    if local_progress:
                        # Merge progress (Khan Academy is source of truth)
                        is_conflict = await self._merge_progress(
                            local_progress, progress
                        )

                        if is_conflict:
                            stats["conflicts"] += 1
                        else:
                            stats["updated_progress"] += 1

                    else:
                        # Create new progress entry
                        new_progress = KhanUserProgressModel(
                            user_id=user_id,
                            khan_user_id=khan_user_id,
                            khan_content_id=progress.content_id,
                            content_type=progress.content_type.value,
                            started_at=progress.started_at,
                            completed_at=progress.completed_at,
                            last_accessed=progress.last_accessed,
                            video_seconds_watched=progress.video_seconds_watched,
                            video_completed=progress.video_completed,
                            problems_attempted=progress.problems_attempted,
                            problems_correct=progress.problems_correct,
                            proficiency_level=progress.proficiency_level,
                            energy_points=progress.energy_points,
                            badges_earned=progress.badges_earned,
                            last_synced_at=datetime.now(),
                        )

                        self.db.add(new_progress)
                        stats["new_progress"] += 1

                    stats["total_items"] += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to sync progress for {progress.content_id}: {e}"
                    )
                    continue

            await self.db.commit()
            logger.info(f"[KHAN PROGRESS] Pull sync completed: {stats}")

            return stats

        except Exception as e:
            logger.error(f"[KHAN PROGRESS] Pull sync failed: {e}")
            raise

    async def _merge_progress(
        self, local_progress, remote_progress: KhanUserProgress
    ) -> bool:
        """
        Merge local and remote progress

        Strategy: Khan Academy is source of truth
        But if local is more recent, mark as conflict

        Returns:
            True if conflict detected, False otherwise
        """
        is_conflict = False

        # Check if local is more recent
        if local_progress.last_accessed and remote_progress.last_accessed:
            if local_progress.last_accessed > remote_progress.last_accessed:
                is_conflict = True
                logger.warning(
                    f"[KHAN PROGRESS] Conflict detected for content {remote_progress.content_id}"
                )

        # Update from remote (Khan Academy is source of truth)
        local_progress.started_at = remote_progress.started_at
        local_progress.completed_at = remote_progress.completed_at
        local_progress.last_accessed = remote_progress.last_accessed
        local_progress.video_seconds_watched = remote_progress.video_seconds_watched
        local_progress.video_completed = remote_progress.video_completed
        local_progress.problems_attempted = remote_progress.problems_attempted
        local_progress.problems_correct = remote_progress.problems_correct
        local_progress.proficiency_level = remote_progress.proficiency_level
        local_progress.energy_points = remote_progress.energy_points
        local_progress.badges_earned = remote_progress.badges_earned
        local_progress.last_synced_at = datetime.now()

        return is_conflict

    async def push_user_progress(
        self, user_id: str, khan_user_id: str, content_id: str
    ) -> bool:
        """
        Task 98.3: Push local progress to Khan Academy

        Bidirectional sync: Send Kiro progress to Khan Academy
        """
        from models.khan_content import KhanUserProgress as KhanUserProgressModel

        try:
            # Get local progress
            stmt = select(KhanUserProgressModel).where(
                and_(
                    KhanUserProgressModel.user_id == user_id,
                    KhanUserProgressModel.khan_content_id == content_id,
                )
            )
            result = await self.db.execute(stmt)
            local_progress = result.scalar_one_or_none()

            if not local_progress:
                logger.warning(
                    f"[KHAN PROGRESS] No local progress found for {content_id}"
                )
                return False

            # Prepare progress data for Khan Academy API
            progress_data = {
                "seconds_watched": local_progress.video_seconds_watched,
                "completed": local_progress.video_completed,
                "total_done": local_progress.problems_attempted,
                "total_correct": local_progress.problems_correct,
                "points_earned": local_progress.energy_points,
            }

            # Push to Khan Academy
            success = await self.khan_client.update_user_progress(
                khan_user_id=khan_user_id,
                content_id=content_id,
                progress_data=progress_data,
            )

            if success:
                # Update last sync time
                local_progress.last_synced_at = datetime.now()
                await self.db.commit()

                logger.info(
                    f"[KHAN PROGRESS] Successfully pushed progress for {content_id}"
                )

            return success

        except Exception as e:
            logger.error(f"[KHAN PROGRESS] Push failed for {content_id}: {e}")
            return False

    async def sync_bidirectional(
        self, user_id: str, khan_user_id: str
    ) -> Dict[str, Any]:
        """
        Task 98.3: Bidirectional progress sync

        1. Pull from Khan Academy (Khan is source of truth)
        2. Push local-only progress to Khan Academy
        """
        from models.khan_content import KhanUserProgress as KhanUserProgressModel

        # Step 1: Pull from Khan Academy
        pull_stats = await self.pull_user_progress(user_id, khan_user_id)

        # Step 2: Find local progress that hasn't been synced to Khan
        stmt = select(KhanUserProgressModel).where(
            and_(
                KhanUserProgressModel.user_id == user_id,
                KhanUserProgressModel.last_synced_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        local_only = result.scalars().all()

        push_stats = {"total_items": len(local_only), "pushed": 0, "failed": 0}

        for progress in local_only:
            success = await self.push_user_progress(
                user_id=user_id,
                khan_user_id=khan_user_id,
                content_id=progress.khan_content_id,
            )

            if success:
                push_stats["pushed"] += 1
            else:
                push_stats["failed"] += 1

        return {"pull": pull_stats, "push": push_stats}

    async def close(self):
        """Close Khan client"""
        await self.khan_client.close()


# Scheduled task for automatic sync
async def scheduled_khan_sync(db: AsyncSession, use_mock: bool = False):
    """
    Daily Khan Academy content sync

    Called by Celery Beat or APScheduler
    """
    logger.info("[SCHEDULED] Starting Khan Academy sync...")

    sync_service = KhanContentSyncService(db, use_mock=use_mock)

    try:
        stats = await sync_service.sync_incremental(since_days=7)

        logger.info(f"[SCHEDULED] Khan sync completed: {stats}")
        return stats

    except Exception as e:
        logger.error(f"[SCHEDULED] Khan sync failed: {e}")
        raise

    finally:
        await sync_service.close()
