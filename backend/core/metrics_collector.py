"""
Metrics Collection System for Video API
Prometheus-based metrics collection with comprehensive tracking

Requirements: 4.4, 4.10, 4.14, 5.12
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from threading import Lock

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """Metrik anlık görüntüsü"""

    timestamp: datetime
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


class MetricsCollector:
    """
    Video API için Prometheus metrics collector

    Toplanan metrikler:
    - video_requests_total: Toplam video isteği sayısı (Counter)
    - video_response_time: Video yanıt süresi (Histogram - P50, P95, P99)
    - cache_hit_rate: Cache hit oranı (Gauge)
    - youtube_api_quota: YouTube API quota kullanımı (Gauge)
    - video_errors_total: Toplam hata sayısı (Counter)
    - active_requests: Aktif istek sayısı (Gauge)
    """

    def __init__(self, registry: CollectorRegistry | None = None):
        """
        MetricsCollector başlat

        Args:
            registry: Prometheus registry (None ise default registry kullanılır)
        """
        self.registry = registry or CollectorRegistry()
        self._lock = Lock()

        # Response time tracking için internal storage
        self._response_times: list[float] = []
        self._max_response_times = 10000  # Son 10k istek

        # Request tracking
        self._request_start_times: dict[str, float] = {}

        # Cache tracking
        self._cache_hits = 0
        self._cache_misses = 0

        # YouTube API quota tracking
        self._youtube_quota_used = 0
        self._youtube_quota_limit = 10000  # Günlük limit

        # Error tracking
        self._errors_by_type: dict[str, int] = defaultdict(int)

        # Initialize Prometheus metrics
        self._init_prometheus_metrics()

        logger.info("MetricsCollector initialized with Prometheus integration")

    def _init_prometheus_metrics(self):
        """Prometheus metriklerini başlat"""

        # Counter: Toplam video istekleri
        self.video_requests_total = Counter(
            "video_requests_total",
            "Total number of video recommendation requests",
            ["status", "cache_status"],
            registry=self.registry,
        )

        # Histogram: Video yanıt süresi (P50, P95, P99 için)
        self.video_response_time = Histogram(
            "video_response_time_seconds",
            "Video recommendation response time in seconds",
            ["endpoint"],
            buckets=(0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0),
            registry=self.registry,
        )

        # Gauge: Cache hit rate
        self.cache_hit_rate_gauge = Gauge(
            "cache_hit_rate", "Cache hit rate (0-1)", registry=self.registry
        )

        # Gauge: YouTube API quota kullanımı
        self.youtube_api_quota_gauge = Gauge(
            "youtube_api_quota_used",
            "YouTube API quota used today",
            registry=self.registry,
        )

        # Gauge: YouTube API quota limiti
        self.youtube_api_quota_limit_gauge = Gauge(
            "youtube_api_quota_limit",
            "YouTube API daily quota limit",
            registry=self.registry,
        )
        self.youtube_api_quota_limit_gauge.set(self._youtube_quota_limit)

        # Counter: Hata sayısı
        self.video_errors_total = Counter(
            "video_errors_total",
            "Total number of video API errors",
            ["error_type", "endpoint"],
            registry=self.registry,
        )

        # Gauge: Aktif istek sayısı
        self.active_requests_gauge = Gauge(
            "active_video_requests",
            "Number of currently active video requests",
            registry=self.registry,
        )

        # Info: Sistem bilgisi
        self.system_info = Info(
            "video_api_info", "Video API system information", registry=self.registry
        )
        self.system_info.info(
            {
                "version": "1.0.0",
                "service": "video_recommendation_api",
                "environment": "production",
            }
        )

        # Gauge: Cache boyutu
        self.cache_size_gauge = Gauge(
            "cache_size_entries", "Number of entries in cache", registry=self.registry
        )

        # Counter: Cache operations
        self.cache_operations_total = Counter(
            "cache_operations_total",
            "Total cache operations",
            ["operation"],  # get, set, delete, clear
            registry=self.registry,
        )

        # ==================== Learning Path Metrics ====================
        # P1.2 Gap Fix: Learning Path-specific metrics

        # Counter: Learning path creation requests
        self.learning_path_creation_total = Counter(
            "learning_path_creation_total",
            "Total number of learning path creation requests",
            [
                "status",
                "subject",
            ],  # status: success/failure, subject: matematik/fizik/etc
            registry=self.registry,
        )

        # Histogram: Learning path creation duration
        self.learning_path_creation_duration = Histogram(
            "learning_path_creation_duration_seconds",
            "Learning path creation duration in seconds (AI agent processing)",
            ["subject"],
            buckets=(5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 60.0, 90.0),
            registry=self.registry,
        )

        # Counter: Learning path API requests (all endpoints)
        self.learning_path_api_requests_total = Counter(
            "learning_path_api_requests_total",
            "Total API requests to learning path endpoints",
            [
                "endpoint",
                "method",
                "status",
            ],  # endpoint: /create-path, /search-resources, etc
            registry=self.registry,
        )

        # Histogram: Resource search duration
        self.resource_search_duration = Histogram(
            "resource_search_duration_seconds",
            "Resource search/recommendation duration in seconds",
            ["subject"],
            buckets=(0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0),
            registry=self.registry,
        )

        # Counter: Resource search results
        self.resource_search_results = Counter(
            "resource_search_results_total",
            "Total number of resources returned by search",
            ["subject", "has_results"],  # has_results: yes/no
            registry=self.registry,
        )

        # Gauge: Active learning paths
        self.active_learning_paths_gauge = Gauge(
            "active_learning_paths",
            "Number of currently active learning paths in system",
            registry=self.registry,
        )

        # Counter: Student profile operations
        self.student_profile_operations_total = Counter(
            "student_profile_operations_total",
            "Total student profile operations",
            [
                "operation",
                "status",
            ],  # operation: create/update/delete, status: success/failure
            registry=self.registry,
        )

        # Counter: Topic completion updates
        self.topic_completion_updates_total = Counter(
            "topic_completion_updates_total",
            "Total topic completion updates",
            ["status"],  # status: success/failure
            registry=self.registry,
        )

        # Counter: Quiz submissions
        self.quiz_submissions_total = Counter(
            "quiz_submissions_total",
            "Total quiz submissions",
            ["passed", "subject"],  # passed: true/false
            registry=self.registry,
        )

        # Histogram: Quiz scores
        self.quiz_scores = Histogram(
            "quiz_scores",
            "Distribution of quiz scores",
            ["subject"],
            buckets=(0, 20, 40, 50, 60, 70, 80, 90, 100),
            registry=self.registry,
        )

        # Counter: Learning path adaptations
        self.learning_path_adaptations_total = Counter(
            "learning_path_adaptations_total",
            "Total learning path adaptations based on performance",
            ["adaptation_type"],  # difficulty_adjustment, pace_adjustment, etc
            registry=self.registry,
        )

        # Gauge: Average student progress
        self.avg_student_progress_gauge = Gauge(
            "avg_student_progress_percentage",
            "Average student progress across all learning paths",
            registry=self.registry,
        )

        # Counter: Fallback video requests
        self.fallback_video_requests_total = Counter(
            "fallback_video_requests_total",
            "Total fallback video requests",
            ["subject", "found"],  # found: yes/no
            registry=self.registry,
        )

    def start_request(
        self, request_id: str, endpoint: str = "/api/youtube/recommendations"
    ):
        """
        İstek başlangıcını kaydet

        Args:
            request_id: Unique request ID
            endpoint: API endpoint
        """
        with self._lock:
            self._request_start_times[request_id] = time.time()
            self.active_requests_gauge.inc()

        logger.debug(f"[{request_id}] Request started: {endpoint}")

    def end_request(
        self,
        request_id: str,
        success: bool = True,
        cache_hit: bool = False,
        endpoint: str = "/api/youtube/recommendations",
    ):
        """
        İstek bitişini kaydet ve metrikleri güncelle

        Args:
            request_id: Unique request ID
            success: İstek başarılı mı?
            cache_hit: Cache'den mi geldi?
            endpoint: API endpoint
        """
        with self._lock:
            # Response time hesapla
            if request_id in self._request_start_times:
                start_time = self._request_start_times.pop(request_id)
                response_time = time.time() - start_time

                # Response time'ı kaydet
                self._response_times.append(response_time)

                # Max limit kontrolü
                if len(self._response_times) > self._max_response_times:
                    self._response_times = self._response_times[
                        -self._max_response_times :
                    ]

                # Prometheus histogram'a kaydet
                self.video_response_time.labels(endpoint=endpoint).observe(
                    response_time
                )
            else:
                response_time = 0.0

            # Request counter güncelle
            status = "success" if success else "error"
            cache_status = "hit" if cache_hit else "miss"
            self.video_requests_total.labels(
                status=status, cache_status=cache_status
            ).inc()

            # Cache tracking
            if cache_hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

            # Cache hit rate güncelle
            self._update_cache_hit_rate()

            # Active requests azalt
            self.active_requests_gauge.dec()

        logger.debug(
            f"[{request_id}] Request ended: success={success}, "
            f"cache_hit={cache_hit}, response_time={response_time:.3f}s"
        )

    def record_error(
        self,
        request_id: str,
        error_type: str,
        endpoint: str = "/api/youtube/recommendations",
    ):
        """
        Hata kaydı

        Args:
            request_id: Unique request ID
            error_type: Hata tipi (timeout, network, server, etc.)
            endpoint: API endpoint
        """
        with self._lock:
            self._errors_by_type[error_type] += 1
            self.video_errors_total.labels(
                error_type=error_type, endpoint=endpoint
            ).inc()

        logger.warning(f"[{request_id}] Error recorded: {error_type}")

    def record_cache_operation(self, operation: str):
        """
        Cache operasyonu kaydet

        Args:
            operation: Operation type (get, set, delete, clear)
        """
        self.cache_operations_total.labels(operation=operation).inc()

    def update_cache_size(self, size: int):
        """
        Cache boyutunu güncelle

        Args:
            size: Cache'deki entry sayısı
        """
        self.cache_size_gauge.set(size)

    def record_youtube_api_call(self, quota_cost: int = 1):
        """
        YouTube API çağrısını kaydet ve quota'yı güncelle

        Args:
            quota_cost: API çağrısının quota maliyeti (default: 1)
        """
        with self._lock:
            self._youtube_quota_used += quota_cost
            self.youtube_api_quota_gauge.set(self._youtube_quota_used)

        # Quota warning
        quota_percentage = (self._youtube_quota_used / self._youtube_quota_limit) * 100
        if quota_percentage >= 80:
            logger.warning(
                f"YouTube API quota %{quota_percentage:.1f} kullanıldı "
                f"({self._youtube_quota_used}/{self._youtube_quota_limit})"
            )

    def reset_youtube_quota(self):
        """YouTube API quota'sını sıfırla (günlük reset için)"""
        with self._lock:
            self._youtube_quota_used = 0
            self.youtube_api_quota_gauge.set(0)

        logger.info("YouTube API quota reset edildi")

    def _update_cache_hit_rate(self):
        """Cache hit rate'i hesapla ve güncelle"""
        total_cache_requests = self._cache_hits + self._cache_misses
        if total_cache_requests > 0:
            hit_rate = self._cache_hits / total_cache_requests
            self.cache_hit_rate_gauge.set(hit_rate)

    def get_cache_hit_rate(self) -> float:
        """
        Cache hit rate'i al

        Returns:
            float: Cache hit rate (0-1 arası)
        """
        total = self._cache_hits + self._cache_misses
        if total == 0:
            return 0.0
        return self._cache_hits / total

    def get_response_time_percentiles(self) -> dict[str, float]:
        """
        Response time percentile'larını hesapla (P50, P95, P99)

        Returns:
            Dict[str, float]: Percentile değerleri
        """
        if not self._response_times:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_times = sorted(self._response_times)
        n = len(sorted_times)

        p50_idx = int(n * 0.50)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        return {
            "p50": sorted_times[p50_idx] if p50_idx < n else 0.0,
            "p95": sorted_times[p95_idx] if p95_idx < n else 0.0,
            "p99": sorted_times[p99_idx] if p99_idx < n else 0.0,
        }

    def get_avg_response_time(self) -> float:
        """
        Ortalama response time'ı al

        Returns:
            float: Ortalama response time (saniye)
        """
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times)

    def get_error_rate(self) -> float:
        """
        Hata oranını hesapla

        Returns:
            float: Hata oranı (0-1 arası)
        """
        # Prometheus counter'dan al
        total_requests = (
            self.video_requests_total.labels(
                status="success", cache_status="hit"
            )._value.get()
            + self.video_requests_total.labels(
                status="success", cache_status="miss"
            )._value.get()
            + self.video_requests_total.labels(
                status="error", cache_status="hit"
            )._value.get()
            + self.video_requests_total.labels(
                status="error", cache_status="miss"
            )._value.get()
        )

        total_errors = (
            self.video_requests_total.labels(
                status="error", cache_status="hit"
            )._value.get()
            + self.video_requests_total.labels(
                status="error", cache_status="miss"
            )._value.get()
        )

        if total_requests == 0:
            return 0.0

        return total_errors / total_requests

    def get_snapshot(self) -> MetricSnapshot:
        """
        Mevcut metriklerin anlık görüntüsünü al

        Returns:
            MetricSnapshot: Metrik snapshot
        """
        percentiles = self.get_response_time_percentiles()

        # Total requests
        total_success = (
            self.video_requests_total.labels(
                status="success", cache_status="hit"
            )._value.get()
            + self.video_requests_total.labels(
                status="success", cache_status="miss"
            )._value.get()
        )
        total_errors = (
            self.video_requests_total.labels(
                status="error", cache_status="hit"
            )._value.get()
            + self.video_requests_total.labels(
                status="error", cache_status="miss"
            )._value.get()
        )

        return MetricSnapshot(
            timestamp=datetime.now(),
            total_requests=int(total_success + total_errors),
            successful_requests=int(total_success),
            failed_requests=int(total_errors),
            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses,
            avg_response_time=self.get_avg_response_time(),
            p50_response_time=percentiles["p50"],
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            youtube_api_quota_used=self._youtube_quota_used,
            error_rate=self.get_error_rate(),
            cache_hit_rate=self.get_cache_hit_rate(),
        )

    def get_prometheus_metrics(self) -> bytes:
        """
        Prometheus formatında metrikleri al

        Returns:
            bytes: Prometheus format metrics
        """
        return generate_latest(self.registry)

    def get_metrics_content_type(self) -> str:
        """
        Prometheus metrics content type

        Returns:
            str: Content type
        """
        return CONTENT_TYPE_LATEST

    def reset_metrics(self):
        """Tüm metrikleri sıfırla (test için)"""
        with self._lock:
            self._response_times.clear()
            self._request_start_times.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            self._youtube_quota_used = 0
            self._errors_by_type.clear()

        logger.info("Metrics reset edildi")

    # ==================== Learning Path Metric Methods ====================
    # P1.2 Gap Fix: Helper methods for Learning Path metrics

    def record_learning_path_creation(
        self, subject: str, duration_seconds: float, success: bool = True
    ):
        """
        Learning path oluşturma işlemini kaydet

        Args:
            subject: Ders adı (matematik, fizik, vb.)
            duration_seconds: İşlem süresi (saniye)
            success: İşlem başarılı mı?
        """
        status = "success" if success else "failure"
        self.learning_path_creation_total.labels(status=status, subject=subject).inc()

        if success:
            self.learning_path_creation_duration.labels(subject=subject).observe(
                duration_seconds
            )

        logger.debug(
            f"Learning path creation recorded: subject={subject}, "
            f"duration={duration_seconds:.2f}s, success={success}"
        )

    def record_learning_path_api_request(
        self, endpoint: str, method: str, status_code: int
    ):
        """
        Learning Path API isteğini kaydet

        Args:
            endpoint: Endpoint adı (örn: /create-path, /search-resources)
            method: HTTP method (GET, POST, PUT, etc.)
            status_code: HTTP status code
        """
        status = "success" if 200 <= status_code < 300 else "error"
        self.learning_path_api_requests_total.labels(
            endpoint=endpoint, method=method, status=status
        ).inc()

    def record_resource_search(
        self, subject: str, duration_seconds: float, result_count: int
    ):
        """
        Kaynak araması işlemini kaydet

        Args:
            subject: Ders adı
            duration_seconds: Arama süresi (saniye)
            result_count: Bulunan kaynak sayısı
        """
        self.resource_search_duration.labels(subject=subject).observe(duration_seconds)

        has_results = "yes" if result_count > 0 else "no"
        self.resource_search_results.labels(
            subject=subject, has_results=has_results
        ).inc()

        logger.debug(
            f"Resource search recorded: subject={subject}, "
            f"duration={duration_seconds:.2f}s, results={result_count}"
        )

    def update_active_learning_paths(self, count: int):
        """
        Aktif öğrenme yolu sayısını güncelle

        Args:
            count: Aktif öğrenme yolu sayısı
        """
        self.active_learning_paths_gauge.set(count)

    def record_student_profile_operation(self, operation: str, success: bool = True):
        """
        Öğrenci profili işlemini kaydet

        Args:
            operation: İşlem tipi (create, update, delete)
            success: İşlem başarılı mı?
        """
        status = "success" if success else "failure"
        self.student_profile_operations_total.labels(
            operation=operation, status=status
        ).inc()

    def record_topic_completion(self, success: bool = True):
        """
        Konu tamamlama güncellemesini kaydet

        Args:
            success: Güncelleme başarılı mı?
        """
        status = "success" if success else "failure"
        self.topic_completion_updates_total.labels(status=status).inc()

    def record_quiz_submission(self, subject: str, score: float, passed: bool):
        """
        Quiz gönderimini kaydet

        Args:
            subject: Ders adı
            score: Quiz skoru (0-100)
            passed: Geçti mi?
        """
        passed_str = "true" if passed else "false"
        self.quiz_submissions_total.labels(passed=passed_str, subject=subject).inc()

        self.quiz_scores.labels(subject=subject).observe(score)

        logger.debug(
            f"Quiz submission recorded: subject={subject}, "
            f"score={score:.1f}, passed={passed}"
        )

    def record_learning_path_adaptation(self, adaptation_type: str):
        """
        Öğrenme yolu adaptasyonunu kaydet

        Args:
            adaptation_type: Adaptasyon tipi (difficulty_adjustment, pace_adjustment, etc.)
        """
        self.learning_path_adaptations_total.labels(
            adaptation_type=adaptation_type
        ).inc()

    def update_avg_student_progress(self, avg_progress: float):
        """
        Ortalama öğrenci ilerleme yüzdesini güncelle

        Args:
            avg_progress: Ortalama ilerleme (0-100)
        """
        self.avg_student_progress_gauge.set(avg_progress)

    def record_fallback_video_request(self, subject: str, found: bool):
        """
        Fallback video isteğini kaydet

        Args:
            subject: Ders adı
            found: Video bulundu mu?
        """
        found_str = "yes" if found else "no"
        self.fallback_video_requests_total.labels(
            subject=subject, found=found_str
        ).inc()


# Global metrics collector instance
_global_metrics_collector: MetricsCollector | None = None
_collector_lock = Lock()


def get_metrics_collector() -> MetricsCollector:
    """
    Global metrics collector instance'ını al (singleton pattern)

    Returns:
        MetricsCollector: Global metrics collector
    """
    global _global_metrics_collector

    if _global_metrics_collector is None:
        with _collector_lock:
            if _global_metrics_collector is None:
                _global_metrics_collector = MetricsCollector()
                logger.info("Global MetricsCollector instance created")

    return _global_metrics_collector


def reset_metrics_collector():
    """Global metrics collector'ı sıfırla (test için)"""
    global _global_metrics_collector

    with _collector_lock:
        if _global_metrics_collector is not None:
            _global_metrics_collector.reset_metrics()
