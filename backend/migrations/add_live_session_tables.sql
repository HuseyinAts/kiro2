-- ============================================================
-- Task 108: Live Q&A Sessions Database Migration
-- ============================================================

-- Create enum types
CREATE TYPE session_status AS ENUM ('scheduled', 'live', 'ended', 'cancelled');
CREATE TYPE session_type AS ENUM ('one_on_one', 'group_session', 'webinar', 'study_group');
CREATE TYPE platform_type AS ENUM ('zoom', 'google_meet', 'jitsi', 'custom');
CREATE TYPE participant_role AS ENUM ('host', 'co_host', 'participant', 'observer');
CREATE TYPE recording_status AS ENUM ('recording', 'processing', 'ready', 'failed');
CREATE TYPE whiteboard_tool_type AS ENUM ('pen', 'eraser', 'text', 'shape', 'highlighter', 'equation');
CREATE TYPE screen_share_type AS ENUM ('entire_screen', 'window', 'application', 'whiteboard');

-- ============================================================
-- Task 108.1: Live Sessions Table
-- ============================================================

CREATE TABLE live_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    session_type session_type DEFAULT 'one_on_one',
    host_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES teacher_profiles(id),

    -- Scheduling
    scheduled_start TIMESTAMP WITH TIME ZONE NOT NULL,
    scheduled_end TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_start TIMESTAMP WITH TIME ZONE,
    actual_end TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,

    -- Status
    status session_status DEFAULT 'scheduled',

    -- Video Conference Integration (Task 108.1)
    platform platform_type DEFAULT 'zoom',
    meeting_id VARCHAR(100),
    meeting_password VARCHAR(100),
    meeting_url VARCHAR(500),
    join_url VARCHAR(500),
    host_url VARCHAR(500),

    -- Platform-specific data
    zoom_meeting_data JSONB DEFAULT '{}'::JSONB,
    meet_event_data JSONB DEFAULT '{}'::JSONB,

    -- Capacity
    max_participants INTEGER DEFAULT 50,
    current_participants INTEGER DEFAULT 0,

    -- Features
    allow_screen_share BOOLEAN DEFAULT TRUE,
    allow_whiteboard BOOLEAN DEFAULT TRUE,
    allow_recording BOOLEAN DEFAULT TRUE,
    allow_chat BOOLEAN DEFAULT TRUE,

    -- Recording (Task 108.4)
    is_recorded BOOLEAN DEFAULT FALSE,
    auto_record BOOLEAN DEFAULT FALSE,

    -- Waiting Room & Security
    enable_waiting_room BOOLEAN DEFAULT FALSE,
    require_password BOOLEAN DEFAULT TRUE,
    enable_mute_on_join BOOLEAN DEFAULT TRUE,

    -- Subject/Topic
    subject VARCHAR(100),
    topics TEXT[],

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for live_sessions
CREATE INDEX idx_live_sessions_host_id ON live_sessions(host_id);
CREATE INDEX idx_live_sessions_teacher_id ON live_sessions(teacher_id) WHERE teacher_id IS NOT NULL;
CREATE INDEX idx_live_sessions_status ON live_sessions(status);
CREATE INDEX idx_live_sessions_scheduled_start ON live_sessions(scheduled_start);
CREATE INDEX idx_live_sessions_platform ON live_sessions(platform);

-- ============================================================
-- Session Participants Table
-- ============================================================

CREATE TABLE session_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Role
    role participant_role DEFAULT 'participant',

    -- Participation
    joined_at TIMESTAMP WITH TIME ZONE,
    left_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER DEFAULT 0,

    -- Status
    is_present BOOLEAN DEFAULT FALSE,
    is_muted BOOLEAN DEFAULT FALSE,
    is_video_on BOOLEAN DEFAULT TRUE,
    is_sharing_screen BOOLEAN DEFAULT FALSE,

    -- Permissions
    can_share_screen BOOLEAN DEFAULT TRUE,
    can_use_whiteboard BOOLEAN DEFAULT TRUE,
    can_chat BOOLEAN DEFAULT TRUE,
    can_unmute_self BOOLEAN DEFAULT TRUE,

    -- Engagement
    questions_asked INTEGER DEFAULT 0,
    hands_raised INTEGER DEFAULT 0,

    -- Connection
    connection_quality VARCHAR(50),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(session_id, user_id)
);

-- Indexes for session_participants
CREATE INDEX idx_session_participants_session_id ON session_participants(session_id);
CREATE INDEX idx_session_participants_user_id ON session_participants(user_id);
CREATE INDEX idx_session_participants_present ON session_participants(is_present) WHERE is_present = TRUE;

-- ============================================================
-- Task 108.2: Screen Shares Table
-- ============================================================

CREATE TABLE screen_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Screen Share Details
    share_type screen_share_type DEFAULT 'entire_screen',
    window_title VARCHAR(255),
    application_name VARCHAR(255),

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for screen_shares
CREATE INDEX idx_screen_shares_session_id ON screen_shares(session_id);
CREATE INDEX idx_screen_shares_user_id ON screen_shares(user_id);

-- ============================================================
-- Task 108.3: Whiteboard Sessions Table
-- ============================================================

CREATE TABLE whiteboard_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,

    -- Whiteboard Info
    name VARCHAR(255),
    page_count INTEGER DEFAULT 1,
    current_page INTEGER DEFAULT 1,

    -- Settings
    background_color VARCHAR(20) DEFAULT '#FFFFFF',
    grid_enabled BOOLEAN DEFAULT TRUE,

    -- State
    is_active BOOLEAN DEFAULT TRUE,

    -- Snapshot
    snapshot_url VARCHAR(500),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for whiteboard_sessions
CREATE INDEX idx_whiteboard_sessions_session_id ON whiteboard_sessions(session_id);

-- ============================================================
-- Task 108.3: Whiteboard Strokes Table (Drawing Tools)
-- ============================================================

CREATE TABLE whiteboard_strokes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    whiteboard_id UUID NOT NULL REFERENCES whiteboard_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Page
    page_number INTEGER DEFAULT 1,

    -- Tool
    tool_type whiteboard_tool_type NOT NULL,

    -- Stroke Properties
    color VARCHAR(20) DEFAULT '#000000',
    width FLOAT DEFAULT 2.0,
    opacity FLOAT DEFAULT 1.0,

    -- Path Data (for pen, highlighter, eraser)
    path_data JSONB DEFAULT '[]'::JSONB,

    -- Shape Data (for shapes)
    shape_type VARCHAR(50),
    shape_data JSONB DEFAULT '{}'::JSONB,

    -- Text Data (for text tool)
    text_content TEXT,
    font_size INTEGER DEFAULT 16,
    font_family VARCHAR(100) DEFAULT 'Arial',

    -- Z-index for layering
    z_index INTEGER DEFAULT 0,

    -- Deleted (soft delete for undo)
    is_deleted BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for whiteboard_strokes
CREATE INDEX idx_whiteboard_strokes_whiteboard_id ON whiteboard_strokes(whiteboard_id);
CREATE INDEX idx_whiteboard_strokes_page ON whiteboard_strokes(whiteboard_id, page_number);
CREATE INDEX idx_whiteboard_strokes_active ON whiteboard_strokes(whiteboard_id, page_number) WHERE is_deleted = FALSE;

-- ============================================================
-- Task 108.3: Whiteboard Equations Table (Math Equation Editor)
-- ============================================================

CREATE TABLE whiteboard_equations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    whiteboard_id UUID NOT NULL REFERENCES whiteboard_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Page
    page_number INTEGER DEFAULT 1,

    -- Position
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,

    -- Equation
    latex_code TEXT NOT NULL,
    rendered_svg TEXT,

    -- Styling
    font_size INTEGER DEFAULT 20,
    color VARCHAR(20) DEFAULT '#000000',

    -- Display
    width FLOAT,
    height FLOAT,

    -- Z-index
    z_index INTEGER DEFAULT 0,

    -- Deleted
    is_deleted BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for whiteboard_equations
CREATE INDEX idx_whiteboard_equations_whiteboard_id ON whiteboard_equations(whiteboard_id);
CREATE INDEX idx_whiteboard_equations_page ON whiteboard_equations(whiteboard_id, page_number);
CREATE INDEX idx_whiteboard_equations_active ON whiteboard_equations(whiteboard_id, page_number) WHERE is_deleted = FALSE;

-- ============================================================
-- Task 108.4: Session Recordings Table
-- ============================================================

CREATE TABLE session_recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,

    -- Recording Info
    title VARCHAR(255),
    description TEXT,

    -- File Information
    file_path VARCHAR(500),
    file_url VARCHAR(500),
    file_size_bytes BIGINT,

    -- Video Details
    duration_seconds INTEGER,
    resolution VARCHAR(20),
    format VARCHAR(20),

    -- Recording Metadata
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,

    -- Status
    status recording_status DEFAULT 'recording',

    -- Platform-specific
    platform_recording_id VARCHAR(255),
    platform_download_url VARCHAR(500),
    platform_passcode VARCHAR(100),

    -- Processing
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,

    -- Thumbnail
    thumbnail_url VARCHAR(500),

    -- Transcription
    transcript_url VARCHAR(500),
    has_transcript BOOLEAN DEFAULT FALSE,

    -- Access Control
    is_public BOOLEAN DEFAULT FALSE,
    requires_authentication BOOLEAN DEFAULT TRUE,
    allowed_users TEXT[],

    -- Analytics
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    average_watch_percentage FLOAT DEFAULT 0.0,

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for session_recordings
CREATE INDEX idx_session_recordings_session_id ON session_recordings(session_id);
CREATE INDEX idx_session_recordings_status ON session_recordings(status);

-- ============================================================
-- Recording Views Table
-- ============================================================

CREATE TABLE recording_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recording_id UUID NOT NULL REFERENCES session_recordings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),

    -- View Details
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,

    -- Progress
    duration_watched_seconds INTEGER DEFAULT 0,
    watch_percentage FLOAT DEFAULT 0.0,
    last_position_seconds INTEGER DEFAULT 0,

    -- Completion
    completed BOOLEAN DEFAULT FALSE,

    -- Session (for anonymous tracking)
    session_id VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for recording_views
CREATE INDEX idx_recording_views_recording_id ON recording_views(recording_id);
CREATE INDEX idx_recording_views_user_id ON recording_views(user_id) WHERE user_id IS NOT NULL;

-- ============================================================
-- Recording Bookmarks Table
-- ============================================================

CREATE TABLE recording_bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recording_id UUID NOT NULL REFERENCES session_recordings(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Bookmark
    timestamp_seconds INTEGER NOT NULL,
    title VARCHAR(255),
    note TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for recording_bookmarks
CREATE INDEX idx_recording_bookmarks_recording_id ON recording_bookmarks(recording_id);
CREATE INDEX idx_recording_bookmarks_user_id ON recording_bookmarks(user_id);

-- ============================================================
-- Session Chat Messages Table
-- ============================================================

CREATE TABLE session_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Message
    message TEXT NOT NULL,

    -- Type
    message_type VARCHAR(50) DEFAULT 'text',

    -- Recipient (for private messages)
    recipient_id UUID REFERENCES users(id),
    is_private BOOLEAN DEFAULT FALSE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Moderation
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for session_chat_messages
CREATE INDEX idx_session_chat_messages_session_id ON session_chat_messages(session_id);
CREATE INDEX idx_session_chat_messages_visible ON session_chat_messages(session_id, created_at DESC) WHERE is_deleted = FALSE;

-- ============================================================
-- Session Analytics Table
-- ============================================================

CREATE TABLE session_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES live_sessions(id) ON DELETE CASCADE,

    -- Participation
    total_participants INTEGER DEFAULT 0,
    peak_concurrent_participants INTEGER DEFAULT 0,
    average_duration_minutes FLOAT DEFAULT 0.0,

    -- Engagement
    total_chat_messages INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    total_screen_shares INTEGER DEFAULT 0,
    whiteboard_used BOOLEAN DEFAULT FALSE,

    -- Quality
    average_connection_quality VARCHAR(50),

    -- Recording
    recording_duration_seconds INTEGER DEFAULT 0,
    recording_views INTEGER DEFAULT 0,

    -- Ratings
    average_rating FLOAT,
    total_ratings INTEGER DEFAULT 0,

    -- Detailed Metrics
    metrics JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for session_analytics
CREATE INDEX idx_session_analytics_session_id ON session_analytics(session_id);

-- ============================================================
-- Triggers for updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_live_session_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_live_sessions_updated_at
    BEFORE UPDATE ON live_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_live_session_updated_at();

CREATE TRIGGER trigger_session_participants_updated_at
    BEFORE UPDATE ON session_participants
    FOR EACH ROW
    EXECUTE FUNCTION update_live_session_updated_at();

CREATE TRIGGER trigger_whiteboard_sessions_updated_at
    BEFORE UPDATE ON whiteboard_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_live_session_updated_at();

CREATE TRIGGER trigger_whiteboard_equations_updated_at
    BEFORE UPDATE ON whiteboard_equations
    FOR EACH ROW
    EXECUTE FUNCTION update_live_session_updated_at();

CREATE TRIGGER trigger_session_recordings_updated_at
    BEFORE UPDATE ON session_recordings
    FOR EACH ROW
    EXECUTE FUNCTION update_live_session_updated_at();

CREATE TRIGGER trigger_recording_views_updated_at
    BEFORE UPDATE ON recording_views
    FOR EACH ROW
    EXECUTE FUNCTION update_live_session_updated_at();

CREATE TRIGGER trigger_session_analytics_updated_at
    BEFORE UPDATE ON session_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_live_session_updated_at();

-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE live_sessions IS 'Task 108.1: Live Q&A sessions with video conference integration';
COMMENT ON TABLE screen_shares IS 'Task 108.2: Screen sharing activity tracking';
COMMENT ON TABLE whiteboard_sessions IS 'Task 108.3: Interactive whiteboard sessions';
COMMENT ON TABLE whiteboard_strokes IS 'Task 108.3: Drawing strokes and shapes';
COMMENT ON TABLE whiteboard_equations IS 'Task 108.3: Math equations with LaTeX';
COMMENT ON TABLE session_recordings IS 'Task 108.4: Session recordings with playback';
COMMENT ON TABLE recording_views IS 'Recording watch tracking and analytics';
COMMENT ON TABLE session_chat_messages IS 'Chat messages during live sessions';
COMMENT ON TABLE session_analytics IS 'Session performance analytics';
