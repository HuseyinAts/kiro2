-- Task 106: AI Chat Assistant Tables Migration

-- Create trigger function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE session_status AS ENUM ('active', 'completed', 'archived');
CREATE TYPE subject_type AS ENUM ('mathematics', 'physics', 'chemistry', 'biology', 'turkish', 'history', 'geography', 'english', 'general');
CREATE TYPE image_processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Chat Sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    subject_type subject_type DEFAULT 'general',
    status session_status DEFAULT 'active',
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    model_name VARCHAR(100) DEFAULT 'gpt-4',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2000,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);

-- Chat Messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role message_role NOT NULL,
    content TEXT NOT NULL,
    image_id UUID,
    model VARCHAR(100),
    tokens_used INTEGER,
    cost DECIMAL(10,4),
    response_time_ms INTEGER,
    confidence_score DECIMAL(3,2),
    relevance_score DECIMAL(3,2),
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    is_helpful BOOLEAN,
    feedback_comment TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);

-- Image Uploads
CREATE TABLE IF NOT EXISTS image_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    image_url VARCHAR(512),
    thumbnail_url VARCHAR(512),
    processing_status image_processing_status DEFAULT 'pending',
    ocr_text TEXT,
    ocr_confidence DECIMAL(3,2),
    contains_math BOOLEAN DEFAULT FALSE,
    math_latex TEXT,
    math_confidence DECIMAL(3,2),
    is_handwritten BOOLEAN DEFAULT FALSE,
    handwriting_quality VARCHAR(50),
    processing_time_ms INTEGER,
    ocr_engine VARCHAR(100),
    error_message TEXT,
    image_description TEXT,
    detected_objects JSONB DEFAULT '[]',
    suggested_subjects JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_image_uploads_session ON image_uploads(session_id);

-- Solution Steps
CREATE TABLE IF NOT EXISTS solution_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    step_type VARCHAR(50),
    latex_formula TEXT,
    calculation_result VARCHAR(255),
    is_alternative_method BOOLEAN DEFAULT FALSE,
    alternative_method_name VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_solution_steps_message ON solution_steps(message_id);

-- Chat Analytics
CREATE TABLE IF NOT EXISTS chat_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(20) DEFAULT 'daily',
    total_sessions INTEGER DEFAULT 0,
    active_sessions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    total_images INTEGER DEFAULT 0,
    subject_distribution JSONB DEFAULT '{}',
    avg_response_time_ms DECIMAL(10,2),
    total_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_analytics_user ON chat_analytics(user_id);

CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
