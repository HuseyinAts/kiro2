# quality_review_status — Convention v3 (Bronze tier)

**Tarih:** 14 May 2026
**Trigger:** Quality Pool Plan v1 (Faz 1.6) Bronze tier sistemi + Faz 0.7 pool kategori kararı
**Önceki:** [Convention v2](quality_review_status_convention.md) — drop hardcoded 'approved', add legacy_v3_unaudited
**Yazan:** Claude session 156

---

## Convention v2'den v3'e fark

Convention v2 (15 May 2026) 7 status değer tanımladı. Convention v3 SADECE 1 yeni değer ekler: `bronze_clean`.

```diff
  pending          - İlk insert default
  unverified       - Pipeline otomatik etiketledi, manuel onay yok
  legacy_v3_unaudited - v3.5 hardcoded approved, %87 hata audit'le
+ bronze_clean     - Pipeline-fix uygulanmış (image link, sanity check, OCR validate),
+                    judge için hazır ama henüz judged değil
  human_verified   - Curator manuel onay
  auto_judged_high - LLM judge yüksek güven (post-Faz 5)
  rejected         - Curator/judge reddetti veya audit-driven reject (Faz 0.7)
  archived         - Soft-delete marker (is_active=False ile birlikte)
```

---

## Yeni Status: `bronze_clean`

### Anlam

Pipeline-fix sprint'leri (Plan v1 Faz 1.1-1.4) uygulanmış satırlar:
- Tier C+D image matcher → image_url populated (eligible row için)
- OCR text validator → noktalama + Türkçe sözlük geçti
- Sanity checker → duplicate options yok, answer A-E içinde

`bronze_clean` = "yapısal kalite kontrolünden geçti, ama içerik (cevap doğruluğu) henüz yargılanmadı".

### Beta'ya uygun mu? ❌ Hayır

`v_safe_for_beta` view sadece `human_verified` ve `auto_judged_high` kabul eder. Bronze beta'da görünmez.

Sebep: Bronze "pipeline-fix passed" demek, "doğru cevap" demek değil. Audit %26 wrong_answer Bayesian'la, %30 raw Gemini Flash. Judge devre dışında bu satırlar öğrenciye gösterilemez.

### Kim set eder?

Faz 1.5 (pipeline-fix run audit) sonrası, Faz 1.6 (Bronze migration script) tarafından otomatik.

**Filtre v1 (revize 16 May 2026):** Doc orijinali `sanity_flags` + `ocr_quality_flag` key'leri arıyordu — bu key'ler gerçek pipeline_metadata'da yok (doc/kod drift). Gerçek deploy edilen filtre:

```sql
UPDATE question_bank
SET quality_review_status = 'bronze_clean', updated_at = NOW()
WHERE quality_review_status = 'unverified'
  AND is_active = TRUE
  AND question_image_url IS NOT NULL  -- pipeline-fix uygulandı (Tier A/B/C/D/E/F/G/I)
  AND NOT (
    -- pipeline_metadata.quality_flags problem içermesi → bronze değil
    pipeline_metadata::jsonb ? 'quality_flags'
    AND pipeline_metadata::jsonb -> 'quality_flags' ?| ARRAY[
      'duplicate_option_values',
      'answer_uncertain',
      'numeric_q_nonnumeric_a',
      'empty_options'
    ]
  );
```

**Gerekçe:** Convention v3 yazıldığında (14 May) `sanity_flags`/`ocr_quality_flag` plan vardı ama Faz 1.3/1.4 script'leri farklı key isimlendirmeyle deploy etti (`quality_flags`). Mevcut sinyaller:
- `question_image_url IS NOT NULL` → 84,905 unverified satır (pipeline-fix kanıtı, Tier A/B legacy + Tier C/D/I audit-trail'li)
- `quality_flags` problem işaretleri → ~1,050 satır (bunlar promotion adayı DEĞİL)
- Audit trail (`tier_d_match`, `tier_i_reocr`, `book_key_match`, `tier_f_match`) → 21,319 satır (alt küme)

Gevşek filtre (84,905) ile sıkı filtre (21,319) arasında karar: Plan v1 satır 145 "~80-100K satır" hedefi gevşek filtreyle uyumlu, Tier A/B legacy ve Session 157 Tier C (16,440 image_url ama flag yazılmamış audit gap) dahil. Bronze beta'ya alınmaz, judge öncesi tier marker olarak yeterli.

### Kim alabilir?

Faz 6.1 (judge pilot) ve Faz 6.3 (judge full run) `bronze_clean` satırları okur:

```sql
SELECT id FROM question_bank
WHERE quality_review_status = 'bronze_clean'
  AND is_active = TRUE
ORDER BY md5(id::text || '<run_id>')
LIMIT N;
```

Judge pass → `auto_judged_high` (Gold tier)
Judge fail → `rejected`

---

## Tam Convention v3 Tablosu

| Değer | Anlam | Set eden | Beta'ya uygun |
|---|---|---|---|
| `pending` | İlk insert default, hiç işlenmemiş | DB schema | ❌ |
| `unverified` | Pipeline çıktısı, hiçbir kontrolden geçmemiş | Pipeline post-process | ❌ |
| `legacy_v3_unaudited` | v3.5 import'undan otomatik "approved" alan | Migration D2 (15 May) | ❌ |
| **`bronze_clean`** | **Pipeline-fix kontrollerinden geçti, judge için hazır** | **Faz 1.6 migration** | ❌ |
| `human_verified` | Gerçek insan onayı (curator UI) | Curator workflow | ✅ |
| `auto_judged_high` | LLM judge yüksek güven (post-Faz 5) | Judge pipeline | ✅ |
| `rejected` | Reddedildi (curator, judge, veya audit-driven) | Curator/judge/migration | ❌ |
| `archived` | Soft-delete marker | CRUD endpoint | ❌ |

### CHECK constraint (yeni)

```sql
ALTER TABLE question_bank
  DROP CONSTRAINT IF EXISTS quality_review_status_v2_check;

ALTER TABLE question_bank
  ADD CONSTRAINT quality_review_status_v3_check
  CHECK (quality_review_status IN (
    'pending',
    'unverified',
    'legacy_v3_unaudited',
    'bronze_clean',
    'human_verified',
    'auto_judged_high',
    'rejected',
    'archived'
  ));
```

---

## Migration Yolu

### Önkoşul: Convention v2 deploy edilmiş olmalı

Mevcut state (live DB, 14 May 2026):
```
unverified            146,387
legacy_v3_unaudited    18,397
pending                 2,775
v_safe_for_beta             0
```

### Adım 1 — Alembic migration (CHECK constraint güncellemesi)

`backend/alembic/versions/20260514_quality_review_status_v3_bronze.py` hazır (bu sessionda eklenir).

Sadece CHECK constraint'i günceller. Data migration yok bu adımda.

### Adım 2 — Faz 0.7 pool categorization migration

`docs/pool_categorization_decision.md` SQL'i çalıştır:
- legacy_v3 ai_upgrade_bayes_*: → `rejected` (~9,834)
- legacy_v3 jsonl_v11: → `rejected` (~1,131)
- legacy_v3 page_inline + ai_solved + crossval + ai_crop: → `unverified` (~5,272)
- legacy_v3 null source: → `pending` (~2,160)

### Adım 3 — Faz 1 pipeline-fix sprint

Tier C+D image matcher + OCR validator + sanity checker uygulanır.

### Adım 4 — Faz 1.6 Bronze migration

Pipeline-fix kontrollerinden geçen satırlar `unverified` → `bronze_clean`.

Beklenen pool: ~80-100K satır (146K unverified - rejected - failed sanity).

### Adım 5 — Faz 5+6 Judge

`bronze_clean` → `auto_judged_high` (pass) veya `rejected` (fail).

---

## Service Callsite Audit (Convention v2 D5'in genişlemesi)

Convention v2 D5'te 3 servis dosyası `'approved'` query'lerinden çıkarıldı. Convention v3 ile aynı dosyalar **`bronze_clean` durumunu kabul edecek mi?** karar gerekli.

### Etkilenecek dosyalar (grep'le tespit, edit Faz 1.6'ya):

| Dosya | Mevcut filter | Convention v3 etkisi |
|---|---|---|
| `backend/app/services/cat_session.py` | `human_verified` + `auto_judged_high` | DEĞİŞMEZ — bronze beta'ya alınmaz |
| `backend/app/services/placement_service.py` | aynı | DEĞİŞMEZ |
| `backend/core/osym_exam_engine.py` | aynı | DEĞİŞMEZ |
| `backend/api/content_management.py` | review/curator queue | YENİ filter `bronze_clean` (judge eligible) |
| `backend/api/quality_gates_api.py` | quality status read | display/admin için bronze kategori ekle |

**Sonuç:** Beta-facing servisler (cat, placement, osym_exam) değişmez. Admin/curator endpoints `bronze_clean` ek olarak ele alır (Faz 1.6 sub-task).

### v_safe_for_beta view değişmez

Convention v2 D4 view zaten `human_verified` + `auto_judged_high` filter ediyor. `bronze_clean` view'a eklenmez. Bronze beta'dan saklı kalır.

---

## Beklenen Pool Evolution (Convention v3 sonrası)

```
ŞU AN (Convention v2 deploy):
  unverified            146,387
  legacy_v3_unaudited    18,397
  pending                 2,775

CONVENTION V3 + FAZ 0.7 MIGRATION:
  unverified            151,659  (+5,272 from legacy_v3)
  legacy_v3_unaudited        0  (komple migrated)
  rejected               10,965  (yeni)
  pending                 4,935  (+2,160 from legacy_v3)
  bronze_clean                0  (henüz Faz 1.6 yok)

FAZ 1.6 BRONZE MIGRATION SONRASI (revize 16 May 2026, gerçek apply):
  unverified            ~61,482  (image_url yok — pipeline-fix uygulanmadı)
  bronze_clean           84,905  (image_url SET, quality_flags problem yok)
  legacy_v3_unaudited    18,397
  pending                 2,775
  Tahmin sapması: gevşek filter (yalnız image_url), strict filter 21K idi.

FAZ 6 JUDGE FULL RUN SONRASI:
  bronze_clean             0    (komple judged)
  auto_judged_high        30-50K (Gold = beta-safe)
  rejected               40-70K (judge fail)
  human_verified           5-10K (Sapphire, curator-built)
  
  v_safe_for_beta:       35-60K (Sapphire + Gold)
```

---

## Geri Uyumluluk

`bronze_clean` query yapan callsite YOK (yeni status). Mevcut servisler `bronze_clean` görünce sadece görmezden gelir (filter'larında değil).

Bir tek istisna: **admin curator queue** — `bronze_clean` satırları curator UI'da gösterilebilir (manuel verify hızlı yol).

---

## Testler

Convention v3 deploy sonrası verifikasyon:

```python
# tests/integration/test_convention_v3.py

def test_bronze_clean_in_constraint():
    """CHECK constraint bronze_clean kabul ediyor mu?"""
    # Insert sample with bronze_clean → should succeed
    
def test_bronze_clean_not_in_safe_view():
    """v_safe_for_beta bronze_clean'i HARİÇ tutmalı."""
    # Insert sample, check view exclusion
    
def test_legacy_v3_in_constraint():
    """Eski değerler hâlâ kabul ediliyor (geri uyumluluk)."""
    # All v2 values still accepted
```

---

## Acil Sonuç

Convention v3 = Convention v2 + 1 yeni status (`bronze_clean`). Migration risk düşük (CHECK constraint extend, data migration ayrı), revert kolay.

Faz 1.6 öncesi deploy edilmeli (Faz 1.6 bronze_clean status'unu yazmaya başlar).

---

## Sıradaki adım

1. ✅ Convention v3 doc yazıldı (bu dosya)
2. Alembic migration template: `backend/alembic/versions/20260514_quality_review_status_v3_bronze.py`
3. Convention v3 deploy ZAMANI: Faz 1.6 öncesi (Faz 1.5 audit sonrası)
4. Service callsite edit'leri: Faz 1.6 alt-task (bu doc'ta listelendi, audit-only)

*Generated by Faz 0.6. Convention v2'nin minimal extension'ı, geri uyumluluk korundu.*
