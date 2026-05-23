"""S197 phantom audit cleanup — basic coverage for Turkish exam middleware.

Targets: enums, ExamContext dataclass, pure helper methods, and factory
functions. All heavy I/O dependencies (cache, metrics, event bus, config)
are patched at import time so no external services are required.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Module-level dep patching — must happen before any import of the module
# ---------------------------------------------------------------------------

_MOCK_MODULES = [
    "core.application_metrics",
    "core.cache_system_integration",
    "core.structured_logging",
    "core.unified_api_gateway",
    "core.unified_config",
    "core.unified_event_bus",
    "core.auth_middleware",
    "core.turkish_exam_event_handlers",
]


@pytest.fixture(scope="module", autouse=True)
def _patch_heavy_deps():
    """Inject mocks for all heavy dependencies before the module loads."""
    injected = []
    for mod in _MOCK_MODULES:
        if mod not in sys.modules:
            sys.modules[mod] = MagicMock()
            injected.append(mod)

    # Specific return values expected at module level
    sys.modules["core.unified_config"].get_unified_config.return_value = MagicMock()
    sys.modules["core.structured_logging"].LogCategory = MagicMock()
    sys.modules["core.structured_logging"].get_logger.return_value = MagicMock()

    yield

    for mod in injected:
        sys.modules.pop(mod, None)


# ---------------------------------------------------------------------------
# Lazy import after fixture scope is established
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tem():
    """Return the middleware module (imported once per test module)."""
    import core.turkish_exam_middleware as _tem

    return _tem


# ===========================================================================
# ExamPeriod enum
# ===========================================================================


class TestExamPeriod:
    def test_exam_period_has_five_members(self, tem):
        assert len(list(tem.ExamPeriod)) == 5

    def test_exam_period_registration_value(self, tem):
        assert tem.ExamPeriod.REGISTRATION.value == "registration"

    def test_exam_period_preparation_value(self, tem):
        assert tem.ExamPeriod.PREPARATION.value == "preparation"

    def test_exam_period_exam_week_value(self, tem):
        assert tem.ExamPeriod.EXAM_WEEK.value == "exam_week"

    def test_exam_period_results_value(self, tem):
        assert tem.ExamPeriod.RESULTS.value == "results"

    def test_exam_period_off_season_value(self, tem):
        assert tem.ExamPeriod.OFF_SEASON.value == "off_season"

    def test_exam_period_members_are_strings(self, tem):
        for member in tem.ExamPeriod:
            assert isinstance(member.value, str)


# ===========================================================================
# ExamSecurityLevel enum
# ===========================================================================


class TestExamSecurityLevel:
    def test_exam_security_level_has_four_members(self, tem):
        assert len(list(tem.ExamSecurityLevel)) == 4

    def test_low_value(self, tem):
        assert tem.ExamSecurityLevel.LOW.value == "low"

    def test_medium_value(self, tem):
        assert tem.ExamSecurityLevel.MEDIUM.value == "medium"

    def test_high_value(self, tem):
        assert tem.ExamSecurityLevel.HIGH.value == "high"

    def test_maximum_value(self, tem):
        assert tem.ExamSecurityLevel.MAXIMUM.value == "maximum"

    def test_security_level_values_are_strings(self, tem):
        for member in tem.ExamSecurityLevel:
            assert isinstance(member.value, str)


# ===========================================================================
# ExamContext dataclass
# ===========================================================================


class TestExamContext:
    def test_exam_context_is_dataclass(self, tem):
        import dataclasses

        assert dataclasses.is_dataclass(tem.ExamContext)

    def test_default_exam_type_is_none(self, tem):
        ctx = tem.ExamContext()
        assert ctx.exam_type is None

    def test_default_session_id_is_none(self, tem):
        ctx = tem.ExamContext()
        assert ctx.session_id is None

    def test_default_current_period_is_off_season(self, tem):
        ctx = tem.ExamContext()
        assert ctx.current_period == tem.ExamPeriod.OFF_SEASON

    def test_default_security_level_is_low(self, tem):
        ctx = tem.ExamContext()
        assert ctx.security_level == tem.ExamSecurityLevel.LOW

    def test_default_time_remaining_is_none(self, tem):
        ctx = tem.ExamContext()
        assert ctx.time_remaining is None

    def test_default_question_number_is_none(self, tem):
        ctx = tem.ExamContext()
        assert ctx.question_number is None

    def test_default_total_questions_is_none(self, tem):
        ctx = tem.ExamContext()
        assert ctx.total_questions is None

    def test_default_subject_is_none(self, tem):
        ctx = tem.ExamContext()
        assert ctx.subject is None

    def test_default_difficulty_is_orta(self, tem):
        ctx = tem.ExamContext()
        assert ctx.difficulty == "orta"

    def test_default_is_practice_is_true(self, tem):
        ctx = tem.ExamContext()
        assert ctx.is_practice is True

    def test_default_metadata_is_empty_dict(self, tem):
        ctx = tem.ExamContext()
        assert ctx.metadata == {}

    def test_metadata_instances_are_independent(self, tem):
        """default_factory must produce a new dict per instance."""
        ctx1 = tem.ExamContext()
        ctx2 = tem.ExamContext()
        ctx1.metadata["key"] = "value"
        assert "key" not in ctx2.metadata

    def test_custom_instantiation(self, tem):
        ctx = tem.ExamContext(
            session_id="sess-001",
            current_period=tem.ExamPeriod.EXAM_WEEK,
            security_level=tem.ExamSecurityLevel.HIGH,
            time_remaining=90,
            question_number=5,
            total_questions=40,
            subject="matematik",
            difficulty="zor",
            is_practice=False,
        )
        assert ctx.session_id == "sess-001"
        assert ctx.current_period == tem.ExamPeriod.EXAM_WEEK
        assert ctx.security_level == tem.ExamSecurityLevel.HIGH
        assert ctx.time_remaining == 90
        assert ctx.question_number == 5
        assert ctx.total_questions == 40
        assert ctx.subject == "matematik"
        assert ctx.difficulty == "zor"
        assert ctx.is_practice is False

    def test_eleven_fields_defined(self, tem):
        import dataclasses

        assert len(dataclasses.fields(tem.ExamContext)) == 11


# ===========================================================================
# configure_exam_middleware — pure function, no I/O
# ===========================================================================


class TestConfigureExamMiddleware:
    def test_tyt_timeout_is_135(self, tem):
        cfg = tem.configure_exam_middleware("tyt")
        assert cfg["session_timeout_minutes"] == 135

    def test_ayt_timeout_is_180(self, tem):
        cfg = tem.configure_exam_middleware("ayt")
        assert cfg["session_timeout_minutes"] == 180

    def test_unknown_type_timeout_is_240(self, tem):
        cfg = tem.configure_exam_middleware("yks")
        assert cfg["session_timeout_minutes"] == 240

    def test_exam_monitoring_enabled_by_default(self, tem):
        cfg = tem.configure_exam_middleware("tyt")
        assert cfg["exam_monitoring"] is True

    def test_anti_cheat_enabled_by_default(self, tem):
        cfg = tem.configure_exam_middleware("ayt")
        assert cfg["anti_cheat_enabled"] is True

    def test_case_insensitive_tyt(self, tem):
        cfg = tem.configure_exam_middleware("TYT")
        assert cfg["session_timeout_minutes"] == 135

    def test_case_insensitive_ayt(self, tem):
        cfg = tem.configure_exam_middleware("AYT")
        assert cfg["session_timeout_minutes"] == 180


# ===========================================================================
# ExamSessionMiddleware._extract_exam_type_from_path — pure helper
# ===========================================================================


class TestExtractExamTypeFromPath:
    @pytest.fixture
    def session_mw(self, tem):
        return tem.ExamSessionMiddleware({})

    def test_tyt_path_lowercase(self, session_mw):
        assert session_mw._extract_exam_type_from_path("/api/v1/tyt/start") == "tyt"

    def test_tyt_path_uppercase(self, session_mw):
        assert session_mw._extract_exam_type_from_path("/api/v1/TYT/start") == "tyt"

    def test_ayt_path(self, session_mw):
        assert (
            session_mw._extract_exam_type_from_path("/api/v1/AYT/question/1") == "ayt"
        )

    def test_yks_path(self, session_mw):
        assert session_mw._extract_exam_type_from_path("/api/v1/yks/info") == "yks"

    def test_unknown_path(self, session_mw):
        assert session_mw._extract_exam_type_from_path("/api/v1/practice") == "unknown"


# ===========================================================================
# ExamSessionMiddleware._is_session_expired — pure helper (no I/O)
# ===========================================================================


class TestIsSessionExpired:
    @pytest.fixture
    def session_mw(self, tem):
        return tem.ExamSessionMiddleware({"session_timeout_minutes": 240})

    def test_recent_session_not_expired(self, session_mw):
        data = {
            "last_activity": (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
        }
        assert session_mw._is_session_expired(data) is False

    def test_old_session_is_expired(self, session_mw):
        data = {"last_activity": (datetime.now(UTC) - timedelta(hours=5)).isoformat()}
        assert session_mw._is_session_expired(data) is True

    def test_exactly_at_timeout_boundary(self, session_mw):
        # 240 min ago — should be expired (timedelta comparison is strict >)
        data = {
            "last_activity": (
                datetime.now(UTC) - timedelta(minutes=240, seconds=1)
            ).isoformat()
        }
        assert session_mw._is_session_expired(data) is True

    def test_just_before_timeout_not_expired(self, session_mw):
        data = {
            "last_activity": (datetime.now(UTC) - timedelta(minutes=239)).isoformat()
        }
        assert session_mw._is_session_expired(data) is False


# ===========================================================================
# ExamSessionMiddleware._calculate_time_remaining — pure helper
# ===========================================================================


class TestCalculateTimeRemaining:
    @pytest.fixture
    def session_mw(self, tem):
        return tem.ExamSessionMiddleware({"session_timeout_minutes": 240})

    def test_returns_int(self, session_mw):
        data = {"started_at": (datetime.now(UTC) - timedelta(minutes=30)).isoformat()}
        result = session_mw._calculate_time_remaining(data)
        assert isinstance(result, int)

    def test_approx_value_for_30_min_elapsed(self, session_mw):
        data = {"started_at": (datetime.now(UTC) - timedelta(minutes=30)).isoformat()}
        result = session_mw._calculate_time_remaining(data)
        assert 200 <= result <= 215  # 240 - 30 ≈ 210

    def test_returns_zero_when_expired(self, session_mw):
        data = {"started_at": (datetime.now(UTC) - timedelta(hours=6)).isoformat()}
        result = session_mw._calculate_time_remaining(data)
        assert result == 0  # clamped at max(0, ...)

    def test_invalid_data_returns_none(self, session_mw):
        result = session_mw._calculate_time_remaining({"started_at": "not-a-date"})
        assert result is None


# ===========================================================================
# ExamSecurityMiddleware._is_user_blocked — pure helper (no I/O)
# ===========================================================================


class TestIsUserBlocked:
    @pytest.fixture
    def security_mw(self, tem):
        return tem.ExamSecurityMiddleware({})

    def test_unknown_user_not_blocked(self, security_mw):
        assert security_mw._is_user_blocked(9999) is False

    def test_user_blocked_with_future_expiry(self, security_mw):
        security_mw.blocked_users[42] = datetime.now(UTC) + timedelta(hours=1)
        assert security_mw._is_user_blocked(42) is True

    def test_block_expires_and_user_is_unblocked(self, security_mw):
        security_mw.blocked_users[43] = datetime.now(UTC) - timedelta(minutes=1)
        assert security_mw._is_user_blocked(43) is False
        # Entry should have been cleaned up
        assert 43 not in security_mw.blocked_users


# ===========================================================================
# Factory functions
# ===========================================================================


class TestFactoryFunctions:
    def test_create_turkish_language_middleware_returns_instance(self, tem):
        instance = tem.create_turkish_language_middleware()
        assert isinstance(instance, tem.TurkishLanguageMiddleware)

    def test_create_exam_security_middleware_returns_instance(self, tem):
        instance = tem.create_exam_security_middleware()
        assert isinstance(instance, tem.ExamSecurityMiddleware)

    def test_create_exam_session_middleware_returns_instance(self, tem):
        instance = tem.create_exam_session_middleware()
        assert isinstance(instance, tem.ExamSessionMiddleware)

    def test_factory_accepts_custom_config(self, tem):
        instance = tem.create_exam_security_middleware(
            {"anti_cheat_enabled": False, "exam_monitoring": False}
        )
        assert instance.anti_cheat_enabled is False
        assert instance.exam_monitoring is False

    def test_session_middleware_default_timeout(self, tem):
        instance = tem.create_exam_session_middleware()
        assert instance.session_timeout_minutes == 240

    def test_get_turkish_exam_middleware_stack_returns_list(self, tem):
        stack = tem.get_turkish_exam_middleware_stack()
        assert isinstance(stack, list)
        assert len(stack) == 3

    def test_middleware_stack_has_named_tuples(self, tem):
        stack = tem.get_turkish_exam_middleware_stack()
        names = [item[0] for item in stack]
        assert "exam_security" in names
        assert "exam_session" in names
        assert "turkish_language" in names


# ===========================================================================
# TurkishLanguageMiddleware — init-level (no __call__)
# ===========================================================================


class TestTurkishLanguageMiddlewareInit:
    def test_turkish_subjects_dict_has_matematik(self, tem):
        mw = tem.TurkishLanguageMiddleware({})
        assert "matematik" in mw.turkish_subjects

    def test_turkish_subjects_count(self, tem):
        mw = tem.TurkishLanguageMiddleware({})
        assert len(mw.turkish_subjects) >= 8

    def test_exam_translations_has_tyt(self, tem):
        mw = tem.TurkishLanguageMiddleware({})
        assert "tyt" in mw.exam_translations
        assert "ayt" in mw.exam_translations

    def test_common_phrases_has_exam_keys(self, tem):
        mw = tem.TurkishLanguageMiddleware({})
        assert "exam_started" in mw.common_phrases
        assert "exam_completed" in mw.common_phrases
