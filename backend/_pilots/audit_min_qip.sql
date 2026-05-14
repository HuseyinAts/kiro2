SELECT min_qip, COUNT(*) AS sayfa
FROM (
    SELECT source_book, source_page,
           MIN((pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page')::int) AS min_qip
    FROM question_bank
    WHERE is_active=TRUE
      AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page') ~ '^[0-9]+$'
    GROUP BY source_book, source_page
) AS x
GROUP BY min_qip ORDER BY min_qip LIMIT 10;
