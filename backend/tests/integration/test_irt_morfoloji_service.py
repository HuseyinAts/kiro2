"""
IRT + Türkçe Morfoloji Servisi Test Dosyası
ÖSYM ve ETS standartlarını aşan soru analizi testleri
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from algorithms.irt_morfoloji_service import (
    IRTMorfolojiService,
    IRTParameters,
    MorphologyComplexity,
    QuestionAnalysis,
    irt_morfoloji_service,
)
from core.turkish_nlp_service import MorphologicalAnalysis


class TestIRTMorfolojiService:
    """IRT + Morfoloji Servisi Test Sınıfı"""

    @pytest.fixture
    def service(self):
        """Test servisi fixture"""
        return IRTMorfolojiService()

    @pytest.fixture
    def mock_morphological_analysis(self):
        """Mock morfolojik analiz"""
        return MorphologicalAnalysis(
            word="çocuklar",
            root="çocuk",
            suffixes=["lar"],
            pos_tag="NOUN",
            derivational_depth=0,
            is_compound=False,
            compound_parts=[],
            complexity_score=0.3,
        )

    @pytest.fixture
    def sample_question_text(self):
        """Örnek soru metni"""
        return "Çocuklar bahçede oynuyorlar. Bu cümlede kaç tane isim vardır?"

    @pytest.fixture
    def sample_student_responses(self):
        """Örnek öğrenci yanıtları"""
        return [
            {"student_id": "1", "answer": "A", "is_correct": True, "response_time": 30},
            {
                "student_id": "2",
                "answer": "B",
                "is_correct": False,
                "response_time": 45,
            },
            {"student_id": "3", "answer": "A", "is_correct": True, "response_time": 25},
            {
                "student_id": "4",
                "answer": "C",
                "is_correct": False,
                "response_time": 60,
            },
            {"student_id": "5", "answer": "A", "is_correct": True, "response_time": 35},
        ]

    def test_service_initialization(self, service):
        """Servis başlatma testi"""
        assert service is not None
        assert hasattr(service, "complexity_weights")
        assert hasattr(service, "osym_standards")
        assert hasattr(service, "ets_standards")
        assert hasattr(service, "turkish_irt_adjustments")

        # Karmasiklik agirliklari kontrolu
        expected_weights = {
            "suffix_count",
            "derivational_depth",
            "compound_complexity",
            "phonetic_changes",
            "semantic_ambiguity",
        }
        assert set(service.complexity_weights.keys()) == expected_weights

        # Turkce ayarlamalar kontrolu
        expected_adjustments = {
            "morphology_factor",
            "cultural_context",
            "semantic_richness",
            "syntactic_complexity",
        }
        assert set(service.turkish_irt_adjustments.keys()) == expected_adjustments

    @pytest.mark.asyncio(loop_scope="function")
    async def test_analyze_question_irt_morphology_basic(
        self, service, sample_question_text, sample_student_responses
    ):
        """Temel IRT + Morfoloji analizi testi"""
        with (
            patch.object(
                service, "_analyze_turkish_morphology_complexity"
            ) as mock_morphology,
            patch.object(service, "_calculate_base_irt_parameters") as mock_irt,
            patch.object(service, "_adjust_irt_with_morphology") as mock_adjust,
        ):
            # Mock returns
            mock_morphology.return_value = MorphologyComplexity(
                word="çocuklar",
                root="çocuk",
                suffixes=["lar"],
                suffix_count=1,
                derivational_depth=0,
                compound_complexity=0.0,
                phonetic_changes=0,
                semantic_ambiguity=0.3,
                overall_complexity=0.4,
            )

            mock_irt.return_value = IRTParameters(
                difficulty=0.5, discrimination=1.2, guessing=0.20, upper_asymptote=1.0
            )

            mock_adjust.return_value = IRTParameters(
                difficulty=0.6, discrimination=1.3, guessing=0.18, upper_asymptote=1.0
            )

            # Test
            result = await service.analyze_question_irt_morphology(
                question_id="test_q1",
                question_text=sample_question_text,
                correct_answer="A",
                student_responses=sample_student_responses,
            )

            # Assertions
            assert isinstance(result, QuestionAnalysis)
            assert result.question_id == "test_q1"
            assert result.question_text == sample_question_text
            assert result.irt_parameters.difficulty == 0.6
            assert result.morphology_complexity.word == "çocuklar"
            assert result.analysis_confidence > 0.0
            assert len(result.recommendations) > 0

    @pytest.mark.asyncio(loop_scope="function")
    async def test_analyze_turkish_morphology_complexity(self, service):
        """Türkçe morfolojik karmaşıklık analizi testi"""
        # OLCUM (6 Eyl 2026): bu test CI'da "assert 'ogrencilerimiz' == 'ogrenci'"
        # ile dusuyordu, yerelde ise geciyordu. Donen deger ne mock'un `word`u
        # ne `root`u -- yani mock HIC DEVREYE GIRMEMIS, gercek servis kosmustu.
        # `turkish_nlp_service` Zemberek server'ina (localhost:6789) baglanamayinca
        # fallback moda gecip "ogrencilerimizden" -> "ogrencilerimiz" donduruyor;
        # CI'da Zemberek yok, bu makinede vardi. Ustelik servis
        # `asyncio.gather(..., return_exceptions=True)` kullandigi icin mock
        # kaynakli bir hata da SESSIZCE yutulup gercek sonuca dusulebiliyordu.
        #
        # Uc yonlu saglamlastirma:
        # 1) Patch hedefi, servisin GERCEKTEN okudugu isim alani
        #    (`algorithms.irt_morfoloji_service.turkish_nlp_service`). Servis
        #    `from core.turkish_nlp_service import turkish_nlp_service` ile kendi
        #    global'ine baglaniyor; oraya yazmak nesne-kimligi/import-sirasi
        #    farklarindan bagimsizdir.
        # 2) `new_callable=AsyncMock`: patch'in "async mi" otomatik algisina
        #    guvenilmiyor. Sync bir mock `await` edilemez, `return_exceptions=True`
        #    onu yutar ve test yine gercek servise duserdi.
        # 3) `assert mock.called`: mock devreye girmezse test SESSIZCE gercek
        #    servisi olcmek yerine ACIK mesajla duser (SS10.52'nin dersi).
        nlp_mock = MagicMock()
        nlp_mock.analyze_morphology = AsyncMock(
            return_value=MorphologicalAnalysis(
                word="öğrencilerimizden",
                root="öğrenci",
                suffixes=["ler", "imiz", "den"],
                pos_tag="NOUN",
                derivational_depth=1,
                is_compound=False,
                compound_parts=[],
                complexity_score=0.8,
            )
        )

        with patch("algorithms.irt_morfoloji_service.turkish_nlp_service", nlp_mock):
            mock_analyze = nlp_mock.analyze_morphology

            text = "Öğrencilerimizden bazıları çok başarılı."
            result = await service._analyze_turkish_morphology_complexity(text)

            assert mock_analyze.called, (
                "analyze_morphology mock'u hic cagrilmadi -- servis gercek "
                "turkish_nlp_service'i kullandi, yani bu test mock'ladigi "
                "mantigi DOGRULAMIYOR (Zemberek fallback'ine dusmus olabilir)"
            )
            assert isinstance(result, MorphologyComplexity)
            assert result.word.lower() == "öğrencilerimizden"
            assert result.root == "öğrenci"
            assert result.suffix_count == 3
            assert result.overall_complexity > 0.0

    def test_calculate_word_complexity(self, service, mock_morphological_analysis):
        """Kelime karmaşıklığı hesaplama testi"""
        complexity = service._calculate_word_complexity(mock_morphological_analysis)

        assert isinstance(complexity, float)
        assert 0.0 <= complexity <= 1.0

    def test_calculate_derivational_depth(self, service):
        """Türetim derinliği hesaplama testi"""
        # Turetim ekleri iceren liste
        suffixes_with_derivation = ["lı", "lık", "ça"]
        depth = service._calculate_derivational_depth(suffixes_with_derivation)
        assert depth == 3

        # Turetim eki olmayan liste
        suffixes_without_derivation = ["lar", "ın", "da"]
        depth = service._calculate_derivational_depth(suffixes_without_derivation)
        assert depth == 0

    def test_calculate_compound_complexity(self, service):
        """Birleşik kelime karmaşıklığı testi"""
        # Uzun kelime (birlesik olabilir)
        long_word = "çekoslovakyalılaştıramadıklarımızdanmısınız"
        complexity = service._calculate_compound_complexity(long_word)
        assert complexity == 0.8

        # Orta uzunluk kelime
        medium_word = "öğrencilerimiz"
        complexity = service._calculate_compound_complexity(medium_word)
        assert complexity == 0.5

        # Kisa kelime
        short_word = "ev"
        complexity = service._calculate_compound_complexity(short_word)
        assert complexity == 0.0

    def test_count_phonetic_changes(self, service):
        """Ses değişimi sayma testi"""
        # Unlu uyumu olan
        root = "ev"
        suffixes = ["de"]
        changes = service._count_phonetic_changes(root, suffixes)
        assert changes >= 0

        # Unlu uyumu olmayan
        root = "kitap"
        suffixes = ["de"]  # "ta" olmalıydı
        changes = service._count_phonetic_changes(root, suffixes)
        assert changes >= 0

    def test_check_vowel_harmony(self, service):
        """Ünlü uyumu kontrolü testi"""
        # On unlu uyumu
        assert service._check_vowel_harmony("e", "i") is True
        assert service._check_vowel_harmony("e", "a") is False

        # Arka unlu uyumu
        assert service._check_vowel_harmony("a", "ı") is True
        assert service._check_vowel_harmony("a", "e") is False

    def test_calculate_semantic_ambiguity(self, service):
        """Anlam belirsizliği hesaplama testi"""
        # Kok orani yuksek (az ek)
        ambiguity = service._calculate_semantic_ambiguity("kitap", "kitap")
        assert ambiguity == 0.2

        # Kok orani dusuk (cok ek)
        ambiguity = service._calculate_semantic_ambiguity("kitaplarımızdan", "kitap")
        assert ambiguity == 0.6  # Gerçek hesaplama sonucu

    @pytest.mark.asyncio(loop_scope="function")
    async def test_calculate_base_irt_parameters(
        self, service, sample_question_text, sample_student_responses
    ):
        """Temel IRT parametreleri hesaplama testi"""
        # Ogrenci yanitlari ile
        params = await service._calculate_base_irt_parameters(
            sample_question_text, "A", sample_student_responses, None
        )

        assert isinstance(params, IRTParameters)
        assert -3.0 <= params.difficulty <= 3.0
        assert 0.5 <= params.discrimination <= 2.5
        assert 0.0 <= params.guessing <= 0.5
        assert params.upper_asymptote == 1.0

        # Temel zorluk ile
        params = await service._calculate_base_irt_parameters(
            sample_question_text, "A", None, 1.5
        )

        assert params.difficulty == 1.5

    @pytest.mark.asyncio(loop_scope="function")
    async def test_adjust_irt_with_morphology(self, service):
        """IRT parametrelerini morfoloji ile ayarlama testi"""
        base_params = IRTParameters(
            difficulty=0.0, discrimination=1.0, guessing=0.20, upper_asymptote=1.0
        )

        morphology = MorphologyComplexity(
            word="öğrencilerimizden",
            root="öğrenci",
            suffixes=["ler", "imiz", "den"],
            suffix_count=3,
            derivational_depth=1,
            compound_complexity=0.5,
            phonetic_changes=0,
            semantic_ambiguity=0.6,
            overall_complexity=0.7,
        )

        adjusted_params = await service._adjust_irt_with_morphology(
            base_params, morphology
        )

        assert isinstance(adjusted_params, IRTParameters)
        # Morfolojik karmasiklik zorluk artirmali
        assert adjusted_params.difficulty > base_params.difficulty
        # Ayirt edicilik artmali
        assert adjusted_params.discrimination > base_params.discrimination
        # Sans faktoru azalmali
        assert adjusted_params.guessing < base_params.guessing

    def test_calculate_turkish_difficulty_factor(self, service):
        """Türkçe zorluk faktörü hesaplama testi"""
        morphology = MorphologyComplexity(
            word="test",
            root="test",
            suffixes=[],
            suffix_count=0,
            derivational_depth=0,
            compound_complexity=0.0,
            phonetic_changes=0,
            semantic_ambiguity=0.3,
            overall_complexity=0.4,
        )

        irt_params = IRTParameters(
            difficulty=0.5, discrimination=1.2, guessing=0.20, upper_asymptote=1.0
        )

        factor = service._calculate_turkish_difficulty_factor(morphology, irt_params)

        assert isinstance(factor, float)
        assert 0.5 <= factor <= 2.0

    @pytest.mark.asyncio(loop_scope="function")
    async def test_compare_with_osym_ets_standards(self, service):
        """ÖSYM/ETS standartları karşılaştırma testi"""
        irt_params = IRTParameters(
            difficulty=0.5, discrimination=1.2, guessing=0.20, upper_asymptote=1.0
        )

        morphology = MorphologyComplexity(
            word="test",
            root="test",
            suffixes=[],
            suffix_count=0,
            derivational_depth=0,
            compound_complexity=0.0,
            phonetic_changes=0,
            semantic_ambiguity=0.3,
            overall_complexity=0.4,
        )

        comparison = await service._compare_with_osym_ets_standards(
            irt_params, morphology
        )

        assert isinstance(comparison, dict)
        expected_keys = {
            "osym_difficulty_match",
            "ets_difficulty_match",
            "osym_discrimination_match",
            "ets_discrimination_match",
            "turkish_enhancement_factor",
            "overall_improvement",
        }
        assert set(comparison.keys()) == expected_keys

        # Tum degerler 0-1 araliginda olmali (overall_improvement haric)
        for key, value in comparison.items():
            if key != "overall_improvement":
                assert 0.0 <= value <= 1.0

    def test_calculate_standard_match(self, service):
        """Standart eşleşme skoru testi"""
        # OSYM standartlari ile tam eslesme
        difficulty = 0.0  # medium range içinde
        match_score = service._calculate_standard_match(
            difficulty, service.osym_standards
        )
        assert match_score == 1.0

        # Aralik disinda
        difficulty = 5.0  # çok yüksek
        match_score = service._calculate_standard_match(
            difficulty, service.osym_standards
        )
        assert 0.0 <= match_score < 1.0

    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_recommendations(self, service):
        """Öneri oluşturma testi"""
        # Cok kolay soru
        irt_params = IRTParameters(
            difficulty=-2.0, discrimination=0.8, guessing=0.20, upper_asymptote=1.0
        )

        morphology = MorphologyComplexity(
            word="test",
            root="test",
            suffixes=[],
            suffix_count=0,
            derivational_depth=0,
            compound_complexity=0.0,
            phonetic_changes=0,
            semantic_ambiguity=0.3,
            overall_complexity=0.2,
        )

        comparison = {"overall_improvement": 0.6}

        recommendations = await service._generate_recommendations(
            irt_params, morphology, comparison
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5
        assert any("kolay" in rec.lower() for rec in recommendations)

    def test_calculate_analysis_confidence(self, service):
        """Analiz güven skoru testi"""
        morphology = MorphologyComplexity(
            word="test",
            root="test",
            suffixes=[],
            suffix_count=0,
            derivational_depth=0,
            compound_complexity=0.0,
            phonetic_changes=0,
            semantic_ambiguity=0.3,
            overall_complexity=0.5,
        )

        # Cok veri ile
        confidence = service._calculate_analysis_confidence(morphology, 100)
        assert 0.3 <= confidence <= 1.0

        # Az veri ile
        confidence = service._calculate_analysis_confidence(morphology, 5)
        assert 0.3 <= confidence <= 1.0

    @pytest.mark.asyncio(loop_scope="function")
    async def test_calculate_irt_probability(self, service):
        """IRT olasılık hesaplama testi"""
        student_ability = 0.5
        irt_params = IRTParameters(
            difficulty=0.0, discrimination=1.0, guessing=0.20, upper_asymptote=1.0
        )

        # Morfoloji ayarlamasi ile
        prob_with_morphology = await service.calculate_irt_probability(
            student_ability, irt_params, morphology_adjustment=True
        )

        # Morfoloji ayarlamasi olmadan
        prob_without_morphology = await service.calculate_irt_probability(
            student_ability, irt_params, morphology_adjustment=False
        )

        assert 0.0 <= prob_with_morphology <= 1.0
        assert 0.0 <= prob_without_morphology <= 1.0

        # Extreme degerler testi
        extreme_ability = 10.0
        prob_extreme = await service.calculate_irt_probability(
            extreme_ability, irt_params, morphology_adjustment=False
        )
        assert prob_extreme > 0.99  # Çok yüksek olasılık

    @pytest.mark.asyncio(loop_scope="function")
    async def test_get_difficulty_recommendation(self, service):
        """Zorluk önerisi testi"""
        current_difficulty = 0.0

        # Yuksek performans - zorluk artirilmali
        new_difficulty, recommendation = await service.get_difficulty_recommendation(
            current_difficulty, 0.9, 0.5
        )
        assert new_difficulty > current_difficulty
        assert "artır" in recommendation.lower()

        # Dusuk performans - zorluk azaltilmali
        new_difficulty, recommendation = await service.get_difficulty_recommendation(
            current_difficulty, 0.2, 0.5
        )
        assert new_difficulty < current_difficulty
        assert "azalt" in recommendation.lower()

        # Dengeli performans
        new_difficulty, recommendation = await service.get_difficulty_recommendation(
            current_difficulty, 0.6, 0.5
        )
        assert "uygun" in recommendation.lower()

    def test_get_service_stats(self, service):
        """Servis istatistikleri testi"""
        stats = service.get_service_stats()

        assert isinstance(stats, dict)
        expected_keys = {
            "service_name",
            "version",
            "features",
            "complexity_weights",
            "turkish_adjustments",
            "supported_standards",
            "supported_models",
        }
        assert set(stats.keys()) == expected_keys

        assert "IRT" in stats["service_name"]
        assert "Morfoloji" in stats["service_name"]
        assert isinstance(stats["features"], list)
        assert len(stats["features"]) > 0

    @pytest.mark.asyncio(loop_scope="function")
    async def test_error_handling(self, service):
        """Hata yönetimi testi"""
        # Gecersiz soru metni
        # SS10.56 ile ayni duzeltme: patch hedefi servisin OKUDUGU isim
        # alanina baglandi ve AsyncMock acikca kullanildi. Eski hali
        # (`core.turkish_nlp_service...`) CI'da devreye girmiyordu; mock
        # calismayinca servis "NLP Error" yerine kendi "kelime bulunamadi"
        # dalina dusuyor ve overall_complexity=0.3 / word='unknown'
        # donduruyordu -- test 0.5 / 'error' bekledigi icin kirmiziydi.
        nlp_mock = MagicMock()
        nlp_mock.analyze_morphology = AsyncMock(side_effect=Exception("NLP Error"))

        with patch("algorithms.irt_morfoloji_service.turkish_nlp_service", nlp_mock):
            result = await service._analyze_turkish_morphology_complexity(
                "invalid text"
            )

            assert nlp_mock.analyze_morphology.called, (
                "analyze_morphology mock'u hic cagrilmadi -- servis gercek "
                "turkish_nlp_service'i kullandi, hata yolu DOGRULANMIYOR"
            )
            # Hata durumunda fallback degerler dondurulmeli
            assert result.overall_complexity == 0.5
            assert result.word == "error"

    def test_global_service_instance(self):
        """Global servis instance testi"""
        assert irt_morfoloji_service is not None
        assert isinstance(irt_morfoloji_service, IRTMorfolojiService)


class TestIRTParameters:
    """IRT Parametreleri Test Sınıfı"""

    def test_irt_parameters_creation(self):
        """IRT parametreleri oluşturma testi"""
        params = IRTParameters(
            difficulty=0.5, discrimination=1.2, guessing=0.20, upper_asymptote=1.0
        )

        assert params.difficulty == 0.5
        assert params.discrimination == 1.2
        assert params.guessing == 0.20
        assert params.upper_asymptote == 1.0

    def test_irt_parameters_validation(self):
        """IRT parametreleri doğrulama testi"""
        # Normal degerler
        params = IRTParameters(
            difficulty=0.0, discrimination=1.0, guessing=0.25, upper_asymptote=1.0
        )

        # Zorluk -3 ile +3 arasinda olmali
        assert -3.0 <= params.difficulty <= 3.0

        # Ayirt edicilik pozitif olmali
        assert params.discrimination > 0

        # Sans faktoru 0-0.5 arasinda olmali
        assert 0.0 <= params.guessing <= 0.5


class TestMorphologyComplexity:
    """Morfolojik Karmaşıklık Test Sınıfı"""

    def test_morphology_complexity_creation(self):
        """Morfolojik karmaşıklık oluşturma testi"""
        complexity = MorphologyComplexity(
            word="öğrenciler",
            root="öğrenci",
            suffixes=["ler"],
            suffix_count=1,
            derivational_depth=0,
            compound_complexity=0.0,
            phonetic_changes=0,
            semantic_ambiguity=0.3,
            overall_complexity=0.4,
        )

        assert complexity.word == "öğrenciler"
        assert complexity.root == "öğrenci"
        assert complexity.suffixes == ["ler"]
        assert complexity.suffix_count == 1
        assert 0.0 <= complexity.overall_complexity <= 1.0


class TestQuestionAnalysis:
    """Soru Analizi Test Sınıfı"""

    def test_question_analysis_creation(self):
        """Soru analizi oluşturma testi"""
        irt_params = IRTParameters(
            difficulty=0.5, discrimination=1.2, guessing=0.20, upper_asymptote=1.0
        )

        morphology = MorphologyComplexity(
            word="test",
            root="test",
            suffixes=[],
            suffix_count=0,
            derivational_depth=0,
            compound_complexity=0.0,
            phonetic_changes=0,
            semantic_ambiguity=0.3,
            overall_complexity=0.4,
        )

        analysis = QuestionAnalysis(
            question_id="test_q1",
            question_text="Test sorusu",
            irt_parameters=irt_params,
            morphology_complexity=morphology,
            adjusted_difficulty=0.6,
            turkish_difficulty_factor=1.2,
            osym_ets_comparison={"osym_match": 0.8},
            recommendations=["Test önerisi"],
            analysis_confidence=0.85,
            metadata={"test": True},
        )

        assert analysis.question_id == "test_q1"
        assert analysis.question_text == "Test sorusu"
        assert isinstance(analysis.irt_parameters, IRTParameters)
        assert isinstance(analysis.morphology_complexity, MorphologyComplexity)
        assert analysis.adjusted_difficulty == 0.6
        assert 0.0 <= analysis.analysis_confidence <= 1.0


@pytest.mark.integration
class TestIRTMorfolojiIntegration:
    """IRT Morfoloji Entegrasyon Testleri"""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_full_analysis_workflow(self):
        """Tam analiz iş akışı testi"""
        service = IRTMorfolojiService()

        # Gercekci Turkce soru
        question_text = """
        Aşağıdaki cümlede kaç tane isim vardır?
        "Öğrencilerimizden bazıları kütüphanede çalışıyorlar."
        A) 2  B) 3  C) 4  D) 5
        """

        student_responses = [
            {
                "student_id": f"s{i}",
                "answer": "B",
                "is_correct": i % 2 == 0,
                "response_time": 30 + i * 5,
            }
            for i in range(20)
        ]

        # SS10.56 ile ayni duzeltme (dosyadaki ucuncu ve son eski-yontem
        # patch'i): servisin OKUDUGU isim alani + acik AsyncMock. Boylece bu
        # dosyada "mock CI'da devreye girmiyor" ailesinden patch kalmadi.
        nlp_mock = MagicMock()
        nlp_mock.analyze_morphology = AsyncMock(
            return_value=MorphologicalAnalysis(
                word="öğrencilerimizden",
                root="öğrenci",
                suffixes=["ler", "imiz", "den"],
                pos_tag="NOUN",
                derivational_depth=1,
                is_compound=False,
                compound_parts=[],
                complexity_score=0.7,
            )
        )

        with patch("algorithms.irt_morfoloji_service.turkish_nlp_service", nlp_mock):
            analysis = await service.analyze_question_irt_morphology(
                question_id="integration_test_1",
                question_text=question_text,
                correct_answer="B",
                student_responses=student_responses,
            )

            # Entegrasyon dogrulamalari
            assert analysis.question_id == "integration_test_1"
            assert analysis.morphology_complexity.overall_complexity > 0
            assert analysis.irt_parameters.difficulty != 0
            assert len(analysis.recommendations) > 0
            assert analysis.analysis_confidence > 0.5
            assert "turkish_optimization" in analysis.metadata
            assert analysis.metadata["turkish_optimization"] is True

    @pytest.mark.performance
    def test_performance_benchmarks(self):
        """Performans benchmark testleri"""
        service = IRTMorfolojiService()

        import time

        # Cok sayida kelime karmasikligi hesaplama
        start_time = time.time()

        for i in range(100):
            mock_analysis = MorphologicalAnalysis(
                word=f"test{i}",
                root=f"test{i}",
                suffixes=["ler", "imiz"],
                pos_tag="NOUN",
                derivational_depth=0,
                is_compound=False,
                compound_parts=[],
                complexity_score=0.5,
            )
            service._calculate_word_complexity(mock_analysis)

        end_time = time.time()
        processing_time = end_time - start_time

        # 100 kelime 1 saniyede islenmeli
        assert processing_time < 1.0

        print(f"100 kelime karmaşıklığı {processing_time:.3f} saniyede hesaplandı")


if __name__ == "__main__":
    # Test calistirma
    pytest.main([__file__, "-v", "--tb=short"])
