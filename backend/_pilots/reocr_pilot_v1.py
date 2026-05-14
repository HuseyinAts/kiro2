#!/usr/bin/env python3
"""
Faz 1.10 Re-OCR Pilot v1 — Gemini Pro vision, 30 sample (15 direct + 15 page).

Strateji:
  - Direct bucket (jsonl_var_metin_var_disk_var): crop dosyasi -> Pro vision
  - Page-level bucket (jsonl_yok): sayfa screenshot -> Pro vision (sayfada
    q_no={qn} sorusunu cikar)

Cikti:
  - backend/_pilots/20260516_reocr_pilot_v1_RAW.tsv (full Gemini OCR ciktisi)
  - backend/_pilots/20260516_reocr_pilot_v1_SCORING.tsv (Huseyin scoring icin)
  - Console: substring overlap istatistik

Karpathy/Tier H lesson: 30 sample minimum, hem direct hem page-level test.
Cift sinyal: (a) Re-OCR metin DB question_text ile uyumlu mu (substring overlap)
              (b) Manuel Huseyin pixel-onay (TSV uzerinden)
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
D_DATASET = PROJECT_ROOT / "d-dataset"
CROP_BASE = D_DATASET / "output" / "crops"
SCREENSHOTS = PROJECT_ROOT / "veriseti" / "zkitap" / "screenshots"
OUT_DIR = Path(__file__).parent
RAW_TSV = OUT_DIR / "20260516_reocr_pilot_v2_RAW.tsv"
SCORING_TSV = OUT_DIR / "20260516_reocr_pilot_v2_SCORING.tsv"
FEASIBILITY_TSV = OUT_DIR / "20260516_re_ocr_feasibility_RESULT.tsv"

PILOT_N_DIRECT = 30
PILOT_N_PAGE = 20
PILOT_SEED = 42
RATE_LIMIT_S = 0.5  # 0.5s/call ~120/dakika (free tier ile uyumlu)

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

PROMPT_PAGE = """You are a high-precision OCR for Turkish YKS exam pages.

This is a FULL PAGE from a Turkish math/physics/geometry textbook.
Find question number {qn} on this page.

Output STRICT JSON only:
{{
  "soru_no": {qn},
  "soru_metni": "<full question text for #{qn}, in NFC Turkish>",
  "secenekler": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
  "has_diagram": true/false,
  "diagram_description": "<brief>" or null,
  "found": true/false
}}

If question #{qn} not found on this page, return {{"found": false}}.
NFC Turkish, preserve LaTeX math, no prose around JSON.
"""


def nfc_lower(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("İ", "i").replace("I", "ı")
    return s.lower()


def jaccard(a: str, b: str) -> float:
    """Word-level Jaccard, NFC + Turkish lowercase."""
    sa = set(nfc_lower(a).split())
    sb = set(nfc_lower(b).split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def substring_overlap(db_text: str, ocr_text: str) -> tuple[int, float]:
    """4+ harf kelime kac tanesi DB metninde yer aliyor (% overlap)."""
    db_norm = nfc_lower(db_text)
    ocr_words = [w for w in nfc_lower(ocr_text).split() if len(w) >= 4]
    if not ocr_words:
        return 0, 0.0
    found = sum(1 for w in ocr_words if w in db_norm)
    return found, found / len(ocr_words)


def load_feasibility() -> list[dict]:
    """Re-OCR feasibility TSV oku."""
    if not FEASIBILITY_TSV.exists():
        raise SystemExit(
            f"Feasibility TSV bulunamadi: {FEASIBILITY_TSV}\n"
            f"Once audit_re_ocr_feasibility.py calistir."
        )
    rows = []
    with open(FEASIBILITY_TSV, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != len(header):
                continue
            rows.append(dict(zip(header, parts)))
    return rows


def select_samples(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Seed'li 15 direct + 15 page-level secim."""
    direct = [
        r
        for r in rows
        if r["match_type"] in ("soru_no_match", "q_idx_match")
        and r["disk_exists"] == "True"
        and r["q_no"] not in ("", "None")
    ]
    page = [r for r in rows if r["match_type"] == "no_match"]
    rng = random.Random(PILOT_SEED)
    direct_sample = rng.sample(direct, min(PILOT_N_DIRECT, len(direct)))
    page_sample = rng.sample(page, min(PILOT_N_PAGE, len(page)))
    return direct_sample, page_sample


def resolve_crop_path(book: str, crop_file: str) -> Path | None:
    p1 = CROP_BASE / book.replace(" ", "_") / crop_file
    p2 = CROP_BASE / book / crop_file
    return p1 if p1.exists() else (p2 if p2.exists() else None)


def resolve_page_path(book: str, page: int) -> Path | None:
    """source_book -> screenshots dir name (case + space sensitive)."""
    candidates = [
        SCREENSHOTS / book / f"sayfa_{page:04d}.png",
    ]
    book_dir = SCREENSHOTS / book
    if not book_dir.exists():
        # Fuzzy: lowercase + nfc match
        target = nfc_lower(book)
        for d in SCREENSHOTS.iterdir():
            if d.is_dir() and nfc_lower(d.name) == target:
                candidates.insert(0, d / f"sayfa_{page:04d}.png")
                break
    for c in candidates:
        if c.exists():
            return c
    return None


def fetch_db_text(ids: list[str]) -> dict[str, dict]:
    from sqlalchemy import create_engine, text

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    engine = create_engine(db_url)
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT id, question_text, option_a, option_b, option_c, option_d, option_e, correct_answer
            FROM question_bank WHERE id = ANY(:ids)
        """),
            {"ids": ids},
        ).fetchall()
    return {
        r[0]: {
            "text": r[1],
            "A": r[2],
            "B": r[3],
            "C": r[4],
            "D": r[5],
            "E": r[6],
            "ans": r[7],
        }
        for r in rows
    }


def call_gemini(model, image_path: Path, prompt: str) -> dict:
    """Gemini Pro vision call, JSON parse."""
    import PIL.Image

    img = PIL.Image.open(image_path)
    resp = model.generate_content([prompt, img])
    raw = resp.text.strip()
    # JSON fence soyma
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        raw = raw.rsplit("```", 1)[0]
    if raw.startswith("json"):
        raw = raw[4:].strip()
    try:
        return {"ok": True, "data": json.loads(raw), "raw": resp.text}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": str(e), "raw": resp.text}


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit(
            "GEMINI_API_KEY env var set degil.\n"
            "PowerShell: $env:GEMINI_API_KEY = '...'\n"
            "Bash: export GEMINI_API_KEY='...'"
        )

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-2.5-pro",
        generation_config={"temperature": 0.0, "max_output_tokens": 4096},
    )
    print("[gemini] gemini-2.5-pro initialized", flush=True)

    rows = load_feasibility()
    print(f"[feasibility] {len(rows):,} satir yuklendi", flush=True)

    direct_sample, page_sample = select_samples(rows)
    print(
        f"[sample] {len(direct_sample)} direct + {len(page_sample)} page-level",
        flush=True,
    )

    all_ids = [r["id"] for r in direct_sample] + [r["id"] for r in page_sample]
    db_data = fetch_db_text(all_ids)
    print(f"[db] {len(db_data)} DB row fetched", flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_f = open(RAW_TSV, "w", encoding="utf-8")
    raw_f.write(
        "idx\tbucket\tid\tbook\tpage\tq_no\timage_path\tok\tjaccard\tsubstr_pct\tdb_len\tdb_tail80\tocr_text\traw_response\n"
    )

    scoring_f = open(SCORING_TSV, "w", encoding="utf-8")
    scoring_f.write(
        "idx\tbucket\tid\tbook\tpage\tq_no\timage_path\tdb_len\tdb_tail80\tocr_text_full\tjaccard\tsubstr_pct\tverdict_huseyin\n"
    )

    stats = Counter()
    results = []
    idx = 0

    def process_sample(bucket: str, sample: list[dict], get_image, prompt_fn):
        nonlocal idx
        for r in sample:
            idx += 1
            id_ = r["id"]
            book = r["book"]
            page = int(r["page"])
            q_no = r["q_no"]
            img_path = get_image(r)
            db_row = db_data.get(id_, {})
            db_text_full = db_row.get("text", "")

            db_len = len(db_text_full or "")
            db_tail80 = (db_text_full or "")[-80:].replace("\t", " ").replace("\n", " ")

            if not img_path:
                print(
                    f"[{idx:02d}/{len(direct_sample) + len(page_sample)}] {bucket} id={id_[:8]} SKIP (image yok)",
                    flush=True,
                )
                stats[f"{bucket}_no_image"] += 1
                raw_f.write(
                    f"{idx}\t{bucket}\t{id_}\t{book}\t{page}\t{q_no}\tNONE\tFalse\t0\t0\t{db_len}\t{db_tail80}\tNO_IMAGE\t\n"
                )
                continue

            prompt = prompt_fn(r)
            try:
                result = call_gemini(model, img_path, prompt)
            except Exception as e:
                print(f"[{idx:02d}] HATA: {e}", flush=True)
                stats[f"{bucket}_error"] += 1
                raw_f.write(
                    f"{idx}\t{bucket}\t{id_}\t{book}\t{page}\t{q_no}\t{img_path}\tFalse\t0\t0\t{db_len}\t{db_tail80}\tERROR:{str(e)[:200]}\t\n"
                )
                continue

            if not result["ok"]:
                stats[f"{bucket}_json_fail"] += 1
                ocr_text = result["raw"][:200].replace("\t", " ").replace("\n", " ")
                raw_f.write(
                    f"{idx}\t{bucket}\t{id_}\t{book}\t{page}\t{q_no}\t{img_path}\tFalse\t0\t0\t{db_len}\t{db_tail80}\t{ocr_text}\t{result['raw'][:500].replace(chr(9), ' ').replace(chr(10), ' ')}\n"
                )
                print(f"[{idx:02d}] JSON FAIL", flush=True)
                time.sleep(RATE_LIMIT_S)
                continue

            data = result["data"]
            if bucket == "page" and not data.get("found", True):
                stats[f"{bucket}_not_found"] += 1
                raw_f.write(
                    f"{idx}\t{bucket}\t{id_}\t{book}\t{page}\t{q_no}\t{img_path}\tFalse\t0\t0\t{db_len}\t{db_tail80}\tNOT_FOUND\t{result['raw'][:300].replace(chr(9), ' ').replace(chr(10), ' ')}\n"
                )
                print(f"[{idx:02d}] q_no={q_no} sayfada bulunamadi", flush=True)
                time.sleep(RATE_LIMIT_S)
                continue

            ocr_text = data.get("soru_metni", "")
            sims = jaccard(db_text_full, ocr_text)
            substr_n, substr_pct = substring_overlap(db_text_full, ocr_text)

            verdict_band = (
                "high" if substr_pct >= 0.70 else "mid" if substr_pct >= 0.50 else "low"
            )
            stats[f"{bucket}_{verdict_band}"] += 1

            ocr_clean = ocr_text.replace("\t", " ").replace("\n", " ")
            raw_f.write(
                f"{idx}\t{bucket}\t{id_}\t{book}\t{page}\t{q_no}\t{img_path}\tTrue\t{sims:.3f}\t{substr_pct:.3f}\t"
                f"{db_len}\t{db_tail80}\t{ocr_clean[:200]}\t"
                f"{result['raw'][:300].replace(chr(9), ' ').replace(chr(10), ' ')}\n"
            )
            scoring_f.write(
                f"{idx}\t{bucket}\t{id_}\t{book}\t{page}\t{q_no}\t{img_path}\t"
                f"{db_len}\t{db_tail80}\t{ocr_clean}\t"
                f"{sims:.3f}\t{substr_pct:.3f}\t\n"
            )

            print(
                f"[{idx:02d}/{len(direct_sample) + len(page_sample)}] {bucket} id={id_[:8]} sim={sims:.2f} substr={substr_pct:.2f}",
                flush=True,
            )
            time.sleep(RATE_LIMIT_S)

    print("\n=== DIRECT BUCKET ===\n")
    process_sample(
        "direct",
        direct_sample,
        lambda r: resolve_crop_path(r["book"], r["crop_file"]),
        lambda r: PROMPT_DIRECT,
    )

    print("\n=== PAGE-LEVEL BUCKET ===\n")
    process_sample(
        "page",
        page_sample,
        lambda r: resolve_page_path(r["book"], int(r["page"])),
        lambda r: PROMPT_PAGE.format(qn=r["q_no"] or "?"),
    )

    raw_f.close()
    scoring_f.close()

    print("\n=== STATS ===")
    for k, v in stats.most_common():
        print(f"  {k:30s} {v}")
    print(f"\nRAW:     {RAW_TSV}")
    print(f"SCORING: {SCORING_TSV}")
    print(
        "\nHuseyin: SCORING_TSV'yi ac, her satir icin verdict_huseyin kolonuna 'ok'/'wrong'/'partial' yaz."
    )


if __name__ == "__main__":
    main()
