#!/usr/bin/env python3
"""
Faz 2.3 — Drift dashboard (Session 161d/162).

Birden fazla doldurulmuş `*_SCORING.tsv` dosyasını alır, multi-audit / multi-hafta
karşılaştırma raporu (markdown + opsiyonel JSON) üretir.

Audit_id + date dosya isminden parse:
  `20260515_audit_C1_SCORING.tsv` → date=2026-05-15, audit_id=audit_C1
  `20260520_weekly_RAW_SCORING.tsv` → date=2026-05-20, audit_id=weekly

USAGE:
  # Mevcut C1/C2/C3:
  python -m backend.scripts.quality.drift_dashboard \
    backend/_pilots/20260515_audit_C1_SCORING.tsv \
    backend/_pilots/20260515_audit_C2_SCORING.tsv \
    backend/_pilots/20260515_audit_C3_SCORING.tsv \
    --output docs/quality_audits/20260516_baseline_dashboard.md

  # Glob ile tüm SCORING dosyaları:
  python -m backend.scripts.quality.drift_dashboard \
    --glob "backend/_pilots/*_SCORING.tsv" \
    --output docs/quality_audits/$(date +%Y%m%d)_dashboard.md

  # JSON output (Faz 2.4 30-gün MA için):
  python -m backend.scripts.quality.drift_dashboard \
    --glob "backend/_pilots/*_SCORING.tsv" \
    --json-output docs/quality_audits/timeseries.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime
from glob import glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCORING_COLS = ("verdict", "error_type")  # notes opsiyonel
FILENAME_PATTERN = re.compile(r"^(\d{8})_(.+?)_SCORING\.tsv$", re.IGNORECASE)


def parse_filename(path: Path) -> tuple[str | None, str | None]:
    """Dosya isminden date (ISO) + audit_id parse. None döner eşleşmezse."""
    m = FILENAME_PATTERN.match(path.name)
    if not m:
        return None, None
    raw_date, audit_id = m.group(1), m.group(2)
    try:
        d = datetime.strptime(raw_date, "%Y%m%d").date().isoformat()
    except ValueError:
        d = None
    return d, audit_id


def load_scoring(path: Path) -> dict:
    """SCORING.tsv → {date, audit_id, total, scored, verdicts, error_types}."""
    if not path.exists():
        sys.exit(f"[error] Bulunamadı: {path}")

    date_iso, audit_id = parse_filename(path)
    if date_iso is None or audit_id is None:
        # Fallback: dosya isim pattern uymuyor — file mtime kullan, audit_id=stem
        date_iso = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        audit_id = path.stem.replace("_SCORING", "")
        print(
            f"[warn] {path.name} pattern eşleşmedi, mtime fallback "
            f"date={date_iso} audit_id={audit_id}",
            flush=True,
        )

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        header = reader.fieldnames or []
        missing = [c for c in SCORING_COLS if c not in header]
        if missing:
            sys.exit(f"[error] {path.name}: eksik scoring kolonları {missing}")
        rows = list(reader)

    total = len(rows)
    verdicts: Counter[str] = Counter()
    error_types: Counter[str] = Counter()
    for r in rows:
        v = (r.get("verdict") or "").strip()
        e = (r.get("error_type") or "").strip()
        verdicts[v or "_empty"] += 1
        if v in {"fail", "unclear"}:
            error_types[e or "_empty"] += 1
    scored = total - verdicts.get("_empty", 0)
    return {
        "path": str(path),
        "date": date_iso,
        "audit_id": audit_id,
        "total": total,
        "scored": scored,
        "verdicts": dict(verdicts),
        "error_types": dict(error_types),
    }


def pct(n: int, denom: int) -> float:
    return (n * 100 / denom) if denom else 0.0


def build_dashboard(records: list[dict]) -> str:
    """Multi-record list → markdown dashboard."""
    # Time-ordered (date asc, audit_id asc)
    records_sorted = sorted(
        records, key=lambda r: (r["date"] or "9999-99-99", r["audit_id"])
    )

    lines: list[str] = []
    lines.append(f"# Quality Audit Dashboard — {datetime.now().date().isoformat()}")
    lines.append("")
    lines.append(f"**Sources:** {len(records)} SCORING TSV")
    dates_uniq = sorted({r["date"] for r in records if r["date"]})
    lines.append(
        f"**Date span:** {dates_uniq[0]} → {dates_uniq[-1]}" if dates_uniq else ""
    )
    lines.append("")

    # --- Multi-audit verdict table (per-row, time-sorted) ---
    lines.append("## Verdict Trend (time-ordered)")
    lines.append("")
    lines.append(
        "| Date | Audit | Total | Scored | pass | fail | unclear | empty | pass% | fail% |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in records_sorted:
        v = r["verdicts"]
        n_total = r["total"]
        n_scored = r["scored"]
        n_pass = v.get("pass", 0)
        n_fail = v.get("fail", 0)
        n_unclear = v.get("unclear", 0)
        n_empty = v.get("_empty", 0)
        lines.append(
            f"| {r['date'] or '—'} | `{r['audit_id']}` | {n_total} | {n_scored} | "
            f"{n_pass} | {n_fail} | {n_unclear} | {n_empty} | "
            f"%{pct(n_pass, n_scored):.1f} | %{pct(n_fail, n_scored):.1f} |"
        )
    lines.append("")

    # --- Error type comparison ---
    all_error_types: set[str] = set()
    for r in records_sorted:
        all_error_types.update(r["error_types"].keys())
    all_error_types.discard("_empty")

    if all_error_types:
        lines.append("## Error Type Cross-Comparison")
        lines.append("")
        cols = ["Audit"] + sorted(all_error_types)
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "---|" * len(cols))
        for r in records_sorted:
            row_cells = [f"{r['date'] or '—'} `{r['audit_id']}`"]
            for et in sorted(all_error_types):
                n = r["error_types"].get(et, 0)
                row_cells.append(str(n) if n else "—")
            lines.append("| " + " | ".join(row_cells) + " |")
        lines.append("")

    # --- Aggregate (across all records) ---
    agg_v: Counter[str] = Counter()
    agg_e: Counter[str] = Counter()
    total_agg = 0
    scored_agg = 0
    for r in records_sorted:
        for k, n in r["verdicts"].items():
            agg_v[k] += n
        for k, n in r["error_types"].items():
            agg_e[k] += n
        total_agg += r["total"]
        scored_agg += r["scored"]

    lines.append("## Aggregate Across All Records")
    lines.append("")
    lines.append(
        f"**Total scored:** {scored_agg:,} / {total_agg:,} (%{pct(scored_agg, total_agg):.1f})"
    )
    lines.append("")
    lines.append("| verdict | count | %scored |")
    lines.append("|---|---|---|")
    for v in ("pass", "fail", "unclear"):
        n = agg_v.get(v, 0)
        lines.append(f"| `{v}` | {n:,} | %{pct(n, scored_agg):.1f} |")
    lines.append("")
    if agg_e:
        lines.append("| error_type | count |")
        lines.append("|---|---|")
        for et, n in agg_e.most_common():
            if et == "_empty":
                continue
            lines.append(f"| `{et}` | {n:,} |")
        lines.append("")

    # --- Drift signals (rough heuristic) ---
    lines.append("## Drift Signals")
    lines.append("")
    if len(dates_uniq) < 2:
        lines.append(
            "Tek tarih var, time-series drift hesaplanamaz. Faz 2.6 (4 hafta baseline) sonrası anlamlı."
        )
    else:
        # Tarih bazlı pass% serisi
        date_pass: dict[str, tuple[int, int]] = {}
        for r in records_sorted:
            d = r["date"] or "—"
            n_pass = r["verdicts"].get("pass", 0)
            n_scored = r["scored"]
            cur = date_pass.get(d, (0, 0))
            date_pass[d] = (cur[0] + n_pass, cur[1] + n_scored)
        series = [(d, pct(p, s)) for d, (p, s) in sorted(date_pass.items()) if s > 0]
        if len(series) >= 2:
            first_pct = series[0][1]
            last_pct = series[-1][1]
            delta = last_pct - first_pct
            arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
            lines.append(
                f"- pass% {series[0][0]}: %{first_pct:.1f} → {series[-1][0]}: %{last_pct:.1f} ({arrow} %{abs(delta):.1f})"
            )
            if delta < -5:
                lines.append("  - ⚠️ pass% 5+ puan düştü, kalite drift incelenmeli")
        lines.append("")

    return "\n".join(lines) + "\n"


def build_json(records: list[dict]) -> str:
    """Machine-readable output (Faz 2.4 30-gün MA için)."""
    records_sorted = sorted(records, key=lambda r: (r["date"] or "9999", r["audit_id"]))
    payload = {
        "generated_at": datetime.now().isoformat(),
        "records": records_sorted,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Multi SCORING TSV → drift dashboard (Plan v1 Faz 2.3)"
    )
    ap.add_argument(
        "scoring_files",
        nargs="*",
        type=Path,
        help="SCORING.tsv dosyaları (positional)",
    )
    ap.add_argument(
        "--glob",
        type=str,
        default=None,
        help="Glob pattern (positional args yerine, örn: 'backend/_pilots/*_SCORING.tsv')",
    )
    ap.add_argument("--output", type=Path, default=None, help="Markdown çıktı dosyası")
    ap.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="JSON çıktı (Faz 2.4 30-gün MA tracker için)",
    )
    args = ap.parse_args()

    paths: list[Path] = list(args.scoring_files)
    if args.glob:
        paths.extend(Path(p) for p in glob(args.glob))
    if not paths:
        sys.exit("[error] Pozisyonel argüman veya --glob ile en az 1 SCORING.tsv ver")

    # De-dup
    paths = sorted({p.resolve() for p in paths})

    records = []
    for p in paths:
        try:
            rec = load_scoring(p)
            records.append(rec)
            print(
                f"[loaded] {p.name} date={rec['date']} audit={rec['audit_id']} "
                f"total={rec['total']} scored={rec['scored']}",
                flush=True,
            )
        except SystemExit as e:
            print(f"[skip] {p.name}: {e}", flush=True)

    if not records:
        sys.exit("[error] Hiçbir SCORING dosyası okunamadı")

    md = build_dashboard(records)
    print("\n" + md)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(md, encoding="utf-8")
        print(f"[markdown] {args.output}")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(build_json(records) + "\n", encoding="utf-8")
        print(f"[json] {args.json_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
