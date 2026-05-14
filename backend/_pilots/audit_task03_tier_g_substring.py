"""Audit Task 03 — Tier G substring overlap re-verify (2,493 satır).

Tier G alt-tier dağılımı:
- G1 (key match + sim>=0.40): 1,961
- G2 (page no-key + sim>=0.55): 171
- G3 (page no-qno + sim>=0.55): 361

G1 Tier F'in daha gevşek versiyonu, G2/G3 page-level fallback. Risk
profili Tier F'tan biraz daha yüksek ama hala çift sinyal var.
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
ocr_by_crop = {}
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


# 30 sample her sub-tier'dan
results_by_subtier = {}
with engine.connect() as c:
    for sub_tier in ["G1", "G2", "G3"]:
        rows = list(
            c.execute(
                text(
                    f"""
            SELECT id::text, source_book,
                   (pipeline_metadata::jsonb -> 'tier_g_match' ->> 'similarity')::float AS sim,
                   pipeline_metadata::jsonb -> 'tier_g_match' ->> 'crop_file' AS cf,
                   LEFT(question_text, 400) AS qt
            FROM question_bank
            WHERE is_active=TRUE
              AND pipeline_metadata::jsonb -> 'tier_g_match' ->> 'tier' = '{sub_tier}'
            ORDER BY md5(id::text)
            LIMIT 30
        """
                )
            )
        )
        results_by_subtier[sub_tier] = rows

print("Tier G substring overlap re-verify (30 sample per sub-tier):")
for sub_tier, rows in results_by_subtier.items():
    strong = 0
    weak = 0
    no_match = 0
    no_ocr = 0
    for qid, book, sim, cf, qt in rows:
        ocr_text = ocr_by_crop.get(cf, "")
        if not ocr_text:
            no_ocr += 1
            continue
        score = substring_overlap(qt, ocr_text)
        if score >= 6:
            strong += 1
        elif score >= 4:
            weak += 1
        else:
            no_match += 1
            if no_match <= 2:
                safe = qt[:60].encode("ascii", "replace").decode("ascii")
                safe_ocr = ocr_text[:60].encode("ascii", "replace").decode("ascii")
                print(f"  ❌ {sub_tier} id={qid[:8]} sim={sim:.3f}")
                print(f"     DB:  {safe}")
                print(f"     OCR: {safe_ocr}")

    total = strong + weak + no_match
    if total > 0:
        print(
            f"\n  {sub_tier} ({len(rows)} sample): strong={strong}, weak={weak}, no_match={no_match}, no_ocr={no_ocr}"
        )
        print(f"  Accuracy: {100 * (strong + weak) / total:.1f}%")
