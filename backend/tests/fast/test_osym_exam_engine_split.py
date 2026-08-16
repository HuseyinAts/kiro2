"""core/osym_exam_engine.py'nin #485 split sonrasi sorgularini civileyen testler.

AST sayaci (`scripts/scan_split_accesses.py`) OLCTU: SINIF=42 · KWARG=2 · ENTITY=5.
Eski regex sayaci "1" diyordu (satir 1327 bir YORUM, fantom): dosya
`QuestionBankItem`'i `as Question` (:33) ve `as _QB` (:692) takma adlariyla import
ediyor, regex takma adi goremiyordu.

Iki ayri kusur sinifi var ve ikisi de sessiz:

1. **SINIF duzeyi** — `select(Question.correct_answer)` gibi erisim strangler
   devredicisinde `AttributeError` atar, yani sorgu CALISMA aninda degil
   KURULUM aninda olur. `_analyze_performance` (:1827) ve `save_answer` (:703)
   bunu ciplak `except` ile yutuyor → motor "0 dogru cevap" ve "is_correct=NULL"
   uretip devam ediyor. `_select_questions` / `_select_beta_questions` ise
   yutmuyor, dogrudan patliyor.

2. **ORNEK duzeyi** — `select(Question)` ile ENTITY secilip donen nesneden
   `question.subject_area` / `.correct_answer` / `.irt_difficulty` okunuyor.
   Uc split iliskisi de `lazy='select'` (models/question_bank.py:201-218,
   `lazy=` belirtilmemis → varsayilan) → async oturumda eager-load yoksa
   `MissingGreenlet`. Bu erisimleri AST sayaci GORMEZ (S214 dersi).

Testler GERCEK `models.question_bank` modeline karsi kosar (S212 D maddesi:
sahte `sys.modules` stub'i kullanan test KIRIK kodda da yesil kalir —
`tests/integration/test_osym_exam_engine.py` tam bu yuzden 26/26 SKIP).
`tests/fast/` altinda `conftest.py` yok; kok `conftest.py` yalnizca `chromadb`
stub'liyor, `models` / `sqlalchemy` degil (olculdu).

`select_from` NOTU (S214 dersi): motorun sorgularinin SELECT listesinde her
zaman bir `question_bank` kolonu (`Question.id` veya tam entity) var, bu yuzden
`.select_from(QuestionBankItem)` SUS olur ve hicbir mutasyonla civilenemez.
Riski `FROM question_bank JOIN ...` + `get_final_froms() == 1` assert'leri
karsiliyor.
"""

import copy
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# S212 / S214 yardimcilari
# ---------------------------------------------------------------------------


def _compiled_sql(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def _compiled_where(stmt) -> str:
    """S214 dersi: WHERE iddiasi SADECE `whereclause` uzerinde aranir.

    `select(Question)` TUM `question_bank` kolonlarini SELECT listesine koyar;
    `is_active` filtresi WHERE'den tamamen silinse bile tam SQL'de
    `question_bank.is_active` dizesi SELECT listesinde durur ve test
    yanlis-yesil kalir (olculdu: mutasyon hayatta kalmisti).
    """
    assert stmt.whereclause is not None, "sorguda hic WHERE yok"
    return str(
        stmt.whereclause.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def _assert_single_from(stmt) -> None:
    """Kartezyen kontrolu — METIN degil YAPI uzerinden (S212 B maddesi)."""
    froms = stmt.get_final_froms()
    assert len(froms) == 1, f"kartezyen carpim: {len(froms)} ayri FROM"


def _eager_loaded(stmt) -> dict[str, str | None]:
    """Yuklenen iliski -> yukleme stratejisi. Metin degil YAPI okur.

    Olculdu (SQLAlchemy 2.0.45): `selectinload(X.rel)` bir `Load` uretir;
    `opt.path[1].key` iliski adini, `dict(opt.context[0].strategy)["lazy"]`
    stratejiyi verir. Secenek yoksa `_with_options` bos demettir → {}.
    """
    loaded: dict[str, str | None] = {}
    for opt in stmt._with_options:
        strategy = dict(opt.context[0].strategy) if opt.context else {}
        loaded[opt.path[1].key] = strategy.get("lazy")
    return loaded


class _CaptureSession:
    """Kurulan her `stmt`'i yakalar; gercek DB'ye gitmez.

    Motorun sonucu TUKETME sekilleri kodda tek tek okundu:
      * `get_current_question`            -> `result.scalar_one_or_none()`
      * `save_answer` notlandirma (:697)  -> `(...).scalar_one_or_none()`
      * `get_subject_performance` (:1326) -> `for question, answer in result`
      * `_select_*` id havuzu             -> `id_result.all()`  (row[0], row[1])
      * `_select_*` entity sorgusu        -> `result.scalars().all()`
      * `_analyze_performance` (:1722)    -> `for row in result` + `row.id`
    """

    def __init__(self, rows_per_call=None, scalar_per_call=None):
        self._rows = rows_per_call or []
        self._scalars = scalar_per_call or []
        self.statements: list = []
        self.committed = False

    async def execute(self, stmt, params=None):
        idx = len(self.statements)
        self.statements.append(stmt)
        rows = self._rows[idx] if idx < len(self._rows) else []
        result = MagicMock()
        result.all.return_value = rows
        result.scalars.return_value.all.return_value = rows
        result.__iter__ = lambda _self: iter(rows)
        result.scalar_one_or_none.return_value = (
            self._scalars[idx] if idx < len(self._scalars) else None
        )
        return result

    async def commit(self):
        self.committed = True

    def add(self, obj):  # pragma: no cover - motor bu yolda kullanmiyor
        pass


class _Ctx:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *exc):
        return False


@pytest.fixture
def wired(monkeypatch):
    """IKI hedefi birden yamalar — ikisi de ZORUNLU (olculdu).

    * `core.osym_exam_engine.get_db_session_context` (modul duzeyi, :24) —
      `get_current_question` / `get_subject_performance` / `_select_*` /
      `_analyze_performance` bunu kullanir.
    * `core.database.get_db_session_context` — `save_answer` (:632) adi
      fonksiyon GOVDESINDE import ediyor. Python `from X import Y`'yi yerel
      bagladigi icin modul-duzeyi yama o fonksiyon icin ETKISIZ kalir; yalniz
      modul yamasi birakilirsa `save_answer` GERCEK DB'ye baglanmaya calisir.
    """
    import core.database
    import core.osym_exam_engine as eng

    def make(rows_per_call=None, scalar_per_call=None):
        session = _CaptureSession(rows_per_call, scalar_per_call)
        monkeypatch.setattr(eng, "get_db_session_context", lambda: _Ctx(session))
        monkeypatch.setattr(
            core.database, "get_db_session_context", lambda: _Ctx(session)
        )
        return session

    return make


@pytest.fixture
def engine():
    """Her testte TAZE motor.

    `_question_pool_cache` (:147) ve `_performance_cache` (:149) ORNEK
    duzeyinde. Paylasilan motorda cache HIT olursa sorgu hic kurulmaz ve test
    yanlis-yesil olur.
    """
    from core.osym_exam_engine import OSYMExamEngine

    return OSYMExamEngine()


def _config(engine, *, subject="MATEMATIK", count=3, difficulty=None, beta=False):
    """`difficulty` SADECE `DIFFICULTY_MAP` anahtari olabilir (:1405).

    Olculdu: `{"kolay", "orta", "zor", "cok_zor"}`. "medium" gibi gecersiz bir
    anahtar `.get()` ile `None` doner → hem zorluk filtresi hem de fallback
    dali (:1625 `and difficulty_levels`) SESSIZCE devre disi kalir ve test
    yanlis-kirmizi olur.
    """
    from models.database import ExamType

    cfg = copy.deepcopy(engine.exam_configs[ExamType.TYT])
    cfg.subject_distribution = {subject: count}
    cfg.total_questions = count
    cfg.difficulty = difficulty
    cfg.beta_practice = beta
    return cfg


def _session_data(engine, **kw):
    from core.osym_exam_engine import ExamSessionData, ExamStatus
    from models.database import ExamType

    payload = {
        "session_id": "s-1",
        "student_id": "u-1",
        "exam_config": engine.exam_configs[ExamType.TYT],
        "status": ExamStatus.IN_PROGRESS,
        "questions": ["q-1"],
        "answers": {"q-1": "A"},
    }
    payload.update(kw)
    return ExamSessionData(**payload)


def _real_question(qid="q-1", *, text="Soru metni?", answer="A", subject="MATEMATIK"):
    """GERCEK ORM nesneleri (S212 D maddesi: sahte stub KIRIK kodda da yesil)."""
    from models.question_bank import (
        QuestionBankItem,
        QuestionContent,
        QuestionDifficultyLevel,
        QuestionMetadata,
        QuestionStatistics,
    )

    question = QuestionBankItem(id=qid, primary_topic_id="t-1", is_active=True)
    question.content = QuestionContent(
        id=qid,
        question_text=text,
        option_a="A sikki",
        option_b="B sikki",
        option_c="C sikki",
        option_d="D sikki",
        option_e=None,
        correct_answer=answer,
    )
    question.metadata_info = QuestionMetadata(id=qid, subject_area=subject)
    question.statistics = QuestionStatistics(
        id=qid, difficulty_level=QuestionDifficultyLevel.MEDIUM
    )
    return question


# ===========================================================================
# Task 2: save_answer notlandirma sorgusu (:697)
# ===========================================================================
class TestSaveAnswerGrading:
    @pytest.mark.asyncio
    async def test_grading_query_selects_from_question_content(self, wired, engine):
        """`_QB.correct_answer` sinif duzeyi → AttributeError → :703 yutuyor.

        Sonuc: notlandirma sorgusu HIC kurulmuyor, `student_answers.is_correct`
        kalici olarak NULL kaliyor ve mastery hattinin filtresi bos donuyor.
        """
        session = wired(scalar_per_call=["A"])
        engine.active_sessions["s-1"] = _session_data(engine, answers={})

        await engine.save_answer("s-1", "q-1", "A")

        selects = [
            st
            for st in session.statements
            if str(st).lstrip().upper().startswith("SELECT")
        ]
        assert selects, "notlandirma sorgusu hic kurulmadi (:703 except yutuyor)"
        assert selects[0].selected_columns[0].table.name == "question_content"

    @pytest.mark.asyncio
    async def test_is_correct_written_true_for_matching_answer(self, wired, engine):
        session = wired(scalar_per_call=["A"])
        engine.active_sessions["s-1"] = _session_data(engine, answers={})

        await engine.save_answer("s-1", "q-1", "a")  # normalize edilmeli

        inserts = [
            st
            for st in session.statements
            if "student_answers" in str(st) and "INSERT" in str(st).upper()
        ]
        assert inserts, "INSERT hic kurulmadi"
        assert inserts[0].compile().params.get("is_correct") is True


# ===========================================================================
# Task 3: _select_beta_questions — pipeline_metadata filtresi (:1436)
# ===========================================================================
class TestSelectBetaQuestions:
    @pytest.mark.asyncio
    async def test_both_queries_build_and_compile(self, wired, engine):
        """Havuz sorgusu + entity sorgusu; ikisi de kurulup derlenebilmeli.

        Havuza bir satir veriliyor, aksi halde `if not pool: return []` erken
        donusu ikinci sorguyu hic kurdurmaz ve test onu olcemez.
        """
        session = wired([[("qb-1",)], []])

        await engine._select_beta_questions(5)

        assert len(session.statements) == 2, session.statements
        for stmt in session.statements:
            _compiled_sql(stmt)
            _assert_single_from(stmt)

    @pytest.mark.asyncio
    async def test_pipeline_metadata_filter_moved_to_metadata_table(
        self, wired, engine
    ):
        session = wired([[("qb-1",)], []])

        await engine._select_beta_questions(5)

        where_sql = _compiled_where(session.statements[0])
        assert "question_metadata.pipeline_metadata" in where_sql, where_sql
        # is_active kapisi YANINA gelir, YERINE degil (core/quality_gate.py).
        assert "question_bank.is_active" in where_sql, where_sql


# ===========================================================================
# Task 4-5: ENTITY donen yollar — eager-load (ORNEK duzeyi kusur)
# ===========================================================================
class TestEntityQueriesEagerLoad:
    @pytest.mark.asyncio
    async def test_get_current_question_eager_loads_all_three(self, wired, engine):
        """api/sinav.py:491-510 donen nesneden 12 split alani okuyor (olculdu).

        content: question_text, question_image_url, image_ocr_text, image_width,
        image_height, option_a..option_e · metadata_info: subject_area ·
        statistics: difficulty_level. Ucu de `lazy='select'` → eager-load yoksa
        async oturumda `MissingGreenlet`.
        """
        session = wired()
        engine.active_sessions["s-2"] = _session_data(
            engine, session_id="s-2", answers={}
        )

        await engine.get_current_question("s-2")

        assert _eager_loaded(session.statements[0]) == {
            "content": "selectin",
            "metadata_info": "selectin",
            "statistics": "selectin",
        }

    @pytest.mark.asyncio
    async def test_get_subject_performance_eager_loads_and_reads_real_orm(
        self, wired, engine
    ):
        """:1329 subject_area · :1346 irt_difficulty · :1351 correct_answer.

        (:1327 bir YORUM satiri — eski regex sayacinin "1 erisim" fantomu.)

        Okuma iddiasi tek basina VAKUM olurdu: `select(Question, StudentAnswer)`
        sinif duzeyi tasinmis alan kullanmadigi icin sorgu bugun de kuruluyor ve
        elle kurulmus transient nesnede devrediciler zaten calisiyor. Bu yuzden
        eager-load iddiasiyla AYNI testte tutuluyor — RED sebebi eager-load,
        okuma assert'i ise fix sonrasi anlam regresyonunu civiliyor.
        """
        question = _real_question("q-1", subject="GEOMETRI")
        answer = SimpleNamespace(
            is_correct=True, response_time_seconds=12.0, selected_answer="A"
        )
        session = wired([[(question, answer)]])

        out = await engine.get_subject_performance("s-1")

        assert _eager_loaded(session.statements[0]) == {
            "content": "selectin",
            "metadata_info": "selectin",
            "statistics": "selectin",
        }
        _assert_single_from(session.statements[0])
        assert [p.subject for p in out] == ["geometri"]
        assert [p.correct_answers for p in out] == [1]


# ===========================================================================
# Task 6: _analyze_performance — sorgu (:1716) + iki UPDATE (:1779, :1785)
# ===========================================================================
class TestAnalyzePerformance:
    @pytest.mark.asyncio
    async def test_correct_answer_selected_from_question_content(self, wired, engine):
        session = wired([[]])

        await engine._analyze_performance(_session_data(engine))

        assert (
            session.statements
        ), "hicbir sorgu kurulmadi (:1827 AttributeError yutuyor)"
        # `correct_answer` question_content'ten gelmeli. `id` kolonunun HANGI
        # tablodan secildigi iddia EDILMEZ: paylasilan PK oldugu icin
        # `Q.id` de `QC.id` de dogru; sirali iddia fix'i gereksiz kisitlar.
        cols = {c.table.name for c in session.statements[0].selected_columns}
        assert "question_content" in cols, cols
        assert cols <= {"question_bank", "question_content"}, cols
        _assert_single_from(session.statements[0])

    @pytest.mark.asyncio
    async def test_correct_answer_scores_one_net(self, wired, engine):
        session = wired([[SimpleNamespace(id="q-1", correct_answer="A")]])

        metrics = await engine._analyze_performance(
            _session_data(engine, questions=["q-1"], answers={"q-1": "A"})
        )

        assert session.statements, "dogru-cevap sorgusu hic kurulmadi"
        assert (
            metrics.correct_answers == 1
        ), "dogru cevap sayilmadi (sessiz AttributeError?)"
        assert metrics.net_score == 1.0

    @pytest.mark.asyncio
    async def test_wrong_answer_scores_zero_net(self, wired, engine):
        session = wired([[SimpleNamespace(id="q-1", correct_answer="B")]])

        metrics = await engine._analyze_performance(
            _session_data(engine, questions=["q-1"], answers={"q-1": "A"})
        )

        assert session.statements, "dogru-cevap sorgusu hic kurulmadi"
        assert (
            metrics.correct_answers,
            metrics.wrong_answers,
            metrics.net_score,
        ) == (0, 1, 0.0)

    @pytest.mark.asyncio
    async def test_times_asked_update_targets_question_statistics(self, wired, engine):
        session = wired([[SimpleNamespace(id="q-1", correct_answer="A")]])

        await engine._analyze_performance(_session_data(engine))

        updates = [
            _compiled_sql(st)
            for st in session.statements
            if str(st).lstrip().upper().startswith("UPDATE")
        ]
        stat_updates = [
            u for u in updates if "times_asked" in u or "times_correct" in u
        ]
        assert stat_updates, "times_asked/times_correct UPDATE'i hic kurulmadi"
        for sql in stat_updates:
            assert sql.startswith("UPDATE question_statistics"), sql


# ===========================================================================
# Task 7: _select_questions — 3-yollu JOIN (:1486-1570, 37 erisim)
# ===========================================================================
class TestSelectQuestions:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self, wired, engine):
        session = wired([[]])

        await engine._select_questions(_config(engine))

        assert session.statements
        for stmt in session.statements:
            _compiled_sql(stmt)
            _assert_single_from(stmt)

    @pytest.mark.asyncio
    async def test_all_three_split_tables_joined(self, wired, engine):
        """content 31 + metadata 3 + statistics 3 = 37 erisim (AST sayaci).

        ON yan tumcesinin OPERAND SIRASI iddia EDILMEZ: olculdu ki
        `QuestionContent.id == QuestionBankItem.id` ile
        `QuestionBankItem.id == QuestionContent.id` ayni sorguyu farkli
        render ediyor. Ikisi de dogru; sira iddia etmek fix'i gereksiz
        kisitlar (S214 "sus kod" dersinin tersi: gereksiz iddia da borctur).
        """
        session = wired([[]])

        await engine._select_questions(_config(engine))

        sql = _compiled_sql(session.statements[0])
        for table in ("question_content", "question_metadata", "question_statistics"):
            assert f"JOIN {table} ON " in sql, (table, sql)
        assert "FROM question_bank JOIN" in sql, sql
        _assert_single_from(session.statements[0])

    @pytest.mark.asyncio
    async def test_quality_gate_and_is_active_preserved(self, wired, engine):
        session = wired([[]])

        await engine._select_questions(_config(engine))

        where_sql = _compiled_where(session.statements[0])
        assert "question_bank.is_active" in where_sql, where_sql
        assert "mv_safe_for_beta" in where_sql, where_sql

    @pytest.mark.asyncio
    async def test_subject_and_exam_type_filter_on_metadata(self, wired, engine):
        session = wired([[]])

        await engine._select_questions(_config(engine, subject="FIZIK"))

        where_sql = _compiled_where(session.statements[0])
        assert "question_metadata.subject_area = 'FIZIK'" in where_sql, where_sql
        assert "question_metadata.exam_type = 'TYT'" in where_sql, where_sql

    @pytest.mark.asyncio
    async def test_difficulty_fallback_reuses_same_base_filters(self, wired, engine):
        """Zorluk havuzu bos → fallback dali (:1625) ikinci sorguyu kurar.

        `difficulty` DIFFICULTY_MAP anahtari OLMALI ("orta"); "medium" verilirse
        `difficulty_levels` None kalir ve fallback dalina HIC girilmez.
        """
        session = wired([[], []])

        await engine._select_questions(_config(engine, count=5, difficulty="orta"))

        assert len(session.statements) >= 2, "fallback sorgusu hic kurulmadi"
        for stmt in session.statements:
            _compiled_sql(stmt)
            _assert_single_from(stmt)
        assert "question_statistics.difficulty_level" in _compiled_where(
            session.statements[0]
        )
