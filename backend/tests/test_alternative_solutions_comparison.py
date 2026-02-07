"""
Test: Alternatif Çözüm Karşılaştırma (TASK 73.2)

Tests for enhanced solution comparison features:
- Side-by-side comparison
- Step-by-step breakdown
- Time complexity analysis
"""

import pytest
from unittest.mock import AsyncMock, patch

from services.alternative_solutions_service import AlternativeSolutionsService


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    return session


@pytest.fixture
def service(mock_db_session):
    """Alternative solutions service instance"""
    return AlternativeSolutionsService(mock_db_session)


@pytest.fixture
def sample_solutions():
    """Sample solutions for testing"""
    return [
        {
            "id": "sol-1",
            "title": "Klasik Çözüm",
            "category": "klasik",
            "difficulty": "orta",
            "estimated_time_seconds": 180,
            "step_count": 8,
            "steps": [
                {
                    "step_number": 1,
                    "description": "Verileri oku",
                    "formula": None,
                    "explanation": "İlk adım",
                },
                {
                    "step_number": 2,
                    "description": "Formülü uygula",
                    "formula": "x = a + b",
                    "explanation": "Toplama işlemi",
                },
                {
                    "step_number": 3,
                    "description": "Sonucu hesapla",
                    "formula": None,
                    "explanation": None,
                },
                {
                    "step_number": 4,
                    "description": "Eğer x > 0 ise devam et",
                    "formula": None,
                    "explanation": "Koşul kontrolü",
                },
                {
                    "step_number": 5,
                    "description": "Her eleman için işlem yap",
                    "formula": None,
                    "explanation": "Döngü",
                },
                {
                    "step_number": 6,
                    "description": "Sonuçları topla",
                    "formula": None,
                    "explanation": None,
                },
                {
                    "step_number": 7,
                    "description": "Kontrol et",
                    "formula": None,
                    "explanation": None,
                },
                {
                    "step_number": 8,
                    "description": "Cevabı yaz",
                    "formula": None,
                    "explanation": None,
                },
            ],
            "advantages": ["Anlaşılır", "Güvenilir"],
            "disadvantages": ["Yavaş"],
            "votes": {"upvotes": 10, "downvotes": 2, "total": 8},
            "usage_count": 50,
            "prerequisites": ["Temel matematik"],
            "tips": ["Dikkatli ol"],
        },
        {
            "id": "sol-2",
            "title": "Hızlı Çözüm",
            "category": "hızlı",
            "difficulty": "zor",
            "estimated_time_seconds": 60,
            "step_count": 3,
            "steps": [
                {
                    "step_number": 1,
                    "description": "Formülü direkt uygula",
                    "formula": "y = 2x + 1",
                    "explanation": "Kısayol",
                },
                {
                    "step_number": 2,
                    "description": "Sonucu bul",
                    "formula": None,
                    "explanation": None,
                },
                {
                    "step_number": 3,
                    "description": "Cevabı yaz",
                    "formula": None,
                    "explanation": None,
                },
            ],
            "advantages": ["Çok hızlı", "Az adım"],
            "disadvantages": ["Zor anlaşılır", "Formül bilgisi gerekir"],
            "votes": {"upvotes": 15, "downvotes": 5, "total": 10},
            "usage_count": 30,
            "prerequisites": ["İleri matematik", "Formül bilgisi"],
            "tips": ["Formülü ezberle", "Pratik yap"],
        },
        {
            "id": "sol-3",
            "title": "Görsel Çözüm",
            "category": "görsel",
            "difficulty": "kolay",
            "estimated_time_seconds": 120,
            "step_count": 5,
            "steps": [
                {
                    "step_number": 1,
                    "description": "Şekil çiz",
                    "formula": None,
                    "explanation": "Görselleştir",
                },
                {
                    "step_number": 2,
                    "description": "Noktaları işaretle",
                    "formula": None,
                    "explanation": None,
                },
                {
                    "step_number": 3,
                    "description": "Bağlantıları gör",
                    "formula": None,
                    "explanation": None,
                },
                {
                    "step_number": 4,
                    "description": "Sonucu oku",
                    "formula": None,
                    "explanation": None,
                },
                {
                    "step_number": 5,
                    "description": "Cevabı yaz",
                    "formula": None,
                    "explanation": None,
                },
            ],
            "advantages": ["Görsel", "Anlaşılır"],
            "disadvantages": ["Çizim gerekir"],
            "votes": {"upvotes": 12, "downvotes": 3, "total": 9},
            "usage_count": 40,
            "prerequisites": ["Temel geometri"],
            "tips": ["Temiz çiz"],
        },
    ]


# ========================================================================
# TASK 73.2.1: Side-by-side Comparison Tests
# ========================================================================


class TestSideBySideComparison:
    """Side-by-side comparison tests"""

    def test_build_side_by_side_comparison_headers(self, service, sample_solutions):
        """Test: Headers doğru oluşturulmalı"""
        result = service._build_side_by_side_comparison(sample_solutions)

        assert "headers" in result
        assert len(result["headers"]) == 3
        assert result["headers"] == ["Klasik Çözüm", "Hızlı Çözüm", "Görsel Çözüm"]

    def test_build_side_by_side_comparison_metrics(self, service, sample_solutions):
        """Test: Metrikler doğru hesaplanmalı"""
        result = service._build_side_by_side_comparison(sample_solutions)

        assert "metrics" in result
        metrics = result["metrics"]

        # Zorluk seviyeleri
        assert metrics["Zorluk Seviyesi"] == ["orta", "zor", "kolay"]

        # Tahmini süreler
        assert metrics["Tahmini Süre (saniye)"] == [180, 60, 120]

        # Adım sayıları
        assert metrics["Adım Sayısı"] == [8, 3, 5]

        # Kategoriler
        assert metrics["Kategori"] == ["klasik", "hızlı", "görsel"]

    def test_build_side_by_side_comparison_steps(self, service, sample_solutions):
        """Test: Adım karşılaştırması doğru yapılmalı"""
        result = service._build_side_by_side_comparison(sample_solutions)

        assert "steps_comparison" in result
        steps = result["steps_comparison"]

        # En fazla adım sayısı kadar satır olmalı
        assert len(steps) == 8  # Klasik çözümde 8 adım var

        # İlk adım kontrolü
        first_step = steps[0]
        assert first_step["step_number"] == 1
        assert len(first_step["solutions"]) == 3

        # Tüm çözümlerde ilk adım var
        assert first_step["solutions"][0]["description"] == "Verileri oku"
        assert first_step["solutions"][1]["description"] == "Formülü direkt uygula"
        assert first_step["solutions"][2]["description"] == "Şekil çiz"

    def test_build_side_by_side_comparison_missing_steps(
        self, service, sample_solutions
    ):
        """Test: Eksik adımlar '—' ile gösterilmeli"""
        result = service._build_side_by_side_comparison(sample_solutions)

        steps = result["steps_comparison"]

        # 4. adımda hızlı çözümde adım yok (sadece 3 adım var)
        fourth_step = steps[3]
        assert fourth_step["solutions"][1]["description"] == "—"
        assert fourth_step["solutions"][1]["formula"] is None


# ========================================================================
# TASK 73.2.2: Step-by-step Breakdown Tests
# ========================================================================


class TestStepByStepBreakdown:
    """Step-by-step breakdown tests"""

    def test_build_step_by_step_breakdown_structure(self, service, sample_solutions):
        """Test: Breakdown yapısı doğru oluşturulmalı"""
        result = service._build_step_by_step_breakdown(sample_solutions)

        assert isinstance(result, list)
        assert len(result) == 3  # 3 çözüm

        # Her çözüm için kontrol
        for breakdown in result:
            assert "solution_id" in breakdown
            assert "title" in breakdown
            assert "total_steps" in breakdown
            assert "steps" in breakdown
            assert "flow_analysis" in breakdown

    def test_build_step_by_step_breakdown_steps(self, service, sample_solutions):
        """Test: Adımlar detaylı analiz edilmeli"""
        result = service._build_step_by_step_breakdown(sample_solutions)

        first_solution = result[0]
        assert first_solution["solution_id"] == "sol-1"
        assert first_solution["total_steps"] == 8
        assert len(first_solution["steps"]) == 8

        # İlk adım kontrolü
        first_step = first_solution["steps"][0]
        assert first_step["step_number"] == 1
        assert first_step["description"] == "Verileri oku"
        assert first_step["type"] in ["linear", "conditional", "iterative"]
        assert "estimated_time_seconds" in first_step

    def test_classify_step_type_linear(self, service):
        """Test: Doğrusal adımlar doğru sınıflandırılmalı"""
        assert service._classify_step_type("Verileri oku") == "linear"
        assert service._classify_step_type("Sonucu hesapla") == "linear"
        assert service._classify_step_type("Cevabı yaz") == "linear"

    def test_classify_step_type_conditional(self, service):
        """Test: Koşullu adımlar doğru sınıflandırılmalı"""
        assert service._classify_step_type("Eğer x > 0 ise devam et") == "conditional"
        assert service._classify_step_type("Durumunda kontrol et") == "conditional"
        assert service._classify_step_type("If condition is true") == "conditional"

    def test_classify_step_type_iterative(self, service):
        """Test: Döngülü adımlar doğru sınıflandırılmalı"""
        assert service._classify_step_type("Her eleman için işlem yap") == "iterative"
        assert service._classify_step_type("Tüm değerleri kontrol et") == "iterative"
        assert service._classify_step_type("Döngü ile hesapla") == "iterative"

    def test_flow_analysis_percentages(self, service, sample_solutions):
        """Test: Akış analizi yüzdeleri doğru hesaplanmalı"""
        result = service._build_step_by_step_breakdown(sample_solutions)

        first_solution = result[0]
        flow = first_solution["flow_analysis"]

        # Yüzdeler toplamı 100 olmalı
        total_percentage = (
            flow["linear_percentage"]
            + flow["conditional_percentage"]
            + flow["iterative_percentage"]
        )
        assert abs(total_percentage - 100.0) < 0.01  # Floating point tolerance


# ========================================================================
# TASK 73.2.3: Time Complexity Analysis Tests
# ========================================================================


class TestTimeComplexityAnalysis:
    """Time complexity analysis tests"""

    def test_analyze_time_complexity_structure(self, service, sample_solutions):
        """Test: Karmaşıklık analizi yapısı doğru olmalı"""
        result = service._analyze_time_complexity(sample_solutions)

        assert "solutions" in result
        assert "comparison" in result
        assert "complexity_ranking" in result

        assert len(result["solutions"]) == 3

    def test_estimate_complexity_fast_solution(self, service):
        """Test: Hızlı çözüm O(1) olmalı"""
        solution = {
            "step_count": 3,
            "category": "hızlı",
        }

        complexity = service._estimate_complexity(solution)

        assert complexity["notation"] == "O(1)"
        assert complexity["space_notation"] == "O(1)"
        assert "Sabit zamanlı" in complexity["explanation"]
        assert complexity["scalability"] == "Mükemmel - problem boyutundan bağımsız"

    def test_estimate_complexity_formula_solution(self, service):
        """Test: Formül çözümü O(1) olmalı"""
        solution = {
            "step_count": 2,
            "category": "formül",
        }

        complexity = service._estimate_complexity(solution)

        assert complexity["notation"] == "O(1)"

    def test_estimate_complexity_classic_solution(self, service):
        """Test: Klasik çözüm O(n) olmalı"""
        solution = {
            "step_count": 8,
            "category": "klasik",
        }

        complexity = service._estimate_complexity(solution)

        assert complexity["notation"] == "O(n)"
        assert complexity["space_notation"] == "O(1)"
        assert "Doğrusal zamanlı" in complexity["explanation"]

    def test_estimate_complexity_logical_solution(self, service):
        """Test: Mantıksal çözüm O(log n) olmalı"""
        solution = {
            "step_count": 5,
            "category": "mantıksal",
        }

        complexity = service._estimate_complexity(solution)

        assert complexity["notation"] == "O(log n)"
        assert "Logaritmik" in complexity["explanation"]

    def test_estimate_complexity_visual_solution(self, service):
        """Test: Görsel çözüm O(n) olmalı"""
        solution = {
            "step_count": 5,
            "category": "görsel",
        }

        complexity = service._estimate_complexity(solution)

        assert complexity["notation"] == "O(n)"
        assert complexity["space_notation"] == "O(n)"  # Görsel bellek kullanır

    def test_complexity_ranking(self, service, sample_solutions):
        """Test: Karmaşıklık sıralaması doğru olmalı"""
        result = service._analyze_time_complexity(sample_solutions)

        ranking = result["complexity_ranking"]

        # En verimli ilk sırada olmalı
        assert len(ranking) == 3

        # Hızlı çözüm (O(1)) en başta olmalı
        assert ranking[0]["title"] == "Hızlı Çözüm"
        assert ranking[0]["complexity_score"] == 1

    def test_find_most_efficient_solution(self, service, sample_solutions):
        """Test: En verimli çözüm doğru bulunmalı"""
        complexity_analysis = service._analyze_time_complexity(sample_solutions)
        most_efficient = service._find_most_efficient_solution(
            sample_solutions, complexity_analysis
        )

        assert most_efficient is not None
        assert most_efficient["title"] == "Hızlı Çözüm"
        assert most_efficient["complexity"] == "O(1)"
        assert "En düşük zaman karmaşıklığı" in most_efficient["reason"]


# ========================================================================
# Integration Tests: Full Comparison
# ========================================================================


class TestFullComparison:
    """Full comparison integration tests"""

    @pytest.mark.asyncio
    async def test_compare_solutions_full_structure(self, service, sample_solutions):
        """Test: Tam karşılaştırma yapısı doğru olmalı"""
        # Mock get_solutions
        with patch.object(service, "get_solutions", return_value=sample_solutions):
            result = await service.compare_solutions(
                question_id="q-1", solution_ids=["sol-1", "sol-2", "sol-3"]
            )

        assert result is not None
        assert result["question_id"] == "q-1"
        assert result["comparison_type"] == "side_by_side"

        # Ana bölümler
        assert "solutions" in result
        assert "side_by_side" in result
        assert "step_by_step_breakdown" in result
        assert "time_complexity_analysis" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_compare_solutions_summary(self, service, sample_solutions):
        """Test: Özet istatistikler doğru hesaplanmalı"""
        with patch.object(service, "get_solutions", return_value=sample_solutions):
            result = await service.compare_solutions(
                question_id="q-1", solution_ids=["sol-1", "sol-2", "sol-3"]
            )

        summary = result["summary"]

        # En kolay: Görsel Çözüm (kolay)
        assert summary["easiest"]["title"] == "Görsel Çözüm"

        # En hızlı: Hızlı Çözüm (60s)
        assert summary["fastest"]["title"] == "Hızlı Çözüm"
        assert summary["fastest"]["time"] == 60

        # En verimli: Hızlı Çözüm (O(1))
        assert summary["most_efficient"]["title"] == "Hızlı Çözüm"

        # En popüler: Hızlı Çözüm (10 oy)
        assert summary["most_popular"]["title"] == "Hızlı Çözüm"
        assert summary["most_popular"]["votes"] == 10

        # En detaylı: Klasik Çözüm (8 adım)
        assert summary["most_detailed"]["title"] == "Klasik Çözüm"
        assert summary["most_detailed"]["steps"] == 8

    @pytest.mark.asyncio
    async def test_compare_solutions_recommendation(self, service, sample_solutions):
        """Test: Çözüm önerisi yapılmalı"""
        with patch.object(service, "get_solutions", return_value=sample_solutions):
            result = await service.compare_solutions(
                question_id="q-1", solution_ids=["sol-1", "sol-2", "sol-3"]
            )

        recommended = result["summary"]["recommended"]

        assert recommended is not None
        assert "id" in recommended
        assert "title" in recommended
        assert "score" in recommended
        assert "reason" in recommended
        assert "score_breakdown" in recommended
        assert "why_recommended" in recommended

    @pytest.mark.asyncio
    async def test_compare_solutions_no_solutions(self, service):
        """Test: Çözüm bulunamazsa None dönmeli"""
        with patch.object(service, "get_solutions", return_value=None):
            result = await service.compare_solutions(
                question_id="q-1", solution_ids=["sol-1"]
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_compare_solutions_empty_selection(self, service, sample_solutions):
        """Test: Seçili çözüm yoksa None dönmeli"""
        with patch.object(service, "get_solutions", return_value=sample_solutions):
            result = await service.compare_solutions(
                question_id="q-1", solution_ids=["non-existent"]
            )

        assert result is None


# ========================================================================
# Recommendation Algorithm Tests
# ========================================================================


class TestRecommendationAlgorithm:
    """Recommendation algorithm tests"""

    def test_recommend_solution_scoring(self, service, sample_solutions):
        """Test: Çok kriterli skorlama doğru çalışmalı"""
        complexity_analysis = service._analyze_time_complexity(sample_solutions)
        recommended = service._recommend_solution(sample_solutions, complexity_analysis)

        assert recommended is not None
        assert "score" in recommended
        assert 0 <= recommended["score"] <= 100

        # Skor detayları
        breakdown = recommended["score_breakdown"]
        assert "difficulty_score" in breakdown
        assert "complexity_score" in breakdown
        assert "time_score" in breakdown
        assert "popularity_score" in breakdown

    def test_generate_recommendation_reason(self, service):
        """Test: Öneri sebebi açıklanmalı"""
        solution = {
            "difficulty": "kolay",
            "estimated_time_seconds": 60,
            "votes": {"total": 10},
        }

        breakdown = {
            "difficulty_score": 25,
            "complexity_score": 25,
            "time_score": 18,
            "popularity_score": 18,
        }

        reason = service._generate_recommendation_reason(solution, breakdown)

        assert isinstance(reason, str)
        assert len(reason) > 0
        assert "kolay" in reason or "hızlı" in reason or "popüler" in reason

    def test_recommend_solution_empty_list(self, service):
        """Test: Boş liste için None dönmeli"""
        recommended = service._recommend_solution([], {})

        assert recommended is None


# ========================================================================
# Edge Cases and Error Handling
# ========================================================================


class TestEdgeCases:
    """Edge cases and error handling tests"""

    def test_side_by_side_single_solution(self, service):
        """Test: Tek çözüm için karşılaştırma"""
        solutions = [
            {
                "id": "sol-1",
                "title": "Tek Çözüm",
                "category": "klasik",
                "difficulty": "orta",
                "estimated_time_seconds": 120,
                "step_count": 5,
                "steps": [
                    {"step_number": i, "description": f"Adım {i}"} for i in range(1, 6)
                ],
                "advantages": [],
                "disadvantages": [],
                "votes": {"total": 0},
                "usage_count": 0,
                "prerequisites": [],
                "tips": [],
            }
        ]

        result = service._build_side_by_side_comparison(solutions)

        assert len(result["headers"]) == 1
        assert len(result["steps_comparison"]) == 5

    def test_step_breakdown_no_steps(self, service):
        """Test: Adım olmayan çözüm"""
        solutions = [
            {
                "id": "sol-1",
                "title": "Adımsız",
                "category": "hızlı",
                "difficulty": "kolay",
                "estimated_time_seconds": 30,
                "step_count": 0,
                "steps": [],
                "advantages": [],
                "disadvantages": [],
                "votes": {"total": 0},
                "usage_count": 0,
                "prerequisites": [],
                "tips": [],
            }
        ]

        result = service._build_step_by_step_breakdown(solutions)

        assert len(result) == 1
        assert result[0]["total_steps"] == 0
        assert len(result[0]["steps"]) == 0

    def test_complexity_unknown_category(self, service):
        """Test: Bilinmeyen kategori için karmaşıklık tahmini"""
        solution = {
            "step_count": 7,
            "category": "bilinmeyen",
        }

        complexity = service._estimate_complexity(solution)

        assert complexity["notation"] in ["O(1)", "O(n)", "O(n²)"]
        assert "Tahmini karmaşıklık" in complexity["explanation"]
