-- Migration 016: subjects + student_abilities + daily_plans + yks_exam_goals
-- Tarih: 2026-04-01
-- Aciklama: Gunluk plan sistemi icin gerekli tablolar ve trigger

-- subjects tablosu
CREATE TABLE IF NOT EXISTS subjects (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    display_name TEXT,
    exam_type   TEXT DEFAULT 'TYT',
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO subjects (name, display_name, exam_type) VALUES
    ('MATEMATIK',  'Matematik',               'TYT_AYT'),
    ('GEOMETRI',   'Geometri',                'TYT_AYT'),
    ('TURKCE',     'Türkçe',                  'TYT'),
    ('EDEBIYAT',   'Türk Dili ve Edebiyatı',  'AYT'),
    ('FIZIK',      'Fizik',                   'AYT'),
    ('KIMYA',      'Kimya',                   'AYT'),
    ('BIYOLOJI',   'Biyoloji',                'AYT'),
    ('TARIH',      'Tarih',                   'AYT'),
    ('COGRAFYA',   'Coğrafya',                'AYT'),
    ('SOSYAL',     'Sosyal Bilimler',         'TYT'),
    ('FEN',        'Fen Bilimleri',           'TYT'),
    ('GENEL',      'Genel Kültür',            'TYT')
ON CONFLICT (name) DO UPDATE SET display_name = EXCLUDED.display_name;

-- yks_exam_goals tablosu
CREATE TABLE IF NOT EXISTS yks_exam_goals (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exam_type        TEXT NOT NULL DEFAULT 'TYT',
    exam_date        DATE NOT NULL,
    daily_minutes    INT DEFAULT 120,
    target_university TEXT,
    target_department TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT yks_exam_goals_user_unique UNIQUE (user_id)
);
CREATE INDEX IF NOT EXISTS idx_yks_goals_user ON yks_exam_goals(user_id);

-- daily_plans tablosu
CREATE TABLE IF NOT EXISTS daily_plans (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID NOT NULL,
    plan_date       DATE NOT NULL,
    exam_date       DATE,
    days_remaining  INT,
    total_minutes   INT,
    plan_json       JSONB DEFAULT '{}'::JSONB,
    weak_subject    TEXT,
    strong_subject  TEXT,
    motivational_note TEXT,
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT daily_plans_user_date_unique UNIQUE (user_id, plan_date),
    CONSTRAINT daily_plans_user_fk FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_daily_plans_user_date ON daily_plans(user_id, plan_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_plans_date ON daily_plans(plan_date);

-- Trigger: kiro2_learning_events -> student_abilities guncelle
CREATE OR REPLACE FUNCTION fn_update_student_ability()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_subject_id INT;
BEGIN
    IF NEW.event_type NOT IN ('exam_answer','cat_answer') THEN RETURN NEW; END IF;
    IF NEW.theta_after IS NULL THEN RETURN NEW; END IF;
    SELECT s.id INTO v_subject_id FROM question_bank qb
    JOIN subjects s ON s.name = qb.subject_area
    WHERE qb.id::text = NEW.question_id::text LIMIT 1;
    IF v_subject_id IS NULL THEN RETURN NEW; END IF;
    INSERT INTO student_abilities (student_id, subject_id, theta, theta_se, updated_at)
    VALUES (NEW.user_id::text, v_subject_id, ROUND(NEW.theta_after::numeric,3), 0.4, NOW())
    ON CONFLICT (student_id, subject_id) DO UPDATE SET
        theta      = ROUND(EXCLUDED.theta::numeric,3),
        theta_se   = GREATEST(student_abilities.theta_se - 0.02, 0.3),
        updated_at = NOW();
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN RETURN NEW;
END; $$;

DROP TRIGGER IF EXISTS trg_update_student_ability ON kiro2_learning_events;
CREATE TRIGGER trg_update_student_ability
AFTER INSERT ON kiro2_learning_events
FOR EACH ROW EXECUTE FUNCTION fn_update_student_ability();

-- Geri donuk: mevcut veriden student_abilities doldur
INSERT INTO student_abilities (student_id, subject_id, theta, theta_se, updated_at)
SELECT le.user_id::text, s.id,
    ROUND(COALESCE(AVG(le.theta_after) FILTER (WHERE le.theta_after BETWEEN -4 AND 4), 0.0)::numeric, 3),
    0.5, MAX(le.occurred_at)
FROM kiro2_learning_events le
JOIN question_bank qb ON qb.id::text = le.question_id::text
JOIN subjects s ON s.name = qb.subject_area
WHERE le.event_type IN ('exam_answer','cat_answer') AND le.is_correct IS NOT NULL
GROUP BY le.user_id, s.id
ON CONFLICT (student_id, subject_id) DO UPDATE SET
    theta=EXCLUDED.theta, theta_se=EXCLUDED.theta_se, updated_at=EXCLUDED.updated_at;

-- yks_exam_goals sahibi kullanicilar icin eksik ders satirlari
INSERT INTO student_abilities (student_id, subject_id, theta, theta_se, updated_at)
SELECT g.user_id::text, s.id, 0.0, 0.5, NOW()
FROM yks_exam_goals g CROSS JOIN subjects s
WHERE NOT EXISTS (
    SELECT 1 FROM student_abilities sa WHERE sa.student_id=g.user_id::text AND sa.subject_id=s.id
)
ON CONFLICT DO NOTHING;
