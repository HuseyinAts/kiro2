"""
Unit tests for api/soru_bankasi.py

Tests all endpoints with mocked service and cache dependencies.
No DB or Redis connections required — everything is mocked.
"""

import sys

sys.path.insert(0, "C:/Users/husey/kiro2/backend")

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.dependencies import AuthenticatedUser

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_FAKE_USER = AuthenticatedUser(
    id="user-42", username="user-42", role="student", email="test@kiro2.com"
)
_ADMIN_USER = AuthenticatedUser(
    id="admin-1", username="admin-1", role="admin", email="admin@kiro2.com"
)
_SERVISI = "api.soru_bankasi.soru_bankasi_servisi"
_CACHE_OBJ = "api.soru_bankasi.question_cache"
# get_cache is imported inside the function body: `from core.redis_cache import get_cache`
_REDIS_GET_CACHE = "core.redis_cache.get_cache"


# ---------------------------------------------------------------------------
# Mock builders
# ---------------------------------------------------------------------------


def _make_question_mock(
    qid: str = "qid-001",
    exam_type_val: str = "TYT",
    subject_val: str = "MATEMATIK",
    difficulty_val: str = "MEDIUM",
    times_asked: int = 10,
    times_correct: int = 7,
) -> MagicMock:
    """Build a mock Question ORM object (question_bank model columns)."""
    q = MagicMock()
    q.id = qid
    q.question_text = "Test sorusu metni"
    q.question_image_url = None
    q.option_a = "A seçeneği"
    q.option_b = "B seçeneği"
    q.option_c = "C seçeneği"
    q.option_d = "D seçeneği"
    q.option_e = "E seçeneği"
    q.correct_answer = "C"
    q.explanation = "Açıklama"
    q.exam_type = exam_type_val
    q.subject_area = subject_val
    q.primary_topic_id = "Cebir"
    q.difficulty_level = MagicMock()
    q.difficulty_level.value = difficulty_val
    q.irt_difficulty = 0.5
    q.irt_discrimination = 1.2
    q.irt_guessing = 0.25
    q.morphology_complexity = 0.35
    q.readability_score = 0.72
    q.times_asked = times_asked
    q.times_correct = times_correct
    q.average_response_time = 45.0
    q.created_at = datetime(2026, 1, 1, 12, 0, 0)
    q.updated_at = datetime(2026, 1, 2, 12, 0, 0)
    q.is_active = True
    return q


def _make_rastgele_mock(
    qid: str = "rq-001",
    konu: str = "Matematik",
    sinav_tipi: str = "TYT",
) -> MagicMock:
    """Build a mock for Turkish-column question returned by rastgele endpoint."""
    q = MagicMock()
    q.id = qid
    q.kod = "KIRO-001"
    q.metin = "Rastgele soru metni"
    q.secenekler = {"A": "a", "B": "b", "C": "c", "D": "d"}
    q.dogru_cevap = "A"
    q.konu = konu
    q.sinav_tipi = sinav_tipi
    q.zorluk = "kolay"
    q.irt_difficulty = -0.3
    return q


def _make_cache_mock(computed_result=None) -> MagicMock:
    """Return a MultiLayerCache mock that returns computed_result."""
    mc = MagicMock()
    mc._initialized = True
    mc.initialize = AsyncMock()
    mc.get_or_compute = AsyncMock(
        return_value=computed_result if computed_result is not None else []
    )
    mc.clear = AsyncMock()
    return mc


def _make_redis_mock(connected: bool = False, cached=None) -> MagicMock:
    """Return a synchronous Redis cache mock."""
    rc = MagicMock()
    rc.is_connected.return_value = connected
    rc.get.return_value = cached
    rc.set = MagicMock()
    return rc


# ---------------------------------------------------------------------------
# App factory — builds a fresh FastAPI app with dependency overrides set
# ---------------------------------------------------------------------------


def _build_app():
    """Build a FastAPI test app including the soru_bankasi router."""
    from api.soru_bankasi import router
    from core.database import get_db_session
    from core.dependencies import get_current_user

    app = FastAPI()
    app.include_router(router)

    # Override FastAPI dependency injection for DB and auth
    app.dependency_overrides[get_db_session] = lambda: AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: _FAKE_USER

    return app


# ---------------------------------------------------------------------------
# Module-level app + client (re-built once per test session)
# ---------------------------------------------------------------------------


def _build_admin_app():
    """Build a FastAPI test app with admin user override (for write-protected endpoints)."""
    from api.soru_bankasi import router
    from core.database import get_db_session
    from core.dependencies import get_current_user

    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_db_session] = lambda: AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: _ADMIN_USER

    return app


@pytest.fixture(scope="module")
def app_and_client():
    """Return (app, client) pair. App is built fresh so overrides are reliable."""
    app = _build_app()
    client = TestClient(app, raise_server_exceptions=False)
    return app, client


@pytest.fixture(scope="module")
def client(app_and_client):
    _, c = app_and_client
    return c


@pytest.fixture(scope="module")
def admin_client():
    """Client with admin user override — for write-protected endpoints."""
    app = _build_admin_app()
    return TestClient(app, raise_server_exceptions=False)


# ===========================================================================
# GET /health  (no dependencies — simplest tests first)
# ===========================================================================


class TestHealthCheck:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_success_flag(self, client):
        response = client.get("/health")
        assert response.json()["success"] is True

    def test_health_service_name(self, client):
        response = client.get("/health")
        assert response.json()["data"]["service"] == "Soru Bankası API"

    def test_health_status_healthy(self, client):
        response = client.get("/health")
        assert response.json()["data"]["status"] == "healthy"

    def test_health_features_list_not_empty(self, client):
        response = client.get("/health")
        features = response.json()["data"]["features"]
        assert isinstance(features, list)
        assert len(features) > 0


# ===========================================================================
# GET /sorular
# ===========================================================================


class TestSorularListele:
    def test_sorular_listele_returns_200(self, client):
        mc = _make_cache_mock(computed_result=[])
        with patch(_CACHE_OBJ, mc):
            response = client.get("/sorular")
        assert response.status_code == 200

    def test_sorular_listele_success_flag(self, client):
        mc = _make_cache_mock(computed_result=[])
        with patch(_CACHE_OBJ, mc):
            response = client.get("/sorular")
        assert response.json()["success"] is True

    def test_sorular_listele_empty_list(self, client):
        mc = _make_cache_mock(computed_result=[])
        with patch(_CACHE_OBJ, mc):
            response = client.get("/sorular")
        body = response.json()
        assert body["count"] == 0
        assert body["data"] == []

    def test_sorular_listele_count_matches_data(self, client):
        one_question = {
            "id": "q1",
            "question_text": "Soru",
            "options": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
            "correct_answer": "A",
            "explanation": "",
            "exam_type": "TYT",
            "subject_area": "MATEMATIK",
            "topic": "Cebir",
            "subtopic": None,
            "difficulty": "MEDIUM",
            "irt_parameters": {
                "difficulty": 0.0,
                "discrimination": 1.0,
                "guessing": 0.25,
            },
            "morphology_complexity": 0.3,
            "readability_score": 0.7,
            "statistics": {
                "times_asked": 5,
                "times_correct": 3,
                "success_rate": 0.6,
                "average_response_time": 40.0,
            },
            "created_at": "2026-01-01T00:00:00",
            "is_active": True,
        }
        mc = _make_cache_mock(computed_result=[one_question])
        with patch(_CACHE_OBJ, mc):
            response = client.get("/sorular")
        body = response.json()
        assert body["count"] == 1
        assert body["data"][0]["id"] == "q1"

    def test_sorular_listele_cache_error_returns_500(self, client):
        mc = _make_cache_mock()
        mc.get_or_compute = AsyncMock(side_effect=RuntimeError("cache down"))
        with patch(_CACHE_OBJ, mc):
            response = client.get("/sorular")
        assert response.status_code == 500

    def test_sorular_listele_with_sinav_tipi_filter(self, client):
        mc = _make_cache_mock(computed_result=[])
        with patch(_CACHE_OBJ, mc):
            response = client.get("/sorular?sinav_tipi=TYT")
        assert response.status_code == 200

    def test_sorular_listele_invalid_limit_rejected(self, client):
        mc = _make_cache_mock()
        with patch(_CACHE_OBJ, mc):
            response = client.get("/sorular?limit=0")
        assert response.status_code == 422

    def test_sorular_listele_limit_too_large_rejected(self, client):
        mc = _make_cache_mock()
        with patch(_CACHE_OBJ, mc):
            response = client.get("/sorular?limit=501")
        assert response.status_code == 422

    def test_sorular_listele_message_contains_count(self, client):
        mc = _make_cache_mock(computed_result=[])
        with patch(_CACHE_OBJ, mc):
            response = client.get("/sorular")
        assert "soru" in response.json()["message"].lower()


# ===========================================================================
# GET /soru/{soru_id}
# ===========================================================================


class TestSoruDetay:
    def test_soru_detay_returns_200_when_found(self, client):
        mock_q = _make_question_mock()
        with patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=mock_q)):
            response = client.get("/soru/qid-001")
        assert response.status_code == 200

    def test_soru_detay_success_flag(self, client):
        mock_q = _make_question_mock()
        with patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=mock_q)):
            response = client.get("/soru/qid-001")
        assert response.json()["success"] is True

    def test_soru_detay_id_in_response(self, client):
        mock_q = _make_question_mock(qid="abc-123")
        with patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=mock_q)):
            response = client.get("/soru/abc-123")
        assert response.json()["data"]["id"] == "abc-123"

    def test_soru_detay_returns_404_when_not_found(self, client):
        with patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=None)):
            response = client.get("/soru/nonexistent-id")
        assert response.status_code == 404

    def test_soru_detay_404_detail_message(self, client):
        with patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=None)):
            response = client.get("/soru/nonexistent-id")
        detail = response.json()["detail"]
        assert isinstance(detail, str)
        assert "bulunamadı" in detail.lower()

    def test_soru_detay_service_error_returns_500(self, client):
        with patch(
            _SERVISI + ".soru_getir",
            new=AsyncMock(side_effect=RuntimeError("db error")),
        ):
            response = client.get("/soru/qid-001")
        assert response.status_code == 500

    def test_soru_detay_irt_parameters_present(self, client):
        mock_q = _make_question_mock()
        with patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=mock_q)):
            response = client.get("/soru/qid-001")
        data = response.json()["data"]
        assert "irt_parameters" in data
        assert data["irt_parameters"]["difficulty"] == pytest.approx(0.5)

    def test_soru_detay_statistics_success_rate(self, client):
        mock_q = _make_question_mock(times_asked=10, times_correct=8)
        with patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=mock_q)):
            response = client.get("/soru/qid-001")
        stats = response.json()["data"]["statistics"]
        assert stats["success_rate"] == pytest.approx(0.8)

    def test_soru_detay_options_structure(self, client):
        mock_q = _make_question_mock()
        with patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=mock_q)):
            response = client.get("/soru/qid-001")
        options = response.json()["data"]["options"]
        assert set(options.keys()) == {"A", "B", "C", "D", "E"}


# ===========================================================================
# GET /rastgele-sorular
# ===========================================================================


class TestRastgeleSorular:
    """get_cache is imported inside the function body with `from core.redis_cache import get_cache`,
    so we must patch it at the source: core.redis_cache.get_cache."""

    _PATCH_TARGET = "core.redis_cache.get_cache"

    def test_rastgele_sorular_returns_200(self, client):
        mock_q = _make_rastgele_mock()
        rc = _make_redis_mock()
        with (
            patch(
                _SERVISI + ".rastgele_sorular_sec", new=AsyncMock(return_value=[mock_q])
            ),
            patch(self._PATCH_TARGET, return_value=rc),
        ):
            response = client.get("/rastgele-sorular?sinav_tipi=TYT&soru_sayisi=1")
        assert response.status_code == 200

    def test_rastgele_sorular_success_flag(self, client):
        rc = _make_redis_mock()
        with (
            patch(_SERVISI + ".rastgele_sorular_sec", new=AsyncMock(return_value=[])),
            patch(self._PATCH_TARGET, return_value=rc),
        ):
            response = client.get("/rastgele-sorular?sinav_tipi=TYT&soru_sayisi=5")
        assert response.json()["success"] is True

    def test_rastgele_sorular_invalid_sinav_tipi_returns_400(self, client):
        rc = _make_redis_mock()
        with (
            patch(_SERVISI + ".rastgele_sorular_sec", new=AsyncMock(return_value=[])),
            patch(self._PATCH_TARGET, return_value=rc),
        ):
            response = client.get("/rastgele-sorular?sinav_tipi=INVALID&soru_sayisi=5")
        assert response.status_code == 400

    def test_rastgele_sorular_invalid_json_konu_dagilimi_returns_400(self, client):
        rc = _make_redis_mock()
        with (
            patch(_SERVISI + ".rastgele_sorular_sec", new=AsyncMock(return_value=[])),
            patch(self._PATCH_TARGET, return_value=rc),
        ):
            response = client.get(
                "/rastgele-sorular?sinav_tipi=TYT&soru_sayisi=5&konu_dagilimi=not-valid-json"
            )
        assert response.status_code == 400

    def test_rastgele_sorular_cache_hit_skips_service(self, client):
        cached_payload = {
            "success": True,
            "data": {
                "sorular": [],
                "secilen_soru_sayisi": 0,
                "istenen_soru_sayisi": 5,
                "konu_dagilimi": {},
            },
            "message": "0 soru başarıyla seçildi",
        }
        rc = _make_redis_mock(connected=True, cached=cached_payload)
        mock_service = AsyncMock()
        with (
            patch(_SERVISI + ".rastgele_sorular_sec", mock_service),
            patch(self._PATCH_TARGET, return_value=rc),
        ):
            response = client.get("/rastgele-sorular?sinav_tipi=TYT&soru_sayisi=5")
        assert response.status_code == 200
        mock_service.assert_not_called()

    def test_rastgele_sorular_konu_dagilimi_counted(self, client):
        mock_q = _make_rastgele_mock(konu="Fizik")
        rc = _make_redis_mock()
        with (
            patch(
                _SERVISI + ".rastgele_sorular_sec",
                new=AsyncMock(return_value=[mock_q, mock_q]),
            ),
            patch(self._PATCH_TARGET, return_value=rc),
        ):
            response = client.get("/rastgele-sorular?sinav_tipi=TYT&soru_sayisi=2")
        konu_dagilimi = response.json()["data"]["konu_dagilimi"]
        assert konu_dagilimi.get("Fizik") == 2

    def test_rastgele_sorular_service_error_returns_500(self, client):
        rc = _make_redis_mock()
        with (
            patch(
                _SERVISI + ".rastgele_sorular_sec",
                new=AsyncMock(side_effect=RuntimeError("db down")),
            ),
            patch(self._PATCH_TARGET, return_value=rc),
        ):
            response = client.get("/rastgele-sorular?sinav_tipi=AYT&soru_sayisi=3")
        assert response.status_code == 500

    def test_rastgele_sorular_secilen_soru_sayisi_in_response(self, client):
        mock_q = _make_rastgele_mock()
        rc = _make_redis_mock()
        with (
            patch(
                _SERVISI + ".rastgele_sorular_sec", new=AsyncMock(return_value=[mock_q])
            ),
            patch(self._PATCH_TARGET, return_value=rc),
        ):
            response = client.get("/rastgele-sorular?sinav_tipi=TYT&soru_sayisi=1")
        data = response.json()["data"]
        assert data["secilen_soru_sayisi"] == 1
        assert data["istenen_soru_sayisi"] == 1


# ===========================================================================
# GET /konular
# ===========================================================================


class TestKonuListesi:
    def test_konular_returns_200(self, client):
        with patch(
            _SERVISI + ".konu_listesi_getir",
            new=AsyncMock(return_value=["Matematik", "Fizik"]),
        ):
            response = client.get("/konular")
        assert response.status_code == 200

    def test_konular_count_matches(self, client):
        with patch(
            _SERVISI + ".konu_listesi_getir",
            new=AsyncMock(return_value=["Matematik", "Fizik", "Kimya"]),
        ):
            response = client.get("/konular")
        assert response.json()["count"] == 3

    def test_konular_success_flag(self, client):
        with patch(_SERVISI + ".konu_listesi_getir", new=AsyncMock(return_value=[])):
            response = client.get("/konular")
        assert response.json()["success"] is True

    def test_konular_data_list(self, client):
        konular = ["Türkçe", "Matematik"]
        with patch(
            _SERVISI + ".konu_listesi_getir", new=AsyncMock(return_value=konular)
        ):
            response = client.get("/konular")
        assert response.json()["data"] == konular

    def test_konular_service_error_returns_500(self, client):
        with patch(
            _SERVISI + ".konu_listesi_getir",
            new=AsyncMock(side_effect=RuntimeError("fail")),
        ):
            response = client.get("/konular")
        assert response.status_code == 500


# ===========================================================================
# GET /istatistikler
# ===========================================================================


class TestIstatistikler:
    def test_istatistikler_returns_200(self, client):
        with patch(
            _SERVISI + ".istatistikler_getir",
            new=AsyncMock(return_value={"total": 77336}),
        ):
            response = client.get("/istatistikler")
        assert response.status_code == 200

    def test_istatistikler_data_passthrough(self, client):
        stats = {"total": 77336, "active": 77000}
        with patch(
            _SERVISI + ".istatistikler_getir", new=AsyncMock(return_value=stats)
        ):
            response = client.get("/istatistikler")
        assert response.json()["data"]["total"] == 77336

    def test_istatistikler_success_flag(self, client):
        with patch(_SERVISI + ".istatistikler_getir", new=AsyncMock(return_value={})):
            response = client.get("/istatistikler")
        assert response.json()["success"] is True

    def test_istatistikler_service_error_returns_500(self, client):
        with patch(
            _SERVISI + ".istatistikler_getir",
            new=AsyncMock(side_effect=RuntimeError("db fail")),
        ):
            response = client.get("/istatistikler")
        assert response.status_code == 500


# ===========================================================================
# POST /soru-performans-guncelle
# ===========================================================================


class TestSoruPerformansGuncelle:
    _URL = "/soru-performans-guncelle?soru_id={sid}&dogru_cevap={dc}&cevap_suresi={cs}"

    def test_performans_guncelle_returns_200_on_success(self, client):
        url = self._URL.format(sid="q1", dc="true", cs="30.0")
        with patch(
            _SERVISI + ".soru_performans_guncelle", new=AsyncMock(return_value=True)
        ):
            response = client.post(url)
        assert response.status_code == 200

    def test_performans_guncelle_success_flag(self, client):
        url = self._URL.format(sid="q1", dc="false", cs="15.5")
        with patch(
            _SERVISI + ".soru_performans_guncelle", new=AsyncMock(return_value=True)
        ):
            response = client.post(url)
        assert response.json()["success"] is True

    def test_performans_guncelle_response_contains_soru_id(self, client):
        url = self._URL.format(sid="abc-q1", dc="true", cs="20.0")
        with patch(
            _SERVISI + ".soru_performans_guncelle", new=AsyncMock(return_value=True)
        ):
            response = client.post(url)
        assert response.json()["data"]["soru_id"] == "abc-q1"

    def test_performans_guncelle_returns_404_when_not_found(self, client):
        url = self._URL.format(sid="missing", dc="true", cs="10.0")
        with patch(
            _SERVISI + ".soru_performans_guncelle", new=AsyncMock(return_value=False)
        ):
            response = client.post(url)
        assert response.status_code == 404

    def test_performans_guncelle_invalid_cevap_suresi_rejected(self, client):
        url = self._URL.format(sid="q1", dc="true", cs="0.0")
        with patch(
            _SERVISI + ".soru_performans_guncelle", new=AsyncMock(return_value=True)
        ):
            response = client.post(url)
        assert response.status_code == 422

    def test_performans_guncelle_service_error_returns_500(self, client):
        url = self._URL.format(sid="q1", dc="true", cs="10.0")
        with patch(
            _SERVISI + ".soru_performans_guncelle",
            new=AsyncMock(side_effect=RuntimeError("db fail")),
        ):
            response = client.post(url)
        assert response.status_code == 500


# ===========================================================================
# POST /soru-ekle
# ===========================================================================


class TestSoruEkle:
    _VALID_PAYLOAD = {
        "soru_metni": "2+2 kaçtır?",
        "secenekler": ["1", "2", "3", "4"],
        "dogru_cevap": "D",
        "sinav_tipi": "TYT",
        "konu": "Matematik",
        "zorluk_seviyesi": "kolay",
    }

    def test_soru_ekle_returns_201(self, client):
        mock_q = _make_question_mock()
        mc = _make_cache_mock()
        with (
            patch(_SERVISI + ".soru_ekle", new=AsyncMock(return_value=mock_q)),
            patch(_CACHE_OBJ, mc),
        ):
            response = client.post("/soru-ekle", json=self._VALID_PAYLOAD)
        assert response.status_code == 201

    def test_soru_ekle_success_flag(self, client):
        mock_q = _make_question_mock()
        mc = _make_cache_mock()
        with (
            patch(_SERVISI + ".soru_ekle", new=AsyncMock(return_value=mock_q)),
            patch(_CACHE_OBJ, mc),
        ):
            response = client.post("/soru-ekle", json=self._VALID_PAYLOAD)
        assert response.json()["success"] is True

    def test_soru_ekle_irt_params_in_response(self, client):
        mock_q = _make_question_mock()
        mc = _make_cache_mock()
        with (
            patch(_SERVISI + ".soru_ekle", new=AsyncMock(return_value=mock_q)),
            patch(_CACHE_OBJ, mc),
        ):
            response = client.post("/soru-ekle", json=self._VALID_PAYLOAD)
        assert "irt_parameters" in response.json()["data"]

    def test_soru_ekle_missing_soru_metni_returns_422(self, client):
        bad = {k: v for k, v in self._VALID_PAYLOAD.items() if k != "soru_metni"}
        response = client.post("/soru-ekle", json=bad)
        assert response.status_code == 422

    def test_soru_ekle_missing_secenekler_returns_422(self, client):
        bad = {k: v for k, v in self._VALID_PAYLOAD.items() if k != "secenekler"}
        response = client.post("/soru-ekle", json=bad)
        assert response.status_code == 422

    def test_soru_ekle_service_error_returns_500(self, client):
        mc = _make_cache_mock()
        with (
            patch(
                _SERVISI + ".soru_ekle",
                new=AsyncMock(side_effect=RuntimeError("write failed")),
            ),
            patch(_CACHE_OBJ, mc),
        ):
            response = client.post("/soru-ekle", json=self._VALID_PAYLOAD)
        assert response.status_code == 500


# ===========================================================================
# PUT /soru-guncelle/{soru_id}
# ===========================================================================


class TestSoruGuncelle:
    """PUT /soru-guncelle/{soru_id} — requires admin or teacher role.

    NOTE: The endpoint compares role.value against lowercase ("admin", "teacher").
    UserRole enum stores uppercase values ("ADMIN", "TEACHER"), so the check
    never passes via standard enum values. All roles currently receive 403.
    Tests document this actual behaviour.
    """

    def test_soru_guncelle_student_role_returns_403(self, client):
        """Student role is rejected with 403."""
        response = client.put("/soru-guncelle/qid-001", json={"dogru_cevap": "A"})
        assert response.status_code == 403

    @pytest.mark.xfail(
        reason="BUG: role guard compares UPPERCASE enum value against lowercase string literal",
        strict=True,
    )
    def test_soru_guncelle_admin_role_should_return_200(self, admin_client):
        """Admin should be able to update questions — currently blocked by case mismatch.

        Production bug: role.value ('ADMIN') compared against 'admin' literal.
        Fix: change guard to role.value.lower() or compare against ('ADMIN', 'TEACHER').
        When fixed, this test will start passing and xfail will flag it.
        """
        mc = _make_cache_mock()
        with (
            patch(_SERVISI + ".soru_guncelle", new=AsyncMock(return_value=None)),
            patch(_CACHE_OBJ, mc),
        ):
            response = admin_client.put(
                "/soru-guncelle/qid-001", json={"dogru_cevap": "A"}
            )
        assert response.status_code == 200

    def test_soru_guncelle_403_detail_message(self, client):
        """403 response contains a readable Turkish error message."""
        response = client.put("/soru-guncelle/qid-001", json={"dogru_cevap": "A"})
        detail = response.json()["detail"]
        assert isinstance(detail, str)
        assert len(detail) > 0


# ===========================================================================
# DELETE /soru-sil/{soru_id}
# ===========================================================================


class TestSoruSil:
    """DELETE /soru-sil/{soru_id} — requires admin or teacher role.

    Same role-case mismatch as TestSoruGuncelle: all roles currently receive 403.
    Tests document the actual runtime behaviour.
    """

    def test_soru_sil_student_role_returns_403(self, client):
        """Student role is rejected with 403."""
        response = client.delete("/soru-sil/qid-001")
        assert response.status_code == 403

    @pytest.mark.xfail(
        reason="BUG: role guard compares UPPERCASE enum value against lowercase string literal",
        strict=True,
    )
    def test_soru_sil_admin_role_should_return_200(self, admin_client):
        """Admin should be able to delete questions — currently blocked by case mismatch."""
        with patch(_SERVISI + ".soru_sil", new=AsyncMock(return_value=True)):
            response = admin_client.delete("/soru-sil/qid-001")
        assert response.status_code == 200

    def test_soru_sil_403_detail_message(self, client):
        """403 response body contains a non-empty detail string."""
        response = client.delete("/soru-sil/qid-001")
        detail = response.json()["detail"]
        assert isinstance(detail, str)
        assert len(detail) > 0


# ===========================================================================
# POST /toplu-soru-ekle
# ===========================================================================


class TestTopluSoruEkle:
    _PAYLOAD = {
        "sorular": [
            {
                "soru_metni": "Soru 1",
                "secenekler": ["A", "B", "C", "D"],
                "dogru_cevap": "A",
                "konu": "Fizik",
            },
            {
                "soru_metni": "Soru 2",
                "secenekler": ["A", "B", "C", "D"],
                "dogru_cevap": "B",
                "konu": "Kimya",
            },
        ]
    }

    def test_toplu_soru_ekle_returns_201(self, client):
        result = {"basarili": 2, "toplam": 2, "hatali": 0}
        mc = _make_cache_mock()
        with (
            patch(_SERVISI + ".toplu_soru_ekle", new=AsyncMock(return_value=result)),
            patch(_CACHE_OBJ, mc),
        ):
            response = client.post("/toplu-soru-ekle", json=self._PAYLOAD)
        assert response.status_code == 201

    def test_toplu_soru_ekle_success_flag(self, client):
        result = {"basarili": 2, "toplam": 2, "hatali": 0}
        mc = _make_cache_mock()
        with (
            patch(_SERVISI + ".toplu_soru_ekle", new=AsyncMock(return_value=result)),
            patch(_CACHE_OBJ, mc),
        ):
            response = client.post("/toplu-soru-ekle", json=self._PAYLOAD)
        assert response.json()["success"] is True

    def test_toplu_soru_ekle_message_contains_counts(self, client):
        result = {"basarili": 2, "toplam": 2, "hatali": 0}
        mc = _make_cache_mock()
        with (
            patch(_SERVISI + ".toplu_soru_ekle", new=AsyncMock(return_value=result)),
            patch(_CACHE_OBJ, mc),
        ):
            response = client.post("/toplu-soru-ekle", json=self._PAYLOAD)
        assert "2/2" in response.json()["message"]

    def test_toplu_soru_ekle_service_error_returns_500(self, client):
        mc = _make_cache_mock()
        with (
            patch(
                _SERVISI + ".toplu_soru_ekle",
                new=AsyncMock(side_effect=RuntimeError("bulk fail")),
            ),
            patch(_CACHE_OBJ, mc),
        ):
            response = client.post("/toplu-soru-ekle", json=self._PAYLOAD)
        assert response.status_code == 500

    def test_toplu_soru_ekle_data_in_response(self, client):
        result = {"basarili": 1, "toplam": 2, "hatali": 1}
        mc = _make_cache_mock()
        with (
            patch(_SERVISI + ".toplu_soru_ekle", new=AsyncMock(return_value=result)),
            patch(_CACHE_OBJ, mc),
        ):
            response = client.post("/toplu-soru-ekle", json=self._PAYLOAD)
        assert response.json()["data"]["hatali"] == 1


# ===========================================================================
# POST /irt-parametreleri-yeniden-hesapla/{soru_id}
# ===========================================================================


class TestIrtParametreleriYenidenHesapla:
    def test_irt_hesapla_returns_200_on_success(self, client):
        mock_q = _make_question_mock(times_asked=15, times_correct=9)
        with (
            patch(
                _SERVISI + ".irt_parametrelerini_yeniden_hesapla",
                new=AsyncMock(return_value=True),
            ),
            patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=mock_q)),
        ):
            response = client.post("/irt-parametreleri-yeniden-hesapla/qid-001")
        assert response.status_code == 200

    def test_irt_hesapla_success_flag(self, client):
        mock_q = _make_question_mock()
        with (
            patch(
                _SERVISI + ".irt_parametrelerini_yeniden_hesapla",
                new=AsyncMock(return_value=True),
            ),
            patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=mock_q)),
        ):
            response = client.post("/irt-parametreleri-yeniden-hesapla/qid-001")
        assert response.json()["success"] is True

    def test_irt_hesapla_new_params_in_response(self, client):
        mock_q = _make_question_mock()
        with (
            patch(
                _SERVISI + ".irt_parametrelerini_yeniden_hesapla",
                new=AsyncMock(return_value=True),
            ),
            patch(_SERVISI + ".soru_getir", new=AsyncMock(return_value=mock_q)),
        ):
            response = client.post("/irt-parametreleri-yeniden-hesapla/qid-001")
        data = response.json()["data"]
        assert "yeni_irt_parametreleri" in data
        assert data["yeni_irt_parametreleri"]["difficulty"] == pytest.approx(0.5)

    def test_irt_hesapla_returns_400_when_insufficient_data(self, client):
        with patch(
            _SERVISI + ".irt_parametrelerini_yeniden_hesapla",
            new=AsyncMock(return_value=False),
        ):
            response = client.post("/irt-parametreleri-yeniden-hesapla/qid-001")
        assert response.status_code == 400

    def test_irt_hesapla_400_detail_contains_minimum(self, client):
        with patch(
            _SERVISI + ".irt_parametrelerini_yeniden_hesapla",
            new=AsyncMock(return_value=False),
        ):
            response = client.post("/irt-parametreleri-yeniden-hesapla/qid-001")
        detail = response.json()["detail"]
        assert "10" in detail

    def test_irt_hesapla_service_exception_returns_500(self, client):
        with patch(
            _SERVISI + ".irt_parametrelerini_yeniden_hesapla",
            new=AsyncMock(side_effect=RuntimeError("crash")),
        ):
            response = client.post("/irt-parametreleri-yeniden-hesapla/qid-001")
        assert response.status_code == 500


# ===========================================================================
# GET /zorluk-filtrele
# ===========================================================================


class TestZorlukFiltrele:
    _BASE_URL = "/zorluk-filtrele?ogrenci_yetenek=0.0&sinav_tipi=TYT"

    def test_zorluk_filtrele_returns_200(self, client):
        mock_q = _make_question_mock()
        with patch(
            _SERVISI + ".zorluk_seviyesi_filtrele",
            new=AsyncMock(return_value=[mock_q]),
        ):
            response = client.get(self._BASE_URL)
        assert response.status_code == 200

    def test_zorluk_filtrele_success_flag(self, client):
        with patch(
            _SERVISI + ".zorluk_seviyesi_filtrele",
            new=AsyncMock(return_value=[]),
        ):
            response = client.get(self._BASE_URL)
        assert response.json()["success"] is True

    def test_zorluk_filtrele_empty_list(self, client):
        with patch(
            _SERVISI + ".zorluk_seviyesi_filtrele",
            new=AsyncMock(return_value=[]),
        ):
            response = client.get(self._BASE_URL)
        data = response.json()["data"]
        assert data["toplam_soru"] == 0
        assert data["sorular"] == []

    def test_zorluk_filtrele_returns_ogrenci_yetenek(self, client):
        with patch(
            _SERVISI + ".zorluk_seviyesi_filtrele",
            new=AsyncMock(return_value=[]),
        ):
            response = client.get(self._BASE_URL + "&tolerans=0.5")
        data = response.json()["data"]
        assert data["ogrenci_yetenek"] == pytest.approx(0.0)

    def test_zorluk_filtrele_zorluk_araligi_correct(self, client):
        with patch(
            _SERVISI + ".zorluk_seviyesi_filtrele",
            new=AsyncMock(return_value=[]),
        ):
            response = client.get(self._BASE_URL + "&tolerans=1.0")
        zorluk_araligi = response.json()["data"]["zorluk_araligi"]
        assert zorluk_araligi["min"] == pytest.approx(-1.0)
        assert zorluk_araligi["max"] == pytest.approx(1.0)

    def test_zorluk_filtrele_recommended_flag_within_tolerance(self, client):
        """Questions within tolerance should have recommended=True."""
        mock_q = _make_question_mock()
        mock_q.irt_difficulty = 0.3  # |0.3 - 0.0| = 0.3 <= 1.0 tolerance
        with patch(
            _SERVISI + ".zorluk_seviyesi_filtrele",
            new=AsyncMock(return_value=[mock_q]),
        ):
            response = client.get(self._BASE_URL + "&tolerans=1.0")
        soru = response.json()["data"]["sorular"][0]
        assert soru["recommended"] is True

    def test_zorluk_filtrele_ogrenci_yetenek_out_of_range_rejected(self, client):
        response = client.get("/zorluk-filtrele?ogrenci_yetenek=5.0&sinav_tipi=TYT")
        assert response.status_code == 422

    def test_zorluk_filtrele_service_error_returns_500(self, client):
        with patch(
            _SERVISI + ".zorluk_seviyesi_filtrele",
            new=AsyncMock(side_effect=RuntimeError("db down")),
        ):
            response = client.get(self._BASE_URL)
        assert response.status_code == 500

    def test_zorluk_filtrele_message_contains_soru(self, client):
        with patch(
            _SERVISI + ".zorluk_seviyesi_filtrele",
            new=AsyncMock(return_value=[]),
        ):
            response = client.get(self._BASE_URL)
        assert "soru" in response.json()["message"].lower()


# ===========================================================================
# POST /irt-parametreli-sorular
# ===========================================================================


class TestIrtParametreliSorular:
    _BASE_PARAMS = "?ogrenci_yetenek=0.0&sinav_tipi=TYT&soru_sayisi=5"

    def test_irt_sorular_returns_200(self, client):
        mock_q = _make_question_mock()
        with (
            patch(
                _SERVISI + ".irt_parametreli_soru_sec",
                new=AsyncMock(return_value=[mock_q]),
            ),
            patch(
                _SERVISI + "._hesapla_bilgi_fonksiyonu",
                new=AsyncMock(return_value=1.5),
            ),
        ):
            response = client.post("/irt-parametreli-sorular" + self._BASE_PARAMS)
        assert response.status_code == 200

    def test_irt_sorular_success_flag(self, client):
        with (
            patch(
                _SERVISI + ".irt_parametreli_soru_sec",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                _SERVISI + "._hesapla_bilgi_fonksiyonu",
                new=AsyncMock(return_value=0.0),
            ),
        ):
            response = client.post("/irt-parametreli-sorular" + self._BASE_PARAMS)
        assert response.json()["success"] is True

    def test_irt_sorular_returns_ogrenci_yetenek(self, client):
        with (
            patch(
                _SERVISI + ".irt_parametreli_soru_sec",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                _SERVISI + "._hesapla_bilgi_fonksiyonu",
                new=AsyncMock(return_value=0.0),
            ),
        ):
            response = client.post("/irt-parametreli-sorular" + self._BASE_PARAMS)
        data = response.json()["data"]
        assert data["ogrenci_yetenek"] == pytest.approx(0.0)

    def test_irt_sorular_adaptasyon_kalitesi_yuksek(self, client):
        """High information value (>1.0) should produce 'yüksek' quality."""
        mock_q = _make_question_mock()
        with (
            patch(
                _SERVISI + ".irt_parametreli_soru_sec",
                new=AsyncMock(return_value=[mock_q]),
            ),
            patch(
                _SERVISI + "._hesapla_bilgi_fonksiyonu",
                new=AsyncMock(return_value=1.5),
            ),
        ):
            response = client.post("/irt-parametreli-sorular" + self._BASE_PARAMS)
        assert response.json()["data"]["adaptasyon_kalitesi"] == "yüksek"

    def test_irt_sorular_adaptasyon_kalitesi_dusuk(self, client):
        """Low information value (<0.5) should produce 'düşük' quality."""
        mock_q = _make_question_mock()
        with (
            patch(
                _SERVISI + ".irt_parametreli_soru_sec",
                new=AsyncMock(return_value=[mock_q]),
            ),
            patch(
                _SERVISI + "._hesapla_bilgi_fonksiyonu",
                new=AsyncMock(return_value=0.3),
            ),
        ):
            response = client.post("/irt-parametreli-sorular" + self._BASE_PARAMS)
        assert response.json()["data"]["adaptasyon_kalitesi"] == "düşük"

    def test_irt_sorular_ogrenci_yetenek_out_of_range_rejected(self, client):
        response = client.post(
            "/irt-parametreli-sorular?ogrenci_yetenek=4.0&sinav_tipi=TYT&soru_sayisi=5"
        )
        assert response.status_code == 422

    def test_irt_sorular_soru_sayisi_too_large_rejected(self, client):
        response = client.post(
            "/irt-parametreli-sorular?ogrenci_yetenek=0.0&sinav_tipi=TYT&soru_sayisi=101"
        )
        assert response.status_code == 422

    def test_irt_sorular_service_error_returns_500(self, client):
        with patch(
            _SERVISI + ".irt_parametreli_soru_sec",
            new=AsyncMock(side_effect=RuntimeError("service down")),
        ):
            response = client.post("/irt-parametreli-sorular" + self._BASE_PARAMS)
        assert response.status_code == 500

    def test_irt_sorular_irt_parameters_in_soru_dict(self, client):
        """Each returned question must expose its IRT parameters."""
        mock_q = _make_question_mock()
        with (
            patch(
                _SERVISI + ".irt_parametreli_soru_sec",
                new=AsyncMock(return_value=[mock_q]),
            ),
            patch(
                _SERVISI + "._hesapla_bilgi_fonksiyonu",
                new=AsyncMock(return_value=1.2),
            ),
        ):
            response = client.post("/irt-parametreli-sorular" + self._BASE_PARAMS)
        soru = response.json()["data"]["sorular"][0]
        assert "irt_parameters" in soru
        assert "difficulty_match" in soru
