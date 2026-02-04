-- Migration 008: Video Cache Table with Optimized Indexing
-- Task 8: Database Optimization ve Indexing
-- Creates video_cache table for caching YouTube video recommendations
-- with composite and individual indexes for fast lookup

-- ============================================================
-- Video Cache Table
-- ============================================================

CREATE TABLE IF NOT EXISTS video_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Video identification
    video_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- Video metadata
    title TEXT NOT NULL,
    description TEXT,
    channel_name VARCHAR(255) NOT NULL,
    channel_id VARCHAR(100) NOT NULL,
    thumbnail_url TEXT,
    duration INTEGER NOT NULL, -- in seconds
    
    -- Classification
    subject VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) NOT NULL, -- 'başlangıç', 'orta', 'ileri'
    exam_type VARCHAR(20) NOT NULL, -- 'TYT', 'AYT', 'LGS'
    language VARCHAR(10) NOT NULL DEFAULT 'tr',
    
    -- Quality metrics
    quality_score FLOAT NOT NULL DEFAULT 0.0,
    relevance_score FLOAT NOT NULL DEFAULT 0.0,
    language_score FLOAT NOT NULL DEFAULT 0.0,
    difficulty_match FLOAT NOT NULL DEFAULT 0.0,
    
    -- Engagement metrics
    view_count BIGINT DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- Additional metadata (JSON)
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Cache management
    access_count INTEGER DEFAULT 0,
    cache_ttl INTEGER DEFAULT 3600, -- TTL in seconds (1 hour default)
    
    -- Constraints
    CONSTRAINT check_quality_score CHECK (quality_score >= 0 AND quality_score <= 10),
    CONSTRAINT check_relevance_score CHECK (relevance_score >= 0 AND relevance_score <= 1),
    CONSTRAINT check_language_score CHECK (language_score >= 0 AND language_score <= 1),
    CONSTRAINT check_difficulty_match CHECK (difficulty_match >= 0 AND difficulty_match <= 1),
    CONSTRAINT check_difficulty CHECK (difficulty IN ('başlangıç', 'kolay', 'orta', 'zor', 'ileri')),
    CONSTRAINT check_exam_type CHECK (exam_type IN ('TYT', 'AYT', 'LGS', 'YKS')),
    CONSTRAINT check_language CHECK (language IN ('tr', 'en', 'ar', 'other'))
);

-- ============================================================
-- Optimized Indexes
-- ============================================================

-- Composite index for common video search queries
-- This is the PRIMARY index for video discovery
-- Covers: subject + difficulty + exam_type + language + quality_score
CREATE INDEX idx_video_search_composite ON video_cache(
    subject,
    difficulty,
    exam_type,
    language,
    quality_score DESC
);

-- Individual indexes for specific queries

-- Quality score index (for sorting by quality)
CREATE INDEX idx_video_quality_score ON video_cache(quality_score DESC);

-- Language index (for language filtering)
CREATE INDEX idx_video_language ON video_cache(language);

-- Last updated index (for cache invalidation and freshness checks)
CREATE INDEX idx_video_last_updated ON video_cache(last_updated DESC);

-- Last accessed index (for LRU cache eviction)
CREATE INDEX idx_video_last_accessed ON video_cache(last_accessed DESC);

-- Subject index (for subject-specific queries)
CREATE INDEX idx_video_subject ON video_cache(subject);

-- Difficulty index (for difficulty-specific queries)
CREATE INDEX idx_video_difficulty ON video_cache(difficulty);

-- Exam type index (for exam-specific queries)
CREATE INDEX idx_video_exam_type ON video_cache(exam_type);

-- Relevance score index (for relevance-based sorting)
CREATE INDEX idx_video_relevance_score ON video_cache(relevance_score DESC);

-- Access count index (for popularity tracking)
CREATE INDEX idx_video_access_count ON video_cache(access_count DESC);

-- Composite index for cache management (LRU eviction)
CREATE INDEX idx_video_cache_management ON video_cache(
    last_accessed DESC,
    access_count DESC
);

-- Composite index for subject + quality (common query pattern)
CREATE INDEX idx_video_subject_quality ON video_cache(
    subject,
    quality_score DESC
);

-- ============================================================
-- Trigger for automatic last_updated timestamp
-- ============================================================

CREATE OR REPLACE FUNCTION update_video_cache_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_video_cache_timestamp
    BEFORE UPDATE ON video_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_video_cache_timestamp();

-- ============================================================
-- Comments for documentation
-- ============================================================

COMMENT ON TABLE video_cache IS 'Cached YouTube video recommendations with quality metrics and optimized indexes';
COMMENT ON COLUMN video_cache.quality_score IS 'Overall video quality score (0-10) based on multiple factors';
COMMENT ON COLUMN video_cache.relevance_score IS 'Subject relevance score (0-1) based on content analysis';
COMMENT ON COLUMN video_cache.language_score IS 'Turkish language confidence score (0-1)';
COMMENT ON COLUMN video_cache.difficulty_match IS 'Difficulty level match score (0-1)';
COMMENT ON COLUMN video_cache.metadata IS 'Additional video metadata in JSON format';
COMMENT ON COLUMN video_cache.cache_ttl IS 'Time-to-live for cache entry in seconds';
COMMENT ON COLUMN video_cache.access_count IS 'Number of times this video was accessed from cache';

-- ============================================================
-- Performance Notes
-- ============================================================

-- The composite index idx_video_search_composite is designed for the most common query pattern:
-- SELECT * FROM video_cache 
-- WHERE subject = ? AND difficulty = ? AND exam_type = ? AND language = ?
-- ORDER BY quality_score DESC
-- LIMIT ?

-- This index will be used for:
-- 1. Fast filtering by subject, difficulty, exam_type, language
-- 2. Efficient sorting by quality_score
-- 3. Avoiding full table scans

-- Expected query performance:
-- - Index scan: O(log n) for lookup
-- - Sequential scan of matching rows: O(k) where k = number of matches
-- - Total: O(log n + k)

-- For a table with 100,000 videos:
-- - Without index: ~100ms (full table scan)
-- - With composite index: ~5-10ms (index scan + sequential read)
-- - Performance improvement: 10-20x faster
