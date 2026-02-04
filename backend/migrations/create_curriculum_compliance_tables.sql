-- Müfredat Uyumluluk Sistemi Veritabanı Tabloları
-- MEB ve ÖSYM müfredat standartları için tablo yapıları

-- MEB Müfredat Standartları Tablosu
CREATE TABLE IF NOT EXISTS meb_curriculum_standards (
    id VARCHAR(255) PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,
    grade_level VARCHAR(10) NOT NULL,
    unit_name VARCHAR(255) NOT NULL,
    topic_name VARCHAR(255) NOT NULL,
    learning_outcomes TEXT, -- JSON array
    key_concepts TEXT, -- JSON array
    skills TEXT, -- JSON array
    duration_hours INTEGER DEFAULT 0,
    prerequisites TEXT, -- JSON array
    assessment_criteria TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- İndeksler
    INDEX idx_meb_subject (subject),
    INDEX idx_meb_grade_level (grade_level),
    INDEX idx_meb_topic_name (topic_name),
    INDEX idx_meb_active (is_active),
    INDEX idx_meb_subject_grade (subject, grade_level)
);

-- ÖSYM Sınav Standartları Tablosu
CREATE TABLE IF NOT EXISTS osym_standards (
    id VARCHAR(255) PRIMARY KEY,
    exam_type VARCHAR(20) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    topic_code VARCHAR(20) NOT NULL,
    topic_name VARCHAR(255) NOT NULL,
    priority_level INTEGER NOT NULL CHECK (priority_level >= 1 AND priority_level <= 5),
    question_count_range TEXT, -- JSON object
    difficulty_distribution TEXT, -- JSON object
    cognitive_levels TEXT, -- JSON array
    exam_frequency DECIMAL(3,2) DEFAULT 0.0,
    last_exam_appearance VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- İndeksler
    INDEX idx_osym_exam_type (exam_type),
    INDEX idx_osym_subject (subject),
    INDEX idx_osym_priority (priority_level),
    INDEX idx_osym_topic_code (topic_code),
    INDEX idx_osym_active (is_active),
    INDEX idx_osym_exam_subject (exam_type, subject),
    INDEX idx_osym_priority_subject (priority_level, subject)
);

-- Öğrenme Kazanımları Tablosu
CREATE TABLE IF NOT EXISTS learning_outcomes (
    id VARCHAR(255) PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    subject VARCHAR(50) NOT NULL,
    grade_level VARCHAR(10) NOT NULL,
    cognitive_level VARCHAR(50) NOT NULL,
    bloom_taxonomy VARCHAR(10) NOT NULL,
    meb_standard_id VARCHAR(255) NOT NULL,
    assessment_methods TEXT, -- JSON array
    sample_activities TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key
    FOREIGN KEY (meb_standard_id) REFERENCES meb_curriculum_standards(id) ON DELETE CASCADE,
    
    -- İndeksler
    INDEX idx_outcome_code (code),
    INDEX idx_outcome_subject (subject),
    INDEX idx_outcome_grade (grade_level),
    INDEX idx_outcome_cognitive (cognitive_level),
    INDEX idx_outcome_meb_standard (meb_standard_id)
);

-- Müfredat Uyumluluk Eşleştirmeleri Tablosu
CREATE TABLE IF NOT EXISTS curriculum_alignments (
    id VARCHAR(255) PRIMARY KEY,
    meb_standard_id VARCHAR(255) NOT NULL,
    osym_standard_id VARCHAR(255) NOT NULL,
    alignment_score DECIMAL(3,2) NOT NULL CHECK (alignment_score >= 0.0 AND alignment_score <= 1.0),
    alignment_type VARCHAR(100) NOT NULL,
    gaps_identified TEXT, -- JSON array
    recommendations TEXT, -- JSON array
    verified_by VARCHAR(255),
    verification_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (meb_standard_id) REFERENCES meb_curriculum_standards(id) ON DELETE CASCADE,
    FOREIGN KEY (osym_standard_id) REFERENCES osym_standards(id) ON DELETE CASCADE,
    
    -- İndeksler
    INDEX idx_alignment_meb (meb_standard_id),
    INDEX idx_alignment_osym (osym_standard_id),
    INDEX idx_alignment_score (alignment_score),
    INDEX idx_alignment_type (alignment_type),
    INDEX idx_alignment_verified (verified_by)
);

-- Soru Bankası Uyumluluk Tablosu
CREATE TABLE IF NOT EXISTS question_bank_compliance (
    id VARCHAR(255) PRIMARY KEY,
    topic_id VARCHAR(255) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    total_questions INTEGER DEFAULT 0,
    osym_format_questions INTEGER DEFAULT 0,
    meb_aligned_questions INTEGER DEFAULT 0,
    difficulty_distribution TEXT, -- JSON object
    compliance_score DECIMAL(3,2) DEFAULT 0.0 CHECK (compliance_score >= 0.0 AND compliance_score <= 1.0),
    minimum_required INTEGER DEFAULT 1000,
    compliance_status VARCHAR(50) DEFAULT 'insufficient',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- İndeksler
    INDEX idx_qbc_topic (topic_id),
    INDEX idx_qbc_subject (subject),
    INDEX idx_qbc_compliance_score (compliance_score),
    INDEX idx_qbc_compliance_status (compliance_status),
    INDEX idx_qbc_next_review (next_review_date)
);

-- Müfredat Uyumluluk Raporları Tablosu
CREATE TABLE IF NOT EXISTS curriculum_compliance_reports (
    id VARCHAR(255) PRIMARY KEY,
    report_type VARCHAR(100) NOT NULL,
    subject VARCHAR(50),
    exam_type VARCHAR(20),
    overall_compliance_score DECIMAL(3,2) NOT NULL CHECK (overall_compliance_score >= 0.0 AND overall_compliance_score <= 1.0),
    meb_compliance_score DECIMAL(3,2) NOT NULL CHECK (meb_compliance_score >= 0.0 AND meb_compliance_score <= 1.0),
    osym_compliance_score DECIMAL(3,2) NOT NULL CHECK (osym_compliance_score >= 0.0 AND osym_compliance_score <= 1.0),
    compliant_topics TEXT, -- JSON array
    non_compliant_topics TEXT, -- JSON array
    missing_topics TEXT, -- JSON array
    question_bank_status TEXT, -- JSON object
    recommendations TEXT, -- JSON array
    priority_actions TEXT, -- JSON array
    generated_by VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_period_start TIMESTAMP,
    report_period_end TIMESTAMP,
    
    -- İndeksler
    INDEX idx_ccr_report_type (report_type),
    INDEX idx_ccr_subject (subject),
    INDEX idx_ccr_exam_type (exam_type),
    INDEX idx_ccr_overall_score (overall_compliance_score),
    INDEX idx_ccr_generated_at (generated_at),
    INDEX idx_ccr_generated_by (generated_by)
);

-- Müfredat Güncelleme Talepleri Tablosu
CREATE TABLE IF NOT EXISTS curriculum_update_requests (
    id VARCHAR(255) PRIMARY KEY,
    update_type VARCHAR(100) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    affected_standards TEXT NOT NULL, -- JSON array
    changes_description TEXT NOT NULL,
    source_document VARCHAR(500),
    requested_by VARCHAR(255) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    implementation_date TIMESTAMP,
    notes TEXT,
    
    -- İndeksler
    INDEX idx_cur_update_type (update_type),
    INDEX idx_cur_subject (subject),
    INDEX idx_cur_status (status),
    INDEX idx_cur_requested_by (requested_by),
    INDEX idx_cur_requested_at (requested_at),
    INDEX idx_cur_reviewed_by (reviewed_by)
);

-- Sorular Tablosu (Soru bankası uyumluluk kontrolü için)
CREATE TABLE IF NOT EXISTS questions (
    id VARCHAR(255) PRIMARY KEY,
    topic_id VARCHAR(255) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'multiple_choice',
    difficulty_level VARCHAR(20) DEFAULT 'orta',
    is_osym_format BOOLEAN DEFAULT FALSE,
    is_meb_aligned BOOLEAN DEFAULT FALSE,
    cognitive_level VARCHAR(50),
    bloom_taxonomy VARCHAR(10),
    options TEXT, -- JSON array for multiple choice
    correct_answer VARCHAR(10),
    explanation TEXT,
    tags TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- İndeksler
    INDEX idx_q_topic (topic_id),
    INDEX idx_q_subject (subject),
    INDEX idx_q_difficulty (difficulty_level),
    INDEX idx_q_osym_format (is_osym_format),
    INDEX idx_q_meb_aligned (is_meb_aligned),
    INDEX idx_q_active (is_active),
    INDEX idx_q_cognitive (cognitive_level)
);

-- Örnek MEB Müfredat Standartları Verisi
INSERT INTO meb_curriculum_standards (
    id, subject, grade_level, unit_name, topic_name, 
    learning_outcomes, key_concepts, skills, duration_hours
) VALUES 
(
    'meb_matematik_12_1', 'matematik', '12', 'Limit ve Süreklilik', 'Limit Kavramı',
    '["Limit kavramını açıklar", "Limit hesaplamalarını yapar"]',
    '["Limit", "Süreklilik", "Yaklaşım"]',
    '["Analitik düşünme", "Problem çözme"]',
    30
),
(
    'meb_turkce_12_1', 'turkce', '12', 'Okuma', 'Metin Analizi',
    '["Metni analiz eder", "Ana fikri bulur"]',
    '["Ana fikir", "Yan fikir", "Metin türü"]',
    '["Analiz", "Sentez", "Değerlendirme"]',
    25
),
(
    'meb_fizik_12_1', 'fizik', '12', 'Elektrik ve Manyetizma', 'Elektrik Akımı',
    '["Elektrik akımını açıklar", "Ohm yasasını uygular"]',
    '["Akım", "Gerilim", "Direnç"]',
    '["Deney yapma", "Veri analizi"]',
    35
) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Örnek ÖSYM Standartları Verisi
INSERT INTO osym_standards (
    id, exam_type, subject, topic_code, topic_name, 
    priority_level, question_count_range, difficulty_distribution, 
    cognitive_levels, exam_frequency
) VALUES 
(
    'osym_tyt_matematik_1', 'tyt', 'matematik', 'MAT01', 'Temel Matematik',
    1, '{"min": 15, "max": 20}', '{"kolay": 0.3, "orta": 0.5, "zor": 0.2}',
    '["bilgi", "kavrama", "uygulama"]', 0.95
),
(
    'osym_ayt_matematik_1', 'ayt', 'matematik', 'MAT02', 'İleri Matematik',
    1, '{"min": 10, "max": 15}', '{"kolay": 0.2, "orta": 0.5, "zor": 0.3}',
    '["uygulama", "analiz", "sentez"]', 0.90
),
(
    'osym_tyt_turkce_1', 'tyt', 'turkce', 'TUR01', 'Türkçe Dil Bilgisi',
    2, '{"min": 12, "max": 18}', '{"kolay": 0.4, "orta": 0.4, "zor": 0.2}',
    '["bilgi", "kavrama", "uygulama"]', 0.85
) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Örnek Öğrenme Kazanımları Verisi
INSERT INTO learning_outcomes (
    id, code, description, subject, grade_level, 
    cognitive_level, bloom_taxonomy, meb_standard_id
) VALUES 
(
    'outcome_meb_matematik_12_1_1', 'M.12.1.1', 'Limit kavramını açıklar ve örnekler verir',
    'matematik', '12', 'kavrama', 'C2', 'meb_matematik_12_1'
),
(
    'outcome_meb_matematik_12_1_2', 'M.12.1.2', 'Limit hesaplamalarını yapar',
    'matematik', '12', 'uygulama', 'C3', 'meb_matematik_12_1'
),
(
    'outcome_meb_turkce_12_1_1', 'T.12.1.1', 'Metni analiz eder ve ana fikrini bulur',
    'turkce', '12', 'analiz', 'C4', 'meb_turkce_12_1'
) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Örnek Soru Verisi (Soru bankası uyumluluk kontrolü için)
INSERT INTO questions (
    id, topic_id, subject, question_text, difficulty_level, 
    is_osym_format, is_meb_aligned, cognitive_level
) VALUES 
('q_mat_1', 'matematik_limit', 'matematik', 'Limit kavramı ile ilgili soru', 'orta', TRUE, TRUE, 'kavrama'),
('q_mat_2', 'matematik_limit', 'matematik', 'Limit hesaplama sorusu', 'zor', TRUE, TRUE, 'uygulama'),
('q_tur_1', 'turkce_metin', 'turkce', 'Metin analizi sorusu', 'kolay', TRUE, TRUE, 'analiz'),
('q_fiz_1', 'fizik_elektrik', 'fizik', 'Elektrik akımı sorusu', 'orta', TRUE, TRUE, 'uygulama')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Trigger'lar (Otomatik güncelleme için)
DELIMITER //

CREATE TRIGGER IF NOT EXISTS update_meb_standards_timestamp 
    BEFORE UPDATE ON meb_curriculum_standards
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

CREATE TRIGGER IF NOT EXISTS update_osym_standards_timestamp 
    BEFORE UPDATE ON osym_standards
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

CREATE TRIGGER IF NOT EXISTS update_learning_outcomes_timestamp 
    BEFORE UPDATE ON learning_outcomes
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

CREATE TRIGGER IF NOT EXISTS update_curriculum_alignments_timestamp 
    BEFORE UPDATE ON curriculum_alignments
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

DELIMITER ;

-- Performans için ek indeksler
CREATE INDEX IF NOT EXISTS idx_meb_topic_subject ON meb_curriculum_standards(topic_name, subject);
CREATE INDEX IF NOT EXISTS idx_osym_frequency_priority ON osym_standards(exam_frequency, priority_level);
CREATE INDEX IF NOT EXISTS idx_questions_compliance ON questions(is_osym_format, is_meb_aligned, is_active);
CREATE INDEX IF NOT EXISTS idx_alignment_scores ON curriculum_alignments(alignment_score DESC);

-- Veritabanı istatistikleri için view
CREATE OR REPLACE VIEW curriculum_compliance_stats AS
SELECT 
    'MEB Standards' as category,
    COUNT(*) as total_count,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_count,
    subject,
    NULL as exam_type
FROM meb_curriculum_standards 
GROUP BY subject

UNION ALL

SELECT 
    'ÖSYM Standards' as category,
    COUNT(*) as total_count,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_count,
    subject,
    exam_type
FROM osym_standards 
GROUP BY subject, exam_type

UNION ALL

SELECT 
    'Learning Outcomes' as category,
    COUNT(*) as total_count,
    COUNT(*) as active_count,
    subject,
    NULL as exam_type
FROM learning_outcomes 
GROUP BY subject;

-- Soru bankası uyumluluk özeti view
CREATE OR REPLACE VIEW question_bank_compliance_summary AS
SELECT 
    subject,
    COUNT(*) as total_questions,
    COUNT(CASE WHEN is_osym_format = TRUE THEN 1 END) as osym_format_questions,
    COUNT(CASE WHEN is_meb_aligned = TRUE THEN 1 END) as meb_aligned_questions,
    ROUND(COUNT(CASE WHEN is_osym_format = TRUE THEN 1 END) / COUNT(*) * 100, 2) as osym_format_percentage,
    ROUND(COUNT(CASE WHEN is_meb_aligned = TRUE THEN 1 END) / COUNT(*) * 100, 2) as meb_aligned_percentage,
    COUNT(CASE WHEN difficulty_level = 'kolay' THEN 1 END) as easy_questions,
    COUNT(CASE WHEN difficulty_level = 'orta' THEN 1 END) as medium_questions,
    COUNT(CASE WHEN difficulty_level = 'zor' THEN 1 END) as hard_questions
FROM questions 
WHERE is_active = TRUE
GROUP BY subject;

-- Başarı mesajı
SELECT 'Müfredat Uyumluluk Sistemi veritabanı tabloları başarıyla oluşturuldu!' as message;