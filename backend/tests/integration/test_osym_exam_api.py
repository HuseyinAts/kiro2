"""
ÖSYM Sınav API Endpoint Testleri
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül ÖSYM sınav API endpoint'lerinin tüm fonksiyonalitelerini test eder:
- Sınav oluşturma ve başlatma
- Soru navigasyonu ve cevap kaydetme
- Performans analizi ve raporlama
- Hata durumları ve güvenlik kontrolleri
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Import centralized JWT helper from conftest (DRY)
try:
    from tests.conftest import (
        _generate_test_jwt,
        TEST_JWT_SECRET,
        TEST_JWT_ALGORITHM,
    )
except ImportError:
    import jwt as _jwt
    TEST_JWT_SECRET = "test-secret-key-for-testing"
    TEST_JWT_ALGORITHM = "HS256"
    def _generate_test_jwt(user_id="1", email="test@test.com", role="student"):
        import time
        payload = {"sub": user_id, "email": email, "role": role, "exp": int(time.time()) + 3600}
        return _jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)

from core.osym_exam_engine import (
    ExamPerformanceMetrics,
    ExamSessionData,
    ExamStatus,
    OSYMExamConfig,
    SubjectPerformance,
)
from main import app
from models.database import ExamType, User


class TestOSYMExamAPI:
    """ÖSYM Sınav API test sınıfı"""

    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Test kullanıcısı"""
        user = User(
            id="test_user_123",
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
        )
        return user

    @pytest.fixture
    def auth_headers(self, monkeypatch):
        """Generate valid JWT authentication headers for testing."""
        monkeypatch.setattr("core.dependencies.JWT_SECRET", TEST_JWT_SECRET)
        monkeypatch.setattr("core.dependencies.JWT_ALGORITHM", TEST_JWT_ALGORITHM)

        token = _generate_test_jwt("1", "test@example.com", "student")
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def mock_session_data(self):
        """Mock sınav oturum verisi"""
        config = OSYMExamConfig(
            exam_type=ExamType.TYT,
            total_questions=120,
            duration_minutes=165,
            subject_distribution={
                "TURKCE": 40,
                "MATEMATIK": 40,
                "FEN": 20,
                "SOSYAL": 20,
            },
        )

        return ExamSessionData(
            session_id="test_session_123",
            student_id="test_user_123",
            exam_config=config,
            status=ExamStatus.NOT_STARTED,
            questions=["q1", "q2", "q3"],
        )

    @pytest.fixture
    def mock_question(self):
        """Mock soru"""
        return MagicMock(
            id="q1",
            question_text="Test sorusu",
            option_a="A seçeneği",
            option_b="B seçeneği",
            option_c="C seçeneği",
            option_d="D seçeneği",
            option_e=None,
            subject_area=MagicMock(value="matematik"),
            topic="Test konusu",
            difficulty=MagicMock(value="medium"),
        )

    def test_create_exam_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Başarılı sınav oluşturma testi"""
        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.create_exam_session",
            return_value="test_session_123",
        ), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ):
            response = client.post(
                "/api/v1/osym-exam/create",
                headers=auth_headers,
                json={"exam_type": "TYT", "custom_config": {"duration_minutes": 165}},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["session_id"] == "test_session_123"
            assert data["student_id"] == "test_user_123"
            assert data["exam_type"] == "TYT"
            assert data["status"] == "not_started"
            assert data["total_questions"] == 120
            assert data["duration_minutes"] == 165

    def test_create_exam_insufficient_questions(self, client, auth_headers, mock_user):
        """Yetersiz soru durumunda hata testi"""
        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.create_exam_session",
            side_effect=ValueError("Yeterli soru bulunamadı"),
        ):
            response = client.post(
                "/api/v1/osym-exam/create",
                headers=auth_headers,
                json={"exam_type": "TYT"},
            )

            assert response.status_code == 400
            assert "Yeterli soru bulunamadı" in response.json()["detail"]

    def test_create_exam_unauthorized(self, client):
        """Yetkisiz erişim testi"""
        response = client.post("/api/v1/osym-exam/create", json={"exam_type": "TYT"})

        assert response.status_code == 401

    def test_start_exam_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Başarılı sınav başlatma testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS
        mock_session_data.started_at = datetime.now()

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.start_exam", return_value=mock_session_data
        ):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/start", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["session_id"] == "test_session_123"
            assert data["status"] == "in_progress"
            assert data["started_at"] is not None

    def test_start_exam_not_found(self, client, auth_headers, mock_user):
        """Var olmayan sınav başlatma testi"""
        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data", return_value=None
        ):
            response = client.post(
                "/api/v1/osym-exam/nonexistent/start", headers=auth_headers
            )

            assert response.status_code == 404
            assert "Sınav oturumu bulunamadı" in response.json()["detail"]

    def test_start_exam_forbidden(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Başka kullanıcının sınavını başlatma testi"""
        mock_session_data.student_id = "other_user"

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/start", headers=auth_headers
            )

            assert response.status_code == 403
            assert "Bu sınava erişim yetkiniz yok" in response.json()["detail"]

    def test_start_exam_already_started(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Zaten başlatılmış sınav testi"""
        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.start_exam",
            side_effect=ValueError("Sınav zaten başlatılmış"),
        ):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/start", headers=auth_headers
            )

            assert response.status_code == 400
            assert "Sınav zaten başlatılmış" in response.json()["detail"]

    def test_get_current_question_success(
        self, client, auth_headers, mock_user, mock_session_data, mock_question
    ):
        """Mevcut soru getirme başarılı testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.get_current_question",
            return_value=mock_question,
        ):
            response = client.get(
                "/api/v1/osym-exam/test_session_123/current-question",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == "q1"
            assert data["question_text"] == "Test sorusu"
            assert data["option_a"] == "A seçeneği"
            assert data["subject_area"] == "matematik"
            assert data["question_order"] == 1  # current_question_index + 1

    def test_get_current_question_not_found(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Soru bulunamadı testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch("api.sinav.osym_exam_engine.get_current_question", return_value=None):
            response = client.get(
                "/api/v1/osym-exam/test_session_123/current-question",
                headers=auth_headers,
            )

            assert response.status_code == 404
            assert "Mevcut soru bulunamadı" in response.json()["detail"]

    def test_save_answer_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Başarılı cevap kaydetme testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch("api.sinav.osym_exam_engine.save_answer", return_value=True):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/save-answer",
                headers=auth_headers,
                json={
                    "question_id": "q1",
                    "selected_answer": "A",
                    "response_time": 30.5,
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["message"] == "Cevap başarıyla kaydedildi"
            assert data["auto_saved"] is True

    def test_save_answer_failed(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Cevap kaydetme başarısız testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch("api.sinav.osym_exam_engine.save_answer", return_value=False):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/save-answer",
                headers=auth_headers,
                json={"question_id": "q1", "selected_answer": "A"},
            )

            assert response.status_code == 400
            assert "Cevap kaydedilemedi" in response.json()["detail"]

    def test_navigate_to_question_success(
        self, client, auth_headers, mock_user, mock_session_data, mock_question
    ):
        """Başarılı soru navigasyonu testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.navigate_to_question",
            return_value=mock_question,
        ):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/navigate",
                headers=auth_headers,
                json={"question_index": 5},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == "q1"
            assert data["question_order"] == 6  # question_index + 1

    def test_navigate_to_question_invalid_index(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Geçersiz soru indeksi navigasyon testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch("api.sinav.osym_exam_engine.navigate_to_question", return_value=None):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/navigate",
                headers=auth_headers,
                json={"question_index": 999},
            )

            assert response.status_code == 404
            assert "Hedef soru bulunamadı" in response.json()["detail"]

    def test_flag_question_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Başarılı soru işaretleme testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch("api.sinav.osym_exam_engine.flag_question", return_value=True):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/flag-question",
                headers=auth_headers,
                json={"question_id": "q1", "flagged": True},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["message"] == "Soru işaretleme durumu güncellendi"
            assert data["flagged"] is True

    def test_get_remaining_time_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Kalan süre getirme başarılı testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.get_remaining_time", return_value=7200
        ):  # 2 saat
            response = client.get(
                "/api/v1/osym-exam/test_session_123/remaining-time",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["remaining_seconds"] == 7200
            assert data["remaining_minutes"] == 120
            assert data["formatted_time"] == "02:00:00"
            assert data["warning"] is False  # 120 dakika > 15 dakika uyarı süresi
            assert data["exam_status"] == "in_progress"

    def test_get_remaining_time_warning(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Kalan süre uyarı testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.get_remaining_time", return_value=600
        ):  # 10 dakika
            response = client.get(
                "/api/v1/osym-exam/test_session_123/remaining-time",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["remaining_seconds"] == 600
            assert data["remaining_minutes"] == 10
            assert data["formatted_time"] == "10:00"
            assert data["warning"] is True  # 10 dakika <= 15 dakika uyarı süresi

    def test_get_remaining_time_not_started(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Başlatılmamış sınavda kalan süre testi"""
        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch("api.sinav.osym_exam_engine.get_remaining_time", return_value=None):
            response = client.get(
                "/api/v1/osym-exam/test_session_123/remaining-time",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["remaining_seconds"] is None
            assert data["remaining_minutes"] is None
            assert data["formatted_time"] == "Sınav başlatılmamış"
            assert data["warning"] is False

    def test_complete_exam_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Başarılı sınav tamamlama testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        mock_performance = ExamPerformanceMetrics(
            total_questions=120,
            answered_questions=100,
            correct_answers=80,
            wrong_answers=20,
            empty_answers=20,
            net_score=75.0,
            raw_score=66.67,
            percentile=85.5,
            estimated_ability=1.2,
            confidence_level=0.95,
        )

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.complete_exam", return_value=mock_performance
        ):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/complete", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["total_questions"] == 120
            assert data["answered_questions"] == 100
            assert data["correct_answers"] == 80
            assert data["wrong_answers"] == 20
            assert data["empty_answers"] == 20
            assert data["net_score"] == 75.0
            assert data["raw_score"] == 66.67
            assert data["percentile"] == 85.5
            assert data["estimated_ability"] == 1.2
            assert data["confidence_level"] == 0.95

    def test_complete_exam_error(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Sınav tamamlama hatası testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.complete_exam",
            side_effect=ValueError("Sınav tamamlanamadı"),
        ):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/complete", headers=auth_headers
            )

            assert response.status_code == 400
            assert "Sınav tamamlanamadı" in response.json()["detail"]

    def test_get_session_info_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Oturum bilgileri getirme başarılı testi"""
        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ):
            response = client.get(
                "/api/v1/osym-exam/test_session_123/session", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["session_id"] == "test_session_123"
            assert data["student_id"] == "test_user_123"
            assert data["exam_type"] == "TYT"
            assert data["status"] == "not_started"
            assert data["total_questions"] == 120
            assert data["duration_minutes"] == 165

    def test_get_performance_analysis_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Performans analizi getirme başarılı testi"""
        mock_performance = ExamPerformanceMetrics(
            total_questions=120,
            answered_questions=100,
            correct_answers=80,
            wrong_answers=20,
            empty_answers=20,
            net_score=75.0,
            raw_score=66.67,
            estimated_ability=1.2,
            confidence_level=0.95,
        )

        mock_session_data.performance_metrics = mock_performance

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ):
            response = client.get(
                "/api/v1/osym-exam/test_session_123/performance", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["total_questions"] == 120
            assert data["net_score"] == 75.0
            assert data["estimated_ability"] == 1.2

    def test_get_performance_analysis_not_completed(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Tamamlanmamış sınavda performans analizi testi"""
        mock_session_data.performance_metrics = None

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ):
            response = client.get(
                "/api/v1/osym-exam/test_session_123/performance", headers=auth_headers
            )

            assert response.status_code == 400
            assert "Sınav henüz tamamlanmamış" in response.json()["detail"]

    def test_get_subject_performance_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Konu performansı getirme başarılı testi"""
        mock_subject_performances = [
            SubjectPerformance(
                subject="matematik",
                total_questions=40,
                correct_answers=30,
                wrong_answers=8,
                empty_answers=2,
                success_rate=75.0,
                average_response_time=45.5,
                difficulty_level=0.8,
            ),
            SubjectPerformance(
                subject="turkce",
                total_questions=40,
                correct_answers=32,
                wrong_answers=6,
                empty_answers=2,
                success_rate=80.0,
                average_response_time=38.2,
                difficulty_level=0.6,
            ),
        ]

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.get_subject_performance",
            return_value=mock_subject_performances,
        ):
            response = client.get(
                "/api/v1/osym-exam/test_session_123/subject-performance",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data) == 2

            # Matematik performansı
            math_perf = data[0]
            assert math_perf["subject"] == "matematik"
            assert math_perf["total_questions"] == 40
            assert math_perf["correct_answers"] == 30
            assert math_perf["success_rate"] == 75.0

            # Türkçe performansı
            turkish_perf = data[1]
            assert turkish_perf["subject"] == "turkce"
            assert turkish_perf["success_rate"] == 80.0

    def test_get_my_exams_success(self, client, auth_headers, mock_user):
        """Kullanıcı sınavları listeleme başarılı testi"""
        # Mock active sessions
        mock_sessions = {
            "session1": ExamSessionData(
                session_id="session1",
                student_id="test_user_123",
                exam_config=OSYMExamConfig(ExamType.TYT, 120, 165, {}),
                status=ExamStatus.COMPLETED,
            ),
            "session2": ExamSessionData(
                session_id="session2",
                student_id="test_user_123",
                exam_config=OSYMExamConfig(ExamType.AYT, 160, 210, {}),
                status=ExamStatus.IN_PROGRESS,
            ),
            "session3": ExamSessionData(
                session_id="session3",
                student_id="other_user",
                exam_config=OSYMExamConfig(ExamType.TYT, 120, 165, {}),
                status=ExamStatus.NOT_STARTED,
            ),
        }

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.active_sessions", mock_sessions
        ):
            response = client.get("/api/v1/osym-exam/my-exams", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()

            # Sadece kullanıcının sınavları döndürülmeli
            assert len(data) == 2

            session_ids = [exam["session_id"] for exam in data]
            assert "session1" in session_ids
            assert "session2" in session_ids
            assert "session3" not in session_ids  # Başka kullanıcının sınavı

    def test_get_my_exams_pagination(self, client, auth_headers, mock_user):
        """Kullanıcı sınavları sayfalama testi"""
        # 5 mock session oluştur
        mock_sessions = {}
        for i in range(5):
            session_id = f"session_{i}"
            mock_sessions[session_id] = ExamSessionData(
                session_id=session_id,
                student_id="test_user_123",
                exam_config=OSYMExamConfig(ExamType.TYT, 120, 165, {}),
                status=ExamStatus.NOT_STARTED,
            )

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.active_sessions", mock_sessions
        ):
            # İlk sayfa (limit=2)
            response = client.get(
                "/api/v1/osym-exam/my-exams?limit=2&offset=0", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

            # İkinci sayfa
            response = client.get(
                "/api/v1/osym-exam/my-exams?limit=2&offset=2", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    def test_get_exam_configs_success(self, client):
        """Sınav konfigürasyonları getirme başarılı testi"""
        response = client.get("/api/v1/osym-exam/exam-configs")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "exam_configs" in data

        configs = data["exam_configs"]

        # TYT konfigürasyonu kontrolü
        assert "TYT" in configs
        tyt_config = configs["TYT"]
        assert tyt_config["total_questions"] == 120
        assert tyt_config["duration_minutes"] == 165
        assert tyt_config["subject_distribution"]["TURKCE"] == 40

        # AYT konfigürasyonu kontrolü
        assert "AYT" in configs
        ayt_config = configs["AYT"]
        assert ayt_config["total_questions"] == 160
        assert ayt_config["duration_minutes"] == 210

        # YDT konfigürasyonu kontrolü
        assert "YDT" in configs
        ydt_config = configs["YDT"]
        assert ydt_config["total_questions"] == 80
        assert ydt_config["duration_minutes"] == 180

    def test_cancel_exam_success(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Başarılı sınav iptal etme testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ), patch(
            "api.sinav.osym_exam_engine.auto_save_tasks",
            {"test_session_123": MagicMock()},
        ):
            response = client.delete(
                "/api/v1/osym-exam/test_session_123", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["message"] == "Sınav başarıyla iptal edildi"
            assert data["session_id"] == "test_session_123"

            # Session durumunun değiştiğini kontrol et
            assert mock_session_data.status == ExamStatus.ABANDONED

    def test_cancel_exam_already_completed(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Tamamlanmış sınavı iptal etme testi"""
        mock_session_data.status = ExamStatus.COMPLETED

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ):
            response = client.delete(
                "/api/v1/osym-exam/test_session_123", headers=auth_headers
            )

            assert response.status_code == 400
            assert (
                "Tamamlanmış veya iptal edilmiş sınavlar" in response.json()["detail"]
            )

    def test_invalid_exam_type(self, client, auth_headers, mock_user):
        """Geçersiz sınav türü testi"""
        with patch("api.sinav.get_current_user", return_value=mock_user):
            response = client.post(
                "/api/v1/osym-exam/create",
                headers=auth_headers,
                json={"exam_type": "INVALID_TYPE"},
            )

            assert response.status_code == 422  # Validation error

    def test_invalid_question_index(
        self, client, auth_headers, mock_user, mock_session_data
    ):
        """Geçersiz soru indeksi testi"""
        mock_session_data.status = ExamStatus.IN_PROGRESS

        with patch("api.sinav.get_current_user", return_value=mock_user), patch(
            "api.sinav.osym_exam_engine.get_session_data",
            return_value=mock_session_data,
        ):
            response = client.post(
                "/api/v1/osym-exam/test_session_123/navigate",
                headers=auth_headers,
                json={"question_index": -1},  # Negatif indeks
            )

            assert response.status_code == 422  # Validation error


class TestOSYMExamAPIIntegration:
    """ÖSYM Sınav API entegrasyon testleri"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, monkeypatch):
        """Generate valid JWT authentication headers for testing."""
        monkeypatch.setattr("core.dependencies.JWT_SECRET", TEST_JWT_SECRET)
        monkeypatch.setattr("core.dependencies.JWT_ALGORITHM", TEST_JWT_ALGORITHM)

        token = _generate_test_jwt("1", "test@example.com", "student")
        return {"Authorization": f"Bearer {token}"}

    def test_full_exam_workflow_api(self, client, auth_headers):
        """Tam sınav akışı API entegrasyon testi"""
        mock_user = User(
            id="integration_test",
            email="test@test.com",
            username="test",
            first_name="Test",
            last_name="User",
        )

        with patch("api.sinav.get_current_user", return_value=mock_user):
            # 1. Sınav oluştur
            with patch(
                "api.sinav.osym_exam_engine.create_exam_session",
                return_value="test_session",
            ), patch("api.sinav.osym_exam_engine.get_session_data") as mock_get_session:
                # Mock session data for create
                mock_session = ExamSessionData(
                    session_id="test_session",
                    student_id="integration_test",
                    exam_config=OSYMExamConfig(ExamType.TYT, 120, 165, {}),
                    status=ExamStatus.NOT_STARTED,
                )
                mock_get_session.return_value = mock_session

                create_response = client.post(
                    "/api/v1/osym-exam/create",
                    headers=auth_headers,
                    json={"exam_type": "TYT"},
                )

                assert create_response.status_code == 200
                session_id = create_response.json()["session_id"]

            # 2. Sınavı başlat
            with patch(
                "api.sinav.osym_exam_engine.get_session_data", return_value=mock_session
            ), patch("api.sinav.osym_exam_engine.start_exam") as mock_start:
                mock_session.status = ExamStatus.IN_PROGRESS
                mock_session.started_at = datetime.now()
                mock_start.return_value = mock_session

                start_response = client.post(
                    f"/api/v1/osym-exam/{session_id}/start", headers=auth_headers
                )

                assert start_response.status_code == 200
                assert start_response.json()["status"] == "in_progress"

            # 3. Mevcut soruyu getir
            with patch(
                "api.sinav.osym_exam_engine.get_session_data", return_value=mock_session
            ), patch(
                "api.sinav.osym_exam_engine.get_current_question"
            ) as mock_get_question:
                mock_question = MagicMock(
                    id="q1",
                    question_text="Test",
                    option_a="A",
                    option_b="B",
                    option_c="C",
                    option_d="D",
                    option_e=None,
                    subject_area=MagicMock(value="matematik"),
                    topic="Test",
                    difficulty=MagicMock(value="medium"),
                )
                mock_get_question.return_value = mock_question

                question_response = client.get(
                    f"/api/v1/osym-exam/{session_id}/current-question",
                    headers=auth_headers,
                )

                assert question_response.status_code == 200
                assert question_response.json()["id"] == "q1"

            # 4. Cevap kaydet
            with patch(
                "api.sinav.osym_exam_engine.get_session_data", return_value=mock_session
            ), patch("api.sinav.osym_exam_engine.save_answer", return_value=True):
                answer_response = client.post(
                    f"/api/v1/osym-exam/{session_id}/save-answer",
                    headers=auth_headers,
                    json={
                        "question_id": "q1",
                        "selected_answer": "A",
                        "response_time": 30.0,
                    },
                )

                assert answer_response.status_code == 200
                assert answer_response.json()["success"] is True

            # 5. Sınavı tamamla
            with patch(
                "api.sinav.osym_exam_engine.get_session_data", return_value=mock_session
            ), patch("api.sinav.osym_exam_engine.complete_exam") as mock_complete:
                mock_performance = ExamPerformanceMetrics(
                    total_questions=120,
                    answered_questions=1,
                    correct_answers=1,
                    wrong_answers=0,
                    empty_answers=119,
                    net_score=1.0,
                    raw_score=0.83,
                    estimated_ability=0.5,
                    confidence_level=0.1,
                )
                mock_complete.return_value = mock_performance

                complete_response = client.post(
                    f"/api/v1/osym-exam/{session_id}/complete", headers=auth_headers
                )

                assert complete_response.status_code == 200
                performance_data = complete_response.json()
                assert performance_data["total_questions"] == 120
                assert performance_data["correct_answers"] == 1
                assert performance_data["net_score"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
