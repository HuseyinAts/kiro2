#!/usr/bin/env python3
"""
Import d-dataset questions into question_bank table.

Usage:
    cd backend
    python scripts/import_d_dataset.py [--dry-run] [--batch-size 1000] [--jsonl-path PATH]

Reads: d-dataset/eslesmis_sorucevap.jsonl (77,336 questions)
Target: question_bank table (PostgreSQL 15, port 5434)
"""

import argparse
import json
import os
import sys
import unicodedata
import uuid
from collections import Counter
from pathlib import Path
from time import time

# Deterministic namespace for UUID generation
KIRO2_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


# =============================================================================
# Turkish Normalization
# =============================================================================

def normalize_tr(text: str) -> str:
    """Turkish-aware lowercase normalization with NFC."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u0130", "i").replace("I", "\u0131")  # İ→i, I→ı
    return text.lower()


# =============================================================================
# Subject Classification
# =============================================================================

# Order matters: AYT-specific math topics BEFORE generic 'matematik'
SUBJECT_PATTERNS: list[tuple[list[str], str, str | None]] = [
    # AYT-only math subtopics
    (["trigonometri", "t\u00fcrev", "turev", "integral", "logaritma",
      "polinom", "fonksiyon", "diziler", "limit ve s\u00fcreklilik"],
     "MATEMATIK", "AYT"),
    (["kat\u0131 cisim", "kati cisim", "analitik geometri"], "GEOMETRI", "AYT"),
    # Generic subjects
    (["geometri", "\u00fc\u00e7gen", "ucgen", "d\u00f6rtgen", "dortgen"], "GEOMETRI", None),
    (["matematik", "problemler", "say\u0131lar", "sayilar",
      "matemateik", "matemat,k", "matemati\u011fin", "matematig",
      "ilac\u0131", "ilaci"], "MATEMATIK", None),
    (["fizik", "fizipedia", "neofizik"], "FIZIK", None),
    (["kimya", "aromat"], "KIMYA", None),
    (["biyoloji"], "BIYOLOJI", None),
    # TURKCE before EDEBIYAT: "Edebiyat Sokağı Dil Bilgisi" -> TURKCE, not EDEBIYAT
    (["paragraf", "t\u00fcrk\u00e7e", "turkce", "t\u00fcrkce", "dil bilgisi",
      "dilbilgisi", "s\u00f6zc\u00fck", "sozcuk", "anlam",
      "atas\u00f6zleri", "atasozu", "kurgulu"], "TURKCE", "TYT"),
    (["edebiyat"], "EDEBIYAT", "AYT"),
    (["tarih"], "TARIH", None),
    (["co\u011frafya", "cografya"], "COGRAFYA", None),
    (["sosyal"], "SOSYAL", "TYT"),
    (["fen bilim"], "FEN", "TYT"),
    (["ingilizce", "ydt"], "INGILIZCE", "YDT"),
]


def classify_book(book_name: str) -> tuple[str, str]:
    """Classify book into (subject, exam_type) from its name."""
    bn = normalize_tr(book_name)

    # Detect subject
    subject: str | None = None
    default_exam: str | None = None
    for patterns, subj, defexam in SUBJECT_PATTERNS:
        for p in patterns:
            if p in bn:
                subject = subj
                default_exam = defexam
                break
        if subject:
            break

    if subject is None:
        subject = "GENEL"

    # Detect exam type explicitly from name
    # TYT wins over AYT when both present (e.g. "Tyt Ayt Geometri" -> TYT)
    exam: str | None = None
    has_tyt = "tyt" in bn
    has_ayt = "ayt" in bn
    has_ydt = "ydt" in bn
    if has_ydt:
        exam = "YDT"
    elif has_tyt:
        exam = "TYT"
    elif has_ayt:
        exam = "AYT"

    if exam is None:
        exam = default_exam or "TYT"

    return subject, exam


# =============================================================================
# ID Generation
# =============================================================================

def generate_question_id(book_name: str, page: int, q_num: int) -> str:
    """Generate deterministic UUID from question identity triple."""
    key = f"{book_name}|{page}|{q_num}"
    return str(uuid.uuid5(KIRO2_NAMESPACE, key))


def generate_topic_id(subject_code: str) -> str:
    """Generate deterministic UUID for a topic entry."""
    return str(uuid.uuid5(KIRO2_NAMESPACE, f"topic_{subject_code}"))


# =============================================================================
# Default Topics
# =============================================================================

DEFAULT_TOPICS: dict[str, tuple[str, str]] = {
    "MATEMATIK": ("MAT", "Matematik"),
    "GEOMETRI": ("GEO", "Geometri"),
    "FIZIK": ("FIZ", "Fizik"),
    "KIMYA": ("KIM", "Kimya"),
    "BIYOLOJI": ("BIY", "Biyoloji"),
    "EDEBIYAT": ("EDB", "T\u00fcrk Dili ve Edebiyat\u0131"),
    "TURKCE": ("TUR", "T\u00fcrk\u00e7e"),
    "TARIH": ("TAR", "Tarih"),
    "COGRAFYA": ("COG", "Co\u011frafya"),
    "SOSYAL": ("SOS", "Sosyal Bilimler"),
    "FEN": ("FEN", "Fen Bilimleri"),
    "INGILIZCE": ("ING", "\u0130ngilizce"),
    "GENEL": ("GEN", "Genel"),
}

# Fields mapped directly to question_bank columns (excluded from pipeline_metadata)
DIRECT_FIELDS = {"text", "options", "answer", "book_name", "page_number",
                 "question_number", "quality_score", "confidence"}


# =============================================================================
# Row Builder
# =============================================================================

def build_row(entry: dict, subject: str, exam_type: str) -> dict:
    """Transform a JSONL entry into a question_bank INSERT parameter dict."""
    options = entry.get("options", {})
    q_id = generate_question_id(
        entry["book_name"],
        entry["page_number"],
        entry["question_number"],
    )
    topic_code = DEFAULT_TOPICS.get(subject, ("GEN", "Genel"))[0]
    topic_id = generate_topic_id(topic_code)

    # Everything not directly mapped goes into pipeline_metadata
    metadata = {k: v for k, v in entry.items() if k not in DIRECT_FIELDS}

    return {
        "id": q_id,
        "question_text": entry.get("text", ""),
        "option_a": options.get("A", ""),
        "option_b": options.get("B", ""),
        "option_c": options.get("C", ""),
        "option_d": options.get("D", ""),
        "option_e": options.get("E"),
        "correct_answer": entry.get("answer", "A"),
        "primary_topic_id": topic_id,
        # Bloom taxonomy (NOT NULL, defaults until AI classification)
        "bloom_level": 2,
        "bloom_category": "understand",
        "difficulty_level": "MEDIUM",
        # IRT 4PL parameters (NOT NULL, uncalibrated defaults)
        "irt_based_difficulty": "medium",
        "student_success_rate": 0.0,
        "difficulty_update_count": 0,
        "irt_discrimination": 1.0,
        "irt_difficulty": 0.0,
        "irt_guessing": 0.2,
        "irt_upper_asymptote": 1.0,
        "is_calibrated": False,
        "calibration_sample_size": 0,
        "calibration_quality_score": entry.get("confidence") or 0.0,
        # Morphology (NOT NULL, zero until analyzed)
        "morphology_complexity": 0.0,
        "word_count": 0,
        "unique_word_count": 0,
        "average_word_length": 0.0,
        "readability_score": 0.0,
        # Usage statistics (NOT NULL, zero for new questions)
        "times_asked": 0,
        "times_correct": 0,
        "times_wrong": 0,
        "times_skipped": 0,
        "average_response_time": 0.0,
        "median_response_time": 0.0,
        "exposure_rate": 0.0,
        # Classification
        "exam_type": exam_type,
        "subject_area": subject,
        "grade_level": 11,  # Default for YKS prep
        "quality_score": entry.get("quality_score") or 0.0,
        "quality_review_status": "approved",
        "osym_format_compliant": True,
        "is_active": True,
        "is_public": False,
        # Pipeline source tracking
        "source_book": entry.get("book_name"),
        "source_page": entry.get("page_number"),
        "pipeline_metadata": json.dumps(metadata, ensure_ascii=False),
    }


# =============================================================================
# Database Operations
# =============================================================================

def ensure_columns(conn) -> None:
    """Add new columns to question_bank if they don't exist yet."""
    from sqlalchemy import text
    conn.execute(text(
        "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS source_book VARCHAR(300)"
    ))
    conn.execute(text(
        "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS source_page INTEGER"
    ))
    conn.execute(text(
        "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS pipeline_metadata JSONB DEFAULT '{}'"
    ))
    # Index for book-based queries
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_qbank_source_book ON question_bank (source_book)"
    ))


def ensure_topics(conn) -> None:
    """Insert default topic_hierarchy entries (ON CONFLICT skip)."""
    from sqlalchemy import text
    for subject, (code, name_tr) in DEFAULT_TOPICS.items():
        topic_id = generate_topic_id(code)
        conn.execute(text("""
            INSERT INTO topic_hierarchy (
                id, level, code, name_tr, is_active,
                osym_relevance, osym_frequency, total_questions, average_difficulty
            )
            VALUES (:id, 1, :code, :name_tr, true, 0.0, 0, 0, 0.0)
            ON CONFLICT (code) DO NOTHING
        """), {"id": topic_id, "code": code, "name_tr": name_tr})


INSERT_SQL = """
    INSERT INTO question_bank (
        id, question_text, option_a, option_b, option_c, option_d, option_e,
        correct_answer, primary_topic_id,
        bloom_level, bloom_category, difficulty_level,
        irt_based_difficulty, student_success_rate, difficulty_update_count,
        irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote,
        is_calibrated, calibration_sample_size, calibration_quality_score,
        morphology_complexity, word_count, unique_word_count,
        average_word_length, readability_score,
        times_asked, times_correct, times_wrong, times_skipped,
        average_response_time, median_response_time, exposure_rate,
        exam_type, subject_area, grade_level,
        quality_score, quality_review_status, osym_format_compliant,
        is_active, is_public,
        source_book, source_page, pipeline_metadata
    ) VALUES (
        :id, :question_text, :option_a, :option_b, :option_c, :option_d, :option_e,
        :correct_answer, :primary_topic_id,
        :bloom_level, :bloom_category, :difficulty_level,
        :irt_based_difficulty, :student_success_rate, :difficulty_update_count,
        :irt_discrimination, :irt_difficulty, :irt_guessing, :irt_upper_asymptote,
        :is_calibrated, :calibration_sample_size, :calibration_quality_score,
        :morphology_complexity, :word_count, :unique_word_count,
        :average_word_length, :readability_score,
        :times_asked, :times_correct, :times_wrong, :times_skipped,
        :average_response_time, :median_response_time, :exposure_rate,
        :exam_type, :subject_area, :grade_level,
        :quality_score, :quality_review_status, :osym_format_compliant,
        :is_active, :is_public,
        :source_book, :source_page, CAST(:pipeline_metadata AS jsonb)
    )
    ON CONFLICT (id) DO NOTHING
"""


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Import d-dataset \u2192 question_bank")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and classify only, don't touch the database")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--jsonl-path", type=str,
                        default=str(Path(__file__).parent.parent.parent
                                    / "d-dataset" / "eslesmis_sorucevap.jsonl"))
    args = parser.parse_args()

    # Load .env for DATABASE_URL
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:changeme@localhost:5434/kiro2",
    )
    # Force sync driver (psycopg2) — strip asyncpg if present in .env
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    # Fix db name if .env has kiro2_db but actual db is kiro2
    db_url = db_url.replace("/kiro2_db", "/kiro2")

    print("=" * 60)
    print("d-dataset -> question_bank Import")
    print("=" * 60)
    print(f"JSONL : {args.jsonl_path}")
    print(f"DB    : {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print(f"Batch : {args.batch_size}")
    print(f"Dry   : {args.dry_run}")
    print()

    # ---- Phase 1: Parse & Classify ----
    t0 = time()
    rows: list[dict] = []
    subject_counts: Counter[str] = Counter()
    exam_counts: Counter[str] = Counter()
    errors: list[tuple[int, str]] = []

    jsonl_path = Path(args.jsonl_path)
    if not jsonl_path.exists():
        print(f"[ERROR] JSONL not found: {jsonl_path}")
        sys.exit(1)

    with open(jsonl_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
                subject, exam_type = classify_book(entry.get("book_name", ""))
                subject_counts[subject] += 1
                exam_counts[exam_type] += 1
                rows.append(build_row(entry, subject, exam_type))
            except Exception as e:
                errors.append((line_num, str(e)))

    t_parse = time() - t0
    print(f"Parsed {len(rows):,} questions in {t_parse:.1f}s ({len(errors)} errors)")
    print()
    print("Subject distribution:")
    for subj, cnt in subject_counts.most_common():
        print(f"  {subj:15s}: {cnt:6d}")
    print()
    print("Exam type distribution:")
    for exam, cnt in exam_counts.most_common():
        print(f"  {exam:5s}: {cnt:6d}")

    if errors:
        print("\nFirst 5 errors:")
        for ln, err in errors[:5]:
            print(f"  Line {ln}: {err}")

    if args.dry_run:
        print("\n[DRY RUN] No database changes made.")
        return

    # ---- Phase 2: Insert into PostgreSQL ----
    from sqlalchemy import create_engine, text

    engine = create_engine(db_url)

    with engine.begin() as conn:
        # Ensure columns exist
        print("\nEnsuring new columns...")
        ensure_columns(conn)
        print("  source_book, source_page, pipeline_metadata OK")

        # Ensure topics exist
        print("Creating default topics...")
        ensure_topics(conn)
        print(f"  {len(DEFAULT_TOPICS)} topics ensured")

        # Batch insert
        print(f"\nInserting {len(rows):,} questions (batch={args.batch_size})...")
        inserted = 0
        skipped = 0

        for i in range(0, len(rows), args.batch_size):
            batch = rows[i : i + args.batch_size]
            for row in batch:
                result = conn.execute(text(INSERT_SQL), row)
                if result.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1

            done = i + len(batch)
            pct = done / len(rows) * 100
            print(f"  [{pct:5.1f}%] {done:,}/{len(rows):,} "
                  f"({inserted:,} new, {skipped:,} dup)")

    # ---- Phase 3: Verify ----
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM question_bank")).scalar()
        by_subject = conn.execute(text(
            "SELECT subject_area, COUNT(*) FROM question_bank "
            "GROUP BY subject_area ORDER BY COUNT(*) DESC"
        )).fetchall()

    engine.dispose()

    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"Total in question_bank: {total:,}")
    print(f"Inserted this run    : {inserted:,}")
    print(f"Skipped (duplicate)  : {skipped:,}")
    print(f"Parse errors         : {len(errors)}")
    print("\nBy subject:")
    for subj, cnt in by_subject:
        print(f"  {subj:15s}: {cnt:6d}")
    print(f"\nDone in {time() - t0:.1f}s")


if __name__ == "__main__":
    main()
