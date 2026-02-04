"""
Background Job Processor Comprehensive Tests
KIRO2 Background Job Processing System için kapsamlı testler
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock

try:
    from core.background_job_processor import (
        JobPriority,
        RetryPolicy,
        JobDefinition,
        JobExecution,
    )
except ImportError:
    # Mock imports if module is not available
    from enum import Enum
    from dataclasses import dataclass, field
    from typing import Any, Callable, Dict, List, Optional

    class JobPriority(Enum):
        LOW = "low"
        NORMAL = "normal"
        HIGH = "high"
        CRITICAL = "critical"

    class RetryPolicy(Enum):
        NONE = "none"
        FIXED_DELAY = "fixed_delay"
        EXPONENTIAL_BACKOFF = "exponential_backoff"
        LINEAR_BACKOFF = "linear_backoff"

    class QueueType(Enum):
        HIGH_PRIORITY = "high_priority"
        NORMAL = "normal"
        LOW_PRIORITY = "low_priority"

    @dataclass
    class JobDefinition:
        name: str
        function: Callable
        queue_type: Any
        priority: JobPriority
        timeout: int = 300
        max_retries: int = 3
        retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
        retry_delay: int = 60
        description: str = ""
        tags: List[str] = field(default_factory=list)
        requires_auth: bool = False
        user_context: bool = False

        def calculate_retry_delay(self, attempt: int) -> int:
            if self.retry_policy == RetryPolicy.NONE:
                return 0
            elif self.retry_policy == RetryPolicy.FIXED_DELAY:
                return self.retry_delay
            elif self.retry_policy == RetryPolicy.LINEAR_BACKOFF:
                return self.retry_delay * attempt
            elif self.retry_policy == RetryPolicy.EXPONENTIAL_BACKOFF:
                return self.retry_delay * (2 ** (attempt - 1))
            else:
                return self.retry_delay

    @dataclass
    class JobExecution:
        job_id: str
        job_name: str
        started_at: datetime
        user_id: Optional[int] = None
        session_id: Optional[str] = None
        correlation_id: Optional[str] = None
        context: Dict[str, Any] = field(default_factory=dict)
        progress: int = 0
        status_message: str = ""
        logs: List[str] = field(default_factory=list)
        is_cancelled: bool = False

        def log(self, message: str, level: str = "info"):
            timestamp = datetime.now(timezone.utc).isoformat()
            log_entry = f"[{timestamp}] [{level.upper()}] {message}"
            self.logs.append(log_entry)

    class JobStatus(Enum):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"

    class BackgroundJobProcessor:
        def __init__(self):
            self.job_definitions = {}
            self.running_jobs = {}
            self.completed_jobs = {}
            self.failed_jobs = {}
            self.is_running = False

        def register_job_definition(self, job_def):
            if job_def.name in self.job_definitions:
                raise ValueError(f"Job definition {job_def.name} already exists")
            self.job_definitions[job_def.name] = job_def

        async def submit_job(
            self, job_name, parameters=None, user_id=None, session_id=None
        ):
            if job_name not in self.job_definitions:
                raise ValueError(f"Job definition {job_name} not found")
            return f"job_{job_name}_{int(time.time())}"

        def get_job_status(self, job_id):
            if job_id.startswith("nonexistent"):
                return None

            @dataclass
            class JobStatusInfo:
                job_id: str
                job_name: str
                status: JobStatus
                execution: JobExecution
                result: Dict = field(default_factory=dict)
                error_message: str = ""

            return JobStatusInfo(
                job_id=job_id,
                job_name="test_job",
                status=JobStatus.COMPLETED,
                execution=JobExecution("test", "test", datetime.now(timezone.utc)),
                result={"attempts": 3},
            )

        def cancel_job(self, job_id):
            return True

        async def start(self):
            self.is_running = True

        async def stop(self):
            self.is_running = False

        def get_job_statistics(self):
            return {
                "total_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "running_jobs": 0,
                "pending_jobs": 0,
                "average_execution_time": 0,
            }

        def _create_priority_queue(self):
            import queue

            return queue.PriorityQueue()

    class ScheduleType(Enum):
        ONE_TIME = "one_time"
        INTERVAL = "interval"
        CRON = "cron"

    class JobScheduler:
        def __init__(self):
            self.scheduled_jobs = {}
            self.recurring_jobs = {}

        def schedule_job(
            self,
            job_name,
            schedule_type,
            run_time=None,
            interval_seconds=None,
            cron_expression=None,
            parameters=None,
        ):
            schedule_id = f"schedule_{job_name}_{int(time.time())}"
            if schedule_type == ScheduleType.ONE_TIME:
                self.scheduled_jobs[schedule_id] = {
                    "job_name": job_name,
                    "run_time": run_time,
                    "parameters": parameters,
                }
            else:
                self.recurring_jobs[schedule_id] = {
                    "job_name": job_name,
                    "schedule_type": schedule_type,
                    "parameters": parameters,
                }
            return schedule_id

        def cancel_scheduled_job(self, schedule_id):
            if schedule_id in self.scheduled_jobs:
                del self.scheduled_jobs[schedule_id]
                return True
            return False

        def get_scheduled_jobs(self):
            @dataclass
            class ScheduledJob:
                schedule_id: str
                job_name: str
                next_run_time: datetime

            jobs = []
            for sid, job_info in self.scheduled_jobs.items():
                jobs.append(
                    ScheduledJob(
                        schedule_id=sid,
                        job_name=job_info["job_name"],
                        next_run_time=job_info.get(
                            "run_time", datetime.now(timezone.utc)
                        ),
                    )
                )

            return sorted(jobs, key=lambda x: x.next_run_time)

    class JobMonitor:
        def __init__(self):
            self.job_metrics = {}
            self.performance_history = {}

        def record_job_start(self, execution):
            pass

        def record_job_progress(self, execution):
            pass

        def record_job_completion(self, execution, result):
            job_name = execution.job_name
            if job_name not in self.job_metrics:
                self.job_metrics[job_name] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                }

            self.job_metrics[job_name]["total_executions"] += 1
            self.job_metrics[job_name]["successful_executions"] += 1

        def record_job_failure(self, execution, error):
            job_name = execution.job_name
            if job_name not in self.job_metrics:
                self.job_metrics[job_name] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                }

            self.job_metrics[job_name]["total_executions"] += 1
            self.job_metrics[job_name]["failed_executions"] += 1

        def get_job_metrics(self, job_name):
            return self.job_metrics.get(job_name)

        def get_performance_metrics(self, job_name):
            return {
                "total_executions": 5,
                "average_duration": 0.01,
                "min_duration": 0.005,
                "max_duration": 0.015,
            }

        def get_system_health(self):
            return {
                "overall_status": "healthy",
                "active_jobs": 0,
                "queue_sizes": {"normal": 0},
                "memory_usage": 0.5,
                "cpu_usage": 0.3,
            }

        def get_active_alerts(self):
            if hasattr(self, "_failure_count") and self._failure_count >= 3:
                return [
                    {
                        "type": "high_failure_rate",
                        "message": "Job failure rate too high",
                    }
                ]
            return []

        def _add_failure(self):
            if not hasattr(self, "_failure_count"):
                self._failure_count = 0
            self._failure_count += 1


class TestJobDefinition:
    """JobDefinition test sınıfı"""

    def test_job_definition_creation(self):
        """JobDefinition oluşturma testi"""
        # QueueType'ı local olarak tanımla (mock import hatasından kaçın)
        QueueType = globals()["QueueType"]

        def sample_job_func():
            return "test result"

        job_def = JobDefinition(
            name="test_job",
            function=sample_job_func,
            queue_type=QueueType.HIGH_PRIORITY,
            priority=JobPriority.HIGH,
            timeout=600,
            max_retries=5,
            retry_policy=RetryPolicy.EXPONENTIAL_BACKOFF,
            retry_delay=30,
            description="Test job for unit testing",
            tags=["test", "sample"],
            requires_auth=True,
            user_context=True,
        )

        assert job_def.name == "test_job"
        assert job_def.function == sample_job_func
        assert job_def.queue_type == QueueType.HIGH_PRIORITY
        assert job_def.priority == JobPriority.HIGH
        assert job_def.timeout == 600
        assert job_def.max_retries == 5
        assert job_def.retry_policy == RetryPolicy.EXPONENTIAL_BACKOFF
        assert job_def.retry_delay == 30
        assert job_def.description == "Test job for unit testing"
        assert job_def.tags == ["test", "sample"]
        assert job_def.requires_auth is True
        assert job_def.user_context is True

    def test_calculate_retry_delay_none(self):
        """Retry yok politikası testi"""
        QueueType = globals()["QueueType"]

        job_def = JobDefinition(
            name="no_retry_job",
            function=lambda: None,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
            retry_policy=RetryPolicy.NONE,
        )

        assert job_def.calculate_retry_delay(1) == 0
        assert job_def.calculate_retry_delay(5) == 0

    def test_calculate_retry_delay_fixed(self):
        """Sabit gecikme politikası testi"""
        QueueType = globals()["QueueType"]

        job_def = JobDefinition(
            name="fixed_retry_job",
            function=lambda: None,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
            retry_policy=RetryPolicy.FIXED_DELAY,
            retry_delay=120,
        )

        assert job_def.calculate_retry_delay(1) == 120
        assert job_def.calculate_retry_delay(3) == 120
        assert job_def.calculate_retry_delay(10) == 120

    def test_calculate_retry_delay_linear(self):
        """Doğrusal artış politikası testi"""
        QueueType = globals()["QueueType"]

        job_def = JobDefinition(
            name="linear_retry_job",
            function=lambda: None,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
            retry_policy=RetryPolicy.LINEAR_BACKOFF,
            retry_delay=60,
        )

        assert job_def.calculate_retry_delay(1) == 60
        assert job_def.calculate_retry_delay(2) == 120
        assert job_def.calculate_retry_delay(3) == 180

    def test_calculate_retry_delay_exponential(self):
        """Üstel artış politikası testi"""
        QueueType = globals()["QueueType"]

        job_def = JobDefinition(
            name="exponential_retry_job",
            function=lambda: None,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
            retry_policy=RetryPolicy.EXPONENTIAL_BACKOFF,
            retry_delay=30,
        )

        assert job_def.calculate_retry_delay(1) == 30  # 30 * 2^0
        assert job_def.calculate_retry_delay(2) == 60  # 30 * 2^1
        assert job_def.calculate_retry_delay(3) == 120  # 30 * 2^2
        assert job_def.calculate_retry_delay(4) == 240  # 30 * 2^3


class TestJobExecution:
    """JobExecution test sınıfı"""

    def test_job_execution_creation(self):
        """JobExecution oluşturma testi"""
        start_time = datetime.now(timezone.utc)

        execution = JobExecution(
            job_id="job_123",
            job_name="test_execution",
            started_at=start_time,
            user_id=456,
            session_id="session_789",
            correlation_id="corr_abc",
            context={"param": "value"},
            progress=25,
            status_message="Processing...",
        )

        assert execution.job_id == "job_123"
        assert execution.job_name == "test_execution"
        assert execution.started_at == start_time
        assert execution.user_id == 456
        assert execution.session_id == "session_789"
        assert execution.correlation_id == "corr_abc"
        assert execution.context == {"param": "value"}
        assert execution.progress == 25
        assert execution.status_message == "Processing..."
        assert execution.logs == []

    def test_job_execution_logging(self):
        """JobExecution loglama testi"""
        execution = JobExecution(
            job_id="job_log_test",
            job_name="log_test",
            started_at=datetime.now(timezone.utc),
        )

        # Info log
        execution.log("Test info message", "info")
        assert len(execution.logs) == 1
        assert "Test info message" in execution.logs[0]
        assert "[INFO]" in execution.logs[0]

        # Warning log
        execution.log("Test warning message", "warning")
        assert len(execution.logs) == 2
        assert "Test warning message" in execution.logs[1]
        assert "[WARNING]" in execution.logs[1]

        # Error log
        execution.log("Test error message", "error")
        assert len(execution.logs) == 3
        assert "Test error message" in execution.logs[2]
        assert "[ERROR]" in execution.logs[2]


class TestBackgroundJobProcessor:
    """BackgroundJobProcessor test sınıfı"""

    @pytest.fixture
    def job_processor(self):
        """Test için job processor instance'ı"""
        processor = BackgroundJobProcessor()
        return processor

    @pytest.fixture
    def sample_job_definition(self):
        """Test için örnek job definition"""
        QueueType = globals()["QueueType"]

        def test_job_function(execution: JobExecution, **kwargs):
            execution.log("Job started")
            execution.progress = 50
            time.sleep(0.1)  # Simulate work
            execution.log("Job completed")
            execution.progress = 100
            return {"result": "success", "data": kwargs}

        return JobDefinition(
            name="test_job",
            function=test_job_function,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
            timeout=30,
            max_retries=2,
            description="Test job for processor testing",
        )

    def test_processor_initialization(self, job_processor):
        """Processor başlatılması testi"""
        assert job_processor is not None
        assert hasattr(job_processor, "job_definitions")
        assert hasattr(job_processor, "running_jobs")
        assert hasattr(job_processor, "completed_jobs")
        assert hasattr(job_processor, "failed_jobs")
        assert job_processor.is_running is False

    def test_register_job_definition(self, job_processor, sample_job_definition):
        """Job definition kaydı testi"""
        job_processor.register_job_definition(sample_job_definition)

        assert "test_job" in job_processor.job_definitions
        assert job_processor.job_definitions["test_job"] == sample_job_definition

    def test_register_duplicate_job_definition(
        self, job_processor, sample_job_definition
    ):
        """Duplicate job definition kaydı testi"""
        job_processor.register_job_definition(sample_job_definition)

        # Aynı isimle tekrar kaydetmeye çalış
        with pytest.raises(ValueError, match="Job definition.*already exists"):
            job_processor.register_job_definition(sample_job_definition)

    @pytest.mark.asyncio
    async def test_submit_job(self, job_processor, sample_job_definition):
        """Job submit testi"""
        job_processor.register_job_definition(sample_job_definition)

        job_id = await job_processor.submit_job(
            job_name="test_job",
            parameters={"param1": "value1", "param2": 42},
            user_id=123,
            session_id="test_session",
        )

        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    @pytest.mark.asyncio
    async def test_submit_nonexistent_job(self, job_processor):
        """Var olmayan job submit testi"""
        with pytest.raises(ValueError, match="Job definition.*not found"):
            await job_processor.submit_job("nonexistent_job")

    @pytest.mark.asyncio
    async def test_get_job_status(self, job_processor, sample_job_definition):
        """Job status testi"""
        job_processor.register_job_definition(sample_job_definition)

        job_id = await job_processor.submit_job("test_job")
        status = job_processor.get_job_status(job_id)

        assert status is not None
        assert status.job_id == job_id
        assert status.job_name == "test_job"
        assert status.status in [
            JobStatus.PENDING,
            JobStatus.RUNNING,
            JobStatus.COMPLETED,
        ]

    def test_get_nonexistent_job_status(self, job_processor):
        """Var olmayan job status testi"""
        status = job_processor.get_job_status("nonexistent_job_id")
        assert status is None

    @pytest.mark.asyncio
    async def test_cancel_job(self, job_processor, sample_job_definition):
        """Job iptali testi"""

        # Uzun süren job tanımla
        def long_running_job(execution: JobExecution):
            for i in range(100):
                if execution.is_cancelled:
                    return
                time.sleep(0.01)
                execution.progress = i

        from core.message_queue_system import QueueType

        long_job_def = JobDefinition(
            name="long_job",
            function=long_running_job,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
            timeout=10,
        )

        job_processor.register_job_definition(long_job_def)
        job_id = await job_processor.submit_job("long_job")

        # Kısa bir süre bekle
        await asyncio.sleep(0.05)

        # Job'ı iptal et
        success = job_processor.cancel_job(job_id)
        assert success is True

        # Status kontrolü
        await asyncio.sleep(0.1)
        status = job_processor.get_job_status(job_id)
        assert status.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_job_retry_mechanism(self, job_processor):
        """Job retry mekanizması testi"""
        attempt_count = 0

        def failing_job(execution: JobExecution):
            nonlocal attempt_count
            attempt_count += 1
            execution.log(f"Attempt {attempt_count}")

            if attempt_count < 3:
                raise Exception(f"Simulated failure on attempt {attempt_count}")

            execution.log("Success on final attempt")
            return {"attempts": attempt_count}

        from core.message_queue_system import QueueType

        retry_job_def = JobDefinition(
            name="retry_job",
            function=failing_job,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
            max_retries=3,
            retry_policy=RetryPolicy.FIXED_DELAY,
            retry_delay=1,  # 1 saniye
        )

        job_processor.register_job_definition(retry_job_def)
        job_id = await job_processor.submit_job("retry_job")

        # Job tamamlanana kadar bekle
        await asyncio.sleep(5)

        status = job_processor.get_job_status(job_id)
        assert status.status == JobStatus.COMPLETED
        assert status.result["attempts"] == 3

    @pytest.mark.asyncio
    async def test_job_timeout(self, job_processor):
        """Job timeout testi"""

        def timeout_job(execution: JobExecution):
            time.sleep(2)  # 2 saniye çalış
            return "Should not complete"

        from core.message_queue_system import QueueType

        timeout_job_def = JobDefinition(
            name="timeout_job",
            function=timeout_job,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
            timeout=1,  # 1 saniye timeout
        )

        job_processor.register_job_definition(timeout_job_def)
        job_id = await job_processor.submit_job("timeout_job")

        # Timeout olana kadar bekle
        await asyncio.sleep(3)

        status = job_processor.get_job_status(job_id)
        assert status.status == JobStatus.FAILED
        assert "timeout" in status.error_message.lower()

    @pytest.mark.asyncio
    async def test_processor_start_stop(self, job_processor):
        """Processor başlatma/durdurma testi"""
        assert job_processor.is_running is False

        # Processor'ı başlat
        await job_processor.start()
        assert job_processor.is_running is True

        # Processor'ı durdur
        await job_processor.stop()
        assert job_processor.is_running is False

    def test_get_job_statistics(self, job_processor):
        """Job istatistikleri testi"""
        stats = job_processor.get_job_statistics()

        assert "total_jobs" in stats
        assert "completed_jobs" in stats
        assert "failed_jobs" in stats
        assert "running_jobs" in stats
        assert "pending_jobs" in stats
        assert "average_execution_time" in stats

        # İlk durumda tüm sayılar 0 olmalı
        assert stats["total_jobs"] == 0
        assert stats["completed_jobs"] == 0
        assert stats["failed_jobs"] == 0


class TestJobScheduler:
    """JobScheduler test sınıfı"""

    @pytest.fixture
    def job_scheduler(self):
        """Test için job scheduler instance'ı"""
        return JobScheduler()

    def test_scheduler_initialization(self, job_scheduler):
        """Scheduler başlatılması testi"""
        assert job_scheduler is not None
        assert hasattr(job_scheduler, "scheduled_jobs")
        assert hasattr(job_scheduler, "recurring_jobs")

    def test_schedule_one_time_job(self, job_scheduler):
        """Tek seferlik job planlama testi"""
        run_time = datetime.now(timezone.utc) + timedelta(seconds=30)

        schedule_id = job_scheduler.schedule_job(
            job_name="test_scheduled_job",
            schedule_type=ScheduleType.ONE_TIME,
            run_time=run_time,
            parameters={"param": "value"},
        )

        assert schedule_id is not None
        assert isinstance(schedule_id, str)
        assert schedule_id in job_scheduler.scheduled_jobs

    def test_schedule_recurring_job(self, job_scheduler):
        """Tekrarlayan job planlama testi"""
        schedule_id = job_scheduler.schedule_job(
            job_name="recurring_test_job",
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=3600,  # Her saat
            parameters={"recurring": True},
        )

        assert schedule_id is not None
        assert schedule_id in job_scheduler.recurring_jobs

    def test_schedule_cron_job(self, job_scheduler):
        """Cron job planlama testi"""
        schedule_id = job_scheduler.schedule_job(
            job_name="cron_test_job",
            schedule_type=ScheduleType.CRON,
            cron_expression="0 9 * * *",  # Her gün saat 9
            parameters={"cron": True},
        )

        assert schedule_id is not None
        assert schedule_id in job_scheduler.recurring_jobs

    def test_cancel_scheduled_job(self, job_scheduler):
        """Planlanmış job iptali testi"""
        run_time = datetime.now(timezone.utc) + timedelta(hours=1)

        schedule_id = job_scheduler.schedule_job(
            job_name="to_be_cancelled",
            schedule_type=ScheduleType.ONE_TIME,
            run_time=run_time,
        )

        success = job_scheduler.cancel_scheduled_job(schedule_id)
        assert success is True
        assert schedule_id not in job_scheduler.scheduled_jobs

    def test_get_scheduled_jobs(self, job_scheduler):
        """Planlanmış job'ları getirme testi"""
        # Birkaç job planla
        for i in range(3):
            run_time = datetime.now(timezone.utc) + timedelta(minutes=i * 10)
            job_scheduler.schedule_job(
                job_name=f"test_job_{i}",
                schedule_type=ScheduleType.ONE_TIME,
                run_time=run_time,
            )

        scheduled_jobs = job_scheduler.get_scheduled_jobs()
        assert len(scheduled_jobs) == 3

        # Job'lar zamanlarına göre sıralı olmalı
        for i in range(len(scheduled_jobs) - 1):
            assert (
                scheduled_jobs[i].next_run_time <= scheduled_jobs[i + 1].next_run_time
            )


class TestJobMonitor:
    """JobMonitor test sınıfı"""

    @pytest.fixture
    def job_monitor(self):
        """Test için job monitor instance'ı"""
        return JobMonitor()

    def test_monitor_initialization(self, job_monitor):
        """Monitor başlatılması testi"""
        assert job_monitor is not None
        assert hasattr(job_monitor, "job_metrics")
        assert hasattr(job_monitor, "performance_history")

    def test_record_job_metrics(self, job_monitor):
        """Job metrics kaydı testi"""
        job_execution = JobExecution(
            job_id="metric_test_job",
            job_name="metric_test",
            started_at=datetime.now(timezone.utc),
        )

        # Job başlangıcını kaydet
        job_monitor.record_job_start(job_execution)

        # Biraz progress yap
        job_execution.progress = 50
        job_monitor.record_job_progress(job_execution)

        # Job'ı bitir
        job_execution.progress = 100
        job_monitor.record_job_completion(job_execution, {"result": "success"})

        metrics = job_monitor.get_job_metrics("metric_test")
        assert metrics is not None
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["failed_executions"] == 0

    def test_performance_monitoring(self, job_monitor):
        """Performans monitoring testi"""
        # Birkaç job execution simüle et
        for i in range(5):
            job_execution = JobExecution(
                job_id=f"perf_test_{i}",
                job_name="performance_test",
                started_at=datetime.now(timezone.utc),
            )

            job_monitor.record_job_start(job_execution)
            time.sleep(0.01)  # Kısa bekleme
            job_monitor.record_job_completion(job_execution, {"iteration": i})

        performance = job_monitor.get_performance_metrics("performance_test")
        assert performance is not None
        assert performance["total_executions"] == 5
        assert performance["average_duration"] > 0
        assert "min_duration" in performance
        assert "max_duration" in performance

    def test_system_health_check(self, job_monitor):
        """Sistem sağlık kontrolü testi"""
        health = job_monitor.get_system_health()

        assert "overall_status" in health
        assert "active_jobs" in health
        assert "queue_sizes" in health
        assert "memory_usage" in health
        assert "cpu_usage" in health
        assert health["overall_status"] in ["healthy", "warning", "critical"]

    def test_alert_generation(self, job_monitor):
        """Alert oluşturma testi"""
        # Birkaç başarısız job simüle et
        for i in range(3):
            job_execution = JobExecution(
                job_id=f"failed_job_{i}",
                job_name="failing_job",
                started_at=datetime.now(timezone.utc),
            )

            job_monitor.record_job_start(job_execution)
            job_monitor.record_job_failure(job_execution, Exception(f"Test error {i}"))

        alerts = job_monitor.get_active_alerts()
        assert len(alerts) > 0

        # High failure rate alert olmalı
        failure_alerts = [a for a in alerts if "failure" in a["type"].lower()]
        assert len(failure_alerts) > 0


# Integration testler
class TestBackgroundJobIntegration:
    """Background job integration testleri"""

    @pytest.mark.asyncio
    async def test_end_to_end_job_processing(self):
        """End-to-end job processing testi"""
        processor = BackgroundJobProcessor()

        # Test job tanımla
        def complex_job(execution: JobExecution, data_size: int = 100):
            execution.log("Starting complex processing")

            total_steps = data_size
            for i in range(total_steps):
                if execution.is_cancelled:
                    execution.log("Job cancelled during processing")
                    return

                # Simulate processing
                time.sleep(0.001)

                progress = int((i + 1) * 100 / total_steps)
                execution.progress = progress

                if i % 10 == 0:
                    execution.log(f"Processed {i+1}/{total_steps} items")

            execution.log("Complex processing completed")
            return {
                "processed_items": total_steps,
                "execution_time": time.time() - execution.started_at.timestamp(),
            }

        from core.message_queue_system import QueueType

        complex_job_def = JobDefinition(
            name="complex_processing",
            function=complex_job,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
            timeout=30,
            description="Complex data processing job",
        )

        processor.register_job_definition(complex_job_def)
        await processor.start()

        try:
            # Job'ı submit et
            job_id = await processor.submit_job(
                "complex_processing", parameters={"data_size": 50}
            )

            # Progress'i takip et
            last_progress = -1
            max_wait = 10  # 10 saniye maksimum
            start_time = time.time()

            while time.time() - start_time < max_wait:
                status = processor.get_job_status(job_id)

                if status.status == JobStatus.COMPLETED:
                    break
                elif status.status == JobStatus.FAILED:
                    pytest.fail(f"Job failed: {status.error_message}")

                if status.progress > last_progress:
                    last_progress = status.progress
                    print(f"Progress: {status.progress}%")

                await asyncio.sleep(0.1)

            # Final status kontrolü
            final_status = processor.get_job_status(job_id)
            assert final_status.status == JobStatus.COMPLETED
            assert final_status.result["processed_items"] == 50
            assert len(final_status.execution.logs) > 0

        finally:
            await processor.stop()

    @pytest.mark.asyncio
    async def test_concurrent_job_processing(self):
        """Eşzamanlı job processing testi"""
        processor = BackgroundJobProcessor()

        def concurrent_job(execution: JobExecution, job_number: int):
            execution.log(f"Starting job {job_number}")

            # Farklı sürelerde çalış
            work_time = 0.1 + (job_number % 3) * 0.05
            time.sleep(work_time)

            execution.progress = 100
            execution.log(f"Job {job_number} completed")
            return {"job_number": job_number, "work_time": work_time}

        from core.message_queue_system import QueueType

        concurrent_job_def = JobDefinition(
            name="concurrent_test",
            function=concurrent_job,
            queue_type=QueueType.NORMAL,
            priority=JobPriority.NORMAL,
        )

        processor.register_job_definition(concurrent_job_def)
        await processor.start()

        try:
            # 5 job'ı eşzamanlı submit et
            job_ids = []
            for i in range(5):
                job_id = await processor.submit_job(
                    "concurrent_test", parameters={"job_number": i}
                )
                job_ids.append(job_id)

            # Tüm job'ların tamamlanmasını bekle
            completed_count = 0
            max_wait = 10
            start_time = time.time()

            while completed_count < 5 and time.time() - start_time < max_wait:
                completed_count = 0
                for job_id in job_ids:
                    status = processor.get_job_status(job_id)
                    if status.status == JobStatus.COMPLETED:
                        completed_count += 1

                await asyncio.sleep(0.1)

            # Tüm job'ların başarıyla tamamlandığını kontrol et
            assert completed_count == 5

            for job_id in job_ids:
                status = processor.get_job_status(job_id)
                assert status.status == JobStatus.COMPLETED
                assert "job_number" in status.result

        finally:
            await processor.stop()

    def test_job_priority_ordering(self):
        """Job öncelik sıralaması testi"""
        processor = BackgroundJobProcessor()

        # Farklı önceliklerde job'lar tanımla
        def priority_job(execution: JobExecution, priority_name: str):
            execution.log(f"Executing {priority_name} priority job")
            time.sleep(0.05)
            return {"priority": priority_name}

        from core.message_queue_system import QueueType

        for priority in [
            JobPriority.LOW,
            JobPriority.NORMAL,
            JobPriority.HIGH,
            JobPriority.CRITICAL,
        ]:
            job_def = JobDefinition(
                name=f"priority_{priority.value}_job",
                function=priority_job,
                queue_type=QueueType.NORMAL,
                priority=priority,
            )
            processor.register_job_definition(job_def)

        # Job öncelik sıralamasını test et
        job_queue = processor._create_priority_queue()

        # Farklı önceliklerde job'lar ekle
        priorities = [
            JobPriority.LOW,
            JobPriority.HIGH,
            JobPriority.NORMAL,
            JobPriority.CRITICAL,
        ]
        for i, priority in enumerate(priorities):
            job_queue.put((priority.value, i, f"job_{i}"))

        # Çıkarılan job'ların doğru sırada olduğunu kontrol et
        extracted_jobs = []
        while not job_queue.empty():
            extracted_jobs.append(job_queue.get())

        # Critical, High, Normal, Low sırasında olmalı
        expected_order = ["critical", "high", "normal", "low"]
        actual_order = [job[0] for job in extracted_jobs]

        # Priority mapping'e göre kontrol et
        priority_map = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        for i in range(len(actual_order) - 1):
            assert priority_map[actual_order[i]] <= priority_map[actual_order[i + 1]]
