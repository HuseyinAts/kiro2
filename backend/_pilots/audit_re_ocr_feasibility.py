#!/usr/bin/env python3
"""
Faz 1.10 Pre-flight: 4,994 has_diagram=true missing satirin disk crop + jsonl
durumunu sorgulayarak Re-OCR matematik bound'unu hesaplar.

Sorgular:
  1. Kac satirin (book, page, q_no) tuple'i jsonl'da var? (key match)
  2. Match olan satirlarin crop_file'i disk'te mevcut mu?
  3. soru_metni="" olan kac jsonl kaydi var (bos OCR = Re-OCR adayi)?
  4. Bucket dagilim: jsonl_match+disk_var / jsonl_match+disk_yok / jsonl_yok

Output: backend/_pilots/20260516_re_ocr_feasibility_RESULT.{tsv,md}
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
D_DATASET = PROJECT_ROOT / "d-dataset"
JSONL = D_DATASET / "output" / "ocr_crops" / "results.jsonl"
CROP_BASE = D_DATASET / "output" / "crops"
OUT_DIR = Path(__file__).parent
TSV_OUT = OUT_DIR / "20260516_re_ocr_feasibility_RESULT.tsv"
MD_OUT = OUT_DIR / "20260516_re_ocr_feasibility_RESULT.md"


def get_engine():
    from sqlalchemy import create_engine

    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")
    return create_engine(db_url)


def parse_q_no(q_no_raw: str | None) -> int | None:
    """'Örnek: 6' or '6' -> 6"""
    if not q_no_raw:
        return None
    s = str(q_no_raw).strip()
    digits = "".join(c for c in s if c.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def load_jsonl_index():
    """jsonl -> dict[(book, page, soru_no/question_index)] = (crop_file, soru_metni)
    Hem soru_no hem question_index ile indeksle (ikisi de denenir).
    """
    print(f"[load] {JSONL.name} okunuyor...", flush=True)
    by_soru_no: dict[tuple[str, int, int], tuple[str, str]] = {}
    by_q_idx: dict[tuple[str, int, int], tuple[str, str]] = {}
    empty_ocr = 0
    total = 0
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            total += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            book = rec.get("book")
            page = rec.get("page_num")
            crop_file = rec.get("crop_file")
            soru_no = rec.get("soru_no")
            q_idx = rec.get("question_index")
            soru_metni = rec.get("soru_metni") or ""
            if not crop_file or not book or page is None:
                continue
            if not soru_metni.strip():
                empty_ocr += 1
            if soru_no is not None:
                try:
                    sn = int(soru_no)
                    by_soru_no[(book, int(page), sn)] = (crop_file, soru_metni)
                except (ValueError, TypeError):
                    pass
            if q_idx is not None:
                try:
                    qi = int(q_idx)
                    by_q_idx[(book, int(page), qi)] = (crop_file, soru_metni)
                except (ValueError, TypeError):
                    pass
    print(
        f"[load] {total:,} jsonl satir, {len(by_soru_no):,} soru_no key, "
        f"{len(by_q_idx):,} q_idx key, {empty_ocr:,} bos OCR",
        flush=True,
    )
    return by_soru_no, by_q_idx, empty_ocr, total


def main():
    engine = get_engine()
    print("[db] missing rows fetch...", flush=True)

    from sqlalchemy import text

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT id, source_book, source_page,
                   pipeline_metadata->'ai_extras'->>'q_no' AS q_no_raw,
                   pipeline_metadata->>'request_key' AS req_key,
                   LEFT(question_text, 100) AS preview
            FROM question_bank
            WHERE is_active = TRUE
              AND question_image_url IS NULL
              AND (pipeline_metadata->'ai_extras'->>'has_diagram')::boolean = TRUE
        """)
        ).fetchall()
    print(f"[db] {len(rows):,} missing satir cekildi", flush=True)

    by_soru_no, by_q_idx, jsonl_empty, jsonl_total = load_jsonl_index()

    # Bucket analizi
    buckets = Counter()
    results = []
    book_match: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [match, total]

    for row in rows:
        id_, book, page, q_no_raw, req_key, preview = row
        qn = parse_q_no(q_no_raw)
        book_match[book][1] += 1

        crop_file = None
        soru_metni = ""
        match_type = "no_match"

        # Strategy 1: (book, page, qn) soru_no match
        if qn is not None and (book, page, qn) in by_soru_no:
            crop_file, soru_metni = by_soru_no[(book, page, qn)]
            match_type = "soru_no_match"
        # Strategy 2: (book, page, qn) question_index match
        elif qn is not None and (book, page, qn) in by_q_idx:
            crop_file, soru_metni = by_q_idx[(book, page, qn)]
            match_type = "q_idx_match"

        # Disk check
        disk_exists = False
        if crop_file:
            crop_path = CROP_BASE / book.replace(" ", "_") / crop_file
            # Fallback: book ad direkt klasör adı olabilir
            if not crop_path.exists():
                crop_path = CROP_BASE / book / crop_file
            disk_exists = crop_path.exists()

        if match_type == "no_match":
            buckets["jsonl_yok"] += 1
        elif disk_exists:
            if soru_metni.strip():
                buckets["jsonl_var_metin_var_disk_var"] += 1
            else:
                buckets["jsonl_var_metin_bos_disk_var"] += 1
            book_match[book][0] += 1
        else:
            buckets["jsonl_var_disk_yok"] += 1

        results.append(
            {
                "id": id_,
                "book": book,
                "page": page,
                "q_no": qn,
                "match_type": match_type,
                "crop_file": crop_file or "",
                "soru_metni_len": len(soru_metni.strip()) if soru_metni else 0,
                "disk_exists": disk_exists,
                "preview": (preview or "").replace("\t", " ").replace("\n", " ")[:100],
            }
        )

    # Yaz: TSV
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(TSV_OUT, "w", encoding="utf-8") as f:
        f.write(
            "id\tbook\tpage\tq_no\tmatch_type\tcrop_file\tsoru_metni_len\tdisk_exists\tpreview\n"
        )
        for r in results:
            f.write(
                f"{r['id']}\t{r['book']}\t{r['page']}\t{r['q_no']}\t{r['match_type']}\t"
                f"{r['crop_file']}\t{r['soru_metni_len']}\t{r['disk_exists']}\t{r['preview']}\n"
            )

    # Yaz: MD özet
    total = sum(buckets.values())
    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("# Re-OCR Feasibility Audit — 16 May 2026\n\n")
        f.write(f"**Total missing satır**: {total:,}\n\n")
        f.write("## Bucket Dağılımı\n\n")
        f.write("| Bucket | Count | % | Re-OCR Strategy |\n")
        f.write("|---|---|---|---|\n")
        strategies = {
            "jsonl_var_metin_bos_disk_var": "✅ **Disk crop var, OCR boş → Direct Re-OCR (en kolay)**",
            "jsonl_var_metin_var_disk_var": "✅ **Disk crop var, OCR var ama sim<0.50 → Re-OCR ile düzelt**",
            "jsonl_var_disk_yok": "⚠️ Disk eksik — jsonl ile silinmiş crop? Skip veya page Re-OCR",
            "jsonl_yok": "⚠️ jsonl'da yok → Page-level Re-OCR (full sayfa görseli işle)",
        }
        for bucket, count in buckets.most_common():
            pct = count * 100 / total if total else 0
            strategy = strategies.get(bucket, "?")
            f.write(f"| `{bucket}` | {count:,} | %{pct:.1f} | {strategy} |\n")
        f.write("\n## jsonl Global Stats\n\n")
        f.write(f"- Total jsonl rows: {jsonl_total:,}\n")
        f.write(
            f'- Empty OCR (soru_metni=""): {jsonl_empty:,} (%{jsonl_empty * 100 / jsonl_total:.1f})\n'
        )
        f.write("\n## Top 10 Book (en çok missing)\n\n")
        f.write("| Book | match/total | match_rate |\n")
        f.write("|---|---|---|\n")
        top_books = sorted(book_match.items(), key=lambda x: -x[1][1])[:10]
        for book, (m, t) in top_books:
            rate = m * 100 / t if t else 0
            f.write(f"| {book[:60]} | {m}/{t} | %{rate:.1f} |\n")

    print("\n=== BUCKETS ===")
    for bucket, count in buckets.most_common():
        pct = count * 100 / total if total else 0
        print(f"  {bucket:40s} {count:5d} (%{pct:.1f})")
    print(f"\nTSV: {TSV_OUT}")
    print(f"MD:  {MD_OUT}")


if __name__ == "__main__":
    main()
