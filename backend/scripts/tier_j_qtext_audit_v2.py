#!/usr/bin/env python3
"""
Tier J pre-audit v2 — FORMAT-AWARE drift detection (READ-ONLY).

PROBLEM with v1 (Round 3 pixel-verify n=30 finding):
  v1 substring_overlap LaTeX↔Unicode farkını "drift" olarak gösteriyor.
  30 sample'ın %53'ü pure formatting drift (gerçek content aynı).
  v1 1,254 satır drift>0.30 dedi → gerçek content drift sadece ~%40 (~501).

v2 SOLUTION:
  Comprehensive LaTeX → plain text normalization, sonra similarity hesabı.
  - $...$ delimiters strip
  - \\perp → ⊥, \\parallel → ∥, \\widehat{X} → X, \\sqrt{X} → √X
  - \frac{a}{b} → a/b, \\cdot → ·, ^\\circ → °, \text{X} → X
  - Broken patterns (\\perp ot, ^ ext{o}) handle
  - Italic-I segment etiketi (|AEI| → |AE|) tolere

OUTPUT:
  - {date}_tier_j_audit_v2_GEOMETRI_RAW.tsv  : v2 drift TSV
  - {date}_tier_j_audit_v2_GEOMETRI_SUMMARY.md : v1 vs v2 karşılaştırma + öneri
  - {date}_tier_j_pixel_sample_v2_GEOMETRI.tsv : v2 true drift'ten 30 random

USAGE:
  python backend/scripts/tier_j_qtext_audit_v2.py
"""

from __future__ import annotations

import argparse
import os
import re
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


# ============================================================================
# v2 LATEX NORMALIZATION — comprehensive
# ============================================================================


# Order matters — apply most specific patterns first
LATEX_REPLACEMENTS = [
    # Math delimiters strip (must come first)
    (r"\\\(", " "),
    (r"\\\)", " "),
    (r"\\\[", " "),
    (r"\\\]", " "),
    # Common commands → Unicode equivalents
    (r"\\perp\b", " ⊥ "),
    (r"\\parallel\b", " ∥ "),
    (r"\\cdot\b", "·"),
    (r"\\times\b", "×"),
    (r"\\div\b", "÷"),
    (r"\\pm\b", "±"),
    (r"\\leq\b", "≤"),
    (r"\\geq\b", "≥"),
    (r"\\neq\b", "≠"),
    (r"\\cap\b", "∩"),
    (r"\\cup\b", "∪"),
    (r"\\in\b", "∈"),
    (r"\\notin\b", "∉"),
    (r"\\subset\b", "⊂"),
    (r"\\rightarrow\b", "→"),
    (r"\\Rightarrow\b", "⇒"),
    (r"\\leftrightarrow\b", "↔"),
    (r"\\rightleftharpoons\b", "⇌"),
    (r"\\alpha\b", "α"),
    (r"\\beta\b", "β"),
    (r"\\gamma\b", "γ"),
    (r"\\delta\b", "δ"),
    (r"\\theta\b", "θ"),
    (r"\\pi\b", "π"),
    (r"\\circ\b", "°"),
    (r"\^\\circ\b", "°"),
    (r"\^\{?\\circ\}?", "°"),
    # Broken LaTeX patterns from real qtext data
    (r"\^\s*ext\{o\}", "°"),  # broken \text{o} parse
    (r"\\perp\s+ot\b", "⊥"),  # broken \perp split
    (r"\bAB\s+ot\b", "AB ⊥"),  # general "X ot" perpendicular fallback
    # Function-like commands — strip command, keep arg
    (r"\\widehat\{([^}]*)\}", r"\1"),
    (r"\\hat\{([^}]*)\}", r"\1"),
    (r"\\overline\{([^}]*)\}", r"\1"),
    (r"\\text\{([^}]*)\}", r"\1"),
    (r"\\textbf\{([^}]*)\}", r"\1"),
    (r"\\textit\{([^}]*)\}", r"\1"),
    (r"\\mathrm\{([^}]*)\}", r"\1"),
    (r"\\mathbf\{([^}]*)\}", r"\1"),
    (r"\\mathit\{([^}]*)\}", r"\1"),
    # \sqrt — keep arg with √ prefix
    (r"\\sqrt\{([^}]*)\}", r"√\1"),
    (r"\\sqrt\s*(\d+)", r"√\1"),
    # \frac{a}{b} → a/b
    (r"\\frac\{([^}]*)\}\{([^}]*)\}", r"\1/\2"),
    # Strip remaining LaTeX commands like \alpha, \beta etc (keep arg if any)
    (r"\\([a-zA-Z]+)\{([^}]*)\}", r"\2"),
    (r"\\[a-zA-Z]+\b", " "),
    # Strip $ delimiters
    (r"\$+", " "),
    # Strip remaining { }
    (r"[{}]", " "),
    # Italic-I segment etiketi — |X| with internal I confused
    # (e.g. |AEI| → |AE|, |EFI| → |EF|)
    (r"\|([A-Z]+)I\|", r"|\1|"),
    (r"I([A-Z]+)I", r"|\1|"),  # IAEI → |AE|
]


def normalize_v2(text: str) -> str:
    """Comprehensive LaTeX → Unicode + Türkçe-aware lowercase."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    for pattern, replacement in LATEX_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    # Türkçe-aware lowercase
    text = text.replace("İ", "i").replace("I", "ı")
    text = text.lower()
    # Collapse whitespace + strip punctuation around tokens
    text = re.sub(r"[,\.;:!\?]+", " ", text)
    return " ".join(text.split())


def substring_overlap_v2(a: str, b: str, min_word_len: int = 3) -> float:
    """Word-level Jaccard on normalized text (lower min_word_len → catches short symbols)."""
    a_norm = normalize_v2(a)
    b_norm = normalize_v2(b)
    a_words = {w for w in a_norm.split() if len(w) >= min_word_len}
    b_words = {w for w in b_norm.split() if len(w) >= min_word_len}
    if not a_words or not b_words:
        return 0.0
    return len(a_words & b_words) / len(a_words | b_words) if a_words | b_words else 0.0


def bucket_drift(sim: float) -> str:
    if sim >= 0.90:
        return "v2_high_agree"
    if sim >= 0.70:
        return "v2_moderate"
    if sim >= 0.50:
        return "v2_substantive"
    return "v2_severe"


# ============================================================================
# DB FETCH (same as v1)
# ============================================================================


def fetch_audit_data(engine, subject: str) -> list[dict]:
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


# ============================================================================
# v1 vs v2 COMPARISON
# ============================================================================


def load_v1_drift_map() -> dict[str, float]:
    """Load v1 drift TSV for delta comparison."""
    v1_path = PILOTS_DIR / "20260515_tier_j_audit_GEOMETRI_RAW.tsv"
    if not v1_path.exists():
        return {}
    import csv

    out = {}
    with open(v1_path, encoding="utf-8") as f:
        rdr = csv.DictReader(f, delimiter="\t")
        for row in rdr:
            out[row["id"]] = float(row["drift_sim"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", default="GEOMETRI")
    ap.add_argument("--sample-pixel", type=int, default=30)
    args = ap.parse_args()

    engine = get_engine()
    print(f"[fetch] Tier I HIGH apply rows, subject={args.subject}", flush=True)
    rows = fetch_audit_data(engine, args.subject)
    print(f"[fetch] {len(rows):,} rows", flush=True)

    if not rows:
        print(f"[done] No rows for {args.subject}")
        return 0

    v1_drift = load_v1_drift_map()
    print(
        f"[v1] {len(v1_drift):,} v1 drift values loaded for delta comparison",
        flush=True,
    )

    print("[compute] v2 format-aware similarity...", flush=True)
    for r in rows:
        r["v2_sim"] = substring_overlap_v2(r["qtext"], r["ocr"])
        r["v2_class"] = bucket_drift(r["v2_sim"])
        r["v1_sim"] = v1_drift.get(r["id"], -1)
        r["delta"] = r["v2_sim"] - r["v1_sim"] if r["v1_sim"] >= 0 else 0

    n = len(rows)
    v2_buckets = Counter(r["v2_class"] for r in rows)

    # v1 buckets recomputed for delta
    def v1_bucket(s):
        if s >= 0.90:
            return "high_agree"
        if s >= 0.70:
            return "moderate_drift"
        if s >= 0.50:
            return "substantive_drift"
        return "severe_drift"

    v1_buckets = Counter(v1_bucket(r["v1_sim"]) for r in rows if r["v1_sim"] >= 0)

    # Bucket transition matrix (v1 → v2)
    transitions: Counter = Counter()
    for r in rows:
        if r["v1_sim"] < 0:
            continue
        v1_b = v1_bucket(r["v1_sim"])
        v2_b = r["v2_class"]
        transitions[(v1_b, v2_b)] += 1

    # Output RAW
    raw_path = PILOTS_DIR / f"{TODAY}_tier_j_audit_v2_{args.subject}_RAW.tsv"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(
            "id\tv1_sim\tv2_sim\tdelta\tv2_class\tcorrect_answer\t"
            "qtext_preview\tocr_preview\timage_url\n"
        )
        for r in sorted(rows, key=lambda x: x["v2_sim"]):
            qprev = (r["qtext"][:120] or "").replace("\t", " ").replace("\n", " ")
            oprev = (r["ocr"][:120] or "").replace("\t", " ").replace("\n", " ")
            f.write(
                f"{r['id']}\t{r['v1_sim']:.3f}\t{r['v2_sim']:.3f}\t{r['delta']:+.3f}\t"
                f"{r['v2_class']}\t{r['correct_answer'] or ''}\t"
                f"{qprev}\t{oprev}\t{r['question_image_url'] or ''}\n"
            )
    print(f"[output] RAW: {raw_path}", flush=True)

    # Output SUMMARY md
    summary_path = PILOTS_DIR / f"{TODAY}_tier_j_audit_v2_{args.subject}_SUMMARY.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Tier J Pre-Audit v2 — Format-Aware ({args.subject}, n={n:,})\n\n")
        f.write(f"**Tarih:** {TODAY}\n")
        f.write(
            "**v1 referans:** `_pilots/20260515_tier_j_audit_GEOMETRI_RAW.tsv` "
            "(substring_overlap, LaTeX-aware DEĞİL)\n"
        )
        f.write(
            "**v2 yeni:** Format-aware (LaTeX → Unicode normalize, sonra similarity)\n\n"
        )

        f.write("## v1 vs v2 Drift Dağılımı\n\n")
        f.write("| Bucket | Range | v1 n | v1 % | v2 n | v2 % | Delta |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|\n")
        for v1key, v2key, label, rng in [
            ("high_agree", "v2_high_agree", "high_agree", ">=0.90"),
            ("moderate_drift", "v2_moderate", "moderate", "0.70-0.90"),
            ("substantive_drift", "v2_substantive", "substantive", "0.50-0.70"),
            ("severe_drift", "v2_severe", "severe", "<0.50"),
        ]:
            v1_n = v1_buckets.get(v1key, 0)
            v2_n = v2_buckets.get(v2key, 0)
            v1_pct = v1_n / n * 100 if n else 0
            v2_pct = v2_n / n * 100 if n else 0
            delta = v2_n - v1_n
            sign = "+" if delta > 0 else ""
            f.write(
                f"| {label} | {rng} | {v1_n:,} | {v1_pct:.1f} | "
                f"{v2_n:,} | {v2_pct:.1f} | {sign}{delta:+,} |\n"
            )

        f.write("\n## v1 → v2 Transition Matrix\n\n")
        f.write(
            "Önemli: v1'de drift gösteren satırların kaçı v2 ile high_agree'ye yükseldi?\n\n"
        )
        f.write("| v1 bucket | v2 bucket | n |\n")
        f.write("|---|---|---:|\n")
        for (v1_b, v2_b), count in sorted(transitions.items(), key=lambda x: -x[1]):
            f.write(f"| {v1_b} | {v2_b} | {count:,} |\n")

        # Key insight: v1 drift>0.30 vs v2 still drift>0.30
        v1_drift_n = sum(
            v1_buckets.get(b, 0)
            for b in ["substantive_drift", "severe_drift", "moderate_drift"]
        )
        v2_drift_n = sum(
            v2_buckets.get(b, 0) for b in ["v2_substantive", "v2_severe", "v2_moderate"]
        )

        f.write("\n## Format-Bias Düzeltmesi\n\n")
        f.write(
            f"- **v1 drift>0.10 ('not high_agree')**: {v1_drift_n:,} satır ({v1_drift_n / n * 100:.1f}%)\n"
        )
        f.write(
            f"- **v2 drift>0.10 ('not high_agree')**: {v2_drift_n:,} satır ({v2_drift_n / n * 100:.1f}%)\n"
        )
        f.write(
            f"- **Format-bias false positive**: {v1_drift_n - v2_drift_n:,} satır artık no-drift\n\n"
        )

        # Tier J recommendation v2
        v2_substantive = v2_buckets.get("v2_substantive", 0) + v2_buckets.get(
            "v2_severe", 0
        )
        f.write("## Tier J Apply Önerisi (v2)\n\n")
        if v2_substantive < 50:
            f.write(
                f"⏸️ **DEFER** — v2 sadece {v2_substantive} satır gerçek substantive content drift. "
                f"Tier J apply effort/payoff zayıf. Judge pipeline (Faz 5+6)'a bırak.\n"
            )
        elif v2_substantive < 200:
            f.write(
                f"🟡 **HEURISTIC** — v2 {v2_substantive} satır gerçek content drift. "
                f"Strateji A (broken LaTeX pattern filter) + 30-sample pixel-verify gate.\n"
            )
        else:
            f.write(
                f"🟢 **JUDGE-FIRST** — v2 {v2_substantive:,} satır gerçek content drift, "
                f"manuel/heuristic için fazla. Strateji C (judge pipeline ~$25 cost) önerilen.\n"
            )

        f.write("\n## Pixel-Verify v2 Sample\n\n")
        f.write(
            f"Random {args.sample_pixel} sample v2 drift<0.85'ten export edildi: "
            f"`{TODAY}_tier_j_pixel_sample_v2_{args.subject}.tsv`\n\n"
        )
        f.write(
            "**Bu sample önceki Round 3 (n=30) sample'ından FARKLI** — v2 normalization "
            "format-bias'ı düzelttiği için yeni gerçek content drift satırlarını öne çıkarır.\n"
        )

    print(f"[output] SUMMARY: {summary_path}", flush=True)

    # Pixel-verify v2 sample
    drift_v2 = [r for r in rows if r["v2_sim"] < 0.85]
    if drift_v2:
        import random as _r

        rng = _r.Random(42)
        sample_n = min(args.sample_pixel, len(drift_v2))
        sample = rng.sample(drift_v2, sample_n)
        sample_path = PILOTS_DIR / f"{TODAY}_tier_j_pixel_sample_v2_{args.subject}.tsv"
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write(
                "id\tv1_sim\tv2_sim\tdelta\tv2_class\tcorrect_answer\t"
                "qtext_full\tocr_full\timage_url\n"
            )
            for r in sample:
                qfull = (r["qtext"] or "").replace("\t", " ").replace("\n", " ")
                ofull = (r["ocr"] or "").replace("\t", " ").replace("\n", " ")
                f.write(
                    f"{r['id']}\t{r['v1_sim']:.3f}\t{r['v2_sim']:.3f}\t"
                    f"{r['delta']:+.3f}\t{r['v2_class']}\t{r['correct_answer'] or ''}\t"
                    f"{qfull}\t{ofull}\t{r['question_image_url'] or ''}\n"
                )
        print(f"[output] SAMPLE v2: {sample_path} ({sample_n} satır)", flush=True)

    # Console summary
    print(f"\n[summary v2] {args.subject} drift dağılımı (n={n:,}):")
    print("  v1 vs v2 karşılaştırma:")
    for v1key, v2key, label in [
        ("high_agree", "v2_high_agree", "high_agree"),
        ("moderate_drift", "v2_moderate", "moderate"),
        ("substantive_drift", "v2_substantive", "substantive"),
        ("severe_drift", "v2_severe", "severe"),
    ]:
        v1_n = v1_buckets.get(v1key, 0)
        v2_n = v2_buckets.get(v2key, 0)
        delta = v2_n - v1_n
        sign = "+" if delta > 0 else ""
        print(f"  {label:14s}  v1={v1_n:>5,} → v2={v2_n:>5,} ({sign}{delta:+,})")

    print(
        f"\n  v1 'real drift' (>0.10): {sum(v1_buckets.get(b, 0) for b in ['substantive_drift', 'severe_drift', 'moderate_drift']):,}"
    )
    print(
        f"  v2 'real drift' (>0.10): {sum(v2_buckets.get(b, 0) for b in ['v2_substantive', 'v2_severe', 'v2_moderate']):,}"
    )
    print(f"  Tier J substantive (drift<0.70 v2): {v2_substantive:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
