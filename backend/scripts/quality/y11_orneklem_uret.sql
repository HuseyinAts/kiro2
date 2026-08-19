\encoding UTF8
-- Y11 on-kosul orneklemi — kiro2_temp kapi esdegeri (34.982), ORANTILI STRATIFIYE.
-- Salt 'y11s232' (S232'de okunan 12 sorunun 'y12salt'indan FARKLI -> bagimsiz cekim).
-- TRUNCATE YOK (14 May 2026 altin kurali). Cikti KOR: cevap anahtari YAZILMAZ.
WITH kapi AS (
    SELECT id, subject_area, exam_type, source_book, question_text,
           option_a, option_b, option_c, option_d, option_e, correct_answer
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true
),
kota(ders, n, grup) AS (VALUES
    -- orantili tahsis (34.982 uzerinden, 60 soru) -> ORAN HESABINA GIRER
    ('MATEMATIK',24,'ORAN'), ('KIMYA',8,'ORAN'), ('FIZIK',6,'ORAN'),
    ('TURKCE',6,'ORAN'), ('GEOMETRI',5,'ORAN'), ('BIYOLOJI',3,'ORAN'),
    ('TARIH',3,'ORAN'), ('EDEBIYAT',3,'ORAN'), ('COGRAFYA',1,'ORAN'),
    ('SOSYAL',1,'ORAN'),
    -- kapsama (populasyonun %0,85'i; orana GIRMEZ, ayri raporlanir)
    ('GENEL',2,'KAPSAMA'), ('FEN',2,'KAPSAMA')
),
sirali AS (
    SELECT k.*, row_number() OVER (PARTITION BY k.subject_area
                                   ORDER BY md5(k.id::text || 'y11s232')) AS sira
    FROM kapi k
),
secim AS (
    SELECT s.*, q.grup
    FROM sirali s JOIN kota q ON q.ders = s.subject_area
    WHERE s.sira <= q.n
)
SELECT '--- [' || grup || '/' || subject_area || '-' || sira || ']'
       || '  id=' || id
       || '  sinav=' || coalesce(exam_type,'-')
       || '  kitap=' || coalesce(source_book,'-')
       || E'\nSORU: ' || question_text
       || E'\n  A) ' || coalesce(option_a,'<BOS>')
       || E'\n  B) ' || coalesce(option_b,'<BOS>')
       || E'\n  C) ' || coalesce(option_c,'<BOS>')
       || E'\n  D) ' || coalesce(option_d,'<BOS>')
       || E'\n  E) ' || coalesce(option_e,'<BOS>')
       || E'\n'
FROM secim
ORDER BY grup DESC, subject_area, sira;
