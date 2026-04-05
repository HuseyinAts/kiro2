"""
Unit / integration tests for admin panel API (api/admin.py).

Strategy:
- Mount only the admin router on a minimal FastAPI app (avoids full application startup).
- Override `get_current_user` and `get_db` with lightweight mocks.
- `admin_kullanici_getir` depends on `get_current_user`, so overriding that
  dependency is sufficient to control both auth and role checks.
- DB is mocked with AsyncMock — no real database required.

Coverage targets:
  GET  /api/v1/admin/users                     — list users
  POST /api/v1/admin/users                     — create user (501)
  GET  /api/v1/admin/users/{id}                — user detail
  PUT  /api/v1/admin/users/{id}                — update user
  DELETE /api/v1/admin/users/{id}              — deactivate user
  GET  /api/v1/admin/dashboard/stats           — dashboard stats
  GET  /api/v1/admin/content/questions         — question bank list
  POST /api/v1/admin/content/questions         — add question
  PUT  /api/v1/admin/content/questions/{id}    — update question
  DELETE /api/v1/admin/content/questions/{id}  — delete question
  GET  /api/v1/admin/content/educational       — educational materials (stub)
  GET  /api/v1/admin/content/search            — full-text search
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# Ensure backend is on sys.path
_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32-chars")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars")

from core.dependencies import AuthenticatedUser, get_current_user, get_db  # noqa: E402
from models.enums_db import UserRole  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers — pre-built mock users
# ---------------------------------------------------------------------------


def _make_admin_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id=1,
        username="admin",
        role=UserRole.ADMIN,
        email="admin@test.com",
    )


def _make_student_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id=2,
        username="student",
        role=UserRole.STUDENT,
        email="student@test.com",
    )


# ---------------------------------------------------------------------------
# Fixture — minimal FastAPI app with only the admin router
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def admin_app() -> FastAPI:
    """Minimal FastAPI app that mounts the admin router."""
    from api.admin import router as admin_router

    app = FastAPI()
    app.include_router(admin_router)
    return app


# ---------------------------------------------------------------------------
# Fixture — AsyncClient with admin auth + mock DB
# ---------------------------------------------------------------------------


def _make_mock_db() -> AsyncMock:
    """Build an AsyncMock that satisfies SQLAlchemy AsyncSession usage."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    # execute returns a result object; configure per-test if you need specific data
    db.execute = AsyncMock()
    return db


@pytest_asyncio.fixture
async def admin_client(admin_app: FastAPI):
    """AsyncClient authenticated as admin with a mocked DB."""
    mock_db = _make_mock_db()

    async def _override_get_current_user() -> AuthenticatedUser:
        return _make_admin_user()

    async def _override_get_db():
        yield mock_db

    admin_app.dependency_overrides[get_current_user] = _override_get_current_user
    admin_app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client._mock_db = mock_db  # expose for per-test configuration
        yield client

    admin_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def student_client(admin_app: FastAPI):
    """AsyncClient authenticated as a non-admin student."""

    async def _override_get_current_user() -> AuthenticatedUser:
        return _make_student_user()

    admin_app.dependency_overrides[get_current_user] = _override_get_current_user
    # No DB override needed — auth check happens before DB access

    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    admin_app.dependency_overrides.clear()


# ===========================================================================
# TESTS: GET /api/v1/admin/users — list users
# ===========================================================================


class TestListUsers:
    """Tests for kullanicilari_listele (GET /api/v1/admin/users)."""

    @pytest.mark.asyncio
    async def test_list_users_returns_200_for_admin(self, admin_client: AsyncClient):
        """Admin user receives 200 with a list payload."""
        # Configure mock DB to return two rows
        mock_row1 = {
            "id": "1",
            "email": "a@test.com",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "A",
            "role": "STUDENT",
            "is_active": True,
            "created_at": "2026-01-01",
            "last_login": None,
            "total_xp": 0,
            "level": 1,
        }
        mock_row2 = {
            "id": "2",
            "email": "b@test.com",
            "username": "bob",
            "first_name": "Bob",
            "last_name": "B",
            "role": "TEACHER",
            "is_active": True,
            "created_at": "2026-01-02",
            "last_login": None,
            "total_xp": 10,
            "level": 2,
        }
        mappings_mock = MagicMock()
        mappings_mock.all.return_value = [mock_row1, mock_row2]
        result_mock = MagicMock()
        result_mock.mappings.return_value = mappings_mock
        admin_client._mock_db.execute = AsyncMock(return_value=result_mock)

        response = await admin_client.get("/api/v1/admin/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["email"] == "a@test.com"

    @pytest.mark.asyncio
    async def test_list_users_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin user receives 403 Forbidden."""
        response = await student_client.get("/api/v1/admin/users")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_users_empty_when_no_users(self, admin_client: AsyncClient):
        """Returns empty list when DB has no rows."""
        mappings_mock = MagicMock()
        mappings_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.mappings.return_value = mappings_mock
        admin_client._mock_db.execute = AsyncMock(return_value=result_mock)

        response = await admin_client.get("/api/v1/admin/users")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_users_accepts_role_filter(self, admin_client: AsyncClient):
        """Role query param is accepted without error."""
        mappings_mock = MagicMock()
        mappings_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.mappings.return_value = mappings_mock
        admin_client._mock_db.execute = AsyncMock(return_value=result_mock)

        response = await admin_client.get("/api/v1/admin/users?rol=STUDENT")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_users_rejects_page_size_exceeding_50(
        self, admin_client: AsyncClient
    ):
        """sayfa_boyutu > 50 is rejected with 422."""
        response = await admin_client.get("/api/v1/admin/users?sayfa_boyutu=99")
        assert response.status_code == 422


# ===========================================================================
# TESTS: POST /api/v1/admin/users — create user (not implemented)
# ===========================================================================


class TestCreateUser:
    """Tests for kullanici_olustur (POST /api/v1/admin/users)."""

    @pytest.mark.asyncio
    async def test_create_user_returns_501(self, admin_client: AsyncClient):
        """Endpoint returns 501 Not Implemented and directs to /auth/kayit."""
        response = await admin_client.post(
            "/api/v1/admin/users",
            json={"email": "new@test.com", "password": "pass"},
        )
        assert response.status_code == 501
        assert "kayit" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_user_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin cannot access this endpoint."""
        response = await student_client.post(
            "/api/v1/admin/users",
            json={"email": "x@test.com"},
        )
        assert response.status_code == 403


# ===========================================================================
# TESTS: GET /api/v1/admin/users/{id} — user detail
# ===========================================================================


class TestUserDetail:
    """Tests for kullanici_detay (GET /api/v1/admin/users/{id})."""

    @pytest.mark.asyncio
    async def test_user_detail_returns_user_data(self, admin_client: AsyncClient):
        """Existing user returns 200 with full details."""
        user_row = {
            "id": "42",
            "email": "u@test.com",
            "username": "user42",
            "first_name": "U",
            "last_name": "42",
            "role": "STUDENT",
            "is_active": True,
            "created_at": "2026-01-01",
            "last_login": None,
            "total_xp": 50,
            "level": 3,
            "phone": None,
        }
        mappings_mock = MagicMock()
        mappings_mock.first.return_value = user_row
        result_mock = MagicMock()
        result_mock.mappings.return_value = mappings_mock
        admin_client._mock_db.execute = AsyncMock(return_value=result_mock)

        response = await admin_client.get("/api/v1/admin/users/42")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "42"
        assert data["email"] == "u@test.com"

    @pytest.mark.asyncio
    async def test_user_detail_returns_404_when_not_found(
        self, admin_client: AsyncClient
    ):
        """Missing user returns 404."""
        mappings_mock = MagicMock()
        mappings_mock.first.return_value = None
        result_mock = MagicMock()
        result_mock.mappings.return_value = mappings_mock
        admin_client._mock_db.execute = AsyncMock(return_value=result_mock)

        response = await admin_client.get("/api/v1/admin/users/9999")

        assert response.status_code == 404
        assert "bulunamadi" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_user_detail_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin cannot view user detail."""
        response = await student_client.get("/api/v1/admin/users/1")
        assert response.status_code == 403


# ===========================================================================
# TESTS: PUT /api/v1/admin/users/{id} — update user
# ===========================================================================


class TestUpdateUser:
    """Tests for kullanici_guncelle (PUT /api/v1/admin/users/{id})."""

    def _configure_update_mock(self, admin_client: AsyncClient, updated_row):
        """Helper: configure DB mock to return updated_row on second execute call."""
        first_result = MagicMock()  # UPDATE execute
        second_mappings = MagicMock()
        second_mappings.first.return_value = updated_row
        second_result = MagicMock()  # SELECT execute
        second_result.mappings.return_value = second_mappings

        call_count = [0]

        async def _execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            return second_result if call_count[0] > 1 else first_result

        admin_client._mock_db.execute = _execute_side_effect

    @pytest.mark.asyncio
    async def test_update_user_is_active(self, admin_client: AsyncClient):
        """Admin can deactivate a user via is_active=false."""
        updated_row = {
            "id": "5",
            "email": "u@test.com",
            "role": "STUDENT",
            "is_active": False,
        }
        self._configure_update_mock(admin_client, updated_row)

        response = await admin_client.put(
            "/api/v1/admin/users/5",
            json={"is_active": False},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_user_role(self, admin_client: AsyncClient):
        """Admin can promote a user to TEACHER role."""
        updated_row = {
            "id": "7",
            "email": "t@test.com",
            "role": "TEACHER",
            "is_active": True,
        }
        self._configure_update_mock(admin_client, updated_row)

        response = await admin_client.put(
            "/api/v1/admin/users/7",
            json={"role": "TEACHER"},
        )

        assert response.status_code == 200
        assert response.json()["data"]["role"] == "TEACHER"

    @pytest.mark.asyncio
    async def test_update_user_invalid_role_returns_400(
        self, admin_client: AsyncClient
    ):
        """Invalid role value returns 400."""
        response = await admin_client.put(
            "/api/v1/admin/users/7",
            json={"role": "SUPERVILLAIN"},
        )
        assert response.status_code == 400
        assert "gecersiz" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_user_empty_payload_returns_400(
        self, admin_client: AsyncClient
    ):
        """No updatable fields in payload returns 400."""
        response = await admin_client.put(
            "/api/v1/admin/users/7",
            json={"unknown_field": "value"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_user_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin cannot update users."""
        response = await student_client.put(
            "/api/v1/admin/users/1",
            json={"is_active": False},
        )
        assert response.status_code == 403


# ===========================================================================
# TESTS: DELETE /api/v1/admin/users/{id} — deactivate user
# ===========================================================================


class TestDeleteUser:
    """Tests for kullanici_sil (DELETE /api/v1/admin/users/{id})."""

    @pytest.mark.asyncio
    async def test_delete_user_soft_deletes_and_returns_200(
        self, admin_client: AsyncClient
    ):
        """Soft delete returns 200 with success message."""
        deleted_row = {"id": "3", "email": "gone@test.com"}
        mappings_mock = MagicMock()
        mappings_mock.first.return_value = deleted_row
        result_mock = MagicMock()
        result_mock.mappings.return_value = mappings_mock
        admin_client._mock_db.execute = AsyncMock(return_value=result_mock)

        response = await admin_client.delete("/api/v1/admin/users/3")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "gone@test.com" in body["message"]
        assert "deaktive" in body["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_user_returns_404_when_not_found(
        self, admin_client: AsyncClient
    ):
        """Deleting non-existent user returns 404."""
        mappings_mock = MagicMock()
        mappings_mock.first.return_value = None
        result_mock = MagicMock()
        result_mock.mappings.return_value = mappings_mock
        admin_client._mock_db.execute = AsyncMock(return_value=result_mock)

        response = await admin_client.delete("/api/v1/admin/users/9999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin cannot delete users."""
        response = await student_client.delete("/api/v1/admin/users/1")
        assert response.status_code == 403


# ===========================================================================
# TESTS: GET /api/v1/admin/dashboard/stats
# ===========================================================================


class TestDashboardStats:
    """Tests for dashboard_istatistikleri (GET /api/v1/admin/dashboard/stats)."""

    def _make_stats_db(self, admin_client: AsyncClient):
        """Configure DB mock for three sequential execute() calls."""
        users_row = {
            "toplam_kullanici": 100,
            "aktif_kullanici": 90,
            "ogrenci": 70,
            "ogretmen": 20,
            "veli": 5,
            "admin": 5,
            "son_30_gun_kayit": 15,
        }
        questions_row = {
            "toplam_soru": 77336,
            "aktif_soru": 64281,
            "kalibre_soru": 50000,
            "calib_pool": 10000,
            "ders_sayisi": 12,
        }
        cat_row = {"session_sayisi": 500}

        call_count = [0]
        results = []
        for row in [users_row, questions_row, cat_row]:
            m = MagicMock()
            m.mappings.return_value.one.return_value = row
            results.append(m)

        async def _execute(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            return results[idx] if idx < len(results) else results[-1]

        admin_client._mock_db.execute = _execute

    @pytest.mark.asyncio
    async def test_dashboard_stats_returns_200(self, admin_client: AsyncClient):
        """Dashboard stats endpoint returns 200 with expected structure."""
        self._make_stats_db(admin_client)

        response = await admin_client.get("/api/v1/admin/dashboard/stats")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "data" in body
        assert "kullanicilar" in body["data"]
        assert "sorular" in body["data"]
        assert "cat_sessions" in body["data"]

    @pytest.mark.asyncio
    async def test_dashboard_stats_kullanici_counts(self, admin_client: AsyncClient):
        """Dashboard correctly exposes user counts."""
        self._make_stats_db(admin_client)

        response = await admin_client.get("/api/v1/admin/dashboard/stats")

        kullanicilar = response.json()["data"]["kullanicilar"]
        assert kullanicilar["toplam_kullanici"] == 100
        assert kullanicilar["aktif_kullanici"] == 90
        assert kullanicilar["ogrenci"] == 70

    @pytest.mark.asyncio
    async def test_dashboard_stats_question_counts(self, admin_client: AsyncClient):
        """Dashboard correctly exposes question counts."""
        self._make_stats_db(admin_client)

        response = await admin_client.get("/api/v1/admin/dashboard/stats")

        sorular = response.json()["data"]["sorular"]
        assert sorular["toplam_soru"] == 77336
        assert sorular["aktif_soru"] == 64281

    @pytest.mark.asyncio
    async def test_dashboard_stats_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin receives 403 on dashboard stats."""
        response = await student_client.get("/api/v1/admin/dashboard/stats")
        assert response.status_code == 403


# ===========================================================================
# TESTS: GET /api/v1/admin/content/questions — question bank list
# ===========================================================================


class TestQuestionBankList:
    """Tests for soru_bankasi_listesi (GET /api/v1/admin/content/questions)."""

    def _configure_question_list_mock(
        self, admin_client: AsyncClient, rows, total: int
    ):
        """Configure two sequential executes: rows query + COUNT query."""
        call_count = [0]

        rows_mappings = MagicMock()
        rows_mappings.all.return_value = rows
        rows_result = MagicMock()
        rows_result.mappings.return_value = rows_mappings

        count_result = MagicMock()
        count_result.scalar.return_value = total

        async def _execute(*args, **kwargs):
            call_count[0] += 1
            return rows_result if call_count[0] == 1 else count_result

        admin_client._mock_db.execute = _execute

    @pytest.mark.asyncio
    async def test_question_list_returns_200(self, admin_client: AsyncClient):
        """Question list returns 200 with success + data + total_count."""
        q_row = {
            "id": "q1",
            "question_text": "2+2=?",
            "subject_area": "matematik",
            "difficulty_level": "EASY",
            "correct_answer": "A",
            "is_calibrated": True,
            "is_calib_pool": False,
            "irt_difficulty": 0.1,
            "irt_discrimination": 1.2,
        }
        self._configure_question_list_mock(admin_client, [q_row], total=1)

        response = await admin_client.get("/api/v1/admin/content/questions")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["total_count"] == 1
        assert body["data"][0]["question_text"] == "2+2=?"

    @pytest.mark.asyncio
    async def test_question_list_accepts_filters(self, admin_client: AsyncClient):
        """konu and zorluk query params are accepted."""
        self._configure_question_list_mock(admin_client, [], total=0)

        response = await admin_client.get(
            "/api/v1/admin/content/questions?konu=fizik&zorluk=HARD"
        )

        assert response.status_code == 200
        assert response.json()["total_count"] == 0

    @pytest.mark.asyncio
    async def test_question_list_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin receives 403."""
        response = await student_client.get("/api/v1/admin/content/questions")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_question_list_rejects_page_size_over_50(
        self, admin_client: AsyncClient
    ):
        """sayfa_boyutu > 50 returns 422."""
        response = await admin_client.get(
            "/api/v1/admin/content/questions?sayfa_boyutu=100"
        )
        assert response.status_code == 422


# ===========================================================================
# TESTS: POST /api/v1/admin/content/questions — add question
# ===========================================================================


class TestAddQuestion:
    """Tests for soru_ekle (POST /api/v1/admin/content/questions)."""

    @pytest.mark.asyncio
    async def test_add_question_success(self, admin_client: AsyncClient):
        """Valid question data returns 200 with success flag."""
        new_question = {
            "id": "newq1",
            "soru_metni": "Soru?",
            "konu": "matematik",
            "zorluk_seviyesi": "ORTA",
            "sinav_tipi": "TYT",
            "dogru_cevap": "B",
            "secenekler": {"A": "1", "B": "2"},
        }
        with patch("api.admin.admin_servisi") as mock_service:
            mock_service.soru_ekle = AsyncMock(return_value=new_question)

            response = await admin_client.post(
                "/api/v1/admin/content/questions",
                json={
                    "soru_metni": "Soru?",
                    "konu": "matematik",
                    "zorluk_seviyesi": "ORTA",
                    "sinav_tipi": "TYT",
                    "dogru_cevap": "B",
                    "secenekler": {"A": "1", "B": "2"},
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["id"] == "newq1"

    @pytest.mark.asyncio
    async def test_add_question_validation_error_returns_400(
        self, admin_client: AsyncClient
    ):
        """Service raises ValueError → endpoint returns 400."""
        with patch("api.admin.admin_servisi") as mock_service:
            mock_service.soru_ekle = AsyncMock(side_effect=ValueError("Alan eksik"))

            response = await admin_client.post(
                "/api/v1/admin/content/questions",
                json={"soru_metni": ""},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_question_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin cannot add questions."""
        response = await student_client.post(
            "/api/v1/admin/content/questions",
            json={"soru_metni": "Soru?"},
        )
        assert response.status_code == 403


# ===========================================================================
# TESTS: PUT /api/v1/admin/content/questions/{id} — update question
# ===========================================================================


class TestUpdateQuestion:
    """Tests for soru_guncelle (PUT /api/v1/admin/content/questions/{id})."""

    @pytest.mark.asyncio
    async def test_update_question_success(self, admin_client: AsyncClient):
        """Valid update returns 200 with updated data."""
        updated = {"id": "q5", "soru_metni": "Updated?", "konu": "fizik"}
        with patch("api.admin.admin_servisi") as mock_service:
            mock_service.soru_guncelle = AsyncMock(return_value=updated)

            response = await admin_client.put(
                "/api/v1/admin/content/questions/q5",
                json={"soru_metni": "Updated?"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["soru_metni"] == "Updated?"

    @pytest.mark.asyncio
    async def test_update_question_not_found_raises_400(
        self, admin_client: AsyncClient
    ):
        """Service raises ValueError for unknown id → 400."""
        with patch("api.admin.admin_servisi") as mock_service:
            mock_service.soru_guncelle = AsyncMock(
                side_effect=ValueError("Soru bulunamadi")
            )

            response = await admin_client.put(
                "/api/v1/admin/content/questions/doesnotexist",
                json={"soru_metni": "x"},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_question_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin cannot update questions."""
        response = await student_client.put(
            "/api/v1/admin/content/questions/q1",
            json={"soru_metni": "x"},
        )
        assert response.status_code == 403


# ===========================================================================
# TESTS: DELETE /api/v1/admin/content/questions/{id} — delete question
# ===========================================================================


class TestDeleteQuestion:
    """Tests for soru_sil (DELETE /api/v1/admin/content/questions/{id})."""

    @pytest.mark.asyncio
    async def test_delete_question_success(self, admin_client: AsyncClient):
        """Deleting existing question returns 200 with success message."""
        with patch("api.admin.admin_servisi") as mock_service:
            mock_service.soru_sil = AsyncMock(return_value=True)

            response = await admin_client.delete("/api/v1/admin/content/questions/q1")

        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_delete_question_returns_500_when_not_found(
        self, admin_client: AsyncClient
    ):
        """Service returns False → endpoint currently returns 500.

        BUG (api/admin.py soru_sil): the bare `except Exception` at line 369
        catches the HTTPException(404) raised on line 366 and replaces it with
        a 500.  The correct fix is to add `except HTTPException: raise` before
        the bare except, matching the pattern used in kullanici_sil.
        This test documents the current (buggy) behaviour so any fix shows up
        as a test change that must be reviewed.
        """
        with patch("api.admin.admin_servisi") as mock_service:
            mock_service.soru_sil = AsyncMock(return_value=False)

            response = await admin_client.delete(
                "/api/v1/admin/content/questions/missing"
            )

        # TODO: change to 404 once the bare-except bug is fixed in soru_sil
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_delete_question_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin cannot delete questions."""
        response = await student_client.delete("/api/v1/admin/content/questions/q1")
        assert response.status_code == 403


# ===========================================================================
# TESTS: Educational materials stub endpoints
# ===========================================================================


class TestEducationalMaterials:
    """Tests for educational materials endpoints (stub — return 501)."""

    @pytest.mark.asyncio
    async def test_educational_list_returns_empty(self, admin_client: AsyncClient):
        """Educational materials list returns empty stub response."""
        response = await admin_client.get("/api/v1/admin/content/educational")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"] == []
        assert body["total_count"] == 0

    @pytest.mark.asyncio
    async def test_educational_post_returns_501(self, admin_client: AsyncClient):
        """POST educational returns 501 (table not yet created)."""
        response = await admin_client.post(
            "/api/v1/admin/content/educational",
            json={"title": "Konu anlatimi"},
        )
        assert response.status_code == 501

    @pytest.mark.asyncio
    async def test_educational_list_returns_403_for_student(
        self, student_client: AsyncClient
    ):
        """Non-admin cannot list educational materials."""
        response = await student_client.get("/api/v1/admin/content/educational")
        assert response.status_code == 403


# ===========================================================================
# TESTS: GET /api/v1/admin/content/search — full-text search
# ===========================================================================


class TestContentSearch:
    """Tests for icerik_ara (GET /api/v1/admin/content/search)."""

    def _configure_search_mock(self, admin_client: AsyncClient, rows, total: int):
        call_count = [0]

        rows_mappings = MagicMock()
        rows_mappings.all.return_value = rows
        rows_result = MagicMock()
        rows_result.mappings.return_value = rows_mappings

        count_result = MagicMock()
        count_result.scalar.return_value = total

        async def _execute(*args, **kwargs):
            call_count[0] += 1
            return rows_result if call_count[0] == 1 else count_result

        admin_client._mock_db.execute = _execute

    @pytest.mark.asyncio
    async def test_search_returns_results(self, admin_client: AsyncClient):
        """Full-text search returns matching questions."""
        q_row = {
            "id": "s1",
            "question_text": "Trigonometri sorusu",
            "subject_area": "matematik",
            "difficulty_level": "MEDIUM",
            "correct_answer": "C",
        }
        self._configure_search_mock(admin_client, [q_row], total=1)

        response = await admin_client.get("/api/v1/admin/content/search?q=trigonometri")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["query"] == "trigonometri"
        assert len(body["data"]) == 1
        assert body["total_count"] == 1

    @pytest.mark.asyncio
    async def test_search_requires_min_length_2(self, admin_client: AsyncClient):
        """Single-character query is rejected with 422."""
        response = await admin_client.get("/api/v1/admin/content/search?q=a")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_returns_empty_when_no_match(self, admin_client: AsyncClient):
        """No matching results returns empty list with total_count 0."""
        self._configure_search_mock(admin_client, [], total=0)

        response = await admin_client.get("/api/v1/admin/content/search?q=xyzzy")

        assert response.status_code == 200
        assert response.json()["data"] == []
        assert response.json()["total_count"] == 0

    @pytest.mark.asyncio
    async def test_search_returns_403_for_student(self, student_client: AsyncClient):
        """Non-admin cannot use content search."""
        response = await student_client.get("/api/v1/admin/content/search?q=mat")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_search_without_q_returns_422(self, admin_client: AsyncClient):
        """Missing required q parameter returns 422."""
        response = await admin_client.get("/api/v1/admin/content/search")
        assert response.status_code == 422


# ===========================================================================
# TESTS: Admin role enforcement — SUPER_ADMIN also passes
# ===========================================================================


class TestAdminRoleEnforcement:
    """Verify that both ADMIN and SUPER_ADMIN pass the admin_kullanici_getir gate."""

    @pytest_asyncio.fixture
    async def super_admin_client(self, admin_app: FastAPI):
        """Client authenticated as SUPER_ADMIN."""
        super_admin = AuthenticatedUser(
            id=99,
            username="superadmin",
            role=UserRole.SUPER_ADMIN,
            email="superadmin@test.com",
        )

        async def _override() -> AuthenticatedUser:
            return super_admin

        async def _db():
            db = _make_mock_db()
            mappings_mock = MagicMock()
            mappings_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.mappings.return_value = mappings_mock
            db.execute = AsyncMock(return_value=result_mock)
            yield db

        admin_app.dependency_overrides[get_current_user] = _override
        admin_app.dependency_overrides[get_db] = _db

        transport = ASGITransport(app=admin_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        admin_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_super_admin_can_list_users(self, super_admin_client: AsyncClient):
        """SUPER_ADMIN role passes admin_kullanici_getir and gets 200."""
        response = await super_admin_client.get("/api/v1/admin/users")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_role_is_rejected(self, admin_app: FastAPI):
        """TEACHER role receives 403 on admin endpoints."""
        teacher = AuthenticatedUser(
            id=10, username="teacher", role=UserRole.TEACHER, email="t@test.com"
        )

        async def _override() -> AuthenticatedUser:
            return teacher

        admin_app.dependency_overrides[get_current_user] = _override
        transport = ASGITransport(app=admin_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/admin/users")

        admin_app.dependency_overrides.clear()
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_role_is_rejected(self, admin_app: FastAPI):
        """PARENT role receives 403 on admin endpoints."""
        parent = AuthenticatedUser(
            id=20, username="parent", role=UserRole.PARENT, email="p@test.com"
        )

        async def _override() -> AuthenticatedUser:
            return parent

        admin_app.dependency_overrides[get_current_user] = _override
        transport = ASGITransport(app=admin_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/admin/dashboard/stats")

        admin_app.dependency_overrides.clear()
        assert response.status_code == 403
