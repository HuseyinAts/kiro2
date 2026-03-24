"""
Social Features Model Tests — F0-F6
Model importlarini, schema yapisini ve varsayilan degerleri dogrular.
"""

import pytest

# ---- F0: Social Safety ----


class TestSocialSafetyModels:
    def test_content_report_import(self):
        from models.social_safety import ContentReport

        assert ContentReport.__tablename__ == "content_reports"

    def test_moderation_action_import(self):
        from models.social_safety import ModerationAction

        assert ModerationAction.__tablename__ == "moderation_actions"

    def test_blocked_user_import(self):
        from models.social_safety import BlockedUser

        assert BlockedUser.__tablename__ == "blocked_users"

    def test_parent_social_settings_import(self):
        from models.social_safety import ParentSocialSettings

        assert ParentSocialSettings.__tablename__ == "parent_social_settings"

    def test_message_audit_log_import(self):
        from models.social_safety import MessageAuditLog

        assert MessageAuditLog.__tablename__ == "message_audit_log"

    def test_content_type_enum(self):
        from models.social_safety import ContentType

        assert "forum_post" in [e.value for e in ContentType]
        assert "duel_chat" in [e.value for e in ContentType]

    def test_report_reason_enum(self):
        from models.social_safety import ReportReason

        assert "inappropriate" in [e.value for e in ReportReason]
        assert "spam" in [e.value for e in ReportReason]


# ---- F1: Soru Meydani ----


class TestSoruMeydaniModels:
    def test_forum_question_import(self):
        from models.soru_meydani import ForumQuestion

        assert ForumQuestion.__tablename__ == "forum_questions"

    def test_forum_solution_import(self):
        from models.soru_meydani import ForumSolution

        assert ForumSolution.__tablename__ == "forum_solutions"

    def test_forum_vote_import(self):
        from models.soru_meydani import ForumVote

        assert ForumVote.__tablename__ == "forum_votes"

    def test_forum_question_has_required_columns(self):
        from models.soru_meydani import ForumQuestion

        col_names = {c.name for c in ForumQuestion.__table__.columns}
        assert "student_id" in col_names
        assert "subject_area" in col_names
        assert "title" in col_names
        assert "question_type" in col_names
        assert "status" in col_names


# ---- F2: Cozum Duellosu ----


class TestCozumDuellosuModels:
    def test_solution_duel_import(self):
        from models.cozum_duellosu import SolutionDuel

        assert SolutionDuel.__tablename__ == "solution_duels"

    def test_solution_duel_submission_import(self):
        from models.cozum_duellosu import SolutionDuelSubmission

        assert SolutionDuelSubmission.__tablename__ == "solution_duel_submissions"

    def test_solution_duel_vote_import(self):
        from models.cozum_duellosu import SolutionDuelVote

        assert SolutionDuelVote.__tablename__ == "solution_duel_votes"

    def test_duel_has_status_column(self):
        from models.cozum_duellosu import SolutionDuel

        col_names = {c.name for c in SolutionDuel.__table__.columns}
        assert "status" in col_names
        assert "challenger_id" in col_names
        assert "opponent_id" in col_names

    def test_vote_unique_constraint(self):
        from models.cozum_duellosu import SolutionDuelVote

        constraints = [
            c.name
            for c in SolutionDuelVote.__table__.constraints
            if hasattr(c, "name") and c.name
        ]
        assert "uq_duel_vote" in constraints


# ---- F3: Oba Seferleri ----


class TestObaSeferleriModels:
    def test_oba_challenge_import(self):
        from models.oba_seferleri import ObaChallenge

        assert ObaChallenge.__tablename__ == "oba_challenges"

    def test_oba_challenge_progress_import(self):
        from models.oba_seferleri import ObaChallengeProgress

        assert ObaChallengeProgress.__tablename__ == "oba_challenge_progress"

    def test_challenge_has_required_columns(self):
        from models.oba_seferleri import ObaChallenge

        col_names = {c.name for c in ObaChallenge.__table__.columns}
        assert "oba_id" in col_names
        assert "target_value" in col_names
        assert "current_value" in col_names
        assert "completed" in col_names


# ---- F4: Pomodoro ----


class TestPomodoroModels:
    def test_pomodoro_room_import(self):
        from models.pomodoro import PomodoroRoom

        assert PomodoroRoom.__tablename__ == "pomodoro_rooms"

    def test_pomodoro_participant_import(self):
        from models.pomodoro import PomodoroParticipant

        assert PomodoroParticipant.__tablename__ == "pomodoro_participants"

    def test_room_has_subject_and_status(self):
        from models.pomodoro import PomodoroRoom

        col_names = {c.name for c in PomodoroRoom.__table__.columns}
        assert "subject_area" in col_names
        assert "status" in col_names
        assert "work_minutes" in col_names


# ---- F5: Birlikte Streak ----


class TestBirlikteStreakModels:
    def test_streak_pair_import(self):
        from models.birlikte_streak import StreakPair

        assert StreakPair.__tablename__ == "streak_pairs"

    def test_streak_daily_log_import(self):
        from models.birlikte_streak import StreakDailyLog

        assert StreakDailyLog.__tablename__ == "streak_daily_log"

    def test_pair_has_both_students(self):
        from models.birlikte_streak import StreakPair

        col_names = {c.name for c in StreakPair.__table__.columns}
        assert "student_a_id" in col_names
        assert "student_b_id" in col_names
        assert "current_streak" in col_names


# ---- F6: Usta-Cirak ----


class TestUstaCirakModels:
    def test_mentor_pair_import(self):
        from models.usta_cirak import MentorPair

        assert MentorPair.__tablename__ == "mentor_pairs"

    def test_mentor_session_import(self):
        from models.usta_cirak import MentorSession

        assert MentorSession.__tablename__ == "mentor_sessions"

    def test_mentor_feedback_import(self):
        from models.usta_cirak import MentorFeedback

        assert MentorFeedback.__tablename__ == "mentor_feedback"

    def test_pair_has_mentor_and_mentee(self):
        from models.usta_cirak import MentorPair

        col_names = {c.name for c in MentorPair.__table__.columns}
        assert "mentor_id" in col_names
        assert "mentee_id" in col_names
        assert "subject_area" in col_names


# ---- Models __init__.py re-exports ----


class TestModelsInit:
    """models/__init__.py'nin tum social modelleri dogru export ettigini dogrula."""

    @pytest.mark.parametrize(
        "model_name",
        [
            # F0
            "ContentReport",
            "ModerationAction",
            "BlockedUser",
            "ParentSocialSettings",
            "MessageAuditLog",
            # F1
            "ForumQuestion",
            "ForumSolution",
            "ForumVote",
            # F2
            "SolutionDuel",
            "SolutionDuelSubmission",
            "SolutionDuelVote",
            # F3
            "ObaChallenge",
            "ObaChallengeProgress",
            # F4
            "PomodoroRoom",
            "PomodoroParticipant",
            # F5
            "StreakPair",
            "StreakDailyLog",
            # F6
            "MentorPair",
            "MentorSession",
            "MentorFeedback",
        ],
    )
    def test_model_in_init_all(self, model_name):
        import models

        assert model_name in models.__all__, f"{model_name} missing from models.__all__"
        assert hasattr(models, model_name), f"{model_name} not importable from models"
