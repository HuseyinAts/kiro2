"""
KIRO2 Alert Service
Log-based alerting with Elasticsearch and notification channels

Bu servis:
- Elasticsearch Watcher ile log monitoring
- Error spike detection
- Critical log alerting
- Multi-channel notifications (Email, Slack)
sağlar.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert lifecycle status."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class AlertRule:
    """
    Alert rule definition.

    Attributes:
        name: Unique rule identifier
        description: Human-readable description
        query: Elasticsearch query
        threshold: Trigger threshold count
        time_window_minutes: Time window for threshold check
        severity: Alert severity level
        throttle_minutes: Minimum time between alerts
        notification_channels: List of channel names
        enabled: Whether rule is active
    """

    name: str
    description: str
    query: Dict[str, Any]
    threshold: int
    time_window_minutes: int = 5
    severity: AlertSeverity = AlertSeverity.WARNING
    throttle_minutes: int = 5
    notification_channels: List[str] = field(default_factory=lambda: ["slack"])
    enabled: bool = True


@dataclass
class Alert:
    """
    Alert instance.

    Attributes:
        id: Unique alert ID
        rule_name: Source rule name
        severity: Alert severity
        title: Alert title
        message: Alert message
        details: Additional context
        created_at: Creation timestamp
        status: Current status
        acknowledged_by: User who acknowledged
        acknowledged_at: Acknowledgement timestamp
    """

    id: str
    rule_name: str
    severity: AlertSeverity
    title: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
        }


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Send alert notification."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get channel name."""
        pass


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, webhook_url: str, channel: str = "#kiro2-alerts"):
        """
        Initialize Slack channel.

        Args:
            webhook_url: Slack webhook URL
            channel: Target channel name
        """
        self.webhook_url = webhook_url
        self.channel = channel

    def get_name(self) -> str:
        return "slack"

    async def send(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        try:
            import aiohttp

            # Severity to color mapping
            color_map = {
                AlertSeverity.INFO: "#36a64f",  # green
                AlertSeverity.WARNING: "#ffc107",  # yellow
                AlertSeverity.ERROR: "#dc3545",  # red
                AlertSeverity.CRITICAL: "#6f42c1",  # purple
            }

            # Severity to emoji mapping
            emoji_map = {
                AlertSeverity.INFO: ":information_source:",
                AlertSeverity.WARNING: ":warning:",
                AlertSeverity.ERROR: ":x:",
                AlertSeverity.CRITICAL: ":rotating_light:",
            }

            payload = {
                "channel": self.channel,
                "username": "KIRO2 Alert Bot",
                "icon_emoji": emoji_map.get(alert.severity, ":bell:"),
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "#808080"),
                        "title": f"{emoji_map.get(alert.severity, '')} {alert.title}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True,
                            },
                            {
                                "title": "Rule",
                                "value": alert.rule_name,
                                "short": True,
                            },
                            {
                                "title": "Time",
                                "value": alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": True,
                            },
                            {
                                "title": "Alert ID",
                                "value": alert.id[:8],
                                "short": True,
                            },
                        ],
                        "footer": "KIRO2 YKS Platform",
                        "ts": int(alert.created_at.timestamp()),
                    }
                ],
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url, json=payload, timeout=10
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent: {alert.id}")
                        return True
                    else:
                        logger.error(f"Slack alert failed: {response.status}")
                        return False

        except ImportError:
            logger.warning("aiohttp not installed, Slack notifications disabled")
            return False
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return False


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
    ):
        """
        Initialize Email channel.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: Sender email address
            to_emails: List of recipient emails
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails

    def get_name(self) -> str:
        return "email"

    async def send(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{alert.severity.value.upper()}] KIRO2 Alert: {alert.title}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)

            # Plain text version
            text_content = f"""
KIRO2 Alert Notification

Title: {alert.title}
Severity: {alert.severity.value.upper()}
Rule: {alert.rule_name}
Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{alert.message}

Alert ID: {alert.id}

---
KIRO2 YKS AI Education Platform
            """

            # HTML version
            severity_colors = {
                AlertSeverity.INFO: "#28a745",
                AlertSeverity.WARNING: "#ffc107",
                AlertSeverity.ERROR: "#dc3545",
                AlertSeverity.CRITICAL: "#6f42c1",
            }

            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .alert-box {{ border-left: 4px solid {severity_colors.get(alert.severity, '#808080')};
                      padding: 15px; background-color: #f8f9fa; margin: 10px 0; }}
        .severity {{ color: {severity_colors.get(alert.severity, '#808080')};
                     font-weight: bold; text-transform: uppercase; }}
        .meta {{ color: #6c757d; font-size: 0.9em; }}
        .footer {{ margin-top: 20px; padding-top: 10px; border-top: 1px solid #dee2e6;
                   color: #6c757d; font-size: 0.85em; }}
    </style>
</head>
<body>
    <h2>KIRO2 Alert Notification</h2>

    <div class="alert-box">
        <h3>{alert.title}</h3>
        <p class="severity">{alert.severity.value}</p>
        <p>{alert.message}</p>
    </div>

    <div class="meta">
        <p><strong>Rule:</strong> {alert.rule_name}</p>
        <p><strong>Time:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><strong>Alert ID:</strong> {alert.id}</p>
    </div>

    <div class="footer">
        <p>KIRO2 YKS AI Education Platform</p>
    </div>
</body>
</html>
            """

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                start_tls=True,
            )

            logger.info(f"Email alert sent: {alert.id}")
            return True

        except ImportError:
            logger.warning("aiosmtplib not installed, email notifications disabled")
            return False
        except Exception as e:
            logger.error(f"Email notification error: {e}")
            return False


class AlertService:
    """
    Main Alert Service for KIRO2.

    Manages alert rules, monitors Elasticsearch, and sends notifications.
    """

    # Default alert rules
    DEFAULT_RULES = [
        AlertRule(
            name="error_spike",
            description="Detects sudden increase in error logs",
            query={
                "bool": {
                    "must": [
                        {"term": {"log_level_normalized": "ERROR"}},
                        {"range": {"@timestamp": {"gte": "now-5m"}}},
                    ]
                }
            },
            threshold=100,
            time_window_minutes=5,
            severity=AlertSeverity.ERROR,
            throttle_minutes=5,
        ),
        AlertRule(
            name="critical_log",
            description="Detects critical/fatal log entries",
            query={
                "bool": {
                    "must": [
                        {
                            "terms": {
                                "log_level_normalized": ["CRITICAL", "FATAL"]
                            }
                        },
                        {"range": {"@timestamp": {"gte": "now-1m"}}},
                    ]
                }
            },
            threshold=1,
            time_window_minutes=1,
            severity=AlertSeverity.CRITICAL,
            throttle_minutes=1,
        ),
        AlertRule(
            name="slow_api_responses",
            description="Detects too many slow API responses",
            query={
                "bool": {
                    "must": [
                        {"term": {"performance_class": "very_slow"}},
                        {"range": {"@timestamp": {"gte": "now-5m"}}},
                    ]
                }
            },
            threshold=50,
            time_window_minutes=5,
            severity=AlertSeverity.WARNING,
            throttle_minutes=10,
        ),
        AlertRule(
            name="auth_failures",
            description="Detects excessive authentication failures",
            query={
                "bool": {
                    "must": [
                        {"term": {"event_category": "authentication"}},
                        {"term": {"success": False}},
                        {"range": {"@timestamp": {"gte": "now-5m"}}},
                    ]
                }
            },
            threshold=20,
            time_window_minutes=5,
            severity=AlertSeverity.WARNING,
            throttle_minutes=5,
        ),
        AlertRule(
            name="exam_errors",
            description="Detects errors in exam processing",
            query={
                "bool": {
                    "must": [
                        {"term": {"event_category": "exam"}},
                        {"term": {"log_level_normalized": "ERROR"}},
                        {"range": {"@timestamp": {"gte": "now-5m"}}},
                    ]
                }
            },
            threshold=10,
            time_window_minutes=5,
            severity=AlertSeverity.ERROR,
            throttle_minutes=5,
        ),
    ]

    def __init__(self, es_client: AsyncElasticsearch):
        """
        Initialize Alert Service.

        Args:
            es_client: Async Elasticsearch client
        """
        self.es_client = es_client
        self.rules: Dict[str, AlertRule] = {}
        self.channels: Dict[str, NotificationChannel] = {}
        self.last_alert_times: Dict[str, datetime] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_index = "kiro2-alerts"

        # Load default rules
        for rule in self.DEFAULT_RULES:
            self.rules[rule.name] = rule

    def add_channel(self, channel: NotificationChannel) -> None:
        """Add notification channel."""
        self.channels[channel.get_name()] = channel
        logger.info(f"Notification channel added: {channel.get_name()}")

    def add_rule(self, rule: AlertRule) -> None:
        """Add or update alert rule."""
        self.rules[rule.name] = rule
        logger.info(f"Alert rule added/updated: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """Remove alert rule."""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Alert rule removed: {rule_name}")
            return True
        return False

    def _should_throttle(self, rule_name: str, throttle_minutes: int) -> bool:
        """Check if alert should be throttled."""
        last_time = self.last_alert_times.get(rule_name)
        if not last_time:
            return False

        elapsed = datetime.now(timezone.utc) - last_time
        return elapsed < timedelta(minutes=throttle_minutes)

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        import uuid

        return str(uuid.uuid4())

    async def _execute_query(self, rule: AlertRule) -> int:
        """Execute alert rule query and return hit count."""
        try:
            response = await self.es_client.count(
                index="kiro2-logs-*", body={"query": rule.query}
            )
            return response.get("count", 0)
        except Exception as e:
            logger.error(f"Alert query error for {rule.name}: {e}")
            return 0

    async def _store_alert(self, alert: Alert) -> bool:
        """Store alert in Elasticsearch."""
        try:
            await self.es_client.index(
                index=self.alert_index,
                id=alert.id,
                body=alert.to_dict(),
                refresh=True,
            )
            return True
        except Exception as e:
            logger.error(f"Alert storage error: {e}")
            return False

    async def _send_notifications(self, alert: Alert, channels: List[str]) -> None:
        """Send notifications to specified channels."""
        tasks = []
        for channel_name in channels:
            channel = self.channels.get(channel_name)
            if channel:
                tasks.append(channel.send(alert))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Notification error: {result}")

    async def check_rule(self, rule: AlertRule) -> Optional[Alert]:
        """
        Check a single rule and create alert if triggered.

        Args:
            rule: Alert rule to check

        Returns:
            Alert if triggered, None otherwise
        """
        if not rule.enabled:
            return None

        # Check throttling
        if self._should_throttle(rule.name, rule.throttle_minutes):
            return None

        # Execute query
        count = await self._execute_query(rule)

        # Check threshold
        if count >= rule.threshold:
            alert = Alert(
                id=self._generate_alert_id(),
                rule_name=rule.name,
                severity=rule.severity,
                title=f"Alert: {rule.description}",
                message=f"Detected {count} occurrences in the last {rule.time_window_minutes} minutes (threshold: {rule.threshold})",
                details={
                    "count": count,
                    "threshold": rule.threshold,
                    "time_window_minutes": rule.time_window_minutes,
                    "query": rule.query,
                },
            )

            # Update throttle time
            self.last_alert_times[rule.name] = datetime.now(timezone.utc)

            # Store and notify
            await self._store_alert(alert)
            await self._send_notifications(alert, rule.notification_channels)

            # Track active alert
            self.active_alerts[alert.id] = alert

            logger.warning(f"Alert triggered: {rule.name} - {count} occurrences")
            return alert

        return None

    async def check_all_rules(self) -> List[Alert]:
        """
        Check all enabled rules.

        Returns:
            List of triggered alerts
        """
        alerts = []
        for rule in self.rules.values():
            alert = await self.check_rule(rule)
            if alert:
                alerts.append(alert)

        return alerts

    async def acknowledge_alert(
        self, alert_id: str, acknowledged_by: str
    ) -> Optional[Alert]:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge
            acknowledged_by: User who acknowledged

        Returns:
            Updated alert or None
        """
        alert = self.active_alerts.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now(timezone.utc)

        await self._store_alert(alert)
        logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
        return alert

    async def silence_rule(self, rule_name: str, duration_minutes: int) -> bool:
        """
        Silence a rule for specified duration.

        Args:
            rule_name: Rule to silence
            duration_minutes: Silence duration

        Returns:
            Success status
        """
        if rule_name in self.rules:
            # Set last alert time to future to prevent triggering
            self.last_alert_times[rule_name] = datetime.now(timezone.utc) + timedelta(
                minutes=duration_minutes
            )
            logger.info(f"Rule silenced: {rule_name} for {duration_minutes} minutes")
            return True
        return False

    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        try:
            response = await self.es_client.search(
                index=self.alert_index,
                body={
                    "query": {"term": {"status": "active"}},
                    "sort": [{"created_at": {"order": "desc"}}],
                    "size": 100,
                },
            )

            alerts = []
            for hit in response.get("hits", {}).get("hits", []):
                source = hit["_source"]
                alerts.append(
                    Alert(
                        id=source["id"],
                        rule_name=source["rule_name"],
                        severity=AlertSeverity(source["severity"]),
                        title=source["title"],
                        message=source["message"],
                        details=source.get("details", {}),
                        created_at=datetime.fromisoformat(source["created_at"]),
                        status=AlertStatus(source["status"]),
                    )
                )
            return alerts

        except Exception as e:
            logger.error(f"Get active alerts error: {e}")
            return list(self.active_alerts.values())

    async def get_alert_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get alert statistics for a time period.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Alert statistics
        """
        try:
            response = await self.es_client.search(
                index=self.alert_index,
                body={
                    "query": {
                        "range": {
                            "created_at": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat(),
                            }
                        }
                    },
                    "aggs": {
                        "by_severity": {"terms": {"field": "severity"}},
                        "by_rule": {"terms": {"field": "rule_name"}},
                        "by_status": {"terms": {"field": "status"}},
                        "over_time": {
                            "date_histogram": {
                                "field": "created_at",
                                "calendar_interval": "hour",
                            }
                        },
                    },
                    "size": 0,
                },
            )

            aggs = response.get("aggregations", {})
            return {
                "total": response.get("hits", {}).get("total", {}).get("value", 0),
                "by_severity": {
                    b["key"]: b["doc_count"]
                    for b in aggs.get("by_severity", {}).get("buckets", [])
                },
                "by_rule": {
                    b["key"]: b["doc_count"]
                    for b in aggs.get("by_rule", {}).get("buckets", [])
                },
                "by_status": {
                    b["key"]: b["doc_count"]
                    for b in aggs.get("by_status", {}).get("buckets", [])
                },
                "over_time": [
                    {"time": b["key_as_string"], "count": b["doc_count"]}
                    for b in aggs.get("over_time", {}).get("buckets", [])
                ],
            }

        except Exception as e:
            logger.error(f"Alert statistics error: {e}")
            return {}


# Global service instance
_alert_service: Optional[AlertService] = None


async def get_alert_service() -> AlertService:
    """
    Get Alert Service singleton.

    Returns:
        AlertService instance
    """
    global _alert_service

    if _alert_service is None:
        from elasticsearch import AsyncElasticsearch
        from core.config import settings

        es_client = AsyncElasticsearch(
            hosts=[settings.ELASTICSEARCH_URL or "http://localhost:9200"],
            retry_on_timeout=True,
            max_retries=3,
        )
        _alert_service = AlertService(es_client)

        # Add default Slack channel if configured
        if hasattr(settings, "SLACK_WEBHOOK_URL") and settings.SLACK_WEBHOOK_URL:
            _alert_service.add_channel(
                SlackNotificationChannel(
                    webhook_url=settings.SLACK_WEBHOOK_URL,
                    channel=getattr(settings, "SLACK_ALERT_CHANNEL", "#kiro2-alerts"),
                )
            )

        # Add email channel if configured
        if hasattr(settings, "SMTP_HOST") and settings.SMTP_HOST:
            _alert_service.add_channel(
                EmailNotificationChannel(
                    smtp_host=settings.SMTP_HOST,
                    smtp_port=getattr(settings, "SMTP_PORT", 587),
                    username=getattr(settings, "SMTP_USERNAME", ""),
                    password=getattr(settings, "SMTP_PASSWORD", ""),
                    from_email=getattr(settings, "ALERT_FROM_EMAIL", "alerts@kiro2.com"),
                    to_emails=getattr(
                        settings, "ALERT_TO_EMAILS", ["admin@kiro2.com"]
                    ),
                )
            )

    return _alert_service


async def start_alert_monitoring(interval_seconds: int = 60) -> None:
    """
    Start continuous alert monitoring.

    Args:
        interval_seconds: Check interval in seconds
    """
    service = await get_alert_service()

    logger.info(f"Starting alert monitoring with {interval_seconds}s interval")

    while True:
        try:
            alerts = await service.check_all_rules()
            if alerts:
                logger.info(f"Alert check completed: {len(alerts)} alerts triggered")
        except Exception as e:
            logger.error(f"Alert monitoring error: {e}")

        await asyncio.sleep(interval_seconds)
