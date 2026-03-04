"""Tests for d-dataset import classification logic."""
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
