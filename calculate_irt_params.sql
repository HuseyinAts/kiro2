-- KIRO2 IRT Parametreleri Hesaplama Script'i
-- Tarih: 2026-01-13

-- IRT Difficulty: Zorluk seviyesine göre ayarla
UPDATE questions SET irt_difficulty = 
    CASE 
        WHEN difficulty = 'easy' THEN -1.0 + (RANDOM() * 0.5)   -- -1.0 ile -0.5 arası
        WHEN difficulty = 'medium' THEN -0.5 + (RANDOM() * 1.0) -- -0.5 ile 0.5 arası
        WHEN difficulty = 'hard' THEN 0.5 + (RANDOM() * 1.0)    -- 0.5 ile 1.5 arası
        ELSE 0.0
    END
WHERE irt_difficulty = 0.0;

-- IRT Discrimination: Ders ve sınav tipine göre ayarla
UPDATE questions SET irt_discrimination = 
    CASE 
        -- Matematik ve Fizik soruları genelde daha ayırt edici
        WHEN subject_area IN ('matematik', 'fizik') THEN 1.2 + (RANDOM() * 0.8)  -- 1.2 ile 2.0 arası
        -- AYT soruları daha ayırt edici
        WHEN exam_type = 'ayt' THEN 1.0 + (RANDOM() * 1.0)  -- 1.0 ile 2.0 arası
        -- TYT soruları orta seviye
        WHEN exam_type = 'tyt' THEN 0.8 + (RANDOM() * 0.8)  -- 0.8 ile 1.6 arası
        ELSE 0.5 + (RANDOM() * 1.0)  -- 0.5 ile 1.5 arası
    END
WHERE irt_discrimination = 1.0;

-- IRT Guessing: Seçenek sayısına göre ayarla
UPDATE questions SET irt_guessing = 
    CASE 
        -- E seçeneği varsa 5 seçenekli (1/5 = 0.20)
        WHEN option_e IS NOT NULL AND option_e != '' THEN 0.18 + (RANDOM() * 0.04)  -- 0.18 ile 0.22 arası
        -- E seçeneği yoksa 4 seçenekli (1/4 = 0.25)
        ELSE 0.23 + (RANDOM() * 0.04)  -- 0.23 ile 0.27 arası
    END
WHERE irt_guessing = 0.2;

-- Morphology Complexity: Türkçe ve sosyal bilimler için daha yüksek
UPDATE questions SET morphology_complexity = 
    CASE 
        WHEN subject_area IN ('turkce', 'sosyal', 'tarih') THEN 0.6 + (RANDOM() * 0.4)  -- 0.6 ile 1.0 arası
        WHEN subject_area IN ('matematik', 'fizik', 'kimya') THEN 0.3 + (RANDOM() * 0.4)  -- 0.3 ile 0.7 arası
        ELSE 0.4 + (RANDOM() * 0.3)  -- 0.4 ile 0.7 arası
    END
WHERE morphology_complexity = 0.5;

-- Readability Score: Soru uzunluğuna göre ayarla
UPDATE questions SET readability_score = 
    CASE 
        WHEN LENGTH(question_text) < 50 THEN 0.8 + (RANDOM() * 0.2)   -- Kısa sorular: 0.8-1.0
        WHEN LENGTH(question_text) < 100 THEN 0.6 + (RANDOM() * 0.3)  -- Orta sorular: 0.6-0.9
        WHEN LENGTH(question_text) < 200 THEN 0.4 + (RANDOM() * 0.3)  -- Uzun sorular: 0.4-0.7
        ELSE 0.2 + (RANDOM() * 0.3)  -- Çok uzun sorular: 0.2-0.5
    END
WHERE readability_score = 0.5;

-- Average Response Time: Zorluk ve soru uzunluğuna göre tahmin et
UPDATE questions SET average_response_time = 
    CASE 
        WHEN difficulty = 'easy' THEN 30.0 + (RANDOM() * 30.0)   -- 30-60 saniye
        WHEN difficulty = 'medium' THEN 45.0 + (RANDOM() * 45.0) -- 45-90 saniye
        WHEN difficulty = 'hard' THEN 60.0 + (RANDOM() * 60.0)   -- 60-120 saniye
        ELSE 45.0 + (RANDOM() * 30.0)
    END
WHERE average_response_time = 0.0;

-- İstatistik özeti
SELECT 
    'IRT Parameters Updated' as status,
    COUNT(*) as total_questions,
    ROUND(AVG(irt_difficulty)::numeric, 3) as avg_difficulty,
    ROUND(AVG(irt_discrimination)::numeric, 3) as avg_discrimination,
    ROUND(AVG(irt_guessing)::numeric, 3) as avg_guessing,
    ROUND(AVG(morphology_complexity)::numeric, 3) as avg_morphology,
    ROUND(AVG(readability_score)::numeric, 3) as avg_readability,
    ROUND(AVG(average_response_time)::numeric, 1) as avg_response_time
FROM questions;