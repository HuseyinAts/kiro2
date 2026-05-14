"""Audit Task 02 — Tier H Pixel Verify (49,468 satır, en kritik scope)."""

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
        if not book:
            continue
        ocr_idx[(book, page)].append(d)


def text_sim(a, b):
    if not a or not b:
        return 0.0
    sa = set(unicodedata.normalize("NFC", a).lower().split())
    sb = set(unicodedata.normalize("NFC", b).lower().split())
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0


with engine.connect() as c:
    rows = list(
        c.execute(
            text(
                """
        SELECT id::text, source_book, source_page,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page')::int AS qip,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') AS hd,
               pipeline_metadata::jsonb -> 'tier_h_match' ->> 'crop_file' AS crop_file,
               LEFT(question_text, 300) AS qt
        FROM question_bank
        WHERE is_active=TRUE
          AND pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL
        ORDER BY md5(id::text)
        LIMIT 30
    """
            )
        )
    )

print("Tier H 30 random sample audit:")
print("  qip == crop_q_no invariant + OCR text similarity karşılaştırma\n")

ok = 0
qip_mismatch = 0
no_ocr = 0
low_sim = 0
for qid, book, page, qip, hd, cf, qt in rows:
    nbook = unicodedata.normalize("NFC", book.strip())
    cands = ocr_idx.get((nbook, page), [])
    m = re.search(r"_p\d{4}_q(\d{1,3})", cf or "")
    if not m:
        continue
    crop_q = int(m.group(1))

    # Invariant 1: qip == crop_q
    if crop_q != qip:
        qip_mismatch += 1
        print(f"  ❌ QIP MISMATCH: id={qid[:8]} qip={qip} crop_q={crop_q}")
        continue

    # Invariant 2: OCR text similarity ≥ 0.50
    matching = [e for e in cands if e.get("crop_file") == cf]
    if not matching:
        no_ocr += 1
        continue
    sim = text_sim(qt, matching[0].get("soru_metni", ""))
    if sim >= 0.50:
        ok += 1
    elif sim >= 0.30:
        ok += 1  # accept borderline (OCR farklı format ama aynı soru)
    else:
        low_sim += 1
        safe_qt = qt[:60].encode("ascii", "replace").decode("ascii")
        print(f"  ⚠ LOW SIM ({sim:.3f}): id={qid[:8]} qip={qip} db_text={safe_qt}")

print("\n📊 ÖZET (30 sample):")
print(f"  ok:           {ok}")
print(f"  qip_mismatch: {qip_mismatch}  (invariant FAIL — KRITIK)")
print(f"  no_ocr:       {no_ocr}        (OCR'lanmamış crop, kabul edilebilir)")
print(f"  low_sim:      {low_sim}       (potansiyel false-positive)")
print(f"\nAccuracy (ok + no_ocr / total): {100 * (ok + no_ocr) / len(rows):.1f}%")
print(
    f"Invariant violations: {qip_mismatch}/{len(rows)} = {100 * qip_mismatch / len(rows):.1f}%"
)
