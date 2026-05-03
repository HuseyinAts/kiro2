-- Session 88 fix #2: manual_review_queue.old_question_id nullable
-- Sebep: Quality gate (Session 88) "yeni soru, eskisi yok" use-case'inde
-- old_question_id NULL olmali. Mevcut "Layer 3 = mevcut korunmus soru" 
-- senaryosunda hala FK ile dogrulanir.
--
-- FK = ON DELETE CASCADE -> NULL'a izin verince FK kontrol skip edilir
-- (PostgreSQL FK semantigi: NULL referans tetiklenmez, MATCH SIMPLE varsayilani).
--
-- Geri alma:
--   UPDATE manual_review_queue SET old_question_id = '<sentinel>' WHERE old_question_id IS NULL;
--   ALTER TABLE manual_review_queue ALTER COLUMN old_question_id SET NOT NULL;

BEGIN;

ALTER TABLE manual_review_queue
  ALTER COLUMN old_question_id DROP NOT NULL;

-- Dogrulama
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'manual_review_queue' AND column_name = 'old_question_id';

COMMIT;