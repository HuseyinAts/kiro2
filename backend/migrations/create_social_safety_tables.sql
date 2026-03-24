-- Social Safety Tables Migration
-- F0: Safety Infrastructure for KIRO2 Social Features
-- Created: 2026-03-24

-- Table 1: content_reports
CREATE TABLE IF NOT EXISTS content_reports (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    reporter_id VARCHAR NOT NULL,
    reported_user_id VARCHAR,
    reported_content_id VARCHAR,
    content_type VARCHAR(30) NOT NULL,
    content_snapshot TEXT,
    reason VARCHAR(20) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    reviewed_by VARCHAR,
    reviewed_at TIMESTAMPTZ,
    resolution_note TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_content_reports_reporter ON content_reports(reporter_id);
CREATE INDEX IF NOT EXISTS idx_content_reports_content ON content_reports(reported_content_id);
CREATE INDEX IF NOT EXISTS idx_content_reports_status ON content_reports(status);

-- Table 2: moderation_actions
CREATE TABLE IF NOT EXISTS moderation_actions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    moderator_id VARCHAR,
    target_user_id VARCHAR NOT NULL,
    content_id VARCHAR,
    content_type VARCHAR(30),
    action_type VARCHAR(30) NOT NULL,
    reason TEXT NOT NULL,
    report_id VARCHAR,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mod_actions_target ON moderation_actions(target_user_id);
CREATE INDEX IF NOT EXISTS idx_mod_actions_type ON moderation_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_mod_actions_expires ON moderation_actions(expires_at);

-- Table 3: blocked_users
CREATE TABLE IF NOT EXISTS blocked_users (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    blocker_id VARCHAR NOT NULL,
    blocked_id VARCHAR NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_block_pair UNIQUE (blocker_id, blocked_id)
);

CREATE INDEX IF NOT EXISTS idx_blocked_users_blocker ON blocked_users(blocker_id);
CREATE INDEX IF NOT EXISTS idx_blocked_users_blocked ON blocked_users(blocked_id);

-- Table 4: parent_social_settings
CREATE TABLE IF NOT EXISTS parent_social_settings (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    parent_id VARCHAR NOT NULL,
    student_id VARCHAR NOT NULL,
    social_enabled BOOLEAN DEFAULT TRUE,
    chat_enabled BOOLEAN DEFAULT TRUE,
    study_rooms_enabled BOOLEAN DEFAULT TRUE,
    duels_enabled BOOLEAN DEFAULT TRUE,
    forum_enabled BOOLEAN DEFAULT TRUE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    visibility_level VARCHAR(20) DEFAULT 'full',
    max_daily_messages INTEGER DEFAULT 200,
    allowed_hours_start INTEGER DEFAULT 6,
    allowed_hours_end INTEGER DEFAULT 23,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_parent_student_settings UNIQUE (parent_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_parent_social_parent ON parent_social_settings(parent_id);
CREATE INDEX IF NOT EXISTS idx_parent_social_student ON parent_social_settings(student_id);

-- Table 5: message_audit_log
CREATE TABLE IF NOT EXISTS message_audit_log (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    sender_id VARCHAR NOT NULL,
    content_type VARCHAR(30) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    content_length INTEGER NOT NULL,
    flagged BOOLEAN DEFAULT FALSE,
    flag_reason VARCHAR(20) DEFAULT 'clean',
    flag_details JSONB,
    pipeline_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_msg_audit_sender ON message_audit_log(sender_id);
CREATE INDEX IF NOT EXISTS idx_msg_audit_flagged ON message_audit_log(flagged);
