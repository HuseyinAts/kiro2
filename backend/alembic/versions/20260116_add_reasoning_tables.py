"""add_reasoning_tables

Revision ID: 20260116_reasoning
Revises: e73a8e0797c1
Create Date: 2026-01-16 10:00:00.000000
Note: Fixed parent from 0df6ae499ee4 to e73a8e0797c1 for linear chain

Sequential Thinking / Reasoning Tables:
- reasoning_sessions: Ana reasoning oturumları
- reasoning_steps: Adım adım reasoning
- sub_problems: Alt problemler (problem decomposition)
- reasoning_cache: Reasoning cache (7 gün TTL)
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260116_reasoning'
down_revision: Union[str, None] = 'e73a8e0797c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ReasoningSessionStatus enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reasoningsessionstatus AS ENUM (
                'pending', 'in_progress', 'completed', 'failed', 'timeout'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ReasoningStepTypeEnum enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reasoningsteptypeenum AS ENUM (
                'understanding', 'decomposition', 'calculation',
                'inference', 'verification', 'conclusion'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # LLMProviderEnum enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE llmproviderenum AS ENUM (
                'gemini', 'openai', 'claude', 'qwen', 'ensemble'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # reasoning_sessions tablosu
    op.create_table(
        'reasoning_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('problem', sa.Text(), nullable=False, comment='Original problem text'),
        sa.Column('problem_type', sa.String(50), nullable=True, comment='Problem type: math, logic, etc.'),
        sa.Column('context', sa.Text(), nullable=True, comment='Additional context'),
        sa.Column('provider', postgresql.ENUM('gemini', 'openai', 'claude', 'qwen', 'ensemble',
                  name='llmproviderenum', create_type=False),
                  server_default='gemini', comment='LLM provider used'),
        sa.Column('model_name', sa.String(100), nullable=True, comment='Specific model used'),
        sa.Column('use_ensemble', sa.Boolean(), server_default='false', comment='Whether ensemble was used'),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', 'timeout',
                  name='reasoningsessionstatus', create_type=False),
                  server_default='pending', comment='Session status'),
        sa.Column('understanding', sa.Text(), nullable=True, comment='Problem understanding'),
        sa.Column('final_answer', sa.Text(), nullable=True, comment='Final answer'),
        sa.Column('verification', sa.Text(), nullable=True, comment='Verification result'),
        sa.Column('confidence', sa.Float(), server_default='0.0', comment='Confidence score 0-1'),
        sa.Column('total_steps', sa.Integer(), server_default='0', comment='Total reasoning steps'),
        sa.Column('latency_ms', sa.Float(), server_default='0.0', comment='Total latency in ms'),
        sa.Column('tokens_used', sa.Integer(), server_default='0', comment='Total tokens used'),
        sa.Column('cost_usd', sa.Float(), server_default='0.0', comment='Total cost in USD'),
        sa.Column('ensemble_scores', postgresql.JSON(), nullable=True, comment='Scores from each provider'),
        sa.Column('winning_provider', sa.String(50), nullable=True, comment='Winning provider in ensemble'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, comment='User who initiated'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    # reasoning_sessions indexes
    op.create_index('idx_reasoning_sessions_user', 'reasoning_sessions', ['user_id'])
    op.create_index('idx_reasoning_sessions_status', 'reasoning_sessions', ['status'])
    op.create_index('idx_reasoning_sessions_provider', 'reasoning_sessions', ['provider'])
    op.create_index('idx_reasoning_sessions_created', 'reasoning_sessions', ['created_at'])

    # reasoning_steps tablosu
    op.create_table(
        'reasoning_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False, comment='Step order (1, 2, 3...)'),
        sa.Column('step_type', postgresql.ENUM('understanding', 'decomposition', 'calculation',
                  'inference', 'verification', 'conclusion',
                  name='reasoningsteptypeenum', create_type=False),
                  server_default='inference', comment='Type of reasoning step'),
        sa.Column('description', sa.Text(), nullable=False, comment='What this step does'),
        sa.Column('reasoning', sa.Text(), nullable=True, comment='Why this step is needed'),
        sa.Column('result', sa.Text(), nullable=True, comment='Result of this step'),
        sa.Column('parent_step_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='1.0', comment='Confidence 0-1'),
        sa.Column('is_verified', sa.Boolean(), server_default='false', comment='Has been verified'),
        sa.Column('verification_result', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('latency_ms', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['session_id'], ['reasoning_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_step_id'], ['reasoning_steps.id'], ondelete='SET NULL'),
    )

    # reasoning_steps indexes
    op.create_index('idx_reasoning_steps_session', 'reasoning_steps', ['session_id'])
    op.create_index('idx_reasoning_steps_number', 'reasoning_steps', ['session_id', 'step_number'])
    op.create_index('idx_reasoning_steps_type', 'reasoning_steps', ['step_type'])

    # sub_problems tablosu
    op.create_table(
        'sub_problems',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, comment='Order in solving sequence'),
        sa.Column('title', sa.String(255), nullable=False, comment='Sub-problem title'),
        sa.Column('description', sa.Text(), nullable=False, comment='Detailed description'),
        sa.Column('dependencies', postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
                  server_default='{}', comment='IDs of dependent sub-problems'),
        sa.Column('difficulty', sa.Float(), server_default='0.5', comment='Difficulty 0-1'),
        sa.Column('estimated_steps', sa.Integer(), server_default='3'),
        sa.Column('is_solved', sa.Boolean(), server_default='false'),
        sa.Column('solution', sa.Text(), nullable=True),
        sa.Column('solution_steps', postgresql.JSON(), nullable=True, comment='Steps used to solve'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('solved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['reasoning_sessions.id'], ondelete='CASCADE'),
    )

    # sub_problems indexes
    op.create_index('idx_sub_problems_session', 'sub_problems', ['session_id'])
    op.create_index('idx_sub_problems_order', 'sub_problems', ['session_id', 'order_index'])
    op.create_index('idx_sub_problems_solved', 'sub_problems', ['is_solved'])

    # reasoning_cache tablosu
    op.create_table(
        'reasoning_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('problem_hash', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('problem_embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('problem_text', sa.Text(), nullable=False),
        sa.Column('reasoning_data', postgresql.JSON(), nullable=False, comment='Full reasoning result'),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('hit_count', sa.Integer(), server_default='0', comment='Number of cache hits'),
        sa.Column('last_hit', sa.DateTime(), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='0.0'),
        sa.Column('was_verified', sa.Boolean(), server_default='false'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
    )

    # reasoning_cache indexes
    op.create_index('idx_reasoning_cache_hash', 'reasoning_cache', ['problem_hash'])
    op.create_index('idx_reasoning_cache_expires', 'reasoning_cache', ['expires_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_reasoning_cache_expires', table_name='reasoning_cache')
    op.drop_index('idx_reasoning_cache_hash', table_name='reasoning_cache')
    op.drop_table('reasoning_cache')

    op.drop_index('idx_sub_problems_solved', table_name='sub_problems')
    op.drop_index('idx_sub_problems_order', table_name='sub_problems')
    op.drop_index('idx_sub_problems_session', table_name='sub_problems')
    op.drop_table('sub_problems')

    op.drop_index('idx_reasoning_steps_type', table_name='reasoning_steps')
    op.drop_index('idx_reasoning_steps_number', table_name='reasoning_steps')
    op.drop_index('idx_reasoning_steps_session', table_name='reasoning_steps')
    op.drop_table('reasoning_steps')

    op.drop_index('idx_reasoning_sessions_created', table_name='reasoning_sessions')
    op.drop_index('idx_reasoning_sessions_provider', table_name='reasoning_sessions')
    op.drop_index('idx_reasoning_sessions_status', table_name='reasoning_sessions')
    op.drop_index('idx_reasoning_sessions_user', table_name='reasoning_sessions')
    op.drop_table('reasoning_sessions')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS llmproviderenum')
    op.execute('DROP TYPE IF EXISTS reasoningsteptypeenum')
    op.execute('DROP TYPE IF EXISTS reasoningsessionstatus')
