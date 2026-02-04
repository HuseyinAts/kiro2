-- Task 104: University Information Tables Migration
-- Campus Info, City Living Costs, Dormitory Info, Scholarship Programs

-- ============================================================
-- Enums
-- ============================================================

CREATE TYPE campus_type AS ENUM (
    'main_campus',
    'satellite_campus',
    'medical_campus',
    'research_campus'
);

CREATE TYPE accommodation_type AS ENUM (
    'state_dormitory',
    'university_dormitory',
    'private_dormitory',
    'apartment',
    'shared_apartment'
);

CREATE TYPE scholarship_type AS ENUM (
    'full_scholarship',
    'partial_scholarship',
    'merit_based',
    'need_based',
    'sports',
    'academic_excellence',
    'special_talent'
);


-- ============================================================
-- Task 104.1: Campus Information Table
-- ============================================================

CREATE TABLE IF NOT EXISTS campus_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE CASCADE,

    -- Basic info
    campus_name VARCHAR(255) NOT NULL,
    campus_type campus_type DEFAULT 'main_campus',
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100),
    address TEXT,

    -- Size
    total_area_sqm INTEGER,
    building_count INTEGER,

    -- Facilities
    libraries JSONB DEFAULT '[]',
    sports_facilities TEXT[] DEFAULT '{}',
    laboratories JSONB DEFAULT '[]',
    dining_facilities JSONB DEFAULT '[]',

    -- Student services
    health_center BOOLEAN DEFAULT FALSE,
    counseling_center BOOLEAN DEFAULT FALSE,
    career_center BOOLEAN DEFAULT FALSE,
    international_office BOOLEAN DEFAULT FALSE,

    -- Technology
    wifi_available BOOLEAN DEFAULT TRUE,
    computer_labs INTEGER DEFAULT 0,
    online_resources BOOLEAN DEFAULT TRUE,

    -- Student life
    student_clubs JSONB DEFAULT '[]',
    total_student_clubs INTEGER DEFAULT 0,
    cultural_centers TEXT[] DEFAULT '{}',
    events_per_year INTEGER,

    -- Transportation
    public_transport_access BOOLEAN DEFAULT TRUE,
    shuttle_service BOOLEAN DEFAULT FALSE,
    parking_spaces INTEGER,
    bicycle_friendly BOOLEAN DEFAULT FALSE,

    -- Accessibility
    wheelchair_accessible BOOLEAN DEFAULT TRUE,
    disability_support BOOLEAN DEFAULT FALSE,

    -- Additional info
    description TEXT,
    highlights TEXT[] DEFAULT '{}',
    photos TEXT[] DEFAULT '{}',

    -- Contact
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_campus_info_university ON campus_info(university_id);
CREATE INDEX idx_campus_info_city ON campus_info(city);
CREATE INDEX idx_campus_info_type ON campus_info(campus_type);


-- ============================================================
-- Task 104.2: City Living Costs Table
-- ============================================================

CREATE TABLE IF NOT EXISTS city_living_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Location
    city VARCHAR(100) NOT NULL,
    region VARCHAR(100),

    -- Accommodation costs (monthly, in TRY)
    rent_studio_min INTEGER,
    rent_studio_max INTEGER,
    rent_studio_avg INTEGER,

    rent_1br_min INTEGER,
    rent_1br_max INTEGER,
    rent_1br_avg INTEGER,

    rent_2br_min INTEGER,
    rent_2br_max INTEGER,
    rent_2br_avg INTEGER,

    -- Shared accommodation
    shared_room_min INTEGER,
    shared_room_max INTEGER,
    shared_room_avg INTEGER,

    -- Utilities (monthly, in TRY)
    utilities_min INTEGER,
    utilities_max INTEGER,
    utilities_avg INTEGER,

    -- Food costs (monthly, in TRY)
    food_budget_min INTEGER,
    food_budget_max INTEGER,
    food_budget_avg INTEGER,

    meal_restaurant_avg INTEGER,
    meal_inexpensive_avg INTEGER,
    groceries_weekly_avg INTEGER,

    -- Transportation costs (monthly, in TRY)
    public_transport_monthly INTEGER,
    public_transport_single INTEGER,
    taxi_start_fare INTEGER,
    taxi_per_km INTEGER,
    student_transport_discount DECIMAL(5,2),

    -- Other expenses (monthly, in TRY)
    entertainment_min INTEGER,
    entertainment_max INTEGER,
    entertainment_avg INTEGER,

    books_supplies_avg INTEGER,
    personal_care_avg INTEGER,
    phone_internet_avg INTEGER,

    -- Total estimates (monthly, in TRY)
    total_min_budget INTEGER,
    total_avg_budget INTEGER,
    total_comfortable_budget INTEGER,

    -- Additional info
    cost_of_living_index DECIMAL(10,2),
    student_discount_available BOOLEAN DEFAULT TRUE,
    notes TEXT,

    -- Time period
    year INTEGER NOT NULL DEFAULT 2024,
    month INTEGER,
    currency VARCHAR(10) DEFAULT 'TRY',

    -- Data source
    data_source VARCHAR(255),
    sample_size INTEGER,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (year >= 2020 AND year <= 2100)
);

CREATE INDEX idx_city_living_cost_city ON city_living_costs(city);
CREATE INDEX idx_city_living_cost_year ON city_living_costs(year);
CREATE INDEX idx_city_living_cost_city_year ON city_living_costs(city, year);


-- ============================================================
-- Task 104.3: Dormitory Information Table
-- ============================================================

CREATE TABLE IF NOT EXISTS dormitory_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID REFERENCES universities(id) ON DELETE CASCADE,

    -- Basic info
    name VARCHAR(255) NOT NULL,
    accommodation_type accommodation_type NOT NULL,
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100),
    address TEXT,

    -- Capacity
    total_capacity INTEGER,
    available_spaces INTEGER,
    gender VARCHAR(20),

    -- Room types
    room_types JSONB DEFAULT '[]',
    single_rooms INTEGER DEFAULT 0,
    double_rooms INTEGER DEFAULT 0,
    triple_rooms INTEGER DEFAULT 0,
    quad_rooms INTEGER DEFAULT 0,

    -- Costs (monthly, in TRY)
    price_min INTEGER,
    price_max INTEGER,
    price_avg INTEGER,

    deposit_required INTEGER,
    meals_included BOOLEAN DEFAULT FALSE,
    meal_plan_cost INTEGER,

    -- Facilities
    wifi_included BOOLEAN DEFAULT TRUE,
    laundry_facilities BOOLEAN DEFAULT TRUE,
    study_rooms BOOLEAN DEFAULT FALSE,
    common_areas BOOLEAN DEFAULT TRUE,
    kitchen_access BOOLEAN DEFAULT FALSE,
    gym BOOLEAN DEFAULT FALSE,
    library BOOLEAN DEFAULT FALSE,
    prayer_room BOOLEAN DEFAULT FALSE,

    -- Room amenities
    furniture_included BOOLEAN DEFAULT TRUE,
    air_conditioning BOOLEAN DEFAULT FALSE,
    heating BOOLEAN DEFAULT TRUE,
    private_bathroom BOOLEAN DEFAULT FALSE,

    -- Security
    security_24_7 BOOLEAN DEFAULT TRUE,
    cctv BOOLEAN DEFAULT FALSE,
    key_card_access BOOLEAN DEFAULT FALSE,

    -- Rules
    curfew VARCHAR(100),
    visitors_allowed BOOLEAN DEFAULT TRUE,
    smoking_allowed BOOLEAN DEFAULT FALSE,
    pets_allowed BOOLEAN DEFAULT FALSE,

    -- Application
    application_period_start VARCHAR(50),
    application_period_end VARCHAR(50),
    application_requirements TEXT[] DEFAULT '{}',
    priority_criteria TEXT[] DEFAULT '{}',

    -- Distance
    distance_to_campus_km DECIMAL(10,2),
    transportation_to_campus TEXT[] DEFAULT '{}',

    -- Additional info
    description TEXT,
    amenities TEXT[] DEFAULT '{}',
    photos TEXT[] DEFAULT '{}',

    -- Contact
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),

    -- Ratings
    cleanliness_rating DECIMAL(3,2),
    location_rating DECIMAL(3,2),
    facilities_rating DECIMAL(3,2),
    value_rating DECIMAL(3,2),
    overall_rating DECIMAL(3,2),

    -- Metadata
    verified BOOLEAN DEFAULT FALSE,
    year INTEGER DEFAULT 2024,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dormitory_info_university ON dormitory_info(university_id);
CREATE INDEX idx_dormitory_info_city ON dormitory_info(city);
CREATE INDEX idx_dormitory_info_type ON dormitory_info(accommodation_type);
CREATE INDEX idx_dormitory_info_price ON dormitory_info(price_avg);


-- ============================================================
-- Task 104.4: Scholarship Programs Table
-- ============================================================

CREATE TABLE IF NOT EXISTS scholarship_programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID REFERENCES universities(id) ON DELETE CASCADE,

    -- Basic info
    name VARCHAR(255) NOT NULL,
    scholarship_type scholarship_type NOT NULL,
    provider VARCHAR(255),

    -- Coverage
    coverage_percentage DECIMAL(5,2),
    covers_tuition BOOLEAN DEFAULT TRUE,
    covers_accommodation BOOLEAN DEFAULT FALSE,
    covers_meals BOOLEAN DEFAULT FALSE,
    covers_books BOOLEAN DEFAULT FALSE,
    covers_transportation BOOLEAN DEFAULT FALSE,

    -- Amount
    amount_min INTEGER,
    amount_max INTEGER,
    amount_avg INTEGER,
    monthly_stipend INTEGER,

    -- Eligibility
    min_exam_score DECIMAL(10,2),
    min_high_school_gpa DECIMAL(4,2),
    min_university_gpa DECIMAL(4,2),
    income_limit INTEGER,

    citizenship_required VARCHAR(100),
    age_limit INTEGER,

    -- Requirements
    eligibility_criteria TEXT[] DEFAULT '{}',
    required_documents TEXT[] DEFAULT '{}',
    special_requirements TEXT,

    -- Application
    application_period_start VARCHAR(50),
    application_period_end VARCHAR(50),
    application_process TEXT,
    application_url VARCHAR(255),

    -- Selection
    selection_criteria JSONB DEFAULT '{}',
    number_of_recipients INTEGER,
    acceptance_rate DECIMAL(5,2),

    -- Duration
    renewable BOOLEAN DEFAULT TRUE,
    max_duration_years INTEGER,
    renewal_requirements TEXT[] DEFAULT '{}',

    -- Obligations
    service_obligation BOOLEAN DEFAULT FALSE,
    service_duration_years INTEGER,
    gpa_requirement DECIMAL(4,2),

    -- Additional benefits
    additional_benefits TEXT[] DEFAULT '{}',
    networking_opportunities BOOLEAN DEFAULT FALSE,
    career_support BOOLEAN DEFAULT FALSE,

    -- Statistics
    total_recipients INTEGER,
    success_rate DECIMAL(5,2),

    -- Additional info
    description TEXT,
    terms_and_conditions TEXT,

    -- Contact
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),

    -- Metadata
    active BOOLEAN DEFAULT TRUE,
    year INTEGER DEFAULT 2024,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scholarship_program_university ON scholarship_programs(university_id);
CREATE INDEX idx_scholarship_program_type ON scholarship_programs(scholarship_type);
CREATE INDEX idx_scholarship_program_active ON scholarship_programs(active);
CREATE INDEX idx_scholarship_program_coverage ON scholarship_programs(coverage_percentage);


-- ============================================================
-- University Statistics (Aggregate) Table
-- ============================================================

CREATE TABLE IF NOT EXISTS university_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    year INTEGER NOT NULL DEFAULT 2024,

    -- Campus statistics
    total_campuses INTEGER DEFAULT 0,
    total_campus_area_sqm INTEGER,
    total_student_clubs INTEGER DEFAULT 0,
    has_health_center BOOLEAN DEFAULT FALSE,
    has_career_center BOOLEAN DEFAULT FALSE,

    -- Living cost statistics
    city VARCHAR(100),
    avg_monthly_cost INTEGER,
    avg_rent INTEGER,
    cost_of_living_index DECIMAL(10,2),

    -- Dormitory statistics
    total_dormitory_capacity INTEGER DEFAULT 0,
    avg_dormitory_cost INTEGER,
    dormitory_types TEXT[] DEFAULT '{}',

    -- Scholarship statistics
    total_scholarships INTEGER DEFAULT 0,
    full_scholarships INTEGER DEFAULT 0,
    partial_scholarships INTEGER DEFAULT 0,
    avg_scholarship_amount INTEGER,
    scholarship_acceptance_rate DECIMAL(5,2),

    -- Combined affordability score
    affordability_score DECIMAL(3,2),

    -- Metadata
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(university_id, year),
    CHECK (year >= 2020 AND year <= 2100),
    CHECK (affordability_score >= 1.0 AND affordability_score <= 10.0)
);

CREATE INDEX idx_university_statistics_university ON university_statistics(university_id);
CREATE INDEX idx_university_statistics_year ON university_statistics(year);
CREATE INDEX idx_university_statistics_university_year ON university_statistics(university_id, year);


-- ============================================================
-- Triggers for updated_at
-- ============================================================

CREATE TRIGGER update_campus_info_updated_at
    BEFORE UPDATE ON campus_info
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_city_living_costs_updated_at
    BEFORE UPDATE ON city_living_costs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dormitory_info_updated_at
    BEFORE UPDATE ON dormitory_info
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scholarship_programs_updated_at
    BEFORE UPDATE ON scholarship_programs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE campus_info IS 'Task 104.1: Campus information including facilities, student life, and services';
COMMENT ON TABLE city_living_costs IS 'Task 104.2: City living cost data for student budget planning';
COMMENT ON TABLE dormitory_info IS 'Task 104.3: Dormitory and accommodation information with costs and facilities';
COMMENT ON TABLE scholarship_programs IS 'Task 104.4: Scholarship and financial aid program details';
COMMENT ON TABLE university_statistics IS 'Aggregate statistics combining campus, living costs, dormitory, and scholarship data';
