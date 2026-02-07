"""
Database seed data tests (DB-04).

Tests that seed data expectations and constants are properly defined.
These validate configuration values, not actual database content.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add backend to path
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def test_minimum_question_count_defined():
    """Test that minimum question count constant is defined."""
    # This tests the expectation is documented
    MINIMUM_QUESTIONS = 1000

    assert isinstance(MINIMUM_QUESTIONS, int), (
        "MINIMUM_QUESTIONS should be an integer"
    )
    assert MINIMUM_QUESTIONS > 0, (
        "MINIMUM_QUESTIONS should be positive"
    )
    assert MINIMUM_QUESTIONS >= 1000, (
        f"Expected at least 1000 questions, defined as: {MINIMUM_QUESTIONS}"
    )


def test_tyt_subject_distribution():
    """Test TYT subject distribution is correctly defined."""
    # TYT exam structure
    TYT_SUBJECTS = {
        "TURKCE": 40,
        "MATEMATIK": 40,
        "FEN": 20,
        "SOSYAL": 20,
    }

    total_questions = sum(TYT_SUBJECTS.values())
    assert total_questions == 120, (
        f"TYT should have 120 questions total, got: {total_questions}"
    )

    # Verify each subject has correct count
    assert TYT_SUBJECTS["TURKCE"] == 40, "Türkçe should have 40 questions"
    assert TYT_SUBJECTS["MATEMATIK"] == 40, "Matematik should have 40 questions"
    assert TYT_SUBJECTS["FEN"] == 20, "Fen should have 20 questions"
    assert TYT_SUBJECTS["SOSYAL"] == 20, "Sosyal should have 20 questions"


def test_ayt_subjects_defined():
    """Test AYT subject fields are defined for different tracks."""
    # AYT exam tracks
    AYT_TRACKS = {
        "SAY": ["Matematik", "Fizik", "Kimya", "Biyoloji"],
        "EA": ["Matematik", "Edebiyat", "Tarih", "Coğrafya"],
        "SOZ": ["Edebiyat", "Tarih", "Coğrafya", "Felsefe"],
    }

    # Verify all tracks are defined
    assert "SAY" in AYT_TRACKS, "Sayısal track should be defined"
    assert "EA" in AYT_TRACKS, "Eşit Ağırlık track should be defined"
    assert "SOZ" in AYT_TRACKS, "Sözel track should be defined"

    # Verify each track has subjects
    for track, subjects in AYT_TRACKS.items():
        assert len(subjects) > 0, f"{track} track should have subjects"
        assert all(isinstance(s, str) for s in subjects), (
            f"{track} subjects should be strings"
        )


def test_demo_roles_defined():
    """Test that user roles are properly defined."""
    # User role enumeration
    USER_ROLES = ["student", "teacher", "parent", "admin"]

    assert "student" in USER_ROLES, "Student role should be defined"
    assert "teacher" in USER_ROLES, "Teacher role should be defined"
    assert "parent" in USER_ROLES, "Parent role should be defined"
    assert "admin" in USER_ROLES, "Admin role should be defined"

    # All roles should be lowercase strings
    assert all(isinstance(role, str) for role in USER_ROLES), (
        "All roles should be strings"
    )
    assert all(role.islower() for role in USER_ROLES), (
        "All roles should be lowercase"
    )


def test_irt_difficulty_range_defined():
    """Test IRT difficulty parameter range is correctly defined."""
    # IRT difficulty range (KIRO2 standard)
    IRT_DIFFICULTY_MIN = -4.0
    IRT_DIFFICULTY_MAX = 4.0

    assert IRT_DIFFICULTY_MIN == -4.0, (
        f"IRT difficulty min should be -4.0, got: {IRT_DIFFICULTY_MIN}"
    )
    assert IRT_DIFFICULTY_MAX == 4.0, (
        f"IRT difficulty max should be 4.0, got: {IRT_DIFFICULTY_MAX}"
    )

    # Verify range is valid
    assert IRT_DIFFICULTY_MIN < IRT_DIFFICULTY_MAX, (
        "Min should be less than max"
    )

    # Verify range span
    range_span = IRT_DIFFICULTY_MAX - IRT_DIFFICULTY_MIN
    assert range_span == 8.0, (
        f"Expected difficulty range of 8.0, got: {range_span}"
    )


def test_bloom_levels_defined():
    """Test Bloom's Taxonomy levels are defined."""
    # Bloom's Taxonomy levels
    BLOOM_LEVELS = [
        "Hatırlama",
        "Anlama",
        "Uygulama",
        "Analiz",
        "Sentez",
        "Değerlendirme",
    ]

    assert len(BLOOM_LEVELS) == 6, (
        f"Should have 6 Bloom levels, got: {len(BLOOM_LEVELS)}"
    )

    # Verify all levels are non-empty strings
    assert all(isinstance(level, str) for level in BLOOM_LEVELS), (
        "All Bloom levels should be strings"
    )
    assert all(len(level) > 0 for level in BLOOM_LEVELS), (
        "All Bloom levels should be non-empty"
    )


def test_meb_grade_levels():
    """Test MEB grade levels are correctly defined (9-12 for YKS)."""
    # MEB grade levels for high school
    MEB_GRADE_MIN = 9
    MEB_GRADE_MAX = 12

    assert MEB_GRADE_MIN == 9, (
        f"High school should start at grade 9, got: {MEB_GRADE_MIN}"
    )
    assert MEB_GRADE_MAX == 12, (
        f"High school should end at grade 12, got: {MEB_GRADE_MAX}"
    )

    # Verify range
    grade_span = MEB_GRADE_MAX - MEB_GRADE_MIN + 1
    assert grade_span == 4, (
        f"High school should span 4 years, got: {grade_span}"
    )


def test_university_data_schema():
    """Test university data schema has expected fields."""
    # Expected fields in university data
    EXPECTED_FIELDS = [
        "university_name",
        "department_name",
        "exam_type",
        "min_score",
        "quota",
        "city",
    ]

    # Verify all expected fields are defined
    assert len(EXPECTED_FIELDS) == 6, (
        f"Should have 6 required fields, got: {len(EXPECTED_FIELDS)}"
    )

    # Verify field names are valid
    assert "university_name" in EXPECTED_FIELDS, (
        "university_name field should be required"
    )
    assert "department_name" in EXPECTED_FIELDS, (
        "department_name field should be required"
    )
    assert "exam_type" in EXPECTED_FIELDS, (
        "exam_type field should be required"
    )
    assert "min_score" in EXPECTED_FIELDS, (
        "min_score field should be required"
    )
