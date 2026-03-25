-- =====================================================================
-- KIRO2 Migration 005 — Learning Path Tables (v2 - VARCHAR user_id)
-- Oluşturma: 2026-03-24
-- NOT: users.id VARCHAR(255) tipi nedeniyle FK referans kaldırıldı
-- =====================================================================

-- ── student_goals ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS student_goals (
    user_id           VARCHAR(255) NOT NULL PRIMARY KEY,
    exam_type         VARCHAR(20)  NOT NULL DEFAULT 'TYT'
                          CHECK (exam_type IN ('TYT','AYT_SAY','AYT_EA','AYT_SOZ')),
    exam_date         DATE         NOT NULL DEFAULT '2026-06-07',
    daily_minutes     INTEGER      NOT NULL DEFAULT 120
                          CHECK (daily_minutes BETWEEN 30 AND 480),
    target_university VARCHAR(200),
    target_department VARCHAR(200),
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── daily_plans ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_plans (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           VARCHAR(255) NOT NULL,
    plan_date         DATE         NOT NULL,
    exam_date         DATE         NOT NULL,
    days_remaining    INTEGER      NOT NULL,
    total_minutes     INTEGER      NOT NULL DEFAULT 0,
    plan_json         JSONB        NOT NULL DEFAULT '{}',
    weak_subject      VARCHAR(50),
    strong_subject    VARCHAR(50),
    motivational_note TEXT,
    generated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, plan_date)
);

-- ── learning_progress_daily ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS learning_progress_daily (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        VARCHAR(255) NOT NULL,
    log_date       DATE         NOT NULL DEFAULT CURRENT_DATE,
    subject        VARCHAR(50)  NOT NULL,
    minutes_spent  INTEGER      NOT NULL DEFAULT 0,
    questions_done INTEGER      NOT NULL DEFAULT 0,
    correct_count  INTEGER      NOT NULL DEFAULT 0,
    activity_type  VARCHAR(30)  NOT NULL DEFAULT 'cat'
                       CHECK (activity_type IN ('cat','fsrs_review','practice','placement')),
    theta_before   FLOAT,
    theta_after    FLOAT,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, log_date, subject, activity_type)
);

-- ── user_theta ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_theta (
    user_id        VARCHAR(255) NOT NULL,
    subject_area   VARCHAR(50)  NOT NULL,
    theta_estimate FLOAT        NOT NULL DEFAULT 0.0,
    theta_se       FLOAT        NOT NULL DEFAULT 0.5,
    response_count INTEGER      NOT NULL DEFAULT 0,
    last_updated   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, subject_area)
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_daily_plans_user_date
    ON daily_plans (user_id, plan_date DESC);

CREATE INDEX IF NOT EXISTS idx_progress_user_date
    ON learning_progress_daily (user_id, log_date DESC);

CREATE INDEX IF NOT EXISTS idx_progress_subject
    ON learning_progress_daily (subject, log_date DESC);

CREATE INDEX IF NOT EXISTS idx_user_theta_user
    ON user_theta (user_id);

-- Yorumlar
COMMENT ON TABLE student_goals IS 'Öğrencinin sınav tipi, tarihi ve günlük çalışma hedefi';
COMMENT ON TABLE daily_plans IS 'ZPD+DAG+IRT+FSRS ile üretilen günlük çalışma planları';
COMMENT ON TABLE learning_progress_daily IS 'Her gün her ders için tamamlama kaydı';
COMMENT ON TABLE user_theta IS 'IRT θ tahmini — ders bazlı yetenek seviyesi';

SELECT 'Migration 005 tamamlandi' AS status;
