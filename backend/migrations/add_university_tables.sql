-- Task 101: University Preference Advisory System Migration
-- Creates tables for universities, departments, programs, and base scores

-- ============================================================
-- Task 101.1: Universities Table
-- ============================================================

CREATE TYPE university_type_enum AS ENUM ('devlet', 'vakif');

CREATE TABLE IF NOT EXISTS universities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic info
    name VARCHAR(255) NOT NULL UNIQUE,
    short_name VARCHAR(50),
    university_type university_type_enum NOT NULL,

    -- Location
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100),
    address TEXT,
    postal_code VARCHAR(10),

    -- Coordinates
    latitude FLOAT,
    longitude FLOAT,

    -- Contact
    phone VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(255),

    -- Profile
    established_year INTEGER,
    rector VARCHAR(100),
    total_students INTEGER,
    total_faculty INTEGER,

    -- Rankings
    world_ranking INTEGER,
    turkey_ranking INTEGER,

    -- Additional info
    description TEXT,
    campus_info JSONB DEFAULT '{}'::jsonb,
    facilities VARCHAR(100)[],

    -- Social media
    social_media JSONB DEFAULT '{}'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_universities_name ON universities(name);
CREATE INDEX idx_universities_city ON universities(city);
CREATE INDEX idx_universities_type ON universities(university_type);
CREATE INDEX idx_universities_active ON universities(is_active);


-- ============================================================
-- Task 101.2: Departments Table
-- ============================================================

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic info
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    faculty VARCHAR(200),

    -- Education details
    degree_type VARCHAR(50) NOT NULL,
    education_language VARCHAR(50) DEFAULT 'Türkçe',
    education_duration INTEGER DEFAULT 4,

    -- Description
    description TEXT,
    overview TEXT,

    -- Career paths
    career_opportunities VARCHAR(200)[],
    job_titles VARCHAR(100)[],
    average_salary INTEGER,
    employment_rate FLOAT,

    -- Prerequisites
    required_subjects VARCHAR(100)[],
    recommended_skills VARCHAR(100)[],

    -- Additional info
    accreditation JSONB DEFAULT '{}'::jsonb,
    international_programs VARCHAR(100)[],

    -- SEO
    seo_keywords VARCHAR(100)[],

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_departments_name ON departments(name);
CREATE INDEX idx_departments_active ON departments(is_active);


-- ============================================================
-- Task 101.3 & 101.4: University Programs (Base Scores + Quotas)
-- ============================================================

CREATE TYPE program_type_enum AS ENUM ('normal', 'kktc', 'ozel_yetenek', 'ikinci_ogretim');
CREATE TYPE score_type_enum AS ENUM ('SAY', 'EA', 'SOZ', 'DIL');

CREATE TABLE IF NOT EXISTS university_programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,

    -- Program info
    program_code VARCHAR(50),
    program_name VARCHAR(255) NOT NULL,
    program_type program_type_enum DEFAULT 'normal',

    -- Year
    year INTEGER NOT NULL,

    -- Score type
    score_type score_type_enum NOT NULL,

    -- Task 101.3: Base Score Data
    base_score FLOAT,
    top_score FLOAT,
    median_score FLOAT,

    -- Task 101.4: Quota Information
    total_quota INTEGER,
    general_quota INTEGER,
    special_quota INTEGER,
    filled_quota INTEGER,

    -- Acceptance metrics
    acceptance_rate FLOAT,
    competition_ratio FLOAT,

    -- Placement statistics
    min_rank INTEGER,
    max_rank INTEGER,
    median_rank INTEGER,

    -- Additional info
    scholarship BOOLEAN DEFAULT FALSE,
    scholarship_percentage FLOAT,
    tuition_fee INTEGER,

    -- Language prep
    has_language_prep BOOLEAN DEFAULT FALSE,
    prep_mandatory BOOLEAN DEFAULT FALSE,

    -- Special conditions
    special_conditions JSONB DEFAULT '{}'::jsonb,
    bonus_coefficients JSONB DEFAULT '{}'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_programs_university ON university_programs(university_id);
CREATE INDEX idx_programs_department ON university_programs(department_id);
CREATE INDEX idx_programs_code ON university_programs(program_code);
CREATE INDEX idx_programs_year ON university_programs(year);
CREATE INDEX idx_programs_score_type ON university_programs(score_type);
CREATE INDEX idx_programs_active ON university_programs(is_active);
CREATE INDEX idx_programs_search ON university_programs(university_id, department_id, year, score_type);
CREATE INDEX idx_programs_base_score ON university_programs(year, score_type, base_score);


-- ============================================================
-- Historical Data
-- ============================================================

CREATE TABLE IF NOT EXISTS program_score_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference
    program_id UUID NOT NULL REFERENCES university_programs(id) ON DELETE CASCADE,

    -- Year
    year INTEGER NOT NULL,

    -- Scores
    base_score FLOAT,
    top_score FLOAT,
    median_score FLOAT,

    -- Quotas
    total_quota INTEGER,
    filled_quota INTEGER,

    -- Rankings
    min_rank INTEGER,
    max_rank INTEGER,

    -- Metadata
    source VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_score_history_program ON program_score_history(program_id);
CREATE INDEX idx_score_history_year ON program_score_history(year);
CREATE INDEX idx_score_history_program_year ON program_score_history(program_id, year);


-- ============================================================
-- User Preferences
-- ============================================================

CREATE TABLE IF NOT EXISTS user_university_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Preferences
    preferred_cities VARCHAR(100)[],
    preferred_university_types VARCHAR(20)[],
    preferred_score_types VARCHAR(10)[],

    -- Score info
    yks_score FLOAT,
    score_type VARCHAR(10),

    -- Career interests
    career_interests VARCHAR(100)[],
    target_departments VARCHAR(100)[],

    -- Budget constraints
    max_tuition_fee INTEGER,
    needs_scholarship BOOLEAN DEFAULT FALSE,

    -- Additional preferences
    preferences JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_user_preferences UNIQUE (user_id)
);

CREATE INDEX idx_user_preferences_user ON user_university_preferences(user_id);


-- ============================================================
-- Update Triggers
-- ============================================================

-- Update updated_at on universities
CREATE OR REPLACE FUNCTION update_university_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_university_timestamp
BEFORE UPDATE ON universities
FOR EACH ROW
EXECUTE FUNCTION update_university_timestamp();


-- Update updated_at on departments
CREATE OR REPLACE FUNCTION update_department_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_department_timestamp
BEFORE UPDATE ON departments
FOR EACH ROW
EXECUTE FUNCTION update_department_timestamp();


-- Update updated_at on university_programs
CREATE OR REPLACE FUNCTION update_program_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_program_timestamp
BEFORE UPDATE ON university_programs
FOR EACH ROW
EXECUTE FUNCTION update_program_timestamp();


-- Update updated_at on user_university_preferences
CREATE OR REPLACE FUNCTION update_user_preferences_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_preferences_timestamp
BEFORE UPDATE ON user_university_preferences
FOR EACH ROW
EXECUTE FUNCTION update_user_preferences_timestamp();


-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE universities IS 'Task 101.1: University database with profiles and locations';
COMMENT ON TABLE departments IS 'Task 101.2: Department database with descriptions and career paths';
COMMENT ON TABLE university_programs IS 'Task 101.3 & 101.4: Programs with base scores and quotas';
COMMENT ON TABLE program_score_history IS 'Task 101.3: Historical base score trends for predictions';
COMMENT ON TABLE user_university_preferences IS 'User preferences for personalized recommendations';
