# FAZ 3: Veri Katmani Tarama Raporu

**Tarih:** 2026-03-21
**Branch:** audit/fullstack-20260321

---

## 1. Dual Table Durumu (questions vs question_bank)

### Tarama Sonucu

| Kategori | Dosya Sayisi | Durum |
|----------|-------------|-------|
| `QuestionBankItem as Question` (DOGRU) | Tum production kodu | OK |
| `from models.database import Question` (LEGACY) | 3 (sadece test) | LOW risk |

### Legacy Import Detaylari

| Dosya | Kullanim | Risk |
|-------|---------|------|
| `tests/conftest.py:751` | Test fixture icinde | LOW |
| `tests/conftest_postgres.py:271` | Postgres test icinde | LOW |
| `tests/test_exam_answer_tracking.py:88` | Test icinde | LOW |

**Sonuc:** Production kodda yanlis tablo kullanimi YOK. Onceki session'larda (78-80) kapsamli fix yapilmis.

---

## 2. ForeignKey Index Durumu

| Metrik | Deger |
|--------|-------|
| Toplam ForeignKey | 303 |
| `index=True` olan | 37 (%12.2) |
| Index eksik | 266 (%87.8) |

**Etki:** JOIN sorgulerinde performans kaybi. Buyuk tablolarda (question_bank 77K) etkili olabilir.

**Ciddiyet:** MEDIUM (mevcut API <4ms p95, acil degil ama teknik borc)

**Oneri:** Alembic migration ile toplu index ekleme. Oncelik: `question_bank` ve `user` tablolarina referans veren FK'lar.

---

## 3. get_async_session Kullanimi

**Tarama:** `async with get_async_session()` pattern'i aranildi.
**Sonuc:** 0 yanlis kullanim. Tum kodlar `get_async_session_context()` (context manager) kullaniyor.

| Dosya | Kullanim | Dogruluk |
|-------|---------|----------|
| soru_bankasi_generator.py | `get_async_session_context()` | OK |
| init_db.py | `get_async_session_context()` | OK |
| seed_fallback_videos.py | `get_async_session_context()` | OK |
| test dosyalari | `get_async_session_context()` | OK |

**Sonuc:** Onceki session'da (78) yapilan fix hala gecerli.

---

## 4. is_active Filtresi

### Kontrol Edilen Ana Sorgular

| Dosya | is_active Filtresi | Durum |
|-------|-------------------|-------|
| soru_bankasi.py | VAR | OK |
| content_management.py | VAR | OK |
| osym_exam_engine.py | VAR | OK |
| exam_performance_service.py | VAR | OK |
| question_crud_api.py | VAR (cogu endpoint) | OK |
| question_bank_v2_routes.py | Kontrol gerekli | MEDIUM |

**Not:** 13,055 cop soru `is_active=FALSE` ile devre disi birakildi (Session 78).
64,281 aktif soru mevcut.

---

## 5. N+1 Query Pattern

### Bilinen N+1 Sorunlari

| Dosya | Fonksiyon | Onceki Durum | Mevcut Durum |
|-------|----------|-------------|-------------|
| exam_performance.py | `_analyze_performance()` | 120 sorgu/loop | FIX (Session 79, batch) |

**Diger potansiyel N+1'ler:** Detayli profiling gerekli. Mevcut API p95 <4ms oldugu icin acil degil.

---

## 6. Migration Durumu

**Alembic:** Aktif, migration dosyalari mevcut.
**Bekleyen migration:** ForeignKey index'leri (toplu ekleme planlanabilir).

---

## STATUS: TAMAM
