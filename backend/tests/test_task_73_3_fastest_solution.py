"""
Test Task 73.3: En Hızlı Çözüm Önerisi
- Solution time estimation
- Efficiency ranking
- Shortcut identification
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from services.alternative_solutions_service import AlternativeSolutionsService


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def service(mock_db_session):
    """Alternative Solutions Service instance"""
    return AlternativeSolutionsService(mock_db_session)


@pytest.fixture
def sample_solutions():
    """Sample solutions for testing"""
    return [
        {
            "id": "sol-1",
            "title": "Formül ile Hızlı Çözüm",
            "category": "formül",
            "difficulty": "kolay",
            "estimated_time_seconds": 30,
            "steps": [
                {"step_number": 1, "description": "Formülü uygula"},
                {"step_number": 2, "description": "Sonucu hesapla"},
            ],
            "advantages": ["Çok hızlı", "Kolay"],
            "disadvantages": ["Formül bilgisi gerekli"],
            "tips": ["Formülü ezberle"],
            "prerequisites": ["Temel formül bilgisi"],
            "votes": {"upvotes": 15, "downvotes": 2, "total": 13},
            "usage_count": 50,
            "video_url": "https://example.com/video1",
        },
        {
            "id": "sol-2",
            "title": "Klasik Yöntem",
            "category": "klasik",
            "difficulty": "orta",
            "estimated_time_seconds": 120,
            "steps": [
                {"step_number": 1, "description": "Verileri analiz et"},
                {"step_number": 2, "description": "Denklem kur"},
                {"step_number": 3, "description": "Denklemi çöz"},
                {"step_number": 4, "description": "Sonucu kontrol et"},
                {"step_number": 5, "description": "Cevabı yaz"},
            ],
            "advantages": ["Detaylı", "Anlaşılır"],
            "disadvantages": ["Uzun sürer"],
            "tips": ["Adım adım ilerle"],
            "prerequisites": ["Temel matematik"],
            "votes": {"upvotes": 8, "downvotes": 1, "total": 7},
            "usage_count": 30,
            "video_url": None,
        },
        {
            "id": "sol-3",
            "title": "Mantıksal Kısayol",
            "category": "mantıksal",
            "difficulty": "zor",
            "estimated_time_seconds": 60,
            "steps": [
                {"step_number": 1, "description": "Mantıksal ilişkiyi gör"},
                {"step_number": 2, "description": "Kısayolu uygula"},
                {"step_number": 3, "description": "Sonuca ulaş"},
            ],
            "advantages": ["Hızlı", "Zekice"],
            "disadvantages": ["Zor anlaşılır"],
            "tips": ["Mantık yürüt"],
            "prerequisites": ["İleri mantık", "Problem çözme"],
            "votes": {"upvotes": 10, "downvotes": 3, "total": 7},
            "usage_count": 20,
            "video_url": "https://example.com/video3",
        },
    ]


class TestTask73_3_FastestSolution:
    """Task 73.3: En Hızlı Çözüm Önerisi Tests"""

    @pytest.mark.asyncio
    async def test_solution_time_estimation(self, service, sample_solutions):
        """Test 73.3.1: Solution time estimation"""
        # Test time estimation method
        estimations = service._estimate_solution_times(sample_solutions)

        # Verify all solutions have estimations
        assert len(estimations) == 3
        assert "sol-1" in estimations
        assert "sol-2" in estimations
        assert "sol-3" in estimations

        # Verify estimation structure
        sol1_est = estimations["sol-1"]
        assert "minimum_time_seconds" in sol1_est
        assert "average_time_seconds" in sol1_est
        assert "maximum_time_seconds" in sol1_est
        assert "confidence_level" in sol1_est
        assert "time_per_step" in sol1_est
        assert "step_breakdown" in sol1_est
        assert "factors" in sol1_est

        # Verify time ranges (min < avg < max)
        assert sol1_est["minimum_time_seconds"] < sol1_est["average_time_seconds"]
        assert sol1_est["average_time_seconds"] < sol1_est["maximum_time_seconds"]

        # Verify step breakdown
        assert len(sol1_est["step_breakdown"]) == 2  # sol-1 has 2 steps
        assert sol1_est["step_breakdown"][0]["step_number"] == 1

    @pytest.mark.asyncio
    async def test_efficiency_ranking(self, service, sample_solutions):
        """Test 73.3.2: Efficiency ranking"""
        # Get time estimations first
        time_estimations = service._estimate_solution_times(sample_solutions)

        # Test efficiency ranking
        ranking = service._rank_by_efficiency(sample_solutions, time_estimations)

        # Verify ranking structure
        assert len(ranking) == 3
        assert all("solution_id" in sol for sol in ranking)
        assert all("efficiency_score" in sol for sol in ranking)
        assert all("rank" in sol for sol in ranking)
        assert all("score_breakdown" in sol for sol in ranking)
        assert all("metrics" in sol for sol in ranking)
        assert all("efficiency_rating" in sol for sol in ranking)

        # Verify ranking order (rank 1 should have highest score)
        assert ranking[0]["rank"] == 1
        assert ranking[1]["rank"] == 2
        assert ranking[2]["rank"] == 3
        assert ranking[0]["efficiency_score"] >= ranking[1]["efficiency_score"]
        assert ranking[1]["efficiency_score"] >= ranking[2]["efficiency_score"]

        # Verify score breakdown components
        breakdown = ranking[0]["score_breakdown"]
        assert "time_score" in breakdown
        assert "step_score" in breakdown
        assert "difficulty_score" in breakdown
        assert "popularity_score" in breakdown

        # Verify efficiency rating
        assert ranking[0]["efficiency_rating"] in [
            "Mükemmel",
            "Çok İyi",
            "İyi",
            "Orta",
            "Düşük",
        ]

    @pytest.mark.asyncio
    async def test_shortcut_identification(self, service, sample_solutions):
        """Test 73.3.3: Shortcut identification"""
        # Test shortcut identification
        shortcuts = service._identify_shortcuts(sample_solutions)

        # Verify shortcuts structure
        assert "total_shortcuts_found" in shortcuts
        assert "by_type" in shortcuts
        assert "fastest_shortcut" in shortcuts
        assert "easiest_shortcut" in shortcuts
        assert "recommendations" in shortcuts

        # Verify shortcut types
        assert "formül" in shortcuts["by_type"]
        assert "mantıksal" in shortcuts["by_type"]
        assert "görsel" in shortcuts["by_type"]
        assert "hesaplama" in shortcuts["by_type"]

        # Verify shortcuts were found
        assert shortcuts["total_shortcuts_found"] > 0

        # Verify formül shortcut (sol-1 is formül category)
        assert len(shortcuts["by_type"]["formül"]) > 0
        formul_shortcut = shortcuts["by_type"]["formül"][0]
        assert formul_shortcut["solution_id"] == "sol-1"
        assert formul_shortcut["type"] == "formül"
        assert "time_saved_seconds" in formul_shortcut
        assert "steps_skipped" in formul_shortcut

        # Verify mantıksal shortcut (sol-3 is mantıksal category)
        assert len(shortcuts["by_type"]["mantıksal"]) > 0
        mantiksal_shortcut = shortcuts["by_type"]["mantıksal"][0]
        assert mantiksal_shortcut["solution_id"] == "sol-3"
        assert mantiksal_shortcut["type"] == "mantıksal"

        # Verify fastest shortcut
        if shortcuts["fastest_shortcut"]:
            assert "solution_id" in shortcuts["fastest_shortcut"]
            assert "time_saved_seconds" in shortcuts["fastest_shortcut"]

        # Verify recommendations
        assert isinstance(shortcuts["recommendations"], list)
        assert len(shortcuts["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_get_fastest_solution_integration(
        self, service, sample_solutions, mock_db_session
    ):
        """Test full get_fastest_solution method integration"""
        # Mock get_solutions to return sample solutions
        service.get_solutions = AsyncMock(return_value=sample_solutions)

        # Call get_fastest_solution
        result = await service.get_fastest_solution("test-question-id")

        # Verify result structure
        assert result is not None
        assert "question_id" in result
        assert "fastest_solution" in result
        assert "time_estimation" in result
        assert "efficiency_ranking" in result
        assert "shortcuts" in result
        assert "comparison_with_others" in result
        assert "recommendation" in result

        # Verify fastest solution (sol-1 with 30 seconds)
        fastest = result["fastest_solution"]
        assert fastest["id"] == "sol-1"
        assert fastest["estimated_time_seconds"] == 30
        assert fastest["category"] == "formül"

        # Verify time estimation
        time_est = result["time_estimation"]
        assert "minimum_time_seconds" in time_est
        assert "average_time_seconds" in time_est
        assert "maximum_time_seconds" in time_est

        # Verify efficiency ranking
        ranking = result["efficiency_ranking"]
        assert len(ranking) == 3
        assert ranking[0]["rank"] == 1

        # Verify shortcuts
        shortcuts = result["shortcuts"]
        assert shortcuts["total_shortcuts_found"] > 0

        # Verify comparison
        comparison = result["comparison_with_others"]
        assert "total_solutions" in comparison
        assert comparison["total_solutions"] == 3

        # Verify recommendation
        recommendation = result["recommendation"]
        assert "why_fastest" in recommendation
        assert "time_saved" in recommendation
        assert "best_for" in recommendation
        assert "prerequisites" in recommendation

    def test_helper_methods(self, service, sample_solutions):
        """Test helper methods"""
        # Test _calculate_confidence_level
        confidence = service._calculate_confidence_level(sample_solutions[0])
        assert confidence in ["yüksek", "orta", "düşük"]

        # Test _get_efficiency_rating
        rating = service._get_efficiency_rating(85.0)
        assert rating == "Mükemmel"
        rating = service._get_efficiency_rating(65.0)
        assert rating == "Çok İyi"
        rating = service._get_efficiency_rating(45.0)
        assert rating == "İyi"

        # Test _estimate_time_saved
        time_saved = service._estimate_time_saved(sample_solutions[0], sample_solutions)
        assert time_saved >= 0

        # Test _estimate_steps_skipped
        steps_skipped = service._estimate_steps_skipped(
            sample_solutions[0], sample_solutions
        )
        assert steps_skipped >= 0

        # Test _compare_with_other_solutions
        comparison = service._compare_with_other_solutions(
            sample_solutions[0], sample_solutions
        )
        assert "total_solutions" in comparison
        assert "time_advantage_seconds" in comparison
        assert "percentile" in comparison

        # Test _explain_why_fastest
        explanation = service._explain_why_fastest(
            sample_solutions[0], sample_solutions
        )
        assert isinstance(explanation, str)
        assert len(explanation) > 0

        # Test _calculate_time_saved
        time_saved_detail = service._calculate_time_saved(
            sample_solutions[0], sample_solutions
        )
        assert "vs_average_seconds" in time_saved_detail
        assert "vs_slowest_seconds" in time_saved_detail
        assert "percentage_saved" in time_saved_detail

        # Test _determine_best_use_case
        use_cases = service._determine_best_use_case(sample_solutions[0])
        assert isinstance(use_cases, list)
        assert len(use_cases) > 0

        # Test _generate_difficulty_warning
        warning = service._generate_difficulty_warning(
            sample_solutions[2]
        )  # zor difficulty
        assert warning is None or isinstance(warning, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
