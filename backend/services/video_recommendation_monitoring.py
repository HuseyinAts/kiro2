"""
Video Recommendation Monitoring Service
Video filtreleme, validation ve performance metriklerini toplar ve loglar
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class FilterMetrics:
    """Video filtreleme metrikleri"""

    total_videos_processed: int = 0
    turkish_filter_passed: int = 0
    turkish_filter_failed: int = 0
    relevance_filter_passed: int = 0
    relevance_filter_failed: int = 0
    accessibility_filter_passed: int = 0
    accessibility_filter_failed: int = 0
    quality_filter_passed: int = 0
    quality_filter_failed: int = 0

    # Ortalama skorlar
    avg_turkish_score: float = 0.0
    avg_relevance_score: float = 0.0
    avg_quality_score: float = 0.0
    avg_final_score: float = 0.0

    # Skor dağılımları
    turkish_score_distribution: Dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    relevance_score_distribution: Dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    quality_score_distribution: Dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )


@dataclass
class ValidationFailure:
    """Validation başarısızlık kaydı"""

    video_id: str
    failure_type: str
    timestamp: datetime
    details: Dict[str, Any]
    video_title: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrikleri"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # Timing metrikleri (saniye)
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    min_processing_time: float = float("inf")
    max_processing_time: float = 0.0

    # API call metrikleri
    youtube_api_calls: int = 0
    youtube_api_errors: int = 0
    youtube_quota_exceeded_count: int = 0
    youtube_rate_limit_count: int = 0

    # Timeout metrikleri
    timeout_count: int = 0

    # Request timing dağılımı (saniye)
    timing_distribution: Dict[str, int] = field(
        default_factory=lambda: {"<1s": 0, "1-2s": 0, "2-3s": 0, "3-5s": 0, ">5s": 0}
    )


@dataclass
class ErrorMetrics:
    """Hata metrikleri"""

    total_errors: int = 0
    error_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_rate: float = 0.0
    recent_errors: List[Dict[str, Any]] = field(default_factory=list)
    max_recent_errors: int = 100


class VideoRecommendationMonitor:
    """
    Video öneri sistemi için monitoring servisi

    Video filtreleme, validation ve performance metriklerini toplar,
    loglar ve raporlar.
    """

    def __init__(self):
        """VideoRecommendationMonitor'ı başlat"""
        self.filter_metrics = FilterMetrics()
        self.performance_metrics = PerformanceMetrics()
        self.error_metrics = ErrorMetrics()

        # Validation başarısızlıkları
        self.validation_failures: List[ValidationFailure] = []
        self.max_validation_failures = 1000  # Son 1000 başarısızlığı sakla

        # Thread-safe operations için lock
        self._lock = Lock()

        # Monitoring başlangıç zamanı
        self.start_time = datetime.now()

        logger.info("Video Recommendation Monitor initialized")

    def log_video_processed(
        self,
        video_id: str,
        video_title: str,
        turkish_score: float,
        relevance_score: float,
        quality_score: float,
        final_score: float,
        passed_filters: bool,
    ):
        """
        İşlenen video metriklerini logla

        Args:
            video_id: Video ID
            video_title: Video başlığı
            turkish_score: Türkçe skoru
            relevance_score: Uygunluk skoru
            quality_score: Kalite skoru
            final_score: Final skor
            passed_filters: Tüm filtreleri geçti mi?
        """
        with self._lock:
            self.filter_metrics.total_videos_processed += 1

            # Skor ortalamaları güncelle
            n = self.filter_metrics.total_videos_processed
            self.filter_metrics.avg_turkish_score = (
                self.filter_metrics.avg_turkish_score * (n - 1) + turkish_score
            ) / n
            self.filter_metrics.avg_relevance_score = (
                self.filter_metrics.avg_relevance_score * (n - 1) + relevance_score
            ) / n
            self.filter_metrics.avg_quality_score = (
                self.filter_metrics.avg_quality_score * (n - 1) + quality_score
            ) / n
            self.filter_metrics.avg_final_score = (
                self.filter_metrics.avg_final_score * (n - 1) + final_score
            ) / n

            # Skor dağılımları güncelle
            self._update_score_distribution(
                self.filter_metrics.turkish_score_distribution, turkish_score
            )
            self._update_score_distribution(
                self.filter_metrics.relevance_score_distribution, relevance_score
            )
            self._update_score_distribution(
                self.filter_metrics.quality_score_distribution, quality_score
            )

            # Log
            if passed_filters:
                logger.debug(
                    f"Video processed: {video_title[:50]}... "
                    f"(T:{turkish_score:.2f}, R:{relevance_score:.2f}, "
                    f"Q:{quality_score:.2f}, F:{final_score:.2f}) - PASSED"
                )
            else:
                logger.debug(
                    f"Video filtered: {video_title[:50]}... "
                    f"(T:{turkish_score:.2f}, R:{relevance_score:.2f}, "
                    f"Q:{quality_score:.2f})"
                )

    def log_filter_result(
        self,
        filter_type: str,
        passed: bool,
        score: Optional[float] = None,
        threshold: Optional[float] = None,
    ):
        """
        Filtre sonucunu logla

        Args:
            filter_type: Filtre tipi (turkish, relevance, accessibility, quality)
            passed: Filtreden geçti mi?
            score: Skor (opsiyonel)
            threshold: Threshold değeri (opsiyonel)
        """
        with self._lock:
            if filter_type == "turkish":
                if passed:
                    self.filter_metrics.turkish_filter_passed += 1
                else:
                    self.filter_metrics.turkish_filter_failed += 1
            elif filter_type == "relevance":
                if passed:
                    self.filter_metrics.relevance_filter_passed += 1
                else:
                    self.filter_metrics.relevance_filter_failed += 1
            elif filter_type == "accessibility":
                if passed:
                    self.filter_metrics.accessibility_filter_passed += 1
                else:
                    self.filter_metrics.accessibility_filter_failed += 1
            elif filter_type == "quality":
                if passed:
                    self.filter_metrics.quality_filter_passed += 1
                else:
                    self.filter_metrics.quality_filter_failed += 1

            # Log
            status = "PASSED" if passed else "FAILED"
            if score is not None and threshold is not None:
                logger.debug(
                    f"{filter_type.upper()} filter: {status} "
                    f"(score: {score:.2f}, threshold: {threshold:.2f})"
                )
            else:
                logger.debug(f"{filter_type.upper()} filter: {status}")

    def log_validation_failure(
        self,
        video_id: str,
        failure_type: str,
        details: Dict[str, Any],
        video_title: Optional[str] = None,
    ):
        """
        Validation başarısızlığını kaydet

        Args:
            video_id: Video ID
            failure_type: Başarısızlık tipi
            details: Detaylar
            video_title: Video başlığı (opsiyonel)
        """
        with self._lock:
            failure = ValidationFailure(
                video_id=video_id,
                failure_type=failure_type,
                timestamp=datetime.now(),
                details=details,
                video_title=video_title,
            )

            self.validation_failures.append(failure)

            # Limit kontrolü
            if len(self.validation_failures) > self.max_validation_failures:
                self.validation_failures = self.validation_failures[
                    -self.max_validation_failures :
                ]

            # Log
            logger.warning(
                f"Validation failure: {failure_type} for video {video_id} "
                f"({video_title[:50] if video_title else 'N/A'}...) - {details}"
            )

    def log_request_start(self) -> float:
        """
        Request başlangıcını logla

        Returns:
            Başlangıç zamanı (timestamp)
        """
        with self._lock:
            self.performance_metrics.total_requests += 1

        return time.time()

    def log_request_end(
        self,
        start_time: float,
        success: bool,
        cache_hit: bool = False,
        video_count: int = 0,
    ):
        """
        Request bitişini logla

        Args:
            start_time: Başlangıç zamanı
            success: Başarılı mı?
            cache_hit: Cache hit mi?
            video_count: Döndürülen video sayısı
        """
        processing_time = time.time() - start_time

        with self._lock:
            if success:
                self.performance_metrics.successful_requests += 1
            else:
                self.performance_metrics.failed_requests += 1

            if cache_hit:
                self.performance_metrics.cache_hits += 1
            else:
                self.performance_metrics.cache_misses += 1

            # Timing metrikleri güncelle
            self.performance_metrics.total_processing_time += processing_time
            self.performance_metrics.avg_processing_time = (
                self.performance_metrics.total_processing_time
                / self.performance_metrics.total_requests
            )
            self.performance_metrics.min_processing_time = min(
                self.performance_metrics.min_processing_time, processing_time
            )
            self.performance_metrics.max_processing_time = max(
                self.performance_metrics.max_processing_time, processing_time
            )

            # Timing dağılımı güncelle
            if processing_time < 1:
                self.performance_metrics.timing_distribution["<1s"] += 1
            elif processing_time < 2:
                self.performance_metrics.timing_distribution["1-2s"] += 1
            elif processing_time < 3:
                self.performance_metrics.timing_distribution["2-3s"] += 1
            elif processing_time < 5:
                self.performance_metrics.timing_distribution["3-5s"] += 1
            else:
                self.performance_metrics.timing_distribution[">5s"] += 1

        # Log
        status = "SUCCESS" if success else "FAILED"
        cache_status = "CACHE_HIT" if cache_hit else "CACHE_MISS"
        logger.info(
            f"Request completed: {status} - {cache_status} - "
            f"{processing_time:.2f}s - {video_count} videos"
        )

    def log_youtube_api_call(self, success: bool = True):
        """
        YouTube API çağrısını logla

        Args:
            success: Başarılı mı?
        """
        with self._lock:
            self.performance_metrics.youtube_api_calls += 1
            if not success:
                self.performance_metrics.youtube_api_errors += 1

    def log_youtube_quota_exceeded(self):
        """YouTube API quota aşımını logla"""
        with self._lock:
            self.performance_metrics.youtube_quota_exceeded_count += 1

        logger.error("YouTube API quota exceeded")

    def log_youtube_rate_limit(self):
        """YouTube API rate limit'i logla"""
        with self._lock:
            self.performance_metrics.youtube_rate_limit_count += 1

        logger.warning("YouTube API rate limit hit")

    def log_timeout(self, operation: str):
        """
        Timeout'u logla

        Args:
            operation: Timeout olan operasyon
        """
        with self._lock:
            self.performance_metrics.timeout_count += 1

        logger.warning(f"Timeout occurred: {operation}")

    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Hata logla

        Args:
            error_type: Hata tipi
            error_message: Hata mesajı
            context: Hata context'i (opsiyonel)
        """
        with self._lock:
            self.error_metrics.total_errors += 1
            self.error_metrics.error_types[error_type] += 1

            # Error rate hesapla
            if self.performance_metrics.total_requests > 0:
                self.error_metrics.error_rate = (
                    self.error_metrics.total_errors
                    / self.performance_metrics.total_requests
                )

            # Recent errors'a ekle
            error_record = {
                "type": error_type,
                "message": error_message,
                "timestamp": datetime.now().isoformat(),
                "context": context or {},
            }
            self.error_metrics.recent_errors.append(error_record)

            # Limit kontrolü
            if (
                len(self.error_metrics.recent_errors)
                > self.error_metrics.max_recent_errors
            ):
                self.error_metrics.recent_errors = self.error_metrics.recent_errors[
                    -self.error_metrics.max_recent_errors :
                ]

        # Log
        logger.error(f"Error: {error_type} - {error_message} " f"(context: {context})")

    def get_filter_stats(self) -> Dict[str, Any]:
        """
        Filtre istatistiklerini al

        Returns:
            Filtre metrikleri
        """
        with self._lock:
            total = self.filter_metrics.total_videos_processed

            return {
                "total_videos_processed": total,
                "filters": {
                    "turkish": {
                        "passed": self.filter_metrics.turkish_filter_passed,
                        "failed": self.filter_metrics.turkish_filter_failed,
                        "pass_rate": (
                            self.filter_metrics.turkish_filter_passed / total
                            if total > 0
                            else 0.0
                        ),
                    },
                    "relevance": {
                        "passed": self.filter_metrics.relevance_filter_passed,
                        "failed": self.filter_metrics.relevance_filter_failed,
                        "pass_rate": (
                            self.filter_metrics.relevance_filter_passed / total
                            if total > 0
                            else 0.0
                        ),
                    },
                    "accessibility": {
                        "passed": self.filter_metrics.accessibility_filter_passed,
                        "failed": self.filter_metrics.accessibility_filter_failed,
                        "pass_rate": (
                            self.filter_metrics.accessibility_filter_passed / total
                            if total > 0
                            else 0.0
                        ),
                    },
                    "quality": {
                        "passed": self.filter_metrics.quality_filter_passed,
                        "failed": self.filter_metrics.quality_filter_failed,
                        "pass_rate": (
                            self.filter_metrics.quality_filter_passed / total
                            if total > 0
                            else 0.0
                        ),
                    },
                },
                "average_scores": {
                    "turkish": round(self.filter_metrics.avg_turkish_score, 3),
                    "relevance": round(self.filter_metrics.avg_relevance_score, 3),
                    "quality": round(self.filter_metrics.avg_quality_score, 3),
                    "final": round(self.filter_metrics.avg_final_score, 3),
                },
                "score_distributions": {
                    "turkish": dict(self.filter_metrics.turkish_score_distribution),
                    "relevance": dict(self.filter_metrics.relevance_score_distribution),
                    "quality": dict(self.filter_metrics.quality_score_distribution),
                },
            }

    def get_validation_failure_stats(self) -> Dict[str, Any]:
        """
        Validation başarısızlık istatistiklerini al

        Returns:
            Validation başarısızlık metrikleri
        """
        with self._lock:
            # Failure type'lara göre grupla
            failure_by_type = defaultdict(int)
            for failure in self.validation_failures:
                failure_by_type[failure.failure_type] += 1

            # Son 10 başarısızlık
            recent_failures = [
                {
                    "video_id": f.video_id,
                    "video_title": f.video_title,
                    "failure_type": f.failure_type,
                    "timestamp": f.timestamp.isoformat(),
                    "details": f.details,
                }
                for f in self.validation_failures[-10:]
            ]

            return {
                "total_failures": len(self.validation_failures),
                "failures_by_type": dict(failure_by_type),
                "recent_failures": recent_failures,
            }

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Performance istatistiklerini al

        Returns:
            Performance metrikleri
        """
        with self._lock:
            total_requests = self.performance_metrics.total_requests

            return {
                "requests": {
                    "total": total_requests,
                    "successful": self.performance_metrics.successful_requests,
                    "failed": self.performance_metrics.failed_requests,
                    "success_rate": (
                        self.performance_metrics.successful_requests / total_requests
                        if total_requests > 0
                        else 0.0
                    ),
                },
                "cache": {
                    "hits": self.performance_metrics.cache_hits,
                    "misses": self.performance_metrics.cache_misses,
                    "hit_rate": (
                        self.performance_metrics.cache_hits / total_requests
                        if total_requests > 0
                        else 0.0
                    ),
                },
                "timing": {
                    "avg_processing_time": round(
                        self.performance_metrics.avg_processing_time, 3
                    ),
                    "min_processing_time": round(
                        self.performance_metrics.min_processing_time, 3
                    ),
                    "max_processing_time": round(
                        self.performance_metrics.max_processing_time, 3
                    ),
                    "distribution": self.performance_metrics.timing_distribution,
                },
                "youtube_api": {
                    "total_calls": self.performance_metrics.youtube_api_calls,
                    "errors": self.performance_metrics.youtube_api_errors,
                    "quota_exceeded": self.performance_metrics.youtube_quota_exceeded_count,
                    "rate_limits": self.performance_metrics.youtube_rate_limit_count,
                    "error_rate": (
                        self.performance_metrics.youtube_api_errors
                        / self.performance_metrics.youtube_api_calls
                        if self.performance_metrics.youtube_api_calls > 0
                        else 0.0
                    ),
                },
                "timeouts": self.performance_metrics.timeout_count,
            }

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Hata istatistiklerini al

        Returns:
            Hata metrikleri
        """
        with self._lock:
            return {
                "total_errors": self.error_metrics.total_errors,
                "error_rate": round(self.error_metrics.error_rate, 4),
                "errors_by_type": dict(self.error_metrics.error_types),
                "recent_errors": self.error_metrics.recent_errors[-10:],
            }

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        Kapsamlı monitoring raporu al

        Returns:
            Tüm metrikleri içeren rapor
        """
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "monitoring_info": {
                "start_time": self.start_time.isoformat(),
                "uptime_seconds": round(uptime, 2),
                "uptime_hours": round(uptime / 3600, 2),
            },
            "filter_stats": self.get_filter_stats(),
            "validation_failures": self.get_validation_failure_stats(),
            "performance_stats": self.get_performance_stats(),
            "error_stats": self.get_error_stats(),
        }

    def log_comprehensive_report(self):
        """Kapsamlı raporu logla"""
        report = self.get_comprehensive_report()

        logger.info("=" * 80)
        logger.info("VIDEO RECOMMENDATION MONITORING REPORT")
        logger.info("=" * 80)

        # Monitoring info
        logger.info(f"Uptime: {report['monitoring_info']['uptime_hours']:.2f} hours")

        # Filter stats
        filter_stats = report["filter_stats"]
        logger.info(
            f"\nTotal videos processed: {filter_stats['total_videos_processed']}"
        )
        logger.info("Filter pass rates:")
        for filter_name, stats in filter_stats["filters"].items():
            logger.info(
                f"  {filter_name.capitalize()}: {stats['pass_rate']:.1%} "
                f"({stats['passed']}/{stats['passed'] + stats['failed']})"
            )

        logger.info("\nAverage scores:")
        for score_name, score in filter_stats["average_scores"].items():
            logger.info(f"  {score_name.capitalize()}: {score:.3f}")

        # Performance stats
        perf_stats = report["performance_stats"]
        logger.info(f"\nTotal requests: {perf_stats['requests']['total']}")
        logger.info(f"Success rate: {perf_stats['requests']['success_rate']:.1%}")
        logger.info(f"Cache hit rate: {perf_stats['cache']['hit_rate']:.1%}")
        logger.info(
            f"Avg processing time: {perf_stats['timing']['avg_processing_time']:.2f}s"
        )

        # YouTube API stats
        youtube_stats = perf_stats["youtube_api"]
        logger.info(f"\nYouTube API calls: {youtube_stats['total_calls']}")
        logger.info(f"YouTube API errors: {youtube_stats['errors']}")
        logger.info(f"Quota exceeded: {youtube_stats['quota_exceeded']}")
        logger.info(f"Rate limits: {youtube_stats['rate_limits']}")

        # Error stats
        error_stats = report["error_stats"]
        logger.info(f"\nTotal errors: {error_stats['total_errors']}")
        logger.info(f"Error rate: {error_stats['error_rate']:.2%}")

        logger.info("=" * 80)

    def reset_metrics(self):
        """Tüm metrikleri sıfırla"""
        with self._lock:
            self.filter_metrics = FilterMetrics()
            self.performance_metrics = PerformanceMetrics()
            self.error_metrics = ErrorMetrics()
            self.validation_failures = []
            self.start_time = datetime.now()

        logger.info("All metrics reset")

    def _update_score_distribution(self, distribution: Dict[str, int], score: float):
        """
        Skor dağılımını güncelle

        Args:
            distribution: Dağılım dictionary'si
            score: Skor değeri
        """
        # 0.1'lik aralıklarla grupla
        if score < 0.3:
            bucket = "0.0-0.3"
        elif score < 0.5:
            bucket = "0.3-0.5"
        elif score < 0.7:
            bucket = "0.5-0.7"
        elif score < 0.9:
            bucket = "0.7-0.9"
        else:
            bucket = "0.9-1.0"

        distribution[bucket] += 1


# Global instance
video_recommendation_monitor = VideoRecommendationMonitor()


def get_video_recommendation_monitor() -> VideoRecommendationMonitor:
    """Video recommendation monitor instance'ını al"""
    return video_recommendation_monitor
