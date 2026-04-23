"""
Structured Logger Usage Examples
=================================

Bu dosya, structured_logger.py modülünün nasıl kullanılacağını gösteren örnekler içerir.
Video API ve diğer servisler için logging best practices.
"""

import time
import traceback

from core.structured_logger import (
    get_logger,
    log_api_request,
    log_api_response,
    log_error_with_context,
)

# ==================== BASIC USAGE ====================


def example_basic_logging():
    """Temel logging kullanımı"""
    logger = get_logger(__name__)

    # Info log
    logger.info("Uygulama başlatıldı")

    # Debug log
    logger.debug("Debug bilgisi", extra={"config": "loaded"})

    # Warning log
    logger.warning("Uyarı mesajı", extra={"threshold": 80})

    # Error log
    logger.error("Hata oluştu", extra={"error_code": "ERR_500"})

    # Critical log
    logger.critical("Kritik hata!", extra={"system": "database"})


# ==================== VIDEO API REQUEST LOGGING ====================


def example_video_api_request_logging():
    """Video API request logging örneği"""
    logger = get_logger("video_api")

    # Request başlangıcı
    request_id = "abc-123-def-456"
    student_profile = {
        "goals": ["TYT Matematik", "TYT Fizik"],
        "currentLevel": {"matematik": 50, "fizik": 60},
        "learningStyle": "visual",
    }

    # Method 1: Helper function kullanarak
    log_api_request(
        logger,
        method="POST",
        path="/api/youtube/recommendations",
        request_id=request_id,
        profile=student_profile,
    )

    # Method 2: Logger convenience method kullanarak
    logger.log_request(
        request_id=request_id,
        endpoint="/api/youtube/recommendations",
        method="POST",
        profile=student_profile,
        user_id=123,
    )


# ==================== VIDEO API RESPONSE LOGGING ====================


def example_video_api_response_logging():
    """Video API response logging örneği"""
    logger = get_logger("video_api")

    request_id = "abc-123-def-456"
    start_time = time.time()

    # ... API işlemleri ...

    response_time = (time.time() - start_time) * 1000  # milliseconds

    # Başarılı response (cache hit)
    log_api_response(
        logger,
        method="POST",
        path="/api/youtube/recommendations",
        status_code=200,
        duration_ms=response_time,
        request_id=request_id,
        cache_hit=True,
        video_count=15,
    )

    # Başarılı response (cache miss)
    logger.log_response(
        request_id=request_id,
        endpoint="/api/youtube/recommendations",
        status=200,
        response_time=response_time,
        cache_hit=False,
        video_count=15,
        discovery_time_ms=2500,
    )


# ==================== ERROR LOGGING ====================


def example_error_logging():
    """Error logging örneği"""
    logger = get_logger("video_api")
    request_id = "abc-123-def-456"

    try:
        # Hata oluşturan kod
        raise ValueError("YouTube API rate limit exceeded")

    except Exception as e:
        # Method 1: Helper function ile
        log_error_with_context(
            logger,
            error=e,
            context="video_discovery",
            request_id=request_id,
            include_stack_trace=True,
            quota_remaining=0,
            retry_after=3600,
        )

        # Method 2: Logger convenience method ile
        logger.log_error_context(
            error_type=type(e).__name__,
            error_message=str(e),
            context="video_discovery",
            request_id=request_id,
            stack_trace=traceback.format_exc(),
            quota_remaining=0,
        )


# ==================== CONTEXT BINDING ====================


def example_context_binding():
    """Context binding örneği - tüm loglara otomatik eklenir"""
    logger = get_logger("video_service")

    # Request ID'yi tüm loglara bind et
    logger = logger.bind(request_id="abc-123", user_id=456)

    # Bu loglar otomatik olarak request_id ve user_id içerecek
    logger.info("Video arama başladı")
    logger.info("Cache kontrol ediliyor")
    logger.info("YouTube API çağrılıyor")

    # Context'i kaldır
    logger = logger.unbind("request_id", "user_id")


# ==================== FULL VIDEO API FLOW ====================


def example_full_video_api_flow():
    """Tam video API flow logging örneği"""
    logger = get_logger("video_recommendation_service")

    # 1. Request başlangıcı
    request_id = "req-2024-001"
    student_profile = {"goals": ["TYT Matematik"], "currentLevel": {"matematik": 50}}

    logger.log_request(
        request_id=request_id,
        endpoint="/api/youtube/recommendations",
        profile=student_profile,
    )

    start_time = time.time()

    try:
        # 2. Cache kontrolü
        logger.info(
            "cache_check_started",
            request_id=request_id,
            cache_key="profile_hash_abc123",
        )

        cache_hit = False  # Örnek

        if cache_hit:
            logger.info(
                "cache_hit", request_id=request_id, cache_key="profile_hash_abc123"
            )
        else:
            logger.info(
                "cache_miss", request_id=request_id, cache_key="profile_hash_abc123"
            )

            # 3. Video discovery
            logger.info(
                "video_discovery_started",
                request_id=request_id,
                subject="matematik",
                difficulty="orta",
            )

            # 4. YouTube API çağrısı
            logger.debug(
                "youtube_api_call",
                request_id=request_id,
                query="TYT matematik orta seviye",
                max_results=10,
            )

            # 5. Filtreleme
            logger.info(
                "video_filtering_started",
                request_id=request_id,
                total_videos=25,
                min_relevance=0.7,
            )

            logger.info(
                "video_filtering_completed",
                request_id=request_id,
                filtered_videos=15,
                removed_videos=10,
            )

        # 6. Response başarılı
        response_time = (time.time() - start_time) * 1000

        logger.log_response(
            request_id=request_id,
            endpoint="/api/youtube/recommendations",
            status=200,
            response_time=response_time,
            cache_hit=cache_hit,
            video_count=15,
        )

    except Exception as e:
        # 7. Hata durumu
        response_time = (time.time() - start_time) * 1000

        logger.log_error_context(
            error_type=type(e).__name__,
            error_message=str(e),
            context="video_recommendation_flow",
            request_id=request_id,
            stack_trace=traceback.format_exc(),
        )

        logger.log_response(
            request_id=request_id,
            endpoint="/api/youtube/recommendations",
            status=500,
            response_time=response_time,
            cache_hit=False,
            error=str(e),
        )


# ==================== PERFORMANCE MONITORING ====================


def example_performance_monitoring():
    """Performance monitoring örneği"""
    logger = get_logger("performance")

    request_id = "perf-001"

    # Slow query warning
    query_time = 5200  # ms
    if query_time > 5000:
        logger.warning(
            "slow_query_detected",
            request_id=request_id,
            query_time_ms=query_time,
            threshold_ms=5000,
            query="SELECT * FROM videos WHERE ...",
        )

    # Cache performance
    cache_hit_rate = 0.65
    if cache_hit_rate < 0.8:
        logger.warning(
            "low_cache_hit_rate",
            cache_hit_rate=cache_hit_rate,
            target_rate=0.8,
            recommendation="Consider cache warming strategy",
        )


# ==================== STRUCTURED DATA LOGGING ====================


def example_structured_data():
    """Structured data logging örneği"""
    logger = get_logger("analytics")

    # Video quality metrics
    logger.info(
        "video_quality_metrics",
        video_id="abc123",
        quality_score=0.85,
        relevance_score=0.92,
        language_score=0.98,
        difficulty_match=0.75,
        view_count=15000,
        like_ratio=0.95,
    )

    # Student interaction
    logger.info(
        "student_video_interaction",
        student_id=123,
        video_id="abc123",
        action="watched",
        watch_duration_seconds=450,
        completion_rate=0.75,
        liked=True,
    )


if __name__ == "__main__":
    print("Structured Logger Examples")
    print("=" * 50)
    print("\nBu dosya örnek kodlar içerir.")
    print("Gerçek kullanım için ilgili servislerde import edin.\n")

    # Örnekleri çalıştır
    example_basic_logging()
    print("\n" + "=" * 50 + "\n")

    example_video_api_request_logging()
    print("\n" + "=" * 50 + "\n")

    example_full_video_api_flow()
