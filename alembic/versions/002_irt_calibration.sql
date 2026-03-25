-- KIRO2 IRT Kalibrasyon sutunlari v3
-- Sadece question_bank tablosuna eksik sutunlari ekle
-- Gercek sutunlar zaten var: irt_discrimination, irt_difficulty, irt_guessing, is_calibrated

ALTER TABLE question_bank
    ADD COLUMN IF NOT EXISTS irt_method         TEXT,
    ADD COLUMN IF NOT EXISTS irt_calibrated_at  TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS irt_n_responses    INTEGER DEFAULT 0;
