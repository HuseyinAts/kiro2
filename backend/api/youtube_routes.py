"""
YouTube Video Discovery API Endpoints
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi import (
    Response as FastAPIResponse,
)
from pydantic import BaseModel, Field, field_validator

try:
    from services.advanced_youtube_search import (
        AdvancedYouTubeSearch,
        get_advanced_youtube_search,
    )
except (ImportError, TypeError):
    AdvancedYouTubeSearch = None
    get_advanced_youtube_search = None

try:
    from services.real_youtube_api import RealYouTubeAPI, get_real_youtube_api
except (ImportError, TypeError):
    RealYouTubeAPI = None
    get_real_youtube_api = None

try:
    from services.semantic_youtube_search import (
        SemanticYouTubeSearch,
        get_semantic_youtube_search,
    )
except (ImportError, TypeError):
    SemanticYouTubeSearch = None
    get_semantic_youtube_search = None

try:
    from services.youtube import (
        DifficultyLevel,
        ExamType,
        SubjectType,
        YouTubeDiscovery,
        get_youtube_discovery,
    )
except (ImportError, TypeError):
    DifficultyLevel = None
    ExamType = None
    SubjectType = None
    YouTubeDiscovery = None
    get_youtube_discovery = None

try:
    from services.health_check_service import (
        HealthCheckService,
        get_health_check_service,
    )
except (ImportError, TypeError):
    HealthCheckService = None
    get_health_check_service = None

try:
    from services.video_recommendation_service import (
        VideoRecommendationService,
        get_video_recommendation_service,
    )
except (ImportError, TypeError):
    VideoRecommendationService = None
    get_video_recommendation_service = None

try:
    from services.youtube_rate_limiter import (
        YouTubeRateLimiter,
        get_youtube_rate_limiter,
    )
except (ImportError, TypeError):
    get_youtube_rate_limiter = None
    YouTubeRateLimiter = None

try:
    from slowapi.errors import RateLimitExceeded
except ImportError:
    # slowapi optional — rate limit handler devre disi kalir
    RateLimitExceeded = Exception

from core.ddos_protection import limiter  # Task 12: Use global limiter
from core.dependencies import (
    AuthenticatedUser,
    get_current_admin_user,
)
from core.metrics_collector import get_metrics_collector

# from core.elasticsearch_logger import get_elasticsearch_logger, LogLevel, LogCategory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/youtube", tags=["YouTube Discovery"])


# Custom rate limit exceeded handler for YouTube endpoints (Task 12 - Requirement 7.6)
async def youtube_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom rate limit exceeded handler with Turkish error messages

    Task 12 - Requirement 7.6: Rate limit exceeded error handling (429 status code)
    """
    # Extract retry-after from exception
    retry_after = getattr(exc, "retry_after", 60)

    # Turkish error message
    error_response = {
        "error": "Rate limit exceeded",
        "message": f"Çok fazla istek gönderdiniz. Lütfen {retry_after} saniye sonra tekrar deneyin.",
        "retry_after": retry_after,
        "detail": "YouTube video önerileri için dakikada maksimum 10 istek yapabilirsiniz.",
        "suggestion": "Lütfen bekleyin veya premium hesaba geçerek daha yüksek limit alın.",
    }

    logger.warning(
        f"Rate limit exceeded for YouTube endpoint: {request.url.path}",
        extra={
            "endpoint": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "retry_after": retry_after,
        },
    )

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response,
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": "10",
            "X-RateLimit-Window": "60",
        },
    )


# Import validated models (Task 23: Security Hardening)


# Pydantic modelleri
class VideoSearchRequest(BaseModel):
    subject: str
    difficulty: str
    exam_type: str
    max_results: int = 20
    search_mode: str = "semantic"  # "semantic", "keyword", "hybrid"
    custom_query: str | None = None

    @field_validator("subject", mode="before")
    @classmethod
    def normalize_subject(cls, v: str) -> str:
        """Turkish NFC + lowercase normalization for subject matching."""
        import unicodedata

        if not v:
            return v
        v = unicodedata.normalize("NFC", v)
        v = v.replace("İ", "i").replace("I", "ı")
        return v.lower()


class StudentProfileRequest(BaseModel):
    goals: list[str]
    currentLevel: dict[str, int]
    learningStyle: str
    preferences: dict[str, Any] = {}


class VideoResponse(BaseModel):
    """
    Video response modeli - Türkçe içerik filtreleme skorları dahil

    Requirements: 13.20, 14.8, 15.15

    Attributes:
        video_id: YouTube video ID
        title: Video başlığı
        channel: Kanal adı
        channel_id: YouTube kanal ID
        duration: Video süresi (ISO 8601 format)
        view_count: İzlenme sayısı
        upload_date: Yüklenme tarihi (ISO 8601 format)
        thumbnail: Thumbnail URL
        quality_score: Genel kalite skoru (0-1)
        subject: Ders konusu
        difficulty: Zorluk seviyesi
        exam_type: Sınav tipi (TYT, AYT, LGS)
        url: Video URL
        language_score: Türkçe dil skoru (0-1) - Req 13.20
        relevance_score: Konu alakalılık skoru (0-1) - Req 14.8
        difficulty_match: Zorluk seviyesi uyum skoru (0-1) - Req 15.15
    """

    video_id: str
    title: str
    channel: str
    channel_id: str
    duration: str
    view_count: int
    upload_date: str
    thumbnail: str
    quality_score: float
    subject: str
    difficulty: str
    exam_type: str
    url: str

    # Task 18: Yeni alanlar - Türkçe içerik filtreleme skorları
    language_score: float | None = Field(
        None, ge=0.0, le=1.0, description="Türkçe dil skoru (0-1)"
    )  # Req 13.20
    relevance_score: float | None = Field(
        None, ge=0.0, le=1.0, description="Konu alakalılık skoru (0-1)"
    )  # Req 14.8
    difficulty_match: float | None = Field(
        None, ge=0.0, le=1.0, description="Zorluk seviyesi uyum skoru (0-1)"
    )  # Req 15.15

    @field_validator(
        "quality_score",
        "language_score",
        "relevance_score",
        "difficulty_match",
        mode="before",
    )
    @classmethod
    def validate_score_range(cls, v):
        """Skorları 0-1 aralığına normalize et (0-10 ölçeği otomatik dönüştürülür)"""
        if v is not None:
            if v > 1.0:
                v = min(v / 10.0, 1.0)
            v = max(v, 0.0)
        return v

    @field_validator("view_count")
    @classmethod
    def validate_view_count(cls, v):
        """İzlenme sayısının negatif olmadığını doğrula"""
        if v < 0:
            raise ValueError("İzlenme sayısı negatif olamaz")
        return v

    @field_validator("video_id", "title", "channel", "url")
    @classmethod
    def validate_not_empty(cls, v):
        """Zorunlu string alanların boş olmadığını doğrula"""
        if not v or not v.strip():
            raise ValueError("Bu alan boş olamaz")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "title": "Matematik - Üçgenler Konu Anlatımı",
                "channel": "Tonguç Akademi",
                "channel_id": "UCxyz123",
                "duration": "PT15M30S",
                "view_count": 125000,
                "upload_date": "2024-01-15T10:30:00Z",
                "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                "quality_score": 0.92,
                "subject": "matematik",
                "difficulty": "orta",
                "exam_type": "TYT",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "language_score": 0.98,
                "relevance_score": 0.87,
                "difficulty_match": 0.95,
            }
        }
    }


class RecommendationResponse(BaseModel):
    """
    Video öneri response modeli - Cache ve performans metrikleri dahil

    Requirements: 13.20, 14.8, 15.15

    Attributes:
        subject_exam: Konu ve sınav tipi (örn: "Matematik TYT")
        videos: Video listesi
        total_count: Toplam video sayısı
        cache_hit: Cache'den mi geldi? (True/False)
        response_time_ms: Yanıt süresi (milisaniye)
    """

    subject_exam: str = Field(..., min_length=1, description="Konu ve sınav tipi")
    videos: list[VideoResponse] = Field(..., description="Video listesi")
    total_count: int = Field(..., ge=0, description="Toplam video sayısı")
    cache_hit: bool | None = Field(False, description="Cache'den mi geldi?")
    response_time_ms: int | None = Field(0, ge=0, description="Yanıt süresi (ms)")

    @field_validator("total_count")
    @classmethod
    def validate_total_count(cls, v, values):
        """Total count'un video listesi uzunluğu ile tutarlı olduğunu doğrula"""
        if "videos" in values and v != len(values["videos"]):
            raise ValueError("total_count video listesi uzunluğu ile eşleşmiyor")
        return v

    @field_validator("response_time_ms")
    @classmethod
    def validate_response_time(cls, v):
        """Yanıt süresinin makul bir değerde olduğunu doğrula"""
        if v is not None and v < 0:
            raise ValueError("Yanıt süresi negatif olamaz")
        if v is not None and v > 60000:  # 60 saniye
            logger.warning(f"Yanıt süresi çok yüksek: {v}ms")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "subject_exam": "Matematik TYT",
                "videos": [
                    {
                        "video_id": "dQw4w9WgXcQ",
                        "title": "Matematik - Üçgenler Konu Anlatımı",
                        "channel": "Tonguç Akademi",
                        "channel_id": "UCxyz123",
                        "duration": "PT15M30S",
                        "view_count": 125000,
                        "upload_date": "2024-01-15T10:30:00Z",
                        "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                        "quality_score": 0.92,
                        "subject": "matematik",
                        "difficulty": "orta",
                        "exam_type": "TYT",
                        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        "language_score": 0.98,
                        "relevance_score": 0.87,
                        "difficulty_match": 0.95,
                    }
                ],
                "total_count": 5,
                "cache_hit": True,
                "response_time_ms": 87,
            }
        }
    }


class SearchStatsResponse(BaseModel):
    total_cached_videos: int
    cache_hit_rate: float
    last_update: datetime
    supported_subjects: list[str]
    supported_exam_types: list[str]


class ComponentHealthResponse(BaseModel):
    """Bileşen sağlık durumu response modeli"""

    name: str
    status: str
    response_time_ms: float
    error_message: str | None = None
    last_check: str | None = None
    details: dict[str, Any] = {}


class SystemHealthResponse(BaseModel):
    """Sistem sağlık durumu response modeli"""

    overall_status: str
    components: list[ComponentHealthResponse]
    metrics: dict[str, Any]
    timestamp: str


class MetricsSnapshotResponse(BaseModel):
    """Metrics snapshot response modeli"""

    timestamp: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    cache_hits: int
    cache_misses: int
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    youtube_api_quota_used: int
    error_rate: float
    cache_hit_rate: float


# Dependency injection - ULTRA FAST VERSION
async def get_discovery_service() -> YouTubeDiscovery:
    """YouTube discovery service'i al - session başlatma"""
    # Session başlatma komple kaldırıldı - instant return
    return get_youtube_discovery()


async def get_advanced_discovery_service() -> AdvancedYouTubeSearch:
    """Advanced YouTube discovery service'i al"""
    return await get_advanced_youtube_search()


async def get_real_youtube_service() -> RealYouTubeAPI:
    """Real YouTube API service'i al"""
    return await get_real_youtube_api()


async def get_semantic_search_service() -> SemanticYouTubeSearch:
    """Semantic YouTube search service'i al"""
    return await get_semantic_youtube_search()


async def get_health_service() -> HealthCheckService:
    """Health check service'i al"""
    return get_health_check_service()


@router.post("/search", response_model=list[VideoResponse])
@limiter.limit("10/minute")  # Task 12: 10 req/min per IP
async def search_videos(
    request_obj: Request,
    response: FastAPIResponse,
    request: VideoSearchRequest,
    semantic_search: SemanticYouTubeSearch = Depends(get_semantic_search_service),
    real_youtube: RealYouTubeAPI = Depends(get_real_youtube_service),
    youtube_rate_limiter: YouTubeRateLimiter = Depends(get_youtube_rate_limiter),
    _current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Semantic/Hybrid YouTube video arama sistemi
    search_mode: 'semantic' (default), 'keyword', 'hybrid'

    Task 12: Rate limiting (10 req/min per IP) ve YouTube API quota tracking
    """
    try:
        search_mode = request.search_mode.lower()
        logger.info(
            f"YouTube arama başlatıldı ({search_mode}): {request.subject}, {request.difficulty}, {request.exam_type}"
        )

        if search_mode == "semantic":
            # Semantic search (embedding-based)
            semantic_matches = await semantic_search.semantic_search_videos(
                subject=request.subject,
                exam_type=request.exam_type,
                difficulty=request.difficulty,
                max_results=request.max_results,
                query_text=request.custom_query,
            )

            # Convert to VideoResponse
            response_videos = []
            for match in semantic_matches:
                response_video = VideoResponse(
                    video_id=match.video_id,
                    title=match.title,
                    channel=match.channel,
                    channel_id=match.channel_id,
                    duration=match.duration,
                    view_count=match.view_count,
                    upload_date=match.upload_date,
                    thumbnail=match.thumbnail,
                    quality_score=match.combined_score,  # Use combined semantic score
                    subject=request.subject,
                    difficulty=request.difficulty,
                    exam_type=request.exam_type,
                    url=match.url,
                )
                response_videos.append(response_video)

            logger.info(
                f"Semantic arama tamamlandı: {len(response_videos)} semantic match"
            )

        elif search_mode == "keyword":
            # Traditional keyword search
            videos = await real_youtube.search_videos(
                subject=request.subject,
                exam_type=request.exam_type,
                difficulty=request.difficulty,
                max_results=request.max_results,
            )

            response_videos = []
            for video in videos:
                response_video = VideoResponse(
                    video_id=video.video_id,
                    title=video.title,
                    channel=video.channel,
                    channel_id=video.channel_id,
                    duration=video.duration,
                    view_count=video.view_count,
                    upload_date=video.upload_date,
                    thumbnail=video.thumbnail,
                    quality_score=video.quality_score,
                    subject=request.subject,
                    difficulty=request.difficulty,
                    exam_type=request.exam_type,
                    url=video.url,
                )
                response_videos.append(response_video)

            logger.info(
                f"Keyword arama tamamlandı: {len(response_videos)} keyword match"
            )

        else:  # hybrid
            # Hybrid: Semantic + Keyword combined
            semantic_matches = await semantic_search.semantic_search_videos(
                subject=request.subject,
                exam_type=request.exam_type,
                difficulty=request.difficulty,
                max_results=request.max_results // 2,
                query_text=request.custom_query,
            )

            keyword_videos = await real_youtube.search_videos(
                subject=request.subject,
                exam_type=request.exam_type,
                difficulty=request.difficulty,
                max_results=request.max_results // 2,
            )

            # Combine and deduplicate
            all_videos = {}

            # Add semantic matches
            for match in semantic_matches:
                all_videos[match.video_id] = VideoResponse(
                    video_id=match.video_id,
                    title=match.title,
                    channel=match.channel,
                    channel_id=match.channel_id,
                    duration=match.duration,
                    view_count=match.view_count,
                    upload_date=match.upload_date,
                    thumbnail=match.thumbnail,
                    quality_score=match.combined_score + 0.1,  # Semantic bonus
                    subject=request.subject,
                    difficulty=request.difficulty,
                    exam_type=request.exam_type,
                    url=match.url,
                )

            # Add keyword matches
            for video in keyword_videos:
                if video.video_id not in all_videos:
                    all_videos[video.video_id] = VideoResponse(
                        video_id=video.video_id,
                        title=video.title,
                        channel=video.channel,
                        channel_id=video.channel_id,
                        duration=video.duration,
                        view_count=video.view_count,
                        upload_date=video.upload_date,
                        thumbnail=video.thumbnail,
                        quality_score=video.quality_score,
                        subject=request.subject,
                        difficulty=request.difficulty,
                        exam_type=request.exam_type,
                        url=video.url,
                    )

            # Sort by quality score
            response_videos = sorted(
                all_videos.values(), key=lambda x: x.quality_score, reverse=True
            )[: request.max_results]

            logger.info(f"Hybrid arama tamamlandı: {len(response_videos)} hybrid match")

        # Task 12: YouTube API quota tracking
        # Consume quota for search operation (100 units per search)
        if search_mode in ["keyword", "hybrid"]:
            # Keyword search uses YouTube API
            quota_consumed = (
                100 if search_mode == "keyword" else 200
            )  # Hybrid uses 2 searches
            await youtube_rate_limiter.consume_quota(
                operation="search", quota_amount=quota_consumed
            )

        # Add rate limit headers
        quota_info = await youtube_rate_limiter.get_quota_info()
        response.headers["X-RateLimit-Limit"] = "10"
        response.headers["X-RateLimit-Window"] = "60"
        response.headers["X-YouTube-Quota-Remaining"] = str(quota_info.remaining_quota)
        response.headers["X-YouTube-Quota-Used"] = str(quota_info.used_quota)

        return response_videos

    except Exception as e:
        logger.error(f"YouTube arama hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# CORS preflight handler for /recommendations
@router.options("/recommendations")
@limiter.exempt  # Exempt from rate limiting
async def recommendations_preflight():
    """Handle CORS preflight requests for /recommendations endpoint"""
    return FastAPIResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID",
            "Access-Control-Max-Age": "86400",
        },
    )


@router.post("/recommendations", response_model=list[RecommendationResponse])
@limiter.limit("10/minute")  # Task 12: 10 req/min per IP
async def get_personalized_recommendations(
    request_obj: Request,
    response: FastAPIResponse,
    request: StudentProfileRequest,
    video_recommendation_service: "VideoRecommendationService" = Depends(
        lambda: get_video_recommendation_service()
    ),
    youtube_rate_limiter: YouTubeRateLimiter = Depends(get_youtube_rate_limiter),
    _current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Kişiselleştirilmiş video önerileri - VideoRecommendationService ile

    Requirements: 1.1, 1.2, 1.6, 2.1, 5.1, 5.2, 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8, 7.9

    Features:
    - Request ID generation (UUID)
    - Structured logging (request start, end, error)
    - Response time measurement
    - Cache hit/miss bilgisi
    - User-friendly error messages
    - Dependency injection ile VideoRecommendationService entegrasyonu
    - Metrics collection (Prometheus)
    - Rate limiting (10 req/min per IP) - Task 12
    - YouTube API quota tracking - Task 12

    Args:
        request_obj: FastAPI Request object (for rate limiting)
        request: Student profile request (goals, currentLevel, learningStyle, preferences)
        video_recommendation_service: Video recommendation service (injected)
        youtube_rate_limiter: YouTube rate limiter (injected)

    Returns:
        List[RecommendationResponse]: Kişiselleştirilmiş video önerileri
    """
    import uuid

    # 1. Request ID generation (UUID)
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Get metrics collector
    metrics_collector = get_metrics_collector()

    # Start request tracking
    metrics_collector.start_request(request_id, endpoint="/api/youtube/recommendations")

    # 2. YouTube API quota kontrolü (Task 12 - Requirement 7.7)
    # Initialize rate limiter if needed
    if not youtube_rate_limiter._quota_info:
        await youtube_rate_limiter.initialize()

    # Quota bilgisini al
    quota_info = await youtube_rate_limiter.get_quota_info()

    # Quota uyarısı (log only, don't block)
    if quota_info.remaining_quota < 1000:
        logger.warning(
            f"[{request_id}] YouTube API quota düşük: {quota_info.remaining_quota} kaldı",
            extra={
                "request_id": request_id,
                "remaining_quota": quota_info.remaining_quota,
                "used_quota": quota_info.used_quota,
                "daily_limit": quota_info.daily_limit,
            },
        )

    # 3. Structured logging - Request start
    logger.info(
        f"[{request_id}] Video recommendations request started",
        extra={
            "request_id": request_id,
            "endpoint": "/api/youtube/recommendations",
            "goals": request.goals[:3],  # İlk 3 hedef
            "learning_style": request.learningStyle,
            "timestamp": datetime.now().isoformat(),
            "youtube_quota_remaining": quota_info.remaining_quota,
        },
    )

    try:
        # 3. Student profile oluştur
        from services.video_recommendation_service import StudentProfile

        student_profile = StudentProfile(
            goals=request.goals,
            currentLevel=request.currentLevel,
            learningStyle=request.learningStyle,
            preferences=request.preferences,
        )

        # 4. Video önerilerini al (VideoRecommendationService)
        recommendations = await video_recommendation_service.get_recommendations(
            student_profile=student_profile, request_id=request_id
        )

        # 5. Response formatına çevir
        response_recommendations = []

        for rec in recommendations:
            # Video responses oluştur
            video_responses = []
            for video in rec.videos:
                video_response = VideoResponse(
                    video_id=video.video_id,
                    title=video.title,
                    channel=video.channel,
                    channel_id=video.channel_id,
                    duration=video.duration,
                    view_count=video.view_count,
                    upload_date=video.upload_date,
                    thumbnail=video.thumbnail,
                    quality_score=video.quality_score,
                    subject=video.subject,
                    difficulty=video.difficulty,
                    exam_type=video.exam_type,
                    url=video.url,
                )
                video_responses.append(video_response)

            # Recommendation response oluştur (cache_hit ve response_time_ms dahil)
            recommendation_response = RecommendationResponse(
                subject_exam=rec.subject_exam,
                videos=video_responses,
                total_count=rec.total_count,
                cache_hit=rec.cache_hit,
                response_time_ms=rec.response_time_ms,
            )
            response_recommendations.append(recommendation_response)

        # 6. Response time measurement
        response_time_ms = int((time.time() - start_time) * 1000)

        # 7. Cache hit/miss bilgisi
        cache_hit = any(rec.cache_hit for rec in recommendations)
        total_videos = sum(rec.total_count for rec in recommendations)

        # 8. YouTube API quota tüketimi (Task 12 - Requirement 7.7)
        # Cache hit değilse quota tüket
        if not cache_hit:
            # Her hedef için yaklaşık 1 search operation (100 quota units)
            quota_consumed = len(request.goals) * 100
            await youtube_rate_limiter.consume_quota(
                operation="search", quota_amount=quota_consumed
            )
            logger.debug(
                f"[{request_id}] YouTube API quota tüketildi: {quota_consumed} units",
                extra={
                    "request_id": request_id,
                    "quota_consumed": quota_consumed,
                    "goals_count": len(request.goals),
                },
            )

        # 9. End request tracking (success)
        metrics_collector.end_request(
            request_id=request_id,
            success=True,
            cache_hit=cache_hit,
            endpoint="/api/youtube/recommendations",
        )

        # 10. Rate limit headers ekle (Task 12 - Requirement 7.5)
        # Get updated quota info
        updated_quota_info = await youtube_rate_limiter.get_quota_info()

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = "10"  # 10 req/min
        response.headers["X-RateLimit-Window"] = "60"  # 60 seconds
        response.headers["X-YouTube-Quota-Remaining"] = str(
            updated_quota_info.remaining_quota
        )
        response.headers["X-YouTube-Quota-Used"] = str(updated_quota_info.used_quota)
        response.headers["X-YouTube-Quota-Limit"] = str(updated_quota_info.daily_limit)
        response.headers["X-YouTube-Quota-Reset"] = (
            updated_quota_info.reset_time.isoformat()
        )
        response.headers["X-Cache-Hit"] = str(cache_hit).lower()

        # 11. Structured logging - Request end (success)
        logger.info(
            f"[{request_id}] Video recommendations request completed successfully",
            extra={
                "request_id": request_id,
                "response_time_ms": response_time_ms,
                "cache_hit": cache_hit,
                "total_videos": total_videos,
                "recommendations_count": len(response_recommendations),
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "youtube_quota_remaining": updated_quota_info.remaining_quota,
            },
        )

        return response_recommendations

    except Exception as e:
        # 9. Response time measurement (error case)
        response_time_ms = int((time.time() - start_time) * 1000)

        # 10. End request tracking (error)
        metrics_collector.end_request(
            request_id=request_id,
            success=False,
            cache_hit=False,
            endpoint="/api/youtube/recommendations",
        )

        # 11. Record error
        error_type = type(e).__name__
        metrics_collector.record_error(
            request_id=request_id,
            error_type=error_type,
            endpoint="/api/youtube/recommendations",
        )

        # 12. Structured logging - Request end (error)
        logger.error(
            f"[{request_id}] Video recommendations request failed",
            extra={
                "request_id": request_id,
                "response_time_ms": response_time_ms,
                "error_type": error_type,
                "error_message": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            },
            exc_info=True,
        )

        # 13. User-friendly error messages
        user_message = "Video önerileri hazırlanırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."

        # Specific error messages
        if "cache" in str(e).lower():
            user_message = "Önbellek sisteminde geçici bir sorun var. Lütfen birkaç saniye sonra tekrar deneyin."
        elif "youtube" in str(e).lower() or "api" in str(e).lower():
            user_message = "Video arama servisi şu anda yavaş yanıt veriyor. Lütfen bekleyin veya tekrar deneyin."
        elif "timeout" in str(e).lower():
            user_message = (
                "Video arama işlemi zaman aşımına uğradı. Lütfen tekrar deneyin."
            )
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            user_message = (
                "Ağ bağlantısı sorunu yaşanıyor. İnternet bağlantınızı kontrol edin."
            )

        raise HTTPException(
            status_code=500,
            detail={
                "message": user_message,
                "request_id": request_id,
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat(),
            },
        )


@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_stats(
    discovery: YouTubeDiscovery = Depends(get_discovery_service),
):
    """
    YouTube arama sistemi istatistikleri
    """
    try:
        import sqlite3

        # Cache istatistiklerini al
        conn = sqlite3.connect(discovery.db_path)
        try:
            # Total cached videos
            cursor = conn.execute("SELECT COUNT(*) FROM video_cache")
            total_cached = cursor.fetchone()[0]

            # Last update
            cursor = conn.execute("SELECT MAX(last_updated) FROM video_cache")
            last_update_str = cursor.fetchone()[0]
            last_update = (
                datetime.fromisoformat(last_update_str)
                if last_update_str
                else datetime.now()
            )
        finally:
            conn.close()

        # Cache hit rate hesapla (basit implementation)
        cache_hit_rate = 0.85  # Placeholder

        return SearchStatsResponse(
            total_cached_videos=total_cached,
            cache_hit_rate=cache_hit_rate,
            last_update=last_update,
            supported_subjects=[subject.value for subject in SubjectType],
            supported_exam_types=[exam.value for exam in ExamType],
        )

    except Exception as e:
        logger.error(f"Stats alma hatası: {e}")
        raise HTTPException(status_code=500, detail="İstatistikler alınamadı")


@router.post("/cache/clear")
async def clear_cache(
    discovery: YouTubeDiscovery = Depends(get_discovery_service),
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    Video cache'ini temizle (admin only)
    """
    try:
        import sqlite3

        with sqlite3.connect(discovery.db_path) as conn:
            conn.execute("DELETE FROM video_cache")
            conn.execute("DELETE FROM search_cache")
            conn.commit()

        return {"message": "Cache başarıyla temizlendi"}

    except Exception as e:
        logger.error(f"Cache temizleme hatası: {e}")
        raise HTTPException(status_code=500, detail="Cache temizlenemedi")


@router.get("/subjects")
async def get_supported_subjects():
    """
    Desteklenen konuları listele
    """
    return {
        "subjects": [
            {"value": subject.value, "label": subject.value.title()}
            for subject in SubjectType
        ],
        "difficulties": [
            {"value": diff.value, "label": diff.value.title()}
            for diff in DifficultyLevel
        ],
        "exam_types": [{"value": exam.value, "label": exam.value} for exam in ExamType],
    }


@router.get("/test")
async def test_endpoint():
    """Test endpoint - instant response"""
    return {"status": "OK", "message": "YouTube Discovery API çalışıyor!"}


@router.get("/health", response_model=SystemHealthResponse)
async def health_check(
    health_service: HealthCheckService = Depends(get_health_service),
):
    """
    YouTube Discovery API sağlık kontrolü

    Requirements: 4.1, 4.2, 4.3, 4.14

    Kontrol edilen bileşenler:
    - YouTube API (API key ve bağlantı durumu)
    - Database (PostgreSQL/SQLite bağlantısı)
    - Redis Cache (bağlantı ve performans)

    Response time hedefi: < 500ms

    Returns:
        SystemHealthResponse: Detaylı sistem sağlık durumu
    """
    try:
        start_time = time.time()

        # Sağlık kontrolü yap
        system_health = await health_service.check_health()

        # Response time kontrolü
        response_time = (time.time() - start_time) * 1000
        if response_time > 500:
            logger.warning(
                f"Health check yanıt süresi hedefi aşıldı: {response_time:.2f}ms > 500ms"
            )

        # Response modeline çevir
        components_response = [
            ComponentHealthResponse(
                name=comp.name,
                status=comp.status.value,
                response_time_ms=comp.response_time_ms,
                error_message=comp.error_message,
                last_check=comp.last_check.isoformat() if comp.last_check else None,
                details=comp.details or {},
            )
            for comp in system_health.components
        ]

        response = SystemHealthResponse(
            overall_status=system_health.overall_status.value,
            components=components_response,
            metrics=system_health.metrics,
            timestamp=system_health.timestamp.isoformat(),
        )

        logger.info(
            f"Health check tamamlandı: {system_health.overall_status.value} "
            f"({response_time:.2f}ms)"
        )

        return response

    except Exception as e:
        logger.error(f"Health check hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/background/update")
async def start_background_update(
    background_tasks: BackgroundTasks,
    discovery: YouTubeDiscovery = Depends(get_discovery_service),
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    Arka planda video database güncellemesi başlat (admin only)
    """

    async def update_video_database():
        """Arka plan görevi: Video database güncelle"""
        try:
            # Her konu ve zorluk kombinasyonu için güncelleme
            for subject in SubjectType:
                for difficulty in DifficultyLevel:
                    for exam_type in [ExamType.TYT, ExamType.AYT]:
                        await discovery.discover_videos(
                            subject=subject,
                            difficulty=difficulty,
                            exam_type=exam_type,
                            max_results=20,
                        )
                        await asyncio.sleep(2)  # Rate limiting

            logger.info("Arka plan video database güncellemesi tamamlandı")

        except Exception as e:
            logger.error(f"Arka plan güncelleme hatası: {e}")

    background_tasks.add_task(update_video_database)

    return {"message": "Arka plan güncellemesi başlatıldı"}


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """
    Prometheus formatında metrikleri döndür

    Requirements: 4.4, 4.10, 4.14, 5.12

    Metrics:
    - video_requests_total: Toplam video isteği sayısı
    - video_response_time_seconds: Video yanıt süresi (histogram - P50, P95, P99)
    - cache_hit_rate: Cache hit oranı
    - youtube_api_quota_used: YouTube API quota kullanımı
    - video_errors_total: Toplam hata sayısı
    - active_video_requests: Aktif istek sayısı

    Returns:
        Prometheus format metrics (text/plain)
    """
    from fastapi.responses import Response

    try:
        metrics_collector = get_metrics_collector()

        # Prometheus formatında metrikleri al
        metrics_data = metrics_collector.get_prometheus_metrics()
        content_type = metrics_collector.get_metrics_content_type()

        return Response(content=metrics_data, media_type=content_type)

    except Exception as e:
        logger.error(f"Prometheus metrics hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/metrics/snapshot", response_model=MetricsSnapshotResponse)
async def get_metrics_snapshot():
    """
    Metriklerin anlık görüntüsünü al (JSON format)

    Requirements: 4.4, 4.10, 4.14, 5.12

    Returns:
        MetricsSnapshotResponse: Detaylı metrik snapshot
    """
    try:
        metrics_collector = get_metrics_collector()

        # Snapshot al
        snapshot = metrics_collector.get_snapshot()

        # Response modeline çevir
        response = MetricsSnapshotResponse(
            timestamp=snapshot.timestamp.isoformat(),
            total_requests=snapshot.total_requests,
            successful_requests=snapshot.successful_requests,
            failed_requests=snapshot.failed_requests,
            cache_hits=snapshot.cache_hits,
            cache_misses=snapshot.cache_misses,
            avg_response_time=snapshot.avg_response_time,
            p50_response_time=snapshot.p50_response_time,
            p95_response_time=snapshot.p95_response_time,
            p99_response_time=snapshot.p99_response_time,
            youtube_api_quota_used=snapshot.youtube_api_quota_used,
            error_rate=snapshot.error_rate,
            cache_hit_rate=snapshot.cache_hit_rate,
        )

        logger.info(
            f"Metrics snapshot: {snapshot.total_requests} requests, "
            f"{snapshot.cache_hit_rate:.2%} cache hit rate, "
            f"{snapshot.avg_response_time:.3f}s avg response time"
        )

        return response

    except Exception as e:
        logger.error(f"Metrics snapshot hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Cleanup middleware
@router.on_event("shutdown")
async def cleanup_discovery():
    """Discovery service cleanup"""
    discovery = get_youtube_discovery()
    await discovery.close_session()
