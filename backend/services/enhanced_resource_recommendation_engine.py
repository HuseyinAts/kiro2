"""
Enhanced Resource Recommendation Engine
Tüm filtreleri ve skorlayıcıları entegre ederek kaliteli video önerileri oluşturur
Teknofest 2025 - Eğitim Eylemci Projesi

RECOMMENDATION SERVICE HIERARCHY (2025-01-24):
Bu proje 4 oneri servisi iceriyor:

1. CONTENT RECOMMENDATIONS (Genel):
   - content_recommendation_service.py - Hybrid filtering (REQ-4)

2. VIDEO RECOMMENDATIONS (YouTube):
   - video_recommendation_service.py - Ana orchestrator (caching)
   - enhanced_resource_recommendation_engine.py (BU DOSYA) - Quality scoring
   - video_recommendation_monitoring.py - Monitoring

3. YOUTUBE SEARCH:
   - semantic_youtube_search.py - Semantic search
   - advanced_youtube_search.py - Advanced filters

BU DOSYANIN ROLU:
- TurkishContentFilter entegrasyonu
- SubjectRelevanceScorer entegrasyonu
- VideoQualityValidator entegrasyonu
- Rate limiting
- Error handling

REFACTORING NEEDED:
Bu dosya 1000+ satir. Bolunmesi onerilen:
1. recommendation_filters.py - Filtering logic
2. recommendation_scorers.py - Scoring logic
3. recommendation_orchestrator.py - Orchestration
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from integrations.youtube_service import YouTubeService, YouTubeVideo
from services.turkish_content_filter import (
    TurkishContentFilter,
)
from services.subject_relevance_scorer import (
    SubjectRelevanceScorer,
)
from services.video_quality_validator import (
    VideoQualityValidator,
    VideoAccessibilityResult,
)
from services.youtube_error_handlers import (
    YouTubeAPIErrorHandler,
    ValidationErrorHandler,
    TimeoutHandler,
    QuotaExceededError,
    InvalidAPIKeyError,
    RateLimitError,
)
from core.cache import cache_manager
from services.video_recommendation_monitoring import (
    get_video_recommendation_monitor,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    API rate limiting için rate limiter

    Belirli bir zaman diliminde maksimum istek sayısını sınırlar.
    """

    def __init__(self, max_requests_per_second: int = 10):
        """
        RateLimiter'ı başlat

        Args:
            max_requests_per_second: Saniyede maksimum istek sayısı
        """
        self.max_requests = max_requests_per_second
        self.request_times: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """
        Rate limit kontrolü yap ve gerekirse bekle

        Bu metod çağrıldığında, rate limit aşılmışsa
        yeterli süre geçene kadar bekler.

        FIX: Lock sleep sırasında tutulmuyor - bu performans için kritik
        FIX: time.monotonic() kullanarak system clock değişikliklerinden etkilenmemesi sağlandı
        """
        wait_time = 0.0

        # 1. Lock içinde wait_time hesapla
        async with self._lock:
            now = time.monotonic()

            # 1 saniyeden eski istekleri temizle
            self.request_times = [t for t in self.request_times if now - t < 1.0]

            # Limit kontrolü
            if len(self.request_times) >= self.max_requests:
                # En eski isteğin üzerinden 1 saniye geçmesini bekle
                wait_time = 1.0 - (now - self.request_times[0])

        # 2. Lock DIŞINDA bekle - diğer istekler bloklanmasın
        if wait_time > 0:
            logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        # 3. Lock içinde isteği kaydet
        async with self._lock:
            now = time.monotonic()
            # Tekrar temizle (bekleme sırasında eskimiş olabilir)
            self.request_times = [t for t in self.request_times if now - t < 1.0]
            self.request_times.append(time.monotonic())

    def get_stats(self) -> Dict[str, Any]:
        """
        Rate limiter istatistiklerini al

        Returns:
            İstatistik dictionary'si
        """
        now = time.monotonic()
        recent_requests = [t for t in self.request_times if now - t < 1.0]

        return {
            "max_requests_per_second": self.max_requests,
            "current_requests_in_window": len(recent_requests),
            "available_capacity": self.max_requests - len(recent_requests),
        }


@dataclass
class RecommendedVideo:
    """Önerilen video modeli"""

    video_id: str
    title: str
    channel_name: str
    channel_id: str
    description: str
    thumbnail_url: str
    duration: str
    duration_minutes: int
    view_count: int
    like_count: int
    upload_date: str
    url: str

    # Scores
    turkish_score: float
    relevance_score: float
    quality_score: float
    final_score: float

    # Validation
    is_accessible: bool
    is_embeddable: bool
    is_turkish: bool

    # Metadata
    tags: List[str]
    caption_available: bool
    definition: str  # 'hd' or 'sd'


class EnhancedResourceRecommendationEngine:
    """
    Gelişmiş kaynak öneri motoru

    Video önerilerini Türkçe filtresi, konu uygunluğu ve kalite kontrolünden
    geçirerek en uygun eğitim videolarını önerir.
    """

    def __init__(self):
        """EnhancedResourceRecommendationEngine'i başlat"""
        self.turkish_filter = TurkishContentFilter()
        self.relevance_scorer = SubjectRelevanceScorer()
        self.quality_validator = VideoQualityValidator()
        self.youtube_service = YouTubeService()

        # Error handlers
        self.youtube_error_handler = YouTubeAPIErrorHandler()
        self.validation_error_handler = ValidationErrorHandler()
        self.timeout_handler = TimeoutHandler(default_timeout=5)

        # Performance optimizations
        self.cache_manager = cache_manager
        self.rate_limiter = RateLimiter(max_requests_per_second=10)
        self.cache_ttl = 3600  # 1 saat

        # Monitoring
        self.monitor = get_video_recommendation_monitor()

        # Threshold değerleri (Demo için düşürüldü - Türkçe video bulunabilirliği için)
        self.min_turkish_score = 0.2
        self.min_relevance_score = 0.4  # Demo için düşürüldü
        self.min_quality_score = 0.2

        # Skorlama ağırlıkları
        self.weights = {
            "turkish": 0.25,
            "relevance": 0.40,
            "quality": 0.25,
            "accessibility": 0.10,
        }

        logger.info("Enhanced Resource Recommendation Engine initialized")

    async def get_recommended_videos(
        self,
        subject: str,
        topic: Optional[str] = None,
        difficulty: str = "orta",
        max_results: int = 10,
        student_profile: Optional[Dict] = None,
    ) -> List[RecommendedVideo]:
        """
        Filtrelenmiş ve skorlanmış video önerileri döner

        Pipeline:
        1. Cache kontrolü (TTL: 1 saat)
        2. YouTube'dan aday videolar al (max_results * 3)
        3. Türkçe filtresi uygula (min score: 0.2)
        4. Konu uygunluğu skorla (min score: 0.4)
        5. Erişilebilirlik doğrula (paralel)
        6. Kalite skorla (min score: 0.2)
        7. Final skorlama ve sıralama
        8. Cache'e kaydet ve döndür

        Args:
            subject: Hedef ders (matematik, fizik, kimya, vb.)
            topic: Hedef konu (türev, hareket, atom, vb.) - opsiyonel
            difficulty: Zorluk seviyesi (kolay, orta, zor)
            max_results: Maksimum sonuç sayısı
            student_profile: Öğrenci profili (opsiyonel)

        Returns:
            List[RecommendedVideo]: Skorlanmış ve sıralanmış videolar
        """
        try:
            # Monitoring: Request başlangıcı
            request_start_time = self.monitor.log_request_start()

            logger.info(
                f"Getting recommendations for subject='{subject}', topic='{topic}', "
                f"difficulty='{difficulty}', max_results={max_results}"
            )

            # 1. Cache kontrolü
            cache_key = self._generate_cache_key(
                subject, topic, difficulty, max_results, student_profile
            )
            cached_videos = await self.cache_manager.get(cache_key)

            if cached_videos:
                logger.info(
                    f"Cache HIT for key '{cache_key}' - returning {len(cached_videos)} videos"
                )
                # Cache'den gelen dict'leri RecommendedVideo'ya çevir
                result_videos = [
                    self._dict_to_recommended_video(v) for v in cached_videos
                ]

                # Monitoring: Request bitişi (cache hit)
                self.monitor.log_request_end(
                    request_start_time,
                    success=True,
                    cache_hit=True,
                    video_count=len(result_videos),
                )

                return result_videos

            # Context for error handling
            context = {
                "subject": subject,
                "topic": topic,
                "difficulty": difficulty,
                "max_results": max_results,
            }

            try:
                # 1. YouTube'dan aday videolar al (3x fazla) - timeout ile
                search_query = self._build_search_query(subject, topic, difficulty)

                # Monitoring: YouTube API çağrısı
                self.monitor.log_youtube_api_call(success=True)

                candidate_videos = await self.timeout_handler.with_timeout(
                    self.youtube_service.search_educational_videos(
                        query=search_query,
                        subject=subject,
                        language="tr",
                        max_results=max_results * 3,
                        order="relevance",
                    ),
                    timeout_seconds=10,
                    fallback_value=[],
                )

                if not candidate_videos:
                    logger.warning(f"No candidate videos found for '{search_query}'")
                    # Monitoring: Request bitişi (başarısız)
                    self.monitor.log_request_end(
                        request_start_time, success=False, cache_hit=False
                    )
                    return []

                logger.info(f"Found {len(candidate_videos)} candidate videos")

            except (QuotaExceededError, InvalidAPIKeyError, RateLimitError) as e:
                # YouTube API hatası - fallback kullan
                logger.error(f"YouTube API error: {str(e)}")

                # Monitoring: YouTube API hatası
                self.monitor.log_youtube_api_call(success=False)
                if isinstance(e, QuotaExceededError):
                    self.monitor.log_youtube_quota_exceeded()
                elif isinstance(e, RateLimitError):
                    self.monitor.log_youtube_rate_limit()

                self.monitor.log_error(
                    error_type=type(e).__name__, error_message=str(e), context=context
                )

                fallback_response = await self.youtube_error_handler.handle_api_error(
                    e, context
                )

                if fallback_response.videos:
                    logger.info(
                        f"Using {len(fallback_response.videos)} videos from {fallback_response.source}"
                    )
                    # Fallback videoları RecommendedVideo formatına çevir
                    result_videos = self._convert_fallback_videos(
                        fallback_response.videos
                    )

                    # Monitoring: Request bitişi (fallback ile başarılı)
                    self.monitor.log_request_end(
                        request_start_time,
                        success=True,
                        cache_hit=False,
                        video_count=len(result_videos),
                    )

                    return result_videos
                else:
                    logger.warning("No fallback videos available")
                    # Monitoring: Request bitişi (başarısız)
                    self.monitor.log_request_end(
                        request_start_time, success=False, cache_hit=False
                    )
                    return []

            # 2-6. Pipeline: Filter → Score → Validate
            recommended_videos = await self._process_video_pipeline(
                candidate_videos, subject, topic, student_profile
            )

            # 7. Top N video döndür
            top_videos = recommended_videos[:max_results]

            # 8. Cache'e kaydet (1 saat TTL)
            if top_videos:
                # RecommendedVideo'ları dict'e çevir (JSON serializable)
                videos_dict = [self._recommended_video_to_dict(v) for v in top_videos]
                await self.cache_manager.set(cache_key, videos_dict, ttl=self.cache_ttl)
                logger.info(f"Cached {len(top_videos)} videos with key '{cache_key}'")

            elapsed_time = time.time() - request_start_time
            logger.info(
                f"Returning {len(top_videos)} recommended videos "
                f"(filtered from {len(candidate_videos)} candidates) "
                f"in {elapsed_time:.2f}s"
            )

            # Monitoring: Request bitişi (başarılı)
            self.monitor.log_request_end(
                request_start_time,
                success=True,
                cache_hit=False,
                video_count=len(top_videos),
            )

            return top_videos

        except Exception as e:
            logger.error(f"Error getting recommended videos: {str(e)}")

            # Monitoring: Hata
            self.monitor.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                context={"subject": subject, "topic": topic},
            )

            # Monitoring: Request bitişi (başarısız)
            self.monitor.log_request_end(
                request_start_time, success=False, cache_hit=False
            )

            return []

    async def _process_video_pipeline(
        self,
        candidate_videos: List[YouTubeVideo],
        subject: str,
        topic: Optional[str],
        student_profile: Optional[Dict] = None,
    ) -> List[RecommendedVideo]:
        """
        Video işleme pipeline'ı (paralel işleme ile optimize edilmiş)

        Args:
            candidate_videos: Aday videolar
            subject: Hedef ders
            topic: Hedef konu
            student_profile: Öğrenci profili (öğrenme stili için)

        Returns:
            İşlenmiş ve skorlanmış videolar
        """
        recommended_videos = []

        # Paralel işleme için tasks (asyncio.gather ile)
        tasks = []
        for video in candidate_videos:
            # Rate limiting uygula
            await self.rate_limiter.acquire()
            task = self._process_single_video(video, subject, topic, student_profile)
            tasks.append(task)

        # Tüm videoları paralel işle
        logger.info(f"Processing {len(tasks)} videos in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Başarılı sonuçları topla
        for result in results:
            if isinstance(result, RecommendedVideo):
                recommended_videos.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Error processing video: {str(result)}")

        # Final skora göre sırala
        recommended_videos.sort(key=lambda v: v.final_score, reverse=True)

        # İstatistikler
        logger.info(
            f"Pipeline complete: {len(recommended_videos)}/{len(candidate_videos)} "
            f"videos passed all filters"
        )

        return recommended_videos

    async def _process_single_video(
        self,
        video: YouTubeVideo,
        subject: str,
        topic: Optional[str],
        student_profile: Optional[Dict] = None,
    ) -> Optional[RecommendedVideo]:
        """
        Tek bir videoyu işle

        Args:
            video: YouTube video
            subject: Hedef ders
            topic: Hedef konu

        Returns:
            RecommendedVideo veya None (filtrelendiyse)
        """
        try:
            # 1. Türkçe filtresi
            turkish_result = await self.turkish_filter.validate_turkish_content(
                video.title, video.description, video.channel_name
            )

            if (
                not turkish_result.is_turkish
                or turkish_result.confidence_score < self.min_turkish_score
            ):
                logger.debug(
                    f"Video '{video.title[:50]}...' filtered out: "
                    f"Turkish score {turkish_result.confidence_score:.2f} < {self.min_turkish_score}"
                )

                # Monitoring: Filtre sonucu
                self.monitor.log_filter_result(
                    "turkish",
                    passed=False,
                    score=turkish_result.confidence_score,
                    threshold=self.min_turkish_score,
                )

                # Monitoring: Validation başarısızlığı
                self.monitor.log_validation_failure(
                    video.video_id,
                    "turkish_filter_failed",
                    {
                        "score": turkish_result.confidence_score,
                        "threshold": self.min_turkish_score,
                    },
                    video_title=video.title,
                )

                # Validation hatası kaydet
                self.validation_error_handler.handle_validation_failure(
                    video.video_id,
                    "turkish_filter_failed",
                    {
                        "score": turkish_result.confidence_score,
                        "threshold": self.min_turkish_score,
                    },
                )
                return None

            # Monitoring: Türkçe filtresi geçti
            self.monitor.log_filter_result(
                "turkish",
                passed=True,
                score=turkish_result.confidence_score,
                threshold=self.min_turkish_score,
            )

            # 2. Konu uygunluğu skorlama
            relevance_result = await self.relevance_scorer.calculate_relevance_score(
                video.title, video.description, video.tags, subject, topic
            )

            if relevance_result.overall_score < self.min_relevance_score:
                logger.debug(
                    f"Video '{video.title[:50]}...' filtered out: "
                    f"Relevance score {relevance_result.overall_score:.2f} < {self.min_relevance_score}"
                )

                # Monitoring: Filtre sonucu
                self.monitor.log_filter_result(
                    "relevance",
                    passed=False,
                    score=relevance_result.overall_score,
                    threshold=self.min_relevance_score,
                )

                # Monitoring: Validation başarısızlığı
                self.monitor.log_validation_failure(
                    video.video_id,
                    "relevance_too_low",
                    {
                        "score": relevance_result.overall_score,
                        "threshold": self.min_relevance_score,
                    },
                    video_title=video.title,
                )

                # Validation hatası kaydet
                self.validation_error_handler.handle_validation_failure(
                    video.video_id,
                    "relevance_too_low",
                    {
                        "score": relevance_result.overall_score,
                        "threshold": self.min_relevance_score,
                    },
                )
                return None

            # Monitoring: Relevance filtresi geçti
            self.monitor.log_filter_result(
                "relevance",
                passed=True,
                score=relevance_result.overall_score,
                threshold=self.min_relevance_score,
            )

            # 3. Erişilebilirlik kontrolü
            accessibility_result = (
                await self.quality_validator.validate_video_accessibility(
                    video.video_id
                )
            )

            if not accessibility_result.is_accessible:
                logger.debug(
                    f"Video '{video.title[:50]}...' filtered out: "
                    f"Not accessible ({accessibility_result.error_reason})"
                )

                # Monitoring: Filtre sonucu
                self.monitor.log_filter_result("accessibility", passed=False)

                # Monitoring: Validation başarısızlığı
                self.monitor.log_validation_failure(
                    video.video_id,
                    "accessibility_failed",
                    {"reason": accessibility_result.error_reason},
                    video_title=video.title,
                )

                # Validation hatası kaydet
                self.validation_error_handler.handle_validation_failure(
                    video.video_id,
                    "accessibility_failed",
                    {"reason": accessibility_result.error_reason},
                )
                return None

            # Monitoring: Accessibility filtresi geçti
            self.monitor.log_filter_result("accessibility", passed=True)

            # 4. Kalite skorlama
            video_metadata = self._extract_video_metadata(video, accessibility_result)
            quality_score = await self.quality_validator.calculate_quality_score(
                video_metadata
            )

            if quality_score < self.min_quality_score:
                logger.debug(
                    f"Video '{video.title[:50]}...' filtered out: "
                    f"Quality score {quality_score:.2f} < {self.min_quality_score}"
                )

                # Monitoring: Filtre sonucu
                self.monitor.log_filter_result(
                    "quality",
                    passed=False,
                    score=quality_score,
                    threshold=self.min_quality_score,
                )

                # Monitoring: Validation başarısızlığı
                self.monitor.log_validation_failure(
                    video.video_id,
                    "quality_too_low",
                    {"score": quality_score, "threshold": self.min_quality_score},
                    video_title=video.title,
                )

                # Validation hatası kaydet
                self.validation_error_handler.handle_validation_failure(
                    video.video_id,
                    "quality_too_low",
                    {"score": quality_score, "threshold": self.min_quality_score},
                )
                return None

            # Monitoring: Quality filtresi geçti
            self.monitor.log_filter_result(
                "quality",
                passed=True,
                score=quality_score,
                threshold=self.min_quality_score,
            )

            # 5. Final skorlama (learning style bonus ile)
            learning_style = (
                student_profile.get("learning_style") if student_profile else None
            )
            has_captions = accessibility_result.has_captions
            has_visual_content = True  # Assume all videos have visual content

            final_score = self._calculate_final_score(
                turkish_result.confidence_score,
                relevance_result.overall_score,
                quality_score,
                accessibility_result.is_accessible,
                learning_style=learning_style,
                has_captions=has_captions,
                has_visual_content=has_visual_content,
            )

            # 6. RecommendedVideo oluştur
            recommended_video = RecommendedVideo(
                video_id=video.video_id,
                title=video.title,
                channel_name=video.channel_name,
                channel_id=video.channel_id,
                description=video.description,
                thumbnail_url=video.thumbnail_url,
                duration=video.duration or "PT0S",
                duration_minutes=video_metadata.get("duration_minutes", 0),
                view_count=video.view_count or 0,
                like_count=video.like_count or 0,
                upload_date=video.published_at.isoformat()
                if video.published_at
                else "",
                url=f"https://www.youtube.com/watch?v={video.video_id}",
                # Scores
                turkish_score=turkish_result.confidence_score,
                relevance_score=relevance_result.overall_score,
                quality_score=quality_score,
                final_score=final_score,
                # Validation
                is_accessible=accessibility_result.is_accessible,
                is_embeddable=accessibility_result.is_embeddable,
                is_turkish=turkish_result.is_turkish,
                # Metadata
                tags=video.tags,
                caption_available=video.caption_available,
                definition=video_metadata.get("definition", "sd"),
            )

            logger.debug(
                f"Video '{video.title[:50]}...' passed all filters: "
                f"final_score={final_score:.2f}"
            )

            # Monitoring: Video işlendi (tüm filtreleri geçti)
            self.monitor.log_video_processed(
                video.video_id,
                video.title,
                turkish_result.confidence_score,
                relevance_result.overall_score,
                quality_score,
                final_score,
                passed_filters=True,
            )

            return recommended_video

        except Exception as e:
            logger.error(f"Error processing video '{video.title[:50]}...': {str(e)}")

            # Monitoring: Hata
            self.monitor.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                context={"video_id": video.video_id, "video_title": video.title},
            )

            return None

    def _calculate_final_score(
        self,
        turkish_score: float,
        relevance_score: float,
        quality_score: float,
        accessibility_ok: bool,
        learning_style: Optional[str] = None,
        has_captions: bool = False,
        has_visual_content: bool = True,
    ) -> float:
        """
        Final skor hesaplama (learning style ağırlıklandırma ile)

        Base Weights:
        - Turkish score: 25%
        - Relevance score: 40%
        - Quality score: 25%
        - Accessibility: 10% (bonus if OK)

        Learning Style Bonuses:
        - V (Visual): +10% for videos with visual content
        - A (Auditory): +10% for clear audio quality videos
        - S (Sensory/Hands-on): +5% for interactive/practical videos
        - V (Verbal/Reading): +10% for videos with captions/subtitles

        Args:
            turkish_score: Türkçe skoru
            relevance_score: Uygunluk skoru
            quality_score: Kalite skoru
            accessibility_ok: Erişilebilir mi?
            learning_style: Öğrenci öğrenme stili (örn: "V-ASVS")
            has_captions: Altyazı var mı?
            has_visual_content: Görsel içerik var mı?

        Returns:
            Final skor (0.0-1.0)
        """
        if not accessibility_ok:
            return 0.0

        # Base score
        final_score = (
            turkish_score * self.weights["turkish"]
            + relevance_score * self.weights["relevance"]
            + quality_score * self.weights["quality"]
            + (self.weights["accessibility"] if accessibility_ok else 0.0)
        )

        # Learning style bonus (max +15%)
        learning_style_bonus = 0.0

        if learning_style:
            learning_style_upper = learning_style.upper()

            # Visual learners (V-AS, V-ASVS, etc.)
            if "V" in learning_style_upper and has_visual_content:
                learning_style_bonus += 0.10
                logger.debug(
                    f"Visual learner bonus: +0.10 (has_visual_content={has_visual_content})"
                )

            # Auditory learners (A-VS, V-AS, etc.)
            if "A" in learning_style_upper:
                # Assume all videos have audio, give small bonus
                learning_style_bonus += 0.05
                logger.debug("Auditory learner bonus: +0.05")

            # Reading/Writing learners (prefer captions)
            # FIX: R in VARK = Reading/Writing, not V (Visual)
            if has_captions and "R" in learning_style_upper:
                learning_style_bonus += 0.10
                logger.debug(
                    f"Reading learner bonus: +0.10 (has_captions={has_captions})"
                )

        final_score += learning_style_bonus

        return min(final_score, 1.0)

    def _extract_video_metadata(
        self, video: YouTubeVideo, accessibility_result: VideoAccessibilityResult
    ) -> Dict[str, Any]:
        """
        Video metadata'sını çıkar

        Args:
            video: YouTube video
            accessibility_result: Erişilebilirlik sonucu

        Returns:
            Metadata dictionary
        """
        # Duration'ı dakikaya çevir
        duration_minutes = self.quality_validator._parse_duration_to_minutes(
            video.duration or "PT0S"
        )

        return {
            "video_id": video.video_id,
            "title": video.title,
            "description": video.description,
            "channel_name": video.channel_name,
            "channel_id": video.channel_id,
            "view_count": video.view_count or 0,
            "like_count": video.like_count or 0,
            "duration": video.duration,
            "duration_minutes": duration_minutes,
            "caption_available": video.caption_available,
            "definition": "hd",  # YouTube API'den alınabilir
            "privacy_status": accessibility_result.privacy_status,
            "embeddable": accessibility_result.is_embeddable,
            "tags": video.tags,
            "language": video.language,
        }

    def _build_search_query(
        self, subject: str, topic: Optional[str], difficulty: str
    ) -> str:
        """
        Arama sorgusunu oluştur

        Args:
            subject: Ders
            topic: Konu
            difficulty: Zorluk seviyesi

        Returns:
            Arama sorgusu
        """
        parts = []

        # Ders
        parts.append(subject)

        # Konu
        if topic:
            parts.append(topic)

        # Zorluk seviyesi mapping
        difficulty_mapping = {
            "kolay": "temel giriş",
            "orta": "konu anlatımı",
            "zor": "ileri seviye",
        }

        difficulty_text = difficulty_mapping.get(difficulty.lower(), "konu anlatımı")
        parts.append(difficulty_text)

        # Eğitim anahtar kelimeleri
        parts.append("ders")

        return " ".join(parts)

    def _convert_fallback_videos(
        self, fallback_videos: List[Dict[str, Any]]
    ) -> List[RecommendedVideo]:
        """
        Fallback videoları RecommendedVideo formatına çevir

        Args:
            fallback_videos: Fallback video listesi

        Returns:
            RecommendedVideo listesi
        """
        recommended_videos = []

        for video_data in fallback_videos:
            try:
                recommended_video = RecommendedVideo(
                    video_id=video_data.get("video_id", ""),
                    title=video_data.get("title", ""),
                    channel_name=video_data.get("channel_name", ""),
                    channel_id=video_data.get("channel_id", ""),
                    description=video_data.get("description", ""),
                    thumbnail_url=video_data.get("thumbnail_url", ""),
                    duration=video_data.get("duration", "PT0S"),
                    duration_minutes=video_data.get("duration_minutes", 0),
                    view_count=video_data.get("view_count", 0),
                    like_count=video_data.get("like_count", 0),
                    upload_date=video_data.get("upload_date", ""),
                    url=video_data.get("url", ""),
                    # Scores - fallback videoları için varsayılan skorlar
                    turkish_score=0.9,
                    relevance_score=0.8,
                    quality_score=0.7,
                    final_score=0.8,
                    # Validation
                    is_accessible=True,
                    is_embeddable=True,
                    is_turkish=True,
                    # Metadata
                    tags=video_data.get("tags", []),
                    caption_available=video_data.get("caption_available", False),
                    definition=video_data.get("definition", "hd"),
                )
                recommended_videos.append(recommended_video)
            except Exception as e:
                logger.error(f"Error converting fallback video: {str(e)}")

        return recommended_videos

    def _generate_cache_key(
        self, subject: str, topic: Optional[str], difficulty: str, max_results: int,
        student_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Cache key oluştur

        Args:
            subject: Ders
            topic: Konu
            difficulty: Zorluk
            max_results: Maksimum sonuç
            student_profile: Öğrenci profili (learning_style cache için)

        Returns:
            Cache key
        """
        topic_str = topic or "none"
        # FIX: student_profile'ı cache key'e ekle (learning_style önemli)
        learning_style = ""
        if student_profile and isinstance(student_profile, dict):
            learning_style = student_profile.get("learning_style", "") or ""
        return f"video_recommendations:{subject}:{topic_str}:{difficulty}:{max_results}:{learning_style}"

    def _recommended_video_to_dict(self, video: RecommendedVideo) -> Dict[str, Any]:
        """
        RecommendedVideo'yu dict'e çevir (JSON serializable)

        Args:
            video: RecommendedVideo instance

        Returns:
            Dictionary
        """
        return {
            "video_id": video.video_id,
            "title": video.title,
            "channel_name": video.channel_name,
            "channel_id": video.channel_id,
            "description": video.description,
            "thumbnail_url": video.thumbnail_url,
            "duration": video.duration,
            "duration_minutes": video.duration_minutes,
            "view_count": video.view_count,
            "like_count": video.like_count,
            "upload_date": video.upload_date,
            "url": video.url,
            "turkish_score": video.turkish_score,
            "relevance_score": video.relevance_score,
            "quality_score": video.quality_score,
            "final_score": video.final_score,
            "is_accessible": video.is_accessible,
            "is_embeddable": video.is_embeddable,
            "is_turkish": video.is_turkish,
            "tags": video.tags,
            "caption_available": video.caption_available,
            "definition": video.definition,
        }

    def _dict_to_recommended_video(self, data: Dict[str, Any]) -> RecommendedVideo:
        """
        Dict'i RecommendedVideo'ya çevir

        Args:
            data: Video dictionary

        Returns:
            RecommendedVideo instance
        """
        return RecommendedVideo(
            video_id=data["video_id"],
            title=data["title"],
            channel_name=data["channel_name"],
            channel_id=data["channel_id"],
            description=data["description"],
            thumbnail_url=data["thumbnail_url"],
            duration=data["duration"],
            duration_minutes=data["duration_minutes"],
            view_count=data["view_count"],
            like_count=data["like_count"],
            upload_date=data["upload_date"],
            url=data["url"],
            turkish_score=data["turkish_score"],
            relevance_score=data["relevance_score"],
            quality_score=data["quality_score"],
            final_score=data["final_score"],
            is_accessible=data["is_accessible"],
            is_embeddable=data["is_embeddable"],
            is_turkish=data["is_turkish"],
            tags=data["tags"],
            caption_available=data["caption_available"],
            definition=data["definition"],
        )

    def get_validation_stats(self) -> Dict[str, int]:
        """
        Validation istatistiklerini al

        Returns:
            Validation başarısızlık istatistikleri
        """
        return self.validation_error_handler.get_failure_stats()

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Performance istatistiklerini al

        Returns:
            Performance metrikleri
        """
        return {
            "cache_stats": self.cache_manager.get_stats(),
            "rate_limiter_stats": self.rate_limiter.get_stats(),
            "validation_stats": self.get_validation_stats(),
        }

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        Monitoring istatistiklerini al

        Returns:
            Tüm monitoring metrikleri
        """
        return self.monitor.get_comprehensive_report()

    def log_monitoring_report(self):
        """Monitoring raporunu logla"""
        self.monitor.log_comprehensive_report()

    async def clear_cache(self):
        """Video öneri cache'ini temizle"""
        try:
            await self.cache_manager.invalidate_pattern("video_recommendations:*")
            logger.info("Video recommendation cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")

    async def close(self):
        """Kaynakları temizle"""
        try:
            await self.youtube_service.close_session()
            await self.quality_validator.close_session()
            logger.info("Enhanced Resource Recommendation Engine closed")
        except Exception as e:
            logger.error(f"Error closing engine: {str(e)}")


# Global instance
enhanced_recommendation_engine = EnhancedResourceRecommendationEngine()


async def get_enhanced_recommendation_engine() -> EnhancedResourceRecommendationEngine:
    """Enhanced recommendation engine instance'ını al"""
    return enhanced_recommendation_engine
