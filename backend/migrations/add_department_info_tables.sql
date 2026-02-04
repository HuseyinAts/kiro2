-- Task 103: Department Information Tables Migration
-- Curriculum, Career Opportunities, Salary Expectations, Sector Analysis

-- ============================================================
-- Enums
-- ============================================================

CREATE TYPE experience_level AS ENUM ('entry', 'junior', 'mid', 'senior', 'expert');

CREATE TYPE industry_type AS ENUM (
    'technology',
    'finance',
    'healthcare',
    'education',
    'manufacturing',
    'retail',
    'consulting',
    'government',
    'energy',
    'other'
);

-- ============================================================
-- Departments Base Table (Required for foreign keys)
-- ============================================================

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    university_id UUID,
    code VARCHAR(50),
    description TEXT,
    faculty VARCHAR(255),
    degree_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, university_id)
);

CREATE INDEX idx_departments_university ON departments(university_id);
CREATE INDEX idx_departments_name ON departments(name);

-- ============================================================
-- Task 103.1: Department Curriculum Table
-- ============================================================

CREATE TABLE IF NOT EXISTS department_curriculum (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,

    -- Basic info
    total_credits INTEGER NOT NULL,
    duration_years INTEGER NOT NULL DEFAULT 4,
    duration_semesters INTEGER NOT NULL DEFAULT 8,

    -- Courses
    core_courses JSONB NOT NULL DEFAULT '[]',
    elective_courses JSONB DEFAULT '[]',
    specialization_tracks TEXT[] DEFAULT '{}',

    -- Learning outcomes
    learning_outcomes TEXT[] DEFAULT '{}',
    skills_gained TEXT[] DEFAULT '{}',

    -- Requirements
    internship_required BOOLEAN DEFAULT FALSE,
    thesis_required BOOLEAN DEFAULT FALSE,
    capstone_project BOOLEAN DEFAULT FALSE,

    -- International
    ects_credits INTEGER,
    exchange_programs_available BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(department_id)
);

CREATE INDEX idx_department_curriculum_dept ON department_curriculum(department_id);


-- ============================================================
-- Task 103.2: Career Opportunities Table
-- ============================================================

CREATE TABLE IF NOT EXISTS career_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,

    -- Job details
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT,
    industry_type industry_type,

    -- Employment stats
    employment_rate DECIMAL(5,2),  -- Percentage (0-100)
    average_hiring_time_days INTEGER,
    demand_level VARCHAR(50),  -- 'high', 'medium', 'low'

    -- Skills and requirements
    required_skills TEXT[] DEFAULT '{}',
    preferred_certifications TEXT[] DEFAULT '{}',

    -- Career outlook
    career_growth_potential VARCHAR(50),  -- 'high', 'medium', 'low'
    work_life_balance_rating DECIMAL(3,2),  -- 1.00 - 5.00
    job_satisfaction_rating DECIMAL(3,2),  -- 1.00 - 5.00

    -- Employers
    top_employers TEXT[] DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_career_opportunities_dept ON career_opportunities(department_id);
CREATE INDEX idx_career_opportunities_industry ON career_opportunities(industry_type);
CREATE INDEX idx_career_opportunities_demand ON career_opportunities(demand_level);


-- ============================================================
-- Task 103.3: Salary Expectations Table
-- ============================================================

CREATE TABLE IF NOT EXISTS salary_expectations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    career_opportunity_id UUID REFERENCES career_opportunities(id) ON DELETE SET NULL,

    -- Experience level
    experience_level experience_level NOT NULL,

    -- Salary ranges
    min_salary INTEGER NOT NULL,
    max_salary INTEGER NOT NULL,
    average_salary INTEGER NOT NULL,
    median_salary INTEGER,

    -- Location
    region VARCHAR(100),
    city VARCHAR(100),

    -- Industry
    industry_type industry_type,

    -- Time period
    currency VARCHAR(10) DEFAULT 'TRY',
    year INTEGER NOT NULL DEFAULT 2024,

    -- Sample info
    sample_size INTEGER,
    data_source VARCHAR(255),

    -- Additional benefits
    average_bonus_percentage DECIMAL(5,2),
    stock_options_common BOOLEAN DEFAULT FALSE,
    remote_work_percentage DECIMAL(5,2),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (min_salary <= average_salary),
    CHECK (average_salary <= max_salary),
    CHECK (year >= 2020 AND year <= 2100)
);

CREATE INDEX idx_salary_expectations_dept ON salary_expectations(department_id);
CREATE INDEX idx_salary_expectations_exp_level ON salary_expectations(experience_level);
CREATE INDEX idx_salary_expectations_city ON salary_expectations(city);
CREATE INDEX idx_salary_expectations_year ON salary_expectations(year);
CREATE INDEX idx_salary_expectations_industry ON salary_expectations(industry_type);


-- ============================================================
-- Task 103.4: Sector Analysis Table
-- ============================================================

CREATE TABLE IF NOT EXISTS sector_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Industry identification
    industry_type industry_type NOT NULL,
    sector_name VARCHAR(255) NOT NULL,

    -- Related departments
    related_department_ids UUID[] DEFAULT '{}',

    -- Market size
    market_size_billion_tl DECIMAL(10,2),
    total_employment INTEGER,

    -- Growth metrics
    annual_growth_rate DECIMAL(5,2),  -- Percentage
    job_growth_rate DECIMAL(5,2),     -- Percentage
    growth_trend VARCHAR(50),          -- 'increasing', 'stable', 'declining'

    -- Job market
    total_job_openings INTEGER,
    in_demand_skills TEXT[] DEFAULT '{}',
    emerging_technologies TEXT[] DEFAULT '{}',

    -- Future outlook
    future_demand_prediction VARCHAR(50),  -- 'high', 'medium', 'low'
    automation_risk VARCHAR(50),           -- 'high', 'medium', 'low'
    future_outlook TEXT,

    -- Ratings
    sustainability_rating DECIMAL(3,2),    -- 1.00 - 5.00
    innovation_index DECIMAL(3,2),         -- 1.00 - 5.00

    -- Time period
    year INTEGER NOT NULL DEFAULT 2024,

    -- Data source
    data_source VARCHAR(255),
    last_analyzed TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(industry_type, year),
    CHECK (year >= 2020 AND year <= 2100)
);

CREATE INDEX idx_sector_analysis_industry ON sector_analysis(industry_type);
CREATE INDEX idx_sector_analysis_year ON sector_analysis(year);


-- ============================================================
-- Department Statistics (Aggregate) Table
-- ============================================================

CREATE TABLE IF NOT EXISTS department_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    year INTEGER NOT NULL DEFAULT 2024,

    -- Employment statistics
    overall_employment_rate DECIMAL(5,2),
    average_hiring_time_days INTEGER,

    -- Salary statistics (entry level)
    entry_level_avg_salary INTEGER,
    entry_level_min_salary INTEGER,
    entry_level_max_salary INTEGER,

    -- Salary statistics (career progression)
    mid_career_avg_salary INTEGER,
    senior_avg_salary INTEGER,
    salary_growth_rate DECIMAL(5,2),  -- Annual percentage growth

    -- Industry distribution
    top_industries JSONB DEFAULT '[]',
    top_cities JSONB DEFAULT '[]',

    -- Metadata
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(department_id, year),
    CHECK (year >= 2020 AND year <= 2100)
);

CREATE INDEX idx_department_statistics_dept ON department_statistics(department_id);
CREATE INDEX idx_department_statistics_year ON department_statistics(year);


-- ============================================================
-- Triggers for updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_department_curriculum_updated_at
    BEFORE UPDATE ON department_curriculum
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_career_opportunities_updated_at
    BEFORE UPDATE ON career_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_salary_expectations_updated_at
    BEFORE UPDATE ON salary_expectations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sector_analysis_updated_at
    BEFORE UPDATE ON sector_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- Sample Data (Optional - for testing)
-- ============================================================

-- Note: Sample data can be inserted after departments table is populated
-- This is just a template for testing

/*
-- Sample curriculum
INSERT INTO department_curriculum (
    department_id,
    total_credits,
    duration_years,
    duration_semesters,
    core_courses,
    elective_courses,
    specialization_tracks,
    skills_gained,
    internship_required
) VALUES (
    'sample-department-uuid',
    240,
    4,
    8,
    '[
        {"code": "CS101", "name": "Introduction to Programming", "credits": 6},
        {"code": "MATH101", "name": "Calculus I", "credits": 6}
    ]'::jsonb,
    '[
        {"code": "CS301", "name": "Machine Learning", "credits": 6},
        {"code": "CS302", "name": "Data Mining", "credits": 6}
    ]'::jsonb,
    ARRAY['Artificial Intelligence', 'Software Engineering', 'Data Science'],
    ARRAY['Programming', 'Problem Solving', 'Algorithm Design'],
    TRUE
);

-- Sample career opportunity
INSERT INTO career_opportunities (
    department_id,
    job_title,
    industry_type,
    employment_rate,
    average_hiring_time_days,
    demand_level,
    required_skills,
    career_growth_potential
) VALUES (
    'sample-department-uuid',
    'Software Engineer',
    'technology',
    92.5,
    45,
    'high',
    ARRAY['Python', 'JavaScript', 'SQL', 'Git'],
    'high'
);

-- Sample salary expectation
INSERT INTO salary_expectations (
    department_id,
    experience_level,
    min_salary,
    max_salary,
    average_salary,
    city,
    industry_type,
    year
) VALUES (
    'sample-department-uuid',
    'entry',
    15000,
    25000,
    20000,
    'Istanbul',
    'technology',
    2024
);

-- Sample sector analysis
INSERT INTO sector_analysis (
    industry_type,
    sector_name,
    market_size_billion_tl,
    annual_growth_rate,
    total_job_openings,
    in_demand_skills,
    future_demand_prediction,
    year
) VALUES (
    'technology',
    'Software Development',
    150.5,
    15.2,
    25000,
    ARRAY['Cloud Computing', 'AI/ML', 'DevOps', 'Cybersecurity'],
    'high',
    2024
);
*/


-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE department_curriculum IS 'Task 103.1: Department curriculum information including courses, credits, and requirements';
COMMENT ON TABLE career_opportunities IS 'Task 103.2: Career opportunities and employment statistics for department graduates';
COMMENT ON TABLE salary_expectations IS 'Task 103.3: Salary expectations by experience level, location, and industry';
COMMENT ON TABLE sector_analysis IS 'Task 103.4: Industry sector analysis including growth trends and job market data';
COMMENT ON TABLE department_statistics IS 'Aggregate statistics combining employment, salary, and sector data for departments';
