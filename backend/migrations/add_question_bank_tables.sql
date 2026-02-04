-- Task 70: Soru Veritabanı Tasarımı Migration
-- Teknofest 2025 Eğitim Eylemci Platformu

-- ============================================================================
-- TASK 70.2: Topic Hierarchy Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS topic_hierarchy (
    id VARCHAR PRIMARY KEY,
    level INTEGER NOT NULL CHECK (level >= 1 AND level <= 5),
    parent_id VARCHAR REFERENCES topic_hierarchy(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    name_tr VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    description TEXT,
    meb_code VARCHAR(100),
    meb_kazanim JSONB,
    osym_relevance FLOAT DEFAULT 0.0 CHECK (osym_relevance >= 0.0 AND osym_relevance <= 1.0),
    osym_frequency INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    average_difficulty FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_topic_code ON topic_hierarchy(code);
CREATE INDEX idx_topic_parent ON topic_hierarchy(parent_id);
CREATE INDEX idx_topic_level ON topic_hierarchy(level);
CREATE INDEX idx_topic_meb_code ON topic_hierarchy(meb_code);

-- ============================================================================
-- TASK 70.2: Question Tags Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS question_tags (
    id VARCHAR PRIMARY KEY,
    tag_name VARCHAR(100) UNIQUE NOT NULL,
    tag_category VARCHAR(50) NOT NULL,
    description TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tag_name ON question_tags(tag_name);
CREATE INDEX idx_tag_category ON question_tags(tag_category);

-- ============================================================================
-- TASK 70.1 & 70.3 & 70.4: Enhanced Question Bank Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS question_bank (
    id VARCHAR PRIMARY KEY,
    
    -- Soru içeriği
    question_text TEXT NOT NULL,
    question_html TEXT,
    question_latex TEXT,
    question_image_url VARCHAR(500),
    question_audio_url VARCHAR(500),
    
    -- Seçenekler
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    option_e TEXT,
    correct_answer VARCHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D', 'E')),
    
    -- Açıklamalar
    explanation TEXT,
    explanation_video_url VARCHAR(500),
    alternative_solutions JSONB,
    
    -- TASK 70.2: Konu etiketleme
    primary_topic_id VARCHAR NOT NULL REFERENCES topic_hierarchy(id),
    secondary_topics JSONB,
    bloom_level INTEGER DEFAULT 1 CHECK (bloom_level >= 1 AND bloom_level <= 6),
    bloom_category VARCHAR(50) DEFAULT 'knowledge',
    
    -- TASK 70.3: 5-level difficulty scale
    difficulty_level VARCHAR(20) NOT NULL DEFAULT 'medium',
    irt_based_difficulty VARCHAR(20) DEFAULT 'medium',
    student_success_rate FLOAT DEFAULT 0.0 CHECK (student_success_rate >= 0.0 AND student_success_rate <= 1.0),
    last_difficulty_update TIMESTAMP WITH TIME ZONE,
    difficulty_update_count INTEGER DEFAULT 0,
    
    -- TASK 70.4: IRT Parameters (4PL Model)
    irt_discrimination FLOAT DEFAULT 1.0 CHECK (irt_discrimination >= 0.1 AND irt_discrimination <= 3.0),
    irt_difficulty FLOAT DEFAULT 0.0 CHECK (irt_difficulty >= -3.0 AND irt_difficulty <= 3.0),
    irt_guessing FLOAT DEFAULT 0.25 CHECK (irt_guessing >= 0.0 AND irt_guessing <= 1.0),
    irt_upper_asymptote FLOAT DEFAULT 1.0 CHECK (irt_upper_asymptote >= 0.0 AND irt_upper_asymptote <= 1.0),
    is_calibrated BOOLEAN DEFAULT FALSE,
    calibration_sample_size INTEGER DEFAULT 0,
    last_calibration_date TIMESTAMP WITH TIME ZONE,
    calibration_quality_score FLOAT DEFAULT 0.0,
    
    -- Türkçe morfoloji analizi
    morphology_complexity FLOAT DEFAULT 0.0,
    word_count INTEGER DEFAULT 0,
    unique_word_count INTEGER DEFAULT 0,
    average_word_length FLOAT DEFAULT 0.0,
    readability_score FLOAT DEFAULT 0.0,
    
    -- İstatistikler
    times_asked INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    times_wrong INTEGER DEFAULT 0,
    times_skipped INTEGER DEFAULT 0,
    average_response_time FLOAT DEFAULT 0.0,
    median_response_time FLOAT DEFAULT 0.0,
    exposure_rate FLOAT DEFAULT 0.0 CHECK (exposure_rate >= 0.0 AND exposure_rate <= 1.0),
    last_used_date TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    exam_type VARCHAR(20) NOT NULL,
    subject_area VARCHAR(50) NOT NULL,
    grade_level INTEGER NOT NULL CHECK (grade_level >= 9 AND grade_level <= 12),
    osym_format_compliant BOOLEAN DEFAULT TRUE,
    osym_year INTEGER,
    quality_score FLOAT DEFAULT 0.0 CHECK (quality_score >= 0.0 AND quality_score <= 100.0),
    quality_review_status VARCHAR(20) DEFAULT 'pending',
    
    -- Sistem alanları
    created_by VARCHAR REFERENCES users(id) ON DELETE CASCADE,
    reviewed_by VARCHAR REFERENCES users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for question_bank
CREATE INDEX idx_qbank_topic ON question_bank(primary_topic_id);
CREATE INDEX idx_qbank_difficulty ON question_bank(difficulty_level);
CREATE INDEX idx_qbank_irt_difficulty ON question_bank(irt_difficulty);
CREATE INDEX idx_qbank_exam_type ON question_bank(exam_type);
CREATE INDEX idx_qbank_subject ON question_bank(subject_area);
CREATE INDEX idx_qbank_grade ON question_bank(grade_level);
CREATE INDEX idx_qbank_calibrated ON question_bank(is_calibrated);
CREATE INDEX idx_qbank_quality ON question_bank(quality_score);
CREATE INDEX idx_qbank_active ON question_bank(is_active);

-- Composite indexes for adaptive test selection
CREATE INDEX idx_qbank_exam_subject_difficulty ON question_bank(exam_type, subject_area, irt_difficulty);
CREATE INDEX idx_qbank_topic_difficulty ON question_bank(primary_topic_id, difficulty_level);
CREATE INDEX idx_qbank_calibrated_active ON question_bank(is_calibrated, is_active, quality_score);

-- ============================================================================
-- TASK 70.2: Question-Tag Association Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS question_tag_associations (
    id VARCHAR PRIMARY KEY,
    question_id VARCHAR NOT NULL REFERENCES question_bank(id) ON DELETE CASCADE,
    tag_id VARCHAR NOT NULL REFERENCES question_tags(id) ON DELETE CASCADE,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(question_id, tag_id)
);

CREATE INDEX idx_qtag_question ON question_tag_associations(question_id);
CREATE INDEX idx_qtag_tag ON question_tag_associations(tag_id);

-- ============================================================================
-- TASK 70.4: IRT Calibration History Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS irt_calibration_history (
    id VARCHAR PRIMARY KEY,
    question_id VARCHAR NOT NULL REFERENCES question_bank(id) ON DELETE CASCADE,
    
    -- Kalibrasyon bilgileri
    calibration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    calibration_method VARCHAR(50) NOT NULL,
    sample_size INTEGER NOT NULL CHECK (sample_size >= 30),
    
    -- Eski parametreler
    old_discrimination FLOAT,
    old_difficulty FLOAT,
    old_guessing FLOAT,
    old_upper_asymptote FLOAT,
    
    -- Yeni parametreler
    new_discrimination FLOAT NOT NULL CHECK (new_discrimination >= 0.1 AND new_discrimination <= 3.0),
    new_difficulty FLOAT NOT NULL CHECK (new_difficulty >= -3.0 AND new_difficulty <= 3.0),
    new_guessing FLOAT NOT NULL CHECK (new_guessing >= 0.0 AND new_guessing <= 1.0),
    new_upper_asymptote FLOAT NOT NULL CHECK (new_upper_asymptote >= 0.0 AND new_upper_asymptote <= 1.0),
    
    -- Kalibrasyon kalitesi
    standard_error FLOAT DEFAULT 0.0,
    convergence_iterations INTEGER DEFAULT 0,
    log_likelihood FLOAT DEFAULT 0.0,
    
    -- Güven aralıkları
    discrimination_ci_lower FLOAT DEFAULT 0.0,
    discrimination_ci_upper FLOAT DEFAULT 0.0,
    difficulty_ci_lower FLOAT DEFAULT 0.0,
    difficulty_ci_upper FLOAT DEFAULT 0.0
);

CREATE INDEX idx_calibration_question ON irt_calibration_history(question_id);
CREATE INDEX idx_calibration_date ON irt_calibration_history(calibration_date);

-- ============================================================================
-- Question Performance Analytics Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS question_performance_analytics (
    id VARCHAR PRIMARY KEY,
    question_id VARCHAR NOT NULL REFERENCES question_bank(id) ON DELETE CASCADE,
    
    -- Analiz dönemi
    analysis_date TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    
    -- Performans metrikleri
    attempts INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    wrong_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    average_response_time FLOAT DEFAULT 0.0,
    
    -- Öğrenci segmentasyonu
    high_ability_success_rate FLOAT DEFAULT 0.0,
    medium_ability_success_rate FLOAT DEFAULT 0.0,
    low_ability_success_rate FLOAT DEFAULT 0.0,
    
    UNIQUE(question_id, analysis_date, period_type)
);

CREATE INDEX idx_qperf_question ON question_performance_analytics(question_id);
CREATE INDEX idx_qperf_date ON question_performance_analytics(analysis_date);
CREATE INDEX idx_qperf_period ON question_performance_analytics(period_type);

-- ============================================================================
-- Sample Data: Topic Hierarchy
-- ============================================================================

-- Ana konular (Level 1)
INSERT INTO topic_hierarchy (id, code, name_tr, level, osym_relevance, osym_frequency) VALUES
('topic-mat', 'MAT', 'Matematik', 1, 1.0, 120),
('topic-tur', 'TUR', 'Türkçe', 1, 1.0, 120),
('topic-fen', 'FEN', 'Fen Bilimleri', 1, 0.9, 80),
('topic-sos', 'SOS', 'Sosyal Bilimler', 1, 0.9, 80);

-- Alt konular (Level 2) - Matematik
INSERT INTO topic_hierarchy (id, code, name_tr, level, parent_id, osym_relevance, osym_frequency) VALUES
('topic-mat-geo', 'MAT.GEO', 'Geometri', 2, 'topic-mat', 0.95, 35),
('topic-mat-alg', 'MAT.ALG', 'Cebir', 2, 'topic-mat', 0.98, 40),
('topic-mat-ana', 'MAT.ANA', 'Analiz', 2, 'topic-mat', 0.85, 25);

-- Detay konular (Level 3) - Geometri
INSERT INTO topic_hierarchy (id, code, name_tr, level, parent_id, osym_relevance, osym_frequency) VALUES
('topic-mat-geo-ucg', 'MAT.GEO.UCG', 'Üçgenler', 3, 'topic-mat-geo', 0.92, 15),
('topic-mat-geo-drt', 'MAT.GEO.DRT', 'Dörtgenler', 3, 'topic-mat-geo', 0.88, 12),
('topic-mat-geo-dai', 'MAT.GEO.DAI', 'Daire', 3, 'topic-mat-geo', 0.85, 8);

-- ============================================================================
-- Sample Data: Question Tags
-- ============================================================================

INSERT INTO question_tags (id, tag_name, tag_category, description) VALUES
('tag-problem-solving', 'problem_solving', 'skill', 'Problem çözme becerisi'),
('tag-critical-thinking', 'critical_thinking', 'skill', 'Eleştirel düşünme'),
('tag-visual', 'visual', 'format', 'Görsel içerikli soru'),
('tag-calculation', 'calculation', 'skill', 'Hesaplama gerektiren'),
('tag-theorem', 'theorem', 'concept', 'Teorem bilgisi');

COMMENT ON TABLE question_bank IS 'Task 70: Gelişmiş soru bankası - 10,000+ soru için optimize edilmiş';
COMMENT ON TABLE topic_hierarchy IS 'Task 70.2: Hiyerarşik konu taksonomisi';
COMMENT ON TABLE irt_calibration_history IS 'Task 70.4: IRT parametre kalibrasyon geçmişi';
COMMENT ON COLUMN question_bank.irt_discrimination IS 'Task 70.4: IRT a parametresi (ayırt edicilik)';
COMMENT ON COLUMN question_bank.irt_difficulty IS 'Task 70.4: IRT b parametresi (zorluk)';
COMMENT ON COLUMN question_bank.irt_guessing IS 'Task 70.4: IRT c parametresi (tahmin)';
COMMENT ON COLUMN question_bank.irt_upper_asymptote IS 'Task 70.4: IRT d parametresi (üst asimptot)';
