#!/usr/bin/env python3
"""
Update Bloom taxonomy (bloom_level, bloom_category) for question_bank rows.

Uses keyword-based heuristic classification adapted for Turkish YKS questions.
Can be refined later with AI models (Qwen3-8B, Gemini).

Bloom's Taxonomy Levels:
  1 = remember    (hatırla)
  2 = understand  (anla)
  3 = apply       (uygula)
  4 = analyze     (analiz et)
  5 = evaluate    (değerlendir)
  6 = create      (oluştur)

Usage:
    cd backend
    python scripts/update_bloom_taxonomy.py [--batch-size 5000] [--dry-run]
"""

import argparse
import os
import re
import unicodedata
from pathlib import Path
from time import time

# ─── Bloom Classification Rules ──────────────────────────────────────────

BLOOM_LEVELS = {
    1: "remember",
    2: "understand",
    3: "apply",
    4: "analyze",
    5: "evaluate",
    6: "create",
}

# Turkish keyword patterns for each Bloom level (lower priority → higher)
# Higher level matches override lower ones.
BLOOM_PATTERNS = {
    6: [  # create (rare in MCQ)
        r"tasarla", r"oluştur", r"yaz[ıi]n[ıi]z",
        r"üret", r"planla", r"kurgula",
    ],
    5: [  # evaluate
        r"değerlendir", r"yanlış", r"doğru.{0,5}yanlış",
        r"hangisi\s+doğrudur", r"hangisi\s+yanlıştır",
        r"hangisi\s+söylenemez", r"hangisi\s+çıkarılamaz",
        r"kesinlikle", r"her zaman", r"kanıtla",
        r"yargıla", r"eleştir", r"savun",
        r"hangisi\s+uygun\s+değildir",
    ],
    4: [  # analyze
        r"karşılaştır", r"sınıfla", r"ayır",
        r"neden.{0,10}sonuç", r"ilişki",
        r"fark[ıi]", r"benzerlik", r"ortak",
        r"arasındaki", r"hangi\s+durumda",
        r"çıkar[ıi]m", r"gra[fp]i[kğ]",
        r"tablo", r"şekil.{0,5}göre",
        r"verilere\s+göre", r"buna\s+göre",
        r"I+\s*[.,]\s*I+",  # Roman numeral lists (I, II, III analysis)
    ],
    3: [  # apply
        r"hesapla", r"bul[au]n[uı]z", r"çöz",
        r"değeri\s+kaç", r"kaç\s*(cm|m|kg|lt|tl|gr)",
        r"kaçtır", r"kaç\s+tanedir", r"kaç\s+olur",
        r"sonucu?\s+kaç", r"toplamı?\s+kaç",
        r"\d+\s*[+\-×÷*/]\s*\d+",  # arithmetic
        r"x\s*[=+\-]", r"f\s*\(\s*x\s*\)",  # algebra
        r"alan[ıi]", r"hacm[ie]", r"çevre",  # geometry application
        r"olasılı[kğ]", r"yüzde",
    ],
    2: [  # understand
        r"açıkla", r"yorumla", r"anlat",
        r"ne\s+anlama", r"ne\s+demek", r"özetle",
        r"ifade\s+ed", r"anlamı",
        r"neyi?\s+anlatı", r"nasıl\s+açıklan",
        r"kavram", r"tanım",
    ],
    1: [  # remember
        r"hangisidir", r"nedir",
        r"adı\s+nedir", r"hangi\s+yıl",
        r"başkenti", r"yazarı", r"eseri",
        r"kim\s+tarafından", r"hangi\s+dönem",
        r"bilinen", r"olarak\s+adlandır",
    ],
}

# Subject-specific overrides
SUBJECT_BASE_LEVELS = {
    "MATEMATIK": 3,   # Math is mostly application
    "GEOMETRI": 3,    # Geometry is mostly application
    "FIZIK": 3,       # Physics is mostly application
    "KIMYA": 3,       # Chemistry is mostly application
    "BIYOLOJI": 2,    # Biology has more recall/understanding
    "TURKCE": 2,      # Turkish language is understanding-heavy
    "EDEBIYAT": 2,    # Literature is understanding-heavy
    "TARIH": 1,       # History has recall elements
    "COGRAFYA": 2,    # Geography is understanding
    "FELSEFE": 4,     # Philosophy involves analysis
    "DIN_KULTURU": 1, # Religion has recall
    "GENEL": 2,       # Default
}


def normalize_text(text: str) -> str:
    """Normalize Turkish text for pattern matching."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()


def classify_bloom(question_text: str, subject: str) -> tuple[int, str]:
    """Classify a question's Bloom level using keyword heuristics.

    Returns (bloom_level, bloom_category).
    """
    if not question_text:
        base = SUBJECT_BASE_LEVELS.get(subject, 2)
        return base, BLOOM_LEVELS[base]

    normalized = normalize_text(question_text)
    detected_level = 0

    # Check patterns from highest to lowest level
    for level in sorted(BLOOM_PATTERNS.keys(), reverse=True):
        for pattern in BLOOM_PATTERNS[level]:
            if re.search(pattern, normalized):
                detected_level = level
                break
        if detected_level:
            break

    # If no pattern matched, use subject-based default
    if detected_level == 0:
        detected_level = SUBJECT_BASE_LEVELS.get(subject, 2)

    # Math/science with numbers → at least "apply"
    if subject in ("MATEMATIK", "GEOMETRI", "FIZIK", "KIMYA"):
        if detected_level < 3 and re.search(r"\d", normalized):
            detected_level = 3

    return detected_level, BLOOM_LEVELS[detected_level]


def main() -> None:
    parser = argparse.ArgumentParser(description="Update Bloom taxonomy")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:changeme@localhost:5434/kiro2",
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")

    from sqlalchemy import create_engine, text
    engine = create_engine(db_url)

    print("=" * 60)
    print("Bloom Taxonomy Classification")
    print("=" * 60)

    # Count questions with default bloom (level=2, category=understand)
    with engine.connect() as conn:
        total = conn.execute(text(
            "SELECT COUNT(*) FROM question_bank WHERE bloom_level = 2 AND bloom_category = 'understand'"
        )).scalar()
        print(f"Questions with default bloom: {total:,}")

    if total == 0:
        print("Nothing to update.")
        return

    if args.dry_run:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT id, question_text, subject_area FROM question_bank "
                "WHERE bloom_level = 2 AND bloom_category = 'understand' LIMIT 10"
            )).fetchall()
        print("\nSample classifications:")
        for r in rows:
            level, category = classify_bloom(r[1], r[2])
            snippet = (r[1] or "")[:60].replace("\n", " ")
            print(f"  [{r[2]:10s}] L{level}={category:12s}  {snippet}...")
        print("\n[DRY RUN] No changes made.")
        return

    # Batch update — fetch all IDs upfront to avoid infinite loop
    # (some rows may classify back to L2=understand, so WHERE clause won't shrink)
    t0 = time()
    updated = 0
    distribution = dict.fromkeys(range(1, 7), 0)

    with engine.connect() as conn:
        all_ids = conn.execute(text(
            "SELECT id FROM question_bank "
            "WHERE bloom_level = 2 AND bloom_category = 'understand' "
            "ORDER BY id"
        )).fetchall()
        id_list = [r[0] for r in all_ids]

    for batch_start in range(0, len(id_list), args.batch_size):
        batch_ids = id_list[batch_start:batch_start + args.batch_size]

        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT id, question_text, subject_area FROM question_bank "
                "WHERE id = ANY(:ids)"
            ), {"ids": batch_ids}).fetchall()

        updates = []
        for r in rows:
            level, category = classify_bloom(r[1], r[2])
            distribution[level] += 1
            updates.append({
                "qid": r[0],
                "bl": level,
                "bc": category,
            })

        with engine.begin() as tx:
            for u in updates:
                tx.execute(text(
                    "UPDATE question_bank SET "
                    "bloom_level = :bl, bloom_category = :bc "
                    "WHERE id = :qid"
                ), u)

        updated += len(rows)
        pct = min(100.0, updated / total * 100)
        print(f"  [{pct:5.1f}%] {updated:,}/{total:,}")

    t_total = time() - t0
    print(f"\n{'=' * 60}")
    print(f"Updated: {updated:,} questions in {t_total:.1f}s")
    print("\nBloom Distribution:")
    for level in range(1, 7):
        name = BLOOM_LEVELS[level]
        count = distribution[level]
        pct = count / max(1, updated) * 100
        bar = "#" * int(pct / 2)
        print(f"  L{level} {name:12s}: {count:>6,} ({pct:5.1f}%) {bar}")


if __name__ == "__main__":
    main()
