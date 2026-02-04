import pytest

"""
KIRO2 Unified Testing Framework
Comprehensive testing infrastructure for Turkish exam platform
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import asyncio
import shutil
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import redis.asyncio as redis
import pytest
import pytest_asyncio
from core.application_metrics import get_metrics_collector
from core.auth_middleware import AuthUser, UserRole
from core.message_queue_system import get_message_queue
from core.multi_level_caching import get_cache_system

# Import system components for testing
from core.structured_logging import LogCategory, get_logger
from core.turkish_exam_event_handlers import TurkishExamType
from core.unified_api_gateway import get_api_gateway
from core.unified_event_bus import get_event_bus

# Test configuration
TEST_CONFIG = {
    "database_url": "sqlite:///test.db",
    "redis_url": "redis://localhost:6379/15",  # Test database
    "cache_enabled": True,
    "event_bus_enabled": True,
    "message_queue_enabled": True,
    "testing": True,
    "log_level": "DEBUG",
}

logger = get_logger(__name__, LogCategory.TESTING)


class HTTPMethod:
    """HTTP method constants"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class TestCategory:
    """Test categories for organization"""

    UNIT = "unit"
    INTEGRATION = "integration"
    API = "api"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TURKISH_EXAM = "turkish_exam"
    END_TO_END = "end_to_end"


class TestPriority:
    """Test priorities"""

    CRITICAL = "critical"  # Must pass for release
    HIGH = "high"  # Important functionality
    MEDIUM = "medium"  # Standard features
    LOW = "low"  # Edge cases, nice-to-have


@dataclass
class TestContext:
    """Test execution context"""

    test_id: str
    category: str
    priority: str
    description: str
    turkish_description: str
    setup_data: Dict[str, Any] = field(default_factory=dict)
    cleanup_tasks: List[Callable] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def __post_init__(self):
        if not self.test_id:
            self.test_id = str(uuid.uuid4())
        self.start_time = datetime.now(timezone.utc)

    def mark_completed(self):
        """Mark test as completed"""
        self.end_time = datetime.now(timezone.utc)

    def get_duration_ms(self) -> float:
        """Get test duration in milliseconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0


class TestDataGenerator:
    """Generate test data for Turkish exam platform"""

    @staticmethod
    def create_test_user(
        user_id: int = None,
        role: UserRole = UserRole.STUDENT,
        username: str = None,
        email: str = None,
    ) -> AuthUser:
        """Create test user"""
        user_id = user_id or 12345
        username = username or f"test_user_{user_id}"
        email = email or f"{username}@test.com"

        # Get permissions for role
        from core.auth_middleware import PermissionManager

        permission_manager = PermissionManager()
        permissions = permission_manager.get_user_permissions(role)

        return AuthUser(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=permissions,
            is_active=True,
            is_verified=True,
            profile_data={
                "name": f"Test {username.title()}",
                "target_exam": "YKS 2024",
                "grade": 12 if role == UserRole.STUDENT else None,
                "school": "Test Lisesi" if role == UserRole.STUDENT else None,
            },
            exam_context={
                "preferred_exam_type": "tyt_ayt",
                "target_university": "Test Üniversitesi",
                "preparation_start_date": "2024-01-01",
            },
        )

    @staticmethod
    def create_test_exam_data(
        exam_type: TurkishExamType = TurkishExamType.TYT,
        difficulty: str = "orta",
        question_count: int = 120,
    ) -> Dict[str, Any]:
        """Create test exam data"""
        subjects = {
            TurkishExamType.TYT: ["turkce", "matematik", "fen", "sosyal"],
            TurkishExamType.AYT: [
                "matematik",
                "fizik",
                "kimya",
                "biyoloji",
                "tarih",
                "cografya",
                "felsefe",
                "din",
            ],
        }

        return {
            "exam_type": exam_type.value,
            "exam_id": str(uuid.uuid4()),
            "duration_minutes": 135 if exam_type == TurkishExamType.TYT else 180,
            "questions_total": question_count,
            "subjects": subjects.get(exam_type, ["matematik"]),
            "difficulty": difficulty,
            "is_simulation": True,
            "questions": [
                {
                    "question_id": i + 1,
                    "subject": subjects.get(exam_type, ["matematik"])[
                        i % len(subjects.get(exam_type, ["matematik"]))
                    ],
                    "difficulty": difficulty,
                    "question_text": f"Test sorusu {i + 1}",
                    "options": ["A", "B", "C", "D", "E"],
                    "correct_answer": "A",
                    "points": 1.0,
                }
                for i in range(question_count)
            ],
        }

    @staticmethod
    def create_test_api_request(
        method: str = "GET",
        path: str = "/test",
        user: AuthUser = None,
        body: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create test API request"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "KIRO2-Test-Client/1.0",
            "Accept-Language": "tr-TR,tr;q=0.9",
        }

        if user:
            headers["X-User-ID"] = str(user.user_id)
            headers["Authorization"] = f"Bearer test_token_{user.user_id}"

        return {
            "method": method,
            "path": path,
            "headers": headers,
            "query_params": {},
            "body": body,
        }

    @staticmethod
    def create_turkish_content_data() -> Dict[str, Any]:
        """Create Turkish educational content test data"""
        return {
            "subjects": {
                "matematik": {
                    "name": "Matematik",
                    "topics": [
                        "Sayılar",
                        "Cebir",
                        "Geometri",
                        "Fonksiyonlar",
                        "Analiz",
                    ],
                    "question_count": 40,
                    "difficulty_levels": ["kolay", "orta", "zor"],
                },
                "turkce": {
                    "name": "Türkçe-Edebiyat",
                    "topics": [
                        "Dil Bilgisi",
                        "Anlam Bilgisi",
                        "Edebiyat",
                        "Okuma Anlama",
                    ],
                    "question_count": 40,
                    "difficulty_levels": ["kolay", "orta", "zor"],
                },
                "tarih": {
                    "name": "Tarih",
                    "topics": [
                        "Türk Tarihi",
                        "Dünya Tarihi",
                        "İnkılap Tarihi",
                        "Çağdaş Türkiye",
                    ],
                    "question_count": 20,
                    "difficulty_levels": ["kolay", "orta", "zor"],
                },
            },
            "universities": [
                {
                    "name": "İstanbul Üniversitesi",
                    "city": "İstanbul",
                    "type": "devlet",
                    "departments": ["Tıp", "Hukuk", "Mühendislik", "İktisat"],
                },
                {
                    "name": "Ankara Üniversitesi",
                    "city": "Ankara",
                    "type": "devlet",
                    "departments": [
                        "Siyasal Bilgiler",
                        "Tıp",
                        "Veteriner",
                        "Eczacılık",
                    ],
                },
            ],
            "exam_periods": {
                "yks_2024": {
                    "registration_start": "2024-02-15",
                    "registration_end": "2024-03-08",
                    "tyt_date": "2024-06-15",
                    "ayt_date": "2024-06-16",
                    "results_date": "2024-07-13",
                }
            },
        }


class TestEnvironment:
    """Test environment management"""

    def __init__(self):
        self.temp_dir = None
        self.test_db_path = None
        self.redis_client = None
        self.cleanup_tasks = []

    async def setup(self) -> "TestEnvironment":
        """Setup test environment"""
        try:
            # Create temporary directory
            self.temp_dir = Path(tempfile.mkdtemp(prefix="kiro2_test_"))

            # Setup test database
            self.test_db_path = self.temp_dir / "test.db"

            # Setup Redis connection for testing
            try:
                self.redis_client = aioredis.from_url(
                    TEST_CONFIG["redis_url"], decode_responses=True
                )
                await self.redis_client.ping()

                # Clean test Redis database
                await self.redis_client.flushdb()

            except Exception as e:
                logger.warning(f"Redis not available for testing: {e}")
                self.redis_client = None

            # Setup test configuration
            await self._setup_test_config()

            logger.info(f"Test environment setup completed: {self.temp_dir}")
            return self

        except Exception as e:
            logger.error(f"Test environment setup failed: {e}")
            await self.cleanup()
            raise

    async def cleanup(self):
        """Cleanup test environment"""
        try:
            # Run cleanup tasks
            for task in self.cleanup_tasks:
                try:
                    if asyncio.iscoroutinefunction(task):
                        await task()
                    else:
                        task()
                except Exception as e:
                    logger.warning(f"Cleanup task failed: {e}")

            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()

            # Remove temporary directory
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)

            logger.info("Test environment cleanup completed")

        except Exception as e:
            logger.error(f"Test environment cleanup failed: {e}")

    async def _setup_test_config(self):
        """Setup test-specific configuration"""
        # This would override the main config for testing

    def add_cleanup_task(self, task: Callable):
        """Add cleanup task"""
        self.cleanup_tasks.append(task)

    async def reset_state(self):
        """Reset test environment state between tests"""
        try:
            # Clear Redis cache
            if self.redis_client:
                await self.redis_client.flushdb()

            # Reset any other stateful components
            logger.debug("Test environment state reset")

        except Exception as e:
            logger.error(f"Test state reset failed: {e}")


class TestRunner:
    """Test execution and reporting"""

    def __init__(self):
        self.test_results = []
        self.environment = TestEnvironment()
        self.metrics_collector = get_metrics_collector()

    async def setup(self):
        """Setup test runner"""
        await self.environment.setup()
        logger.info("Test runner setup completed")

    async def teardown(self):
        """Teardown test runner"""
        await self.environment.cleanup()
        logger.info("Test runner teardown completed")

    async def run_test(
        self, test_func: Callable, context: TestContext
    ) -> Dict[str, Any]:
        """Run individual test with context"""
        try:
            logger.info(
                f"Running test: {context.description}",
                extra={"test_id": context.test_id, "category": context.category},
            )

            # Reset environment state
            await self.environment.reset_state()

            # Execute test
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func(context, self.environment)
            else:
                result = test_func(context, self.environment)

            # Mark as completed
            context.mark_completed()

            # Record success
            test_result = {
                "test_id": context.test_id,
                "description": context.description,
                "category": context.category,
                "priority": context.priority,
                "status": "passed",
                "duration_ms": context.get_duration_ms(),
                "result": result,
                "timestamp": context.end_time.isoformat(),
            }

            self.test_results.append(test_result)

            logger.info(
                f"Test passed: {context.description} ({context.get_duration_ms():.2f}ms)"
            )
            return test_result

        except Exception as e:
            context.mark_completed()

            # Record failure
            test_result = {
                "test_id": context.test_id,
                "description": context.description,
                "category": context.category,
                "priority": context.priority,
                "status": "failed",
                "duration_ms": context.get_duration_ms(),
                "error": str(e),
                "timestamp": context.end_time.isoformat(),
            }

            self.test_results.append(test_result)

            logger.error(f"Test failed: {context.description}: {e}")
            raise

    def generate_report(self) -> Dict[str, Any]:
        """Generate test execution report"""
        if not self.test_results:
            return {"message": "No tests executed"}

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "passed"])
        failed_tests = total_tests - passed_tests

        # Calculate statistics by category
        category_stats = {}
        for result in self.test_results:
            category = result["category"]
            if category not in category_stats:
                category_stats[category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "avg_duration": 0,
                }

            category_stats[category]["total"] += 1
            if result["status"] == "passed":
                category_stats[category]["passed"] += 1
            else:
                category_stats[category]["failed"] += 1

        # Calculate average durations
        for category in category_stats:
            category_results = [
                r for r in self.test_results if r["category"] == category
            ]
            avg_duration = sum(r["duration_ms"] for r in category_results) / len(
                category_results
            )
            category_stats[category]["avg_duration"] = round(avg_duration, 2)

        total_duration = sum(r["duration_ms"] for r in self.test_results)

        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": round((passed_tests / total_tests) * 100, 2),
                "total_duration_ms": round(total_duration, 2),
                "avg_duration_ms": round(total_duration / total_tests, 2),
            },
            "category_breakdown": category_stats,
            "failed_tests": [r for r in self.test_results if r["status"] == "failed"],
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": "test",
        }


# Pytest fixtures for Turkish exam testing


@pytest_asyncio.fixture
async def test_environment():
    """Test environment fixture"""
    env = TestEnvironment()
    await env.setup()
    yield env
    await env.cleanup()


@pytest.fixture
def test_user():
    """Test user fixture"""
    return TestDataGenerator.create_test_user()


@pytest.fixture
def test_student():
    """Test student user fixture"""
    return TestDataGenerator.create_test_user(
        user_id=1001,
        role=UserRole.STUDENT,
        username="test_student",
        email="student@test.com",
    )


@pytest.fixture
def test_teacher():
    """Test teacher user fixture"""
    return TestDataGenerator.create_test_user(
        user_id=2001,
        role=UserRole.TEACHER,
        username="test_teacher",
        email="teacher@test.com",
    )


@pytest.fixture
def test_admin():
    """Test admin user fixture"""
    return TestDataGenerator.create_test_user(
        user_id=3001, role=UserRole.ADMIN, username="test_admin", email="admin@test.com"
    )


@pytest.fixture
def tyt_exam_data():
    """TYT exam data fixture"""
    return TestDataGenerator.create_test_exam_data(TurkishExamType.TYT)


@pytest.fixture
def ayt_exam_data():
    """AYT exam data fixture"""
    return TestDataGenerator.create_test_exam_data(
        TurkishExamType.AYT, question_count=80
    )


@pytest.fixture
def turkish_content_data():
    """Turkish content data fixture"""
    return TestDataGenerator.create_turkish_content_data()


@pytest_asyncio.fixture
async def api_gateway():
    """API Gateway fixture"""
    gateway = await get_api_gateway()
    yield gateway


@pytest_asyncio.fixture
async def cache_system():
    """Cache system fixture"""
    cache = await get_cache_system()
    yield cache
    # Cleanup
    await cache.clear_all()


@pytest_asyncio.fixture
async def event_bus():
    """Event bus fixture"""
    bus = await get_event_bus()
    yield bus


@pytest_asyncio.fixture
async def message_queue():
    """Message queue fixture"""
    queue = await get_message_queue()
    yield queue


# Test decorators for Turkish exam platform


def turkish_exam_test(
    category: str = TestCategory.TURKISH_EXAM,
    priority: str = TestPriority.MEDIUM,
    description: str = "",
    turkish_description: str = "",
):
    """Decorator for Turkish exam specific tests"""

    def decorator(func):
        func._test_category = category
        func._test_priority = priority
        func._test_description = description
        func._test_turkish_description = turkish_description
        return func

    return decorator


def critical_test(description: str = "", turkish_description: str = ""):
    """Decorator for critical tests"""
    return turkish_exam_test(
        category=TestCategory.UNIT,
        priority=TestPriority.CRITICAL,
        description=description,
        turkish_description=turkish_description,
    )


def integration_test(description: str = "", turkish_description: str = ""):
    """Decorator for integration tests"""
    return turkish_exam_test(
        category=TestCategory.INTEGRATION,
        priority=TestPriority.HIGH,
        description=description,
        turkish_description=turkish_description,
    )


def api_test(description: str = "", turkish_description: str = ""):
    """Decorator for API tests"""
    return turkish_exam_test(
        category=TestCategory.API,
        priority=TestPriority.HIGH,
        description=description,
        turkish_description=turkish_description,
    )


def performance_test(description: str = "", turkish_description: str = ""):
    """Decorator for performance tests"""
    return turkish_exam_test(
        category=TestCategory.PERFORMANCE,
        priority=TestPriority.MEDIUM,
        description=description,
        turkish_description=turkish_description,
    )


# Utility functions for testing


async def create_test_context(
    description: str,
    turkish_description: str = "",
    category: str = TestCategory.UNIT,
    priority: str = TestPriority.MEDIUM,
) -> TestContext:
    """Create test context"""
    return TestContext(
        test_id=str(uuid.uuid4()),
        category=category,
        priority=priority,
        description=description,
        turkish_description=turkish_description or description,
    )


def assert_turkish_response(
    response_data: Dict[str, Any], check_localization: bool = True
):
    """Assert Turkish-specific response data"""
    assert response_data is not None, "Response data should not be None"

    if check_localization:
        # Check for Turkish translations
        turkish_fields = [key for key in response_data.keys() if key.endswith("_tr")]
        assert len(turkish_fields) > 0, "Response should contain Turkish translations"

        # Check for Turkish headers if present
        if "headers" in response_data:
            headers = response_data["headers"]
            if "Content-Language" in headers:
                assert (
                    "tr" in headers["Content-Language"]
                ), "Content-Language should include Turkish"


def assert_exam_data_valid(exam_data: Dict[str, Any], exam_type: TurkishExamType):
    """Assert exam data validity for Turkish exams"""
    assert "exam_type" in exam_data, "Exam data should contain exam_type"
    assert (
        exam_data["exam_type"] == exam_type.value
    ), f"Exam type should be {exam_type.value}"

    assert "questions" in exam_data, "Exam data should contain questions"
    assert len(exam_data["questions"]) > 0, "Exam should have questions"

    # Check Turkish-specific exam constraints
    if exam_type == TurkishExamType.TYT:
        assert exam_data.get("duration_minutes") == 135, "TYT should be 135 minutes"
        expected_subjects = ["turkce", "matematik", "fen", "sosyal"]
    elif exam_type == TurkishExamType.AYT:
        assert exam_data.get("duration_minutes") == 180, "AYT should be 180 minutes"
        expected_subjects = [
            "matematik",
            "fizik",
            "kimya",
            "biyoloji",
            "tarih",
            "cografya",
        ]

    # Check subjects are present
    subjects = exam_data.get("subjects", [])
    for expected_subject in expected_subjects:
        assert (
            expected_subject in subjects
        ), f"Exam should contain {expected_subject} subject"


async def wait_for_async_completion(coro, timeout: float = 5.0):
    """Wait for async operation to complete with timeout"""
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        return result
    except asyncio.TimeoutError:
        raise AssertionError(f"Async operation timed out after {timeout} seconds")


# Mock factories for testing


class MockFactory:
    """Factory for creating mock objects"""

    @staticmethod
    def create_mock_redis():
        """Create mock Redis client"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        mock_redis.ping.return_value = True
        mock_redis.flushdb.return_value = True
        return mock_redis

    @staticmethod
    def create_mock_database():
        """Create mock database session"""
        mock_db = MagicMock()
        mock_db.commit.return_value = None
        mock_db.rollback.return_value = None
        mock_db.close.return_value = None
        return mock_db

    @staticmethod
    def create_mock_event_bus():
        """Create mock event bus"""
        mock_bus = AsyncMock()
        mock_bus.publish.return_value = str(uuid.uuid4())
        mock_bus.subscribe.return_value = str(uuid.uuid4())
        return mock_bus

    @staticmethod
    def create_mock_message_queue():
        """Create mock message queue"""
        mock_queue = AsyncMock()
        mock_queue.enqueue.return_value = True
        mock_queue.start_consumers.return_value = None
        mock_queue.stop_consumers.return_value = None
        return mock_queue


# Test configuration helper
def get_test_config() -> Dict[str, Any]:
    """Get test configuration"""
    return TEST_CONFIG.copy()


if __name__ == "__main__":
    # Example usage
    async def main():
        runner = TestRunner()
        await runner.setup()

        try:
            # Example test
            async def sample_test(context: TestContext, env: TestEnvironment):
                assert True, "Sample test"
                return {"result": "success"}

            context = await create_test_context("Sample test", "Örnek test")
            result = await runner.run_test(sample_test, context)

            print("Test Result:", result)
            print("Report:", runner.generate_report())

        finally:
            await runner.teardown()

    asyncio.run(main())
