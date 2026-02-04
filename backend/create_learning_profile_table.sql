-- Create student_learning_profiles table for VARK + Felder-Silverman profiles
-- Part of Mock Data Cleanup - Phase 4
-- Replaces in-memory self.student_profiles dictionary

CREATE TABLE IF NOT EXISTS student_learning_profiles (
    -- Primary key
    id VARCHAR PRIMARY KEY,

    -- Foreign key to users table
    student_id VARCHAR NOT NULL UNIQUE,

    -- VARK dimensions (0.0-1.0 range)
    vark_visual REAL NOT NULL DEFAULT 0.0,
    vark_auditory REAL NOT NULL DEFAULT 0.0,
    vark_reading REAL NOT NULL DEFAULT 0.0,
    vark_kinesthetic REAL NOT NULL DEFAULT 0.0,

    -- Felder-Silverman dimensions (-1.0 to +1.0 range)
    felder_active_reflective REAL NOT NULL DEFAULT 0.0,
    felder_sensing_intuitive REAL NOT NULL DEFAULT 0.0,
    felder_visual_verbal REAL NOT NULL DEFAULT 0.0,
    felder_sequential_global REAL NOT NULL DEFAULT 0.0,

    -- Computed values
    hybrid_code VARCHAR(20) NOT NULL,
    dominant_vark_style VARCHAR(20) NOT NULL,
    dominant_felder_dimension VARCHAR(30) NOT NULL,

    -- Metadata
    confidence_score REAL NOT NULL DEFAULT 0.0,
    profile_description TEXT,

    -- Behavioral data snapshots (JSON)
    behavioral_data_snapshot TEXT,  -- JSON stored as TEXT in SQLite
    questionnaire_responses TEXT,   -- JSON stored as TEXT in SQLite

    -- Timestamps
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_learning_profiles_student ON student_learning_profiles(student_id);
CREATE INDEX IF NOT EXISTS idx_learning_profiles_hybrid_code ON student_learning_profiles(hybrid_code);
CREATE INDEX IF NOT EXISTS idx_learning_profiles_updated ON student_learning_profiles(updated_at);

-- Trigger to update updated_at timestamp (SQLite version)
CREATE TRIGGER IF NOT EXISTS update_learning_profile_timestamp
AFTER UPDATE ON student_learning_profiles
FOR EACH ROW
BEGIN
    UPDATE student_learning_profiles
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
