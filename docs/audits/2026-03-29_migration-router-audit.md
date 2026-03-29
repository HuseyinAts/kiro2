# P2 Teknik Borc Audit — Migration + Router (29 Mart 2026)

## 1. Router Kayit Audit

**Kapsam:** `backend/api/` (~115 dosya) + `backend/api/v1/` (8 dosya)

| Metrik | Deger |
|--------|-------|
| ROUTER_MAPPING entry sayisi | 109 |
| `app.api.*` entryler | 6 (tumu gecerli) |
| `api.v1.*` entryler | 5 (tumu gecerli) |
| Dead entry (dosyasi yok) | 0 |
| Kayitsiz router (404 riski) | 2 → `_deprecated/` tasindi |

### Tasiman Dosyalar

| Dosya | Neden |
|-------|-------|
| `api/v1/optimal_ai.py` | `optimal_hybrid_system` modulu yok, 0 referans |
| `api/v1/question_parser_api.py` | `services.question_parser.pipeline` yok, 0 referans |

### Kasitli Disarda Birakilanlar

- `api/sentry_demo.py` — demo/test (guvenlik riski, loader.py'de yorumda)
- `api/tracing_example.py` — demo/test (ayni sebep)
- `api/_deprecated/` — 3 dosya (zaten deprecated)

**Sonuc:** 0 kayitsiz aktif router. Tum 404 riskleri giderildi.

---

## 2. Migration Raw SQL Audit

**Kapsam:** 39 alembic migration dosyasi

### Risk Dagilimi

| Risk | Dosya Sayisi | Durum |
|------|-------------|-------|
| HIGH | 4 | 3/4 fix edildi (ORM model + migration fix) |
| MEDIUM | 5 | Tumu DB ile uyumlu (dogrulanmis) |
| LOW | ~20 | Standart `op.create_table()` pattern |
| NONE | ~10 | Merge head, index-only, no-op |

### HIGH Risk Detay

| Migration | Tablo | Durum |
|-----------|-------|-------|
| `20260329_create_kiro2_cat_sessions.py` | kiro2_cat_sessions | FIXED — ORM model (`84701e7`) |
| `20260329_create_kiro2_learning_events.py` | kiro2_learning_events | FIXED — ORM model (`84701e7`) |
| `20260329_create_topic_prerequisites.py` | topic_prerequisites | FIXED — ORM model (`84701e7`) |
| `7c540cf490c2_add_gamification_tables.py` | 12 gamification tablo | OK — ORM modelleri `gamification.py`'de mevcut, DB semasi uyumlu |

### MEDIUM Risk Detay

| Migration | Kontrol | Sonuc |
|-----------|---------|-------|
| `20260320_fix_gamification_fk_types.py` | 8 tablo FK type → VARCHAR | OK — tum FK kolonlari `character varying` |
| `20260320_fix_bkt_state_column_types.py` | bkt_states.student_id | OK — `character varying` |
| `20260312_add_image_metadata_columns.py` | question_bank 3 kolon | OK — `image_ocr_text` text, `image_width`/`image_height` integer |
| `004_advanced_performance_indexes.py` | `sorular` tablosu indexleri | N/A — `sorular` tablosu artik YOK (silinmis) |
| `20260102_fix_missing_columns.py` | users, questions ALTER | OK — migration sureci tamamlanmis |

### Onemli Bulgular

1. **`sorular` tablosu artik yok** — `004_advanced_performance_indexes.py`'deki GIN/trgm indexleri gecersiz ama zararsiz (tablo silinmis)
2. **Gamification FK fix basarili** — 11/11 kontrol edilen kolon `character varying` (VARCHAR) tipinde
3. **Image metadata kolonlari mevcut** — `IF NOT EXISTS` guard'i gereksizdi ama zarar vermedi
4. **Tum HIGH risk migration'lar icin ORM model mevcut** — alembic autogenerate artik drift tespit edebilir

### Kalan Risk

- Tarihi migration'lardaki `IF NOT EXISTS` pattern'i kalici — bu dosyalar DEGISTIRILMEMELI
- Gelecek migration'lar CLAUDE.md kurallarina uygun yazilacak (ORM-first, no raw DDL)

---

## Dogrulama Yontemi

```sql
-- Gamification FK type dogrulama
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('realm_progress','streaks','xp_transactions','oba_uyeler',
                     'user_badges','duels','parent_child','student_abilities','bkt_states')
  AND column_name IN ('user_id','student_id','player1_id','parent_id')
ORDER BY table_name;

-- Image metadata kolon dogrulama
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'question_bank'
  AND column_name IN ('image_ocr_text','image_width','image_height');
```
