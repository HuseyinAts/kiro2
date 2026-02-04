-- ============================================================
-- Task 107: Teacher Pool Database Migration
-- ============================================================

-- Create enum types
CREATE TYPE teacher_status AS ENUM ('pending', 'verified', 'suspended', 'rejected');
CREATE TYPE verification_status AS ENUM ('not_submitted', 'pending', 'approved', 'rejected');
CREATE TYPE subject_expertise AS ENUM (
    'mathematics', 'physics', 'chemistry', 'biology',
    'turkish', 'history', 'geography', 'english',
    'philosophy', 'literature', 'geometry'
);
CREATE TYPE grade_level AS ENUM (
    'grade_9', 'grade_10', 'grade_11', 'grade_12',
    'university_prep', 'all_grades'
);
CREATE TYPE certification_type AS ENUM (
    'teaching_license', 'university_degree', 'masters_degree',
    'phd_degree', 'training_certificate', 'experience_certificate'
);
CREATE TYPE day_of_week AS ENUM (
    'monday', 'tuesday', 'wednesday', 'thursday',
    'friday', 'saturday', 'sunday'
);
CREATE TYPE time_slot_status AS ENUM ('available', 'booked', 'blocked');
CREATE TYPE appointment_status AS ENUM (
    'pending', 'confirmed', 'cancelled', 'completed', 'no_show'
);
CREATE TYPE appointment_type AS ENUM (
    'one_on_one', 'group_session', 'question_answer', 'exam_prep'
);

-- ============================================================
-- Task 107.1: Teacher Profiles Table
-- ============================================================

CREATE TABLE teacher_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Basic Information
    full_name VARCHAR(255) NOT NULL,
    title VARCHAR(100),
    bio TEXT,
    profile_photo_url VARCHAR(500),

    -- Contact
    phone VARCHAR(20),
    email VARCHAR(255),
    city VARCHAR(100),
    district VARCHAR(100),

    -- Professional Information
    years_of_experience INTEGER DEFAULT 0,
    education_level VARCHAR(100),
    university VARCHAR(255),
    department VARCHAR(255),
    graduation_year INTEGER,

    -- Status
    status teacher_status DEFAULT 'pending' NOT NULL,
    verification_status verification_status DEFAULT 'not_submitted',
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES users(id),

    -- Ratings & Statistics
    average_rating FLOAT DEFAULT 0.0,
    total_reviews INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    total_students INTEGER DEFAULT 0,

    -- Pricing
    hourly_rate FLOAT,
    currency VARCHAR(10) DEFAULT 'TRY',

    -- Settings
    is_accepting_students BOOLEAN DEFAULT TRUE,
    max_students INTEGER DEFAULT 50,
    online_teaching BOOLEAN DEFAULT TRUE,
    in_person_teaching BOOLEAN DEFAULT FALSE,

    -- Metadata
    application_notes TEXT,
    admin_notes TEXT,
    rejection_reason TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for teacher_profiles
CREATE INDEX idx_teacher_profiles_user_id ON teacher_profiles(user_id);
CREATE INDEX idx_teacher_profiles_status ON teacher_profiles(status);
CREATE INDEX idx_teacher_profiles_city ON teacher_profiles(city);
CREATE INDEX idx_teacher_profiles_rating ON teacher_profiles(average_rating DESC);
CREATE INDEX idx_teacher_profiles_accepting ON teacher_profiles(is_accepting_students) WHERE is_accepting_students = TRUE;

-- ============================================================
-- Task 107.2: Teacher Expertise Table
-- ============================================================

CREATE TABLE teacher_expertise (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,

    -- Expertise Details
    subject subject_expertise NOT NULL,
    grade_levels TEXT[], -- Array of grade levels

    -- Proficiency
    proficiency_level VARCHAR(50),
    years_teaching_subject INTEGER DEFAULT 0,

    -- Specializations
    specializations JSONB DEFAULT '[]'::JSONB,
    exam_types JSONB DEFAULT '[]'::JSONB,

    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for teacher_expertise
CREATE INDEX idx_teacher_expertise_teacher_id ON teacher_expertise(teacher_id);
CREATE INDEX idx_teacher_expertise_subject ON teacher_expertise(subject);
CREATE INDEX idx_teacher_expertise_verified ON teacher_expertise(is_verified);

-- ============================================================
-- Task 107.2: Teacher Certifications Table
-- ============================================================

CREATE TABLE teacher_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,

    -- Certification Details
    certification_type certification_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    credential_id VARCHAR(100),

    -- Documentation
    document_url VARCHAR(500),
    description TEXT,

    -- Verification
    verification_status verification_status DEFAULT 'pending',
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES users(id),
    rejection_reason TEXT,

    -- Display
    is_featured BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for teacher_certifications
CREATE INDEX idx_teacher_certifications_teacher_id ON teacher_certifications(teacher_id);
CREATE INDEX idx_teacher_certifications_type ON teacher_certifications(certification_type);
CREATE INDEX idx_teacher_certifications_verification ON teacher_certifications(verification_status);

-- ============================================================
-- Task 107.3: Teacher Availability Table
-- ============================================================

CREATE TABLE teacher_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,

    -- Time Slot
    day_of_week day_of_week NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,

    -- Date Range
    specific_date DATE, -- For specific date overrides
    valid_from DATE,
    valid_until DATE,

    -- Status
    status time_slot_status DEFAULT 'available',

    -- Capacity
    max_students INTEGER DEFAULT 1,
    current_bookings INTEGER DEFAULT 0,

    -- Metadata
    notes TEXT,
    is_recurring BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for teacher_availability
CREATE INDEX idx_teacher_availability_teacher_id ON teacher_availability(teacher_id);
CREATE INDEX idx_teacher_availability_day ON teacher_availability(day_of_week);
CREATE INDEX idx_teacher_availability_status ON teacher_availability(status) WHERE status = 'available';
CREATE INDEX idx_teacher_availability_date ON teacher_availability(specific_date) WHERE specific_date IS NOT NULL;

-- ============================================================
-- Task 107.4: Appointments Table
-- ============================================================

CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    availability_slot_id UUID REFERENCES teacher_availability(id),

    -- Appointment Details
    appointment_type appointment_type DEFAULT 'one_on_one',
    subject subject_expertise,

    -- Schedule
    scheduled_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 60,

    -- Status
    status appointment_status DEFAULT 'pending',

    -- Student Information
    topic VARCHAR(255),
    description TEXT,
    student_notes TEXT,

    -- Teacher Information
    teacher_notes TEXT,
    preparation_materials JSONB DEFAULT '[]'::JSONB,

    -- Confirmation
    confirmed_at TIMESTAMP WITH TIME ZONE,
    confirmed_by UUID REFERENCES users(id),

    -- Cancellation
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancelled_by UUID REFERENCES users(id),
    cancellation_reason TEXT,

    -- Completion
    completed_at TIMESTAMP WITH TIME ZONE,
    session_summary TEXT,
    homework_assigned TEXT,

    -- Meeting Details
    meeting_url VARCHAR(500),
    meeting_id VARCHAR(100),
    meeting_password VARCHAR(100),

    -- Reminders
    reminder_sent_at TIMESTAMP WITH TIME ZONE,
    reminder_count INTEGER DEFAULT 0,

    -- Pricing
    price FLOAT,
    currency VARCHAR(10) DEFAULT 'TRY',
    payment_status VARCHAR(50),

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for appointments
CREATE INDEX idx_appointments_teacher_id ON appointments(teacher_id);
CREATE INDEX idx_appointments_student_id ON appointments(student_id);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_date ON appointments(scheduled_date);
CREATE INDEX idx_appointments_teacher_date ON appointments(teacher_id, scheduled_date);
CREATE INDEX idx_appointments_student_date ON appointments(student_id, scheduled_date);

-- ============================================================
-- Task 107.4: Appointment Reminders Table
-- ============================================================

CREATE TABLE appointment_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,

    -- Reminder Details
    remind_at TIMESTAMP WITH TIME ZONE NOT NULL,
    reminder_type VARCHAR(50), -- email, sms, push

    -- Status
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE,

    -- Recipient
    recipient_type VARCHAR(50), -- student or teacher
    recipient_id UUID REFERENCES users(id),

    -- Message
    message_template VARCHAR(100),
    message_sent TEXT,

    -- Delivery
    delivery_status VARCHAR(50),
    error_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for appointment_reminders
CREATE INDEX idx_appointment_reminders_appointment_id ON appointment_reminders(appointment_id);
CREATE INDEX idx_appointment_reminders_pending ON appointment_reminders(remind_at)
    WHERE is_sent = FALSE;

-- ============================================================
-- Teacher Reviews Table
-- ============================================================

CREATE TABLE teacher_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id),

    -- Ratings (1-5 stars)
    overall_rating INTEGER NOT NULL CHECK (overall_rating >= 1 AND overall_rating <= 5),
    teaching_quality INTEGER CHECK (teaching_quality >= 1 AND teaching_quality <= 5),
    communication INTEGER CHECK (communication >= 1 AND communication <= 5),
    punctuality INTEGER CHECK (punctuality >= 1 AND punctuality <= 5),
    helpfulness INTEGER CHECK (helpfulness >= 1 AND helpfulness <= 5),

    -- Review Text
    title VARCHAR(255),
    content TEXT,

    -- Response
    teacher_response TEXT,
    responded_at TIMESTAMP WITH TIME ZONE,

    -- Moderation
    is_verified BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    is_hidden BOOLEAN DEFAULT FALSE,

    -- Helpfulness
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for teacher_reviews
CREATE INDEX idx_teacher_reviews_teacher_id ON teacher_reviews(teacher_id);
CREATE INDEX idx_teacher_reviews_student_id ON teacher_reviews(student_id);
CREATE INDEX idx_teacher_reviews_visible ON teacher_reviews(teacher_id, created_at DESC)
    WHERE is_hidden = FALSE;
CREATE INDEX idx_teacher_reviews_rating ON teacher_reviews(overall_rating);

-- ============================================================
-- Teacher Statistics Table
-- ============================================================

CREATE TABLE teacher_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL UNIQUE REFERENCES teacher_profiles(id) ON DELETE CASCADE,

    -- Session Statistics
    total_sessions INTEGER DEFAULT 0,
    completed_sessions INTEGER DEFAULT 0,
    cancelled_sessions INTEGER DEFAULT 0,
    no_show_sessions INTEGER DEFAULT 0,

    -- Student Statistics
    total_students INTEGER DEFAULT 0,
    active_students INTEGER DEFAULT 0,

    -- Rating Statistics
    average_rating FLOAT DEFAULT 0.0,
    total_reviews INTEGER DEFAULT 0,
    five_star_count INTEGER DEFAULT 0,
    four_star_count INTEGER DEFAULT 0,
    three_star_count INTEGER DEFAULT 0,
    two_star_count INTEGER DEFAULT 0,
    one_star_count INTEGER DEFAULT 0,

    -- Response Statistics
    average_response_time_minutes INTEGER DEFAULT 0,

    -- Financial Statistics
    total_earnings FLOAT DEFAULT 0.0,
    this_month_earnings FLOAT DEFAULT 0.0,

    -- Time Statistics
    total_teaching_hours FLOAT DEFAULT 0.0,
    this_month_hours FLOAT DEFAULT 0.0,

    -- Subject Breakdown
    subject_stats JSONB DEFAULT '{}'::JSONB,

    -- Monthly Data
    monthly_data JSONB DEFAULT '{}'::JSONB,

    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for teacher_statistics
CREATE INDEX idx_teacher_statistics_teacher_id ON teacher_statistics(teacher_id);

-- ============================================================
-- Triggers for updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_teacher_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_teacher_profiles_updated_at
    BEFORE UPDATE ON teacher_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_updated_at();

CREATE TRIGGER trigger_teacher_expertise_updated_at
    BEFORE UPDATE ON teacher_expertise
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_updated_at();

CREATE TRIGGER trigger_teacher_certifications_updated_at
    BEFORE UPDATE ON teacher_certifications
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_updated_at();

CREATE TRIGGER trigger_teacher_availability_updated_at
    BEFORE UPDATE ON teacher_availability
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_updated_at();

CREATE TRIGGER trigger_appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_updated_at();

CREATE TRIGGER trigger_teacher_reviews_updated_at
    BEFORE UPDATE ON teacher_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_updated_at();

CREATE TRIGGER trigger_teacher_statistics_updated_at
    BEFORE UPDATE ON teacher_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_updated_at();

-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE teacher_profiles IS 'Task 107.1: Teacher registration and profile management';
COMMENT ON TABLE teacher_expertise IS 'Task 107.2: Teacher subject expertise and grade level specialization';
COMMENT ON TABLE teacher_certifications IS 'Task 107.2: Teacher certifications and credentials';
COMMENT ON TABLE teacher_availability IS 'Task 107.3: Teacher availability calendar and time slots';
COMMENT ON TABLE appointments IS 'Task 107.4: Appointment scheduling and management';
COMMENT ON TABLE appointment_reminders IS 'Task 107.4: Appointment reminder notifications';
COMMENT ON TABLE teacher_reviews IS 'Student reviews and ratings for teachers';
COMMENT ON TABLE teacher_statistics IS 'Aggregated statistics for teacher performance';
