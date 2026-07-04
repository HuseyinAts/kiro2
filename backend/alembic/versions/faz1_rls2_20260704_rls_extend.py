"""faz1 RLS genişletme — kalan 60 org-scoped tabloya RLS

Katman B/C + grup-2 kalan tabloları: tenant_isolation policy (permissive-when-unset)
+ FORCE. faz1_rls (13 tablo) ile aynı desen. identity tablolar HARİÇ.
Reversible.

Revision ID: faz1_rls2_20260704
Revises: faz1_katmanBC_20260704
Create Date: 2026-07-04
"""
from collections.abc import Sequence
from typing import Union
from alembic import op

revision: str = "faz1_rls2_20260704"
down_revision: Union[str, None] = "faz1_katmanBC_20260704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RLS_TABLES = ['api_keys', 'audit_logs', 'chat_analytics', 'chat_sessions', 'classrooms', 'coaching_events', 'daily_plans', 'daily_quests', 'duel_ratings', 'dungeon_progress', 'eba_video_recommendations', 'eba_video_usage', 'eba_video_watches', 'forum_questions', 'fsrs_student_profiles', 'fsrs_study_sessions', 'fsrs_subject_stats', 'image_uploads', 'khan_oauth_tokens', 'kiro2_cat_sessions', 'kvkk_data_export_requests', 'league_history', 'league_memberships', 'learning_analytics', 'learning_path_student_profiles', 'learning_progress_daily', 'manipulative_activities', 'manipulative_progress', 'notifications', 'oba_challenge_progress', 'oba_uyeler', 'osb_settings', 'parent_child', 'parent_notifications', 'parent_social_settings', 'point_transactions', 'pomodoro_participants', 'quiz_submissions', 'realm_progress', 'refresh_tokens', 'sessions', 'solution_duel_submissions', 'streak_daily_log', 'streak_tracking', 'streaks', 'student_engagement_signals', 'student_goals', 'student_learning_profiles', 'student_nano_skill_mastery', 'study_plans', 'study_rooms', 'study_sessions', 'teacher_pool_profiles', 'topic_completions', 'user_achievements', 'user_badges', 'weekly_progress', 'xp_transactions', 'yks_exam_goals', 'zpd_history']
_PRED = (
    "current_setting('app.current_org_id', true) IS NULL "
    "OR current_setting('app.current_org_id', true) = '' "
    "OR organization_id = current_setting('app.current_org_id', true)"
)


def upgrade() -> None:
    for t in RLS_TABLES:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant_isolation ON {t} FOR ALL USING ({_PRED}) WITH CHECK ({_PRED})")


def downgrade() -> None:
    for t in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {t}")
        op.execute(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY")
