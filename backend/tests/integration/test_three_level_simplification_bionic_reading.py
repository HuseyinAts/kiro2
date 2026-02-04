"""
3 Seviyeli Türkçe Metin Basitleştirme ve Türkçe Bionic Reading Test Suite
Dünyada İlk Türkçe Metin Basitleştirme ve Disleksi Desteği

Bu test dosyası, 3 seviyeli metin basitleştirme ve Türkçe Bionic Reading
özelliklerini kapsamlı şekilde test eder.

Requirements: 10.5, 10.6, 12.5
"""

import asyncio
import re
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from algorithms.three_level_turkish_simplification import (
    ThreeLevelTurkishSimplification,
)
from algorithms.turkish_bionic_reading import TurkishBionicReading
from models.revolutionary_models import SimplificationResult


class TestLexicalSimplification:
    """Seviye 1: Kelime seviyesi basitleştirme testleri"""

    @pytest.fixture
    def simplification_system(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.asyncio
    async def test_ottoman_academic_word_replacement(self, simplification_system):
        """Osmanlıca/akademik kelime değiştirme"""

        ottoman_text = (
            "Bu mütalaa çok önemli bir tetkik gerektiriyor ve münasebet kurmalıyız."
        )

        simplified = await simplification_system._lexical_simplification(ottoman_text)

        # Osmanlıca kelimeler değiştirilmeli
        assert "mütalaa" not in simplified
        assert "tetkik" not in simplified
        assert "münasebet" not in simplified

        # Modern Türkçe karşılıkları bulunmalı
        assert "okuma" in simplified or "görüş" in simplified
        assert "inceleme" in simplified or "araştırma" in simplified
        assert "ilişki" in simplified or "bağlantı" in simplified

    @pytest.mark.asyncio
    async def test_foreign_origin_word_replacement(self, simplification_system):
        """Yabancı kökenli kelime değiştirme"""

        foreign_text = (
            "Bu proje implementasyonu optimize edilmeli ve performans analiz edilmeli."
        )

        with patch.object(
            simplification_system, "_get_turkish_equivalents"
        ) as mock_equivalents:
            mock_equivalents.return_value = {
                "implementasyon": "uygulama",
                "optimize": "eniyile",
                "performans": "başarım",
                "analiz": "çözümleme",
            }

            simplified = await simplification_system._lexical_simplification(
                foreign_text
            )

        # Türkçe karşılıklar kullanılmalı
        assert "uygulama" in simplified
        assert "eniyile" in simplified or "iyileştir" in simplified
        assert "başarım" in simplified or "verim" in simplified

    @pytest.mark.asyncio
    async def test_technical_term_simplification(self, simplification_system):
        """Teknik terim basitleştirme"""

        technical_text = (
            "Algoritma optimizasyonu için heuristik metodoloji kullanılacak."
        )

        with patch.object(
            simplification_system, "_get_turkish_equivalents"
        ) as mock_equivalents:
            mock_equivalents.return_value = {
                "algoritma": "işlem dizisi",
                "optimizasyon": "iyileştirme",
                "heuristik": "deneyimsel",
                "metodoloji": "yöntem",
            }

            simplified = await simplification_system._lexical_simplification(
                technical_text
            )

        # Basit terimler kullanılmalı
        assert "işlem dizisi" in simplified or "yöntem" in simplified
        assert "iyileştirme" in simplified
        assert "deneyimsel" in simplified or "tecrübeye dayalı" in simplified

    @pytest.mark.asyncio
    async def test_preserve_simple_words(self, simplification_system):
        """Basit kelimeleri koruma"""

        simple_text = "Bu ev çok güzel ve büyük bir bahçesi var."

        simplified = await simplification_system._lexical_simplification(simple_text)

        # Basit kelimeler değişmemeli
        assert "ev" in simplified
        assert "güzel" in simplified
        assert "büyük" in simplified
        assert "bahçe" in simplified


class TestSyntacticSimplification:
    """Seviye 2: Cümle yapısı basitleştirme testleri"""

    @pytest.fixture
    def simplification_system(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.asyncio
    async def test_complex_sentence_splitting(self, simplification_system):
        """Karmaşık cümle bölme"""

        complex_sentence = (
            "Okulda okuduğum kitabı eve gelince tekrar okudum ve çok beğendim."
        )

        simplified = await simplification_system._syntactic_simplification(
            complex_sentence
        )

        # Cümle bölünmeli
        sentences = [s.strip() for s in simplified.split(".") if s.strip()]
        assert len(sentences) >= 2

        # Her cümle daha basit olmalı
        for sentence in sentences:
            # Sıfat cümlesi kalıpları olmamalı
            assert not re.search(r"\w+(dığı|diği|duğu|düğü)\s+\w+", sentence)

    @pytest.mark.asyncio
    async def test_relative_clause_simplification(self, simplification_system):
        """Sıfat cümlesi basitleştirme"""

        relative_clause_text = "Dün aldığım kitabı bugün okudum."

        with patch.object(
            simplification_system, "_split_complex_turkish_sentence"
        ) as mock_split:
            mock_split.return_value = ["Dün bir kitap aldım", "Bu kitabı bugün okudum"]

            simplified = await simplification_system._syntactic_simplification(
                relative_clause_text
            )

        # İki ayrı cümle olmalı
        sentences = [s.strip() for s in simplified.split(".") if s.strip()]
        assert len(sentences) >= 2

    @pytest.mark.asyncio
    async def test_compound_sentence_breaking(self, simplification_system):
        """Birleşik cümle ayırma"""

        compound_text = "Hava güzel olduğu için parka gittik ve orada oynadık."

        simplified = await simplification_system._syntactic_simplification(
            compound_text
        )

        # Bağlaçlarla ayrılmış cümleler bölünmeli
        sentences = [s.strip() for s in simplified.split(".") if s.strip()]

        # En az 2 cümle olmalı
        assert len(sentences) >= 2

        # Bağlaçlar kaldırılmalı veya basitleştirilmeli
        full_text = simplified.lower()
        complex_conjunctions = ["olduğu için", "olmasına rağmen", "olduğunda"]

        for conj in complex_conjunctions:
            if conj in compound_text.lower():
                assert conj not in full_text or len(sentences) > 1

    @pytest.mark.asyncio
    async def test_adverbial_clause_simplification(self, simplification_system):
        """Zarf cümlesi basitleştirme"""

        adverbial_text = "Çalışarak başarılı oldum ve mutlu oldum."

        simplified = await simplification_system._syntactic_simplification(
            adverbial_text
        )

        # Zarf-fiil yapıları basitleştirilmeli
        sentences = [s.strip() for s in simplified.split(".") if s.strip()]

        # Daha açık ifadeler kullanılmalı
        full_text = simplified.lower()
        assert "çalış" in full_text
        assert "başarılı" in full_text


class TestSemanticRestructuring:
    """Seviye 3: Anlam korunumu ile yeniden yazma testleri"""

    @pytest.fixture
    def simplification_system(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.asyncio
    async def test_metaphor_to_concrete_conversion(self, simplification_system):
        """Metafor → somut ifade dönüşümü"""

        metaphorical_text = "Bilgi güçtür ve zamanın kıymetini bilmek gerekir."

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "text": "Çok şey bilmek insana yardımcı olur ve zamanı iyi kullanmak önemlidir.",
            }

            simplified = await simplification_system._semantic_restructuring(
                metaphorical_text, "intermediate"
            )

        # Metaforlar somut ifadelere dönüşmeli
        assert "yardımcı olur" in simplified or "faydalıdır" in simplified
        assert "iyi kullanmak" in simplified or "verimli kullanmak" in simplified

    @pytest.mark.asyncio
    async def test_abstract_to_concrete_examples(self, simplification_system):
        """Soyut → somut örnek dönüşümü"""

        abstract_text = "Demokrasi önemli bir yönetim şeklidir."

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "text": "Demokrasi, halkın seçimlerle yöneticilerini seçtiği bir sistemdir.",
            }

            simplified = await simplification_system._semantic_restructuring(
                abstract_text, "beginner"
            )

        # Somut açıklama eklenmeli
        assert "seçim" in simplified or "oy" in simplified
        assert "halk" in simplified or "vatandaş" in simplified

    @pytest.mark.asyncio
    async def test_passive_to_active_voice(self, simplification_system):
        """Pasif → aktif çatı dönüşümü"""

        passive_text = "Kitap öğrenci tarafından okundu."

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {"success": True, "text": "Öğrenci kitabı okudu."}

            simplified = await simplification_system._semantic_restructuring(
                passive_text, "intermediate"
            )

        # Aktif çatı kullanılmalı
        assert "öğrenci" in simplified.lower()
        assert "okudu" in simplified.lower()
        assert "tarafından" not in simplified.lower()

    @pytest.mark.asyncio
    async def test_long_sentence_breaking(self, simplification_system):
        """Uzun cümle kırma"""

        long_text = "Türkiye'nin en büyük şehri olan İstanbul, tarihi ve kültürel zenginlikleri ile dünya çapında ünlü bir şehirdir ve her yıl milyonlarca turist tarafından ziyaret edilmektedir."

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "text": "İstanbul Türkiye'nin en büyük şehridir. Bu şehir tarihi ve kültürel zenginlikleri ile ünlüdür. Her yıl milyonlarca turist İstanbul'u ziyaret eder.",
            }

            simplified = await simplification_system._semantic_restructuring(
                long_text, "intermediate"
            )

        # Kısa cümleler olmalı
        sentences = [s.strip() for s in simplified.split(".") if s.strip()]
        assert len(sentences) >= 2

        # Her cümle daha kısa olmalı
        for sentence in sentences:
            assert len(sentence.split()) <= 15  # Maksimum 15 kelime


class TestThreeLevelIntegration:
    """3 seviyeli entegrasyon testleri"""

    @pytest.fixture
    def simplification_system(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.asyncio
    async def test_complete_three_level_process(self, simplification_system):
        """Tam 3 seviyeli süreç"""

        complex_text = "Çekoslovakyalılaştıramadıklarımızdanmısınız sorusunun mütalaa edilmesi, bu konudaki tetkiklerin derinlemesine analiz edilmesini gerektirmektedir."

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "text": "Bu soruyu incelemek gerekiyor. Konu hakkında araştırmalar yapılmalı.",
            }

            result = await simplification_system.revolutionary_simplification(
                complex_text, "intermediate"
            )

        # Sonuç yapısı kontrolü
        assert isinstance(result, SimplificationResult)
        assert hasattr(result, "original_text")
        assert hasattr(result, "level1_lexical")
        assert hasattr(result, "level2_syntactic")
        assert hasattr(result, "level3_semantic")
        assert hasattr(result, "complexity_reduction")
        assert hasattr(result, "readability_score")

        # Orijinal metin korunmuş
        assert result.original_text == complex_text

        # Her seviye daha basit olmalı
        assert len(result.level3_semantic) <= len(result.original_text)
        assert result.complexity_reduction > 0

    @pytest.mark.asyncio
    async def test_target_level_adaptation(self, simplification_system):
        """Hedef seviye adaptasyonu"""

        text = "Quantum fiziği çok karmaşık bir konudur."

        # Başlangıç seviyesi
        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "text": "Atom fiziği çok zor bir konudur.",
            }

            beginner_result = await simplification_system.revolutionary_simplification(
                text, "beginner"
            )

        # Orta seviye
        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "text": "Kuantum fiziği karmaşık bir bilim dalıdır.",
            }

            intermediate_result = (
                await simplification_system.revolutionary_simplification(
                    text, "intermediate"
                )
            )

        # Başlangıç seviyesi daha basit olmalı
        assert len(beginner_result.level3_semantic.split()) <= len(
            intermediate_result.level3_semantic.split()
        )

    @pytest.mark.asyncio
    async def test_complexity_reduction_calculation(self, simplification_system):
        """Karmaşıklık azaltma hesaplama"""

        complex_text = (
            "Antikonstitüsyonelleştiricileştiriveremeyebileceklerimizdenmişsinizcesine"
        )

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {"success": True, "text": "Anayasaya aykırı"}

            result = await simplification_system.revolutionary_simplification(
                complex_text, "beginner"
            )

        # Karmaşıklık önemli ölçüde azalmalı
        assert result.complexity_reduction > 0.5  # En az %50 azalma
        assert result.readability_score > 0.7  # Yüksek okunabilirlik


class TestTurkishBionicReading:
    """Türkçe Bionic Reading testleri"""

    @pytest.fixture
    def bionic_system(self):
        return TurkishBionicReading()

    @pytest.mark.asyncio
    async def test_root_suffix_separation(self, bionic_system):
        """Kök-ek ayrımı"""

        with patch.object(bionic_system.zemberek, "analyze") as mock_analyze:
            mock_analyze.return_value = Mock(
                root="çocuk", suffixes=["lar"], is_compound=False
            )

            result = await bionic_system.turkish_bionic_reading("çocuklar")

        # Sadece kök bold olmalı
        assert "**çoc**" in result or "**çocu**" in result
        # Ek bold olmamalı
        assert "**lar**" not in result
        assert "lar" in result  # Ek korunmalı ama bold değil

    @pytest.mark.asyncio
    async def test_compound_word_handling(self, bionic_system):
        """Birleşik kelime işleme"""

        with patch.object(bionic_system.zemberek, "analyze") as mock_analyze:
            mock_analyze.return_value = Mock(
                root="başbakan",
                suffixes=[],
                is_compound=True,
                compound_parts=["baş", "bakan"],
            )

            result = await bionic_system.turkish_bionic_reading("başbakan")

        # Birleşik kelimenin ilk kısmı bold olmalı
        assert "**baş**" in result or "**başb**" in result

    @pytest.mark.asyncio
    async def test_punctuation_preservation(self, bionic_system):
        """Noktalama işareti koruma"""

        with patch.object(bionic_system.zemberek, "analyze") as mock_analyze:
            mock_analyze.return_value = Mock(
                root="merhaba", suffixes=[], is_compound=False
            )

            result = await bionic_system.turkish_bionic_reading("merhaba!")

        # Noktalama korunmalı
        assert result.endswith("!")
        assert "**mer**" in result or "**merh**" in result

    @pytest.mark.asyncio
    async def test_short_word_handling(self, bionic_system):
        """Kısa kelime işleme"""

        short_words = ["ev", "su", "el"]

        for word in short_words:
            result = await bionic_system.turkish_bionic_reading(word)

            # Çok kısa kelimeler bold yapılmamalı
            if len(word) < 3:
                assert "**" not in result
                assert result == word

    @pytest.mark.asyncio
    async def test_sentence_bionic_conversion(self, bionic_system):
        """Cümle Bionic dönüşümü"""

        sentence = "Çocuklar bahçede oynuyorlar"

        with patch.object(bionic_system.zemberek, "analyze") as mock_analyze:
            # Her kelime için farklı analiz döndür
            def side_effect(word):
                analyses = {
                    "çocuklar": Mock(root="çocuk", suffixes=["lar"], is_compound=False),
                    "bahçede": Mock(root="bahçe", suffixes=["de"], is_compound=False),
                    "oynuyorlar": Mock(
                        root="oyna", suffixes=["yor", "lar"], is_compound=False
                    ),
                }
                return analyses.get(
                    word.lower(), Mock(root=word, suffixes=[], is_compound=False)
                )

            mock_analyze.side_effect = side_effect

            result = await bionic_system.turkish_bionic_reading(sentence)

        # Her kelime işlenmiş olmalı
        words = result.split()
        assert len(words) == 3

        # Bold formatı uygulanmış olmalı
        assert "**" in result

    def test_punctuation_separation_utility(self, bionic_system):
        """Noktalama ayırma yardımcı fonksiyonu"""

        test_cases = [
            ("merhaba!", "merhaba", "!"),
            ("ne?!.", "ne", "?!."),
            ("test", "test", ""),
            ("kelime,", "kelime", ","),
            ("son;", "son", ";"),
        ]

        for input_word, expected_clean, expected_punct in test_cases:
            clean, punct = bionic_system._separate_punctuation(input_word)
            assert clean == expected_clean
            assert punct == expected_punct


class TestDyslexiaSupport:
    """Disleksi desteği testleri"""

    @pytest.fixture
    def bionic_system(self):
        return TurkishBionicReading()

    @pytest.mark.asyncio
    async def test_reading_speed_improvement(self, bionic_system):
        """Okuma hızı iyileştirme"""

        # Uzun metin
        long_text = "Türkiye Cumhuriyeti Anayasası'nın birinci maddesine göre Türkiye devleti bir cumhuriyettir"

        with patch.object(bionic_system.zemberek, "analyze") as mock_analyze:
            mock_analyze.return_value = Mock(
                root="test", suffixes=[], is_compound=False
            )

            bionic_text = await bionic_system.turkish_bionic_reading(long_text)

        # Bold kelimeler okuma hızını artırmalı
        bold_count = bionic_text.count("**") // 2  # Çift ** = 1 bold kelime
        total_words = len(long_text.split())

        # Çoğu kelime bold formatında olmalı
        assert bold_count >= total_words * 0.7  # En az %70'i

    @pytest.mark.asyncio
    async def test_cognitive_load_reduction(self, bionic_system):
        """Bilişsel yük azaltma"""

        # Karmaşık kelimeler
        complex_words = [
            "antikonstitüsyonelleştiricileştiriveremeyebileceklerimizdenmişsinizcesine",
            "çekoslovakyalılaştıramadıklarımızdanmısınız",
            "muvaffakiyetsizleştiricileştiriveremeyebileceklerimizdenmişsinizcesine",
        ]

        for word in complex_words:
            with patch.object(bionic_system.zemberek, "analyze") as mock_analyze:
                mock_analyze.return_value = Mock(
                    root=word[:10],  # İlk 10 karakter kök
                    suffixes=[word[10:]],  # Geri kalanı ek
                    is_compound=False,
                )

                result = await bionic_system.turkish_bionic_reading(word)

            # Sadece kök kısmı bold olmalı (bilişsel yük azaltma)
            bold_parts = re.findall(r"\*\*(.*?)\*\*", result)
            assert len(bold_parts) == 1  # Sadece bir bold kısım

            # Bold kısım kelime başında olmalı
            assert result.startswith("**")

    @pytest.mark.asyncio
    async def test_turkish_specific_dyslexia_features(self, bionic_system):
        """Türkçe'ye özel disleksi özellikleri"""

        # Türkçe'de sık karıştırılan harfler
        confusing_words = [
            "bağımsızlık",  # b/d karışıklığı
            "değişiklik",  # d/b karışıklığı
            "gelişmek",  # g/ğ karışıklığı
            "öğrenmek",  # ö/o karışıklığı
        ]

        for word in confusing_words:
            with patch.object(bionic_system.zemberek, "analyze") as mock_analyze:
                mock_analyze.return_value = Mock(
                    root=word.split("ı")[0] if "ı" in word else word[:5],
                    suffixes=[],
                    is_compound=False,
                )

                result = await bionic_system.turkish_bionic_reading(word)

            # İlk harfler bold olmalı (karışıklığı önlemek için)
            assert result.startswith("**")

            # Bold kısım çok uzun olmamalı (aşırı vurgu önleme)
            bold_parts = re.findall(r"\*\*(.*?)\*\*", result)
            if bold_parts:
                assert len(bold_parts[0]) <= 4  # Maksimum 4 karakter


class TestPerformanceAndScalability:
    """Performans ve ölçeklenebilirlik testleri"""

    @pytest.fixture
    def simplification_system(self):
        return ThreeLevelTurkishSimplification()

    @pytest.fixture
    def bionic_system(self):
        return TurkishBionicReading()

    @pytest.mark.asyncio
    async def test_batch_simplification_performance(self, simplification_system):
        """Toplu basitleştirme performansı"""

        # 50 metin
        texts = [
            f"Bu çok karmaşık bir metin örneği {i} numaralı deneme." for i in range(50)
        ]

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "text": "Bu basit bir metin örneği.",
            }

            start_time = datetime.now()

            # Paralel işlem
            tasks = [
                simplification_system.revolutionary_simplification(text, "intermediate")
                for text in texts
            ]

            results = await asyncio.gather(*tasks)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

        # 50 metin 10 saniyede basitleştirilmeli
        assert duration < 10.0
        assert len(results) == 50

        # Tüm sonuçlar geçerli
        for result in results:
            assert isinstance(result, SimplificationResult)

    @pytest.mark.asyncio
    async def test_bionic_reading_batch_performance(self, bionic_system):
        """Toplu Bionic Reading performansı"""

        # 100 cümle
        sentences = [
            f"Bu test cümlesi {i} numaralı örnek metindir." for i in range(100)
        ]

        with patch.object(bionic_system.zemberek, "analyze") as mock_analyze:
            mock_analyze.return_value = Mock(
                root="test", suffixes=[], is_compound=False
            )

            start_time = datetime.now()

            # Paralel işlem
            tasks = [
                bionic_system.turkish_bionic_reading(sentence) for sentence in sentences
            ]

            results = await asyncio.gather(*tasks)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

        # 100 cümle 3 saniyede işlenmeli
        assert duration < 3.0
        assert len(results) == 100

        # Tüm sonuçlar bold formatı içermeli
        for result in results:
            assert "**" in result

    @pytest.mark.asyncio
    async def test_memory_efficiency_large_texts(self, simplification_system):
        """Büyük metinler bellek verimliliği"""

        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 10KB metin (çok uzun)
        large_text = "Bu çok uzun bir metin örneğidir. " * 500

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {"success": True, "text": "Bu basit bir metin."}

            # 10 büyük metin işle
            for i in range(10):
                await simplification_system.revolutionary_simplification(
                    large_text, "intermediate"
                )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Bellek artışı 50MB'dan az olmalı
        assert memory_increase < 50


class TestErrorHandlingAndEdgeCases:
    """Hata işleme ve sınır durumları testleri"""

    @pytest.fixture
    def simplification_system(self):
        return ThreeLevelTurkishSimplification()

    @pytest.fixture
    def bionic_system(self):
        return TurkishBionicReading()

    @pytest.mark.asyncio
    async def test_empty_text_handling(self, simplification_system):
        """Boş metin işleme"""

        empty_texts = ["", " ", "\n", "\t"]

        for text in empty_texts:
            with patch("core.llm_service.generate") as mock_llm:
                mock_llm.return_value = {"success": True, "text": ""}

                result = await simplification_system.revolutionary_simplification(
                    text, "intermediate"
                )

            # Boş metin için geçerli sonuç
            assert isinstance(result, SimplificationResult)
            assert result.original_text == text

    @pytest.mark.asyncio
    async def test_llm_service_failure_resilience(self, simplification_system):
        """LLM servis arızası dayanıklılığı"""

        text = "Test metni"

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {"success": False, "error": "API hatası"}

            result = await simplification_system.revolutionary_simplification(
                text, "intermediate"
            )

        # Fallback mekanizması çalışmalı
        assert isinstance(result, SimplificationResult)
        assert result.level3_semantic == text  # Fallback: orijinal metin

    @pytest.mark.asyncio
    async def test_zemberek_failure_resilience(self, bionic_system):
        """Zemberek arızası dayanıklılığı"""

        with patch.object(
            bionic_system.zemberek, "analyze", side_effect=Exception("Zemberek hatası")
        ):
            result = await bionic_system.turkish_bionic_reading("test kelimesi")

        # Fallback mekanizması çalışmalı
        assert "**" in result  # Basit bold formatı uygulanmalı
        assert "test" in result
        assert "kelimesi" in result

    @pytest.mark.asyncio
    async def test_extremely_long_text_handling(self, simplification_system):
        """Aşırı uzun metin işleme"""

        # 100KB metin
        very_long_text = "Bu çok uzun bir metin örneğidir. " * 2000

        with patch("core.llm_service.generate") as mock_llm:
            mock_llm.return_value = {"success": True, "text": "Bu basit bir metin."}

            # Timeout kontrolü
            start_time = datetime.now()

            result = await simplification_system.revolutionary_simplification(
                very_long_text, "intermediate"
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

        # Çok uzun metin bile makul sürede işlenmeli
        assert duration < 30.0  # 30 saniye limit
        assert isinstance(result, SimplificationResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
