"""
Seed topic_hierarchy with YKS Matematik sub-topics (level-2)
and update question_bank.primary_topic_id based on source_book + question_text matching.

Usage:
    python backend/scripts/seed_topic_hierarchy.py --dry-run   # Preview changes
    python backend/scripts/seed_topic_hierarchy.py --apply      # Apply changes

Idempotent: safe to run multiple times (ON CONFLICT DO NOTHING + already-updated check).
"""

import argparse
import sys
import unicodedata
import uuid

import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "dbname": "kiro2",
    "user": "postgres",
}

# Matematik parent
MATEMATIK_PARENT_ID = "c3261158-b5b3-5b21-aba0-926d0391c800"

# Level-2 alt-konular (TYT + AYT Matematik)
SUBTOPICS = [
    ("MAT.SAY", "Sayılar ve İşlemler", "Numbers and Operations"),
    ("MAT.CRP", "Çarpanlara Ayırma", "Factoring"),
    ("MAT.DNK", "Denklemler", "Equations"),
    ("MAT.EST", "Eşitsizlikler", "Inequalities"),
    ("MAT.MTL", "Mutlak Değer", "Absolute Value"),
    ("MAT.FON", "Fonksiyonlar", "Functions"),
    ("MAT.POL", "Polinomlar", "Polynomials"),
    ("MAT.PRM", "Permütasyon", "Permutation"),
    ("MAT.KMB", "Kombinasyon", "Combination"),
    ("MAT.OLS", "Olasılık", "Probability"),
    ("MAT.TRG", "Trigonometri", "Trigonometry"),
    ("MAT.TRV", "Türev", "Derivative"),
    ("MAT.INT", "İntegral", "Integral"),
    ("MAT.LOG", "Logaritma", "Logarithm"),
    ("MAT.USL", "Üslü ve Köklü Sayılar", "Exponents and Radicals"),
    ("MAT.LMT", "Limit ve Süreklilik", "Limit and Continuity"),
    ("MAT.PRB", "Problemler", "Word Problems"),
    ("MAT.IST", "İstatistik", "Statistics"),
]

# source_book keyword -> subtopic code mapping
# Turkish lowercase keywords to match in source_book field
BOOK_KEYWORD_MAP = {
    "fonksiyon": "MAT.FON",
    "türev": "MAT.TRV",
    "integral": "MAT.INT",
    "polinom": "MAT.POL",
    "trigonometri": "MAT.TRG",
    "olasılık": "MAT.OLS",
    "olasilik": "MAT.OLS",
    "logaritma": "MAT.LOG",
    "denklem": "MAT.DNK",
    "eşitsizlik": "MAT.EST",
    "esitsizlik": "MAT.EST",
    "çarpan": "MAT.CRP",
    "carpan": "MAT.CRP",
    "permütasyon": "MAT.PRM",
    "permutasyon": "MAT.PRM",
    "kombinasyon": "MAT.KMB",
    "istatistik": "MAT.IST",
    "limit": "MAT.LMT",
    "sayılar": "MAT.SAY",
    "mutlak": "MAT.MTL",
    "üslü": "MAT.USL",
    "köklü": "MAT.USL",
    "problem": "MAT.PRB",
}

# question_text keyword -> subtopic code mapping
# More restrictive than book keywords to reduce false positives
TEXT_KEYWORD_MAP = {
    "türev": "MAT.TRV",
    "integral": "MAT.INT",
    "polinom": "MAT.POL",
    "trigonometri": "MAT.TRG",
    "logaritma": "MAT.LOG",
    "olasılık": "MAT.OLS",
    "olasilik": "MAT.OLS",
    "permütasyon": "MAT.PRM",
    "permutasyon": "MAT.PRM",
    "kombinasyon": "MAT.KMB",
    "eşitsizlik": "MAT.EST",
    "esitsizlik": "MAT.EST",
    "istatistik": "MAT.IST",
    "fonksiyon": "MAT.FON",
    "çarpanlara ayır": "MAT.CRP",
    "çarpanlar": "MAT.CRP",
    "mutlak değer": "MAT.MTL",
    "limit": "MAT.LMT",
}


def normalize_tr(text: str) -> str:
    """NFC normalize + Turkish lowercase."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()


def seed_subtopics(cur, dry_run: bool) -> int:
    """Insert level-2 subtopics under Matematik."""
    inserted = 0
    for code, name_tr, name_en in SUBTOPICS:
        topic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kiro2.topic.{code}"))
        if dry_run:
            print(f"  [DRY] INSERT topic: {code} = {name_tr} (id={topic_id})")
            inserted += 1
        else:
            cur.execute(
                """
                INSERT INTO topic_hierarchy
                    (id, level, parent_id, code, name_tr, name_en,
                     osym_relevance, osym_frequency, total_questions,
                     average_difficulty, is_active)
                VALUES (%s, 2, %s, %s, %s, %s, 0.5, 0, 0, 0.5, true)
                ON CONFLICT (code) DO NOTHING
                """,
                (topic_id, MATEMATIK_PARENT_ID, code, name_tr, name_en),
            )
            if cur.rowcount > 0:
                inserted += 1
                print(f"  INSERT: {code} = {name_tr}")
            else:
                print(f"  SKIP (exists): {code} = {name_tr}")
    return inserted


def get_subtopic_ids(cur) -> dict[str, str]:
    """Get code -> id mapping for level-2 subtopics."""
    cur.execute(
        "SELECT code, id FROM topic_hierarchy WHERE level = 2 AND parent_id = %s",
        (MATEMATIK_PARENT_ID,),
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def match_single_keyword(text: str, keyword_map: dict[str, str]) -> str | None:
    """Return subtopic code if exactly ONE keyword matches, else None."""
    text_lower = normalize_tr(text)
    matches = set()
    for keyword, code in keyword_map.items():
        if keyword in text_lower:
            matches.add(code)
    return matches.pop() if len(matches) == 1 else None


def update_by_source_book(cur, subtopic_ids: dict[str, str], dry_run: bool) -> int:
    """Phase A: Update primary_topic_id based on source_book keyword match."""
    # Get all active math questions still pointing to level-1 Matematik
    cur.execute(
        """
        SELECT id, source_book FROM question_bank
        WHERE is_active = true
          AND subject_area = 'MATEMATIK'
          AND primary_topic_id = %s
          AND source_book IS NOT NULL
          AND source_book != ''
        """,
        (MATEMATIK_PARENT_ID,),
    )
    rows = cur.fetchall()
    updated = 0
    for qid, source_book in rows:
        code = match_single_keyword(source_book, BOOK_KEYWORD_MAP)
        if code and code in subtopic_ids:
            if dry_run:
                updated += 1
            else:
                cur.execute(
                    "UPDATE question_bank SET primary_topic_id = %s WHERE id = %s",
                    (subtopic_ids[code], qid),
                )
                updated += cur.rowcount
    return updated


def update_by_question_text(cur, subtopic_ids: dict[str, str], dry_run: bool) -> int:
    """Phase B: Update remaining questions based on question_text keyword match."""
    # Only questions still at level-1 (not updated by Phase A)
    cur.execute(
        """
        SELECT id, question_text FROM question_bank
        WHERE is_active = true
          AND subject_area = 'MATEMATIK'
          AND primary_topic_id = %s
          AND question_text IS NOT NULL
          AND question_text != ''
        """,
        (MATEMATIK_PARENT_ID,),
    )
    rows = cur.fetchall()
    updated = 0
    for qid, question_text in rows:
        code = match_single_keyword(question_text, TEXT_KEYWORD_MAP)
        if code and code in subtopic_ids:
            if dry_run:
                updated += 1
            else:
                cur.execute(
                    "UPDATE question_bank SET primary_topic_id = %s WHERE id = %s",
                    (subtopic_ids[code], qid),
                )
                updated += cur.rowcount
    return updated


def main():
    parser = argparse.ArgumentParser(description="Seed topic_hierarchy subtopics")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Preview without changes")
    group.add_argument("--apply", action="store_true", help="Apply changes to DB")
    args = parser.parse_args()

    dry_run = args.dry_run

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cur = conn.cursor()

        # Verify Matematik parent exists
        cur.execute(
            "SELECT id, name_tr FROM topic_hierarchy WHERE id = %s",
            (MATEMATIK_PARENT_ID,),
        )
        parent = cur.fetchone()
        if not parent:
            print(f"ERROR: Matematik parent {MATEMATIK_PARENT_ID} not found!")
            sys.exit(1)
        print(f"Parent: {parent[1]} (id={parent[0]})")

        # Step 1: Seed subtopics
        print(f"\n{'[DRY-RUN] ' if dry_run else ''}Step 1: Seeding subtopics...")
        inserted = seed_subtopics(cur, dry_run)
        print(f"  -> {inserted} subtopics {'would be ' if dry_run else ''}inserted")

        if not dry_run:
            conn.commit()

        # Get subtopic IDs (need real IDs for update phase)
        if dry_run:
            # Generate deterministic IDs for preview
            subtopic_ids = {
                code: str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kiro2.topic.{code}"))
                for code, _, _ in SUBTOPICS
            }
        else:
            subtopic_ids = get_subtopic_ids(cur)

        # Count questions at level-1
        cur.execute(
            "SELECT COUNT(*) FROM question_bank WHERE is_active = true AND subject_area = 'MATEMATIK' AND primary_topic_id = %s",
            (MATEMATIK_PARENT_ID,),
        )
        total_at_level1 = cur.fetchone()[0]
        print(f"\nQuestions at level-1 Matematik: {total_at_level1}")

        # Step 2A: Update by source_book
        print(f"\n{'[DRY-RUN] ' if dry_run else ''}Step 2A: source_book matching...")
        book_updated = update_by_source_book(cur, subtopic_ids, dry_run)
        print(f"  -> {book_updated} questions {'would be ' if dry_run else ''}updated")

        if not dry_run:
            conn.commit()

        # Step 2B: Update by question_text
        print(f"\n{'[DRY-RUN] ' if dry_run else ''}Step 2B: question_text matching...")
        text_updated = update_by_question_text(cur, subtopic_ids, dry_run)
        print(f"  -> {text_updated} questions {'would be ' if dry_run else ''}updated")

        if not dry_run:
            conn.commit()

        # Summary
        total_updated = book_updated + text_updated
        remaining = total_at_level1 - total_updated
        pct = (total_updated / total_at_level1 * 100) if total_at_level1 > 0 else 0
        print(f"\n{'=' * 50}")
        print(f"Summary {'(DRY-RUN)' if dry_run else ''}:")
        print(f"  Subtopics inserted: {inserted}")
        print(f"  Questions updated (source_book): {book_updated}")
        print(f"  Questions updated (question_text): {text_updated}")
        print(f"  Total updated: {total_updated} ({pct:.1f}%)")
        print(f"  Remaining at level-1: {remaining}")

        if not dry_run:
            # Show distribution
            cur.execute(
                """
                SELECT th.code, th.name_tr, COUNT(qb.id) as cnt
                FROM topic_hierarchy th
                LEFT JOIN question_bank qb ON qb.primary_topic_id = th.id AND qb.is_active = true
                WHERE th.level = 2 AND th.parent_id = %s
                GROUP BY th.code, th.name_tr
                ORDER BY cnt DESC
                """,
                (MATEMATIK_PARENT_ID,),
            )
            print("\nDistribution:")
            for code, name, cnt in cur.fetchall():
                print(f"  {code:10s} {name:25s} {cnt:6d}")

            # Update total_questions count
            cur.execute(
                """
                UPDATE topic_hierarchy th
                SET total_questions = sub.cnt
                FROM (
                    SELECT qb.primary_topic_id, COUNT(*) as cnt
                    FROM question_bank qb
                    WHERE qb.is_active = true
                    GROUP BY qb.primary_topic_id
                ) sub
                WHERE th.id = sub.primary_topic_id AND th.level = 2
                """
            )
            conn.commit()
            print("\ntotal_questions counts updated.")

    finally:
        conn.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
