"""K4 -- exam_performance_service konu/zaman sorgulari 4-tablo bolunmesine gocurulmeli.

Olculen kusur (izole reprodukte edildi, 26 Agu 2026):

    >>> from models.question_bank import QuestionBankItem as Question
    >>> Question.subject_area
    AttributeError: QuestionBankItem.subject_area sinif duzeyinde kullanilamaz:
                    bu alan artik metadata_info iliskisinde. Sorguda JOIN kullanin.
    >>> func.case((cond, 1), else_=0)
    TypeError: Function.__init__() got an unexpected keyword argument 'else_'

Iki BAGIMSIZ 500 kaynagi. api/exam_performance.py'deki 5 ucun 5'i de
analyze_exam_performance() uzerinden bu iki metoda giriyor (AST ile sayildi),
ve servis :255-260'ta exception'i YENIDEN FIRLATIYOR -> HTTP 500.

Bu dosya mevcut 1619 satirlik mock paketinden AYRI: o paket bu iki metoda hic
dokunmuyor (grep: 0 eslesme).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import func
from sqlalchemy.dialects import postgresql

from models.question_bank import QuestionBankItem as Question
from services.exam_performance_service import ExamPerformanceService

# --------------------------------------------------------------------------
# Yardimcilar
# --------------------------------------------------------------------------


class YakalayanOturum:
    """execute()'a verilen stmt'leri yakalayan sahte AsyncSession."""

    def __init__(self, sonuclar):
        self.sorgular = []
        self._sonuclar = list(sonuclar)

    async def execute(self, stmt):
        self.sorgular.append(stmt)
        if not self._sonuclar:
            raise AssertionError(
                f"Beklenenden fazla execute cagrisi: {len(self.sorgular)}"
            )
        return self._sonuclar.pop(0)


def _sql(deyim) -> str:
    return str(
        deyim.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


@pytest.fixture
def servis():
    return ExamPerformanceService()


@pytest.fixture
def sinav_oturumu():
    oturum = MagicMock()
    oturum.id = "exam-session-K4"
    oturum.student_id = "student-K4"
    oturum.status = "completed"
    oturum.total_questions = 40
    oturum.time_spent_seconds = 3600
    oturum.duration_minutes = 90
    return oturum


def _konu_satirlari():
    """_analyze_subject_performances'in tukettigi iki sonuc kumesi."""
    istatistik = [
        SimpleNamespace(
            subject_area="MATEMATIK",
            primary_topic_id="topic-1",
            total_questions=10,
            correct_answers=6,
            wrong_answers=4,
            empty_answers=0,
            avg_response_time=55.0,
            avg_difficulty=0.5,
        )
    ]
    zorluk = [
        SimpleNamespace(
            subject_area="MATEMATIK",
            primary_topic_id="topic-1",
            difficulty_level=SimpleNamespace(value="medium"),
            count=10,
        )
    ]
    return [istatistik, zorluk]


def _zaman_satirlari():
    """_analyze_time_usage'in tukettigi iki sonuc kumesi."""
    konu_bazli = [
        SimpleNamespace(subject_area="MATEMATIK", avg_time=55.0, question_count=10)
    ]
    hiz = [
        SimpleNamespace(response_time_seconds=10),
        SimpleNamespace(response_time_seconds=60),
        SimpleNamespace(response_time_seconds=200),
    ]
    return [konu_bazli, hiz]


# --------------------------------------------------------------------------
# 0. ALET DOGRULAMASI -- kusurun PREMISI hala gecerli mi?
#    Bu iki test duserse kapatilacak bir sey yok demektir.
# --------------------------------------------------------------------------


def test_premis_tasinan_kolonlar_sinif_duzeyinde_hala_hata_firlatiyor():
    """Uyumluluk katmani sessiz None DONMUYOR, yol gosteren hata veriyor."""
    for alan, beklenen_iliski in (
        ("subject_area", "metadata_info"),
        ("correct_answer", "content"),
        ("irt_difficulty", "statistics"),
        ("difficulty_level", "statistics"),
    ):
        with pytest.raises(AttributeError) as hata:
            getattr(Question, alan)
        assert beklenen_iliski in str(
            hata.value
        ), f"{alan} artik {beklenen_iliski} uzerinde olmali"

    # Bolunmemis kalan kolonlar AYNEN erisilebilir olmali.
    for alan in ("id", "primary_topic_id", "is_active"):
        assert getattr(Question, alan) is not None


def test_premis_func_case_else_kwargini_kabul_etmiyor():
    """func.case(...) generic Function uretir; else_ kwargi TypeError verir."""
    with pytest.raises(TypeError) as hata:
        func.case((Question.id == "x", 1), else_=0)
    assert "else_" in str(hata.value)


# --------------------------------------------------------------------------
# 1. _analyze_subject_performances
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_konu_performansi_istisnasiz_tamamlaniyor(servis, sinav_oturumu):
    """BUGUN: AttributeError (subject_area sinif duzeyinde)."""
    oturum = YakalayanOturum(_konu_satirlari())

    sonuc = await servis._analyze_subject_performances(oturum, sinav_oturumu)

    # KONTROL KOLU: 'return []' veya kolonlari silen bir "fix" burada duser.
    assert len(sonuc) == 1
    kayit = sonuc[0]
    assert kayit["subject"] == "MATEMATIK"
    assert kayit["topic"] == "topic-1"
    assert kayit["total_questions"] == 10
    assert kayit["correct_answers"] == 6
    assert kayit["success_rate"] == 60.0
    assert kayit["net_score"] == 5.0  # 6 - 4/4
    assert kayit["average_difficulty"] == 0.5  # irt_difficulty hala seciliyor
    assert kayit["difficulty_distribution"] == {"medium": 10}


@pytest.mark.asyncio
async def test_konu_performansi_sorgusu_dogru_tablolara_join_ediyor(
    servis, sinav_oturumu
):
    """stmt derlenip yapisi olculuyor -- bugun stmt hic olusmuyor."""
    oturum = YakalayanOturum(_konu_satirlari())

    await servis._analyze_subject_performances(oturum, sinav_oturumu)

    assert len(oturum.sorgular) == 2, "iki toplu sorgu bekleniyor (N+1 yok)"

    for deyim in oturum.sorgular:
        sql = _sql(deyim)
        # Kartezyen carpim yok: metinsel virgul sayimi alt-sorguya takilir,
        # bu yuzden get_final_froms() kullaniliyor.
        assert (
            len(deyim.get_final_froms()) == 1
        ), f"kartezyen carpim: {len(deyim.get_final_froms())} FROM -> {sql}"
        assert "question_bank" in sql
        assert "question_metadata" in sql, "subject_area question_metadata'da"

        # KONTROL KOLU: is_active filtresi WHERE'de KALMALI. Iddiayi yalnizca
        # whereclause'da ariyoruz -- select(Entity) kolonu SELECT listesine de
        # koyar ve filtre silinse bile dize tam SQL'de durur.
        where_sql = _sql(deyim.whereclause)
        assert "is_active" in where_sql
        assert "exam-session-K4" in where_sql

    istatistik_sql = _sql(oturum.sorgular[0])
    assert "CASE WHEN" in istatistik_sql, "case() gercekten derlenmedi"
    assert "question_content" in istatistik_sql, "correct_answer question_content'te"
    assert "question_statistics" in istatistik_sql, "irt_difficulty statistics'te"

    zorluk_sql = _sql(oturum.sorgular[1])
    assert "question_statistics" in zorluk_sql, "difficulty_level statistics'te"


# --------------------------------------------------------------------------
# 2. _analyze_time_usage
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_zaman_analizi_istisnasiz_tamamlaniyor(servis, sinav_oturumu):
    """BUGUN: AttributeError (subject_area sinif duzeyinde)."""
    oturum = YakalayanOturum(_zaman_satirlari())

    sonuc = await servis._analyze_time_usage(oturum, sinav_oturumu)

    # KONTROL KOLU: konu kirilimi ve hiz dagilimi korunmali.
    assert sonuc["time_by_subject"] == {
        "MATEMATIK": {"average_time": 55.0, "question_count": 10}
    }
    assert sonuc["speed_analysis"] == {"too_fast": 1, "optimal": 1, "too_slow": 1}
    assert sonuc["total_duration_seconds"] == 3600
    assert sonuc["average_time_per_question"] == 90.0


@pytest.mark.asyncio
async def test_zaman_analizi_sorgusu_metadata_join_ediyor(servis, sinav_oturumu):
    oturum = YakalayanOturum(_zaman_satirlari())

    await servis._analyze_time_usage(oturum, sinav_oturumu)

    konu_deyimi = oturum.sorgular[0]
    sql = _sql(konu_deyimi)
    assert len(konu_deyimi.get_final_froms()) == 1, f"kartezyen carpim -> {sql}"
    assert "question_bank" in sql
    assert "question_metadata" in sql, "subject_area question_metadata'da"

    where_sql = _sql(konu_deyimi.whereclause)
    assert "is_active" in where_sql
    assert "exam-session-K4" in where_sql
