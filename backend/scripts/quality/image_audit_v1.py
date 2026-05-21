#!/usr/bin/env python3
"""
Bug #11 fix — Image Audit Pipeline (Gemini Vision)

Beta test (17 May 2026): Hüseyin ekran görüntüleri 3-sample vision audit
ortaya koydu ki Bug #8 fix yetersiz:
  - %100 sample'da solution leak (image içinde options görünüyor)
  - %67 sample'da content mismatch (DB text ≠ image içeriği)
  - %100 sample'da q_index yanlış (URL q_no ≠ image soru numarası)

Bu Bug #8 fix tier-based çıkardı (37,490 page-level) ama no_tier
46,749 sample'da da aynı patoloji var.

KALICI ÇÖZÜM: Her image'ı Gemini Vision ile audit et, sonuç DB'ye yaz,
beta sadece audit-passed sample'ları görür.

PER IMAGE OUTPUT (JSON):
  {
    "has_options": bool,          # Image içinde A) B) C) D) E) görünüyor mu?
    "content_match": bool,        # Image içerik DB text ile uyuşuyor mu?
    "image_quality": str,         # "clean" | "options_visible" | "page_full" | "empty"
    "primary_content": str,       # "figure" | "table" | "graph" | "text" | "mixed"
    "confidence": float,          # 0.0-1.0
    "notes": str                  # Kısa açıklama
  }

VERDICT MATRIX:
  has_options=False AND content_match=True  → CLEAN     (beta-eligible)
  has_options=True  AND content_match=True  → SALVAGE   (re-crop adayı)
  has_options=False AND content_match=False → REJECT    (mismatch)
  has_options=True  AND content_match=False → REJECT    (mismatch + leak)

PIPELINE_METADATA.IMAGE_AUDIT_V1 YAZILIR (idempotent).

USAGE:
  # Pilot (20 sample, smoke test):
  python backend/scripts/quality/image_audit_v1.py --pilot 20

  # Scale validation (500 sample):
  python backend/scripts/quality/image_audit_v1.py --pilot 500

  # Full audit (84K sample, background):
  python backend/scripts/quality/image_audit_v1.py --full --workers 10

  # Resume previous run:
  python backend/scripts/quality/image_audit_v1.py --full --resume --workers 10
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
CHECKPOINT_FILE = PILOTS_DIR / "checkpoint_image_audit_v1.json"
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")
AUDIT_VERSION = "v1"

MODEL_NAME = "gemini-2.5-flash"  # Cheap, fast, Vision-capable

# Crop file location (Docker volume mount)
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"

PROMPT_TEMPLATE = """Sen bir TYT/AYT sınavı içerik analiz uzmanısın. Aşağıdaki image bir Türkçe öğrenci sınav sorusuna ait.

Verilen DB soru metni:
\"\"\"{question_text}\"\"\"

Image'ı incele. Sadece JSON döndür, başka metin YOK:

{{
  "has_options": <true|false>,
  "content_match": <true|false>,
  "image_quality": "<clean|options_visible|page_full|empty>",
  "primary_content": "<figure|table|graph|text|mixed>",
  "confidence": <0.0-1.0>,
  "notes": "<kısa Türkçe açıklama, max 100 char>"
}}

Tanımlar:
- has_options: Image'ın içinde A) B) C) D) E) gibi çoktan seçmeli şıklar GÖRÜNÜYOR mu? (yanıt anahtarı sızıntısı)
- content_match: Image'daki görsel içerik DB soru metni ile EŞLEŞIYOR mu? (örn. metin "3 birim", image "2 birim" → false)
- image_quality:
    - "clean": sadece şekil/grafik/tablo (options yok, sayfa yapısı yok)
    - "options_visible": şekil + altında options bloğu görünür
    - "page_full": tüm kitap sayfası (options + diğer soru parçaları)
    - "empty": boş/bozuk/anlaşılmaz
- confidence: cevabınızdan ne kadar emin (0.0=bilemiyorum, 1.0=kesin)
"""


# ============================================================================
# DB
# ============================================================================
def get_engine():
    from sqlalchemy import create_engine

    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def fetch_samples(limit: int | None, exclude_audited: bool = True):
    """Audit-bekleyen sample'ları çek."""
    from sqlalchemy import text

    where = """
        is_active = TRUE
        AND quality_review_status IN ('human_verified', 'auto_judged_high')
        AND question_image_url IS NOT NULL
        AND question_image_url != ''
    """
    if exclude_audited:
        where += """
        AND (
            pipeline_metadata IS NULL
            OR NOT (pipeline_metadata::jsonb ? 'image_audit_v1')
        )
        """

    sql = f"""
        SELECT id::text AS id, question_text, question_image_url, subject_area
        FROM question_bank
        WHERE {where}
        ORDER BY md5(id::text)
        {f"LIMIT {limit}" if limit else ""}
    """

    eng = get_engine()
    with eng.connect() as c:
        rows = c.execute(text(sql)).fetchall()
    return [dict(r._mapping) for r in rows]


def write_audit_to_db(qid: str, audit_obj: dict, eng=None):
    """pipeline_metadata.image_audit_v1 yaz (idempotent)."""
    from sqlalchemy import text

    if eng is None:
        eng = get_engine()
    audit_json = json.dumps(audit_obj)
    with eng.begin() as c:
        c.execute(
            text(
                """
                UPDATE question_bank
                SET pipeline_metadata = jsonb_set(
                        COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                        '{image_audit_v1}',
                        CAST(:audit AS jsonb),
                        TRUE
                    )::json,
                    updated_at = NOW()
                WHERE id::text = :qid
                """
            ),
            {"qid": qid, "audit": audit_json},
        )


# ============================================================================
# Image resolve
# ============================================================================
def resolve_image_path(image_url: str) -> Path | None:
    """question_image_url → local Path."""
    if not image_url:
        return None
    # /static/crops/Book/Book_p0001_q01.png → CROPS_BASE/Book/Book_p0001_q01.png
    if image_url.startswith("/static/crops/"):
        rel = image_url[len("/static/crops/") :]
        return CROPS_BASE / rel
    return None


# ============================================================================
# Gemini Vision call
# ============================================================================
def call_gemini_vision(model, image_path: Path, question_text: str) -> dict:
    """Gemini Vision audit. Return dict (parsed JSON) or {"error": "..."}."""
    try:
        from PIL import Image
    except ImportError:
        return {"error": "PIL not installed"}

    if not image_path.exists():
        return {"error": f"image not found: {image_path}"}

    try:
        img = Image.open(image_path)
    except Exception as e:
        return {"error": f"PIL open failed: {e}"}

    prompt = PROMPT_TEMPLATE.format(
        question_text=(question_text or "")[:800]  # truncate to keep prompt small
    )

    try:
        response = model.generate_content(
            [prompt, img],
            generation_config={"temperature": 0.0, "max_output_tokens": 512},
        )
    except Exception as e:
        return {"error": f"gemini call failed: {type(e).__name__}: {e}"}

    # Try to extract text
    try:
        text_resp = response.text
    except Exception:
        # finish_reason != STOP etc.
        try:
            text_resp = response.candidates[0].content.parts[0].text
        except Exception as e:
            return {"error": f"no text in response: {e}"}

    # Parse JSON (Gemini sometimes wraps in ```json ... ```)
    cleaned = text_resp.strip()
    if cleaned.startswith("```"):
        # Strip first/last lines
        lines = cleaned.split("\n")
        cleaned = "\n".join(l for l in lines if not l.startswith("```"))
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except Exception as e:
        return {"error": f"json parse failed: {e}", "raw_text": text_resp[:300]}

    # Validate required fields
    required = ["has_options", "content_match", "image_quality", "primary_content"]
    missing = [k for k in required if k not in parsed]
    if missing:
        return {"error": f"missing fields: {missing}", "raw": parsed}

    return parsed


def compute_verdict(audit: dict) -> str:
    """Audit result → verdict."""
    if "error" in audit:
        return "error"
    h = audit.get("has_options", False)
    m = audit.get("content_match", False)
    if not h and m:
        return "clean"
    if h and m:
        return "salvage"
    return "reject"


# ============================================================================
# Checkpoint
# ============================================================================
_checkpoint_lock = threading.Lock()


def load_checkpoint() -> set:
    if not CHECKPOINT_FILE.exists():
        return set()
    try:
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        return set(data.get("processed", []))
    except Exception:
        return set()


def save_checkpoint(processed: set):
    with _checkpoint_lock:
        CHECKPOINT_FILE.write_text(
            json.dumps(
                {"processed": list(processed), "ts": datetime.now().isoformat()}
            ),
            encoding="utf-8",
        )


# ============================================================================
# Process single sample
# ============================================================================
_print_lock = threading.Lock()


def process_one(model, sample: dict, eng) -> dict:
    """Single sample audit → DB write → return result dict."""
    qid = sample["id"]
    img_path = resolve_image_path(sample["question_image_url"])

    if img_path is None or not img_path.exists():
        result = {
            "id": qid,
            "verdict": "error",
            "error": "image file missing",
            "image_url": sample["question_image_url"],
        }
        # Write error verdict to DB so we don't retry
        audit_obj = {
            "audit_date": AUDIT_DATE,
            "model": MODEL_NAME,
            "error": "image file missing",
            "verdict": "error",
        }
        try:
            write_audit_to_db(qid, audit_obj, eng)
        except Exception:
            pass
        return result

    audit_raw = call_gemini_vision(model, img_path, sample["question_text"])

    if "error" in audit_raw:
        result = {"id": qid, "verdict": "error", "error": audit_raw["error"]}
        audit_obj = {
            "audit_date": AUDIT_DATE,
            "model": MODEL_NAME,
            "error": audit_raw["error"],
            "verdict": "error",
        }
        try:
            write_audit_to_db(qid, audit_obj, eng)
        except Exception:
            pass
        return result

    verdict = compute_verdict(audit_raw)
    audit_obj = {
        "audit_date": AUDIT_DATE,
        "model": MODEL_NAME,
        "verdict": verdict,
        **audit_raw,
    }
    try:
        write_audit_to_db(qid, audit_obj, eng)
    except Exception as e:
        return {"id": qid, "verdict": verdict, "error": f"db write failed: {e}"}

    return {"id": qid, "verdict": verdict, **audit_raw}


# ============================================================================
# Main
# ============================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=None, help="N sample audit (test)")
    ap.add_argument("--full", action="store_true", help="Full pool audit")
    ap.add_argument("--resume", action="store_true", help="Skip already-audited")
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()

    if not (args.pilot or args.full):
        print("HATA: --pilot N veya --full gerekli", flush=True)
        sys.exit(2)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("HATA: GEMINI_API_KEY env var gerekli", flush=True)
        print("  Set ile: export GEMINI_API_KEY='AIza...'", flush=True)
        sys.exit(2)

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"[gemini] {MODEL_NAME} initialized", flush=True)

    limit = args.pilot if args.pilot else None
    samples = fetch_samples(limit, exclude_audited=args.resume or args.full)
    print(f"[samples] {len(samples):,} satır audit edilecek", flush=True)

    if not samples:
        print("[done] hiç sample yok", flush=True)
        return 0

    eng = get_engine()
    start = time.time()

    processed = load_checkpoint() if args.resume else set()
    if processed:
        samples = [s for s in samples if s["id"] not in processed]
        print(
            f"[resume] {len(processed):,} atlandı, {len(samples):,} kaldı", flush=True
        )

    stats = {"clean": 0, "salvage": 0, "reject": 0, "error": 0}
    stats_lock = threading.Lock()

    def _worker(s):
        result = process_one(model, s, eng)
        with stats_lock:
            stats[result.get("verdict", "error")] = (
                stats.get(result.get("verdict", "error"), 0) + 1
            )
        with _checkpoint_lock:
            processed.add(s["id"])
        return result

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(_worker, s) for s in samples]
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                r = fut.result()
                results.append(r)
            except Exception as e:
                with _print_lock:
                    print(f"[error] future failed: {e}", flush=True)
            # Progress + checkpoint every 50
            if i % 50 == 0:
                save_checkpoint(processed)
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta_min = (len(samples) - i) / rate / 60 if rate > 0 else 0
                with _print_lock:
                    print(
                        f"[progress] {i:,}/{len(samples):,}  "
                        f"clean={stats['clean']} salvage={stats['salvage']} "
                        f"reject={stats['reject']} error={stats['error']}  "
                        f"rate={rate:.1f}/s ETA={eta_min:.0f}min",
                        flush=True,
                    )

    save_checkpoint(processed)
    elapsed = time.time() - start

    # Final report
    print()
    print("=" * 60)
    print(f"[done] {len(samples):,} sample işlendi, {elapsed / 60:.1f} dakika")
    total = sum(stats.values())
    if total > 0:
        print(
            f"  clean:    {stats['clean']:>6,}  ({100 * stats['clean'] / total:.1f}%)"
        )
        print(
            f"  salvage:  {stats['salvage']:>6,}  ({100 * stats['salvage'] / total:.1f}%)"
        )
        print(
            f"  reject:   {stats['reject']:>6,}  ({100 * stats['reject'] / total:.1f}%)"
        )
        print(
            f"  error:    {stats['error']:>6,}  ({100 * stats['error'] / total:.1f}%)"
        )
    print("=" * 60)

    # Write result TSV
    if results:
        result_tsv = (
            PILOTS_DIR
            / f"{datetime.now().strftime('%Y%m%d')}_image_audit_v1_RESULT.tsv"
        )
        import csv as _csv

        with result_tsv.open("w", encoding="utf-8", newline="") as f:
            writer = _csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "verdict",
                    "has_options",
                    "content_match",
                    "image_quality",
                    "primary_content",
                    "confidence",
                    "notes",
                    "error",
                ],
                delimiter="\t",
                extrasaction="ignore",
            )
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        print(f"[result] {result_tsv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
