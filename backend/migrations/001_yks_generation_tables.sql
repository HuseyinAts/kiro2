-- YKS Soru Üretim Tabloları Migration
-- Task 9: pgvector extension + YKS tabloları
-- Çalıştırma: psql -h localhost -p 5434 -U kiro2_user -d kiro2 -f 001_yks_generation_tables.sql

BEGIN;

-- 1. pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Generation runs (audit trail)
CREATE TABLE IF NOT EXISTS yks_generation_runs (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    exam_type VARCHAR(20) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    topic VARCHAR(200),
    target_difficulty VARCHAR(20),
    target_solo VARCHAR(30),
    target_count INTEGER DEFAULT 1,
    model_name VARCHAR(100) NOT NULL,
    model_params JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    generated_count INTEGER DEFAULT 0,
    accepted_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DOUBLE PRECISION DEFAULT 0.0,
    duration_seconds DOUBLE PRECISION DEFAULT 0.0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_genrun_status ON yks_generation_runs(status);
CREATE INDEX IF NOT EXISTS idx_genrun_exam ON yks_generation_runs(exam_type);
CREATE INDEX IF NOT EXISTS idx_genrun_created ON yks_generation_runs(created_at);

-- 3. Generated questions
CREATE TABLE IF NOT EXISTS yks_generated_questions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    generation_run_id VARCHAR NOT NULL REFERENCES yks_generation_runs(id) ON DELETE CASCADE,
    question_bank_id VARCHAR REFERENCES question_bank(id) ON DELETE SET NULL,
    question_text TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_answer VARCHAR(1) NOT NULL CHECK (correct_answer IN ('A','B','C','D','E')),
    explanation TEXT,
    exam_type VARCHAR(20) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    topic VARCHAR(200),
    solo_label VARCHAR(30),
    solo_confidence DOUBLE PRECISION,
    marzano_label VARCHAR(30),
    marzano_confidence DOUBLE PRECISION,
    bloom_level INTEGER,
    irt_difficulty DOUBLE PRECISION,
    irt_discrimination DOUBLE PRECISION,
    irt_guessing DOUBLE PRECISION,
    quality_score DOUBLE PRECISION DEFAULT 0.0 CHECK (quality_score >= 0 AND quality_score <= 100),
    judge_verdict VARCHAR(20),
    judge_reasoning TEXT,
    copy_risk_score DOUBLE PRECISION DEFAULT 0.0 CHECK (copy_risk_score >= 0 AND copy_risk_score <= 1),
    is_accepted BOOLEAN DEFAULT FALSE,
    is_reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_genq_run ON yks_generated_questions(generation_run_id);
CREATE INDEX IF NOT EXISTS idx_genq_exam ON yks_generated_questions(exam_type);
CREATE INDEX IF NOT EXISTS idx_genq_solo ON yks_generated_questions(solo_label);
CREATE INDEX IF NOT EXISTS idx_genq_accepted ON yks_generated_questions(is_accepted);
CREATE INDEX IF NOT EXISTS idx_genq_quality ON yks_generated_questions(quality_score);

-- 4. Question embeddings (pgvector)
CREATE TABLE IF NOT EXISTS yks_question_embeddings (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    generated_question_id VARCHAR REFERENCES yks_generated_questions(id) ON DELETE CASCADE,
    question_bank_id VARCHAR REFERENCES question_bank(id) ON DELETE CASCADE,
    embedding vector(768) NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    embedding_dim INTEGER DEFAULT 768,
    text_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(text_hash, embedding_model)
);

CREATE INDEX IF NOT EXISTS idx_emb_gen_q ON yks_question_embeddings(generated_question_id);
CREATE INDEX IF NOT EXISTS idx_emb_bank_q ON yks_question_embeddings(question_bank_id);

-- HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_emb_hnsw ON yks_question_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- 5. Human feedback
CREATE TABLE IF NOT EXISTS yks_human_feedback (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    question_id VARCHAR NOT NULL REFERENCES yks_generated_questions(id) ON DELETE CASCADE,
    reviewer_id VARCHAR REFERENCES users(id) ON DELETE SET NULL,
    verdict VARCHAR(20) NOT NULL,
    quality_rating INTEGER NOT NULL CHECK (quality_rating >= 1 AND quality_rating <= 5),
    difficulty_rating INTEGER CHECK (difficulty_rating >= 1 AND difficulty_rating <= 5),
    comments TEXT,
    suggested_edits JSONB,
    issues JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fb_question ON yks_human_feedback(question_id);
CREATE INDEX IF NOT EXISTS idx_fb_verdict ON yks_human_feedback(verdict);

COMMIT;
