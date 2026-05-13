-- D2_legacy_approved_downgrade.sql
-- Date: 2026-05-15
-- Author: Claude session (Session 156)
-- Purpose: 14 May 2026 audit (approved %87 hata) + smoking gun analizi sonrası
--   17,950 yanlış 'approved' satırını 'legacy_v3_unaudited'a çevir.
--
-- Smoking gun: backend/scripts/import_d_dataset.py:212 (commit 877cb44c,
--   4 Mart 2026) literal "approved" hardcoded yazıyordu. Manuel onay
--   süreci hiç yapılmamıştı. 14 May audit:
--     - approved 30-örnek mini-audit: %87 hata
--     - exact|true %84, fuzzy|true %76, exact|false %44, fuzzy|false %40
--
-- Convention v2: docs/quality_review_status_convention.md
--
-- DRY-RUN ÖNCE (Hüseyin çalıştıracak):
--   psql -p 5434 -U postgres -d kiro2 -c "
--     SELECT quality_review_status, COUNT(*)
--     FROM question_bank
--     WHERE is_active = TRUE
--     GROUP BY quality_review_status
--     ORDER BY COUNT(*) DESC;
--   "
--
-- BACKUP TAVSİYE (transaction içinde değiştirdiğimiz için reversible ama
--   yine de):
--   pg_dump -p 5434 -U postgres -d kiro2 -t question_bank --data-only \
--     > backup_question_bank_pre_D2.sql
--
-- ROLLBACK:
--   UPDATE question_bank
--   SET quality_review_status = 'approved'
--   WHERE quality_review_status = 'legacy_v3_unaudited';

BEGIN;

-- Önceki sayım (verification için)
SELECT
  'pre_migration' AS phase,
  quality_review_status,
  COUNT(*) AS n
FROM question_bank
WHERE is_active = TRUE
GROUP BY quality_review_status
ORDER BY n DESC;

-- Esas update
UPDATE question_bank
SET quality_review_status = 'legacy_v3_unaudited',
    updated_at = NOW()
WHERE quality_review_status = 'approved';

-- Sonraki sayım (verification için)
SELECT
  'post_migration' AS phase,
  quality_review_status,
  COUNT(*) AS n
FROM question_bank
WHERE is_active = TRUE
GROUP BY quality_review_status
ORDER BY n DESC;

-- Beklenen sonuç: 'approved' = 0, 'legacy_v3_unaudited' = ~17,950
-- Eğer sayılar beklenenle uyuşmazsa COMMIT yapma, ROLLBACK et.

COMMIT;

-- Post-deploy: v_safe_for_beta view'u güncellenmeli (D4 migration).
-- D4 olmadan view 'approved'u beklediği için boş sonuç döner.
