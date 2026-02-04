-- Migration: Create sorular table (Turkish column names)
-- Created: 2025-11-09
-- Priority: P0 - CRITICAL
-- Description: Turkish-named question bank table for imported questions
-- Complements the 'questions' table (English names) from migration 003

CREATE TABLE IF NOT EXISTS sorular (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Soru içeriği (Question content)
    kod VARCHAR(255),  -- Question code/ID (e.g., PROD_MAT_Q001)
    metin TEXT NOT NULL,  -- Question text
    secenekler JSONB NOT NULL,  -- Answer options (JSON: {"A": "...", "B": "...", ...})
    dogru_cevap VARCHAR(1) NOT NULL CHECK (dogru_cevap IN ('A', 'B', 'C', 'D', 'E')),  -- Correct answer

    -- Sınıf ve konu bilgileri (Subject and topic info)
    sinav_tipi VARCHAR(50) NOT NULL CHECK (sinav_tipi IN ('TYT', 'AYT', 'YDT', 'YKS_MOCK', 'DIAGNOSTIC')),  -- Exam type
    konu VARCHAR(255) NOT NULL,  -- Topic (e.g., "Matematik - Sayılar")
    alt_konu VARCHAR(255),  -- Subtopic (e.g., "Rasyonel Sayılar")
    kazanim TEXT,  -- Learning outcome/achievement

    -- IRT parametreleri (IRT parameters)
    irt_discrimination DECIMAL(10, 6),  -- 'a' parameter (0.5 - 2.5)
    irt_difficulty DECIMAL(10, 6),  -- 'b' parameter (-3 to +3)
    irt_guessing DECIMAL(5, 4) DEFAULT 0.25,  -- 'c' parameter (typically 0.25 for 5 options)
    irt_upper_asymptote DECIMAL(5, 4),  -- 'd' parameter (upper asymptote)

    -- Zorluk seviyesi (Difficulty level)
    zorluk VARCHAR(50) CHECK (zorluk IN ('kolay', 'orta', 'zor')),

    -- İstatistikler (Statistics)
    cozulme_sayisi INTEGER DEFAULT 0,  -- Times attempted
    dogru_cozulme_sayisi INTEGER DEFAULT 0,  -- Times answered correctly
    ortalama_sure DECIMAL(10, 2),  -- Average time to solve (seconds)

    -- Metin analizi (Text analysis)
    morfoloji_skoru DECIMAL(5, 2),  -- Morphology score
    kelime_sayisi INTEGER,  -- Word count
    cumle_karmasikligi DECIMAL(5, 2),  -- Sentence complexity

    -- Medya (Media)
    gorsel_url TEXT,  -- Image URL
    video_url TEXT,  -- Video solution URL

    -- Kaynak bilgisi (Source info)
    kaynak VARCHAR(255),  -- Source (e.g., "ÖSYM 2024", "AI Generated")
    yil INTEGER,  -- Year

    -- Durum (Status)
    aktif BOOLEAN DEFAULT true,
    status VARCHAR(50) DEFAULT 'approved' CHECK (status IN ('draft', 'approved', 'archived', 'rejected')),

    -- Tarihler (Dates)
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Advanced metadata (from Wave 2B quality system)
    irt_confidence DECIMAL(5, 2),  -- Confidence in IRT parameters (0-1)
    calibration_sample_size INTEGER,  -- Number of responses used for calibration
    last_calibration_date TIMESTAMP,  -- Last IRT calibration date
    plagiarism_score DECIMAL(5, 2),  -- Plagiarism detection score (0-1)
    plagiarism_check_date TIMESTAMP,
    knowledge_graph_id VARCHAR(255),  -- Link to knowledge graph node
    prerequisite_topics JSONB DEFAULT '[]'::jsonb,  -- Prerequisite topics array
    ai_validation_confidence DECIMAL(5, 2),  -- AI validation confidence (0-1)
    expert_review_score INTEGER CHECK (expert_review_score >= 0 AND expert_review_score <= 10),  -- Human expert score (0-10)
    expert_reviewer_id UUID,  -- ID of expert who reviewed
    review_date TIMESTAMP,  -- Date of expert review
    bloom_level VARCHAR(50) CHECK (bloom_level IN ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')),
    cognitive_skills JSONB DEFAULT '[]'::jsonb,  -- Array of cognitive skills tested
    usage_count INTEGER DEFAULT 0,  -- Number of times used in exams
    correct_rate DECIMAL(5, 4),  -- Overall correct answer rate (0-1)
    avg_response_time INTEGER,  -- Average response time in seconds

    -- Visual content support (Phase 1: Tables, Phase 2: Graphs, Phase 3: Geometry, Phase 4: Maps/Diagrams)
    visual_content JSONB  -- Structured visual content data
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sorular_kod ON sorular(kod);
CREATE INDEX IF NOT EXISTS idx_sorular_sinav_tipi ON sorular(sinav_tipi);
CREATE INDEX IF NOT EXISTS idx_sorular_konu ON sorular(konu);
CREATE INDEX IF NOT EXISTS idx_sorular_alt_konu ON sorular(alt_konu);
CREATE INDEX IF NOT EXISTS idx_sorular_zorluk ON sorular(zorluk);
CREATE INDEX IF NOT EXISTS idx_sorular_status ON sorular(status);
CREATE INDEX IF NOT EXISTS idx_sorular_aktif ON sorular(aktif);
CREATE INDEX IF NOT EXISTS idx_sorular_bloom_level ON sorular(bloom_level);
CREATE INDEX IF NOT EXISTS idx_sorular_sinav_tipi_konu ON sorular(sinav_tipi, konu);
CREATE INDEX IF NOT EXISTS idx_sorular_irt_difficulty ON sorular(irt_difficulty);
CREATE INDEX IF NOT EXISTS idx_sorular_correct_rate ON sorular(correct_rate);

-- Full-text search index for Turkish text
CREATE INDEX IF NOT EXISTS idx_sorular_metin_fts ON sorular USING gin(to_tsvector('turkish', metin));

-- Trigger for updated_at (guncelleme_tarihi)
CREATE OR REPLACE FUNCTION update_sorular_guncelleme_tarihi()
RETURNS TRIGGER AS $$
BEGIN
    NEW.guncelleme_tarihi = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sorular_guncelleme_tarihi
    BEFORE UPDATE ON sorular
    FOR EACH ROW
    EXECUTE FUNCTION update_sorular_guncelleme_tarihi();

-- Comments
COMMENT ON TABLE sorular IS 'Turkish question bank with IRT parameters and Wave 2B quality metrics';
COMMENT ON COLUMN sorular.id IS 'Unique question identifier (UUID)';
COMMENT ON COLUMN sorular.kod IS 'Question code (e.g., PROD_MAT_Q001)';
COMMENT ON COLUMN sorular.metin IS 'Question text in Turkish';
COMMENT ON COLUMN sorular.secenekler IS 'Answer options as JSON object with keys A-E';
COMMENT ON COLUMN sorular.dogru_cevap IS 'Correct answer (A, B, C, D, or E)';
COMMENT ON COLUMN sorular.konu IS 'Topic (e.g., "Matematik - Sayılar")';
COMMENT ON COLUMN sorular.irt_difficulty IS 'IRT difficulty parameter (b): -3 (easy) to +3 (hard)';
COMMENT ON COLUMN sorular.irt_discrimination IS 'IRT discrimination parameter (a): how well question differentiates ability levels';
COMMENT ON COLUMN sorular.irt_guessing IS 'IRT guessing parameter (c): probability of random correct answer';
COMMENT ON COLUMN sorular.visual_content IS 'Structured data for tables, graphs, geometry diagrams, or maps';
COMMENT ON COLUMN sorular.bloom_level IS 'Bloom''s taxonomy level: remember, understand, apply, analyze, evaluate, create';
COMMENT ON COLUMN sorular.expert_review_score IS 'Human expert quality rating (0-10)';
COMMENT ON COLUMN sorular.plagiarism_score IS 'Automated plagiarism detection score (0-1, lower is better)';
