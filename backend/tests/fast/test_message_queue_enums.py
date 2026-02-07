"""
Fast unit tests for message queue system enums
Tests: QueuePriority, JobStatus, QueueType enums
Coverage target: +10-15% for core.message_queue_system
"""


class TestQueuePriority:
    """Test QueuePriority enum"""

    def test_queue_priority_values(self):
        """Test QueuePriority enum values"""
        from core.message_queue_system import QueuePriority

        assert QueuePriority.LOW.value == "low"
        assert QueuePriority.NORMAL.value == "normal"
        assert QueuePriority.HIGH.value == "high"
        assert QueuePriority.CRITICAL.value == "critical"

    def test_queue_priority_count(self):
        """Test QueuePriority has 4 levels"""
        from core.message_queue_system import QueuePriority

        priorities = list(QueuePriority)
        assert len(priorities) == 4


class TestJobStatus:
    """Test JobStatus enum"""

    def test_job_status_values(self):
        """Test JobStatus enum values"""
        from core.message_queue_system import JobStatus

        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.RETRYING.value == "retrying"
        assert JobStatus.CANCELLED.value == "cancelled"
        assert JobStatus.SCHEDULED.value == "scheduled"

    def test_job_status_count(self):
        """Test JobStatus has 7 statuses"""
        from core.message_queue_system import JobStatus

        statuses = list(JobStatus)
        assert len(statuses) == 7


class TestQueueType:
    """Test QueueType enum"""

    def test_queue_type_high_priority(self):
        """Test high priority queue types"""
        from core.message_queue_system import QueueType

        assert QueueType.REAL_TIME.value == "real_time"
        assert QueueType.AUTHENTICATION.value == "authentication"
        assert QueueType.EXAM_PROCESSING.value == "exam_processing"

    def test_queue_type_normal_priority(self):
        """Test normal priority queue types"""
        from core.message_queue_system import QueueType

        assert QueueType.NOTIFICATIONS.value == "notifications"
        assert QueueType.CONTENT_PROCESSING.value == "content"
        assert QueueType.ANALYTICS.value == "analytics"

    def test_queue_type_enum_exists(self):
        """Test QueueType enum exists"""
        from core.message_queue_system import QueueType

        assert QueueType is not None
        types = list(QueueType)
        assert len(types) >= 6
