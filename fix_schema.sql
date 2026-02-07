-- KIRO2 Schema Fix - Add missing columns for OSYM API compatibility

-- 1. Add exam_type column
ALTER TABLE questions ADD COLUMN IF NOT EXISTS exam_type VARCHAR(10);

-- 2. Add subject column (denormalized for faster queries)
ALTER TABLE questions ADD COLUMN IF NOT EXISTS subject VARCHAR(100);

-- 3. Add topic column (denormalized)
ALTER TABLE questions ADD COLUMN IF NOT EXISTS topic VARCHAR(200);

-- 4. Update existing questions with subject names from subjects table
UPDATE questions q 
SET subject = s.name 
FROM subjects s 
WHERE q.subject_id = s.id AND q.subject IS NULL;

-- 5. Set default exam_type for existing questions
UPDATE questions SET exam_type = 'TYT' WHERE exam_type IS NULL;

-- 6. Verify the changes
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'questions' 
ORDER BY ordinal_position;
