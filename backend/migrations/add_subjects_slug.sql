-- =========================================================
-- Migration: subjects tablosuna slug kolonu ekle
-- yks_estimator.py bu kolonu kullanıyor
-- =========================================================

ALTER TABLE subjects ADD COLUMN IF NOT EXISTS slug VARCHAR(50);

-- Mevcut kayıtlar için slug üret (name'den)
UPDATE subjects
SET slug = LOWER(REGEXP_REPLACE(
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
        REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
        name, 'ı', 'i'), 'ğ', 'g'), 'ü', 'u'), 'ş', 's'),
        'ö', 'o'), 'ç', 'c'), 'İ', 'I'), 'Ğ', 'G'), 'Ü', 'U'),
        'Ş', 'S'), 'Ö', 'O'), 'Ç', 'C'),
    '[^a-zA-Z0-9]+', '-', 'g'
))
WHERE slug IS NULL;

-- Boş kalan slug'lar için code kullan
UPDATE subjects
SET slug = LOWER(code)
WHERE slug IS NULL OR slug = '';

-- Benzersizlik için index
CREATE UNIQUE INDEX IF NOT EXISTS idx_subjects_slug ON subjects(slug) WHERE slug IS NOT NULL;

SELECT id, name, code, slug FROM subjects ORDER BY name;
