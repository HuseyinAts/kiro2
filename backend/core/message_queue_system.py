"""
KIRO2 Message Queue System
Advanced message queue and background job processing for Turkish exam platform
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import asyncio
import json
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import redis.asyncio as redis

from core.application_metrics import MetricType, get_metrics_collector
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config

config = get_unified_config()
logger = get_logger(__name__, LogCategory.QUEUE)


class QueuePriority(Enum):
    """Message queue priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class JobStatus(Enum):
    """Background job status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


class QueueType(Enum):
    """Queue types for different workloads"""

    # High priority queues
    REAL_TIME = "real_time"  # WebSocket notifications, live updates
    AUTHENTICATION = "authentication"  # Login, logout, token refresh
    EXAM_PROCESSING = "exam_processing"  # TYT/AYT exam submissions

    # Normal priority queues
    NOTIFICATIONS = "notifications"  # Email, SMS, push notifications
    CONTENT_PROCESSING = "content"  # Content generation, analysis
    ANALYTICS = "analytics"  # Learning analytics, progress tracking

    # Low priority queues
    BATCH_PROCESSING = "batch"  # Reports, bulk operations
    CLEANUP = "cleanup"  # Database cleanup, cache maintenance
    MAINTENANCE = "maintenance"  # System maintenance tasks


@dataclass
class QueueMessage:
    """Message in the queue system"""

    id: str
    queue_type: QueueType
    payload: dict[str, Any]
    priority: QueuePriority
    created_at: datetime
    scheduled_at: datetime | None = None
    attempts: int = 0
    max_attempts: int = 3
    timeout: int = 300  # 5 minutes default
    user_id: int | None = None
    session_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.correlation_id:
            self.correlation_id = self.id

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary"""
        data = asdict(self)
        data["queue_type"] = self.queue_type.value
        data["priority"] = self.priority.value
        data["created_at"] = self.created_at.isoformat()
        if self.scheduled_at:
            data["scheduled_at"] = self.scheduled_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueueMessage":
        """Create message from dictionary"""
        data = data.copy()
        data["queue_type"] = QueueType(data["queue_type"])
        data["priority"] = QueuePriority(data["priority"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("scheduled_at"):
            data["scheduled_at"] = datetime.fromisoformat(data["scheduled_at"])
        return cls(**data)


@dataclass
class BackgroundJob:
    """Background job definition"""

    id: str
    job_type: str
    function_name: str
    args: list[Any]
    kwargs: dict[str, Any]
    queue_type: QueueType
    priority: QueuePriority
    status: JobStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any | None = None
    error: str | None = None
    progress: int = 0  # 0-100
    attempts: int = 0
    max_attempts: int = 3
    timeout: int = 300
    user_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary"""
        data = asdict(self)
        data["queue_type"] = self.queue_type.value
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data


class RedisMessageQueue:
    """Redis-based message queue with streams"""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or getattr(
            config, "redis_url", "redis://localhost:6379/0"
        )
        self.redis_client: redis.Redis | None = None
        self.consumer_group = "kiro2_consumers"
        self.consumer_name = f"consumer_{uuid.uuid4().hex[:8]}"
        self.running = False

        # Queue configuration
        self.queue_configs = self._get_queue_configs()

        # Consumer tasks
        self.consumer_tasks: dict[QueueType, asyncio.Task] = {}
        self.metrics_collector = get_metrics_collector()

    def _get_queue_configs(self) -> dict[QueueType, dict[str, Any]]:
        """Get queue configurations"""
        return {
            QueueType.REAL_TIME: {
                "stream_name": "queue:real_time",
                "max_len": 10000,
                "consumer_count": 3,
                "batch_size": 1,
                "block_time": 100,  # 100ms
            },
            QueueType.AUTHENTICATION: {
                "stream_name": "queue:authentication",
                "max_len": 5000,
                "consumer_count": 2,
                "batch_size": 5,
                "block_time": 1000,
            },
            QueueType.EXAM_PROCESSING: {
                "stream_name": "queue:exam_processing",
                "max_len": 20000,
                "consumer_count": 4,
                "batch_size": 1,
                "block_time": 500,
            },
            QueueType.NOTIFICATIONS: {
                "stream_name": "queue:notifications",
                "max_len": 50000,
                "consumer_count": 2,
                "batch_size": 10,
                "block_time": 2000,
            },
            QueueType.CONTENT_PROCESSING: {
                "stream_name": "queue:content",
                "max_len": 10000,
                "consumer_count": 2,
                "batch_size": 3,
                "block_time": 5000,
            },
            QueueType.ANALYTICS: {
                "stream_name": "queue:analytics",
                "max_len": 100000,
                "consumer_count": 1,
                "batch_size": 20,
                "block_time": 10000,
            },
            QueueType.BATCH_PROCESSING: {
                "stream_name": "queue:batch",
                "max_len": 5000,
                "consumer_count": 1,
                "batch_size": 50,
                "block_time": 30000,
            },
            QueueType.CLEANUP: {
                "stream_name": "queue:cleanup",
                "max_len": 1000,
                "consumer_count": 1,
                "batch_size": 10,
                "block_time": 60000,
            },
            QueueType.MAINTENANCE: {
                "stream_name": "queue:maintenance",
                "max_len": 1000,
                "consumer_count": 1,
                "batch_size": 5,
                "block_time": 60000,
            },
        }

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url, decode_responses=False, max_connections=20
            )

            # Test connection
            await self.redis_client.ping()

            # Initialize consumer groups
            await self._initialize_consumer_groups()

            logger.info(
                "Redis Message Queue connected",
                message_tr="Redis Mesaj Kuyruğu bağlandı",
            )

        except Exception as e:
            logger.error(f"Redis Message Queue connection failed: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis Message Queue disconnected")

    async def _initialize_consumer_groups(self):
        """Initialize consumer groups for all queues"""
        for queue_type, config in self.queue_configs.items():
            stream_name = config["stream_name"]
            try:
                await self.redis_client.xgroup_create(
                    stream_name, self.consumer_group, id="0", mkstream=True
                )
                logger.debug(f"Consumer group created for {stream_name}")
            except Exception as e:
                if "BUSYGROUP" not in str(e):
                    logger.error(
                        f"Failed to create consumer group for {stream_name}: {e}"
                    )

    async def enqueue(self, message: QueueMessage) -> bool:
        """Add message to queue"""
        try:
            if not self.redis_client:
                await self.connect()

            config = self.queue_configs[message.queue_type]
            stream_name = config["stream_name"]

            # Serialize message
            serialized_data = {
                "data": json.dumps(message.to_dict()),
                "priority": message.priority.value,
                "user_id": str(message.user_id) if message.user_id else "",
                "correlation_id": message.correlation_id,
            }

            # Add to Redis stream
            message_id = await self.redis_client.xadd(
                stream_name, serialized_data, maxlen=config["max_len"]
            )

            # Record metrics
            self.metrics_collector.record_metric(
                MetricType.QUEUE_ENQUEUE,
                1,
                metadata={
                    "queue_type": message.queue_type.value,
                    "priority": message.priority.value,
                },
            )

            logger.debug(f"Message enqueued: {message.id} to {stream_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return False

    async def start_consumers(self):
        """Start consumer tasks for all queues"""
        if self.running:
            return

        self.running = True

        for queue_type, config in self.queue_configs.items():
            # Start multiple consumers per queue based on configuration
            consumer_count = config["consumer_count"]
            for i in range(consumer_count):
                consumer_name = f"{self.consumer_name}_{queue_type.value}_{i}"
                task = asyncio.create_task(
                    self._consume_queue(queue_type, consumer_name)
                )
                self.consumer_tasks[f"{queue_type.value}_{i}"] = task

        logger.info(
            f"Started {len(self.consumer_tasks)} consumer tasks",
            message_tr=f"{len(self.consumer_tasks)} tüketici görevi başlatıldı",
        )

    async def stop_consumers(self):
        """Stop all consumer tasks"""
        self.running = False

        # Cancel all consumer tasks
        for task in self.consumer_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self.consumer_tasks:
            await asyncio.gather(*self.consumer_tasks.values(), return_exceptions=True)

        self.consumer_tasks.clear()
        logger.info("All consumer tasks stopped")

    async def _consume_queue(self, queue_type: QueueType, consumer_name: str):
        """Consume messages from a specific queue"""
        config = self.queue_configs[queue_type]
        stream_name = config["stream_name"]
        batch_size = config["batch_size"]
        block_time = config["block_time"]

        logger.debug(f"Consumer started: {consumer_name} for {stream_name}")

        while self.running:
            try:
                # Read messages from stream
                messages = await self.redis_client.xreadgroup(
                    self.consumer_group,
                    consumer_name,
                    {stream_name: ">"},
                    count=batch_size,
                    block=block_time,
                )

                if not messages:
                    continue

                # Process messages
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        try:
                            await self._process_message(
                                msg_id, fields, stream_name, queue_type
                            )
                        except Exception as e:
                            logger.error(f"Message processing error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer error for {consumer_name}: {e}")
                await asyncio.sleep(5.0)  # Back off on error

    async def _process_message(
        self,
        msg_id: bytes,
        fields: dict[bytes, bytes],
        stream_name: str,
        queue_type: QueueType,
    ):
        """Process a single message"""
        try:
            # Deserialize message
            data = json.loads(fields[b"data"].decode("utf-8"))
            message = QueueMessage.from_dict(data)

            # Process based on queue type
            success = await self._handle_message_by_type(message, queue_type)

            if success:
                # Acknowledge message
                await self.redis_client.xack(stream_name, self.consumer_group, msg_id)

                # Record success metric
                self.metrics_collector.record_metric(
                    MetricType.QUEUE_PROCESS_SUCCESS,
                    1,
                    metadata={"queue_type": queue_type.value},
                )

                logger.debug(f"Message processed successfully: {message.id}")
            else:
                # Handle failure (could implement retry logic)
                logger.error(f"Message processing failed: {message.id}")

                # Record failure metric
                self.metrics_collector.record_metric(
                    MetricType.QUEUE_PROCESS_FAILURE,
                    1,
                    metadata={"queue_type": queue_type.value},
                )

        except Exception as e:
            logger.error(f"Message processing error: {e}")

    async def _handle_message_by_type(
        self, message: QueueMessage, queue_type: QueueType
    ) -> bool:
        """Handle message based on queue type"""
        try:
            if queue_type == QueueType.REAL_TIME:
                return await self._handle_real_time_message(message)
            if queue_type == QueueType.AUTHENTICATION:
                return await self._handle_auth_message(message)
            if queue_type == QueueType.EXAM_PROCESSING:
                return await self._handle_exam_message(message)
            if queue_type == QueueType.NOTIFICATIONS:
                return await self._handle_notification_message(message)
            if queue_type == QueueType.CONTENT_PROCESSING:
                return await self._handle_content_message(message)
            if queue_type == QueueType.ANALYTICS:
                return await self._handle_analytics_message(message)
            if queue_type == QueueType.BATCH_PROCESSING:
                return await self._handle_batch_message(message)
            if queue_type == QueueType.CLEANUP:
                return await self._handle_cleanup_message(message)
            if queue_type == QueueType.MAINTENANCE:
                return await self._handle_maintenance_message(message)
            logger.warning(f"Unknown queue type: {queue_type}")
            return False

        except Exception as e:
            logger.error(f"Message handler error for {queue_type}: {e}")
            return False

    async def _handle_real_time_message(self, message: QueueMessage) -> bool:
        """Handle real-time messages (WebSocket, live updates)"""
        try:
            action = message.payload.get("action")

            if action == "websocket_broadcast":
                # Broadcast to WebSocket connections
                await self._broadcast_websocket_message(message)
            elif action == "live_exam_update":
                # Update live exam data
                await self._handle_live_exam_update(message)
            elif action == "real_time_notification":
                # Send real-time notification
                await self._send_real_time_notification(message)

            return True

        except Exception as e:
            logger.error(f"Real-time message handling error: {e}")
            return False

    async def _handle_auth_message(self, message: QueueMessage) -> bool:
        """Handle authentication-related messages"""
        try:
            action = message.payload.get("action")

            if action == "user_login":
                # Process user login
                await self._process_user_login(message)
            elif action == "token_refresh":
                # Refresh user token
                await self._refresh_user_token(message)
            elif action == "logout_all_sessions":
                # Logout user from all sessions
                await self._logout_all_sessions(message)

            return True

        except Exception as e:
            logger.error(f"Auth message handling error: {e}")
            return False

    async def _handle_exam_message(self, message: QueueMessage) -> bool:
        """Handle Turkish exam processing messages"""
        try:
            action = message.payload.get("action")
            exam_type = message.payload.get("exam_type", "").lower()

            if action == "process_exam_submission":
                # Process TYT/AYT exam submission
                await self._process_exam_submission(message, exam_type)
            elif action == "calculate_exam_results":
                # Calculate exam results and ranking
                await self._calculate_exam_results(message, exam_type)
            elif action == "generate_exam_report":
                # Generate detailed exam report
                await self._generate_exam_report(message, exam_type)
            elif action == "update_student_progress":
                # Update student learning progress
                await self._update_student_progress(message)

            return True

        except Exception as e:
            logger.error(f"Exam message handling error: {e}")
            return False

    async def _handle_notification_message(self, message: QueueMessage) -> bool:
        """Handle notification messages"""
        try:
            notification_type = message.payload.get("type")

            if notification_type == "email":
                await self._send_email_notification(message)
            elif notification_type == "sms":
                await self._send_sms_notification(message)
            elif notification_type == "push":
                await self._send_push_notification(message)
            elif notification_type == "exam_reminder":
                await self._send_exam_reminder(message)

            return True

        except Exception as e:
            logger.error(f"Notification handling error: {e}")
            return False

    async def _handle_content_message(self, message: QueueMessage) -> bool:
        """Handle content processing messages"""
        try:
            action = message.payload.get("action")

            if action == "generate_questions":
                await self._generate_questions(message)
            elif action == "analyze_content":
                await self._analyze_content(message)
            elif action == "update_content_metadata":
                await self._update_content_metadata(message)

            return True

        except Exception as e:
            logger.error(f"Content processing error: {e}")
            return False

    async def _handle_analytics_message(self, message: QueueMessage) -> bool:
        """Handle analytics messages"""
        try:
            action = message.payload.get("action")

            if action == "calculate_learning_analytics":
                await self._calculate_learning_analytics(message)
            elif action == "update_progress_tracking":
                await self._update_progress_tracking(message)
            elif action == "generate_performance_report":
                await self._generate_performance_report(message)

            return True

        except Exception as e:
            logger.error(f"Analytics processing error: {e}")
            return False

    async def _handle_batch_message(self, message: QueueMessage) -> bool:
        """Handle batch processing messages"""
        try:
            action = message.payload.get("action")

            if action == "bulk_user_import":
                await self._bulk_user_import(message)
            elif action == "generate_monthly_reports":
                await self._generate_monthly_reports(message)
            elif action == "backup_database":
                await self._backup_database(message)

            return True

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return False

    async def _handle_cleanup_message(self, message: QueueMessage) -> bool:
        """Handle cleanup messages"""
        try:
            action = message.payload.get("action")

            if action == "clean_expired_sessions":
                await self._clean_expired_sessions(message)
            elif action == "clean_old_logs":
                await self._clean_old_logs(message)
            elif action == "optimize_database":
                await self._optimize_database(message)

            return True

        except Exception as e:
            logger.error(f"Cleanup processing error: {e}")
            return False

    async def _handle_maintenance_message(self, message: QueueMessage) -> bool:
        """Handle maintenance messages"""
        try:
            action = message.payload.get("action")

            if action == "system_health_check":
                await self._system_health_check(message)
            elif action == "update_system_configuration":
                await self._update_system_configuration(message)
            elif action == "restart_services":
                await self._restart_services(message)

            return True

        except Exception as e:
            logger.error(f"Maintenance processing error: {e}")
            return False

    # Placeholder implementations for message handlers
    # These would be implemented with actual business logic

    async def _broadcast_websocket_message(self, message: QueueMessage):
        """Broadcast message to WebSocket connections"""
        # Implementation would integrate with WebSocket manager
        logger.debug("Broadcasting WebSocket message")

    async def _handle_live_exam_update(self, message: QueueMessage):
        """Handle live exam updates"""
        logger.debug("Handling live exam update")

    async def _send_real_time_notification(self, message: QueueMessage):
        """Send real-time notification"""
        logger.debug("Sending real-time notification")

    async def _process_user_login(self, message: QueueMessage):
        """Process user login"""
        logger.debug("Processing user login")

    async def _refresh_user_token(self, message: QueueMessage):
        """Refresh user token"""
        logger.debug("Refreshing user token")

    async def _logout_all_sessions(self, message: QueueMessage):
        """Logout user from all sessions"""
        logger.debug("Logging out all sessions")

    async def _process_exam_submission(self, message: QueueMessage, exam_type: str):
        """Process exam submission"""
        logger.info(
            f"Processing {exam_type.upper()} exam submission for user {message.user_id}",
            message_tr=f"Kullanıcı {message.user_id} için {exam_type.upper()} sınavı işleniyor",
        )

    async def _calculate_exam_results(self, message: QueueMessage, exam_type: str):
        """Calculate exam results"""
        logger.info(f"Calculating {exam_type.upper()} results")

    async def _generate_exam_report(self, message: QueueMessage, exam_type: str):
        """Generate exam report"""
        logger.info(f"Generating {exam_type.upper()} report")

    async def _update_student_progress(self, message: QueueMessage):
        """Update student progress"""
        logger.debug("Updating student progress")

    async def _send_email_notification(self, message: QueueMessage):
        """Send email notification"""
        logger.debug("Sending email notification")

    async def _send_sms_notification(self, message: QueueMessage):
        """Send SMS notification"""
        logger.debug("Sending SMS notification")

    async def _send_push_notification(self, message: QueueMessage):
        """Send push notification"""
        logger.debug("Sending push notification")

    async def _send_exam_reminder(self, message: QueueMessage):
        """Send exam reminder"""
        logger.info(
            "Sending exam reminder", message_tr="Sınav hatırlatması gönderiliyor"
        )

    async def _generate_questions(self, message: QueueMessage):
        """Generate questions"""
        logger.debug("Generating questions")

    async def _analyze_content(self, message: QueueMessage):
        """Analyze content"""
        logger.debug("Analyzing content")

    async def _update_content_metadata(self, message: QueueMessage):
        """Update content metadata"""
        logger.debug("Updating content metadata")

    async def _calculate_learning_analytics(self, message: QueueMessage):
        """Calculate learning analytics"""
        logger.debug("Calculating learning analytics")

    async def _update_progress_tracking(self, message: QueueMessage):
        """Update progress tracking"""
        logger.debug("Updating progress tracking")

    async def _generate_performance_report(self, message: QueueMessage):
        """Generate performance report"""
        logger.debug("Generating performance report")

    async def _bulk_user_import(self, message: QueueMessage):
        """Bulk user import"""
        logger.debug("Processing bulk user import")

    async def _generate_monthly_reports(self, message: QueueMessage):
        """Generate monthly reports"""
        logger.debug("Generating monthly reports")

    async def _backup_database(self, message: QueueMessage):
        """Backup database"""
        logger.info(
            "Creating database backup", message_tr="Veritabanı yedeği oluşturuluyor"
        )

    async def _clean_expired_sessions(self, message: QueueMessage):
        """Clean expired sessions"""
        logger.debug("Cleaning expired sessions")

    async def _clean_old_logs(self, message: QueueMessage):
        """Clean old logs"""
        logger.debug("Cleaning old logs")

    async def _optimize_database(self, message: QueueMessage):
        """Optimize database"""
        logger.debug("Optimizing database")

    async def _system_health_check(self, message: QueueMessage):
        """System health check"""
        logger.debug("Performing system health check")

    async def _update_system_configuration(self, message: QueueMessage):
        """Update system configuration"""
        logger.debug("Updating system configuration")

    async def _restart_services(self, message: QueueMessage):
        """Restart services"""
        logger.info("Restarting services", message_tr="Servisler yeniden başlatılıyor")

    async def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics"""
        try:
            stats = {}

            for queue_type, config in self.queue_configs.items():
                stream_name = config["stream_name"]

                # Get stream info
                try:
                    info = await self.redis_client.xinfo_stream(stream_name)
                    stats[queue_type.value] = {
                        "length": info.get("length", 0),
                        "groups": info.get("groups", 0),
                        "first_entry": info.get("first-entry"),
                        "last_entry": info.get("last-entry"),
                    }
                except Exception as e:
                    stats[queue_type.value] = {"error": str(e)}

            return {
                "running": self.running,
                "consumer_tasks": len(self.consumer_tasks),
                "queue_stats": stats,
            }

        except Exception as e:
            logger.error(f"Queue stats error: {e}")
            return {"error": str(e)}


class BackgroundJobProcessor:
    """Background job processor with scheduling and monitoring"""

    def __init__(self, message_queue: RedisMessageQueue):
        self.message_queue = message_queue
        self.jobs: dict[str, BackgroundJob] = {}
        self.job_handlers: dict[str, Callable] = {}
        self.scheduled_jobs: dict[str, asyncio.Task] = {}
        self.running = False
        self.scheduler_task: asyncio.Task | None = None

    def register_job_handler(self, job_type: str, handler: Callable):
        """Register a job handler"""
        self.job_handlers[job_type] = handler
        logger.debug(f"Registered job handler: {job_type}")

    async def schedule_job(
        self,
        job_type: str,
        function_name: str,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        queue_type: QueueType = QueueType.BATCH_PROCESSING,
        priority: QueuePriority = QueuePriority.NORMAL,
        delay_seconds: int = 0,
        scheduled_at: datetime | None = None,
        user_id: int | None = None,
        **metadata,
    ) -> str:
        """Schedule a background job"""

        job = BackgroundJob(
            id=str(uuid.uuid4()),
            job_type=job_type,
            function_name=function_name,
            args=args or [],
            kwargs=kwargs or {},
            queue_type=queue_type,
            priority=priority,
            status=JobStatus.PENDING
            if delay_seconds == 0 and not scheduled_at
            else JobStatus.SCHEDULED,
            created_at=datetime.now(UTC),
            user_id=user_id,
            metadata=metadata,
        )

        self.jobs[job.id] = job

        if scheduled_at or delay_seconds > 0:
            # Schedule for later execution
            if not scheduled_at:
                scheduled_at = datetime.now(UTC) + timedelta(seconds=delay_seconds)

            # Create scheduler task
            self.scheduled_jobs[job.id] = asyncio.create_task(
                self._schedule_delayed_job(job, scheduled_at)
            )
        else:
            # Execute immediately
            await self._enqueue_job(job)

        return job.id

    async def _schedule_delayed_job(self, job: BackgroundJob, scheduled_at: datetime):
        """Schedule a job for delayed execution"""
        try:
            # Wait until scheduled time
            now = datetime.now(UTC)
            if scheduled_at > now:
                delay = (scheduled_at - now).total_seconds()
                await asyncio.sleep(delay)

            # Enqueue the job
            await self._enqueue_job(job)

        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
        except Exception as e:
            logger.error(f"Scheduled job error: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            # Clean up
            if job.id in self.scheduled_jobs:
                del self.scheduled_jobs[job.id]

    async def _enqueue_job(self, job: BackgroundJob):
        """Enqueue a job for processing"""
        try:
            message = QueueMessage(
                id=str(uuid.uuid4()),
                queue_type=job.queue_type,
                payload={
                    "job_id": job.id,
                    "job_type": job.job_type,
                    "function_name": job.function_name,
                    "args": job.args,
                    "kwargs": job.kwargs,
                },
                priority=job.priority,
                created_at=datetime.now(UTC),
                user_id=job.user_id,
                correlation_id=job.id,
                metadata=job.metadata,
            )

            success = await self.message_queue.enqueue(message)
            if success:
                job.status = JobStatus.PENDING
                logger.debug(f"Job enqueued: {job.id}")
            else:
                job.status = JobStatus.FAILED
                job.error = "Failed to enqueue job"

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            logger.error(f"Job enqueue error: {e}")

    def get_job_status(self, job_id: str) -> BackgroundJob | None:
        """Get job status"""
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job"""
        if job_id in self.scheduled_jobs:
            self.scheduled_jobs[job_id].cancel()
            del self.scheduled_jobs[job_id]

            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.CANCELLED

            return True
        return False

    def get_job_stats(self) -> dict[str, Any]:
        """Get job processing statistics"""
        status_counts = defaultdict(int)
        for job in self.jobs.values():
            status_counts[job.status.value] += 1

        return {
            "total_jobs": len(self.jobs),
            "scheduled_jobs": len(self.scheduled_jobs),
            "status_breakdown": dict(status_counts),
            "registered_handlers": list(self.job_handlers.keys()),
        }


# Global instances
_message_queue: RedisMessageQueue | None = None
_job_processor: BackgroundJobProcessor | None = None


async def get_message_queue() -> RedisMessageQueue:
    """Get global message queue instance"""
    global _message_queue

    if _message_queue is None:
        _message_queue = RedisMessageQueue()
        await _message_queue.connect()
        await _message_queue.start_consumers()

    return _message_queue


async def get_job_processor() -> BackgroundJobProcessor:
    """Get global job processor instance"""
    global _job_processor

    if _job_processor is None:
        queue = await get_message_queue()
        _job_processor = BackgroundJobProcessor(queue)

    return _job_processor


# Utility functions
async def enqueue_message(
    queue_type: QueueType,
    payload: dict[str, Any],
    priority: QueuePriority = QueuePriority.NORMAL,
    user_id: int | None = None,
    **kwargs,
) -> bool:
    """Enqueue a message"""
    queue = await get_message_queue()

    message = QueueMessage(
        id=str(uuid.uuid4()),
        queue_type=queue_type,
        payload=payload,
        priority=priority,
        created_at=datetime.now(UTC),
        user_id=user_id,
        **kwargs,
    )

    return await queue.enqueue(message)


async def schedule_background_job(
    job_type: str,
    function_name: str,
    args: list[Any] = None,
    kwargs: dict[str, Any] = None,
    delay_seconds: int = 0,
    **job_kwargs,
) -> str:
    """Schedule a background job"""
    processor = await get_job_processor()
    return await processor.schedule_job(
        job_type, function_name, args, kwargs, delay_seconds=delay_seconds, **job_kwargs
    )


# Turkish exam specific utilities
async def enqueue_exam_processing(
    exam_type: str,  # 'tyt', 'ayt', 'yks'
    user_id: int,
    exam_data: dict[str, Any],
    priority: QueuePriority = QueuePriority.HIGH,
) -> bool:
    """Enqueue Turkish exam processing"""
    return await enqueue_message(
        queue_type=QueueType.EXAM_PROCESSING,
        payload={
            "action": "process_exam_submission",
            "exam_type": exam_type,
            "exam_data": exam_data,
        },
        priority=priority,
        user_id=user_id,
    )


async def enqueue_exam_reminder(
    user_id: int, exam_type: str, exam_date: datetime, reminder_type: str = "24h_before"
) -> bool:
    """Enqueue exam reminder notification"""
    return await enqueue_message(
        queue_type=QueueType.NOTIFICATIONS,
        payload={
            "type": "exam_reminder",
            "exam_type": exam_type,
            "exam_date": exam_date.isoformat(),
            "reminder_type": reminder_type,
            "message_tr": f"{exam_type.upper()} sınavınız {exam_date.strftime('%d.%m.%Y')} tarihinde",
        },
        priority=QueuePriority.HIGH,
        user_id=user_id,
    )
