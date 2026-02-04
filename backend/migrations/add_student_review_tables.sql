-- Task 105: Student Review Tables Migration
-- Review System, Ratings, Moderation, and Filtering

-- ============================================================
-- Enums
-- ============================================================

CREATE TYPE review_type AS ENUM (
    'university',
    'department',
    'professor',
    'course',
    'dormitory',
    'general'
);

CREATE TYPE review_status AS ENUM (
    'pending',
    'approved',
    'rejected',
    'flagged',
    'removed'
);

CREATE TYPE report_reason AS ENUM (
    'spam',
    'inappropriate',
    'offensive',
    'fake',
    'misleading',
    'off_topic',
    'other'
);

CREATE TYPE rating_category AS ENUM (
    'education_quality',
    'faculty',
    'campus_facilities',
    'social_life',
    'career_opportunities',
    'accommodation',
    'food_service',
    'administration',
    'value_for_money'
);


-- ============================================================
-- Task 105.1: Student Reviews Table
-- ============================================================

CREATE TABLE IF NOT EXISTS student_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Review target
    review_type review_type NOT NULL,
    university_id UUID REFERENCES universities(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    professor_id UUID,
    course_id UUID,
    dormitory_id UUID REFERENCES dormitory_info(id) ON DELETE CASCADE,

    -- Review content
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,

    -- Overall rating (1.0 - 5.0)
    overall_rating DECIMAL(3,2) NOT NULL CHECK (overall_rating >= 1.0 AND overall_rating <= 5.0),

    -- Additional metadata
    pros JSONB DEFAULT '[]',
    cons JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',

    -- Student info
    student_year INTEGER,
    enrollment_year INTEGER,
    is_current_student BOOLEAN DEFAULT TRUE,
    is_alumni BOOLEAN DEFAULT FALSE,

    -- Task 105.3: Moderation
    status review_status DEFAULT 'pending',
    moderation_notes TEXT,
    moderated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    moderated_at TIMESTAMP WITH TIME ZONE,

    -- Spam/quality scores (0.0 - 1.0)
    spam_score DECIMAL(3,2) DEFAULT 0.0 CHECK (spam_score >= 0.0 AND spam_score <= 1.0),
    quality_score DECIMAL(3,2) DEFAULT 0.5 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),

    -- Auto-moderation flags
    contains_profanity BOOLEAN DEFAULT FALSE,
    contains_contact_info BOOLEAN DEFAULT FALSE,
    is_too_short BOOLEAN DEFAULT FALSE,

    -- Task 105.2: Verified reviews
    is_verified BOOLEAN DEFAULT FALSE,
    verification_method VARCHAR(100),
    verified_at TIMESTAMP WITH TIME ZONE,

    -- Engagement metrics
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    report_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,

    -- Metadata
    language VARCHAR(10) DEFAULT 'tr',
    ip_address VARCHAR(50),
    user_agent VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_student_reviews_user ON student_reviews(user_id);
CREATE INDEX idx_student_reviews_type ON student_reviews(review_type);
CREATE INDEX idx_student_reviews_university ON student_reviews(university_id);
CREATE INDEX idx_student_reviews_department ON student_reviews(department_id);
CREATE INDEX idx_student_reviews_status ON student_reviews(status);
CREATE INDEX idx_student_reviews_rating ON student_reviews(overall_rating);
CREATE INDEX idx_student_reviews_created ON student_reviews(created_at);
CREATE INDEX idx_student_reviews_verified ON student_reviews(is_verified);


-- ============================================================
-- Task 105.2: Multi-criteria Ratings Table
-- ============================================================

CREATE TABLE IF NOT EXISTS review_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES student_reviews(id) ON DELETE CASCADE,

    -- Rating category and value
    category rating_category NOT NULL,
    rating DECIMAL(3,2) NOT NULL CHECK (rating >= 1.0 AND rating <= 5.0),

    -- Optional comment for this specific category
    comment TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_review_ratings_review ON review_ratings(review_id);
CREATE INDEX idx_review_ratings_category ON review_ratings(category);
CREATE INDEX idx_review_ratings_rating ON review_ratings(rating);
CREATE UNIQUE INDEX idx_review_ratings_unique ON review_ratings(review_id, category);


-- ============================================================
-- Task 105.2: Review Votes Table (Helpful/Not Helpful)
-- ============================================================

CREATE TABLE IF NOT EXISTS review_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES student_reviews(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Vote type
    is_helpful BOOLEAN NOT NULL,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_review_votes_review ON review_votes(review_id);
CREATE INDEX idx_review_votes_user ON review_votes(user_id);
CREATE UNIQUE INDEX idx_review_votes_unique ON review_votes(review_id, user_id);


-- ============================================================
-- Task 105.3: Review Reports Table
-- ============================================================

CREATE TABLE IF NOT EXISTS review_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES student_reviews(id) ON DELETE CASCADE,
    reporter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Report details
    reason report_reason NOT NULL,
    description TEXT,

    -- Report status
    status VARCHAR(50) DEFAULT 'pending',
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_review_reports_review ON review_reports(review_id);
CREATE INDEX idx_review_reports_reporter ON review_reports(reporter_id);
CREATE INDEX idx_review_reports_status ON review_reports(status);
CREATE INDEX idx_review_reports_reason ON review_reports(reason);


-- ============================================================
-- Review Statistics (Aggregate) Table
-- ============================================================

CREATE TABLE IF NOT EXISTS review_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Target
    review_type review_type NOT NULL,
    university_id UUID REFERENCES universities(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    dormitory_id UUID REFERENCES dormitory_info(id) ON DELETE CASCADE,

    -- Overall statistics
    total_reviews INTEGER DEFAULT 0,
    verified_reviews INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),

    -- Rating distribution (1-5 stars)
    rating_1_count INTEGER DEFAULT 0,
    rating_2_count INTEGER DEFAULT 0,
    rating_3_count INTEGER DEFAULT 0,
    rating_4_count INTEGER DEFAULT 0,
    rating_5_count INTEGER DEFAULT 0,

    -- Category averages (JSONB for flexibility)
    category_averages JSONB DEFAULT '{}',

    -- Engagement
    total_helpful_votes INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,

    -- Sentiment analysis (optional)
    positive_percentage DECIMAL(5,2),
    negative_percentage DECIMAL(5,2),

    -- Common tags
    top_tags JSONB DEFAULT '[]',

    -- Metadata
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_review_statistics_type ON review_statistics(review_type);
CREATE INDEX idx_review_statistics_university ON review_statistics(university_id);
CREATE INDEX idx_review_statistics_department ON review_statistics(department_id);
CREATE INDEX idx_review_statistics_rating ON review_statistics(average_rating);


-- ============================================================
-- Moderation Queue Table
-- ============================================================

CREATE TABLE IF NOT EXISTS moderation_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES student_reviews(id) ON DELETE CASCADE,

    -- Priority
    priority INTEGER DEFAULT 0,

    -- Auto-flagged reasons
    flag_reasons JSONB DEFAULT '[]',

    -- Assignment
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP WITH TIME ZONE,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_moderation_queue_review ON moderation_queue(review_id);
CREATE INDEX idx_moderation_queue_status ON moderation_queue(status);
CREATE INDEX idx_moderation_queue_priority ON moderation_queue(priority);
CREATE INDEX idx_moderation_queue_assigned ON moderation_queue(assigned_to);


-- ============================================================
-- Triggers for updated_at
-- ============================================================

CREATE TRIGGER update_student_reviews_updated_at
    BEFORE UPDATE ON student_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_review_ratings_updated_at
    BEFORE UPDATE ON review_ratings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE student_reviews IS 'Task 105.1: Student reviews with spam detection and moderation';
COMMENT ON TABLE review_ratings IS 'Task 105.2: Multi-criteria ratings for reviews';
COMMENT ON TABLE review_votes IS 'Task 105.2: Helpful/not helpful votes for reviews';
COMMENT ON TABLE review_reports IS 'Task 105.3: Reports of inappropriate or spam reviews';
COMMENT ON TABLE review_statistics IS 'Aggregate statistics for reviews by target (university, department, etc.)';
COMMENT ON TABLE moderation_queue IS 'Task 105.3: Queue of reviews needing moderation';
