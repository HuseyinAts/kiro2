"""
Integration Test Fixtures and Utilities
Reusable fixtures for integration testing
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

# Import centralized JWT helper from conftest (DRY)
try:
    from tests.conftest import TEST_JWT_ALGORITHM, TEST_JWT_SECRET, _generate_test_jwt
except ImportError:
    import jwt as _jwt
    TEST_JWT_SECRET = "test-secret-key-for-testing"
    TEST_JWT_ALGORITHM = "HS256"
    def _generate_test_jwt(user_id="1", email="test@test.com", role="student"):
        import time
        payload = {"sub": user_id, "email": email, "role": role, "exp": int(time.time()) + 3600}
        return _jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)


# ==================== DATABASE FIXTURES ====================


@pytest.fixture
def mock_database_session():
    """Mock database session for integration tests"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.begin = AsyncMock()

    # Mock query results
    mock_result = Mock()
    mock_result.fetchone = Mock(return_value={"id": 1, "test": "value"})
    mock_result.fetchall = Mock(return_value=[{"id": 1, "test": "value"}])
    session.execute.return_value = mock_result

    return session


@pytest.fixture
def database_test_data():
    """Sample database test data"""
    return {
        "users": [
            {
                "kullanici_id": "user_001",
                "email": "test1@example.com",
                "ad_soyad": "Test User 1",
                "rol": "ogrenci",
                "aktif": True,
                "olusturma_tarihi": datetime.now(),
            },
            {
                "kullanici_id": "user_002",
                "email": "test2@example.com",
                "ad_soyad": "Test User 2",
                "rol": "ogretmen",
                "aktif": True,
                "olusturma_tarihi": datetime.now(),
            },
            {
                "kullanici_id": "user_003",
                "email": "test3@example.com",
                "ad_soyad": "Test User 3",
                "rol": "veli",
                "aktif": True,
                "olusturma_tarihi": datetime.now(),
            },
        ],
        "questions": [
            {
                "soru_id": "q_001",
                "soru_metni": "2 + 2 = ?",
                "secenekler": ["A) 3", "B) 4", "C) 5", "D) 6"],
                "dogru_cevap": "B",
                "konu": "Matematik",
                "zorluk_seviyesi": "kolay",
                "sinav_tipi": "TYT",
            },
            {
                "soru_id": "q_002",
                "soru_metni": "Türkiye'nin başkenti neresidir?",
                "secenekler": ["A) İstanbul", "B) Ankara", "C) İzmir", "D) Bursa"],
                "dogru_cevap": "B",
                "konu": "Coğrafya",
                "zorluk_seviyesi": "kolay",
                "sinav_tipi": "TYT",
            },
        ],
        "exams": [
            {
                "sinav_id": "exam_001",
                "ogrenci_id": "user_001",
                "sinav_tipi": "TYT",
                "toplam_soru_sayisi": 100,
                "sure_dakika": 180,
                "durum": "tamamlandi",
            }
        ],
    }


# ==================== API FIXTURES ====================


@pytest.fixture
def mock_api_client():
    """Mock API client for integration tests"""
    client = Mock()

    # Mock successful responses
    client.post = Mock(
        return_value=Mock(
            status_code=201, json=Mock(return_value={"success": True, "id": "test_id"})
        )
    )

    client.get = Mock(
        return_value=Mock(
            status_code=200, json=Mock(return_value={"success": True, "data": []})
        )
    )

    client.put = Mock(
        return_value=Mock(
            status_code=200, json=Mock(return_value={"success": True, "updated": True})
        )
    )

    client.delete = Mock(return_value=Mock(status_code=204, text=""))

    return client


@pytest.fixture
def api_test_payloads():
    """Standard API test payloads"""
    return {
        "user_registration": {
            "email": "api_test@example.com",
            "ad_soyad": "API Test User",
            "telefon": "05551234567",
            "sifre": "secure_password123",
            "rol": "ogrenci",
        },
        "user_login": {"email": "api_test@example.com", "sifre": "secure_password123"},
        "article_content": {
            "baslik": "Test Matematik Makalesi",
            "icerik": "Bu bir test matematik makalesidir. İçerik yeterince uzun olmalı çünkü minimum 50 karakter gerekiyor.",
            "kategori": "Matematik",
            "yazar": "Test Yazarı",
            "etiketler": ["matematik", "test", "eğitim"],
            "zorluk_seviyesi": "orta",
        },
        "video_content": {
            "baslik": "Test Video Dersi",
            "aciklama": "Bu bir test video dersidir.",
            "video_url": "https://example.com/test-video.mp4",
            "kategori": "Matematik",
            "yazar": "Video Eğitmeni",
            "sure_dakika": 15,
            "zorluk_seviyesi": "orta",
        },
        "quiz_content": {
            "baslik": "Matematik Quiz",
            "aciklama": "Temel matematik quiz",
            "kategori": "Matematik",
            "yazar": "Quiz Hazırlayıcısı",
            "sorular": [
                {
                    "soru_metni": "2 + 2 = ?",
                    "secenekler": ["3", "4", "5", "6"],
                    "dogru_cevap": 1,
                }
            ],
        },
    }


# ==================== SERVICE FIXTURES ====================


@pytest.fixture
def mock_user_service():
    """Mock user service for integration tests"""
    service = Mock()

    # Mock user creation
    service.kullanici_olustur = AsyncMock(
        return_value={
            "kullanici_id": str(uuid.uuid4()),
            "email": "test@example.com",
            "ad_soyad": "Test User",
            "rol": "ogrenci",
            "aktif": True,
            "olusturma_tarihi": datetime.now(),
        }
    )

    # Mock user retrieval
    service.kullanici_getir = AsyncMock(
        return_value={
            "kullanici_id": "test_user_123",
            "email": "test@example.com",
            "ad_soyad": "Test User",
            "rol": "ogrenci",
        }
    )

    # Mock authentication - generate real JWT token
    test_user_id = "test_user_123"
    test_email = "test@example.com"
    test_role = "ogrenci"
    service.kullanici_giris = AsyncMock(
        return_value={
            "access_token": _generate_test_jwt(test_user_id, test_email, test_role),
            "kullanici": {
                "kullanici_id": test_user_id,
                "email": test_email,
                "rol": test_role,
            },
        }
    )

    # Mock token validation
    service.token_dogrula = AsyncMock(
        return_value={
            "kullanici_id": "test_user_123",
            "email": "test@example.com",
            "rol": "ogrenci",
        }
    )

    return service


@pytest.fixture
def mock_content_service():
    """Mock content service for integration tests"""
    service = Mock()

    # Mock content creation
    service.create_content = AsyncMock(
        return_value={
            "content_id": str(uuid.uuid4()),
            "success": True,
            "message": "Content created successfully",
        }
    )

    # Mock content retrieval
    service.get_content = AsyncMock(
        return_value=[
            {
                "content_id": "content_123",
                "baslik": "Test Content",
                "kategori": "Test",
                "yazar": "Test Author",
            }
        ]
    )

    # Mock content search
    service.search_content = AsyncMock(
        return_value={"results": [], "total": 0, "page": 1}
    )

    return service


@pytest.fixture
def mock_exam_service():
    """Mock exam service for integration tests"""
    service = Mock()

    # Mock exam creation
    service.create_exam = AsyncMock(
        return_value={
            "sinav_id": str(uuid.uuid4()),
            "success": True,
            "message": "Exam created successfully",
        }
    )

    # Mock exam scoring
    service.score_exam = AsyncMock(
        return_value={
            "dogru_sayisi": 8,
            "yanlis_sayisi": 2,
            "bos_sayisi": 0,
            "net_sayisi": 7.5,
            "ham_puan": 45.0,
            "yuzde": 80.0,
        }
    )

    # Mock exam results
    service.get_exam_results = AsyncMock(
        return_value={
            "sinav_id": "exam_123",
            "ogrenci_id": "user_123",
            "sonuclar": {"toplam_puan": 450.0, "basari_yuzdesi": 85.0},
        }
    )

    return service


# ==================== WORKFLOW FIXTURES ====================


@pytest.fixture
def integration_test_workflow():
    """Complete integration test workflow fixture"""

    class TestWorkflow:
        def __init__(self):
            self.users = {}
            self.content = {}
            self.exams = {}
            self.sessions = {}

        def create_test_user(self, user_data=None):
            """Create a test user for workflow"""
            if not user_data:
                user_data = {
                    "email": f"workflow_test_{uuid.uuid4()}@example.com",
                    "ad_soyad": "Workflow Test User",
                    "sifre": "test_password123",
                    "rol": "ogrenci",
                }

            user_id = str(uuid.uuid4())
            user = {
                "kullanici_id": user_id,
                "email": user_data["email"],
                "ad_soyad": user_data["ad_soyad"],
                "rol": user_data["rol"],
                "olusturma_tarihi": datetime.now(),
            }

            self.users[user_id] = user
            return user

        def create_test_content(self, content_data=None):
            """Create test content for workflow"""
            if not content_data:
                content_data = {
                    "baslik": "Workflow Test Content",
                    "icerik": "This is test content for workflow testing.",
                    "kategori": "Test",
                    "yazar": "Workflow Tester",
                }

            content_id = str(uuid.uuid4())
            content = {
                "content_id": content_id,
                **content_data,
                "olusturma_tarihi": datetime.now(),
            }

            self.content[content_id] = content
            return content

        def create_test_exam(self, user_id, exam_data=None):
            """Create test exam for workflow"""
            if user_id not in self.users:
                raise ValueError("User not found")

            if not exam_data:
                exam_data = {
                    "sinav_tipi": "TYT",
                    "toplam_soru_sayisi": 10,
                    "sure_dakika": 30,
                }

            exam_id = str(uuid.uuid4())
            exam = {
                "sinav_id": exam_id,
                "ogrenci_id": user_id,
                **exam_data,
                "durum": "hazir",
                "olusturma_tarihi": datetime.now(),
            }

            self.exams[exam_id] = exam
            return exam

        def simulate_exam_completion(self, exam_id, answers=None):
            """Simulate exam completion"""
            if exam_id not in self.exams:
                raise ValueError("Exam not found")

            exam = self.exams[exam_id]

            if not answers:
                # Generate random answers
                answers = {}
                for i in range(exam["toplam_soru_sayisi"]):
                    answers[f"q_{i}"] = "B"  # Mock all correct answers

            # Calculate scores
            correct = len(answers)
            wrong = 0
            blank = exam["toplam_soru_sayisi"] - correct
            net_score = correct - (wrong * 0.25)

            result = {
                "sonuc_id": str(uuid.uuid4()),
                "sinav_id": exam_id,
                "ogrenci_id": exam["ogrenci_id"],
                "dogru_sayisi": correct,
                "yanlis_sayisi": wrong,
                "bos_sayisi": blank,
                "net_sayisi": net_score,
                "ham_puan": net_score * 5,  # Mock scoring
                "tamamlanma_tarihi": datetime.now(),
            }

            # Update exam status
            exam["durum"] = "tamamlandi"

            return result

        def get_user_progress(self, user_id):
            """Get user progress summary"""
            if user_id not in self.users:
                raise ValueError("User not found")

            user_exams = [e for e in self.exams.values() if e["ogrenci_id"] == user_id]
            completed_exams = [e for e in user_exams if e["durum"] == "tamamlandi"]

            return {
                "user_id": user_id,
                "total_exams": len(user_exams),
                "completed_exams": len(completed_exams),
                "completion_rate": len(completed_exams) / len(user_exams)
                if user_exams
                else 0,
                "last_activity": max([e["olusturma_tarihi"] for e in user_exams])
                if user_exams
                else None,
            }

    return TestWorkflow()


# ==================== PERFORMANCE FIXTURES ====================


@pytest.fixture
def performance_test_data():
    """Data for performance testing"""
    return {
        "large_content": "x" * 50000,  # 50KB content
        "many_users": [
            {
                "email": f"perf_user_{i}@example.com",
                "ad_soyad": f"Performance User {i}",
                "rol": "ogrenci",
            }
            for i in range(100)
        ],
        "many_questions": [
            {
                "soru_id": f"perf_q_{i}",
                "soru_metni": f"Performance test question {i}?",
                "secenekler": ["A) 1", "B) 2", "C) 3", "D) 4"],
                "dogru_cevap": "A",
                "konu": "Performance",
            }
            for i in range(1000)
        ],
    }


@pytest.fixture
def load_test_simulator():
    """Load testing simulator"""

    class LoadTestSimulator:
        def __init__(self):
            self.concurrent_requests = 0
            self.total_requests = 0
            self.response_times = []

        def simulate_concurrent_requests(self, count, operation_func):
            """Simulate concurrent requests"""
            import threading
            import time

            results = []
            threads = []

            def worker():
                start_time = time.time()
                try:
                    result = operation_func()
                    end_time = time.time()
                    response_time = end_time - start_time

                    results.append(
                        {
                            "success": True,
                            "response_time": response_time,
                            "result": result,
                        }
                    )
                    self.response_times.append(response_time)
                except Exception as e:
                    results.append(
                        {"success": False, "error": str(e), "response_time": None}
                    )

            # Create and start threads
            for i in range(count):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

            self.total_requests += count

            return {
                "total_requests": count,
                "successful_requests": len([r for r in results if r["success"]]),
                "failed_requests": len([r for r in results if not r["success"]]),
                "average_response_time": sum(self.response_times)
                / len(self.response_times)
                if self.response_times
                else 0,
                "max_response_time": max(self.response_times)
                if self.response_times
                else 0,
                "min_response_time": min(self.response_times)
                if self.response_times
                else 0,
            }

    return LoadTestSimulator()


# ==================== SECURITY FIXTURES ====================


@pytest.fixture
def security_test_payloads():
    """Security testing payloads"""
    return {
        "xss_payloads": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",
        ],
        "sql_injection_payloads": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; UPDATE users SET password='hacked'; --",
            "1' UNION SELECT * FROM users--",
        ],
        "path_traversal_payloads": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ],
        "large_payloads": {
            "oversized_string": "A" * 1000000,  # 1MB string
            "deep_json": {"level_" + str(i): {"data": "test"} for i in range(1000)},
        },
    }


# ==================== VALIDATION FIXTURES ====================


@pytest.fixture
def validation_test_cases():
    """Validation test cases for different scenarios"""
    return {
        "user_validation": {
            "valid_emails": [
                "test@example.com",
                "user.name@domain.co.uk",
                "student123@university.edu.tr",
            ],
            "invalid_emails": ["not-an-email", "@domain.com", "user@", "user@.com", ""],
            "valid_passwords": ["password123", "SecureP@ss123", "myverylongpassword"],
            "invalid_passwords": ["123", "pass", "", "     "],
        },
        "content_validation": {
            "valid_titles": [
                "Valid Title",
                "Matematik Dersi - Trigonometri",
                "Test İçerik Başlığı",
            ],
            "invalid_titles": ["", "AB", "A" * 300],  # Too short  # Too long
            "valid_content": [
                "Bu yeterince uzun bir içerik metnidir. Test amaçlı yazılmış.",
                "Matematik konusunda detaylı açıklamalar içeren bir makale içeriği.",
            ],
            "invalid_content": ["", "Kısa", "X" * 100000],  # Too short  # Too long
        },
    }


# ==================== UTILITY FUNCTIONS ====================


def create_test_user_data(role="ogrenci", **kwargs):
    """Create test user data with defaults"""
    base_data = {
        "email": f"test_{uuid.uuid4()}@example.com",
        "ad_soyad": "Test User",
        "telefon": "05551234567",
        "sifre": "test_password123",
        "rol": role,
        "aktif": True,
    }
    base_data.update(kwargs)
    return base_data


def create_test_content_data(content_type="makale", **kwargs):
    """Create test content data with defaults"""
    base_data = {
        "baslik": f"Test {content_type.title()}",
        "kategori": "Test",
        "yazar": "Test Author",
        "etiketler": ["test"],
        "zorluk_seviyesi": "orta",
    }

    if content_type == "makale":
        base_data["icerik"] = "Bu bir test makalesidir. İçerik yeterince uzun olmalı."
    elif content_type == "video":
        base_data["video_url"] = "https://example.com/test-video.mp4"
        base_data["sure_dakika"] = 10
        base_data["aciklama"] = "Test video açıklaması"
    elif content_type == "quiz":
        base_data["aciklama"] = "Test quiz açıklaması"
        base_data["sorular"] = [
            {
                "soru_metni": "Test sorusu?",
                "secenekler": ["A) 1", "B) 2", "C) 3", "D) 4"],
                "dogru_cevap": 1,
            }
        ]

    base_data.update(kwargs)
    return base_data


def assert_api_response_structure(response, expected_fields=None):
    """Assert API response has expected structure"""
    assert isinstance(response, dict), "Response should be a dictionary"

    if expected_fields:
        for field in expected_fields:
            assert field in response, f"Field '{field}' missing from response"

    # Common API response fields
    common_fields = ["success"]
    for field in common_fields:
        if field in response:
            assert isinstance(
                response[field], bool
            ), f"Field '{field}' should be boolean"


def generate_test_id(prefix="test"):
    """Generate unique test ID"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def mock_datetime_now(fixed_datetime=None):
    """Mock datetime.now() for consistent testing"""
    if not fixed_datetime:
        fixed_datetime = datetime(2024, 1, 1, 12, 0, 0)

    return fixed_datetime
