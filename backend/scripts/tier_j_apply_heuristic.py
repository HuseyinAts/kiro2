#!/usr/bin/env python3
"""
Tier J apply — Heuristic filter (Strategy A from 60-sample pixel-verify evidence).

PURPOSE:
  Pre-audit (v2 format-aware) showed ~530 GEOMETRI HIGH apply rows have real
  content drift between qtext (legacy) and image_ocr_text (Tier I new). Pixel-
  verify (Round 3+4 = n=60) showed 40% of drift cases are real qtext errors,
  60% are LaTeX-vs-Unicode format only.

  Blind apply NET NEGATIVE (LaTeX→Unicode = beta UI render quality loss).
  Smart apply needs to detect HIGH-CONFIDENCE qtext errors only.

HIGH-CONFIDENCE PATTERNS (Tier J apply):
  1. Broken LaTeX: `\\perp ot`, `^ ext{o}`, `\\widehat{}` empty
  2. qtext substantially shorter than image_ocr (length_ratio < 0.7) → truncated
  3. qtext contains "I"-like italic OCR remnants: `|XYI|`, `IXYI`

LOW-CONFIDENCE (skip — leave for Faz 6.1 judge):
  1. Subtle segment label differences (ABC vs ACB) — needs semantic understanding
  2. ∥/⊥/=/< swaps — needs image verify

USAGE:
  # Detect mode (default, READ-ONLY, no UPDATE)
  python backend/scripts/tier_j_apply_heuristic.py

  # Apply mode (DB UPDATE qtext = ocr WHERE detected)
  python backend/scripts/tier_j_apply_heuristic.py --apply

  # With sample pixel-verify export
  python backend/scripts/tier_j_apply_heuristic.py --sample-verify 30

OUTPUTS:
  - {date}_tier_j_apply_heuristic_DETECTED.tsv : detected rows TSV
  - {date}_tier_j_apply_heuristic_SUMMARY.md   : detection counts + reasoning
  - {date}_tier_j_apply_heuristic_VERIFY.tsv   : random N for pixel-verify (--sample-verify)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
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


# ============================================================================
# HEURISTIC DETECTORS
# ============================================================================


# Broken LaTeX patterns — qtext'te varsa Tier I image_ocr daha güvenilir
BROKEN_LATEX_PATTERNS = [
    (
        r"\^\s+ext\{o\}",
        "broken_text_o",
    ),  # ^ ext{o} → \text{o} parse fail (R3 sample 13)
    (r"\\perp\s+ot\b", "broken_perp_ot"),  # \perp ot → \perp split
    (r"\\widehat\{\s*\}", "empty_widehat"),  # \widehat{} empty
    (r"\\\\[a-zA-Z]+\b", "double_backslash_command"),  # \\command (escaped, render bug)
]


def has_unclosed_latex(text: str) -> list[str]:
    """Detect unclosed LaTeX delimiters via character counting (avoids regex EOS bugs)."""
    issues = []
    if text.count("$") % 2 == 1:
        issues.append("odd_dollar_count")
    o, c = text.count("{"), text.count("}")
    if abs(o - c) >= 2:  # tolerate 1 (Türkçe text içinde {} olabilir)
        issues.append(f"brace_imbalance_{o - c:+d}")
    return issues


# Italic-I OCR artifacts in qtext → Tier I OCR usually fixes these
ITALIC_I_PATTERNS = [
    (r"\|[A-Z]{1,3}I\|", "italic_i_segment"),  # |XYI| where I should be |
    (r"\bI[A-Z]{2,4}I\b", "italic_i_brackets"),  # IXYI → |XY|
    (r"\|[A-Z]\|I\|", "italic_i_double"),  # |X|I| → |XI|
]


def detect_broken_latex(text: str) -> list[str]:
    """Return list of broken LaTeX issues found in text."""
    issues = []
    for pattern, label in BROKEN_LATEX_PATTERNS:
        if re.search(pattern, text):
            issues.append(label)
    return issues


def detect_italic_i(text: str) -> list[str]:
    """Return list of italic-I OCR artifacts."""
    issues = []
    for pattern, label in ITALIC_I_PATTERNS:
        if re.search(pattern, text):
            issues.append(label)
    return issues


def length_ratio(qtext: str, ocr: str) -> float:
    """qtext length / ocr length. <0.7 → qtext truncated."""
    if not ocr:
        return 1.0
    return len(qtext) / len(ocr) if len(ocr) > 0 else 1.0


def classify_row(qtext: str, ocr: str) -> dict:
    """
    Classify whether row is high-confidence Tier J apply candidate.

    Returns dict with:
      - confidence: 'high' | 'medium' | 'skip'
      - reasons: list of detected issue labels
      - length_ratio: float
    """
    qtext = qtext or ""
    ocr = ocr or ""

    broken = detect_broken_latex(qtext)
    unclosed = has_unclosed_latex(qtext)
    italic = detect_italic_i(qtext)
    lr = length_ratio(qtext, ocr)

    reasons = []
    confidence = "skip"

    # HIGH confidence: broken LaTeX or unclosed delimiters
    if broken or unclosed:
        confidence = "high"
        reasons.extend(broken + unclosed)

    # HIGH confidence: italic-I segment artifacts
    if italic:
        confidence = "high"
        reasons.extend(italic)

    # MEDIUM confidence: significant length truncation
    if lr < 0.65 and len(ocr) > 100:  # ocr substantial AND qtext shorter
        if confidence != "high":
            confidence = "medium"
        reasons.append(f"truncation_lr={lr:.2f}")

    # SAFETY: if ocr is empty or very short, don't apply
    if len(ocr) < 30:
        confidence = "skip"
        reasons.append("ocr_too_short")

    # SAFETY: if qtext and ocr are essentially the same length and no broken patterns,
    # this is likely just format diff — skip
    if confidence == "skip" and 0.85 <= lr <= 1.15 and not (broken or italic):
        reasons.append("likely_format_only")

    return {
        "confidence": confidence,
        "reasons": reasons,
        "length_ratio": lr,
    }


# ============================================================================
# DB FETCH
# ============================================================================


def fetch_drift_candidates(engine, subject: str = "GEOMETRI") -> list[dict]:
    """Fetch all Tier I HIGH apply rows for subject."""
    from sqlalchemy import text

    sql = text(f"""
        SELECT id,
               subject_area,
               COALESCE(question_text, '') AS qtext,
               COALESCE(image_ocr_text, '') AS ocr,
               correct_answer,
               question_image_url
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


def apply_tier_j(
    engine, *, id_: str, new_qtext: str, reasons: list[str], dry_run: bool = True
):
    """UPDATE question_text + pipeline_metadata.tier_j_qtext audit trail."""
    if dry_run:
        return

    from sqlalchemy import text

    delta = json.dumps(
        {
            "tier_j_qtext": {
                "date": TODAY,
                "method": "heuristic_v1",
                "reasons": reasons,
                "from_field": "image_ocr_text",
            }
        },
        ensure_ascii=False,
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE question_bank
                SET question_text = :new_qtext,
                    pipeline_metadata = (
                        COALESCE(pipeline_metadata, '{}'::json)::jsonb
                        || CAST(:delta AS jsonb)
                    )::json,
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"new_qtext": new_qtext, "delta": delta, "id": id_},
        )


# ============================================================================
# MAIN
# ============================================================================


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", default="GEOMETRI")
    ap.add_argument(
        "--apply", action="store_true", help="Actually UPDATE DB (default detect-only)"
    )
    ap.add_argument(
        "--sample-verify",
        type=int,
        default=30,
        help="Random N detected sample TSV for pixel-verify",
    )
    ap.add_argument(
        "--high-only", action="store_true", help="Only HIGH confidence (skip MEDIUM)"
    )
    args = ap.parse_args()

    engine = get_engine()
    print(f"[fetch] Tier I HIGH apply rows, subject={args.subject}", flush=True)
    rows = fetch_drift_candidates(engine, args.subject)
    print(f"[fetch] {len(rows):,} rows", flush=True)

    print("[classify] Heuristic detection...", flush=True)
    detected = []
    for r in rows:
        result = classify_row(r["qtext"], r["ocr"])
        if result["confidence"] in ("high", "medium"):
            r["_classify"] = result
            detected.append(r)

    if args.high_only:
        detected = [r for r in detected if r["_classify"]["confidence"] == "high"]

    n = len(rows)
    n_high = sum(1 for r in detected if r["_classify"]["confidence"] == "high")
    n_med = sum(1 for r in detected if r["_classify"]["confidence"] == "medium")

    print(
        f"\n[detect] {len(detected):,} candidates ({n_high} HIGH + {n_med} MEDIUM)",
        flush=True,
    )
    print(f"  Total {args.subject} HIGH apply: {n:,}")
    print(f"  Detected: {len(detected):,} ({len(detected) / n * 100:.1f}%)", flush=True)

    # Reason histogram
    all_reasons = Counter()
    for r in detected:
        for reason in r["_classify"]["reasons"]:
            all_reasons[reason.split("_lr=")[0]] += 1

    print("\n[reasons]:")
    for reason, count in all_reasons.most_common():
        print(f"  {reason:30s} {count:>5,}")

    # Output DETECTED TSV
    out_path = PILOTS_DIR / f"{TODAY}_tier_j_apply_heuristic_DETECTED.tsv"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(
            "id\tconfidence\treasons\tlength_ratio\tcorrect_answer\t"
            "qtext_preview\tocr_preview\timage_url\n"
        )
        for r in detected:
            qprev = (r["qtext"][:120] or "").replace("\t", " ").replace("\n", " ")
            oprev = (r["ocr"][:120] or "").replace("\t", " ").replace("\n", " ")
            reasons = "|".join(r["_classify"]["reasons"])
            f.write(
                f"{r['id']}\t{r['_classify']['confidence']}\t{reasons}\t"
                f"{r['_classify']['length_ratio']:.3f}\t{r['correct_answer'] or ''}\t"
                f"{qprev}\t{oprev}\t{r['question_image_url'] or ''}\n"
            )
    print(f"\n[output] DETECTED: {out_path}", flush=True)

    # Sample for pixel-verify
    if args.sample_verify and detected:
        import random as _r

        rng = _r.Random(42)
        sample_n = min(args.sample_verify, len(detected))
        sample = rng.sample(detected, sample_n)
        sample_path = PILOTS_DIR / f"{TODAY}_tier_j_apply_heuristic_VERIFY.tsv"
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write(
                "id\tconfidence\treasons\tlength_ratio\tcorrect_answer\t"
                "qtext_full\tocr_full\timage_url\n"
            )
            for r in sample:
                qfull = (r["qtext"] or "").replace("\t", " ").replace("\n", " ")
                ofull = (r["ocr"] or "").replace("\t", " ").replace("\n", " ")
                reasons = "|".join(r["_classify"]["reasons"])
                f.write(
                    f"{r['id']}\t{r['_classify']['confidence']}\t{reasons}\t"
                    f"{r['_classify']['length_ratio']:.3f}\t{r['correct_answer'] or ''}\t"
                    f"{qfull}\t{ofull}\t{r['question_image_url'] or ''}\n"
                )
        print(f"[output] VERIFY: {sample_path} ({sample_n} satır)", flush=True)

    # Apply mode
    if args.apply:
        print(f"\n[apply] {len(detected)} satır UPDATE'leniyor...", flush=True)
        backup_path = PILOTS_DIR / f"{TODAY}_tier_j_apply_BACKUP.tsv"
        with open(backup_path, "w", encoding="utf-8") as bf:
            bf.write("id\tprev_qtext\n")
            applied = 0
            errors = 0
            for r in detected:
                try:
                    qprev_safe = (
                        (r["qtext"] or "").replace("\t", " ").replace("\n", " ")
                    )
                    bf.write(f"{r['id']}\t{qprev_safe}\n")
                    apply_tier_j(
                        engine,
                        id_=r["id"],
                        new_qtext=r["ocr"],
                        reasons=r["_classify"]["reasons"],
                        dry_run=False,
                    )
                    applied += 1
                except Exception as e:
                    errors += 1
                    print(f"[ERR {r['id'][:8]}] {str(e)[:80]}", flush=True)
        print(f"\n[applied] {applied} satır UPDATE'lendi, {errors} hata")
        print(f"[backup] {backup_path}")
    else:
        print("\n[detect-only] DB UPDATE YAPILMADI. Apply için: --apply flag")

    return 0


if __name__ == "__main__":
    sys.exit(main())
