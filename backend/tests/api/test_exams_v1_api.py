"""`/api/v1/exams` ucu: kayit, IDOR ve UYDURMA (SS10.65 -> SS10.71 -> SS10.73).

GECMIS (SS10.65, 7 Eyl 2026)
----------------------------
Bu dosyadaki 4 test de 404 aliyordu -- CI'da ve YERELDE birebir ayni.
Sebep mock/izolasyon kusuru degildi: `backend/api/v1/exams.py` VARDI ama
`backend/routers/loader.py` kayit tablosunda YOKTU, yani 4 uc hicbir zaman
uygulamaya baglanmamisti. Testler o sirada `xfail(strict=True)` ile
civilenmisti: "router kaydedilirse XPASS verip KIRAR, o an guncellensin".

BUGUN (SS10.71): router kaydedildi, dolayisiyla xfail KALKTI. Testler artik
gercekten kosuyor.

KAYITTAN ONCE KAPATILAN GUVENLIK KUSURU
---------------------------------------
`@router.get("/{session_id}")` kardes uclarin (`/answer`, `/submit`) aksine
`get_current_user` ALMIYOR ve sahiplik kontrolu YAPMIYORDU. Bu haliyle
kaydedilseydi herhangi biri herhangi bir ogrencinin sinav oturumunu --
SORULARI ve VERDIGI CEVAPLARI dahil -- kimlik dogrulamasiz okuyabilirdi
(IDOR). Kayittan ONCE kapatildi; asagidaki
`test_get_exam_session_baskasinin_oturumu_403` o kapiyi civiliyor.

UYDURMA (SS10.73)
-----------------
Rota baglanmadan once "baglansaydi ogrenci ne gorurdu" olculdu. Uc, bos
bransi TUM bankadan brans gozetmeksizin dolduruyor; metin/sik eksikse
"Ornek soru N" / "Secenek A" uyduruyordu. Canli veride TUR ve SOS'ta 0 soru,
bankanin ~%90'i kimya oldugu icin ogrenci "Turkce" bolumunde kimya sorusu
gorurdu. Ayrica uretim sirasi (TUR,MAT,SOS,FEN) puanlama sirasindan
(TUR,SOS,MAT,FEN) farkliydi: 120 sorunun 40'i yanlis bransta puanlaniyordu.
Buradaki dort yeni test o uc kapiyi da civiliyor.

Detay: docs/guvenlik-borcu.md SS10.65, SS10.71 ve SS10.73
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from api.v1.exams import (
    TYT_BOLUMLERI,
    _branch_for_order,
    _options_from_content,
)
from core.dependencies import get_current_user, get_db
from main import app
from models.enums_db import ExamType


def _konu_sonucu(konu_idleri: list[str]) -> MagicMock:
    """`_brans_konu_idleri`'nin bekledigi satir sekli: tek kolonlu tuple'lar."""
    sonuc = MagicMock()
    sonuc.all.return_value = [(kid,) for kid in konu_idleri]
    return sonuc


def _havuz_sonucu(adet: int, onek: str) -> MagicMock:
    """`_brans_soru_havuzu`'nun bekledigi satir sekli: (soru_id, zorluk).

    zorluk None -> `_zorluk()` "orta" doner; all-orta havuz assembler'in
    fallback zinciriyle tam `adet` soru verir (test_assembly.py:128-146).
    """
    sonuc = MagicMock()
    sonuc.all.return_value = [(f"{onek}-{i}", None) for i in range(adet)]
    return sonuc


@pytest.fixture
def mock_db_session():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.add_all = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session


def test_bolum_sirasi_puanlama_sirasiyla_ayni():
    """SIRA CIVISI (SS10.73) -- DB'ye hic dokunmaz, ortamdan bagimsizdir.

    ONCEKI KUSUR: uretim `TYT_BLUEPRINT` dict SIRASINI (TUR,MAT,SOS,FEN),
    puanlama ise elle yazilmis `_BRANCH_RANGES`'i (TUR,SOS,MAT,FEN)
    kullaniyordu. 41-60 arasi sorular MAT olarak uretilip SOS olarak,
    81-100 arasi SOS olarak uretilip MAT olarak puanlaniyordu: soru bankasi
    kusursuz olsa BILE 120 sorunun 40'i yanlis bransta.

    Bu test iki sirayi yan yana koyar. Biri digerinden ayrilirsa KIRILIR.
    """
    uretim_sirasi: list[str] = []
    for brans, adet in TYT_BOLUMLERI:
        uretim_sirasi.extend([brans] * adet)

    for sira, beklenen in enumerate(uretim_sirasi, start=1):
        assert _branch_for_order(sira) == beklenen, (
            f"{sira}. soru {beklenen} olarak URETILIYOR ama "
            f"{_branch_for_order(sira)} olarak PUANLANIYOR "
            "-- api/v1/exams.py TYT_BOLUMLERI / _BRANCH_RANGES, docs SS10.73."
        )


def test_secenek_uydurmaz():
    """`_options_from_content` artik sahte secenek URETMEZ (SS10.73).

    Eskiden icerik yoksa "Secenek A".."Secenek E" donuyordu; ogrenci
    cevaplanabilir gorunen ama gercek olmayan bir soru gorurdu.
    """
    assert _options_from_content(None) == []
    bos_icerik = MagicMock(
        option_a=None, option_b=None, option_c=None, option_d=None, option_e=None
    )
    assert _options_from_content(bos_icerik) == []


@pytest.mark.asyncio
async def test_generate_mock_exam_endpoint(mock_db_session):
    """Tam dolu havuzla 120 soruluk deneme kurulur VE siralar dogru bransa duser.

    Her brans kendi onekiyle soru uretir ("TUR-0", "SOS-3"...); boylece
    `add_all`'a giden ExamQuestion listesinden her sorunun URETILDIGI brans
    okunabilir ve `_branch_for_order`'in PUANLAYACAGI bransla karsilastirilir.
    """
    yanitlar = []
    for brans, adet in TYT_BOLUMLERI:
        yanitlar.append(_konu_sonucu([f"konu-{brans}"]))
        yanitlar.append(_havuz_sonucu(adet, brans))
    mock_db_session.execute.side_effect = yanitlar

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id="test-student-id")

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/v1/exams/generate-mock", json={"student_id": "test-student-id"}
            )
            assert resp.status_code == 201, resp.text
            data = resp.json()
            assert data["status"] == "success"
            assert "exam_session_id" in data
            assert data["total_questions"] == 120

        eklenenler = mock_db_session.add_all.call_args[0][0]
        assert len(eklenenler) == 120
        for eq in eklenenler:
            uretilen_brans = eq.question_id.split("-")[0]
            assert uretilen_brans == _branch_for_order(eq.question_order), (
                f"{eq.question_order}. sirada {uretilen_brans} sorusu var ama "
                f"{_branch_for_order(eq.question_order)} olarak puanlanacak "
                "-- docs SS10.73."
            )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generate_mock_eksik_brans_409(mock_db_session):
    """UYDURMA CIVISI (SS10.73): eksik brans TUM bankadan doldurulamaz.

    ONCEKI DAVRANIS: bir bransin sorusu yetmezse "fallback" tum aktif
    bankadan brans gozetmeksizin doldurur, uc 201 "success" donerdi. Canli
    olcumde TUR/SOS'ta 0 soru, bankanin ~%90'i kimya oldugu icin ogrenciye
    "Turkce" basligi altinda kimya sorulari gosterilecekti.

    Artik uc 409 doner ve hangi bransin eksik oldugunu SOYLER. 201 goruluyorsa
    brans-koru fallback geri gelmis demektir.
    """
    bos = MagicMock()
    bos.all.return_value = []
    mock_db_session.execute.return_value = bos

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id="test-student-id")

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/v1/exams/generate-mock", json={"student_id": "test-student-id"}
            )
            assert resp.status_code == 409, (
                "Soru bankasi bos iken deneme KURULMAMALI. 201 goruluyorsa "
                "brans-koru fallback geri gelmis demektir -- docs SS10.73."
            )
            assert "TUR (0/40)" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_exam_session_endpoint(mock_db_session):
    # Mock ExamSession object returned by get_exam_session query
    mock_session_obj = MagicMock()
    mock_session_obj.id = "session-123"
    # SS10.71: uc artik sahiplik kontrolu yapiyor; oturum ISTEYENE ait olmali.
    mock_session_obj.student_id = "test-student-id"
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
async def test_get_exam_session_baskasinin_oturumu_403(mock_db_session):
    """IDOR CIVISI (SS10.71).

    `GET /api/v1/exams/{session_id}` kayittan once `get_current_user` ALMIYOR
    ve sahiplik kontrolu YAPMIYORDU; herhangi biri herhangi bir ogrencinin
    sinav oturumunu -- sorulari ve verdigi cevaplariyla -- okuyabilirdi.

    Bu test o kapiyi civiliyor: oturum BASKASINA aitse 403 donmeli. Kontrol
    kaldirilirsa bu test 200 gorup KIRILIR.

    Not: yalnizca 200/403 ayrimini olcuyor, sorularin bicimini degil -- o
    zaten `test_get_exam_session_endpoint` icinde civili.
    """
    baskasinin_oturumu = MagicMock()
    baskasinin_oturumu.id = "session-999"
    baskasinin_oturumu.student_id = "baska-ogrenci-id"
    baskasinin_oturumu.exam_questions = []
    baskasinin_oturumu.student_answers = []

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = baskasinin_oturumu
    mock_db_session.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id="test-student-id")

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/exams/session-999")
            assert resp.status_code == 403, (
                "Baskasinin sinav oturumu 403 DONMELI. 200 goruluyorsa "
                "sahiplik kontrolu kaldirilmis demektir (IDOR) -- "
                "api/v1/exams.py:305, docs SS10.71."
            )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_exam_session_icerigi_eksik_soru_409(mock_db_session):
    """UYDURMA CIVISI (SS10.73): eksik icerikli soru "Ornek soru" diye sunulmaz.

    ONCEKI DAVRANIS: metin yoksa "Ornek soru N", soru kaydi yoksa "dummy-N"
    id, secenek yoksa "Secenek A..E" uydurulur ve HTTP 200 donulurdu -- yani
    ogrenci uydurma bir soruyu cevaplardi. Artik 409 doner ve eksik sirayi
    soyler. 200 goruluyorsa uydurma geri gelmis demektir.
    """
    oturum = MagicMock()
    oturum.id = "session-777"
    oturum.student_id = "test-student-id"
    oturum.exam_name = "TYT Deneme"
    oturum.exam_type = ExamType.TYT
    oturum.total_questions = 1
    oturum.duration_minutes = 165
    oturum.status = "in_progress"

    eksik_eq = MagicMock()
    eksik_eq.question_order = 7
    eksik_eq.question = MagicMock(
        id="q-7",
        content=MagicMock(
            question_text=None,
            option_a=None,
            option_b=None,
            option_c=None,
            option_d=None,
            option_e=None,
        ),
    )
    oturum.exam_questions = [eksik_eq]
    oturum.student_answers = []

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = oturum
    mock_db_session.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id="test-student-id")

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/exams/session-777")
            assert resp.status_code == 409, (
                "Icerigi eksik soru UYDURULARAK sunulmamali (200 = uydurma "
                "geri geldi) -- api/v1/exams.py, docs SS10.73."
            )
            assert "7" in resp.json()["detail"]
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
