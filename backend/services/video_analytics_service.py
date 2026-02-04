"""
Task 100: Video Analytics Service

Service for video watch tracking, completion tracking, notes, and bookmarks
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import asyncio

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.video_analytics import (
    VideoWatchSession,
    VideoCompletionMilestone,
    VideoNote,
    VideoBookmark,
    VideoAnalyticsSummary,
)


class VideoAnalyticsService:
    """
    Task 100: Video Analytics Service

    Handles all video watch tracking, notes, and bookmarks
    """

    # Completion milestone thresholds
    MILESTONES = [25, 50, 75, 100]

    # Auto-completion threshold (90% watched = completed)
    AUTO_COMPLETION_THRESHOLD = 90.0

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Task 100.1: Watch Time Tracking
    # ============================================================

    async def start_watch_session(
        self, user_id: UUID, video_id: str, video_source: str, video_duration: int
    ) -> VideoWatchSession:
        """
        Start a new watch session

        Args:
            user_id: User ID
            video_id: Video identifier
            video_source: Source (youtube, eba, khan, etc.)
            video_duration: Total video duration in seconds

        Returns:
            New VideoWatchSession
        """
        session = VideoWatchSession(
            user_id=user_id,
            video_id=video_id,
            video_source=video_source,
            video_duration=video_duration,
            started_at=datetime.now(),
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def update_watch_progress(
        self, session_id: UUID, current_position: int, playback_speed: float = 1.0
    ) -> VideoWatchSession:
        """
        Update watch progress (called periodically, e.g., every 10 seconds)

        Args:
            session_id: Watch session ID
            current_position: Current video position in seconds
            playback_speed: Current playback speed

        Returns:
            Updated VideoWatchSession
        """
        # Get session
        result = await self.db.execute(
            select(VideoWatchSession).where(VideoWatchSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update last position
        old_position = session.last_position
        session.last_position = current_position
        session.playback_speed = playback_speed
        session.last_updated = datetime.now()

        # Add to watched segments
        if old_position < current_position:
            # User moved forward (normal playback)
            session.watch_duration += current_position - old_position

            # Add segment
            if not session.watched_segments:
                session.watched_segments = []

            session.watched_segments.append(
                {
                    "start": old_position,
                    "end": current_position,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Calculate completion percentage
        if session.video_duration > 0:
            session.completion_percentage = min(
                (current_position / session.video_duration) * 100, 100.0
            )

        # Check for auto-completion
        if (
            session.completion_percentage >= self.AUTO_COMPLETION_THRESHOLD
            and not session.is_completed
        ):
            session.is_completed = True
            session.completed_at = datetime.now()

            # Award 100% milestone
            await self._check_and_award_milestone(
                session.user_id, session.video_id, session.video_source, 100
            )

        await self.db.commit()
        await self.db.refresh(session)

        # Check for other milestones
        await self._check_all_milestones(session)

        return session

    async def record_pause(self, session_id: UUID) -> None:
        """Record a pause event"""
        result = await self.db.execute(
            select(VideoWatchSession).where(VideoWatchSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            session.pause_count += 1
            await self.db.commit()

    async def record_seek(
        self, session_id: UUID, from_position: int, to_position: int
    ) -> None:
        """
        Record a seek event (forward/backward)

        Args:
            session_id: Session ID
            from_position: Position before seek
            to_position: Position after seek
        """
        result = await self.db.execute(
            select(VideoWatchSession).where(VideoWatchSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            session.seek_count += 1
            session.last_position = to_position
            await self.db.commit()

    async def end_watch_session(
        self, session_id: UUID, final_position: int
    ) -> VideoWatchSession:
        """
        End a watch session

        Args:
            session_id: Session ID
            final_position: Final video position

        Returns:
            Completed session
        """
        result = await self.db.execute(
            select(VideoWatchSession).where(VideoWatchSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update final position
        session.last_position = final_position
        session.dropped_at = final_position

        # Calculate final completion percentage
        if session.video_duration > 0:
            session.completion_percentage = min(
                (final_position / session.video_duration) * 100, 100.0
            )

        # Check completion
        if (
            session.completion_percentage >= self.AUTO_COMPLETION_THRESHOLD
            and not session.is_completed
        ):
            session.is_completed = True
            session.completed_at = datetime.now()

        session.last_updated = datetime.now()
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def get_video_engagement_metrics(
        self, video_id: str, video_source: str
    ) -> Dict[str, Any]:
        """
        Get engagement metrics for a specific video

        Returns:
            Dict with average completion, drop-off points, etc.
        """
        # Get all sessions for this video
        result = await self.db.execute(
            select(VideoWatchSession).where(
                and_(
                    VideoWatchSession.video_id == video_id,
                    VideoWatchSession.video_source == video_source,
                )
            )
        )
        sessions = result.scalars().all()

        if not sessions:
            return {
                "total_views": 0,
                "average_completion": 0.0,
                "completion_rate": 0.0,
                "drop_off_points": [],
            }

        # Calculate metrics
        total_views = len(sessions)
        completed_views = sum(1 for s in sessions if s.is_completed)
        average_completion = (
            sum(s.completion_percentage for s in sessions) / total_views
        )

        # Drop-off analysis
        drop_off_positions = [
            s.dropped_at for s in sessions if s.dropped_at and not s.is_completed
        ]
        drop_off_histogram = self._create_drop_off_histogram(drop_off_positions)

        return {
            "total_views": total_views,
            "completed_views": completed_views,
            "completion_rate": (completed_views / total_views) * 100
            if total_views > 0
            else 0.0,
            "average_completion": average_completion,
            "average_watch_time": sum(s.watch_duration for s in sessions) / total_views,
            "drop_off_points": drop_off_histogram,
        }

    def _create_drop_off_histogram(
        self, positions: List[int], bucket_size: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Create histogram of drop-off points

        Args:
            positions: List of drop-off positions in seconds
            bucket_size: Bucket size in seconds (default 30s)

        Returns:
            List of {position: int, count: int}
        """
        if not positions:
            return []

        # Create buckets
        max_position = max(positions)
        buckets = {}

        for pos in positions:
            bucket = (pos // bucket_size) * bucket_size
            buckets[bucket] = buckets.get(bucket, 0) + 1

        # Sort and format
        return [
            {"position": pos, "count": count} for pos, count in sorted(buckets.items())
        ]

    # ============================================================
    # Task 100.2: Completion Milestones
    # ============================================================

    async def _check_all_milestones(self, session: VideoWatchSession) -> None:
        """Check and award all milestones for a session"""
        for milestone in self.MILESTONES:
            if session.completion_percentage >= milestone:
                await self._check_and_award_milestone(
                    session.user_id, session.video_id, session.video_source, milestone
                )

    async def _check_and_award_milestone(
        self, user_id: UUID, video_id: str, video_source: str, milestone: int
    ) -> Optional[VideoCompletionMilestone]:
        """
        Check if milestone exists, if not create it

        Args:
            user_id: User ID
            video_id: Video ID
            video_source: Video source
            milestone: Milestone percentage (25, 50, 75, 100)

        Returns:
            VideoCompletionMilestone if newly created, None if already exists
        """
        # Check if already achieved
        result = await self.db.execute(
            select(VideoCompletionMilestone).where(
                and_(
                    VideoCompletionMilestone.user_id == user_id,
                    VideoCompletionMilestone.video_id == video_id,
                    VideoCompletionMilestone.milestone_percentage == milestone,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return None

        # Create new milestone
        new_milestone = VideoCompletionMilestone(
            user_id=user_id,
            video_id=video_id,
            video_source=video_source,
            milestone_percentage=milestone,
            achieved_at=datetime.now(),
        )

        self.db.add(new_milestone)
        await self.db.commit()
        await self.db.refresh(new_milestone)

        return new_milestone

    async def get_user_milestones(
        self, user_id: UUID, video_id: Optional[str] = None
    ) -> List[VideoCompletionMilestone]:
        """
        Get all milestones for a user

        Args:
            user_id: User ID
            video_id: Optional video ID filter

        Returns:
            List of VideoCompletionMilestone
        """
        query = select(VideoCompletionMilestone).where(
            VideoCompletionMilestone.user_id == user_id
        )

        if video_id:
            query = query.where(VideoCompletionMilestone.video_id == video_id)

        query = query.order_by(desc(VideoCompletionMilestone.achieved_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============================================================
    # Task 100.3: Note-Taking Integration
    # ============================================================

    async def create_note(
        self,
        user_id: UUID,
        video_id: str,
        video_source: str,
        content: str,
        timestamp: int,
        session_id: Optional[UUID] = None,
        is_important: bool = False,
        tags: Optional[List[str]] = None,
        video_caption: Optional[str] = None,
    ) -> VideoNote:
        """
        Create a timestamped note

        Args:
            user_id: User ID
            video_id: Video ID
            video_source: Video source
            content: Note content
            timestamp: Video position when note was taken (seconds)
            session_id: Optional session ID
            is_important: Is this an important/starred note
            tags: Optional tags
            video_caption: Optional video caption at that timestamp

        Returns:
            New VideoNote
        """
        note = VideoNote(
            user_id=user_id,
            video_id=video_id,
            video_source=video_source,
            session_id=session_id,
            content=content,
            timestamp=timestamp,
            is_important=is_important,
            tags=tags or [],
            video_caption=video_caption,
        )

        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)

        return note

    async def update_note(
        self,
        note_id: UUID,
        content: Optional[str] = None,
        is_important: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> VideoNote:
        """Update a note"""
        result = await self.db.execute(select(VideoNote).where(VideoNote.id == note_id))
        note = result.scalar_one_or_none()

        if not note:
            raise ValueError(f"Note {note_id} not found")

        if content is not None:
            note.content = content
        if is_important is not None:
            note.is_important = is_important
        if tags is not None:
            note.tags = tags

        note.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(note)

        return note

    async def delete_note(self, note_id: UUID) -> None:
        """Delete a note"""
        result = await self.db.execute(select(VideoNote).where(VideoNote.id == note_id))
        note = result.scalar_one_or_none()

        if note:
            await self.db.delete(note)
            await self.db.commit()

    async def get_video_notes(
        self, user_id: UUID, video_id: str, video_source: str
    ) -> List[VideoNote]:
        """
        Get all notes for a video

        Returns notes ordered by timestamp
        """
        result = await self.db.execute(
            select(VideoNote)
            .where(
                and_(
                    VideoNote.user_id == user_id,
                    VideoNote.video_id == video_id,
                    VideoNote.video_source == video_source,
                )
            )
            .order_by(VideoNote.timestamp)
        )
        return result.scalars().all()

    async def search_notes(
        self,
        user_id: UUID,
        query: str,
        video_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[VideoNote]:
        """
        Search user's notes

        Args:
            user_id: User ID
            query: Search query (searches in content)
            video_id: Optional video ID filter
            tags: Optional tag filter

        Returns:
            List of matching VideoNote
        """
        conditions = [VideoNote.user_id == user_id]

        # Content search
        if query:
            conditions.append(VideoNote.content.ilike(f"%{query}%"))

        # Video filter
        if video_id:
            conditions.append(VideoNote.video_id == video_id)

        # Tag filter
        if tags:
            for tag in tags:
                conditions.append(VideoNote.tags.contains([tag]))

        result = await self.db.execute(
            select(VideoNote)
            .where(and_(*conditions))
            .order_by(desc(VideoNote.created_at))
        )
        return result.scalars().all()

    # ============================================================
    # Task 100.4: Bookmark Management
    # ============================================================

    async def create_bookmark(
        self,
        user_id: UUID,
        video_id: str,
        video_source: str,
        timestamp: int,
        title: str,
        description: Optional[str] = None,
        session_id: Optional[UUID] = None,
        bookmark_type: str = "manual",
        is_public: bool = False,
    ) -> VideoBookmark:
        """
        Create a bookmark

        Args:
            user_id: User ID
            video_id: Video ID
            video_source: Video source
            timestamp: Video position (seconds)
            title: Bookmark title
            description: Optional description
            session_id: Optional session ID
            bookmark_type: Type (manual, key_moment, auto_generated)
            is_public: Is this bookmark public

        Returns:
            New VideoBookmark
        """
        bookmark = VideoBookmark(
            user_id=user_id,
            video_id=video_id,
            video_source=video_source,
            session_id=session_id,
            timestamp=timestamp,
            title=title,
            description=description,
            bookmark_type=bookmark_type,
            is_public=is_public,
        )

        self.db.add(bookmark)
        await self.db.commit()
        await self.db.refresh(bookmark)

        return bookmark

    async def update_bookmark(
        self,
        bookmark_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> VideoBookmark:
        """Update a bookmark"""
        result = await self.db.execute(
            select(VideoBookmark).where(VideoBookmark.id == bookmark_id)
        )
        bookmark = result.scalar_one_or_none()

        if not bookmark:
            raise ValueError(f"Bookmark {bookmark_id} not found")

        if title is not None:
            bookmark.title = title
        if description is not None:
            bookmark.description = description
        if is_public is not None:
            bookmark.is_public = is_public

        bookmark.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(bookmark)

        return bookmark

    async def delete_bookmark(self, bookmark_id: UUID) -> None:
        """Delete a bookmark"""
        result = await self.db.execute(
            select(VideoBookmark).where(VideoBookmark.id == bookmark_id)
        )
        bookmark = result.scalar_one_or_none()

        if bookmark:
            await self.db.delete(bookmark)
            await self.db.commit()

    async def get_video_bookmarks(
        self,
        user_id: UUID,
        video_id: str,
        video_source: str,
        include_public: bool = False,
    ) -> List[VideoBookmark]:
        """
        Get bookmarks for a video

        Args:
            user_id: User ID
            video_id: Video ID
            video_source: Video source
            include_public: Include public bookmarks from other users

        Returns:
            List of VideoBookmark ordered by timestamp
        """
        if include_public:
            # User's bookmarks + public bookmarks
            conditions = or_(
                and_(
                    VideoBookmark.user_id == user_id,
                    VideoBookmark.video_id == video_id,
                    VideoBookmark.video_source == video_source,
                ),
                and_(
                    VideoBookmark.video_id == video_id,
                    VideoBookmark.video_source == video_source,
                    VideoBookmark.is_public == True,
                ),
            )
        else:
            # User's bookmarks only
            conditions = and_(
                VideoBookmark.user_id == user_id,
                VideoBookmark.video_id == video_id,
                VideoBookmark.video_source == video_source,
            )

        result = await self.db.execute(
            select(VideoBookmark).where(conditions).order_by(VideoBookmark.timestamp)
        )
        return result.scalars().all()

    async def increment_bookmark_share(self, bookmark_id: UUID) -> None:
        """Increment share count for a bookmark"""
        result = await self.db.execute(
            select(VideoBookmark).where(VideoBookmark.id == bookmark_id)
        )
        bookmark = result.scalar_one_or_none()

        if bookmark:
            bookmark.share_count += 1
            await self.db.commit()

    # ============================================================
    # Analytics Summary
    # ============================================================

    async def generate_daily_summary(
        self, user_id: UUID, date: datetime
    ) -> VideoAnalyticsSummary:
        """Generate daily analytics summary for a user"""
        period_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)

        return await self._generate_summary(user_id, "daily", period_start, period_end)

    async def _generate_summary(
        self,
        user_id: UUID,
        period_type: str,
        period_start: datetime,
        period_end: datetime,
    ) -> VideoAnalyticsSummary:
        """Generate analytics summary for a period"""
        # Get all sessions in period
        result = await self.db.execute(
            select(VideoWatchSession).where(
                and_(
                    VideoWatchSession.user_id == user_id,
                    VideoWatchSession.started_at >= period_start,
                    VideoWatchSession.started_at < period_end,
                )
            )
        )
        sessions = result.scalars().all()

        if not sessions:
            return VideoAnalyticsSummary(
                user_id=user_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
            )

        # Calculate metrics
        total_videos = len(sessions)
        total_watch_time = sum(s.watch_duration for s in sessions)
        total_completed = sum(1 for s in sessions if s.is_completed)
        avg_completion = sum(s.completion_percentage for s in sessions) / total_videos

        # Source breakdown
        source_breakdown = {}
        for session in sessions:
            source_breakdown[session.video_source] = (
                source_breakdown.get(session.video_source, 0) + 1
            )

        # Get notes and bookmarks count
        notes_result = await self.db.execute(
            select(func.count(VideoNote.id)).where(
                and_(
                    VideoNote.user_id == user_id,
                    VideoNote.created_at >= period_start,
                    VideoNote.created_at < period_end,
                )
            )
        )
        total_notes = notes_result.scalar() or 0

        bookmarks_result = await self.db.execute(
            select(func.count(VideoBookmark.id)).where(
                and_(
                    VideoBookmark.user_id == user_id,
                    VideoBookmark.created_at >= period_start,
                    VideoBookmark.created_at < period_end,
                )
            )
        )
        total_bookmarks = bookmarks_result.scalar() or 0

        # Average playback speed
        avg_speed = sum(s.playback_speed for s in sessions) / total_videos

        # Check if already exists
        existing_result = await self.db.execute(
            select(VideoAnalyticsSummary).where(
                and_(
                    VideoAnalyticsSummary.user_id == user_id,
                    VideoAnalyticsSummary.period_type == period_type,
                    VideoAnalyticsSummary.period_start == period_start,
                )
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.total_videos_watched = total_videos
            existing.total_watch_time = total_watch_time
            existing.total_videos_completed = total_completed
            existing.average_completion_rate = avg_completion
            existing.total_notes = total_notes
            existing.total_bookmarks = total_bookmarks
            existing.average_playback_speed = avg_speed
            existing.source_breakdown = source_breakdown
            existing.updated_at = datetime.now()

            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new
            summary = VideoAnalyticsSummary(
                user_id=user_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                total_videos_watched=total_videos,
                total_watch_time=total_watch_time,
                total_videos_completed=total_completed,
                average_completion_rate=avg_completion,
                total_notes=total_notes,
                total_bookmarks=total_bookmarks,
                average_playback_speed=avg_speed,
                source_breakdown=source_breakdown,
            )

            self.db.add(summary)
            await self.db.commit()
            await self.db.refresh(summary)

            return summary
