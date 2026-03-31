-- Migration 016: Isolate synthetic events from kiro2_learning_events
-- Sentetik verileri ayri tabloya tasi — IRT kalibrasyonu ve analytics'i temizle
-- Tarih: 2026-03-31

BEGIN;

-- 1. Ayni sema ile yeni tablo olustur
CREATE TABLE IF NOT EXISTS kiro2_learning_events_synthetic (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    question_id TEXT NOT NULL,
    session_id UUID,
    event_type TEXT NOT NULL DEFAULT 'synthetic_response',
    is_correct BOOLEAN,
    theta_after NUMERIC,
    response_ms INTEGER,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_synthetic_events_user
    ON kiro2_learning_events_synthetic(user_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_synthetic_events_question
    ON kiro2_learning_events_synthetic(question_id);

-- 2. Sentetik verileri yeni tabloya kopyala
INSERT INTO kiro2_learning_events_synthetic
SELECT * FROM kiro2_learning_events
WHERE event_type = 'synthetic_response'
ON CONFLICT (id) DO NOTHING;

-- 3. Ana tablodan sil
DELETE FROM kiro2_learning_events
WHERE event_type = 'synthetic_response';

-- 4. Dogrulama
DO $$
DECLARE
    synth_in_main INTEGER;
    synth_in_archive INTEGER;
BEGIN
    SELECT COUNT(*) INTO synth_in_main
    FROM kiro2_learning_events WHERE event_type = 'synthetic_response';

    SELECT COUNT(*) INTO synth_in_archive
    FROM kiro2_learning_events_synthetic;

    RAISE NOTICE 'Synthetic in main table: % (should be 0)', synth_in_main;
    RAISE NOTICE 'Synthetic in archive table: %', synth_in_archive;

    IF synth_in_main > 0 THEN
        RAISE EXCEPTION 'HATA: Ana tabloda hala synthetic event var!';
    END IF;
END $$;

COMMIT;
