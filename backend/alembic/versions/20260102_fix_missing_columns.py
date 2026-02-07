"""Fix missing columns: users.role and questions.correct_answer

Revision ID: 20260102_fix_cols
Revises: 20251122_add_critical_service_tables
Create Date: 2026-01-02

This migration adds missing columns that are causing index creation to fail:
- users.role (UserRole enum)
- questions.correct_answer (String)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260102_fix_cols'
down_revision = 'add_critical_service_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if role column exists in users table, add if not
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns for users table
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Add role column if missing
    if 'role' not in users_columns:
        # First create the enum type if it doesn't exist
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE userrole AS ENUM ('STUDENT', 'TEACHER', 'PARENT', 'ADMIN');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        op.add_column('users', sa.Column('role', 
            sa.Enum('STUDENT', 'TEACHER', 'PARENT', 'ADMIN', name='userrole'),
            nullable=True))
        
        # Set default value for existing rows
        op.execute("UPDATE users SET role = 'STUDENT' WHERE role IS NULL")
        
        # Make column not nullable after setting defaults
        op.alter_column('users', 'role', nullable=False)
        
        print("[OK] Added 'role' column to users table")
    else:
        print("[SKIP] 'role' column already exists in users table")
    
    # Get existing columns for questions table
    questions_columns = [col['name'] for col in inspector.get_columns('questions')]
    
    # Add correct_answer column if missing
    if 'correct_answer' not in questions_columns:
        op.add_column('questions', sa.Column('correct_answer', 
            sa.String(1), nullable=True))
        
        # Set default value for existing rows (A as placeholder)
        op.execute("UPDATE questions SET correct_answer = 'A' WHERE correct_answer IS NULL")
        
        # Make column not nullable after setting defaults
        op.alter_column('questions', 'correct_answer', nullable=False)
        
        print("[OK] Added 'correct_answer' column to questions table")
    else:
        print("[SKIP] 'correct_answer' column already exists in questions table")
    
    # Now create the indexes that were failing
    # Index on users.role
    try:
        op.create_index('idx_users_role', 'users', ['role'], unique=False)
        print("[OK] Created index idx_users_role")
    except Exception as e:
        print(f"[SKIP] Index idx_users_role: {e}")
    
    # Index on questions.correct_answer
    try:
        op.create_index('idx_questions_correct_answer', 'questions', ['correct_answer'], unique=False)
        print("[OK] Created index idx_questions_correct_answer")
    except Exception as e:
        print(f"[SKIP] Index idx_questions_correct_answer: {e}")


def downgrade() -> None:
    # Drop indexes first
    try:
        op.drop_index('idx_questions_correct_answer', table_name='questions')
    except:
        pass
    
    try:
        op.drop_index('idx_users_role', table_name='users')
    except:
        pass
    
    # Drop columns
    try:
        op.drop_column('questions', 'correct_answer')
    except:
        pass
    
    try:
        op.drop_column('users', 'role')
    except:
        pass
    
    # Drop enum type
    try:
        op.execute("DROP TYPE IF EXISTS userrole")
    except:
        pass
