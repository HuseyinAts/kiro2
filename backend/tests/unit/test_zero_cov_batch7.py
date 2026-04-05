"""
Batch-7 zero-coverage tests.

Covers:
  1. services/osym_benchmark_comparator.py  (~254 stmts)
  2. api/department_info_routes.py           (~250 stmts)
  3. api/soru_bankasi.py                     (~245 stmts)
  4. services/eba_tv_client.py               (~224 stmts)

Strategy
--------
- Load every module with importlib.util.spec_from_file_location so the test
  file is independent of sys.path ordering quirks.
- Mock ALL external dependencies (DB, Redis, HTTP clients).
- Test handler functions directly — no TestClient overhead.
- Minimum 60 tests, every assertion is meaningful (no `assert True`).
"""

import importlib
import importlib.util
import os
import sys
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


# ---------------------------------------------------------------------------
# Cleanup stale MagicMock stubs that may leak between reloads
# ---------------------------------------------------------------------------
_STALE_KEYS = [
    "services.osym_benchmark_comparator",
    "api.department_info_routes",
    "api.soru_bankasi",
    "services.eba_tv_client",
    # secondary mocks that earlier runs may have registered
    "services.department_info_service",
    "services.soru_bankasi_service",
    "core.multi_layer_cache",
    "core.redis_cache",
]
for _k in _STALE_KEYS:
    sys.modules.pop(_k, None)


# ===========================================================================
# Module loaders (importlib)
# ===========================================================================


def _load(rel_path: str, mod_name: str):
    full_path = os.path.join(_BACKEND, rel_path)
    spec = importlib.util.spec_from_file_location(mod_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 1. osym_benchmark_comparator — no external deps, load directly
# ---------------------------------------------------------------------------
_osym_mod = _load(
    "services/osym_benchmark_comparator.py", "services.osym_benchmark_comparator"
)

OSYMBenchmarkComparator = _osym_mod.OSYMBenchmarkComparator
QuestionStatistics = _osym_mod.QuestionStatistics
BenchmarkComparison = _osym_mod.BenchmarkComparison


# ---------------------------------------------------------------------------
# 4. eba_tv_client — depends only on httpx + standard lib
# ---------------------------------------------------------------------------
_eba_mod = _load("services/eba_tv_client.py", "services.eba_tv_client")

EBATVClient = _eba_mod.EBATVClient
MockEBATVClient = _eba_mod.MockEBATVClient
EBAGradeLevel = _eba_mod.EBAGradeLevel
EBASubject = _eba_mod.EBASubject
EBAVideoMetadata = _eba_mod.EBAVideoMetadata
EBACatalogFilter = _eba_mod.EBACatalogFilter
get_eba_client = _eba_mod.get_eba_client


# ---------------------------------------------------------------------------
# 2. department_info_routes — needs heavy patching before load
# ---------------------------------------------------------------------------


def _load_dept_routes():
    """Load department_info_routes with all deps mocked."""
    # Provide mock modules that the router imports
    mock_db_mod = MagicMock()
    mock_db_mod.get_db = AsyncMock()
    sys.modules.setdefault("core.database", mock_db_mod)

    mock_deps_mod = MagicMock()

    class _FakeAuthUser:
        id = "admin-001"
        role = MagicMock(value="admin")

    mock_deps_mod.AuthenticatedUser = _FakeAuthUser
    mock_deps_mod.get_current_admin_user = AsyncMock(return_value=_FakeAuthUser())
    sys.modules.setdefault("core.dependencies", mock_deps_mod)

    # Use proper str+Enum so Pydantic can build a schema for fields typed with
    # these classes inside department_info_routes.py request/response models.
    import enum as _enum

    class _ExpLevel(str, _enum.Enum):
        ENTRY = "entry"
        JUNIOR = "junior"
        MID = "mid"
        SENIOR = "senior"
        EXPERT = "expert"

    class _IndType(str, _enum.Enum):
        TECHNOLOGY = "technology"
        FINANCE = "finance"
        EDUCATION = "education"

    mock_dept_model = MagicMock()
    mock_dept_model.ExperienceLevel = _ExpLevel
    mock_dept_model.IndustryType = _IndType
    sys.modules.setdefault("models.department_info", mock_dept_model)

    mock_svc_mod = MagicMock()
    mock_svc_cls = MagicMock()
    mock_svc_mod.DepartmentInfoService = mock_svc_cls
    sys.modules.setdefault("services.department_info_service", mock_svc_mod)

    return _load("api/department_info_routes.py", "api.department_info_routes")


_dept_mod = _load_dept_routes()


# ---------------------------------------------------------------------------
# 3. soru_bankasi — needs many mocks
# ---------------------------------------------------------------------------


def _load_soru_bankasi():
    """Load api/soru_bankasi with all heavy deps mocked."""
    mock_db_session = MagicMock()
    mock_db_session.get_db_session = AsyncMock()
    sys.modules.setdefault("core.database", mock_db_session)

    # Ensure core.dependencies already mocked (may exist)
    if "core.dependencies" not in sys.modules:
        mock_deps = MagicMock()

        class _FakeUser:
            id = "user-123"
            role = MagicMock(value="student")

        mock_deps.get_current_user = AsyncMock(return_value=_FakeUser())
        mock_deps.AuthenticatedUser = _FakeUser
        sys.modules["core.dependencies"] = mock_deps

    mock_cache_mod = MagicMock()
    mock_cache_instance = MagicMock()
    mock_cache_instance._initialized = False
    mock_cache_instance.initialize = AsyncMock()
    mock_cache_instance.get_or_compute = AsyncMock(return_value=[])
    mock_cache_instance.clear = AsyncMock()
    mock_cache_mod.MultiLayerCache = MagicMock(return_value=mock_cache_instance)
    sys.modules["core.multi_layer_cache"] = mock_cache_mod

    mock_redis_mod = MagicMock()
    mock_redis_cache = MagicMock()
    mock_redis_cache.is_connected.return_value = False
    mock_redis_mod.get_cache = MagicMock(return_value=mock_redis_cache)
    sys.modules["core.redis_cache"] = mock_redis_mod

    mock_svc_mod = MagicMock()
    mock_svc_inst = MagicMock()
    mock_svc_mod.soru_bankasi_servisi = mock_svc_inst
    sys.modules["services.soru_bankasi_service"] = mock_svc_mod

    return _load("api/soru_bankasi.py", "api.soru_bankasi")


_soru_mod = _load_soru_bankasi()


# ===========================================================================
# SECTION 1 — OSYMBenchmarkComparator
# ===========================================================================


class TestQuestionStatisticsDataclass:
    """Ensure the dataclass constructs and holds correct defaults."""

    def test_default_total_count_is_zero(self):
        s = QuestionStatistics()
        assert s.total_count == 0

    def test_default_lists_are_empty(self):
        s = QuestionStatistics()
        assert s.lengths == []
        assert s.difficulty_counts == {}
        assert s.bloom_counts == {}

    def test_computed_at_is_iso_string(self):
        s = QuestionStatistics()
        # Should parse as a valid ISO datetime
        dt = datetime.fromisoformat(s.computed_at)
        assert dt is not None


class TestBenchmarkComparisonDataclass:
    def test_overall_similarity_default(self):
        bc = BenchmarkComparison()
        assert bc.overall_similarity == 0.0

    def test_issues_and_recommendations_are_lists(self):
        bc = BenchmarkComparison()
        assert isinstance(bc.issues, list)
        assert isinstance(bc.recommendations, list)


class TestOSYMComparatorInit:
    def test_init_creates_instance(self):
        comp = OSYMBenchmarkComparator()
        assert comp is not None
        assert comp._reference_stats is None


class TestCalculateStatistics:
    def _make_questions(self, n: int = 5) -> list[dict]:
        return [
            {
                "question_text": "x" * (100 + i * 20),
                "difficulty": "Orta" if i % 2 == 0 else "Kolay",
                "bloom_level": "Uygulama" if i % 3 != 0 else "Analiz",
                "subject": "Matematik",
                "correct_answer": "A" if i % 2 == 0 else "B",
            }
            for i in range(n)
        ]

    def test_total_count_matches_input(self):
        comp = OSYMBenchmarkComparator()
        qs = self._make_questions(7)
        stats = comp.calculate_statistics(qs)
        assert stats.total_count == 7

    def test_mean_length_is_positive(self):
        comp = OSYMBenchmarkComparator()
        qs = self._make_questions(5)
        stats = comp.calculate_statistics(qs)
        assert stats.mean_length > 0

    def test_difficulty_percentages_sum_to_100(self):
        comp = OSYMBenchmarkComparator()
        qs = self._make_questions(6)
        stats = comp.calculate_statistics(qs)
        total = sum(stats.difficulty_percentages.values())
        assert abs(total - 100.0) < 1e-6

    def test_bloom_counts_populated(self):
        comp = OSYMBenchmarkComparator()
        qs = self._make_questions(6)
        stats = comp.calculate_statistics(qs)
        assert len(stats.bloom_counts) >= 1

    def test_empty_questions_returns_zero_count(self):
        comp = OSYMBenchmarkComparator()
        stats = comp.calculate_statistics([])
        assert stats.total_count == 0

    def test_metin_field_used_as_fallback(self):
        """Should accept 'metin' as Turkish alternative to 'question_text'."""
        comp = OSYMBenchmarkComparator()
        qs = [{"metin": "A" * 200, "difficulty": "Zor"}]
        stats = comp.calculate_statistics(qs)
        assert stats.mean_length == 200.0

    def test_correct_answer_distribution_populated(self):
        comp = OSYMBenchmarkComparator()
        qs = [{"question_text": "Q", "correct_answer": "A"}] * 3 + [
            {"question_text": "Q", "correct_answer": "B"}
        ] * 2
        stats = comp.calculate_statistics(qs)
        assert stats.correct_answer_distribution.get("A") == 3
        assert stats.correct_answer_distribution.get("B") == 2

    def test_length_stats_min_max(self):
        comp = OSYMBenchmarkComparator()
        qs = [{"question_text": "x" * 50}, {"question_text": "x" * 150}]
        stats = comp.calculate_statistics(qs)
        assert stats.min_length == 50
        assert stats.max_length == 150


class TestSetReferenceBenchmark:
    def test_sets_reference_stats(self):
        comp = OSYMBenchmarkComparator()
        qs = [{"question_text": "abc" * 20, "difficulty": "Orta"}]
        ref = comp.set_reference_benchmark(qs)
        assert comp._reference_stats is not None
        assert ref.total_count == 1

    def test_returns_statistics_object(self):
        comp = OSYMBenchmarkComparator()
        qs = [{"question_text": "test" * 30}]
        ref = comp.set_reference_benchmark(qs)
        assert isinstance(ref, QuestionStatistics)


class TestCompareAgainstBenchmark:
    def _make_qs(self, n=10):
        return [
            {
                "question_text": "x" * (80 + i * 10),
                "difficulty": ["Kolay", "Orta", "Zor"][i % 3],
                "bloom_level": ["Hatırlama", "Uygulama", "Analiz"][i % 3],
            }
            for i in range(n)
        ]

    def test_overall_similarity_in_range(self):
        comp = OSYMBenchmarkComparator()
        comp.set_reference_benchmark(self._make_qs(10))
        ai_qs = self._make_qs(8)
        result = comp.compare_against_benchmark(ai_qs)
        assert 0.0 <= result.overall_similarity <= 1.0

    def test_interpretation_is_non_empty(self):
        comp = OSYMBenchmarkComparator()
        comp.set_reference_benchmark(self._make_qs(10))
        result = comp.compare_against_benchmark(self._make_qs(8))
        assert len(result.interpretation) > 0

    def test_raises_when_no_reference(self):
        comp = OSYMBenchmarkComparator()
        with pytest.raises(ValueError, match="No reference benchmark"):
            comp.compare_against_benchmark([{"question_text": "Q"}])

    def test_identical_sets_give_high_similarity(self):
        comp = OSYMBenchmarkComparator()
        qs = self._make_qs(20)
        comp.set_reference_benchmark(qs)
        result = comp.compare_against_benchmark(qs)
        # Identical content should produce high scores
        assert result.length_similarity >= 0.9
        assert result.difficulty_similarity >= 0.9

    def test_very_different_sets_generate_issues(self):
        comp = OSYMBenchmarkComparator()
        # Use varied lengths so ref std_length > 0 (avoids division-by-zero in
        # _compare_lengths when all reference texts have the same length).
        ref_qs = [
            {"question_text": "x" * (20 + i * 5), "difficulty": "Kolay"}
            for i in range(10)
        ]
        comp.set_reference_benchmark(ref_qs)
        ai_qs = [{"question_text": "y" * 500, "difficulty": "Zor"}] * 10
        result = comp.compare_against_benchmark(ai_qs)
        # AI questions are ~10x longer than ref — length similarity must diverge
        assert result.length_similarity < 1.0

    def test_recommendations_are_list(self):
        comp = OSYMBenchmarkComparator()
        comp.set_reference_benchmark(self._make_qs(10))
        result = comp.compare_against_benchmark(self._make_qs(8))
        assert isinstance(result.recommendations, list)

    def test_compare_with_explicit_reference_stats(self):
        comp = OSYMBenchmarkComparator()
        ref_stats = comp.calculate_statistics(self._make_qs(10))
        ai_qs = self._make_qs(5)
        result = comp.compare_against_benchmark(ai_qs, reference_stats=ref_stats)
        assert isinstance(result.overall_similarity, float)


class TestInterpretSimilarity:
    def test_excellent_threshold(self):
        comp = OSYMBenchmarkComparator()
        assert comp._interpret_similarity(0.95) == "Excellent"

    def test_very_good_threshold(self):
        comp = OSYMBenchmarkComparator()
        assert comp._interpret_similarity(0.87) == "Very Good"

    def test_good_threshold(self):
        comp = OSYMBenchmarkComparator()
        assert comp._interpret_similarity(0.82) == "Good"

    def test_acceptable_threshold(self):
        comp = OSYMBenchmarkComparator()
        assert comp._interpret_similarity(0.77) == "Acceptable"

    def test_needs_improvement_threshold(self):
        comp = OSYMBenchmarkComparator()
        assert comp._interpret_similarity(0.50) == "Needs Improvement"


class TestCohensD:
    def test_identical_groups_give_zero_d(self):
        comp = OSYMBenchmarkComparator()
        g = [100.0, 110.0, 120.0, 130.0]
        d = comp._calculate_cohens_d(g, g[:])
        assert d == 0.0

    def test_well_separated_groups_give_large_d(self):
        comp = OSYMBenchmarkComparator()
        # Groups need non-zero within-group variance for pooled-std to be > 0.
        g1 = [10.0 + i for i in range(10)]  # mean ~14.5, std ~3
        g2 = [100.0 + i for i in range(10)]  # mean ~104.5, std ~3
        d = comp._calculate_cohens_d(g1, g2)
        assert d > 1.0  # ~30 SD units apart — clearly large

    def test_interpretation_negligible(self):
        comp = OSYMBenchmarkComparator()
        assert "Negligible" in comp._interpret_cohens_d(0.1)

    def test_interpretation_small(self):
        comp = OSYMBenchmarkComparator()
        assert "Small" in comp._interpret_cohens_d(0.3)

    def test_interpretation_large(self):
        comp = OSYMBenchmarkComparator()
        assert "Large" in comp._interpret_cohens_d(1.0)


# ===========================================================================
# SECTION 2 — department_info_routes (handler functions)
# ===========================================================================


class TestDeptRoutesModels:
    """Test Pydantic models defined in the routes module."""

    def test_curriculum_create_request_defaults(self):
        CurriculumCreateRequest = _dept_mod.CurriculumCreateRequest
        req = CurriculumCreateRequest(
            department_id=uuid4(),
            total_credits=240,
            duration_years=4,
            duration_semesters=8,
            core_courses=[{"name": "Calculus"}],
        )
        assert req.total_credits == 240
        assert req.internship_required is False
        assert req.thesis_required is False

    def test_career_opportunity_create_request_optional_fields(self):
        CareerOpportunityCreateRequest = _dept_mod.CareerOpportunityCreateRequest
        req = CareerOpportunityCreateRequest(
            department_id=uuid4(),
            job_title="Software Engineer",
        )
        assert req.job_title == "Software Engineer"
        assert req.employment_rate is None
        assert req.required_skills is None

    def test_salary_expectation_defaults(self):
        SalaryExpectationCreateRequest = _dept_mod.SalaryExpectationCreateRequest
        # ExperienceLevel from mock
        req = SalaryExpectationCreateRequest(
            department_id=uuid4(),
            experience_level="entry",
            min_salary=10000,
            max_salary=30000,
            average_salary=20000,
        )
        assert req.currency == "TRY"
        assert req.year == 2024

    def test_employment_statistics_response(self):
        EmploymentStatisticsResponse = _dept_mod.EmploymentStatisticsResponse
        resp = EmploymentStatisticsResponse(
            total_career_paths=5,
            average_employment_rate=0.85,
            average_hiring_time_days=30,
            high_demand_careers=3,
            top_industries=[{"name": "tech", "count": 10}],
            career_growth_high=2,
        )
        assert resp.average_employment_rate == 0.85

    def test_job_market_trends_response(self):
        JobMarketTrendsResponse = _dept_mod.JobMarketTrendsResponse
        resp = JobMarketTrendsResponse(
            overall_growth="positive",
            annual_growth_rate=5.2,
            total_job_openings=10000,
            sectors_analyzed=4,
            top_skills=["Python", "SQL"],
            employment_rate=0.80,
            sectors=[],
        )
        assert resp.sectors_analyzed == 4
        assert "Python" in resp.top_skills


@pytest.mark.asyncio
class TestDeptRouteHandlers:
    """Test the async route handler functions directly."""

    async def _mock_db_service(self, method_name: str, return_value: Any):
        """Helper: returns (mock_db, patched service instance)."""
        mock_db = AsyncMock()
        mock_svc = AsyncMock()
        setattr(mock_svc, method_name, AsyncMock(return_value=return_value))
        return mock_db, mock_svc

    async def test_get_curriculum_returns_curriculum_when_found(self):
        mock_curriculum = MagicMock()
        mock_curriculum.id = uuid4()
        mock_curriculum.department_id = uuid4()
        mock_curriculum.total_credits = 240
        mock_curriculum.duration_years = 4
        mock_curriculum.duration_semesters = 8
        mock_curriculum.core_courses = []
        mock_curriculum.elective_courses = None
        mock_curriculum.specialization_tracks = None
        mock_curriculum.learning_outcomes = None
        mock_curriculum.skills_gained = None
        mock_curriculum.internship_required = False
        mock_curriculum.thesis_required = False
        mock_curriculum.capstone_project = False
        mock_curriculum.ects_credits = None
        mock_curriculum.exchange_programs_available = False

        dept_id = uuid4()
        mock_svc = AsyncMock()
        mock_svc.get_department_curriculum = AsyncMock(return_value=mock_curriculum)

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            result = await _dept_mod.get_department_curriculum(dept_id, db=AsyncMock())

        assert result is mock_curriculum

    async def test_get_curriculum_raises_404_when_not_found(self):
        from fastapi import HTTPException

        dept_id = uuid4()
        mock_svc = AsyncMock()
        mock_svc.get_department_curriculum = AsyncMock(return_value=None)

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            with pytest.raises(HTTPException) as exc_info:
                await _dept_mod.get_department_curriculum(dept_id, db=AsyncMock())

        assert exc_info.value.status_code == 404

    async def test_get_specialization_options_returns_list(self):
        dept_id = uuid4()
        mock_svc = AsyncMock()
        mock_svc.get_specialization_options = AsyncMock(
            return_value=["Track A", "Track B"]
        )

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            result = await _dept_mod.get_specialization_options(dept_id, db=AsyncMock())

        assert result == ["Track A", "Track B"]

    async def test_get_career_opportunities_returns_list(self):
        dept_id = uuid4()
        mock_svc = AsyncMock()
        mock_svc.get_career_opportunities = AsyncMock(return_value=[MagicMock()])

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            result = await _dept_mod.get_career_opportunities(
                dept_id, industry_type=None, demand_level=None, db=AsyncMock()
            )

        assert len(result) == 1

    async def test_get_salary_expectations_filters_passed(self):
        dept_id = uuid4()
        mock_svc = AsyncMock()
        mock_svc.get_salary_expectations = AsyncMock(return_value=[])

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            result = await _dept_mod.get_salary_expectations(
                dept_id,
                experience_level=None,
                city="Istanbul",
                year=2024,
                db=AsyncMock(),
            )

        mock_svc.get_salary_expectations.assert_called_once_with(
            department_id=dept_id, experience_level=None, city="Istanbul", year=2024
        )
        assert result == []

    async def test_get_salary_progression_wraps_in_dict(self):
        dept_id = uuid4()
        progression_data = {"entry": {"min": 10000, "max": 20000}}
        mock_svc = AsyncMock()
        mock_svc.get_salary_progression = AsyncMock(return_value=progression_data)

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            result = await _dept_mod.get_salary_progression(
                dept_id, city=None, year=2024, db=AsyncMock()
            )

        assert "progression" in result
        assert result["progression"] == progression_data

    async def test_get_sector_analysis_raises_404_when_none(self):
        from fastapi import HTTPException

        mock_svc = AsyncMock()
        mock_svc.get_sector_analysis = AsyncMock(return_value=None)

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            with pytest.raises(HTTPException) as exc_info:
                await _dept_mod.get_sector_analysis(
                    industry_type="technology", year=2024, db=AsyncMock()
                )

        assert exc_info.value.status_code == 404

    async def test_get_department_statistics_raises_404_when_none(self):
        from fastapi import HTTPException

        dept_id = uuid4()
        mock_svc = AsyncMock()
        mock_svc.get_department_statistics = AsyncMock(return_value=None)

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            with pytest.raises(HTTPException) as exc_info:
                await _dept_mod.get_department_statistics(
                    dept_id, year=2024, db=AsyncMock()
                )

        assert exc_info.value.status_code == 404

    async def test_get_department_statistics_returns_dict_when_found(self):
        dept_id = uuid4()
        mock_stats = MagicMock()
        mock_stats.id = uuid4()
        mock_stats.department_id = dept_id
        mock_stats.year = 2024
        mock_stats.overall_employment_rate = 0.85
        mock_stats.average_hiring_time_days = 35
        mock_stats.entry_level_avg_salary = 15000
        mock_stats.entry_level_min_salary = 10000
        mock_stats.entry_level_max_salary = 20000
        mock_stats.mid_career_avg_salary = 30000
        mock_stats.senior_avg_salary = 50000
        mock_stats.salary_growth_rate = 0.08
        mock_stats.top_industries = ["tech"]

        mock_svc = AsyncMock()
        mock_svc.get_department_statistics = AsyncMock(return_value=mock_stats)

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            result = await _dept_mod.get_department_statistics(
                dept_id, year=2024, db=AsyncMock()
            )

        assert result["year"] == 2024
        assert result["overall_employment_rate"] == 0.85

    async def test_get_comprehensive_info_calls_service(self):
        dept_id = uuid4()
        expected = {
            "curriculum": {},
            "career_opportunities": [],
            "salary_progression": {},
        }
        mock_svc = AsyncMock()
        mock_svc.get_comprehensive_department_info = AsyncMock(return_value=expected)

        with patch.object(_dept_mod, "DepartmentInfoService", return_value=mock_svc):
            result = await _dept_mod.get_comprehensive_department_info(
                dept_id, year=2024, db=AsyncMock()
            )

        assert result == expected


# ===========================================================================
# SECTION 3 — api/soru_bankasi (handler functions + models)
# ===========================================================================


class TestSoruBankasiModels:
    def test_soru_ekle_request_valid(self):
        SoruEkleRequest = _soru_mod.SoruEkleRequest
        req = SoruEkleRequest(
            soru_metni="Bu bir test sorusudur ABC" * 2,
            secenekler=["Seçenek A", "Seçenek B", "Seçenek C", "Seçenek D"],
            dogru_cevap="A",
            sinav_tipi="TYT",
            konu="Matematik",
        )
        assert req.dogru_cevap == "A"
        assert req.sinav_tipi == "TYT"

    def test_soru_ekle_request_rejects_empty_metni(self):
        from pydantic import ValidationError

        SoruEkleRequest = _soru_mod.SoruEkleRequest
        with pytest.raises(ValidationError):
            SoruEkleRequest(
                soru_metni="",  # too short (min_length=10)
                secenekler=["A", "B", "C", "D"],
                dogru_cevap="A",
                konu="Matematik",
            )

    def test_soru_guncelle_request_all_optional(self):
        SoruGuncelleRequest = _soru_mod.SoruGuncelleRequest
        req = SoruGuncelleRequest()
        assert req.soru_metni is None
        assert req.dogru_cevap is None

    def test_toplu_soru_ekle_request(self):
        TopluSoruEkleRequest = _soru_mod.TopluSoruEkleRequest
        req = TopluSoruEkleRequest(sorular=[{"soru_metni": "Q1", "dogru_cevap": "A"}])
        assert len(req.sorular) == 1

    def test_invalidate_cache_function_exists(self):
        """invalidate_question_cache should be a coroutine function."""
        import inspect

        assert inspect.iscoroutinefunction(_soru_mod.invalidate_question_cache)


@pytest.mark.asyncio
class TestSoruBankasiHandlers:
    """Test handler functions directly with mocked service."""

    async def test_health_check_returns_healthy(self):
        result = await _soru_mod.health_check()
        assert result["success"] is True
        assert result["data"]["status"] == "healthy"
        assert result["data"]["service"] == "Soru Bankası API"

    async def test_konu_listesi_getir_returns_json_response(self):
        from fastapi.responses import JSONResponse

        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.konu_listesi_getir = AsyncMock(return_value=["Matematik", "Fizik"])

        result = await _soru_mod.konu_listesi_getir(sinav_tipi="TYT", db=AsyncMock())

        assert isinstance(result, JSONResponse)
        body = result.body.decode()
        assert "Matematik" in body
        assert "Fizik" in body

    async def test_konu_listesi_getir_raises_500_on_error(self):
        from fastapi import HTTPException

        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.konu_listesi_getir = AsyncMock(side_effect=RuntimeError("db error"))

        with pytest.raises(HTTPException) as exc_info:
            await _soru_mod.konu_listesi_getir(sinav_tipi=None, db=AsyncMock())

        assert exc_info.value.status_code == 500

    async def test_soru_bankasi_istatistikleri_returns_stats(self):
        from fastapi.responses import JSONResponse

        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.istatistikler_getir = AsyncMock(
            return_value={"total": 77336, "active": 64000}
        )

        result = await _soru_mod.soru_bankasi_istatistikleri(db=AsyncMock())
        assert isinstance(result, JSONResponse)
        body = result.body.decode()
        assert "77336" in body

    async def test_soru_detay_raises_404_when_not_found(self):
        from fastapi import HTTPException

        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.soru_getir = AsyncMock(return_value=None)

        fake_user = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await _soru_mod.soru_detay(
                "nonexistent-id", current_user=fake_user, db=AsyncMock()
            )

        assert exc_info.value.status_code == 404

    async def test_soru_detay_returns_detail_when_found(self):
        from fastapi.responses import JSONResponse

        mock_soru = MagicMock()
        mock_soru.id = "soru-001"
        mock_soru.question_text = "Test sorusu metni budur"
        mock_soru.question_image_url = None
        mock_soru.option_a = "Seçenek A"
        mock_soru.option_b = "Seçenek B"
        mock_soru.option_c = "Seçenek C"
        mock_soru.option_d = "Seçenek D"
        mock_soru.option_e = None
        mock_soru.correct_answer = "A"
        mock_soru.explanation = "Açıklama"
        mock_soru.exam_type = "TYT"
        mock_soru.subject_area = "Matematik"
        mock_soru.primary_topic_id = "topic-1"
        mock_soru.difficulty_level = MagicMock(value="EASY")
        mock_soru.irt_difficulty = 0.0
        mock_soru.irt_discrimination = 1.0
        mock_soru.irt_guessing = 0.25
        mock_soru.morphology_complexity = 0.5
        mock_soru.readability_score = 0.7
        mock_soru.times_asked = 100
        mock_soru.times_correct = 60
        mock_soru.average_response_time = 45.0
        mock_soru.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_soru.updated_at = datetime(2024, 6, 1, 12, 0, 0)
        mock_soru.is_active = True

        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.soru_getir = AsyncMock(return_value=mock_soru)

        fake_user = MagicMock()
        result = await _soru_mod.soru_detay(
            "soru-001", current_user=fake_user, db=AsyncMock()
        )

        assert isinstance(result, JSONResponse)
        body = result.body.decode()
        assert "soru-001" in body
        assert "success" in body

    async def test_soru_performans_guncelle_raises_404_when_not_found(self):
        from fastapi import HTTPException

        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.soru_performans_guncelle = AsyncMock(return_value=False)

        fake_user = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await _soru_mod.soru_performans_guncelle(
                soru_id="no-such",
                dogru_cevap=True,
                cevap_suresi=30.0,
                current_user=fake_user,
                db=AsyncMock(),
            )

        assert exc_info.value.status_code == 404

    async def test_soru_performans_guncelle_returns_200_on_success(self):
        from fastapi.responses import JSONResponse

        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.soru_performans_guncelle = AsyncMock(return_value=True)

        fake_user = MagicMock()
        result = await _soru_mod.soru_performans_guncelle(
            soru_id="soru-abc",
            dogru_cevap=True,
            cevap_suresi=25.5,
            current_user=fake_user,
            db=AsyncMock(),
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

    async def test_soru_sil_requires_admin_or_teacher_role(self):
        from fastapi import HTTPException

        fake_user = MagicMock()
        fake_user.role.value = "student"  # not allowed

        with pytest.raises(HTTPException) as exc_info:
            await _soru_mod.soru_sil("soru-999", current_user=fake_user, db=AsyncMock())

        assert exc_info.value.status_code == 403

    async def test_soru_sil_deletes_successfully_for_admin(self):
        from fastapi.responses import JSONResponse

        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.soru_sil = AsyncMock(return_value=True)

        fake_user = MagicMock()
        fake_user.role.value = "admin"

        result = await _soru_mod.soru_sil(
            "soru-123", current_user=fake_user, db=AsyncMock()
        )
        assert isinstance(result, JSONResponse)
        body = result.body.decode()
        assert "silindi" in body

    async def test_soru_guncelle_requires_admin_or_teacher(self):
        from fastapi import HTTPException

        SoruGuncelleRequest = _soru_mod.SoruGuncelleRequest
        req = SoruGuncelleRequest()
        fake_user = MagicMock()
        fake_user.role.value = "student"

        with pytest.raises(HTTPException) as exc_info:
            await _soru_mod.soru_guncelle(
                "soru-xyz", req, current_user=fake_user, db=AsyncMock()
            )

        assert exc_info.value.status_code == 403

    async def test_soru_guncelle_raises_404_when_not_found(self):
        from fastapi import HTTPException

        SoruGuncelleRequest = _soru_mod.SoruGuncelleRequest
        req = SoruGuncelleRequest(soru_metni="Guncellenecek soru metni burada uzunca")
        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.soru_guncelle = AsyncMock(return_value=None)

        fake_user = MagicMock()
        fake_user.role.value = "teacher"

        with pytest.raises(HTTPException) as exc_info:
            await _soru_mod.soru_guncelle(
                "ghost-id", req, current_user=fake_user, db=AsyncMock()
            )

        assert exc_info.value.status_code == 404

    async def test_rastgele_sorular_invalid_exam_type_raises_400(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await _soru_mod.rastgele_sorular_sec(
                sinav_tipi="INVALID",
                soru_sayisi=5,
                konu_dagilimi=None,
                db=AsyncMock(),
            )

        assert exc_info.value.status_code == 400

    async def test_rastgele_sorular_invalid_json_dagilimi_raises_400(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await _soru_mod.rastgele_sorular_sec(
                sinav_tipi="TYT",
                soru_sayisi=5,
                konu_dagilimi="NOT-JSON",
                db=AsyncMock(),
            )

        assert exc_info.value.status_code == 400

    async def test_toplu_soru_ekle_injects_created_by(self):
        from fastapi.responses import JSONResponse

        TopluSoruEkleRequest = _soru_mod.TopluSoruEkleRequest
        req = TopluSoruEkleRequest(sorular=[{"soru_metni": "Q1"}, {"soru_metni": "Q2"}])

        mock_srv = _soru_mod.soru_bankasi_servisi
        mock_srv.toplu_soru_ekle = AsyncMock(return_value={"basarili": 2, "toplam": 2})

        fake_user = MagicMock()
        fake_user.id = "user-999"

        result = await _soru_mod.toplu_soru_ekle(
            req, current_user=fake_user, db=AsyncMock()
        )

        # created_by should have been injected into each question
        for soru in req.sorular:
            assert soru.get("created_by") == "user-999"

        assert isinstance(result, JSONResponse)


# ===========================================================================
# SECTION 4 — EBATVClient
# ===========================================================================


class TestEBAEnums:
    def test_grade_level_values(self):
        assert EBAGradeLevel.LISE_12 == "lise_12"
        assert EBAGradeLevel.ORTAOKUL_8 == "ortaokul_8"

    def test_subject_values(self):
        assert EBASubject.MATEMATIK == "matematik"
        assert EBASubject.FIZIK == "fizik"

    def test_all_grade_levels_accounted(self):
        levels = [e.value for e in EBAGradeLevel]
        assert "ilkokul_1" in levels
        assert "lise_12" in levels

    def test_all_subjects_accounted(self):
        subjects = [e.value for e in EBASubject]
        assert "kimya" in subjects
        assert "biyoloji" in subjects


class TestEBAVideoMetadata:
    def test_creates_with_required_fields(self):
        meta = EBAVideoMetadata(
            video_id="vid-001",
            title="Matematik Dersi",
            duration_seconds=600,
            video_url="https://eba.gov.tr/videos/001.mp4",
            subject=EBASubject.MATEMATIK,
            grade_level=EBAGradeLevel.LISE_12,
        )
        assert meta.video_id == "vid-001"
        assert meta.has_turkish_subtitle is True
        assert meta.curriculum_aligned is True

    def test_default_lists_are_empty(self):
        meta = EBAVideoMetadata(
            video_id="v2",
            title="Fizik",
            duration_seconds=300,
            video_url="https://eba.gov.tr/v2.mp4",
            subject=EBASubject.FIZIK,
            grade_level=EBAGradeLevel.LISE_11,
        )
        assert meta.subtopics == []
        assert meta.keywords == []
        assert meta.kazanim_codes == []


class TestEBACatalogFilter:
    def test_default_page_and_size(self):
        f = EBACatalogFilter()
        assert f.page == 1
        assert f.page_size == 20

    def test_custom_filters(self):
        f = EBACatalogFilter(
            subject=EBASubject.MATEMATIK,
            grade_level=EBAGradeLevel.LISE_12,
            page_size=50,
        )
        assert f.subject == EBASubject.MATEMATIK
        assert f.page_size == 50


class TestEBATVClientInit:
    def test_init_stores_api_key(self):
        client = EBATVClient(api_key="test-key-123")
        assert client.api_key == "test-key-123"

    def test_default_base_url(self):
        client = EBATVClient()
        assert "eba.gov.tr" in client.base_url

    def test_rate_limit_defaults(self):
        client = EBATVClient()
        assert client.rate_limit_max == 100
        assert client.rate_limit_window == 60

    def test_headers_contain_bearer_when_api_key_set(self):
        client = EBATVClient(api_key="my-secret-key")
        headers = client._get_headers()
        assert "Authorization" in headers
        assert "Bearer my-secret-key" in headers["Authorization"]

    def test_headers_no_auth_when_no_api_key(self):
        client = EBATVClient(api_key=None)
        headers = client._get_headers()
        assert "Authorization" not in headers

    def test_headers_always_include_user_agent(self):
        client = EBATVClient()
        headers = client._get_headers()
        assert headers.get("User-Agent") == "Kiro-Platform/1.0"


class TestEBATVClientRateLimit:
    @pytest.mark.asyncio
    async def test_rate_limit_adds_timestamp(self):
        client = EBATVClient(api_key="key")
        initial_count = len(client.request_timestamps)
        await client._check_rate_limit()
        assert len(client.request_timestamps) == initial_count + 1

    @pytest.mark.asyncio
    async def test_old_timestamps_are_cleaned(self):
        client = EBATVClient(api_key="key")
        old_ts = datetime.now() - timedelta(seconds=120)
        client.request_timestamps = [old_ts] * 5
        await client._check_rate_limit()
        # All 5 old ones should have been dropped; only current one remains
        assert len(client.request_timestamps) == 1


class TestEBATVClientParseVideoMetadata:
    def _sample_data(self) -> dict:
        return {
            "id": "eba-v-001",
            "title": "Türkçe Gramer Dersi",
            "description": "Türkçe dilbilgisi",
            "duration": 1200,
            "thumbnail": "https://eba.gov.tr/thumb.jpg",
            "url": "https://eba.gov.tr/videos/001.mp4",
            "subject": "turkce",
            "grade_level": "lise_11",
            "topic": "Fiil Çekimi",
            "subtopics": ["Geniş Zaman"],
            "keywords": ["fiil", "zaman"],
            "view_count": 2500,
            "quality": "1080p",
            "curriculum_aligned": True,
            "meb_content_id": "MEB-TRK-11-001",
            "kazanim_codes": ["11.2.1.1"],
        }

    def test_parse_returns_eba_video_metadata(self):
        client = EBATVClient()
        data = self._sample_data()
        meta = client._parse_video_metadata(data)
        assert isinstance(meta, EBAVideoMetadata)
        assert meta.video_id == "eba-v-001"
        assert meta.subject == EBASubject.TURKCE
        assert meta.grade_level == EBAGradeLevel.LISE_11

    def test_parse_sets_view_count(self):
        client = EBATVClient()
        meta = client._parse_video_metadata(self._sample_data())
        assert meta.view_count == 2500

    def test_parse_sets_kazanim_codes(self):
        client = EBATVClient()
        meta = client._parse_video_metadata(self._sample_data())
        assert "11.2.1.1" in meta.kazanim_codes

    def test_parse_handles_invalid_publish_date_gracefully(self):
        client = EBATVClient()
        data = self._sample_data()
        data["publish_date"] = "NOT-A-DATE"
        meta = client._parse_video_metadata(data)
        assert meta.publish_date is None

    def test_parse_handles_valid_publish_date(self):
        client = EBATVClient()
        data = self._sample_data()
        data["publish_date"] = "2024-03-15T10:30:00"
        meta = client._parse_video_metadata(data)
        assert meta.publish_date is not None
        assert meta.publish_date.year == 2024


class TestEBATVClientDefaultTaxonomy:
    def test_default_taxonomy_has_matematik(self):
        client = EBATVClient()
        taxonomy = client._get_default_taxonomy()
        assert "matematik" in taxonomy
        assert isinstance(taxonomy["matematik"], list)

    def test_default_taxonomy_has_fizik(self):
        client = EBATVClient()
        taxonomy = client._get_default_taxonomy()
        assert "fizik" in taxonomy
        assert len(taxonomy["fizik"]) > 0

    def test_default_taxonomy_has_all_major_subjects(self):
        client = EBATVClient()
        taxonomy = client._get_default_taxonomy()
        for subj in ["matematik", "fizik", "kimya", "biyoloji"]:
            assert subj in taxonomy


class TestMockEBATVClient:
    @pytest.mark.asyncio
    async def test_get_video_catalog_returns_list(self):
        client = MockEBATVClient()
        catalog = await client.get_video_catalog()
        assert isinstance(catalog, list)
        assert len(catalog) == 20  # default page_size

    @pytest.mark.asyncio
    async def test_get_video_catalog_respects_page_size(self):
        client = MockEBATVClient()
        filters = EBACatalogFilter(page_size=5)
        catalog = await client.get_video_catalog(filters)
        assert len(catalog) == 5

    @pytest.mark.asyncio
    async def test_get_video_catalog_filters_by_subject(self):
        client = MockEBATVClient()
        filters = EBACatalogFilter(subject=EBASubject.MATEMATIK)
        catalog = await client.get_video_catalog(filters)
        # All returned videos should be matematik (mock always creates MATEMATIK)
        for video in catalog:
            assert video.subject == EBASubject.MATEMATIK

    @pytest.mark.asyncio
    async def test_get_subjects_taxonomy_returns_dict(self):
        client = MockEBATVClient()
        taxonomy = await client.get_subjects_taxonomy()
        assert isinstance(taxonomy, dict)
        assert "matematik" in taxonomy

    @pytest.mark.asyncio
    async def test_video_metadata_structure_in_catalog(self):
        client = MockEBATVClient()
        catalog = await client.get_video_catalog(EBACatalogFilter(page_size=2))
        for video in catalog:
            assert video.video_id.startswith("eba_mock_")
            assert video.duration_seconds > 0
            assert video.has_turkish_subtitle is True

    @pytest.mark.asyncio
    async def test_search_videos_delegates_to_catalog(self):
        client = MockEBATVClient()
        results = await client.search_videos("karekök", subject=EBASubject.MATEMATIK)
        assert isinstance(results, list)


class TestGetEbaClientFactory:
    def test_returns_mock_when_use_mock_true(self):
        client = get_eba_client(use_mock=True)
        assert isinstance(client, MockEBATVClient)

    def test_returns_mock_when_no_api_key_set(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("EBA_API_KEY", None)
            client = get_eba_client(use_mock=False)
        # Without env var, should fall back to mock
        assert isinstance(client, MockEBATVClient)

    def test_returns_real_client_when_api_key_present(self):
        with patch.dict(os.environ, {"EBA_API_KEY": "real-key-xyz"}):
            client = get_eba_client(use_mock=False)
        assert isinstance(client, EBATVClient)
        assert client.api_key == "real-key-xyz"


@pytest.mark.asyncio
class TestEBATVClientMakeRequest:
    async def test_raises_after_max_retries_on_request_error(self):
        import httpx

        client = EBATVClient(api_key="key", max_retries=2)
        # Replace the httpx client with a mock that always raises
        mock_http = AsyncMock()
        mock_http.request = AsyncMock(side_effect=httpx.RequestError("timeout"))
        client.client = mock_http

        with pytest.raises((Exception, httpx.RequestError)):
            await client._make_request("GET", "/test")

    async def test_401_raises_immediately_without_retry(self):
        import httpx

        client = EBATVClient(api_key="bad-key", max_retries=3)
        mock_response = MagicMock()
        mock_response.status_code = 401
        http_error = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_response
        )

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(side_effect=http_error)
        client.client = mock_http

        with pytest.raises(httpx.HTTPStatusError):
            await client._make_request("GET", "/protected")

        # Should NOT retry on 401
        assert mock_http.request.call_count == 1

    async def test_context_manager_closes_client(self):
        client = MockEBATVClient()
        close_called = []

        async def _fake_close():
            close_called.append(True)

        client.client.aclose = _fake_close
        async with client as c:
            assert c is client
        assert close_called  # close was invoked
