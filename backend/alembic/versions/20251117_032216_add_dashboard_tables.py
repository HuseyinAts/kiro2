"""Add dashboard tables (student_goals, notifications)

Revision ID: 20251117_032216
Revises: f822e22c28c6
Create Date: 2025-11-17 03:22:16

This migration adds tables required for student dashboard service:
- student_goals: Student goal tracking
- notifications: User notification system

Part of Mock Data Cleanup - Phase 1
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251117_032216'
down_revision = 'f822e22c28c6'
branch_labels = None
depends_on = None


def upgrade():
    """Create student_goals and notifications tables"""

    # Create student_goals table
    op.create_table(
        'student_goals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal_type', sa.String(length=20), nullable=False),  # 'gunluk', 'haftalik', 'aylik'
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=True, server_default='0'),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='aktif'),  # 'aktif', 'tamamlandi', 'iptal'
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # Create indexes for student_goals
    op.create_index('idx_student_goals_user', 'student_goals', ['user_id'])
    op.create_index('idx_student_goals_status', 'student_goals', ['user_id', 'status'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=20), nullable=False),  # 'basari', 'uyari', 'bilgi', 'hata'
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # Create indexes for notifications
    op.create_index('idx_notifications_user', 'notifications', ['user_id'])
    op.create_index('idx_notifications_unread', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notifications_created', 'notifications', ['created_at'], unique=False)


def downgrade():
    """Drop student_goals and notifications tables"""

    # Drop indexes first
    op.drop_index('idx_notifications_created', table_name='notifications')
    op.drop_index('idx_notifications_unread', table_name='notifications')
    op.drop_index('idx_notifications_user', table_name='notifications')
    op.drop_index('idx_student_goals_status', table_name='student_goals')
    op.drop_index('idx_student_goals_user', table_name='student_goals')

    # Drop tables
    op.drop_table('notifications')
    op.drop_table('student_goals')
