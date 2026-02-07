-- KIRO2 Soru Import - Tek Adimda
-- 36,967 soru yukler

-- 1. Topic'leri olustur
INSERT INTO topic_hierarchy (id, level, code, name_tr, meb_code, is_active, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 1, 'MAT', 'Matematik', 'MAT', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'GEO', 'Geometri', 'GEO', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'FIZ', 'Fizik', 'FIZ', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'KIM', 'Kimya', 'KIM', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'BIO', 'Biyoloji', 'BIO', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'TUR', 'Turkce', 'TUR', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'EDB', 'Edebiyat', 'EDB', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'TAR', 'Tarih', 'TAR', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'COG', 'Cografya', 'COG', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'PAR', 'Paragraf', 'PAR', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'GEN', 'Genel', 'GEN', true, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Gecici tablo
DROP TABLE IF EXISTS temp_import;
CREATE TABLE temp_import (
    question_text TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    option_e TEXT,
    correct_answer VARCHAR(1),
    exam_type VARCHAR(10),
    subject_area VARCHAR(50),
    source_book VARCHAR(200),
    page_number VARCHAR(20)
);

-- 3. CSV yukle (COPY komutu)
\COPY temp_import FROM 'C:/Users/husey/kiro2/kiro2_import.csv' WITH (FORMAT csv, ENCODING 'UTF8');

-- 4. Ana tabloya aktar
INSERT INTO question_bank (
    id, question_text, option_a, option_b, option_c, option_d, option_e,
    correct_answer, primary_topic_id, exam_type, subject_area, grade_level,
    quality_score, is_active, is_public, difficulty_level, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    t.question_text,
    t.option_a,
    t.option_b,
    t.option_c,
    t.option_d,
    NULLIF(t.option_e, ''),
    t.correct_answer,
    th.id,
    t.exam_type,
    t.subject_area,
    11,
    0.0,
    true,
    true,
    'medium',
    NOW(),
    NOW()
FROM temp_import t
LEFT JOIN topic_hierarchy th ON th.code = (
    CASE t.subject_area
        WHEN 'Matematik' THEN 'MAT'
        WHEN 'Geometri' THEN 'GEO'
        WHEN 'Fizik' THEN 'FIZ'
        WHEN 'Kimya' THEN 'KIM'
        WHEN 'Biyoloji' THEN 'BIO'
        WHEN 'Turkce' THEN 'TUR'
        WHEN 'Edebiyat' THEN 'EDB'
        WHEN 'Tarih' THEN 'TAR'
        WHEN 'Cografya' THEN 'COG'
        WHEN 'Paragraf' THEN 'PAR'
        ELSE 'GEN'
    END
);

-- 5. Sonuc
SELECT 'YUKLENEN SORU SAYISI: ' || COUNT(*)::text FROM question_bank;

-- 6. Temizlik
DROP TABLE IF EXISTS temp_import;
