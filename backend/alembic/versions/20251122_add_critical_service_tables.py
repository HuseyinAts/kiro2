"""Add critical service tables for Phase 2 migration

Adds 6 missing tables needed for critical services:
- sessions (user authentication/tokens)
- student_goals (student goal tracking)
- notifications (system-wide notifications)
- parent_reports (weekly parent reports)
- parent_approvals (parent approval requests)
- student_grades (teacher grades)
- class_reports (teacher class reports)

Revision ID: add_critical_service_tables
Revises: 20251117_044637
Create Date: 2025-11-22

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_critical_service_tables'
down_revision = '20251117_044637'  # Previous: add_student_profile_fields
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create missing critical service tables"""

    # =================================================================
    # 1. SESSIONS - User authentication & token management
    # =================================================================
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column('device_info', sa.JSON(), nullable=True, comment='Device/browser info'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='User authentication sessions and tokens'
    )
    op.create_index('idx_session_user_id', 'sessions', ['user_id'])
    op.create_index('idx_session_expires_at', 'sessions', ['expires_at'])
    op.create_index('idx_session_active', 'sessions', ['is_active', 'expires_at'])

    # =================================================================
    # 2. STUDENT_GOALS - Student goal tracking
    # =================================================================
    op.create_table(
        'student_goals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal_type', sa.String(length=50), nullable=False, comment='haftalik_calisma, sinav_hedefi, konu_tamamlama'),
        sa.Column('target_value', sa.Integer(), nullable=False),
        sa.Column('current_value', sa.Integer(), default=0, nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), default='aktif', nullable=False, comment='aktif, tamamlandi, iptal_edildi'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Student goals and targets'
    )
    op.create_index('idx_goal_user_status', 'student_goals', ['user_id', 'status'])
    op.create_index('idx_goal_end_date', 'student_goals', ['end_date'])

    # =================================================================
    # 3. NOTIFICATIONS - System-wide notifications
    # =================================================================
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False, comment='bilgi, basari, uyari, hata'),
        sa.Column('action_url', sa.String(length=500), nullable=True, comment='Optional URL for action button'),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('priority', sa.Integer(), default=0, nullable=False, comment='Higher = more important'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='Auto-delete after this date'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='User notifications across all roles'
    )
    op.create_index('idx_notification_user_read', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notification_created_at', 'notifications', ['created_at'])
    op.create_index('idx_notification_priority', 'notifications', ['user_id', 'priority', 'is_read'])

    # =================================================================
    # 4. PARENT_REPORTS - Weekly parent reports
    # =================================================================
    op.create_table(
        'parent_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('parent_user_id', sa.String(), nullable=False),
        sa.Column('student_user_id', sa.String(), nullable=False),
        sa.Column('student_name', sa.String(length=200), nullable=False),
        sa.Column('report_period', sa.String(length=50), nullable=False, comment='e.g., 2025-W47'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),

        # Statistics
        sa.Column('total_study_minutes', sa.Integer(), default=0, nullable=False),
        sa.Column('completed_exams_count', sa.Integer(), default=0, nullable=False),
        sa.Column('average_success_rate', sa.Float(), default=0.0, nullable=False, comment='0-100'),

        # Performance arrays (JSON)
        sa.Column('strong_subjects', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column('weak_subjects', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column('weekly_progress_description', sa.Text(), nullable=True),

        # Recommendations (JSON)
        sa.Column('parent_recommendations', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column('support_areas', postgresql.ARRAY(sa.String()), default=[], nullable=False),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False),

        sa.ForeignKeyConstraint(['parent_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Weekly reports sent to parents about student performance'
    )
    op.create_index('idx_parent_report_parent', 'parent_reports', ['parent_user_id', 'created_at'])
    op.create_index('idx_parent_report_student', 'parent_reports', ['student_user_id'])
    op.create_index('idx_parent_report_period', 'parent_reports', ['report_period'])

    # =================================================================
    # 5. PARENT_APPROVALS - Parent approval requests
    # =================================================================
    op.create_table(
        'parent_approvals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_user_id', sa.String(), nullable=False),
        sa.Column('parent_user_id', sa.String(), nullable=False),
        sa.Column('request_type', sa.String(length=100), nullable=False, comment='ekstra_ders_izni, sinav_kayit, ozel_egitim'),
        sa.Column('request_description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), default='beklemede', nullable=False, comment='beklemede, onaylandi, reddedildi'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parent_note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Parent approval requests from students'
    )
    op.create_index('idx_approval_parent_status', 'parent_approvals', ['parent_user_id', 'status'])
    op.create_index('idx_approval_student', 'parent_approvals', ['student_user_id'])

    # =================================================================
    # 6. STUDENT_GRADES - Teacher-assigned student grades
    # =================================================================
    op.create_table(
        'student_grades',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('teacher_user_id', sa.String(), nullable=False),
        sa.Column('student_user_id', sa.String(), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=False, comment='Matematik, Türkçe, etc.'),
        sa.Column('grade_type', sa.String(length=50), nullable=False, comment='yazili, sözlü, proje, performans'),
        sa.Column('grade_value', sa.Float(), nullable=False, comment='0-100 or other scale'),
        sa.Column('max_grade', sa.Float(), default=100.0, nullable=False),
        sa.Column('weight', sa.Float(), default=1.0, nullable=False, comment='Weight in final grade calculation'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False, comment='2024-2025'),
        sa.Column('semester', sa.Integer(), nullable=False, comment='1 or 2'),
        sa.ForeignKeyConstraint(['teacher_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Teacher-assigned grades for students'
    )
    op.create_index('idx_grade_student_subject', 'student_grades', ['student_user_id', 'subject'])
    op.create_index('idx_grade_teacher', 'student_grades', ['teacher_user_id'])
    op.create_index('idx_grade_academic_year', 'student_grades', ['academic_year', 'semester'])

    # =================================================================
    # 7. CLASS_REPORTS - Teacher class performance reports
    # =================================================================
    op.create_table(
        'class_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('teacher_user_id', sa.String(), nullable=False),
        sa.Column('class_name', sa.String(length=100), nullable=False, comment='12-A, 11-B, etc.'),
        sa.Column('subject', sa.String(length=100), nullable=False),
        sa.Column('report_period', sa.String(length=50), nullable=False, comment='2025-W47, 2025-Q1, etc.'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),

        # Class statistics
        sa.Column('total_students', sa.Integer(), default=0, nullable=False),
        sa.Column('average_grade', sa.Float(), default=0.0, nullable=False),
        sa.Column('passing_students', sa.Integer(), default=0, nullable=False),
        sa.Column('failing_students', sa.Integer(), default=0, nullable=False),

        # Performance distribution (JSON)
        sa.Column('grade_distribution', sa.JSON(), nullable=True, comment='{"90-100": 5, "80-90": 10, ...}'),
        sa.Column('top_students', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column('struggling_students', postgresql.ARRAY(sa.String()), default=[], nullable=False),

        # Recommendations
        sa.Column('teacher_notes', sa.Text(), nullable=True),
        sa.Column('recommendations', postgresql.ARRAY(sa.String()), default=[], nullable=False),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['teacher_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Teacher reports for class performance'
    )
    op.create_index('idx_class_report_teacher', 'class_reports', ['teacher_user_id', 'created_at'])
    op.create_index('idx_class_report_period', 'class_reports', ['report_period'])


def downgrade() -> None:
    """Drop all created tables"""
    op.drop_table('class_reports')
    op.drop_table('student_grades')
    op.drop_table('parent_approvals')
    op.drop_table('parent_reports')
    op.drop_table('notifications')
    op.drop_table('student_goals')
    op.drop_table('sessions')
