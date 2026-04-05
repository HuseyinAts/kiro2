"""
Comprehensive unit tests for the OSYM exam (sinav) API.

Tests all major endpoints in backend/api/sinav.py using:
- app.dependency_overrides for auth bypass (correct FastAPI approach)
- unittest.mock.patch("api.sinav.osym_exam_engine") for engine singleton
- FastAPI TestClient for HTTP-level assertions

Coverage: all happy paths, 404 not-found, 403 ownership-check,
401 unauthenticated, 400 bad-request, and 422 validation-error cases.
"""

from __future__ import annotations

import os
import sys

# Ensure backend directory is on path before any local imports
_BACKEND_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
from core.dependencies import (  # type: ignore[import]
    AuthenticatedUser,
    get_current_user,
)

# ---------------------------------------------------------------------------
# Engine data-classes needed to build mock return values
# ---------------------------------------------------------------------------
from core.osym_exam_engine import (  # type: ignore[import]
    ExamPerformanceMetrics,
    ExamSessionData,
    ExamStatus,
    OSYMExamConfig,
    SubjectPerformance,
)

# ---------------------------------------------------------------------------
# App import
# ---------------------------------------------------------------------------
from main import app  # type: ignore[import]
from models.database import ExamType  # type: ignore[import]
from models.enums_db import UserRole  # type: ignore[import]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEST_USER_ID = 1
TEST_USER_ID_STR = "1"  # str(TEST_USER_ID) — matches session_data.student_id
TEST_SESSION_ID = "session-abc-123"
OTHER_USER_ID = 999

ENGINE_PATH = "api.sinav.osym_exam_engine"


# ---------------------------------------------------------------------------
# Helpers: build reusable mock objects
# ---------------------------------------------------------------------------


def _make_exam_config(exam_type: ExamType = ExamType.TYT) -> OSYMExamConfig:
    return OSYMExamConfig(
        exam_type=exam_type,
        total_questions=120,
        duration_minutes=165,
        subject_distribution={"TURKCE": 40, "MATEMATIK": 40, "FEN": 20, "SOSYAL": 20},
        auto_save_interval=30,
        warning_time_minutes=15,
    )


def _make_session(
    student_id: int = TEST_USER_ID,
    session_id: str = TEST_SESSION_ID,
    status: ExamStatus = ExamStatus.NOT_STARTED,
    student_id_as_str: bool = True,
) -> ExamSessionData:
    # /my-exams uses direct equality `session_data.student_id == current_user.id`
    # where current_user.id is int. All other endpoints use str() on both sides.
    # Pass student_id_as_str=False to test the my-exams L1 matching path.
    sid = str(student_id) if student_id_as_str else student_id
    s = ExamSessionData(
        session_id=session_id,
        student_id=sid,
        exam_config=_make_exam_config(),
        status=status,
        started_at=None,
        completed_at=None,
        current_question_index=0,
        questions=["q1", "q2", "q3"],
        answers={},
    )
    return s


def _make_in_progress_session(student_id: int = TEST_USER_ID) -> ExamSessionData:
    s = _make_session(student_id=student_id, status=ExamStatus.IN_PROGRESS)
    s.started_at = datetime(2026, 1, 1, 10, 0, 0)
    return s


def _make_performance() -> ExamPerformanceMetrics:
    return ExamPerformanceMetrics(
        total_questions=120,
        answered_questions=115,
        correct_answers=85,
        wrong_answers=30,
        empty_answers=5,
        net_score=77.5,
        raw_score=70.8,
        percentile=75.5,
        estimated_ability=1.2,
        confidence_level=0.95,
    )


def _make_mock_question() -> MagicMock:
    q = MagicMock()
    q.id = "q-uuid-001"
    q.question_text = "Asagidakilerden hangisi dogrudur?"
    q.question_image_url = None
    q.image_ocr_text = None
    q.image_width = None
    q.image_height = None
    q.option_a = "Secenek A"
    q.option_b = "Secenek B"
    q.option_c = "Secenek C"
    q.option_d = "Secenek D"
    q.option_e = None
    q.subject_area = "MATEMATIK"
    q.primary_topic_id = "calculus"
    q.difficulty_level = MagicMock()
    q.difficulty_level.value = "MEDIUM"
    return q


# ---------------------------------------------------------------------------
# Auth override helpers
# ---------------------------------------------------------------------------


def _auth_override(user_id: int = TEST_USER_ID):
    """Return an async callable that overrides get_current_user dependency."""
    user = AuthenticatedUser(
        id=user_id,
        username="test_student",
        role=UserRole.STUDENT,
        email="test@test.com",
    )

    async def _override():
        return user

    return _override


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    """TestClient with auth dependency overridden to return TEST_USER_ID."""
    app.dependency_overrides[get_current_user] = _auth_override(TEST_USER_ID)
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


@pytest.fixture()
def client_no_auth():
    """TestClient with no auth override — real auth logic fires (returns 401)."""
    app.dependency_overrides.clear()
    yield TestClient(app, raise_server_exceptions=False)


# ===========================================================================
# 1. GET /my-exams
# ===========================================================================


class TestGetMyExams:
    """Tests for GET /api/v1/osym-exam/my-exams.

    Implementation notes:
    - L1 path: iterates active_sessions, compares session.student_id == user.id.
      Because session.student_id is str and user.id is int, this never matches in
      normal operation — the endpoint falls through to L2 (Redis) in that case.
    - L2 path: calls get_student_sessions (inline import) and populates L1 cache.
    - Tests here exercise the L2 path via mocked get_student_sessions.
    """

    def test_returns_empty_list_when_no_sessions(self, client):
        """User with no active sessions gets an empty list response."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.active_sessions = {}
            with patch(
                "core.exam_session_store.get_student_sessions",
                AsyncMock(return_value=[]),
            ):
                response = client.get("/api/v1/osym-exam/my-exams")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

    def test_returns_sessions_from_redis_l2_fallback(self, client):
        """When L1 cache misses, sessions are fetched from Redis L2 and returned."""
        session = _make_session(student_id=TEST_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            # L1 is empty — forces the L2 Redis lookup
            mock_engine.active_sessions = {}
            with patch(
                "core.exam_session_store.get_student_sessions",
                AsyncMock(return_value=[session]),
            ):
                response = client.get("/api/v1/osym-exam/my-exams")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["session_id"] == TEST_SESSION_ID
        assert data[0]["exam_type"] == "tyt"
        assert data[0]["status"] == "not_started"
        assert data[0]["total_questions"] == 120
        assert data[0]["duration_minutes"] == 165

    def test_pagination_limit_restricts_results(self, client):
        """limit query parameter restricts the number of sessions returned."""
        sessions = [
            _make_session(student_id=TEST_USER_ID, session_id=f"s{i}")
            for i in range(10)
        ]
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.active_sessions = {}
            with patch(
                "core.exam_session_store.get_student_sessions",
                AsyncMock(return_value=sessions),
            ):
                response = client.get("/api/v1/osym-exam/my-exams?limit=3&offset=0")
        assert response.status_code == 200
        assert len(response.json()) <= 3

    def test_pagination_offset_skips_results(self, client):
        """offset parameter skips the first N sessions."""
        sessions = [
            _make_session(student_id=TEST_USER_ID, session_id=f"s{i}") for i in range(5)
        ]
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.active_sessions = {}
            with patch(
                "core.exam_session_store.get_student_sessions",
                AsyncMock(return_value=sessions),
            ):
                response = client.get("/api/v1/osym-exam/my-exams?limit=10&offset=3")
        assert response.status_code == 200
        # 5 total - 3 offset = 2 results
        assert len(response.json()) == 2

    def test_requires_authentication(self, client_no_auth):
        """Unauthenticated request is rejected with 401."""
        response = client_no_auth.get("/api/v1/osym-exam/my-exams")
        assert response.status_code == 401


# ===========================================================================
# 2. GET /exam-configs
# ===========================================================================


class TestGetExamConfigs:
    """Tests for GET /api/v1/osym-exam/exam-configs"""

    def test_returns_tyt_config_with_correct_structure(self, client):
        """Exam configs endpoint returns TYT config with required fields."""
        tyt = _make_exam_config(ExamType.TYT)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.exam_configs = {ExamType.TYT: tyt}
            response = client.get("/api/v1/osym-exam/exam-configs")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "exam_configs" in body
        tyt_cfg = body["exam_configs"]["tyt"]
        assert tyt_cfg["total_questions"] == 120
        assert tyt_cfg["duration_minutes"] == 165

    def test_returns_all_configured_exam_types(self, client):
        """All exam types present in engine.exam_configs appear in response."""
        configs = {
            ExamType.TYT: _make_exam_config(ExamType.TYT),
            ExamType.AYT: _make_exam_config(ExamType.AYT),
        }
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.exam_configs = configs
            response = client.get("/api/v1/osym-exam/exam-configs")
        assert response.status_code == 200
        exam_configs = response.json()["exam_configs"]
        assert "tyt" in exam_configs
        assert "ayt" in exam_configs

    def test_requires_authentication(self, client_no_auth):
        """Unauthenticated request is rejected with 401."""
        response = client_no_auth.get("/api/v1/osym-exam/exam-configs")
        assert response.status_code == 401


# ===========================================================================
# 3. POST /create
# ===========================================================================


class TestCreateExam:
    """Tests for POST /api/v1/osym-exam/create"""

    def test_creates_exam_successfully_tyt(self, client):
        """Valid TYT create request returns session with correct structure."""
        session = _make_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.create_exam_session = AsyncMock(return_value=TEST_SESSION_ID)
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.post(
                "/api/v1/osym-exam/create", json={"exam_type": "tyt"}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == TEST_SESSION_ID
        assert data["status"] == "not_started"
        assert data["total_questions"] == 120
        assert data["duration_minutes"] == 165
        assert data["current_question_index"] == 0

    @pytest.mark.parametrize("exam_type", ["tyt", "ayt", "ydt"])
    def test_creates_exam_for_all_types(self, client, exam_type):
        """Exam creation succeeds for TYT, AYT and YDT exam types."""
        session = _make_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.create_exam_session = AsyncMock(return_value=TEST_SESSION_ID)
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.post(
                "/api/v1/osym-exam/create", json={"exam_type": exam_type}
            )
        assert response.status_code == 200
        assert "session_id" in response.json()

    def test_response_contains_all_required_fields(self, client):
        """Create response includes all ExamSessionResponse fields."""
        session = _make_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.create_exam_session = AsyncMock(return_value=TEST_SESSION_ID)
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.post(
                "/api/v1/osym-exam/create", json={"exam_type": "tyt"}
            )
        data = response.json()
        for field in [
            "session_id",
            "student_id",
            "exam_type",
            "status",
            "total_questions",
            "duration_minutes",
            "current_question_index",
        ]:
            assert field in data, f"Missing field: {field}"

    def test_returns_400_on_value_error_from_engine(self, client):
        """ValueError raised by engine (e.g. insufficient questions) maps to HTTP 400."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.create_exam_session = AsyncMock(
                side_effect=ValueError("Yeterli soru bulunamadi")
            )
            response = client.post(
                "/api/v1/osym-exam/create", json={"exam_type": "tyt"}
            )
        assert response.status_code == 400

    def test_returns_500_when_session_not_created(self, client):
        """If create_exam_session returns an id but get_session_data returns None, 500 is raised."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.create_exam_session = AsyncMock(return_value="new-session-id")
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.post(
                "/api/v1/osym-exam/create", json={"exam_type": "tyt"}
            )
        assert response.status_code == 500

    def test_returns_422_on_invalid_exam_type(self, client):
        """Unknown exam_type string fails Pydantic validation with 422."""
        response = client.post(
            "/api/v1/osym-exam/create", json={"exam_type": "INVALID_TYPE_XYZ"}
        )
        assert response.status_code == 422

    def test_returns_422_when_exam_type_missing(self, client):
        """Missing required exam_type field triggers Pydantic 422."""
        response = client.post("/api/v1/osym-exam/create", json={})
        assert response.status_code == 422

    def test_requires_authentication(self, client_no_auth):
        """Unauthenticated create request is rejected with 401."""
        response = client_no_auth.post(
            "/api/v1/osym-exam/create", json={"exam_type": "tyt"}
        )
        assert response.status_code == 401


# ===========================================================================
# 4. POST /{session_id}/start
# ===========================================================================


class TestStartExam:
    """Tests for POST /api/v1/osym-exam/{session_id}/start.

    NOTE: This endpoint does NOT have `except HTTPException: raise`, so
    HTTPException(404/403) raised inside the try-block is caught by
    `except Exception` and converted to 500. This is a known production
    code limitation — tests document the actual behaviour.
    """

    def test_starts_exam_successfully(self, client):
        """Starting a valid NOT_STARTED session returns in_progress status."""
        session = _make_session()
        started = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.start_exam = AsyncMock(return_value=started)
            response = client.post(f"/api/v1/osym-exam/{TEST_SESSION_ID}/start")
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

    @pytest.mark.xfail(
        reason="BUG: missing 'except HTTPException: raise' — 404 swallowed into 500",
        strict=True,
    )
    def test_returns_404_when_session_not_found(self, client):
        """Non-existent session should return 404, but gets swallowed to 500."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.post("/api/v1/osym-exam/nonexistent/start")
        assert response.status_code == 404

    @pytest.mark.xfail(
        reason="BUG: missing 'except HTTPException: raise' — 403 swallowed into 500",
        strict=True,
    )
    def test_returns_403_when_session_belongs_to_other_user(self, client):
        """Wrong-owner session should return 403, but gets swallowed to 500."""
        other_session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=other_session)
            response = client.post(f"/api/v1/osym-exam/{TEST_SESSION_ID}/start")
        assert response.status_code == 403

    def test_returns_400_when_already_started(self, client):
        """ValueError from start_exam (exam already started) maps to 400."""
        session = _make_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.start_exam = AsyncMock(
                side_effect=ValueError("Sinav zaten baslatilmis")
            )
            response = client.post(f"/api/v1/osym-exam/{TEST_SESSION_ID}/start")
        assert response.status_code == 400

    def test_requires_authentication(self, client_no_auth):
        """Unauthenticated start request is rejected with 401."""
        response = client_no_auth.post(f"/api/v1/osym-exam/{TEST_SESSION_ID}/start")
        assert response.status_code == 401


# ===========================================================================
# 5. GET /{session_id}/current-question
# ===========================================================================


class TestGetCurrentQuestion:
    """Tests for GET /api/v1/osym-exam/{session_id}/current-question"""

    def test_returns_current_question_structure(self, client):
        """Returns well-structured QuestionResponse for in-progress exam."""
        session = _make_in_progress_session()
        question = _make_mock_question()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_current_question = AsyncMock(return_value=question)
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/current-question"
            )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "q-uuid-001"
        assert data["option_a"] == "Secenek A"
        assert data["subject_area"] == "MATEMATIK"
        assert data["difficulty"] == "MEDIUM"
        # current_question_index=0 → order=1
        assert data["question_order"] == 1

    def test_includes_all_required_question_fields(self, client):
        """All QuestionResponse fields are present in the response."""
        session = _make_in_progress_session()
        question = _make_mock_question()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_current_question = AsyncMock(return_value=question)
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/current-question"
            )
        data = response.json()
        for field in [
            "id",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "subject_area",
            "topic",
            "difficulty",
            "question_order",
        ]:
            assert field in data, f"Missing field: {field}"

    def test_returns_404_when_session_not_found(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.get("/api/v1/osym-exam/bad/current-question")
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/current-question"
            )
        assert response.status_code == 403

    def test_returns_404_when_engine_returns_no_question(self, client):
        """Engine returning None for get_current_question maps to 404."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_current_question = AsyncMock(return_value=None)
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/current-question"
            )
        assert response.status_code == 404


# ===========================================================================
# 6. POST /{session_id}/save-answer
# ===========================================================================


class TestSaveAnswer:
    """Tests for POST /api/v1/osym-exam/{session_id}/save-answer"""

    def test_saves_valid_answer_successfully(self, client):
        """Valid answer payload returns success=True and auto_saved=True."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.save_answer = AsyncMock(return_value=True)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/save-answer",
                json={
                    "question_id": "q-uuid-001",
                    "selected_answer": "A",
                    "response_time": 45.0,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["auto_saved"] is True

    @pytest.mark.parametrize("answer", ["A", "B", "C", "D", "E"])
    def test_saves_all_valid_answer_options(self, client, answer):
        """Answers A through E are all accepted successfully."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.save_answer = AsyncMock(return_value=True)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/save-answer",
                json={"question_id": "q-uuid-001", "selected_answer": answer},
            )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_saves_empty_answer_none(self, client):
        """selected_answer=None (skip question) is accepted."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.save_answer = AsyncMock(return_value=True)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/save-answer",
                json={"question_id": "q-uuid-001", "selected_answer": None},
            )
        assert response.status_code == 200

    def test_returns_400_when_save_returns_false(self, client):
        """Engine returning False for save maps to HTTP 400."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.save_answer = AsyncMock(return_value=False)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/save-answer",
                json={"question_id": "q-uuid-001", "selected_answer": "B"},
            )
        assert response.status_code == 400

    def test_returns_404_for_unknown_session(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.post(
                "/api/v1/osym-exam/ghost/save-answer",
                json={"question_id": "q1", "selected_answer": "A"},
            )
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/save-answer",
                json={"question_id": "q1", "selected_answer": "C"},
            )
        assert response.status_code == 403

    def test_returns_422_when_question_id_missing(self, client):
        """Missing required question_id field triggers Pydantic 422."""
        response = client.post(
            f"/api/v1/osym-exam/{TEST_SESSION_ID}/save-answer",
            json={"selected_answer": "A"},
        )
        assert response.status_code == 422

    def test_returns_422_when_rating_out_of_range(self, client):
        """Rating outside 1-4 range triggers Pydantic validation error."""
        response = client.post(
            f"/api/v1/osym-exam/{TEST_SESSION_ID}/save-answer",
            json={"question_id": "q1", "selected_answer": "A", "rating": 5},
        )
        assert response.status_code == 422

    def test_requires_authentication(self, client_no_auth):
        """Unauthenticated save request is rejected with 401."""
        response = client_no_auth.post(
            f"/api/v1/osym-exam/{TEST_SESSION_ID}/save-answer",
            json={"question_id": "q1", "selected_answer": "A"},
        )
        assert response.status_code == 401


# ===========================================================================
# 7. POST /{session_id}/navigate
# ===========================================================================


class TestNavigateToQuestion:
    """Tests for POST /api/v1/osym-exam/{session_id}/navigate"""

    def test_navigates_to_valid_question_index(self, client):
        """Navigate to index 5 returns question with question_order=6."""
        session = _make_in_progress_session()
        question = _make_mock_question()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.navigate_to_question = AsyncMock(return_value=question)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/navigate",
                json={"question_index": 5},
            )
        assert response.status_code == 200
        assert response.json()["question_order"] == 6

    def test_navigate_to_first_question(self, client):
        """Navigating to index 0 sets question_order to 1."""
        session = _make_in_progress_session()
        question = _make_mock_question()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.navigate_to_question = AsyncMock(return_value=question)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/navigate",
                json={"question_index": 0},
            )
        assert response.status_code == 200
        assert response.json()["question_order"] == 1

    def test_returns_404_when_target_question_not_found(self, client):
        """Engine returning None for navigation maps to 404."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.navigate_to_question = AsyncMock(return_value=None)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/navigate",
                json={"question_index": 999},
            )
        assert response.status_code == 404

    def test_returns_422_when_negative_index(self, client):
        """Negative question_index violates ge=0 constraint and triggers 422."""
        response = client.post(
            f"/api/v1/osym-exam/{TEST_SESSION_ID}/navigate",
            json={"question_index": -1},
        )
        assert response.status_code == 422

    def test_returns_404_for_unknown_session(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.post(
                "/api/v1/osym-exam/ghost/navigate",
                json={"question_index": 0},
            )
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/navigate",
                json={"question_index": 0},
            )
        assert response.status_code == 403


# ===========================================================================
# 8. POST /{session_id}/flag-question
# ===========================================================================


class TestFlagQuestion:
    """Tests for POST /api/v1/osym-exam/{session_id}/flag-question"""

    def test_flags_question_successfully(self, client):
        """Valid flag request returns success=True and flagged=True."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.flag_question = AsyncMock(return_value=True)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/flag-question",
                json={"question_id": "q-uuid-001", "flagged": True},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["flagged"] is True

    def test_unflags_question_returns_false_in_flagged_field(self, client):
        """Unflag request returns flagged=False in response."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.flag_question = AsyncMock(return_value=True)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/flag-question",
                json={"question_id": "q-uuid-001", "flagged": False},
            )
        assert response.status_code == 200
        assert response.json()["flagged"] is False

    def test_returns_400_when_flag_operation_fails(self, client):
        """Engine returning False from flag_question maps to HTTP 400."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.flag_question = AsyncMock(return_value=False)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/flag-question",
                json={"question_id": "q-uuid-001", "flagged": True},
            )
        assert response.status_code == 400

    def test_returns_404_for_unknown_session(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.post(
                "/api/v1/osym-exam/ghost/flag-question",
                json={"question_id": "q1", "flagged": True},
            )
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.post(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/flag-question",
                json={"question_id": "q1", "flagged": True},
            )
        assert response.status_code == 403


# ===========================================================================
# 9. GET /{session_id}/remaining-time
# ===========================================================================


class TestGetRemainingTime:
    """Tests for GET /api/v1/osym-exam/{session_id}/remaining-time"""

    def test_returns_remaining_seconds_and_formatted_time(self, client):
        """Running exam returns remaining_seconds, remaining_minutes, formatted_time."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_remaining_time = AsyncMock(return_value=9000)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/remaining-time")
        assert response.status_code == 200
        data = response.json()
        assert data["remaining_seconds"] == 9000
        assert data["remaining_minutes"] == 150
        assert "formatted_time" in data
        assert data["warning"] is False  # 150 min > 15 min threshold

    def test_warning_true_when_below_threshold(self, client):
        """Warning flag is True when fewer than warning_time_minutes remain."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            # 13 minutes = 780 seconds, less than 15-minute threshold
            mock_engine.get_remaining_time = AsyncMock(return_value=780)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/remaining-time")
        assert response.status_code == 200
        assert response.json()["warning"] is True

    def test_none_remaining_time_returns_not_started_message(self, client):
        """Engine returning None maps to a descriptive not-started response."""
        session = _make_session()  # NOT_STARTED
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_remaining_time = AsyncMock(return_value=None)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/remaining-time")
        assert response.status_code == 200
        data = response.json()
        assert data["remaining_seconds"] is None
        assert "formatted_time" in data

    def test_returns_404_for_unknown_session(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.get("/api/v1/osym-exam/ghost/remaining-time")
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/remaining-time")
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "remaining_seconds,expected_warning",
        [(900, True), (1800, False), (300, True), (9900, False)],
    )
    def test_warning_threshold_parametrized(
        self, client, remaining_seconds, expected_warning
    ):
        """Warning boundary: True below 15 min threshold, False above."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_remaining_time = AsyncMock(return_value=remaining_seconds)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/remaining-time")
        assert response.status_code == 200
        assert response.json()["warning"] == expected_warning


# ===========================================================================
# 10. POST /{session_id}/complete
# ===========================================================================


class TestCompleteExam:
    """Tests for POST /api/v1/osym-exam/{session_id}/complete.

    NOTE: Like start_exam, this endpoint does NOT have `except HTTPException: raise`,
    so HTTPException(404/403) raised inside the try-block is caught by
    `except Exception` and converted to 500. Tests document actual behaviour.
    """

    def test_completes_exam_and_returns_full_metrics(self, client):
        """Completing exam returns PerformanceResponse with all metric fields."""
        session = _make_in_progress_session()
        metrics = _make_performance()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.complete_exam = AsyncMock(return_value=metrics)
            # Suppress the fire-and-forget event service call
            with patch("core.database.get_db_session_context") as mock_ctx:
                mock_db = AsyncMock()
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
                response = client.post(f"/api/v1/osym-exam/{TEST_SESSION_ID}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["total_questions"] == 120
        assert data["correct_answers"] == 85
        assert data["net_score"] == pytest.approx(77.5)
        assert data["estimated_ability"] == pytest.approx(1.2)
        assert data["confidence_level"] == pytest.approx(0.95)

    @pytest.mark.xfail(
        reason="BUG: missing 'except HTTPException: raise' — 404 swallowed into 500",
        strict=True,
    )
    def test_returns_404_when_session_not_found(self, client):
        """Non-existent session should return 404, but gets swallowed to 500."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.post("/api/v1/osym-exam/ghost/complete")
        assert response.status_code == 404

    @pytest.mark.xfail(
        reason="BUG: missing 'except HTTPException: raise' — 403 swallowed into 500",
        strict=True,
    )
    def test_returns_403_for_wrong_user(self, client):
        """Wrong-owner session should return 403, but gets swallowed to 500."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.post(f"/api/v1/osym-exam/{TEST_SESSION_ID}/complete")
        assert response.status_code == 403

    def test_returns_400_on_value_error_from_engine(self, client):
        """ValueError from complete_exam (already completed) maps to 400."""
        session = _make_session(status=ExamStatus.COMPLETED)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.complete_exam = AsyncMock(
                side_effect=ValueError("Sinav zaten tamamlandi")
            )
            response = client.post(f"/api/v1/osym-exam/{TEST_SESSION_ID}/complete")
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "correct,wrong,empty",
        [(100, 20, 0), (85, 30, 5), (60, 50, 10), (30, 80, 10)],
    )
    def test_various_score_distributions(self, client, correct, wrong, empty):
        """Exam completion works for different correct/wrong/empty distributions."""
        session = _make_in_progress_session()
        metrics = ExamPerformanceMetrics(
            total_questions=120,
            answered_questions=correct + wrong,
            correct_answers=correct,
            wrong_answers=wrong,
            empty_answers=empty,
            net_score=float(correct - wrong * 0.25),
            raw_score=float(correct),
            percentile=50.0,
            estimated_ability=0.0,
            confidence_level=0.9,
        )
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.complete_exam = AsyncMock(return_value=metrics)
            with patch("core.database.get_db_session_context") as mock_ctx:
                mock_db = AsyncMock()
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
                response = client.post(f"/api/v1/osym-exam/{TEST_SESSION_ID}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["correct_answers"] == correct
        assert data["wrong_answers"] == wrong


# ===========================================================================
# 11. GET /{session_id}/session  (session info)
# ===========================================================================


class TestGetSessionInfo:
    """Tests for GET /api/v1/osym-exam/{session_id}/session"""

    def test_returns_session_info_for_valid_session(self, client):
        """Valid session returns ExamSessionResponse with all required fields."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/session")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == TEST_SESSION_ID
        assert data["status"] == "in_progress"
        assert data["total_questions"] == 120

    def test_returns_404_when_session_not_found(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.get("/api/v1/osym-exam/no-such/session")
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/session")
        assert response.status_code == 403


# ===========================================================================
# 12. GET /{session_id}/performance
# ===========================================================================


class TestGetPerformanceAnalysis:
    """Tests for GET /api/v1/osym-exam/{session_id}/performance"""

    def test_returns_performance_for_completed_exam(self, client):
        """Session with performance_metrics attached returns PerformanceResponse."""
        session = _make_in_progress_session()
        session.performance_metrics = _make_performance()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/performance")
        assert response.status_code == 200
        data = response.json()
        assert data["correct_answers"] == 85
        assert data["net_score"] == pytest.approx(77.5)
        assert data["percentile"] == pytest.approx(75.5)

    def test_returns_400_when_no_performance_metrics(self, client):
        """In-progress exam with no performance_metrics returns 400."""
        session = _make_in_progress_session()
        session.performance_metrics = None
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/performance")
        assert response.status_code == 400

    def test_returns_404_when_session_not_found(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.get("/api/v1/osym-exam/ghost/performance")
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.get(f"/api/v1/osym-exam/{TEST_SESSION_ID}/performance")
        assert response.status_code == 403


# ===========================================================================
# 13. GET /{session_id}/subject-performance
# ===========================================================================


class TestGetSubjectPerformance:
    """Tests for GET /api/v1/osym-exam/{session_id}/subject-performance"""

    def test_returns_per_subject_metrics(self, client):
        """Returns list of SubjectPerformanceResponse with correct data."""
        session = _make_in_progress_session()
        math_perf = SubjectPerformance(
            subject="MATEMATIK",
            total_questions=40,
            correct_answers=28,
            wrong_answers=10,
            empty_answers=2,
            success_rate=70.0,
            average_response_time=65.5,
            difficulty_level=0.8,
        )
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_subject_performance = AsyncMock(return_value=[math_perf])
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/subject-performance"
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["subject"] == "MATEMATIK"
        assert data[0]["success_rate"] == pytest.approx(70.0)
        assert data[0]["total_questions"] == 40

    def test_returns_multiple_subjects(self, client):
        """Multiple subjects are all returned in the list."""
        session = _make_in_progress_session()
        perfs = [
            SubjectPerformance("MATEMATIK", 40, 28, 10, 2, 70.0, 65.5, 0.8),
            SubjectPerformance("TURKCE", 40, 32, 6, 2, 80.0, 45.0, 0.6),
        ]
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_subject_performance = AsyncMock(return_value=perfs)
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/subject-performance"
            )
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_returns_404_when_session_not_found(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.get("/api/v1/osym-exam/ghost/subject-performance")
        assert response.status_code == 404


# ===========================================================================
# 14. DELETE /{session_id}  (cancel exam)
# ===========================================================================


class TestCancelExam:
    """Tests for DELETE /api/v1/osym-exam/{session_id}"""

    def test_cancels_not_started_exam_successfully(self, client):
        """NOT_STARTED exam can be cancelled; returns success=True."""
        session = _make_session(status=ExamStatus.NOT_STARTED)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.auto_save_tasks = {}
            mock_engine.active_sessions = {TEST_SESSION_ID: session}
            response = client.delete(f"/api/v1/osym-exam/{TEST_SESSION_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == TEST_SESSION_ID

    def test_cancels_in_progress_exam_successfully(self, client):
        """IN_PROGRESS exam can also be cancelled."""
        session = _make_in_progress_session()
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.auto_save_tasks = {}
            mock_engine.active_sessions = {TEST_SESSION_ID: session}
            response = client.delete(f"/api/v1/osym-exam/{TEST_SESSION_ID}")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_returns_400_when_exam_already_completed(self, client):
        """COMPLETED exam cannot be cancelled a second time — returns 400."""
        session = _make_session(status=ExamStatus.COMPLETED)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.delete(f"/api/v1/osym-exam/{TEST_SESSION_ID}")
        assert response.status_code == 400

    def test_returns_400_when_exam_already_abandoned(self, client):
        """ABANDONED exam cannot be cancelled again — returns 400."""
        session = _make_session(status=ExamStatus.ABANDONED)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.delete(f"/api/v1/osym-exam/{TEST_SESSION_ID}")
        assert response.status_code == 400

    def test_returns_404_when_session_not_found(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.delete("/api/v1/osym-exam/nonexistent")
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.delete(f"/api/v1/osym-exam/{TEST_SESSION_ID}")
        assert response.status_code == 403


# ===========================================================================
# 15. GET /{session_id}/unanswered-questions
# ===========================================================================


class TestGetUnansweredQuestions:
    """Tests for GET /api/v1/osym-exam/{session_id}/unanswered-questions"""

    def test_returns_unanswered_question_ids_and_count(self, client):
        """Returns list of unanswered IDs, unanswered_count and total_questions."""
        session = _make_in_progress_session()
        session.questions = ["q1", "q2", "q3"]
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_unanswered_questions = AsyncMock(return_value=["q2", "q3"])
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/unanswered-questions"
            )
        assert response.status_code == 200
        data = response.json()
        assert data["unanswered_count"] == 2
        assert data["total_questions"] == 3
        assert "q2" in data["unanswered_question_ids"]
        assert "q3" in data["unanswered_question_ids"]
        assert data["session_id"] == TEST_SESSION_ID

    def test_returns_empty_list_when_all_answered(self, client):
        """All questions answered results in unanswered_count=0 and empty list."""
        session = _make_in_progress_session()
        session.questions = ["q1", "q2"]
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_unanswered_questions = AsyncMock(return_value=[])
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/unanswered-questions"
            )
        assert response.status_code == 200
        data = response.json()
        assert data["unanswered_count"] == 0
        assert data["unanswered_question_ids"] == []

    def test_returns_404_when_session_not_found(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.get("/api/v1/osym-exam/ghost/unanswered-questions")
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/unanswered-questions"
            )
        assert response.status_code == 403


# ===========================================================================
# 16. GET /{session_id}/completion-stats
# ===========================================================================


class TestGetCompletionStats:
    """Tests for GET /api/v1/osym-exam/{session_id}/completion-stats"""

    def test_returns_completion_statistics(self, client):
        """Returns answered, unanswered and completion_percentage correctly."""
        session = _make_in_progress_session()
        stats = {
            "total_questions": 120,
            "answered_questions": 90,
            "unanswered_questions": 30,
            "completion_percentage": 75.0,
        }
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_answer_statistics = AsyncMock(return_value=stats)
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/completion-stats"
            )
        assert response.status_code == 200
        data = response.json()
        assert data["total_questions"] == 120
        assert data["answered_questions"] == 90
        assert data["unanswered_questions"] == 30
        assert data["completion_percentage"] == pytest.approx(75.0)
        assert data["session_id"] == TEST_SESSION_ID

    def test_full_completion_shows_100_percent(self, client):
        """100% completion is reported when all questions are answered."""
        session = _make_in_progress_session()
        stats = {
            "total_questions": 120,
            "answered_questions": 120,
            "unanswered_questions": 0,
            "completion_percentage": 100.0,
        }
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            mock_engine.get_answer_statistics = AsyncMock(return_value=stats)
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/completion-stats"
            )
        assert response.status_code == 200
        assert response.json()["completion_percentage"] == pytest.approx(100.0)

    def test_returns_404_when_session_not_found(self, client):
        """Non-existent session returns 404."""
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=None)
            response = client.get("/api/v1/osym-exam/ghost/completion-stats")
        assert response.status_code == 404

    def test_returns_403_for_wrong_user(self, client):
        """Session owned by another user returns 403."""
        session = _make_session(student_id=OTHER_USER_ID)
        with patch(ENGINE_PATH) as mock_engine:
            mock_engine.get_session_data = AsyncMock(return_value=session)
            response = client.get(
                f"/api/v1/osym-exam/{TEST_SESSION_ID}/completion-stats"
            )
        assert response.status_code == 403
