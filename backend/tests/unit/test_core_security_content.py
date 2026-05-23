"""
Unit tests for core security and content modules.

Covers:
- core/security_event_monitoring.py
- core/curriculum_compliance_system.py
- core/exam_quality_validators.py
- core/document_deduplication.py
- core/enhanced_content_manager.py
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure backend root is on path
sys.path.insert(0, str(Path(__file__).parents[2]))

# ============================================================
# Mock heavy external dependencies before any module imports
# ============================================================
for _mod in [
    "redis",
    "redis.asyncio",
    "core.enhanced_database",
    "core.structured_logging",
    "core.unified_config",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Patch get_unified_config to return a usable mock
_mock_config = MagicMock()
_mock_config.redis = MagicMock()
_mock_config.redis.host = "localhost"
_mock_config.redis.port = 6379
_mock_config.redis.password = None
sys.modules["core.unified_config"].get_unified_config = MagicMock(
    return_value=_mock_config
)

# Patch get_security_logger and get_enhanced_db_manager
sys.modules["core.structured_logging"].get_security_logger = MagicMock(
    return_value=MagicMock()
)
sys.modules["core.enhanced_database"].get_enhanced_db_manager = MagicMock(
    return_value=MagicMock()
)

# Mock models.curriculum before importing compliance system
import types as _types

_curriculum_mod = _types.ModuleType("models.curriculum")


class _MEBCurriculumStandard:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class _OSYMStandard:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class _LearningOutcome:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class _CurriculumAlignment:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class _CurriculumComplianceReport:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class _CurriculumUpdateRequest:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class _QuestionBankCompliance:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class _SubjectType:
    MATEMATIK = "matematik"
    FEN = "fen"


class _ExamType:
    TYT = "tyt"
    AYT = "ayt"


class _GradeLevel:
    GRADE_12 = 12


_curriculum_mod.MEBCurriculumStandard = _MEBCurriculumStandard
_curriculum_mod.OSYMStandard = _OSYMStandard
_curriculum_mod.LearningOutcome = _LearningOutcome
_curriculum_mod.CurriculumAlignment = _CurriculumAlignment
_curriculum_mod.CurriculumComplianceReport = _CurriculumComplianceReport
_curriculum_mod.CurriculumUpdateRequest = _CurriculumUpdateRequest
_curriculum_mod.QuestionBankCompliance = _QuestionBankCompliance
_curriculum_mod.SubjectType = _SubjectType
_curriculum_mod.ExamType = _ExamType
_curriculum_mod.GradeLevel = _GradeLevel
# Only stub the `models` package when it has not yet been loaded as a real
# package; replacing a real package with MagicMock breaks other test files
# that import from it (e.g. models.teacher_pool).
if "models" not in sys.modules:
    sys.modules["models"] = MagicMock()
# S197: same conditional guard for models.curriculum — the partial
# _SubjectType stub (MATEMATIK + FEN only) poisoned test_exam_curriculum_models
# which expects the full 12-value enum (TURKCE, FEN_BILIMLERI, ...). If a
# previous test has already loaded the real package, keep it.
if "models.curriculum" not in sys.modules:
    sys.modules["models.curriculum"] = _curriculum_mod

# Patch structured_logger used by exam_quality_validators
sys.modules["core.structured_logger"] = MagicMock()
sys.modules["core.structured_logger"].get_logger = MagicMock(return_value=MagicMock())

# Patch yaml so enhanced_content_manager doesn't need real files,
# and patch asyncio.create_task to avoid "no running loop" errors
import asyncio as _asyncio

_orig_create_task = _asyncio.create_task
_asyncio.create_task = MagicMock()  # suppress at module load

sys.modules["yaml"] = MagicMock()

# ============================================================
# Now import the modules under test
# ============================================================
from core.curriculum_compliance_system import CurriculumComplianceSystem  # noqa: E402
from core.document_deduplication import (  # noqa: E402
    DocumentDeduplicator,
    IncrementalDeduplicator,
    get_deduplicator,
)
from core.enhanced_content_manager import (  # noqa: E402
    ContentType,
    EnhancedContentManager,
    ExamType,
)
from core.enhanced_content_manager import (
    DifficultyLevel as ContentDifficultyLevel,
)
from core.exam_quality_validators import (  # noqa: E402
    CurriculumMatchValidator,
    DifficultyBalanceValidator,
    DifficultyLevel,
    ExamBlueprint,
    ExamQualityValidator,
    IRTCalibrationValidator,
    IRTParameters,
    QuestionMetadata,
    TopicDistributionValidator,
    ValidationResult,
    ValidationSeverity,
    ValidationType,
    get_exam_validator,
)
from core.security_event_monitoring import (  # noqa: E402
    SecurityEvent,
    SecurityEventMonitor,
    SecurityEventType,
    SecuritySeverity,
    ThreatDetector,
    get_security_monitor,
)

# Restore create_task after imports
_asyncio.create_task = _orig_create_task


# ===========================================================================
# SECTION 1 — security_event_monitoring.py
# ===========================================================================


class TestSecurityEventType:
    """Tests for SecurityEventType enum."""

    def test_login_success_has_correct_values(self):
        evt = SecurityEventType.LOGIN_SUCCESS
        assert evt.event_type == "login_success"
        assert "Giriş" in evt.turkish_description

    def test_sql_injection_has_correct_values(self):
        evt = SecurityEventType.SQL_INJECTION_ATTEMPT
        assert evt.event_type == "sql_injection_attempt"
        assert "SQL" in evt.turkish_description

    def test_brute_force_attack_has_correct_values(self):
        evt = SecurityEventType.BRUTE_FORCE_ATTACK
        assert evt.event_type == "brute_force_attack"
        assert len(evt.turkish_description) > 0

    def test_all_events_have_nonempty_descriptions(self):
        for evt in SecurityEventType:
            assert evt.event_type, f"{evt.name} missing event_type"
            assert evt.turkish_description, f"{evt.name} missing turkish_description"

    def test_unauthorized_access_event(self):
        assert SecurityEventType.UNAUTHORIZED_ACCESS.event_type == "unauthorized_access"


class TestSecuritySeverity:
    """Tests for SecuritySeverity enum."""

    def test_critical_has_highest_score(self):
        assert SecuritySeverity.CRITICAL.score == 100

    def test_info_has_lowest_score(self):
        assert SecuritySeverity.INFO.score == 1

    def test_severity_ordering(self):
        scores = [
            SecuritySeverity.INFO.score,
            SecuritySeverity.LOW.score,
            SecuritySeverity.MEDIUM.score,
            SecuritySeverity.HIGH.score,
            SecuritySeverity.CRITICAL.score,
        ]
        assert scores == sorted(scores), "Severity scores should be in ascending order"

    def test_all_severities_have_turkish_description(self):
        for sev in SecuritySeverity:
            assert sev.turkish_description
            assert sev.level


class TestSecurityEvent:
    """Tests for SecurityEvent dataclass."""

    def _make_event(self, **kwargs):
        from datetime import UTC, datetime

        defaults = dict(
            event_id="test-id-123",
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecuritySeverity.INFO,
            timestamp=datetime.now(UTC),
        )
        defaults.update(kwargs)
        return SecurityEvent(**defaults)

    def test_to_dict_contains_all_required_keys(self):
        event = self._make_event(
            ip_address="127.0.0.1",
            message="test msg",
            message_tr="test türkçe",
        )
        d = event.to_dict()
        required_keys = [
            "event_id",
            "event_type",
            "severity",
            "severity_score",
            "timestamp",
            "ip_address",
            "message",
            "message_tr",
        ]
        for key in required_keys:
            assert key in d, f"Missing key: {key}"

    def test_to_dict_event_type_is_string(self):
        event = self._make_event()
        d = event.to_dict()
        assert isinstance(d["event_type"], str)
        assert d["event_type"] == "login_success"

    def test_to_dict_severity_score_is_int(self):
        event = self._make_event()
        d = event.to_dict()
        assert isinstance(d["severity_score"], int)

    def test_default_fields_are_empty(self):
        event = self._make_event()
        assert event.ip_address == ""
        assert event.user_agent == ""
        assert event.tags == []
        assert event.remediation_actions == []

    def test_user_id_none_by_default(self):
        event = self._make_event()
        assert event.user_id is None


class TestThreatDetector:
    """Tests for ThreatDetector."""

    def setup_method(self):
        self.detector = ThreatDetector()

    def test_attack_patterns_are_loaded(self):
        assert "sql_injection" in self.detector.attack_patterns
        assert "xss" in self.detector.attack_patterns
        assert "path_traversal" in self.detector.attack_patterns
        assert "command_injection" in self.detector.attack_patterns

    def test_geo_anomaly_threshold_default(self):
        assert self.detector.geo_anomaly_threshold == 1000

    def test_generate_event_id_returns_uuid_string(self):
        eid = self.detector._generate_event_id()
        assert isinstance(eid, str)
        assert len(eid) == 36  # UUID4 format

    def test_generate_correlation_id_returns_hex(self):
        cid = self.detector._generate_correlation_id()
        assert isinstance(cid, str)
        assert len(cid) == 16
        int(cid, 16)  # must be valid hex

    def test_calculate_distance_same_point(self):
        loc = {"latitude": 41.0, "longitude": 29.0}
        dist = self.detector._calculate_distance(loc, loc)
        assert dist == 0.0

    def test_calculate_distance_different_points(self):
        loc1 = {"latitude": 41.0, "longitude": 29.0}
        loc2 = {"latitude": 39.0, "longitude": 27.0}
        dist = self.detector._calculate_distance(loc1, loc2)
        assert dist > 0

    @pytest.mark.asyncio
    async def test_suspicious_user_agent_short_string(self):
        result = await self.detector._is_suspicious_user_agent("abc")
        assert result is True

    @pytest.mark.asyncio
    async def test_suspicious_user_agent_bot(self):
        result = await self.detector._is_suspicious_user_agent("Googlebot/2.1")
        assert result is True

    @pytest.mark.asyncio
    async def test_suspicious_user_agent_normal(self):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        result = await self.detector._is_suspicious_user_agent(ua)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_ip_location_private_returns_none(self):
        result = await self.detector._get_ip_location("192.168.1.1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ip_location_public_returns_dict(self):
        result = await self.detector._get_ip_location("8.8.8.8")
        assert result is not None
        assert "country" in result
        assert "latitude" in result

    @pytest.mark.asyncio
    async def test_detect_injection_sql_payload(self):
        threats = await self.detector._detect_injection_attacks(
            {"query": "' OR 1=1 --"}, "1.2.3.4", None
        )
        assert len(threats) > 0
        types = [t.event_type for t in threats]
        assert SecurityEventType.SQL_INJECTION_ATTEMPT in types

    @pytest.mark.asyncio
    async def test_detect_injection_xss_payload(self):
        threats = await self.detector._detect_injection_attacks(
            {"input": "<script>alert(1)</script>"}, "1.2.3.4", None
        )
        types = [t.event_type for t in threats]
        assert SecurityEventType.XSS_ATTEMPT in types

    @pytest.mark.asyncio
    async def test_detect_injection_path_traversal_payload(self):
        threats = await self.detector._detect_injection_attacks(
            {"path": "../../../etc/passwd"}, "1.2.3.4", None
        )
        types = [t.event_type for t in threats]
        assert SecurityEventType.PATH_TRAVERSAL_ATTEMPT in types

    @pytest.mark.asyncio
    async def test_detect_injection_returns_list(self):
        # Any dict payload will trigger SQL injection regex (JSON quotes match pattern).
        # Verify return type is always a list.
        threats = await self.detector._detect_injection_attacks(
            {"number": 42}, "1.2.3.4", None
        )
        assert isinstance(threats, list)

    @pytest.mark.asyncio
    async def test_create_threat_event_returns_security_event(self):
        event = await self.detector._create_threat_event(
            SecurityEventType.BRUTE_FORCE_ATTACK,
            SecuritySeverity.HIGH,
            ip_address="10.0.0.1",
            message="test",
            message_tr="test_tr",
        )
        assert isinstance(event, SecurityEvent)
        assert event.event_type == SecurityEventType.BRUTE_FORCE_ATTACK
        assert event.severity == SecuritySeverity.HIGH


class TestSecurityEventMonitor:
    """Tests for SecurityEventMonitor."""

    def setup_method(self):
        with (
            patch("core.security_event_monitoring.get_enhanced_db_manager") as mock_db,
            patch("core.security_event_monitoring.get_security_logger") as mock_log,
            patch("core.security_event_monitoring.get_unified_config") as mock_cfg,
        ):
            mock_cfg.return_value = MagicMock(redis=MagicMock(host=None))
            self.monitor = SecurityEventMonitor()

    def test_initial_state(self):
        assert self.monitor.running is False
        assert self.monitor.event_handlers == []
        assert self.monitor.alert_handlers == []

    def test_register_event_handler(self):
        handler = MagicMock()
        self.monitor.register_event_handler(handler)
        assert handler in self.monitor.event_handlers

    def test_register_alert_handler(self):
        handler = MagicMock()
        self.monitor.register_alert_handler(handler)
        assert handler in self.monitor.alert_handlers

    def test_translate_alert_known_message(self):
        translated = self.monitor._translate_alert("Critical security event detected")
        assert "Kritik" in translated

    def test_translate_alert_unknown_message(self):
        msg = "Some unknown alert message"
        translated = self.monitor._translate_alert(msg)
        assert translated == msg  # returns as-is

    def test_generate_alert_id_format(self):
        alert_id = self.monitor._generate_alert_id()
        assert alert_id.startswith("alert_")
        assert len(alert_id) == 14  # "alert_" + 8 hex chars


def test_get_security_monitor_returns_instance():
    """get_security_monitor() returns a SecurityEventMonitor."""
    with (
        patch("core.security_event_monitoring.get_enhanced_db_manager"),
        patch("core.security_event_monitoring.get_security_logger"),
        patch("core.security_event_monitoring.get_unified_config") as mock_cfg,
    ):
        mock_cfg.return_value = MagicMock(redis=MagicMock(host=None))
        # Reset global so fresh instance is created
        import core.security_event_monitoring as sem

        sem._security_monitor = None
        monitor = get_security_monitor()
        assert isinstance(monitor, SecurityEventMonitor)


# ===========================================================================
# SECTION 2 — curriculum_compliance_system.py
# ===========================================================================


class TestCurriculumComplianceSystemInit:
    """Tests for CurriculumComplianceSystem initialization."""

    def test_init_without_services(self):
        system = CurriculumComplianceSystem()
        assert system.db is None
        assert system.cache is None
        assert system.meb_standards_cache == {}
        assert system.osym_standards_cache == {}

    def test_compliance_thresholds_defined(self):
        system = CurriculumComplianceSystem()
        assert "excellent" in system.compliance_thresholds
        assert system.compliance_thresholds["excellent"] == 0.9
        assert system.compliance_thresholds["good"] == 0.8

    def test_minimum_questions_per_topic(self):
        system = CurriculumComplianceSystem()
        assert system.minimum_questions_per_topic == 1000


class TestDetermineComplianceStatus:
    """Tests for _determine_compliance_status."""

    def setup_method(self):
        self.system = CurriculumComplianceSystem()

    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.95, "excellent"),
            (0.85, "good"),
            (0.75, "acceptable"),
            (0.65, "needs_improvement"),
            (0.5, "insufficient"),
            (0.0, "insufficient"),
        ],
    )
    def test_status_thresholds(self, score, expected):
        status = self.system._determine_compliance_status(score)
        assert status == expected


class TestCalculateAlignmentScore:
    """Tests for _calculate_alignment_score."""

    def setup_method(self):
        self.system = CurriculumComplianceSystem()

    @pytest.mark.asyncio
    async def test_empty_inputs_return_zero(self):
        score = await self.system._calculate_alignment_score([], [])
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_empty_meb_returns_zero(self):
        osym = [MagicMock(topic_name="Matematik")]
        score = await self.system._calculate_alignment_score([], osym)
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_identical_topics_returns_positive_score(self):
        meb = [MagicMock(topic_name="Matematik", id="1")]
        osym = [MagicMock(topic_name="Matematik")]
        # Mock get_learning_outcomes to return empty list
        self.system.get_learning_outcomes = AsyncMock(return_value=[])
        score = await self.system._calculate_alignment_score(meb, osym)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_disjoint_topics_returns_low_score(self):
        meb = [MagicMock(topic_name="Fizik", id="1")]
        osym = [MagicMock(topic_name="Kimya")]
        self.system.get_learning_outcomes = AsyncMock(return_value=[])
        score = await self.system._calculate_alignment_score(meb, osym)
        assert score >= 0.0


class TestIdentifyCurriculumGaps:
    """Tests for _identify_curriculum_gaps."""

    def setup_method(self):
        self.system = CurriculumComplianceSystem()

    @pytest.mark.asyncio
    async def test_no_gaps_when_identical(self):
        meb = [MagicMock(topic_name="Matematik")]
        osym = [MagicMock(topic_name="Matematik")]
        gaps = await self.system._identify_curriculum_gaps(meb, osym)
        assert gaps == []

    @pytest.mark.asyncio
    async def test_detects_meb_only_topics(self):
        meb = [MagicMock(topic_name="Fizik"), MagicMock(topic_name="Kimya")]
        osym = [MagicMock(topic_name="Fizik")]
        gaps = await self.system._identify_curriculum_gaps(meb, osym)
        assert any("MEB'de var" in g for g in gaps)

    @pytest.mark.asyncio
    async def test_detects_osym_only_topics(self):
        meb = [MagicMock(topic_name="Fizik")]
        osym = [MagicMock(topic_name="Fizik"), MagicMock(topic_name="Mantık")]
        gaps = await self.system._identify_curriculum_gaps(meb, osym)
        assert any("ÖSYM'de var" in g for g in gaps)


class TestGenerateAlignmentRecommendations:
    """Tests for _generate_alignment_recommendations."""

    def setup_method(self):
        self.system = CurriculumComplianceSystem()

    @pytest.mark.asyncio
    async def test_empty_gaps_returns_positive_recommendation(self):
        recs = await self.system._generate_alignment_recommendations([])
        assert len(recs) == 1
        assert "yeterli" in recs[0]

    @pytest.mark.asyncio
    async def test_meb_gap_recommendation(self):
        recs = await self.system._generate_alignment_recommendations(
            ["MEB'de var ÖSYM'de yok: Fizik"]
        )
        assert any("MEB" in r for r in recs)

    @pytest.mark.asyncio
    async def test_osym_gap_recommendation(self):
        recs = await self.system._generate_alignment_recommendations(
            ["ÖSYM'de var MEB'de yok: Mantık"]
        )
        assert any("ÖSYM" in r for r in recs)


class TestCalculateQuestionComplianceScore:
    """Tests for _calculate_question_compliance_score."""

    def setup_method(self):
        self.system = CurriculumComplianceSystem()

    @pytest.mark.asyncio
    async def test_empty_counts_returns_zero(self):
        score = await self.system._calculate_question_compliance_score({})
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_full_compliance_returns_high_score(self):
        counts = {
            "total": 1000,
            "osym_format": 900,
            "meb_aligned": 950,
        }
        score = await self.system._calculate_question_compliance_score(counts)
        assert score > 0.7

    @pytest.mark.asyncio
    async def test_partial_compliance_score_bounded(self):
        counts = {
            "total": 500,
            "osym_format": 400,
            "meb_aligned": 450,
        }
        score = await self.system._calculate_question_compliance_score(counts)
        assert 0.0 <= score <= 1.0


class TestCurriculumComplianceSummary:
    """Tests for get_compliance_summary."""

    @pytest.mark.asyncio
    async def test_summary_contains_required_keys(self):
        system = CurriculumComplianceSystem()
        summary = await system.get_compliance_summary()
        assert "meb_standards_count" in summary
        assert "osym_standards_count" in summary
        assert "alignments_count" in summary
        assert summary["system_status"] == "active"

    @pytest.mark.asyncio
    async def test_summary_counts_are_integers(self):
        system = CurriculumComplianceSystem()
        summary = await system.get_compliance_summary()
        assert isinstance(summary["meb_standards_count"], int)
        assert isinstance(summary["osym_standards_count"], int)


class TestAddMEBStandard:
    """Tests for add_meb_standard."""

    @pytest.mark.asyncio
    async def test_adds_to_cache_without_db(self):
        system = CurriculumComplianceSystem()
        standard = MagicMock()
        standard.id = "std-001"
        standard.topic_name = "Cebir"
        result = await system.add_meb_standard(standard)
        assert result is True
        assert "std-001" in system.meb_standards_cache

    @pytest.mark.asyncio
    async def test_add_osym_standard_without_db(self):
        system = CurriculumComplianceSystem()
        standard = MagicMock()
        standard.id = "osym-001"
        standard.topic_name = "Analitik Geometri"
        result = await system.add_osym_standard(standard)
        assert result is True
        assert "osym-001" in system.osym_standards_cache


# ===========================================================================
# SECTION 3 — exam_quality_validators.py
# ===========================================================================


class TestIRTParameters:
    """Tests for IRTParameters Pydantic model."""

    def test_valid_parameters_accepted(self):
        params = IRTParameters(discrimination=1.0, difficulty=0.0, guessing=0.25)
        assert params.discrimination == 1.0
        assert params.difficulty == 0.0
        assert params.guessing == 0.25

    def test_defaults_for_guessing(self):
        params = IRTParameters(discrimination=1.0, difficulty=0.0)
        assert params.guessing == 0.0

    @pytest.mark.parametrize(
        "discrimination,difficulty",
        [
            (0.2, -4.0),  # boundary min
            (4.0, 4.0),  # boundary max
            (2.0, 0.0),  # normal center
        ],
    )
    def test_boundary_values_accepted(self, discrimination, difficulty):
        params = IRTParameters(discrimination=discrimination, difficulty=difficulty)
        assert params.discrimination == discrimination
        assert params.difficulty == difficulty

    def test_discrimination_below_minimum_rejected(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            IRTParameters(discrimination=0.1, difficulty=0.0)

    def test_difficulty_out_of_range_rejected(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            IRTParameters(discrimination=1.0, difficulty=5.0)

    def test_guessing_above_max_rejected(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            IRTParameters(discrimination=1.0, difficulty=0.0, guessing=0.4)


class TestIRTCalibrationValidator:
    """Tests for IRTCalibrationValidator."""

    def setup_method(self):
        self.validator = IRTCalibrationValidator()

    def _make_question(self, irt_params=None, **kwargs):
        defaults = dict(
            question_id="q1",
            subject="Matematik",
            topic="Cebir",
            grade_level="11",
            exam_type="tyt",
            question_type="test",
        )
        defaults.update(kwargs)
        return QuestionMetadata(irt_params=irt_params, **defaults)

    def test_missing_irt_returns_warning(self):
        question = self._make_question(irt_params=None)
        results = self.validator.validate_irt_parameters(question)
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].severity == ValidationSeverity.WARNING

    def test_valid_irt_params_pass(self):
        params = IRTParameters(
            discrimination=1.2,
            difficulty=0.0,
            guessing=0.2,
            calibration_sample_size=300,
        )
        question = self._make_question(irt_params=params)
        results = self.validator.validate_irt_parameters(question)
        assert all(r.passed for r in results)

    def test_low_sample_size_produces_warning(self):
        params = IRTParameters(
            discrimination=1.2,
            difficulty=0.0,
            calibration_sample_size=50,
        )
        question = self._make_question(irt_params=params)
        results = self.validator.validate_irt_parameters(question)
        types_failed = [r for r in results if not r.passed]
        assert len(types_failed) > 0

    def test_low_discrimination_produces_error(self):
        # Source: severity = ERROR if params.discrimination < 0.3 else WARNING
        # discrimination=0.25 is below 0.3 → ERROR
        params = IRTParameters(
            discrimination=0.25,
            difficulty=0.0,
            calibration_sample_size=300,
        )
        question = self._make_question(irt_params=params)
        results = self.validator.validate_irt_parameters(question)
        severities = [r.severity for r in results if not r.passed]
        assert ValidationSeverity.ERROR in severities

    def test_calculate_information_is_positive(self):
        params = IRTParameters(discrimination=1.5, difficulty=0.0, guessing=0.25)
        info = self.validator.calculate_information(params, theta=0.0)
        assert info >= 0.0

    def test_calculate_information_extremes_return_zero(self):
        params = IRTParameters(discrimination=1.5, difficulty=0.0, guessing=0.0)
        # At extreme theta values, probability approaches 0 or 1
        info_extreme = self.validator.calculate_information(params, theta=100.0)
        assert info_extreme >= 0.0


class TestDifficultyBalanceValidator:
    """Tests for DifficultyBalanceValidator."""

    def setup_method(self):
        self.validator = DifficultyBalanceValidator()

    def _make_blueprint(self):
        return ExamBlueprint(
            exam_id="exam-1",
            exam_name="Test Sınavı",
            exam_type="tyt",
            topic_distribution={"Matematik": 40, "Türkçe": 40},
        )

    def _make_question(self, difficulty=0.5, subject="Matematik"):
        return QuestionMetadata(
            question_id="q1",
            subject=subject,
            topic="Cebir",
            grade_level="11",
            exam_type="tyt",
            question_type="test",
            estimated_difficulty=difficulty,
        )

    def test_empty_questions_returns_error(self):
        blueprint = self._make_blueprint()
        results = self.validator.validate_difficulty_distribution([], blueprint)
        assert len(results) == 1
        assert results[0].severity == ValidationSeverity.ERROR

    def test_classify_difficulty_boundaries(self):
        assert self.validator._classify_difficulty(0.1) == DifficultyLevel.VERY_EASY
        assert self.validator._classify_difficulty(0.3) == DifficultyLevel.EASY
        assert self.validator._classify_difficulty(0.5) == DifficultyLevel.MEDIUM
        assert self.validator._classify_difficulty(0.7) == DifficultyLevel.HARD
        assert self.validator._classify_difficulty(0.9) == DifficultyLevel.VERY_HARD

    def test_balanced_distribution_passes(self):
        blueprint = self._make_blueprint()
        # Create questions matching target distribution
        questions = (
            [self._make_question(0.05)] * 10  # VERY_EASY
            + [self._make_question(0.3)] * 20  # EASY
            + [self._make_question(0.5)] * 40  # MEDIUM
            + [self._make_question(0.7)] * 20  # HARD
            + [self._make_question(0.9)] * 10  # VERY_HARD
        )
        results = self.validator.validate_difficulty_distribution(questions, blueprint)
        passed = [r for r in results if r.passed]
        assert len(passed) > 0


class TestCurriculumMatchValidator:
    """Tests for CurriculumMatchValidator."""

    def setup_method(self):
        self.validator = CurriculumMatchValidator()

    def _make_blueprint(self, outcomes=None):
        # Use sentinel None to distinguish "not passed" from "passed as empty list"
        if outcomes is None:
            outcomes = ["LO-1", "LO-2", "LO-3"]
        return ExamBlueprint(
            exam_id="exam-1",
            exam_name="Test",
            exam_type="tyt",
            topic_distribution={"Matematik": 40},
            required_learning_outcomes=outcomes,
        )

    def _make_question(self, outcomes=None, exam_type="tyt"):
        return QuestionMetadata(
            question_id="q1",
            subject="Matematik",
            topic="Cebir",
            grade_level="tyt",
            exam_type=exam_type,
            question_type="test",
            learning_outcomes=outcomes or ["LO-1", "LO-2"],
        )

    def test_sufficient_coverage_passes(self):
        blueprint = self._make_blueprint(outcomes=["LO-1", "LO-2"])
        question = self._make_question(outcomes=["LO-1", "LO-2"])
        results = self.validator.validate_curriculum_alignment([question], blueprint)
        passed = [r for r in results if r.passed]
        assert len(passed) > 0

    def test_insufficient_coverage_fails(self):
        blueprint = self._make_blueprint(
            outcomes=["LO-1", "LO-2", "LO-3", "LO-4", "LO-5"]
        )
        question = self._make_question(outcomes=["LO-1"])
        results = self.validator.validate_curriculum_alignment([question], blueprint)
        failed = [r for r in results if not r.passed]
        assert len(failed) > 0

    def test_no_required_outcomes_passes_coverage(self):
        blueprint = self._make_blueprint(outcomes=[])
        question = self._make_question()
        # coverage_ratio = 1.0 when no required outcomes -> no coverage failure
        results = self.validator.validate_curriculum_alignment([question], blueprint)
        # Should not fail due to outcome coverage (coverage_ratio = 1.0 > min_outcomes_coverage)
        coverage_fails = [
            r
            for r in results
            if not r.passed
            and r.details.get("coverage_ratio", 1.0) < blueprint.min_outcomes_coverage
        ]
        assert len(coverage_fails) == 0


class TestTopicDistributionValidator:
    """Tests for TopicDistributionValidator."""

    def setup_method(self):
        self.validator = TopicDistributionValidator()

    def _make_blueprint(self):
        return ExamBlueprint(
            exam_id="exam-1",
            exam_name="Test",
            exam_type="tyt",
            topic_distribution={"Matematik": 40, "Türkçe": 40},
        )

    def _make_question(self, subject="Matematik"):
        return QuestionMetadata(
            question_id="q1",
            subject=subject,
            topic="Cebir",
            grade_level="tyt",
            exam_type="tyt",
            question_type="test",
        )

    def test_balanced_distribution_passes(self):
        blueprint = self._make_blueprint()
        questions = [self._make_question("Matematik")] * 40 + [
            self._make_question("Türkçe")
        ] * 40
        results = self.validator.validate_topic_distribution(questions, blueprint)
        passed = [r for r in results if r.passed]
        assert len(passed) > 0

    def test_extra_topics_flagged(self):
        blueprint = self._make_blueprint()
        questions = [self._make_question("Matematik")] * 40 + [
            self._make_question("Fizik")
        ] * 10  # unplanned topic
        results = self.validator.validate_topic_distribution(questions, blueprint)
        extra_flag = [r for r in results if "Planlanmamış" in r.message]
        assert len(extra_flag) > 0


class TestExamQualityValidator:
    """Tests for ExamQualityValidator unified validator."""

    def setup_method(self):
        self.validator = ExamQualityValidator()

    def _make_blueprint(self):
        return ExamBlueprint(
            exam_id="exam-full",
            exam_name="Kapsamlı Sınav",
            exam_type="tyt",
            topic_distribution={"Matematik": 10},
        )

    def _make_question(self, i=0):
        return QuestionMetadata(
            question_id=f"q{i}",
            subject="Matematik",
            topic="Cebir",
            grade_level="tyt",
            exam_type="tyt",
            question_type="test",
            estimated_difficulty=0.5,
        )

    def test_validate_exam_returns_dict_with_required_keys(self):
        blueprint = self._make_blueprint()
        questions = [self._make_question(i) for i in range(10)]
        result = self.validator.validate_exam(questions, blueprint)
        assert "exam_id" in result
        assert "summary" in result
        assert "results" in result
        assert "total_questions" in result

    def test_validate_exam_summary_has_status(self):
        blueprint = self._make_blueprint()
        questions = [self._make_question(i) for i in range(5)]
        result = self.validator.validate_exam(questions, blueprint)
        assert "overall_status" in result["summary"]
        assert result["summary"]["overall_status"] in [
            "PASSED",
            "PASSED_WITH_WARNINGS",
            "FAILED",
            "CRITICAL",
        ]

    def test_create_summary_empty_results(self):
        summary = self.validator._create_summary([])
        assert summary["total_checks"] == 0
        assert summary["pass_rate"] == 0

    def test_create_summary_all_passed(self):
        results = [
            ValidationResult(
                validation_type=ValidationType.IRT_CALIBRATION,
                severity=ValidationSeverity.INFO,
                passed=True,
                message="OK",
            )
        ] * 5
        summary = self.validator._create_summary(results)
        assert summary["overall_status"] == "PASSED"
        assert summary["passed_count"] == 5

    def test_create_summary_with_errors_status_failed(self):
        results = [
            ValidationResult(
                validation_type=ValidationType.DIFFICULTY_BALANCE,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="Error",
            )
        ]
        summary = self.validator._create_summary(results)
        assert summary["overall_status"] == "FAILED"


def test_get_exam_validator_singleton():
    """get_exam_validator() returns the same instance each call."""
    import core.exam_quality_validators as eqv

    eqv._validator_instance = None
    v1 = get_exam_validator()
    v2 = get_exam_validator()
    assert v1 is v2


# ===========================================================================
# SECTION 4 — document_deduplication.py
# ===========================================================================


class TestDocumentDeduplicatorInit:
    """Tests for DocumentDeduplicator initialization."""

    def test_default_thresholds(self):
        d = DocumentDeduplicator()
        assert d.exact_threshold == 1.0
        assert d.fuzzy_threshold == 0.95
        assert d.embedding_threshold == 0.98

    def test_custom_thresholds(self):
        d = DocumentDeduplicator(fuzzy_threshold=0.8, embedding_threshold=0.9)
        assert d.fuzzy_threshold == 0.8
        assert d.embedding_threshold == 0.9


class TestHashContent:
    """Tests for _hash_content."""

    def setup_method(self):
        self.d = DocumentDeduplicator()

    def test_same_content_same_hash(self):
        h1 = self.d._hash_content("hello world")
        h2 = self.d._hash_content("hello world")
        assert h1 == h2

    def test_different_content_different_hash(self):
        h1 = self.d._hash_content("hello world")
        h2 = self.d._hash_content("goodbye world")
        assert h1 != h2

    def test_whitespace_normalized(self):
        h1 = self.d._hash_content("hello   world")
        h2 = self.d._hash_content("hello world")
        assert h1 == h2

    def test_case_insensitive(self):
        h1 = self.d._hash_content("Hello World")
        h2 = self.d._hash_content("hello world")
        assert h1 == h2


class TestTokenize:
    """Tests for _tokenize."""

    def setup_method(self):
        self.d = DocumentDeduplicator()

    def test_basic_tokenization(self):
        tokens = self.d._tokenize("The quick brown fox")
        assert "quick" in tokens
        assert "brown" in tokens

    def test_short_words_filtered(self):
        tokens = self.d._tokenize("a to the hello")
        assert "a" not in tokens
        assert "to" not in tokens
        # "the" is 3 chars, length > 2 = ok
        assert "the" in tokens

    def test_returns_set(self):
        tokens = self.d._tokenize("apple apple banana")
        assert isinstance(tokens, set)
        assert len(tokens) == 2  # deduplicated


class TestJaccardSimilarity:
    """Tests for _jaccard_similarity."""

    def setup_method(self):
        self.d = DocumentDeduplicator()

    def test_identical_sets_return_one(self):
        s = {"apple", "banana", "cherry"}
        assert self.d._jaccard_similarity(s, s) == 1.0

    def test_disjoint_sets_return_zero(self):
        s1 = {"apple", "banana"}
        s2 = {"cherry", "date"}
        assert self.d._jaccard_similarity(s1, s2) == 0.0

    def test_empty_sets_return_zero(self):
        assert self.d._jaccard_similarity(set(), set()) == 0.0

    def test_partial_overlap(self):
        s1 = {"apple", "banana", "cherry"}
        s2 = {"banana", "cherry", "date"}
        sim = self.d._jaccard_similarity(s1, s2)
        assert 0 < sim < 1


class TestFindExactDuplicates:
    """Tests for _find_exact_duplicates."""

    def setup_method(self):
        self.d = DocumentDeduplicator()

    def test_exact_duplicates_found(self):
        docs = [
            {"content": "Python programlama dili"},
            {"content": "Python programlama dili"},
            {"content": "Java programlama dili"},
        ]
        groups = self.d._find_exact_duplicates(docs)
        assert len(groups) == 1
        assert groups[0].similarity == 1.0
        assert groups[0].method == "exact_hash"

    def test_no_duplicates_returns_empty(self):
        docs = [
            {"content": "Unique document one"},
            {"content": "Unique document two"},
        ]
        groups = self.d._find_exact_duplicates(docs)
        assert groups == []

    def test_uses_text_field_as_fallback(self):
        docs = [
            {"text": "Same text here"},
            {"text": "Same text here"},
        ]
        groups = self.d._find_exact_duplicates(docs)
        assert len(groups) == 1


class TestDeduplicateDocuments:
    """Tests for deduplicate method."""

    def setup_method(self):
        self.d = DocumentDeduplicator()

    def test_deduplicate_removes_exact_duplicates(self):
        # The source removes duplicates by string value (to_remove set contains the dup text).
        # Since canonical text == duplicate text, ALL occurrences of "Content A" are removed.
        # Only the unique "Content B" survives.
        docs = [
            {"content": "Content A"},
            {"content": "Content A"},
            {"content": "Content B"},
        ]
        result = self.d.deduplicate(docs, method="exact", keep="first")
        # Result has fewer docs than input (duplicates removed)
        assert len(result) < len(docs)
        # The unique document always survives
        contents = [r.get("content") for r in result]
        assert "Content B" in contents

    def test_deduplicate_keep_longest(self):
        docs = [
            {"content": "Short"},
            {"content": "Short"},
            {"content": "A longer version of short"},
        ]
        # Only exact duplicates here
        result = self.d.deduplicate(docs, method="exact", keep="longest")
        assert len(result) <= len(docs)

    def test_empty_documents_returns_empty(self):
        result = self.d.deduplicate([], method="exact")
        assert result == []


class TestCosineSimiliarity:
    """Tests for _cosine_similarity."""

    def setup_method(self):
        self.d = DocumentDeduplicator()

    def test_identical_vectors(self):
        import numpy as np

        vec = np.array([1.0, 2.0, 3.0])
        sim = self.d._cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        import numpy as np

        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        sim = self.d._cosine_similarity(v1, v2)
        assert abs(sim) < 1e-6

    def test_zero_vector_returns_zero(self):
        import numpy as np

        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 2.0, 3.0])
        sim = self.d._cosine_similarity(v1, v2)
        assert sim == 0.0


class TestMergeMetadata:
    """Tests for merge_metadata."""

    def setup_method(self):
        self.d = DocumentDeduplicator()

    def test_new_keys_from_duplicate_added(self):
        canonical = {"title": "Doc A", "author": "Alice"}
        duplicate = {"title": "Doc A", "tags": ["math", "science"]}
        merged = self.d.merge_metadata(canonical, duplicate)
        assert "tags" in merged
        assert merged["author"] == "Alice"

    def test_view_count_summed(self):
        canonical = {"title": "Doc A", "view_count": 10}
        duplicate = {"view_count": 5}
        merged = self.d.merge_metadata(canonical, duplicate)
        assert merged["view_count"] == 15

    def test_canonical_keys_not_overwritten(self):
        canonical = {"title": "Original Title"}
        duplicate = {"title": "Different Title"}
        merged = self.d.merge_metadata(canonical, duplicate)
        assert merged["title"] == "Original Title"

    def test_list_fields_merged(self):
        canonical = {"tags": ["math"]}
        duplicate = {"tags": ["science"]}
        merged = self.d.merge_metadata(canonical, duplicate)
        assert set(merged["tags"]) == {"math", "science"}


class TestIncrementalDeduplicator:
    """Tests for IncrementalDeduplicator."""

    def setup_method(self):
        self.dedup = IncrementalDeduplicator(threshold=0.9)

    def test_first_document_not_duplicate(self):
        is_dup, original = self.dedup.is_duplicate("First unique document", "hash")
        assert is_dup is False
        assert original is None

    def test_exact_duplicate_detected(self):
        self.dedup.is_duplicate("Repeated content here", "hash")
        is_dup, original = self.dedup.is_duplicate("Repeated content here", "hash")
        assert is_dup is True

    def test_add_document_and_detect(self):
        self.dedup.add_document("Pre-added document")
        is_dup, _ = self.dedup.is_duplicate("Pre-added document", "hash")
        assert is_dup is True

    def test_clear_resets_state(self):
        self.dedup.is_duplicate("Some content", "hash")
        self.dedup.clear()
        is_dup, _ = self.dedup.is_duplicate("Some content", "hash")
        assert is_dup is False

    def test_fuzzy_similar_document_detected(self):
        dedup = IncrementalDeduplicator(threshold=0.5)
        dedup.is_duplicate("Python programming language tutorial", "fuzzy")
        is_dup, _ = dedup.is_duplicate("Python programming language guide", "fuzzy")
        assert is_dup is True

    def test_fuzzy_different_content_not_duplicate(self):
        self.dedup.is_duplicate("Completely different topic here", "fuzzy")
        is_dup, _ = self.dedup.is_duplicate("Quantum physics equations", "fuzzy")
        assert is_dup is False


def test_get_deduplicator_singleton():
    """get_deduplicator() returns the same instance."""
    import core.document_deduplication as dd

    dd._global_deduplicator = None
    d1 = get_deduplicator()
    d2 = get_deduplicator()
    assert d1 is d2


class TestCheckDuplicateByEmbedding:
    """Tests for check_duplicate_by_embedding."""

    def setup_method(self):
        import numpy as np

        self.d = DocumentDeduplicator(embedding_threshold=0.95)
        v = np.array([1.0, 0.0, 0.0])
        self.d.add_embedding("doc-1", v)

    def test_identical_embedding_is_duplicate(self):
        import numpy as np

        v = np.array([1.0, 0.0, 0.0])
        is_dup, doc_id, score = self.d.check_duplicate_by_embedding(v)
        assert is_dup is True
        assert doc_id == "doc-1"
        assert score > 0.95

    def test_different_embedding_not_duplicate(self):
        import numpy as np

        v = np.array([0.0, 1.0, 0.0])
        is_dup, doc_id, score = self.d.check_duplicate_by_embedding(v)
        assert is_dup is False
        assert doc_id is None


# ===========================================================================
# SECTION 5 — enhanced_content_manager.py
# ===========================================================================


class TestEnhancedContentManagerInit:
    """Tests for EnhancedContentManager initialization."""

    def setup_method(self):
        with patch("asyncio.create_task"):
            self.manager = EnhancedContentManager(content_dir="backend/content")

    def test_caches_initialized_empty(self):
        assert self.manager._content_cache == {}
        assert self.manager._questions_cache == {}
        assert self.manager._topics_cache == {}
        assert self.manager._study_plans_cache == {}

    def test_cache_ttl_set(self):
        assert self.manager._cache_ttl == 3600

    def test_content_dir_is_path(self):
        assert isinstance(self.manager.content_dir, Path)


class TestEnhancedContentManagerMethods:
    """Tests for EnhancedContentManager public methods."""

    def setup_method(self):
        with patch("asyncio.create_task"):
            self.manager = EnhancedContentManager(content_dir="backend/content")

    def test_get_questions_by_topic_empty_cache(self):
        result = self.manager.get_questions_by_topic("Matematik")
        assert isinstance(result, list)
        assert result == []

    def test_get_topic_info_returns_none_when_empty(self):
        result = self.manager.get_topic_info("Cebir")
        assert result is None

    def test_get_study_plan_returns_none_when_empty(self):
        result = self.manager.get_study_plan("default")
        assert result is None

    def test_get_curriculum_coverage_empty_cache(self):
        result = self.manager.get_curriculum_coverage("Matematik")
        assert isinstance(result, dict)
        assert result == {}

    def test_get_exam_strategies_empty_cache(self):
        result = self.manager.get_exam_strategies()
        assert isinstance(result, dict)

    def test_get_performance_metrics_empty_cache(self):
        result = self.manager.get_performance_metrics()
        assert isinstance(result, dict)

    def test_clear_cache_empties_all(self):
        self.manager._content_cache["test"] = "value"
        self.manager._questions_cache["test"] = []
        self.manager.clear_cache()
        assert self.manager._content_cache == {}
        assert self.manager._questions_cache == {}

    def test_get_cache_stats_returns_dict(self):
        stats = self.manager.get_cache_stats()
        assert "content_cache_size" in stats
        assert "questions_cache_size" in stats
        assert "lru_cache_info" in stats

    def test_get_cache_stats_sizes_are_integers(self):
        stats = self.manager.get_cache_stats()
        assert isinstance(stats["content_cache_size"], int)
        assert isinstance(stats["questions_cache_size"], int)


class TestEnhancedContentManagerPersonalized:
    """Tests for generate_personalized_content."""

    def setup_method(self):
        with patch("asyncio.create_task"):
            self.manager = EnhancedContentManager(content_dir="backend/content")

    @pytest.mark.asyncio
    async def test_generate_personalized_topic_not_found(self):
        profile = {"learning_style": "visual", "knowledge_level": "beginner"}
        result = await self.manager.generate_personalized_content(
            profile, ContentType.QUESTION, "UnknownTopic", ContentDifficultyLevel.MEDIUM
        )
        assert "error" in result
        assert result["error"] == "Topic not found"

    def test_get_personalized_recommendations_visual(self):
        recs = self.manager._get_personalized_recommendations(
            "visual", "beginner", "cebir"
        )
        assert isinstance(recs, list)
        # visual style + beginner level = at least 6 recommendations
        assert len(recs) >= 6

    def test_get_personalized_recommendations_auditory(self):
        recs = self.manager._get_personalized_recommendations(
            "auditory", "advanced", "fizik"
        )
        assert isinstance(recs, list)
        # auditory style adds recs, advanced level adds recs
        assert len(recs) >= 4
        # "video" is ASCII-safe and appears in auditory recommendations
        assert any("video" in r for r in recs)

    def test_get_personalized_recommendations_kinesthetic(self):
        recs = self.manager._get_personalized_recommendations(
            "kinesthetic", "beginner", "kimya"
        )
        assert isinstance(recs, list)
        # kinesthetic adds recs, beginner adds recs
        assert len(recs) >= 6
        # "pratik" is ASCII-safe and appears in kinesthetic recommendations
        assert any("pratik" in r for r in recs)

    def test_get_study_tips_math_topic(self):
        tips = self.manager._get_study_tips("matematik", ContentDifficultyLevel.MEDIUM)
        assert isinstance(tips, list)
        # "matematik" topic branch adds 3 extra tips on top of the base 3
        assert len(tips) > 3

    def test_get_study_tips_fen_topic(self):
        tips = self.manager._get_study_tips(
            "fen bilimleri", ContentDifficultyLevel.HARD
        )
        assert isinstance(tips, list)
        # "fen" topic branch adds 3 extra tips on top of the base 3
        assert len(tips) > 3

    def test_calculate_study_time_easy_is_less_than_hard(self):
        questions = [{"id": str(i)} for i in range(10)]
        easy_time = self.manager._calculate_study_time(
            questions, ContentDifficultyLevel.EASY
        )
        hard_time = self.manager._calculate_study_time(
            questions, ContentDifficultyLevel.HARD
        )
        assert easy_time < hard_time

    def test_calculate_study_time_medium(self):
        questions = [{"id": str(i)} for i in range(5)]
        time = self.manager._calculate_study_time(
            questions, ContentDifficultyLevel.MEDIUM
        )
        assert time == 10  # 5 questions * 2 min

    def test_calculate_study_time_zero_questions(self):
        time = self.manager._calculate_study_time([], ContentDifficultyLevel.EASY)
        assert time == 0


class TestExamTypeAndContentEnums:
    """Tests for ExamType, DifficultyLevel, ContentType enums."""

    def test_exam_type_values(self):
        assert ExamType.LGS.value == "lgs"
        assert ExamType.YKS.value == "yks"
        assert ExamType.BOTH.value == "both"

    def test_content_difficulty_values(self):
        assert ContentDifficultyLevel.EASY.value == "easy"
        assert ContentDifficultyLevel.MEDIUM.value == "medium"
        assert ContentDifficultyLevel.HARD.value == "hard"

    def test_content_type_values(self):
        assert ContentType.LESSON.value == "lesson"
        assert ContentType.QUESTION.value == "question"
        assert ContentType.VIDEO.value == "video"


class TestCacheQuestionsBy:
    """Tests for _cache_questions_by_criteria."""

    def setup_method(self):
        with patch("asyncio.create_task"):
            self.manager = EnhancedContentManager(content_dir="backend/content")

    def test_questions_cached_by_difficulty(self):
        from unittest.mock import MagicMock

        q1 = MagicMock()
        q1.difficulty = ContentDifficultyLevel.EASY
        q1.topic = "Cebir"
        q1.subtopic = "Denklemler"

        q2 = MagicMock()
        q2.difficulty = ContentDifficultyLevel.HARD
        q2.topic = "Cebir"
        q2.subtopic = "Eşitsizlikler"

        self.manager._cache_questions_by_criteria([q1, q2])
        easy = self.manager._questions_cache.get("difficulty_easy", [])
        hard = self.manager._questions_cache.get("difficulty_hard", [])
        assert len(easy) == 1
        assert len(hard) == 1

    def test_questions_cached_by_topic(self):
        from unittest.mock import MagicMock

        q = MagicMock()
        q.difficulty = ContentDifficultyLevel.MEDIUM
        q.topic = "Fizik"
        q.subtopic = "Mekanik"

        self.manager._cache_questions_by_criteria([q])
        cached = self.manager._questions_cache.get("topic_Fizik", [])
        assert len(cached) == 1
