"""add_claude_md_improvement_tables

Revision ID: 20260117_claude_md
Revises: 20260116_reasoning
Create Date: 2026-01-17 12:00:00.000000

CLAUDE.md Self-Improvement Tables:
- claude_md_feedback_records: Agent task feedback kayıtları
- claude_md_rule_effectiveness: Rule effectiveness skorları
- claude_md_improvement_triggers: İyileştirme tetikleyicileri
- claude_md_pattern_detections: Pattern tespitleri
- claude_md_rule_versions: Rule version tracking
- claude_md_audit_logs: Audit logging

Spec: claude-md-self-improvement Phase 0.5
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260117_claude_md'
down_revision: Union[str, None] = '20260116_reasoning'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ======================================================================
    # 1. claude_md_feedback_records
    # ======================================================================
    op.create_table(
        'claude_md_feedback_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', sa.String(255), nullable=False, index=True,
                  comment='Task identifier'),
        sa.Column('rule_id', sa.String(255), nullable=True, index=True,
                  comment='CLAUDE.md rule identifier'),

        # Feedback türü
        sa.Column('feedback_type', sa.String(50), nullable=False,
                  server_default='automatic',
                  comment='explicit, implicit, automatic'),
        sa.Column('outcome', sa.String(50), nullable=False,
                  server_default='success',
                  comment='success, failure, partial, timeout'),

        # Explicit feedback
        sa.Column('rating', sa.Integer(), nullable=True,
                  comment='User rating 1-5'),
        sa.Column('comment', sa.Text(), nullable=True,
                  comment='User comment'),

        # Implicit feedback
        sa.Column('retry_count', sa.Integer(), server_default='0',
                  comment='Retry count'),
        sa.Column('edit_frequency', sa.Integer(), server_default='0',
                  comment='Edit frequency'),
        sa.Column('execution_time', sa.Float(), server_default='0.0',
                  comment='Execution time in seconds'),

        # Automatic feedback (Boris Cherny verification)
        sa.Column('test_passed', sa.Boolean(), nullable=True,
                  comment='Test result'),
        sa.Column('lint_passed', sa.Boolean(), nullable=True,
                  comment='Lint result'),
        sa.Column('type_check_passed', sa.Boolean(), nullable=True,
                  comment='Type check result'),

        # Metadata
        sa.Column('session_id', sa.String(255), nullable=True,
                  comment='Claude Code session ID'),
        sa.Column('agent_type', sa.String(100), nullable=True,
                  comment='Agent type'),
        sa.Column('context', postgresql.JSONB(), server_default='{}',
                  comment='Additional context'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'),
                  index=True, comment='Creation timestamp'),
    )

    # Indexes for efficient querying
    op.create_index(
        'ix_feedback_rule_created',
        'claude_md_feedback_records',
        ['rule_id', 'created_at']
    )
    op.create_index(
        'ix_feedback_type_outcome',
        'claude_md_feedback_records',
        ['feedback_type', 'outcome']
    )

    # ======================================================================
    # 2. claude_md_rule_effectiveness
    # ======================================================================
    op.create_table(
        'claude_md_rule_effectiveness',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_id', sa.String(255), nullable=False, unique=True,
                  index=True, comment='Unique rule identifier'),
        sa.Column('rule_text', sa.Text(), nullable=True,
                  comment='Rule text'),
        sa.Column('section', sa.String(255), nullable=True,
                  comment='CLAUDE.md section'),

        # Metrikler
        sa.Column('total_feedback', sa.Integer(), server_default='0',
                  comment='Total feedback count'),
        sa.Column('success_count', sa.Integer(), server_default='0',
                  comment='Success count'),
        sa.Column('failure_count', sa.Integer(), server_default='0',
                  comment='Failure count'),

        # Hesaplanan skorlar
        sa.Column('effectiveness_score', sa.Float(), server_default='0.0',
                  comment='Effectiveness score 0-1'),
        sa.Column('confidence', sa.Float(), server_default='0.0',
                  comment='Confidence level'),

        # Ağırlıklı skorlar
        sa.Column('explicit_score', sa.Float(), server_default='0.0',
                  comment='Explicit feedback score'),
        sa.Column('implicit_score', sa.Float(), server_default='0.0',
                  comment='Implicit feedback score'),

        # Periyot
        sa.Column('window_days', sa.Integer(), server_default='30',
                  comment='Evaluation window in days'),

        # Timestamps
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('NOW()'),
                  comment='Last update timestamp'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'),
                  comment='Creation timestamp'),
    )

    # ======================================================================
    # 3. claude_md_improvement_triggers
    # ======================================================================
    op.create_table(
        'claude_md_improvement_triggers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_id', sa.String(255), nullable=False, index=True,
                  comment='Rule to improve'),
        sa.Column('trigger_reason', sa.Text(), nullable=False,
                  comment='Trigger reason'),

        # Threshold bilgileri
        sa.Column('current_score', sa.Float(), nullable=False,
                  comment='Current effectiveness score'),
        sa.Column('threshold', sa.Float(), server_default='0.6',
                  comment='Trigger threshold'),
        sa.Column('improvement_target', sa.Float(), server_default='0.8',
                  comment='Target score'),

        # Önerilen aksiyonlar
        sa.Column('suggested_actions', postgresql.JSONB(), server_default='[]',
                  comment='Suggested actions'),
        sa.Column('priority', sa.Integer(), server_default='1',
                  comment='Priority 1-5'),

        # Durum
        sa.Column('triggered_at', sa.DateTime(), server_default=sa.text('NOW()'),
                  index=True, comment='Trigger timestamp'),
        sa.Column('processed', sa.Boolean(), server_default='false',
                  comment='Is processed'),
        sa.Column('processed_at', sa.DateTime(), nullable=True,
                  comment='Processing timestamp'),

        # Onay workflow
        sa.Column('approved', sa.Boolean(), nullable=True,
                  comment='Is approved'),
        sa.Column('approved_by', sa.String(255), nullable=True,
                  comment='Approved by'),

        # Uygulama
        sa.Column('applied', sa.Boolean(), server_default='false',
                  comment='Is applied'),
        sa.Column('applied_at', sa.DateTime(), nullable=True,
                  comment='Application timestamp'),
    )

    op.create_index(
        'ix_trigger_pending',
        'claude_md_improvement_triggers',
        ['processed', 'priority']
    )

    # ======================================================================
    # 4. claude_md_pattern_detections
    # ======================================================================
    op.create_table(
        'claude_md_pattern_detections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('pattern_type', sa.String(50), nullable=False, index=True,
                  comment='error, success, anti'),
        sa.Column('description', sa.Text(), nullable=False,
                  comment='Pattern description'),

        # İstatistikler
        sa.Column('occurrence_count', sa.Integer(), server_default='0',
                  comment='Occurrence count'),
        sa.Column('confidence', sa.Float(), server_default='0.0',
                  comment='Confidence level >= 0.95'),

        # İlişkili kurallar
        sa.Column('related_rules', postgresql.JSONB(), server_default='[]',
                  comment='Related rule IDs'),
        sa.Column('recommendation', sa.Text(), nullable=True,
                  comment='Recommendation'),

        # Timestamps
        sa.Column('detected_at', sa.DateTime(), server_default=sa.text('NOW()'),
                  comment='Detection timestamp'),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('NOW()'),
                  comment='Last seen timestamp'),
        sa.Column('active', sa.Boolean(), server_default='true',
                  comment='Is active'),
    )

    op.create_index(
        'ix_pattern_active_type',
        'claude_md_pattern_detections',
        ['active', 'pattern_type']
    )

    # ======================================================================
    # 5. claude_md_rule_versions
    # ======================================================================
    op.create_table(
        'claude_md_rule_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_id', sa.String(255), nullable=False, index=True,
                  comment='Rule identifier'),
        sa.Column('version', sa.String(50), nullable=False,
                  comment='Semantic version'),
        sa.Column('rule_text', sa.Text(), nullable=False,
                  comment='Rule text'),
        sa.Column('change_reason', sa.Text(), nullable=True,
                  comment='Change reason'),

        # Version tracking
        sa.Column('previous_version_id', postgresql.UUID(as_uuid=True),
                  nullable=True, comment='Previous version ID'),

        # Etkinlik karşılaştırma
        sa.Column('effectiveness_before', sa.Float(), nullable=True,
                  comment='Effectiveness before change'),
        sa.Column('effectiveness_after', sa.Float(), nullable=True,
                  comment='Effectiveness after change'),

        # Metadata
        sa.Column('created_by', sa.String(255), nullable=True,
                  comment='Created by agent/user'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'),
                  index=True, comment='Creation timestamp'),
        sa.Column('is_current', sa.Boolean(), server_default='true',
                  comment='Is current version'),

        sa.UniqueConstraint('rule_id', 'version', name='uq_rule_version'),
    )

    op.create_index(
        'ix_rule_current',
        'claude_md_rule_versions',
        ['rule_id', 'is_current']
    )

    # ======================================================================
    # 6. claude_md_audit_logs
    # ======================================================================
    op.create_table(
        'claude_md_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('action', sa.String(100), nullable=False, index=True,
                  comment='Action performed'),
        sa.Column('entity_type', sa.String(50), nullable=False, index=True,
                  comment='feedback, rule, trigger, pattern'),
        sa.Column('entity_id', sa.String(255), nullable=True,
                  comment='Entity ID'),
        sa.Column('actor', sa.String(255), nullable=True,
                  comment='Actor (agent/user)'),
        sa.Column('reason', sa.Text(), nullable=True,
                  comment='Reason'),
        sa.Column('details', postgresql.JSONB(), server_default='{}',
                  comment='Details'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'),
                  index=True, comment='Creation timestamp'),
    )

    op.create_index(
        'ix_audit_entity',
        'claude_md_audit_logs',
        ['entity_type', 'entity_id']
    )
    op.create_index(
        'ix_audit_action_time',
        'claude_md_audit_logs',
        ['action', 'created_at']
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('claude_md_audit_logs')
    op.drop_table('claude_md_rule_versions')
    op.drop_table('claude_md_pattern_detections')
    op.drop_table('claude_md_improvement_triggers')
    op.drop_table('claude_md_rule_effectiveness')
    op.drop_table('claude_md_feedback_records')
