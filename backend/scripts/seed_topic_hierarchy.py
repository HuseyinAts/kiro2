"""
Seed topic_hierarchy with YKS Matematik sub-topics (level-2)
and update question_bank.primary_topic_id based on source_book + question_text matching.

Usage:
    python backend/scripts/seed_topic_hierarchy.py --dry-run   # Phase 1: keyword matching
    python backend/scripts/seed_topic_hierarchy.py --apply      # Phase 1: apply
    python backend/scripts/seed_topic_hierarchy.py --phase2 --dry-run  # Phase 2: regex patterns
    python backend/scripts/seed_topic_hierarchy.py --phase2 --apply    # Phase 2: apply

Idempotent: safe to run multiple times (ON CONFLICT DO NOTHING + already-updated check).
"""

import argparse
import os
import re
import sys
import unicodedata
import uuid

import psycopg2

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5434")),
    "dbname": os.environ.get("DB_NAME", "kiro2"),
    "user": os.environ.get("DB_USER", "postgres"),
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

# Phase 2: Additional subtopics discovered by microscopic analysis
PHASE2_SUBTOPICS = [
    ("MAT.GEO", "Geometri", "Geometry"),
    ("MAT.DIZ", "Diziler ve Seriler", "Sequences and Series"),
]

# Phase 2: Regex patterns for deeper question_text matching
# Each key is a subtopic code, value is list of regex patterns
# A question matches a code if ANY of its patterns match
REGEX_PATTERNS: dict[str, list[str]] = {
    "MAT.TRG": [
        r"\bsin\b",
        r"\bcos\b",
        r"\btan\b",
        r"cosec",
        r"cotan",
        r"trigonometr",
        r"tanjant",
        r"arctan",
    ],
    "MAT.FON": [r"f\s*\(", r"g\s*\(", r"h\s*\(\s*[a-zıüöşçğ0-9]", r"fonksiyon"],
    "MAT.POL": [r"polinom", r"dereceli\s+ifade"],
    "MAT.LOG": [r"\blog\b", r"\bln\b", r"logaritma"],
    "MAT.LMT": [r"\blim\b", r"limit"],
    "MAT.INT": [r"∫", r"integral", r"antitürev"],
    "MAT.TRV": [r"türev", r"dy/dx", r"d/dx", r"f\s*'\s*\("],
    "MAT.OLS": [r"olasılık", r"olasilik", r"ihtimal"],
    "MAT.PRM": [r"permütasyon", r"permutasyon"],
    "MAT.KMB": [r"kombinasyon"],
    "MAT.SAY": [
        r"asal\s+sayı",
        r"tam\s+sayı",
        r"doğal\s+sayı",
        r"bölünebil",
        r"\bebob\b",
        r"\bekok\b",
        r"rasyonel",
        r"irrasyonel",
    ],
    "MAT.PRB": [
        r"havuz",
        r"işçi",
        r"karışım",
        r"yüzde",
        r"kâr",
        r"zarar",
        r"hız.*?mesafe",
        r"faiz",
    ],
    "MAT.EST": [r"eşitsizli[kğ]"],
    "MAT.DNK": [r"denklem\w*\s*(çöz|sistem|kök)"],
    "MAT.MTL": [r"mutlak\s+değer"],
    "MAT.USL": [r"üslü", r"köklü", r"karekök", r"√"],
    "MAT.IST": [
        r"istatistik",
        r"aritmetik\s+ortalama",
        r"ortalama\w*\s+(not|puan|ya[şs]|boy|kilo|s[ıi]cakl[ıi]k|skor|de[gğ]er|a[gğ][ıi]rl[ıi]k)",
        r"medyan",
        r"standart\s+sapma",
        r"varyans",
        r"histogram",
        r"çeyrekler\s+açıklığı",
        r"frekans\s+tablo",
    ],
    "MAT.CRP": [r"çarpanlar\w*\s*a[yı]", r"çarpanlar"],
    "MAT.GEO": [
        r"üçgen",
        r"dörtgen",
        r"daire",
        r"çember",
        r"kenar\s+uzunlu",
        r"alan\w*\s*(hesap|bul|kaç)",
        r"çevre\w*\s*(uzunlu|hesap|kaç)",
        r"açı\w*\s*(ölçü|derece|kaç)",
        r"dikdörtgen",
        r"kare\w*\s*alan",
        r"paralel\w*kenar",
        r"yamuk",
        r"prizma",
        r"silindir",
        r"küre",
        r"piramit",
        r"koni",
    ],
    "MAT.DIZ": [
        r"aritmetik\s+dizi",
        r"geometrik\s+dizi",
        r"aritmetik\s+seri",
        r"geometrik\s+seri",
        r"dizi\w*\s*terim",
    ],
}

# Compile regex patterns for performance
_COMPILED_PATTERNS: dict[str, list[re.Pattern]] = {}
for _code, _patterns in REGEX_PATTERNS.items():
    _COMPILED_PATTERNS[_code] = [re.compile(p, re.IGNORECASE) for p in _patterns]


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


def match_single_regex(text: str) -> str | None:
    """Return subtopic code if exactly ONE regex pattern group matches, else None."""
    text_norm = normalize_tr(text)
    matched_codes: set[str] = set()
    for code, patterns in _COMPILED_PATTERNS.items():
        for pat in patterns:
            if pat.search(text_norm):
                matched_codes.add(code)
                break  # One pattern per code is enough
    return matched_codes.pop() if len(matched_codes) == 1 else None


def update_by_regex(
    cur, subtopic_ids: dict[str, str], dry_run: bool
) -> tuple[int, int]:
    """Phase 2: Update remaining level-1 questions using regex pattern matching.

    Returns (updated_count, ambiguous_count).
    """
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
    ambiguous = 0
    for qid, question_text in rows:
        code = match_single_regex(question_text)
        if code is not None:
            if code in subtopic_ids:
                if dry_run:
                    updated += 1
                else:
                    cur.execute(
                        "UPDATE question_bank SET primary_topic_id = %s WHERE id = %s",
                        (subtopic_ids[code], qid),
                    )
                    updated += cur.rowcount
        else:
            # Distinguish ambiguous (multi-match) from no match
            text_norm = normalize_tr(question_text)
            match_count = sum(
                1
                for _, patterns in _COMPILED_PATTERNS.items()
                if any(pat.search(text_norm) for pat in patterns)
            )
            if match_count > 1:
                ambiguous += 1
    return updated, ambiguous


def show_distribution(cur):
    """Show current subtopic distribution."""
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


def update_total_questions(cur, conn):
    """Update total_questions counts on topic_hierarchy."""
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


def run_phase1(cur, conn, dry_run: bool):
    """Phase 1: keyword-based matching (source_book + question_text)."""
    # Step 1: Seed subtopics
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Step 1: Seeding subtopics...")
    inserted = seed_subtopics(cur, dry_run)
    print(f"  -> {inserted} subtopics {'would be ' if dry_run else ''}inserted")

    if not dry_run:
        conn.commit()

    # Get subtopic IDs
    if dry_run:
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

    # Step 2A: source_book matching
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Step 2A: source_book matching...")
    book_updated = update_by_source_book(cur, subtopic_ids, dry_run)
    print(f"  -> {book_updated} questions {'would be ' if dry_run else ''}updated")
    if not dry_run:
        conn.commit()

    # Step 2B: question_text keyword matching
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
    print(f"Phase 1 Summary {'(DRY-RUN)' if dry_run else ''}:")
    print(f"  Subtopics inserted: {inserted}")
    print(f"  Questions updated (source_book): {book_updated}")
    print(f"  Questions updated (question_text): {text_updated}")
    print(f"  Total updated: {total_updated} ({pct:.1f}%)")
    print(f"  Remaining at level-1: {remaining}")

    if not dry_run:
        show_distribution(cur)
        update_total_questions(cur, conn)


def run_phase2(cur, conn, dry_run: bool):
    """Phase 2: regex pattern-based matching on remaining level-1 questions."""
    # Seed Phase 2 subtopics (Geometri, Diziler)
    print(
        f"\n{'[DRY-RUN] ' if dry_run else ''}Phase 2 Step 1: Seeding new subtopics..."
    )
    inserted = 0
    for code, name_tr, name_en in PHASE2_SUBTOPICS:
        topic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kiro2.topic.{code}"))
        if dry_run:
            print(f"  [DRY] INSERT topic: {code} = {name_tr}")
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
    if not dry_run:
        conn.commit()
    print(f"  -> {inserted} new subtopics {'would be ' if dry_run else ''}inserted")

    # Get all subtopic IDs (including new ones)
    if dry_run:
        subtopic_ids = {
            code: str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kiro2.topic.{code}"))
            for code, _, _ in SUBTOPICS + PHASE2_SUBTOPICS
        }
    else:
        subtopic_ids = get_subtopic_ids(cur)

    # Count remaining at level-1
    cur.execute(
        "SELECT COUNT(*) FROM question_bank WHERE is_active = true AND subject_area = 'MATEMATIK' AND primary_topic_id = %s",
        (MATEMATIK_PARENT_ID,),
    )
    remaining_before = cur.fetchone()[0]
    print(f"\nRemaining at level-1 before Phase 2: {remaining_before}")

    # Phase 2: Regex pattern matching
    print(
        f"\n{'[DRY-RUN] ' if dry_run else ''}Phase 2 Step 2: Regex pattern matching..."
    )
    regex_updated, ambiguous = update_by_regex(cur, subtopic_ids, dry_run)
    print(f"  -> {regex_updated} questions {'would be ' if dry_run else ''}updated")
    print(f"  -> {ambiguous} questions skipped (ambiguous — matched multiple topics)")
    if not dry_run:
        conn.commit()

    # Summary
    remaining_after = remaining_before - regex_updated
    pct = (regex_updated / remaining_before * 100) if remaining_before > 0 else 0
    print(f"\n{'=' * 50}")
    print(f"Phase 2 Summary {'(DRY-RUN)' if dry_run else ''}:")
    print(f"  New subtopics: {inserted}")
    print(f"  Regex matched (single): {regex_updated} ({pct:.1f}%)")
    print(f"  Regex ambiguous (skipped): {ambiguous}")
    print(f"  Remaining at level-1: {remaining_after}")

    # Total across both phases
    cur.execute(
        "SELECT COUNT(*) FROM question_bank WHERE is_active = true AND subject_area = 'MATEMATIK'"
    )
    total_math = cur.fetchone()[0]
    total_categorized = total_math - remaining_after
    total_pct = (total_categorized / total_math * 100) if total_math > 0 else 0
    print(f"\n  TOTAL categorized: {total_categorized}/{total_math} ({total_pct:.1f}%)")

    if not dry_run:
        show_distribution(cur)
        update_total_questions(cur, conn)


def run_fix_fp(cur, conn, dry_run: bool):
    """Fix false positives: re-verify regex-matched questions with updated patterns.

    Steps:
    1. Find all level-2 questions that were assigned by regex (not by book keyword)
    2. Re-run match_single_regex with updated patterns
    3. If no longer matches or matches different code → reset to level-1
    4. Re-run Phase 2 regex on newly-reset questions
    """
    subtopic_ids = get_subtopic_ids(cur)

    # Get all level-2 Matematik questions (including source_book for verification)
    cur.execute(
        """
        SELECT qb.id, qb.question_text, qb.primary_topic_id, th.code,
               COALESCE(qb.source_book, '')
        FROM question_bank qb
        JOIN topic_hierarchy th ON th.id = qb.primary_topic_id
        WHERE qb.is_active = true
          AND qb.subject_area = 'MATEMATIK'
          AND th.level = 2
          AND th.parent_id = %s
          AND qb.question_text IS NOT NULL
          AND qb.question_text != ''
        """,
        (MATEMATIK_PARENT_ID,),
    )
    rows = cur.fetchall()
    print(f"\nLevel-2 Matematik questions to verify: {len(rows)}")

    reset_count = 0
    mismatch_count = 0
    ok_count = 0
    book_ok_count = 0
    reset_by_code: dict[str, int] = {}

    for qid, question_text, current_topic_id, current_code, source_book in rows:
        new_code = match_single_regex(question_text)
        if new_code == current_code:
            ok_count += 1
        elif new_code is None:
            # No regex match → check text keyword AND book keyword
            text_code = match_single_keyword(question_text, TEXT_KEYWORD_MAP)
            if text_code == current_code:
                ok_count += 1
                continue
            book_code = (
                match_single_keyword(source_book, BOOK_KEYWORD_MAP)
                if source_book
                else None
            )
            if book_code == current_code:
                book_ok_count += 1
                continue
            # Neither regex, text keyword, nor book keyword confirms → reset
            reset_count += 1
            reset_by_code[current_code] = reset_by_code.get(current_code, 0) + 1
            if not dry_run:
                cur.execute(
                    "UPDATE question_bank SET primary_topic_id = %s WHERE id = %s",
                    (MATEMATIK_PARENT_ID, qid),
                )
        elif new_code != current_code:
            # Matches a DIFFERENT code now → check book/text first
            text_code = match_single_keyword(question_text, TEXT_KEYWORD_MAP)
            book_code = (
                match_single_keyword(source_book, BOOK_KEYWORD_MAP)
                if source_book
                else None
            )
            if text_code == current_code or book_code == current_code:
                ok_count += 1  # Book/text confirms current assignment
            else:
                mismatch_count += 1
                reset_by_code[current_code] = reset_by_code.get(current_code, 0) + 1
                if not dry_run:
                    cur.execute(
                        "UPDATE question_bank SET primary_topic_id = %s WHERE id = %s",
                        (MATEMATIK_PARENT_ID, qid),
                    )

    if not dry_run:
        conn.commit()

    total_reset = reset_count + mismatch_count
    print(f"\n{'=' * 50}")
    print(f"Fix-FP Verify {'(DRY-RUN)' if dry_run else ''}:")
    print(f"  OK (regex/text confirmed): {ok_count}")
    print(f"  OK (book keyword confirmed): {book_ok_count}")
    print(f"  Reset (no match): {reset_count}")
    print(f"  Reset (code changed): {mismatch_count}")
    print(f"  Total reset to level-1: {total_reset}")
    if reset_by_code:
        print("\n  Resets by original code:")
        for code, cnt in sorted(reset_by_code.items(), key=lambda x: -x[1]):
            print(f"    {code}: {cnt}")

    # Re-run regex on reset questions
    if total_reset > 0:
        print(
            f"\n{'[DRY-RUN] ' if dry_run else ''}Re-running regex on {total_reset} reset questions..."
        )
        re_matched, re_ambiguous = update_by_regex(cur, subtopic_ids, dry_run)
        print(f"  -> {re_matched} re-matched")
        print(f"  -> {re_ambiguous} ambiguous (skipped)")
        if not dry_run:
            conn.commit()
    else:
        print("\nNo false positives found.")

    if not dry_run:
        show_distribution(cur)
        update_total_questions(cur, conn)


def main():
    parser = argparse.ArgumentParser(description="Seed topic_hierarchy subtopics")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Preview without changes")
    group.add_argument("--apply", action="store_true", help="Apply changes to DB")
    parser.add_argument(
        "--phase2", action="store_true", help="Run Phase 2 regex matching"
    )
    parser.add_argument(
        "--fix-fp",
        action="store_true",
        help="Fix false positives: re-verify and re-categorize with updated patterns",
    )
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

        if args.fix_fp:
            run_fix_fp(cur, conn, dry_run)
        elif args.phase2:
            run_phase2(cur, conn, dry_run)
        else:
            run_phase1(cur, conn, dry_run)

    finally:
        conn.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
