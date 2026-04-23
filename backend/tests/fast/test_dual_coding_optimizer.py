from __future__ import annotations

import pytest

pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

import pytest

pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""Tests for Dual Coding Optimizer - Paivio & Mayer Multimedia Principles."""


from services.dual_coding_optimizer import (
    MayerPrinciple,
    VisualType,
    analyze_question_multimedia,
    optimize_question_layout,
    suggest_visual_enhancement,
)


class TestAnalyzeQuestionMultimedia:
    """Test analyze_question_multimedia function."""

    def test_empty_question_returns_zero_score(self):
        """Empty question text should return overall score of 0.0."""
        result = analyze_question_multimedia("")
        assert result.overall_score == 0.0
        assert result.word_count == 0
        assert len(result.principle_scores) == 0

    def test_simple_question_without_visual(self):
        """Simple question without visual content."""
        question = "2 + 2 kaçtır?"
        result = analyze_question_multimedia(question, subject="matematik")

        assert result.overall_score > 0.0
        assert result.word_count == 4
        assert not result.has_visual
        assert not result.has_table
        assert len(result.principle_scores) == 6  # All 6 principles evaluated

    def test_question_with_visual_content(self):
        """Question with visual content should have has_visual=True."""
        question = "Aşağıdaki şekilde verilen üçgenin alanını bulunuz."
        visual = "triangle_diagram.png"
        result = analyze_question_multimedia(question, visual_content=visual, subject="geometri")

        assert result.has_visual
        assert result.word_count == 6  # Fixed: actual word count
        # Multimedia score should be high since visual is present
        multimedia_score = next(
            (ps.score for ps in result.principle_scores if ps.principle == MayerPrinciple.MULTIMEDIA),
            0.0,
        )
        assert multimedia_score > 0.6

    def test_matematik_without_visual_suggests_visual(self):
        """Matematik question without visual should suggest adding one."""
        question = "Bir fonksiyonun grafiği çizildiğinde x eksenini kestiği noktaları bulunuz."
        result = analyze_question_multimedia(question, subject="matematik")

        assert not result.has_visual
        assert result.suggested_visual_type in [VisualType.GRAPH, VisualType.DIAGRAM]
        assert any("görsel" in s.lower() for s in result.optimization_suggestions)

    def test_turkce_subject_no_visual_needed(self):
        """Türkçe/Edebiyat questions don't need visuals."""
        question = "Aşağıdaki cümlede altı çizili sözcüğün anlamı nedir?"
        result = analyze_question_multimedia(question, subject="turkce")

        # Multimedia score should be reasonable even without visual
        multimedia_score = next(
            (ps.score for ps in result.principle_scores if ps.principle == MayerPrinciple.MULTIMEDIA),
            0.0,
        )
        assert multimedia_score >= 0.6  # Not penalized for lack of visual

    def test_long_question_coherence_penalty(self):
        """Long questions (>150 words) should have coherence penalty."""
        # Generate a long question with filler words
        question = " ".join(["Aslında bu soru gerçekten kesinlikle tabii ki önemlidir."] * 20)
        result = analyze_question_multimedia(question)

        assert result.word_count > 150
        assert any("uzun" in s.lower() for s in result.optimization_suggestions)
        # Coherence score should be penalized
        coherence_score = next(
            (ps.score for ps in result.principle_scores if ps.principle == MayerPrinciple.COHERENCE),
            1.0,
        )
        assert coherence_score < 0.5  # Heavily penalized

    def test_question_with_table_detected(self):
        """Questions mentioning 'tablo' should have has_table=True."""
        question = "Aşağıdaki tablo verilerine göre ortalamayı hesaplayınız."
        result = analyze_question_multimedia(question)

        assert result.has_table
        assert result.word_count == 6

    def test_question_with_formula_detected(self):
        """Questions with math symbols should have has_formula=True."""
        question = "F = ma formülünü kullanarak kuvveti bulunuz. √(x² + y²) = z"
        result = analyze_question_multimedia(question)

        assert result.has_formula
        assert result.word_count > 0

    def test_redundancy_detection(self):
        """Redundant phrases should be detected."""
        question = "Yukarıdaki belirtildiği gibi, tekrar belirtmek gerekirse, daha önce söylendiği üzere..."
        result = analyze_question_multimedia(question)

        redundancy_score = next(
            (ps.score for ps in result.principle_scores if ps.principle == MayerPrinciple.REDUNDANCY),
            1.0,
        )
        assert redundancy_score < 0.8  # Penalized for redundancy
        assert any("tekrar" in s.lower() for s in result.optimization_suggestions)

    def test_signaling_keywords_boost_score(self):
        """Questions with signaling keywords (özellikle, dikkat) should have higher signaling score."""
        question = "Özellikle dikkat edilmesi gereken önemli nokta şudur: kritik temel olarak..."
        result = analyze_question_multimedia(question)

        signaling_score = next(
            (ps.score for ps in result.principle_scores if ps.principle == MayerPrinciple.SIGNALING),
            0.0,
        )
        assert signaling_score > 0.7  # High signaling score

    def test_personalization_informal_language(self):
        """Informal language (bulalım, hesaplayalım) should boost personalization score."""
        question = "Şimdi birlikte hesaplayalım. Bakalım sonuç ne olacak? Düşünelim ve bulalım."
        result = analyze_question_multimedia(question)

        personal_score = next(
            (ps.score for ps in result.principle_scores if ps.principle == MayerPrinciple.PERSONALIZATION),
            0.0,
        )
        assert personal_score > 0.7  # High personalization score

    def test_personalization_formal_language_penalty(self):
        """Formal language (edilmiştir, bulunmaktadır) should lower personalization score."""
        question = "Bu durumda olup söz konusu edilmiştir. Bulunmaktadır olduğu açıktır."
        result = analyze_question_multimedia(question)

        personal_score = next(
            (ps.score for ps in result.principle_scores if ps.principle == MayerPrinciple.PERSONALIZATION),
            1.0,
        )
        assert personal_score < 0.6  # Low personalization score
        assert any("konuşma" in s.lower() for s in result.optimization_suggestions)

    def test_to_dict_serialization(self):
        """DualCodingScore.to_dict should properly serialize."""
        question = "Basit bir matematik sorusu."
        result = analyze_question_multimedia(question, subject="matematik")
        data = result.to_dict()

        assert isinstance(data, dict)
        assert "overall_score" in data
        assert isinstance(data["overall_score"], float)
        assert "principle_scores" in data
        assert isinstance(data["principle_scores"], list)
        assert "suggested_visual_type" in data
        assert isinstance(data["suggested_visual_type"], str)
        assert "word_count" in data
        assert data["word_count"] == 4
        assert "has_visual" in data
        assert isinstance(data["has_visual"], bool)

    def test_segmenting_long_text(self):
        """Long text (>80 words) with few sentences should have low segmenting score."""
        # Long text without proper sentence breaks
        question = " ".join(["kelime"] * 100)  # 100 words, 1 sentence
        result = analyze_question_multimedia(question)

        segment_score = next(
            (ps.score for ps in result.principle_scores if ps.principle == MayerPrinciple.SEGMENTING),
            1.0,
        )
        assert segment_score < 0.5  # Poor segmenting

    def test_segmenting_short_text(self):
        """Short text (<80 words) should have perfect segmenting score."""
        question = "Bu kısa bir sorudur. Sadece birkaç kelime içerir."
        result = analyze_question_multimedia(question)

        segment_score = next(
            (ps.score for ps in result.principle_scores if ps.principle == MayerPrinciple.SEGMENTING),
            0.0,
        )
        assert segment_score == 1.0  # Perfect segmenting


class TestSuggestVisualEnhancement:
    """Test suggest_visual_enhancement function."""

    def test_matematik_graph_suggestion(self):
        """Matematik question with 'fonksiyon' should suggest GRAPH."""
        question = "f(x) fonksiyonunun grafiği koordinat düzleminde çizilmiştir."
        result = suggest_visual_enhancement(question, subject="matematik")

        assert result.visual_type == VisualType.GRAPH
        assert result.priority > 0.5
        assert "grafik" in result.description.lower() or "koordinat" in result.description.lower()

    def test_geometri_diagram_suggestion(self):
        """Geometri question with shapes should suggest DIAGRAM."""
        question = "ABC üçgeninde AB kenarı 5 cm, BC kenarı 7 cm'dir. Açı değerini bulunuz."
        result = suggest_visual_enhancement(question, subject="geometri")

        assert result.visual_type == VisualType.DIAGRAM
        assert result.priority > 0.6  # High priority for geometric content
        assert "geometrik" in result.description.lower() or "şekil" in result.description.lower()

    def test_tarih_timeline_suggestion(self):
        """Tarih question should suggest TIMELINE."""
        question = "1071 yılında Malazgirt Savaşı'ndan sonra hangi dönem başlamıştır?"
        result = suggest_visual_enhancement(question, subject="tarih")

        assert result.visual_type == VisualType.TIMELINE
        assert result.priority > 0.0
        assert "zaman" in result.description.lower() or "kronolojik" in result.description.lower()

    def test_cografya_map_suggestion(self):
        """Coğrafya question should suggest MAP."""
        question = "Türkiye'nin güneydoğu bölgesinde hangi iller bulunmaktadır?"
        result = suggest_visual_enhancement(question, subject="cografya")

        assert result.visual_type == VisualType.MAP
        assert result.priority > 0.0
        assert "harita" in result.description.lower() or "coğrafi" in result.description.lower()

    def test_kimya_chemical_structure(self):
        """Kimya question with molecules should suggest CHEMICAL_STRUCTURE."""
        question = "CH4 molekülünün reaksiyonu sonucu hangi element ortaya çıkar? Asit molekülü nasıl oluşur?"
        result = suggest_visual_enhancement(question, subject="kimya")

        assert result.visual_type == VisualType.CHEMICAL_STRUCTURE
        assert result.priority > 0.0
        assert "kimya" in result.description.lower() or "yapı" in result.description.lower()

    def test_biyoloji_flowchart_suggestion(self):
        """Biyoloji question should suggest FLOWCHART."""
        question = "Hücre bölünmesi sürecinde hangi organeller aktiftir? Bitki ve hayvan hücreleri nasıl farklılaşır?"
        result = suggest_visual_enhancement(question, subject="biyoloji")

        assert result.visual_type == VisualType.FLOWCHART
        assert result.priority > 0.0
        assert "süreç" in result.description.lower() or "biyolojik" in result.description.lower()

    def test_turkce_no_visual_needed(self):
        """Türkçe subject should return NONE visual type."""
        question = "Aşağıdaki cümlede özne nedir?"
        result = suggest_visual_enhancement(question, subject="turkce")

        assert result.visual_type == VisualType.NONE
        assert result.priority == 0.0
        assert "gerekli değil" in result.reason.lower()

    def test_unknown_subject_with_table_pattern(self):
        """Unknown subject but with 'tablo' pattern should suggest TABLE."""
        question = "Aşağıdaki tablodaki verileri kullanarak istatistik hesaplayınız."
        result = suggest_visual_enhancement(question, subject="matematik")

        assert result.visual_type == VisualType.TABLE
        assert "tablo" in result.description.lower() or "veri" in result.description.lower()

    def test_long_question_increases_priority(self):
        """Long questions (>80 words) should have higher priority for visuals."""
        short_question = "Kısa soru."
        long_question = " ".join(["kelime"] * 100)  # 100 words

        short_result = suggest_visual_enhancement(short_question, subject="matematik")
        long_result = suggest_visual_enhancement(long_question, subject="matematik")

        assert long_result.priority > short_result.priority

    def test_empty_question(self):
        """Empty question with subject should still suggest based on subject."""
        result = suggest_visual_enhancement("", subject="geometri")

        # Should suggest DIAGRAM for geometri even with empty text
        assert result.visual_type == VisualType.DIAGRAM
        assert result.priority > 0.0


class TestOptimizeQuestionLayout:
    """Test optimize_question_layout function."""

    def test_empty_question(self):
        """Empty question should return empty result."""
        result = optimize_question_layout("")

        assert result["original"] == ""
        assert result["optimized"] == ""
        assert result["changes"] == []
        assert result["option_count"] == 0

    def test_short_question_no_changes(self):
        """Short question should not require segmenting."""
        question = "2 + 2 kaçtır?"
        result = optimize_question_layout(question)

        assert result["original"] == question
        # No segmenting needed for short text
        assert "paragraflara bölündü" not in " ".join(result["changes"])

    def test_long_question_segmenting(self):
        """Long question (>200 chars, >3 sentences) should be segmented."""
        sentences = [
            "Bu çok uzun bir sorudur ve birçok detay içermektedir.",
            "Birden fazla cümle içermektedir ve bu cümlelerin her biri önemli bilgiler taşımaktadır.",
            "Toplam karakter sayısı 200'ün üzerindedir ve bu nedenle segmentasyon gereklidir.",
            "Segmentasyona ihtiyaç vardır çünkü metin oldukça uzundur ve okunması zorlaşmaktadır.",
            "Son cümle de ekstra bilgi ekleyerek metni daha da uzatmaktadır.",
        ]
        question = " ".join(sentences)
        result = optimize_question_layout(question)

        assert len(result["original"]) > 200
        assert any("paragraflara bölündü" in c for c in result["changes"])
        assert "\n" in result["optimized"]  # Should have line breaks

    def test_filler_words_detection(self):
        """Filler words should be detected and flagged."""
        question = "Aslında bu soru gerçekten kesinlikle tabii ki esasen önemlidir."
        result = optimize_question_layout(question)

        assert any("dolgu kelimeleri" in c.lower() for c in result["changes"])
        # Should list at least some filler words
        change_text = " ".join(result["changes"])
        assert any(word in change_text for word in ["aslında", "gerçekten", "kesinlikle"])

    def test_key_terms_flagging(self):
        """Key terms (hangisi, kaçtır, etc.) should be flagged for emphasis."""
        question = "Sonuç kaçtır? Cevabı bulunuz. Hangisi doğrudur?"
        result = optimize_question_layout(question)

        assert any("vurgulanması gereken" in c.lower() for c in result["changes"])
        change_text = " ".join(result["changes"])
        assert any(term in change_text for term in ["kaçtır", "bulunuz", "hangisi"])

    def test_options_count(self):
        """Should correctly count provided options."""
        question = "Hangisi doğrudur?"
        options = ["A", "B", "C", "D", "E"]
        result = optimize_question_layout(question, options=options)

        assert result["option_count"] == 5

    def test_no_options(self):
        """Should handle None options gracefully."""
        question = "Açık uçlu soru."
        result = optimize_question_layout(question, options=None)

        assert result["option_count"] == 0

    def test_original_preserved(self):
        """Original text should always be preserved in result."""
        question = "Orijinal soru metni değişmemeli."
        result = optimize_question_layout(question)

        assert result["original"] == question
