-- Kalibrasyon havuzu migration
-- Her dersten 200 "pilot soru" seç → warm-up bunlardan seçecek
-- Bu sayede 500 öğrenci × 3 soru = 1500 yanıt, 200 soruda birikir

-- 1. question_bank'a is_calib_pool kolonu ekle
ALTER TABLE question_bank
ADD COLUMN IF NOT EXISTS is_calib_pool BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_qbank_calib_pool
ON question_bank (subject_area, is_calib_pool)
WHERE is_calib_pool = TRUE AND is_active = TRUE;

-- 2. Her dersten 200 pilot soru seç
-- Kriter: ZPD merkezinden (b ∈ [-1, 1]), en yüksek exposure_rate'li sorular
-- Exposure rate yüksek = daha önce gösterilmiş = kaliteli

WITH ranked AS (
    SELECT
        id,
        subject_area,
        ROW_NUMBER() OVER (
            PARTITION BY subject_area
            ORDER BY
                exposure_rate DESC,           -- en çok gösterilen
                times_asked DESC,             -- en çok sorulan
                quality_score DESC,           -- en kaliteli
                ABS(irt_difficulty) ASC       -- b=0'a yakın (orta zorluk)
        ) AS rn
    FROM question_bank
    WHERE is_active = TRUE
      AND irt_difficulty BETWEEN -1.0 AND 1.0
)
UPDATE question_bank
SET is_calib_pool = TRUE
WHERE id IN (
    SELECT id FROM ranked WHERE rn <= 200
);

-- Sonuç
SELECT
    subject_area,
    COUNT(*) FILTER (WHERE is_calib_pool = TRUE) AS havuz_sayisi,
    COUNT(*)                                       AS toplam_soru
FROM question_bank
WHERE is_active = TRUE
GROUP BY subject_area
ORDER BY havuz_sayisi DESC;
