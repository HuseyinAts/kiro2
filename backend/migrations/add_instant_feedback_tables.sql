-- Task 92: Instant Feedback System - Database Migration
-- DEHB desteği için seri takibi ve performans geçmişi tabloları

-- ============================================================================
-- 1. Create streak_tracking table
-- ============================================================================

CREATE TABLE IF NOT EXISTS streak_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Streak data
    current_streak INTEGER DEFAULT 0 NOT NULL,
    best_streak INTEGER DEFAULT 0 NOT NULL,

    -- Metadata
    streak_start_date TIMESTAMP WITH TIME ZONE,
    last_correct_answer TIMESTAMP WITH TIME ZONE,
    milestones_reached JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Constraints
    CONSTRAINT uq_streak_user UNIQUE (user_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_streak_user_id ON streak_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_streak_current ON streak_tracking(current_streak);
CREATE INDEX IF NOT EXISTS idx_streak_best ON streak_tracking(best_streak);

-- ============================================================================
-- 2. Create performance_history table
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Performance data
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    questions_answered INTEGER DEFAULT 1,
    correct_answers INTEGER DEFAULT 0,

    -- Context
    subject VARCHAR(100),
    difficulty VARCHAR(50),

    -- Streak at time of recording
    streak_at_time INTEGER DEFAULT 0,

    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_performance_user_id ON performance_history(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_recorded_at ON performance_history(recorded_at);
CREATE INDEX IF NOT EXISTS idx_performance_user_date ON performance_history(user_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_performance_subject ON performance_history(subject);

-- ============================================================================
-- 3. Create update trigger for streak_tracking
-- ============================================================================

CREATE OR REPLACE FUNCTION update_streak_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_streak_updated_at ON streak_tracking;
CREATE TRIGGER trigger_update_streak_updated_at
    BEFORE UPDATE ON streak_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_streak_updated_at();

-- ============================================================================
-- 4. Verification
-- ============================================================================

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Task 92 Instant Feedback tables migration completed successfully';
    RAISE NOTICE 'Tables created: streak_tracking, performance_history';
END $$;
