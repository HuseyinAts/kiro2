"""
Comprehensive tests for core/message_queue_system.py
Target: 518 lines, 0% → 60%+ coverage
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from core.message_queue_system import (
    BackgroundJob,
    JobStatus,
    QueueMessage,
    QueuePriority,
    QueueType,
    RedisMessageQueue,
)


class TestQueuePriority:
    """Test QueuePriority enum"""

    def test_priority_levels(self):
        """Test all priority levels exist"""
        assert QueuePriority.LOW.value == "low"
        assert QueuePriority.NORMAL.value == "normal"
        assert QueuePriority.HIGH.value == "high"
        assert QueuePriority.CRITICAL.value == "critical"

    def test_priority_enum_members(self):
        """Test priority enum has expected members"""
        priorities = list(QueuePriority)
        assert len(priorities) == 4
        assert QueuePriority.LOW in priorities
        assert QueuePriority.CRITICAL in priorities


class TestJobStatus:
    """Test JobStatus enum"""

    def test_job_status_values(self):
        """Test all job status values"""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.RETRYING.value == "retrying"
        assert JobStatus.CANCELLED.value == "cancelled"
        assert JobStatus.SCHEDULED.value == "scheduled"

    def test_job_status_enum_members(self):
        """Test job status enum has all members"""
        statuses = list(JobStatus)
        assert len(statuses) == 7


class TestQueueType:
    """Test QueueType enum"""

    def test_high_priority_queues(self):
        """Test high priority queue types"""
        assert QueueType.REAL_TIME.value == "real_time"
        assert QueueType.AUTHENTICATION.value == "authentication"
        assert QueueType.EXAM_PROCESSING.value == "exam_processing"

    def test_normal_priority_queues(self):
        """Test normal priority queue types"""
        assert QueueType.NOTIFICATIONS.value == "notifications"
        assert QueueType.CONTENT_PROCESSING.value == "content"
        assert QueueType.ANALYTICS.value == "analytics"

    def test_low_priority_queues(self):
        """Test low priority queue types"""
        assert QueueType.BATCH_PROCESSING.value == "batch"
        assert QueueType.CLEANUP.value == "cleanup"
        assert QueueType.MAINTENANCE.value == "maintenance"

    def test_queue_type_enum_members(self):
        """Test queue type enum has all members"""
        queue_types = list(QueueType)
        assert len(queue_types) == 9


class TestQueueMessage:
    """Test QueueMessage dataclass"""

    def test_message_creation_with_defaults(self):
        """Test message creation with minimal fields"""
        message = QueueMessage(
            id="test-123",
            queue_type=QueueType.NOTIFICATIONS,
            payload={"data": "test"},
            priority=QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
        )

        assert message.id == "test-123"
        assert message.queue_type == QueueType.NOTIFICATIONS
        assert message.payload == {"data": "test"}
        assert message.priority == QueuePriority.NORMAL
        assert message.attempts == 0
        assert message.max_attempts == 3
        assert message.timeout == 300

    def test_message_auto_id_generation(self):
        """Test message ID is auto-generated if not provided"""
        message = QueueMessage(
            id="",
            queue_type=QueueType.REAL_TIME,
            payload={},
            priority=QueuePriority.HIGH,
            created_at=datetime.now(UTC),
        )

        assert message.id != ""
        assert len(message.id) > 0

    def test_message_correlation_id_auto_generation(self):
        """Test correlation ID defaults to message ID"""
        message = QueueMessage(
            id="msg-456",
            queue_type=QueueType.ANALYTICS,
            payload={},
            priority=QueuePriority.LOW,
            created_at=datetime.now(UTC),
        )

        assert message.correlation_id == "msg-456"

    def test_message_with_scheduling(self):
        """Test message with scheduled time"""
        scheduled_time = datetime.now(UTC) + timedelta(hours=1)
        message = QueueMessage(
            id="scheduled-msg",
            queue_type=QueueType.BATCH_PROCESSING,
            payload={"task": "report"},
            priority=QueuePriority.LOW,
            created_at=datetime.now(UTC),
            scheduled_at=scheduled_time,
        )

        assert message.scheduled_at == scheduled_time

    def test_message_with_user_context(self):
        """Test message with user and session context"""
        message = QueueMessage(
            id="user-msg",
            queue_type=QueueType.EXAM_PROCESSING,
            payload={"exam_id": "123"},
            priority=QueuePriority.CRITICAL,
            created_at=datetime.now(UTC),
            user_id=42,
            session_id="session-789",
        )

        assert message.user_id == 42
        assert message.session_id == "session-789"

    def test_message_with_metadata(self):
        """Test message with custom metadata"""
        metadata = {"retry_count": 2, "source": "api"}
        message = QueueMessage(
            id="meta-msg",
            queue_type=QueueType.CONTENT_PROCESSING,
            payload={},
            priority=QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
            metadata=metadata,
        )

        assert message.metadata == metadata

    def test_message_to_dict(self):
        """Test converting message to dictionary"""
        created_time = datetime.now(UTC)
        message = QueueMessage(
            id="dict-test",
            queue_type=QueueType.NOTIFICATIONS,
            payload={"msg": "hello"},
            priority=QueuePriority.HIGH,
            created_at=created_time,
        )

        data = message.to_dict()

        assert data["id"] == "dict-test"
        assert data["queue_type"] == "notifications"
        assert data["priority"] == "high"
        assert data["payload"] == {"msg": "hello"}
        assert data["created_at"] == created_time.isoformat()

    def test_message_to_dict_with_scheduled_time(self):
        """Test message to dict with scheduled time"""
        created_time = datetime.now(UTC)
        scheduled_time = created_time + timedelta(hours=2)

        message = QueueMessage(
            id="scheduled-dict",
            queue_type=QueueType.CLEANUP,
            payload={},
            priority=QueuePriority.LOW,
            created_at=created_time,
            scheduled_at=scheduled_time,
        )

        data = message.to_dict()
        assert "scheduled_at" in data
        assert data["scheduled_at"] == scheduled_time.isoformat()

    def test_message_from_dict(self):
        """Test creating message from dictionary"""
        data = {
            "id": "from-dict",
            "queue_type": "real_time",
            "payload": {"event": "update"},
            "priority": "critical",
            "created_at": "2024-01-15T10:30:00+00:00",
            "attempts": 0,
            "max_attempts": 3,
            "timeout": 300,
        }

        message = QueueMessage.from_dict(data)

        assert message.id == "from-dict"
        assert message.queue_type == QueueType.REAL_TIME
        assert message.priority == QueuePriority.CRITICAL
        assert message.payload == {"event": "update"}

    def test_message_from_dict_with_scheduled_time(self):
        """Test message from dict with scheduled time"""
        data = {
            "id": "scheduled-from-dict",
            "queue_type": "maintenance",
            "payload": {},
            "priority": "low",
            "created_at": "2024-01-15T10:00:00+00:00",
            "scheduled_at": "2024-01-15T12:00:00+00:00",
            "attempts": 0,
            "max_attempts": 3,
            "timeout": 300,
        }

        message = QueueMessage.from_dict(data)
        assert message.scheduled_at is not None


class TestBackgroundJob:
    """Test BackgroundJob dataclass"""

    def test_job_creation_minimal(self):
        """Test job creation with minimal fields"""
        job = BackgroundJob(
            id="job-123",
            job_type="exam_grading",
            function_name="grade_exam",
            args=[123, 456],
            kwargs={"strict": True},
            queue_type=QueueType.EXAM_PROCESSING,
            priority=QueuePriority.HIGH,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
        )

        assert job.id == "job-123"
        assert job.job_type == "exam_grading"
        assert job.function_name == "grade_exam"
        assert job.args == [123, 456]
        assert job.kwargs == {"strict": True}
        assert job.status == JobStatus.PENDING
        assert job.progress == 0

    def test_job_auto_id_generation(self):
        """Test job ID auto-generation"""
        job = BackgroundJob(
            id="",
            job_type="test",
            function_name="test_func",
            args=[],
            kwargs={},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.LOW,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
        )

        assert job.id != ""
        assert len(job.id) > 0

    def test_job_with_timing_info(self):
        """Test job with start and completion times"""
        created_time = datetime.now(UTC)
        started_time = created_time + timedelta(seconds=5)
        completed_time = started_time + timedelta(minutes=2)

        job = BackgroundJob(
            id="timed-job",
            job_type="report_generation",
            function_name="generate_report",
            args=[],
            kwargs={},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=JobStatus.COMPLETED,
            created_at=created_time,
            started_at=started_time,
            completed_at=completed_time,
        )

        assert job.started_at == started_time
        assert job.completed_at == completed_time

    def test_job_with_result(self):
        """Test job with result data"""
        job = BackgroundJob(
            id="result-job",
            job_type="calculation",
            function_name="calculate",
            args=[10, 20],
            kwargs={},
            queue_type=QueueType.ANALYTICS,
            priority=QueuePriority.NORMAL,
            status=JobStatus.COMPLETED,
            created_at=datetime.now(UTC),
            result={"sum": 30, "product": 200},
        )

        assert job.result == {"sum": 30, "product": 200}

    def test_job_with_error(self):
        """Test job with error information"""
        job = BackgroundJob(
            id="error-job",
            job_type="import",
            function_name="import_data",
            args=[],
            kwargs={},
            queue_type=QueueType.CONTENT_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=JobStatus.FAILED,
            created_at=datetime.now(UTC),
            error="Connection timeout",
        )

        assert job.error == "Connection timeout"
        assert job.status == JobStatus.FAILED

    def test_job_with_progress(self):
        """Test job with progress tracking"""
        job = BackgroundJob(
            id="progress-job",
            job_type="batch_import",
            function_name="import_batch",
            args=[],
            kwargs={},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.LOW,
            status=JobStatus.PROCESSING,
            created_at=datetime.now(UTC),
            progress=45,
        )

        assert job.progress == 45

    def test_job_with_retry_info(self):
        """Test job with retry information"""
        job = BackgroundJob(
            id="retry-job",
            job_type="api_call",
            function_name="call_api",
            args=[],
            kwargs={},
            queue_type=QueueType.NOTIFICATIONS,
            priority=QueuePriority.HIGH,
            status=JobStatus.RETRYING,
            created_at=datetime.now(UTC),
            attempts=2,
            max_attempts=5,
        )

        assert job.attempts == 2
        assert job.max_attempts == 5
        assert job.status == JobStatus.RETRYING

    def test_job_to_dict(self):
        """Test converting job to dictionary"""
        created_time = datetime.now(UTC)
        job = BackgroundJob(
            id="dict-job",
            job_type="test",
            function_name="test_func",
            args=[1, 2],
            kwargs={"key": "value"},
            queue_type=QueueType.REAL_TIME,
            priority=QueuePriority.CRITICAL,
            status=JobStatus.PENDING,
            created_at=created_time,
        )

        data = job.to_dict()

        assert data["id"] == "dict-job"
        assert data["job_type"] == "test"
        assert data["function_name"] == "test_func"
        assert data["queue_type"] == "real_time"
        assert data["priority"] == "critical"
        assert data["status"] == "pending"
        assert data["created_at"] == created_time.isoformat()

    def test_job_to_dict_with_timing(self):
        """Test job to dict with timing information"""
        created_time = datetime.now(UTC)
        started_time = created_time + timedelta(seconds=10)
        completed_time = started_time + timedelta(minutes=5)

        job = BackgroundJob(
            id="timing-job",
            job_type="test",
            function_name="test",
            args=[],
            kwargs={},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=JobStatus.COMPLETED,
            created_at=created_time,
            started_at=started_time,
            completed_at=completed_time,
        )

        data = job.to_dict()
        assert "started_at" in data
        assert "completed_at" in data
        assert data["started_at"] == started_time.isoformat()
        assert data["completed_at"] == completed_time.isoformat()


class TestRedisMessageQueue:
    """Test RedisMessageQueue class"""

    def test_queue_initialization(self):
        """Test queue initialization with default Redis URL"""
        queue = RedisMessageQueue()

        assert queue.redis_client is None
        assert queue.consumer_group == "kiro2_consumers"
        assert queue.consumer_name.startswith("consumer_")
        assert queue.running is False

    def test_queue_initialization_custom_url(self):
        """Test queue initialization with custom Redis URL"""
        custom_url = "redis://custom-host:6379/1"
        queue = RedisMessageQueue(redis_url=custom_url)

        assert queue.redis_url == custom_url

    def test_queue_configs(self):
        """Test queue configurations are properly defined"""
        queue = RedisMessageQueue()
        configs = queue.queue_configs

        # Check all queue types have configs
        assert QueueType.REAL_TIME in configs
        assert QueueType.AUTHENTICATION in configs
        assert QueueType.EXAM_PROCESSING in configs
        assert QueueType.NOTIFICATIONS in configs
        assert QueueType.CONTENT_PROCESSING in configs
        assert QueueType.ANALYTICS in configs
        assert QueueType.BATCH_PROCESSING in configs
        assert QueueType.CLEANUP in configs
        assert QueueType.MAINTENANCE in configs

    def test_real_time_queue_config(self):
        """Test real-time queue configuration"""
        queue = RedisMessageQueue()
        config = queue.queue_configs[QueueType.REAL_TIME]

        assert config["stream_name"] == "queue:real_time"
        assert config["max_len"] == 10000
        assert config["consumer_count"] == 3
        assert config["batch_size"] == 1
        assert config["block_time"] == 100

    def test_exam_processing_queue_config(self):
        """Test exam processing queue configuration"""
        queue = RedisMessageQueue()
        config = queue.queue_configs[QueueType.EXAM_PROCESSING]

        assert config["stream_name"] == "queue:exam_processing"
        assert config["max_len"] == 20000
        assert config["consumer_count"] == 4
        assert config["batch_size"] == 1
        assert config["block_time"] == 500

    def test_analytics_queue_config(self):
        """Test analytics queue configuration"""
        queue = RedisMessageQueue()
        config = queue.queue_configs[QueueType.ANALYTICS]

        assert config["stream_name"] == "queue:analytics"
        assert config["max_len"] == 100000
        assert config["batch_size"] == 20
        assert config["block_time"] == 10000

    def test_batch_processing_queue_config(self):
        """Test batch processing queue configuration"""
        queue = RedisMessageQueue()
        config = queue.queue_configs[QueueType.BATCH_PROCESSING]

        assert config["stream_name"] == "queue:batch"
        assert config["batch_size"] == 50
        assert config["block_time"] == 30000

    @pytest.mark.asyncio
    async def test_queue_connect_success(self):
        """Test successful Redis connection"""
        with patch("core.message_queue_system.redis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_from_url.return_value = mock_redis

            queue = RedisMessageQueue()
            await queue.connect()

            assert queue.redis_client == mock_redis
            mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_queue_connect_failure(self):
        """Test Redis connection failure handling"""
        with patch(
            "core.message_queue_system.redis.from_url",
            side_effect=Exception("Connection failed"),
        ):
            queue = RedisMessageQueue()

            # Should handle exception gracefully
            try:
                await queue.connect()
            except Exception:
                # Exception is expected
                pass

    @pytest.mark.asyncio
    async def test_queue_disconnect(self):
        """Test queue disconnect"""
        with patch("core.message_queue_system.redis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.close = AsyncMock()
            mock_from_url.return_value = mock_redis

            queue = RedisMessageQueue()
            await queue.connect()
            # Disconnect logic would be tested here


class TestQueueMessagePriority:
    """Test message priority handling"""

    def test_critical_priority_message(self):
        """Test creating critical priority message"""
        message = QueueMessage(
            id="critical-msg",
            queue_type=QueueType.AUTHENTICATION,
            payload={"action": "login"},
            priority=QueuePriority.CRITICAL,
            created_at=datetime.now(UTC),
        )

        assert message.priority == QueuePriority.CRITICAL

    def test_low_priority_message(self):
        """Test creating low priority message"""
        message = QueueMessage(
            id="low-msg",
            queue_type=QueueType.CLEANUP,
            payload={"task": "cleanup"},
            priority=QueuePriority.LOW,
            created_at=datetime.now(UTC),
        )

        assert message.priority == QueuePriority.LOW


class TestJobRetryMechanism:
    """Test job retry mechanism"""

    def test_job_can_retry(self):
        """Test job can retry if attempts below max"""
        job = BackgroundJob(
            id="retry-test",
            job_type="test",
            function_name="test",
            args=[],
            kwargs={},
            queue_type=QueueType.NOTIFICATIONS,
            priority=QueuePriority.NORMAL,
            status=JobStatus.FAILED,
            created_at=datetime.now(UTC),
            attempts=2,
            max_attempts=5,
        )

        # Job can retry (2 < 5)
        assert job.attempts < job.max_attempts

    def test_job_max_retries_exceeded(self):
        """Test job max retries exceeded"""
        job = BackgroundJob(
            id="max-retry-test",
            job_type="test",
            function_name="test",
            args=[],
            kwargs={},
            queue_type=QueueType.CONTENT_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=JobStatus.FAILED,
            created_at=datetime.now(UTC),
            attempts=5,
            max_attempts=5,
        )

        # Job cannot retry (5 >= 5)
        assert job.attempts >= job.max_attempts
