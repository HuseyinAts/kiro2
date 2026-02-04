-- Task 100: Video Analytics Tables Migration
-- Creates tables for video watch tracking, notes, and bookmarks

-- ============================================================
-- Task 100.1: Video Watch Sessions
-- ============================================================

CREATE TABLE IF NOT EXISTS video_watch_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session info
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(100) NOT NULL,
    video_source VARCHAR(20) NOT NULL,

    -- Watch metrics
    watch_duration INTEGER DEFAULT 0,
    video_duration INTEGER NOT NULL,
    completion_percentage FLOAT DEFAULT 0.0,

    -- Progress tracking
    last_position INTEGER DEFAULT 0,
    watched_segments JSONB DEFAULT '[]'::jsonb,

    -- Engagement metrics
    pause_count INTEGER DEFAULT 0,
    seek_count INTEGER DEFAULT 0,
    playback_speed FLOAT DEFAULT 1.0,

    -- Drop-off analysis
    dropped_at INTEGER,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    CONSTRAINT check_completion_percentage CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    CONSTRAINT check_playback_speed CHECK (playback_speed > 0)
);

CREATE INDEX idx_video_watch_sessions_user ON video_watch_sessions(user_id);
CREATE INDEX idx_video_watch_sessions_video ON video_watch_sessions(video_id);
CREATE INDEX idx_video_watch_sessions_started ON video_watch_sessions(started_at);
CREATE INDEX idx_video_watch_sessions_user_video ON video_watch_sessions(user_id, video_id);


-- ============================================================
-- Task 100.2: Completion Milestones
-- ============================================================

CREATE TABLE IF NOT EXISTS video_completion_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User and video
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(100) NOT NULL,
    video_source VARCHAR(20) NOT NULL,

    -- Milestone info
    milestone_percentage INTEGER NOT NULL,
    achieved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Badge awarded
    badge_awarded BOOLEAN DEFAULT FALSE,
    badge_id UUID REFERENCES user_badges(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT check_milestone_percentage CHECK (milestone_percentage IN (25, 50, 75, 100)),
    CONSTRAINT unique_user_video_milestone UNIQUE (user_id, video_id, milestone_percentage)
);

CREATE INDEX idx_video_completion_milestones_user ON video_completion_milestones(user_id);
CREATE INDEX idx_video_completion_milestones_video ON video_completion_milestones(video_id);


-- ============================================================
-- Task 100.3: Timestamped Notes
-- ============================================================

CREATE TABLE IF NOT EXISTS video_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User and video
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(100) NOT NULL,
    video_source VARCHAR(20) NOT NULL,

    -- Session reference
    session_id UUID REFERENCES video_watch_sessions(id) ON DELETE SET NULL,

    -- Note content
    content TEXT NOT NULL,
    timestamp INTEGER NOT NULL,

    -- Note metadata
    is_important BOOLEAN DEFAULT FALSE,
    tags VARCHAR(50)[],

    -- Note context
    video_caption TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_timestamp CHECK (timestamp >= 0)
);

CREATE INDEX idx_video_notes_user ON video_notes(user_id);
CREATE INDEX idx_video_notes_video ON video_notes(video_id);
CREATE INDEX idx_video_notes_created ON video_notes(created_at);
CREATE INDEX idx_video_notes_user_video ON video_notes(user_id, video_id);
CREATE INDEX idx_video_notes_timestamp ON video_notes(video_id, timestamp);

-- Full-text search on note content
CREATE INDEX idx_video_notes_content_search ON video_notes USING gin(to_tsvector('turkish', content));


-- ============================================================
-- Task 100.4: Video Bookmarks
-- ============================================================

CREATE TABLE IF NOT EXISTS video_bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User and video
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(100) NOT NULL,
    video_source VARCHAR(20) NOT NULL,

    -- Session reference
    session_id UUID REFERENCES video_watch_sessions(id) ON DELETE SET NULL,

    -- Bookmark info
    timestamp INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- Bookmark type
    bookmark_type VARCHAR(20) DEFAULT 'manual',

    -- Sharing
    is_public BOOLEAN DEFAULT FALSE,
    share_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_bookmark_timestamp CHECK (timestamp >= 0),
    CONSTRAINT check_bookmark_type CHECK (bookmark_type IN ('manual', 'key_moment', 'auto_generated'))
);

CREATE INDEX idx_video_bookmarks_user ON video_bookmarks(user_id);
CREATE INDEX idx_video_bookmarks_video ON video_bookmarks(video_id);
CREATE INDEX idx_video_bookmarks_created ON video_bookmarks(created_at);
CREATE INDEX idx_video_bookmarks_public ON video_bookmarks(video_id, is_public);
CREATE INDEX idx_video_bookmarks_user_video ON video_bookmarks(user_id, video_id);
CREATE INDEX idx_video_bookmarks_timestamp ON video_bookmarks(video_id, timestamp);


-- ============================================================
-- Analytics Summary
-- ============================================================

CREATE TABLE IF NOT EXISTS video_analytics_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User and period
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_type VARCHAR(10) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Watch metrics
    total_videos_watched INTEGER DEFAULT 0,
    total_watch_time INTEGER DEFAULT 0,
    total_videos_completed INTEGER DEFAULT 0,
    average_completion_rate FLOAT DEFAULT 0.0,

    -- Engagement metrics
    total_notes INTEGER DEFAULT 0,
    total_bookmarks INTEGER DEFAULT 0,
    average_playback_speed FLOAT DEFAULT 1.0,

    -- Breakdowns
    source_breakdown JSONB DEFAULT '{}'::jsonb,
    subject_breakdown JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_period_type CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    CONSTRAINT unique_user_period UNIQUE (user_id, period_type, period_start)
);

CREATE INDEX idx_video_analytics_summary_user ON video_analytics_summary(user_id);
CREATE INDEX idx_video_analytics_summary_period ON video_analytics_summary(period_start);


-- ============================================================
-- Update Triggers
-- ============================================================

-- Update last_updated on video_watch_sessions
CREATE OR REPLACE FUNCTION update_video_watch_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_video_watch_session_timestamp
BEFORE UPDATE ON video_watch_sessions
FOR EACH ROW
EXECUTE FUNCTION update_video_watch_session_timestamp();


-- Update updated_at on video_notes
CREATE OR REPLACE FUNCTION update_video_note_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_video_note_timestamp
BEFORE UPDATE ON video_notes
FOR EACH ROW
EXECUTE FUNCTION update_video_note_timestamp();


-- Update updated_at on video_bookmarks
CREATE OR REPLACE FUNCTION update_video_bookmark_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_video_bookmark_timestamp
BEFORE UPDATE ON video_bookmarks
FOR EACH ROW
EXECUTE FUNCTION update_video_bookmark_timestamp();


-- Update updated_at on video_analytics_summary
CREATE OR REPLACE FUNCTION update_video_analytics_summary_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_video_analytics_summary_timestamp
BEFORE UPDATE ON video_analytics_summary
FOR EACH ROW
EXECUTE FUNCTION update_video_analytics_summary_timestamp();


-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE video_watch_sessions IS 'Task 100.1: Tracks individual video watch sessions with engagement metrics';
COMMENT ON TABLE video_completion_milestones IS 'Task 100.2: Tracks completion milestones (25%, 50%, 75%, 100%)';
COMMENT ON TABLE video_notes IS 'Task 100.3: Timestamped notes taken during video playback';
COMMENT ON TABLE video_bookmarks IS 'Task 100.4: Bookmarks for key moments in videos';
COMMENT ON TABLE video_analytics_summary IS 'Aggregated analytics summaries (daily/weekly/monthly)';
