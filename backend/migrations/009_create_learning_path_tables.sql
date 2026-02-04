-- Learning Path Tables Migration
-- P0 Fix: Database persistence for Learning Path system
-- Created: 2025-01-04

-- ==================== Student Profiles ====================

CREATE TABLE IF NOT EXISTS student_profiles (
    student_id VARCHAR(100) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    grade VARCHAR(20) NOT NULL,
    exam_target VARCHAR(50) NOT NULL,
    learning_style VARCHAR(50) NOT NULL DEFAULT 'mixed',
    knowledge_level VARCHAR(50) NOT NULL DEFAULT 'beginner',
    interests JSONB NOT NULL DEFAULT '[]'::jsonb,
    goals JSONB NOT NULL DEFAULT '[]'::jsonb,
    available_time INTEGER NOT NULL DEFAULT 60,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_student_grade ON student_profiles(grade);
CREATE INDEX idx_student_exam_target ON student_profiles(exam_target);
CREATE INDEX idx_student_learning_style ON student_profiles(learning_style);
CREATE INDEX idx_student_user_id ON student_profiles(user_id);

-- ==================== Learning Paths ====================

CREATE TABLE IF NOT EXISTS learning_paths (
    path_id VARCHAR(100) PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    subject VARCHAR(100) NOT NULL,
    difficulty_level VARCHAR(50) NOT NULL DEFAULT 'intermediate',
    duration_weeks INTEGER NOT NULL DEFAULT 4,
    target_date TIMESTAMP,
    modules JSONB NOT NULL DEFAULT '[]'::jsonb,
    phases JSONB NOT NULL DEFAULT '[]'::jsonb,
    resources JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_generated BOOLEAN NOT NULL DEFAULT TRUE,
    reasoning TEXT,
    agent_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    total_modules INTEGER NOT NULL DEFAULT 0,
    completed_modules INTEGER NOT NULL DEFAULT 0,
    total_topics INTEGER NOT NULL DEFAULT 0,
    completed_topics INTEGER NOT NULL DEFAULT 0,
    overall_progress NUMERIC(5,2) NOT NULL DEFAULT 0.0 CHECK (overall_progress >= 0 AND overall_progress <= 100),
    total_time INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_path_student_subject ON learning_paths(student_id, subject);
CREATE INDEX idx_path_created_at ON learning_paths(created_at);
CREATE INDEX idx_path_student_id ON learning_paths(student_id);

-- ==================== Topic Completions ====================

CREATE TABLE IF NOT EXISTS topic_completions (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completion_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, node_id)
);

CREATE INDEX idx_completion_student_node ON topic_completions(student_id, node_id);
CREATE INDEX idx_completion_student_id ON topic_completions(student_id);

-- ==================== Topic Progress ====================

CREATE TABLE IF NOT EXISTS topic_progress (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    time_spent INTEGER NOT NULL DEFAULT 0,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_progress_student_node ON topic_progress(student_id, node_id);
CREATE INDEX idx_progress_student_id ON topic_progress(student_id);

-- ==================== Quiz Submissions ====================

CREATE TABLE IF NOT EXISTS quiz_submissions (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    quiz_id VARCHAR(100) NOT NULL,
    question_count INTEGER NOT NULL,
    passing_score NUMERIC(5,2) NOT NULL DEFAULT 70.0,
    score NUMERIC(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    correct_count INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    answers JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_time_seconds INTEGER NOT NULL DEFAULT 0,
    submitted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_quiz_student_quiz ON quiz_submissions(student_id, quiz_id);
CREATE INDEX idx_quiz_submitted_at ON quiz_submissions(submitted_at);
CREATE INDEX idx_quiz_student_id ON quiz_submissions(student_id);

-- ==================== Fallback Videos ====================

CREATE TABLE IF NOT EXISTS fallback_videos (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(100) NOT NULL,
    topic VARCHAR(100),
    video_id VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    duration VARCHAR(20),
    duration_minutes INTEGER,
    channel_name VARCHAR(200),
    channel_id VARCHAR(100),
    turkish_score NUMERIC(3,2) NOT NULL DEFAULT 1.0,
    relevance_score NUMERIC(3,2) NOT NULL DEFAULT 1.0,
    quality_score NUMERIC(3,2) NOT NULL DEFAULT 1.0,
    final_score NUMERIC(3,2) NOT NULL DEFAULT 1.0,
    is_accessible BOOLEAN NOT NULL DEFAULT TRUE,
    is_embeddable BOOLEAN NOT NULL DEFAULT TRUE,
    is_turkish BOOLEAN NOT NULL DEFAULT TRUE,
    is_example BOOLEAN NOT NULL DEFAULT TRUE,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fallback_subject_topic ON fallback_videos(subject, topic);
CREATE INDEX idx_fallback_is_example ON fallback_videos(is_example);
CREATE INDEX idx_fallback_final_score ON fallback_videos(final_score);
CREATE INDEX idx_fallback_subject ON fallback_videos(subject);

-- ==================== Triggers for updated_at ====================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_student_profiles_updated_at BEFORE UPDATE ON student_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_paths_updated_at BEFORE UPDATE ON learning_paths
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_topic_completions_updated_at BEFORE UPDATE ON topic_completions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_topic_progress_updated_at BEFORE UPDATE ON topic_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fallback_videos_updated_at BEFORE UPDATE ON fallback_videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== Comments ====================

COMMENT ON TABLE student_profiles IS 'Student profiles for learning path system';
COMMENT ON TABLE learning_paths IS 'AI-generated learning paths';
COMMENT ON TABLE topic_completions IS 'Topic completion status tracking';
COMMENT ON TABLE topic_progress IS 'Detailed topic progress tracking';
COMMENT ON TABLE quiz_submissions IS 'Quiz submission results';
COMMENT ON TABLE fallback_videos IS 'Fallback/example videos for when live search fails';

COMMENT ON COLUMN learning_paths.overall_progress IS 'Overall progress percentage (0-100)';
COMMENT ON COLUMN fallback_videos.is_example IS 'Flag to indicate this is an example video';
