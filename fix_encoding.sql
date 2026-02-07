-- KIRO2 Türkçe Karakter Encoding Düzeltme Script'i
-- Tarih: 2026-01-13

-- Bozuk Türkçe karakterleri düzelt
UPDATE questions SET 
    question_text = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
        REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(question_text,
        'Ã§', 'ç'),
        'Ä±', 'ı'),
        'ÄŸ', 'ğ'),
        'Å', 'ş'),
        'Ã¶', 'ö'),
        'Ã¼', 'ü'),
        'Ä°', 'İ'),
        'Ã‡', 'Ç'),
        'Åž', 'Ş'),
        'Ã–', 'Ö'),
        'Ãœ', 'Ü'),
        'Ä', 'Ğ')
WHERE question_text LIKE '%Ã%' OR question_text LIKE '%Ä%' OR question_text LIKE '%Å%';

-- Seçeneklerdeki karakterleri düzelt
UPDATE questions SET 
    option_a = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(option_a,
        'Ã§', 'ç'), 'Ä±', 'ı'), 'ÄŸ', 'ğ'), 'Å', 'ş'), 'Ã¶', 'ö'), 'Ã¼', 'ü')
WHERE option_a LIKE '%Ã%' OR option_a LIKE '%Ä%';

UPDATE questions SET 
    option_b = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(option_b,
        'Ã§', 'ç'), 'Ä±', 'ı'), 'ÄŸ', 'ğ'), 'Å', 'ş'), 'Ã¶', 'ö'), 'Ã¼', 'ü')
WHERE option_b LIKE '%Ã%' OR option_b LIKE '%Ä%';

UPDATE questions SET 
    option_c = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(option_c,
        'Ã§', 'ç'), 'Ä±', 'ı'), 'ÄŸ', 'ğ'), 'Å', 'ş'), 'Ã¶', 'ö'), 'Ã¼', 'ü')
WHERE option_c LIKE '%Ã%' OR option_c LIKE '%Ä%';

UPDATE questions SET 
    option_d = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(option_d,
        'Ã§', 'ç'), 'Ä±', 'ı'), 'ÄŸ', 'ğ'), 'Å', 'ş'), 'Ã¶', 'ö'), 'Ã¼', 'ü')
WHERE option_d LIKE '%Ã%' OR option_d LIKE '%Ä%';

UPDATE questions SET 
    option_e = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(option_e,
        'Ã§', 'ç'), 'Ä±', 'ı'), 'ÄŸ', 'ğ'), 'Å', 'ş'), 'Ã¶', 'ö'), 'Ã¼', 'ü')
WHERE option_e LIKE '%Ã%' OR option_e LIKE '%Ä%';

-- Yaygın encoding hatalarını düzelt
UPDATE questions SET
    question_text = REPLACE(question_text, '�', ''),
    option_a = REPLACE(option_a, '�', ''),
    option_b = REPLACE(option_b, '�', ''),
    option_c = REPLACE(option_c, '�', ''),
    option_d = REPLACE(option_d, '�', ''),
    option_e = REPLACE(option_e, '�', '')
WHERE question_text LIKE '%�%' 
   OR option_a LIKE '%�%'
   OR option_b LIKE '%�%'
   OR option_c LIKE '%�%'
   OR option_d LIKE '%�%'
   OR option_e LIKE '%�%';

-- Düzeltme sonrası kontrol
SELECT COUNT(*) as bozuk_karakter_sayisi
FROM questions
WHERE question_text LIKE '%Ã%' 
   OR question_text LIKE '%Ä%'
   OR question_text LIKE '%Å%'
   OR question_text LIKE '%�%';