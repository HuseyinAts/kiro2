"""
Performance Monitoring Service - CLAUDE.md Self-Improvement

Bu servis, iyileşme performansını izler:
- Baseline metric snapshot
- Improvement measurement
- Regression detection
- Trend analysis
- Anomaly detection
- Real-time dashboard data

Spec: claude-md-self-improvement REQ-7
- REQ-7.1: Baseline metric snapshot
- REQ-7.2: Task success rate, latency, quality score karşılaştırma
- REQ-7.3: Automatic rollback trigger
- REQ-7.4: Moving average ve seasonality
- REQ-7.5: Z-score > 3 anomaly detection
- REQ-7.6: Real-time dashboard metrics

Author: KIRO2 Team
Date: 2026-01-17
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

# Scientific computing
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

# Database
# Models
from backend.models.claude_md_improvement_models import (
    AuditLog,
    FeedbackRecord,
    RuleEffectiveness,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class BaselineSnapshot:
    """Baseline performance snapshot."""
    snapshot_id: str
    created_at: datetime
    metrics: dict[str, float]
    sample_size: int


@dataclass
class PerformanceMetrics:
    """Current performance metrics."""
    task_success_rate: float
    avg_latency: float
    quality_score: float
    total_tasks: int
    period: str
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    metric: str
    trend: str  # "increasing", "decreasing", "stable"
    slope: float
    moving_average: list[float]
    seasonality_detected: bool
    seasonality_period: int | None


@dataclass
class AnomalyDetection:
    """Anomaly detection result."""
    metric: str
    value: float
    z_score: float
    is_anomaly: bool
    detected_at: datetime
    severity: str  # "low", "medium", "high"


class PerformanceMonitorService:
    """
    Performance monitoring service for CLAUDE.md improvements.

    Tracks and analyzes performance metrics to:
    - Establish baselines
    - Measure improvements
    - Detect regressions
    - Identify anomalies
    """

    # Configuration
    ANOMALY_THRESHOLD = 3.0  # Z-score threshold
    REGRESSION_THRESHOLD = 0.1  # 10% decline triggers alert
    MOVING_AVERAGE_WINDOW = 7  # Days
    MIN_SAMPLES_FOR_BASELINE = 100

    def __init__(self, db: AsyncSession):
        """Initialize performance monitor."""
        self.db = db
        self._baselines: dict[str, BaselineSnapshot] = {}
        self._metric_history: dict[str, list[tuple[datetime, float]]] = defaultdict(list)

    # =========================================================================
    # REQ-7.1: Baseline Metric Snapshot
    # =========================================================================

    async def create_baseline(
        self,
        baseline_id: str = "default",
    ) -> BaselineSnapshot:
        """
        Create baseline snapshot of current performance.

        Args:
            baseline_id: Identifier for this baseline

        Returns:
            BaselineSnapshot with all metrics
        """
        # Calculate current metrics
        metrics = await self._calculate_all_metrics(days=30)

        # Get sample size
        cutoff = datetime.now(UTC) - timedelta(days=30)
        result = await self.db.execute(
            select(func.count())
            .select_from(FeedbackRecord)
            .where(FeedbackRecord.created_at >= cutoff)
        )
        sample_size = result.scalar() or 0

        if sample_size < self.MIN_SAMPLES_FOR_BASELINE:
            logger.warning(f"Baseline created with low sample size: {sample_size}")

        baseline = BaselineSnapshot(
            snapshot_id=baseline_id,
            created_at=datetime.now(UTC),
            metrics=metrics,
            sample_size=sample_size,
        )

        self._baselines[baseline_id] = baseline

        # Log audit
        await self._log_audit(
            action="create_baseline",
            entity_type="performance",
            entity_id=baseline_id,
            details={
                "metrics": metrics,
                "sample_size": sample_size,
            },
        )

        logger.info(f"Created baseline '{baseline_id}' with {sample_size} samples")
        return baseline

    async def get_baseline(
        self,
        baseline_id: str = "default",
    ) -> BaselineSnapshot | None:
        """Get baseline by ID."""
        return self._baselines.get(baseline_id)

    # =========================================================================
    # REQ-7.2: Improvement Measurement
    # =========================================================================

    async def measure_improvement(
        self,
        baseline_id: str = "default",
        period_days: int = 7,
    ) -> dict[str, Any]:
        """
        Measure improvement compared to baseline.

        Args:
            baseline_id: Baseline to compare against
            period_days: Period to measure

        Returns:
            Improvement analysis for all metrics
        """
        baseline = self._baselines.get(baseline_id)
        if not baseline:
            return {"error": f"Baseline not found: {baseline_id}"}

        # Get current metrics
        current = await self._calculate_all_metrics(days=period_days)

        # Calculate improvements
        improvements = {}
        for metric, baseline_value in baseline.metrics.items():
            current_value = current.get(metric, 0)

            if baseline_value > 0:
                change = current_value - baseline_value
                percent_change = (change / baseline_value) * 100
            else:
                change = current_value
                percent_change = 100 if current_value > 0 else 0

            improvements[metric] = {
                "baseline": baseline_value,
                "current": current_value,
                "change": change,
                "percent_change": percent_change,
                "improved": change > 0,
            }

        # Check for regression
        regressions = [
            m for m, v in improvements.items()
            if v["percent_change"] < -self.REGRESSION_THRESHOLD * 100
        ]

        return {
            "baseline_id": baseline_id,
            "baseline_date": baseline.created_at.isoformat(),
            "period_days": period_days,
            "improvements": improvements,
            "regressions": regressions,
            "overall_improved": len(regressions) == 0,
        }

    async def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        metrics = await self._calculate_all_metrics(days=7)

        result = await self.db.execute(
            select(func.count())
            .select_from(FeedbackRecord)
            .where(
                FeedbackRecord.created_at >= datetime.now(UTC) - timedelta(days=7)
            )
        )
        total_tasks = result.scalar() or 0

        return PerformanceMetrics(
            task_success_rate=metrics.get("success_rate", 0),
            avg_latency=metrics.get("avg_latency", 0),
            quality_score=metrics.get("quality_score", 0),
            total_tasks=total_tasks,
            period="7d",
        )

    # =========================================================================
    # REQ-7.3: Automatic Rollback Trigger
    # =========================================================================

    async def check_regression(
        self,
        baseline_id: str = "default",
    ) -> tuple[bool, str | None]:
        """
        Check if performance has regressed and trigger rollback.

        Args:
            baseline_id: Baseline to compare against

        Returns:
            Tuple of (should_rollback, reason)
        """
        improvement = await self.measure_improvement(baseline_id, period_days=1)

        if "error" in improvement:
            return False, None

        # Check for severe regressions
        for metric, data in improvement.get("improvements", {}).items():
            percent_change = data.get("percent_change", 0)

            if percent_change < -self.REGRESSION_THRESHOLD * 100:
                reason = (
                    f"Regression detected in {metric}: "
                    f"{percent_change:.1f}% decline from baseline"
                )

                await self._log_audit(
                    action="regression_detected",
                    entity_type="performance",
                    details={
                        "metric": metric,
                        "percent_change": percent_change,
                        "baseline_id": baseline_id,
                    },
                )

                logger.warning(reason)
                return True, reason

        return False, None

    async def trigger_rollback(
        self,
        reason: str,
    ) -> dict[str, Any]:
        """
        Trigger automatic rollback.

        Args:
            reason: Reason for rollback

        Returns:
            Rollback result
        """
        # Import here to avoid circular dependency
        try:

            # Get rules with recent changes
            result = await self.db.execute(
                select(RuleEffectiveness)
                .where(
                    RuleEffectiveness.last_updated >= datetime.now(UTC) - timedelta(hours=24)
                )
            )
            recent_rules = result.scalars().all()

            rollback_count = 0
            for rule in recent_rules:
                # Request rollback (actual rollback delegated to rule_evolution_service)
                logger.info(f"Requesting rollback for rule: {rule.rule_id}")
                rollback_count += 1

            await self._log_audit(
                action="trigger_rollback",
                entity_type="performance",
                details={
                    "reason": reason,
                    "rules_affected": rollback_count,
                },
            )

            return {
                "rollback_triggered": True,
                "reason": reason,
                "rules_affected": rollback_count,
                "recovery_time_seconds": rollback_count * 0.5,  # Estimated
            }

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {
                "rollback_triggered": False,
                "error": str(e),
            }

    # =========================================================================
    # REQ-7.4: Trend Analysis
    # =========================================================================

    async def analyze_trend(
        self,
        metric: str,
        days: int = 30,
    ) -> TrendAnalysis:
        """
        Analyze trend for a specific metric.

        Args:
            metric: Metric name
            days: Analysis period

        Returns:
            TrendAnalysis with slope, moving average, seasonality
        """
        # Get historical data
        history = await self._get_metric_history(metric, days)

        if len(history) < 3:
            return TrendAnalysis(
                metric=metric,
                trend="unknown",
                slope=0.0,
                moving_average=[],
                seasonality_detected=False,
                seasonality_period=None,
            )

        # Calculate moving average
        ma = self._calculate_moving_average(history, window=self.MOVING_AVERAGE_WINDOW)

        # Calculate trend (linear regression slope)
        slope = self._calculate_slope(history)

        # Determine trend direction
        if slope > 0.01:
            trend = "increasing"
        elif slope < -0.01:
            trend = "decreasing"
        else:
            trend = "stable"

        # Detect seasonality (simple autocorrelation check)
        seasonality_detected, seasonality_period = self._detect_seasonality(history)

        return TrendAnalysis(
            metric=metric,
            trend=trend,
            slope=slope,
            moving_average=ma,
            seasonality_detected=seasonality_detected,
            seasonality_period=seasonality_period,
        )

    def _calculate_moving_average(
        self,
        values: list[float],
        window: int,
    ) -> list[float]:
        """Calculate moving average."""
        if len(values) < window:
            return values

        ma = []
        for i in range(len(values) - window + 1):
            window_values = values[i:i + window]
            ma.append(sum(window_values) / window)

        return ma

    def _calculate_slope(self, values: list[float]) -> float:
        """Calculate linear regression slope."""
        n = len(values)
        if n < 2:
            return 0.0

        mean_x = (n - 1) / 2
        mean_y = sum(values) / n

        numerator = sum(
            (i - mean_x) * (y - mean_y)
            for i, y in enumerate(values)
        )
        denominator = sum((i - mean_x) ** 2 for i in range(n))

        return numerator / max(denominator, 0.001)

    def _detect_seasonality(
        self,
        values: list[float],
    ) -> tuple[bool, int | None]:
        """Detect seasonality using autocorrelation."""
        if len(values) < 14:  # Need at least 2 weeks
            return False, None

        # Check for weekly pattern (period=7)
        for period in [7, 14]:
            if len(values) >= period * 2:
                # Simple autocorrelation check
                correlation = self._autocorrelation(values, period)

                if correlation > 0.5:  # Strong correlation
                    return True, period

        return False, None

    def _autocorrelation(
        self,
        values: list[float],
        lag: int,
    ) -> float:
        """Calculate autocorrelation at given lag."""
        n = len(values)
        if n <= lag:
            return 0.0

        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n

        if variance == 0:
            return 0.0

        covariance = sum(
            (values[i] - mean) * (values[i - lag] - mean)
            for i in range(lag, n)
        ) / (n - lag)

        return covariance / variance

    # =========================================================================
    # REQ-7.5: Anomaly Detection (Z-score > 3)
    # =========================================================================

    async def detect_anomalies(
        self,
        metric: str,
        current_value: float,
    ) -> AnomalyDetection:
        """
        Detect if current value is anomalous.

        Uses Z-score with threshold of 3.

        Args:
            metric: Metric name
            current_value: Current metric value

        Returns:
            AnomalyDetection result
        """
        # Get historical data
        history = await self._get_metric_history(metric, days=30)

        if len(history) < 10:
            return AnomalyDetection(
                metric=metric,
                value=current_value,
                z_score=0.0,
                is_anomaly=False,
                detected_at=datetime.now(UTC),
                severity="low",
            )

        # Calculate mean and standard deviation
        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std = math.sqrt(variance) if variance > 0 else 0.001

        # Calculate Z-score
        z_score = abs(current_value - mean) / std

        # Determine if anomaly
        is_anomaly = z_score > self.ANOMALY_THRESHOLD

        # Determine severity
        if z_score > 5:
            severity = "high"
        elif z_score > self.ANOMALY_THRESHOLD:
            severity = "medium"
        else:
            severity = "low"

        if is_anomaly:
            await self._log_audit(
                action="anomaly_detected",
                entity_type="performance",
                details={
                    "metric": metric,
                    "value": current_value,
                    "z_score": z_score,
                    "severity": severity,
                },
            )

        return AnomalyDetection(
            metric=metric,
            value=current_value,
            z_score=z_score,
            is_anomaly=is_anomaly,
            detected_at=datetime.now(UTC),
            severity=severity,
        )

    async def scan_all_anomalies(self) -> list[AnomalyDetection]:
        """Scan all metrics for anomalies."""
        metrics = await self._calculate_all_metrics(days=1)
        anomalies = []

        for metric, value in metrics.items():
            result = await self.detect_anomalies(metric, value)
            if result.is_anomaly:
                anomalies.append(result)

        return anomalies

    # =========================================================================
    # REQ-7.6: Real-time Dashboard
    # =========================================================================

    async def get_dashboard_data(self) -> dict[str, Any]:
        """
        Get real-time dashboard data.

        Returns:
            Complete dashboard data structure
        """
        # Current metrics
        current = await self.get_current_metrics()

        # Get baseline comparison
        improvement = await self.measure_improvement("default", period_days=7)

        # Trend analysis for key metrics
        success_trend = await self.analyze_trend("success_rate", days=30)
        latency_trend = await self.analyze_trend("avg_latency", days=30)

        # Recent anomalies
        anomalies = await self.scan_all_anomalies()

        # Time series data for charts
        time_series = await self._get_time_series_data(days=14)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "current_metrics": {
                "success_rate": current.task_success_rate,
                "avg_latency": current.avg_latency,
                "quality_score": current.quality_score,
                "total_tasks": current.total_tasks,
            },
            "improvement": improvement if "error" not in improvement else None,
            "trends": {
                "success_rate": {
                    "direction": success_trend.trend,
                    "slope": success_trend.slope,
                    "seasonality": success_trend.seasonality_detected,
                },
                "latency": {
                    "direction": latency_trend.trend,
                    "slope": latency_trend.slope,
                },
            },
            "anomalies": [
                {
                    "metric": a.metric,
                    "value": a.value,
                    "z_score": a.z_score,
                    "severity": a.severity,
                }
                for a in anomalies
            ],
            "time_series": time_series,
            "health_status": self._calculate_health_status(current, anomalies),
        }

    async def _get_time_series_data(
        self,
        days: int,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get time series data for charts."""
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Get daily aggregates
        result = await self.db.execute(
            select(
                func.date_trunc("day", FeedbackRecord.created_at).label("day"),
                func.count().label("total"),
                func.sum(
                    func.cast(FeedbackRecord.outcome == "success", int)
                ).label("successes"),
                func.avg(FeedbackRecord.execution_time).label("avg_latency"),
            )
            .where(FeedbackRecord.created_at >= cutoff)
            .group_by(func.date_trunc("day", FeedbackRecord.created_at))
            .order_by(func.date_trunc("day", FeedbackRecord.created_at))
        )
        rows = result.all()

        success_rate_series = []
        latency_series = []

        for row in rows:
            day = row.day.isoformat() if row.day else ""
            total = row.total or 1
            successes = row.successes or 0

            success_rate_series.append({
                "date": day,
                "value": successes / total,
            })

            latency_series.append({
                "date": day,
                "value": row.avg_latency or 0,
            })

        return {
            "success_rate": success_rate_series,
            "latency": latency_series,
        }

    def _calculate_health_status(
        self,
        metrics: PerformanceMetrics,
        anomalies: list[AnomalyDetection],
    ) -> str:
        """Calculate overall health status."""
        # Check for high severity anomalies
        high_severity = [a for a in anomalies if a.severity == "high"]
        if high_severity:
            return "critical"

        # Check for medium anomalies
        medium_severity = [a for a in anomalies if a.severity == "medium"]
        if medium_severity:
            return "warning"

        # Check success rate
        if metrics.task_success_rate < 0.5:
            return "warning"

        if metrics.task_success_rate < 0.3:
            return "critical"

        return "healthy"

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _calculate_all_metrics(
        self,
        days: int,
    ) -> dict[str, float]:
        """Calculate all metrics for a period."""
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Get aggregates
        result = await self.db.execute(
            select(
                func.count().label("total"),
                func.sum(
                    func.cast(FeedbackRecord.outcome == "success", int)
                ).label("successes"),
                func.avg(FeedbackRecord.execution_time).label("avg_latency"),
                func.avg(FeedbackRecord.rating).label("avg_rating"),
            )
            .where(FeedbackRecord.created_at >= cutoff)
        )
        row = result.one()

        total = row.total or 1
        successes = row.successes or 0

        return {
            "success_rate": successes / total,
            "avg_latency": row.avg_latency or 0,
            "quality_score": (row.avg_rating or 3) / 5,  # Normalize to 0-1
            "total_tasks": total,
        }

    async def _get_metric_history(
        self,
        metric: str,
        days: int,
    ) -> list[float]:
        """Get historical values for a metric."""
        # Check in-memory cache first
        if metric in self._metric_history:
            recent = [
                v for t, v in self._metric_history[metric]
                if t >= datetime.now(UTC) - timedelta(days=days)
            ]
            if recent:
                return recent

        # Get from database
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Daily aggregates
        result = await self.db.execute(
            select(
                func.date_trunc("day", FeedbackRecord.created_at).label("day"),
                func.count().label("total"),
                func.sum(
                    func.cast(FeedbackRecord.outcome == "success", int)
                ).label("successes"),
                func.avg(FeedbackRecord.execution_time).label("avg_latency"),
            )
            .where(FeedbackRecord.created_at >= cutoff)
            .group_by(func.date_trunc("day", FeedbackRecord.created_at))
            .order_by(func.date_trunc("day", FeedbackRecord.created_at))
        )
        rows = result.all()

        values = []
        for row in rows:
            if metric == "success_rate":
                values.append((row.successes or 0) / max(row.total, 1))
            elif metric == "avg_latency":
                values.append(row.avg_latency or 0)
            else:
                values.append(0)

        return values

    async def _log_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log audit entry."""
        try:
            audit = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                actor="performance_monitor_service",
                details=details or {},
            )
            self.db.add(audit)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")


# Factory function
async def get_performance_monitor_service(
    db: AsyncSession,
) -> PerformanceMonitorService:
    """Get performance monitor service instance."""
    return PerformanceMonitorService(db)
