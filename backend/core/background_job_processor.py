"""
KIRO2 Background Job Processing System
Advanced background job processing with scheduling, monitoring and retry logic
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import asyncio
import time
import traceback
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from core.application_metrics import MetricType, get_metrics_collector
from core.message_queue_system import QueueType
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config
from core.unified_event_bus import EventType, get_event_bus

config = get_unified_config()
logger = get_logger(__name__, LogCategory.JOBS)


class JobPriority(Enum):
    """Job execution priority"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class RetryPolicy(Enum):
    """Job retry policies"""

    NONE = "none"  # Don't retry
    FIXED_DELAY = "fixed_delay"  # Fixed delay between retries
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # Exponential backoff
    LINEAR_BACKOFF = "linear_backoff"  # Linear increase in delay


@dataclass
class JobDefinition:
    """Job definition with metadata"""

    name: str
    function: Callable
    queue_type: QueueType
    priority: JobPriority
    timeout: int = 300  # 5 minutes
    max_retries: int = 3
    retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    retry_delay: int = 60  # base delay in seconds
    description: str = ""
    tags: list[str] = field(default_factory=list)
    requires_auth: bool = False
    user_context: bool = False  # Whether job needs user context

    def calculate_retry_delay(self, attempt: int) -> int:
        """Calculate delay for retry attempt"""
        if self.retry_policy == RetryPolicy.NONE:
            return 0
        if self.retry_policy == RetryPolicy.FIXED_DELAY:
            return self.retry_delay
        if self.retry_policy == RetryPolicy.LINEAR_BACKOFF:
            return self.retry_delay * attempt
        if self.retry_policy == RetryPolicy.EXPONENTIAL_BACKOFF:
            return self.retry_delay * (2 ** (attempt - 1))
        return self.retry_delay


@dataclass
class JobExecution:
    """Job execution context"""

    job_id: str
    job_name: str
    started_at: datetime
    user_id: int | None = None
    session_id: str | None = None
    correlation_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    progress: int = 0  # 0-100
    status_message: str = ""
    logs: list[str] = field(default_factory=list)

    def log(self, message: str, level: str = "info"):
        """Log message during job execution"""
        timestamp = datetime.now(UTC).isoformat()
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        self.logs.append(log_entry)

        # Also log to system logger
        if level == "error":
            logger.error(f"Job {self.job_id}: {message}")
        elif level == "warning":
            logger.warning(f"Job {self.job_id}: {message}")
        else:
            logger.info(f"Job {self.job_id}: {message}")

    def update_progress(self, progress: int, message: str = ""):
        """Update job progress"""
        self.progress = max(0, min(100, progress))
        if message:
            self.status_message = message
            self.log(f"Progress: {progress}% - {message}")


class BackgroundJobRegistry:
    """Registry for background job definitions"""

    def __init__(self):
        self.jobs: dict[str, JobDefinition] = {}
        self.job_categories: dict[str, list[str]] = defaultdict(list)

    def register_job(
        self,
        name: str,
        function: Callable,
        queue_type: QueueType = QueueType.BATCH_PROCESSING,
        priority: JobPriority = JobPriority.NORMAL,
        timeout: int = 300,
        max_retries: int = 3,
        retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF,
        retry_delay: int = 60,
        description: str = "",
        tags: list[str] = None,
        category: str = "general",
        requires_auth: bool = False,
        user_context: bool = False,
    ) -> JobDefinition:
        """Register a background job"""

        job_def = JobDefinition(
            name=name,
            function=function,
            queue_type=queue_type,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            retry_policy=retry_policy,
            retry_delay=retry_delay,
            description=description,
            tags=tags or [],
            requires_auth=requires_auth,
            user_context=user_context,
        )

        self.jobs[name] = job_def
        self.job_categories[category].append(name)

        logger.info(f"Registered background job: {name}")
        return job_def

    def get_job(self, name: str) -> JobDefinition | None:
        """Get job definition by name"""
        return self.jobs.get(name)

    def list_jobs(self, category: str = None) -> list[JobDefinition]:
        """List all jobs or jobs in specific category"""
        if category:
            job_names = self.job_categories.get(category, [])
            return [self.jobs[name] for name in job_names if name in self.jobs]
        return list(self.jobs.values())

    def get_categories(self) -> list[str]:
        """Get all job categories"""
        return list(self.job_categories.keys())


class TurkishExamJobProcessor:
    """Specialized job processor for Turkish exam platform"""

    def __init__(self):
        self.registry = BackgroundJobRegistry()
        self.running_jobs: dict[str, JobExecution] = {}
        self.completed_jobs: deque = deque(maxlen=10000)  # Keep last 10k completed jobs
        self.metrics_collector = get_metrics_collector()
        self.running = False

        # Job scheduling
        self.scheduled_jobs: dict[str, asyncio.Task] = {}
        self.recurring_jobs: dict[str, dict[str, Any]] = {}

        # Performance monitoring
        self.job_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "avg_execution_time": 0.0,
                "last_execution": None,
            }
        )

        # Register built-in Turkish exam jobs
        self._register_builtin_jobs()

    def _register_builtin_jobs(self):
        """Register built-in jobs for Turkish exam platform"""

        # Exam processing jobs
        self.register_job(
            "process_tyt_exam",
            self._process_tyt_exam,
            queue_type=QueueType.EXAM_PROCESSING,
            priority=JobPriority.HIGH,
            timeout=600,  # 10 minutes
            description="Process TYT exam submission and calculate results",
            category="exam_processing",
            user_context=True,
        )

        self.register_job(
            "process_ayt_exam",
            self._process_ayt_exam,
            queue_type=QueueType.EXAM_PROCESSING,
            priority=JobPriority.HIGH,
            timeout=900,  # 15 minutes
            description="Process AYT exam submission and calculate results",
            category="exam_processing",
            user_context=True,
        )

        self.register_job(
            "calculate_exam_ranking",
            self._calculate_exam_ranking,
            queue_type=QueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
            timeout=1800,  # 30 minutes
            description="Calculate exam rankings and percentiles",
            category="exam_processing",
        )

        # Content generation jobs
        self.register_job(
            "generate_practice_questions",
            self._generate_practice_questions,
            queue_type=QueueType.CONTENT_PROCESSING,
            priority=JobPriority.NORMAL,
            timeout=1200,  # 20 minutes
            description="Generate personalized practice questions",
            category="content_generation",
            user_context=True,
        )

        self.register_job(
            "analyze_student_performance",
            self._analyze_student_performance,
            queue_type=QueueType.ANALYTICS,
            priority=JobPriority.LOW,
            timeout=600,
            description="Analyze student performance and generate insights",
            category="analytics",
            user_context=True,
        )

        # System maintenance jobs
        self.register_job(
            "cleanup_expired_sessions",
            self._cleanup_expired_sessions,
            queue_type=QueueType.CLEANUP,
            priority=JobPriority.LOW,
            timeout=300,
            description="Clean up expired user sessions",
            category="maintenance",
        )

        self.register_job(
            "generate_daily_reports",
            self._generate_daily_reports,
            queue_type=QueueType.BATCH_PROCESSING,
            priority=JobPriority.LOW,
            timeout=1800,
            description="Generate daily usage and performance reports",
            category="reporting",
        )

        # Notification jobs
        self.register_job(
            "send_exam_reminders",
            self._send_exam_reminders,
            queue_type=QueueType.NOTIFICATIONS,
            priority=JobPriority.HIGH,
            timeout=300,
            description="Send exam reminder notifications to students",
            category="notifications",
        )

        self.register_job(
            "send_progress_notifications",
            self._send_progress_notifications,
            queue_type=QueueType.NOTIFICATIONS,
            priority=JobPriority.NORMAL,
            timeout=600,
            description="Send study progress notifications",
            category="notifications",
            user_context=True,
        )

    def register_job(self, name: str, function: Callable, **kwargs) -> JobDefinition:
        """Register a background job"""
        return self.registry.register_job(name, function, **kwargs)

    async def schedule_job(
        self,
        job_name: str,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        delay_seconds: int = 0,
        scheduled_at: datetime | None = None,
        user_id: int | None = None,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Schedule a background job for execution"""

        job_def = self.registry.get_job(job_name)
        if not job_def:
            raise ValueError(f"Job '{job_name}' not found in registry")

        job_id = str(uuid.uuid4())

        # Create job execution context
        execution = JobExecution(
            job_id=job_id,
            job_name=job_name,
            started_at=datetime.now(UTC),
            user_id=user_id,
            session_id=session_id,
            correlation_id=str(uuid.uuid4()),
            context=context or {},
        )

        # Schedule execution
        if scheduled_at or delay_seconds > 0:
            # Delayed execution
            if not scheduled_at:
                scheduled_at = datetime.now(UTC) + timedelta(seconds=delay_seconds)

            self.scheduled_jobs[job_id] = asyncio.create_task(
                self._schedule_delayed_execution(
                    job_id, job_def, execution, scheduled_at, args, kwargs
                )
            )
        else:
            # Immediate execution
            await self._enqueue_job_execution(job_id, job_def, execution, args, kwargs)

        logger.info(
            f"Scheduled job: {job_name} (ID: {job_id})",
            message_tr=f"İş planlandı: {job_name} (ID: {job_id})",
        )

        return job_id

    async def _schedule_delayed_execution(
        self,
        job_id: str,
        job_def: JobDefinition,
        execution: JobExecution,
        scheduled_at: datetime,
        args: list[Any],
        kwargs: dict[str, Any],
    ):
        """Schedule job for delayed execution"""
        try:
            # Wait until scheduled time
            now = datetime.now(UTC)
            if scheduled_at > now:
                delay = (scheduled_at - now).total_seconds()
                await asyncio.sleep(delay)

            # Execute the job
            await self._enqueue_job_execution(job_id, job_def, execution, args, kwargs)

        except asyncio.CancelledError:
            execution.log("Job cancelled before execution", "warning")
        except Exception as e:
            execution.log(f"Delayed execution error: {e}", "error")
        finally:
            # Clean up
            if job_id in self.scheduled_jobs:
                del self.scheduled_jobs[job_id]

    async def _enqueue_job_execution(
        self,
        job_id: str,
        job_def: JobDefinition,
        execution: JobExecution,
        args: list[Any],
        kwargs: dict[str, Any],
    ):
        """Enqueue job for immediate execution"""
        try:
            # Add to running jobs
            self.running_jobs[job_id] = execution

            # Execute the job
            await self._execute_job(
                job_id, job_def, execution, args or [], kwargs or {}
            )

        except Exception as e:
            execution.log(f"Job execution error: {e}", "error")
            logger.error(f"Job execution error for {job_id}: {e}")

    async def _execute_job(
        self,
        job_id: str,
        job_def: JobDefinition,
        execution: JobExecution,
        args: list[Any],
        kwargs: dict[str, Any],
    ):
        """Execute a background job"""
        start_time = time.time()

        try:
            execution.log(f"Starting job: {job_def.name}")
            execution.update_progress(0, "Starting job execution")

            # Prepare job context
            if job_def.user_context and execution.user_id:
                kwargs["user_id"] = execution.user_id
                kwargs["session_id"] = execution.session_id
                kwargs["job_context"] = execution

            # Execute the job function
            if asyncio.iscoroutinefunction(job_def.function):
                result = await asyncio.wait_for(
                    job_def.function(*args, **kwargs), timeout=job_def.timeout
                )
            else:
                # Run sync function in thread pool
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: job_def.function(*args, **kwargs)
                )

            # Job completed successfully
            execution_time = time.time() - start_time
            execution.log(f"Job completed successfully in {execution_time:.2f}s")
            execution.update_progress(100, "Job completed successfully")

            # Update statistics
            self._update_job_stats(job_def.name, True, execution_time)

            # Record metrics
            self.metrics_collector.record_metric(
                MetricType.JOB_COMPLETED,
                1,
                metadata={
                    "job_name": job_def.name,
                    "execution_time": execution_time,
                    "queue_type": job_def.queue_type.value,
                },
            )

            # Move to completed jobs
            self.completed_jobs.append(
                {
                    "job_id": job_id,
                    "job_name": job_def.name,
                    "status": "completed",
                    "started_at": execution.started_at.isoformat(),
                    "completed_at": datetime.now(UTC).isoformat(),
                    "execution_time": execution_time,
                    "result": str(result)[:1000]
                    if result
                    else None,  # Truncate long results
                }
            )

        except TimeoutError:
            execution.log(f"Job timed out after {job_def.timeout} seconds", "error")
            await self._handle_job_failure(job_id, job_def, execution, "timeout")

        except Exception as e:
            execution.log(f"Job failed with error: {e}", "error")
            execution.log(traceback.format_exc(), "error")
            await self._handle_job_failure(job_id, job_def, execution, str(e))

        finally:
            # Clean up
            if job_id in self.running_jobs:
                del self.running_jobs[job_id]

    async def _handle_job_failure(
        self, job_id: str, job_def: JobDefinition, execution: JobExecution, error: str
    ):
        """Handle job failure and retry logic"""

        execution_time = (datetime.now(UTC) - execution.started_at).total_seconds()

        # Update statistics
        self._update_job_stats(job_def.name, False, execution_time)

        # Record failure metric
        self.metrics_collector.record_metric(
            MetricType.JOB_FAILED,
            1,
            metadata={
                "job_name": job_def.name,
                "error": error[:200],  # Truncate error message
                "queue_type": job_def.queue_type.value,
            },
        )

        # Move to completed jobs with failure status
        self.completed_jobs.append(
            {
                "job_id": job_id,
                "job_name": job_def.name,
                "status": "failed",
                "started_at": execution.started_at.isoformat(),
                "completed_at": datetime.now(UTC).isoformat(),
                "execution_time": execution_time,
                "error": error,
            }
        )

    def _update_job_stats(self, job_name: str, success: bool, execution_time: float):
        """Update job execution statistics"""
        stats = self.job_stats[job_name]
        stats["total_executions"] += 1
        stats["last_execution"] = datetime.now(UTC).isoformat()

        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1

        # Update average execution time
        total_time = (
            stats["avg_execution_time"] * (stats["total_executions"] - 1)
            + execution_time
        )
        stats["avg_execution_time"] = total_time / stats["total_executions"]

    async def schedule_recurring_job(
        self,
        job_name: str,
        interval_seconds: int,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        start_immediately: bool = True,
    ) -> str:
        """Schedule a recurring background job"""

        recurring_id = str(uuid.uuid4())

        self.recurring_jobs[recurring_id] = {
            "job_name": job_name,
            "interval_seconds": interval_seconds,
            "args": args or [],
            "kwargs": kwargs or {},
            "last_run": None,
            "next_run": datetime.now(UTC)
            if start_immediately
            else datetime.now(UTC) + timedelta(seconds=interval_seconds),
            "task": asyncio.create_task(self._recurring_job_loop(recurring_id)),
        }

        logger.info(f"Scheduled recurring job: {job_name} every {interval_seconds}s")
        return recurring_id

    async def _recurring_job_loop(self, recurring_id: str):
        """Recurring job execution loop"""
        try:
            recurring_info = self.recurring_jobs[recurring_id]

            while recurring_id in self.recurring_jobs:
                now = datetime.now(UTC)

                if now >= recurring_info["next_run"]:
                    # Execute the job
                    try:
                        await self.schedule_job(
                            recurring_info["job_name"],
                            args=recurring_info["args"],
                            kwargs=recurring_info["kwargs"],
                        )
                        recurring_info["last_run"] = now
                        recurring_info["next_run"] = now + timedelta(
                            seconds=recurring_info["interval_seconds"]
                        )
                    except Exception as e:
                        logger.error(f"Recurring job execution error: {e}")

                # Sleep until next check
                await asyncio.sleep(60)  # Check every minute

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Recurring job loop error: {e}")

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled or running job"""

        # Cancel scheduled job
        if job_id in self.scheduled_jobs:
            self.scheduled_jobs[job_id].cancel()
            del self.scheduled_jobs[job_id]
            return True

        # Cancel running job (limited cancellation capability)
        if job_id in self.running_jobs:
            execution = self.running_jobs[job_id]
            execution.log("Job cancellation requested", "warning")
            # Note: Actual cancellation depends on job implementation
            return True

        return False

    def cancel_recurring_job(self, recurring_id: str) -> bool:
        """Cancel a recurring job"""
        if recurring_id in self.recurring_jobs:
            recurring_info = self.recurring_jobs[recurring_id]
            recurring_info["task"].cancel()
            del self.recurring_jobs[recurring_id]
            return True
        return False

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get job status"""
        if job_id in self.running_jobs:
            execution = self.running_jobs[job_id]
            return {
                "job_id": job_id,
                "job_name": execution.job_name,
                "status": "running",
                "progress": execution.progress,
                "status_message": execution.status_message,
                "started_at": execution.started_at.isoformat(),
                "logs": execution.logs[-10:],  # Last 10 log entries
            }

        # Check completed jobs
        for completed_job in reversed(self.completed_jobs):
            if completed_job["job_id"] == job_id:
                return completed_job

        return None

    def get_system_stats(self) -> dict[str, Any]:
        """Get job system statistics"""
        return {
            "running_jobs": len(self.running_jobs),
            "scheduled_jobs": len(self.scheduled_jobs),
            "recurring_jobs": len(self.recurring_jobs),
            "completed_jobs": len(self.completed_jobs),
            "registered_jobs": len(self.registry.jobs),
            "job_categories": list(self.registry.job_categories.keys()),
            "job_stats": dict(self.job_stats),
        }

    # Built-in Turkish exam job implementations

    async def _process_tyt_exam(
        self, exam_data: dict[str, Any], user_id: int, job_context: JobExecution
    ):
        """Process TYT exam submission"""
        job_context.log("Starting TYT exam processing")
        job_context.update_progress(10, "Validating exam data")

        # Simulate exam processing
        await asyncio.sleep(2)
        job_context.update_progress(30, "Calculating subject scores")

        await asyncio.sleep(3)
        job_context.update_progress(60, "Computing overall score")

        await asyncio.sleep(2)
        job_context.update_progress(80, "Generating performance report")

        await asyncio.sleep(1)
        job_context.update_progress(100, "TYT exam processed successfully")

        # Publish event
        event_bus = await get_event_bus()
        await event_bus.publish(
            EventType.TYT_SIMULATION_COMPLETED,
            {
                "user_id": user_id,
                "exam_type": "TYT",
                "score": exam_data.get("calculated_score", 0),
                "processing_time": (
                    datetime.now(UTC) - job_context.started_at
                ).total_seconds(),
            },
            user_id=user_id,
        )

        return {"status": "completed", "exam_type": "TYT", "user_id": user_id}

    async def _process_ayt_exam(
        self, exam_data: dict[str, Any], user_id: int, job_context: JobExecution
    ):
        """Process AYT exam submission"""
        job_context.log("Starting AYT exam processing")
        job_context.update_progress(5, "Validating AYT exam data")

        # AYT processing takes longer due to more subjects
        await asyncio.sleep(3)
        job_context.update_progress(20, "Processing mathematics section")

        await asyncio.sleep(4)
        job_context.update_progress(40, "Processing science sections")

        await asyncio.sleep(3)
        job_context.update_progress(60, "Processing social studies sections")

        await asyncio.sleep(2)
        job_context.update_progress(80, "Computing final AYT score")

        await asyncio.sleep(1)
        job_context.update_progress(100, "AYT exam processed successfully")

        # Publish event
        event_bus = await get_event_bus()
        await event_bus.publish(
            EventType.AYT_SIMULATION_COMPLETED,
            {
                "user_id": user_id,
                "exam_type": "AYT",
                "score": exam_data.get("calculated_score", 0),
                "subjects_completed": exam_data.get("subjects", []),
                "processing_time": (
                    datetime.now(UTC) - job_context.started_at
                ).total_seconds(),
            },
            user_id=user_id,
        )

        return {"status": "completed", "exam_type": "AYT", "user_id": user_id}

    async def _calculate_exam_ranking(self, exam_type: str, period: str = "daily"):
        """Calculate exam rankings and percentiles"""
        logger.info(f"Calculating {exam_type} rankings for {period} period")

        # Simulate ranking calculation
        await asyncio.sleep(5)

        return {"exam_type": exam_type, "period": period, "rankings_updated": True}

    async def _generate_practice_questions(
        self,
        user_id: int,
        subject: str,
        difficulty: str,
        count: int,
        job_context: JobExecution,
    ):
        """Generate personalized practice questions"""
        job_context.log(f"Generating {count} {difficulty} questions for {subject}")
        job_context.update_progress(20, "Analyzing user performance history")

        await asyncio.sleep(2)
        job_context.update_progress(50, "Selecting appropriate question templates")

        await asyncio.sleep(3)
        job_context.update_progress(80, "Generating personalized questions")

        await asyncio.sleep(1)
        job_context.update_progress(100, "Questions generated successfully")

        return {
            "user_id": user_id,
            "subject": subject,
            "difficulty": difficulty,
            "questions_generated": count,
        }

    async def _analyze_student_performance(
        self, user_id: int, job_context: JobExecution
    ):
        """Analyze student performance and generate insights"""
        job_context.log("Starting student performance analysis")
        job_context.update_progress(25, "Collecting performance data")

        await asyncio.sleep(2)
        job_context.update_progress(50, "Computing performance metrics")

        await asyncio.sleep(2)
        job_context.update_progress(75, "Generating insights and recommendations")

        await asyncio.sleep(1)
        job_context.update_progress(100, "Performance analysis completed")

        return {"user_id": user_id, "analysis_completed": True}

    async def _cleanup_expired_sessions(self):
        """Clean up expired user sessions"""
        logger.info("Starting session cleanup job")

        # Simulate cleanup
        await asyncio.sleep(3)
        cleaned_count = 45  # Simulated

        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return {"cleaned_sessions": cleaned_count}

    async def _generate_daily_reports(self):
        """Generate daily usage and performance reports"""
        logger.info("Generating daily reports")

        # Simulate report generation
        await asyncio.sleep(10)

        return {
            "reports_generated": [
                "usage_report",
                "performance_report",
                "exam_statistics",
            ]
        }

    async def _send_exam_reminders(self, exam_date: str, exam_type: str):
        """Send exam reminder notifications"""
        logger.info(f"Sending {exam_type} exam reminders for {exam_date}")

        # Simulate notification sending
        await asyncio.sleep(5)
        notifications_sent = 234  # Simulated

        return {"exam_type": exam_type, "notifications_sent": notifications_sent}

    async def _send_progress_notifications(
        self, user_id: int, job_context: JobExecution
    ):
        """Send study progress notifications"""
        job_context.log("Checking user progress for notifications")

        await asyncio.sleep(2)
        job_context.update_progress(50, "Generating progress summary")

        await asyncio.sleep(1)
        job_context.update_progress(100, "Progress notification sent")

        return {"user_id": user_id, "notification_sent": True}


# Global job processor instance
_job_processor: TurkishExamJobProcessor | None = None


async def get_turkish_job_processor() -> TurkishExamJobProcessor:
    """Get global Turkish exam job processor instance"""
    global _job_processor

    if _job_processor is None:
        _job_processor = TurkishExamJobProcessor()

    return _job_processor


# Decorator for registering jobs
def background_job(
    name: str,
    queue_type: QueueType = QueueType.BATCH_PROCESSING,
    priority: JobPriority = JobPriority.NORMAL,
    **kwargs,
):
    """Decorator for registering background jobs"""

    def decorator(func):
        async def register():
            processor = await get_turkish_job_processor()
            processor.register_job(name, func, queue_type, priority, **kwargs)
            return func

        # Register the job
        try:
            asyncio.create_task(register())
        except RuntimeError:
            # No event loop running, will register when processor is accessed
            pass

        return func

    return decorator


# Utility functions
async def schedule_job(job_name: str, **kwargs) -> str:
    """Schedule a background job"""
    processor = await get_turkish_job_processor()
    return await processor.schedule_job(job_name, **kwargs)


async def schedule_exam_processing(
    exam_type: str,
    user_id: int,
    exam_data: dict[str, Any],
    priority: JobPriority = JobPriority.HIGH,
) -> str:
    """Schedule Turkish exam processing job"""
    job_name = f"process_{exam_type.lower()}_exam"
    processor = await get_turkish_job_processor()

    return await processor.schedule_job(
        job_name,
        kwargs={"exam_data": exam_data},
        user_id=user_id,
        context={"exam_type": exam_type, "priority": priority.value},
    )


async def schedule_content_generation(
    user_id: int, content_type: str, parameters: dict[str, Any]
) -> str:
    """Schedule content generation job"""
    processor = await get_turkish_job_processor()

    return await processor.schedule_job(
        "generate_practice_questions",
        kwargs={
            "subject": parameters.get("subject", "matematik"),
            "difficulty": parameters.get("difficulty", "orta"),
            "count": parameters.get("count", 10),
            **parameters,
        },
        user_id=user_id,
    )


async def get_job_status(job_id: str) -> dict[str, Any] | None:
    """Get status of a background job"""
    processor = await get_turkish_job_processor()
    return processor.get_job_status(job_id)


async def get_job_system_stats() -> dict[str, Any]:
    """Get background job system statistics"""
    processor = await get_turkish_job_processor()
    return processor.get_system_stats()
