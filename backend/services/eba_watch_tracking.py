"""
Task 97.4: EBA Video İzleme Takibi
Watch progress tracking, completion status, analytics
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel
import uuid

from models.database import EBAVideo
from models.eba_video import EBAVideoWatch

logger = logging.getLogger(__name__)


class WatchSessionStart(BaseModel):
    """İzleme oturumu başlatma"""

    video_id: str  # EBA video ID
    user_id: uuid.UUID


class WatchProgressUpdate(BaseModel):
    """İzleme ilerlemesi güncelleme"""

    session_id: uuid.UUID
    current_time: int  # seconds
    duration: int  # total video duration


class WatchSessionEnd(BaseModel):
    """İzleme oturumu sonlandırma"""

    session_id: uuid.UUID
    final_time: int  # seconds
    completed: bool


class WatchAnalytics(BaseModel):
    """İzleme analitikleri"""

    total_watch_time: int  # seconds
    completed_videos: int
    in_progress_videos: int
    completion_rate: float  # percentage
    average_watch_percentage: float
    total_sessions: int


class EBAWatchTrackingService:
    """
    Task 97.4: İzleme Takibi

    - Watch progress tracking (video kaçıncı saniyede?)
    - Completion status (video tamamlandı mı?)
    - Analytics integration (toplam izleme süresi, tamamlama oranı)
    - Resume functionality (kaldığın yerden devam et)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_watch_session(
        self, user_id: uuid.UUID, eba_video_id: str
    ) -> uuid.UUID:
        """
        Yeni izleme oturumu başlat

        Returns:
            session_id: Izleme oturumu ID'si
        """
        # Get video from database
        stmt = select(EBAVideo).where(EBAVideo.eba_video_id == eba_video_id)
        result = await self.db.execute(stmt)
        video = result.scalar_one_or_none()

        if not video:
            raise ValueError(f"EBA video not found: {eba_video_id}")

        # Check if there's an existing incomplete session
        stmt = (
            select(EBAVideoWatch)
            .where(
                and_(
                    EBAVideoWatch.user_id == user_id,
                    EBAVideoWatch.eba_video_id == video.id,
                    EBAVideoWatch.completed == False,
                )
            )
            .order_by(EBAVideoWatch.created_at.desc())
        )

        result = await self.db.execute(stmt)
        existing_session = result.scalar_one_or_none()

        if existing_session:
            # Resume existing session
            logger.info(
                f"[WATCH] Resuming session {existing_session.id} at {existing_session.last_position}s"
            )
            return existing_session.id

        # Create new session
        session = EBAVideoWatch(
            user_id=user_id,
            eba_video_id=video.id,
            session_start=datetime.now(),
            last_position=0,
            completed=False,
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            f"[WATCH] Started new session {session.id} for video {eba_video_id}"
        )
        return session.id

    async def update_watch_progress(
        self, session_id: uuid.UUID, current_time: int, video_duration: int
    ) -> Dict[str, Any]:
        """
        İzleme ilerlemesini güncelle

        Args:
            session_id: İzleme oturumu ID
            current_time: Geçerli video pozisyonu (saniye)
            video_duration: Toplam video süresi (saniye)

        Returns:
            Updated session info with completion status
        """
        # Get session
        stmt = select(EBAVideoWatch).where(EBAVideoWatch.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Watch session not found: {session_id}")

        # Update progress
        session.last_position = current_time
        session.last_updated = datetime.now()

        # Calculate watch percentage
        watch_percentage = (
            (current_time / video_duration) * 100 if video_duration > 0 else 0
        )
        session.watch_percentage = watch_percentage

        # Check if completed (watched >= 90% of video)
        if watch_percentage >= 90 and not session.completed:
            session.completed = True
            session.completed_at = datetime.now()
            logger.info(
                f"[WATCH] Session {session_id} completed! (watched {watch_percentage:.1f}%)"
            )

        await self.db.commit()

        return {
            "session_id": str(session_id),
            "current_time": current_time,
            "watch_percentage": watch_percentage,
            "completed": session.completed,
        }

    async def end_watch_session(
        self, session_id: uuid.UUID, final_time: int
    ) -> Dict[str, Any]:
        """
        İzleme oturumunu sonlandır
        """
        stmt = select(EBAVideoWatch).where(EBAVideoWatch.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Watch session not found: {session_id}")

        # Update final position
        session.last_position = final_time
        session.session_end = datetime.now()

        # Calculate total watch time for this session
        if session.session_start and session.session_end:
            total_time = (session.session_end - session.session_start).total_seconds()
            session.total_watch_time = int(total_time)

        await self.db.commit()

        logger.info(f"[WATCH] Ended session {session_id} at {final_time}s")

        return {
            "session_id": str(session_id),
            "final_position": final_time,
            "completed": session.completed,
            "total_watch_time": session.total_watch_time,
        }

    async def get_user_watch_history(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Kullanıcının izleme geçmişi
        """
        stmt = (
            select(EBAVideoWatch, EBAVideo)
            .join(EBAVideo, EBAVideoWatch.eba_video_id == EBAVideo.id)
            .where(EBAVideoWatch.user_id == user_id)
            .order_by(EBAVideoWatch.last_updated.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        history = []
        for watch, video in rows:
            history.append(
                {
                    "session_id": str(watch.id),
                    "video_id": video.eba_video_id,
                    "video_title": video.title,
                    "video_duration": video.duration_seconds,
                    "last_position": watch.last_position,
                    "watch_percentage": watch.watch_percentage,
                    "completed": watch.completed,
                    "last_watched": watch.last_updated.isoformat()
                    if watch.last_updated
                    else None,
                    "thumbnail_url": video.thumbnail_url,
                }
            )

        return history

    async def get_resume_position(
        self, user_id: uuid.UUID, eba_video_id: str
    ) -> Optional[int]:
        """
        Kaldığın yerden devam et - son pozisyonu getir

        Returns:
            Last position in seconds, or None if never watched
        """
        # Get video
        stmt = select(EBAVideo).where(EBAVideo.eba_video_id == eba_video_id)
        result = await self.db.execute(stmt)
        video = result.scalar_one_or_none()

        if not video:
            return None

        # Get last incomplete session
        stmt = (
            select(EBAVideoWatch)
            .where(
                and_(
                    EBAVideoWatch.user_id == user_id,
                    EBAVideoWatch.eba_video_id == video.id,
                    EBAVideoWatch.completed == False,
                )
            )
            .order_by(EBAVideoWatch.last_updated.desc())
        )

        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            return session.last_position

        return None

    async def get_user_analytics(
        self, user_id: uuid.UUID, since_days: Optional[int] = None
    ) -> WatchAnalytics:
        """
        Kullanıcı izleme analitikleri

        Args:
            user_id: Kullanıcı ID
            since_days: Son X gün (None = tüm zamanlar)

        Returns:
            WatchAnalytics with detailed stats
        """
        # Build query filter
        filters = [EBAVideoWatch.user_id == user_id]

        if since_days:
            cutoff = datetime.now() - timedelta(days=since_days)
            filters.append(EBAVideoWatch.created_at >= cutoff)

        # Total watch time
        stmt = select(func.sum(EBAVideoWatch.total_watch_time)).where(and_(*filters))
        result = await self.db.execute(stmt)
        total_watch_time = result.scalar_one() or 0

        # Completed videos
        stmt = select(func.count(EBAVideoWatch.id)).where(
            and_(*filters, EBAVideoWatch.completed == True)
        )
        result = await self.db.execute(stmt)
        completed_videos = result.scalar_one()

        # In-progress videos
        stmt = select(func.count(EBAVideoWatch.id)).where(
            and_(*filters, EBAVideoWatch.completed == False)
        )
        result = await self.db.execute(stmt)
        in_progress_videos = result.scalar_one()

        # Total sessions
        stmt = select(func.count(EBAVideoWatch.id)).where(and_(*filters))
        result = await self.db.execute(stmt)
        total_sessions = result.scalar_one()

        # Average watch percentage
        stmt = select(func.avg(EBAVideoWatch.watch_percentage)).where(and_(*filters))
        result = await self.db.execute(stmt)
        avg_watch_percentage = result.scalar_one() or 0.0

        # Completion rate
        completion_rate = (
            (completed_videos / total_sessions) * 100 if total_sessions > 0 else 0.0
        )

        return WatchAnalytics(
            total_watch_time=int(total_watch_time),
            completed_videos=completed_videos,
            in_progress_videos=in_progress_videos,
            completion_rate=completion_rate,
            average_watch_percentage=float(avg_watch_percentage),
            total_sessions=total_sessions,
        )

    async def get_video_analytics(self, eba_video_id: str) -> Dict[str, Any]:
        """
        Video bazlı analitikler (tüm kullanıcılar)

        - Kaç kişi izledi
        - Ortalama tamamlama oranı
        - Toplam izlenme süresi
        - Drop-off noktaları (where people stop watching)
        """
        # Get video
        stmt = select(EBAVideo).where(EBAVideo.eba_video_id == eba_video_id)
        result = await self.db.execute(stmt)
        video = result.scalar_one_or_none()

        if not video:
            raise ValueError(f"EBA video not found: {eba_video_id}")

        # Total viewers (unique users)
        stmt = select(func.count(func.distinct(EBAVideoWatch.user_id))).where(
            EBAVideoWatch.eba_video_id == video.id
        )
        result = await self.db.execute(stmt)
        total_viewers = result.scalar_one()

        # Completed count
        stmt = select(func.count(EBAVideoWatch.id)).where(
            and_(
                EBAVideoWatch.eba_video_id == video.id, EBAVideoWatch.completed == True
            )
        )
        result = await self.db.execute(stmt)
        completed_count = result.scalar_one()

        # Total sessions
        stmt = select(func.count(EBAVideoWatch.id)).where(
            EBAVideoWatch.eba_video_id == video.id
        )
        result = await self.db.execute(stmt)
        total_sessions = result.scalar_one()

        # Average completion percentage
        stmt = select(func.avg(EBAVideoWatch.watch_percentage)).where(
            EBAVideoWatch.eba_video_id == video.id
        )
        result = await self.db.execute(stmt)
        avg_completion = result.scalar_one() or 0.0

        # Total watch time
        stmt = select(func.sum(EBAVideoWatch.total_watch_time)).where(
            EBAVideoWatch.eba_video_id == video.id
        )
        result = await self.db.execute(stmt)
        total_watch_time = result.scalar_one() or 0

        # Completion rate
        completion_rate = (
            (completed_count / total_sessions) * 100 if total_sessions > 0 else 0.0
        )

        # Drop-off analysis: Get distribution of last_position
        stmt = select(EBAVideoWatch.last_position).where(
            and_(
                EBAVideoWatch.eba_video_id == video.id, EBAVideoWatch.completed == False
            )
        )
        result = await self.db.execute(stmt)
        drop_off_positions = [row[0] for row in result.all()]

        # Calculate drop-off quartiles
        drop_off_distribution = self._calculate_drop_off_distribution(
            drop_off_positions, video.duration_seconds
        )

        return {
            "video_id": eba_video_id,
            "video_title": video.title,
            "video_duration": video.duration_seconds,
            "total_viewers": total_viewers,
            "total_sessions": total_sessions,
            "completed_count": completed_count,
            "completion_rate": completion_rate,
            "average_completion_percentage": float(avg_completion),
            "total_watch_time": int(total_watch_time),
            "drop_off_distribution": drop_off_distribution,
        }

    def _calculate_drop_off_distribution(
        self, positions: List[int], video_duration: int
    ) -> Dict[str, int]:
        """
        Calculate where users drop off

        Returns distribution:
        - 0-25%: count
        - 25-50%: count
        - 50-75%: count
        - 75-100%: count
        """
        if not positions or video_duration == 0:
            return {"0-25%": 0, "25-50%": 0, "50-75%": 0, "75-100%": 0}

        distribution = {"0-25%": 0, "25-50%": 0, "50-75%": 0, "75-100%": 0}

        for pos in positions:
            percentage = (pos / video_duration) * 100

            if percentage < 25:
                distribution["0-25%"] += 1
            elif percentage < 50:
                distribution["25-50%"] += 1
            elif percentage < 75:
                distribution["50-75%"] += 1
            else:
                distribution["75-100%"] += 1

        return distribution

    async def get_popular_videos(
        self,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        En popüler videolar (en çok izlenen)
        """
        # Build subquery to count sessions per video
        from sqlalchemy import desc

        stmt = select(
            EBAVideo, func.count(EBAVideoWatch.id).label("watch_count")
        ).outerjoin(EBAVideoWatch, EBAVideoWatch.eba_video_id == EBAVideo.id)

        # Apply filters
        filters = []
        if subject:
            filters.append(EBAVideo.subject == subject)
        if grade_level:
            filters.append(EBAVideo.grade_level == grade_level)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.group_by(EBAVideo.id).order_by(desc("watch_count")).limit(limit)

        result = await self.db.execute(stmt)
        rows = result.all()

        popular_videos = []
        for video, watch_count in rows:
            popular_videos.append(
                {
                    "video_id": video.eba_video_id,
                    "title": video.title,
                    "subject": video.subject,
                    "grade_level": video.grade_level,
                    "duration": video.duration_seconds,
                    "watch_count": watch_count,
                    "thumbnail_url": video.thumbnail_url,
                }
            )

        return popular_videos
