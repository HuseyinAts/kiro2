"""faz1 Katman B/C — kalan tenant-owned tablolara org_id (toplu)

60 tablo: analytics/dashboard + büyük/düşük-hassasiyet (image_uploads 70K vb).
topic_hierarchy HARİÇ (parent_id=üst-konu, global taksonomi).
Backfill=direct legacy (tek-kiracılı). nullable→NOT NULL→server_default.
Reversible.

Revision ID: faz1_katmanBC_20260704
Revises: faz1_rls_20260704
Create Date: 2026-07-04
"""
from collections.abc import Sequence
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "faz1_katmanBC_20260704"
down_revision: Union[str, None] = "faz1_rls_20260704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY = "org_legacy_default"
TABLES = ['api_keys', 'audit_logs', 'chat_analytics', 'chat_sessions', 'classrooms', 'coaching_events', 'daily_plans', 'daily_quests', 'duel_ratings', 'dungeon_progress', 'eba_video_recommendations', 'eba_video_usage', 'eba_video_watches', 'forum_questions', 'fsrs_student_profiles', 'fsrs_study_sessions', 'fsrs_subject_stats', 'image_uploads', 'khan_oauth_tokens', 'kiro2_cat_sessions', 'kvkk_data_export_requests', 'league_history', 'league_memberships', 'learning_analytics', 'learning_path_student_profiles', 'learning_progress_daily', 'manipulative_activities', 'manipulative_progress', 'notifications', 'oba_challenge_progress', 'oba_uyeler', 'osb_settings', 'parent_child', 'parent_notifications', 'parent_social_settings', 'point_transactions', 'pomodoro_participants', 'quiz_submissions', 'realm_progress', 'refresh_tokens', 'sessions', 'solution_duel_submissions', 'streak_daily_log', 'streak_tracking', 'streaks', 'student_engagement_signals', 'student_goals', 'student_learning_profiles', 'student_nano_skill_mastery', 'study_plans', 'study_rooms', 'study_sessions', 'teacher_pool_profiles', 'topic_completions', 'user_achievements', 'user_badges', 'weekly_progress', 'xp_transactions', 'yks_exam_goals', 'zpd_history']


def upgrade() -> None:
    conn = op.get_bind()
    for tbl in TABLES:
        op.add_column(tbl, sa.Column("organization_id", sa.String(), nullable=True))
        op.create_foreign_key(f"fk_{tbl}_organization", tbl, "organizations", ["organization_id"], ["id"], ondelete="RESTRICT")
        op.create_index(f"idx_{tbl}_organization_id", tbl, ["organization_id"])
        op.execute(sa.text(f"UPDATE {tbl} SET organization_id = :l WHERE organization_id IS NULL").bindparams(l=LEGACY))
        n = conn.execute(sa.text(f"SELECT count(*) FROM {tbl} WHERE organization_id IS NULL")).scalar()
        if n:
            raise RuntimeError(f"{tbl}: {n} NULL")
        op.alter_column(tbl, "organization_id", existing_type=sa.String(), nullable=False, server_default=LEGACY)


def downgrade() -> None:
    for tbl in TABLES:
        op.drop_index(f"idx_{tbl}_organization_id", table_name=tbl)
        op.drop_constraint(f"fk_{tbl}_organization", tbl, type_="foreignkey")
        op.drop_column(tbl, "organization_id")
