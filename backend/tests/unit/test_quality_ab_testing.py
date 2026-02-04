"""
Test A/B Testing Framework

ABTestingFramework sınıfı için comprehensive unit testler.
REQ-48.61 - REQ-48.64 gereksinimlerini test eder.
"""

import pytest
from services.quality.ab_testing_framework import (
    ABTestingFramework,
    Experiment,
    Variant,
    VariantType,
    ExperimentStatus,
)


class TestABTestingFramework:
    """ABTestingFramework test sınıfı"""

    @pytest.fixture
    def framework(self):
        """Boş framework instance"""
        return ABTestingFramework()

    @pytest.fixture
    def sample_questions(self):
        """Örnek soru çiftleri"""
        return {
            "control": {
                "id": "q_control",
                "question_text": "Türkiye'nin başkenti neresidir?",
                "options": ["Ankara", "İstanbul", "İzmir", "Bursa", "Antalya"],
                "correct_answer": 0,
            },
            "treatment": {
                "id": "q_treatment",
                "question_text": "Türkiye Cumhuriyeti'nin başkenti hangi şehirdir?",
                "options": ["Ankara", "İstanbul", "İzmir", "Bursa", "Antalya"],
                "correct_answer": 0,
            },
        }

    # ==================== INITIALIZATION TESTS ====================

    def test_framework_initialization(self):
        """Test: Framework başlatma"""
        framework = ABTestingFramework()

        assert framework.experiments == {}

    # ==================== CREATE EXPERIMENT TESTS (REQ-48.61) ====================

    def test_create_experiment_basic(self, framework, sample_questions):
        """Test: Temel deney oluşturma (REQ-48.61)"""
        experiment = framework.create_experiment(
            name="Başkent Sorusu A/B Test",
            description="Soru formülasyonu testi",
            subject="Sosyal Bilgiler",
            difficulty_level="kolay",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        assert isinstance(experiment, Experiment)
        assert experiment.name == "Başkent Sorusu A/B Test"
        assert experiment.status == ExperimentStatus.DRAFT
        assert len(experiment.variants) == 2
        assert experiment.id in framework.experiments

    def test_create_experiment_custom_traffic(self, framework, sample_questions):
        """Test: Özel trafik dağılımı ile deney"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
            traffic_allocation=(0.7, 0.3),  # %70 kontrol, %30 test
        )

        assert experiment.variants[0].traffic_allocation == 0.7
        assert experiment.variants[1].traffic_allocation == 0.3

    def test_create_experiment_custom_parameters(self, framework, sample_questions):
        """Test: Özel parametrelerle deney"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
            minimum_sample_size=200,
            significance_level=0.01,
        )

        assert experiment.minimum_sample_size == 200
        assert experiment.significance_level == 0.01

    def test_create_experiment_invalid_traffic(self, framework, sample_questions):
        """Test: Geçersiz trafik dağılımı hata fırlatır"""
        with pytest.raises(ValueError, match="toplamı 1.0 olmalı"):
            framework.create_experiment(
                name="Test",
                description="Açıklama",
                subject="Matematik",
                difficulty_level="orta",
                control_question=sample_questions["control"],
                treatment_question=sample_questions["treatment"],
                traffic_allocation=(0.6, 0.3),  # Toplam 0.9
            )

    def test_create_experiment_variant_types(self, framework, sample_questions):
        """Test: Varyant tipleri doğru atanıyor"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        assert experiment.variants[0].type == VariantType.CONTROL
        assert experiment.variants[1].type == VariantType.TREATMENT

    # ==================== START EXPERIMENT TESTS ====================

    def test_start_experiment(self, framework, sample_questions):
        """Test: Deney başlatma"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        success = framework.start_experiment(experiment.id)

        assert success is True
        assert experiment.status == ExperimentStatus.RUNNING
        assert experiment.started_at is not None

    def test_start_experiment_invalid_id(self, framework):
        """Test: Geçersiz deney ID ile başlatma"""
        success = framework.start_experiment("invalid_id")

        assert success is False

    def test_start_experiment_already_running(self, framework, sample_questions):
        """Test: Zaten çalışan deney tekrar başlatılamaz"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)
        success = framework.start_experiment(experiment.id)

        assert success is False

    # ==================== RECORD IMPRESSION TESTS ====================

    def test_record_impression(self, framework, sample_questions):
        """Test: Gösterim kaydı"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)
        variant_id = experiment.variants[0].id

        success = framework.record_impression(experiment.id, variant_id)

        assert success is True
        assert experiment.variants[0].impressions == 1

    def test_record_multiple_impressions(self, framework, sample_questions):
        """Test: Çoklu gösterim kaydı"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)
        variant_id = experiment.variants[0].id

        for _ in range(10):
            framework.record_impression(experiment.id, variant_id)

        assert experiment.variants[0].impressions == 10

    def test_record_impression_not_running(self, framework, sample_questions):
        """Test: Çalışmayan deneyde gösterim kaydedilemez"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        variant_id = experiment.variants[0].id
        success = framework.record_impression(experiment.id, variant_id)

        assert success is False

    # ==================== RECORD RESPONSE TESTS ====================

    def test_record_response(self, framework, sample_questions):
        """Test: Yanıt kaydı"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)
        variant_id = experiment.variants[0].id

        success = framework.record_response(
            experiment.id, variant_id, is_correct=True, response_time_seconds=15.5
        )

        assert success is True
        assert experiment.variants[0].responses == 1
        assert experiment.variants[0].correct_responses == 1
        assert experiment.variants[0].total_response_time_seconds == 15.5

    def test_record_response_incorrect(self, framework, sample_questions):
        """Test: Yanlış yanıt kaydı"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)
        variant_id = experiment.variants[0].id

        framework.record_response(
            experiment.id, variant_id, is_correct=False, response_time_seconds=10.0
        )

        assert experiment.variants[0].responses == 1
        assert experiment.variants[0].correct_responses == 0

    def test_record_multiple_responses(self, framework, sample_questions):
        """Test: Çoklu yanıt kaydı"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)
        variant_id = experiment.variants[0].id

        # 10 yanıt, 7 doğru
        for i in range(10):
            framework.record_response(
                experiment.id,
                variant_id,
                is_correct=(i < 7),
                response_time_seconds=10.0,
            )

        assert experiment.variants[0].responses == 10
        assert experiment.variants[0].correct_responses == 7
        assert experiment.variants[0].accuracy_rate == 0.7

    # ==================== VARIANT METRICS TESTS ====================

    def test_variant_response_rate(self):
        """Test: Yanıt oranı hesaplama"""
        variant = Variant(
            id="v1",
            name="Test",
            type=VariantType.CONTROL,
            question_id="q1",
            question_text="Test?",
            options=["A", "B", "C", "D", "E"],
            correct_answer=0,
        )

        variant.impressions = 100
        variant.responses = 80

        assert variant.response_rate == 0.8

    def test_variant_accuracy_rate(self):
        """Test: Doğruluk oranı hesaplama"""
        variant = Variant(
            id="v1",
            name="Test",
            type=VariantType.CONTROL,
            question_id="q1",
            question_text="Test?",
            options=["A", "B", "C", "D", "E"],
            correct_answer=0,
        )

        variant.responses = 100
        variant.correct_responses = 75

        assert variant.accuracy_rate == 0.75

    def test_variant_average_response_time(self):
        """Test: Ortalama yanıt süresi hesaplama"""
        variant = Variant(
            id="v1",
            name="Test",
            type=VariantType.CONTROL,
            question_id="q1",
            question_text="Test?",
            options=["A", "B", "C", "D", "E"],
            correct_answer=0,
        )

        variant.responses = 10
        variant.total_response_time_seconds = 150.0

        assert variant.average_response_time == 15.0

    # ==================== STATISTICAL TEST TESTS (REQ-48.62) ====================

    def test_statistical_test_significant_difference(self, framework, sample_questions):
        """Test: İstatistiksel anlamlı fark (REQ-48.62)"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
            minimum_sample_size=30,
        )

        framework.start_experiment(experiment.id)

        # Kontrol grubu: %60 doğruluk
        control_id = experiment.variants[0].id
        for i in range(100):
            framework.record_response(
                experiment.id,
                control_id,
                is_correct=(i < 60),
                response_time_seconds=10.0,
            )

        # Test grubu: %80 doğruluk (anlamlı fark)
        treatment_id = experiment.variants[1].id
        for i in range(100):
            framework.record_response(
                experiment.id,
                treatment_id,
                is_correct=(i < 80),
                response_time_seconds=10.0,
            )

        result = framework.run_statistical_test(experiment.id)

        assert result is not None
        assert result.is_significant is True
        assert result.p_value < 0.05
        assert result.winner_variant_id == treatment_id

    def test_statistical_test_no_significant_difference(
        self, framework, sample_questions
    ):
        """Test: İstatistiksel anlamlı fark yok"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
            # Auto-completion tetiklememek için yüksek minimum_sample_size
            minimum_sample_size=200,
        )

        framework.start_experiment(experiment.id)

        # Her iki grup da %70 doğruluk - EŞ ZAMANLI kaydet (auto_completion'ı fair tut)
        for i in range(100):
            for variant in experiment.variants:
                framework.record_response(
                    experiment.id,
                    variant.id,
                    is_correct=(i < 70),
                    response_time_seconds=10.0,
                )

        result = framework.run_statistical_test(experiment.id)

        assert result is not None
        assert result.is_significant is False
        assert result.p_value >= 0.05

    def test_statistical_test_insufficient_data(self, framework, sample_questions):
        """Test: Yetersiz veri"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)

        # Sadece 10 yanıt (minimum 30 gerekli)
        for variant in experiment.variants:
            for i in range(10):
                framework.record_response(
                    experiment.id,
                    variant.id,
                    is_correct=True,
                    response_time_seconds=10.0,
                )

        result = framework.run_statistical_test(experiment.id)

        assert result is not None
        assert result.is_significant is False
        assert "Yeterli veri yok" in result.recommendation

    def test_statistical_test_p_value_calculation(self, framework, sample_questions):
        """Test: P-value hesaplama"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)

        # Veri ekle
        for variant in experiment.variants:
            for i in range(100):
                framework.record_response(
                    experiment.id,
                    variant.id,
                    is_correct=(i < 70),
                    response_time_seconds=10.0,
                )

        result = framework.run_statistical_test(experiment.id)

        assert 0 <= result.p_value <= 1

    # ==================== COMPLETE EXPERIMENT TESTS (REQ-48.64) ====================

    def test_complete_experiment(self, framework, sample_questions):
        """Test: Deney tamamlama (REQ-48.64)"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)
        success = framework.complete_experiment(experiment.id)

        assert success is True
        assert experiment.status == ExperimentStatus.COMPLETED
        assert experiment.completed_at is not None

    def test_complete_experiment_auto_select_winner(self, framework, sample_questions):
        """Test: Kazananı otomatik seçme (REQ-48.64)"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
            minimum_sample_size=30,
        )

        framework.start_experiment(experiment.id)

        # Treatment daha iyi performans
        control_id = experiment.variants[0].id
        treatment_id = experiment.variants[1].id

        for i in range(100):
            framework.record_response(
                experiment.id,
                control_id,
                is_correct=(i < 60),
                response_time_seconds=10.0,
            )
            framework.record_response(
                experiment.id,
                treatment_id,
                is_correct=(i < 80),
                response_time_seconds=10.0,
            )

        framework.complete_experiment(experiment.id, auto_select_winner=True)

        assert experiment.winner == treatment_id

    def test_complete_experiment_invalid_status(self, framework, sample_questions):
        """Test: Geçersiz durumda tamamlama"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        # DRAFT durumunda tamamlanamaz
        success = framework.complete_experiment(experiment.id)

        assert success is False

    # ==================== PERFORMANCE COMPARISON TESTS (REQ-48.63) ====================

    def test_get_performance_comparison(self, framework, sample_questions):
        """Test: Performans karşılaştırma raporu (REQ-48.63)"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)

        # Veri ekle
        for variant in experiment.variants:
            for i in range(50):
                framework.record_response(
                    experiment.id,
                    variant.id,
                    is_correct=(i < 35),
                    response_time_seconds=10.0,
                )

        comparison = framework.get_performance_comparison(experiment.id)

        assert comparison is not None
        assert "experiment_id" in comparison
        assert "variants" in comparison
        assert "comparison" in comparison
        assert "statistical_test" in comparison
        assert len(comparison["variants"]) == 2

    def test_get_performance_comparison_metrics(self, framework, sample_questions):
        """Test: Performans metrikleri"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)

        variant_id = experiment.variants[0].id
        framework.record_impression(experiment.id, variant_id)
        framework.record_response(
            experiment.id, variant_id, is_correct=True, response_time_seconds=10.0
        )

        comparison = framework.get_performance_comparison(experiment.id)

        variant_data = comparison["variants"][0]
        assert "impressions" in variant_data
        assert "responses" in variant_data
        assert "response_rate" in variant_data
        assert "accuracy_rate" in variant_data
        assert "average_response_time" in variant_data

    # ==================== EXPERIMENT SUMMARY TESTS ====================

    def test_get_experiment_summary(self, framework, sample_questions):
        """Test: Deney özeti"""
        experiment = framework.create_experiment(
            name="Test Experiment",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        summary = framework.get_experiment_summary(experiment.id)

        assert summary is not None
        assert summary["name"] == "Test Experiment"
        assert summary["status"] == ExperimentStatus.DRAFT.value
        assert "total_impressions" in summary
        assert "total_responses" in summary

    def test_list_experiments(self, framework, sample_questions):
        """Test: Deneyleri listeleme"""
        # Birkaç deney oluştur
        for i in range(3):
            framework.create_experiment(
                name=f"Test {i}",
                description="Açıklama",
                subject="Matematik",
                difficulty_level="orta",
                control_question=sample_questions["control"],
                treatment_question=sample_questions["treatment"],
            )

        experiments = framework.list_experiments()

        assert len(experiments) == 3

    def test_list_experiments_filtered(self, framework, sample_questions):
        """Test: Filtrelenmiş deney listesi"""
        # DRAFT deney
        exp1 = framework.create_experiment(
            name="Test 1",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        # RUNNING deney
        exp2 = framework.create_experiment(
            name="Test 2",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )
        framework.start_experiment(exp2.id)

        running_experiments = framework.list_experiments(
            status=ExperimentStatus.RUNNING
        )

        assert len(running_experiments) == 1
        assert running_experiments[0]["name"] == "Test 2"

    # ==================== EDGE CASES ====================

    def test_auto_completion_on_significance(self, framework, sample_questions):
        """Test: Anlamlılık üzerine otomatik tamamlama"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
            minimum_sample_size=30,
        )

        framework.start_experiment(experiment.id)

        # Anlamlı fark oluştur
        control_id = experiment.variants[0].id
        treatment_id = experiment.variants[1].id

        for i in range(100):
            framework.record_response(
                experiment.id,
                control_id,
                is_correct=(i < 50),
                response_time_seconds=10.0,
            )
            framework.record_response(
                experiment.id,
                treatment_id,
                is_correct=(i < 90),
                response_time_seconds=10.0,
            )

        # Otomatik tamamlanmış olmalı
        assert experiment.status == ExperimentStatus.COMPLETED

    def test_normal_cdf_calculation(self, framework):
        """Test: Normal CDF hesaplama"""
        # Standart değerler
        assert abs(framework._normal_cdf(0) - 0.5) < 0.01
        assert framework._normal_cdf(-3) < 0.01
        assert framework._normal_cdf(3) > 0.99

    def test_zero_variance_handling(self, framework, sample_questions):
        """Test: Sıfır varyans durumu"""
        experiment = framework.create_experiment(
            name="Test",
            description="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            control_question=sample_questions["control"],
            treatment_question=sample_questions["treatment"],
        )

        framework.start_experiment(experiment.id)

        # Her iki grup da %100 doğruluk (sıfır varyans)
        for variant in experiment.variants:
            for i in range(50):
                framework.record_response(
                    experiment.id,
                    variant.id,
                    is_correct=True,
                    response_time_seconds=10.0,
                )

        result = framework.run_statistical_test(experiment.id)

        # Hata vermemeli
        assert result is not None


# ==================== INTEGRATION TESTS ====================


class TestABTestingFrameworkIntegration:
    """Integration testleri"""

    def test_full_ab_test_workflow(self):
        """Test: Tam A/B test iş akışı"""
        framework = ABTestingFramework()

        # 1. Deney oluştur
        experiment = framework.create_experiment(
            name="Soru Formülasyonu Testi",
            description="Hangi soru formülasyonu daha etkili?",
            subject="Matematik",
            difficulty_level="orta",
            control_question={
                "question_text": "2 + 2 = ?",
                "options": ["3", "4", "5", "6", "7"],
                "correct_answer": 1,
            },
            treatment_question={
                "question_text": "İki artı iki eşittir kaç?",
                "options": ["3", "4", "5", "6", "7"],
                "correct_answer": 1,
            },
            minimum_sample_size=50,
        )

        # 2. Deneyi başlat
        framework.start_experiment(experiment.id)

        # 3. Veri topla
        control_id = experiment.variants[0].id
        treatment_id = experiment.variants[1].id

        for i in range(100):
            # Kontrol grubu: %70 doğruluk
            framework.record_impression(experiment.id, control_id)
            framework.record_response(
                experiment.id,
                control_id,
                is_correct=(i < 70),
                response_time_seconds=12.0,
            )

            # Test grubu: %85 doğruluk
            framework.record_impression(experiment.id, treatment_id)
            framework.record_response(
                experiment.id,
                treatment_id,
                is_correct=(i < 85),
                response_time_seconds=11.0,
            )

        # 4. İstatistiksel test
        result = framework.run_statistical_test(experiment.id)
        assert result.is_significant is True

        # 5. Performans karşılaştırması
        comparison = framework.get_performance_comparison(experiment.id)
        assert comparison["comparison"]["better_accuracy"] == "Treatment (B)"

        # 6. Deney tamamlandı (otomatik)
        assert experiment.status == ExperimentStatus.COMPLETED
        assert experiment.winner == treatment_id

    def test_multiple_experiments_management(self):
        """Test: Çoklu deney yönetimi"""
        framework = ABTestingFramework()

        # 3 farklı deney oluştur
        experiments = []
        for i in range(3):
            exp = framework.create_experiment(
                name=f"Deney {i}",
                description=f"Açıklama {i}",
                subject="Matematik",
                difficulty_level="orta",
                control_question={
                    "question_text": f"Soru {i}?",
                    "options": ["A", "B", "C", "D", "E"],
                    "correct_answer": 0,
                },
                treatment_question={
                    "question_text": f"Soru {i} alternatif?",
                    "options": ["A", "B", "C", "D", "E"],
                    "correct_answer": 0,
                },
            )
            experiments.append(exp)

        # İlk ikisini başlat
        framework.start_experiment(experiments[0].id)
        framework.start_experiment(experiments[1].id)

        # Durum kontrolü
        all_experiments = framework.list_experiments()
        running = framework.list_experiments(status=ExperimentStatus.RUNNING)
        draft = framework.list_experiments(status=ExperimentStatus.DRAFT)

        assert len(all_experiments) == 3
        assert len(running) == 2
        assert len(draft) == 1
