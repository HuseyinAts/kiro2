-- KIRO2 - question_bank_staging.correct_answer NOT NULL kaldir
-- Sebep: Vision modelin sekilli/grafik sorularda correct_answer cikaramamasi
-- pilot batch'inde 5 sayfanin staging'e bile girememesine yol aciyor (~25 soru kayip).
-- Tasarim: NULL'lar staging'e girer, resolve_conflict'in kalite gate'i Layer 3'e
-- (manual_review_queue) yonlendirir. Vision cikitisi kaybolmaz, manuel duzeltme
-- akisina dahil olur.
--
-- Geri alma: NULL satirlar manuel duzeltildikten/temizlendikten sonra
--   ALTER TABLE question_bank_staging ALTER COLUMN correct_answer SET NOT NULL;
--
-- Iliskili: M3 plan §6 hata matrisi - "flag + devam" niyetiyle uyumlu.

BEGIN;

ALTER TABLE question_bank_staging
  ALTER COLUMN correct_answer DROP NOT NULL;

-- Dogrulama
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_name = 'question_bank_staging' AND column_name = 'correct_answer';

COMMIT;