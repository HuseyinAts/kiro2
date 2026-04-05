-- CAT pool genisletme: her ders x zorluk icin 30 soru
-- is_calib_pool=FALSE ve difficulty_level != MEDIUM sorulaRdan en fazla 30 ekle

WITH ranked AS (
    SELECT 
        q.id,
        q.subject_area,
        q.difficulty_level,
        ROW_NUMBER() OVER (
            PARTITION BY q.subject_area, q.difficulty_level
            ORDER BY q.id
        ) as rn,
        (
            SELECT COUNT(*) 
            FROM question_bank p
            WHERE p.is_active = TRUE
              AND p.is_calib_pool = TRUE
              AND p.subject_area = q.subject_area
              AND p.difficulty_level = q.difficulty_level
        ) as existing_count
    FROM question_bank q
    WHERE q.is_active = TRUE
      AND q.is_calib_pool = FALSE
      AND q.difficulty_level IN ('VERY_EASY', 'EASY', 'HARD', 'VERY_HARD')
)
UPDATE question_bank
SET is_calib_pool = TRUE
WHERE id IN (
    SELECT id FROM ranked
    WHERE rn <= GREATEST(0, 30 - existing_count)
      AND existing_count < 30
);
