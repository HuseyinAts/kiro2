"""
Prometheus Metrics Exporter
Teknofest 2025 - Eğitim Eylemci Projesi

Custom metrics export for Prometheus monitoring:
- Video recommendation metrics
- Learning style detection metrics
- API performance metrics
- User activity metrics
"""

import logging
import os
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """
    Prometheus Metrics Exporter

    Custom metrics collection and export for platform monitoring
    """

    def __init__(self, port: int = 9091, enable_custom_metrics: bool = True):
        """
        Initialize Prometheus Exporter

        Args:
            port: Prometheus exporter port
            enable_custom_metrics: Enable platform-specific custom metrics
        """
        self.port = port
        self.enable_custom_metrics = enable_custom_metrics

        # Initialize metrics
        self._init_metrics()

        logger.info(f"Prometheus Exporter initialized on port {port}")

    def _init_metrics(self):
        """Initialize Prometheus metrics"""

        # Video Recommendation Metrics
        self.video_recommendations_total = Counter(
            "kiro_video_recommendations_total",
            "Total number of video recommendations made",
            ["subject", "learning_style"],
        )

        self.video_recommendation_latency = Histogram(
            "kiro_video_recommendation_latency_seconds",
            "Video recommendation latency in seconds",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
        )

        self.turkish_content_filter_score = Histogram(
            "kiro_turkish_content_filter_score",
            "Turkish content filter score distribution",
            buckets=[0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        )

        # Learning Style Metrics
        self.learning_style_detections = Counter(
            "kiro_learning_style_detections_total",
            "Total learning style detections",
            ["profile_type"],
        )

        self.learning_style_confidence = Histogram(
            "kiro_learning_style_confidence",
            "Learning style detection confidence scores",
            buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        )

        # API Performance Metrics
        self.api_requests_total = Counter(
            "kiro_api_requests_total",
            "Total API requests",
            ["endpoint", "method", "status"],
        )

        self.api_request_duration = Histogram(
            "kiro_api_request_duration_seconds",
            "API request duration in seconds",
            ["endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0],
        )

        # User Activity Metrics
        self.active_users = Gauge(
            "kiro_active_users", "Current number of active users", ["user_type"]
        )

        self.questions_solved = Counter(
            "kiro_questions_solved_total",
            "Total questions solved",
            ["subject", "difficulty"],
        )

        self.exam_attempts = Counter(
            "kiro_exam_attempts_total", "Total exam attempts", ["exam_type"]
        )

        # Agent Metrics
        self.agent_messages = Counter(
            "kiro_agent_messages_total",
            "Total agent messages processed",
            ["agent_type", "message_type"],
        )

        self.blackboard_broadcasts = Counter(
            "kiro_blackboard_broadcasts_total", "Total blackboard broadcasts", ["topic"]
        )

        self.blackboard_latency = Histogram(
            "kiro_blackboard_broadcast_latency_ms",
            "Blackboard broadcast latency in milliseconds",
            buckets=[10, 25, 50, 75, 100, 200],
        )

        # Database Metrics
        self.db_connections = Gauge(
            "kiro_db_connections", "Current database connections", ["pool"]
        )

        self.db_query_duration = Histogram(
            "kiro_db_query_duration_seconds",
            "Database query duration",
            ["query_type"],
            buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0],
        )

        # Cache Metrics
        self.cache_hits = Counter(
            "kiro_cache_hits_total", "Total cache hits", ["cache_type"]
        )

        self.cache_misses = Counter(
            "kiro_cache_misses_total", "Total cache misses", ["cache_type"]
        )

        logger.info("Prometheus metrics initialized")

    def record_video_recommendation(
        self,
        subject: str,
        learning_style: str,
        latency_seconds: float,
        turkish_score: float,
    ):
        """Record video recommendation metrics"""
        self.video_recommendations_total.labels(
            subject=subject, learning_style=learning_style
        ).inc()

        self.video_recommendation_latency.observe(latency_seconds)
        self.turkish_content_filter_score.observe(turkish_score)

    def record_learning_style_detection(self, profile_type: str, confidence: float):
        """Record learning style detection"""
        self.learning_style_detections.labels(profile_type=profile_type).inc()
        self.learning_style_confidence.observe(confidence)

    def record_api_request(
        self, endpoint: str, method: str, status: int, duration_seconds: float
    ):
        """Record API request metrics"""
        self.api_requests_total.labels(
            endpoint=endpoint, method=method, status=str(status)
        ).inc()

        self.api_request_duration.labels(endpoint=endpoint).observe(duration_seconds)

    def record_blackboard_broadcast(self, topic: str, latency_ms: float):
        """Record blackboard broadcast"""
        self.blackboard_broadcasts.labels(topic=topic).inc()
        self.blackboard_latency.observe(latency_ms)

    def set_active_users(self, user_type: str, count: int):
        """Set active users gauge"""
        self.active_users.labels(user_type=user_type).set(count)

    def record_question_solved(self, subject: str, difficulty: str):
        """Record question solved"""
        self.questions_solved.labels(subject=subject, difficulty=difficulty).inc()

    def record_exam_attempt(self, exam_type: str):
        """Record exam attempt"""
        self.exam_attempts.labels(exam_type=exam_type).inc()

    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        return generate_latest(REGISTRY).decode("utf-8")


# Global exporter instance
_exporter: PrometheusExporter = None


def get_exporter() -> PrometheusExporter:
    """Get or create global Prometheus exporter"""
    global _exporter
    if _exporter is None:
        _exporter = PrometheusExporter()
    return _exporter


if __name__ == "__main__":
    import sys
    import time

    port = int(os.getenv("PROMETHEUS_PORT", "9091"))

    if "--test" in sys.argv:
        # Test mode
        exporter = PrometheusExporter(port=port)

        # Simulate some metrics
        exporter.record_video_recommendation(
            subject="matematik",
            learning_style="Visual-Active",
            latency_seconds=1.5,
            turkish_score=0.85,
        )

        exporter.record_learning_style_detection(
            profile_type="Visual-Active-Sensing-Sequential", confidence=0.82
        )

        exporter.record_api_request(
            endpoint="/api/v1/videos", method="GET", status=200, duration_seconds=0.15
        )

        print("Metrics sample:")
        print(exporter.get_metrics()[:500])
    else:
        # Service mode - keep running
        exporter = PrometheusExporter(port=port)
        print(f"[Prometheus Exporter] Started on port {port}")
        print(
            f"[Prometheus Exporter] Metrics available at http://localhost:{port}/metrics"
        )
        print("[Prometheus Exporter] Press Ctrl+C to stop")

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[Prometheus Exporter] Shutting down...")
