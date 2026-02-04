-- Migration: Create exams table
-- Created: 2025-10-28
-- Priority: CRITICAL
-- Description: Core exam sessions and attempts table

CREATE TABLE IF NOT EXISTS exams (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exam_type VARCHAR(50) NOT NULL CHECK (exam_type IN ('TYT', 'AYT', 'YDT', 'YKS_MOCK', 'DIAGNOSTIC', 'FORMATIVE')),
    exam_name VARCHAR(255),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'paused', 'completed', 'abandoned', 'auto_submitted')),
    total_questions INTEGER DEFAULT 0,
    answered_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    wrong_answers INTEGER DEFAULT 0,
    empty_answers INTEGER DEFAULT 0,
    net_score DECIMAL(10, 2),
    time_limit_minutes INTEGER,
    time_spent_seconds INTEGER DEFAULT 0,
    completion_percentage DECIMAL(5, 2),
    difficulty_level VARCHAR(50),
    subject_filter JSONB,
    exam_config JSONB DEFAULT '{}'::jsonb,
    performance_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_exams_user_id ON exams(user_id);
CREATE INDEX IF NOT EXISTS idx_exams_status ON exams(status);
CREATE INDEX IF NOT EXISTS idx_exams_exam_type ON exams(exam_type);
CREATE INDEX IF NOT EXISTS idx_exams_start_time ON exams(start_time);
CREATE INDEX IF NOT EXISTS idx_exams_created_at ON exams(created_at);
CREATE INDEX IF NOT EXISTS idx_exams_user_status ON exams(user_id, status);
CREATE INDEX IF NOT EXISTS idx_exams_user_exam_type ON exams(user_id, exam_type);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_exams_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_exams_updated_at
    BEFORE UPDATE ON exams
    FOR EACH ROW
    EXECUTE FUNCTION update_exams_updated_at();

-- Comments
COMMENT ON TABLE exams IS 'Exam sessions and student attempts';
COMMENT ON COLUMN exams.session_id IS 'Unique exam session identifier';
COMMENT ON COLUMN exams.user_id IS 'Student taking the exam';
COMMENT ON COLUMN exams.exam_type IS 'Type of exam (TYT, AYT, YDT, etc.)';
COMMENT ON COLUMN exams.status IS 'Current status of exam session';
COMMENT ON COLUMN exams.net_score IS 'Net score (correct - wrong/4)';
COMMENT ON COLUMN exams.performance_data IS 'Detailed performance analytics (JSON)';
