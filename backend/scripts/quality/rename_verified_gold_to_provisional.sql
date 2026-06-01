-- P1 (1 Haz 2026): verified_gold → verified_provisional
-- Gerekçe: tek kör-solver run'ı kalıcı ground-truth SAYILMAZ (K1b dairesellik
-- tekrarı). 2. bağımsız sinyal (farklı model re-solve / insan-GT) ile teyit
-- edilince verified_provisional → verified_gold terfi eder (P3).
-- Metadata-only, non-destructive: correct_answer / status DOKUNULMAZ.
--
-- Çalıştırma (Windows, Türkçe-güvenli):
--   "C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2 \
--       -f backend/scripts/quality/rename_verified_gold_to_provisional.sql

\set ON_ERROR_STOP on
BEGIN;

-- 1) Backup (rollback için): etkilenecek satırların id + pipeline_metadata
DROP TABLE IF EXISTS question_bank_provisional_rename_backup_20260601;
CREATE TABLE question_bank_provisional_rename_backup_20260601 AS
  SELECT id, pipeline_metadata FROM question_bank
  WHERE pipeline_metadata::jsonb ->> 'verified_gold' = 'true';

-- Ön-kontrol: kaç satır etkilenecek (beklenen ~2,734)
SELECT COUNT(*) AS will_rename
FROM question_bank
WHERE pipeline_metadata::jsonb ->> 'verified_gold' = 'true';

-- 2) Anahtarı yeniden adlandır: verified_provisional='true' ekle, verified_gold sil
UPDATE question_bank qb
SET pipeline_metadata = (
    (COALESCE(qb.pipeline_metadata::jsonb, '{}'::jsonb)
     || jsonb_build_object('verified_provisional', 'true'))
    - 'verified_gold'
)::json
WHERE qb.pipeline_metadata::jsonb ->> 'verified_gold' = 'true';

COMMIT;

-- 3) Doğrulama: provisional = backup_rows, gold = 0 olmalı
SELECT
  (SELECT COUNT(*) FROM question_bank
     WHERE pipeline_metadata::jsonb ->> 'verified_provisional' = 'true') AS provisional,
  (SELECT COUNT(*) FROM question_bank
     WHERE pipeline_metadata::jsonb ->> 'verified_gold' = 'true')        AS gold_remaining,
  (SELECT COUNT(*) FROM question_bank_provisional_rename_backup_20260601) AS backup_rows;

-- ROLLBACK (gerekirse):
--   UPDATE question_bank qb SET pipeline_metadata = b.pipeline_metadata
--   FROM question_bank_provisional_rename_backup_20260601 b WHERE qb.id = b.id;
