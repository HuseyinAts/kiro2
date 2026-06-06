"""
Heuristic Difficulty Assignment Script
Soru metninin karmaşıklığına göre zorluk seviyesi atar.

IRT kalibrasyonu öğrenci yanıt verisi gerektirir (min 30 yanıt/soru).
MVP'de 0 yanıt olduğundan, metin-bazlı heuristic kullanılır.

Kullanım:
    python scripts/assign_difficulty_heuristic.py --dry-run   # Önizleme
    python scripts/assign_difficulty_heuristic.py              # Uygula
"""

import argparse
import os
import re

import psycopg2

# DB connection — reads from env vars with local dev defaults
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5434")),
    "dbname": os.environ.get("DB_NAME", "kiro2"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
}

# IRT difficulty mapping (keys match DB enum: UPPERCASE)
IRT_MAP = {
    "VERY_EASY": -2.0,
    "EASY": -1.0,
    "MEDIUM": 0.0,
    "HARD": 1.0,
    "VERY_HARD": 2.0,
}

# Math/formula indicators
MATH_PATTERNS = [
    r"[=+\-×÷∑∫√∞≤≥≠±]",  # math symbols
    r"\b\d+\s*[+\-*/]\s*\d+",  # arithmetic expressions
    r"\b(sin|cos|tan|log|ln|lim)\b",  # trig/log functions
    r"x\s*[²³⁴]|x\^",  # powers
    r"\b(denklem|fonksiyon|integral|türev|limit)\b",  # Turkish math terms
    r"[₀₁₂₃₄₅₆₇₈₉]",  # subscripts
]

# Complex question structure indicators
COMPLEX_PATTERNS = [
    r"\bI\b.*\bII\b.*\bIII\b",  # Roman numeral lists (I, II, III)
    r"(Yukarıda|Aşağıda).*göre",  # Reference to passage
    r"hangisi.*doğrudur|hangisi.*yanlış",  # Which is correct/wrong
    r"kaç\s*tanesi|kaçı",  # How many of them
    r"verilenlerin\s*(hangisi|kaçı)",  # Which of the given
]

# Easy question indicators
EASY_PATTERNS = [
    r"aşağıdakilerden\s+hangisi",  # Simple "which of the following"
    r"ne\s+denir|ne\s+anlama\s+gelir",  # Definition questions
    r"hangi\s+yıl|nerede\s+kurulmuştur",  # Factual recall
]

# Subjects that tend to be harder
HARDER_SUBJECTS = {"GEOMETRI", "BIYOLOJI", "KIMYA"}
EASIER_SUBJECTS = {"TURKCE", "SOSYAL", "TARIH"}


def calculate_difficulty_score(
    question_text: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    option_e: str,
    subject_area: str,
    exam_type: str,
) -> tuple[str, float]:
    """
    Calculate difficulty level and IRT difficulty for a question.

    Returns:
        (difficulty_level, irt_difficulty) tuple
    """
    score = 0.0  # Range: -2.0 (very easy) to +2.0 (very hard)

    text = question_text or ""
    options = [o for o in [option_a, option_b, option_c, option_d, option_e] if o]

    # 1. Text length (base signal — strongest predictor)
    text_len = len(text)
    if text_len < 60:
        score -= 1.5  # Very short = likely very easy
    elif text_len < 120:
        score -= 0.8
    elif text_len < 200:
        score -= 0.2
    elif text_len < 350:
        score += 0.3
    elif text_len < 500:
        score += 0.8
    else:
        score += 1.3  # Long = likely hard

    # 2. Math/formula density
    math_count = sum(
        len(re.findall(pattern, text, re.IGNORECASE)) for pattern in MATH_PATTERNS
    )
    if math_count >= 5:
        score += 0.8
    elif math_count >= 2:
        score += 0.3

    # 3. Complex question structure
    complex_count = sum(
        1 for pattern in COMPLEX_PATTERNS if re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    )
    score += complex_count * 0.4

    # 4. Easy question indicators
    easy_count = sum(
        1 for pattern in EASY_PATTERNS if re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    )
    score -= easy_count * 0.3

    # 5. Option complexity (average length)
    if options:
        avg_opt_len = sum(len(o) for o in options) / len(options)
        if avg_opt_len > 80:
            score += 0.5  # Long options = harder
        elif avg_opt_len < 15:
            score -= 0.3  # Short options = easier

    # 6. Subject bias
    if subject_area in HARDER_SUBJECTS:
        score += 0.3
    elif subject_area in EASIER_SUBJECTS:
        score -= 0.2

    # 7. Exam type bias (AYT generally harder than TYT)
    if exam_type == "AYT":
        score += 0.3

    # Clamp to [-2.5, 2.5] then map to difficulty level
    score = max(-2.5, min(2.5, score))

    # DB enum values are UPPERCASE: VERY_EASY, EASY, MEDIUM, HARD, VERY_HARD
    if score <= -1.0:
        level = "VERY_EASY"
    elif score <= -0.2:
        level = "EASY"
    elif score <= 0.4:
        level = "MEDIUM"
    elif score <= 1.0:
        level = "HARD"
    else:
        level = "VERY_HARD"

    irt_difficulty = IRT_MAP[level]

    return level, irt_difficulty


def main():
    parser = argparse.ArgumentParser(description="Heuristic difficulty assignment")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without updating DB"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Limit questions to process (0=all)"
    )
    args = parser.parse_args()

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Fetch all active questions
    query = """
        SELECT id, question_text, option_a, option_b, option_c, option_d, option_e,
               subject_area, exam_type
        FROM question_bank
        WHERE is_active = TRUE
    """
    if args.limit > 0:
        query += " LIMIT %s"
        cur.execute(query, (args.limit,))
    else:
        cur.execute(query)
    rows = cur.fetchall()
    total = len(rows)
    print(f"Processing {total} questions...")

    # Calculate difficulty for each question
    distribution = {"VERY_EASY": 0, "EASY": 0, "MEDIUM": 0, "HARD": 0, "VERY_HARD": 0}
    updates = []

    for row in rows:
        qid, text, oa, ob, oc, od, oe, subject, exam_type = row
        level, irt_diff = calculate_difficulty_score(
            text or "",
            oa or "",
            ob or "",
            oc or "",
            od or "",
            oe or "",
            subject or "",
            exam_type or "",
        )
        distribution[level] += 1
        updates.append((level, irt_diff, qid))

    # Print distribution
    print(f"\n{'=' * 50}")
    print("Zorluk Dağılımı:")
    print(f"{'=' * 50}")
    for level, count in sorted(distribution.items()):
        pct = (count / total * 100) if total > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {level:12s}: {count:6d} ({pct:5.1f}%) {bar}")
    print(f"  {'TOPLAM':12s}: {total:6d}")

    if args.dry_run:
        print("\n[DRY RUN] Veritabanı güncellenmedi.")
        # Show sample
        print("\nÖrnek atamalar (ilk 10):")
        cur2 = conn.cursor()
        for level, irt_diff, qid in updates[:10]:
            cur2.execute(
                "SELECT question_text, subject_area FROM question_bank WHERE id = %s",
                (qid,),
            )
            r = cur2.fetchone()
            text_preview = (r[0] or "")[:60].replace("\n", " ")
            print(f"  [{level:10s}] (b={irt_diff:+.1f}) {r[1]:12s} | {text_preview}...")
        conn.close()
        return

    # Apply updates
    print("\nVeritabanı güncelleniyor...")
    batch_size = 1000
    for i in range(0, len(updates), batch_size):
        batch = updates[i : i + batch_size]
        cur.executemany(
            """UPDATE question_bank
               SET difficulty_level = %s, irt_difficulty = %s
               WHERE id = %s""",
            batch,
        )
        conn.commit()
        done = min(i + batch_size, len(updates))
        print(f"  {done}/{total} güncellendi", end="\r")

    print(f"\n\n[OK] {total} soru guncellendi.")

    # Verify
    cur.execute("""
        SELECT difficulty_level, COUNT(*)
        FROM question_bank
        WHERE is_active = TRUE
        GROUP BY difficulty_level
        ORDER BY difficulty_level
    """)
    print("\nDoğrulama (DB sorgusu):")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")

    conn.close()


if __name__ == "__main__":
    main()
