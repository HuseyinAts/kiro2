"""
Turkish NLP Utilities — canonical text normalization.

CRITICAL RULES (CLAUDE.md §Turkish NLP):
1. NFC normalization FIRST (prevents İ decomposition)
2. Turkish mapping: İ→i, I→ı  (NOT İ→I!)
3. Standard lowercase LAST

⚠️ TWO DIFFERENT NORMALIZATION CONTEXTS:
- Free Turkish text (titles, descriptions) → use `normalize_tr()` (Turkish locale)
- Subject/exam identifiers (DB tags) → use `subject_key()` / `subject_db()` (ASCII safe)

Subject identifiers (MATEMATIK, TURKCE, FIZIK...) are stored in DB without dotted-İ
(ASCII variant). Applying Turkish locale rules to them produces "matematık" (dotless ı)
which never matches dict/cache keys written as "matematik". Use the subject helpers below.
"""

import unicodedata


def normalize_tr(text: str) -> str:
    """NFC + Turkish-correct lowercase normalization.

    Use for: search, comparison, deduplication of FREE TURKISH TEXT
    (article titles, descriptions, user input prose).

    DO NOT use for subject identifiers — see `subject_key()` instead.
    """
    if not text:
        return text
    text = unicodedata.normalize("NFC", text)
    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()


def tr_casefold(text: str) -> str:
    """Case-insensitive comparison key for Turkish (alias for normalize_tr)."""
    return normalize_tr(text)


# ---------------------------------------------------------------------------
# Subject identifier normalization (ASCII tags, NOT Turkish prose)
# ---------------------------------------------------------------------------
#
# subject_area / exam_type values in KIRO2 are ASCII identifiers stored in
# DB as UPPERCASE: "MATEMATIK", "TURKCE", "FIZIK", "TYT", "AYT", ...
# They use ASCII I (no dot) — NOT Turkish İ.
#
# Applying `normalize_tr()` to them is WRONG because the I→ı mapping
# produces "matematık" instead of "matematik" → cache/dict miss.
#
# Endpoint Gate Rule (.claude/rules/case-convention.md):
#   Every endpoint that accepts a `subject` / `subject_area` / `exam_type`
#   parameter MUST normalize via `subject_db()` before DB query
#   and `subject_key()` before cache/dict lookup.


def subject_db(subject: str | None) -> str | None:
    """Normalize subject identifier for DB query (UPPERCASE, ASCII safe).

    Use for: SQL `WHERE subject_area = :subject`, DAG `get_subject_topics()`,
    `topic_hierarchy.subject_area` lookups.

    Examples:
        subject_db("matematik")  -> "MATEMATIK"
        subject_db("MATEMATIK")  -> "MATEMATIK"
        subject_db("Matematik")  -> "MATEMATIK"
        subject_db(None)         -> None
    """
    if subject is None:
        return None
    return subject.strip().upper() if subject else subject


def subject_key(subject: str | None) -> str | None:
    """Normalize subject identifier for in-memory dict / cache key (lowercase, ASCII safe).

    Use for: fallback dict lookups, Redis cache keys, BKT/IRT/FSRS algorithm slugs,
    enum value comparisons.

    Examples:
        subject_key("MATEMATIK") -> "matematik"
        subject_key("matematik") -> "matematik"
        subject_key("Matematik") -> "matematik"
        subject_key(None)        -> None
    """
    if subject is None:
        return None
    return subject.strip().lower() if subject else subject
