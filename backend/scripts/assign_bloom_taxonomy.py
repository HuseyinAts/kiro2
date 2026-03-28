"""
Bloom Taxonomy Batch Assignment Script
Keyword-based Bloom level assignment for question_bank.

Uses the same keyword logic as bloom_taxonomy_classifier.py
but runs directly on DB without torch/transformers dependency.

Usage:
    python scripts/assign_bloom_taxonomy.py --dry-run   # Preview
    python scripts/assign_bloom_taxonomy.py              # Apply
"""

import argparse
import os

import psycopg2

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5434")),
    "dbname": os.environ.get("DB_NAME", "kiro2"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
}

BLOOM_LEVELS = {
    1: "bilgi",
    2: "kavrama",
    3: "uygulama",
    4: "analiz",
    5: "sentez",
    6: "degerlendirme",
}

BLOOM_KEYWORDS = {
    1: [
        "tanimla",
        "listele",
        "adlandir",
        "belirt",
        "hatirla",
        "kim",
        "nedir",
        "nerede",
        "ne zaman",
        "say",
        "tanimlayiniz",
    ],
    2: [
        "acikla",
        "ozetle",
        "yorumla",
        "karsilastir",
        "siniflandir",
        "orneklendir",
        "neden",
        "nasil",
        "anlat",
        "betimle",
    ],
    3: [
        "uygula",
        "coz",
        "hesapla",
        "kullan",
        "goster",
        "bul",
        "islem yap",
        "hesaplama",
        "yapiniz",
        "bulunuz",
        "hesaplayiniz",
    ],
    4: [
        "analiz et",
        "ayir",
        "incele",
        "karsilastir",
        "iliskilendir",
        "ayirt et",
        "organize et",
        "siniflandir",
        "neden-sonuc",
    ],
    5: [
        "olustur",
        "tasarla",
        "gelistir",
        "birlestir",
        "sentezle",
        "oner",
        "plan yap",
        "uret",
        "formule et",
    ],
    6: [
        "degerlendir",
        "elestir",
        "karar ver",
        "savun",
        "yargila",
        "onceliklendir",
        "hangisi dogrudur",
        "hangisi yanlistir",
    ],
}


def classify_question(text: str) -> tuple[int, str, float]:
    """Keyword-based Bloom classification."""
    if not text:
        return 2, "kavrama", 0.5

    text_lower = text.lower()
    # Turkish normalization
    text_lower = (
        text_lower.replace("İ", "i")
        .replace("I", "ı")
        .replace("ş", "s")
        .replace("ç", "c")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
    )

    level_scores = {}
    for level, keywords in BLOOM_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        level_scores[level] = score

    if max(level_scores.values()) == 0:
        return 2, "kavrama", 0.5

    best_level = max(level_scores, key=level_scores.get)
    max_score = level_scores[best_level]
    confidence = min(0.95, 0.5 + (max_score / 10))

    return best_level, BLOOM_LEVELS[best_level], confidence


def main():
    parser = argparse.ArgumentParser(description="Bloom taxonomy batch assignment")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        SELECT id, question_text
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

    distribution = dict.fromkeys(BLOOM_LEVELS.values(), 0)
    updates = []

    for qid, text in rows:
        level, category, confidence = classify_question(text or "")
        distribution[category] += 1
        updates.append((level, category, confidence, qid))

    print(f"\n{'=' * 50}")
    print("Bloom Taxonomy Distribution:")
    print(f"{'=' * 50}")
    for cat, count in sorted(
        distribution.items(), key=lambda x: list(BLOOM_LEVELS.values()).index(x[0])
    ):
        pct = (count / total * 100) if total > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {cat:18s}: {count:6d} ({pct:5.1f}%) {bar}")
    print(f"  {'TOPLAM':18s}: {total:6d}")

    if args.dry_run:
        print("\n[DRY RUN] DB not updated.")
        cur2 = conn.cursor()
        for level, category, conf, qid in updates[:10]:
            cur2.execute(
                "SELECT question_text FROM question_bank WHERE id = %s", (qid,)
            )
            r = cur2.fetchone()
            preview = (r[0] or "")[:50].replace("\n", " ")
            print(f"  [{category:14s}] (L{level}, conf={conf:.2f}) {preview}...")
        conn.close()
        return

    print("\nUpdating database...")
    batch_size = 1000
    for i in range(0, len(updates), batch_size):
        batch = updates[i : i + batch_size]
        cur.executemany(
            """UPDATE question_bank
               SET bloom_level = %s, bloom_category = %s
               WHERE id = %s""",
            [(level, category, qid) for level, category, conf, qid in batch],
        )
        conn.commit()
        done = min(i + batch_size, len(updates))
        print(f"  {done}/{total} updated", end="\r")

    print(f"\n\n[OK] {total} questions updated with Bloom taxonomy.")

    # Verify
    cur.execute("""
        SELECT bloom_category, COUNT(*)
        FROM question_bank
        WHERE is_active = TRUE AND bloom_category IS NOT NULL
        GROUP BY bloom_category
        ORDER BY bloom_category
    """)
    print("\nVerification (DB query):")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")

    conn.close()


if __name__ == "__main__":
    main()
