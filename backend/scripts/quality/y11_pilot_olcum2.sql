-- Y11 FAZ C — ikinci olcum turu (salt okunur). CANLI kiro2'ya kosulur.
-- Kosum: psql -U postgres -h localhost -p 5434 -d kiro2 -f <bu dosya>
\set ON_ERROR_STOP on

\echo '=== A. topic_kod_haritasi: canli topic_hierarchy kodlari ==='
SELECT code, id, level FROM topic_hierarchy ORDER BY code;

\echo '=== B. KAYNAKTAKI 16 KOD canlida var mi (eksik = goc DURUR) ==='
WITH kaynak_kodlar(code) AS (
    VALUES ('KIM.DEN'),('KIM.ASI'),('KIM.ORG'),('TYT-KIM-02'),('KIM'),
           ('TYT-KIM-04'),('TYT-KIM-01'),('TYT-KIM-03'),('TYT-KIM-09'),
           ('TYT-KIM-11'),('KIM.TER'),('TYT-KIM-10'),('FIZ'),('TYT-KIM-12'),
           ('MAT.TRV'),('FEN')
)
SELECT k.code,
       (t.id IS NOT NULL) AS canlida_var,
       t.id AS canli_id
FROM kaynak_kodlar k
LEFT JOIN topic_hierarchy t ON t.code = k.code
ORDER BY canlida_var, k.code;

\echo '=== C. pipeline_metadata KOLON TIPI (json mi jsonb mi) ==='
SELECT table_name, column_name, data_type, udt_name
FROM information_schema.columns
WHERE column_name IN ('pipeline_metadata','id','question_image_url','bloom_category')
  AND table_name IN ('question_bank','question_content','question_metadata','question_statistics')
ORDER BY table_name, column_name;

\echo '=== D. damga geri-okunabilir mi: json vs jsonb ->> davranisi ==='
SELECT '{"a":1,"y11_batch":"y11-kimya-2026-08"}'::json  ->> 'y11_batch' AS json_okuma,
       '{"a":1,"y11_batch":"y11-kimya-2026-08"}'::jsonb ->> 'y11_batch' AS jsonb_okuma;
