#!/usr/bin/env python3
"""
Faz 1.10 Tier I Post-Audit — Apply sonrası 50 random sample doğrulama.

SCOPE:
  - Input: tier_i_apply_RESULT.tsv (action=apply satırları)
  - Random 50 sample → DB state doğrulama → pixel-doğrulama TSV
  - Tier H lesson: Apply ÖNCESİ pilot + apply SONRASI audit ZORUNLU

INVARIANTS:
  - READ-ONLY (DB UPDATE YOK, apply'a çakışmaz)
  - Apply hala çalışırken paralel çalışabilir (snapshot at run-time)
  - Hüseyin pixel akışına uygun RAW TSV format

USAGE:
  python backend/scripts/tier_i_postaudit.py                # 50 sample, seed=42
  python backend/scripts/tier_i_postaudit.py --sample-size 100 --seed 7
  python backend/scripts/tier_i_postaudit.py --dry-run      # DB sorgu yapma, sadece sample seç
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
CROP_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"
DEFAULT_INPUT = PILOTS_DIR / "20260516_tier_i_apply_RESULT.tsv"
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")


def nfc_lower(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("İ", "i").replace("I", "ı")
    return s.lower()


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def load_apply_rows(tsv_path: Path) -> list[dict]:
    rows = []
    with open(tsv_path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != len(header):
                continue
            r = dict(zip(header, parts))
            if r.get("action") == "apply":
                rows.append(r)
    return rows


def fetch_db_state(ids: list[str]) -> dict[str, dict]:
    from sqlalchemy import text

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT id::text, question_text, question_image_url,
                   image_ocr_text, pipeline_metadata
            FROM question_bank
            WHERE id::text = ANY(:ids)
        """),
            {"ids": ids},
        ).fetchall()
    out = {}
    for r in rows:
        meta = r[4] if r[4] else {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        tier_i_flag = meta.get("tier_i_reocr", {}) if isinstance(meta, dict) else {}
        out[r[0]] = {
            "q_text": r[1] or "",
            "img_url": r[2] or "",
            "ocr_text": r[3] or "",
            "tier_i": tier_i_flag,
        }
    return out


def resolve_crop_path(book: str, image_url: str) -> Path | None:
    if not image_url:
        return None
    crop_file = image_url.rsplit("/", 1)[-1]
    p1 = CROP_BASE / book.replace(" ", "_") / crop_file
    p2 = CROP_BASE / book / crop_file
    return p1 if p1.exists() else (p2 if p2.exists() else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--sample-size", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    if not args.input.exists():
        print(f"[error] Input not found: {args.input}")
        return 1

    apply_rows = load_apply_rows(args.input)
    print(f"[load] {len(apply_rows)} action=apply satırı yüklendi ({args.input.name})")

    if len(apply_rows) == 0:
        print("[error] Apply satırı yok — apply henüz başlamadı/tamamlanmadı")
        return 1

    rng = random.Random(args.seed)
    sample_size = min(args.sample_size, len(apply_rows))
    sample = rng.sample(apply_rows, sample_size)
    print(f"[sample] {sample_size} random sample seçildi (seed={args.seed})")

    if args.dry_run:
        print("[dry-run] DB sorgu atlandı. Sample ID listesi:")
        for r in sample[:5]:
            print(
                f"  {r['id']} | {r['book'][:50]} | p{r['page']} q{r['q_no']} | substr={r['substr_pct']}"
            )
        print(f"  ... ({len(sample) - 5} more)")
        return 0

    ids = [r["id"] for r in sample]
    print(f"[db] {len(ids)} satır fetch ediliyor...")
    db_state = fetch_db_state(ids)
    print(f"[db] {len(db_state)} satır alındı")

    out_path = args.output or (
        PILOTS_DIR / f"20260516_tier_i_postaudit_n{sample_size}_RAW.tsv"
    )

    aligned = 0
    misaligned = 0
    flag_missing = 0
    crop_missing = 0
    not_in_db = 0

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(
            "id\tbook\tpage\tq_no\tsubstr_pct\timg_url_bound\ttier_i_flag_present\t"
            "crop_exists\tdb_q_text_preview\tdb_ocr_preview\tdiagnosis\n"
        )
        for r in sample:
            qid = r["id"]
            db = db_state.get(qid)
            if db is None:
                not_in_db += 1
                f.write(
                    f"{qid}\t{r['book']}\t{r['page']}\t{r['q_no']}\t{r['substr_pct']}\t"
                    f"NOT_IN_DB\tNOT_IN_DB\tNOT_IN_DB\t-\t-\tNOT_IN_DB\n"
                )
                continue

            expected_url = r["image_url"]
            url_bound = db["img_url"] == expected_url
            flag_present = bool(db["tier_i"].get("date"))
            crop_path = resolve_crop_path(r["book"], db["img_url"])
            crop_ok = crop_path is not None

            q_preview = (db["q_text"] or "")[:200].replace("\t", " ").replace("\n", " ")
            ocr_preview = (
                (db["ocr_text"] or "")[:200].replace("\t", " ").replace("\n", " ")
            )

            diagnosis = []
            if not url_bound:
                misaligned += 1
                diagnosis.append("URL_MISMATCH")
            else:
                aligned += 1
            if not flag_present:
                flag_missing += 1
                diagnosis.append("FLAG_MISSING")
            if not crop_ok:
                crop_missing += 1
                diagnosis.append("CROP_MISSING")
            if not diagnosis:
                diagnosis = ["OK"]

            f.write(
                f"{qid}\t{r['book']}\t{r['page']}\t{r['q_no']}\t{r['substr_pct']}\t"
                f"{'1' if url_bound else '0'}\t{'1' if flag_present else '0'}\t"
                f"{'1' if crop_ok else '0'}\t{q_preview}\t{ocr_preview}\t"
                f"{','.join(diagnosis)}\n"
            )

    print("\n[summary] Post-audit results:")
    print(
        f"  URL aligned:    {aligned}/{sample_size} ({100 * aligned / sample_size:.1f}%)"
    )
    print(
        f"  URL mismatch:   {misaligned}/{sample_size} ({100 * misaligned / sample_size:.1f}%)"
    )
    print(
        f"  Flag missing:   {flag_missing}/{sample_size} ({100 * flag_missing / sample_size:.1f}%)"
    )
    print(
        f"  Crop missing:   {crop_missing}/{sample_size} ({100 * crop_missing / sample_size:.1f}%)"
    )
    print(f"  Not in DB:      {not_in_db}/{sample_size}")
    print(f"\n[output] {out_path}")
    print("\nNext: Hüseyin pixel-doğrulama her sample için:")
    print("  - Crop dosyasını aç")
    print("  - DB q_text_preview ile karşılaştır")
    print("  - OK / WRONG / UNCLEAR işaretle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
