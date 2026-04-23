"""
Bottleneck Detector
Pipeline performans darboğazlarını tespit ve analiz

Requirements (REQ-8.2, REQ-8.5):
- Yavaş agent'ları işaretler
- Caching, parallelization, model optimization önerir
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BottleneckInfo:
    """Bottleneck bilgisi"""
    stage_name: str
    avg_duration: float
    max_duration: float
    p95_duration: float
    severity: str  # low, medium, high, critical
    impact_score: float  # 0-1
    recommendations: list[str]


class BottleneckDetector:
    """
    Pipeline Bottleneck Tespit Sistemi

    Analiz yöntemleri:
    - Execution time analizi
    - Variance analizi
    - Trend analizi
    - Impact scoring
    """

    # Severity thresholds (saniye)
    THRESHOLDS = {
        "low": 10,
        "medium": 20,
        "high": 30,
        "critical": 60
    }

    # Stage weights (impact hesabı için)
    STAGE_WEIGHTS = {
        "content_generator": 0.25,
        "difficulty_calibration": 0.20,
        "distractor_generator": 0.20,
        "osym_compliance": 0.20,
        "language_qa": 0.15,
        "quality_gate": 0.0
    }

    def __init__(self):
        """Detector başlat"""
        self._timing_history: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
        self._max_history = 500

    def record_timing(self, stage_name: str, duration: float) -> None:
        """
        Timing kaydet

        Args:
            stage_name: Aşama adı
            duration: Süre (saniye)
        """
        self._timing_history[stage_name].append((datetime.now(UTC), duration))

        # History sınırla
        if len(self._timing_history[stage_name]) > self._max_history:
            self._timing_history[stage_name] = self._timing_history[stage_name][-self._max_history:]

    def detect_bottlenecks(self, threshold_multiplier: float = 1.0) -> list[BottleneckInfo]:
        """
        Bottleneck'leri tespit et

        Args:
            threshold_multiplier: Eşik çarpanı

        Returns:
            List[BottleneckInfo]: Tespit edilen bottleneck'ler
        """
        bottlenecks = []

        for stage_name, timings in self._timing_history.items():
            if len(timings) < 5:
                continue

            durations = [t[1] for t in timings]

            # İstatistikler
            avg = sum(durations) / len(durations)
            max_val = max(durations)
            sorted_d = sorted(durations)
            p95 = sorted_d[int(len(sorted_d) * 0.95)]

            # Severity belirleme
            severity = self._calculate_severity(p95, threshold_multiplier)

            if severity != "normal":
                # Impact score
                impact = self._calculate_impact(stage_name, avg)

                # Recommendations
                recommendations = self._generate_recommendations(
                    stage_name, avg, max_val, severity
                )

                bottlenecks.append(BottleneckInfo(
                    stage_name=stage_name,
                    avg_duration=round(avg, 2),
                    max_duration=round(max_val, 2),
                    p95_duration=round(p95, 2),
                    severity=severity,
                    impact_score=impact,
                    recommendations=recommendations
                ))

        # Severity'ye göre sırala
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(
            bottlenecks,
            key=lambda x: (severity_order.get(x.severity, 4), -x.impact_score)
        )

    def _calculate_severity(self, p95: float, multiplier: float = 1.0) -> str:
        """Severity hesapla"""
        adjusted_p95 = p95 / multiplier

        if adjusted_p95 >= self.THRESHOLDS["critical"]:
            return "critical"
        if adjusted_p95 >= self.THRESHOLDS["high"]:
            return "high"
        if adjusted_p95 >= self.THRESHOLDS["medium"]:
            return "medium"
        if adjusted_p95 >= self.THRESHOLDS["low"]:
            return "low"
        return "normal"

    def _calculate_impact(self, stage_name: str, avg_duration: float) -> float:
        """
        Impact score hesapla

        Factors:
        - Stage weight
        - Duration relative to threshold
        - Position in pipeline (early = higher impact)
        """
        weight = self.STAGE_WEIGHTS.get(stage_name, 0.1)

        # Duration factor
        duration_factor = min(avg_duration / self.THRESHOLDS["high"], 1.0)

        # Position factor (basit - stage_name'e göre)
        stage_order = ["content_generator", "difficulty_calibration",
                       "distractor_generator", "osym_compliance",
                       "language_qa", "quality_gate"]
        try:
            position = stage_order.index(stage_name)
            position_factor = 1.0 - (position * 0.1)
        except ValueError:
            position_factor = 0.5

        impact = (weight * 0.4 + duration_factor * 0.4 + position_factor * 0.2)
        return round(impact, 3)

    def _generate_recommendations(
        self,
        stage_name: str,
        avg_duration: float,
        max_duration: float,
        severity: str
    ) -> list[str]:
        """Optimization önerileri üret"""
        recommendations = []

        # Genel öneriler
        if severity in ["critical", "high"]:
            recommendations.append(
                f"Kritik: {stage_name} aşaması ciddi bottleneck oluşturuyor"
            )

        # Stage-specific öneriler
        stage_recommendations = {
            "content_generator": [
                "LLM çağrılarını cache'leyin (benzer kazanımlar için)",
                "Batch processing ile birden fazla soru üretin",
                "Daha hızlı LLM modeli kullanın (quality trade-off)"
            ],
            "difficulty_calibration": [
                "IRT hesaplamalarını pre-compute edin",
                "Zorluk tahminlerini cache'leyin",
                "Basitleştirilmiş IRT modeli kullanın"
            ],
            "distractor_generator": [
                "Çeldirici template'leri kullanın",
                "Subject-specific distractor pool oluşturun",
                "LLM çağrılarını batch'leyin"
            ],
            "osym_compliance": [
                "Format validation'ı paralel çalıştırın",
                "Regex pattern'ları pre-compile edin",
                "Rule-based validation'ı cache'leyin"
            ],
            "language_qa": [
                "Zemberek sonuçlarını cache'leyin",
                "Okunabilirlik skorlarını pre-compute edin",
                "Spelling check'i async yapın"
            ],
            "quality_gate": [
                "Score aggregation'ı optimize edin",
                "Decision logic'i basitleştirin"
            ]
        }

        stage_recs = stage_recommendations.get(stage_name, [])
        recommendations.extend(stage_recs[:2])

        # Variance yüksekse
        if max_duration > avg_duration * 2:
            recommendations.append(
                "Yüksek variance: Timeout ve retry logic'i gözden geçirin"
            )

        # Genel optimization
        if avg_duration > self.THRESHOLDS["medium"]:
            recommendations.append("Model parallelization'ı değerlendirin")

        return recommendations[:4]

    def get_stage_analysis(self, stage_name: str) -> dict[str, Any]:
        """
        Detaylı stage analizi

        Args:
            stage_name: Aşama adı

        Returns:
            Dict: Analiz sonuçları
        """
        timings = self._timing_history.get(stage_name, [])

        if len(timings) < 2:
            return {"stage_name": stage_name, "insufficient_data": True}

        durations = [t[1] for t in timings]

        # İstatistikler
        avg = sum(durations) / len(durations)
        variance = sum((d - avg) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5

        sorted_d = sorted(durations)
        median = sorted_d[len(sorted_d) // 2]
        p90 = sorted_d[int(len(sorted_d) * 0.90)]
        p95 = sorted_d[int(len(sorted_d) * 0.95)]
        p99 = sorted_d[int(len(sorted_d) * 0.99)] if len(sorted_d) > 100 else max(durations)

        # Trend (son 20 vs önceki 20)
        if len(durations) >= 40:
            recent_avg = sum(durations[-20:]) / 20
            older_avg = sum(durations[-40:-20]) / 20
            trend = "improving" if recent_avg < older_avg * 0.9 else \
                    "worsening" if recent_avg > older_avg * 1.1 else "stable"
        else:
            trend = "insufficient_data"

        return {
            "stage_name": stage_name,
            "sample_count": len(durations),
            "statistics": {
                "mean": round(avg, 3),
                "median": round(median, 3),
                "std_dev": round(std_dev, 3),
                "min": round(min(durations), 3),
                "max": round(max(durations), 3),
                "p90": round(p90, 3),
                "p95": round(p95, 3),
                "p99": round(p99, 3)
            },
            "severity": self._calculate_severity(p95),
            "trend": trend,
            "is_bottleneck": p95 > self.THRESHOLDS["medium"]
        }

    def get_optimization_priority(self) -> list[dict[str, Any]]:
        """
        Optimization öncelik listesi

        ROI (Return on Investment) bazlı sıralama
        """
        priorities = []

        for stage_name in self._timing_history.keys():
            analysis = self.get_stage_analysis(stage_name)

            if analysis.get("insufficient_data"):
                continue

            stats = analysis.get("statistics", {})

            # ROI hesabı
            # Impact = weight * duration
            # Effort = complexity (basit tahmin)
            weight = self.STAGE_WEIGHTS.get(stage_name, 0.1)
            duration = stats.get("mean", 0)
            impact = weight * duration

            # Effort tahmini (1-5)
            effort_map = {
                "content_generator": 4,
                "difficulty_calibration": 2,
                "distractor_generator": 3,
                "osym_compliance": 2,
                "language_qa": 3,
                "quality_gate": 1
            }
            effort = effort_map.get(stage_name, 3)

            roi = impact / effort if effort > 0 else 0

            priorities.append({
                "stage_name": stage_name,
                "impact": round(impact, 3),
                "effort": effort,
                "roi": round(roi, 3),
                "severity": analysis.get("severity"),
                "recommendations": self._generate_recommendations(
                    stage_name, duration, stats.get("max", duration), analysis.get("severity", "low")
                )[:2]
            })

        return sorted(priorities, key=lambda x: x["roi"], reverse=True)
