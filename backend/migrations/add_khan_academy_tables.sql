-- Task 98: Khan Academy Integration Database Tables
-- Created: 2025-10-26

-- ============================================
-- Table 1: khan_contents (Task 98.2: Content Catalog)
-- ============================================

CREATE TABLE IF NOT EXISTS khan_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Khan Academy ID
    khan_content_id VARCHAR(100) UNIQUE NOT NULL,

    -- Content metadata
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content_type VARCHAR(20) NOT NULL,  -- video, exercise, article

    -- Classification
    subject VARCHAR(50) NOT NULL,
    topic VARCHAR(200),

    -- Video specific
    video_url VARCHAR(1000),
    duration_seconds INTEGER,
    thumbnail_url VARCHAR(1000),

    -- Exercise specific
    exercise_url VARCHAR(1000),
    problem_count INTEGER,

    -- Language
    language VARCHAR(5) DEFAULT 'tr',

    -- Metadata
    difficulty_level VARCHAR(20),
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_khan_contents_id ON khan_contents(khan_content_id);
CREATE INDEX idx_khan_contents_type ON khan_contents(content_type);
CREATE INDEX idx_khan_contents_subject ON khan_contents(subject);
CREATE INDEX idx_khan_contents_language ON khan_contents(language);
CREATE INDEX idx_khan_contents_subject_type ON khan_contents(subject, content_type);


-- ============================================
-- Table 2: khan_user_progress (Task 98.3: Progress Tracking)
-- ============================================

CREATE TABLE IF NOT EXISTS khan_user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    khan_user_id VARCHAR(100),
    khan_content_id UUID NOT NULL REFERENCES khan_contents(id) ON DELETE CASCADE,

    -- Content type
    content_type VARCHAR(20) NOT NULL,

    -- Progress timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_accessed TIMESTAMP WITH TIME ZONE,

    -- Video progress
    video_seconds_watched INTEGER DEFAULT 0,
    video_completed BOOLEAN DEFAULT FALSE,

    -- Exercise progress
    problems_attempted INTEGER DEFAULT 0,
    problems_correct INTEGER DEFAULT 0,
    proficiency_level VARCHAR(20),

    -- Gamification
    energy_points INTEGER DEFAULT 0,
    badges_earned TEXT[],

    -- Sync metadata
    last_synced_at TIMESTAMP WITH TIME ZONE,
    sync_conflict BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint: one progress per user per content
    UNIQUE(user_id, khan_content_id)
);

-- Indexes
CREATE INDEX idx_khan_progress_user ON khan_user_progress(user_id);
CREATE INDEX idx_khan_progress_khan_user ON khan_user_progress(khan_user_id);
CREATE INDEX idx_khan_progress_content ON khan_user_progress(khan_content_id);
CREATE INDEX idx_khan_progress_user_content ON khan_user_progress(user_id, khan_content_id);
CREATE INDEX idx_khan_progress_completed ON khan_progress(video_completed);
CREATE INDEX idx_khan_progress_sync_conflict ON khan_user_progress(sync_conflict);


-- ============================================
-- Table 3: khan_certificates (Task 98.4: Badges/Certificates)
-- ============================================

CREATE TABLE IF NOT EXISTS khan_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    khan_user_id VARCHAR(100),

    -- Badge details
    badge_id VARCHAR(100) UNIQUE NOT NULL,
    badge_name VARCHAR(200) NOT NULL,
    badge_category VARCHAR(50) NOT NULL,
    description TEXT,
    icon_url VARCHAR(1000),

    -- Verification
    verification_url VARCHAR(1000),
    earned_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_khan_certs_user ON khan_certificates(user_id);
CREATE INDEX idx_khan_certs_khan_user ON khan_certificates(khan_user_id);
CREATE INDEX idx_khan_certs_category ON khan_certificates(badge_category);
CREATE INDEX idx_khan_certs_earned ON khan_certificates(earned_at DESC);


-- ============================================
-- Table 4: khan_oauth_tokens (Task 98.1: OAuth Storage)
-- ============================================

CREATE TABLE IF NOT EXISTS khan_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User association
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    khan_user_id VARCHAR(100),

    -- OAuth tokens
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(20) DEFAULT 'Bearer',

    -- Token expiration
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Scopes
    scopes TEXT[],

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_refreshed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_khan_oauth_user ON khan_oauth_tokens(user_id);
CREATE INDEX idx_khan_oauth_khan_user ON khan_oauth_tokens(khan_user_id);
CREATE INDEX idx_khan_oauth_expires ON khan_oauth_tokens(expires_at);
CREATE INDEX idx_khan_oauth_active ON khan_oauth_tokens(is_active);


-- ============================================
-- Sample Data (for testing)
-- ============================================

-- Insert sample Khan Academy content
INSERT INTO khan_contents (
    khan_content_id,
    title,
    description,
    content_type,
    subject,
    topic,
    video_url,
    duration_seconds,
    thumbnail_url,
    language,
    difficulty_level
) VALUES
(
    'khan_sample_video_1',
    'Cebir Temelleri - Denklemler',
    'Khan Academy Türkçe cebir dersi: Denklem çözme teknikleri',
    'video',
    'math',
    'algebra',
    'https://cdn.khanacademy.org/videos/algebra_basics.mp4',
    720,
    'https://cdn.khanacademy.org/thumbnails/algebra_basics.jpg',
    'tr',
    'beginner'
),
(
    'khan_sample_exercise_1',
    'Cebir Alıştırmaları - Seviye 1',
    'Temel cebir alıştırmaları ve problemleri',
    'exercise',
    'math',
    'algebra',
    NULL,
    NULL,
    NULL,
    'tr',
    'beginner'
),
(
    'khan_sample_video_2',
    'Fizik: Newtonun Hareket Yasaları',
    'Newton\'ın üç hareket yasası detaylı anlatım',
    'video',
    'science',
    'physics',
    'https://cdn.khanacademy.org/videos/newton_laws.mp4',
    900,
    'https://cdn.khanacademy.org/thumbnails/newton_laws.jpg',
    'tr',
    'intermediate'
);


-- ============================================
-- Functions and Triggers
-- ============================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_khan_oauth_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_khan_oauth_timestamp
BEFORE UPDATE ON khan_oauth_tokens
FOR EACH ROW
EXECUTE FUNCTION update_khan_oauth_timestamp();


-- Function: Auto-mark video as completed at 90%
CREATE OR REPLACE FUNCTION auto_complete_khan_video()
RETURNS TRIGGER AS $$
BEGIN
    -- Get video duration
    DECLARE
        video_duration INTEGER;
    BEGIN
        SELECT duration_seconds INTO video_duration
        FROM khan_contents
        WHERE id = NEW.khan_content_id AND content_type = 'video';

        IF video_duration IS NOT NULL AND video_duration > 0 THEN
            IF NEW.video_seconds_watched >= (video_duration * 0.9) THEN
                NEW.video_completed = TRUE;
                IF NEW.completed_at IS NULL THEN
                    NEW.completed_at = NOW();
                END IF;
            END IF;
        END IF;
    END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_complete_khan_video
BEFORE INSERT OR UPDATE ON khan_user_progress
FOR EACH ROW
WHEN (NEW.content_type = 'video')
EXECUTE FUNCTION auto_complete_khan_video();


-- Function: Calculate exercise proficiency
CREATE OR REPLACE FUNCTION calculate_khan_proficiency()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.content_type = 'exercise' AND NEW.problems_attempted > 0 THEN
        DECLARE
            accuracy FLOAT;
        BEGIN
            accuracy = (NEW.problems_correct::FLOAT / NEW.problems_attempted::FLOAT) * 100;

            -- Determine proficiency level
            IF NEW.problems_attempted < 3 THEN
                NEW.proficiency_level = 'practicing';
            ELSIF accuracy >= 80 AND NEW.problems_attempted >= 5 THEN
                NEW.proficiency_level = 'mastered';
            ELSIF accuracy >= 60 THEN
                NEW.proficiency_level = 'proficient';
            ELSE
                NEW.proficiency_level = 'struggling';
            END IF;
        END;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_khan_proficiency
BEFORE INSERT OR UPDATE ON khan_user_progress
FOR EACH ROW
WHEN (NEW.content_type = 'exercise')
EXECUTE FUNCTION calculate_khan_proficiency();


-- ============================================
-- Views
-- ============================================

-- View: User's Khan Academy learning summary
CREATE OR REPLACE VIEW khan_user_learning_summary AS
SELECT
    u.id AS user_id,
    u.email,
    COUNT(DISTINCT kup.khan_content_id) AS total_content_accessed,
    COUNT(DISTINCT CASE WHEN kup.video_completed = TRUE THEN kup.khan_content_id END) AS videos_completed,
    COUNT(DISTINCT CASE WHEN kup.proficiency_level = 'mastered' THEN kup.khan_content_id END) AS exercises_mastered,
    SUM(kup.energy_points) AS total_energy_points,
    COUNT(DISTINCT kc.id) AS total_badges,
    MAX(kup.last_accessed) AS last_accessed_khan
FROM users u
LEFT JOIN khan_user_progress kup ON u.id = kup.user_id
LEFT JOIN khan_certificates kc ON u.id = kc.user_id
GROUP BY u.id, u.email;


-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE khan_contents IS 'Task 98.2: Khan Academy Turkish content catalog';
COMMENT ON TABLE khan_user_progress IS 'Task 98.3: User progress with bidirectional sync';
COMMENT ON TABLE khan_certificates IS 'Task 98.4: Khan Academy badges and certificates';
COMMENT ON TABLE khan_oauth_tokens IS 'Task 98.1: OAuth 2.0 token storage';

COMMENT ON COLUMN khan_user_progress.sync_conflict IS 'TRUE if local and remote progress conflict during sync';
COMMENT ON COLUMN khan_user_progress.proficiency_level IS 'practicing, proficient, mastered, struggling';
COMMENT ON COLUMN khan_user_progress.energy_points IS 'Khan Academy gamification points';
