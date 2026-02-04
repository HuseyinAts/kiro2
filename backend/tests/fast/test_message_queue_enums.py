"""
Fast unit tests for message queue system enums
Tests: QueuePriority, JobStatus, QueueType enums
Coverage target: +10-15% for core.message_queue_system
"""
import pytest


class TestQueuePriority:
    """Test QueuePriority enum"""

    def test_queue_priority_values(self):
        """Test QueuePriority enum values"""
        from core.message_queue_system import QueuePriority

        assert QueuePriority.LOW == "low"
        assert QueuePriority.NORMAL == "normal"
        assert QueuePriority.HIGH == "high"
        assert QueuePriority.CRITICAL == "critical"

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

        assert JobStatus.PENDING == "pending"
        assert JobStatus.PROCESSING == "processing"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"
        assert JobStatus.RETRYING == "retrying"
        assert JobStatus.CANCELLED == "cancelled"
        assert JobStatus.SCHEDULED == "scheduled"

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

        assert QueueType.REAL_TIME == "real_time"
        assert QueueType.AUTHENTICATION == "authentication"
        assert QueueType.EXAM_PROCESSING == "exam_processing"

    def test_queue_type_normal_priority(self):
        """Test normal priority queue types"""
        from core.message_queue_system import QueueType

        assert QueueType.NOTIFICATIONS == "notifications"
        assert QueueType.CONTENT_PROCESSING == "content"
        assert QueueType.ANALYTICS == "analytics"

    def test_queue_type_enum_exists(self):
        """Test QueueType enum exists"""
        from core.message_queue_system import QueueType

        assert QueueType is not None
        types = list(QueueType)
        assert len(types) >= 6
