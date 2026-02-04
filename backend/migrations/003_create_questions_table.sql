-- Migration: Create questions table
-- Created: 2025-10-28
-- Priority: CRITICAL
-- Description: Question bank with IRT parameters and metadata

CREATE TABLE IF NOT EXISTS questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject VARCHAR(100) NOT NULL,
    topic VARCHAR(255),
    subtopic VARCHAR(255),
    difficulty VARCHAR(50) CHECK (difficulty IN ('kolay', 'orta', 'zor')),
    exam_type VARCHAR(50) CHECK (exam_type IN ('TYT', 'AYT', 'YDT', 'YKS_MOCK', 'DIAGNOSTIC')),
    stem TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_answer VARCHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D', 'E')),
    explanation TEXT,
    solution_steps JSONB,
    bloom_level VARCHAR(50) CHECK (bloom_level IN ('hatırlama', 'anlama', 'uygulama', 'analiz', 'sentez', 'değerlendirme')),
    kazanim_codes JSONB DEFAULT '[]'::jsonb,
    keywords JSONB DEFAULT '[]'::jsonb,

    -- IRT (Item Response Theory) Parameters
    irt_discrimination DECIMAL(10, 6),  -- 'a' parameter (0.5 - 2.5)
    irt_difficulty DECIMAL(10, 6),      -- 'b' parameter (-3 to +3)
    irt_guessing DECIMAL(5, 4) DEFAULT 0.25,  -- 'c' parameter (typically 0.25 for 4 options)

    -- Question Usage Statistics
    times_used INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    times_wrong INTEGER DEFAULT 0,
    times_empty INTEGER DEFAULT 0,
    average_time_seconds DECIMAL(10, 2),

    -- Status and Metadata
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'archived', 'deprecated')),
    quality_score DECIMAL(5, 2),
    author_id UUID,
    verified_by UUID,
    verified_at TIMESTAMP,
    image_url TEXT,
    video_solution_url TEXT,
    source VARCHAR(255),
    year INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject);
CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_exam_type ON questions(exam_type);
CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status);
CREATE INDEX IF NOT EXISTS idx_questions_bloom_level ON questions(bloom_level);
CREATE INDEX IF NOT EXISTS idx_questions_subject_difficulty ON questions(subject, difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_exam_type_subject ON questions(exam_type, subject);
CREATE INDEX IF NOT EXISTS idx_questions_irt_difficulty ON questions(irt_difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_quality_score ON questions(quality_score);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_questions_stem_fts ON questions USING gin(to_tsvector('turkish', stem));

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_questions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_questions_updated_at
    BEFORE UPDATE ON questions
    FOR EACH ROW
    EXECUTE FUNCTION update_questions_updated_at();

-- Comments
COMMENT ON TABLE questions IS 'Question bank with IRT parameters';
COMMENT ON COLUMN questions.question_id IS 'Unique question identifier';
COMMENT ON COLUMN questions.stem IS 'Question text/prompt';
COMMENT ON COLUMN questions.options IS 'Answer options (JSON array)';
COMMENT ON COLUMN questions.irt_discrimination IS 'IRT discrimination parameter (a)';
COMMENT ON COLUMN questions.irt_difficulty IS 'IRT difficulty parameter (b)';
COMMENT ON COLUMN questions.irt_guessing IS 'IRT guessing parameter (c)';
COMMENT ON COLUMN questions.quality_score IS 'Question quality rating (0-10)';
