-- KIRO2 Prerequisite DAG Migration v3
-- FK YOK — topic_hierarchy bağımsız çalışır

CREATE TABLE IF NOT EXISTS topic_prerequisites (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id    TEXT    NOT NULL,
    prereq_id   TEXT    NOT NULL,
    prereq_type TEXT    NOT NULL DEFAULT 'hard'
                    CHECK (prereq_type IN ('hard','soft')),
    strength    DECIMAL(3,2) NOT NULL DEFAULT 1.0
                    CHECK (strength BETWEEN 0.0 AND 1.0),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (topic_id, prereq_id)
);

CREATE INDEX IF NOT EXISTS idx_tp_topic  ON topic_prerequisites (topic_id)  WHERE is_active;
CREATE INDEX IF NOT EXISTS idx_tp_prereq ON topic_prerequisites (prereq_id) WHERE is_active;

-- Mastery view: sadece tablolar varsa olustur
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'kiro2_cat_sessions')
    AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'question_bank')
    AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'topic_hierarchy')
    THEN
        EXECUTE '
            CREATE OR REPLACE VIEW vw_user_topic_mastery AS
            SELECT
                cs.user_id,
                q.primary_topic_id     AS topic_id,
                th.name_tr             AS topic_name,
                q.subject_area         AS subject_name,
                MAX(cs.theta_final)    AS best_theta,
                COUNT(*)               AS session_count,
                MAX(cs.completed_at)   AS last_studied
            FROM kiro2_cat_sessions cs
            JOIN question_bank q    ON q.subject_area = cs.subject_id
            JOIN topic_hierarchy th ON th.id = q.primary_topic_id
            WHERE cs.state = ''completed''
            GROUP BY cs.user_id, q.primary_topic_id, th.name_tr, q.subject_area
        ';
    END IF;
END $$;
