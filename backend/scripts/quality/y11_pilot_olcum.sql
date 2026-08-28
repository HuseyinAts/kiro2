-- Y11 FAZ C — pilot orneklemi tasarlamak icin OLCUM (salt okunur).
-- Kaynak: kiro2_temp. Hicbir kalici yazim yok: TEMP tablo oturum sonunda duser.
-- Kosum: psql -U postgres -h localhost -p 5434 -d kiro2_temp -f <bu dosya>
\set ON_ERROR_STOP on

-- OLCULDU: question_bank.id `character varying`, uuid DEGIL (ilk surum `uuid`
-- dedi ve `operator does not exist: uuid = character varying` ile dustu).
CREATE TEMP TABLE kabul (id text PRIMARY KEY);
\copy kabul FROM 'C:/tmp/y11_kabul_ids.txt'

\echo '=== 0. KONTROL KOLU: KABUL id kumesi kaynakta var mi ==='
SELECT (SELECT count(*) FROM kabul)                              AS tsv_id,
       (SELECT count(*) FROM kabul k JOIN question_bank q USING (id)) AS kaynakta_bulunan;

\echo '=== 1. topic_code dagilimi (remap ihtiyaci) ==='
SELECT t.code, count(*) AS soru
FROM kabul k
JOIN question_bank q USING (id)
JOIN topic_hierarchy t ON t.id = q.primary_topic_id
GROUP BY t.code
ORDER BY soru DESC;

\echo '=== 2. created_by / reviewed_by yetimligi ==='
SELECT count(*) FILTER (WHERE q.created_by  IS NULL) AS created_by_null,
       count(*) FILTER (WHERE q.created_by  IS NOT NULL) AS created_by_dolu,
       count(*) FILTER (WHERE q.reviewed_by IS NOT NULL) AS reviewed_by_dolu
FROM kabul k JOIN question_bank q USING (id);

\echo '=== 3. match_tier dagilimi (kapidan elenecekler) ==='
SELECT COALESCE(q.pipeline_metadata->>'match_tier','<NULL>') AS match_tier, count(*)
FROM kabul k JOIN question_bank q USING (id)
GROUP BY 1 ORDER BY 2 DESC;

\echo '=== 4. gorsel sinifi (kural 13) ==='
SELECT CASE
         WHEN q.question_image_url IS NULL                              THEN 'url_yok'
         WHEN q.question_image_url LIKE '%_PAGE%'                       THEN 'PAGE -> NULL'
         WHEN q.source_book = 'Apotemi 2024 Ayt Kimya Soru Bankasi'     THEN 'sizintili kitap -> NULL'
         ELSE 'crop -> TASINIR'
       END AS sinif, count(*)
FROM kabul k JOIN question_bank q USING (id)
GROUP BY 1 ORDER BY 2 DESC;

\echo '=== 5. bloom_level dagilimi (kural 8 — bilinmeyen seviye DURDURUR) ==='
SELECT q.bloom_level, count(*)
FROM kabul k JOIN question_bank q USING (id)
GROUP BY 1 ORDER BY 1;

\echo '=== 6. pipeline_metadata tipi (damga eklenebilir mi) ==='
SELECT jsonb_typeof(q.pipeline_metadata) AS tip, count(*)
FROM kabul k JOIN question_bank q USING (id)
GROUP BY 1;

\echo '=== 7. difficulty_level dagilimi (gocun asil degeri) ==='
SELECT q.difficulty_level::text, count(*)
FROM kabul k JOIN question_bank q USING (id)
GROUP BY 1 ORDER BY 2 DESC;
