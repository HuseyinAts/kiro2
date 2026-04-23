"""
Video Çözüm Sistemi API
Teknofest 2025 Eğitim Eylemci Platformu

Task 72: Video Çözüm Sistemi API Endpoints
"""

import asyncio
import logging
from datetime import UTC
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.dependencies import AuthenticatedUser, UserRole, get_current_user
from models.video_solution import (
    VideoProcessingStatus,
    VideoSolution,
)
from services.video_solution_service import VideoSolutionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/video-solutions", tags=["Video Solutions"])

_VIDEO_PRIVILEGED_ROLES = frozenset({UserRole.ADMIN, UserRole.SUPER_ADMIN})


# ============================================================================
# Response Models
# ============================================================================


class VideoSolutionResponse(BaseModel):
    """Video solution response model"""

    id: str
    question_id: str
    title: str
    description: str | None

    # Upload bilgileri
    original_filename: str
    original_format: str
    original_size_bytes: int
    original_duration_seconds: float

    # Processing durumu
    processing_status: str
    is_format_valid: bool

    # URLs
    cdn_url: str | None
    thumbnail_url: str | None
    hls_playlist_url: str | None

    # Compression bilgileri
    compressed_size_bytes: int | None
    compression_ratio: float | None

    # Metadata
    solution_method: str | None
    instructor_name: str | None

    # Stats
    total_views: int
    quality_score: float
    is_approved: bool

    # Timestamps
    created_at: str
    processing_completed_at: str | None

    model_config = ConfigDict(from_attributes=True)


class VideoUploadResponse(BaseModel):
    """Video upload response"""

    success: bool
    message: str
    video: VideoSolutionResponse | None


class VideoListResponse(BaseModel):
    """Video list response"""

    total: int
    videos: list[VideoSolutionResponse]


# ============================================================================
# TASK 72.1: Video Upload Endpoint
# ============================================================================


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Video Yükle",
    description="""
    Soru çözüm videosu yükle (TASK 72.1)
    
    - Video upload interface
    - Format validation (REQ-14.1)
    - Compression optimization
    - Automatic thumbnail generation (REQ-14.3)
    
    Desteklenen formatlar: MP4, WEBM, AVI, MOV, MKV
    Maximum dosya boyutu: 500 MB
    """,
)
async def upload_video(
    question_id: str = Form(..., description="İlişkili soru ID"),
    title: str = Form(..., description="Video başlığı"),
    description: str | None = Form(None, description="Video açıklaması"),
    solution_method: str | None = Form(
        None, description="Çözüm yöntemi (hızlı, klasik, vb.)"
    ),
    file: UploadFile = File(..., description="Video dosyası"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Video yükle ve işleme başlat

    REQ-14.1: Video URL doğrulama
    REQ-14.2: Video süresini otomatik alma
    REQ-14.3: Thumbnail oluşturma
    """
    try:
        service = VideoSolutionService(db)

        success, error_msg, video_solution = await service.upload_video(
            file=file,
            question_id=question_id,
            user_id=current_user.id,
            title=title,
            description=description,
            solution_method=solution_method,
        )

        if not success:
            return VideoUploadResponse(success=False, message=error_msg, video=None)

        # Response oluştur
        video_response = VideoSolutionResponse(
            id=video_solution.id,
            question_id=video_solution.question_id,
            title=video_solution.title,
            description=video_solution.description,
            original_filename=video_solution.original_filename,
            original_format=video_solution.original_format.value,
            original_size_bytes=video_solution.original_size_bytes,
            original_duration_seconds=video_solution.original_duration_seconds,
            processing_status=video_solution.processing_status.value,
            is_format_valid=video_solution.is_format_valid,
            cdn_url=video_solution.cdn_url,
            thumbnail_url=video_solution.thumbnail_url,
            hls_playlist_url=video_solution.hls_playlist_url,
            compressed_size_bytes=video_solution.compressed_size_bytes,
            compression_ratio=video_solution.compression_ratio,
            solution_method=video_solution.solution_method,
            instructor_name=video_solution.instructor_name,
            total_views=video_solution.total_views,
            quality_score=video_solution.quality_score,
            is_approved=video_solution.is_approved,
            created_at=video_solution.created_at.isoformat(),
            processing_completed_at=video_solution.processing_completed_at.isoformat()
            if video_solution.processing_completed_at
            else None,
        )

        return VideoUploadResponse(
            success=True,
            message="Video başarıyla yüklendi ve işleme alındı",
            video=video_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video upload endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ============================================================================
# Video Query Endpoints
# ============================================================================


@router.get(
    "/{video_id}",
    response_model=VideoSolutionResponse,
    summary="Video Detayı",
    description="Video çözüm detaylarını getir",
)
async def get_video(
    video_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Video detaylarını getir"""
    result = await db.execute(
        select(VideoSolution).where(
            VideoSolution.id == video_id, VideoSolution.is_active == True
        )
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video bulunamadı"
        )

    return VideoSolutionResponse(
        id=video.id,
        question_id=video.question_id,
        title=video.title,
        description=video.description,
        original_filename=video.original_filename,
        original_format=video.original_format.value,
        original_size_bytes=video.original_size_bytes,
        original_duration_seconds=video.original_duration_seconds,
        processing_status=video.processing_status.value,
        is_format_valid=video.is_format_valid,
        cdn_url=video.cdn_url,
        thumbnail_url=video.thumbnail_url,
        hls_playlist_url=video.hls_playlist_url,
        compressed_size_bytes=video.compressed_size_bytes,
        compression_ratio=video.compression_ratio,
        solution_method=video.solution_method,
        instructor_name=video.instructor_name,
        total_views=video.total_views,
        quality_score=video.quality_score,
        is_approved=video.is_approved,
        created_at=video.created_at.isoformat(),
        processing_completed_at=video.processing_completed_at.isoformat()
        if video.processing_completed_at
        else None,
    )


@router.get(
    "/question/{question_id}",
    response_model=VideoListResponse,
    summary="Soru Videoları",
    description="Belirli bir soruya ait tüm çözüm videolarını listele",
)
async def get_videos_by_question(
    question_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Soruya ait videoları listele"""
    result = await db.execute(
        select(VideoSolution)
        .where(
            VideoSolution.question_id == question_id,
            VideoSolution.is_active == True,
            VideoSolution.processing_status == VideoProcessingStatus.READY,
        )
        .order_by(VideoSolution.quality_score.desc())
    )
    videos = result.scalars().all()

    video_responses = [
        VideoSolutionResponse(
            id=v.id,
            question_id=v.question_id,
            title=v.title,
            description=v.description,
            original_filename=v.original_filename,
            original_format=v.original_format.value,
            original_size_bytes=v.original_size_bytes,
            original_duration_seconds=v.original_duration_seconds,
            processing_status=v.processing_status.value,
            is_format_valid=v.is_format_valid,
            cdn_url=v.cdn_url,
            thumbnail_url=v.thumbnail_url,
            hls_playlist_url=v.hls_playlist_url,
            compressed_size_bytes=v.compressed_size_bytes,
            compression_ratio=v.compression_ratio,
            solution_method=v.solution_method,
            instructor_name=v.instructor_name,
            total_views=v.total_views,
            quality_score=v.quality_score,
            is_approved=v.is_approved,
            created_at=v.created_at.isoformat(),
            processing_completed_at=v.processing_completed_at.isoformat()
            if v.processing_completed_at
            else None,
        )
        for v in videos
    ]

    return VideoListResponse(total=len(video_responses), videos=video_responses)


@router.get(
    "/",
    response_model=VideoListResponse,
    summary="Video Listesi",
    description="Tüm videoları listele (filtreleme ve sayfalama ile)",
)
async def list_videos(
    skip: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(20, ge=1, le=100, description="Getirilecek kayıt sayısı"),
    status: VideoProcessingStatus | None = Query(
        None, description="İşleme durumu filtresi"
    ),
    approved_only: bool = Query(False, description="Sadece onaylı videoları getir"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Videoları listele"""
    query = select(VideoSolution).where(VideoSolution.is_active == True)

    if status:
        query = query.where(VideoSolution.processing_status == status)

    if approved_only:
        query = query.where(VideoSolution.is_approved == True)

    query = query.order_by(VideoSolution.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    videos = result.scalars().all()

    # Total count
    count_query = select(VideoSolution).where(VideoSolution.is_active == True)
    if status:
        count_query = count_query.where(VideoSolution.processing_status == status)
    if approved_only:
        count_query = count_query.where(VideoSolution.is_approved == True)

    from sqlalchemy import func as sql_func

    total_result = await db.execute(
        select(sql_func.count()).select_from(count_query.subquery())
    )
    total = total_result.scalar()

    video_responses = [
        VideoSolutionResponse(
            id=v.id,
            question_id=v.question_id,
            title=v.title,
            description=v.description,
            original_filename=v.original_filename,
            original_format=v.original_format.value,
            original_size_bytes=v.original_size_bytes,
            original_duration_seconds=v.original_duration_seconds,
            processing_status=v.processing_status.value,
            is_format_valid=v.is_format_valid,
            cdn_url=v.cdn_url,
            thumbnail_url=v.thumbnail_url,
            hls_playlist_url=v.hls_playlist_url,
            compressed_size_bytes=v.compressed_size_bytes,
            compression_ratio=v.compression_ratio,
            solution_method=v.solution_method,
            instructor_name=v.instructor_name,
            total_views=v.total_views,
            quality_score=v.quality_score,
            is_approved=v.is_approved,
            created_at=v.created_at.isoformat(),
            processing_completed_at=v.processing_completed_at.isoformat()
            if v.processing_completed_at
            else None,
        )
        for v in videos
    ]

    return VideoListResponse(total=total, videos=video_responses)


# ============================================================================
# Video Management Endpoints
# ============================================================================


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Video Sil",
    description="Videoyu sil (soft delete)",
)
async def delete_video(
    video_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Videoyu sil"""
    result = await db.execute(select(VideoSolution).where(VideoSolution.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video bulunamadı"
        )

    # Sadece yükleyen kullanıcı veya admin silebilir
    if video.uploaded_by != current_user.id and current_user.role not in _VIDEO_PRIVILEGED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu videoyu silme yetkiniz yok",
        )

    video.is_active = False
    await db.commit()


@router.patch(
    "/{video_id}/approve",
    response_model=VideoSolutionResponse,
    summary="Video Onayla",
    description="Videoyu onayla (sadece admin)",
)
async def approve_video(
    video_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Videoyu onayla"""
    if current_user.role not in _VIDEO_PRIVILEGED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli",
        )

    result = await db.execute(select(VideoSolution).where(VideoSolution.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video bulunamadı"
        )

    from datetime import datetime

    video.is_approved = True
    video.approved_by = current_user.id
    video.approved_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(video)

    return VideoSolutionResponse(
        id=video.id,
        question_id=video.question_id,
        title=video.title,
        description=video.description,
        original_filename=video.original_filename,
        original_format=video.original_format.value,
        original_size_bytes=video.original_size_bytes,
        original_duration_seconds=video.original_duration_seconds,
        processing_status=video.processing_status.value,
        is_format_valid=video.is_format_valid,
        cdn_url=video.cdn_url,
        thumbnail_url=video.thumbnail_url,
        hls_playlist_url=video.hls_playlist_url,
        compressed_size_bytes=video.compressed_size_bytes,
        compression_ratio=video.compression_ratio,
        solution_method=video.solution_method,
        instructor_name=video.instructor_name,
        total_views=video.total_views,
        quality_score=video.quality_score,
        is_approved=video.is_approved,
        created_at=video.created_at.isoformat(),
        processing_completed_at=video.processing_completed_at.isoformat()
        if video.processing_completed_at
        else None,
    )


# ============================================================================
# TASK 72.2: Video Streaming Endpoints
# ============================================================================


@router.post(
    "/{video_id}/generate-streaming",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Streaming Formatları Oluştur",
    description="""
    Video için HLS ve DASH streaming formatları oluştur (TASK 72.2)
    
    - HLS playlist generation
    - DASH manifest generation
    - Adaptive bitrate variants
    - CDN upload (opsiyonel)
    """,
)
async def generate_streaming_formats(
    video_id: str,
    generate_hls: bool = Query(True, description="HLS formatı oluştur"),
    generate_dash: bool = Query(False, description="DASH formatı oluştur"),
    upload_to_cdn: bool = Query(False, description="CDN'e yükle"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Streaming formatları oluştur

    REQ-14.4: Video streaming
    REQ-14.5: Adaptive bitrate
    """
    try:
        # Video kontrolü
        result = await db.execute(
            select(VideoSolution).where(VideoSolution.id == video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Video bulunamadı"
            )

        # Sadece yükleyen kullanıcı veya admin işlem yapabilir
        if video.uploaded_by != current_user.id and current_user.role not in _VIDEO_PRIVILEGED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu video için streaming formatları oluşturma yetkiniz yok",
            )

        # Video hazır mı kontrol et
        if video.processing_status != VideoProcessingStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video henüz hazır değil. Durum: {video.processing_status.value}",
            )

        # Arka planda streaming formatları oluştur
        from pathlib import Path

        asyncio.create_task(
            _generate_streaming_async(
                video_id=video_id,
                video_path=Path(video.cdn_url or video.original_url),
                generate_hls=generate_hls,
                generate_dash=generate_dash,
                upload_to_cdn=upload_to_cdn,
                db=db,
            )
        )

        return {
            "success": True,
            "message": "Streaming formatları oluşturuluyor",
            "video_id": video_id,
            "formats": {"hls": generate_hls, "dash": generate_dash},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate streaming formats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


async def _generate_streaming_async(
    video_id: str,
    video_path: Path,
    generate_hls: bool,
    generate_dash: bool,
    upload_to_cdn: bool,
    db: AsyncSession,
):
    """Arka planda streaming formatları oluştur"""
    try:
        from pathlib import Path

        from services.video_solution_service import VideoStreamingService

        streaming_dir = Path("uploads/streaming") / video_id
        streaming_dir.mkdir(parents=True, exist_ok=True)

        # Video kaydını al
        result = await db.execute(
            select(VideoSolution).where(VideoSolution.id == video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            logger.error(f"Video not found: {video_id}")
            return

        # HLS oluştur
        if generate_hls:
            hls_dir = streaming_dir / "hls"
            (
                success,
                error_msg,
                hls_info,
            ) = await VideoStreamingService.generate_hls_playlist(video_path, hls_dir)

            if success:
                video.hls_playlist_url = str(hls_info["master_playlist"])
                video.available_qualities = {
                    v["quality"]: v["playlist_path"] for v in hls_info["variants"]
                }
                logger.info(f"HLS generated for video: {video_id}")
            else:
                logger.error(f"HLS generation failed: {error_msg}")

        # DASH oluştur
        if generate_dash:
            dash_dir = streaming_dir / "dash"
            (
                success,
                error_msg,
                manifest_path,
            ) = await VideoStreamingService.generate_dash_manifest(video_path, dash_dir)

            if success:
                video.dash_manifest_url = manifest_path
                logger.info(f"DASH generated for video: {video_id}")
            else:
                logger.error(f"DASH generation failed: {error_msg}")

        # CDN'e yükle (opsiyonel)
        if upload_to_cdn:
            # CDN upload placeholder
            logger.info(f"CDN upload requested for video: {video_id}")

        await db.commit()

    except Exception as e:
        logger.error(f"Streaming generation async error: {e}")


@router.post(
    "/{video_id}/track-view",
    status_code=status.HTTP_201_CREATED,
    summary="Video İzleme Kaydı",
    description="""
    Video izleme analitiği kaydet (REQ-14.4)
    
    - İzlenme sayısı artırma
    - İzleme süresi kaydetme
    - Tamamlanma oranı hesaplama
    """,
)
async def track_video_view(
    video_id: str,
    session_id: str = Form(..., description="Session ID"),
    watch_duration_seconds: float = Form(..., description="İzleme süresi (saniye)"),
    completion_percentage: float = Form(
        ..., ge=0, le=100, description="Tamamlanma yüzdesi"
    ),
    device_type: str | None = Form(None, description="Cihaz tipi"),
    browser: str | None = Form(None, description="Tarayıcı"),
    os: str | None = Form(None, description="İşletim sistemi"),
    current_user: AuthenticatedUser | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Video izleme kaydı oluştur

    REQ-14.4: İzlenme sayısını artırma
    """
    try:
        from services.video_solution_service import VideoAnalyticsService

        device_info = {"device_type": device_type, "browser": browser, "os": os}

        analytics_service = VideoAnalyticsService(db)
        success = await analytics_service.track_view(
            video_id=video_id,
            user_id=current_user.id if current_user else None,
            session_id=session_id,
            watch_duration_seconds=watch_duration_seconds,
            completion_percentage=completion_percentage,
            device_info=device_info,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="İzleme kaydı oluşturulamadı",
            )

        return {"success": True, "message": "İzleme kaydı oluşturuldu"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Track video view error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/{video_id}/analytics",
    summary="Video Analitiği",
    description="Video izleme istatistiklerini getir",
)
async def get_video_analytics(
    video_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Video analytics getir"""
    try:
        from sqlalchemy import func as sql_func

        from models.video_solution import VideoAnalytics

        # Video kontrolü
        result = await db.execute(
            select(VideoSolution).where(VideoSolution.id == video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Video bulunamadı"
            )

        # Analytics istatistikleri
        analytics_result = await db.execute(
            select(
                sql_func.count(VideoAnalytics.id).label("total_views"),
                sql_func.sum(VideoAnalytics.watch_duration_seconds).label(
                    "total_watch_time"
                ),
                sql_func.avg(VideoAnalytics.completion_percentage).label(
                    "avg_completion"
                ),
                sql_func.avg(VideoAnalytics.watch_duration_seconds).label(
                    "avg_watch_time"
                ),
            ).where(VideoAnalytics.video_id == video_id)
        )
        stats = analytics_result.one()

        return {
            "video_id": video_id,
            "total_views": stats.total_views or 0,
            "total_watch_time_seconds": float(stats.total_watch_time or 0),
            "average_completion_percentage": float(stats.avg_completion or 0),
            "average_watch_time_seconds": float(stats.avg_watch_time or 0),
            "quality_score": video.quality_score,
            "is_approved": video.is_approved,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get video analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ============================================================================
# TASK 72.3: Video Transcript Endpoints
# ============================================================================


@router.post(
    "/{video_id}/generate-transcript",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Transkript Oluştur",
    description="""
    Video için otomatik transkript oluştur (TASK 72.3)
    
    - Auto-generated transcripts (Whisper AI)
    - Timestamped segments
    - Keyword extraction
    """,
)
async def generate_transcript(
    video_id: str,
    language: str = Query("tr", description="Dil kodu"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Otomatik transkript oluştur

    REQ-14.1: Video URL doğrulama
    REQ-14.2: Video süresini otomatik alma
    """
    try:
        # Video kontrolü
        result = await db.execute(
            select(VideoSolution).where(VideoSolution.id == video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Video bulunamadı"
            )

        # Arka planda transkript oluştur
        from pathlib import Path

        asyncio.create_task(
            _generate_transcript_async(
                video_id=video_id,
                video_path=Path(video.cdn_url or video.original_url),
                language=language,
                db=db,
            )
        )

        return {
            "success": True,
            "message": "Transkript oluşturuluyor",
            "video_id": video_id,
            "language": language,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate transcript error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


async def _generate_transcript_async(
    video_id: str, video_path: Path, language: str, db: AsyncSession
):
    """Arka planda transkript oluştur"""
    try:
        from services.video_transcript_service import VideoTranscriptService

        service = VideoTranscriptService(db)
        success, error_msg, transcript = await service.generate_auto_transcript(
            video_id=video_id, video_path=video_path, language=language
        )

        if success:
            # Anahtar kelimeleri çıkar
            await service.extract_keywords(transcript.id)
            logger.info(f"Transcript generated for video: {video_id}")
        else:
            logger.error(f"Transcript generation failed: {error_msg}")

    except Exception as e:
        logger.error(f"Transcript generation async error: {e}")


@router.get(
    "/{video_id}/transcripts",
    summary="Transkriptleri Listele",
    description="Video transkriptlerini listele",
)
async def list_transcripts(
    video_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Video transkriptlerini listele"""
    try:
        from models.video_solution import VideoTranscript

        result = await db.execute(
            select(VideoTranscript).where(
                VideoTranscript.video_id == video_id, VideoTranscript.is_active == True
            )
        )
        transcripts = result.scalars().all()

        return {
            "video_id": video_id,
            "total": len(transcripts),
            "transcripts": [
                {
                    "id": t.id,
                    "language": t.language,
                    "status": t.transcript_status.value,
                    "word_count": t.word_count,
                    "readability_score": t.readability_score,
                    "auto_generated_by": t.auto_generated_by,
                    "confidence": t.auto_generation_confidence,
                    "edit_count": t.edit_count,
                    "created_at": t.created_at.isoformat(),
                }
                for t in transcripts
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List transcripts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/transcripts/{transcript_id}",
    summary="Transkript Detayı",
    description="Transkript detaylarını ve segmentleri getir",
)
async def get_transcript(
    transcript_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Transkript detaylarını getir"""
    try:
        from models.video_solution import VideoTranscript

        result = await db.execute(
            select(VideoTranscript).where(VideoTranscript.id == transcript_id)
        )
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transkript bulunamadı"
            )

        return {
            "id": transcript.id,
            "video_id": transcript.video_id,
            "language": transcript.language,
            "full_text": transcript.full_text,
            "timestamped_segments": transcript.timestamped_segments,
            "status": transcript.transcript_status.value,
            "word_count": transcript.word_count,
            "keywords": transcript.keywords,
            "topics": transcript.topics,
            "readability_score": transcript.readability_score,
            "created_at": transcript.created_at.isoformat(),
            "updated_at": transcript.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get transcript error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.patch(
    "/transcripts/{transcript_id}",
    summary="Transkript Düzenle",
    description="Transkripti manuel olarak düzenle (TASK 72.3: Manual transcript editing)",
)
async def update_transcript(
    transcript_id: str,
    full_text: str | None = Form(None, description="Yeni tam metin"),
    timestamped_segments: str | None = Form(None, description="Yeni segmentler (JSON)"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Transkripti düzenle"""
    try:
        import json

        from services.video_transcript_service import VideoTranscriptService

        # JSON parse
        segments_dict = None
        if timestamped_segments:
            segments_dict = json.loads(timestamped_segments)

        service = VideoTranscriptService(db)
        success, error_msg, transcript = await service.update_transcript(
            transcript_id=transcript_id,
            user_id=current_user.id,
            full_text=full_text,
            timestamped_segments=segments_dict,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )

        return {
            "success": True,
            "message": "Transkript güncellendi",
            "transcript_id": transcript.id,
            "edit_count": transcript.edit_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update transcript error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ============================================================================
# TASK 72.4: Video Search Endpoints
# ============================================================================


@router.get(
    "/search",
    summary="Video Arama",
    description="""
    Videolarda arama yap (TASK 72.4)
    
    - Transcript-based search
    - Topic-based filtering
    - Timestamp navigation
    """,
)
async def search_videos(
    q: str = Query(..., description="Arama sorgusu"),
    search_in_transcripts: bool = Query(True, description="Transkriptlerde ara"),
    topic: str | None = Query(None, description="Konu filtresi"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Videolarda arama yap

    REQ-14.5: Süre filtresi
    REQ-14.6: Güncelleme yetkisi
    """
    try:
        results = []

        # Transkriptlerde ara
        if search_in_transcripts:
            from services.video_transcript_service import VideoTranscriptService

            service = VideoTranscriptService(db)
            transcript_results = await service.search_transcripts(
                query=q, language="tr"
            )

            # Video bilgilerini ekle
            for tr_result in transcript_results:
                video_result = await db.execute(
                    select(VideoSolution).where(
                        VideoSolution.id == tr_result["video_id"]
                    )
                )
                video = video_result.scalar_one_or_none()

                if video:
                    results.append(
                        {
                            "video_id": video.id,
                            "title": video.title,
                            "description": video.description,
                            "thumbnail_url": video.thumbnail_url,
                            "duration_seconds": video.original_duration_seconds,
                            "matching_segments": tr_result["matching_segments"],
                            "total_matches": tr_result["total_matches"],
                        }
                    )

        # Başlık ve açıklamada ara
        title_search = select(VideoSolution).where(
            VideoSolution.is_active == True,
            VideoSolution.processing_status == VideoProcessingStatus.READY,
        )

        # Arama filtresi
        from sqlalchemy import or_

        title_search = title_search.where(
            or_(
                VideoSolution.title.ilike(f"%{q}%"),
                VideoSolution.description.ilike(f"%{q}%"),
            )
        )

        # Konu filtresi
        if topic:
            # Topic filtering implementation
            pass

        title_search = title_search.offset(skip).limit(limit)

        title_result = await db.execute(title_search)
        title_videos = title_result.scalars().all()

        # Sonuçları birleştir (duplicate'leri kaldır)
        video_ids = {r["video_id"] for r in results}

        for video in title_videos:
            if video.id not in video_ids:
                results.append(
                    {
                        "video_id": video.id,
                        "title": video.title,
                        "description": video.description,
                        "thumbnail_url": video.thumbnail_url,
                        "duration_seconds": video.original_duration_seconds,
                        "matching_segments": [],
                        "total_matches": 0,
                    }
                )

        return {"query": q, "total": len(results), "results": results}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
