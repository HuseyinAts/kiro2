"""
Deactivate garbage questions in the 'questions' table.

Detects and deactivates questions that should not appear in exams:
- OCR template/prompt leaks
- All options identical or meaningless
- Visual-dependent questions without images
- Wrong subject (non-math content in math questions)
- Hallucinated/nonsensical text
- Too-short or contextless questions

Usage:
    python backend/scripts/deactivate_bad_questions.py --dry-run   # Report only
    python backend/scripts/deactivate_bad_questions.py              # Deactivate
    python backend/scripts/deactivate_bad_questions.py --table question_bank  # Target question_bank
"""

import argparse
import os
import re
import sys
from collections import defaultdict

import psycopg2

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5434/kiro2",
)

# ── Pattern Definitions ──────────────────────────────────────────────────────

OCR_TEMPLATE_PATTERNS = [
    r"Görseldeki tüm metni",
    r"JSON formatında çıkar",
    r"dikkatli oku ve",
    r"aşağıdaki metni analiz et",
    r"OCR çıktısı",
    r"image contains",
    r"screenshot",
    r"Lütfen aşağıdaki seçeneklerden doğru yanıt seçiniz",
]

HALLUCINATION_PATTERNS = [
    r"comme\s+un[e]?\s+autre",
    r"personne\s+ne\s+peut",
    r"général\s+de\s+la",
    r"c['']est\s+un[e]?",
    r"il\s+est\s+important\s+de\s+noter",
    r"(.{10,}?)\1{3,}",  # Same phrase repeated 4+ times
]

# Keywords that indicate wrong subject (should NOT appear in matematik questions)
WRONG_SUBJECT_KEYWORDS_MATEMATIK = [
    "fosil", "fosfor", "Rosa Luxemburg", "politika siyaset",
    "cinsiyet eşitliği", "ekonomi politikası",
    "fotosentez", "klorofil", "mitoz", "mayoz", "hücre bölünmesi",
    "Öğrenme Alanı", "Öğrenme Çıktıları", "Dersin Amacı",
    "kromozom", "genetik", "evrim",
]

# Visual reference phrases (question references a figure but has no image)
VISUAL_REFERENCE_PATTERNS = [
    r"[Şş]ekil(?:deki|de)",
    r"[Gg]rafik(?:teki|te|deki|de)",
    r"[Tt]ablo(?:daki|da|deki|de)",
    r"[Yy]ukarıdaki (?:şekil|grafik|tablo|diyagram|resim)",
    r"[Aa]şağıdaki (?:şekil|grafik|tablo|diyagram|resim)",
    r"[Kk]ırmızı renkli parçanın",
    r"[Tt]aralı (?:bölge|alan)",
    r"[Nn]oktalı çizgi",
    r"[Gg]österilen (?:şekil|grafik)",
]

MIN_QUESTION_TEXT_LENGTH = 20
MIN_OPTION_LENGTH = 1


def parse_db_url(url: str) -> dict:
    """Parse DATABASE_URL into psycopg2 connection params."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5434,
        "dbname": parsed.path.lstrip("/") or "kiro2",
        "user": parsed.username or "postgres",
        "password": parsed.password or "postgres",
    }


def check_ocr_template(text: str) -> str | None:
    for pattern in OCR_TEMPLATE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return f"OCR template: {pattern}"
    return None


def check_hallucination(text: str) -> str | None:
    for pattern in HALLUCINATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return f"Hallucination: {pattern}"
    return None


def check_wrong_subject(text: str, subject: str) -> str | None:
    if subject != "matematik":
        return None
    text_lower = text.lower()
    for kw in WRONG_SUBJECT_KEYWORDS_MATEMATIK:
        if kw.lower() in text_lower:
            return f"Wrong subject keyword: {kw}"
    return None


def check_visual_without_image(text: str, image_url: str | None) -> str | None:
    if image_url:
        return None
    for pattern in VISUAL_REFERENCE_PATTERNS:
        if re.search(pattern, text):
            return f"Visual ref without image: {pattern}"
    return None


def check_short_text(text: str) -> str | None:
    if len(text.strip()) < MIN_QUESTION_TEXT_LENGTH:
        return f"Too short: {len(text.strip())} chars"
    return None


def check_identical_options(opt_a: str, opt_b: str, opt_c: str, opt_d: str) -> str | None:
    opts = [opt_a.strip(), opt_b.strip(), opt_c.strip(), opt_d.strip()]
    if len(set(opts)) == 1:
        return "All 4 options identical"
    return None


def check_empty_options(opt_a: str, opt_b: str, opt_c: str, opt_d: str) -> str | None:
    for label, opt in [("A", opt_a), ("B", opt_b), ("C", opt_c), ("D", opt_d)]:
        if not opt or len(opt.strip()) < MIN_OPTION_LENGTH:
            return f"Empty option {label}"
    return None


def analyze_question(row: dict) -> str | None:
    """Return a reason string if question is bad, None if ok."""
    text = row["question_text"] or ""
    image_url = row.get("question_image_url")
    subject = (row.get("subject_area") or "").lower()
    opt_a = row.get("option_a") or ""
    opt_b = row.get("option_b") or ""
    opt_c = row.get("option_c") or ""
    opt_d = row.get("option_d") or ""

    checks = [
        check_ocr_template(text),
        check_hallucination(text),
        check_wrong_subject(text, subject),
        check_visual_without_image(text, image_url),
        check_short_text(text),
        check_identical_options(opt_a, opt_b, opt_c, opt_d),
        check_empty_options(opt_a, opt_b, opt_c, opt_d),
    ]

    for reason in checks:
        if reason:
            return reason
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Detect and deactivate garbage questions"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Only report, do not modify database"
    )
    parser.add_argument(
        "--table", default="question_bank",
        choices=["questions", "question_bank"],
        help="Which table to clean (default: question_bank)"
    )
    parser.add_argument(
        "--subject", default=None,
        help="Filter by subject_area (e.g. matematik)"
    )
    args = parser.parse_args()

    table = args.table
    active_col = "aktif" if table == "questions" else "is_active"
    image_col = "question_image_url"

    conn_params = parse_db_url(DB_URL)
    print(f"Connecting to {conn_params['host']}:{conn_params['port']}/{conn_params['dbname']}")
    conn = psycopg2.connect(**conn_params)

    try:
        cur = conn.cursor()

        # Build WHERE clause
        where_parts = [f"{active_col} = TRUE"]
        params: list = []
        if args.subject:
            where_parts.append("UPPER(subject_area) = %s")
            params.append(args.subject.upper())

        where_clause = " AND ".join(where_parts)

        cur.execute(
            f"SELECT id, question_text, {image_col}, subject_area, "
            f"option_a, option_b, option_c, option_d "
            f"FROM {table} WHERE {where_clause}",
            params,
        )

        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        print(f"Loaded {len(rows):,} active questions from '{table}'")

        bad_ids: list[str] = []
        category_counts: dict[str, int] = defaultdict(int)
        examples: dict[str, list] = defaultdict(list)

        for row in rows:
            reason = analyze_question(row)
            if reason:
                bad_ids.append(row["id"])
                # Extract category (before colon)
                cat = reason.split(":")[0].strip()
                category_counts[cat] += 1
                if len(examples[cat]) < 3:
                    preview = (row["question_text"] or "")[:80].replace("\n", " ")
                    examples[cat].append(f"  {row['id'][:8]}... | {preview}")

        # Report
        print(f"\n{'='*60}")
        print(f"GARBAGE QUESTION REPORT — table: {table}")
        print(f"{'='*60}")
        print(f"Total active:     {len(rows):,}")
        print(f"Garbage detected: {len(bad_ids):,}")
        print(f"Clean remaining:  {len(rows) - len(bad_ids):,}")
        print()

        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            print(f"  [{count:>4}] {cat}")
            for ex in examples[cat]:
                print(f"         {ex}")
            print()

        if args.dry_run:
            print("DRY RUN — no changes made.")
            print(f"Run without --dry-run to deactivate {len(bad_ids)} questions.")
        elif bad_ids:
            # Deactivate in batches
            batch_size = 500
            for i in range(0, len(bad_ids), batch_size):
                batch = bad_ids[i : i + batch_size]
                placeholders = ",".join(["%s"] * len(batch))
                cur.execute(
                    f"UPDATE {table} SET {active_col} = FALSE "
                    f"WHERE id IN ({placeholders})",
                    batch,
                )
            conn.commit()
            print(f"DEACTIVATED {len(bad_ids)} questions.")
        else:
            print("No garbage questions found. Database is clean.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
