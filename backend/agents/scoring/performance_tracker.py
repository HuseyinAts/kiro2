"""
Performance Tracker - Agent Performans Izleme
REQ-8.3, REQ-8.4, REQ-8.5
Teknofest 2025 - KIRO2 YKS Platformu

Agent performans metriklerini izler ve iyilestirme tespit eder.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..domain_experts.base_domain_agent import DomainType, DomainResponse

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Agent performans metrikleri"""

    domain: DomainType
    total_questions: int = 0
    successful_responses: int = 0
    failed_responses: int = 0
    total_tokens_used: int = 0
    total_response_time_ms: float = 0.0
    average_confidence: float = 0.0
    last_activity: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """Basari orani"""
        if self.total_questions == 0:
            return 0.0
        return self.successful_responses / self.total_questions

    @property
    def average_response_time_ms(self) -> float:
        """Ortalama yanit suresi"""
        if self.total_questions == 0:
            return 0.0
        return self.total_response_time_ms / self.total_questions

    @property
    def average_tokens_per_question(self) -> float:
        """Soru basina ortalama token"""
        if self.total_questions == 0:
            return 0.0
        return self.total_tokens_used / self.total_questions


class PerformanceTracker:
    """
    Performans Izleyici (REQ-8.3, REQ-8.4, REQ-8.5)

    Her agent icin performans metriklerini izler,
    trend analizi yapar ve iyilestirme tespit eder.
    """

    def __init__(self):
        """PerformanceTracker olustur"""
        self._metrics: Dict[DomainType, PerformanceMetrics] = {}
        self._history: Dict[DomainType, List[Dict[str, Any]]] = {}
        logger.info("PerformanceTracker initialized")

    def track_response(self, response: DomainResponse):
        """
        Agent yanitini izle

        Args:
            response: Agent yaniti
        """
        domain = response.domain

        # Initialize metrics if needed
        if domain not in self._metrics:
            self._metrics[domain] = PerformanceMetrics(domain=domain)
            self._history[domain] = []

        metrics = self._metrics[domain]

        # Update metrics
        metrics.total_questions += 1
        if response.is_successful():
            metrics.successful_responses += 1
        else:
            metrics.failed_responses += 1

        metrics.total_tokens_used += response.tokens_used
        metrics.total_response_time_ms += response.response_time_ms
        metrics.last_activity = datetime.now()

        # Update running average for confidence
        n = metrics.total_questions
        metrics.average_confidence = (
            metrics.average_confidence * (n - 1) + response.confidence
        ) / n

        # Store in history
        self._history[domain].append({
            "timestamp": datetime.now().isoformat(),
            "confidence": response.confidence,
            "response_time_ms": response.response_time_ms,
            "tokens_used": response.tokens_used,
            "success": response.is_successful(),
        })

        logger.debug(
            f"Tracked response for {domain.value}: "
            f"success={response.is_successful()}, confidence={response.confidence:.2f}"
        )

    def get_metrics(self, domain: DomainType) -> Optional[PerformanceMetrics]:
        """Domain icin metrikleri al"""
        return self._metrics.get(domain)

    def get_all_metrics(self) -> Dict[DomainType, PerformanceMetrics]:
        """Tum metrikleri al"""
        return dict(self._metrics)

    def detect_improvement(
        self,
        domain: DomainType,
        window_size: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Iyilestirme tespit et (REQ-8.5)

        Son window_size yaniti onceki donemle karsilastir.

        Args:
            domain: Agent domain'i
            window_size: Karsilastirma pencere boyutu

        Returns:
            Iyilestirme analiz sonucu veya None
        """
        history = self._history.get(domain, [])
        if len(history) < window_size * 2:
            return None  # Not enough data

        recent = history[-window_size:]
        previous = history[-(window_size * 2):-window_size]

        recent_avg_conf = sum(h["confidence"] for h in recent) / len(recent)
        previous_avg_conf = sum(h["confidence"] for h in previous) / len(previous)

        recent_success_rate = sum(1 for h in recent if h["success"]) / len(recent)
        previous_success_rate = sum(1 for h in previous if h["success"]) / len(previous)

        recent_avg_time = sum(h["response_time_ms"] for h in recent) / len(recent)
        previous_avg_time = sum(h["response_time_ms"] for h in previous) / len(previous)

        confidence_change = recent_avg_conf - previous_avg_conf
        success_change = recent_success_rate - previous_success_rate
        time_change = previous_avg_time - recent_avg_time  # Negative is better

        is_improving = (
            confidence_change > 0.05 or
            success_change > 0.05 or
            time_change > 100  # 100ms improvement
        )

        return {
            "domain": domain.value,
            "is_improving": is_improving,
            "confidence_change": confidence_change,
            "success_rate_change": success_change,
            "response_time_change_ms": time_change,
            "recent_metrics": {
                "avg_confidence": recent_avg_conf,
                "success_rate": recent_success_rate,
                "avg_response_time_ms": recent_avg_time,
            },
            "previous_metrics": {
                "avg_confidence": previous_avg_conf,
                "success_rate": previous_success_rate,
                "avg_response_time_ms": previous_avg_time,
            },
        }

    def get_trend(
        self,
        domain: DomainType,
        metric: str = "confidence",
        points: int = 10,
    ) -> Optional[List[float]]:
        """
        Metrik trendi al

        Args:
            domain: Agent domain'i
            metric: "confidence", "response_time_ms", "tokens_used"
            points: Veri noktasi sayisi

        Returns:
            Son N veri noktasi veya None
        """
        history = self._history.get(domain, [])
        if not history:
            return None

        recent = history[-points:]
        return [h.get(metric, 0) for h in recent]

    def get_summary(self) -> Dict[str, Any]:
        """Performans ozeti al"""
        summary = {
            "domains_tracked": len(self._metrics),
            "total_questions": sum(m.total_questions for m in self._metrics.values()),
            "overall_success_rate": 0.0,
            "domains": {},
        }

        total_success = sum(m.successful_responses for m in self._metrics.values())
        total_questions = sum(m.total_questions for m in self._metrics.values())
        if total_questions > 0:
            summary["overall_success_rate"] = total_success / total_questions

        for domain, metrics in self._metrics.items():
            improvement = self.detect_improvement(domain)
            summary["domains"][domain.value] = {
                "total_questions": metrics.total_questions,
                "success_rate": metrics.success_rate,
                "average_confidence": metrics.average_confidence,
                "average_response_time_ms": metrics.average_response_time_ms,
                "is_improving": improvement["is_improving"] if improvement else None,
                "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None,
            }

        return summary
