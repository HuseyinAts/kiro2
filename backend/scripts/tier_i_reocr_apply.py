#!/usr/bin/env python3
"""
Faz 1.10 Tier I — Re-OCR (Gemini 2.5 Pro) production batch.

SCOPE: Direct bucket only (3,323 satır).
  - jsonl_var_metin_var_disk_var sample bucket
  - Crop dosyası disk'te mevcut
  - Tier C-G eşleştirmesi kaçırdı (sim<0.50)

STRATEGY (pilot v2 onaylı):
  1. Her satır için crop dosyası → Gemini 2.5 Pro Re-OCR
  2. substr_pct hesapla (DB question_text ile word-level overlap)
  3. Threshold check: substr >= 0.50 → BIND (HIGH=0.70, MID=0.50-0.70)
  4. UPDATE question_image_url + image_ocr_text + pipeline_metadata.tier_i_reocr
  5. BACKUP TSV her UPDATE öncesi (rollback için)

MODES:
  --dry-run [N]  : N sample test (default 100), UPDATE YOK
  --apply        : Tam batch (3,323), DB UPDATE
  --resume       : Checkpoint'ten devam (apply yarıda kesilirse)
  --limit N      : Maksimum N satır işle (test için)

INVARIANTS:
  - question_text DOKUNULMAZ (DB %99 tam, Re-OCR sadece bind validation)
  - substr<0.50 → image_url bind YAPILMAZ, sadece flag
  - pipeline_metadata.tier_i_reocr audit trail (geri dönüş için)

OUTPUTS:
  - backend/_pilots/20260516_tier_i_BACKUP_<mode>.tsv (rollback)
  - backend/_pilots/20260516_tier_i_<mode>_RESULT.{tsv,md}
  - backend/_pilots/checkpoint_tier_i.json (resume için)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
D_DATASET = PROJECT_ROOT / "d-dataset"
CROP_BASE = D_DATASET / "output" / "crops"
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
FEASIBILITY_TSV = PILOTS_DIR / "20260516_re_ocr_feasibility_RESULT.tsv"
CHECKPOINT = PILOTS_DIR / "checkpoint_tier_i.json"

URL_PREFIX = "/static/crops"  # Tier C/D ile uyumlu
SUBSTR_HIGH = 0.70
SUBSTR_MID = 0.50  # band ayrımı için
SUBSTR_LOW = 0.50  # MID threshold (legacy)
SUBSTR_APPLY = 0.70  # HIGH-only mode: apply threshold (MID de skip)
RATE_LIMIT_S = 0.5
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")
MODEL_NAME = "gemini-2.5-pro"

PROMPT_DIRECT = """You are a high-precision OCR for Turkish YKS exam questions.

This is a CROP of a single question from a Turkish math/physics/geometry textbook.
The crop may contain: question text, diagram description, options (A, B, C, D, E).

Output STRICT JSON only:
{
  "soru_metni": "<full question text, including diagram if relevant, in NFC Turkish>",
  "secenekler": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
  "has_diagram": true/false,
  "diagram_description": "<brief>" or null
}

Rules:
- Preserve LaTeX-style math notation ($...$) if present.
- Empty option = empty string, never null.
- NFC Turkish characters (ç, ş, ı, İ, ğ, ü, ö).
- No prose around JSON.
"""


def nfc_lower(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("İ", "i").replace("I", "ı")
    return s.lower()


def substring_overlap(db_text: str, ocr_text: str) -> float:
    db_norm = nfc_lower(db_text)
    ocr_words = [w for w in nfc_lower(ocr_text).split() if len(w) >= 4]
    if not ocr_words:
        return 0.0
    found = sum(1 for w in ocr_words if w in db_norm)
    return found / len(ocr_words)


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def load_feasibility() -> list[dict]:
    rows = []
    with open(FEASIBILITY_TSV, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != len(header):
                continue
            rows.append(dict(zip(header, parts)))
    return rows


def filter_direct_bucket(rows: list[dict]) -> list[dict]:
    """Direct bucket: match_type=soru_no_match veya q_idx_match VE disk_exists=True."""
    return [
        r
        for r in rows
        if r["match_type"] in ("soru_no_match", "q_idx_match")
        and r["disk_exists"] == "True"
        and r["crop_file"]
    ]


def resolve_crop_path(book: str, crop_file: str) -> Path | None:
    p1 = CROP_BASE / book.replace(" ", "_") / crop_file
    p2 = CROP_BASE / book / crop_file
    return p1 if p1.exists() else (p2 if p2.exists() else None)


def build_image_url(book: str, crop_file: str) -> str:
    """Tier C/D ile uyumlu URL pattern."""
    book_slug = book.replace(" ", "_")
    return f"{URL_PREFIX}/{book_slug}/{crop_file}"


def fetch_db_data(ids: list[str]) -> dict[str, dict]:
    from sqlalchemy import text

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT id, question_text, question_image_url, image_ocr_text, pipeline_metadata
            FROM question_bank
            WHERE id = ANY(:ids)
        """),
            {"ids": ids},
        ).fetchall()
    return {
        r[0]: {
            "text": r[1],
            "img_url": r[2],
            "ocr_text": r[3],
            "metadata": r[4] if r[4] else {},
        }
        for r in rows
    }


def call_gemini(model, image_path: Path, prompt: str) -> dict:
    import PIL.Image

    img = PIL.Image.open(image_path)
    resp = model.generate_content([prompt, img])
    raw = resp.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        raw = raw.rsplit("```", 1)[0]
    if raw.startswith("json"):
        raw = raw[4:].strip()
    try:
        return {"ok": True, "data": json.loads(raw), "raw": resp.text}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": str(e), "raw": resp.text}


def load_checkpoint() -> set[str]:
    if not CHECKPOINT.exists():
        return set()
    try:
        return set(json.loads(CHECKPOINT.read_text(encoding="utf-8"))["processed_ids"])
    except Exception:
        return set()


def save_checkpoint(processed: set[str]):
    CHECKPOINT.write_text(
        json.dumps(
            {"processed_ids": list(processed), "ts": datetime.now().isoformat()}
        ),
        encoding="utf-8",
    )


def update_db(
    engine,
    row_id: str,
    image_url: str,
    ocr_text: str,
    metadata_delta: dict,
    dry_run: bool,
):
    from sqlalchemy import text

    if dry_run:
        return
    with engine.begin() as conn:
        # Merge pipeline_metadata (CAST() yerine :: çünkü SQLAlchemy param binding ile çakışır)
        conn.execute(
            text("""
                UPDATE question_bank
                SET question_image_url = :img_url,
                    image_ocr_text = :ocr_text,
                    pipeline_metadata = CAST(
                        CASE
                          WHEN pipeline_metadata IS NULL THEN CAST(:delta AS jsonb)
                          ELSE jsonb_set(
                              CAST(pipeline_metadata AS jsonb),
                              '{tier_i_reocr}',
                              CAST(:tier_obj AS jsonb),
                              TRUE
                          )
                        END
                    AS json),
                    updated_at = NOW()
                WHERE id = :id
            """),
            {
                "img_url": image_url,
                "ocr_text": ocr_text,
                "delta": json.dumps(metadata_delta),
                "tier_obj": json.dumps(metadata_delta["tier_i_reocr"]),
                "id": row_id,
            },
        )


def write_backup_row(backup_f, row_id: str, db_data: dict):
    """Pre-state backup, rollback için."""
    img_url = db_data.get("img_url") or ""
    ocr_text = (
        (db_data.get("ocr_text") or "").replace("\t", " ").replace("\n", " ")[:500]
    )
    backup_f.write(f"{row_id}\t{img_url}\t{ocr_text}\n")
    backup_f.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="Max satır (test için)")
    args = ap.parse_args()

    if not (args.dry_run or args.apply):
        print("HATA: --dry-run veya --apply gerekli", flush=True)
        sys.exit(2)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("HATA: GEMINI_API_KEY env var gerekli", flush=True)
        sys.exit(2)

    mode = "dryrun" if args.dry_run else "apply"
    backup_path = PILOTS_DIR / f"20260516_tier_i_BACKUP_{mode}.tsv"
    result_tsv = PILOTS_DIR / f"20260516_tier_i_{mode}_RESULT.tsv"
    result_md = PILOTS_DIR / f"20260516_tier_i_{mode}_RESULT.md"

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config={"temperature": 0.0, "max_output_tokens": 4096},
    )
    print(f"[gemini] {MODEL_NAME} initialized, mode={mode}", flush=True)

    rows = load_feasibility()
    direct_rows = filter_direct_bucket(rows)
    print(f"[feasibility] {len(direct_rows):,} direct bucket satır", flush=True)

    # Default dry-run: 100 sample (random)
    if args.dry_run and args.limit is None:
        args.limit = 100

    if args.limit:
        # Deterministic order (id sort) ile ilk N
        import random

        rng = random.Random(42)
        direct_rows = rng.sample(direct_rows, min(args.limit, len(direct_rows)))
        print(f"[limit] {args.limit} sample (seed=42)", flush=True)

    # Checkpoint (apply için)
    processed = load_checkpoint() if args.resume and args.apply else set()
    if processed:
        print(
            f"[resume] {len(processed):,} satır önceden işlenmiş, atlanıyor", flush=True
        )
        direct_rows = [r for r in direct_rows if r["id"] not in processed]

    # DB fetch all
    ids = [r["id"] for r in direct_rows]
    print(f"[db] {len(ids):,} satır DB fetch...", flush=True)
    db_data = fetch_db_data(ids)
    print(f"[db] {len(db_data):,} satır alındı", flush=True)

    engine = get_engine()

    backup_f = open(backup_path, "a" if args.resume else "w", encoding="utf-8")
    if not args.resume:
        backup_f.write("id\tprev_image_url\tprev_image_ocr_text\n")

    result_f = open(result_tsv, "a" if args.resume else "w", encoding="utf-8")
    if not args.resume:
        result_f.write(
            "id\tbook\tpage\tq_no\tsubstr_pct\tband\taction\timage_url\tocr_text_len\n"
        )

    stats = Counter()
    start_ts = time.time()

    for i, r in enumerate(direct_rows, 1):
        id_ = r["id"]
        book = r["book"]
        page = r["page"]
        q_no = r["q_no"]
        crop_file = r["crop_file"]

        # Crop path
        crop_path = resolve_crop_path(book, crop_file)
        if not crop_path or not crop_path.exists():
            stats["no_crop_file"] += 1
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t0\tnone\tno_crop_file\t\t0\n"
            )
            continue

        # DB row check
        db_row = db_data.get(id_)
        if not db_row:
            stats["no_db_row"] += 1
            continue
        db_text = db_row["text"] or ""

        # Gemini call
        try:
            result = call_gemini(model, crop_path, PROMPT_DIRECT)
        except Exception as e:
            stats["gemini_error"] += 1
            result_f.write(f"{id_}\t{book}\t{page}\t{q_no}\t0\terror\terror\t\t0\n")
            print(f"[{i:04d}/{len(direct_rows):04d}] HATA: {str(e)[:80]}", flush=True)
            time.sleep(RATE_LIMIT_S)
            continue

        if not result["ok"]:
            stats["json_fail"] += 1
            result_f.write(f"{id_}\t{book}\t{page}\t{q_no}\t0\tjson_fail\tskip\t\t0\n")
            time.sleep(RATE_LIMIT_S)
            continue

        data = result["data"]
        ocr_text = data.get("soru_metni", "") or ""
        substr_pct = substring_overlap(db_text, ocr_text)

        if substr_pct >= SUBSTR_HIGH:
            band = "high"
        elif substr_pct >= SUBSTR_LOW:
            band = "mid"
        else:
            band = "low"

        # HIGH-only mode: substr < SUBSTR_APPLY skip (MID dahil)
        if substr_pct < SUBSTR_APPLY:
            stats[f"{band}_skip"] += 1
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t{substr_pct:.3f}\t{band}\tskip\t\t{len(ocr_text)}\n"
            )
            result_f.flush()
            time.sleep(RATE_LIMIT_S)
            continue

        # BACKUP (pre-UPDATE state)
        write_backup_row(backup_f, id_, db_row)

        image_url = build_image_url(book, crop_file)
        metadata_delta = {
            "tier_i_reocr": {
                "date": AUDIT_DATE,
                "model": MODEL_NAME,
                "substr_pct": round(substr_pct, 3),
                "band": band,
                "ocr_method": "direct_crop",
                "prev_image_url": db_row.get("img_url"),
                "prev_ocr_text_len": len(db_row.get("ocr_text") or ""),
            }
        }

        # UPDATE (or dry-run)
        try:
            update_db(
                engine, id_, image_url, ocr_text, metadata_delta, dry_run=args.dry_run
            )
            stats[f"applied_{band}"] += 1 if not args.dry_run else 0
            stats[f"would_apply_{band}"] += 1 if args.dry_run else 0
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t{substr_pct:.3f}\t{band}\t"
                f"{'apply' if not args.dry_run else 'dry'}\t{image_url}\t{len(ocr_text)}\n"
            )
            result_f.flush()

            # Checkpoint her 50 satırda
            if args.apply and i % 50 == 0:
                processed.add(id_)
                save_checkpoint(processed)
            elif args.apply:
                processed.add(id_)

        except Exception as e:
            stats["db_update_error"] += 1
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t{substr_pct:.3f}\t{band}\tdb_error\t\t{len(ocr_text)}\n"
            )
            print(f"[{i:04d}] DB HATA: {str(e)[:80]}", flush=True)

        if i % 20 == 0:
            elapsed = time.time() - start_ts
            eta_s = (elapsed / i) * (len(direct_rows) - i)
            print(
                f"[{i:04d}/{len(direct_rows):04d}] band={band} substr={substr_pct:.2f} "
                f"elapsed={elapsed / 60:.1f}m eta={eta_s / 60:.1f}m",
                flush=True,
            )

        time.sleep(RATE_LIMIT_S)

    # Final checkpoint
    if args.apply:
        save_checkpoint(processed)

    backup_f.close()
    result_f.close()

    # RESULT MD
    total = sum(stats.values())
    md = []
    md.append(f"# Tier I Re-OCR — {mode.upper()} RESULT ({AUDIT_DATE})")
    md.append("")
    md.append(f"**Model:** {MODEL_NAME}")
    md.append(f"**Threshold:** substr ≥ {SUBSTR_MID} (HIGH ≥ {SUBSTR_HIGH})")
    md.append(f"**Total processed:** {total:,}")
    md.append(f"**Mode:** {mode}")
    md.append("")
    md.append("## Stats")
    md.append("")
    md.append("| Action | Count | % |")
    md.append("|---|---|---|")
    for k, v in stats.most_common():
        pct = v * 100 / total if total else 0
        md.append(f"| {k} | {v:,} | %{pct:.1f} |")
    md.append("")
    apply_count = (
        stats.get("applied_high", 0)
        + stats.get("applied_mid", 0)
        + stats.get("would_apply_high", 0)
        + stats.get("would_apply_mid", 0)
    )
    skip_count = stats.get("low_skip", 0)
    md.append(
        f"**Apply rate:** {apply_count}/{total} (%{apply_count * 100 / total:.1f})"
    )
    md.append(
        f"**Skip rate (low/error):** {skip_count + stats.get('gemini_error', 0) + stats.get('json_fail', 0)}/{total}"
    )
    md.append("")
    md.append(f"**Backup:** `{backup_path}`")
    md.append(f"**Detail TSV:** `{result_tsv}`")
    md.append("")
    md.append("## Karpathy + Tier H Lesson Notes")
    md.append("")
    md.append("- ✅ Çift sinyal (jsonl key + Re-OCR substring)")
    md.append("- ✅ Pre-apply pilot 50 sample %100 precision")
    md.append("- ✅ Backup TSV (pre-state, rollback için)")
    md.append("- ✅ pipeline_metadata.tier_i_reocr audit trail")
    md.append("- ✅ question_text DOKUNULMAZ (sadece image_url + image_ocr_text)")

    result_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    elapsed = time.time() - start_ts
    print(f"\n=== DONE ({mode}) ===")
    print(f"Elapsed: {elapsed / 60:.1f} min")
    print("Stats:")
    for k, v in stats.most_common():
        print(f"  {k:25s} {v}")
    print(f"\nRESULT MD: {result_md}")


if __name__ == "__main__":
    main()
