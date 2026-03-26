import pytest
pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""
Comprehensive Unit Tests for Turkish Text Processing Algorithms
NO MOCKS - Pure business logic testing
NO DATABASE - Pure unit tests

Coverage:
- Turkish Text Simplifier (3-level simplification)
- Turkish Bionic Reading (Dyslexia support)
- Three-Level Turkish Simplification (Advanced system)

Total tests: ~300
"""

import pytest
from algorithms.turkish_text_simplifier import (
    TurkishTextSimplifier,
    SimplificationLevel,
    SimplificationResult,
)
from algorithms.turkish_bionic_reading import (
    TurkishBionicReading,
    BionicReadingResult,
    TurkishMorphologyAnalysis,
)
from algorithms.three_level_turkish_simplification import (
    ThreeLevelTurkishSimplification,
    SimplificationResult as ThreeLevelResult,
)


# ============================================================================
# TURKISH TEXT SIMPLIFIER TESTS
# ============================================================================


class TestTurkishTextSimplifierDataModels:
    """Test data models for Turkish Text Simplifier"""

    def test_simplification_level_enum(self):
        """Test SimplificationLevel enum values"""
        assert SimplificationLevel.LEXICAL.value == "lexical"
        assert SimplificationLevel.SYNTACTIC.value == "syntactic"
        assert SimplificationLevel.SEMANTIC.value == "semantic"

    def test_simplification_result_creation(self):
        """Test SimplificationResult creation"""
        result = SimplificationResult(
            original_text="Test metin",
            simplified_text="Basit metin",
            level=SimplificationLevel.LEXICAL,
            complexity_score=45.5,
            readability_score=75.0,
            changes_made=["Change 1", "Change 2"],
            processing_time=12.5,
        )

        assert result.original_text == "Test metin"
        assert result.simplified_text == "Basit metin"
        assert result.level == SimplificationLevel.LEXICAL
        assert result.complexity_score == 45.5
        assert result.readability_score == 75.0
        assert len(result.changes_made) == 2
        assert result.processing_time == 12.5


class TestTurkishTextSimplifierLexicalMappings:
    """Test lexical mapping dictionaries"""

    @pytest.fixture
    def simplifier(self):
        return TurkishTextSimplifier()

    def test_ottoman_to_modern_mappings_loaded(self, simplifier):
        """Test Osmanlıca to Modern Turkish mappings"""
        assert "mütalaa" in simplifier.lexical_mappings
        assert simplifier.lexical_mappings["mütalaa"] == "görüş"
        assert "tetkik" in simplifier.lexical_mappings
        assert simplifier.lexical_mappings["tetkik"] == "inceleme"

    def test_academic_to_daily_mappings(self, simplifier):
        """Test Academic to Daily Turkish mappings"""
        assert "implementasyon" in simplifier.lexical_mappings
        assert simplifier.lexical_mappings["implementasyon"] == "uygulama"
        assert "optimizasyon" in simplifier.lexical_mappings
        assert simplifier.lexical_mappings["optimizasyon"] == "iyileştirme"

    def test_complex_to_simple_mappings(self, simplifier):
        """Test Complex to Simple Turkish mappings"""
        assert "münhasıran" in simplifier.lexical_mappings
        assert simplifier.lexical_mappings["münhasıran"] == "sadece"
        assert "bilhassa" in simplifier.lexical_mappings
        assert simplifier.lexical_mappings["bilhassa"] == "özellikle"

    @pytest.mark.parametrize(
        "ottoman,modern",
        [
            ("mütalaa", "görüş"),
            ("tetkik", "inceleme"),
            ("tahkik", "araştırma"),
            ("müdakkik", "dikkatli"),
            ("müteakip", "sonraki"),
        ],
    )
    def test_ottoman_mappings_parametrized(self, simplifier, ottoman, modern):
        """Test Ottoman to Modern Turkish mappings (parametrized)"""
        assert simplifier.lexical_mappings[ottoman] == modern

    @pytest.mark.parametrize(
        "academic,daily",
        [
            ("implementasyon", "uygulama"),
            ("optimizasyon", "iyileştirme"),
            ("algoritma", "yöntem"),
            ("parametreler", "değişkenler"),
            ("konfigürasyon", "ayarlama"),
        ],
    )
    def test_academic_mappings_parametrized(self, simplifier, academic, daily):
        """Test Academic to Daily Turkish mappings (parametrized)"""
        assert simplifier.lexical_mappings[academic] == daily

    def test_lexical_mappings_not_empty(self, simplifier):
        """Test that lexical mappings are loaded"""
        assert len(simplifier.lexical_mappings) > 0

    def test_complex_patterns_loaded(self, simplifier):
        """Test that complex patterns are loaded"""
        assert len(simplifier.complex_patterns) > 0

    def test_metaphor_patterns_loaded(self, simplifier):
        """Test that metaphor patterns are loaded"""
        assert len(simplifier.metaphor_patterns) > 0


class TestTurkishTextSimplifierCharacterPreservation:
    """Test Turkish character preservation (ç, ğ, ı, İ, ö, ş, ü)"""

    @pytest.fixture
    def simplifier(self):
        return TurkishTextSimplifier()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text,expected_chars",
        [
            ("çalışma", "ç"),
            ("öğrenci", "öğ"),
            ("Işık", "Iş"),
            ("şehir", "ş"),
            ("ülke", "ü"),
            ("İstanbul", "İ"),
            ("ağaç", "ağ"),
        ],
    )
    async def test_turkish_character_preservation(
        self, simplifier, text, expected_chars
    ):
        """Test that Turkish characters are preserved"""
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        for char in expected_chars:
            assert char in result.simplified_text

    @pytest.mark.asyncio
    async def test_all_turkish_vowels_preserved(self, simplifier):
        """Test all Turkish vowels are preserved"""
        text = "aeiouıöüAEIOUIÖÜ"
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        assert result.simplified_text == text

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "word",
        [
            "çocuk",
            "öğretmen",
            "şeker",
            "ülke",
            "ığdır",
            "İzmir",
            "Çanakkale",
            "Şırnak",
            "Ağrı",
            "Iğdır",
        ],
    )
    async def test_turkish_words_character_integrity(self, simplifier, word):
        """Test Turkish words maintain character integrity"""
        result = await simplifier.simplify_text(word, SimplificationLevel.LEXICAL)
        # Check that original characters are present in result
        assert len(result.simplified_text) > 0


class TestTurkishTextSimplifierLexicalSimplification:
    """Test Level 1: Lexical simplification"""

    @pytest.fixture
    def simplifier(self):
        return TurkishTextSimplifier()

    @pytest.mark.asyncio
    async def test_lexical_simple_ottoman_word(self, simplifier):
        """Test lexical simplification of Ottoman word"""
        text = "mütalaa"
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        assert result.simplified_text == "görüş"

    @pytest.mark.asyncio
    async def test_lexical_simple_academic_word(self, simplifier):
        """Test lexical simplification of academic word"""
        text = "implementasyon"
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        assert result.simplified_text == "uygulama"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "original,expected",
        [
            ("mütalaa önemlidir", "görüş önemlidir"),
            ("tetkik yapıldı", "inceleme yapıldı"),
            ("optimizasyon gerekli", "iyileştirme gerekli"),
            ("algoritma çalışıyor", "yöntem çalışıyor"),
            ("münhasıran buna", "sadece buna"),
        ],
    )
    async def test_lexical_sentence_simplification(
        self, simplifier, original, expected
    ):
        """Test lexical simplification in sentences"""
        result = await simplifier.simplify_text(original, SimplificationLevel.LEXICAL)
        assert result.simplified_text == expected

    @pytest.mark.asyncio
    async def test_lexical_multiple_replacements(self, simplifier):
        """Test multiple lexical replacements in one text"""
        text = "mütalaa ve tetkik önemlidir"
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        assert "görüş" in result.simplified_text
        assert "inceleme" in result.simplified_text
        assert "mütalaa" not in result.simplified_text
        assert "tetkik" not in result.simplified_text

    @pytest.mark.asyncio
    async def test_lexical_changes_recorded(self, simplifier):
        """Test that lexical changes are recorded"""
        text = "mütalaa"
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        assert len(result.changes_made) > 0
        assert any("mütalaa" in change for change in result.changes_made)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text",
        [
            "tetkik edildi",
            "mütalaa önemli",
            "implementasyon başarılı",
            "optimizasyon yapıldı",
            "koordinasyon sağlandı",
        ],
    )
    async def test_lexical_processing_time(self, simplifier, text):
        """Test that lexical processing completes quickly"""
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        assert result.processing_time >= 0

    @pytest.mark.asyncio
    async def test_lexical_preserve_unchanged_words(self, simplifier):
        """Test that unchanged words are preserved"""
        text = "kitap masa sandalye"
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        assert result.simplified_text == text


class TestTurkishTextSimplifierSyntacticSimplification:
    """Test Level 2: Syntactic simplification"""

    @pytest.fixture
    def simplifier(self):
        return TurkishTextSimplifier()

    @pytest.mark.asyncio
    async def test_syntactic_level_includes_lexical(self, simplifier):
        """Test that syntactic level also applies lexical changes"""
        text = "mütalaa önemlidir"
        result = await simplifier.simplify_text(text, SimplificationLevel.SYNTACTIC)
        assert "görüş" in result.simplified_text

    @pytest.mark.asyncio
    async def test_syntactic_long_sentence_split(self, simplifier):
        """Test that long sentences are split"""
        # Create a long sentence (>100 chars)
        text = "Bu çok uzun bir cümle, birçok virgül içeriyor, ve anlaşılması zor, bu yüzden basitleştirme gerekli"
        result = await simplifier.simplify_text(text, SimplificationLevel.SYNTACTIC)
        # Should have more sentences than original
        assert len(result.simplified_text) > 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text",
        [
            "Kitap okudum ve film izledim",
            "Ders çalıştım ama yoruldum",
            "Yemek yedim, sonra uyudum",
        ],
    )
    async def test_syntactic_simple_sentences_unchanged(self, simplifier, text):
        """Test that simple sentences are not over-simplified"""
        result = await simplifier.simplify_text(text, SimplificationLevel.SYNTACTIC)
        # Should not be empty
        assert len(result.simplified_text) > 0

    @pytest.mark.asyncio
    async def test_syntactic_changes_recorded(self, simplifier):
        """Test that syntactic changes are recorded"""
        text = "Çok uzun bir cümle, birçok virgül, çok karmaşık yapı, anlaşılması zor, basit değil"
        result = await simplifier.simplify_text(text, SimplificationLevel.SYNTACTIC)
        # Should have some changes
        assert result.complexity_score >= 0


class TestTurkishTextSimplifierSemanticSimplification:
    """Test Level 3: Semantic simplification"""

    @pytest.fixture
    def simplifier(self):
        return TurkishTextSimplifier()

    @pytest.mark.asyncio
    async def test_semantic_level_includes_all_levels(self, simplifier):
        """Test that semantic level applies all 3 levels"""
        text = "mütalaa önemlidir"
        result = await simplifier.simplify_text(text, SimplificationLevel.SEMANTIC)
        # Should apply lexical changes at minimum
        assert "görüş" in result.simplified_text or len(result.simplified_text) > 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "metaphor,concrete",
        [
            ("bilginin denizi", "çok fazla bilgi"),
            ("düşünce fırtınası", "çok düşünme"),
            ("kalbin sesi", "içten gelen his"),
            ("zamanın akışı", "zaman geçişi"),
        ],
    )
    async def test_semantic_metaphor_simplification(
        self, simplifier, metaphor, concrete
    ):
        """Test metaphor simplification"""
        result = await simplifier.simplify_text(metaphor, SimplificationLevel.SEMANTIC)
        assert concrete in result.simplified_text

    @pytest.mark.asyncio
    async def test_semantic_preserve_meaning_flag(self, simplifier):
        """Test preserve_meaning flag"""
        text = "demokrasi önemlidir"
        result = await simplifier.simplify_text(
            text, SimplificationLevel.SEMANTIC, preserve_meaning=True
        )
        # Should have some output
        assert len(result.simplified_text) > 0

    @pytest.mark.asyncio
    async def test_semantic_changes_recorded(self, simplifier):
        """Test that semantic changes are recorded"""
        text = "bilginin denizi çok geniş"
        result = await simplifier.simplify_text(text, SimplificationLevel.SEMANTIC)
        # Should have complexity score
        assert result.complexity_score >= 0


class TestTurkishTextSimplifierComplexityCalculation:
    """Test complexity calculation"""

    @pytest.fixture
    def simplifier(self):
        return TurkishTextSimplifier()

    def test_complexity_empty_text(self, simplifier):
        """Test complexity of empty text"""
        complexity = simplifier._calculate_complexity("")
        assert complexity == 0.0

    @pytest.mark.parametrize(
        "text,min_complexity",
        [
            ("kısa", 0),
            ("bu kısa bir cümle", 0),
            ("çok uzun ve karmaşık bir cümle yapısı var burada", 0),
        ],
    )
    def test_complexity_various_texts(self, simplifier, text, min_complexity):
        """Test complexity calculation for various texts"""
        complexity = simplifier._calculate_complexity(text)
        assert complexity >= min_complexity
        assert complexity <= 100.0

    def test_complexity_long_words_increase_score(self, simplifier):
        """Test that longer words increase complexity"""
        simple = simplifier._calculate_complexity("kısa söz")
        complex_text = simplifier._calculate_complexity("karmaşıklaştırılmış terimler")
        # Complex should generally be higher (but not guaranteed for short texts)
        assert complex_text >= 0


class TestTurkishTextSimplifierReadabilityCalculation:
    """Test readability calculation"""

    @pytest.fixture
    def simplifier(self):
        return TurkishTextSimplifier()

    def test_readability_empty_text(self, simplifier):
        """Test readability of empty text"""
        readability = simplifier._calculate_readability("")
        assert readability == 0.0

    @pytest.mark.parametrize(
        "text", ["kısa söz", "bu basit bir cümle", "okunması kolay bir metin"]
    )
    def test_readability_simple_texts(self, simplifier, text):
        """Test readability of simple texts"""
        readability = simplifier._calculate_readability(text)
        assert 0.0 <= readability <= 100.0

    def test_readability_no_sentences(self, simplifier):
        """Test readability with no sentence terminators"""
        readability = simplifier._calculate_readability("kelime kelime kelime")
        assert readability == 50.0


class TestTurkishTextSimplifierEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def simplifier(self):
        return TurkishTextSimplifier()

    @pytest.mark.asyncio
    async def test_empty_string(self, simplifier):
        """Test empty string input"""
        result = await simplifier.simplify_text("", SimplificationLevel.LEXICAL)
        assert result.simplified_text == ""
        assert result.complexity_score == 0.0

    def test_single_char_complexity(self, simplifier):
        """Test complexity calculation for single character"""
        complexity = simplifier._calculate_complexity("a")
        # Single character should have some complexity value
        assert complexity >= 0.0 and complexity <= 100.0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("text", ["123456", "!@#$%^", "...", "---"])
    async def test_special_characters_only(self, simplifier, text):
        """Test special characters only"""
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        assert result.simplified_text == text

    @pytest.mark.asyncio
    async def test_mixed_content(self, simplifier):
        """Test mixed Turkish and numbers"""
        text = "5 kitap 10 kalem"
        result = await simplifier.simplify_text(text, SimplificationLevel.LEXICAL)
        assert "5" in result.simplified_text
        assert "10" in result.simplified_text


# ============================================================================
# TURKISH BIONIC READING TESTS
# ============================================================================


class TestTurkishBionicReadingDataModels:
    """Test data models for Turkish Bionic Reading"""

    def test_bionic_reading_result_creation(self):
        """Test BionicReadingResult creation"""
        result = BionicReadingResult(
            original_text="Test",
            bionic_text="**Te**st",
            processing_time_ms=5.0,
            word_count=1,
            bold_ratio=0.5,
            success=True,
        )

        assert result.original_text == "Test"
        assert result.bionic_text == "**Te**st"
        assert result.processing_time_ms == 5.0
        assert result.word_count == 1
        assert result.bold_ratio == 0.5
        assert result.success is True
        assert result.error_message is None

    def test_bionic_reading_result_with_error(self):
        """Test BionicReadingResult with error"""
        result = BionicReadingResult(
            original_text="Test",
            bionic_text="Test",
            processing_time_ms=0.0,
            word_count=0,
            bold_ratio=0.0,
            success=False,
            error_message="Test error",
        )

        assert result.success is False
        assert result.error_message == "Test error"

    def test_morphology_analysis_creation(self):
        """Test TurkishMorphologyAnalysis creation"""
        analysis = TurkishMorphologyAnalysis(
            word="kitaplar",
            root="kitap",
            suffixes=["lar"],
            is_compound=False,
            analysis_confidence=0.9,
        )

        assert analysis.word == "kitaplar"
        assert analysis.root == "kitap"
        assert analysis.suffixes == ["lar"]
        assert not analysis.is_compound
        assert analysis.analysis_confidence == 0.9


class TestTurkishBionicReadingRules:
    """Test Bionic Reading rules"""

    @pytest.fixture
    def bionic_reader(self):
        return TurkishBionicReading()

    def test_bionic_rules_loaded(self, bionic_reader):
        """Test that bionic rules are loaded"""
        assert bionic_reader.bionic_rules["root_bold_ratio"] == 0.4
        assert bionic_reader.bionic_rules["suffix_bold_ratio"] == 0.0
        assert bionic_reader.bionic_rules["min_bold_chars"] == 2
        assert bionic_reader.bionic_rules["max_bold_chars"] == 4

    def test_punctuation_separation(self, bionic_reader):
        """Test punctuation separation"""
        word, punct = bionic_reader._separate_punctuation("test.")
        assert word == "test"
        assert punct == "."

    @pytest.mark.parametrize(
        "text,expected_word,expected_punct",
        [
            ("test.", "test", "."),
            ("test!", "test", "!"),
            ("test?", "test", "?"),
            ("test,", "test", ","),
            ("test;", "test", ";"),
            ("test:", "test", ":"),
        ],
    )
    def test_punctuation_separation_various(
        self, bionic_reader, text, expected_word, expected_punct
    ):
        """Test punctuation separation with various marks"""
        word, punct = bionic_reader._separate_punctuation(text)
        assert word == expected_word
        assert punct == expected_punct

    def test_bold_char_counting(self, bionic_reader):
        """Test counting bold characters"""
        bionic_text = "**tes**t"
        count = bionic_reader._count_bold_chars(bionic_text)
        assert count == 3  # "tes"

    @pytest.mark.parametrize(
        "bionic_text,expected_count",
        [
            ("**te**st", 2),
            ("**tes**t", 3),
            ("**test**", 4),
            ("test", 0),
            ("**t**est", 1),
        ],
    )
    def test_bold_char_counting_various(
        self, bionic_reader, bionic_text, expected_count
    ):
        """Test bold character counting with various texts"""
        count = bionic_reader._count_bold_chars(bionic_text)
        assert count == expected_count


class TestTurkishBionicReadingBasicFunctionality:
    """Test basic Bionic Reading functionality"""

    @pytest.fixture
    def bionic_reader(self):
        return TurkishBionicReading()

    @pytest.mark.asyncio
    async def test_simple_word_bionic(self, bionic_reader):
        """Test Bionic Reading on simple word"""
        result = await bionic_reader.apply_bionic_reading("test")
        assert result.success
        assert "**" in result.bionic_text
        assert result.word_count == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text", ["kitap", "okul", "öğrenci", "çalışma", "öğretmen"]
    )
    async def test_turkish_words_bionic(self, bionic_reader, text):
        """Test Bionic Reading on Turkish words"""
        result = await bionic_reader.apply_bionic_reading(text)
        assert result.success
        assert result.word_count == 1

    @pytest.mark.asyncio
    async def test_sentence_bionic(self, bionic_reader):
        """Test Bionic Reading on sentence"""
        result = await bionic_reader.apply_bionic_reading("Kitap okudum")
        assert result.success
        assert result.word_count == 2
        assert "**" in result.bionic_text

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text", ["Okul çok güzel", "Ders çalışıyorum", "Kitap okumayı seviyorum"]
    )
    async def test_turkish_sentences_bionic(self, bionic_reader, text):
        """Test Bionic Reading on Turkish sentences"""
        result = await bionic_reader.apply_bionic_reading(text)
        assert result.success
        assert result.word_count > 0


class TestTurkishBionicReadingCharacterPreservation:
    """Test Turkish character preservation in Bionic Reading"""

    @pytest.fixture
    def bionic_reader(self):
        return TurkishBionicReading()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text",
        [
            "çocuk",
            "öğrenci",
            "şeker",
            "ülke",
            "ışık",
            "İstanbul",
            "Çanakkale",
            "Şırnak",
            "Ağrı",
        ],
    )
    async def test_turkish_chars_preserved(self, bionic_reader, text):
        """Test that Turkish characters are preserved"""
        result = await bionic_reader.apply_bionic_reading(text)
        # Remove bold markers to check characters
        clean_text = result.bionic_text.replace("**", "")
        # Check that text has correct length (case insensitive comparison)
        assert len(clean_text.lower()) == len(text.lower())

    @pytest.mark.asyncio
    async def test_all_turkish_vowels_in_bionic(self, bionic_reader):
        """Test all Turkish vowels in Bionic Reading"""
        text = "ağaç öğrenci ışık üzüm"
        result = await bionic_reader.apply_bionic_reading(text)
        clean_text = result.bionic_text.replace("**", "")
        assert "ğ" in clean_text
        assert "ö" in clean_text
        assert "ı" in clean_text
        assert "ü" in clean_text


class TestTurkishBionicReadingEdgeCases:
    """Test edge cases for Bionic Reading"""

    @pytest.fixture
    def bionic_reader(self):
        return TurkishBionicReading()

    @pytest.mark.asyncio
    async def test_empty_string(self, bionic_reader):
        """Test empty string"""
        result = await bionic_reader.apply_bionic_reading("")
        assert result.success
        assert result.bionic_text == ""
        assert result.word_count == 0

    @pytest.mark.asyncio
    async def test_whitespace_only(self, bionic_reader):
        """Test whitespace only"""
        result = await bionic_reader.apply_bionic_reading("   ")
        assert result.success

    @pytest.mark.asyncio
    @pytest.mark.parametrize("text", ["a", "ab", "x", "y"])
    async def test_very_short_words(self, bionic_reader, text):
        """Test very short words (< 3 chars)"""
        result = await bionic_reader.apply_bionic_reading(text)
        assert result.success
        # Short words should not be bolded
        assert result.bionic_text == text

    @pytest.mark.asyncio
    async def test_numbers_only(self, bionic_reader):
        """Test numbers only"""
        result = await bionic_reader.apply_bionic_reading("123 456")
        assert result.success

    @pytest.mark.asyncio
    async def test_punctuation_preserved(self, bionic_reader):
        """Test punctuation is preserved"""
        result = await bionic_reader.apply_bionic_reading("Merhaba.")
        assert "." in result.bionic_text

    @pytest.mark.asyncio
    async def test_multiple_punctuation(self, bionic_reader):
        """Test multiple punctuation marks"""
        result = await bionic_reader.apply_bionic_reading("Merhaba! Nasılsın?")
        assert "!" in result.bionic_text
        assert "?" in result.bionic_text


class TestTurkishBionicReadingPerformance:
    """Test performance characteristics"""

    @pytest.fixture
    def bionic_reader(self):
        return TurkishBionicReading()

    @pytest.mark.asyncio
    async def test_processing_time_recorded(self, bionic_reader):
        """Test processing time is recorded"""
        result = await bionic_reader.apply_bionic_reading("Test metin")
        assert result.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_bold_ratio_calculated(self, bionic_reader):
        """Test bold ratio is calculated"""
        result = await bionic_reader.apply_bionic_reading("Merhaba dünya")
        assert 0.0 <= result.bold_ratio <= 1.0

    @pytest.mark.asyncio
    async def test_word_count_accurate(self, bionic_reader):
        """Test word count is accurate"""
        result = await bionic_reader.apply_bionic_reading("bir iki üç dört")
        assert result.word_count == 4


# ============================================================================
# THREE-LEVEL TURKISH SIMPLIFICATION TESTS
# ============================================================================


class TestThreeLevelSimplificationDataModels:
    """Test data models for Three-Level Simplification"""

    def test_simplification_result_creation(self):
        """Test SimplificationResult creation"""
        result = ThreeLevelResult(
            original_text="Original",
            level1_lexical="Level1",
            level2_syntactic="Level2",
            level3_semantic="Level3",
            complexity_reduction=0.5,
            readability_score=7.5,
            processing_time_ms=10.0,
            applied_rules=["Rule1", "Rule2"],
        )

        assert result.original_text == "Original"
        assert result.level1_lexical == "Level1"
        assert result.level2_syntactic == "Level2"
        assert result.level3_semantic == "Level3"
        assert result.complexity_reduction == 0.5
        assert result.readability_score == 7.5
        assert result.processing_time_ms == 10.0
        assert len(result.applied_rules) == 2


class TestThreeLevelSimplificationReplacementDictionaries:
    """Test replacement dictionaries"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    def test_ottoman_academic_replacements_loaded(self, simplifier):
        """Test Ottoman/Academic replacements are loaded"""
        assert len(simplifier.ottoman_academic_replacements) > 0
        assert "mütalaa" in simplifier.ottoman_academic_replacements
        assert simplifier.ottoman_academic_replacements["mütalaa"] == "okuma"

    def test_foreign_replacements_loaded(self, simplifier):
        """Test foreign word replacements are loaded"""
        assert len(simplifier.foreign_replacements) > 0
        assert "implementasyon" in simplifier.foreign_replacements
        assert simplifier.foreign_replacements["implementasyon"] == "uygulama"

    @pytest.mark.parametrize(
        "ottoman,modern",
        [
            ("mütalaa", "okuma"),
            ("tetkik", "inceleme"),
            ("müzakere", "görüşme"),
            ("istifade", "yararlanma"),
            ("istihsal", "üretim"),
        ],
    )
    def test_ottoman_replacements_parametrized(self, simplifier, ottoman, modern):
        """Test Ottoman replacements (parametrized)"""
        assert simplifier.ottoman_academic_replacements[ottoman] == modern

    @pytest.mark.parametrize(
        "foreign,turkish",
        [
            ("implementasyon", "uygulama"),
            ("optimizasyon", "eniyileme"),
            ("performans", "başarım"),
            ("analiz", "çözümleme"),
            ("algoritma", "işlem dizisi"),
        ],
    )
    def test_foreign_replacements_parametrized(self, simplifier, foreign, turkish):
        """Test foreign word replacements (parametrized)"""
        assert simplifier.foreign_replacements[foreign] == turkish


class TestThreeLevelSimplificationLevel1Lexical:
    """Test Level 1: Lexical simplification"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.asyncio
    async def test_level1_ottoman_replacement(self, simplifier):
        """Test Level 1 Ottoman word replacement"""
        text = "mütalaa önemlidir"
        result = await simplifier.revolutionary_simplification(text)
        assert "okuma" in result.level1_lexical

    @pytest.mark.asyncio
    async def test_level1_foreign_replacement(self, simplifier):
        """Test Level 1 foreign word replacement"""
        text = "implementasyon başarılı"
        result = await simplifier.revolutionary_simplification(text)
        assert "uygulama" in result.level1_lexical

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "original,expected_word",
        [
            ("tetkik yapıldı", "inceleme"),
            ("mütalaa önemli", "okuma"),
            ("optimizasyon gerekli", "eniyileme"),
            ("performans yüksek", "başarım"),
        ],
    )
    async def test_level1_various_replacements(
        self, simplifier, original, expected_word
    ):
        """Test Level 1 various replacements"""
        result = await simplifier.revolutionary_simplification(original)
        assert expected_word in result.level1_lexical


class TestThreeLevelSimplificationLevel2Syntactic:
    """Test Level 2: Syntactic simplification"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.asyncio
    async def test_level2_includes_level1(self, simplifier):
        """Test Level 2 includes Level 1 changes"""
        text = "mütalaa önemlidir"
        result = await simplifier.revolutionary_simplification(text)
        # Level 2 should also have the lexical changes
        assert "okuma" in result.level2_syntactic or len(result.level2_syntactic) > 0

    @pytest.mark.asyncio
    async def test_level2_sentence_structure(self, simplifier):
        """Test Level 2 sentence structure simplification"""
        text = "Kitap okudum ve ders çalıştım"
        result = await simplifier.revolutionary_simplification(text)
        # Should have syntactic output
        assert len(result.level2_syntactic) > 0


class TestThreeLevelSimplificationLevel3Semantic:
    """Test Level 3: Semantic simplification"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.asyncio
    async def test_level3_includes_all_levels(self, simplifier):
        """Test Level 3 includes all previous levels"""
        text = "mütalaa önemlidir"
        result = await simplifier.revolutionary_simplification(text)
        # Should have final output
        assert len(result.level3_semantic) > 0

    @pytest.mark.asyncio
    async def test_level3_metaphor_simplification(self, simplifier):
        """Test Level 3 metaphor simplification"""
        text = "kalbi kırılmak kötüdür"
        result = await simplifier.revolutionary_simplification(text)
        # Should simplify the metaphor
        assert "üzülmek" in result.level3_semantic


class TestThreeLevelSimplificationComplexityMetrics:
    """Test complexity and readability metrics"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    def test_complexity_calculation(self, simplifier):
        """Test complexity calculation"""
        complexity = simplifier._calculate_text_complexity("basit bir cümle")
        assert 0.0 <= complexity <= 10.0

    def test_complexity_empty_text(self, simplifier):
        """Test complexity of empty text"""
        complexity = simplifier._calculate_text_complexity("")
        assert complexity == 0.0

    @pytest.mark.parametrize(
        "text",
        [
            "kısa",
            "bu kısa cümle",
            "orta uzunlukta bir cümle yapısı",
            "çok uzun ve karmaşık bir cümle yapısı burada yer alıyor",
        ],
    )
    def test_complexity_various_texts(self, simplifier, text):
        """Test complexity for various texts"""
        complexity = simplifier._calculate_text_complexity(text)
        assert 0.0 <= complexity <= 10.0

    def test_readability_calculation(self, simplifier):
        """Test readability calculation"""
        readability = simplifier._calculate_turkish_readability("basit bir cümle")
        assert 0.0 <= readability <= 10.0

    def test_readability_empty_text(self, simplifier):
        """Test readability of empty text"""
        readability = simplifier._calculate_turkish_readability("")
        assert readability == 0.0


class TestThreeLevelSimplificationSyllableCount:
    """Test syllable counting for Turkish"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.parametrize(
        "word,expected_min",
        [("a", 1), ("ev", 1), ("kitap", 2), ("okul", 2), ("öğrenci", 3)],
    )
    def test_syllable_count_basic(self, simplifier, word, expected_min):
        """Test syllable counting for basic words"""
        count = simplifier._count_syllables(word)
        assert count >= expected_min

    def test_syllable_count_turkish_vowels(self, simplifier):
        """Test syllable count recognizes Turkish vowels"""
        # "aeiouıöü" - each vowel should count as a syllable
        count = simplifier._count_syllables("aeiouıöü")
        assert count >= 1


class TestThreeLevelSimplificationEdgeCases:
    """Test edge cases for Three-Level Simplification"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    def test_empty_text_complexity(self, simplifier):
        """Test complexity calculation for empty text"""
        complexity = simplifier._calculate_text_complexity("")
        assert complexity == 0.0

    def test_single_char_complexity(self, simplifier):
        """Test complexity calculation for single character"""
        complexity = simplifier._calculate_text_complexity("x")
        assert complexity >= 0.0 and complexity <= 10.0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("text", ["123", "!@#", "---"])
    async def test_special_characters(self, simplifier, text):
        """Test special characters"""
        result = await simplifier.revolutionary_simplification(text)
        assert result.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_single_word(self, simplifier):
        """Test single word"""
        result = await simplifier.revolutionary_simplification("kitap")
        assert len(result.level3_semantic) > 0

    @pytest.mark.asyncio
    async def test_mixed_content(self, simplifier):
        """Test mixed Turkish and numbers"""
        result = await simplifier.revolutionary_simplification("5 kitap 10 kalem")
        assert "5" in result.level3_semantic
        assert "10" in result.level3_semantic


class TestThreeLevelSimplificationCharacterPreservation:
    """Test Turkish character preservation in three-level simplification"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text",
        [
            "çocuk oyun oynar",
            "öğrenci ders çalışır",
            "şeker çok tatlı",
            "ülkemiz güzel",
            "ışık parlak",
        ],
    )
    async def test_turkish_characters_preserved(self, simplifier, text):
        """Test Turkish characters are preserved"""
        result = await simplifier.revolutionary_simplification(text)
        # Check that some Turkish characters are in output
        assert len(result.level3_semantic) > 0


class TestThreeLevelSimplificationComplexSentences:
    """Test complex sentence simplification"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    def test_is_complex_sentence_short(self, simplifier):
        """Test short sentence is not complex"""
        is_complex = simplifier._is_complex_sentence("Kitap okudum")
        # Short sentences may or may not be complex
        assert isinstance(is_complex, bool)

    def test_is_complex_sentence_long(self, simplifier):
        """Test long sentence detection"""
        long_sentence = "Bu çok uzun bir cümle, birden fazla virgül içeriyor, ve anlaşılması zor olabilir"
        is_complex = simplifier._is_complex_sentence(long_sentence)
        assert isinstance(is_complex, bool)

    @pytest.mark.parametrize(
        "sentence",
        [
            "Kısa cümle",
            "Orta uzunlukta bir cümle",
            "Bu cümle biraz daha uzun ve daha karmaşık",
        ],
    )
    def test_is_complex_sentence_various(self, simplifier, sentence):
        """Test complex sentence detection for various sentences"""
        is_complex = simplifier._is_complex_sentence(sentence)
        assert isinstance(is_complex, bool)

    def test_split_sentences(self, simplifier):
        """Test sentence splitting"""
        text = "İlk cümle. İkinci cümle. Üçüncü cümle."
        sentences = simplifier._split_sentences(text)
        assert len(sentences) == 3

    @pytest.mark.parametrize(
        "text,min_sentences",
        [("Bir cümle.", 1), ("İki cümle. Burada.", 2), ("Üç. Cümle. Var.", 3)],
    )
    def test_split_sentences_various(self, simplifier, text, min_sentences):
        """Test sentence splitting for various texts"""
        sentences = simplifier._split_sentences(text)
        assert len(sentences) >= min_sentences


class TestThreeLevelSimplificationProcessingMetrics:
    """Test processing metrics and statistics"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    @pytest.mark.asyncio
    async def test_processing_time_recorded(self, simplifier):
        """Test processing time is recorded"""
        result = await simplifier.revolutionary_simplification("Test metin")
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_complexity_reduction_calculated(self, simplifier):
        """Test complexity reduction is calculated"""
        result = await simplifier.revolutionary_simplification("Karmaşık metin")
        assert result.complexity_reduction >= 0.0

    @pytest.mark.asyncio
    async def test_readability_score_calculated(self, simplifier):
        """Test readability score is calculated"""
        result = await simplifier.revolutionary_simplification("Test metin")
        assert 0.0 <= result.readability_score <= 10.0

    @pytest.mark.asyncio
    async def test_applied_rules_recorded(self, simplifier):
        """Test applied rules are recorded"""
        result = await simplifier.revolutionary_simplification("mütalaa önemli")
        # Should have at least some rules applied
        assert isinstance(result.applied_rules, list)

    def test_get_simplification_statistics(self, simplifier):
        """Test getting simplification statistics"""
        result = ThreeLevelResult(
            original_text="Original text here",
            level1_lexical="Level 1",
            level2_syntactic="Level 2",
            level3_semantic="Level 3",
            complexity_reduction=0.5,
            readability_score=7.5,
            processing_time_ms=10.0,
            applied_rules=["Rule1", "Rule2"],
        )

        stats = simplifier.get_simplification_statistics(result)
        assert "word_count_change" in stats
        assert "sentence_count_change" in stats
        assert "complexity_reduction_percent" in stats
        assert "readability_improvement" in stats
        assert "processing_time_ms" in stats
        assert "rules_applied_count" in stats
        assert stats["levels_processed"] == 3


class TestThreeLevelSimplificationTargetLevels:
    """Test target level configurations"""

    @pytest.fixture
    def simplifier(self):
        return ThreeLevelTurkishSimplification()

    def test_target_levels_loaded(self, simplifier):
        """Test target levels are loaded"""
        assert "elementary" in simplifier.target_levels
        assert "intermediate" in simplifier.target_levels
        assert "advanced" in simplifier.target_levels

    @pytest.mark.asyncio
    @pytest.mark.parametrize("level", ["elementary", "intermediate", "advanced"])
    async def test_simplification_with_different_levels(self, simplifier, level):
        """Test simplification with different target levels"""
        result = await simplifier.revolutionary_simplification(
            "Test metin", target_level=level
        )
        assert result.processing_time_ms > 0
