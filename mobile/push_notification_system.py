"""
KIRO2 Push Notification System
Cross-platform push notification management for Turkish exam preparation platform
Türkiye Üniversite Sınavları Hazırlık Platformu - Push Bildirim Sistemi
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
import json
import uuid
import sqlite3
from pathlib import Path

from backend.core.structured_logging import get_logger, LogCategory
from backend.core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.MOBILE)
config = get_unified_config()


class NotificationType(Enum):
    """Types of notifications"""
    STUDY_REMINDER = "study_reminder"
    EXAM_ALERT = "exam_alert"
    PERFORMANCE_UPDATE = "performance_update"
    ACHIEVEMENT = "achievement"
    NEWS_UPDATE = "news_update"
    SOCIAL_INTERACTION = "social_interaction"
    SYSTEM_MESSAGE = "system_message"
    EXAM_COUNTDOWN = "exam_countdown"
    DAILY_GOAL = "daily_goal"
    WEEKLY_REPORT = "weekly_report"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Notification delivery channels"""
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"
    SYSTEM_TRAY = "system_tray"


class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    CLICKED = "clicked"
    DISMISSED = "dismissed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class NotificationTemplate:
    """Template for notification content"""
    template_id: str
    notification_type: NotificationType
    
    # Content templates
    title_template: str
    body_template: str
    action_text: str = ""
    
    # Turkish localization
    title_template_tr: str = ""
    body_template_tr: str = ""
    action_text_tr: str = ""
    
    # Template variables
    template_variables: List[str] = field(default_factory=list)
    
    # Styling
    icon: Optional[str] = None
    color: Optional[str] = None
    sound: Optional[str] = None
    
    # Behavior
    is_actionable: bool = False
    auto_dismiss: bool = True
    dismiss_timeout: int = 5000  # milliseconds
    
    # Platform-specific templates
    platform_templates: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.title_template_tr:
            self.title_template_tr = self.title_template
        if not self.body_template_tr:
            self.body_template_tr = self.body_template
        if not self.action_text_tr:
            self.action_text_tr = self.action_text
    
    def render_content(self, variables: Dict[str, Any], language: str = "tr") -> Dict[str, str]:
        """Render notification content with variables"""
        title_template = self.title_template_tr if language == "tr" else self.title_template
        body_template = self.body_template_tr if language == "tr" else self.body_template
        action_template = self.action_text_tr if language == "tr" else self.action_text
        
        try:
            title = title_template.format(**variables) if variables else title_template
            body = body_template.format(**variables) if variables else body_template
            action = action_template.format(**variables) if variables else action_template
            
            return {
                "title": title,
                "body": body,
                "action_text": action
            }
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return {
                "title": title_template,
                "body": body_template,
                "action_text": action_template
            }


@dataclass
class PushNotification:
    """Push notification data structure"""
    notification_id: str
    user_id: str
    notification_type: NotificationType
    
    # Content
    title: str
    body: str
    action_text: str = ""
    
    # Metadata
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.PUSH])
    
    # Scheduling
    scheduled_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    
    # Targeting
    device_tokens: List[str] = field(default_factory=list)
    platform_filters: List[str] = field(default_factory=list)
    
    # Data payload
    data_payload: Dict[str, Any] = field(default_factory=dict)
    
    # Behavior
    is_actionable: bool = False
    action_url: Optional[str] = None
    deep_link: Optional[str] = None
    
    # Styling
    icon: Optional[str] = None
    color: Optional[str] = None
    sound: Optional[str] = "default"
    badge_count: Optional[int] = None
    
    # Status tracking
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Analytics
    delivery_attempts: int = 0
    click_count: int = 0
    delivery_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.notification_id:
            self.notification_id = str(uuid.uuid4())
        
        if not self.expiry_time:
            # Default expiry: 7 days from creation
            self.expiry_time = self.created_at + timedelta(days=7)
    
    def is_expired(self) -> bool:
        """Check if notification is expired"""
        return datetime.now(timezone.utc) > self.expiry_time
    
    def is_ready_to_send(self) -> bool:
        """Check if notification is ready to be sent"""
        if self.status != NotificationStatus.SCHEDULED:
            return False
        
        if self.scheduled_time and datetime.now(timezone.utc) < self.scheduled_time:
            return False
        
        return not self.is_expired()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/storage"""
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "type": self.notification_type.value,
            "title": self.title,
            "body": self.body,
            "action_text": self.action_text,
            "priority": self.priority.value,
            "channels": [channel.value for channel in self.channels],
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "expiry_time": self.expiry_time.isoformat() if self.expiry_time else None,
            "device_tokens": self.device_tokens,
            "platform_filters": self.platform_filters,
            "data_payload": self.data_payload,
            "is_actionable": self.is_actionable,
            "action_url": self.action_url,
            "deep_link": self.deep_link,
            "styling": {
                "icon": self.icon,
                "color": self.color,
                "sound": self.sound,
                "badge_count": self.badge_count
            },
            "status": self.status.value,
            "timestamps": {
                "created_at": self.created_at.isoformat(),
                "sent_at": self.sent_at.isoformat() if self.sent_at else None,
                "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None
            },
            "analytics": {
                "delivery_attempts": self.delivery_attempts,
                "click_count": self.click_count,
                "delivery_errors": self.delivery_errors
            }
        }


class NotificationScheduler:
    """Scheduler for managing notification timing"""
    
    def __init__(self, db_path: str = "notifications.db"):
        self.db_path = db_path
        self.scheduled_notifications: Dict[str, PushNotification] = {}
        self.recurring_schedules: Dict[str, Dict[str, Any]] = {}
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize SQLite database for notifications"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    action_text TEXT,
                    priority TEXT NOT NULL,
                    channels TEXT NOT NULL,
                    scheduled_time TEXT,
                    expiry_time TEXT,
                    device_tokens TEXT,
                    platform_filters TEXT,
                    data_payload TEXT,
                    is_actionable INTEGER,
                    action_url TEXT,
                    deep_link TEXT,
                    icon TEXT,
                    color TEXT,
                    sound TEXT,
                    badge_count INTEGER,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    sent_at TEXT,
                    delivered_at TEXT,
                    delivery_attempts INTEGER DEFAULT 0,
                    click_count INTEGER DEFAULT 0,
                    delivery_errors TEXT,
                    INDEX idx_user_id (user_id),
                    INDEX idx_status (status),
                    INDEX idx_scheduled_time (scheduled_time),
                    INDEX idx_notification_type (notification_type)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recurring_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    template_id TEXT NOT NULL,
                    schedule_pattern TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_executed TEXT,
                    next_execution TEXT,
                    execution_count INTEGER DEFAULT 0,
                    template_variables TEXT,
                    INDEX idx_user_id (user_id),
                    INDEX idx_next_execution (next_execution),
                    INDEX idx_active (is_active)
                )
            """)
    
    async def schedule_notification(self, notification: PushNotification) -> bool:
        """Schedule a notification for delivery"""
        try:
            notification.status = NotificationStatus.SCHEDULED
            self.scheduled_notifications[notification.notification_id] = notification
            
            # Save to database
            await self._save_notification_to_db(notification)
            
            logger.info(f"Scheduled notification {notification.notification_id} for user {notification.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule notification: {e}")
            return False
    
    async def _save_notification_to_db(self, notification: PushNotification) -> None:
        """Save notification to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO notifications (
                    notification_id, user_id, notification_type, title, body, action_text,
                    priority, channels, scheduled_time, expiry_time, device_tokens,
                    platform_filters, data_payload, is_actionable, action_url, deep_link,
                    icon, color, sound, badge_count, status, created_at, sent_at,
                    delivered_at, delivery_attempts, click_count, delivery_errors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notification.notification_id,
                notification.user_id,
                notification.notification_type.value,
                notification.title,
                notification.body,
                notification.action_text,
                notification.priority.value,
                json.dumps([ch.value for ch in notification.channels]),
                notification.scheduled_time.isoformat() if notification.scheduled_time else None,
                notification.expiry_time.isoformat() if notification.expiry_time else None,
                json.dumps(notification.device_tokens),
                json.dumps(notification.platform_filters),
                json.dumps(notification.data_payload),
                1 if notification.is_actionable else 0,
                notification.action_url,
                notification.deep_link,
                notification.icon,
                notification.color,
                notification.sound,
                notification.badge_count,
                notification.status.value,
                notification.created_at.isoformat(),
                notification.sent_at.isoformat() if notification.sent_at else None,
                notification.delivered_at.isoformat() if notification.delivered_at else None,
                notification.delivery_attempts,
                notification.click_count,
                json.dumps(notification.delivery_errors)
            ))
    
    async def get_ready_notifications(self) -> List[PushNotification]:
        """Get notifications ready to be sent"""
        ready_notifications = []
        
        for notification in self.scheduled_notifications.values():
            if notification.is_ready_to_send():
                ready_notifications.append(notification)
        
        # Also load from database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM notifications 
                WHERE status = 'scheduled' 
                AND (scheduled_time IS NULL OR scheduled_time <= ?)
                AND expiry_time > ?
            """, (
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))
            
            for row in cursor.fetchall():
                notification = self._notification_from_db_row(row)
                if notification and notification.notification_id not in self.scheduled_notifications:
                    ready_notifications.append(notification)
        
        return ready_notifications
    
    def _notification_from_db_row(self, row: tuple) -> Optional[PushNotification]:
        """Create notification object from database row"""
        try:
            return PushNotification(
                notification_id=row[0],
                user_id=row[1],
                notification_type=NotificationType(row[2]),
                title=row[3],
                body=row[4],
                action_text=row[5] or "",
                priority=NotificationPriority(row[6]),
                channels=[NotificationChannel(ch) for ch in json.loads(row[7])],
                scheduled_time=datetime.fromisoformat(row[8]) if row[8] else None,
                expiry_time=datetime.fromisoformat(row[9]) if row[9] else None,
                device_tokens=json.loads(row[10]) if row[10] else [],
                platform_filters=json.loads(row[11]) if row[11] else [],
                data_payload=json.loads(row[12]) if row[12] else {},
                is_actionable=bool(row[13]),
                action_url=row[14],
                deep_link=row[15],
                icon=row[16],
                color=row[17],
                sound=row[18] or "default",
                badge_count=row[19],
                status=NotificationStatus(row[20]),
                created_at=datetime.fromisoformat(row[21]),
                sent_at=datetime.fromisoformat(row[22]) if row[22] else None,
                delivered_at=datetime.fromisoformat(row[23]) if row[23] else None,
                delivery_attempts=row[24],
                click_count=row[25],
                delivery_errors=json.loads(row[26]) if row[26] else []
            )
        except Exception as e:
            logger.error(f"Failed to create notification from DB row: {e}")
            return None
    
    async def create_recurring_schedule(
        self,
        user_id: str,
        notification_type: NotificationType,
        template_id: str,
        schedule_pattern: str,
        template_variables: Dict[str, Any] = None
    ) -> str:
        """Create a recurring notification schedule"""
        schedule_id = str(uuid.uuid4())
        
        # Calculate next execution time based on pattern
        next_execution = self._calculate_next_execution(schedule_pattern)
        
        schedule_data = {
            "schedule_id": schedule_id,
            "user_id": user_id,
            "notification_type": notification_type.value,
            "template_id": template_id,
            "schedule_pattern": schedule_pattern,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_executed": None,
            "next_execution": next_execution.isoformat(),
            "execution_count": 0,
            "template_variables": json.dumps(template_variables or {})
        }
        
        self.recurring_schedules[schedule_id] = schedule_data
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO recurring_schedules (
                    schedule_id, user_id, notification_type, template_id, schedule_pattern,
                    is_active, created_at, last_executed, next_execution, execution_count,
                    template_variables
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schedule_id, user_id, notification_type.value, template_id, schedule_pattern,
                1, schedule_data["created_at"], None, schedule_data["next_execution"],
                0, schedule_data["template_variables"]
            ))
        
        logger.info(f"Created recurring schedule {schedule_id} for user {user_id}")
        return schedule_id
    
    def _calculate_next_execution(self, pattern: str) -> datetime:
        """Calculate next execution time from pattern"""
        now = datetime.now(timezone.utc)
        
        if pattern == "daily":
            # Next day at 9:00 AM
            next_exec = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif pattern == "weekly":
            # Next week same day at 9:00 AM
            next_exec = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(weeks=1)
        elif pattern == "study_reminder":
            # Every 3 hours during study hours (9-21)
            if now.hour >= 21:
                next_exec = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                next_exec = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=3)
                if next_exec.hour > 21:
                    next_exec = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif pattern == "exam_countdown":
            # Daily at 8:00 AM
            next_exec = now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:
            # Default: 1 hour from now
            next_exec = now + timedelta(hours=1)
        
        return next_exec


class PushNotificationService:
    """Main push notification service"""
    
    def __init__(self):
        self.templates: Dict[str, NotificationTemplate] = {}
        self.scheduler = NotificationScheduler()
        self.delivery_providers: Dict[str, Any] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        
        # Analytics
        self.delivery_stats: Dict[str, int] = {
            "sent": 0,
            "delivered": 0,
            "clicked": 0,
            "failed": 0
        }
        
        self._initialize_default_templates()
    
    def _initialize_default_templates(self) -> None:
        """Initialize default notification templates"""
        
        # Study reminder template
        study_reminder = NotificationTemplate(
            template_id="study_reminder",
            notification_type=NotificationType.STUDY_REMINDER,
            title_template="Çalışma Zamanı! ⏰",
            body_template="{subject} konusunda çalışma zamanın geldi. Hedefine ulaşmak için şimdi başla!",
            action_text="Çalışmaya Başla",
            title_template_tr="Çalışma Zamanı! ⏰",
            body_template_tr="{subject} konusunda çalışma zamanın geldi. Hedefine ulaşmak için şimdi başla!",
            action_text_tr="Çalışmaya Başla",
            template_variables=["subject"],
            icon="study",
            color="#4CAF50",
            sound="study_bell",
            is_actionable=True
        )
        
        # Exam alert template
        exam_alert = NotificationTemplate(
            template_id="exam_alert",
            notification_type=NotificationType.EXAM_ALERT,
            title_template="Sınav Uyarısı! [BOOKS]",
            body_template="{exam_name} sınavına {days_left} gün kaldı. Hazırlığını tamamladın mı?",
            action_text="Sınava Hazırlan",
            title_template_tr="Sınav Uyarısı! [BOOKS]",
            body_template_tr="{exam_name} sınavına {days_left} gün kaldı. Hazırlığını tamamladın mı?",
            action_text_tr="Sınava Hazırlan",
            template_variables=["exam_name", "days_left"],
            icon="exam",
            color="#FF9800",
            sound="exam_alert",
            is_actionable=True
        )
        
        # Performance update template
        performance_update = NotificationTemplate(
            template_id="performance_update",
            notification_type=NotificationType.PERFORMANCE_UPDATE,
            title_template="İlerleme Raporu [CHART]",
            body_template="Bu hafta {correct_answers} doğru cevap verdin! Başarı oranın: %{success_rate}",
            action_text="Detayları Gör",
            title_template_tr="İlerleme Raporu [CHART]",
            body_template_tr="Bu hafta {correct_answers} doğru cevap verdin! Başarı oranın: %{success_rate}",
            action_text_tr="Detayları Gör",
            template_variables=["correct_answers", "success_rate"],
            icon="performance",
            color="#2196F3",
            sound="success",
            is_actionable=True
        )
        
        # Achievement template
        achievement = NotificationTemplate(
            template_id="achievement",
            notification_type=NotificationType.ACHIEVEMENT,
            title_template="Tebrikler! [PARTY]",
            body_template="{achievement_name} rozetini kazandın! Harika bir başarı!",
            action_text="Rozetimi Gör",
            title_template_tr="Tebrikler! [PARTY]",
            body_template_tr="{achievement_name} rozetini kazandın! Harika bir başarı!",
            action_text_tr="Rozetimi Gör",
            template_variables=["achievement_name"],
            icon="achievement",
            color="#FFD700",
            sound="achievement",
            is_actionable=True
        )
        
        # Daily goal template
        daily_goal = NotificationTemplate(
            template_id="daily_goal",
            notification_type=NotificationType.DAILY_GOAL,
            title_template="Günlük Hedef [TARGET]",
            body_template="Bugün {remaining_questions} soru daha çözmen gerekiyor. Hadi başla!",
            action_text="Soru Çöz",
            title_template_tr="Günlük Hedef [TARGET]",
            body_template_tr="Bugün {remaining_questions} soru daha çözmen gerekiyor. Hadi başla!",
            action_text_tr="Soru Çöz",
            template_variables=["remaining_questions"],
            icon="target",
            color="#9C27B0",
            sound="goal_reminder",
            is_actionable=True
        )
        
        # Store templates
        self.templates = {
            "study_reminder": study_reminder,
            "exam_alert": exam_alert,
            "performance_update": performance_update,
            "achievement": achievement,
            "daily_goal": daily_goal
        }
    
    async def send_notification(
        self,
        user_id: str,
        template_id: str,
        template_variables: Dict[str, Any] = None,
        device_tokens: List[str] = None,
        scheduled_time: Optional[datetime] = None
    ) -> str:
        """Send notification using template"""
        
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        
        # Render content
        content = template.render_content(template_variables or {}, "tr")
        
        # Create notification
        notification = PushNotification(
            user_id=user_id,
            notification_type=template.notification_type,
            title=content["title"],
            body=content["body"],
            action_text=content["action_text"],
            scheduled_time=scheduled_time,
            device_tokens=device_tokens or [],
            is_actionable=template.is_actionable,
            icon=template.icon,
            color=template.color,
            sound=template.sound,
            data_payload=template_variables or {}
        )
        
        # Schedule notification
        if scheduled_time:
            await self.scheduler.schedule_notification(notification)
        else:
            # Send immediately
            await self._send_immediate_notification(notification)
        
        return notification.notification_id
    
    async def _send_immediate_notification(self, notification: PushNotification) -> bool:
        """Send notification immediately"""
        try:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            notification.delivery_attempts += 1
            
            # Here would be the actual push notification sending logic
            # For now, we'll simulate success
            success = await self._deliver_to_platforms(notification)
            
            if success:
                notification.status = NotificationStatus.DELIVERED
                notification.delivered_at = datetime.now(timezone.utc)
                self.delivery_stats["sent"] += 1
                self.delivery_stats["delivered"] += 1
            else:
                notification.status = NotificationStatus.FAILED
                notification.delivery_errors.append("Platform delivery failed")
                self.delivery_stats["failed"] += 1
            
            # Update in database
            await self.scheduler._save_notification_to_db(notification)
            
            logger.info(f"Notification {notification.notification_id} delivery: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to send notification {notification.notification_id}: {e}")
            notification.status = NotificationStatus.FAILED
            notification.delivery_errors.append(str(e))
            self.delivery_stats["failed"] += 1
            return False
    
    async def _deliver_to_platforms(self, notification: PushNotification) -> bool:
        """Deliver notification to platform-specific services"""
        success = True
        
        for channel in notification.channels:
            if channel == NotificationChannel.PUSH:
                # Send to push notification service (FCM, APNs, etc.)
                platform_success = await self._send_push_notification(notification)
                success = success and platform_success
            elif channel == NotificationChannel.EMAIL:
                # Send email notification
                platform_success = await self._send_email_notification(notification)
                success = success and platform_success
            elif channel == NotificationChannel.SMS:
                # Send SMS notification
                platform_success = await self._send_sms_notification(notification)
                success = success and platform_success
        
        return success
    
    async def _send_push_notification(self, notification: PushNotification) -> bool:
        """Send push notification via FCM/APNs"""
        # Mock implementation - would integrate with actual push services
        logger.info(f"Sending push notification: {notification.title}")
        return True
    
    async def _send_email_notification(self, notification: PushNotification) -> bool:
        """Send email notification"""
        # Mock implementation - would integrate with email service
        logger.info(f"Sending email notification: {notification.title}")
        return True
    
    async def _send_sms_notification(self, notification: PushNotification) -> bool:
        """Send SMS notification"""
        # Mock implementation - would integrate with SMS service
        logger.info(f"Sending SMS notification: {notification.title}")
        return True
    
    async def create_study_reminder(self, user_id: str, subject: str, device_tokens: List[str] = None) -> str:
        """Create study reminder notification"""
        return await self.send_notification(
            user_id=user_id,
            template_id="study_reminder",
            template_variables={"subject": subject},
            device_tokens=device_tokens
        )
    
    async def create_exam_alert(
        self,
        user_id: str,
        exam_name: str,
        days_left: int,
        device_tokens: List[str] = None
    ) -> str:
        """Create exam alert notification"""
        return await self.send_notification(
            user_id=user_id,
            template_id="exam_alert",
            template_variables={"exam_name": exam_name, "days_left": days_left},
            device_tokens=device_tokens
        )
    
    async def create_performance_update(
        self,
        user_id: str,
        correct_answers: int,
        success_rate: float,
        device_tokens: List[str] = None
    ) -> str:
        """Create performance update notification"""
        return await self.send_notification(
            user_id=user_id,
            template_id="performance_update",
            template_variables={
                "correct_answers": correct_answers,
                "success_rate": round(success_rate, 1)
            },
            device_tokens=device_tokens
        )
    
    async def create_achievement_notification(
        self,
        user_id: str,
        achievement_name: str,
        device_tokens: List[str] = None
    ) -> str:
        """Create achievement notification"""
        return await self.send_notification(
            user_id=user_id,
            template_id="achievement",
            template_variables={"achievement_name": achievement_name},
            device_tokens=device_tokens
        )
    
    async def create_daily_goal_reminder(
        self,
        user_id: str,
        remaining_questions: int,
        device_tokens: List[str] = None
    ) -> str:
        """Create daily goal reminder"""
        return await self.send_notification(
            user_id=user_id,
            template_id="daily_goal",
            template_variables={"remaining_questions": remaining_questions},
            device_tokens=device_tokens
        )
    
    async def setup_recurring_reminders(self, user_id: str, preferences: Dict[str, Any]) -> List[str]:
        """Setup recurring notifications based on user preferences"""
        schedule_ids = []
        
        # Study reminders
        if preferences.get("study_reminders_enabled", True):
            schedule_id = await self.scheduler.create_recurring_schedule(
                user_id=user_id,
                notification_type=NotificationType.STUDY_REMINDER,
                template_id="study_reminder",
                schedule_pattern="study_reminder",
                template_variables={"subject": "Matematik"}
            )
            schedule_ids.append(schedule_id)
        
        # Daily goals
        if preferences.get("daily_goals_enabled", True):
            schedule_id = await self.scheduler.create_recurring_schedule(
                user_id=user_id,
                notification_type=NotificationType.DAILY_GOAL,
                template_id="daily_goal",
                schedule_pattern="daily",
                template_variables={"remaining_questions": 10}
            )
            schedule_ids.append(schedule_id)
        
        # Performance updates
        if preferences.get("performance_updates_enabled", True):
            schedule_id = await self.scheduler.create_recurring_schedule(
                user_id=user_id,
                notification_type=NotificationType.PERFORMANCE_UPDATE,
                template_id="performance_update",
                schedule_pattern="weekly",
                template_variables={"correct_answers": 0, "success_rate": 0}
            )
            schedule_ids.append(schedule_id)
        
        return schedule_ids
    
    async def process_scheduled_notifications(self) -> int:
        """Process and send scheduled notifications"""
        ready_notifications = await self.scheduler.get_ready_notifications()
        sent_count = 0
        
        for notification in ready_notifications:
            success = await self._send_immediate_notification(notification)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def handle_notification_click(self, notification_id: str, user_id: str) -> bool:
        """Handle notification click event"""
        try:
            with sqlite3.connect(self.scheduler.db_path) as conn:
                cursor = conn.execute("""
                    SELECT click_count FROM notifications 
                    WHERE notification_id = ? AND user_id = ?
                """, (notification_id, user_id))
                
                row = cursor.fetchone()
                if row:
                    new_click_count = row[0] + 1
                    conn.execute("""
                        UPDATE notifications 
                        SET click_count = ?, status = 'clicked'
                        WHERE notification_id = ? AND user_id = ?
                    """, (new_click_count, notification_id, user_id))
                    
                    self.delivery_stats["clicked"] += 1
                    logger.info(f"Notification {notification_id} clicked by user {user_id}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to handle notification click: {e}")
            return False
    
    def get_notification_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get notification analytics"""
        analytics = {
            "overall_stats": self.delivery_stats.copy(),
            "templates_used": len(self.templates),
            "active_schedules": len(self.scheduler.recurring_schedules)
        }
        
        if user_id:
            # Get user-specific analytics
            with sqlite3.connect(self.scheduler.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        notification_type,
                        status,
                        COUNT(*) as count,
                        AVG(click_count) as avg_clicks
                    FROM notifications 
                    WHERE user_id = ?
                    GROUP BY notification_type, status
                """, (user_id,))
                
                user_stats = {}
                for row in cursor.fetchall():
                    notification_type = row[0]
                    status = row[1]
                    count = row[2]
                    avg_clicks = row[3]
                    
                    if notification_type not in user_stats:
                        user_stats[notification_type] = {}
                    
                    user_stats[notification_type][status] = {
                        "count": count,
                        "avg_clicks": avg_clicks
                    }
                
                analytics["user_stats"] = user_stats
        
        return analytics


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Push Notification System")
    print("=" * 40)
    
    async def test_notification_system():
        """Test notification system"""
        service = PushNotificationService()
        
        # Test study reminder
        notification_id = await service.create_study_reminder(
            user_id="test_user_123",
            subject="Matematik - Türev",
            device_tokens=["device_token_123"]
        )
        print(f"Study reminder created: {notification_id}")
        
        # Test exam alert
        notification_id = await service.create_exam_alert(
            user_id="test_user_123",
            exam_name="TYT Deneme Sınavı",
            days_left=5,
            device_tokens=["device_token_123"]
        )
        print(f"Exam alert created: {notification_id}")
        
        # Test performance update
        notification_id = await service.create_performance_update(
            user_id="test_user_123",
            correct_answers=25,
            success_rate=78.5,
            device_tokens=["device_token_123"]
        )
        print(f"Performance update created: {notification_id}")
        
        # Test achievement
        notification_id = await service.create_achievement_notification(
            user_id="test_user_123",
            achievement_name="İlk 100 Soru",
            device_tokens=["device_token_123"]
        )
        print(f"Achievement notification created: {notification_id}")
        
        # Test daily goal reminder
        notification_id = await service.create_daily_goal_reminder(
            user_id="test_user_123",
            remaining_questions=15,
            device_tokens=["device_token_123"]
        )
        print(f"Daily goal reminder created: {notification_id}")
        
        # Setup recurring reminders
        preferences = {
            "study_reminders_enabled": True,
            "daily_goals_enabled": True,
            "performance_updates_enabled": True
        }
        schedule_ids = await service.setup_recurring_reminders("test_user_123", preferences)
        print(f"Recurring schedules created: {len(schedule_ids)}")
        
        # Process scheduled notifications
        sent_count = await service.process_scheduled_notifications()
        print(f"Processed notifications: {sent_count}")
        
        # Test notification click
        click_success = await service.handle_notification_click(notification_id, "test_user_123")
        print(f"Notification click handled: {click_success}")
        
        # Get analytics
        analytics = service.get_notification_analytics("test_user_123")
        print(f"Analytics: {analytics['overall_stats']}")
        
        print("\nPush notification system test completed!")
    
    # Run test
    asyncio.run(test_notification_system())