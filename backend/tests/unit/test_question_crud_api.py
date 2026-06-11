"""
Unit Tests for api/question_crud_api.py

Tests all endpoints using FastAPI TestClient with mocked service layer.
No DB connections, no Redis — all dependencies mocked.

Endpoints covered:
- POST   /api/v1/questions/create           (create_question)
- POST   /api/v1/questions/bulk-create      (bulk_create_questions)
- PUT    /api/v1/questions/{id}             (update_question)
- GET    /api/v1/questions/{id}/history     (get_question_history)
- DELETE /api/v1/questions/{id}             (delete_question)
- POST   /api/v1/questions/{id}/archive     (archive_question)
- POST   /api/v1/questions/{id}/restore     (restore_question)
- GET    /api/v1/questions/archived         (get_archived_questions)
- POST   /api/v1/questions/search           (search_questions)
- GET    /api/v1/questions/search/elasticsearch (elasticsearch_search)
- GET    /api/v1/questions/{id}             (get_question)
- GET    /api/v1/questions/statistics/overview (get_statistics)
- GET    /api/v1/questions/health           (health_check)
- GET    /api/v1/questions/random           (get_random_questions)
- GET    /api/v1/questions/books            (list_source_books)
- POST   /api/v1/questions/semantic-search  (semantic_search)
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
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_question(
    qid: str = "q-uuid-001",
    question_text: str = "2 + 2 = ?",
    exam_type: str = "TYT",
    subject_area: str = "MATEMATIK",
    difficulty_value: str = "MEDIUM",
    times_asked: int = 10,
    times_correct: int = 7,
) -> MagicMock:
    """Return a MagicMock that looks like a QuestionBankItem."""
    q = MagicMock()
    q.id = qid
    q.question_text = question_text
    q.question_html = "<p>2 + 2 = ?</p>"
    q.question_latex = None
    q.question_image_url = None
    q.image_ocr_text = None
    q.image_width = None
    q.image_height = None
    q.option_a = "3"
    q.option_b = "4"
    q.option_c = "5"
    q.option_d = "6"
    q.option_e = None
    q.correct_answer = "B"
    q.explanation = "Temel toplama işlemi"
    q.explanation_video_url = None
    q.alternative_solutions = None
    q.exam_type = exam_type
    q.subject_area = subject_area
    q.source_book = "Test Kitabı"
    q.primary_topic_id = 1
    q.grade_level = 12
    q.difficulty_level = MagicMock()
    q.difficulty_level.value = difficulty_value
    q.bloom_level = 1
    q.bloom_category = "Hatırlama"
    q.irt_difficulty = 0.0
    q.irt_discrimination = 1.0
    q.irt_guessing = 0.2
    q.irt_upper_asymptote = 1.0
    q.morphology_complexity = 0.5
    q.readability_score = 0.8
    q.times_asked = times_asked
    q.times_correct = times_correct
    q.times_wrong = times_asked - times_correct
    q.times_skipped = 0
    q.average_response_time = 45.0
    q.quality_score = 0.9
    q.quality_review_status = "approved"
    q.osym_format_compliant = True
    q.word_count = 6
    q.is_active = True
    q.is_public = False
    q.created_at = datetime(2026, 1, 1, 10, 0, 0)
    q.updated_at = datetime(2026, 1, 2, 10, 0, 0)
    return q


def _mock_current_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="user-001", username="user-001", role="teacher", email="test@example.com"
    )


# ---------------------------------------------------------------------------
# App setup with dependency overrides
# ---------------------------------------------------------------------------


def _create_app(mock_service: MagicMock, mock_db: MagicMock = None) -> FastAPI:
    """
    Build a minimal FastAPI app that includes the question_crud_api router
    with auth and DB dependencies overridden.
    """
    from api.question_crud_api import get_question_service
    from api.question_crud_api import router as q_router
    from core.database import get_db_session
    from core.dependencies import get_current_user

    app = FastAPI()

    async def _override_auth():
        return _mock_current_user()

    async def _override_db():
        db = mock_db or AsyncMock()
        yield db

    async def _override_service():
        return mock_service

    app.dependency_overrides[get_current_user] = _override_auth
    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_question_service] = _override_service
    app.include_router(q_router)
    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service():
    """A fresh AsyncMock QuestionCRUDService for each test."""
    svc = AsyncMock()
    return svc


@pytest.fixture
def mock_question():
    return _make_mock_question()


@pytest.fixture
def valid_create_payload():
    return {
        "soru_metni": "Türkiye'nin başkenti neresidir?",
        "secenekler": ["Ankara", "İstanbul", "İzmir", "Bursa"],
        "dogru_cevap": "A",
        "sinav_tipi": "TYT",
        "konu": "Coğrafya",
        "zorluk_seviyesi": "kolay",
        "sinif_seviyesi": 11,
        "bloom_seviyesi": 1,
    }


@pytest.fixture
def valid_update_payload():
    return {"soru_metni": "Türkiye'nin en büyük ili hangisidir?"}


# ===========================================================================
# 1. Health check — tested via direct async call (route order issue:
#    GET /{question_id} is registered before GET /health in the router,
#    so HTTP /health is captured by the dynamic route in TestClient)
# ===========================================================================


@pytest.mark.asyncio
async def test_health_check_returns_200():
    from api.question_crud_api import health_check

    response = await health_check()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_body_structure():
    import json

    from api.question_crud_api import health_check

    response = await health_check()
    data = json.loads(response.body)
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert "features" in data["data"]
    assert isinstance(data["data"]["features"], list)
    assert len(data["data"]["features"]) > 0


# ===========================================================================
# 2. GET /statistics/overview
# ===========================================================================


def test_get_statistics_happy_path(mock_service):
    mock_service.get_question_statistics = AsyncMock(
        return_value={"total": 1000, "by_exam": {"TYT": 600, "AYT": 400}}
    )
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/statistics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 1000


def test_get_statistics_service_error_returns_500(mock_service):
    mock_service.get_question_statistics = AsyncMock(
        side_effect=RuntimeError("DB hatası")
    )
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/statistics/overview")
    assert response.status_code == 500


# ===========================================================================
# 3. GET /archived
# ===========================================================================


def test_get_archived_questions_empty(mock_service):
    mock_service.get_archived_questions = AsyncMock(return_value=[])
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/archived")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["count"] == 0
    assert data["data"]["questions"] == []


def test_get_archived_questions_with_results(mock_service, mock_question):
    mock_service.get_archived_questions = AsyncMock(return_value=[mock_question])
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/archived")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["count"] == 1
    assert data["data"]["questions"][0]["id"] == "q-uuid-001"


def test_get_archived_questions_pagination(mock_service):
    mock_service.get_archived_questions = AsyncMock(return_value=[])
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/archived?limit=50&offset=100")
    assert response.status_code == 200
    # Verify pagination params were passed through
    mock_service.get_archived_questions.assert_awaited_once_with(limit=50, offset=100)


# ===========================================================================
# 4. POST /search
# ===========================================================================


def _make_search_result(questions):
    return {
        "questions": questions,
        "total_count": len(questions),
        "limit": 100,
        "offset": 0,
        "facets": {},
    }


def test_search_questions_empty_result(mock_service):
    mock_service.search_questions = AsyncMock(return_value=_make_search_result([]))
    app = _create_app(mock_service)
    client = TestClient(app)

    payload = {"limit": 10, "offset": 0}
    response = client.post("/api/v1/questions/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_count"] == 0


def test_search_questions_with_results(mock_service, mock_question):
    mock_service.search_questions = AsyncMock(
        return_value=_make_search_result([mock_question])
    )
    app = _create_app(mock_service)
    client = TestClient(app)

    payload = {"search_query": "türkiye", "exam_type": "TYT", "limit": 10, "offset": 0}
    response = client.post("/api/v1/questions/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["questions"]) == 1
    q = data["data"]["questions"][0]
    assert q["id"] == "q-uuid-001"
    assert q["exam_type"] == "TYT"


def test_search_questions_show_answers_hidden_by_default(mock_service, mock_question):
    mock_service.search_questions = AsyncMock(
        return_value=_make_search_result([mock_question])
    )
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post(
        "/api/v1/questions/search",
        json={"show_answers": False, "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    q = response.json()["data"]["questions"][0]
    assert "correct_answer" not in q
    assert "options" not in q


def test_search_questions_show_answers_when_requested(mock_service, mock_question):
    mock_service.search_questions = AsyncMock(
        return_value=_make_search_result([mock_question])
    )
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post(
        "/api/v1/questions/search",
        json={"show_answers": True, "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    q = response.json()["data"]["questions"][0]
    assert "correct_answer" in q
    assert "options" in q


def test_search_questions_service_error_returns_500(mock_service):
    mock_service.search_questions = AsyncMock(side_effect=Exception("boom"))
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post("/api/v1/questions/search", json={"limit": 10, "offset": 0})
    assert response.status_code == 500


# ===========================================================================
# 5. GET /search/elasticsearch
# ===========================================================================


def test_elasticsearch_search_happy_path(mock_service, mock_question):
    mock_service.advanced_search_with_elasticsearch = AsyncMock(
        return_value=[mock_question]
    )
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get(
        "/api/v1/questions/search/elasticsearch",
        params={"query": "matematik"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["search_engine"] == "elasticsearch"
    assert data["data"]["count"] == 1


def test_elasticsearch_search_with_filters(mock_service):
    mock_service.advanced_search_with_elasticsearch = AsyncMock(return_value=[])
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get(
        "/api/v1/questions/search/elasticsearch",
        params={"query": "integral", "exam_type": "AYT", "subject": "MATEMATIK"},
    )
    assert response.status_code == 200
    # Verify filters forwarded to service
    call_kwargs = mock_service.advanced_search_with_elasticsearch.call_args
    assert call_kwargs.kwargs["filters"]["exam_type"] == "AYT"
    assert call_kwargs.kwargs["filters"]["subject_area"] == "MATEMATIK"


def test_elasticsearch_search_missing_query_returns_422(mock_service):
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/search/elasticsearch")
    assert response.status_code == 422


# ===========================================================================
# 6. GET /random — tested via direct async call
#    (GET /{question_id} registered before GET /random — HTTP routing conflict)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_random_questions_happy_path(mock_service, mock_question):
    from api.question_crud_api import get_random_questions
    from unittest.mock import MagicMock
    from fastapi import Request

    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()
    mock_request.state.user = None
    mock_request.headers = {}
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"

    mock_service.get_random_questions = AsyncMock(return_value=[mock_question] * 3)
    response = await get_random_questions(
        request=mock_request, count=3, subject_area=None, exam_type=None, service=mock_service
    )
    import json

    data = json.loads(response.body)
    assert data["data"]["count"] == 3
    assert len(data["data"]["questions"]) == 3


@pytest.mark.asyncio
async def test_get_random_questions_includes_options_and_answer(
    mock_service, mock_question
):
    import json

    from api.question_crud_api import get_random_questions
    from unittest.mock import MagicMock
    from fastapi import Request

    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()
    mock_request.state.user = None
    mock_request.headers = {}
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"

    mock_service.get_random_questions = AsyncMock(return_value=[mock_question])
    response = await get_random_questions(
        request=mock_request, count=10, subject_area=None, exam_type=None, service=mock_service
    )
    data = json.loads(response.body)
    q = data["data"]["questions"][0]
    assert "options" in q
    assert q["options"]["A"] == "3"
    assert q["correct_answer"] == "B"


@pytest.mark.asyncio
async def test_get_random_questions_with_filters(mock_service):
    import json

    from api.question_crud_api import get_random_questions
    from unittest.mock import MagicMock
    from fastapi import Request

    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()
    mock_request.state.user = None
    mock_request.headers = {}
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"

    mock_service.get_random_questions = AsyncMock(return_value=[])
    response = await get_random_questions(
        request=mock_request, count=5, subject_area="MATEMATIK", exam_type="TYT", service=mock_service
    )
    data = json.loads(response.body)
    assert data["data"]["count"] == 0
    mock_service.get_random_questions.assert_awaited_once_with(
        count=5, subject_area="MATEMATIK", exam_type="TYT"
    )


@pytest.mark.asyncio
async def test_get_random_questions_service_error_raises_500(mock_service):
    from fastapi import HTTPException

    from api.question_crud_api import get_random_questions
    from unittest.mock import MagicMock
    from fastapi import Request

    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()
    mock_request.state.user = None
    mock_request.headers = {}
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"

    mock_service.get_random_questions = AsyncMock(side_effect=Exception("DB error"))
    with pytest.raises(HTTPException) as exc_info:
        await get_random_questions(
            request=mock_request, count=10, subject_area=None, exam_type=None, service=mock_service
        )
    assert exc_info.value.status_code == 500


# ===========================================================================
# 7. GET /books — tested via direct async call
#    (same HTTP routing conflict as /random and /health)
# ===========================================================================


@pytest.mark.asyncio
async def test_list_source_books_returns_list(mock_service):
    import json

    from api.question_crud_api import list_source_books

    mock_service.list_source_books = AsyncMock(
        return_value=[
            {"name": "Aydın Matematik", "question_count": 340},
            {"name": "Bilgi Fizik", "question_count": 210},
        ]
    )
    response = await list_source_books(
        subject_area=None, exam_type=None, service=mock_service
    )
    data = json.loads(response.body)
    assert data["data"]["total_books"] == 2
    assert data["data"]["books"][0]["name"] == "Aydın Matematik"


@pytest.mark.asyncio
async def test_list_source_books_filters_forwarded(mock_service):
    import json

    from api.question_crud_api import list_source_books

    mock_service.list_source_books = AsyncMock(return_value=[])
    response = await list_source_books(
        subject_area="FIZIK", exam_type="AYT", service=mock_service
    )
    data = json.loads(response.body)
    assert data["data"]["total_books"] == 0
    mock_service.list_source_books.assert_awaited_once_with(
        subject_area="FIZIK", exam_type="AYT"
    )


@pytest.mark.asyncio
async def test_list_source_books_service_error_raises_500(mock_service):
    from fastapi import HTTPException

    from api.question_crud_api import list_source_books

    mock_service.list_source_books = AsyncMock(side_effect=Exception("db error"))
    with pytest.raises(HTTPException) as exc_info:
        await list_source_books(subject_area=None, exam_type=None, service=mock_service)
    assert exc_info.value.status_code == 500


# ===========================================================================
# 8. POST /create — tested via direct async call because the endpoint
#    uses UploadFile=File(None) making it multipart/form-data rather
#    than JSON, which conflicts with json= in TestClient.
# ===========================================================================


@pytest.mark.asyncio
async def test_create_question_happy_path(
    mock_service, mock_question, valid_create_payload
):
    import json

    from api.question_crud_api import QuestionCreateRequest, create_question

    mock_service.create_question = AsyncMock(return_value=mock_question)
    request = QuestionCreateRequest(**valid_create_payload)
    current_user = _mock_current_user()

    response = await create_question(
        request=request,
        image=None,
        current_user=current_user,
        service=mock_service,
    )
    data = json.loads(response.body)
    assert data["success"] is True
    assert data["data"]["id"] == "q-uuid-001"
    assert data["data"]["exam_type"] == "TYT"


@pytest.mark.asyncio
async def test_create_question_service_called_with_user_id(
    mock_service, mock_question, valid_create_payload
):
    from api.question_crud_api import QuestionCreateRequest, create_question

    mock_service.create_question = AsyncMock(return_value=mock_question)
    request = QuestionCreateRequest(**valid_create_payload)
    current_user = _mock_current_user()

    await create_question(
        request=request,
        image=None,
        current_user=current_user,
        service=mock_service,
    )
    call_kwargs = mock_service.create_question.call_args
    assert call_kwargs.kwargs["created_by"] == "user-001"


def test_create_question_missing_required_fields_returns_422(mock_service):
    """Pydantic validation — missing secenekler, dogru_cevap, konu."""
    from pydantic import ValidationError

    from api.question_crud_api import QuestionCreateRequest

    with pytest.raises(ValidationError):
        QuestionCreateRequest(soru_metni="Eksik payload")


@pytest.mark.asyncio
async def test_create_question_service_error_returns_500(
    mock_service, valid_create_payload
):
    from fastapi import HTTPException

    from api.question_crud_api import QuestionCreateRequest, create_question

    mock_service.create_question = AsyncMock(side_effect=Exception("DB yazma hatası"))
    request = QuestionCreateRequest(**valid_create_payload)

    with pytest.raises(HTTPException) as exc_info:
        await create_question(
            request=request,
            image=None,
            current_user=_mock_current_user(),
            service=mock_service,
        )
    assert exc_info.value.status_code == 500


def test_create_question_secenekler_too_short_raises_validation_error():
    """secenekler min_items=4 — three options should fail Pydantic validation."""
    from pydantic import ValidationError

    from api.question_crud_api import QuestionCreateRequest

    with pytest.raises(ValidationError):
        QuestionCreateRequest(
            soru_metni="Soru?",
            secenekler=["A", "B", "C"],  # only 3 — min is 4
            dogru_cevap="A",
            konu="Fizik",
        )


# ===========================================================================
# 9. POST /bulk-create
# ===========================================================================


def test_bulk_create_questions_happy_path(mock_service, valid_create_payload):
    mock_service.bulk_create_questions = AsyncMock(
        return_value={"success_count": 2, "fail_count": 0, "errors": []}
    )
    app = _create_app(mock_service)
    client = TestClient(app)

    payload = [valid_create_payload, valid_create_payload]
    response = client.post("/api/v1/questions/bulk-create", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "2/2" in data["message"]


def test_bulk_create_questions_partial_failure(mock_service, valid_create_payload):
    mock_service.bulk_create_questions = AsyncMock(
        return_value={"success_count": 1, "fail_count": 1, "errors": ["Hata 2"]}
    )
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post(
        "/api/v1/questions/bulk-create",
        json=[valid_create_payload, valid_create_payload],
    )
    assert response.status_code == 201
    data = response.json()
    assert "1/2" in data["message"]


def test_bulk_create_questions_service_error_returns_500(
    mock_service, valid_create_payload
):
    mock_service.bulk_create_questions = AsyncMock(side_effect=Exception("toplu hata"))
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post("/api/v1/questions/bulk-create", json=[valid_create_payload])
    assert response.status_code == 500


# ===========================================================================
# 10. PUT /{question_id}
# ===========================================================================


def test_update_question_happy_path(mock_service, mock_question, valid_update_payload):
    mock_service.update_question = AsyncMock(return_value=mock_question)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.put("/api/v1/questions/q-uuid-001", json=valid_update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "soru_metni" in data["data"]["updated_fields"]


def test_update_question_not_found_returns_404(mock_service, valid_update_payload):
    mock_service.update_question = AsyncMock(return_value=None)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.put("/api/v1/questions/nonexistent-id", json=valid_update_payload)
    assert response.status_code == 404
    assert "bulunamadı" in response.json()["detail"]


def test_update_question_empty_body_returns_400(mock_service):
    app = _create_app(mock_service)
    client = TestClient(app)

    # All fields are Optional — empty dict means no fields to update
    response = client.put("/api/v1/questions/q-uuid-001", json={})
    assert response.status_code == 400
    assert "Güncellenecek alan bulunamadı" in response.json()["detail"]


def test_update_question_version_created_by_default(
    mock_service, mock_question, valid_update_payload
):
    mock_service.update_question = AsyncMock(return_value=mock_question)
    app = _create_app(mock_service)
    client = TestClient(app)

    client.put("/api/v1/questions/q-uuid-001", json=valid_update_payload)

    call_kwargs = mock_service.update_question.call_args
    assert call_kwargs.kwargs["create_version"] is True


def test_update_question_service_error_returns_500(mock_service, valid_update_payload):
    mock_service.update_question = AsyncMock(side_effect=Exception("DB lock"))
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.put("/api/v1/questions/q-uuid-001", json=valid_update_payload)
    assert response.status_code == 500


# ===========================================================================
# 11. GET /{question_id}/history
# ===========================================================================


def test_get_question_history_happy_path(mock_service):
    history = [
        {"version": 1, "changed_at": "2026-01-01T10:00:00", "changes": {}},
        {
            "version": 2,
            "changed_at": "2026-01-02T10:00:00",
            "changes": {"soru_metni": "new"},
        },
    ]
    mock_service.get_question_history = AsyncMock(return_value=history)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/q-uuid-001/history")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["version_count"] == 2
    assert data["data"]["question_id"] == "q-uuid-001"


def test_get_question_history_empty(mock_service):
    mock_service.get_question_history = AsyncMock(return_value=[])
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/new-q/history")
    assert response.status_code == 200
    assert response.json()["data"]["version_count"] == 0


def test_get_question_history_service_error_returns_500(mock_service):
    mock_service.get_question_history = AsyncMock(side_effect=Exception("timeout"))
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/q-uuid-001/history")
    assert response.status_code == 500


# ===========================================================================
# 12. DELETE /{question_id}
# ===========================================================================


def test_delete_question_soft_delete_happy_path(mock_service):
    mock_service.delete_question = AsyncMock(return_value=True)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.delete("/api/v1/questions/q-uuid-001")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["can_restore"] is True
    assert data["data"]["permanent"] is False


def test_delete_question_permanent(mock_service):
    mock_service.delete_question = AsyncMock(return_value=True)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.delete("/api/v1/questions/q-uuid-001?permanent=true")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["permanent"] is True
    assert data["data"]["can_restore"] is False
    assert (
        "kalıcı olarak silindi" in data["message"]
        or "başarıyla silindi" in data["message"]
    )


def test_delete_question_not_found_returns_404(mock_service):
    mock_service.delete_question = AsyncMock(return_value=False)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.delete("/api/v1/questions/ghost-id")
    assert response.status_code == 404


def test_delete_question_service_error_returns_500(mock_service):
    mock_service.delete_question = AsyncMock(side_effect=Exception("fk constraint"))
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.delete("/api/v1/questions/q-uuid-001")
    assert response.status_code == 500


# ===========================================================================
# 13. POST /{question_id}/archive
# ===========================================================================


def test_archive_question_happy_path(mock_service):
    mock_service.archive_question = AsyncMock(return_value=True)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post("/api/v1/questions/q-uuid-001/archive")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "archived"


def test_archive_question_not_found_returns_404(mock_service):
    mock_service.archive_question = AsyncMock(return_value=False)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post("/api/v1/questions/missing-q/archive")
    assert response.status_code == 404


def test_archive_question_service_error_returns_500(mock_service):
    mock_service.archive_question = AsyncMock(side_effect=Exception("oops"))
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post("/api/v1/questions/q-uuid-001/archive")
    assert response.status_code == 500


# ===========================================================================
# 14. POST /{question_id}/restore
# ===========================================================================


def test_restore_question_happy_path(mock_service):
    mock_service.restore_question = AsyncMock(return_value=True)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post("/api/v1/questions/q-uuid-001/restore")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "active"


def test_restore_question_not_found_returns_404(mock_service):
    mock_service.restore_question = AsyncMock(return_value=False)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post("/api/v1/questions/ghost/restore")
    assert response.status_code == 404


def test_restore_question_service_error_returns_500(mock_service):
    mock_service.restore_question = AsyncMock(side_effect=Exception("connection lost"))
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.post("/api/v1/questions/q-uuid-001/restore")
    assert response.status_code == 500


# ===========================================================================
# 15. GET /{question_id}  (get_question — must come after /archived, /random, etc.)
# ===========================================================================


def test_get_question_by_id_happy_path(mock_service, mock_question):
    mock_service.get_question_by_id = AsyncMock(return_value=mock_question)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/q-uuid-001")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    q = data["data"]
    assert q["id"] == "q-uuid-001"
    assert q["correct_answer"] == "B"
    assert "options" in q
    assert "irt_parameters" in q
    assert "statistics" in q
    assert "quality" in q


def test_get_question_by_id_not_found_returns_404(mock_service):
    mock_service.get_question_by_id = AsyncMock(return_value=None)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/does-not-exist")
    assert response.status_code == 404
    assert "bulunamadı" in response.json()["detail"]


def test_get_question_by_id_success_rate_zero_asked(mock_service):
    """When times_asked == 0 success_rate must be 0 (no division by zero)."""
    q = _make_mock_question(times_asked=0, times_correct=0)
    mock_service.get_question_by_id = AsyncMock(return_value=q)
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/q-uuid-001")
    assert response.status_code == 200
    stats = response.json()["data"]["statistics"]
    assert stats["success_rate"] == 0


def test_get_question_by_id_service_error_returns_500(mock_service):
    mock_service.get_question_by_id = AsyncMock(side_effect=Exception("timeout"))
    app = _create_app(mock_service)
    client = TestClient(app)

    response = client.get("/api/v1/questions/q-uuid-001")
    assert response.status_code == 500


# ===========================================================================
# 16. POST /semantic-search
# ===========================================================================


def _make_mock_db_with_rows(rows=None):
    """Build an AsyncMock DB session that returns given rows from execute()."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = rows or []
    mock_db.execute = AsyncMock(return_value=mock_result)
    return mock_db


def _build_semantic_app(mock_db: MagicMock, mock_user: dict = None) -> FastAPI:
    from api.question_crud_api import get_question_service
    from api.question_crud_api import router as q_router
    from core.database import get_db_session
    from core.dependencies import get_current_user

    app = FastAPI()
    svc = AsyncMock()

    async def _override_auth():
        return mock_user or _mock_current_user()

    async def _override_db():
        yield mock_db

    async def _override_service():
        return svc

    app.dependency_overrides[get_current_user] = _override_auth
    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_question_service] = _override_service
    app.include_router(q_router)
    return app


@patch("api.question_crud_api.httpx.AsyncClient")
def test_semantic_search_happy_path(mock_httpx_cls):
    """Successful semantic search with mocked Ollama and DB."""
    # Setup Ollama mock
    mock_http_resp = MagicMock()
    mock_http_resp.raise_for_status = MagicMock()
    mock_http_resp.json.return_value = {"embeddings": [[0.1] * 768]}
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_http_resp)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_httpx_cls.return_value = mock_client_instance

    # DB row mock
    row = MagicMock()
    row.id = "q-sem-001"
    row.question_text = "Türkiye'nin başkenti?"
    row.question_image_url = None
    row.image_ocr_text = None
    row.image_width = None
    row.image_height = None
    row.exam_type = "TYT"
    row.subject_area = "COGRAFYA"
    row.source_book = "Coğrafya Kitabı"
    row.difficulty_level = "EASY"
    row.bloom_level = 1
    row.bloom_category = "Hatırlama"
    row.quality_score = 0.95
    row.word_count = 4
    row.option_a = "Ankara"
    row.option_b = "İstanbul"
    row.option_c = "İzmir"
    row.option_d = "Bursa"
    row.option_e = None
    row.correct_answer = "A"
    row.similarity = 0.92

    mock_db = _make_mock_db_with_rows([row])
    app = _build_semantic_app(mock_db)
    client = TestClient(app)

    response = client.post(
        "/api/v1/questions/semantic-search",
        json={"query": "Türkiye başkenti", "top_k": 5, "min_similarity": 0.3},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_results"] == 1
    assert data["data"]["model"] == "nomic-embed-text"
    assert data["data"]["embedding_dim"] == 768
    assert data["data"]["questions"][0]["id"] == "q-sem-001"
    assert data["data"]["questions"][0]["similarity"] == 0.92


@patch("api.question_crud_api.httpx.AsyncClient")
def test_semantic_search_shows_answers_when_requested(mock_httpx_cls):
    mock_http_resp = MagicMock()
    mock_http_resp.raise_for_status = MagicMock()
    mock_http_resp.json.return_value = {"embeddings": [[0.1] * 768]}
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_http_resp)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_httpx_cls.return_value = mock_client_instance

    row = MagicMock()
    row.id = "q-sem-002"
    row.question_text = "Soru?"
    row.question_image_url = None
    row.image_ocr_text = None
    row.image_width = None
    row.image_height = None
    row.exam_type = "AYT"
    row.subject_area = "MATEMATIK"
    row.source_book = "Kitap"
    row.difficulty_level = "HARD"
    row.bloom_level = 3
    row.bloom_category = "Uygulama"
    row.quality_score = 0.8
    row.word_count = 5
    row.option_a = "1"
    row.option_b = "2"
    row.option_c = "3"
    row.option_d = "4"
    row.option_e = None
    row.correct_answer = "C"
    row.similarity = 0.75

    mock_db = _make_mock_db_with_rows([row])
    app = _build_semantic_app(mock_db)
    client = TestClient(app)

    response = client.post(
        "/api/v1/questions/semantic-search",
        json={"query": "limit hesaplama", "show_answers": True},
    )
    assert response.status_code == 200
    q = response.json()["data"]["questions"][0]
    assert "options" in q
    assert q["correct_answer"] == "C"


@patch("api.question_crud_api.httpx.AsyncClient")
def test_semantic_search_ollama_timeout_returns_503(mock_httpx_cls):
    import httpx

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(
        side_effect=httpx.TimeoutException("timeout", request=MagicMock())
    )
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_httpx_cls.return_value = mock_client_instance

    mock_db = _make_mock_db_with_rows()
    app = _build_semantic_app(mock_db)
    client = TestClient(app)

    response = client.post(
        "/api/v1/questions/semantic-search",
        json={"query": "integral konusu"},
    )
    assert response.status_code == 503
    assert "zaman" in response.json()["detail"].lower()


@patch("api.question_crud_api.httpx.AsyncClient")
def test_semantic_search_ollama_http_error_returns_503(mock_httpx_cls):
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "server error",
            request=MagicMock(),
            response=mock_response,
        )
    )
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_httpx_cls.return_value = mock_client_instance

    mock_db = _make_mock_db_with_rows()
    app = _build_semantic_app(mock_db)
    client = TestClient(app)

    response = client.post(
        "/api/v1/questions/semantic-search",
        json={"query": "türev kuralları"},
    )
    assert response.status_code == 503


@patch("api.question_crud_api.httpx.AsyncClient")
def test_semantic_search_empty_embeddings_returns_503(mock_httpx_cls):
    mock_http_resp = MagicMock()
    mock_http_resp.raise_for_status = MagicMock()
    mock_http_resp.json.return_value = {"embeddings": []}  # empty list

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_http_resp)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_httpx_cls.return_value = mock_client_instance

    mock_db = _make_mock_db_with_rows()
    app = _build_semantic_app(mock_db)
    client = TestClient(app)

    response = client.post(
        "/api/v1/questions/semantic-search",
        json={"query": "olasılık hesaplama"},
    )
    assert response.status_code == 503
    assert "gecersiz yanit" in response.json()["detail"]


@patch("api.question_crud_api.httpx.AsyncClient")
def test_semantic_search_error_key_in_response_returns_503(mock_httpx_cls):
    mock_http_resp = MagicMock()
    mock_http_resp.raise_for_status = MagicMock()
    mock_http_resp.json.return_value = {"error": "model not found"}

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_http_resp)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_httpx_cls.return_value = mock_client_instance

    mock_db = _make_mock_db_with_rows()
    app = _build_semantic_app(mock_db)
    client = TestClient(app)

    response = client.post(
        "/api/v1/questions/semantic-search",
        json={"query": "hız mesafe zaman"},
    )
    assert response.status_code == 503


def test_semantic_search_query_too_short_returns_422():
    mock_db = _make_mock_db_with_rows()
    app = _build_semantic_app(mock_db)
    client = TestClient(app)

    # query min_length=3 — two chars should fail
    response = client.post(
        "/api/v1/questions/semantic-search",
        json={"query": "ab"},
    )
    assert response.status_code == 422


def test_semantic_search_invalid_exam_type_returns_422():
    mock_db = _make_mock_db_with_rows()
    app = _build_semantic_app(mock_db)
    client = TestClient(app)

    # exam_type pattern only allows TYT|AYT|YDT
    response = client.post(
        "/api/v1/questions/semantic-search",
        json={"query": "trigonometri", "exam_type": "LGS"},
    )
    assert response.status_code == 422
