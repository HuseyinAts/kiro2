-- KIRO2 CAT Session Migration v3
-- FK YOK — users/kullanicilar tablosu garantili degil

CREATE TABLE IF NOT EXISTS kiro2_cat_sessions (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL,
    subject_id          TEXT        NOT NULL,
    theta_final         DECIMAL(6,4) NOT NULL DEFAULT 0.0,
    se_final            DECIMAL(6,4) NOT NULL DEFAULT 1.0,
    n_questions         SMALLINT    NOT NULL DEFAULT 0,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    state               TEXT        NOT NULL DEFAULT 'active'
                            CHECK (state IN ('active','completed','abandoned')),
    termination_reason  TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kiro2_cat_user ON kiro2_cat_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_kiro2_cat_subj ON kiro2_cat_sessions (user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_kiro2_cat_done ON kiro2_cat_sessions (user_id, completed_at DESC)
    WHERE state = 'completed';

CREATE TABLE IF NOT EXISTS kiro2_learning_events (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL,
    question_id TEXT        NOT NULL,
    session_id  UUID,
    event_type  TEXT        NOT NULL DEFAULT 'cat_answer',
    is_correct  BOOLEAN,
    theta_after DECIMAL(6,4),
    response_ms INTEGER,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kiro2_le_user     ON kiro2_learning_events (user_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_kiro2_le_question ON kiro2_learning_events (question_id, event_type);
