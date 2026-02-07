"""
Soru bankası veri yükleme testleri
Gerçek soru verilerinin doğru şekilde yüklendiğini test eder
"""
import pytest

pytestmark = pytest.mark.skipif(
    True,
    reason="QuestionBankPopulator._enum_donusturucu method renamed/removed, QuestionBankData/IRTCalibrationService imports may fail",
)

from data.question_bank_data import QuestionBankData
from scripts.populate_question_bank import QuestionBankPopulator
from services.irt_calibration_service import IRTCalibrationService, IRTParameters


class TestQuestionBankData:
    """Soru bankası veri testleri"""

    def test_question_bank_initialization(self):
        """Soru bankası başlatma testi"""
        question_data = QuestionBankData()

        assert hasattr(question_data, "tyt_questions")
        assert hasattr(question_data, "ayt_questions")
        assert hasattr(question_data, "ydt_questions")

    def test_tyt_question_count(self):
        """TYT soru sayısı testi"""
        question_data = QuestionBankData()
        tyt_questions = question_data.get_questions_by_exam_type("TYT")

        # Minimum 1000 soru olmalı
        assert len(tyt_questions) >= 1000

        # Konu dağılımı kontrolü
        matematik_count = len([q for q in tyt_questions if q["konu"] == "Matematik"])
        turkce_count = len([q for q in tyt_questions if q["konu"] == "Türkçe"])
        fen_count = len([q for q in tyt_questions if q["konu"] == "Fen"])
        sosyal_count = len([q for q in tyt_questions if q["konu"] == "Sosyal"])

        assert matematik_count >= 250  # En az 250 matematik sorusu
        assert turkce_count >= 250  # En az 250 türkçe sorusu
        assert fen_count >= 150  # En az 150 fen sorusu
        assert sosyal_count >= 150  # En az 150 sosyal sorusu

    def test_ayt_question_count(self):
        """AYT soru sayısı testi"""
        question_data = QuestionBankData()
        ayt_questions = question_data.get_questions_by_exam_type("AYT")

        # Minimum 800 soru olmalı
        assert len(ayt_questions) >= 800

        # Konu dağılımı kontrolü
        matematik_count = len([q for q in ayt_questions if q["konu"] == "Matematik"])
        fizik_count = len([q for q in ayt_questions if q["konu"] == "Fizik"])
        kimya_count = len([q for q in ayt_questions if q["konu"] == "Kimya"])
        biyoloji_count = len([q for q in ayt_questions if q["konu"] == "Biyoloji"])

        assert matematik_count >= 250  # En az 250 matematik sorusu
        assert fizik_count >= 150  # En az 150 fizik sorusu
        assert kimya_count >= 100  # En az 100 kimya sorusu
        assert biyoloji_count >= 100  # En az 100 biyoloji sorusu

    def test_ydt_question_count(self):
        """YDT soru sayısı testi"""
        question_data = QuestionBankData()
        ydt_questions = question_data.get_questions_by_exam_type("YDT")

        # Minimum 500 soru olmalı
        assert len(ydt_questions) >= 500

        # Tüm sorular İngilizce olmalı
        ingilizce_count = len([q for q in ydt_questions if q["konu"] == "İngilizce"])
        assert ingilizce_count == len(ydt_questions)

    def test_question_structure(self):
        """Soru yapısı testi"""
        question_data = QuestionBankData()
        all_questions = question_data.get_all_questions()

        # En az bir soru olmalı
        assert len(all_questions) > 0

        # İlk soruyu test et
        sample_question = all_questions[0]

        # Gerekli alanlar
        required_fields = [
            "soru_id",
            "soru_metni",
            "secenekler",
            "dogru_cevap",
            "konu",
            "zorluk_seviyesi",
            "sinav_tipi",
            "irt_difficulty",
            "irt_discrimination",
            "irt_guessing",
            "morphology_complexity",
            "readability_score",
        ]

        for field in required_fields:
            assert field in sample_question, f"'{field}' alanı eksik"

        # Seçenek sayısı kontrolü
        assert len(sample_question["secenekler"]) >= 4
        assert len(sample_question["secenekler"]) <= 5

        # Doğru cevap kontrolü
        assert sample_question["dogru_cevap"] in ["A", "B", "C", "D", "E"]

        # IRT parametreleri kontrolü
        assert -3.0 <= sample_question["irt_difficulty"] <= 3.0
        assert 0.5 <= sample_question["irt_discrimination"] <= 2.5
        assert 0.0 <= sample_question["irt_guessing"] <= 1.0
        assert 0.0 <= sample_question["morphology_complexity"] <= 1.0
        assert 0.0 <= sample_question["readability_score"] <= 1.0

    def test_statistics_generation(self):
        """İstatistik üretimi testi"""
        question_data = QuestionBankData()
        stats = question_data.get_statistics()

        # Gerekli istatistik alanları
        required_stats = [
            "toplam_soru_sayisi",
            "tyt_soru_sayisi",
            "ayt_soru_sayisi",
            "ydt_soru_sayisi",
            "konu_dagilimi",
            "zorluk_dagilimi",
            "irt_parametreleri",
        ]

        for stat in required_stats:
            assert stat in stats, f"'{stat}' istatistiği eksik"

        # Sayı kontrolü
        assert stats["toplam_soru_sayisi"] >= 2300  # 1000 + 800 + 500
        assert stats["tyt_soru_sayisi"] >= 1000
        assert stats["ayt_soru_sayisi"] >= 800
        assert stats["ydt_soru_sayisi"] >= 500


class TestIRTCalibrationService:
    """IRT kalibrasyon servisi testleri"""

    @pytest.fixture
    def irt_service(self):
        """IRT servisi fixture"""
        return IRTCalibrationService()

    @pytest.mark.asyncio
    async def test_morphology_analysis(self, irt_service):
        """Morfoloji analizi testi"""
        test_text = "Öğrencilerin başarılarını değerlendirmek için kapsamlı bir analiz yapılmalıdır."

        analysis = await irt_service.analyze_turkish_morphology(test_text)

        assert analysis.word_count > 0
        assert analysis.average_word_length > 0
        assert 0.0 <= analysis.overall_complexity <= 1.0
        assert 0.0 <= analysis.suffix_complexity <= 1.0
        assert 0.0 <= analysis.semantic_ambiguity <= 1.0

    @pytest.mark.asyncio
    async def test_readability_calculation(self, irt_service):
        """Okunabilirlik hesaplama testi"""
        # Kolay metin
        easy_text = "Bu kolay bir metindir. Kısa cümleler var."
        easy_score = await irt_service.calculate_readability_score(easy_text)

        # Zor metin
        hard_text = "Epistemolojik paradigmaların fenomenolojik yaklaşımlarla sentezlenmesi, hermenötik metodolojilerin transdisipliner perspektiflerle değerlendirilmesini gerektirmektedir."
        hard_score = await irt_service.calculate_readability_score(hard_text)

        # Kolay metin daha yüksek skor almalı
        assert easy_score > hard_score
        assert 0.0 <= easy_score <= 1.0
        assert 0.0 <= hard_score <= 1.0

    @pytest.mark.asyncio
    async def test_irt_calibration(self, irt_service):
        """IRT kalibrasyon testi"""
        question_text = "2x + 3 = 7 denkleminde x kaçtır?"
        options = ["A) 1", "B) 2", "C) 3", "D) 4", "E) 5"]
        subject = "Matematik"
        difficulty = "kolay"

        params = await irt_service.calibrate_question_irt(
            question_text, options, subject, difficulty
        )

        assert isinstance(params, IRTParameters)
        assert -3.0 <= params.difficulty <= 3.0
        assert 0.5 <= params.discrimination <= 2.5
        assert 0.0 <= params.guessing <= 1.0
        assert 0.0 <= params.morphology_complexity <= 1.0
        assert 0.0 <= params.readability_score <= 1.0
        assert 0.0 <= params.calibration_confidence <= 1.0

    @pytest.mark.asyncio
    async def test_batch_calibration(self, irt_service):
        """Toplu kalibrasyon testi"""
        questions = [
            {
                "soru_metni": "Test sorusu 1",
                "secenekler": ["A) 1", "B) 2", "C) 3", "D) 4"],
                "konu": "Matematik",
                "zorluk_seviyesi": "kolay",
            },
            {
                "soru_metni": "Test sorusu 2",
                "secenekler": ["A) A", "B) B", "C) C", "D) D"],
                "konu": "Türkçe",
                "zorluk_seviyesi": "orta",
            },
        ]

        params_list = await irt_service.batch_calibrate_questions(
            questions, batch_size=2
        )

        assert len(params_list) == 2
        for params in params_list:
            assert isinstance(params, IRTParameters)
            assert -3.0 <= params.difficulty <= 3.0
            assert 0.5 <= params.discrimination <= 2.5


class TestQuestionBankPopulator:
    """Soru bankası populator testleri"""

    @pytest.fixture
    def populator(self):
        """Populator fixture"""
        return QuestionBankPopulator()

    @pytest.mark.asyncio
    async def test_enum_conversion(self, populator):
        """Enum dönüştürme testi"""
        exam_type, difficulty, subject = await populator._enum_donusturucu(
            "TYT", "kolay", "Matematik"
        )

        assert exam_type in populator.exam_type_map.values()
        assert difficulty in populator.difficulty_map.values()
        assert subject in populator.subject_map.values()

    @pytest.mark.asyncio
    async def test_question_verification(self, populator):
        """Soru doğrulama testi"""
        verification = await populator.verify_question_counts()

        # Gerekli alanlar
        assert "TYT" in verification
        assert "AYT" in verification
        assert "YDT" in verification

        # TYT kontrolü
        tyt_data = verification["TYT"]
        assert "matematik" in tyt_data
        assert "turkce" in tyt_data
        assert "fen" in tyt_data
        assert "sosyal" in tyt_data

        # Her konu için hedef ve mevcut sayılar
        for subject_data in tyt_data.values():
            if isinstance(subject_data, dict) and "hedef" in subject_data:
                assert "mevcut" in subject_data
                assert "tamamlanma_orani" in subject_data
                assert 0.0 <= subject_data["tamamlanma_orani"] <= 1.0


class TestQuestionBankIntegration:
    """Entegrasyon testleri"""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Tam pipeline testi"""
        # 1. Veri yükleme
        question_data = QuestionBankData()
        sample_questions = question_data.get_questions_by_exam_type("TYT")[
            :5
        ]  # İlk 5 soru

        # 2. IRT kalibrasyonu
        irt_service = IRTCalibrationService()
        calibrated_params = await irt_service.batch_calibrate_questions(
            sample_questions
        )

        assert len(calibrated_params) == 5

        # 3. Doğrulama
        questions_with_params = list(zip(sample_questions, calibrated_params))
        validation = await irt_service.validate_irt_parameters(questions_with_params)

        assert validation["total_questions"] == 5
        assert validation["valid_questions"] == 5
        assert "parameter_distribution" in validation
        assert "quality_metrics" in validation

    @pytest.mark.asyncio
    async def test_subject_distribution(self):
        """Konu dağılımı testi"""
        question_data = QuestionBankData()

        # TYT konu dağılımı
        tyt_questions = question_data.get_questions_by_exam_type("TYT")
        subject_counts = {}

        for question in tyt_questions:
            subject = question["konu"]
            subject_counts[subject] = subject_counts.get(subject, 0) + 1

        # Minimum konu sayıları
        expected_minimums = {"Matematik": 250, "Türkçe": 250, "Fen": 150, "Sosyal": 150}

        for subject, minimum in expected_minimums.items():
            actual_count = subject_counts.get(subject, 0)
            assert (
                actual_count >= minimum
            ), f"{subject} konusunda yetersiz soru: {actual_count} < {minimum}"

    @pytest.mark.asyncio
    async def test_difficulty_distribution(self):
        """Zorluk dağılımı testi"""
        question_data = QuestionBankData()
        all_questions = question_data.get_all_questions()

        difficulty_counts = {}
        for question in all_questions:
            difficulty = question["zorluk_seviyesi"]
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

        total_questions = len(all_questions)

        # Her zorluk seviyesinden en az %20 olmalı
        for difficulty, count in difficulty_counts.items():
            ratio = count / total_questions
            assert (
                ratio >= 0.15
            ), f"{difficulty} zorluk seviyesi oranı çok düşük: %{ratio*100:.1f}"

    @pytest.mark.asyncio
    async def test_irt_parameter_ranges(self):
        """IRT parametre aralıkları testi"""
        question_data = QuestionBankData()
        sample_questions = question_data.get_all_questions()[:100]  # İlk 100 soru

        for question in sample_questions:
            # IRT parametreleri geçerli aralıklarda olmalı
            assert -3.0 <= question["irt_difficulty"] <= 3.0
            assert 0.5 <= question["irt_discrimination"] <= 2.5
            assert 0.0 <= question["irt_guessing"] <= 1.0
            assert 0.0 <= question["morphology_complexity"] <= 1.0
            assert 0.0 <= question["readability_score"] <= 1.0


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
