-- migrate_aromat_topic_to_tur_par.sql
-- 30 Nis 2026 — Aromat paragraf 11 sorusu: TYT-TR-03 -> TUR.PAR
-- pipeline_metadata json tipinde, || ve ? icin jsonb cast gerekli.

BEGIN;

UPDATE question_bank
SET
  primary_topic_id = '09857a7f-b1a8-4183-9dc2-ae5667f21ea0',
  pipeline_metadata = (
    pipeline_metadata::jsonb
    || jsonb_build_object(
         'topic_migrated_from', 'TYT-TR-03',
         'topic_migrated_at',   now()
       )
  )::json,
  updated_at = now()
WHERE pipeline_metadata->>'merge_source' = 'claude_opus_4_7_v1'
  AND primary_topic_id = 'f0e9c5dd-4e65-5a65-9741-a3b89aa29e8e';

DO $$
DECLARE
  cnt int;
BEGIN
  SELECT COUNT(*) INTO cnt
  FROM question_bank
  WHERE pipeline_metadata->>'merge_source' = 'claude_opus_4_7_v1'
    AND primary_topic_id = '09857a7f-b1a8-4183-9dc2-ae5667f21ea0'
    AND pipeline_metadata::jsonb ? 'topic_migrated_from';

  IF cnt <> 11 THEN
    RAISE EXCEPTION 'Beklenen 11 migre satir, gercek %. Rollback yapiliyor.', cnt;
  END IF;

  RAISE NOTICE 'OK: % satir TUR.PAR a migre edildi.', cnt;
END $$;

COMMIT;
