"""
Agent Metrics - Prometheus Metrics for Expert Agents
Task 18.3: Monitoring Dashboard

Metrics exported:
- expert_agent_questions_total: Total questions processed (counter)
- expert_agent_response_time_seconds: Response time histogram
- expert_agent_specialization_score: Current specialization score (gauge)
- expert_agent_contamination_rate: Cross-domain contamination rate (gauge)
- expert_agent_tokens_used: Token usage histogram
- expert_agent_success_rate: Success rate per domain (summary)
"""

import logging
import time
from contextlib import contextmanager

from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
    generate_latest,
)

logger = logging.getLogger(__name__)


# ============================================================
# Counters - Total counts
# ============================================================

QUESTIONS_PROCESSED = Counter(
    'expert_agent_questions_total',
    'Total questions processed by expert agents',
    ['domain', 'status']
)

MULTI_DOMAIN_QUESTIONS = Counter(
    'expert_agent_multidomain_total',
    'Total multi-domain questions processed'
)

AGENT_ERRORS = Counter(
    'expert_agent_errors_total',
    'Total errors in agent processing',
    ['domain', 'error_type']
)


# ============================================================
# Histograms - Distribution metrics
# ============================================================

RESPONSE_TIME = Histogram(
    'expert_agent_response_time_seconds',
    'Response time in seconds per agent',
    ['domain'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0]
)

TOKEN_USAGE = Histogram(
    'expert_agent_tokens_used',
    'Tokens used per request',
    ['domain'],
    buckets=[100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000, 200000]
)

CONFIDENCE_DISTRIBUTION = Histogram(
    'expert_agent_confidence',
    'Agent response confidence distribution',
    ['domain'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)


# ============================================================
# Gauges - Current values
# ============================================================

SPECIALIZATION_SCORE = Gauge(
    'expert_agent_specialization_score',
    'Current specialization score per domain',
    ['domain']
)

CONTEXT_USAGE_PERCENT = Gauge(
    'expert_agent_context_usage_percent',
    'Context usage percentage (of 200K limit)',
    ['domain']
)

CONTAMINATION_RATE = Gauge(
    'expert_agent_contamination_rate',
    'Cross-domain contamination rate (target: < 0.05)'
)

ACTIVE_AGENTS = Gauge(
    'expert_agent_active_count',
    'Number of currently active agents'
)

BLACKBOARD_MESSAGES = Gauge(
    'expert_agent_blackboard_messages',
    'Current messages in blackboard',
    ['domain']
)


# ============================================================
# Summaries - Statistical summaries
# ============================================================

SUCCESS_RATE = Summary(
    'expert_agent_success_rate',
    'Success rate per domain',
    ['domain']
)

USER_SATISFACTION = Summary(
    'expert_agent_user_satisfaction',
    'User satisfaction score per domain',
    ['domain']
)


# ============================================================
# Info - Static metadata
# ============================================================

AGENT_INFO = Info(
    'expert_agent_info',
    'Agent system information'
)


# ============================================================
# Helper Functions
# ============================================================

def record_question_processed(
    domain: str,
    success: bool,
    response_time_ms: float,
    tokens_used: int,
    confidence: float,
) -> None:
    """
    Record metrics for a processed question.

    Args:
        domain: Agent domain (matematik, fizik, etc.)
        success: Whether processing was successful
        response_time_ms: Response time in milliseconds
        tokens_used: Number of tokens used
        confidence: Response confidence [0, 1]
    """
    # Counter
    status = "success" if success else "failure"
    QUESTIONS_PROCESSED.labels(domain=domain, status=status).inc()

    # Histograms
    RESPONSE_TIME.labels(domain=domain).observe(response_time_ms / 1000.0)
    TOKEN_USAGE.labels(domain=domain).observe(tokens_used)
    CONFIDENCE_DISTRIBUTION.labels(domain=domain).observe(confidence)

    # Summary
    SUCCESS_RATE.labels(domain=domain).observe(1 if success else 0)


def record_multi_domain_question() -> None:
    """Record a multi-domain question."""
    MULTI_DOMAIN_QUESTIONS.inc()


def record_error(domain: str, error_type: str) -> None:
    """Record an agent error."""
    AGENT_ERRORS.labels(domain=domain, error_type=error_type).inc()


def update_specialization_score(domain: str, score: float) -> None:
    """Update specialization score for a domain."""
    SPECIALIZATION_SCORE.labels(domain=domain).set(score)


def update_context_usage(domain: str, usage_percent: float) -> None:
    """Update context usage percentage for a domain."""
    CONTEXT_USAGE_PERCENT.labels(domain=domain).set(usage_percent)


def update_contamination_rate(rate: float) -> None:
    """Update global contamination rate."""
    CONTAMINATION_RATE.set(rate)


def update_active_agents(count: int) -> None:
    """Update number of active agents."""
    ACTIVE_AGENTS.set(count)


def update_blackboard_messages(domain: str, count: int) -> None:
    """Update blackboard message count for a domain."""
    BLACKBOARD_MESSAGES.labels(domain=domain).set(count)


def record_user_satisfaction(domain: str, score: float) -> None:
    """Record user satisfaction score."""
    USER_SATISFACTION.labels(domain=domain).observe(score)


def set_agent_info(version: str, domains: str, max_context: int) -> None:
    """Set agent system information."""
    AGENT_INFO.info({
        'version': version,
        'supported_domains': domains,
        'max_context_tokens': str(max_context),
    })


@contextmanager
def track_response_time(domain: str):
    """
    Context manager to track response time.

    Usage:
        with track_response_time("matematik"):
            # process question
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed_ms = (time.time() - start_time) * 1000
        RESPONSE_TIME.labels(domain=domain).observe(elapsed_ms / 1000.0)


# ============================================================
# Metrics Exporter
# ============================================================

class AgentMetricsExporter:
    """
    Prometheus metrics exporter for expert agents.
    """

    def __init__(self):
        """Initialize metrics exporter."""
        self._initialized = False

    def initialize(
        self,
        version: str = "1.0.0",
        domains: str = "matematik,fizik,turkce,sosyal,biyoloji,yabanci_dil",
        max_context: int = 200000,
    ) -> None:
        """Initialize metrics with static info."""
        if not self._initialized:
            set_agent_info(version, domains, max_context)
            self._initialized = True
            logger.info("Agent metrics exporter initialized")

    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format."""
        return generate_latest(REGISTRY)

    def reset_metrics(self) -> None:
        """Reset all metrics (for testing)."""
        # Note: In production, metrics persist across requests


# Global exporter instance
metrics_exporter = AgentMetricsExporter()


# ============================================================
# FastAPI Integration
# ============================================================

def get_metrics_endpoint():
    """
    Get Prometheus metrics endpoint response.

    Usage in FastAPI:
        @app.get("/metrics")
        async def metrics():
            return Response(
                content=get_metrics_endpoint(),
                media_type="text/plain"
            )
    """
    return metrics_exporter.get_metrics()
