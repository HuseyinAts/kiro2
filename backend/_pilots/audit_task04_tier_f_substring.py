"""Audit Task 04 — Tier F substring overlap re-verify (7,441 satır).

Tier H'taki text-karşılaştırma yöntemini Tier F'e uygula. Beklenen:
Tier F key match + sim>=0.50 ile yapıldı, dolayısıyla substring overlap
yüksek olmalı (Tier H gibi %75 yanlış değil).
"""

import json
import os
import re
import sys
import unicodedata
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

# OCR index by crop_file
ocr_by_crop = {}  # crop_file -> ocr_text
with OCR_PATH.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        cf = d.get("crop_file", "")
        if cf:
            ocr_by_crop[cf] = d.get("soru_metni", "") or ""


def substring_overlap(db_text, ocr_text):
    db_n = re.sub(
        r"\s+", " ", unicodedata.normalize("NFC", db_text or "").lower()
    ).strip()
    ocr_n = re.sub(
        r"\s+", " ", unicodedata.normalize("NFC", ocr_text or "").lower()
    ).strip()
    db_words = db_n.split()
    if not db_words:
        return 0
    for window in [10, 8, 6, 5, 4]:
        if window > len(db_words):
            continue
        for i in range(len(db_words) - window + 1):
            if " ".join(db_words[i : i + window]) in ocr_n:
                return window
    return 0


with engine.connect() as c:
    rows = list(
        c.execute(
            text(
                """
        SELECT id::text, source_book, source_page,
               (pipeline_metadata::jsonb -> 'tier_f_match' ->> 'similarity')::float AS sim,
               pipeline_metadata::jsonb -> 'tier_f_match' ->> 'crop_file' AS cf,
               LEFT(question_text, 400) AS qt
        FROM question_bank
        WHERE is_active=TRUE AND pipeline_metadata::jsonb -> 'tier_f_match' IS NOT NULL
        ORDER BY md5(id::text)
        LIMIT 50
    """
            )
        )
    )

print("Tier F 50 sample — substring overlap re-verify:")
strong = 0
weak = 0
no_match = 0
no_ocr = 0
sim_buckets = {"0.50-0.60": [], "0.60-0.70": []}

for qid, book, page, stored_sim, cf, qt in rows:
    ocr_text = ocr_by_crop.get(cf, "")
    if not ocr_text:
        no_ocr += 1
        continue
    score = substring_overlap(qt, ocr_text)
    bucket = "0.50-0.60" if stored_sim < 0.60 else "0.60-0.70"
    sim_buckets[bucket].append(score)
    if score >= 6:
        strong += 1
    elif score >= 4:
        weak += 1
    else:
        no_match += 1
        safe_qt = qt[:60].encode("ascii", "replace").decode("ascii")
        safe_ocr = ocr_text[:60].encode("ascii", "replace").decode("ascii")
        print(f"  ❌ id={qid[:8]} sim={stored_sim:.3f} score={score}")
        print(f"     DB:  {safe_qt}")
        print(f"     OCR: {safe_ocr}")

print("\n📊 Tier F (50 sample):")
print(f"  strong (≥6 word): {strong}")
print(f"  weak (4-5 word):  {weak}")
print(f"  no_match (<4):    {no_match}")
print(f"  no_ocr:           {no_ocr}")
total = strong + weak + no_match
if total > 0:
    print(
        f"\n  Accuracy: {100 * (strong + weak) / total:.1f}% ({strong + weak}/{total})"
    )
print("\nBucket bazlı:")
for b, scores in sim_buckets.items():
    if scores:
        n_ok = sum(1 for s in scores if s >= 4)
        print(f"  {b}: {n_ok}/{len(scores)} ok ({100 * n_ok / len(scores):.0f}%)")
