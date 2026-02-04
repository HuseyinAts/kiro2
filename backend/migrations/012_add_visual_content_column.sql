-- Migration: Add visual_content column for tables, graphs, and diagrams
-- Created: 2025-11-07
-- Priority: HIGH (Phase 1 of Visual Questions Roadmap)
-- Description: Adds JSONB column to support visual elements in questions

-- Add visual_content column to questions table
ALTER TABLE questions
ADD COLUMN IF NOT EXISTS visual_content JSONB DEFAULT NULL;

-- Add visual_content column to sorular table (OSYM questions)
ALTER TABLE sorular
ADD COLUMN IF NOT EXISTS visual_content JSONB DEFAULT NULL;

-- Create index for visual content queries
CREATE INDEX IF NOT EXISTS idx_questions_visual_content ON questions USING GIN(visual_content);
CREATE INDEX IF NOT EXISTS idx_sorular_visual_content ON sorular USING GIN(visual_content);

-- Create index for questions with visual content
CREATE INDEX IF NOT EXISTS idx_questions_has_visual ON questions((visual_content IS NOT NULL)) WHERE visual_content IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sorular_has_visual ON sorular((visual_content IS NOT NULL)) WHERE visual_content IS NOT NULL;

-- Comments
COMMENT ON COLUMN questions.visual_content IS 'Visual content metadata (tables, graphs, geometry, diagrams) in JSON format';
COMMENT ON COLUMN sorular.visual_content IS 'Visual content metadata (tables, graphs, geometry, diagrams) in JSON format';

/*
Visual Content JSON Structure:
{
  "type": "table" | "graph" | "geometry" | "diagram" | "map" | "image",
  "format": "markdown" | "html" | "svg" | "png" | "matplotlib" | "plotly",
  "content": "...",  // Markdown table, SVG code, base64 image, etc.
  "data": {},  // Optional: structured data for graphs/tables
  "metadata": {
    "width": 600,
    "height": 400,
    "caption": "Tablo 1: Sonuçlar",
    "alt_text": "Bar chart showing results"
  }
}

Examples:

1. Markdown Table:
{
  "type": "table",
  "format": "markdown",
  "content": "| Ürün | Fiyat | Miktar |\n|------|-------|--------|\n| A | 100 | 5 |\n| B | 200 | 3 |",
  "metadata": {
    "caption": "Tablo 1: Ürün Listesi"
  }
}

2. Function Graph:
{
  "type": "graph",
  "format": "matplotlib",
  "data": {
    "function": "y = x^2 + 2x + 1",
    "x_range": [-5, 5],
    "y_range": [-2, 10]
  },
  "content": "<base64_encoded_image>",
  "metadata": {
    "width": 600,
    "height": 400,
    "caption": "Grafik 1: Parabolün grafiği"
  }
}

3. Geometry Figure:
{
  "type": "geometry",
  "format": "svg",
  "content": "<svg>...</svg>",
  "data": {
    "shape": "triangle",
    "sides": [3, 4, 5],
    "angles": [30, 60, 90]
  },
  "metadata": {
    "caption": "Şekil 1: Dik üçgen",
    "width": 400,
    "height": 400
  }
}
*/

-- Validation check constraint (optional - can be added later for strict validation)
-- ALTER TABLE questions ADD CONSTRAINT check_visual_content_type
--   CHECK (visual_content IS NULL OR visual_content->>'type' IN ('table', 'graph', 'geometry', 'diagram', 'map', 'image'));

-- Update statistics
ANALYZE questions;
ANALYZE sorular;

-- Report
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 012: Visual Content Support';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Added visual_content JSONB column to:';
    RAISE NOTICE '  - questions table';
    RAISE NOTICE '  - sorular table';
    RAISE NOTICE '';
    RAISE NOTICE 'Created indexes:';
    RAISE NOTICE '  - GIN index for JSON queries';
    RAISE NOTICE '  - Partial index for visual questions';
    RAISE NOTICE '';
    RAISE NOTICE 'Visual types supported:';
    RAISE NOTICE '  Phase 1: tables (markdown)';
    RAISE NOTICE '  Phase 2: graphs (matplotlib/plotly)';
    RAISE NOTICE '  Phase 3: geometry (SVG)';
    RAISE NOTICE '  Phase 4-5: diagrams, maps, images';
    RAISE NOTICE '========================================';
END $$;
