"""
Subject Classification Validator for KIRO2 Question Bank.

Detects and fixes misclassified questions:
1. Math questions in non-math subjects (TURKCE, EDEBIYAT, TARIH, etc.)
2. GENEL category exclusion from subject-specific exams
3. Questions lacking passage text ("parcaya gore" without passage)

Usage:
    # Dry run (report only)
    python backend/scripts/validate_subject_classification.py --dry-run

    # Fix misclassified questions (deactivate)
    python backend/scripts/validate_subject_classification.py --fix

    # Reclassify instead of deactivate
    python backend/scripts/validate_subject_classification.py --fix --reclassify
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg

DB_URL = "postgresql://postgres:postgres@localhost:5434/kiro2"

# Subject-specific keyword patterns for classification validation
MATH_INDICATORS = [
    # LaTeX/formula patterns
    "$", "\\frac", "\\sqrt", "\\int",
    # Turkish math keywords
    "denklem", "fonksiyon", "integral", "turev",
    "logaritma", "polinom", "matris",
    # Question patterns that are clearly math
    "hesaplay", "toplami kac", "sonucu kac",
]

MATH_STRONG_INDICATORS = [
    # These alone confirm math (not just mention)
    "denklemin kok", "fonksiyonun grafig",
    "integral", "turev", "polinom",
    "$a_", "$x^", "$\\frac", "$\\sqrt",
    "2x +", "3x -", "x^2",
    "matematiksel", "sayilarin toplami",
]

# Subjects where math content is WRONG
NON_MATH_SUBJECTS = ["TURKCE", "EDEBIYAT", "TARIH", "COGRAFYA", "SOSYAL"]

# Subjects where math content is EXPECTED
MATH_SUBJECTS = ["MATEMATIK", "GEOMETRI", "FIZIK", "KIMYA", "FEN"]


async def get_connection():
    return await asyncpg.connect(DB_URL)


async def find_math_in_non_math(conn) -> list[dict]:
    """Find questions with math content in non-math subjects."""
    # Build WHERE clause for math indicators
    like_clauses = []
    for indicator in MATH_INDICATORS:
        escaped = indicator.replace("'", "''")
        like_clauses.append(f"LOWER(question_text) LIKE '%{escaped}%'")

    like_sql = " OR ".join(like_clauses)

    subjects_sql = ", ".join(f"'{s}'" for s in NON_MATH_SUBJECTS)

    query = f"""
        SELECT id, subject_area, exam_type, source_book,
               LEFT(question_text, 200) as preview,
               question_text
        FROM question_bank
        WHERE is_active = true
          AND subject_area IN ({subjects_sql})
          AND ({like_sql})
        ORDER BY subject_area, id
    """

    rows = await conn.fetch(query)

    # Filter for strong indicators (reduce false positives)
    misclassified = []
    for row in rows:
        text_lower = row["question_text"].lower()
        strong_count = sum(1 for s in MATH_STRONG_INDICATORS if s.lower() in text_lower)
        weak_count = sum(1 for w in MATH_INDICATORS if w.lower() in text_lower)

        # Strong indicator = definitely misclassified
        # Multiple weak indicators = likely misclassified
        if strong_count >= 1 or weak_count >= 3:
            misclassified.append({
                "id": str(row["id"]),
                "subject_area": row["subject_area"],
                "exam_type": row["exam_type"],
                "source_book": row["source_book"],
                "preview": row["preview"],
                "strong_count": strong_count,
                "weak_count": weak_count,
            })

    return misclassified


async def find_genel_questions(conn) -> int:
    """Count questions in GENEL category (should not be in subject-specific exams)."""
    row = await conn.fetchrow(
        "SELECT COUNT(*) as cnt FROM question_bank WHERE is_active = true AND subject_area = 'GENEL'"
    )
    return row["cnt"]


async def find_passage_questions_without_passage(conn) -> list[dict]:
    """Find 'parcaya gore' questions that lack passage text."""
    query = """
        SELECT id, subject_area, LEFT(question_text, 200) as preview
        FROM question_bank
        WHERE is_active = true
          AND (LOWER(question_text) LIKE '%parcaya gore%'
               OR LOWER(question_text) LIKE '%paragraf%gore%'
               OR LOWER(question_text) LIKE '%metne gore%'
               OR LOWER(question_text) LIKE '%bu parcada%')
          AND LENGTH(question_text) < 300
        ORDER BY subject_area
        LIMIT 50
    """
    rows = await conn.fetch(query)
    return [dict(r) for r in rows]


async def deactivate_questions(conn, question_ids: list[str]):
    """Deactivate misclassified questions (reversible)."""
    if not question_ids:
        return 0

    query = """
        UPDATE question_bank
        SET is_active = false
        WHERE id = ANY($1::uuid[])
          AND is_active = true
    """
    result = await conn.execute(query, question_ids)
    return int(result.split()[-1])


async def reclassify_questions(conn, question_ids: list[str], new_subject: str):
    """Reclassify misclassified questions to correct subject."""
    if not question_ids:
        return 0

    query = """
        UPDATE question_bank
        SET subject_area = $1
        WHERE id = ANY($2::uuid[])
          AND is_active = true
    """
    result = await conn.execute(query, new_subject, question_ids)
    return int(result.split()[-1])


async def main():
    parser = argparse.ArgumentParser(description="Validate subject classification")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no changes")
    parser.add_argument("--fix", action="store_true", help="Deactivate misclassified questions")
    parser.add_argument("--reclassify", action="store_true", help="Reclassify instead of deactivate")
    args = parser.parse_args()

    if not args.dry_run and not args.fix:
        args.dry_run = True  # Default to dry-run

    conn = await get_connection()

    try:
        print("=" * 60)
        print("KIRO2 Subject Classification Validator")
        print("=" * 60)

        # 1. Math in non-math subjects
        print("\n1. Math questions in non-math subjects:")
        misclassified = await find_math_in_non_math(conn)

        by_subject = {}
        for q in misclassified:
            by_subject.setdefault(q["subject_area"], []).append(q)

        for subject, questions in sorted(by_subject.items()):
            print(f"\n  {subject}: {len(questions)} misclassified")
            for q in questions[:3]:
                preview = q["preview"][:80].replace("\n", " ")
                print(f"    - [{q['source_book'][:30]}] {preview}...")

        total_misclassified = len(misclassified)
        print(f"\n  TOTAL: {total_misclassified} misclassified questions")

        # 2. GENEL category
        genel_count = await find_genel_questions(conn)
        print(f"\n2. GENEL category: {genel_count} questions (mixed subjects)")
        print("   These should be excluded from subject-specific exams")

        # 3. Passage questions without passage
        print("\n3. 'Parcaya gore' questions with short text (possibly missing passage):")
        passage_questions = await find_passage_questions_without_passage(conn)
        print(f"   Found: {len(passage_questions)} potentially affected")
        for q in passage_questions[:5]:
            preview = str(q["preview"])[:80].replace("\n", " ")
            print(f"    - [{q['subject_area']}] {preview}...")

        # Fix if requested
        if args.fix:
            print("\n" + "=" * 60)
            print("APPLYING FIXES")
            print("=" * 60)

            misclassified_ids = [q["id"] for q in misclassified]

            if args.reclassify:
                # Reclassify math questions to MATEMATIK
                count = await reclassify_questions(conn, misclassified_ids, "MATEMATIK")
                print(f"\n  Reclassified {count} questions to MATEMATIK")
            else:
                # Deactivate misclassified
                count = await deactivate_questions(conn, misclassified_ids)
                print(f"\n  Deactivated {count} misclassified questions")

            print("\n  Done! Changes are reversible via:")
            print("  UPDATE question_bank SET is_active = true WHERE id IN (...)")

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  Math in non-math subjects: {total_misclassified}")
        print(f"  GENEL (mixed) category: {genel_count}")
        print(f"  Short passage questions: {len(passage_questions)}")
        print(f"\n  RECOMMENDED: {'--fix to apply' if args.dry_run else 'Applied!'}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
