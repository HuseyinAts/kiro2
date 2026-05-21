"""
Task 97.2: Video Katalog Senkronizasyonu
EBA TV video kataloğunu otomatik olarak çeker ve veritabanına kaydeder
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import EBAVideo
from services.eba_tv_client import (
    EBACatalogFilter,
    EBAGradeLevel,
    EBASubject,
    EBAVideoMetadata,
    get_eba_client,
)

logger = logging.getLogger(__name__)


class EBACatalogSyncService:
    """
    Task 97.2: Video Katalog Çekme

    - EBA API'den video kataloğunu çeker
    - Metadata extraction (başlık, açıklama, süre, thumbnail)
    - Veritabanına kayıt
    - Incremental sync (sadece yeni/güncellenmiş videolar)
    - Automatic scheduling (günlük sync)
    """

    def __init__(self, db: AsyncSession, use_mock: bool = False):
        self.db = db
        self.eba_client = get_eba_client(use_mock=use_mock)

    async def sync_full_catalog(
        self,
        subjects: list[EBASubject] | None = None,
        grade_levels: list[EBAGradeLevel] | None = None,
    ) -> dict[str, int]:
        """
        Full catalog sync

        Tüm EBA kataloğunu çeker ve veritabanını günceller
        """
        stats = {"total_fetched": 0, "new_videos": 0, "updated_videos": 0, "errors": 0}

        # Default: sync all subjects and grades
        if subjects is None:
            subjects = list(EBASubject)

        if grade_levels is None:
            grade_levels = list(EBAGradeLevel)

        logger.info("[EBA SYNC] Starting full catalog sync...")
        logger.info(
            f"[EBA SYNC] Subjects: {len(subjects)}, Grade levels: {len(grade_levels)}"
        )

        for subject in subjects:
            for grade_level in grade_levels:
                try:
                    result = await self._sync_category(subject, grade_level)
                    stats["total_fetched"] += result["fetched"]
                    stats["new_videos"] += result["new"]
                    stats["updated_videos"] += result["updated"]

                except Exception as e:
                    logger.error(
                        f"[EBA SYNC] Failed to sync {subject.value} - {grade_level.value}: {e}"
                    , exc_info=True)
                    stats["errors"] += 1
                    continue

        logger.info(f"[EBA SYNC] Completed. Stats: {stats}")
        return stats

    async def _sync_category(
        self, subject: EBASubject, grade_level: EBAGradeLevel
    ) -> dict[str, int]:
        """Sync a specific subject + grade level combination"""

        stats = {"fetched": 0, "new": 0, "updated": 0}

        # Fetch all pages for this category
        page = 1
        has_more = True

        while has_more:
            filters = EBACatalogFilter(
                subject=subject, grade_level=grade_level, page=page, page_size=50
            )

            try:
                videos = await self.eba_client.get_video_catalog(filters)

                if not videos:
                    has_more = False
                    break

                stats["fetched"] += len(videos)

                # FIX N+1: Batch save all videos without committing
                for video_meta in videos:
                    try:
                        is_new = await self._save_video(video_meta, commit=False)
                        if is_new:
                            stats["new"] += 1
                        else:
                            stats["updated"] += 1

                    except Exception as e:
                        logger.warning(
                            f"Failed to save video {video_meta.video_id}: {e}"
                        )
                        await self.db.rollback()
                        continue

                # FIX N+1: Commit after each page instead of after each video
                await self.db.commit()

                # Check if there are more pages
                if len(videos) < filters.page_size:
                    has_more = False
                else:
                    page += 1

            except Exception as e:
                logger.error(f"Failed to fetch page {page}: {e}", exc_info=True)
                await self.db.rollback()
                has_more = False

        logger.info(f"[EBA SYNC] {subject.value} - {grade_level.value}: {stats}")
        return stats

    async def _save_video(
        self, video_meta: EBAVideoMetadata, commit: bool = True
    ) -> bool:
        """
        Save video to database

        Args:
            video_meta: Video metadata to save
            commit: Whether to commit immediately (default True for backwards compatibility)

        Returns:
            True if new video, False if updated existing video
        """
        # Check if video already exists
        stmt = select(EBAVideo).where(EBAVideo.eba_video_id == video_meta.video_id)
        result = await self.db.execute(stmt)
        existing_video = result.scalar_one_or_none()

        if existing_video:
            # Update existing video
            existing_video.title = video_meta.title
            existing_video.description = video_meta.description
            existing_video.duration_seconds = video_meta.duration_seconds
            existing_video.thumbnail_url = video_meta.thumbnail_url
            existing_video.video_url = video_meta.video_url
            existing_video.topic = video_meta.topic
            existing_video.subtopics = video_meta.subtopics
            existing_video.keywords = video_meta.keywords
            existing_video.view_count = video_meta.view_count
            existing_video.quality = video_meta.quality
            existing_video.meb_content_id = video_meta.meb_content_id
            existing_video.kazanim_codes = video_meta.kazanim_codes
            existing_video.last_synced_at = datetime.now()

            if commit:
                await self.db.commit()
            return False

        # Create new video
        new_video = EBAVideo(
            eba_video_id=video_meta.video_id,
            title=video_meta.title,
            description=video_meta.description,
            duration_seconds=video_meta.duration_seconds,
            thumbnail_url=video_meta.thumbnail_url,
            video_url=video_meta.video_url,
            subject=video_meta.subject.value,
            grade_level=video_meta.grade_level.value,
            topic=video_meta.topic,
            subtopics=video_meta.subtopics,
            keywords=video_meta.keywords,
            publish_date=video_meta.publish_date,
            view_count=video_meta.view_count,
            quality=video_meta.quality,
            has_turkish_subtitle=video_meta.has_turkish_subtitle,
            curriculum_aligned=video_meta.curriculum_aligned,
            meb_content_id=video_meta.meb_content_id,
            kazanim_codes=video_meta.kazanim_codes,
            last_synced_at=datetime.now(),
        )

        self.db.add(new_video)
        if commit:
            await self.db.commit()
        return True

    async def sync_incremental(self, since_hours: int = 24) -> dict[str, int]:
        """
        Incremental sync

        Sadece son X saat içinde güncellenen videoları çeker
        Günlük otomatik sync için kullanılır
        """
        logger.info(f"[EBA SYNC] Starting incremental sync (last {since_hours} hours)")

        stats = {"total_fetched": 0, "new_videos": 0, "updated_videos": 0, "errors": 0}

        # Get all videos from EBA (no time filter in API, so we fetch all and compare)
        # In production, EBA API should support "updated_since" parameter

        try:
            # Fetch recent videos (assumption: sorted by publish_date desc)
            filters = EBACatalogFilter(page=1, page_size=100)
            videos = await self.eba_client.get_video_catalog(filters)

            cutoff_time = datetime.now() - timedelta(hours=since_hours)

            for video_meta in videos:
                # Check if video is recent
                if video_meta.publish_date and video_meta.publish_date < cutoff_time:
                    continue

                try:
                    is_new = await self._save_video(video_meta)
                    stats["total_fetched"] += 1

                    if is_new:
                        stats["new_videos"] += 1
                    else:
                        stats["updated_videos"] += 1

                except Exception as e:
                    logger.warning(f"Failed to save video {video_meta.video_id}: {e}")
                    await self.db.rollback()
                    stats["errors"] += 1
                    continue

            logger.info(f"[EBA SYNC] Incremental sync completed. Stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"[EBA SYNC] Incremental sync failed: {e}", exc_info=True)
            raise

    async def sync_by_curriculum_code(
        self, kazanim_code: str
    ) -> list[EBAVideoMetadata]:
        """
        Belirli bir müfredat kazanımına ait videoları çeker

        Örnek: "8.1.2.1" -> 8. sınıf Matematik, 1. ünite, 2. konu, 1. kazanım
        """
        logger.info(f"[EBA SYNC] Fetching videos for kazanım code: {kazanim_code}")

        try:
            # Fetch curriculum alignment from EBA
            # Parse kazanım code to extract subject and grade
            grade_num = int(kazanim_code.split(".")[0])

            # Map grade number to EBAGradeLevel
            grade_level_map = {
                1: EBAGradeLevel.ILKOKUL_1,
                2: EBAGradeLevel.ILKOKUL_2,
                3: EBAGradeLevel.ILKOKUL_3,
                4: EBAGradeLevel.ILKOKUL_4,
                5: EBAGradeLevel.ORTAOKUL_5,
                6: EBAGradeLevel.ORTAOKUL_6,
                7: EBAGradeLevel.ORTAOKUL_7,
                8: EBAGradeLevel.ORTAOKUL_8,
                9: EBAGradeLevel.LISE_9,
                10: EBAGradeLevel.LISE_10,
                11: EBAGradeLevel.LISE_11,
                12: EBAGradeLevel.LISE_12,
            }

            grade_level = grade_level_map.get(grade_num)
            if not grade_level:
                logger.warning(f"Invalid grade number in kazanım code: {grade_num}")
                return []

            # Fetch all videos for this grade (we'll filter by kazanim_codes)
            # In production, EBA API should support filtering by kazanim_code
            filters = EBACatalogFilter(grade_level=grade_level, page_size=100)

            all_videos = await self.eba_client.get_video_catalog(filters)

            # Filter by kazanim_code
            matching_videos = [v for v in all_videos if kazanim_code in v.kazanim_codes]

            logger.info(
                f"[EBA SYNC] Found {len(matching_videos)} videos for kazanım {kazanim_code}"
            )
            return matching_videos

        except Exception as e:
            logger.error(f"Failed to fetch videos for kazanım {kazanim_code}: {e}", exc_info=True)
            return []

    async def get_sync_status(self) -> dict[str, Any]:
        """
        Get sync status and statistics
        """
        from sqlalchemy import func

        # Total videos in database
        stmt = select(func.count(EBAVideo.id))
        result = await self.db.execute(stmt)
        total_videos = result.scalar_one()

        # Videos by subject
        stmt = select(EBAVideo.subject, func.count(EBAVideo.id)).group_by(
            EBAVideo.subject
        )
        result = await self.db.execute(stmt)
        videos_by_subject = dict(result.all())

        # Videos by grade level
        stmt = select(EBAVideo.grade_level, func.count(EBAVideo.id)).group_by(
            EBAVideo.grade_level
        )
        result = await self.db.execute(stmt)
        videos_by_grade = dict(result.all())

        # Last sync time
        stmt = select(func.max(EBAVideo.last_synced_at))
        result = await self.db.execute(stmt)
        last_sync = result.scalar_one()

        return {
            "total_videos": total_videos,
            "videos_by_subject": videos_by_subject,
            "videos_by_grade": videos_by_grade,
            "last_sync_at": last_sync.isoformat() if last_sync else None,
            "sync_age_hours": (
                (datetime.now() - last_sync).total_seconds() / 3600
                if last_sync
                else None
            ),
        }

    async def close(self):
        """Close EBA client"""
        await self.eba_client.close()


# Scheduled task for automatic sync
async def scheduled_eba_sync(db: AsyncSession, use_mock: bool = False):
    """
    Günlük otomatik EBA sync görevi

    Celery Beat veya APScheduler ile çağrılır
    """
    logger.info("[SCHEDULED] Starting EBA catalog sync...")

    sync_service = EBACatalogSyncService(db, use_mock=use_mock)

    try:
        # Incremental sync (last 24 hours)
        stats = await sync_service.sync_incremental(since_hours=24)

        logger.info(f"[SCHEDULED] EBA sync completed: {stats}")
        return stats

    except Exception as e:
        logger.error(f"[SCHEDULED] EBA sync failed: {e}", exc_info=True)
        raise

    finally:
        await sync_service.close()
