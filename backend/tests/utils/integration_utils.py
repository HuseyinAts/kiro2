"""
Integration Test Utilities
Helper functions and classes for integration testing
"""
import asyncio
import time
import logging
from typing import Dict, List, Any, Callable
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
import uuid

# Import centralized JWT helper from conftest (DRY)
try:
    from tests.conftest import _generate_test_jwt, TEST_JWT_SECRET, TEST_JWT_ALGORITHM
except ImportError:
    import jwt as _jwt
    TEST_JWT_SECRET = "test-secret-key-for-testing"
    TEST_JWT_ALGORITHM = "HS256"
    def _generate_test_jwt(user_id="1", email="test@test.com", role="student"):
        import time
        payload = {"sub": user_id, "email": email, "role": role, "exp": int(time.time()) + 3600}
        return _jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)


class IntegrationTestHelper:
    """Helper class for integration testing"""

    def __init__(self):
        self.test_data = {}
        self.cleanup_tasks = []
        self.logger = logging.getLogger(__name__)

    def register_cleanup(self, cleanup_func: Callable):
        """Register cleanup function to run after test"""
        self.cleanup_tasks.append(cleanup_func)

    async def cleanup(self):
        """Run all registered cleanup tasks"""
        for cleanup_func in self.cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
            except Exception as e:
                self.logger.warning(f"Cleanup task failed: {e}")

        self.cleanup_tasks.clear()
        self.test_data.clear()


class APITestClient:
    """Test client for API integration testing"""

    def __init__(self, base_url="http://test", timeout=30):
        self.base_url = base_url
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json"}
        self.session_token = None

    def set_auth_token(self, token: str):
        """Set authentication token for requests"""
        self.session_token = token
        self.headers["Authorization"] = f"Bearer {token}"

    def clear_auth(self):
        """Clear authentication token"""
        self.session_token = None
        if "Authorization" in self.headers:
            del self.headers["Authorization"]

    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request (mock implementation for testing)"""
        # Mock implementation - would use real HTTP client in production
        url = f"{self.base_url}{endpoint}"

        # Simulate request processing
        await asyncio.sleep(0.01)  # Simulate network latency

        # Mock response based on endpoint
        if endpoint.startswith("/api/v1/auth/kayit"):
            return self._mock_registration_response(kwargs.get("json", {}))
        elif endpoint.startswith("/api/v1/auth/giris"):
            return self._mock_login_response(kwargs.get("json", {}))
        elif endpoint.startswith("/api/v1/content"):
            return self._mock_content_response(method, kwargs.get("json", {}))
        else:
            return {"status_code": 404, "json": {"error": "Endpoint not found"}}

    def _mock_registration_response(self, data: Dict) -> Dict:
        """Mock user registration response"""
        if not data.get("email") or not data.get("sifre"):
            return {"status_code": 422, "json": {"error": "Missing required fields"}}

        if len(data.get("sifre", "")) < 6:
            return {"status_code": 422, "json": {"error": "Password too short"}}

        return {
            "status_code": 201,
            "json": {
                "kullanici_id": str(uuid.uuid4()),
                "email": data["email"],
                "ad_soyad": data.get("ad_soyad", ""),
                "rol": data.get("rol", "ogrenci"),
                "olusturma_tarihi": datetime.now().isoformat(),
            },
        }

    def _mock_login_response(self, data: Dict) -> Dict:
        """Mock user login response"""
        if not data.get("email") or not data.get("sifre"):
            return {"status_code": 422, "json": {"error": "Missing credentials"}}

        return {
            "status_code": 200,
            "json": {
                "access_token": _generate_test_jwt(str(uuid.uuid4()), data["email"]),
                "token_type": "bearer",
                "expires_in": 3600,
                "kullanici": {
                    "kullanici_id": str(uuid.uuid4()),
                    "email": data["email"],
                    "rol": "ogrenci",
                },
            },
        }

    def _mock_content_response(self, method: str, data: Dict) -> Dict:
        """Mock content API response"""
        if method == "POST":
            if not data.get("baslik"):
                return {"status_code": 422, "json": {"error": "Title required"}}

            return {
                "status_code": 201,
                "json": {
                    "success": True,
                    "content_id": str(uuid.uuid4()),
                    "message": "Content created successfully",
                },
            }
        elif method == "GET":
            return {
                "status_code": 200,
                "json": {"success": True, "data": [], "total": 0},
            }
        else:
            return {"status_code": 405, "json": {"error": "Method not allowed"}}


class WorkflowTestRunner:
    """Runner for workflow integration tests"""

    def __init__(self):
        self.steps = []
        self.results = []
        self.context = {}

    def add_step(self, name: str, step_func: Callable, *args, **kwargs):
        """Add a step to the workflow"""
        self.steps.append(
            {"name": name, "func": step_func, "args": args, "kwargs": kwargs}
        )

    async def run(self) -> List[Dict[str, Any]]:
        """Run all workflow steps"""
        self.results.clear()

        for i, step in enumerate(self.steps):
            start_time = time.time()

            try:
                # Pass context to step function
                if "context" not in step["kwargs"]:
                    step["kwargs"]["context"] = self.context

                if asyncio.iscoroutinefunction(step["func"]):
                    result = await step["func"](*step["args"], **step["kwargs"])
                else:
                    result = step["func"](*step["args"], **step["kwargs"])

                end_time = time.time()

                step_result = {
                    "step": i + 1,
                    "name": step["name"],
                    "success": True,
                    "result": result,
                    "duration": end_time - start_time,
                    "error": None,
                }

                # Update context with result
                if isinstance(result, dict):
                    self.context.update(result)

            except Exception as e:
                end_time = time.time()
                step_result = {
                    "step": i + 1,
                    "name": step["name"],
                    "success": False,
                    "result": None,
                    "duration": end_time - start_time,
                    "error": str(e),
                }

            self.results.append(step_result)

            # Stop on failure if configured
            if not step_result["success"]:
                break

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get workflow execution summary"""
        total_steps = len(self.results)
        successful_steps = len([r for r in self.results if r["success"]])
        total_duration = sum([r["duration"] for r in self.results])

        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": total_steps - successful_steps,
            "success_rate": (successful_steps / total_steps) * 100
            if total_steps > 0
            else 0,
            "total_duration": total_duration,
            "average_step_duration": total_duration / total_steps
            if total_steps > 0
            else 0,
        }


class PerformanceMonitor:
    """Monitor performance during integration tests"""

    def __init__(self):
        self.metrics = {
            "response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "requests_per_second": 0,
            "error_rate": 0,
        }
        self.start_time = None
        self.request_count = 0
        self.error_count = 0

    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.metrics = {
            "response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "requests_per_second": 0,
            "error_rate": 0,
        }

    def record_request(self, response_time: float, success: bool = True):
        """Record a request and its performance"""
        self.metrics["response_times"].append(response_time)
        self.request_count += 1

        if not success:
            self.error_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        if not self.metrics["response_times"]:
            return self.metrics

        elapsed_time = time.time() - self.start_time if self.start_time else 1

        return {
            "requests_per_second": self.request_count / elapsed_time,
            "error_rate": (self.error_count / self.request_count) * 100
            if self.request_count > 0
            else 0,
            "average_response_time": sum(self.metrics["response_times"])
            / len(self.metrics["response_times"]),
            "min_response_time": min(self.metrics["response_times"]),
            "max_response_time": max(self.metrics["response_times"]),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "elapsed_time": elapsed_time,
        }


class DataValidator:
    """Validate data integrity during integration tests"""

    @staticmethod
    def validate_user_data(user_data: Dict) -> List[str]:
        """Validate user data structure"""
        errors = []

        required_fields = ["kullanici_id", "email", "ad_soyad", "rol"]
        for field in required_fields:
            if field not in user_data:
                errors.append(f"Missing required field: {field}")

        if "email" in user_data and "@" not in user_data["email"]:
            errors.append("Invalid email format")

        if "rol" in user_data and user_data["rol"] not in [
            "ogrenci",
            "ogretmen",
            "veli",
            "admin",
        ]:
            errors.append("Invalid role")

        return errors

    @staticmethod
    def validate_content_data(content_data: Dict) -> List[str]:
        """Validate content data structure"""
        errors = []

        required_fields = ["baslik", "kategori", "yazar"]
        for field in required_fields:
            if field not in content_data:
                errors.append(f"Missing required field: {field}")

        if "baslik" in content_data and len(content_data["baslik"]) < 3:
            errors.append("Title too short")

        return errors

    @staticmethod
    def validate_exam_data(exam_data: Dict) -> List[str]:
        """Validate exam data structure"""
        errors = []

        required_fields = ["sinav_id", "ogrenci_id", "sinav_tipi"]
        for field in required_fields:
            if field not in exam_data:
                errors.append(f"Missing required field: {field}")

        if "sinav_tipi" in exam_data and exam_data["sinav_tipi"] not in [
            "TYT",
            "AYT",
            "YDT",
        ]:
            errors.append("Invalid exam type")

        return errors


class SecurityTester:
    """Security testing utilities"""

    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "&#60;script&#62;alert('XSS')&#60;/script&#62;",
    ]

    SQL_INJECTION_PAYLOADS = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; UPDATE users SET password='hacked'; --",
        "1' UNION SELECT * FROM users--",
    ]

    @classmethod
    def test_xss_protection(cls, test_func: Callable, field_name: str) -> List[str]:
        """Test XSS protection for a field"""
        vulnerabilities = []

        for payload in cls.XSS_PAYLOADS:
            try:
                result = test_func({field_name: payload})

                # Check if payload is reflected without encoding
                if payload in str(result):
                    vulnerabilities.append(f"XSS vulnerability with payload: {payload}")
            except Exception:
                # Exception is acceptable - indicates input validation
                pass

        return vulnerabilities

    @classmethod
    def test_sql_injection_protection(
        cls, test_func: Callable, field_name: str
    ) -> List[str]:
        """Test SQL injection protection for a field"""
        vulnerabilities = []

        for payload in cls.SQL_INJECTION_PAYLOADS:
            try:
                result = test_func({field_name: payload})

                # If function completes without error, check for SQL errors in response
                if any(
                    keyword in str(result).lower()
                    for keyword in ["sql", "syntax", "mysql", "postgres"]
                ):
                    vulnerabilities.append(
                        f"Possible SQL injection with payload: {payload}"
                    )
            except Exception:
                # Exception is acceptable - indicates input validation
                pass

        return vulnerabilities


class TestDataGenerator:
    """Generate test data for integration tests"""

    @staticmethod
    def generate_users(count: int) -> List[Dict]:
        """Generate test user data"""
        users = []

        for i in range(count):
            user = {
                "kullanici_id": str(uuid.uuid4()),
                "email": f"test_user_{i}@example.com",
                "ad_soyad": f"Test User {i}",
                "telefon": f"0555123{i:04d}",
                "rol": ["ogrenci", "ogretmen", "veli"][i % 3],
                "aktif": True,
                "olusturma_tarihi": datetime.now() - timedelta(days=i),
            }
            users.append(user)

        return users

    @staticmethod
    def generate_content(count: int) -> List[Dict]:
        """Generate test content data"""
        content = []
        categories = ["Matematik", "Fizik", "Kimya", "Biyoloji", "Türkçe"]

        for i in range(count):
            content_item = {
                "content_id": str(uuid.uuid4()),
                "baslik": f"Test Content {i}",
                "icerik": f"This is test content number {i}. It contains educational material.",
                "kategori": categories[i % len(categories)],
                "yazar": f"Author {i}",
                "etiketler": [f"tag{i}", "test"],
                "zorluk_seviyesi": ["kolay", "orta", "zor"][i % 3],
                "olusturma_tarihi": datetime.now() - timedelta(hours=i),
            }
            content.append(content_item)

        return content

    @staticmethod
    def generate_exam_questions(count: int) -> List[Dict]:
        """Generate test exam questions"""
        questions = []
        subjects = ["Matematik", "Fizik", "Kimya", "Türkçe", "Tarih"]

        for i in range(count):
            question = {
                "soru_id": f"q_{uuid.uuid4().hex[:8]}",
                "soru_metni": f"Test question {i}?",
                "secenekler": [
                    f"A) Option {i}A",
                    f"B) Option {i}B",
                    f"C) Option {i}C",
                    f"D) Option {i}D",
                ],
                "dogru_cevap": ["A", "B", "C", "D"][i % 4],
                "konu": subjects[i % len(subjects)],
                "zorluk_seviyesi": ["kolay", "orta", "zor"][i % 3],
                "sinav_tipi": ["TYT", "AYT", "YDT"][i % 3],
            }
            questions.append(question)

        return questions


@asynccontextmanager
async def integration_test_context():
    """Context manager for integration tests"""
    helper = IntegrationTestHelper()
    monitor = PerformanceMonitor()

    try:
        monitor.start_monitoring()
        yield {
            "helper": helper,
            "monitor": monitor,
            "client": APITestClient(),
            "workflow": WorkflowTestRunner(),
            "validator": DataValidator(),
            "security": SecurityTester(),
            "generator": TestDataGenerator(),
        }
    finally:
        await helper.cleanup()


def assert_performance_acceptable(
    metrics: Dict[str, Any], max_response_time: float = 1.0, max_error_rate: float = 5.0
):
    """Assert that performance metrics are acceptable"""
    assert (
        metrics["average_response_time"] <= max_response_time
    ), f"Average response time {metrics['average_response_time']} exceeds {max_response_time}"
    assert (
        metrics["error_rate"] <= max_error_rate
    ), f"Error rate {metrics['error_rate']}% exceeds {max_error_rate}%"
    assert metrics["requests_per_second"] > 0, "No requests processed"


def assert_security_clean(vulnerabilities: List[str]):
    """Assert that no security vulnerabilities were found"""
    assert (
        len(vulnerabilities) == 0
    ), f"Security vulnerabilities found: {vulnerabilities}"


def assert_data_integrity(validation_errors: List[str]):
    """Assert that data integrity is maintained"""
    assert len(validation_errors) == 0, f"Data integrity errors: {validation_errors}"
