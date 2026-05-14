"""Audit Task 02b — Tier H DÜZELTILMIŞ doğrulama (substring kontrolü).

Jaccard yanıltıcı çünkü:
- DB text = sadece soru cümlesi (kısa)
- OCR text = paragraf+soru veya full crop content (uzun)

Doğru doğrulama: DB text'in son 60-100 karakteri OCR text içinde var mı?
Veya tersi: DB text'in herhangi bir 5-word substring'i OCR text'te var mı?
"""

import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from sqlalchemy import create_engine, text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass
db_url = (
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
    .replace("postgresql+asyncpg://", "postgresql://")
    .replace("/kiro2_db", "/kiro2")
)
engine = create_engine(db_url)

OCR_PATH = Path("d-dataset/output/ocr_crops/results.jsonl")

ocr_idx = defaultdict(list)
with OCR_PATH.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        book = unicodedata.normalize(
            "NFC", (d.get("book", "") or "").replace("_", " ").strip()
        )
        try:
            page = int(d.get("page_num"))
        except (TypeError, ValueError):
            continue
        if book:
            ocr_idx[(book, page)].append(d)


def normalize(s):
    """NFC + lowercase + whitespace collapse."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "").lower()).strip()


def substring_overlap(db_text, ocr_text):
    """DB text'in en uzun N-word substring'inin OCR text'te varlığını ölç.

    Returns:
      best_match_words: en uzun ortak word sekansının uzunluğu
      db_words: DB text'in word count'u
      ratio: best_match / db_words
    """
    db_n = normalize(db_text)
    ocr_n = normalize(ocr_text)
    db_words = db_n.split()
    if not db_words:
        return 0, 0, 0.0
    # Sliding window: 5-word substring DB → OCR'da mı?
    n_words = len(db_words)
    best = 0
    # Try descending window sizes for efficiency
    for window in [10, 8, 6, 5, 4]:
        if window > n_words:
            continue
        for i in range(n_words - window + 1):
            substr = " ".join(db_words[i : i + window])
            if substr in ocr_n:
                best = max(best, window)
                break
        if best >= window:
            break
    return best, n_words, best / n_words if n_words else 0.0


with engine.connect() as c:
    rows = list(
        c.execute(
            text(
                """
        SELECT id::text, source_book, source_page,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page')::int AS qip,
               pipeline_metadata::jsonb -> 'tier_h_match' ->> 'crop_file' AS crop_file,
               LEFT(question_text, 600) AS qt
        FROM question_bank
        WHERE is_active=TRUE
          AND pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL
        ORDER BY md5(id::text)
        LIMIT 30
    """
            )
        )
    )

print("Tier H 30 sample — substring overlap kontrolü:")
ok_strong = 0  # >=6 word match
ok_weak = 0  # 4-5 word match
no_match = 0  # 0-3 word match
no_ocr = 0
for qid, book, page, qip, cf, qt in rows:
    nbook = unicodedata.normalize("NFC", book.strip())
    cands = ocr_idx.get((nbook, page), [])
    matching = [e for e in cands if e.get("crop_file") == cf]
    if not matching:
        no_ocr += 1
        continue
    ocr_text = matching[0].get("soru_metni", "")
    best, db_n, ratio = substring_overlap(qt, ocr_text)
    if best >= 6:
        ok_strong += 1
    elif best >= 4:
        ok_weak += 1
    else:
        no_match += 1
        safe = qt[:60].encode("ascii", "replace").decode("ascii")
        safe_ocr = ocr_text[:60].encode("ascii", "replace").decode("ascii")
        print(f"  ❌ NO_MATCH: id={qid[:8]} best={best} db_words={db_n}")
        print(f"     DB:  {safe}")
        print(f"     OCR: {safe_ocr}")

print("\n📊 Substring overlap ÖZET (30 sample):")
print(f"  ok_strong (≥6 word match): {ok_strong}")
print(f"  ok_weak (4-5 word match):  {ok_weak}")
print(f"  no_match (0-3 word):       {no_match}")
print(f"  no_ocr:                    {no_ocr}")
total_valid = ok_strong + ok_weak + no_match
if total_valid > 0:
    print(
        f"\nReal accuracy: {100 * (ok_strong + ok_weak) / total_valid:.1f}% "
        f"({ok_strong + ok_weak}/{total_valid})"
    )
