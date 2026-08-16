# ÖSYM Sınav Motoru — #485 Split Göçü Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `backend/core/osym_exam_engine.py`'deki 42 sınıf-düzeyi + 5 entity-select split erişimini JOIN/eager-load'a çevirerek ÖSYM sınav akışını (oluştur → soru getir → cevap kaydet → sonuç analiz) çalışır hale getirmek ve her adımı mutasyonla çivilemek.

**Architecture:** `question_bank` tablosu #484'te 69 alanla üç yavru tabloya bölündü (`QuestionContent`, `QuestionMetadata`, `QuestionStatistics`; paylaşılan PK = `id`). `QuestionBankItem` üzerindeki strangler devredici, taşınmış bir alana **sınıf düzeyinde** erişilirse `AttributeError` atar — yani sorgu çalışma anında değil **kurulum anında** ölür. Üç fix kalıbı var: (a) **JOIN** — sorgu ana tablodan da kolon istiyorsa, (b) **DOĞRUDAN_SPLIT** — sorgu yalnız yavru tabloya dokunuyorsa (paylaşılan PK sayesinde JOIN gereksiz), (c) **EAGER_LOAD** — entity seçilip örnek üzerinden alan okunuyorsa (`lazy='select'` + async = `MissingGreenlet`).

**Tech Stack:** Python 3.11+, SQLAlchemy 2.0 (async), FastAPI, pytest + pytest-asyncio, PostgreSQL 18 (port 5434).

---

## 1. ANALİZ — sorun ne, neden görülmedi

### 1.1 Kök neden zinciri

| # | Katman | Ne oldu | Kanıt |
|---|---|---|---|
| 1 | Şema | #484 (S210) `question_bank`'ı böldü, `QuestionBankItem`'a devredici koydu. Devredici sınıf düzeyinde **bilerek** `AttributeError` atıyor — sessiz varsayılan yerine yol gösterici hata (doğru tasarım). | `getattr(QuestionBankItem,'subject_area')` → `AttributeError: ... sinif duzeyinde kullanilamaz` |
| 2 | Göç | Tüketiciler dosya dosya göç edecekti. İlerleme ölçütü bir **regex sayacıydı**: `re.finditer(r'QuestionBankItem\.(\w+)')`. | S215 handoff'undaki tek satırlık python komutu |
| 3 | **Ölçüm hatası** | Sayaç iki yönde kör: **yorum/docstring metnini** erişim sayıyor, **alias'lı import'ları** görmüyor. 7 dosya alias kullanıyor (`as Question` ×6, `as Soru`, `as _QB`). | `osym_exam_engine.py:1327` bir yorum satırı; AST sayacı 42 buldu, regex 1 |
| 4 | Sonuç | En büyük 3 dosya (94/105 sınıf erişimi) **hiç görünmedi**. 8 oturum (S211-S218) "kalan 9/5" sanısıyla çalıştı. | AST: 146 SINIF / 66 ENTITY / 13 dosya vs regex: 10 kalem (2'si fantom) |
| 5 | Sessizlik | Etkilenen yolların hepsinde çıplak `except` var → hata 500 olarak değil **200 + boş/yanlış veri** olarak çıkıyor. | `:1827`, `:1396`, `:702` |
| 6 | Ağ yok | `tests/integration/test_osym_exam_engine.py` **26/26 SKIP** (modül başındaki `patch.dict(sys.modules)` + iki koşulsuz `skipif(True)`). Regresyonu yakalayacak hiçbir test yok. | `pytest ... -q` → `26 skipped` |

**Özet: bu bir kod hatası değil, bir ölçüm hatasıdır.** `.claude/rules/audit-methodology.md`'nin "Ölçüm aletini doğrula — kontrol kolunun bilinen sonucu ürettiğini göster" kuralı yazılıydı ve göç sayacına hiç uygulanmamıştı.

### 1.2 Neyin kesin, neyin çıkarım olduğu

| İddia | Statü | Dayanak |
|---|---|---|
| Sorgu kurulamıyor | **ÖLÇÜLDÜ** | Devredici 11/13 alanda `AttributeError` attı |
| Kod yolu canlı, ölü değil | **ÖLÇÜLDÜ** | `routers/loader.py:51` kayıtlı, `DISABLED_ROUTERS` boş, 18 uç mount, `examService.ts` 14'ünü çağırıyor |
| S211-S218 kapanışları gerçek | **ÖLÇÜLDÜ** | 11 ilanın 10'u dosya okunarak doğrulandı; istisna `question_crud_service` archive/restore (API tüketicisi yok) |
| "Üretimde 500 dönüyor" | **ÇIKARIM** | Bu makinede `question_bank` = 0 satır → uçtan uca doğrulanamaz |

**Bu kısıt planı şekillendiriyor:** kabul kriteri **uçtan uca değil, sorgu-yapısı düzeyinde**. Testler derlenmiş SQL'i, `get_final_froms()`'u ve eager-load yapısını sınar. Veri geri yüklenmeden hiçbir görev "öğrenci akışı çalışıyor" diye kapatılamaz.

### 1.3 Kapsam kararı

Bu plan **yalnız `core/osym_exam_engine.py` + ölçüm aleti** kapsar. Kalan 12 dosya ayrı planlar:

| Dosya | SINIF+ENTITY | Not |
|---|---|---|
| `services/soru_bankasi_service.py` | 41+15 | canlı, P0 — ayrı plan |
| `application/commands/sinav.py` | 16+0 | canlı, P0 — BKT hiç çalışmıyor, ayrı plan |
| `repositories/question_repository.py` | 16+5 | **sıfır tüketici** — göç değil, silme kararı |
| `services/exam_performance_service.py` | 11+0 | P1 |
| diğer 8 dosya | 20+21 | P1/P2 |

**Kritik uyarı:** Bu plan bitince "sınav akışı kapandı" **ilan edilemez** — `application/commands/sinav.py` düzelmeden cevap-kaydetme/BKT yolu hâlâ sessizce ölü.

---

## 2. FILE STRUCTURE

| Dosya | Sorumluluk | Durum |
|---|---|---|
| `backend/scripts/scan_split_accesses.py` | AST tabanlı, alias-farkında göç sayacı. Tek sorumluluk: ölçmek. | Oluşturuldu (commit'siz) |
| `backend/tests/fast/test_osym_exam_engine_split.py` | Motorun 6 sorgusunu yapı düzeyinde çivileyen testler. Gerçek ORM modeline karşı koşar. | Oluşturulacak |
| `backend/core/osym_exam_engine.py` | 6 ayrı fonksiyonda sorgu düzeltmesi. Dosya 2057 satır; bölme YOK (cerrahi müdahale). | Değiştirilecek |
| `.claude/sessions/latest.md` | S215-S218'in kırık sayaçla üretilmiş rakamlarına düzeltme satırı. | Değiştirilecek |

**Neden dosya bölünmüyor:** `osym_exam_engine.py` 2057 satır ve bölmeyi hak ediyor olabilir, ama bu görev bir göç. CLAUDE.md "Cerrahi Müdahale": bozuk olmayanı refactor etme. Bölme ayrı bir commit'in konusu.

---

## 3. ORTAK BİLGİ (her task'ta gerekli)

**Çalışma dizini:** tüm komutlar `C:\Users\husey\kiro2\backend` içinden.

**Test koşumu:**
```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py -q --no-cov
```
`-p no:xdist` **KULLANMA** — usage error üretir, mutasyon "0 test düştü" gibi görünür (`reference_pytest-xdist-mutasyon-tuzagi`).

**Commit:** `pytest-fast` ve `kiro2-api-import-smoke` hook'ları bu depoda kırık (S215/S211'den devir, konu dışı). Commit komutu:
```bash
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "..."
```

**Mutasyon kuralı:** sonuç `failed` olmalı. `error` (collection) görürsen ölçüm **geçersizdir** — mutasyonu kabuk tırnağıyla değil Python ile uygula. Geri alım:
```bash
git checkout HEAD -- core/osym_exam_engine.py && git status --short   # çıktı BOŞ olmalı
```

**Split alan → tablo eşlemesi (bu planda kullanılanlar):**

| Alan | Tablo | İlişki adı |
|---|---|---|
| `question_text`, `option_a`–`option_e`, `correct_answer`, `question_image_url` | `QuestionContent` | `content` |
| `subject_area`, `exam_type`, `pipeline_metadata` | `QuestionMetadata` | `metadata_info` |
| `difficulty_level`, `quality_review_status`, `times_asked`, `times_correct`, `irt_difficulty` | `QuestionStatistics` | `statistics` |
| `id`, `is_active`, `is_anchor`, `primary_topic_id` | `QuestionBankItem` (bölünmedi) | — |

İlişkilerde `lazy=` **belirtilmemiş** → varsayılan `select` → async oturumda eager-load'suz erişim `MissingGreenlet` atar (`models/question_bank.py:201-218`).

---

## Task 0: Ölçüm aletini sabitle

**Files:**
- Create: `backend/scripts/scan_split_accesses.py` (zaten diskte, commit edilmemiş)

- [ ] **Step 1: Kontrol kolunu koştur**

Aletin bilinen-iyi sonucu ürettiğini kanıtla. Bu iki dosya eski regex sayacında da 2'şerdi:

```bash
python scripts/scan_split_accesses.py 2>&1 | grep -E "irt_daemon|mega_feature_tasks"
```
Beklenen:
```
core\irt_daemon.py  [SINIF=2 ENTITY=1]
tasks\mega_feature_tasks.py  [SINIF=2 ENTITY=0]
```
Bu çıktı gelmezse **DUR** — alet arızalı, bulgu değil.

- [ ] **Step 2: Bilinen-kötüyü elediğini kanıtla**

`osym_exam_engine.py:1327` bir yorum satırıdır ("`# QuestionBankItem.subject_area is String, not Enum`"). AST sayacı onu raporlamamalı:

```bash
python scripts/scan_split_accesses.py 2>&1 | grep ":1327"
```
Beklenen: **boş çıktı** (exit 1).

- [ ] **Step 3: Tam ölçümü kaydet**

```bash
python scripts/scan_split_accesses.py > ../docs/audits/2026-08-16_485_ast_olcum.txt 2>&1
tail -3 ../docs/audits/2026-08-16_485_ast_olcum.txt
```
Beklenen son satır: `TOPLAM  SINIF=146  ENTITY=66`

- [ ] **Step 4: Commit**

```bash
git add scripts/scan_split_accesses.py ../docs/audits/2026-08-16_485_ast_olcum.txt
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "fix(tools): #485 goc sayacini AST tabanli + alias-farkinda yap

Eski regex sayaci iki yonde de yaniliyordu:
- FAZLA: yorum/docstring metnini erisim sayiyordu (osym_exam_engine.py:1327 fantom)
- EKSIK: alias'li import'lari gormuyordu (as Question x6, as Soru, as _QB)

Kontrol kolu: irt_daemon=2, mega_feature_tasks=2 (eski sayacla birebir).
Olculen gercek kapsam: 146 SINIF / 66 ENTITY / 13 dosya (eski sayac: 10, 2'si fantom)."
```

---

## Task 1: Test iskeleti + RED kanıtı

**Files:**
- Create: `backend/tests/fast/test_osym_exam_engine_split.py`

**Neden önce bu:** Motorun mevcut test zemini **sıfır** (26/26 SKIP). Fix'i doğrulayabilecek tek şey bu dosya. TDD: önce RED kanıtla.

- [ ] **Step 1: Test dosyasını yaz**

```python
# backend/tests/fast/test_osym_exam_engine_split.py
"""osym_exam_engine.py'nin #485 split sonrasi sorgularini civileyen testler.

AST sayaci (scripts/scan_split_accesses.py) OLCTU: SINIF=42 ENTITY=5.
Eski regex sayaci 1 diyordu (satir 1327 = YORUM, fantom): dosya QuestionBankItem'i
`as Question` (:33) ve `as _QB` (:692) ile import ediyor, regex bunu goremiyordu.

Testler GERCEK models.question_bank modeline karsi kosar (S212-D dersi: sahte
sys.modules stub'i kullanan test KIRIK kodda da yesil kalir).
tests/fast/ altinda conftest.py YOK -> stub kirlenmesi riski yok.
"""

import copy
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql


# ---------- S212/S214 yardimcilari ----------
def _compiled_sql(stmt) -> str:
    return str(
        stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
    )


def _compiled_where(stmt) -> str:
    """S214 dersi: WHERE iddiasi SADECE whereclause'da aranir.

    select(Entity) TUM kolonlari SELECT listesine koyar; filtre silinse bile
    tam SQL'de kolon adi eslesir ve test yanlis-yesil kalir.
    """
    return str(
        stmt.whereclause.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def _assert_single_from(stmt) -> None:
    """S212-B dersi: kartezyen METINLE degil YAPIYLA olculur."""
    froms = stmt.get_final_froms()
    assert len(froms) == 1, f"kartezyen carpim: {len(froms)} ayri FROM"


def _eager_loaded(stmt) -> dict:
    """Hangi iliskiler icin eager-load secenegi eklenmis? Metin degil YAPI okur."""
    loaded = {}
    for opt in stmt._with_options:
        strategy = dict(opt.context[0].strategy) if opt.context else {}
        loaded[opt.path[1].key] = strategy.get("lazy")
    return loaded


class _CaptureSession:
    """Kurulan her stmt'i yakalar; gercek DB'ye gitmez."""

    def __init__(self, rows_per_call=None, scalar_per_call=None):
        self._rows = rows_per_call or []
        self._scalars = scalar_per_call or []
        self.statements = []
        self.committed = False

    async def execute(self, stmt, params=None):
        idx = len(self.statements)
        self.statements.append(stmt)
        rows = self._rows[idx] if idx < len(self._rows) else []
        r = MagicMock()
        r.all.return_value = rows
        r.scalars.return_value.all.return_value = rows
        r.__iter__ = lambda _s: iter(rows)  # `for q, a in result` icin
        r.scalar_one_or_none.return_value = (
            self._scalars[idx] if idx < len(self._scalars) else None
        )
        return r

    async def commit(self):
        self.committed = True

    def add(self, obj):
        pass


class _Ctx:
    def __init__(self, session):
        self._s = session

    async def __aenter__(self):
        return self._s

    async def __aexit__(self, *exc):
        return False


@pytest.fixture
def wired(monkeypatch):
    """IKI hedefi birden yamalar.

    save_answer (:632) fonksiyon GOVDESINDE `get_db_session_context` import ediyor;
    bu ad fonksiyonun tamami icin yerellesir ve yalniz modul-duzeyi yama ETKISIZ
    kalir (o durumda gercek DB'ye baglanip ForeignKeyViolationError verir).
    """
    import core.database
    import core.osym_exam_engine as eng

    def make(rows_per_call=None, scalar_per_call=None):
        session = _CaptureSession(rows_per_call, scalar_per_call)
        monkeypatch.setattr(eng, "get_db_session_context", lambda: _Ctx(session))
        monkeypatch.setattr(core.database, "get_db_session_context", lambda: _Ctx(session))
        return session

    return make


@pytest.fixture
def engine():
    """Her testte TAZE motor.

    _question_pool_cache / _performance_cache ORNEK duzeyinde (:147/:149).
    Paylasilan motorda cache HIT olursa sorgu hic kurulmaz -> test yanlis-yesil.
    """
    from core.osym_exam_engine import OSYMExamEngine

    return OSYMExamEngine()


def _config(engine, *, subject="MATEMATIK", count=3, difficulty=None, beta=False):
    """difficulty SADECE DIFFICULTY_MAP anahtari olabilir (:1405):
    kolay | orta | zor | cok_zor.
    'medium' gecersizdir -> None doner -> zorluk filtresi VE fallback dali (:1622)
    sessizce devre disi kalir ve test yanlis-kirmizi olur.
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

    d = dict(
        session_id="s-1",
        student_id="u-1",
        exam_config=engine.exam_configs[ExamType.TYT],
        status=ExamStatus.IN_PROGRESS,
        questions=["q-1"],
        answers={"q-1": "A"},
    )
    d.update(kw)
    return ExamSessionData(**d)


def _real_question(qid="q-1", *, text="Soru metni?", answer="A", subject="MATEMATIK"):
    """GERCEK ORM nesneleri (S212-D: sahte stub KIRIK kodda da yesil kalir)."""
    from models.question_bank import (
        QuestionBankItem,
        QuestionContent,
        QuestionDifficultyLevel,
        QuestionMetadata,
        QuestionStatistics,
    )

    q = QuestionBankItem(id=qid, primary_topic_id="t-1", is_active=True)
    q.content = QuestionContent(
        id=qid,
        question_text=text,
        option_a="A sikki",
        option_b="B sikki",
        option_c="C sikki",
        option_d="D sikki",
        option_e=None,
        correct_answer=answer,
    )
    q.metadata_info = QuestionMetadata(id=qid, subject_area=subject)
    q.statistics = QuestionStatistics(
        id=qid, difficulty_level=QuestionDifficultyLevel.MEDIUM
    )
    return q


# ============ Task 2: save_answer notlandirma ============
class TestSaveAnswerGrading:
    @pytest.mark.asyncio
    async def test_grading_query_selects_from_question_content(self, wired, engine):
        s = wired(scalar_per_call=["A"])
        engine.active_sessions["s-1"] = _session_data(engine, answers={})
        await engine.save_answer("s-1", "q-1", "A")
        selects = [
            st for st in s.statements if str(st).lstrip().upper().startswith("SELECT")
        ]
        assert selects, "not verme sorgusu hic kurulmadi (except yutuyor)"
        assert selects[0].selected_columns[0].table.name == "question_content"

    @pytest.mark.asyncio
    async def test_is_correct_written_true_for_matching_answer(self, wired, engine):
        s = wired(scalar_per_call=["A"])
        engine.active_sessions["s-1"] = _session_data(engine, answers={})
        await engine.save_answer("s-1", "q-1", "a")  # normalize edilmeli
        inserts = [
            st
            for st in s.statements
            if "student_answers" in str(st) and "INSERT" in str(st).upper()
        ]
        assert inserts, "INSERT hic kurulmadi"
        assert inserts[0].compile().params.get("is_correct") is True


# ============ Task 3: _select_beta_questions ============
class TestSelectBetaQuestions:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self, wired, engine):
        s = wired([[], []])
        await engine._select_beta_questions(5)
        for stmt in s.statements:
            _compiled_sql(stmt)
            _assert_single_from(stmt)

    @pytest.mark.asyncio
    async def test_pipeline_metadata_filter_moved_to_metadata_table(self, wired, engine):
        s = wired([[], []])
        await engine._select_beta_questions(5)
        where_sql = _compiled_where(s.statements[0])
        assert "question_metadata.pipeline_metadata" in where_sql, where_sql
        assert "question_bank.is_active" in where_sql, where_sql  # quality_gate.py:48


# ============ Task 4-5: ENTITY yollari (eager-load) ============
class TestEntityQueriesEagerLoad:
    @pytest.mark.asyncio
    async def test_get_current_question_eager_loads_all_three(self, wired, engine):
        """api/sinav.py:493-508 donen nesneden 12 split alan okuyor."""
        s = wired()
        engine.active_sessions["s-2"] = _session_data(
            engine, session_id="s-2", answers={}
        )
        await engine.get_current_question("s-2")
        assert _eager_loaded(s.statements[0]) == {
            "content": "selectin",
            "metadata_info": "selectin",
            "statistics": "selectin",
        }

    @pytest.mark.asyncio
    async def test_get_subject_performance_eager_loads_three(self, wired, engine):
        """:1329 subject_area(metadata) · :1346 irt_difficulty(statistics)
        · :1351 correct_answer(content).  (:1327 YORUM = eski sayacin fantomu.)
        """
        s = wired([[]])
        await engine.get_subject_performance("s-1")
        loaded = _eager_loaded(s.statements[0])
        assert loaded.get("metadata_info") == "selectin"
        assert loaded.get("statistics") == "selectin"
        assert loaded.get("content") == "selectin"
        _assert_single_from(s.statements[0])

    @pytest.mark.asyncio
    async def test_subject_read_from_real_orm_instance(self, wired, engine):
        q = _real_question("q-1", subject="GEOMETRI")
        answer = MagicMock(
            is_correct=True, response_time_seconds=12.0, selected_answer="A"
        )
        wired([[(q, answer)]])
        out = await engine.get_subject_performance("s-1")
        assert [p.subject for p in out] == ["geometri"]


# ============ Task 6: _analyze_performance ============
class TestAnalyzePerformance:
    @pytest.mark.asyncio
    async def test_correct_answer_selected_from_question_content(self, wired, engine):
        s = wired([[]])
        await engine._analyze_performance(_session_data(engine))
        assert s.statements, "hicbir sorgu kurulmadi (AttributeError yutuluyor)"
        cols = {c.table.name for c in s.statements[0].selected_columns}
        assert cols == {"question_bank", "question_content"}, cols
        _assert_single_from(s.statements[0])

    @pytest.mark.asyncio
    async def test_correct_answer_scores_one_net(self, wired, engine):
        wired([[("q-1", "A")]])
        m = await engine._analyze_performance(
            _session_data(engine, questions=["q-1"], answers={"q-1": "A"})
        )
        assert m.correct_answers == 1, "dogru cevap sayilmadi (sessiz AttributeError?)"
        assert m.net_score == 1.0

    @pytest.mark.asyncio
    async def test_wrong_answer_scores_zero_net(self, wired, engine):
        wired([[("q-1", "B")]])
        m = await engine._analyze_performance(
            _session_data(engine, questions=["q-1"], answers={"q-1": "A"})
        )
        assert (m.correct_answers, m.wrong_answers, m.net_score) == (0, 1, 0.0)

    @pytest.mark.asyncio
    async def test_times_asked_update_targets_question_statistics(self, wired, engine):
        s = wired([[("q-1", "A")]])
        await engine._analyze_performance(_session_data(engine))
        updates = [
            _compiled_sql(st)
            for st in s.statements
            if str(st).lstrip().upper().startswith("UPDATE")
        ]
        stat = [u for u in updates if "times_asked" in u or "times_correct" in u]
        assert stat, "times_asked/times_correct UPDATE'i hic kurulmadi"
        for u in stat:
            assert u.startswith("UPDATE question_statistics"), u


# ============ Task 7: _select_questions ============
class TestSelectQuestions:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self, wired, engine):
        s = wired([[]])
        await engine._select_questions(_config(engine))
        for stmt in s.statements:
            _compiled_sql(stmt)
            _assert_single_from(stmt)

    @pytest.mark.asyncio
    async def test_all_three_split_tables_joined(self, wired, engine):
        """content 31 + metadata 3 + statistics 3 = 37 erisim."""
        s = wired([[]])
        await engine._select_questions(_config(engine))
        sql = _compiled_sql(s.statements[0])
        assert "FROM question_bank JOIN" in sql, sql
        for t in ("question_metadata", "question_content", "question_statistics"):
            assert f"JOIN {t} ON {t}.id = question_bank.id" in sql, (t, sql)

    @pytest.mark.asyncio
    async def test_quality_gate_and_is_active_preserved(self, wired, engine):
        s = wired([[]])
        await engine._select_questions(_config(engine))
        where_sql = _compiled_where(s.statements[0])
        assert "question_bank.is_active" in where_sql, where_sql
        assert "mv_safe_for_beta" in where_sql, where_sql

    @pytest.mark.asyncio
    async def test_subject_and_exam_type_filter_on_metadata(self, wired, engine):
        s = wired([[]])
        await engine._select_questions(_config(engine, subject="FIZIK"))
        where_sql = _compiled_where(s.statements[0])
        assert "question_metadata.subject_area = 'FIZIK'" in where_sql, where_sql
        assert "question_metadata.exam_type = 'TYT'" in where_sql, where_sql

    @pytest.mark.asyncio
    async def test_difficulty_fallback_reuses_same_base_filters(self, wired, engine):
        """difficulty DIFFICULTY_MAP anahtari OLMALI ('orta'); 'medium' -> None
        -> fallback dali (:1622 `and difficulty_levels`) hic girilmez.
        """
        s = wired([[], [], []])
        await engine._select_questions(_config(engine, count=5, difficulty="orta"))
        assert len(s.statements) >= 2, "fallback sorgusu hic kurulmadi"
        for stmt in s.statements:
            _compiled_sql(stmt)
            _assert_single_from(stmt)


# select_from NOTU (S214 dersi): 5 sorgunun 5'inde de SELECT listesi bir
# question_bank kolonu iceriyor -> `.select_from(QuestionBankItem)` SUS olur,
# hicbir mutasyonla civilenemez. Riski `assert "FROM question_bank JOIN" in sql`
# karsiliyor.
```

- [ ] **Step 2: RED kanıtla**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py -q --no-cov 2>&1 | tail -20
```
Beklenen: **çoğu test FAIL**. Ölçülen RED tabanları:
- `_select_*` testleri → `AttributeError: ... sinif duzeyinde kullanilamaz`
- `_analyze_performance` → `assert s.statements` düşer (`stmts=0`, `except` yutuyor)
- `save_answer` → `assert selects` düşer
- eager-load testleri → `_eager_loaded(...) == {}` (henüz `.options()` yok)

Herhangi bir test **fix'ten ÖNCE geçiyorsa** o test değersizdir (vakum test) — ya sil ya assert'i sıkılaştır.

- [ ] **Step 3: RED çıktısını kaydet ve commit**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py -q --no-cov > /tmp/red_baseline.txt 2>&1 || true
git add tests/fast/test_osym_exam_engine_split.py
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "test(osym): #485 split gocu icin RED testler (fix ONCESI)

osym_exam_engine.py'nin test zemini sifirdi (test_osym_exam_engine.py 26/26 SKIP).
Bu dosya 6 sorguyu YAPI duzeyinde civiliyor: derlenmis SQL, get_final_froms(),
eager-load secenekleri. Gercek ORM modeline karsi kosar (sahte stub KIRIK kodda
da yesil kalirdi - S212-D dersi).

Su an FAIL ediyor; her fix task'i bir kismini yesile cevirecek."
```

---

## Task 2: `save_answer` — notlandırma sorgusu (`:697`)

**Files:**
- Modify: `backend/core/osym_exam_engine.py:690-703`
- Test: `backend/tests/fast/test_osym_exam_engine_split.py::TestSaveAnswerGrading`

**Neden ilk:** En küçük kusur, tek sorgu, JOIN gerekmiyor. Ama etkisi büyük: `student_answers.is_correct` kalıcı `NULL` kalıyor ve mastery pipeline bu alana göre filtreliyor. Commit `56a84bbea` bu hatayı bir kez düzeltmişti; split sessizce geri aldı.

- [ ] **Step 1: Testin şu an düştüğünü doğrula**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py::TestSaveAnswerGrading -q --no-cov
```
Beklenen: 2 failed.

- [ ] **Step 2: Fix'i uygula**

`core/osym_exam_engine.py` içinde, `690-703` arasındaki bloğu bul:

```python
                try:
                    from sqlalchemy import select as _select

                    from models.question_bank import QuestionBankItem as _QB

                    async with get_db_session_context() as _grade_db:
                        _ca = (
                            await _grade_db.execute(
                                _select(_QB.correct_answer).where(_QB.id == question_id)
                            )
                        ).scalar_one_or_none()
```

Şununla değiştir:

```python
                try:
                    from sqlalchemy import select as _select

                    # #485: correct_answer artik QuestionContent'te.
                    # Paylasilan PK (id) sayesinde JOIN gerekmez — dogrudan
                    # yavru tabloya filtrelemek yeterli.
                    from models.question_bank import QuestionContent as _QC

                    async with get_db_session_context() as _grade_db:
                        _ca = (
                            await _grade_db.execute(
                                _select(_QC.correct_answer).where(_QC.id == question_id)
                            )
                        ).scalar_one_or_none()
```

- [ ] **Step 3: Import sayımını doğrula**

Biçimlendirici, kullanılmaz kalan import'u siler (`reference_formatter-import-stripping`). `_QB` başka yerde kullanılıyor mu?

```bash
grep -n "_QB" core/osym_exam_engine.py
```
Beklenen: **boş çıktı**. Çıktı varsa o kullanımları da göç ettir.

- [ ] **Step 4: Testin geçtiğini doğrula**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py::TestSaveAnswerGrading -q --no-cov
```
Beklenen: `2 passed`.

- [ ] **Step 5: Mutasyon M1 — hedef tabloyu boz**

`_QC.correct_answer` → `_QB.correct_answer` yap (ve import'u geri koy). Koştur:
```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py::TestSaveAnswerGrading -q --no-cov
```
Beklenen: `test_grading_query_selects_from_question_content` **FAILED** (`error` DEĞİL).
Geri al:
```bash
git checkout HEAD -- core/osym_exam_engine.py && git status --short
```
Not: bu adım fix'i de geri alır — Step 2'yi tekrar uygula. (Alternatif: mutasyondan önce Step 2'yi commit'le, sonra `git checkout HEAD --` fix'i korur.)

- [ ] **Step 6: Mutasyon M2 — notlandırmayı devre dışı bırak**

`if _ca:` → `if False:` yap, koştur.
Beklenen: `test_is_correct_written_true_for_matching_answer` **FAILED**.
Geri al ve doğrula (yukarıdaki komut).

- [ ] **Step 7: Lint + commit**

```bash
pre-commit run --files core/osym_exam_engine.py tests/fast/test_osym_exam_engine_split.py
```
Pre-existing borç çıkarsa: `git stash push -- core/osym_exam_engine.py` ile HEAD'e karşı aynı hook'u koştur; borç HEAD'de de varsa **davranışı değiştirme**, per-file-ignore/`# nosec` ile işaretle ve commit mesajında belirt. `git stash pop` sonrası `git status` ile geri alımı doğrula.

```bash
git add core/osym_exam_engine.py
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "fix(osym): save_answer notlandirma sorgusu QuestionContent'e cevrildi (#485)

correct_answer split ile QuestionContent'e tasindi; _QB.correct_answer sinif
duzeyinde AttributeError atiyordu ve :702 logger.debug bunu yutuyordu ->
student_answers.is_correct kalici NULL (mastery pipeline bu alana gore filtreliyor).
Commit 56a84bbea'nin fix'i sessizce geri gitmisti.

JOIN gerekmedi: paylasilan PK, dosyada baska split kolon kullanilmiyor.
Mutasyon 2/2 oldurudu (hedef tablo, notlandirma dali)."
```

---

## Task 3: `_select_beta_questions` — `pipeline_metadata` filtresi (`:1436`)

**Files:**
- Modify: `backend/core/osym_exam_engine.py:1433-1439`
- Test: `...::TestSelectBetaQuestions`

- [ ] **Step 1: RED doğrula**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py::TestSelectBetaQuestions -q --no-cov
```
Beklenen: 2 failed (`AttributeError: QuestionBankItem.pipeline_metadata ...`).

- [ ] **Step 2: Import ekle**

`core/osym_exam_engine.py:33` civarındaki import bloğuna ekle:

```python
from models.question_bank import QuestionBankItem as Question
from models.question_bank import QuestionContent, QuestionMetadata, QuestionStatistics
```

- [ ] **Step 3: Fix'i uygula**

`1433-1439` bloğunu bul:

```python
                id_result = await db_session.execute(
                    select(Question.id).where(
                        Question.is_active.is_(True),
                        Question.pipeline_metadata.op("->>")("verified_provisional")
                        == "true",
                    )
                )
```

Şununla değiştir:

```python
                id_result = await db_session.execute(
                    # #485: pipeline_metadata artik QuestionMetadata'da.
                    # SELECT listesinde Question.id var -> select_from() gerekmez
                    # (S214: SELECT listesi split-only degilse select_from SUS'tur).
                    select(Question.id)
                    .join(QuestionMetadata, QuestionMetadata.id == Question.id)
                    .where(
                        Question.is_active.is_(True),
                        QuestionMetadata.pipeline_metadata.op("->>")(
                            "verified_provisional"
                        )
                        == "true",
                    )
                )
```

`is_active` filtresini **KALDIRMA** — kalite kapısıyla birlikte çalışıyor (`core/quality_gate.py:48`).

- [ ] **Step 4: GREEN doğrula**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py::TestSelectBetaQuestions -q --no-cov
```
Beklenen: `2 passed`.

- [ ] **Step 5: Mutasyon M3 — `is_active` filtresini sil**

`Question.is_active.is_(True),` satırını sil, koştur.
Beklenen: `test_pipeline_metadata_filter_moved_to_metadata_table` **FAILED**.
(Bu test yalnız `stmt.whereclause`'a bakıyor — S214 dersi. Tam SQL'e baksaydı `question_bank.is_active` SELECT listesinden eşleşir ve mutasyon **hayatta kalırdı**.)
Geri al + `git status --short` ile doğrula.

- [ ] **Step 6: Mutasyon M4 — JOIN'i sil**

`.join(QuestionMetadata, ...)` satırını sil, koştur.
Beklenen: `test_query_builds_and_compiles` **FAILED** (sorgu kurulamaz).
Geri al + doğrula.

- [ ] **Step 7: Commit**

```bash
pre-commit run --files core/osym_exam_engine.py
git add core/osym_exam_engine.py
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "fix(osym): _select_beta_questions pipeline_metadata JOIN'e cevrildi (#485)

Mutasyon 2/2 oldurudu (is_active filtresi, JOIN)."
```

---

## Task 4: `get_current_question` — eager-load (`:567`)

**Files:**
- Modify: `backend/core/osym_exam_engine.py:565-573`
- Test: `...::TestEntityQueriesEagerLoad::test_get_current_question_eager_loads_all_three`

**Neden gerekli:** Sorgu kurulur (yalnız `id`/`is_active` kullanıyor) ama dönen nesneden `api/sinav.py:493-508` **12 split alan** okuyor. İlişkiler `lazy='select'` → async'te `MissingGreenlet`. `navigate_to_question:817` aynı fonksiyona delege ediyor.

- [ ] **Step 1: RED doğrula**

```bash
python -m pytest "tests/fast/test_osym_exam_engine_split.py::TestEntityQueriesEagerLoad::test_get_current_question_eager_loads_all_three" -q --no-cov
```
Beklenen: FAILED (`{} != {...}` — hiç `.options()` yok).

- [ ] **Step 2: Import ekle**

Dosya başındaki SQLAlchemy import'una ekle:
```python
from sqlalchemy.orm import selectinload
```

- [ ] **Step 3: Fix'i uygula**

`565-571` bloğunu bul:

```python
                result = await db_session.execute(
                    select(Question).where(
                        Question.id == question_id, Question.is_active.is_(True)
                    )
                )
```

Şununla değiştir:

```python
                result = await db_session.execute(
                    # #485: donen nesneden api/sinav.py:493-508 12 split alan okuyor
                    # (content 10 + metadata 1 + statistics 1). Iliskiler lazy='select'
                    # (models/question_bank.py:201-218) -> eager-load olmadan
                    # async oturumda MissingGreenlet.
                    select(Question)
                    .options(
                        selectinload(Question.content),
                        selectinload(Question.metadata_info),
                        selectinload(Question.statistics),
                    )
                    .where(Question.id == question_id, Question.is_active.is_(True))
                )
```

- [ ] **Step 4: GREEN doğrula**

```bash
python -m pytest "tests/fast/test_osym_exam_engine_split.py::TestEntityQueriesEagerLoad::test_get_current_question_eager_loads_all_three" -q --no-cov
```
Beklenen: `1 passed`.

- [ ] **Step 5: Mutasyon M5 — bir eager-load'ı sil**

`selectinload(Question.content),` satırını sil, koştur.
Beklenen: **FAILED** (test sözlüğü yapıdan okuyor, metinden değil).
Geri al + `git status --short`.

- [ ] **Step 6: Commit**

```bash
pre-commit run --files core/osym_exam_engine.py
git add core/osym_exam_engine.py
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "fix(osym): get_current_question uc split iliskiyi eager-load ediyor (#485)

Mutasyon 1/1 oldurudu."
```

---

## Task 5: `get_subject_performance` — eager-load (`:1313`)

**Files:**
- Modify: `backend/core/osym_exam_engine.py:1312-1324`
- Test: `...::TestEntityQueriesEagerLoad` (kalan 2 test)

**Neden gerekli:** Döngüde üç ayrı yavru tablodan okuma var — `:1329` `subject_area` (metadata), `:1346` `irt_difficulty` (statistics), `:1351` `correct_answer` (content). `:1396` çıplak `except` → `return []` → HTTP 200 ile **boş ders kırılımı**.

- [ ] **Step 1: RED doğrula**

```bash
python -m pytest "tests/fast/test_osym_exam_engine_split.py::TestEntityQueriesEagerLoad" -q --no-cov
```
Beklenen: 2 failed (`test_get_current_question...` Task 4'ten geçiyor olmalı).

- [ ] **Step 2: Fix'i uygula**

`1312-1324` bloğunu bul:

```python
                result = await db_session.execute(
                    select(Question, StudentAnswer)
                    .join(ExamQuestion, Question.id == ExamQuestion.question_id)
```

`select(...)` ile `.join(...)` arasına `.options(...)` ekle:

```python
                result = await db_session.execute(
                    select(Question, StudentAnswer)
                    # #485: dongude :1329 subject_area(metadata) · :1346
                    # irt_difficulty(statistics) · :1351 correct_answer(content)
                    # okunuyor; lazy='select' -> eager-load sart.
                    .options(
                        selectinload(Question.content),
                        selectinload(Question.metadata_info),
                        selectinload(Question.statistics),
                    )
                    .join(ExamQuestion, Question.id == ExamQuestion.question_id)
```

Gerisi (outerjoin/where/order_by) **aynen kalır**.

- [ ] **Step 3: GREEN doğrula**

```bash
python -m pytest "tests/fast/test_osym_exam_engine_split.py::TestEntityQueriesEagerLoad" -q --no-cov
```
Beklenen: `3 passed`.

- [ ] **Step 4: Mutasyon M6 — metadata eager-load'ını sil**

`selectinload(Question.metadata_info),` (bu bloktaki) satırını sil, koştur.
Beklenen: `test_get_subject_performance_eager_loads_three` **FAILED**.
Geri al + doğrula.

- [ ] **Step 5: Commit**

```bash
pre-commit run --files core/osym_exam_engine.py
git add core/osym_exam_engine.py
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "fix(osym): get_subject_performance uc split iliskiyi eager-load ediyor (#485)

:1396 ciplak except MissingGreenlet'i yutup return [] yapiyordu ->
HTTP 200 ile bos ders kirilimi. Mutasyon 1/1 oldurudu."
```

---

## Task 6: `_analyze_performance` — sorgu + iki UPDATE (`:1716`, `:1779`, `:1785`)

**Files:**
- Modify: `backend/core/osym_exam_engine.py:1715-1721` ve `1777-1789`
- Test: `...::TestAnalyzePerformance`

**Neden tek commit:** Seri bağlı. `:1716` düzelirse sıradaki hata `:1779` olur ve kullanıcı-görünür kazanç **0** kalır. `:1827` çıplak `except` ikisini de yutuyor → sınav sonucu HTTP 200 ile `correct=0 / net=0.0`.

- [ ] **Step 1: RED doğrula**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py::TestAnalyzePerformance -q --no-cov
```
Beklenen: 4 failed.

- [ ] **Step 2: SELECT'i JOIN'e çevir**

`1715-1721` bloğunu bul:

```python
                    result = await db_session.execute(
                        select(Question.id, Question.correct_answer).where(
                            Question.id.in_(question_ids),
                            Question.is_active.is_(True),
                        )
                    )
```

Şununla değiştir:

```python
                    result = await db_session.execute(
                        # #485: correct_answer QuestionContent'te; id ana tabloda
                        # kaldigi icin JOIN sart (iki tablodan da kolon seciliyor).
                        select(Question.id, QuestionContent.correct_answer)
                        .join(QuestionContent, QuestionContent.id == Question.id)
                        .where(
                            Question.id.in_(question_ids),
                            Question.is_active.is_(True),
                        )
                    )
```

- [ ] **Step 3: İki UPDATE'i `QuestionStatistics`'e çevir**

`1777-1789` bloğunu bul:

```python
                    if all_answered_ids:
                        await db_session.execute(
                            update(Question)
                            .where(Question.id.in_(all_answered_ids))
                            .values(times_asked=Question.times_asked + 1)
                        )
                    if correct_ids:
                        await db_session.execute(
                            update(Question)
                            .where(Question.id.in_(correct_ids))
                            .values(times_correct=Question.times_correct + 1)
                        )
```

Şununla değiştir:

```python
                    # #485: times_asked/times_correct QuestionStatistics'e tasindi.
                    # Ana tablo UPDATE'i yavru tabloyu YAZAMAZ — hedef degismeli.
                    if all_answered_ids:
                        await db_session.execute(
                            update(QuestionStatistics)
                            .where(QuestionStatistics.id.in_(all_answered_ids))
                            .values(times_asked=QuestionStatistics.times_asked + 1)
                        )
                    if correct_ids:
                        await db_session.execute(
                            update(QuestionStatistics)
                            .where(QuestionStatistics.id.in_(correct_ids))
                            .values(times_correct=QuestionStatistics.times_correct + 1)
                        )
```

- [ ] **Step 4: GREEN doğrula**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py::TestAnalyzePerformance -q --no-cov
```
Beklenen: `4 passed`.

- [ ] **Step 5: Mutasyon M7 — cevabı sabitle**

`QuestionContent.correct_answer` → `sa_literal("A").label("correct_answer")` yerine daha basit: SELECT'te `QuestionContent.correct_answer` → `Question.id.label("correct_answer")` yap, koştur.
Beklenen: `test_correct_answer_selected_from_question_content` **FAILED**.
Geri al + doğrula.

- [ ] **Step 6: Mutasyon M8 — UPDATE hedefini boz**

İlk `update(QuestionStatistics)` → `update(Question)` yap (ve `.where`/`.values`'ı da `Question`'a çevir ki kurulabilsin — `times_asked` sınıf düzeyinde patlayacağı için bu mutasyon `AttributeError` verir; o durumda mutasyonu şöyle yap: `update(QuestionStatistics)` → `update(QuestionContent)` ve `.values(times_asked=...)` → `.values(question_text="x")`).
Beklenen: `test_times_asked_update_targets_question_statistics` **FAILED** (`error` değil).
Geri al + doğrula.

- [ ] **Step 7: Commit**

```bash
pre-commit run --files core/osym_exam_engine.py
git add core/osym_exam_engine.py
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "fix(osym): _analyze_performance SELECT JOIN'e + iki UPDATE QuestionStatistics'e (#485)

Seri bagli iki kusur tek commit'te: :1716 sorgu kurulamiyordu, :1779/:1785
UPDATE ana tabloyu hedefliyordu (yavruyu yazamaz). :1827 ciplak except ikisini
de yutuyordu -> sinav sonucu HTTP 200 ile correct=0/net=0.0.

Mutasyon 2/2 oldurudu."
```

---

## Task 7: `_select_questions` — 3-yollu JOIN (`:1486-1570`, 37 erişim)

**Files:**
- Modify: `backend/core/osym_exam_engine.py:1486-1650`
- Test: `...::TestSelectQuestions`

**Neden en son:** En büyük ve en riskli. 37 erişim tek bir `base_filters` listesinde; iki dal (normal `:1588` + zorluk-fallback `:1639`) **aynı listeyi** kullanıyor → tek fix iki dalı da kapatır. Yanlış JOIN sessizce havuzu daraltır.

### ⚠️ TASK 7 TEHLİKELERİ (Task 2 incelemesinde ÖLÇÜLDÜ — okumadan başlama)

**Bu fonksiyon şu an ÖLÜ KOD.** `:1485`'te `Question.exam_type` sınıf düzeyinde patlıyor,
yani `:1586`'daki örnekleme bloğuna hiç ulaşılmıyor. Kanıt (canlı traceback):
`AttributeError: QuestionBankItem.exam_type sinif duzeyinde kullanilamaz`.
**Senin JOIN işin, aşağıdaki iki davranışı ilk kez çalıştırılabilir hâle getirecek.**
İkisi de S210 devrinden gelme, commit `d7eaeb3b1`'e aynı dosyada olduğu için süpürüldü,
Task 2'nin kusuru DEĞİL — ama senin commit'inde canlanacak ve sana yazılacak.

| # | Ne | Nerede | Risk |
|---|---|---|---|
| H1 | **Boş havuz artık koşulsuz cache'leniyor.** HEAD~1'de `if pool:` guard vardı; süpürülen blok `[]`'i de yazıyor. | `:1592-1593`, `:1645-1646` | `question_bank` boşken (taze checkout — bu makinede 0 satır — veya import ortası) `anchor_pool`/`normal_pool` `[]` cache'lenir; sonraki her çağrıda `is None` False olur, DB bir daha sorgulanmaz. `TTLCache(ttl=3600)` → **60 dakikaya kadar sessizce boş sınav**. Eski kod bir sonraki istekte kendini onarıyordu. |
| H2 | **Her sınava %15 IRT-ankraj kotası zorlanıyor.** `anchor_target = max(1, round(count*0.15)) if count >= 5 else 0`, hem ana hem fallback yolda. | `:1595`, `:1649` | Ankraj maddeleri IRT eşitleme (equating) için var. Üretilen her sınavın ~%15'ine servis etmek ankraj setini yakar ve gelecekteki equating koşumlarını kirletebilir. **Psikometrik ürün kararı** — kod kararı değil. |

**KARARLAR (16 Ağu 2026, kullanıcı onayı alındı — tekrar tartışma):**

- **H1 → DÜZELT.** Boş-havuz cache'leme guard'ı geri gelecek. Task 7 commit'inde
  `if anchor_pool:` / `if normal_pool:` (veya eşdeğeri) ile koşullu yazım. Bu bir kod
  kararı, kullanıcı onayı gerekmiyor. Mutasyonla çivile: guard'ı kaldır → boş-havuz
  testi düşmeli. (Test yok — Task 7'de YAZ.)
- **H2 → ŞİMDİLİK KAPAT.** `anchor_target = 0` yap (kotayı devre dışı bırak), motor eski
  davranışına dönsün. **Kodu silme** — kotayı hesaplayan satırı koru ama etkisiz kıl ve
  neden kapatıldığını yorumla yaz, ki ankraj/equating stratejisi ele alınırken bulunabilsin.
  Gerekçe: bu psikometrik bir ürün kararı ve S210 devrinden gelme; görünmez bir yan etki
  olarak shiplenmemeli. Ayrı oturumda ele alınacak (ankraj seti büyüklüğü, kullanım
  geçmişi, equating durumu ölçülmeden karar verilemez).

**Diğer ölçülmüş notlar:**
- `is_anchor` **taşınmadı** — parent'ta (`models/question_bank.py:175`, canlı şemada
  `0001_baseline_schema.sql:3467`). Göç etme; `select(Question.id, Question.is_anchor)`
  devrediciye hiç dokunmuyor.
- `select_from` **gerekmiyor** (S214 kuralı): SELECT listesinde parent kolonu var
  (`Question.id`, `is_anchor`) → SQLAlchemy sol tarafı çıkarır. Eklenirse SQL **bayt-birebir
  aynı** kalır ve hiçbir mutasyonla çivilenemez. Riski `assert "FROM question_bank JOIN" in sql` karşılar.
- Göç edilecek id-havuzu sorguları **iki değil üç**: `:1586` (ana), `:1637` (fallback) ve
  kardeş `_select_beta_questions`'daki `:1431` (Task 3 kapsamı, `pipeline_metadata` `:1432`).
- `:1595-1610` ile `:1649-1665` arası ~40 satır **kopyala-yapıştır** ve iki kopya satır
  sarmasında zaten farklılaşmış. İkisini birden düzenle, yoksa sessizce ayrışırlar.
- `:1448`'deki `# nosec B311` gerekçe yorumu **bayat**: "3 cagri yeri" diyor, süpürülen blok
  sonrası 5 oldu (`:1451, :1601, :1607, :1654, :1662`).

- [ ] **Step 1: RED doğrula**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py::TestSelectQuestions -q --no-cov
```
Beklenen: 5 failed.

- [ ] **Step 2: `base_filters` içindeki alan referanslarını göç ettir**

`1486-1550` arasındaki `base_filters` listesinde şu değişiklikleri yap (yalnız tablo öneki değişir, mantık **aynen kalır**):

| Eski | Yeni |
|---|---|
| `Question.exam_type` | `QuestionMetadata.exam_type` |
| `Question.subject_area` | `QuestionMetadata.subject_area` |
| `Question.question_text` | `QuestionContent.question_text` |
| `Question.option_a` … `option_d` | `QuestionContent.option_a` … `option_d` |
| `Question.question_image_url` | `QuestionContent.question_image_url` |
| `Question.quality_review_status` | `QuestionStatistics.quality_review_status` |
| `Question.difficulty_level` (`:1555`) | `QuestionStatistics.difficulty_level` |

**Değişmeyecekler:** `Question.is_active`, `safe_for_beta_gate(Question.id)`, `Question.id`, `Question.is_anchor`.

- [ ] **Step 3: Her iki sorgu dalına üçlü JOIN ekle**

`:1588` ve `:1639` civarındaki iki `select(...)` çağrısının her birine ekle (`.where(and_(*filters))`'dan **önce**):

```python
                    .join(QuestionContent, QuestionContent.id == Question.id)
                    .join(QuestionMetadata, QuestionMetadata.id == Question.id)
                    .join(QuestionStatistics, QuestionStatistics.id == Question.id)
```

`.select_from(...)` **EKLEME** — SELECT listesinde `Question.id`/`Question.is_anchor` var, dolayısıyla süs olur ve hiçbir mutasyonla çivilenemez (S214 dersi). Riski `test_all_three_split_tables_joined` karşılıyor.

- [ ] **Step 4: GREEN doğrula**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py::TestSelectQuestions -q --no-cov
```
Beklenen: `5 passed`.

- [ ] **Step 5: Tüm dosyayı koştur (regresyon)**

```bash
python -m pytest tests/fast/test_osym_exam_engine_split.py -q --no-cov
```
Beklenen: **hepsi passed** (Task 2-6 dahil).

- [ ] **Step 6: Mutasyon M9 — metadata filtresini sil**

`QuestionMetadata.exam_type == ...` satırını `base_filters`'tan sil, koştur.
Beklenen: `test_subject_and_exam_type_filter_on_metadata` **FAILED**.
Geri al + doğrula.

- [ ] **Step 7: Mutasyon M10 — kalite kapısını sil**

`safe_for_beta_gate(Question.id),` satırını sil, koştur.
Beklenen: `test_quality_gate_and_is_active_preserved` **FAILED**.
Geri al + doğrula.

- [ ] **Step 8: Mutasyon M11 — bir JOIN'i sil**

`.join(QuestionContent, ...)` satırını sil, koştur.
Beklenen: `test_all_three_split_tables_joined` **FAILED** (ve muhtemelen kartezyen → `_assert_single_from` da düşer).
Geri al + doğrula.

- [ ] **Step 9: Sayacı yeniden koştur**

```bash
python scripts/scan_split_accesses.py 2>&1 | grep osym_exam_engine
```
Beklenen: `core\osym_exam_engine.py  [SINIF=0 ENTITY=5]`
(ENTITY=5 **kalır** — `:1456`/`:1615`/`:1665` yalnız `.id` okuyor, eager-load N/A; `:567`/`:1313` artık `.options()`'lı ama sayaç bunu ayırt etmiyor.)

- [ ] **Step 10: Commit**

```bash
pre-commit run --files core/osym_exam_engine.py
git add core/osym_exam_engine.py
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "fix(osym): _select_questions 3-yollu JOIN'e cevrildi (#485, 37 erisim)

base_filters listesindeki 37 sinif-duzeyi erisim uc yavru tabloya dagitildi
(content 31 + metadata 3 + statistics 3). Iki dal (normal + zorluk-fallback)
ayni listeyi kullandigi icin tek fix ikisini de kapatti.

select_from EKLENMEDI: SELECT listesinde Question.id/is_anchor var -> sus olur
(S214 dersi). Riski 'FROM question_bank JOIN' assert'i karsiliyor.

Mutasyon 3/3 oldurudu. osym_exam_engine.py SINIF: 42 -> 0."
```

---

## Task 8: Handoff düzeltmesi + kapanış

**Files:**
- Modify: `.claude/sessions/latest.md`

**Neden:** S215-S218 handoff'larındaki "kalan 12/8", "11/7", "10/6", "9/5" rakamları **kırık sayaçla** üretildi. `.claude/lessons/` politikası: sessiz silme yok, düzeltme görünür olmalı.

- [ ] **Step 1: Düzeltme bloğunu ekle**

`.claude/sessions/latest.md`'nin en üstüne (ilk `---`'den sonra) ekle:

```markdown
## ⚠️ DÜZELTME (16 Ağu 2026) — S215-S218 "kalan N/M" rakamları GEÇERSİZ

S211-S218'in ilerleme ölçütü olan regex sayacı (`re.finditer(r'QuestionBankItem\.(\w+)')`)
iki yönde de kördü:
- **FAZLA saydı:** yorum/docstring metnini erişim sanıyordu (`osym_exam_engine.py:1327`
  bir yorum satırı — "kalan 1 erişim" fantomdu).
- **EKSİK saydı:** alias'lı import'ları görmüyordu. 7 dosya alias kullanıyor
  (`as Question` ×6, `as Soru`, `as _QB`). Aynı körlük S214'ün yedek kontrolü
  `grep 'select(QuestionBankItem)'` için de geçerliydi.

AST tabanlı sayaç (`backend/scripts/scan_split_accesses.py`, kontrol kolu:
`irt_daemon`=2 · `mega_feature_tasks`=2 birebir örtüştü) gerçek kapsamı ölçtü:
**146 SINIF / 66 ENTITY / 13 dosya** — eski sayaç 10 kalem diyordu, 2'si fantom.

**Kapanış ilanları geçerli:** S211-S218'in 11 ilanının 10'u dosya okunarak
doğrulandı, gerçekten kapalı. Tek istisna `question_crud_service.py`
`archive_question`/`restore_question` (eager-load atlanmış; API tüketicisi yok).
Yani sorun "yanlış kapatma" değil, **hiç açılmama**.

**Açık kalan (öncelik sırasıyla):** `soru_bankasi_service.py` (41+15, canlı) ·
`application/commands/sinav.py` (16, canlı — BKT hiç çalışmıyor) ·
`repositories/question_repository.py` (16+5, **sıfır tüketici** → silme kararı) ·
`exam_performance_service.py` (11) · diğer 8 dosya (20+21).
```

- [ ] **Step 2: Commit**

```bash
git add ../.claude/sessions/latest.md
SKIP=pytest-fast,kiro2-api-import-smoke git commit -m "chore: S215-S218 'kalan N/M' rakamlarina duzeltme satiri (#485)

Sessiz silme yok: rakamlar kirik sayacla uretildi, gercek kapsam 146/66/13."
```

- [ ] **Step 3: Ders kaydına satır ekle**

`.claude/lessons/ders_kaydi.yaml`'a yeni ders ekle (`durum: aktif`, kanıt = bu planın Task 0 kontrol kolu çıktısı, `zorlayici: null` — henüz bu dersi koruyan test yok):

> Bir göç/ilerleme sayacı **regex ile** yazılmışsa iki yönde de yanılır: yorum sayar, alias göremez. Sayaç AST tabanlı olmalı ve **kontrol kolu** (bilinen-iyi dosyanın bilinen sayısı) her koşumda doğrulanmalı. "Kalan N" bir ölçümdür; aleti doğrulanmamış sayaçtan gelen N **tahmindir**.

---

## 4. SELF-REVIEW

**Spec coverage:** Analizde sayılan 5 motor kusuru → Task 2-7 (`:697`→T2, `:1436`→T3, `:567`→T4, `:1313`→T5, `:1716`+`:1779/1785`→T6, `:1486-1570`→T7). Ölçüm aleti → T0. Test zemini → T1. Handoff borcu → T8. **Boşluk yok.**

**Placeholder taraması:** "TBD"/"uygun hata yönetimi ekle"/"benzer şekilde" yok; her kod adımı gerçek kod bloğu içeriyor. Task 6 Step 6'daki mutasyon iki alternatifle verildi çünkü naif mutasyon `AttributeError` (yani `error`, `failed` değil) üretir — bu kasıtlı.

**Tip tutarlılığı:** İlişki adları her task'ta aynı: `content` / `metadata_info` / `statistics`. Sınıf adları: `QuestionContent` / `QuestionMetadata` / `QuestionStatistics`. Alias `Question` = `QuestionBankItem` (dosyanın mevcut kuralı, korundu). Test yardımcıları (`_compiled_where`, `_assert_single_from`, `_eager_loaded`) T1'de tanımlı, T2-T7'de kullanılıyor.

**Bilinen sınır:** Kabul kriteri sorgu-yapısı düzeyinde. `question_bank` = 0 satır olduğu için hiçbir task "öğrenci akışı çalışıyor" kanıtı üretmez. Bu plan bitince **"sınav akışı kapandı" ilan edilemez** — `application/commands/sinav.py` ayrı plan.
