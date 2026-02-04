"""
KIRO2 Real-time Exam Metrics and Monitoring System
Comprehensive real-time monitoring and alerting system for exams
Türkiye Üniversite Sınavları Hazırlık Platformu - Gerçek Zamanlı Sınav İzleme Sistemi
"""

import asyncio
import json
import statistics
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
import websockets
from analytics.unified_analytics_data_model import (
    AnalyticsEvent,
    AnalyticsEventType,
    TurkishExamType,
    TurkishSubject,
)
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.ANALYTICS)
config = get_unified_config()


class MonitoringLevel(Enum):
    """Monitoring alert levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MetricType(Enum):
    """Types of metrics being monitored"""

    EXAM_PARTICIPATION = "exam_participation"
    PERFORMANCE_ANOMALY = "performance_anomaly"
    SYSTEM_PERFORMANCE = "system_performance"
    CHEATING_DETECTION = "cheating_detection"
    TECHNICAL_ISSUES = "technical_issues"
    ENGAGEMENT_METRICS = "engagement_metrics"


class AlertType(Enum):
    """Types of alerts"""

    HIGH_FAILURE_RATE = "high_failure_rate"
    UNUSUAL_PERFORMANCE_PATTERN = "unusual_performance_pattern"
    SUSPECTED_CHEATING = "suspected_cheating"
    TECHNICAL_MALFUNCTION = "technical_malfunction"
    LOW_PARTICIPATION = "low_participation"
    SYSTEM_OVERLOAD = "system_overload"
    NETWORK_ISSUES = "network_issues"


@dataclass
class RealTimeMetric:
    """Individual real-time metric"""

    metric_id: str
    metric_type: MetricType
    timestamp: datetime
    value: Union[int, float, str, Dict[str, Any]]

    # Context information
    exam_id: Optional[str] = None
    student_id: Optional[int] = None
    subject: Optional[TurkishSubject] = None
    session_id: Optional[str] = None

    # Metadata
    source: str = "system"
    tags: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.metric_id:
            self.metric_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metric_id": self.metric_id,
            "metric_type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "exam_id": self.exam_id,
            "student_id": self.student_id,
            "subject": self.subject.value if self.subject else None,
            "session_id": self.session_id,
            "source": self.source,
            "tags": self.tags,
        }


@dataclass
class Alert:
    """System alert for anomalies or important events"""

    alert_id: str
    alert_type: AlertType
    level: MonitoringLevel
    timestamp: datetime

    # Alert content
    title: str
    message: str
    title_tr: str = ""
    message_tr: str = ""

    # Context
    exam_id: Optional[str] = None
    student_ids: List[int] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)

    # Alert lifecycle
    acknowledged: bool = False
    resolved: bool = False
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Actions
    suggested_actions: List[str] = field(default_factory=list)
    automated_actions_taken: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.alert_id:
            self.alert_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc)

    def acknowledge(self, user: str) -> None:
        """Acknowledge the alert"""
        self.acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = datetime.now(timezone.utc)

    def resolve(self, user: str) -> None:
        """Resolve the alert"""
        self.resolved = True
        self.resolved_by = user
        self.resolved_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "level": self.level.value,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "message": self.message,
            "title_tr": self.title_tr,
            "message_tr": self.message_tr,
            "exam_id": self.exam_id,
            "student_ids": self.student_ids,
            "affected_systems": self.affected_systems,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "acknowledged_by": self.acknowledged_by,
            "resolved_by": self.resolved_by,
            "suggested_actions": self.suggested_actions,
            "automated_actions_taken": self.automated_actions_taken,
        }


@dataclass
class ExamSession:
    """Live exam session being monitored"""

    session_id: str
    exam_id: str
    exam_type: TurkishExamType

    # Session info
    start_time: datetime
    scheduled_end_time: datetime
    actual_end_time: Optional[datetime] = None

    # Participants
    registered_students: List[int] = field(default_factory=list)
    active_students: List[int] = field(default_factory=list)
    completed_students: List[int] = field(default_factory=list)
    dropped_students: List[int] = field(default_factory=list)

    # Real-time statistics
    current_participation_rate: float = 0.0
    average_completion_rate: float = 0.0
    average_score: float = 0.0
    question_difficulty_stats: Dict[str, Any] = field(default_factory=dict)

    # Technical metrics
    server_response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_counts: Dict[str, int] = field(default_factory=dict)
    bandwidth_usage: Dict[str, float] = field(default_factory=dict)

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate current session metrics"""
        total_registered = len(self.registered_students)
        currently_active = len(self.active_students)
        completed = len(self.completed_students)
        dropped = len(self.dropped_students)

        return {
            "total_registered": total_registered,
            "currently_active": currently_active,
            "completed": completed,
            "dropped": dropped,
            "participation_rate": (currently_active / total_registered * 100)
            if total_registered > 0
            else 0,
            "completion_rate": (completed / total_registered * 100)
            if total_registered > 0
            else 0,
            "drop_rate": (dropped / total_registered * 100)
            if total_registered > 0
            else 0,
            "average_response_time": statistics.mean(self.server_response_times)
            if self.server_response_times
            else 0,
            "error_rate": sum(self.error_counts.values())
            / max(1, currently_active)
            * 100,
        }


class RealTimeMetricsCollector:
    """Collects and processes real-time metrics"""

    def __init__(self):
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.redis_client = None
        self.collection_interval = config.get_setting(
            "analytics.metrics_collection_interval", 5
        )

    async def initialize(self) -> None:
        """Initialize Redis connection"""
        try:
            redis_url = config.get_setting("redis.url", "redis://localhost:6379")
            self.redis_client = aioredis.from_url(redis_url)
            logger.info("Real-time metrics collector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")

    async def collect_metric(self, metric: RealTimeMetric) -> None:
        """Collect a single metric"""
        self.metrics_buffer.append(metric)

        # Store in Redis for real-time access
        if self.redis_client:
            await self.redis_client.lpush(
                f"metrics:{metric.metric_type.value}", json.dumps(metric.to_dict())
            )
            # Keep only last 1000 metrics per type
            await self.redis_client.ltrim(f"metrics:{metric.metric_type.value}", 0, 999)

    async def collect_exam_event(self, event: AnalyticsEvent) -> None:
        """Collect exam-related events and convert to metrics"""
        metric_value = {
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "event_data": event.event_data,
        }

        # Determine metric type based on event
        if event.event_type in [
            AnalyticsEventType.EXAM_START,
            AnalyticsEventType.EXAM_COMPLETE,
        ]:
            metric_type = MetricType.EXAM_PARTICIPATION
        elif event.event_type in [
            AnalyticsEventType.QUESTION_ANSWER,
            AnalyticsEventType.SCORE_ACHIEVEMENT,
        ]:
            metric_type = MetricType.PERFORMANCE_ANOMALY
        else:
            metric_type = MetricType.ENGAGEMENT_METRICS

        metric = RealTimeMetric(
            metric_type=metric_type,
            timestamp=event.timestamp,
            value=metric_value,
            exam_id=event.exam_context.get("exam_id") if event.exam_context else None,
            student_id=event.user_id,
            subject=event.subject,
            session_id=event.session_id,
            source="exam_system",
        )

        await self.collect_metric(metric)

    async def get_recent_metrics(
        self,
        metric_type: MetricType,
        limit: int = 100,
        time_window: timedelta = timedelta(minutes=10),
    ) -> List[RealTimeMetric]:
        """Get recent metrics of specific type"""
        if not self.redis_client:
            return []

        try:
            metric_data = await self.redis_client.lrange(
                f"metrics:{metric_type.value}", 0, limit - 1
            )

            metrics = []
            cutoff_time = datetime.now(timezone.utc) - time_window

            for data in metric_data:
                metric_dict = json.loads(data)
                metric_time = datetime.fromisoformat(
                    metric_dict["timestamp"].replace("Z", "+00:00")
                )

                if metric_time >= cutoff_time:
                    # Reconstruct metric object
                    metric = RealTimeMetric(
                        metric_id=metric_dict["metric_id"],
                        metric_type=MetricType(metric_dict["metric_type"]),
                        timestamp=metric_time,
                        value=metric_dict["value"],
                        exam_id=metric_dict.get("exam_id"),
                        student_id=metric_dict.get("student_id"),
                        session_id=metric_dict.get("session_id"),
                        source=metric_dict["source"],
                        tags=metric_dict["tags"],
                    )
                    metrics.append(metric)

            return metrics
        except Exception as e:
            logger.error(f"Failed to get recent metrics: {e}")
            return []


class AnomalyDetector:
    """Detects anomalies in real-time exam data"""

    def __init__(self):
        self.baseline_stats = {}
        self.detection_rules = self._initialize_detection_rules()

    def _initialize_detection_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize anomaly detection rules"""
        return {
            "high_error_rate": {
                "threshold": 10.0,  # 10% error rate
                "window_minutes": 5,
                "severity": MonitoringLevel.WARNING,
            },
            "low_participation": {
                "threshold": 70.0,  # Below 70% participation
                "window_minutes": 10,
                "severity": MonitoringLevel.WARNING,
            },
            "unusual_score_distribution": {
                "std_dev_threshold": 3.0,  # 3 standard deviations
                "window_minutes": 15,
                "severity": MonitoringLevel.INFO,
            },
            "rapid_dropouts": {
                "threshold": 20.0,  # 20% dropout rate in short time
                "window_minutes": 5,
                "severity": MonitoringLevel.CRITICAL,
            },
            "suspected_cheating_pattern": {
                "similarity_threshold": 0.95,  # 95% similarity in answers
                "time_threshold": 30,  # 30 seconds difference
                "severity": MonitoringLevel.CRITICAL,
            },
            "system_overload": {
                "response_time_threshold": 5000,  # 5 second response time
                "cpu_threshold": 90.0,  # 90% CPU usage
                "memory_threshold": 90.0,  # 90% memory usage
                "severity": MonitoringLevel.EMERGENCY,
            },
        }

    async def detect_anomalies(
        self, session: ExamSession, recent_metrics: List[RealTimeMetric]
    ) -> List[Alert]:
        """Detect anomalies in exam session"""
        alerts = []
        session_metrics = session.calculate_metrics()

        # Check error rate
        if (
            session_metrics["error_rate"]
            > self.detection_rules["high_error_rate"]["threshold"]
        ):
            alert = Alert(
                alert_type=AlertType.TECHNICAL_MALFUNCTION,
                level=self.detection_rules["high_error_rate"]["severity"],
                title="High Error Rate Detected",
                message=f"Error rate is {session_metrics['error_rate']:.1f}% in exam {session.exam_id}",
                title_tr="Yüksek Hata Oranı Tespit Edildi",
                message_tr=f"Sınav {session.exam_id}'de hata oranı %{session_metrics['error_rate']:.1f}",
                exam_id=session.exam_id,
                suggested_actions=[
                    "Check server health",
                    "Review recent deployments",
                    "Monitor network connectivity",
                ],
            )
            alerts.append(alert)

        # Check participation rate
        if (
            session_metrics["participation_rate"]
            < self.detection_rules["low_participation"]["threshold"]
        ):
            alert = Alert(
                alert_type=AlertType.LOW_PARTICIPATION,
                level=self.detection_rules["low_participation"]["severity"],
                title="Low Participation Rate",
                message=f"Only {session_metrics['participation_rate']:.1f}% participation in exam {session.exam_id}",
                title_tr="Düşük Katılım Oranı",
                message_tr=f"Sınav {session.exam_id}'de sadece %{session_metrics['participation_rate']:.1f} katılım",
                exam_id=session.exam_id,
                suggested_actions=[
                    "Check exam notifications",
                    "Verify system accessibility",
                    "Contact students with technical issues",
                ],
            )
            alerts.append(alert)

        # Check for rapid dropouts
        if (
            session_metrics["drop_rate"]
            > self.detection_rules["rapid_dropouts"]["threshold"]
        ):
            alert = Alert(
                alert_type=AlertType.TECHNICAL_MALFUNCTION,
                level=self.detection_rules["rapid_dropouts"]["severity"],
                title="High Dropout Rate",
                message=f"Dropout rate is {session_metrics['drop_rate']:.1f}% in exam {session.exam_id}",
                title_tr="Yüksek Bırakma Oranı",
                message_tr=f"Sınav {session.exam_id}'de bırakma oranı %{session_metrics['drop_rate']:.1f}",
                exam_id=session.exam_id,
                student_ids=session.dropped_students,
                suggested_actions=[
                    "Investigate technical issues",
                    "Contact affected students",
                    "Consider exam extension",
                ],
            )
            alerts.append(alert)

        # Detect cheating patterns
        cheating_alerts = await self._detect_cheating_patterns(session, recent_metrics)
        alerts.extend(cheating_alerts)

        # Detect system performance issues
        performance_alerts = await self._detect_performance_issues(session_metrics)
        alerts.extend(performance_alerts)

        return alerts

    async def _detect_cheating_patterns(
        self, session: ExamSession, recent_metrics: List[RealTimeMetric]
    ) -> List[Alert]:
        """Detect potential cheating patterns"""
        alerts = []

        # Group answer events by question and time
        answer_events = defaultdict(list)
        for metric in recent_metrics:
            if (
                metric.metric_type == MetricType.PERFORMANCE_ANOMALY
                and isinstance(metric.value, dict)
                and metric.value.get("event_type") == "question_answer"
            ):
                question_id = metric.value.get("event_data", {}).get("question_id")
                if question_id:
                    answer_events[question_id].append(metric)

        # Check for suspicious answer patterns
        for question_id, events in answer_events.items():
            if len(events) < 5:  # Need at least 5 responses to analyze
                continue

            # Group by answer and check timing
            answers_by_choice = defaultdict(list)
            for event in events:
                answer = event.value.get("event_data", {}).get("selected_answer")
                if answer:
                    answers_by_choice[answer].append(event)

            # Check for identical answers with suspicious timing
            for answer, answer_events_list in answers_by_choice.items():
                if len(answer_events_list) >= 3:  # 3 or more identical answers
                    timestamps = [e.timestamp for e in answer_events_list]
                    time_diffs = [
                        abs((timestamps[i] - timestamps[i - 1]).total_seconds())
                        for i in range(1, len(timestamps))
                    ]

                    # If most answers came within 30 seconds of each other
                    suspicious_count = sum(1 for diff in time_diffs if diff < 30)
                    if (
                        suspicious_count >= len(time_diffs) * 0.7
                    ):  # 70% within 30 seconds
                        suspected_students = [e.student_id for e in answer_events_list]

                        alert = Alert(
                            alert_type=AlertType.SUSPECTED_CHEATING,
                            level=MonitoringLevel.CRITICAL,
                            title="Suspicious Answer Pattern Detected",
                            message=f"Similar answers submitted within short time frame for question {question_id}",
                            title_tr="Şüpheli Cevap Kalıbı Tespit Edildi",
                            message_tr=f"Soru {question_id} için kısa süre içinde benzer cevaplar gönderildi",
                            exam_id=session.exam_id,
                            student_ids=suspected_students,
                            suggested_actions=[
                                "Review student submissions manually",
                                "Check for communication between students",
                                "Consider flagging for detailed investigation",
                            ],
                        )
                        alerts.append(alert)

        return alerts

    async def _detect_performance_issues(
        self, session_metrics: Dict[str, Any]
    ) -> List[Alert]:
        """Detect system performance issues"""
        alerts = []

        # Check response time
        if (
            session_metrics["average_response_time"]
            > self.detection_rules["system_overload"]["response_time_threshold"]
        ):
            alert = Alert(
                alert_type=AlertType.SYSTEM_OVERLOAD,
                level=MonitoringLevel.EMERGENCY,
                title="System Response Time Critical",
                message=f"Average response time is {session_metrics['average_response_time']:.0f}ms",
                title_tr="Sistem Yanıt Süresi Kritik",
                message_tr=f"Ortalama yanıt süresi {session_metrics['average_response_time']:.0f}ms",
                suggested_actions=[
                    "Scale up server resources",
                    "Check database performance",
                    "Review system load balancing",
                ],
                automated_actions_taken=[
                    "Auto-scaling initiated",
                    "Load balancer notified",
                ],
            )
            alerts.append(alert)

        return alerts


class RealTimeMonitoringDashboard:
    """Real-time monitoring dashboard for exam sessions"""

    def __init__(self):
        self.active_sessions: Dict[str, ExamSession] = {}
        self.metrics_collector = RealTimeMetricsCollector()
        self.anomaly_detector = AnomalyDetector()
        self.active_alerts: Dict[str, Alert] = {}
        self.websocket_connections: List = []

        # Monitoring configuration
        self.monitoring_interval = config.get_setting("monitoring.interval_seconds", 10)
        self.alert_retention_hours = config.get_setting(
            "monitoring.alert_retention_hours", 24
        )

    async def initialize(self) -> None:
        """Initialize monitoring system"""
        await self.metrics_collector.initialize()
        logger.info("Real-time monitoring dashboard initialized")

    async def register_exam_session(self, session: ExamSession) -> None:
        """Register a new exam session for monitoring"""
        self.active_sessions[session.session_id] = session
        logger.info(f"Registered exam session {session.session_id} for monitoring")

        # Broadcast session start to connected clients
        await self._broadcast_update(
            {
                "type": "session_started",
                "session": {
                    "session_id": session.session_id,
                    "exam_id": session.exam_id,
                    "exam_type": session.exam_type.value,
                    "start_time": session.start_time.isoformat(),
                    "registered_students": len(session.registered_students),
                },
            }
        )

    async def update_session_participant(
        self,
        session_id: str,
        student_id: int,
        action: str,  # "join", "leave", "complete"
    ) -> None:
        """Update session participant status"""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]

        if action == "join":
            if student_id not in session.active_students:
                session.active_students.append(student_id)
        elif action == "leave":
            if student_id in session.active_students:
                session.active_students.remove(student_id)
            if student_id not in session.dropped_students:
                session.dropped_students.append(student_id)
        elif action == "complete":
            if student_id in session.active_students:
                session.active_students.remove(student_id)
            if student_id not in session.completed_students:
                session.completed_students.append(student_id)

        # Broadcast update
        await self._broadcast_session_update(session_id)

    async def start_monitoring_loop(self) -> None:
        """Start the main monitoring loop"""
        logger.info("Starting real-time monitoring loop")

        while True:
            try:
                await self._monitoring_cycle()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _monitoring_cycle(self) -> None:
        """Single monitoring cycle"""
        for session_id, session in self.active_sessions.copy().items():
            # Check if session is still active
            if session.actual_end_time and datetime.now(
                timezone.utc
            ) - session.actual_end_time > timedelta(hours=1):
                # Remove old completed sessions
                del self.active_sessions[session_id]
                continue

            # Get recent metrics for this session
            recent_metrics = await self.metrics_collector.get_recent_metrics(
                MetricType.EXAM_PARTICIPATION, time_window=timedelta(minutes=15)
            )

            # Filter metrics for this session
            session_metrics = [m for m in recent_metrics if m.session_id == session_id]

            # Detect anomalies
            new_alerts = await self.anomaly_detector.detect_anomalies(
                session, session_metrics
            )

            # Process new alerts
            for alert in new_alerts:
                await self._process_alert(alert)

            # Broadcast session update
            await self._broadcast_session_update(session_id)

        # Clean up old alerts
        await self._cleanup_old_alerts()

    async def _process_alert(self, alert: Alert) -> None:
        """Process a new alert"""
        self.active_alerts[alert.alert_id] = alert

        # Log alert
        log_level = {
            MonitoringLevel.INFO: logger.info,
            MonitoringLevel.WARNING: logger.warning,
            MonitoringLevel.CRITICAL: logger.error,
            MonitoringLevel.EMERGENCY: logger.critical,
        }.get(alert.level, logger.info)

        log_level(f"Alert: {alert.title} - {alert.message}")

        # Execute automated actions if any
        for action in alert.automated_actions_taken:
            logger.info(f"Automated action taken: {action}")

        # Broadcast alert to connected clients
        await self._broadcast_update({"type": "alert", "alert": alert.to_dict()})

    async def _broadcast_session_update(self, session_id: str) -> None:
        """Broadcast session update to connected clients"""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        metrics = session.calculate_metrics()

        await self._broadcast_update(
            {
                "type": "session_update",
                "session_id": session_id,
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _broadcast_update(self, data: Dict[str, Any]) -> None:
        """Broadcast update to all connected WebSocket clients"""
        if not self.websocket_connections:
            return

        message = json.dumps(data)
        disconnected = []

        for websocket in self.websocket_connections:
            try:
                await websocket.send(message)
            except websockets.ConnectionClosed:
                disconnected.append(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)

    async def _cleanup_old_alerts(self) -> None:
        """Clean up old resolved alerts"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            hours=self.alert_retention_hours
        )

        alerts_to_remove = []
        for alert_id, alert in self.active_alerts.items():
            if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff_time:
                alerts_to_remove.append(alert_id)

        for alert_id in alerts_to_remove:
            del self.active_alerts[alert_id]

    async def add_websocket_connection(self, websocket) -> None:
        """Add new WebSocket connection for real-time updates"""
        self.websocket_connections.append(websocket)
        logger.info("New WebSocket connection added for monitoring")

        # Send current state to new connection
        await websocket.send(
            json.dumps(
                {
                    "type": "initial_state",
                    "active_sessions": {
                        sid: {
                            "session_id": session.session_id,
                            "exam_id": session.exam_id,
                            "exam_type": session.exam_type.value,
                            "metrics": session.calculate_metrics(),
                        }
                        for sid, session in self.active_sessions.items()
                    },
                    "active_alerts": {
                        aid: alert.to_dict()
                        for aid, alert in self.active_alerts.items()
                        if not alert.resolved
                    },
                }
            )
        )

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_sessions": len(self.active_sessions),
            "total_active_students": sum(
                len(session.active_students)
                for session in self.active_sessions.values()
            ),
            "active_alerts": len(
                [a for a in self.active_alerts.values() if not a.resolved]
            ),
            "critical_alerts": len(
                [
                    a
                    for a in self.active_alerts.values()
                    if not a.resolved
                    and a.level in [MonitoringLevel.CRITICAL, MonitoringLevel.EMERGENCY]
                ]
            ),
            "sessions": [
                {
                    "session_id": session.session_id,
                    "exam_id": session.exam_id,
                    "exam_type": session.exam_type.value,
                    "metrics": session.calculate_metrics(),
                    "start_time": session.start_time.isoformat(),
                }
                for session in self.active_sessions.values()
            ],
            "recent_alerts": sorted(
                [
                    alert.to_dict()
                    for alert in self.active_alerts.values()
                    if not alert.resolved
                ],
                key=lambda x: x["timestamp"],
                reverse=True,
            )[:10],
        }

    async def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledge(user)
            await self._broadcast_update(
                {
                    "type": "alert_acknowledged",
                    "alert_id": alert_id,
                    "acknowledged_by": user,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            return True
        return False

    async def resolve_alert(self, alert_id: str, user: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolve(user)
            await self._broadcast_update(
                {
                    "type": "alert_resolved",
                    "alert_id": alert_id,
                    "resolved_by": user,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            return True
        return False


# Global monitoring instance
monitoring_dashboard = RealTimeMonitoringDashboard()


# WebSocket handler for real-time updates
async def websocket_handler(websocket, path):
    """Handle WebSocket connections for real-time monitoring"""
    await monitoring_dashboard.add_websocket_connection(websocket)
    try:
        await websocket.wait_closed()
    except websockets.ConnectionClosed:
        pass
    finally:
        if websocket in monitoring_dashboard.websocket_connections:
            monitoring_dashboard.websocket_connections.remove(websocket)


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Real-time Exam Metrics and Monitoring System")
    print("=" * 55)

    async def test_monitoring_system():
        """Test monitoring system"""
        # Initialize monitoring dashboard
        await monitoring_dashboard.initialize()

        # Create sample exam session
        session = ExamSession(
            session_id="session_test_001",
            exam_id="tyt_final_2024",
            exam_type=TurkishExamType.TYT,
            start_time=datetime.now(timezone.utc),
            scheduled_end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            registered_students=list(range(1001, 1051)),  # 50 students
        )

        # Register session
        await monitoring_dashboard.register_exam_session(session)
        print(f"Registered exam session: {session.session_id}")

        # Simulate student activities
        for i in range(1001, 1021):  # 20 students join
            await monitoring_dashboard.update_session_participant(
                session.session_id, i, "join"
            )

        print(f"20 students joined the exam")

        # Simulate some students leaving (creating a dropout alert)
        for i in range(1001, 1011):  # 10 students leave
            await monitoring_dashboard.update_session_participant(
                session.session_id, i, "leave"
            )

        print(f"10 students left the exam (should trigger dropout alert)")

        # Get dashboard data
        dashboard_data = monitoring_dashboard.get_dashboard_data()
        print(f"Active sessions: {dashboard_data['active_sessions']}")
        print(f"Active alerts: {dashboard_data['active_alerts']}")
        print(f"Critical alerts: {dashboard_data['critical_alerts']}")

        # Run one monitoring cycle manually
        await monitoring_dashboard._monitoring_cycle()

        updated_data = monitoring_dashboard.get_dashboard_data()
        print(
            f"After monitoring cycle - Active alerts: {updated_data['active_alerts']}"
        )

    # Run test
    asyncio.run(test_monitoring_system())
