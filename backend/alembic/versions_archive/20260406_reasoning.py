"""create_reasoning_tables

Revision ID: 20260406_reasoning
Revises: 20260406_video_analytics
Create Date: 2026-04-06
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID

from alembic import op

revision = "20260406_reasoning"
down_revision = "20260406_video_analytics"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reasoningsteptypeenum AS ENUM ('understanding','decomposition','calculation','inference','verification','conclusion');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reasoningsessionstatus AS ENUM ('pending','in_progress','completed','failed','timeout');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE llmproviderenum AS ENUM ('gemini','openai','claude','qwen','ensemble');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.create_table(
        "reasoning_sessions",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("problem", sa.Text, nullable=False),
        sa.Column("problem_type", sa.String(50), nullable=True),
        sa.Column("context", sa.Text, nullable=True),
        sa.Column("provider", sa.String(20), default="gemini"),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("use_ensemble", sa.Boolean, default=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("understanding", sa.Text, nullable=True),
        sa.Column("final_answer", sa.Text, nullable=True),
        sa.Column("verification", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("total_steps", sa.Integer, default=0),
        sa.Column("latency_ms", sa.Float, default=0.0),
        sa.Column("tokens_used", sa.Integer, default=0),
        sa.Column("cost_usd", sa.Float, default=0.0),
        sa.Column("ensemble_scores", JSON, nullable=True),
        sa.Column("winning_provider", sa.String(50), nullable=True),
        sa.Column(
            "user_id",
            sa.String,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_reasoning_sessions_user", "reasoning_sessions", ["user_id"])
    op.create_index("idx_reasoning_sessions_status", "reasoning_sessions", ["status"])
    op.create_index(
        "idx_reasoning_sessions_created", "reasoning_sessions", ["created_at"]
    )

    op.create_table(
        "reasoning_steps",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("reasoning_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("step_type", sa.String(20), default="inference"),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("result", sa.Text, nullable=True),
        sa.Column(
            "parent_step_id",
            UUID(as_uuid=True),
            sa.ForeignKey("reasoning_steps.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence", sa.Float, default=1.0),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verification_result", sa.Text, nullable=True),
        sa.Column("start_time", sa.DateTime, nullable=True),
        sa.Column("end_time", sa.DateTime, nullable=True),
        sa.Column("latency_ms", sa.Float, default=0.0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_reasoning_steps_session", "reasoning_steps", ["session_id"])
    op.create_index(
        "idx_reasoning_steps_number", "reasoning_steps", ["session_id", "step_number"]
    )

    op.create_table(
        "sub_problems",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("reasoning_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("dependencies", ARRAY(UUID(as_uuid=True)), nullable=True),
        sa.Column("difficulty", sa.Float, default=0.5),
        sa.Column("estimated_steps", sa.Integer, default=3),
        sa.Column("is_solved", sa.Boolean, default=False),
        sa.Column("solution", sa.Text, nullable=True),
        sa.Column("solution_steps", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("solved_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_sub_problems_session", "sub_problems", ["session_id"])

    op.create_table(
        "reasoning_cache",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("problem_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("problem_embedding", ARRAY(sa.Float), nullable=True),
        sa.Column("problem_text", sa.Text, nullable=False),
        sa.Column("reasoning_data", JSON, nullable=False),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("hit_count", sa.Integer, default=0),
        sa.Column("last_hit", sa.DateTime, nullable=True),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("was_verified", sa.Boolean, default=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_reasoning_cache_expires", "reasoning_cache", ["expires_at"])


def downgrade():
    op.drop_table("reasoning_cache")
    op.drop_table("sub_problems")
    op.drop_table("reasoning_steps")
    op.drop_table("reasoning_sessions")
    op.execute("DROP TYPE IF EXISTS llmproviderenum")
    op.execute("DROP TYPE IF EXISTS reasoningsessionstatus")
    op.execute("DROP TYPE IF EXISTS reasoningsteptypeenum")
