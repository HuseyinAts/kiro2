#!/usr/bin/env python3
"""
Faz 2.2 — Hüseyin scoring template + summary (Session 161d/162).

Mevcut Faz 2.1 audit harness'in (RAW.tsv) çıktısını alır, manuel scoring için
hazırlar (verdict/error_type/notes kolonları append) veya doldurulmuş
SCORING.tsv'den özet üretir.

Generic — herhangi bir RAW TSV (C1/C2/C3/weekly/curator) kabul eder; tüm orijinal
kolonları korur + 3 ek kolon append eder.

USAGE:
  # RAW → SCORING (3 boş kolon append):
  python -m backend.scripts.quality.scoring_template --prepare RAW.tsv
  python -m backend.scripts.quality.scoring_template --prepare RAW.tsv --output OUT.tsv

  # SCORING → summary (verdict + error_type dağılımı, optional strata breakdown):
  python -m backend.scripts.quality.scoring_template --summarize SCORING.tsv
  python -m backend.scripts.quality.scoring_template --summarize SCORING.tsv --strata-col subject_area
  python -m backend.scripts.quality.scoring_template --summarize SCORING.tsv --output RESULT.md
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCORING_COLS = ("verdict", "error_type", "notes")
VALID_VERDICTS = frozenset({"", "pass", "fail", "unclear"})
VALID_ERROR_TYPES = frozenset(
    {
        "",
        "missing_diagram",
        "ocr",
        "wrong_answer",
        "incomplete",
        "wrong_topic",
        "duplicate_option",
        "garbage_text",
        "other",
    }
)


def prepare(raw_path: Path, output: Path | None) -> Path:
    """RAW.tsv → SCORING.tsv (verdict/error_type/notes boş kolonlar append)."""
    if not raw_path.exists():
        sys.exit(f"[error] RAW TSV bulunamadı: {raw_path}")

    out_path = output or raw_path.with_name(raw_path.stem + "_SCORING.tsv")

    with raw_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        rows = list(reader)
    if not rows:
        sys.exit("[error] RAW TSV boş")
    header = rows[0]

    if any(c in header for c in SCORING_COLS):
        sys.exit(
            f"[error] RAW TSV zaten scoring kolonu içeriyor: "
            f"{[c for c in SCORING_COLS if c in header]}. Idempotent çağrı için "
            f"--summarize kullan."
        )

    new_header = header + list(SCORING_COLS)
    body = [row + ["", "", ""] for row in rows[1:]]

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(new_header)
        writer.writerows(body)

    print(
        f"[prepare] {len(body):,} satır → {out_path}\n"
        f"          {len(header)} orig col + {len(SCORING_COLS)} scoring col"
    )
    return out_path


def summarize(scoring_path: Path, strata_col: str | None, output: Path | None) -> str:
    """SCORING.tsv → verdict + error_type dağılımı (markdown)."""
    if not scoring_path.exists():
        sys.exit(f"[error] SCORING TSV bulunamadı: {scoring_path}")

    with scoring_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
    if not rows:
        sys.exit("[error] SCORING TSV boş")

    header = list(rows[0].keys())
    missing = [c for c in SCORING_COLS if c not in header]
    if missing:
        sys.exit(f"[error] Eksik scoring kolonları: {missing}")
    if strata_col and strata_col not in header:
        sys.exit(f"[error] Strata kolonu '{strata_col}' TSV'de yok. Kolonlar: {header}")

    # Validation + counters
    verdict_counter: Counter[str] = Counter()
    error_counter: Counter[str] = Counter()
    invalid_verdicts: list[tuple[int, str]] = []
    invalid_errors: list[tuple[int, str]] = []
    inconsistent: list[
        tuple[int, str]
    ] = []  # pass + error_type or fail/unclear + empty
    strata_dist: dict[str, Counter[str]] = defaultdict(Counter)

    for i, r in enumerate(rows, start=2):  # +2: 1-indexed + header
        v = (r.get("verdict") or "").strip()
        e = (r.get("error_type") or "").strip()
        if v not in VALID_VERDICTS:
            invalid_verdicts.append((i, v))
        if e not in VALID_ERROR_TYPES:
            invalid_errors.append((i, e))
        verdict_counter[v or "_empty"] += 1
        if v in {"fail", "unclear"}:
            error_counter[e or "_empty"] += 1
        if v == "pass" and e:
            inconsistent.append((i, f"verdict=pass but error_type={e!r}"))
        if v in {"fail", "unclear"} and not e:
            inconsistent.append((i, f"verdict={v} but error_type empty"))
        if strata_col:
            strata_dist[r.get(strata_col, "_missing")][v or "_empty"] += 1

    total = len(rows)
    scored = total - verdict_counter.get("_empty", 0)
    scored_pct = (scored * 100 / total) if total else 0.0

    lines: list[str] = []
    lines.append(f"# Scoring Summary — {scoring_path.name}")
    lines.append("")
    lines.append(f"**Total rows:** {total:,}")
    lines.append(f"**Scored:** {scored:,} (%{scored_pct:.1f})")
    lines.append("")
    lines.append("## Verdict Distribution")
    lines.append("")
    lines.append("| Verdict | Count | % of total | % of scored |")
    lines.append("|---|---|---|---|")
    for v in ("pass", "fail", "unclear", "_empty"):
        n = verdict_counter.get(v, 0)
        pct_total = (n * 100 / total) if total else 0.0
        pct_scored = (n * 100 / scored) if scored and v != "_empty" else 0.0
        scored_str = f"%{pct_scored:.1f}" if v != "_empty" else "—"
        lines.append(f"| `{v}` | {n:,} | %{pct_total:.1f} | {scored_str} |")
    lines.append("")

    if error_counter:
        lines.append("## Error Type Distribution (verdict ∈ {fail, unclear})")
        lines.append("")
        lines.append("| error_type | Count | % |")
        lines.append("|---|---|---|")
        n_total_err = sum(error_counter.values())
        for et, n in error_counter.most_common():
            pct = (n * 100 / n_total_err) if n_total_err else 0.0
            lines.append(f"| `{et}` | {n:,} | %{pct:.1f} |")
        lines.append("")

    if strata_col:
        lines.append(f"## Strata Breakdown ({strata_col})")
        lines.append("")
        lines.append(f"| {strata_col} | total | pass | fail | unclear | empty |")
        lines.append("|---|---|---|---|---|---|")
        for stratum, ctr in sorted(strata_dist.items()):
            n_total = sum(ctr.values())
            lines.append(
                f"| {stratum} | {n_total:,} | {ctr.get('pass', 0)} | "
                f"{ctr.get('fail', 0)} | {ctr.get('unclear', 0)} | "
                f"{ctr.get('_empty', 0)} |"
            )
        lines.append("")

    if invalid_verdicts or invalid_errors or inconsistent:
        lines.append("## ⚠️  Validation Issues")
        lines.append("")
        if invalid_verdicts:
            lines.append(
                f"- **Invalid verdict** ({len(invalid_verdicts)}): expected one of "
                f"{sorted(VALID_VERDICTS - {''})} or empty"
            )
            for ln, v in invalid_verdicts[:5]:
                lines.append(f"  - line {ln}: `{v}`")
            if len(invalid_verdicts) > 5:
                lines.append(f"  - ... +{len(invalid_verdicts) - 5} more")
        if invalid_errors:
            lines.append(
                f"- **Invalid error_type** ({len(invalid_errors)}): expected one of "
                f"{sorted(VALID_ERROR_TYPES - {''})} or empty"
            )
            for ln, e in invalid_errors[:5]:
                lines.append(f"  - line {ln}: `{e}`")
            if len(invalid_errors) > 5:
                lines.append(f"  - ... +{len(invalid_errors) - 5} more")
        if inconsistent:
            lines.append(
                f"- **Inconsistent verdict/error_type** ({len(inconsistent)}):"
            )
            for ln, msg in inconsistent[:5]:
                lines.append(f"  - line {ln}: {msg}")
            if len(inconsistent) > 5:
                lines.append(f"  - ... +{len(inconsistent) - 5} more")
        lines.append("")
    else:
        lines.append("## ✅ Validation: clean (no invalid or inconsistent rows)")
        lines.append("")

    md = "\n".join(lines)
    print(md)
    if output:
        output.write_text(md + "\n", encoding="utf-8")
        print(f"\n[written] {output}")
    return md


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Audit RAW TSV scoring template + summary (Plan v1 Faz 2.2)"
    )
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", type=Path, metavar="RAW.tsv")
    mode.add_argument("--summarize", type=Path, metavar="SCORING.tsv")
    ap.add_argument("--output", type=Path, default=None)
    ap.add_argument(
        "--strata-col",
        type=str,
        default=None,
        help="--summarize için: bu kolona göre verdict dağılımı kır (örn. subject_area)",
    )
    args = ap.parse_args()

    if args.prepare:
        prepare(args.prepare, args.output)
    else:
        summarize(args.summarize, args.strata_col, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
