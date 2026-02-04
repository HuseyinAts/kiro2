-- Migration: Make correct_answer nullable
-- Created: 2025-11-05
-- Description: Allow questions without answers (e.g., when answer key not available yet)

ALTER TABLE questions
ALTER COLUMN correct_answer DROP NOT NULL;

COMMENT ON COLUMN questions.correct_answer IS 'Correct answer (A-E), nullable for questions without answer key';
