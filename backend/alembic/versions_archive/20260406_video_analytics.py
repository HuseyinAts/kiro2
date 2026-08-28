"""create_video_analytics_tables

Revision ID: 20260406_video_analytics
Revises: 20260406_ferpa_coppa
Create Date: 2026-04-06
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

revision = "20260406_video_analytics"
down_revision = "20260406_ferpa_coppa"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "video_completion_milestones",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", sa.String, sa.ForeignKey("users.id"), nullable=False, index=True
        ),
        sa.Column("video_id", sa.String(100), nullable=False, index=True),
        sa.Column("video_source", sa.String(20), nullable=False),
        sa.Column("milestone_percentage", sa.Integer, nullable=False),
        sa.Column(
            "achieved_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("badge_awarded", sa.Boolean, default=False),
        sa.Column(
            "badge_id", sa.String, sa.ForeignKey("user_badges.id"), nullable=True
        ),
        sa.UniqueConstraint(
            "user_id",
            "video_id",
            "milestone_percentage",
            name="idx_user_video_milestone",
        ),
    )

    op.create_table(
        "video_notes",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", sa.String, sa.ForeignKey("users.id"), nullable=False, index=True
        ),
        sa.Column("video_id", sa.String(100), nullable=False, index=True),
        sa.Column("video_source", sa.String(20), nullable=False),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("video_watch_sessions.id"),
            nullable=True,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("timestamp", sa.Integer, nullable=False),
        sa.Column("is_important", sa.Boolean, default=False),
        sa.Column("tags", ARRAY(sa.String), nullable=True),
        sa.Column("video_caption", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "video_bookmarks",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", sa.String, sa.ForeignKey("users.id"), nullable=False, index=True
        ),
        sa.Column("video_id", sa.String(100), nullable=False, index=True),
        sa.Column("video_source", sa.String(20), nullable=False),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("video_watch_sessions.id"),
            nullable=True,
        ),
        sa.Column("timestamp", sa.Integer, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("bookmark_type", sa.String(20), default="manual"),
        sa.Column("is_public", sa.Boolean, default=False),
        sa.Column("share_count", sa.Integer, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "video_analytics_summary",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", sa.String, sa.ForeignKey("users.id"), nullable=False, index=True
        ),
        sa.Column("period_type", sa.String(10), nullable=False),
        sa.Column(
            "period_start", sa.DateTime(timezone=True), nullable=False, index=True
        ),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_videos_watched", sa.Integer, default=0),
        sa.Column("total_watch_time", sa.Integer, default=0),
        sa.Column("total_videos_completed", sa.Integer, default=0),
        sa.Column("average_completion_rate", sa.Float, default=0.0),
        sa.Column("total_notes", sa.Integer, default=0),
        sa.Column("total_bookmarks", sa.Integer, default=0),
        sa.Column("average_playback_speed", sa.Float, default=1.0),
        sa.Column("source_breakdown", JSONB, nullable=True),
        sa.Column("subject_breakdown", JSONB, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "user_id", "period_type", "period_start", name="idx_user_period"
        ),
    )


def downgrade():
    op.drop_table("video_analytics_summary")
    op.drop_table("video_bookmarks")
    op.drop_table("video_notes")
    op.drop_table("video_completion_milestones")
