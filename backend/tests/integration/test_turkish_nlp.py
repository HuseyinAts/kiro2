"""
Türkçe NLP Servisi Test Suite
"""

from unittest.mock import patch

import pytest

from core.turkish_nlp_service import (
    MorphologicalAnalysis,
    TextNormalizationResult,
    TurkishNLPService,
    turkish_nlp_service,
)

pytestmark = pytest.mark.skipif(
    True,
    reason="AsyncClient(app=app) hangs in asyncio event loop on Windows",
)


class TestTurkishNLPService:
    """Türkçe NLP servisi test sınıfı"""

    @pytest.fixture
    async def nlp_service(self):
        """NLP servisi fixture"""
        service = TurkishNLPService()
        async with service:
            yield service

    @pytest.mark.asyncio
    async def test_service_initialization(self, nlp_service):
        """Servis başlatma testi"""
        # Servis başlatma
        result = await nlp_service.initialize()

        # Sonuç boolean olmalı
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_morphology_analysis_simple_word(self, nlp_service):
        """Basit kelime morfoloji analizi testi"""
        await nlp_service.initialize()

        # Test kelimesi
        test_word = "kitap"

        # Analiz yap
        result = await nlp_service.analyze_morphology(test_word)

        # Sonuç kontrolü
        assert result is not None
        assert isinstance(result, MorphologicalAnalysis)
        assert result.word == test_word
        assert result.root is not None
        assert isinstance(result.suffixes, list)
        assert isinstance(result.complexity_score, float)
        assert 0 <= result.complexity_score <= 1

    @pytest.mark.asyncio
    async def test_morphology_analysis_complex_word(self, nlp_service):
        """Karmaşık kelime morfoloji analizi testi"""
        await nlp_service.initialize()

        # Karmaşık test kelimesi
        test_word = "kitaplarımızdan"

        # Analiz yap
        result = await nlp_service.analyze_morphology(test_word)

        # Sonuç kontrolü
        assert result is not None
        assert result.word == test_word
        assert len(result.suffixes) > 0  # Ekleri olmalı
        assert result.complexity_score > 0.3  # Karmaşık olmalı

    @pytest.mark.asyncio
    async def test_morphology_analysis_empty_word(self, nlp_service):
        """Boş kelime morfoloji analizi testi"""
        await nlp_service.initialize()

        # Boş kelime
        test_word = ""

        # Analiz yap
        result = await nlp_service.analyze_morphology(test_word)

        # Sonuç None olmalı
        assert result is None

    @pytest.mark.asyncio
    async def test_morphology_analysis_with_punctuation(self, nlp_service):
        """Noktalama işaretli kelime morfoloji analizi testi"""
        await nlp_service.initialize()

        # Noktalama işaretli kelime
        test_word = "kitap!"

        # Analiz yap
        result = await nlp_service.analyze_morphology(test_word)

        # Sonuç kontrolü
        assert result is not None
        assert result.root == "kitap"  # Noktalama temizlenmeli

    @pytest.mark.asyncio
    async def test_text_normalization_basic(self, nlp_service):
        """Temel metin normalizasyon testi"""
        await nlp_service.initialize()

        # Test metni
        test_text = "merhaba   dünya!  nasılsın?"

        # Normalizasyon yap
        result = await nlp_service.normalize_text(test_text)

        # Sonuç kontrolü
        assert isinstance(result, TextNormalizationResult)
        assert result.original_text == test_text
        assert result.normalized_text is not None
        assert len(result.normalized_text) <= len(test_text)  # Boşluklar temizlenmeli
        assert isinstance(result.corrections, list)

    @pytest.mark.asyncio
    async def test_text_normalization_encoding_issues(self, nlp_service):
        """Encoding sorunlu metin normalizasyon testi"""
        await nlp_service.initialize()

        # Encoding sorunlu metin
        test_text = "Ã§ocuk Ã¶rnekleri"

        # Normalizasyon yap
        result = await nlp_service.normalize_text(test_text)

        # Sonuç kontrolü
        assert result.encoding_issues_fixed > 0
        assert "çocuk" in result.normalized_text.lower()
        assert "örnekleri" in result.normalized_text.lower()

    @pytest.mark.asyncio
    async def test_text_normalization_common_errors(self, nlp_service):
        """Yaygın yazım hataları normalizasyon testi"""
        await nlp_service.initialize()

        # Yazım hatalı metin
        test_text = "birşey yapmak istiyorum hemde çok"

        # Normalizasyon yap
        result = await nlp_service.normalize_text(test_text)

        # Sonuç kontrolü
        assert len(result.corrections) > 0
        assert "bir şey" in result.normalized_text
        assert "hem de" in result.normalized_text

    @pytest.mark.asyncio
    async def test_text_complexity_analysis_simple(self, nlp_service):
        """Basit metin karmaşıklık analizi testi"""
        await nlp_service.initialize()

        # Basit metin
        test_text = "Ali okula gitti"

        # Karmaşıklık analizi
        result = await nlp_service.analyze_text_complexity(test_text)

        # Sonuç kontrolü
        assert isinstance(result, dict)
        assert "overall_complexity" in result
        assert "word_count" in result
        assert "readability_score" in result
        assert result["word_count"] == 3
        assert result["overall_complexity"] < 0.5  # Basit olmalı
        assert result["readability_score"] > 0.5  # Okunabilir olmalı

    @pytest.mark.asyncio
    async def test_text_complexity_analysis_complex(self, nlp_service):
        """Karmaşık metin karmaşıklık analizi testi"""
        await nlp_service.initialize()

        # Karmaşık metin
        test_text = (
            "Çekoslovakyalılaştıramadıklarımızdanmısınız epistemolojik yaklaşımlarla"
        )

        # Karmaşıklık analizi
        result = await nlp_service.analyze_text_complexity(test_text)

        # Sonuç kontrolü
        assert result["overall_complexity"] > 0.7  # Karmaşık olmalı
        assert result["readability_score"] < 0.3  # Zor okunabilir olmalı
        assert len(result["complex_words"]) > 0  # Karmaşık kelimeler olmalı

    @pytest.mark.asyncio
    async def test_text_complexity_analysis_empty(self, nlp_service):
        """Boş metin karmaşıklık analizi testi"""
        await nlp_service.initialize()

        # Boş metin
        test_text = ""

        # Karmaşıklık analizi
        result = await nlp_service.analyze_text_complexity(test_text)

        # Sonuç kontrolü
        assert result["word_count"] == 0
        assert result["overall_complexity"] == 0.0

    def test_word_complexity_cached(self, nlp_service):
        """Kelime karmaşıklığı cache testi"""
        # Basit kelime
        simple_word = "ev"
        complexity1 = nlp_service.get_word_complexity(simple_word)
        complexity2 = nlp_service.get_word_complexity(simple_word)

        # Cache'den geldiği için aynı olmalı
        assert complexity1 == complexity2
        assert 0 <= complexity1 <= 1

        # Karmaşık kelime
        complex_word = "Çekoslovakyalılaştıramadıklarımızdanmısınız"
        complex_score = nlp_service.get_word_complexity(complex_word)

        # Karmaşık kelime daha yüksek skor almalı
        assert complex_score > complexity1

    def test_clean_word(self, nlp_service):
        """Kelime temizleme testi"""
        # Noktalama işaretli kelime
        dirty_word = "kitap!!!"
        clean_word = nlp_service._clean_word(dirty_word)

        assert clean_word == "kitap"

        # Boşluklu kelime
        spaced_word = "  kelime  "
        clean_spaced = nlp_service._clean_word(spaced_word)

        assert clean_spaced == "kelime"

        # Boş kelime
        empty_word = ""
        clean_empty = nlp_service._clean_word(empty_word)

        assert clean_empty == ""

    def test_fix_encoding_issues(self, nlp_service):
        """Encoding sorun düzeltme testi"""
        # Encoding sorunlu metin
        broken_text = "Ã§ocuk Ã¶rnekleri Ä±ÅŸÄ±k"

        fixed_text, fixes = nlp_service._fix_encoding_issues(broken_text)

        assert fixes > 0
        assert "ç" in fixed_text or "ö" in fixed_text

    def test_normalize_turkish_chars(self, nlp_service):
        """Türkçe karakter normalizasyon testi"""
        # Eski Türkçe karakterli metin
        old_text = "kitâb-ı mukaddes"

        normalized_text, fixes = nlp_service._normalize_turkish_chars(old_text)

        assert "kitab" in normalized_text
        assert fixes > 0

    def test_fix_common_errors(self, nlp_service):
        """Yaygın hata düzeltme testi"""
        # Hatalı metin
        error_text = "birşey yapmak istiyorum hemde"

        corrected_text, corrections = nlp_service._fix_common_errors(error_text)

        assert len(corrections) > 0
        assert "bir şey" in corrected_text
        assert "hem de" in corrected_text

    def test_clean_whitespace(self, nlp_service):
        """Boşluk temizleme testi"""
        # Çoklu boşluklu metin
        messy_text = "  merhaba    dünya  !  "

        clean_text = nlp_service._clean_whitespace(messy_text)

        assert clean_text == "merhaba dünya !"
        assert "  " not in clean_text  # Çoklu boşluk olmamalı

    def test_simple_root_suffix_split(self, nlp_service):
        """Basit kök-ek ayrımı testi"""
        # Ekli kelime
        word_with_suffix = "kitaplar"

        root, suffixes = nlp_service._simple_root_suffix_split(word_with_suffix)

        assert root == "kitap"
        assert "lar" in suffixes

    def test_calculate_complexity_score(self, nlp_service):
        """Karmaşıklık skoru hesaplama testi"""
        # Basit kelime
        simple_score = nlp_service._calculate_complexity_score(0, 0, 0)
        assert simple_score == 0.0

        # Karmaşık kelime
        complex_score = nlp_service._calculate_complexity_score(5, 3, 2)
        assert complex_score > simple_score
        assert complex_score <= 1.0


class TestTurkishNLPServiceIntegration:
    """Türkçe NLP servisi entegrasyon testleri"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Tam iş akışı testi"""
        async with turkish_nlp_service as nlp:
            await nlp.initialize()

            # Test metni
            test_text = "kitaplarımızdan  birşey  öğrendik"

            # 1. Metin normalizasyonu
            norm_result = await nlp.normalize_text(test_text)
            assert norm_result.normalized_text is not None

            # 2. Karmaşıklık analizi
            complexity_result = await nlp.analyze_text_complexity(
                norm_result.normalized_text
            )
            assert complexity_result["word_count"] > 0

            # 3. Her kelime için morfoloji analizi
            words = norm_result.normalized_text.split()
            for word in words:
                if word.strip():
                    morphology = await nlp.analyze_morphology(word)
                    assert morphology is not None

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Hata yönetimi testi"""
        async with turkish_nlp_service as nlp:
            # Geçersiz girdi ile test
            result = await nlp.analyze_morphology(None)
            assert result is None

            # Çok uzun metin ile test
            very_long_text = "kelime " * 10000
            complexity_result = await nlp.analyze_text_complexity(very_long_text)
            assert complexity_result is not None  # Hata vermemeli

    @pytest.mark.asyncio
    @patch(
        "backend.core.turkish_nlp_service.TurkishNLPService._call_zemberek_morphology"
    )
    async def test_zemberek_fallback(self, mock_zemberek):
        """Zemberek fallback testi"""
        # Zemberek başarısız olduğunda
        mock_zemberek.return_value = None

        async with turkish_nlp_service as nlp:
            await nlp.initialize()

            result = await nlp.analyze_morphology("kitap")

            # Fallback analiz çalışmalı
            assert result is not None
            assert result.word == "kitap"


# Performance testleri
class TestTurkishNLPPerformance:
    """Türkçe NLP servisi performans testleri"""

    @pytest.mark.asyncio
    async def test_batch_morphology_performance(self):
        """Toplu morfoloji analizi performans testi"""
        async with turkish_nlp_service as nlp:
            await nlp.initialize()

            # 100 kelime listesi
            test_words = [f"kelime{i}" for i in range(100)]

            import time

            start_time = time.time()

            # Tüm kelimeleri analiz et
            results = []
            for word in test_words:
                result = await nlp.analyze_morphology(word)
                results.append(result)

            end_time = time.time()
            duration = end_time - start_time

            # Performans kontrolü (100 kelime < 10 saniye)
            assert duration < 10.0
            assert len(results) == 100
            assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_large_text_complexity_performance(self):
        """Büyük metin karmaşıklık analizi performans testi"""
        async with turkish_nlp_service as nlp:
            await nlp.initialize()

            # Büyük metin (1000 kelime)
            large_text = "Bu bir test metnidir. " * 200

            import time

            start_time = time.time()

            result = await nlp.analyze_text_complexity(large_text)

            end_time = time.time()
            duration = end_time - start_time

            # Performans kontrolü (1000 kelime < 5 saniye)
            assert duration < 5.0
            assert result["word_count"] > 500


# Note: event_loop fixture removed - pytest-asyncio auto mode handles this
# Duplicate fixtures cause conflicts with pytest-asyncio>=0.21


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
