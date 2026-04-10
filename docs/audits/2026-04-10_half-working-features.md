# Half-Working Features Audit — Session 136

**Tarih:** 10 Nisan 2026
**Metot:** Grep-based pattern scan + canlı DB sorgu + Golden Flow probe doğrulaması
**Kapsam:** `backend/` (api, services, core, models, tests)
**Felsefe:** "200 kanıt değil. Write test: state okuma → aksiyon → state tekrar okuma → değişti mi?"

Bu rapor **teşhis haritası** — kod değiştirilmedi. Amaç: yarım çalışan özelliklerin
bulunduğu bölgeleri Option B (domain GF write tests) ve Option C (fix) adımlarına
input sağlamak.

---

## Özet Skorkart

| Kategori | Tespit | Seviye |
|----------|--------|--------|
| Fire-and-forget try/except (API layer) | **21 hot spot** | 🟡 3 HIGH, 18 MEDIUM (fallback) |
| Pydantic validation boundary gaps | **11 endpoint** | 🔴 CRITICAL PATTERN |
| Legacy Question() kwargs trap | **1 prod + 3 deprecated** | 🔴 CRITICAL (K4 kanıtlı) |
| Lenient `< 500` assertion (tests) | **3 test, GF suite** | 🟡 MEDIUM |
| NULL `primary_topic_id` in qb | **0 / 77,401** | ✅ OK |
| Subject case alignment | **INGILIZCE qb'de var, topic_hierarchy'de yok** | 🟡 MINOR |
| Topic_hierarchy boş subject_area (`None`) | **125 rows, 1 NULL group** | 🟡 MEDIUM |

**Live-probe doğrulanmış yarım feature'lar (Session 136):**
- K1 — GF3 yalancı yeşil ✅ DÜZELTİLDİ (bu session)
- K2 — save-answer BKT pipeline `algorithm: null` döndürür (aralıklı, root cause NULL topic DEĞİL)
- K3 — save-answer boş `question_id` kabul eder (GF3w FAIL olarak kanıtlı)
- K4 — admin POST question create 500 (GF6w FAIL olarak kanıtlı)

---

## Scan 1 — Fire-and-Forget try/except Pattern

**Aranan:** `except Exception as X: logger.warning/info/debug(...)` — hata yutan bloklar.
**Toplam bulgu:** 100+ match (`backend/` geneli). **API layer:** ~21 hot spot.

### 🔴 HIGH IMPACT — State Değişikliği Sessiz Çöker

| Dosya:Satır | Ne Yapıyor | Semptom |
|-------------|-----------|---------|
| `backend/api/sinav.py:737-738` | `except Exception: logger.warning("BKT pipeline hatası...")` | **K2** — save-answer 200 + `algorithm: null`, mastery güncellenmez |
| `backend/api/enhanced_chat.py:426,510,539` | Chat DB persist fail → `logger.warning` | Kullanıcı mesajı kaydedildi sanır, DB'de yok |
| `backend/api/auth.py:329-330` | Refresh token DB persist fail | Cookie'de refresh token var, DB'de yok → sessiz session desync |

### 🟡 MEDIUM — Fallback Legitimate ama Silent Degradation

| Dosya:Satır | Bağlam |
|-------------|--------|
| `backend/api/bilge_alp.py:210,260` | LLM unavailable fallback — mock response |
| `backend/api/enhanced_chat.py:347,376,481` | LiteLLM/Ollama/stream fallback |
| `backend/agents/learning_path_agent.py:238,1060,1151,1160,1233,1433` | YouTube/KhanAcademy/OER/lesson fetch fails |
| `backend/agents/coordination/blackboard.py:198,316,328,443` | Redis connection + message parse fails |
| `backend/services/bertscore_evaluator.py:34,121,175,245,307` | HF login, scorer init, eval fails |
| `backend/services/admin_service.py:97,120` | Admin yetki kontrolü — exception → False (fail-closed OK ama log yetersiz) |

**Aksiyon önerisi:**
- `sinav.py:737` → `logger.warning` → `logger.exception` + response'a `"algorithm_failed": True` bilgisi
- `enhanced_chat.py` DB persist fails → response'a `"persist_warning": True`
- `auth.py:329` → refresh token persist fail KRITIK — response'a 500 dön veya refresh endpoint'i DB'den doğrulasın

---

## Scan 2 — Pydantic Validation Boundary Gaps

**Aranan:** `question_id: str = Field(...)` - `min_length` ya da UUID type kontrolü yok.

### 🔴 PATTERN — 11 Endpoint'te Aynı Bug

| Dosya:Satır | Endpoint | min_length? |
|-------------|----------|-------------|
| `backend/api/sinav.py:62` | `SaveAnswerRequest` (K3 kanıtlı) | ❌ |
| `backend/api/sinav.py:85` | flag question | ❌ |
| `backend/api/exam_answer_tracking.py:62` | AnswerTrackingCreate | ❌ |
| `backend/api/irt_morfoloji.py:23,352` | IRT submit | ❌ |
| `backend/api/learning_path_v2.py:224` | LP v2 answer | ❌ |
| `backend/api/productive_failure_api.py:60` | PF submit | ❌ |
| `backend/api/schemas/irt_schemas.py:201,268` | IRT param | ❌ |
| `backend/api/v1/semantic_search.py:111` | semantic search | ❌ |
| `backend/api/dina_api.py:39` | DINA submit | ✅ `min_length=1` |
| `backend/api/offline_sync_api.py:70` | offline sync | ✅ (selected_answer için) |

**Sonuç:** Boundary validation, `dina_api.py` dışında hiçbir yerde uygulanmıyor.
**Bu bir paternel bug değil — tek bir unutulmuş Field constraint, 11 kopyada tekrarlanıyor.**

**Aksiyon önerisi (Option C kapsamı):**
```python
# backend/api/sinav.py:62
question_id: str = Field(..., min_length=1, description="Soru UUID")
# veya daha sıkı:
from uuid import UUID
question_id: UUID = Field(..., description="Soru UUID")
```

Diğer 10 dosya — ayrı follow-up task (bu Session 136 scope dışı, GF3w fix sadece sinav.py).

---

## Scan 3 — Legacy Question() kwargs Trap (Dual Table)

**Aranan:** `Question(...)` constructor çağrılarında `topic=`, `subtopic=`, `difficulty=` kwargs.

### 🔴 PRODUCTION — Hemen Etkili

| Dosya:Satır | Durum |
|-------------|-------|
| `backend/services/soru_bankasi_service.py:183-209` | **K4 kanıtlı** — Admin POST /content/questions 500 dönüyor |

**Root cause detay:**
```python
# services/soru_bankasi_service.py:20
from models.question_bank import QuestionBankItem as Question  # production model

# services/soru_bankasi_service.py:183
yeni_soru = Question(
    ...
    topic=soru_data.get("konu", "Genel"),        # ❌ QuestionBankItem'da yok
    subtopic=soru_data.get("alt_konu"),          # ❌ QuestionBankItem'da yok
    difficulty=difficulty,                        # ❌ field adı 'difficulty_level' (Enum)
    # primary_topic_id= EKSIK                     # ❌ NOT NULL FK constraint
)
# services/soru_bankasi_service.py:217
except Exception as e:
    raise Exception(f"Soru eklenirken hata oluştu: {e}")  # generic 500
```

**QuestionBankItem model** (`models/question_bank.py:315-333`):
- `primary_topic_id: str ForeignKey("topic_hierarchy.id"), nullable=False`
- `difficulty_level: Enum(QuestionDifficultyLevel), default=MEDIUM`
- `topic`, `subtopic`, `difficulty` field'ları **YOK**

### 🟢 DEPRECATED — Etkisiz

| Dosya:Satır | Durum |
|-------------|-------|
| `backend/core/enhanced_content_manager.py:182` | Farklı `Question` class (seed loader, JSON content) |
| `backend/_deprecated/algorithms/turkish_morphology_aware_irt.py` | Arşivlendi |
| `backend/agents/_archive/study_buddy_agent.py` | Arşivlendi |

**Aksiyon önerisi (Option C kapsamı):**
```python
# 1. primary_topic_id: topic_hierarchy'den lookup
topic_row = await session.execute(
    select(TopicHierarchy.id).where(
        TopicHierarchy.subject_area == subject_db(soru_data["konu"]),
        TopicHierarchy.name == soru_data.get("alt_konu", soru_data["konu"]),
    )
)
primary_topic_id = topic_row.scalar_one_or_none()
if not primary_topic_id:
    raise HTTPException(400, f"Topic not found: {soru_data['konu']}")

# 2. Legacy kwargs kaldır
yeni_soru = Question(
    question_text=...,
    correct_answer=...,
    subject_area=subject_db(soru_data.get("konu")),  # UPPERCASE
    difficulty_level=difficulty,                      # Enum, not .value
    primary_topic_id=primary_topic_id,                # NOT NULL FK
    # topic/subtopic kaldırıldı
)
```

---

## Scan 4 — Lenient `< 500` Assertion Cluster

**Aranan:** `assert status_code < 500` — GF lenient pattern.

| Dosya:Satır | Bağlam | Değerlendirme |
|-------------|--------|---------------|
| `backend/tests/e2e/test_golden_flows.py:179` | GF5 teacher profile | 🟡 Feature gate OK olabilir, ama write-path için yetersiz |
| `backend/tests/e2e/test_golden_flows.py:221` | GF7 video fallback | 🟡 Feature gate OK |
| `backend/tests/e2e/test_golden_flows.py:271` | GF8 parent children | 🟡 Feature gate OK |
| `backend/tests/contract/test_schemathesis_api.py:308` | Contract tests | ✅ Property-based, OK |
| `backend/tests/integration/test_platform_health_audit.py:127,228` | Health audit | ✅ Health check bağlamı |
| `backend/tests/test_authenticated_stub_guardrails.py:312,338,365` | Stub guardrails | ✅ Guardrail bağlamı |

**Not:** GF5/GF7/GF8 `< 500` lenient ama **read-path** oldukları için kabul edilebilir.
Session 136 yeni yazdığımız GF1w/GF3w/GF6w **fail-closed** (state assert, status eşitliği).
Bu dizi için kural: **write-path → fail-closed, read-path → lenient kabul**.

---

## Scan 5 — DB Constraint Sanity

### Question Bank NULL Primary Topic

```sql
SELECT COUNT(*) total, COUNT(*) FILTER (WHERE primary_topic_id IS NULL) null_topic,
       COUNT(*) FILTER (WHERE is_active = true) active
FROM question_bank;
-- Result: (77401, 0, 64270)
```

**Bulgu:** ✅ **0 NULL** primary_topic_id. Bu, K2 varsayılan root cause'u
(`sinav.py:662` guard NULL topic atar) **YANLIŞ** olduğunu kanıtlar.
BKT pipeline silent fail başka nedenle — muhtemelen `subject_area` case mismatch
(BKT subject_slug lookup) veya BKTService kendi içinde sessiz başarısız oluyor.

**Action item:** GF1w test canlıda tekrar çalıştır, `algorithm: null` durumunu tekrar yakala,
`sinav.py:737` log'u `logger.exception` yap, asıl stacktrace'i gör.

### Subject_area Case Alignment

```sql
SELECT subject_area, COUNT(*) FROM question_bank WHERE is_active=true GROUP BY 1;
-- MATEMATIK: 18462, TURKCE: 10856, GEOMETRI: 9494, FIZIK: 6544, KIMYA: 6051,
-- EDEBIYAT: 3688, BIYOLOJI: 2523, TARIH: 2367, GENEL: 2318, SOSYAL: 1250,
-- COGRAFYA: 398, FEN: 314, INGILIZCE: 5

SELECT DISTINCT subject_area FROM topic_hierarchy ORDER BY 1;
-- BIYOLOJI, COGRAFYA, EDEBIYAT, FEN, FIZIK, GENEL, GEOMETRI, KIMYA,
-- MATEMATIK, SOSYAL, TARIH, TURKCE, None
```

**Bulgu:**
- 🟡 **INGILIZCE** qb'de 5 soru var ama topic_hierarchy'de yok → 5 soru için DAG topic lookup başarısız olacak
- 🟡 **topic_hierarchy.subject_area = NULL** row'lar var (125 total satır, 1 NULL group) — orphan topic'ler
- ✅ Case uyumu: tümü UPPERCASE, `.claude/rules/case-convention.md` ihlali yok

---

## Çıkarımlar — Yarım Feature Haritası

### Kesin Yarım (Kanıtlı, Suite FAIL Ediyor)

| # | Feature | Test | Root Cause |
|---|---------|------|-----------|
| 1 | save-answer validation | GF3w FAIL | `SaveAnswerRequest.question_id` `min_length` yok (+10 endpoint aynı) |
| 2 | admin question create | GF6w FAIL | `soru_bankasi_service.soru_ekle()` legacy kwargs + NOT NULL FK |
| 3 | save-answer BKT pipeline | GF1w aralıklı | `sinav.py:737` fire-and-forget, silent swallow |

### Muhtemel Yarım (Domain GF Test Gerekli — Option B)

| # | Alan | Hipotez | GF Test Adayı |
|---|------|---------|---------------|
| 4 | Gamification puan | save-answer → puan artmıyor olabilir | GF2w |
| 5 | Chat DB persist | 3 ayrı silent fail path | GF3wA |
| 6 | Teacher assignment | Write test yok, öğrenci görmüyor olabilir | GF5w |
| 7 | Parent consent | Onay sonrası child_data erişim | GF8w |
| 8 | Video solution | Request → link persistence | GF7w |
| 9 | Auth refresh token | `auth.py:329` silent DB fail | GF1wB |
| 10 | Placement test | Answer → theta_se update | GF2wB |

### Yarım Değil (Bu Audit'te Temizlendi)

- ✅ NULL primary_topic_id (0 bulundu)
- ✅ Case convention (UPPERCASE tüm katmanlar)
- ✅ Lenient `< 500` — read-path için kabul edilebilir

---

## Sonraki Adımlar

- **Option B** (bu session devamı): 8 domain GF write-path test ekle, hangilerinin gerçekten
  yarım olduğunu canlı suite ile tespit et.
- **Option C** (Option B sonrası): GF3w + GF6w kaynak fix'leri. Suite GREEN olmalı.
- **Follow-up (bu session dışı):**
  - Scan 2'deki 10 diğer endpoint `min_length` pattern fix'i (toplu PR)
  - `sinav.py:737` → `logger.exception` (BKT stacktrace görünür olsun)
  - `enhanced_chat.py` DB persist fail → response'a warning ekle
  - INGILIZCE topic_hierarchy entry ekle (5 soru orphan)

---

*Rapor: Session 136, Option A — canlı backend (:8000) + backend/ grep taraması.*
*Tamamlandı: 10 Nisan 2026.*
