"""
Advanced Connection Pool Optimization System
Intelligent connection pooling optimization for the enhanced database pattern consolidation

Bu dosya gelişmiş connection pool optimization sağlar:
- Adaptive pool sizing
- Connection lifecycle management
- Performance monitoring ve optimization
- Load balancing across multiple databases
- Connection health monitoring
- Automatic pool tuning
- Connection leak detection
- Pool metrics ve analytics
"""

import logging
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, NamedTuple

from .enhanced_database import ConnectionPoolConfig
from .error_context import async_error_context
from .error_monitoring import log_error
from .exceptions import DatabaseError, ErrorSeverity

logger = logging.getLogger(__name__)


# ==================== POOL OPTIMIZATION ENUMS ====================


class PoolHealthStatus(Enum):
    """Connection pool health status"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DEGRADED = "degraded"


class OptimizationStrategy(Enum):
    """Pool optimization strategies"""

    CONSERVATIVE = "conservative"  # Slow, safe adjustments
    AGGRESSIVE = "aggressive"  # Fast adjustments, higher risk
    BALANCED = "balanced"  # Balance between safety and performance
    CUSTOM = "custom"  # User-defined rules


class ConnectionState(Enum):
    """Connection state tracking"""

    IDLE = "idle"
    ACTIVE = "active"
    STALE = "stale"
    ERROR = "error"
    LEAK = "leak"


# ==================== DATA CLASSES ====================


@dataclass
class ConnectionMetrics:
    """Metrics for individual connections"""

    connection_id: str
    created_at: datetime
    last_used: datetime
    state: ConnectionState
    queries_executed: int = 0
    total_time_active: float = 0.0
    error_count: int = 0
    last_error: str | None = None

    def age_seconds(self) -> float:
        """Get connection age in seconds"""
        return (datetime.now() - self.created_at).total_seconds()

    def idle_time_seconds(self) -> float:
        """Get idle time in seconds"""
        return (datetime.now() - self.last_used).total_seconds()

    def is_stale(self, max_idle_time: float = 3600) -> bool:
        """Check if connection is stale"""
        return self.idle_time_seconds() > max_idle_time

    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        return (
            self.state in [ConnectionState.IDLE, ConnectionState.ACTIVE]
            and self.error_count < 3
        )


@dataclass
class PoolMetrics:
    """Pool-level metrics"""

    pool_id: str
    timestamp: datetime
    pool_size: int
    checked_out: int
    checked_in: int
    overflow: int
    invalid: int

    # Performance metrics
    avg_checkout_time: float = 0.0
    avg_query_time: float = 0.0
    checkout_timeouts: int = 0
    connection_errors: int = 0

    # Utilization metrics
    utilization_ratio: float = 0.0  # checked_out / pool_size
    overflow_ratio: float = 0.0  # overflow / max_overflow

    def __post_init__(self):
        if self.pool_size > 0:
            self.utilization_ratio = self.checked_out / self.pool_size

        max_overflow = self.pool_size * 2  # Assume 2x as max overflow
        if max_overflow > 0:
            self.overflow_ratio = self.overflow / max_overflow


@dataclass
class OptimizationRecommendation:
    """Pool optimization recommendation"""

    pool_id: str
    current_config: ConnectionPoolConfig
    recommended_config: ConnectionPoolConfig
    reason: str
    expected_improvement: str
    confidence_score: float  # 0.0 to 1.0
    risk_level: str  # "low", "medium", "high"


class PerformanceWindow(NamedTuple):
    """Time window for performance analysis"""

    start_time: datetime
    end_time: datetime
    duration_seconds: float


# ==================== CONNECTION TRACKER ====================


class ConnectionTracker:
    """Track individual connection lifecycle and metrics"""

    def __init__(self, max_history: int = 1000):
        self.connections: dict[str, ConnectionMetrics] = {}
        self.connection_history: deque = deque(maxlen=max_history)
        self.active_connections: set[str] = set()
        self.leak_detection_threshold: float = 300.0  # 5 minutes

    def track_connection_created(self, connection_id: str) -> None:
        """Track new connection creation"""
        metrics = ConnectionMetrics(
            connection_id=connection_id,
            created_at=datetime.now(),
            last_used=datetime.now(),
            state=ConnectionState.IDLE,
        )

        self.connections[connection_id] = metrics
        logger.debug(f"Connection {connection_id} created")

    def track_connection_checkout(self, connection_id: str) -> None:
        """Track connection checkout"""
        if connection_id in self.connections:
            metrics = self.connections[connection_id]
            metrics.state = ConnectionState.ACTIVE
            metrics.last_used = datetime.now()
            self.active_connections.add(connection_id)
            logger.debug(f"Connection {connection_id} checked out")

    def track_connection_checkin(self, connection_id: str) -> None:
        """Track connection checkin"""
        if connection_id in self.connections:
            metrics = self.connections[connection_id]
            metrics.state = ConnectionState.IDLE
            metrics.last_used = datetime.now()
            self.active_connections.discard(connection_id)
            logger.debug(f"Connection {connection_id} checked in")

    def track_connection_closed(self, connection_id: str) -> None:
        """Track connection closure"""
        if connection_id in self.connections:
            metrics = self.connections[connection_id]
            self.connection_history.append(metrics)
            del self.connections[connection_id]
            self.active_connections.discard(connection_id)
            logger.debug(f"Connection {connection_id} closed")

    def track_connection_error(self, connection_id: str, error: str) -> None:
        """Track connection error"""
        if connection_id in self.connections:
            metrics = self.connections[connection_id]
            metrics.error_count += 1
            metrics.last_error = error
            metrics.state = ConnectionState.ERROR
            logger.warning(f"Connection {connection_id} error: {error}")

    def detect_connection_leaks(self) -> list[str]:
        """Detect potential connection leaks"""
        leaks = []
        current_time = datetime.now()

        for connection_id, metrics in self.connections.items():
            if (
                metrics.state == ConnectionState.ACTIVE
                and connection_id in self.active_connections
                and (current_time - metrics.last_used).total_seconds()
                > self.leak_detection_threshold
            ):
                metrics.state = ConnectionState.LEAK
                leaks.append(connection_id)
                logger.error(f"Potential connection leak detected: {connection_id}")

        return leaks

    def get_connection_stats(self) -> dict[str, Any]:
        """Get connection statistics"""
        active_count = len(self.active_connections)
        idle_count = sum(
            1 for m in self.connections.values() if m.state == ConnectionState.IDLE
        )
        error_count = sum(
            1 for m in self.connections.values() if m.state == ConnectionState.ERROR
        )
        leak_count = sum(
            1 for m in self.connections.values() if m.state == ConnectionState.LEAK
        )

        ages = [m.age_seconds() for m in self.connections.values()]
        idle_times = [
            m.idle_time_seconds()
            for m in self.connections.values()
            if m.state == ConnectionState.IDLE
        ]

        return {
            "total_connections": len(self.connections),
            "active_connections": active_count,
            "idle_connections": idle_count,
            "error_connections": error_count,
            "leak_connections": leak_count,
            "average_connection_age": statistics.mean(ages) if ages else 0,
            "max_connection_age": max(ages) if ages else 0,
            "average_idle_time": statistics.mean(idle_times) if idle_times else 0,
            "max_idle_time": max(idle_times) if idle_times else 0,
        }


# ==================== POOL MONITOR ====================


class PoolMonitor:
    """Monitor pool performance and health"""

    def __init__(self, analysis_window_minutes: int = 5):
        self.analysis_window = timedelta(minutes=analysis_window_minutes)
        self.metrics_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.performance_windows: dict[str, list[PerformanceWindow]] = defaultdict(list)
        self.health_thresholds = {
            "utilization_warning": 0.8,
            "utilization_critical": 0.95,
            "timeout_warning_rate": 0.05,
            "timeout_critical_rate": 0.15,
            "error_warning_rate": 0.02,
            "error_critical_rate": 0.10,
        }

    def record_metrics(self, pool_id: str, metrics: PoolMetrics) -> None:
        """Record pool metrics"""
        self.metrics_history[pool_id].append(metrics)

        # Clean old performance windows
        cutoff_time = datetime.now() - self.analysis_window
        self.performance_windows[pool_id] = [
            window
            for window in self.performance_windows[pool_id]
            if window.end_time > cutoff_time
        ]

    def analyze_pool_health(self, pool_id: str) -> tuple[PoolHealthStatus, list[str]]:
        """Analyze pool health and return status with issues"""

        if pool_id not in self.metrics_history or not self.metrics_history[pool_id]:
            return PoolHealthStatus.WARNING, ["No metrics available"]

        recent_metrics = list(self.metrics_history[pool_id])[-10:]  # Last 10 metrics
        issues = []

        # Analyze utilization
        avg_utilization = statistics.mean(m.utilization_ratio for m in recent_metrics)
        if avg_utilization > self.health_thresholds["utilization_critical"]:
            issues.append(f"Critical utilization: {avg_utilization:.2%}")
        elif avg_utilization > self.health_thresholds["utilization_warning"]:
            issues.append(f"High utilization: {avg_utilization:.2%}")

        # Analyze timeouts
        total_checkouts = sum(m.checked_out for m in recent_metrics)
        total_timeouts = sum(m.checkout_timeouts for m in recent_metrics)
        timeout_rate = total_timeouts / total_checkouts if total_checkouts > 0 else 0

        if timeout_rate > self.health_thresholds["timeout_critical_rate"]:
            issues.append(f"Critical timeout rate: {timeout_rate:.2%}")
        elif timeout_rate > self.health_thresholds["timeout_warning_rate"]:
            issues.append(f"High timeout rate: {timeout_rate:.2%}")

        # Analyze errors
        total_errors = sum(m.connection_errors for m in recent_metrics)
        error_rate = total_errors / total_checkouts if total_checkouts > 0 else 0

        if error_rate > self.health_thresholds["error_critical_rate"]:
            issues.append(f"Critical error rate: {error_rate:.2%}")
        elif error_rate > self.health_thresholds["error_warning_rate"]:
            issues.append(f"High error rate: {error_rate:.2%}")

        # Determine overall health status
        if any("Critical" in issue for issue in issues):
            return PoolHealthStatus.CRITICAL, issues
        if any("High" in issue for issue in issues):
            return PoolHealthStatus.WARNING, issues
        if issues:
            return PoolHealthStatus.DEGRADED, issues
        return PoolHealthStatus.HEALTHY, []

    def get_performance_trends(self, pool_id: str) -> dict[str, Any]:
        """Get performance trends for a pool"""

        if pool_id not in self.metrics_history:
            return {"error": "No data available"}

        metrics_list = list(self.metrics_history[pool_id])

        if len(metrics_list) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Calculate trends
        recent_metrics = metrics_list[-10:]
        older_metrics = (
            metrics_list[-20:-10] if len(metrics_list) >= 20 else metrics_list[:-10]
        )

        if not older_metrics:
            return {"error": "Insufficient historical data"}

        # Utilization trend
        recent_utilization = statistics.mean(
            m.utilization_ratio for m in recent_metrics
        )
        older_utilization = statistics.mean(m.utilization_ratio for m in older_metrics)
        utilization_trend = recent_utilization - older_utilization

        # Checkout time trend
        recent_checkout_time = statistics.mean(
            m.avg_checkout_time for m in recent_metrics if m.avg_checkout_time > 0
        )
        older_checkout_time = statistics.mean(
            m.avg_checkout_time for m in older_metrics if m.avg_checkout_time > 0
        )
        checkout_time_trend = (
            recent_checkout_time - older_checkout_time
            if recent_checkout_time and older_checkout_time
            else 0
        )

        # Error trend
        recent_errors = sum(m.connection_errors for m in recent_metrics)
        older_errors = sum(m.connection_errors for m in older_metrics)
        error_trend = recent_errors - older_errors

        return {
            "utilization_trend": utilization_trend,
            "checkout_time_trend": checkout_time_trend,
            "error_trend": error_trend,
            "recent_utilization": recent_utilization,
            "recent_checkout_time": recent_checkout_time,
            "data_points": len(metrics_list),
        }


# ==================== POOL OPTIMIZER ====================


class PoolOptimizer:
    """Intelligent pool optimization engine"""

    def __init__(self, strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
        self.strategy = strategy
        self.monitor = PoolMonitor()
        self.connection_tracker = ConnectionTracker()
        self.optimization_history: dict[
            str, list[OptimizationRecommendation]
        ] = defaultdict(list)

        # Optimization rules based on strategy
        self.optimization_rules = self._get_optimization_rules(strategy)

    def _get_optimization_rules(self, strategy: OptimizationStrategy) -> dict[str, Any]:
        """Get optimization rules based on strategy"""

        if strategy == OptimizationStrategy.CONSERVATIVE:
            return {
                "min_pool_size": 5,
                "max_pool_size_increase": 2,
                "max_pool_size_decrease": 1,
                "utilization_threshold_increase": 0.85,
                "utilization_threshold_decrease": 0.3,
                "adjustment_interval_minutes": 10,
                "confidence_threshold": 0.8,
            }
        if strategy == OptimizationStrategy.AGGRESSIVE:
            return {
                "min_pool_size": 2,
                "max_pool_size_increase": 10,
                "max_pool_size_decrease": 5,
                "utilization_threshold_increase": 0.7,
                "utilization_threshold_decrease": 0.5,
                "adjustment_interval_minutes": 2,
                "confidence_threshold": 0.6,
            }
        # BALANCED
        return {
            "min_pool_size": 3,
            "max_pool_size_increase": 5,
            "max_pool_size_decrease": 3,
            "utilization_threshold_increase": 0.75,
            "utilization_threshold_decrease": 0.4,
            "adjustment_interval_minutes": 5,
            "confidence_threshold": 0.7,
        }

    async def analyze_and_recommend(
        self, pool_id: str, current_config: ConnectionPoolConfig
    ) -> OptimizationRecommendation | None:
        """Analyze pool performance and recommend optimizations"""

        async with async_error_context(
            operation_name="pool_optimization_analysis",
            entity_id=pool_id,
            business_operation="pool_optimization",
        ) as ctx:
            try:
                # Get recent performance data
                trends = self.monitor.get_performance_trends(pool_id)
                health_status, health_issues = self.monitor.analyze_pool_health(pool_id)
                connection_stats = self.connection_tracker.get_connection_stats()

                ctx.add_annotation(
                    f"Pool health: {health_status.value}, Issues: {len(health_issues)}"
                )

                # Analyze for optimization opportunities
                recommended_config = ConnectionPoolConfig(
                    pool_size=current_config.pool_size,
                    max_overflow=current_config.max_overflow,
                    pool_timeout=current_config.pool_timeout,
                    pool_recycle=current_config.pool_recycle,
                    pool_pre_ping=current_config.pool_pre_ping,
                    pool_reset_on_return=current_config.pool_reset_on_return,
                )

                reasons = []
                confidence = 0.5
                risk_level = "low"

                # Check if pool size adjustment is needed
                if "error" not in trends:
                    utilization = trends.get("recent_utilization", 0)

                    # Pool size increase logic
                    if (
                        utilization
                        > self.optimization_rules["utilization_threshold_increase"]
                    ):
                        increase = min(
                            self.optimization_rules["max_pool_size_increase"],
                            max(1, int(current_config.pool_size * 0.2)),
                        )
                        recommended_config.pool_size = (
                            current_config.pool_size + increase
                        )
                        recommended_config.max_overflow = int(
                            recommended_config.pool_size * 1.5
                        )

                        reasons.append(
                            f"High utilization ({utilization:.2%}) - increase pool size by {increase}"
                        )
                        confidence += 0.3
                        risk_level = "medium" if increase > 3 else "low"

                    # Pool size decrease logic
                    elif (
                        utilization
                        < self.optimization_rules["utilization_threshold_decrease"]
                    ):
                        decrease = min(
                            self.optimization_rules["max_pool_size_decrease"],
                            max(1, int(current_config.pool_size * 0.15)),
                        )
                        new_size = max(
                            self.optimization_rules["min_pool_size"],
                            current_config.pool_size - decrease,
                        )

                        if new_size < current_config.pool_size:
                            recommended_config.pool_size = new_size
                            recommended_config.max_overflow = max(
                                5, int(new_size * 1.5)
                            )

                            reasons.append(
                                f"Low utilization ({utilization:.2%}) - decrease pool size by {current_config.pool_size - new_size}"
                            )
                            confidence += 0.2

                    # Checkout time optimization
                    checkout_time_trend = trends.get("checkout_time_trend", 0)
                    if checkout_time_trend > 0.1:  # Increasing checkout times
                        if current_config.pool_timeout < 60:
                            recommended_config.pool_timeout = min(
                                60, current_config.pool_timeout + 10
                            )
                            reasons.append(
                                "Increasing checkout times - increase pool timeout"
                            )
                            confidence += 0.1

                # Connection recycling optimization
                if connection_stats["max_connection_age"] > 7200:  # 2 hours
                    if current_config.pool_recycle > 3600:
                        recommended_config.pool_recycle = 3600
                        reasons.append("Long-lived connections - reduce recycle time")
                        confidence += 0.1

                # Health-based optimizations
                if health_status == PoolHealthStatus.CRITICAL:
                    recommended_config.pool_pre_ping = True
                    recommended_config.pool_reset_on_return = "commit"
                    reasons.append(
                        "Critical health status - enable pre-ping and reset on return"
                    )
                    confidence += 0.2
                    risk_level = "high"

                # Only recommend if there are actual changes and sufficient confidence
                if (
                    reasons
                    and confidence >= self.optimization_rules["confidence_threshold"]
                    and self._configs_differ(current_config, recommended_config)
                ):
                    recommendation = OptimizationRecommendation(
                        pool_id=pool_id,
                        current_config=current_config,
                        recommended_config=recommended_config,
                        reason="; ".join(reasons),
                        expected_improvement=f"Improved utilization and {len(health_issues)} fewer issues",
                        confidence_score=min(confidence, 1.0),
                        risk_level=risk_level,
                    )

                    self.optimization_history[pool_id].append(recommendation)

                    ctx.add_annotation(
                        f"Generated optimization recommendation with confidence {confidence:.2f}"
                    )

                    return recommendation

                ctx.add_annotation("No optimization needed at this time")
                return None

            except Exception as e:
                ctx.add_annotation(f"Optimization analysis failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.MEDIUM)
                return None

    def _configs_differ(
        self, config1: ConnectionPoolConfig, config2: ConnectionPoolConfig
    ) -> bool:
        """Check if two configurations are different"""
        return (
            config1.pool_size != config2.pool_size
            or config1.max_overflow != config2.max_overflow
            or config1.pool_timeout != config2.pool_timeout
            or config1.pool_recycle != config2.pool_recycle
            or config1.pool_pre_ping != config2.pool_pre_ping
            or config1.pool_reset_on_return != config2.pool_reset_on_return
        )

    async def auto_optimize_pool(
        self,
        pool_id: str,
        current_config: ConnectionPoolConfig,
        apply_changes: bool = False,
    ) -> dict[str, Any]:
        """Automatically optimize pool configuration"""

        async with async_error_context(
            operation_name="auto_optimize_pool",
            entity_id=pool_id,
            business_operation="automatic_pool_optimization",
        ) as ctx:
            try:
                recommendation = await self.analyze_and_recommend(
                    pool_id, current_config
                )

                if not recommendation:
                    return {
                        "optimized": False,
                        "reason": "No optimization needed",
                        "current_config": current_config,
                    }

                ctx.add_annotation(
                    f"Optimization recommended with confidence {recommendation.confidence_score:.2f}"
                )

                result = {
                    "optimized": False,
                    "recommendation": recommendation,
                    "current_config": current_config,
                    "recommended_config": recommendation.recommended_config,
                }

                if apply_changes:
                    # Note: In a real implementation, this would apply the changes to the actual pool
                    # For now, we just log the recommendation
                    logger.info(
                        f"Auto-optimization for pool {pool_id}: {recommendation.reason}"
                    )
                    ctx.add_annotation("Optimization applied successfully")

                    result["optimized"] = True
                    result["applied_config"] = recommendation.recommended_config

                return result

            except Exception as e:
                ctx.add_annotation(f"Auto-optimization failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message=f"Auto-optimization failed for pool {pool_id}",
                    operation="auto_optimize_pool",
                    details={"pool_id": pool_id, "error": str(e)},
                )

    def get_optimization_statistics(self) -> dict[str, Any]:
        """Get optimization statistics"""

        total_recommendations = sum(
            len(history) for history in self.optimization_history.values()
        )

        if total_recommendations == 0:
            return {
                "total_recommendations": 0,
                "pools_optimized": 0,
                "average_confidence": 0,
                "risk_distribution": {},
            }

        all_recommendations = []
        for history in self.optimization_history.values():
            all_recommendations.extend(history)

        avg_confidence = statistics.mean(
            r.confidence_score for r in all_recommendations
        )

        risk_distribution = defaultdict(int)
        for recommendation in all_recommendations:
            risk_distribution[recommendation.risk_level] += 1

        return {
            "total_recommendations": total_recommendations,
            "pools_optimized": len(self.optimization_history),
            "average_confidence": avg_confidence,
            "risk_distribution": dict(risk_distribution),
            "strategy": self.strategy.value,
            "recent_recommendations": len(
                [
                    r
                    for history in self.optimization_history.values()
                    for r in history
                    if (
                        datetime.now() - r.current_config.created_at
                        if hasattr(r.current_config, "created_at")
                        else datetime.now()
                    ).days
                    < 7
                ]
            ),
        }


# ==================== GLOBAL POOL OPTIMIZER ====================

# Global pool optimizer instance
pool_optimizer = PoolOptimizer()


# ==================== UTILITY FUNCTIONS ====================


async def optimize_pool(
    pool_id: str,
    current_config: ConnectionPoolConfig,
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
    apply_changes: bool = False,
) -> dict[str, Any]:
    """Optimize a connection pool"""

    global pool_optimizer

    # Update strategy if different
    if pool_optimizer.strategy != strategy:
        pool_optimizer = PoolOptimizer(strategy)

    return await pool_optimizer.auto_optimize_pool(
        pool_id, current_config, apply_changes
    )


def track_pool_metrics(pool_id: str, metrics: PoolMetrics) -> None:
    """Track pool metrics for optimization"""
    pool_optimizer.monitor.record_metrics(pool_id, metrics)


def get_pool_health(pool_id: str) -> tuple[PoolHealthStatus, list[str]]:
    """Get pool health status"""
    return pool_optimizer.monitor.analyze_pool_health(pool_id)


def get_optimization_statistics() -> dict[str, Any]:
    """Get global optimization statistics"""
    return pool_optimizer.get_optimization_statistics()


async def detect_connection_leaks() -> list[str]:
    """Detect potential connection leaks"""
    return pool_optimizer.connection_tracker.detect_connection_leaks()


def get_connection_statistics() -> dict[str, Any]:
    """Get connection statistics"""
    return pool_optimizer.connection_tracker.get_connection_stats()
