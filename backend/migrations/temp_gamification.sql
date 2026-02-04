-- Migration: Create gamification tables
-- Created: 2025-10-28
-- Priority: HIGH (Phase 2)
-- Description: Badges, leaderboards, experience points, streaks

-- User Badges Table
CREATE TABLE IF NOT EXISTS user_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES kullanicilar(id) ON DELETE CASCADE,
    badge_code VARCHAR(100) NOT NULL,
    badge_name VARCHAR(255) NOT NULL,
    badge_description TEXT,
    badge_category VARCHAR(100),
    badge_tier VARCHAR(50) CHECK (badge_tier IN ('bronze', 'silver', 'gold', 'platinum', 'diamond')),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress_current INTEGER DEFAULT 0,
    progress_required INTEGER,
    is_displayed BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,

    UNIQUE(user_id, badge_code)
);

-- Leaderboard Entries Table
CREATE TABLE IF NOT EXISTS leaderboard_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES kullanicilar(id) ON DELETE CASCADE,
    leaderboard_type VARCHAR(100) NOT NULL,
    score DECIMAL(15, 2) NOT NULL,
    rank INTEGER,
    period VARCHAR(50) CHECK (period IN ('daily', 'weekly', 'monthly', 'all_time')),
    subject VARCHAR(100),
    exam_type VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,

    UNIQUE(user_id, leaderboard_type, period)
);

-- Experience Points Table
CREATE TABLE IF NOT EXISTS experience_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES kullanicilar(id) ON DELETE CASCADE,
    points INTEGER DEFAULT 0 NOT NULL,
    level INTEGER DEFAULT 1 NOT NULL,
    points_to_next_level INTEGER,
    total_points_earned INTEGER DEFAULT 0,

    -- Experience categories
    exam_points INTEGER DEFAULT 0,
    study_points INTEGER DEFAULT 0,
    achievement_points INTEGER DEFAULT 0,
    social_points INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id)
);

-- Streak Tracking Table
CREATE TABLE IF NOT EXISTS streak_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES kullanicilar(id) ON DELETE CASCADE,
    streak_type VARCHAR(100) NOT NULL,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_activity_date DATE,
    streak_start_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, streak_type)
);

-- Point Transactions Table (Audit Trail)
CREATE TABLE IF NOT EXISTS point_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES kullanicilar(id) ON DELETE CASCADE,
    transaction_type VARCHAR(100) NOT NULL,
    points_change INTEGER NOT NULL,
    points_before INTEGER,
    points_after INTEGER,
    reason TEXT,
    source VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_badges_user_id ON user_badges(user_id);
CREATE INDEX IF NOT EXISTS idx_user_badges_category ON user_badges(badge_category);
CREATE INDEX IF NOT EXISTS idx_user_badges_earned_at ON user_badges(earned_at);

CREATE INDEX IF NOT EXISTS idx_leaderboard_type_period ON leaderboard_entries(leaderboard_type, period);
CREATE INDEX IF NOT EXISTS idx_leaderboard_rank ON leaderboard_entries(rank);
CREATE INDEX IF NOT EXISTS idx_leaderboard_score ON leaderboard_entries(score DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_updated_at ON leaderboard_entries(updated_at);

CREATE INDEX IF NOT EXISTS idx_experience_user_id ON experience_points(user_id);
CREATE INDEX IF NOT EXISTS idx_experience_level ON experience_points(level);
CREATE INDEX IF NOT EXISTS idx_experience_points ON experience_points(points DESC);

CREATE INDEX IF NOT EXISTS idx_streak_user_id ON streak_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_streak_type ON streak_tracking(streak_type);
CREATE INDEX IF NOT EXISTS idx_streak_active ON streak_tracking(is_active);

CREATE INDEX IF NOT EXISTS idx_point_transactions_user_id ON point_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_point_transactions_created_at ON point_transactions(created_at);

-- Triggers
CREATE OR REPLACE FUNCTION update_experience_points_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_experience_points_updated_at
    BEFORE UPDATE ON experience_points
    FOR EACH ROW
    EXECUTE FUNCTION update_experience_points_updated_at();

CREATE TRIGGER trigger_streak_tracking_updated_at
    BEFORE UPDATE ON streak_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_experience_points_updated_at();

-- Comments
COMMENT ON TABLE user_badges IS 'User earned badges and achievements';
COMMENT ON TABLE leaderboard_entries IS 'Leaderboard rankings by type and period';
COMMENT ON TABLE experience_points IS 'User experience points and levels';
COMMENT ON TABLE streak_tracking IS 'User activity streaks (daily, weekly, etc.)';
COMMENT ON TABLE point_transactions IS 'Audit trail for all point changes';

