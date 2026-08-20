-- Y11 FAZ C — ucuncu olcum: KABUL kumesinde json kolonlarin DOLULUGU ve TIPI.
-- Neden: hedefte 7 kolon `json`. Yukleyici bunlari `json.dumps` ile str'e cevirecek.
-- Eger bir kolon JSON *string skalari* tutuyorsa (json_typeof='string'), okuma
-- kodeki onu Python `str` yapar ve "str geldi -> kodek yok" guard'i YANLIS alarm verir.
-- Kosum: psql -U postgres -h localhost -p 5434 -d kiro2_temp -f <bu dosya>
\set ON_ERROR_STOP on

CREATE TEMP TABLE kabul (id text PRIMARY KEY);
\copy kabul FROM 'C:/tmp/y11_kabul_ids.txt'

\echo '=== json kolon DOLULUGU (KABUL 3666) ==='
SELECT count(*) FILTER (WHERE q.alternative_solutions IS NOT NULL) AS alt_soln,
       count(*) FILTER (WHERE q.misconception_tags    IS NOT NULL) AS misconc,
       count(*) FILTER (WHERE q.secondary_topics      IS NOT NULL) AS sec_top,
       count(*) FILTER (WHERE q.similar_question_ids  IS NOT NULL) AS sim_ids,
       count(*) FILTER (WHERE q.solution_steps        IS NOT NULL) AS sol_steps,
       count(*) FILTER (WHERE q.pipeline_metadata     IS NOT NULL) AS pipe_md
FROM kabul k JOIN question_bank q USING (id);

\echo '=== json_typeof — string skalari VAR MI (guard tasarimini belirler) ==='
SELECT 'pipeline_metadata'     AS kolon, json_typeof(q.pipeline_metadata)     AS tip, count(*)
FROM kabul k JOIN question_bank q USING (id) WHERE q.pipeline_metadata IS NOT NULL GROUP BY 1,2
UNION ALL
SELECT 'secondary_topics',      json_typeof(q.secondary_topics), count(*)
FROM kabul k JOIN question_bank q USING (id) WHERE q.secondary_topics IS NOT NULL GROUP BY 1,2
UNION ALL
SELECT 'misconception_tags',    json_typeof(q.misconception_tags), count(*)
FROM kabul k JOIN question_bank q USING (id) WHERE q.misconception_tags IS NOT NULL GROUP BY 1,2
UNION ALL
SELECT 'similar_question_ids',  json_typeof(q.similar_question_ids), count(*)
FROM kabul k JOIN question_bank q USING (id) WHERE q.similar_question_ids IS NOT NULL GROUP BY 1,2
UNION ALL
SELECT 'solution_steps',        json_typeof(q.solution_steps), count(*)
FROM kabul k JOIN question_bank q USING (id) WHERE q.solution_steps IS NOT NULL GROUP BY 1,2
UNION ALL
SELECT 'alternative_solutions', json_typeof(q.alternative_solutions), count(*)
FROM kabul k JOIN question_bank q USING (id) WHERE q.alternative_solutions IS NOT NULL GROUP BY 1,2
ORDER BY 1,2;
