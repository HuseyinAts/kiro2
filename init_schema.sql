-- KIRO2 Temel Şema
-- Users tablosu
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    grade_level SMALLINT CHECK (grade_level BETWEEN 9 AND 12),
    target_exam VARCHAR(10) CHECK (target_exam IN ('TYT', 'AYT', 'YDT')),
    ability_theta DECIMAL(5,4) DEFAULT 0,
    total_xp INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_practice_date DATE,
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Subjects (Dersler)
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE,
    exam_type VARCHAR(10) CHECK (exam_type IN ('TYT', 'AYT', 'YDT')),
    is_active BOOLEAN DEFAULT TRUE
);

-- Topics (Konular)
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES subjects(id),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50),
    difficulty_avg DECIMAL(3,2) DEFAULT 0
);

-- Subtopics (Alt Konular)
CREATE TABLE IF NOT EXISTS subtopics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID REFERENCES topics(id),
    name VARCHAR(200) NOT NULL
);

-- Questions (Sorular)
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(50) UNIQUE,
    stem TEXT NOT NULL,
    stem_image_url TEXT,
    options JSONB NOT NULL,
    correct_option CHAR(1) NOT NULL CHECK (correct_option IN ('A','B','C','D','E')),
    explanation TEXT,
    difficulty DECIMAL(5,4) DEFAULT 0,
    discrimination DECIMAL(5,4) DEFAULT 1,
    guessing DECIMAL(4,3) DEFAULT 0.25,
    irt_calibrated BOOLEAN DEFAULT FALSE,
    subject_id UUID REFERENCES subjects(id),
    topic_id UUID REFERENCES topics(id),
    subtopic_id UUID REFERENCES subtopics(id),
    source VARCHAR(100),
    year SMALLINT,
    tags TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Answer History
CREATE TABLE IF NOT EXISTS answer_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    selected_option CHAR(1) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    fsrs_rating SMALLINT CHECK (fsrs_rating BETWEEN 1 AND 4),
    session_id UUID,
    exam_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- FSRS State
CREATE TABLE IF NOT EXISTS user_item_fsrs (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    stability DECIMAL(10,4) DEFAULT 1.0,
    difficulty DECIMAL(4,2) DEFAULT 5.0,
    due_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_review TIMESTAMPTZ,
    scheduled_days INTEGER DEFAULT 0,
    elapsed_days INTEGER DEFAULT 0,
    state SMALLINT DEFAULT 0,
    reps INTEGER DEFAULT 0,
    lapses INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, question_id)
);

-- Achievements
CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url TEXT,
    xp_reward INTEGER DEFAULT 0,
    criteria JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- User Achievements
CREATE TABLE IF NOT EXISTS user_achievements (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID REFERENCES achievements(id),
    earned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, achievement_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic_id);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_answer_history_user ON answer_history(user_id);
CREATE INDEX IF NOT EXISTS idx_fsrs_due ON user_item_fsrs(user_id, due_date);
