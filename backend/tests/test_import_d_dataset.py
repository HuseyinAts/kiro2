"""Tests for d-dataset import classification logic and morphology metrics."""
import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.import_d_dataset import (
    classify_book,
    normalize_tr,
    generate_question_id,
    generate_topic_id,
    build_row,
    DEFAULT_TOPICS,
)
from scripts.update_morphology import (
    tokenize_turkish,
    count_sentences,
    calc_readability,
    compute_metrics,
)


class TestNormalizeTr:
    def test_istanbul(self):
        assert normalize_tr("\u0130STANBUL") == "istanbul"

    def test_turkish_i_dotless(self):
        assert normalize_tr("I\u015eIK") == "\u0131\u015f\u0131k"

    def test_empty(self):
        assert normalize_tr("") == ""

    def test_nfc_normalization(self):
        # Composed vs decomposed forms should normalize the same
        composed = "\u00e7"  # ç
        decomposed = "c\u0327"  # c + combining cedilla
        assert normalize_tr(composed) == normalize_tr(decomposed)


class TestClassifyBook:
    @pytest.mark.parametrize("book,expected_subject,expected_exam", [
        ("345 2025 Ayt Matematik Soru Bankas\u0131", "MATEMATIK", "AYT"),
        ("Bilgi Sarmal\u0131-2025-Tyt-Matematik Soru Bankas\u0131", "MATEMATIK", "TYT"),
        ("Orijinal-2024-Geometri Soru Bankas\u0131", "GEOMETRI", "TYT"),
        ("345 2025 Ayt Fizik Soru Bankas\u0131", "FIZIK", "AYT"),
        ("Apotemi Tyt Ayt Kimya 2019-2020", "KIMYA", "TYT"),
        ("Edebiyat Denizi Ayt Edebiyat Soru Bankasi", "EDEBIYAT", "AYT"),
        ("Esen Tyt T\u00fcrk\u00e7e Soru Bankas\u0131", "TURKCE", "TYT"),
        ("Mikro Orijinal Tyt Paragraf Soru Bankas\u0131 2024", "TURKCE", "TYT"),
        ("Orijinal-2025-Ayt-Matematik T\u00fcrev", "MATEMATIK", "AYT"),
        ("Orijinal-2025-Analitik Geometri", "GEOMETRI", "AYT"),
        ("345 2025 Tyt Biyoloji Soru Bankas\u0131", "BIYOLOJI", "TYT"),
        ("Esen Aps Tyt Ayt Tarih Soru Bankas\u0131", "TARIH", "TYT"),
        ("AC\u0130L-2025-TYT-Matemati\u011fin \u0130lac\u0131", "MATEMATIK", "TYT"),
        ("Fizipedia Ayt Fizik Soru Bankas\u0131 2025", "FIZIK", "AYT"),
        ("Edebiyat Soka\u011f\u0131 Dil Bilgisi Soru Bankas\u0131 2024", "TURKCE", "TYT"),
        ("Esen Tyt Cografya Soru Bankas\u0131", "COGRAFYA", "TYT"),
    ])
    def test_known_books(self, book, expected_subject, expected_exam):
        subject, exam = classify_book(book)
        assert subject == expected_subject, f"{book}: expected {expected_subject}, got {subject}"
        assert exam == expected_exam, f"{book}: expected {expected_exam}, got {exam}"

    def test_unknown_book_gets_genel(self):
        subject, exam = classify_book("Unknown Publisher Random Book 2025")
        assert subject == "GENEL"

    def test_exam_type_from_name_overrides_default(self):
        # Even though geometri defaults to None exam, 'Ayt' in name -> AYT
        subject, exam = classify_book("Orijinal-2025-Ayt-Geometri")
        assert exam == "AYT"

    def test_tyt_ayt_both_present_prefers_tyt(self):
        # When both appear, TYT takes precedence (lower level)
        subject, exam = classify_book("Full Matematik Tyt Ayt Geometri")
        assert exam == "TYT"


class TestGenerateQuestionId:
    def test_deterministic(self):
        id1 = generate_question_id("Book A", 10, 5)
        id2 = generate_question_id("Book A", 10, 5)
        assert id1 == id2

    def test_different_inputs(self):
        id1 = generate_question_id("Book A", 10, 5)
        id2 = generate_question_id("Book A", 10, 6)
        assert id1 != id2

    def test_uuid_format(self):
        import uuid
        qid = generate_question_id("Test", 1, 1)
        parsed = uuid.UUID(qid)  # Should not raise
        assert str(parsed) == qid


class TestGenerateTopicId:
    def test_deterministic(self):
        id1 = generate_topic_id("MAT")
        id2 = generate_topic_id("MAT")
        assert id1 == id2

    def test_all_subjects_have_topics(self):
        for subject, (code, name) in DEFAULT_TOPICS.items():
            tid = generate_topic_id(code)
            assert tid, f"No topic ID for {subject}"


class TestBuildRow:
    def test_basic_row(self):
        entry = {
            "book_name": "Test Book",
            "page_number": 42,
            "question_number": 3,
            "text": "What is 2+2?",
            "options": {"A": "3", "B": "4", "C": "5", "D": "6", "E": "7"},
            "answer": "B",
            "quality_score": 95.0,
            "confidence": 0.98,
        }
        row = build_row(entry, "MATEMATIK", "TYT")
        assert row["question_text"] == "What is 2+2?"
        assert row["correct_answer"] == "B"
        assert row["option_b"] == "4"
        assert row["exam_type"] == "TYT"
        assert row["subject_area"] == "MATEMATIK"
        assert row["grade_level"] == 11
        assert row["quality_score"] == 95.0
        assert row["source_book"] == "Test Book"
        assert row["source_page"] == 42

    def test_pipeline_metadata_excludes_direct_fields(self):
        entry = {
            "book_name": "Test",
            "page_number": 1,
            "question_number": 1,
            "text": "Q",
            "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
            "answer": "A",
            "quality_score": 100.0,
            "confidence": 0.9,
            "match_type": "exact",
            "answer_source": "book",
            "ai_sources": ["opus"],
        }
        row = build_row(entry, "FIZIK", "AYT")
        metadata = json.loads(row["pipeline_metadata"])
        # Direct fields should NOT be in metadata
        assert "text" not in metadata
        assert "options" not in metadata
        assert "answer" not in metadata
        # Pipeline fields SHOULD be in metadata
        assert metadata["match_type"] == "exact"
        assert metadata["answer_source"] == "book"
        assert metadata["ai_sources"] == ["opus"]

    def test_missing_option_e(self):
        entry = {
            "book_name": "Test",
            "page_number": 1,
            "question_number": 1,
            "text": "Q",
            "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
            "answer": "A",
        }
        row = build_row(entry, "TURKCE", "TYT")
        assert row["option_e"] is None


# =============================================================================
# Morphology Metrics Tests
# =============================================================================


class TestTokenizeTurkish:
    def test_basic(self):
        assert tokenize_turkish("Merhaba dünya") == ["Merhaba", "dünya"]

    def test_with_punctuation(self):
        tokens = tokenize_turkish("A) seçenek, B) seçenek.")
        assert "A" in tokens
        assert "seçenek" in tokens

    def test_empty(self):
        assert tokenize_turkish("") == []

    def test_turkish_chars(self):
        tokens = tokenize_turkish("çığ öşüğ İstanbul")
        assert len(tokens) == 3

    def test_math_question(self):
        tokens = tokenize_turkish("x + y = 10 ise x kaçtır?")
        assert "x" in tokens
        assert "kaçtır" in tokens


class TestCountSentences:
    def test_single(self):
        assert count_sentences("Merhaba dünya.") == 1

    def test_multiple(self):
        assert count_sentences("Soru nedir? Cevap budur. Tamam!") == 3

    def test_empty(self):
        assert count_sentences("") == 0


class TestCalcReadability:
    def test_short_easy(self):
        # Short sentences, short words = easy
        score = calc_readability(5, 1, 3.0)
        assert score > 50

    def test_zero_words(self):
        assert calc_readability(0, 0, 0.0) == 50.0


class TestComputeMetrics:
    def test_basic_turkish(self):
        m = compute_metrics("Bu bir matematik sorusudur. Cevap A seçeneğidir.")
        assert m["word_count"] > 0
        assert m["unique_word_count"] > 0
        assert m["average_word_length"] > 0
        assert 0 <= m["readability_score"] <= 100
        assert 0 <= m["morphology_complexity"] <= 1

    def test_empty_text(self):
        m = compute_metrics("")
        assert m["word_count"] == 0
        assert m["readability_score"] == 50.0
        assert m["morphology_complexity"] == 0.0

    def test_real_question(self):
        text = (
            "Bir dik prizmanın tabanı bir dikdörtgendir. "
            "Prizmanın yüksekliği 5 cm ve tabanın uzun kenarı 4 cm'dir."
        )
        m = compute_metrics(text)
        assert m["word_count"] >= 10
        assert m["unique_word_count"] >= 8
        assert m["average_word_length"] > 3.0


# =============================================================================
# Build Row Defaults Tests
# =============================================================================


class TestBuildRowDefaults:
    """Test that build_row provides correct defaults for NOT NULL columns."""

    def _make_entry(self):
        return {
            "book_name": "Test Book",
            "page_number": 1,
            "question_number": 1,
            "text": "Soru metni",
            "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
            "answer": "B",
        }

    def test_irt_defaults(self):
        row = build_row(self._make_entry(), "MATEMATIK", "TYT")
        assert row["irt_discrimination"] == 1.0
        assert row["irt_difficulty"] == 0.0
        assert row["irt_guessing"] == 0.2
        assert row["irt_upper_asymptote"] == 1.0
        assert row["is_calibrated"] is False

    def test_bloom_defaults(self):
        row = build_row(self._make_entry(), "FIZIK", "AYT")
        assert row["bloom_level"] == 2
        assert row["bloom_category"] == "understand"

    def test_difficulty_default(self):
        row = build_row(self._make_entry(), "KIMYA", "TYT")
        assert row["difficulty_level"] == "MEDIUM"

    def test_irt_based_difficulty_is_string(self):
        row = build_row(self._make_entry(), "TURKCE", "TYT")
        assert row["irt_based_difficulty"] == "medium"
        assert isinstance(row["irt_based_difficulty"], str)

    def test_statistics_zero(self):
        row = build_row(self._make_entry(), "TARIH", "TYT")
        assert row["times_asked"] == 0
        assert row["times_correct"] == 0
        assert row["average_response_time"] == 0.0


# =============================================================================
# Bloom Taxonomy Classifier Tests
# =============================================================================

from scripts.update_bloom_taxonomy import classify_bloom


class TestClassifyBloom:
    def test_apply_math_calculation(self):
        level, cat = classify_bloom("x + 3 = 7 ise x kaçtır?", "MATEMATIK")
        assert level == 3
        assert cat == "apply"

    def test_evaluate_which_is_wrong(self):
        level, cat = classify_bloom(
            "Aşağıdakilerden hangisi yanlıştır?", "TURKCE"
        )
        assert level == 5
        assert cat == "evaluate"

    def test_analyze_graph_based(self):
        level, cat = classify_bloom(
            "Verilen grafiğe göre aşağıdakilerden hangisi doğrudur?", "FIZIK"
        )
        assert level >= 4  # analyze or evaluate

    def test_remember_history(self):
        level, cat = classify_bloom(
            "İstanbul'un fethi hangi yılda gerçekleşmiştir?", "TARIH"
        )
        assert level == 1
        assert cat == "remember"

    def test_empty_text_uses_subject_default(self):
        level, _ = classify_bloom("", "MATEMATIK")
        assert level == 3  # Math default is apply

    def test_math_with_numbers_at_least_apply(self):
        level, _ = classify_bloom("5 ile 3 toplandığında sonuç nedir?", "MATEMATIK")
        assert level >= 3

    def test_all_levels_have_valid_category(self):
        valid = {"remember", "understand", "apply", "analyze", "evaluate", "create"}
        for text, subj in [
            ("tanımı nedir?", "TARIH"),
            ("ne anlama gelir?", "TURKCE"),
            ("hesaplayınız", "MATEMATIK"),
            ("karşılaştırınız", "FIZIK"),
            ("hangisi yanlıştır?", "BIYOLOJI"),
            ("tasarlayınız", "GENEL"),
        ]:
            _, cat = classify_bloom(text, subj)
            assert cat in valid, f"{text}: got invalid category '{cat}'"
