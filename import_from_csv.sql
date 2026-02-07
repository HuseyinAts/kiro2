-- KIRO2 Soru Import SQL
-- Kullanım: psql -h localhost -p 5434 -U postgres -d kiro2 -f import_from_csv.sql

-- 1. Topic'leri oluştur
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

-- 2. Geçici tablo oluştur
DROP TABLE IF EXISTS temp_questions;
CREATE TEMP TABLE temp_questions (
    id TEXT,
    question_text TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    option_e TEXT,
    correct_answer TEXT,
    topic_code TEXT,
    exam_type TEXT,
    subject_area TEXT,
    grade_level TEXT,
    difficulty_level TEXT,
    is_active TEXT,
    is_public TEXT,
    quality_score TEXT
);

-- 3. CSV'yi geçici tabloya yükle
\copy temp_questions FROM 'C:/Users/husey/kiro2/kiro2_import.csv' WITH (FORMAT csv, DELIMITER E'\t', ENCODING 'UTF8');

-- 4. Ana tabloya aktar (topic_id ile birlikte)
INSERT INTO question_bank (
    id, question_text, option_a, option_b, option_c, option_d, option_e,
    correct_answer, primary_topic_id, exam_type, subject_area, grade_level,
    difficulty_level, is_active, is_public, quality_score, created_at, updated_at
)
SELECT 
    t.id::uuid,
    t.question_text,
    t.option_a,
    t.option_b,
    t.option_c,
    NULLIF(t.option_d, ''),
    NULLIF(t.option_e, ''),
    t.correct_answer,
    th.id,
    t.exam_type,
    t.subject_area,
    t.grade_level::integer,
    t.difficulty_level::question_difficulty_level,
    t.is_active::boolean,
    t.is_public::boolean,
    t.quality_score::float,
    NOW(),
    NOW()
FROM temp_questions t
LEFT JOIN topic_hierarchy th ON th.code = t.topic_code;

-- 5. Sonucu göster
SELECT COUNT(*) as toplam_soru FROM question_bank;
