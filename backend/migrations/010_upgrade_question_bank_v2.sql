-- Migration 010: Upgrade Question Bank to v2.0
-- Next-Gen Features: IRT, Knowledge Graph, Plagiarism Detection
-- Date: 2025-11-05

-- ============================================================================
-- PHASE 0: CREATE MIGRATION HISTORY TABLE IF NOT EXISTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS migration_history (
    version VARCHAR(10) PRIMARY KEY,
    description TEXT,
    executed_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- PHASE 1: ADD NEW COLUMNS TO EXISTING TABLES
-- ============================================================================

-- Add IRT parameters (Item Response Theory)
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS irt_discrimination FLOAT DEFAULT 1.0
    CHECK (irt_discrimination >= 0.5 AND irt_discrimination <= 2.5);

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS irt_guessing FLOAT DEFAULT 0.25
    CHECK (irt_guessing >= 0.0 AND irt_guessing <= 0.5);

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS irt_confidence FLOAT
    CHECK (irt_confidence >= 0.0 AND irt_confidence <= 1.0);

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS calibration_sample_size INT DEFAULT 0;

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS last_calibration_date TIMESTAMP;

-- Add plagiarism detection score
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS plagiarism_score FLOAT DEFAULT 0.0
    CHECK (plagiarism_score >= 0.0 AND plagiarism_score <= 1.0);

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS plagiarism_check_date TIMESTAMP;

-- Add knowledge graph reference
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS knowledge_graph_id VARCHAR(100);

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS prerequisite_topics TEXT[];

-- Add quality metrics
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS ai_validation_confidence FLOAT
    CHECK (ai_validation_confidence >= 0.0 AND ai_validation_confidence <= 1.0);

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS expert_review_score INT
    CHECK (expert_review_score >= 0 AND expert_review_score <= 100);

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS expert_reviewer_id UUID;

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS review_date TIMESTAMP;

-- Add Bloom's taxonomy
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS bloom_level VARCHAR(20)
    CHECK (bloom_level IN ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create'));

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS cognitive_skills TEXT[];

-- Add usage statistics
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS usage_count INT DEFAULT 0;

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS correct_rate FLOAT;

ALTER TABLE sorular ADD COLUMN IF NOT EXISTS avg_response_time INT; -- seconds

-- Add status tracking
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending_review'
    CHECK (status IN ('pending_review', 'approved', 'rejected', 'needs_revision', 'archived'));

-- ============================================================================
-- PHASE 2: CREATE NEW TABLES FOR V2 FEATURES
-- ============================================================================

-- CAT (Computer Adaptive Testing) Sessions
CREATE TABLE IF NOT EXISTS cat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES kullanicilar(id) ON DELETE CASCADE,
    session_id VARCHAR(100) UNIQUE NOT NULL,

    -- Session metadata
    konu VARCHAR(100) NOT NULL,
    sinav_tipi VARCHAR(10),
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,

    -- Ability tracking
    initial_theta FLOAT DEFAULT 0.0,
    final_theta FLOAT,
    final_sem FLOAT, -- Standard Error of Measurement
    confidence_interval_lower FLOAT,
    confidence_interval_upper FLOAT,

    -- Session stats
    questions_answered INT DEFAULT 0,
    correct_answers INT DEFAULT 0,
    total_time_seconds INT,

    -- Status
    is_complete BOOLEAN DEFAULT FALSE,
    completion_reason VARCHAR(50), -- 'target_sem', 'max_questions', 'time_limit'

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cat_sessions_student ON cat_sessions(student_id);
CREATE INDEX idx_cat_sessions_session_id ON cat_sessions(session_id);
CREATE INDEX idx_cat_sessions_complete ON cat_sessions(is_complete);

-- CAT Response History
CREATE TABLE IF NOT EXISTS cat_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES cat_sessions(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES sorular(id) ON DELETE CASCADE,

    -- Response data
    is_correct BOOLEAN NOT NULL,
    response_time_seconds INT NOT NULL,
    selected_answer VARCHAR(1),

    -- IRT parameters at time of question
    irt_difficulty FLOAT NOT NULL,
    irt_discrimination FLOAT NOT NULL,

    -- Ability estimate after this response
    theta_estimate FLOAT NOT NULL,
    sem_estimate FLOAT NOT NULL,

    -- Fisher Information
    information_value FLOAT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cat_responses_session ON cat_responses(session_id);
CREATE INDEX idx_cat_responses_question ON cat_responses(question_id);

-- Expert Review Tasks (HITL Workflow)
CREATE TABLE IF NOT EXISTS expert_review_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(100) UNIQUE NOT NULL,
    question_id UUID NOT NULL REFERENCES sorular(id) ON DELETE CASCADE,

    -- Assignment
    assigned_expert_id UUID REFERENCES kullanicilar(id) ON DELETE SET NULL,
    assigned_time TIMESTAMP,
    completed_time TIMESTAMP,

    -- Task metadata
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    expertise_match FLOAT CHECK (expertise_match >= 0.0 AND expertise_match <= 1.0),
    estimated_time_minutes INT DEFAULT 3,
    incentive_points INT DEFAULT 10,

    -- AI validation result (JSON)
    ai_validation_result JSONB,

    -- Expert decision
    decision VARCHAR(20) CHECK (decision IN ('approve', 'reject', 'needs_revision', 'escalate')),
    pedagogy_score INT CHECK (pedagogy_score >= 0 AND pedagogy_score <= 100),
    comments TEXT,
    suggested_changes JSONB,
    review_time_seconds INT,

    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'completed', 'escalated')),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_review_tasks_expert ON expert_review_tasks(assigned_expert_id);
CREATE INDEX idx_review_tasks_question ON expert_review_tasks(question_id);
CREATE INDEX idx_review_tasks_status ON expert_review_tasks(status);
CREATE INDEX idx_review_tasks_priority ON expert_review_tasks(priority);

-- Expert Profiles
CREATE TABLE IF NOT EXISTS expert_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES kullanicilar(id) ON DELETE CASCADE,

    -- Expertise
    expertise_level VARCHAR(20) CHECK (expertise_level IN ('junior', 'senior', 'master')),
    specializations TEXT[] NOT NULL,

    -- Performance metrics
    total_reviews INT DEFAULT 0,
    approval_rate FLOAT DEFAULT 0.0,
    average_review_time FLOAT DEFAULT 0.0, -- seconds
    quality_score FLOAT DEFAULT 0.0 CHECK (quality_score >= 0.0 AND quality_score <= 100.0),

    -- Gamification
    points INT DEFAULT 0,
    badges TEXT[],
    leaderboard_rank INT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_expert_profiles_user ON expert_profiles(user_id);
CREATE INDEX idx_expert_profiles_active ON expert_profiles(is_active);
CREATE INDEX idx_expert_profiles_rank ON expert_profiles(leaderboard_rank);

-- Knowledge Graph Relationships
CREATE TABLE IF NOT EXISTS knowledge_graph_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationship
    source_node_id VARCHAR(100) NOT NULL,
    source_node_type VARCHAR(50) NOT NULL, -- 'question', 'topic', 'kazanim', 'bloom_level'
    target_node_id VARCHAR(100) NOT NULL,
    target_node_type VARCHAR(50) NOT NULL,

    -- Relationship type
    relation_type VARCHAR(50) NOT NULL, -- 'tests', 'prerequisite_of', 'related_to', 'difficulty_similar'
    weight FLOAT DEFAULT 1.0,

    -- Metadata
    metadata JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kg_source ON knowledge_graph_relationships(source_node_id, source_node_type);
CREATE INDEX idx_kg_target ON knowledge_graph_relationships(target_node_id, target_node_type);
CREATE INDEX idx_kg_relation ON knowledge_graph_relationships(relation_type);

-- ============================================================================
-- PHASE 3: CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- IRT-based question selection (for CAT)
CREATE INDEX IF NOT EXISTS idx_sorular_irt_difficulty ON sorular(irt_difficulty);
CREATE INDEX IF NOT EXISTS idx_sorular_irt_discrimination ON sorular(irt_discrimination);

-- Quality filtering
CREATE INDEX IF NOT EXISTS idx_sorular_status ON sorular(status);
CREATE INDEX IF NOT EXISTS idx_sorular_ai_confidence ON sorular(ai_validation_confidence);
CREATE INDEX IF NOT EXISTS idx_sorular_expert_score ON sorular(expert_review_score);

-- Knowledge graph queries
CREATE INDEX IF NOT EXISTS idx_sorular_kg_id ON sorular(knowledge_graph_id);
CREATE INDEX IF NOT EXISTS idx_sorular_bloom ON sorular(bloom_level);

-- Plagiarism detection
CREATE INDEX IF NOT EXISTS idx_sorular_plagiarism ON sorular(plagiarism_score);

-- Usage analytics
CREATE INDEX IF NOT EXISTS idx_sorular_usage_count ON sorular(usage_count);
CREATE INDEX IF NOT EXISTS idx_sorular_correct_rate ON sorular(correct_rate);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sorular_active_quality ON sorular(aktif, status, ai_validation_confidence)
    WHERE aktif = TRUE AND status = 'approved';

CREATE INDEX IF NOT EXISTS idx_sorular_cat_selection ON sorular(konu, irt_difficulty, aktif, status)
    WHERE aktif = TRUE AND status = 'approved';

-- ============================================================================
-- PHASE 4: UPDATE EXISTING DATA WITH DEFAULT VALUES
-- ============================================================================

-- Set default IRT parameters for existing questions
UPDATE sorular
SET
    irt_difficulty = CASE
        WHEN zorluk = 'easy' THEN 0.3
        WHEN zorluk = 'medium' THEN 0.5
        WHEN zorluk = 'hard' THEN 0.7
        ELSE 0.5
    END,
    irt_discrimination = 1.0,
    irt_guessing = 0.25,
    calibration_sample_size = 0,
    plagiarism_score = 0.0,
    status = 'approved' -- Existing questions assumed approved
WHERE irt_difficulty IS NULL;

-- Set default Bloom level based on existing difficulty
UPDATE sorular
SET bloom_level = CASE
        WHEN zorluk = 'easy' THEN 'remember'
        WHEN zorluk = 'medium' THEN 'apply'
        WHEN zorluk = 'hard' THEN 'analyze'
        ELSE 'apply'
    END
WHERE bloom_level IS NULL;

-- ============================================================================
-- PHASE 5: ADD TRIGGERS FOR AUTO-UPDATES
-- ============================================================================

-- Auto-update timestamp trigger for cat_sessions
CREATE OR REPLACE FUNCTION update_cat_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cat_session_update
    BEFORE UPDATE ON cat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_cat_session_timestamp();

-- Auto-update timestamp trigger for expert_review_tasks
CREATE TRIGGER trigger_review_task_update
    BEFORE UPDATE ON expert_review_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_cat_session_timestamp();

-- Auto-update timestamp trigger for expert_profiles
CREATE TRIGGER trigger_expert_profile_update
    BEFORE UPDATE ON expert_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_cat_session_timestamp();

-- ============================================================================
-- PHASE 6: CREATE VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: High-quality questions ready for CAT
CREATE OR REPLACE VIEW vw_cat_ready_questions AS
SELECT
    id,
    metin,
    secenekler,
    dogru_cevap,
    konu,
    alt_konu,
    irt_difficulty,
    irt_discrimination,
    irt_guessing,
    bloom_level,
    usage_count,
    correct_rate
FROM sorular
WHERE
    aktif = TRUE
    AND status = 'approved'
    AND irt_confidence IS NOT NULL
    AND irt_confidence > 0.7
    AND calibration_sample_size >= 30
    AND plagiarism_score < 0.85;

-- View: Questions needing expert review
CREATE OR REPLACE VIEW vw_needs_expert_review AS
SELECT
    s.id,
    s.metin,
    s.konu,
    s.ai_validation_confidence,
    s.plagiarism_score,
    s.status,
    s.olusturma_tarihi
FROM sorular s
LEFT JOIN expert_review_tasks t ON s.id = t.question_id
WHERE
    s.status = 'pending_review'
    AND (s.ai_validation_confidence < 0.75 OR s.plagiarism_score > 0.75)
    AND t.id IS NULL -- Not yet assigned to a task
ORDER BY
    CASE
        WHEN s.ai_validation_confidence < 0.60 THEN 1 -- Urgent
        WHEN s.ai_validation_confidence < 0.75 THEN 2 -- High priority
        ELSE 3
    END,
    s.olusturma_tarihi DESC;

-- View: Expert leaderboard
CREATE OR REPLACE VIEW vw_expert_leaderboard AS
SELECT
    ep.id,
    u.ad || ' ' || u.soyad AS expert_name,
    ep.expertise_level,
    ep.total_reviews,
    ep.approval_rate,
    ep.quality_score,
    ep.points,
    ep.leaderboard_rank,
    array_length(ep.badges, 1) AS badge_count
FROM expert_profiles ep
JOIN kullanicilar u ON ep.user_id = u.id
WHERE ep.is_active = TRUE
ORDER BY ep.points DESC, ep.quality_score DESC;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration
INSERT INTO migration_history (version, description, executed_at)
VALUES ('010', 'Question Bank v2.0 - IRT, CAT, Knowledge Graph, HITL', NOW())
ON CONFLICT (version) DO NOTHING;

-- Summary
DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Migration 010 completed successfully!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Added features:';
    RAISE NOTICE '  - IRT parameters (difficulty, discrimination, guessing)';
    RAISE NOTICE '  - CAT sessions and response tracking';
    RAISE NOTICE '  - Expert review workflow (HITL)';
    RAISE NOTICE '  - Knowledge graph relationships';
    RAISE NOTICE '  - Plagiarism detection scores';
    RAISE NOTICE '  - Blooms taxonomy classification';
    RAISE NOTICE '  - Quality metrics and analytics';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'New tables: 6';
    RAISE NOTICE 'New indexes: 15+';
    RAISE NOTICE 'New views: 3';
    RAISE NOTICE 'New triggers: 3';
    RAISE NOTICE '============================================================';
END $$;
