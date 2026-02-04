-- Migration: Create EBA TV and Khan Academy tables
-- Created: 2025-10-28
-- Priority: HIGH (Phase 2)
-- Description: EBA videos, Khan content, watch tracking

-- EBA Videos Table
CREATE TABLE IF NOT EXISTS eba_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    eba_video_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    subject VARCHAR(100),
    grade_level VARCHAR(50),
    topic VARCHAR(255),
    duration_seconds INTEGER,
    thumbnail_url TEXT,
    video_url TEXT,
    quality VARCHAR(50),
    kazanim_codes JSONB DEFAULT '[]'::jsonb,
    keywords JSONB DEFAULT '[]'::jsonb,
    view_count INTEGER DEFAULT 0,
    rating DECIMAL(3, 2),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Khan Academy Content Table
CREATE TABLE IF NOT EXISTS khan_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    khan_content_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content_type VARCHAR(100),
    subject VARCHAR(100),
    difficulty VARCHAR(50),
    duration_seconds INTEGER,
    url TEXT,
    thumbnail_url TEXT,
    progress_key VARCHAR(255),
    parent_content_id VARCHAR(255),
    keywords JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video Watch Sessions Table
CREATE TABLE IF NOT EXISTS video_watch_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(255) NOT NULL,
    video_source VARCHAR(50) CHECK (video_source IN ('eba', 'khan', 'youtube', 'custom')),
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    total_watch_time_seconds INTEGER DEFAULT 0,
    video_duration_seconds INTEGER,
    completion_rate DECIMAL(5, 2),
    max_position_reached INTEGER DEFAULT 0,
    pause_count INTEGER DEFAULT 0,
    seek_count INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Video Analytics Milestones Table
CREATE TABLE IF NOT EXISTS video_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    milestone_type VARCHAR(100) NOT NULL,
    milestone_name VARCHAR(255) NOT NULL,
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_count INTEGER,
    total_watch_time_seconds INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,

    UNIQUE(user_id, milestone_type, milestone_name)
);

-- Khan Academy OAuth Tokens Table
CREATE TABLE IF NOT EXISTS khan_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50),
    expires_at TIMESTAMP,
    scope TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id)
);

-- Khan Progress Sync Table
CREATE TABLE IF NOT EXISTS khan_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    khan_content_id VARCHAR(255) NOT NULL,
    progress_percentage DECIMAL(5, 2),
    completed BOOLEAN DEFAULT FALSE,
    time_spent_seconds INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,

    UNIQUE(user_id, khan_content_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_eba_videos_subject ON eba_videos(subject);
CREATE INDEX IF NOT EXISTS idx_eba_videos_grade_level ON eba_videos(grade_level);
CREATE INDEX IF NOT EXISTS idx_eba_videos_topic ON eba_videos(topic);
CREATE INDEX IF NOT EXISTS idx_eba_videos_active ON eba_videos(is_active);

CREATE INDEX IF NOT EXISTS idx_khan_content_subject ON khan_content(subject);
CREATE INDEX IF NOT EXISTS idx_khan_content_type ON khan_content(content_type);
CREATE INDEX IF NOT EXISTS idx_khan_content_difficulty ON khan_content(difficulty);

CREATE INDEX IF NOT EXISTS idx_video_watch_user_id ON video_watch_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_video_watch_source ON video_watch_sessions(video_source);
CREATE INDEX IF NOT EXISTS idx_video_watch_video_id ON video_watch_sessions(video_id);
CREATE INDEX IF NOT EXISTS idx_video_watch_start ON video_watch_sessions(session_start);

CREATE INDEX IF NOT EXISTS idx_video_milestones_user_id ON video_milestones(user_id);
CREATE INDEX IF NOT EXISTS idx_video_milestones_type ON video_milestones(milestone_type);

CREATE INDEX IF NOT EXISTS idx_khan_oauth_user_id ON khan_oauth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_khan_oauth_active ON khan_oauth_tokens(is_active);

CREATE INDEX IF NOT EXISTS idx_khan_progress_user_id ON khan_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_khan_progress_content_id ON khan_progress(khan_content_id);

-- Triggers
CREATE OR REPLACE FUNCTION update_video_tables_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_eba_videos_updated_at
    BEFORE UPDATE ON eba_videos
    FOR EACH ROW
    EXECUTE FUNCTION update_video_tables_updated_at();

CREATE TRIGGER trigger_khan_content_updated_at
    BEFORE UPDATE ON khan_content
    FOR EACH ROW
    EXECUTE FUNCTION update_video_tables_updated_at();

CREATE TRIGGER trigger_khan_oauth_updated_at
    BEFORE UPDATE ON khan_oauth_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_video_tables_updated_at();

-- Comments
COMMENT ON TABLE eba_videos IS 'EBA TV video catalog';
COMMENT ON TABLE khan_content IS 'Khan Academy content catalog';
COMMENT ON TABLE video_watch_sessions IS 'User video watch sessions (all sources)';
COMMENT ON TABLE video_milestones IS 'Video watching milestones and achievements';
COMMENT ON TABLE khan_oauth_tokens IS 'Khan Academy OAuth authentication tokens';
COMMENT ON TABLE khan_progress IS 'Khan Academy progress synchronization';
