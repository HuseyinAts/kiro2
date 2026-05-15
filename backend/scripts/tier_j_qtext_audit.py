#!/usr/bin/env python3
"""
Tier J pre-audit — question_text drift detection (READ-ONLY).

PURPOSE:
  Tier I (Faz 1.10) bazı GEOMETRI satırlarında image_ocr_text'i legacy
  question_text'ten daha doğru yazdı (Sample 3: A(KBC) vs A(ABCD); Sample 7:
  |BK| vs |KI|). Tier J fizibilite kararı için tüm GEOMETRI HIGH apply
  satırlarında qtext vs image_ocr drift'i ölç.

SCOPE LIMITATION (Round 2 spot-check sonrası):
  - subject_area = 'GEOMETRI' YALNIZCA. Non-geometri'de Tier I marjinal/sıfır
    kazanç + KIMYA'da regression riski (sample n=5: 1 typo).
  - Memory referans: [[tier-i-subject-asymmetric]]

USAGE:
  python backend/scripts/tier_j_qtext_audit.py
  python backend/scripts/tier_j_qtext_audit.py --subject MATEMATIK  # opsiyonel
  python backend/scripts/tier_j_qtext_audit.py --sample-pixel 30    # pixel-verify sample export

OUTPUT:
  - _pilots/{date}_tier_j_audit_{subject}_RAW.tsv    : tüm row drift verisi
  - _pilots/{date}_tier_j_audit_{subject}_SUMMARY.md : drift dağılımı + öneri
  - _pilots/{date}_tier_j_pixel_sample_{subject}.tsv : random N sample (drift<0.85'ten)

NEXT (audit sonrası):
  Eğer drift class 'substantive' >100 satır → Tier J apply script tasarla
  (geometri-only, drift<0.85 + sample audit gate).
"""

from __future__ import annotations

import argparse
import os
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
TODAY = datetime.now().strftime("%Y%m%d")


def get_engine():
    from sqlalchemy import create_engine

    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5434/kiro2",
    ).replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    return create_engine(url)


def normalize_for_compare(text: str) -> str:
    """NFC normalize + lowercase + collapse whitespace for fair comparison."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    # Strip LaTeX delimiters $...$ ve \(...\)
    text = text.replace("$", " ").replace("\\(", " ").replace("\\)", " ")
    # Strip common LaTeX commands (basit yaklaşım)
    text = text.replace("\\perp", "⊥").replace("\\parallel", "∥")
    text = text.replace("\\sqrt", "√").replace("\\cdot", "·")
    text = text.replace("\\widehat{", "").replace("\\frac{", "").replace("}", " ")
    # Lowercase Türkçe-aware
    text = text.replace("İ", "i").replace("I", "ı").lower()
    # Collapse whitespace
    return " ".join(text.split())


def substring_overlap(a: str, b: str, min_word_len: int = 4) -> float:
    """
    Word-level Jaccard overlap on tokens with len >= min_word_len.
    (Tier I'daki substring_overlap ile aynı algoritma.)
    """
    a_norm = normalize_for_compare(a)
    b_norm = normalize_for_compare(b)
    a_words = {w for w in a_norm.split() if len(w) >= min_word_len}
    b_words = {w for w in b_norm.split() if len(w) >= min_word_len}
    if not a_words or not b_words:
        return 0.0
    intersection = len(a_words & b_words)
    union = len(a_words | b_words)
    return intersection / union if union > 0 else 0.0


def bucket_drift(sim: float) -> str:
    """Bucket drift severity."""
    if sim >= 0.90:
        return "high_agree"
    if sim >= 0.70:
        return "moderate_drift"
    if sim >= 0.50:
        return "substantive_drift"
    return "severe_drift"


def fetch_audit_data(engine, subject: str) -> list[dict]:
    """Fetch all Tier I HIGH applied rows for a subject."""
    from sqlalchemy import text

    sql = text(f"""
        SELECT id,
               subject_area,
               COALESCE(question_text, '') AS qtext,
               COALESCE(image_ocr_text, '') AS ocr,
               correct_answer,
               question_image_url,
               (pipeline_metadata::jsonb -> 'tier_i_reocr' ->> 'substr_pct')::float AS tier_i_substr
        FROM question_bank
        WHERE pipeline_metadata::jsonb -> 'tier_i_reocr' ->> 'band' = 'high'
          AND is_active = TRUE
          AND subject_area = '{subject}'
          AND question_text IS NOT NULL
          AND image_ocr_text IS NOT NULL
        ORDER BY id
    """)
    with engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(sql).fetchall()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", default="GEOMETRI")
    ap.add_argument(
        "--sample-pixel",
        type=int,
        default=30,
        help="Pixel-verify için drift bucket'tan random N sample export",
    )
    args = ap.parse_args()

    engine = get_engine()
    print(f"[fetch] Tier I HIGH apply rows, subject={args.subject}", flush=True)
    rows = fetch_audit_data(engine, args.subject)
    print(f"[fetch] {len(rows):,} satır alındı", flush=True)

    if not rows:
        print(f"[done] No HIGH apply rows for subject={args.subject}")
        return 0

    # Compute drift for each row
    print("[compute] qtext vs image_ocr substring_overlap...", flush=True)
    for r in rows:
        r["drift_sim"] = substring_overlap(r["qtext"], r["ocr"])
        r["drift_class"] = bucket_drift(r["drift_sim"])

    # Bucket stats
    buckets = Counter(r["drift_class"] for r in rows)
    n = len(rows)

    # Output RAW TSV
    raw_path = PILOTS_DIR / f"{TODAY}_tier_j_audit_{args.subject}_RAW.tsv"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(
            "id\tsubject\tdrift_sim\tdrift_class\ttier_i_substr\tcorrect_answer\t"
            "qtext_preview\tocr_preview\timage_url\n"
        )
        for r in sorted(rows, key=lambda x: x["drift_sim"]):
            qprev = (r["qtext"][:120] or "").replace("\t", " ").replace("\n", " ")
            oprev = (r["ocr"][:120] or "").replace("\t", " ").replace("\n", " ")
            f.write(
                f"{r['id']}\t{r['subject_area']}\t{r['drift_sim']:.3f}\t"
                f"{r['drift_class']}\t{r['tier_i_substr'] or 0:.3f}\t"
                f"{r['correct_answer'] or ''}\t"
                f"{qprev}\t{oprev}\t{r['question_image_url'] or ''}\n"
            )
    print(f"[output] RAW: {raw_path}", flush=True)

    # Output SUMMARY md
    summary_path = PILOTS_DIR / f"{TODAY}_tier_j_audit_{args.subject}_SUMMARY.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Tier J Pre-Audit — {args.subject} (n={n:,})\n\n")
        f.write(f"**Tarih:** {TODAY}\n")
        f.write(
            f"**Source:** question_bank WHERE pipeline_metadata.tier_i_reocr.band='high' AND subject_area='{args.subject}'\n\n"
        )
        f.write("## Drift Dağılımı (qtext vs image_ocr_text)\n\n")
        f.write("| Bucket | Range | n | % | Tier J Yön |\n")
        f.write("|---|---|---:|---:|---|\n")
        descriptions = {
            "high_agree": (">=0.90", "🟢 NO-OP — qtext ve image_ocr aynı, dokunma"),
            "moderate_drift": ("0.70-0.90", "🟡 INSPECT — örnekleme + manuel"),
            "substantive_drift": (
                "0.50-0.70",
                "🟠 LIKELY UPGRADE — image_ocr büyük olasılıkla daha doğru",
            ),
            "severe_drift": (
                "<0.50",
                "🔴 PIXEL-VERIFY ZORUNLU — yüksek değişiklik, image'a karşı doğrula",
            ),
        }
        for bucket in [
            "high_agree",
            "moderate_drift",
            "substantive_drift",
            "severe_drift",
        ]:
            count = buckets.get(bucket, 0)
            pct = (count / n * 100) if n else 0
            range_, action = descriptions[bucket]
            f.write(f"| {bucket} | {range_} | {count:,} | {pct:.1f} | {action} |\n")
        f.write(f"| **TOPLAM** | | **{n:,}** | 100.0 | |\n\n")

        # Tier J recommendation
        gain_candidates = buckets.get("substantive_drift", 0) + buckets.get(
            "severe_drift", 0
        )
        f.write("## Tier J Apply Önerisi\n\n")
        if gain_candidates < 50:
            f.write(
                f"⏸️ **DEFER** — Sadece {gain_candidates} satır drift<0.70. "
                f"Tier J apply effort/payoff zayıf. Judge pipeline'a bırak.\n"
            )
        elif gain_candidates < 200:
            f.write(
                f"🟡 **PILOT-FIRST** — {gain_candidates} satır drift<0.70 var. "
                f"Önce 50 sample pixel-verify, accuracy >%90 ise Tier J apply.\n"
            )
        else:
            f.write(
                f"🟢 **PROCEED** — {gain_candidates:,} satır drift<0.70 var, kayda değer kazanım. "
                f"30 sample pixel-verify gate + Tier J apply (geometri-only, drift<0.85 + dry-run zorunlu).\n"
            )

        f.write("\n## Pixel-Verify Sample\n\n")
        f.write(
            f"**Random {args.sample_pixel} sample** drift<0.85 olan satırlardan "
            f"export edildi: `{TODAY}_tier_j_pixel_sample_{args.subject}.tsv`\n\n"
        )
        f.write("Pixel-verify protokolü:\n")
        f.write("1. Her sample için crop_url'i image olarak aç\n")
        f.write("2. qtext_preview ve ocr_preview yan yana karşılaştır\n")
        f.write("3. Image'a göre hangisi doğru? → ground truth işaretle\n")
        f.write("4. Eğer image_ocr 30/30 (>%90) DOĞRU ise: Tier J apply güvenli\n")
        f.write("5. Eğer karışıksa (image_ocr ~%50-70 doğru): manuel curator queue\n")

    print(f"[output] SUMMARY: {summary_path}", flush=True)

    # Pixel-verify sample export
    drift_rows = [r for r in rows if r["drift_sim"] < 0.85]
    if drift_rows:
        import random as _r

        rng = _r.Random(42)
        sample_n = min(args.sample_pixel, len(drift_rows))
        sample = rng.sample(drift_rows, sample_n)
        sample_path = PILOTS_DIR / f"{TODAY}_tier_j_pixel_sample_{args.subject}.tsv"
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write(
                "id\tdrift_sim\tdrift_class\tcorrect_answer\t"
                "qtext_full\tocr_full\timage_url\n"
            )
            for r in sample:
                qfull = (r["qtext"] or "").replace("\t", " ").replace("\n", " ")
                ofull = (r["ocr"] or "").replace("\t", " ").replace("\n", " ")
                f.write(
                    f"{r['id']}\t{r['drift_sim']:.3f}\t{r['drift_class']}\t"
                    f"{r['correct_answer'] or ''}\t"
                    f"{qfull}\t{ofull}\t{r['question_image_url'] or ''}\n"
                )
        print(f"[output] SAMPLE: {sample_path} ({sample_n} satır)", flush=True)
    else:
        print(
            "[note] No drift<0.85 rows — qtext ve image_ocr büyük çoğunlukla aynı.",
            flush=True,
        )

    # Console summary
    print(f"\n[summary] {args.subject} drift dağılımı (n={n:,}):")
    for bucket in ["high_agree", "moderate_drift", "substantive_drift", "severe_drift"]:
        count = buckets.get(bucket, 0)
        pct = (count / n * 100) if n else 0
        print(f"  {bucket:20s} {count:>5,} ({pct:>5.1f}%)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
