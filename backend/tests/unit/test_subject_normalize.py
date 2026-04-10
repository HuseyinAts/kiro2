"""
Regression: subject_db / subject_key — ASCII identifier normalization.

These helpers exist because `normalize_tr()` (Turkish locale) maps I → ı,
producing "matematık" for "MATEMATIK". DB stores ASCII "MATEMATIK" without
dotted-İ, so applying Turkish locale to it breaks dict/cache lookups.

Pattern ref: .claude/rules/case-convention.md (Endpoint Gate)
Root cause: Session 134 — GF7 video fallback returns success:false
            for UPPERCASE input because of normalize_tr I → ı mapping.
"""

from __future__ import annotations

from core.turkish_nlp_utils import normalize_tr, subject_db, subject_key

# ---------------------------------------------------------------------------
# subject_db — UPPERCASE for DB query
# ---------------------------------------------------------------------------


def test_subject_db_uppercases_lowercase():
    assert subject_db("matematik") == "MATEMATIK"


def test_subject_db_idempotent_on_uppercase():
    assert subject_db("MATEMATIK") == "MATEMATIK"


def test_subject_db_strips_whitespace():
    assert subject_db("  matematik  ") == "MATEMATIK"


def test_subject_db_passes_none_through():
    assert subject_db(None) is None


def test_subject_db_passes_empty_through():
    assert subject_db("") == ""


# ---------------------------------------------------------------------------
# subject_key — lowercase for dict / cache key
# ---------------------------------------------------------------------------


def test_subject_key_lowercases_uppercase():
    """The bug we're fixing: MATEMATIK must NOT become matematık."""
    assert subject_key("MATEMATIK") == "matematik"


def test_subject_key_idempotent_on_lowercase():
    assert subject_key("matematik") == "matematik"


def test_subject_key_strips_whitespace():
    assert subject_key("  Matematik  ") == "matematik"


def test_subject_key_passes_none_through():
    assert subject_key(None) is None


# ---------------------------------------------------------------------------
# Round-trip — both helpers must be deterministic across case variations
# ---------------------------------------------------------------------------


def test_round_trip_db_then_key_stable():
    """DB → key normalization should be consistent regardless of input case."""
    cases = ["matematik", "MATEMATIK", "Matematik", "  matematik  "]
    db_results = {subject_db(c) for c in cases}
    key_results = {subject_key(c) for c in cases}
    assert db_results == {"MATEMATIK"}
    assert key_results == {"matematik"}


# ---------------------------------------------------------------------------
# Documentation test: why we don't use normalize_tr() for subject identifiers
# ---------------------------------------------------------------------------


def test_normalize_tr_breaks_subject_keys_documented():
    """Documents why subject_key() exists.

    normalize_tr() applies Turkish locale (I → ı). For ASCII identifier
    "MATEMATIK" this produces "matematık" (dotless ı), which is NOT what
    dict keys expect ("matematik" with dotted i).
    """
    assert normalize_tr("MATEMATIK") == "matematık"  # Wrong for dict key
    assert subject_key("MATEMATIK") == "matematik"  # Correct for dict key
    assert normalize_tr("MATEMATIK") != subject_key("MATEMATIK")
