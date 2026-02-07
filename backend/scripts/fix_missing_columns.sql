-- =====================================================
-- KIRO2 Database Schema Fix Script
-- Date: 2026-01-02
-- Purpose: Add missing columns causing index failures
-- =====================================================

-- 1. Create UserRole enum if not exists
DO $$ BEGIN
    CREATE TYPE userrole AS ENUM ('STUDENT', 'TEACHER', 'PARENT', 'ADMIN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Add role column to users table if not exists
DO $$ BEGIN
    ALTER TABLE users ADD COLUMN role userrole;
EXCEPTION
    WHEN duplicate_column THEN null;
END $$;

-- 3. Set default value for existing users
UPDATE users SET role = 'STUDENT' WHERE role IS NULL;

-- 4. Make role column NOT NULL (after setting defaults)
ALTER TABLE users ALTER COLUMN role SET NOT NULL;

-- 5. Add correct_answer column to questions table if not exists
DO $$ BEGIN
    ALTER TABLE questions ADD COLUMN correct_answer VARCHAR(1);
EXCEPTION
    WHEN duplicate_column THEN null;
END $$;

-- 6. Set default value for existing questions
UPDATE questions SET correct_answer = 'A' WHERE correct_answer IS NULL;

-- 7. Make correct_answer column NOT NULL
ALTER TABLE questions ALTER COLUMN correct_answer SET NOT NULL;

-- 8. Create indexes (with IF NOT EXISTS equivalent)
DO $$ BEGIN
    CREATE INDEX idx_users_role ON users(role);
EXCEPTION
    WHEN duplicate_table THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_questions_correct_answer ON questions(correct_answer);
EXCEPTION
    WHEN duplicate_table THEN null;
END $$;

-- 9. Verify changes
SELECT 'users.role' as column_name, 
       EXISTS(SELECT 1 FROM information_schema.columns 
              WHERE table_name='users' AND column_name='role') as exists;

SELECT 'questions.correct_answer' as column_name,
       EXISTS(SELECT 1 FROM information_schema.columns 
              WHERE table_name='questions' AND column_name='correct_answer') as exists;

-- Done!
SELECT '✅ Schema fix complete!' as status;
