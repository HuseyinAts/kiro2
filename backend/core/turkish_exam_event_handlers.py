"""
KIRO2 Turkish Exam Event Handlers
Specialized event handlers for Turkish university entrance examination system
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from core.application_metrics import MetricType, get_metrics_collector
from core.background_job_processor import (
    get_turkish_job_processor,
    schedule_exam_processing,
)
from core.message_queue_system import QueuePriority, QueueType, enqueue_message
from core.realtime_notification_system import (
    NotificationPriority,
    NotificationType,
    get_notification_system,
    notify_time_warning,
    send_realtime_notification,
)
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config
from core.unified_event_bus import Event, EventType, get_event_bus

config = get_unified_config()
logger = get_logger(__name__, LogCategory.EVENTS)


class TurkishExamType(Enum):
    """Turkish examination types"""

    YKS = "yks"  # Yükseköğretim Kurumları Sınavı
    TYT = "tyt"  # Temel Yeterlilik Testi
    AYT = "ayt"  # Alan Yeterlilik Testi
    MSU = "msu"  # Matematik ve Fen Bilimleri Testi
    DIL = "dil"  # Yabancı Dil Testi
    KPSS = "kpss"  # Kamu Personeli Seçme Sınavı
    ALES = "ales"  # Akademik Personel ve Lisansüstü Eğitimi Giriş Sınavı


class ExamEventAction(Enum):
    """Exam event actions"""

    REGISTERED = "registered"
    STARTED = "started"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIME_WARNING = "time_warning"
    RESULTS_READY = "results_ready"
    RANKING_UPDATED = "ranking_updated"


@dataclass
class ExamSession:
    """Turkish exam session information"""

    session_id: str
    user_id: int
    exam_type: TurkishExamType
    exam_date: datetime
    start_time: datetime
    duration_minutes: int
    questions_total: int
    questions_answered: int = 0
    current_section: str = ""
    remaining_time_minutes: int = 0
    is_simulation: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_progress_percentage(self) -> float:
        """Calculate exam progress percentage"""
        if self.questions_total == 0:
            return 0.0
        return (self.questions_answered / self.questions_total) * 100.0

    def get_time_progress_percentage(self) -> float:
        """Calculate time progress percentage"""
        elapsed_minutes = self.duration_minutes - self.remaining_time_minutes
        return (elapsed_minutes / self.duration_minutes) * 100.0


@dataclass
class ExamResult:
    """Turkish exam results"""

    exam_session_id: str
    user_id: int
    exam_type: TurkishExamType
    total_score: float
    section_scores: dict[str, float]
    correct_answers: int
    wrong_answers: int
    empty_answers: int
    percentile: float | None = None
    ranking: int | None = None
    performance_analysis: dict[str, Any] = field(default_factory=dict)


class TurkishExamEventHandlers:
    """Comprehensive event handlers for Turkish exam system"""

    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self.active_sessions: dict[str, ExamSession] = {}
        self.exam_results: dict[str, ExamResult] = {}
        self.notification_templates = self._load_notification_templates()
        self.registered = False

        # Subject mappings for Turkish education system
        self.turkish_subjects = {
            "matematik": "Matematik",
            "turkce": "Türkçe-Edebiyat",
            "tarih": "Tarih",
            "cografya": "Coğrafya",
            "felsefe": "Felsefe",
            "fizik": "Fizik",
            "kimya": "Kimya",
            "biyoloji": "Biyoloji",
            "geometri": "Geometri",
        }

    def _load_notification_templates(self) -> dict[str, dict[str, str]]:
        """Load Turkish exam notification templates"""
        return {
            "exam_started": {
                "title": "{exam_type} Exam Started",
                "title_tr": "{exam_type} Sınavı Başladı",
                "message": "Your {exam_type} exam has started. You have {duration} minutes. Good luck!",
                "message_tr": "{exam_type} sınavınız başladı. {duration} dakikanız var. Başarılar!",
            },
            "time_warning_30": {
                "title": "30 Minutes Remaining",
                "title_tr": "30 Dakika Kaldı",
                "message": "You have 30 minutes left in your {exam_type} exam.",
                "message_tr": "{exam_type} sınavınızda 30 dakikanız kaldı.",
            },
            "time_warning_15": {
                "title": "15 Minutes Remaining",
                "title_tr": "15 Dakika Kaldı",
                "message": "Only 15 minutes left! Please review your answers.",
                "message_tr": "Sadece 15 dakika kaldı! Lütfen cevaplarınızı gözden geçirin.",
            },
            "time_warning_5": {
                "title": "Final Warning - 5 Minutes",
                "title_tr": "Son Uyarı - 5 Dakika",
                "message": "Only 5 minutes remaining in your {exam_type} exam!",
                "message_tr": "{exam_type} sınavınızda sadece 5 dakika kaldı!",
            },
            "exam_completed": {
                "title": "Exam Completed",
                "title_tr": "Sınav Tamamlandı",
                "message": "You have successfully completed your {exam_type} exam. Results will be available soon.",
                "message_tr": "{exam_type} sınavınızı başarıyla tamamladınız. Sonuçlar yakında hazır olacak.",
            },
            "results_ready": {
                "title": "Exam Results Ready",
                "title_tr": "Sınav Sonuçları Hazır",
                "message": "Your {exam_type} exam results are now available. Score: {score}",
                "message_tr": "{exam_type} sınav sonuçlarınız hazır. Puanınız: {score}",
            },
            "yks_registration": {
                "title": "YKS Registration Period",
                "title_tr": "YKS Kayıt Dönemi",
                "message": "YKS registration is now open until {end_date}",
                "message_tr": "YKS kaydı {end_date} tarihine kadar açık",
            },
        }

    async def register_handlers(self):
        """Register all Turkish exam event handlers"""
        if self.registered:
            return

        try:
            event_bus = await get_event_bus()

            # Register core exam event handlers
            await self._register_exam_lifecycle_handlers(event_bus)
            await self._register_progress_handlers(event_bus)
            await self._register_notification_handlers(event_bus)
            await self._register_analytics_handlers(event_bus)
            await self._register_system_handlers(event_bus)

            self.registered = True
            logger.info(
                "Turkish exam event handlers registered successfully",
                message_tr="Türk sınavı olay işleyicileri başarıyla kaydedildi",
            )

        except Exception as e:
            logger.error(f"Failed to register Turkish exam event handlers: {e}")
            raise

    async def _register_exam_lifecycle_handlers(self, event_bus):
        """Register exam lifecycle event handlers"""

        @event_bus.subscribe(EventType.TYT_SIMULATION_STARTED, priority=10)
        async def handle_tyt_started(event: Event):
            await self._handle_exam_started(event, TurkishExamType.TYT)

        @event_bus.subscribe(EventType.AYT_SIMULATION_STARTED, priority=10)
        async def handle_ayt_started(event: Event):
            await self._handle_exam_started(event, TurkishExamType.AYT)

        @event_bus.subscribe(EventType.TYT_SIMULATION_COMPLETED, priority=10)
        async def handle_tyt_completed(event: Event):
            await self._handle_exam_completed(event, TurkishExamType.TYT)

        @event_bus.subscribe(EventType.AYT_SIMULATION_COMPLETED, priority=10)
        async def handle_ayt_completed(event: Event):
            await self._handle_exam_completed(event, TurkishExamType.AYT)

        @event_bus.subscribe(EventType.YKS_REGISTRATION_OPENED, priority=5)
        async def handle_yks_registration_opened(event: Event):
            await self._handle_yks_registration(event, "opened")

        @event_bus.subscribe(EventType.YKS_REGISTRATION_CLOSED, priority=5)
        async def handle_yks_registration_closed(event: Event):
            await self._handle_yks_registration(event, "closed")

    async def _register_progress_handlers(self, event_bus):
        """Register exam progress tracking handlers"""

        @event_bus.subscribe(EventType.QUESTION_ANSWERED, priority=8)
        async def handle_question_answered(event: Event):
            await self._handle_question_progress(event)

        @event_bus.subscribe(EventType.LEARNING_PROGRESS_UPDATED, priority=6)
        async def handle_learning_progress(event: Event):
            await self._handle_learning_progress(event)

    async def _register_notification_handlers(self, event_bus):
        """Register notification event handlers"""

        @event_bus.subscribe(EventType.PRACTICE_TEST_STARTED, priority=7)
        async def handle_practice_started(event: Event):
            await self._handle_practice_notification(event, "started")

        @event_bus.subscribe(EventType.PRACTICE_TEST_COMPLETED, priority=7)
        async def handle_practice_completed(event: Event):
            await self._handle_practice_notification(event, "completed")

        @event_bus.subscribe(EventType.EXAM_RESULTS_PUBLISHED, priority=8)
        async def handle_results_published(event: Event):
            await self._handle_results_notification(event)

    async def _register_analytics_handlers(self, event_bus):
        """Register analytics and reporting handlers"""

        @event_bus.subscribe(EventType.USER_ACTION_TRACKED, priority=4)
        async def handle_user_analytics(event: Event):
            await self._handle_analytics_tracking(event)

        @event_bus.subscribe(EventType.PERFORMANCE_METRIC_RECORDED, priority=4)
        async def handle_performance_metrics(event: Event):
            await self._handle_performance_analysis(event)

        @event_bus.subscribe(EventType.RANKING_CALCULATED, priority=6)
        async def handle_ranking_update(event: Event):
            await self._handle_ranking_notification(event)

    async def _register_system_handlers(self, event_bus):
        """Register system-level event handlers"""

        @event_bus.subscribe(EventType.USER_LOGIN, priority=3)
        async def handle_user_login(event: Event):
            await self._handle_user_context_setup(event)

        @event_bus.subscribe(EventType.SYSTEM_STARTUP, priority=2)
        async def handle_system_startup(event: Event):
            await self._handle_system_initialization(event)

    # Core Event Handler Implementations

    async def _handle_exam_started(self, event: Event, exam_type: TurkishExamType):
        """Handle exam start events"""
        try:
            user_id = event.user_id
            session_id = event.session_id or event.data.get("session_id")

            # Create exam session
            exam_session = ExamSession(
                session_id=session_id,
                user_id=user_id,
                exam_type=exam_type,
                exam_date=datetime.now(UTC),
                start_time=datetime.now(UTC),
                duration_minutes=event.data.get("duration_minutes", 180),
                questions_total=event.data.get("questions_total", 120),
                remaining_time_minutes=event.data.get("duration_minutes", 180),
                is_simulation=event.data.get("is_simulation", True),
                metadata=event.data,
            )

            self.active_sessions[session_id] = exam_session

            # Send real-time notification
            await self._send_exam_notification(
                user_id,
                session_id,
                exam_type.value.upper(),
                "exam_started",
                duration=exam_session.duration_minutes,
            )

            # Schedule time warnings
            await self._schedule_time_warnings(exam_session)

            # Enqueue background processing
            await enqueue_message(
                QueueType.EXAM_PROCESSING,
                {
                    "action": "track_exam_session",
                    "session_id": session_id,
                    "exam_type": exam_type.value,
                    "user_id": user_id,
                },
                priority=QueuePriority.HIGH,
                user_id=user_id,
            )

            # Record metrics
            self.metrics_collector.record_metric(
                MetricType.EXAM_STARTED,
                1,
                metadata={
                    "exam_type": exam_type.value,
                    "user_id": user_id,
                    "is_simulation": exam_session.is_simulation,
                },
            )

            logger.info(
                f"{exam_type.value.upper()} exam started for user {user_id}",
                message_tr=f"Kullanıcı {user_id} için {exam_type.value.upper()} sınavı başladı",
            )

        except Exception as e:
            logger.error(f"Error handling exam started event: {e}")

    async def _handle_exam_completed(self, event: Event, exam_type: TurkishExamType):
        """Handle exam completion events"""
        try:
            user_id = event.user_id
            session_id = event.session_id or event.data.get("session_id")

            # Get exam session
            exam_session = self.active_sessions.get(session_id)
            if not exam_session:
                logger.warning(f"No active session found for {session_id}")
                return

            # Create exam result
            exam_result = ExamResult(
                exam_session_id=session_id,
                user_id=user_id,
                exam_type=exam_type,
                total_score=event.data.get("total_score", 0),
                section_scores=event.data.get("section_scores", {}),
                correct_answers=event.data.get("correct_answers", 0),
                wrong_answers=event.data.get("wrong_answers", 0),
                empty_answers=event.data.get("empty_answers", 0),
                performance_analysis=event.data.get("performance_analysis", {}),
            )

            self.exam_results[session_id] = exam_result

            # Send completion notification
            await self._send_exam_notification(
                user_id, session_id, exam_type.value.upper(), "exam_completed"
            )

            # Schedule background processing for results
            job_processor = await get_turkish_job_processor()
            await job_processor.schedule_job(
                "calculate_exam_ranking",
                args=[exam_type.value, "daily"],
                queue_type=QueueType.ANALYTICS,
                priority=QueuePriority.NORMAL,
            )

            # Schedule result analysis
            await schedule_exam_processing(
                exam_type.value,
                user_id,
                {
                    "exam_result": exam_result.__dict__,
                    "session_data": exam_session.__dict__,
                },
            )

            # Clean up active session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

            # Record completion metrics
            self.metrics_collector.record_metric(
                MetricType.EXAM_COMPLETED,
                1,
                metadata={
                    "exam_type": exam_type.value,
                    "user_id": user_id,
                    "score": exam_result.total_score,
                    "duration": (
                        datetime.now(UTC) - exam_session.start_time
                    ).total_seconds(),
                },
            )

            logger.info(
                f"{exam_type.value.upper()} exam completed for user {user_id}, score: {exam_result.total_score}",
                message_tr=f"Kullanıcı {user_id} için {exam_type.value.upper()} sınavı tamamlandı, puan: {exam_result.total_score}",
            )

        except Exception as e:
            logger.error(f"Error handling exam completed event: {e}")

    async def _handle_yks_registration(self, event: Event, action: str):
        """Handle YKS registration events"""
        try:
            end_date = event.data.get("registration_end_date", "TBA")

            # Broadcast system announcement
            notification_system = await get_notification_system()

            if action == "opened":
                await notification_system.send_system_announcement(
                    title="YKS Registration Period Started",
                    message=f"YKS registration is now open until {end_date}",
                    title_tr="YKS Kayıt Dönemi Başladı",
                    message_tr=f"YKS kaydı {end_date} tarihine kadar açık",
                    priority=NotificationPriority.HIGH,
                )
            else:
                await notification_system.send_system_announcement(
                    title="YKS Registration Period Ended",
                    message="YKS registration period has ended",
                    title_tr="YKS Kayıt Dönemi Sona Erdi",
                    message_tr="YKS kayıt dönemi sona ermiştir",
                    priority=NotificationPriority.HIGH,
                )

            # Enqueue notification processing
            await enqueue_message(
                QueueType.NOTIFICATIONS,
                {
                    "type": "yks_registration",
                    "action": action,
                    "end_date": end_date,
                    "broadcast": True,
                },
                priority=QueuePriority.HIGH,
            )

            logger.info(
                f"YKS registration {action} event processed",
                message_tr=f"YKS kayıt {action} olayı işlendi",
            )

        except Exception as e:
            logger.error(f"Error handling YKS registration event: {e}")

    async def _handle_question_progress(self, event: Event):
        """Handle question answering progress"""
        try:
            user_id = event.user_id
            session_id = event.session_id

            if session_id not in self.active_sessions:
                return

            exam_session = self.active_sessions[session_id]
            exam_session.questions_answered += 1
            exam_session.current_section = event.data.get("subject", "")

            # Update progress metadata
            exam_session.metadata["last_question_time"] = datetime.now(UTC).isoformat()
            exam_session.metadata[
                "current_progress"
            ] = exam_session.get_progress_percentage()

            # Send progress update if significant milestone
            progress = exam_session.get_progress_percentage()
            if progress in [25, 50, 75]:
                await send_realtime_notification(
                    NotificationType.LESSON_PROGRESS,
                    f"Progress Update: {progress:.0f}%",
                    f"You have completed {progress:.0f}% of the exam",
                    user_id=user_id,
                    title_tr=f"İlerleme Güncellemesi: %{progress:.0f}",
                    message_tr=f"Sınavın %{progress:.0f}'ını tamamladınız",
                )

            logger.debug(
                f"Question progress updated for session {session_id}: {progress:.1f}%"
            )

        except Exception as e:
            logger.error(f"Error handling question progress: {e}")

    async def _handle_learning_progress(self, event: Event):
        """Handle learning progress updates"""
        try:
            user_id = event.user_id
            subject = event.data.get("subject", "")
            progress_data = event.data.get("progress", {})

            # Convert Turkish subject names
            subject_tr = self.turkish_subjects.get(subject.lower(), subject)

            # Enqueue analytics processing
            await enqueue_message(
                QueueType.ANALYTICS,
                {
                    "action": "update_learning_progress",
                    "user_id": user_id,
                    "subject": subject,
                    "subject_tr": subject_tr,
                    "progress_data": progress_data,
                },
                priority=QueuePriority.NORMAL,
                user_id=user_id,
            )

            # Check for achievements
            if progress_data.get("milestone_reached"):
                await self._handle_achievement_notification(
                    user_id, subject_tr, progress_data
                )

            logger.debug(
                f"Learning progress updated for user {user_id} in {subject_tr}"
            )

        except Exception as e:
            logger.error(f"Error handling learning progress: {e}")

    async def _handle_achievement_notification(
        self, user_id: int, subject: str, progress_data: dict[str, Any]
    ):
        """Handle achievement notifications"""
        try:
            achievement_type = progress_data.get("achievement_type", "milestone")
            achievement_name = progress_data.get(
                "achievement_name", f"{subject} Progress"
            )

            await send_realtime_notification(
                NotificationType.ACHIEVEMENT_UNLOCKED,
                f"Achievement Unlocked: {achievement_name}",
                f"Congratulations on your progress in {subject}!",
                user_id=user_id,
                title_tr=f"Başarı Kazanıldı: {achievement_name}",
                message_tr=f"{subject} konusundaki ilerlemeniz için tebrikler!",
                priority=NotificationPriority.HIGH,
            )

            logger.info(
                f"Achievement notification sent to user {user_id}: {achievement_name}"
            )

        except Exception as e:
            logger.error(f"Error sending achievement notification: {e}")

    async def _schedule_time_warnings(self, exam_session: ExamSession):
        """Schedule time warning notifications for exam"""
        try:
            job_processor = await get_turkish_job_processor()

            # Schedule warnings at different intervals
            warning_times = [30, 15, 5]  # minutes before end

            for warning_minutes in warning_times:
                if exam_session.duration_minutes > warning_minutes:
                    delay_seconds = (
                        exam_session.duration_minutes - warning_minutes
                    ) * 60

                    await job_processor.schedule_job(
                        "send_exam_time_warning",
                        args=[
                            exam_session.user_id,
                            exam_session.exam_type.value,
                            warning_minutes,
                        ],
                        delay_seconds=delay_seconds,
                        queue_type=QueueType.NOTIFICATIONS,
                        priority=QueuePriority.HIGH,
                    )

            logger.debug(
                f"Time warnings scheduled for exam session {exam_session.session_id}"
            )

        except Exception as e:
            logger.error(f"Error scheduling time warnings: {e}")

    async def _send_exam_notification(
        self,
        user_id: int,
        session_id: str,
        exam_type: str,
        template_key: str,
        **template_vars,
    ):
        """Send exam-specific notification using templates"""
        try:
            template = self.notification_templates.get(template_key, {})
            if not template:
                logger.warning(f"No template found for key: {template_key}")
                return

            # Format template variables
            format_vars = {"exam_type": exam_type, **template_vars}

            title = template.get("title", "").format(**format_vars)
            message = template.get("message", "").format(**format_vars)
            title_tr = template.get("title_tr", "").format(**format_vars)
            message_tr = template.get("message_tr", "").format(**format_vars)

            # Determine notification type
            notification_type_map = {
                "exam_started": NotificationType.EXAM_STARTED,
                "exam_completed": NotificationType.EXAM_COMPLETED,
                "time_warning_30": NotificationType.EXAM_TIME_WARNING,
                "time_warning_15": NotificationType.EXAM_TIME_WARNING,
                "time_warning_5": NotificationType.EXAM_TIME_WARNING,
                "results_ready": NotificationType.EXAM_RESULTS_READY,
            }

            notification_type = notification_type_map.get(
                template_key, NotificationType.SYSTEM_ANNOUNCEMENT
            )

            await send_realtime_notification(
                notification_type=notification_type,
                title=title,
                message=message,
                user_id=user_id,
                title_tr=title_tr,
                message_tr=message_tr,
                priority=NotificationPriority.HIGH,
                data={"exam_type": exam_type, "session_id": session_id},
            )

            logger.debug(f"Exam notification sent: {template_key} to user {user_id}")

        except Exception as e:
            logger.error(f"Error sending exam notification: {e}")

    # Additional handler methods...

    async def _handle_practice_notification(self, event: Event, action: str):
        """Handle practice test notifications"""
        try:
            user_id = event.user_id
            test_type = event.data.get("test_type", "practice")
            subject = event.data.get("subject", "")

            if action == "started":
                await send_realtime_notification(
                    NotificationType.EXAM_STARTED,
                    "Practice Test Started",
                    f"Your {subject} practice test has begun",
                    user_id=user_id,
                    title_tr="Deneme Sınavı Başladı",
                    message_tr=f"{subject} deneme sınavınız başladı",
                )
            else:
                await send_realtime_notification(
                    NotificationType.EXAM_COMPLETED,
                    "Practice Test Completed",
                    f"You have completed the {subject} practice test",
                    user_id=user_id,
                    title_tr="Deneme Sınavı Tamamlandı",
                    message_tr=f"{subject} deneme sınavını tamamladınız",
                )

            logger.debug(f"Practice test {action} notification sent to user {user_id}")

        except Exception as e:
            logger.error(f"Error handling practice notification: {e}")

    async def _handle_results_notification(self, event: Event):
        """Handle exam results notification"""
        try:
            user_id = event.user_id
            exam_type = event.data.get("exam_type", "exam")
            score = event.data.get("score", 0)

            await self._send_exam_notification(
                user_id,
                event.session_id or "",
                exam_type.upper(),
                "results_ready",
                score=score,
            )

            logger.info(f"Results notification sent to user {user_id} for {exam_type}")

        except Exception as e:
            logger.error(f"Error handling results notification: {e}")

    async def _handle_analytics_tracking(self, event: Event):
        """Handle user analytics tracking"""
        try:
            # Process analytics data for Turkish exam insights
            await enqueue_message(
                QueueType.ANALYTICS,
                {
                    "action": "process_user_analytics",
                    "event_data": event.data,
                    "user_id": event.user_id,
                    "timestamp": event.timestamp.isoformat(),
                },
                priority=QueuePriority.LOW,
                user_id=event.user_id,
            )

        except Exception as e:
            logger.error(f"Error handling analytics tracking: {e}")

    async def _handle_performance_analysis(self, event: Event):
        """Handle performance metric analysis"""
        try:
            # Analyze performance patterns for Turkish students
            performance_data = event.data

            await enqueue_message(
                QueueType.ANALYTICS,
                {
                    "action": "analyze_performance_patterns",
                    "performance_data": performance_data,
                    "analysis_type": "turkish_exam_patterns",
                },
                priority=QueuePriority.NORMAL,
            )

        except Exception as e:
            logger.error(f"Error handling performance analysis: {e}")

    async def _handle_ranking_notification(self, event: Event):
        """Handle ranking update notifications"""
        try:
            exam_type = event.data.get("exam_type", "")
            rankings = event.data.get("rankings", [])

            # Notify users of ranking updates
            for ranking_data in rankings[:100]:  # Top 100
                user_id = ranking_data.get("user_id")
                rank = ranking_data.get("rank")

                if user_id and rank:
                    await send_realtime_notification(
                        NotificationType.EXAM_RANKING_UPDATE,
                        f"{exam_type} Ranking Update",
                        f"Your new rank: #{rank}",
                        user_id=user_id,
                        title_tr=f"{exam_type} Sıralama Güncellesi",
                        message_tr=f"Yeni sıralamanız: #{rank}",
                        priority=NotificationPriority.NORMAL,
                    )

            logger.info(f"Ranking notifications sent for {exam_type}")

        except Exception as e:
            logger.error(f"Error handling ranking notification: {e}")

    async def _handle_user_context_setup(self, event: Event):
        """Handle user context setup on login"""
        try:
            user_id = event.user_id

            # Setup user-specific event context
            # This could include loading user preferences, exam history, etc.

            logger.debug(f"User context setup for {user_id}")

        except Exception as e:
            logger.error(f"Error setting up user context: {e}")

    async def _handle_system_initialization(self, event: Event):
        """Handle system startup initialization"""
        try:
            # Initialize Turkish exam system components
            logger.info("Turkish exam event system initialized on system startup")

        except Exception as e:
            logger.error(f"Error in system initialization: {e}")

    def get_active_sessions(self) -> dict[str, ExamSession]:
        """Get all active exam sessions"""
        return self.active_sessions.copy()

    def get_exam_results(self) -> dict[str, ExamResult]:
        """Get all exam results"""
        return self.exam_results.copy()

    def get_session_stats(self) -> dict[str, Any]:
        """Get session statistics"""
        return {
            "active_sessions": len(self.active_sessions),
            "completed_exams": len(self.exam_results),
            "session_by_type": {
                exam_type.value: sum(
                    1 for s in self.active_sessions.values() if s.exam_type == exam_type
                )
                for exam_type in TurkishExamType
            },
        }


# Global event handlers instance
_turkish_exam_handlers: TurkishExamEventHandlers | None = None


async def get_turkish_exam_handlers() -> TurkishExamEventHandlers:
    """Get global Turkish exam event handlers instance"""
    global _turkish_exam_handlers

    if _turkish_exam_handlers is None:
        _turkish_exam_handlers = TurkishExamEventHandlers()
        await _turkish_exam_handlers.register_handlers()

    return _turkish_exam_handlers


# Utility functions for Turkish exam events


async def publish_turkish_exam_event(
    exam_type: TurkishExamType,
    action: ExamEventAction,
    user_id: int,
    exam_data: dict[str, Any],
    session_id: str | None = None,
) -> str:
    """Publish Turkish exam events with proper typing"""
    from core.unified_event_bus import (
        publish_turkish_exam_event as _publish_event,
    )

    return await _publish_event(
        exam_type.value, action.value, user_id, exam_data, session_id
    )


async def start_turkish_exam_session(
    user_id: int,
    exam_type: TurkishExamType,
    duration_minutes: int = 180,
    questions_total: int = 120,
    is_simulation: bool = True,
) -> str:
    """Start a new Turkish exam session"""
    import uuid

    session_id = str(uuid.uuid4())

    await publish_turkish_exam_event(
        exam_type=exam_type,
        action=ExamEventAction.STARTED,
        user_id=user_id,
        exam_data={
            "session_id": session_id,
            "duration_minutes": duration_minutes,
            "questions_total": questions_total,
            "is_simulation": is_simulation,
            "start_time": datetime.now(UTC).isoformat(),
        },
        session_id=session_id,
    )

    return session_id


async def complete_turkish_exam_session(
    session_id: str,
    user_id: int,
    exam_type: TurkishExamType,
    exam_results: dict[str, Any],
) -> str:
    """Complete Turkish exam session with results"""
    return await publish_turkish_exam_event(
        exam_type=exam_type,
        action=ExamEventAction.COMPLETED,
        user_id=user_id,
        exam_data={
            "session_id": session_id,
            "completion_time": datetime.now(UTC).isoformat(),
            **exam_results,
        },
        session_id=session_id,
    )


async def send_exam_time_warning(
    user_id: int, exam_type: str, minutes_remaining: int, session_id: str | None = None
) -> str:
    """Send exam time warning notification"""
    return await notify_time_warning(
        user_id=user_id,
        exam_type=exam_type,
        minutes_remaining=minutes_remaining,
        session_id=session_id,
    )
