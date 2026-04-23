"""
Performance Monitor
Pipeline performans izleme ve metrik toplama

Requirements (REQ-8.x):
- REQ-8.1: Her agent'ın execution time'ını ölçer
- REQ-8.2: Bottleneck tespit eder
- REQ-8.3: Saat başına üretilen soru sayısını hesaplar
- REQ-8.4: Success rate hesaplar
- REQ-8.5: Optimization önerileri sunar
- REQ-8.6: Trend analizi yapar
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StageMetric:
    """Aşama metriği"""
    stage_name: str
    execution_time: float
    score: float
    passed: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PipelineMetric:
    """Pipeline metriği"""
    pipeline_id: str
    total_duration: float
    final_score: float
    decision: str
    stage_metrics: list[StageMetric]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PerformanceMonitor:
    """
    Pipeline Performans İzleyici

    Metrikler:
    - Stage execution times
    - Pipeline success rate
    - Throughput (questions/hour)
    - Quality scores over time
    """

    # Bottleneck threshold (saniye)
    BOTTLENECK_THRESHOLD = 30

    # Target metrics
    TARGET_THROUGHPUT = 50  # questions/hour
    TARGET_SUCCESS_RATE = 0.90
    TARGET_AVG_SCORE = 0.85

    def __init__(self, max_history: int = 1000):
        """
        Monitor başlat

        Args:
            max_history: Saklanacak maksimum metrik sayısı
        """
        self.max_history = max_history
        self._pipeline_metrics: list[PipelineMetric] = []
        self._stage_timings: dict[str, list[float]] = defaultdict(list)
        self._start_time = datetime.now(UTC)

    def record_pipeline(
        self,
        pipeline_id: str,
        total_duration: float,
        final_score: float,
        decision: str,
        stage_results: list[dict[str, Any]]
    ) -> None:
        """
        Pipeline metriği kaydet

        Args:
            pipeline_id: Pipeline ID
            total_duration: Toplam süre
            final_score: Final skor
            decision: Karar
            stage_results: Aşama sonuçları
        """
        # Stage metrikleri
        stage_metrics = []
        for result in stage_results:
            metric = StageMetric(
                stage_name=result.get("stage_name", result.get("stage", "")),
                execution_time=result.get("duration", 0.0),
                score=result.get("score", 0.0),
                passed=result.get("passed", False)
            )
            stage_metrics.append(metric)

            # Stage timing kaydet
            self._stage_timings[metric.stage_name].append(metric.execution_time)

        # Pipeline metriği
        pipeline_metric = PipelineMetric(
            pipeline_id=pipeline_id,
            total_duration=total_duration,
            final_score=final_score,
            decision=decision,
            stage_metrics=stage_metrics
        )

        self._pipeline_metrics.append(pipeline_metric)

        # History sınırla
        if len(self._pipeline_metrics) > self.max_history:
            self._pipeline_metrics = self._pipeline_metrics[-self.max_history:]

        logger.debug(f"Recorded metrics for pipeline {pipeline_id}")

    def get_stage_metrics(self, stage_name: str) -> dict[str, Any]:
        """
        Aşama metriklerini getir

        Args:
            stage_name: Aşama adı

        Returns:
            Dict: Aşama metrikleri
        """
        timings = self._stage_timings.get(stage_name, [])

        if not timings:
            return {"stage_name": stage_name, "no_data": True}

        return {
            "stage_name": stage_name,
            "total_executions": len(timings),
            "avg_duration": round(sum(timings) / len(timings), 2),
            "min_duration": round(min(timings), 2),
            "max_duration": round(max(timings), 2),
            "is_bottleneck": max(timings) > self.BOTTLENECK_THRESHOLD
        }

    def get_throughput(self, period_hours: float = 1.0) -> float:
        """
        Saat başına üretim hızını hesapla (REQ-8.3)

        Args:
            period_hours: Hesaplama periyodu (saat)

        Returns:
            float: Saat başına soru sayısı
        """
        if not self._pipeline_metrics:
            return 0.0

        # Son period'daki pipeline'ları say
        cutoff = datetime.now(UTC) - timedelta(hours=period_hours)
        recent = [
            p for p in self._pipeline_metrics
            if p.timestamp >= cutoff
        ]

        if not recent:
            return 0.0

        # Başarılı pipeline'ları say
        successful = sum(1 for p in recent if p.decision == "approved")

        return round(successful / period_hours, 1)

    def get_success_rate(self) -> float:
        """
        Başarı oranını hesapla (REQ-8.4)

        Returns:
            float: Başarı oranı (0-1)
        """
        if not self._pipeline_metrics:
            return 0.0

        approved = sum(1 for p in self._pipeline_metrics if p.decision == "approved")
        return round(approved / len(self._pipeline_metrics), 4)

    def get_bottlenecks(self) -> list[dict[str, Any]]:
        """
        Bottleneck'leri tespit et (REQ-8.2)

        Returns:
            List: Bottleneck stage'ler
        """
        bottlenecks = []

        for stage_name, timings in self._stage_timings.items():
            if not timings:
                continue

            avg_time = sum(timings) / len(timings)
            max_time = max(timings)

            if max_time > self.BOTTLENECK_THRESHOLD or avg_time > self.BOTTLENECK_THRESHOLD * 0.7:
                bottlenecks.append({
                    "stage_name": stage_name,
                    "avg_duration": round(avg_time, 2),
                    "max_duration": round(max_time, 2),
                    "severity": "high" if max_time > self.BOTTLENECK_THRESHOLD * 2 else "medium"
                })

        return sorted(bottlenecks, key=lambda x: x["max_duration"], reverse=True)

    def get_optimization_suggestions(self) -> list[str]:
        """
        Optimization önerileri (REQ-8.5)

        Returns:
            List[str]: Öneriler
        """
        suggestions = []

        # Throughput kontrolü
        throughput = self.get_throughput()
        if throughput < self.TARGET_THROUGHPUT:
            suggestions.append(
                f"Throughput düşük ({throughput:.1f}/saat). "
                f"Hedef: {self.TARGET_THROUGHPUT}/saat"
            )

        # Success rate kontrolü
        success_rate = self.get_success_rate()
        if success_rate < self.TARGET_SUCCESS_RATE:
            suggestions.append(
                f"Başarı oranı düşük ({success_rate:.1%}). "
                f"Hedef: {self.TARGET_SUCCESS_RATE:.0%}"
            )

        # Bottleneck önerileri
        bottlenecks = self.get_bottlenecks()
        for bn in bottlenecks[:2]:
            stage = bn["stage_name"]
            suggestions.append(f"{stage} aşaması yavaş - caching veya model optimization düşünün")

        # Ortalama skor
        if self._pipeline_metrics:
            avg_score = sum(p.final_score for p in self._pipeline_metrics) / len(self._pipeline_metrics)
            if avg_score < self.TARGET_AVG_SCORE:
                suggestions.append(
                    f"Ortalama skor düşük ({avg_score:.1%}). "
                    "LLM prompt'larını iyileştirin"
                )

        # Parallelization önerisi
        sequential_stages = ["content_generator", "difficulty_calibration", "distractor_generator"]
        for stage in sequential_stages:
            metrics = self.get_stage_metrics(stage)
            if metrics.get("avg_duration", 0) > 20:
                suggestions.append(f"{stage} için batch processing düşünün")
                break

        return suggestions

    def get_trend_analysis(self, days: int = 7) -> dict[str, Any]:
        """
        Trend analizi (REQ-8.6)

        Args:
            days: Analiz periyodu (gün)

        Returns:
            Dict: Trend verileri
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        recent = [p for p in self._pipeline_metrics if p.timestamp >= cutoff]

        if len(recent) < 2:
            return {"insufficient_data": True}

        # Günlük grupla
        daily_data: dict[str, list[PipelineMetric]] = defaultdict(list)
        for p in recent:
            day = p.timestamp.strftime("%Y-%m-%d")
            daily_data[day].append(p)

        # Trend hesapla
        trend = {
            "period_days": days,
            "total_pipelines": len(recent),
            "daily_avg_pipelines": len(recent) / days,
            "daily_metrics": []
        }

        for day, metrics in sorted(daily_data.items()):
            day_stats = {
                "date": day,
                "count": len(metrics),
                "avg_score": round(sum(p.final_score for p in metrics) / len(metrics), 3),
                "success_rate": sum(1 for p in metrics if p.decision == "approved") / len(metrics),
                "avg_duration": round(sum(p.total_duration for p in metrics) / len(metrics), 2)
            }
            trend["daily_metrics"].append(day_stats)

        # Trend yönü
        if len(trend["daily_metrics"]) >= 2:
            first_half = trend["daily_metrics"][:len(trend["daily_metrics"])//2]
            second_half = trend["daily_metrics"][len(trend["daily_metrics"])//2:]

            first_avg = sum(d["avg_score"] for d in first_half) / len(first_half)
            second_avg = sum(d["avg_score"] for d in second_half) / len(second_half)

            if second_avg > first_avg + 0.05:
                trend["direction"] = "improving"
            elif second_avg < first_avg - 0.05:
                trend["direction"] = "declining"
            else:
                trend["direction"] = "stable"
        else:
            trend["direction"] = "unknown"

        return trend

    def get_summary(self) -> dict[str, Any]:
        """Tüm metriklerin özeti"""
        return {
            "total_pipelines": len(self._pipeline_metrics),
            "success_rate": self.get_success_rate(),
            "throughput_per_hour": self.get_throughput(),
            "bottlenecks": self.get_bottlenecks()[:3],
            "optimization_suggestions": self.get_optimization_suggestions()[:3],
            "uptime_hours": (datetime.now(UTC) - self._start_time).total_seconds() / 3600
        }
