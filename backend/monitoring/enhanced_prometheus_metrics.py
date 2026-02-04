"""
Enhanced Prometheus Metrics for Kiro2 Platform
Sprint 10: Comprehensive Monitoring & Observability

Expanded metrics collection covering all platform aspects:
- Business metrics (users, exams, questions)
- System metrics (CPU, memory, disk)
- Application metrics (API, database, cache)
- AI/ML metrics (FSRS, IRT, recommendations)
- Security metrics (auth, rate limiting)
"""
import logging
import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    generate_latest,
    REGISTRY,
    CollectorRegistry,
)

logger = logging.getLogger(__name__)


class EnhancedPrometheusMetrics:
    """
    Enhanced Prometheus Metrics Collection

    Comprehensive metrics for Kiro2 platform monitoring
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize enhanced metrics

        Args:
            registry: Prometheus registry (defaults to default registry)
        """
        self.registry = registry or REGISTRY
        self._init_business_metrics()
        self._init_system_metrics()
        self._init_application_metrics()
        self._init_ai_ml_metrics()
        self._init_security_metrics()
        self._init_database_metrics()
        self._init_cache_metrics()

        logger.info("[ROCKET] Enhanced Prometheus metrics initialized - Full observability active!")

    # ==================== BUSINESS METRICS ====================

    def _init_business_metrics(self):
        """Initialize business KPI metrics"""

        # User Metrics
        self.total_users = Gauge(
            "kiro_users_total",
            "Total number of registered users",
            ["role"],  # student, teacher, parent, admin
            registry=self.registry
        )

        self.active_users_daily = Gauge(
            "kiro_active_users_daily",
            "Daily active users",
            ["role"],
            registry=self.registry
        )

        self.user_registrations = Counter(
            "kiro_user_registrations_total",
            "Total user registrations",
            ["role", "source"],  # source: web, mobile, api
            registry=self.registry
        )

        self.premium_conversions = Counter(
            "kiro_premium_conversions_total",
            "Premium subscription conversions",
            ["conversion_type"],  # upgrade, renewal, downgrade
            registry=self.registry
        )

        # Exam Metrics
        self.exams_started = Counter(
            "kiro_exams_started_total",
            "Total exams started",
            ["exam_type"],  # TYT, AYT, YDT, mock
            registry=self.registry
        )

        self.exams_completed = Counter(
            "kiro_exams_completed_total",
            "Total exams completed",
            ["exam_type", "completion_status"],  # finished, abandoned
            registry=self.registry
        )

        self.exam_scores = Histogram(
            "kiro_exam_scores",
            "Exam score distribution",
            ["exam_type"],
            buckets=[0, 20, 40, 60, 80, 100],
            registry=self.registry
        )

        self.exam_duration_minutes = Histogram(
            "kiro_exam_duration_minutes",
            "Exam duration in minutes",
            ["exam_type"],
            buckets=[15, 30, 45, 60, 90, 120, 135],
            registry=self.registry
        )

        # Question Metrics
        self.questions_answered = Counter(
            "kiro_questions_answered_total",
            "Total questions answered",
            ["subject", "difficulty", "correct"],  # correct: true/false
            registry=self.registry
        )

        self.question_response_time = Histogram(
            "kiro_question_response_time_seconds",
            "Time taken to answer question",
            ["subject"],
            buckets=[5, 15, 30, 60, 120, 180, 300],
            registry=self.registry
        )

        # Learning Path Metrics
        self.learning_paths_created = Counter(
            "kiro_learning_paths_created_total",
            "Total learning paths created",
            ["algorithm"],  # FSRS, IRT, ZPD
            registry=self.registry
        )

        self.daily_study_sessions = Counter(
            "kiro_study_sessions_total",
            "Total daily study sessions",
            ["session_type"],  # practice, review, exam
            registry=self.registry
        )

        self.study_duration_minutes = Histogram(
            "kiro_study_duration_minutes",
            "Study session duration",
            buckets=[5, 15, 30, 60, 120, 180],
            registry=self.registry
        )

    # ==================== SYSTEM METRICS ====================

    def _init_system_metrics(self):
        """Initialize system-level metrics"""

        # CPU Metrics
        self.cpu_usage_percent = Gauge(
            "kiro_system_cpu_usage_percent",
            "System CPU usage percentage",
            registry=self.registry
        )

        self.cpu_count = Gauge(
            "kiro_system_cpu_count",
            "Number of CPU cores",
            registry=self.registry
        )

        # Memory Metrics
        self.memory_usage_bytes = Gauge(
            "kiro_system_memory_usage_bytes",
            "System memory usage in bytes",
            registry=self.registry
        )

        self.memory_available_bytes = Gauge(
            "kiro_system_memory_available_bytes",
            "System available memory in bytes",
            registry=self.registry
        )

        self.memory_percent = Gauge(
            "kiro_system_memory_percent",
            "System memory usage percentage",
            registry=self.registry
        )

        # Disk Metrics
        self.disk_usage_bytes = Gauge(
            "kiro_system_disk_usage_bytes",
            "Disk usage in bytes",
            ["mountpoint"],
            registry=self.registry
        )

        self.disk_free_bytes = Gauge(
            "kiro_system_disk_free_bytes",
            "Disk free space in bytes",
            ["mountpoint"],
            registry=self.registry
        )

        # Network Metrics
        self.network_sent_bytes = Counter(
            "kiro_system_network_sent_bytes_total",
            "Total bytes sent over network",
            registry=self.registry
        )

        self.network_received_bytes = Counter(
            "kiro_system_network_received_bytes_total",
            "Total bytes received over network",
            registry=self.registry
        )

        # Process Metrics
        self.process_open_files = Gauge(
            "kiro_process_open_files",
            "Number of open file descriptors",
            registry=self.registry
        )

        self.process_threads = Gauge(
            "kiro_process_threads",
            "Number of threads",
            registry=self.registry
        )

    # ==================== APPLICATION METRICS ====================

    def _init_application_metrics(self):
        """Initialize application-level metrics"""

        # HTTP Metrics
        self.http_requests_total = Counter(
            "kiro_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            "kiro_http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )

        self.http_request_size_bytes = Histogram(
            "kiro_http_request_size_bytes",
            "HTTP request size",
            ["method", "endpoint"],
            buckets=[100, 1000, 10000, 100000, 1000000],
            registry=self.registry
        )

        self.http_response_size_bytes = Histogram(
            "kiro_http_response_size_bytes",
            "HTTP response size",
            ["method", "endpoint"],
            buckets=[100, 1000, 10000, 100000, 1000000],
            registry=self.registry
        )

        # Error Metrics
        self.errors_total = Counter(
            "kiro_errors_total",
            "Total errors",
            ["error_type", "severity"],  # severity: warning, error, critical
            registry=self.registry
        )

        self.unhandled_exceptions = Counter(
            "kiro_unhandled_exceptions_total",
            "Total unhandled exceptions",
            ["exception_type"],
            registry=self.registry
        )

        # Background Job Metrics
        self.background_jobs_total = Counter(
            "kiro_background_jobs_total",
            "Total background jobs",
            ["job_type", "status"],  # status: success, failure, retry
            registry=self.registry
        )

        self.background_job_duration_seconds = Histogram(
            "kiro_background_job_duration_seconds",
            "Background job duration",
            ["job_type"],
            buckets=[1, 5, 10, 30, 60, 300, 600],
            registry=self.registry
        )

        # WebSocket Metrics
        self.websocket_connections = Gauge(
            "kiro_websocket_connections_active",
            "Active WebSocket connections",
            ["connection_type"],
            registry=self.registry
        )

        self.websocket_messages_sent = Counter(
            "kiro_websocket_messages_sent_total",
            "Total WebSocket messages sent",
            ["message_type"],
            registry=self.registry
        )

        self.websocket_messages_received = Counter(
            "kiro_websocket_messages_received_total",
            "Total WebSocket messages received",
            ["message_type"],
            registry=self.registry
        )

    # ==================== AI/ML METRICS ====================

    def _init_ai_ml_metrics(self):
        """Initialize AI/ML algorithm metrics"""

        # FSRS Algorithm Metrics
        self.fsrs_reviews_scheduled = Counter(
            "kiro_fsrs_reviews_scheduled_total",
            "Total FSRS reviews scheduled",
            ["difficulty"],  # again, hard, good, easy
            registry=self.registry
        )

        self.fsrs_stability = Histogram(
            "kiro_fsrs_stability_days",
            "FSRS stability parameter distribution",
            buckets=[1, 3, 7, 14, 30, 60, 90, 180],
            registry=self.registry
        )

        self.fsrs_difficulty = Histogram(
            "kiro_fsrs_difficulty_score",
            "FSRS difficulty parameter distribution",
            buckets=[0, 2, 4, 6, 8, 10],
            registry=self.registry
        )

        # IRT Model Metrics
        self.irt_theta_estimates = Histogram(
            "kiro_irt_theta_estimates",
            "IRT theta (ability) estimates",
            ["subject"],
            buckets=[-3, -2, -1, 0, 1, 2, 3],
            registry=self.registry
        )

        self.irt_item_difficulty = Histogram(
            "kiro_irt_item_difficulty",
            "IRT item difficulty (b parameter)",
            ["subject"],
            buckets=[-3, -2, -1, 0, 1, 2, 3],
            registry=self.registry
        )

        self.irt_item_discrimination = Histogram(
            "kiro_irt_item_discrimination",
            "IRT item discrimination (a parameter)",
            buckets=[0, 0.5, 1.0, 1.5, 2.0, 2.5],
            registry=self.registry
        )

        # Recommendation Engine Metrics
        self.recommendations_generated = Counter(
            "kiro_recommendations_generated_total",
            "Total recommendations generated",
            ["recommendation_type"],  # question, video, content
            registry=self.registry
        )

        self.recommendation_accuracy = Histogram(
            "kiro_recommendation_accuracy",
            "Recommendation accuracy score",
            buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0],
            registry=self.registry
        )

        self.recommendation_latency_seconds = Histogram(
            "kiro_recommendation_latency_seconds",
            "Recommendation generation latency",
            ["algorithm"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry
        )

        # AI Model Metrics
        self.ai_model_requests = Counter(
            "kiro_ai_model_requests_total",
            "Total AI model requests",
            ["model"],  # GPT-4, BERTurk, etc.
            registry=self.registry
        )

        self.ai_model_latency_seconds = Histogram(
            "kiro_ai_model_latency_seconds",
            "AI model response latency",
            ["model"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )

        self.ai_model_tokens_used = Counter(
            "kiro_ai_model_tokens_used_total",
            "Total AI model tokens used",
            ["model", "token_type"],  # prompt, completion
            registry=self.registry
        )

    # ==================== SECURITY METRICS ====================

    def _init_security_metrics(self):
        """Initialize security-related metrics"""

        # Authentication Metrics
        self.auth_attempts = Counter(
            "kiro_auth_attempts_total",
            "Total authentication attempts",
            ["method", "result"],  # method: password, 2fa; result: success, failure
            registry=self.registry
        )

        self.auth_failures = Counter(
            "kiro_auth_failures_total",
            "Total authentication failures",
            ["failure_reason"],  # invalid_password, invalid_2fa, account_locked
            registry=self.registry
        )

        self.two_factor_enabled = Gauge(
            "kiro_two_factor_enabled_users",
            "Number of users with 2FA enabled",
            registry=self.registry
        )

        # Rate Limiting Metrics
        self.rate_limit_hits = Counter(
            "kiro_rate_limit_hits_total",
            "Total rate limit violations",
            ["endpoint", "tier"],  # tier: FREE, PREMIUM, ADMIN
            registry=self.registry
        )

        self.rate_limit_remaining = Gauge(
            "kiro_rate_limit_remaining",
            "Remaining rate limit quota",
            ["user_id", "endpoint"],
            registry=self.registry
        )

        # Security Events
        self.security_events = Counter(
            "kiro_security_events_total",
            "Total security events",
            ["event_type"],  # sql_injection, xss, csrf, suspicious_activity
            registry=self.registry
        )

        self.blocked_ips = Counter(
            "kiro_blocked_ips_total",
            "Total blocked IP addresses",
            ["reason"],
            registry=self.registry
        )

        # KVKK Compliance Metrics
        self.kvkk_consent_given = Counter(
            "kiro_kvkk_consent_given_total",
            "Total KVKK consents given",
            ["purpose"],
            registry=self.registry
        )

        self.kvkk_data_exports = Counter(
            "kiro_kvkk_data_exports_total",
            "Total KVKK data export requests",
            ["status"],  # completed, pending, failed
            registry=self.registry
        )

        self.kvkk_data_deletions = Counter(
            "kiro_kvkk_data_deletions_total",
            "Total KVKK data deletion requests",
            ["status"],
            registry=self.registry
        )

    # ==================== DATABASE METRICS ====================

    def _init_database_metrics(self):
        """Initialize database metrics"""

        # Connection Pool Metrics
        self.db_connections_active = Gauge(
            "kiro_db_connections_active",
            "Active database connections",
            ["pool"],
            registry=self.registry
        )

        self.db_connections_idle = Gauge(
            "kiro_db_connections_idle",
            "Idle database connections",
            ["pool"],
            registry=self.registry
        )

        self.db_connections_total = Gauge(
            "kiro_db_connections_total",
            "Total database connections",
            ["pool"],
            registry=self.registry
        )

        # Query Metrics
        self.db_queries_total = Counter(
            "kiro_db_queries_total",
            "Total database queries",
            ["query_type", "table"],  # query_type: SELECT, INSERT, UPDATE, DELETE
            registry=self.registry
        )

        self.db_query_duration_seconds = Histogram(
            "kiro_db_query_duration_seconds",
            "Database query duration",
            ["query_type", "table"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )

        self.db_slow_queries = Counter(
            "kiro_db_slow_queries_total",
            "Total slow queries (>1s)",
            ["table"],
            registry=self.registry
        )

        # Transaction Metrics
        self.db_transactions_total = Counter(
            "kiro_db_transactions_total",
            "Total database transactions",
            ["status"],  # committed, rollback
            registry=self.registry
        )

        self.db_deadlocks = Counter(
            "kiro_db_deadlocks_total",
            "Total database deadlocks",
            registry=self.registry
        )

    # ==================== CACHE METRICS ====================

    def _init_cache_metrics(self):
        """Initialize cache metrics"""

        # Cache Hit/Miss Metrics
        self.cache_operations = Counter(
            "kiro_cache_operations_total",
            "Total cache operations",
            ["operation", "cache_layer", "result"],  # operation: get, set, delete; result: hit, miss, error
            registry=self.registry
        )

        self.cache_hit_ratio = Gauge(
            "kiro_cache_hit_ratio",
            "Cache hit ratio (0-1)",
            ["cache_layer"],  # L1: app, L2: redis
            registry=self.registry
        )

        # Cache Performance Metrics
        self.cache_operation_duration_seconds = Histogram(
            "kiro_cache_operation_duration_seconds",
            "Cache operation duration",
            ["operation", "cache_layer"],
            buckets=[0.0001, 0.001, 0.01, 0.1, 1.0],
            registry=self.registry
        )

        # Cache Size Metrics
        self.cache_size_bytes = Gauge(
            "kiro_cache_size_bytes",
            "Cache size in bytes",
            ["cache_layer"],
            registry=self.registry
        )

        self.cache_entries = Gauge(
            "kiro_cache_entries",
            "Number of cache entries",
            ["cache_layer"],
            registry=self.registry
        )

        # Cache Invalidation Metrics
        self.cache_invalidations = Counter(
            "kiro_cache_invalidations_total",
            "Total cache invalidations",
            ["reason"],  # manual, expired, evicted, updated
            registry=self.registry
        )

    # ==================== SYSTEM RESOURCE COLLECTORS ====================

    def collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            # CPU
            self.cpu_usage_percent.set(psutil.cpu_percent(interval=0.1))
            self.cpu_count.set(psutil.cpu_count())

            # Memory
            memory = psutil.virtual_memory()
            self.memory_usage_bytes.set(memory.used)
            self.memory_available_bytes.set(memory.available)
            self.memory_percent.set(memory.percent)

            # Disk
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self.disk_usage_bytes.labels(mountpoint=partition.mountpoint).set(usage.used)
                    self.disk_free_bytes.labels(mountpoint=partition.mountpoint).set(usage.free)
                except PermissionError:
                    pass

            # Network
            net_io = psutil.net_io_counters()
            self.network_sent_bytes.inc(net_io.bytes_sent)
            self.network_received_bytes.inc(net_io.bytes_recv)

            # Process
            process = psutil.Process()
            self.process_open_files.set(len(process.open_files()))
            self.process_threads.set(process.num_threads())

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format"""
        return generate_latest(self.registry).decode('utf-8')


# Global instance
_enhanced_metrics: Optional[EnhancedPrometheusMetrics] = None


def get_enhanced_metrics() -> EnhancedPrometheusMetrics:
    """Get or create global enhanced metrics instance"""
    global _enhanced_metrics
    if _enhanced_metrics is None:
        _enhanced_metrics = EnhancedPrometheusMetrics()
    return _enhanced_metrics


if __name__ == "__main__":
    # Test metrics collection
    metrics = EnhancedPrometheusMetrics()

    # Simulate some metrics
    metrics.user_registrations.labels(role="student", source="web").inc()
    metrics.exams_started.labels(exam_type="TYT").inc()
    metrics.questions_answered.labels(subject="matematik", difficulty="medium", correct="true").inc()
    metrics.http_requests_total.labels(method="GET", endpoint="/api/v1/exams", status_code="200").inc()
    metrics.auth_attempts.labels(method="password", result="success").inc()

    # Collect system metrics
    metrics.collect_system_metrics()

    print("=" * 80)
    print("ENHANCED PROMETHEUS METRICS - SAMPLE OUTPUT")
    print("=" * 80)
    metrics_text = metrics.get_metrics_text()
    print(metrics_text[:2000])
    print("\n[...truncated...]")
    metric_count = len(metrics_text.splitlines())
    print(f"\nTotal metrics collected: {metric_count}")
