-- Migration: Create exam_answers table
-- Created: 2025-10-28
-- Priority: CRITICAL
-- Description: Student answers for exam questions

CREATE TABLE IF NOT EXISTS exam_answers (
    answer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES exams(session_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    given_answer VARCHAR(1) CHECK (given_answer IN ('A', 'B', 'C', 'D', 'E', NULL)),
    is_correct BOOLEAN,
    is_flagged BOOLEAN DEFAULT FALSE,
    time_spent_seconds INTEGER DEFAULT 0,
    confidence_level INTEGER CHECK (confidence_level BETWEEN 1 AND 5),
    answer_order INTEGER,
    answered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure one answer per question per session
    UNIQUE(session_id, question_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_exam_answers_session_id ON exam_answers(session_id);
CREATE INDEX IF NOT EXISTS idx_exam_answers_question_id ON exam_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_exam_answers_user_id ON exam_answers(user_id);
CREATE INDEX IF NOT EXISTS idx_exam_answers_is_correct ON exam_answers(is_correct);
CREATE INDEX IF NOT EXISTS idx_exam_answers_session_question ON exam_answers(session_id, question_id);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_exam_answers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_exam_answers_updated_at
    BEFORE UPDATE ON exam_answers
    FOR EACH ROW
    EXECUTE FUNCTION update_exam_answers_updated_at();

-- Comments
COMMENT ON TABLE exam_answers IS 'Student answers for exam questions';
COMMENT ON COLUMN exam_answers.given_answer IS 'Student selected answer (A-E or NULL for empty)';
COMMENT ON COLUMN exam_answers.is_correct IS 'Whether answer is correct';
COMMENT ON COLUMN exam_answers.is_flagged IS 'Student flagged for review';
COMMENT ON COLUMN exam_answers.confidence_level IS 'Student confidence (1-5)';
