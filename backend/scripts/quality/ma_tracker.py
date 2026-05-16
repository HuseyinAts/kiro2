#!/usr/bin/env python3
"""
Faz 2.4 — 30-gün moving average tracker + alarm (Session 161d/162).

Input: Faz 2.3 drift_dashboard --json-output (timeseries.json).
Logic: tarih-bazlı pass% serisi → 30-gün rolling average → alarm flag.

ALARM TRIGGERS:
  - MA(30g) < baseline_pass_pct - 5pp   → drift uyarısı
  - Tek hafta < baseline_pass_pct - 10pp → flash drop
  - Veri yetersiz (<2 hafta)            → "baseline not yet established"

USAGE:
  python -m backend.scripts.quality.ma_tracker timeseries.json
  python -m backend.scripts.quality.ma_tracker timeseries.json --baseline-pct 20.9
  python -m backend.scripts.quality.ma_tracker timeseries.json --output ma_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WINDOW_DAYS = 30
DROP_ALARM_PP = 5.0  # MA(30) < baseline - 5pp → drift alarm
FLASH_ALARM_PP = 10.0  # Single week < baseline - 10pp → flash drop


def load_timeseries(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"[error] timeseries.json bulunamadı: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records", [])
    if not records:
        sys.exit("[error] timeseries.json içinde 'records' boş")
    return records


def aggregate_by_date(records: list[dict]) -> dict[date, dict]:
    """Date → {scored, pass, fail, unclear} aggregate."""
    by_date: dict[date, dict] = defaultdict(
        lambda: {"scored": 0, "pass": 0, "fail": 0, "unclear": 0}
    )
    for r in records:
        d_str = r.get("date")
        if not d_str:
            continue
        try:
            d = date.fromisoformat(d_str)
        except ValueError:
            continue
        agg = by_date[d]
        agg["scored"] += r.get("scored", 0)
        v = r.get("verdicts", {})
        agg["pass"] += v.get("pass", 0)
        agg["fail"] += v.get("fail", 0)
        agg["unclear"] += v.get("unclear", 0)
    return dict(by_date)


def rolling_average(
    by_date: dict[date, dict], window_days: int
) -> list[tuple[date, float, int]]:
    """Her tarih için son N gün içindeki pass% MA."""
    if not by_date:
        return []
    dates = sorted(by_date.keys())
    result: list[tuple[date, float, int]] = []
    for current in dates:
        window_start = current - timedelta(days=window_days - 1)
        total_scored = 0
        total_pass = 0
        for d, agg in by_date.items():
            if window_start <= d <= current:
                total_scored += agg["scored"]
                total_pass += agg["pass"]
        if total_scored:
            pct = total_pass * 100 / total_scored
            result.append((current, pct, total_scored))
    return result


def build_report(
    records: list[dict],
    baseline_pct: float | None,
) -> tuple[str, dict]:
    """Markdown rapor + alarm state (commit/CI integration için)."""
    by_date = aggregate_by_date(records)
    dates_sorted = sorted(by_date.keys())

    state = {
        "generated_at": datetime.now().isoformat(),
        "n_dates": len(dates_sorted),
        "alarms": [],
    }

    lines: list[str] = []
    lines.append(
        f"# Quality Audit 30-Day MA Report — {datetime.now().date().isoformat()}"
    )
    lines.append("")
    lines.append(f"**Dates covered:** {len(dates_sorted)}")
    if dates_sorted:
        lines.append(f"**Date span:** {dates_sorted[0]} → {dates_sorted[-1]}")
    lines.append(f"**Window:** {WINDOW_DAYS} gün")
    if baseline_pct is not None:
        lines.append(f"**Baseline pass%:** {baseline_pct:.1f}")
        lines.append(
            f"**Alarm thresholds:** MA < {baseline_pct - DROP_ALARM_PP:.1f} "
            f"(drift), tek tarih < {baseline_pct - FLASH_ALARM_PP:.1f} (flash)"
        )
    lines.append("")

    # Veri yetersiz mi?
    if len(dates_sorted) < 2:
        lines.append("## ⚠️ Veri Yetersiz")
        lines.append("")
        lines.append(
            f"Sadece {len(dates_sorted)} tarihte data var. 30-gün MA için en az 2 "
            f"hafta gerek. Faz 2.6 (4 hafta baseline) tamamlandıktan sonra anlamlı."
        )
        state["alarms"].append("insufficient_data")
        return "\n".join(lines) + "\n", state

    # Per-date pass% tablo
    lines.append("## Tarih-Bazlı pass% Trend")
    lines.append("")
    lines.append("| Date | Scored | Pass | Pass% | Δ baseline |")
    lines.append("|---|---|---|---|---|")
    for d in dates_sorted:
        agg = by_date[d]
        n = agg["scored"]
        p = agg["pass"]
        pct = (p * 100 / n) if n else 0.0
        delta_str = "—"
        if baseline_pct is not None:
            delta = pct - baseline_pct
            arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
            delta_str = f"{arrow} %{abs(delta):.1f}"
            if -delta >= FLASH_ALARM_PP:
                state["alarms"].append(
                    {"type": "flash_drop", "date": str(d), "pass_pct": round(pct, 2)}
                )
                delta_str += " ⚠️"
        lines.append(f"| {d} | {n} | {p} | %{pct:.1f} | {delta_str} |")
    lines.append("")

    # MA serisi
    ma_series = rolling_average(by_date, WINDOW_DAYS)
    lines.append(f"## {WINDOW_DAYS}-Gün Rolling Average")
    lines.append("")
    lines.append("| Date | Window Pass% (MA) | Window Scored |")
    lines.append("|---|---|---|")
    for d, pct, n in ma_series:
        marker = ""
        if baseline_pct is not None and (baseline_pct - pct) >= DROP_ALARM_PP:
            state["alarms"].append(
                {"type": "ma_drift", "date": str(d), "ma_pct": round(pct, 2)}
            )
            marker = " ⚠️"
        lines.append(f"| {d} | %{pct:.1f}{marker} | {n} |")
    lines.append("")

    # Latest MA delta
    if baseline_pct is not None and ma_series:
        latest_d, latest_pct, _ = ma_series[-1]
        delta = latest_pct - baseline_pct
        sign = "+" if delta >= 0 else ""
        lines.append(f"## Latest Status ({latest_d})")
        lines.append("")
        lines.append(f"- **MA pass%:** %{latest_pct:.1f}")
        lines.append(f"- **vs baseline:** {sign}%{delta:.1f}pp")
        if -delta >= DROP_ALARM_PP:
            lines.append(
                f"- **🚨 DRIFT ALARM:** MA {DROP_ALARM_PP}pp altında baseline'ın"
            )
        else:
            lines.append("- **✅ Drift normal sınırda**")
        lines.append("")

    if state["alarms"]:
        lines.append("## 🚨 Aktif Alarmlar")
        lines.append("")
        for a in state["alarms"]:
            lines.append(f"- {a}")
        lines.append("")
    else:
        lines.append("## ✅ Alarm yok")
        lines.append("")

    return "\n".join(lines) + "\n", state


def main() -> int:
    ap = argparse.ArgumentParser(
        description="30-gün MA tracker + alarm (Plan v1 Faz 2.4)"
    )
    ap.add_argument("timeseries", type=Path, help="Faz 2.3 timeseries.json")
    ap.add_argument(
        "--baseline-pct",
        type=float,
        default=None,
        help="Baseline pass%% (drift karşılaştırması). Yoksa sadece raw trend.",
    )
    ap.add_argument("--output", type=Path, default=None)
    ap.add_argument("--state-output", type=Path, default=None, help="Alarm state JSON")
    args = ap.parse_args()

    records = load_timeseries(args.timeseries)
    md, state = build_report(records, args.baseline_pct)
    print(md)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(md, encoding="utf-8")
        print(f"[markdown] {args.output}")
    if args.state_output:
        args.state_output.parent.mkdir(parents=True, exist_ok=True)
        args.state_output.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[state] {args.state_output}")

    # Exit code 2 if alarm active (CI integration için)
    if any(
        isinstance(a, dict) and a.get("type") in {"ma_drift", "flash_drop"}
        for a in state["alarms"]
    ):
        print("\n[exit] Alarm active → exit code 2")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
