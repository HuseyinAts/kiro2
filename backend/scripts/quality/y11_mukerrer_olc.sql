\encoding UTF8
-- Y11 — kiro2_temp'te MUKERRER soru olcumu (KIMYA-94 = KIMYA-1313 bulgusundan sonra).
-- Normalizasyon: bosluk sadelestirme + kucuk harf. Cok agresif degil (LaTeX korunuyor).
WITH kapi AS (
    SELECT id, subject_area, source_book, correct_answer,
           lower(regexp_replace(btrim(question_text), '\s+', ' ', 'g')) AS norm
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true
),
g AS (
    SELECT norm, count(*) AS n,
           count(DISTINCT correct_answer) AS farkli_anahtar,
           count(DISTINCT source_book) AS farkli_kitap
    FROM kapi GROUP BY norm
)
SELECT 'TUM KAPI (34.982)'
UNION ALL SELECT '  benzersiz metin        : ' || count(*) FROM g
UNION ALL SELECT '  toplam satir           : ' || sum(n) FROM g
UNION ALL SELECT '  MUKERRER satir (fazla) : ' || (sum(n) - count(*)) || '  (%'
       || round(100.0*(sum(n)-count(*))/sum(n), 2) || ')' FROM g
UNION ALL SELECT ''
UNION ALL SELECT '  2+ kez gecen metin     : ' || count(*) FROM g WHERE n > 1
UNION ALL SELECT '  en cok tekrar          : ' || max(n) FROM g
UNION ALL SELECT '  ⚠ ayni metin FARKLI anahtarla: ' || count(*) || ' metin'
  FROM g WHERE n > 1 AND farkli_anahtar > 1
UNION ALL SELECT '  ayni metin FARKLI kitapta    : ' || count(*) || ' metin'
  FROM g WHERE n > 1 AND farkli_kitap > 1
UNION ALL SELECT ''
UNION ALL SELECT 'SAYISAL DERSLER (MAT/GEO/KIM/FIZ)'
UNION ALL SELECT '  benzersiz / toplam     : ' || count(*) || ' / ' || sum(n)
       || '  -> mukerrer %' || round(100.0*(sum(n)-count(*))/sum(n), 2)
  FROM (SELECT norm, count(*) n FROM kapi
        WHERE subject_area IN ('MATEMATIK','GEOMETRI','KIMYA','FIZIK')
        GROUP BY norm) s
UNION ALL SELECT '  KIMYA benzersiz/toplam : ' || count(*) || ' / ' || sum(n)
       || '  -> mukerrer %' || round(100.0*(sum(n)-count(*))/sum(n), 2)
  FROM (SELECT norm, count(*) n FROM kapi WHERE subject_area='KIMYA' GROUP BY norm) k;
