-- Migration: Create parent and teacher relationship tables
-- Created: 2025-10-28
-- Priority: HIGH (Phase 2)
-- Description: Parent-child relationships, teacher profiles

-- Parent-Child Relationships Table
CREATE TABLE IF NOT EXISTS parent_children (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    child_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) CHECK (relationship_type IN ('parent', 'guardian', 'mentor')),
    is_primary BOOLEAN DEFAULT FALSE,
    can_view_performance BOOLEAN DEFAULT TRUE,
    can_view_exams BOOLEAN DEFAULT TRUE,
    can_receive_notifications BOOLEAN DEFAULT TRUE,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(parent_user_id, child_user_id)
);

-- Teacher Profiles Table
CREATE TABLE IF NOT EXISTS teacher_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    subjects JSONB DEFAULT '[]'::jsonb,
    grade_levels JSONB DEFAULT '[]'::jsonb,
    education VARCHAR(500),
    years_of_experience INTEGER,
    hourly_rate DECIMAL(10, 2),
    rating DECIMAL(3, 2),
    total_reviews INTEGER DEFAULT 0,
    total_appointments INTEGER DEFAULT 0,
    online_teaching BOOLEAN DEFAULT TRUE,
    in_person_teaching BOOLEAN DEFAULT FALSE,
    city VARCHAR(100),
    verification_status VARCHAR(50) DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'rejected')),
    verified_at TIMESTAMP,
    verified_by UUID,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id)
);

-- Teacher Expertise Table
CREATE TABLE IF NOT EXISTS teacher_expertise (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,
    subject VARCHAR(100) NOT NULL,
    topic VARCHAR(255),
    proficiency_level VARCHAR(50) CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    years_teaching INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teacher Certifications Table
CREATE TABLE IF NOT EXISTS teacher_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,
    certification_name VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    credential_id VARCHAR(255),
    credential_url TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    verified_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teacher Availability Slots Table
CREATE TABLE IF NOT EXISTS teacher_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_recurring BOOLEAN DEFAULT TRUE,
    specific_date DATE,
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teacher-Student Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    appointment_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    appointment_type VARCHAR(50) CHECK (appointment_type IN ('online', 'in_person')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')),
    meeting_url TEXT,
    topic VARCHAR(255),
    notes TEXT,
    student_notes TEXT,
    teacher_notes TEXT,
    confirmed_at TIMESTAMP,
    confirmed_by UUID,
    cancelled_at TIMESTAMP,
    cancelled_by UUID,
    cancellation_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teacher Reviews Table
CREATE TABLE IF NOT EXISTS teacher_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teacher_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    teaching_quality INTEGER CHECK (teaching_quality BETWEEN 1 AND 5),
    communication INTEGER CHECK (communication BETWEEN 1 AND 5),
    punctuality INTEGER CHECK (punctuality BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(appointment_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_parent_children_parent ON parent_children(parent_user_id);
CREATE INDEX IF NOT EXISTS idx_parent_children_child ON parent_children(child_user_id);

CREATE INDEX IF NOT EXISTS idx_teacher_profiles_user_id ON teacher_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_teacher_profiles_active ON teacher_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_teacher_profiles_verification ON teacher_profiles(verification_status);
CREATE INDEX IF NOT EXISTS idx_teacher_profiles_city ON teacher_profiles(city);
CREATE INDEX IF NOT EXISTS idx_teacher_profiles_rating ON teacher_profiles(rating DESC);

CREATE INDEX IF NOT EXISTS idx_teacher_expertise_teacher ON teacher_expertise(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_expertise_subject ON teacher_expertise(subject);

CREATE INDEX IF NOT EXISTS idx_teacher_certifications_teacher ON teacher_certifications(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_certifications_verified ON teacher_certifications(is_verified);

CREATE INDEX IF NOT EXISTS idx_teacher_availability_teacher ON teacher_availability(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_availability_day ON teacher_availability(day_of_week);
CREATE INDEX IF NOT EXISTS idx_teacher_availability_blocked ON teacher_availability(is_blocked);

CREATE INDEX IF NOT EXISTS idx_appointments_teacher ON appointments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_appointments_student ON appointments(student_id);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);

CREATE INDEX IF NOT EXISTS idx_teacher_reviews_teacher ON teacher_reviews(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_reviews_student ON teacher_reviews(student_id);
CREATE INDEX IF NOT EXISTS idx_teacher_reviews_rating ON teacher_reviews(rating);

-- Triggers
CREATE OR REPLACE FUNCTION update_teacher_tables_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_parent_children_updated_at
    BEFORE UPDATE ON parent_children
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_tables_updated_at();

CREATE TRIGGER trigger_teacher_profiles_updated_at
    BEFORE UPDATE ON teacher_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_tables_updated_at();

CREATE TRIGGER trigger_teacher_availability_updated_at
    BEFORE UPDATE ON teacher_availability
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_tables_updated_at();

CREATE TRIGGER trigger_appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_tables_updated_at();

CREATE TRIGGER trigger_teacher_reviews_updated_at
    BEFORE UPDATE ON teacher_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_teacher_tables_updated_at();

-- Comments
COMMENT ON TABLE parent_children IS 'Parent-child relationship mapping';
COMMENT ON TABLE teacher_profiles IS 'Teacher profile information';
COMMENT ON TABLE teacher_expertise IS 'Teacher subject expertise and proficiency';
COMMENT ON TABLE teacher_certifications IS 'Teacher certifications and credentials';
COMMENT ON TABLE teacher_availability IS 'Teacher availability schedule';
COMMENT ON TABLE appointments IS 'Teacher-student appointments';
COMMENT ON TABLE teacher_reviews IS 'Teacher reviews by students';
