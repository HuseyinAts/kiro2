"""`/api/v1/exams` ucu: ROUTER KAYITLI DEGIL (SS10.65).

OLCULEN DURUM (7 Eyl 2026)
--------------------------
Bu dosyadaki 4 test de 404 aliyor -- CI'da ve YERELDE birebir ayni
(`pytest tests/api/test_exams_v1_api.py -n 0` -> 4 failed, 404).
Sebep bir mock/izolasyon kusuru degil: uc GERCEKTEN yok.

    backend/api/v1/exams.py:20   router = APIRouter(prefix="/api/v1/exams")
    backend/api/v1/exams.py:192  @router.post("/generate-mock")
    backend/api/v1/exams.py:305  @router.get("/{session_id}")
    backend/api/v1/exams.py:367  @router.post("/{session_id}/answer")
    backend/api/v1/exams.py:423  @router.post("/{session_id}/submit")

Router VAR ama hicbir yerden kaydedilmiyor: `git grep "api.v1.exams"`
yalnizca dosyanin kendisini ve middleware/dokuman referanslarini buluyor;
`backend/routers/loader.py` kayit tablosunda YOK.

Karsi taraf da yayinda degil: `frontend/src/features/exams/ExamSession.tsx`
`mockExamService`i cagiriyor ama o bilesen yalnizca kendi testinden ithal
ediliyor, hicbir rotaya bagli degil. Yani bu CANLI bir kirik degil,
BITMEMIS bir ozellik -- iki ucu da bagli degil.

NEDEN SILINMIYOR, NEDEN xfail
-----------------------------
Testler dogru bir iddiada bulunuyor (ozellik calismali). Silmek bilgiyi yok
eder; `skip` sessizce unutulur. `xfail(strict=True)` ise: bugun yesil, ama
router kaydedildigi an XPASS verip KIRAR -- yani "ozellik acildi, testi
guncelle" sinyali otomatik gelir. Bu, deponun `test_icerik_gecerliligi.py`de
kurdugu desenin aynisi.

KAYIT ONCESI COZULMESI GEREKEN GUVENLIK KUSURU (Huseyin'in karari)
------------------------------------------------------------------
`@router.get("/{session_id}")` (satir 305) `get_current_user` ALMIYOR ve
sahiplik kontrolu YAPMIYOR: kardes uclarin (`/answer`, `/submit`) aksine.
Router bugunku haliyle kaydedilirse, herhangi biri herhangi bir ogrencinin
sinav oturumunu -- sorulari ve verdigi cevaplariyla -- kimlik dogrulamasiz
okuyabilir (IDOR). Kayit bu duzeltmeden ONCE yapilmamali.

Detay: docs/guvenlik-borcu.md SS10.65
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from core.dependencies import get_current_user, get_db
from main import app
from models.enums_db import ExamType

pytestmark = pytest.mark.xfail(
    strict=True,
    reason=(
        "api/v1/exams.py router'i hicbir yerden kaydedilmiyor -> 4 uc de 404. "
        "Bitmemis ozellik (frontend ExamSession.tsx de rotaya bagli degil). "
        "Kayit yapilirsa bu testler XPASS verip kirar; o an guncellensin. "
        "ONCE satir 305'teki kimlik dogrulamasiz GET /{session_id} (IDOR) "
        "duzeltilmeli -- SS10.65."
    ),
)


@pytest.fixture
def mock_db_session():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.add_all = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session


@pytest.mark.asyncio
async def test_generate_mock_exam_endpoint(mock_db_session):
    # Mock database queries for topic and question selection
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id="test-student-id")

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/v1/exams/generate-mock", json={"student_id": "test-student-id"}
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["status"] == "success"
            assert "exam_session_id" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_exam_session_endpoint(mock_db_session):
    # Mock ExamSession object returned by get_exam_session query
    mock_session_obj = MagicMock()
    mock_session_obj.id = "session-123"
    mock_session_obj.exam_name = "TYT Deneme Sınavı"
    mock_session_obj.exam_type = ExamType.TYT
    mock_session_obj.total_questions = 120
    mock_session_obj.duration_minutes = 165
    mock_session_obj.status = "in_progress"

    mock_eq = MagicMock()
    mock_eq.question_order = 1
    # Soru metni/secenekler question_bank'ta degil question_content'te tutulur.
    # MagicMock her attr'i otomatik uretir; kullanilmayan siklar acikca None olmali.
    mock_eq.question = MagicMock(
        id="q-1",
        content=MagicMock(
            question_text="Soru metni",
            option_a="Şık A",
            option_b="Şık B",
            option_c=None,
            option_d=None,
            option_e=None,
        ),
    )

    mock_session_obj.exam_questions = [mock_eq]
    mock_session_obj.student_answers = []

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_session_obj
    mock_db_session.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id="test-student-id")

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/exams/session-123")
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == "session-123"
            assert len(data["questions"]) == 1
            q = data["questions"][0]
            assert q["text"] == "Soru metni"
            assert q["branch"] == "TUR"
            assert q["options"] == [
                {"letter": "A", "text": "Şık A"},
                {"letter": "B", "text": "Şık B"},
            ]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_save_answer_endpoint(mock_db_session):
    mock_session_obj = MagicMock(id="session-123", student_id="test-student-id")
    mock_result_session = MagicMock()
    mock_result_session.scalar_one_or_none.return_value = mock_session_obj

    mock_result_ans = MagicMock()
    mock_result_ans.scalar_one_or_none.return_value = None  # No prior answer recorded

    mock_db_session.execute.side_effect = [mock_result_session, mock_result_ans]

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id="test-student-id")

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/v1/exams/session-123/answer",
                json={
                    "question_id": "q-1",
                    "selected_answer": "A",
                    "response_time_seconds": 10.0,
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            assert data["selected_answer"] == "A"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_exam_endpoint(mock_db_session):
    mock_session_obj = MagicMock()
    mock_session_obj.id = "session-123"
    mock_session_obj.student_id = "test-student-id"
    mock_session_obj.status = "in_progress"

    mock_eq = MagicMock()
    mock_eq.question_order = 1
    # correct_answer question_content'te (question_bank'ta boyle bir kolon yok).
    mock_eq.question = MagicMock(
        id="q-1",
        content=MagicMock(correct_answer="A", explanation="Çözüm"),
    )

    mock_ans = MagicMock()
    mock_ans.question_id = "q-1"
    mock_ans.selected_answer = "A"

    mock_session_obj.exam_questions = [mock_eq]
    mock_session_obj.student_answers = [mock_ans]

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_session_obj
    mock_db_session.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id="test-student-id")

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/v1/exams/session-123/submit", json={"time_spent_seconds": 3600}
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            assert data["total_correct"] == 1
            assert data["branch_breakdown"]["TUR"]["net"] == 1.0
    finally:
        app.dependency_overrides.clear()
