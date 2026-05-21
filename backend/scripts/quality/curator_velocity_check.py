#!/usr/bin/env python3
"""Curator velocity check — Faz 4.3.

Curator verdict velocity dağılımını çıkartır:
  - mean / median / p10 / p90 / stddev
  - outlier (Z > 2): muhtemel bot/hızlı tıklama veya stale tab
  - subject_area bazında breakdown
  - günlük throughput trendi

Data source: question_bank.pipeline_metadata.curator_verdict.velocity_seconds
(Faz 3.1'de eklendi, Curator UI POST /verdict her seferinde yazıyor).

Usage:
  python backend/scripts/quality/curator_velocity_check.py
  python backend/scripts/quality/curator_velocity_check.py --since 7  # last 7 days
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys

import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DSN = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")


def fetch_velocities(since_days: int = 30):
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          id::text,
          subject_area,
          quality_review_status,
          (pipeline_metadata::jsonb -> 'curator_verdict' ->> 'velocity_seconds')::float
            AS velocity_sec,
          (pipeline_metadata::jsonb -> 'curator_verdict' ->> 'reviewed_at')::timestamptz
            AS reviewed_at,
          pipeline_metadata::jsonb -> 'curator_verdict' ->> 'verdict' AS verdict
        FROM question_bank
        WHERE pipeline_metadata::jsonb ? 'curator_verdict'
          AND (pipeline_metadata::jsonb -> 'curator_verdict' ->> 'reviewed_at')::timestamptz
              > NOW() - (%s || ' days')::interval
        ORDER BY reviewed_at DESC
        """,
        (since_days,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def report(rows, since_days: int):
    if not rows:
        print(f"[velocity] No curator verdicts in last {since_days} days.")
        print("  (Curator UI henüz canlı kullanılmadı veya sample sayısı 0.)")
        return

    vels = [r[3] for r in rows if r[3] is not None]
    if not vels:
        print(f"[velocity] {len(rows)} verdict, but no velocity_seconds recorded.")
        return

    mean = statistics.mean(vels)
    median = statistics.median(vels)
    stdev = statistics.stdev(vels) if len(vels) > 1 else 0.0
    p10 = statistics.quantiles(vels, n=10)[0] if len(vels) >= 10 else min(vels)
    p90 = statistics.quantiles(vels, n=10)[8] if len(vels) >= 10 else max(vels)

    print(f"# Curator Velocity Check — last {since_days}d")
    print(f"  Total verdicts: {len(rows):,}")
    print(f"  With velocity:  {len(vels):,}")
    print()
    print("## Distribution")
    print(f"  mean:   {mean:6.1f}s")
    print(f"  median: {median:6.1f}s")
    print(f"  stdev:  {stdev:6.1f}s")
    print(f"  p10:    {p10:6.1f}s")
    print(f"  p90:    {p90:6.1f}s")
    print()

    # Outliers (Z > 2)
    if stdev > 0:
        outliers = [
            r for r in rows if r[3] is not None and abs(r[3] - mean) > 2 * stdev
        ]
        print(f"## Outliers (Z > 2): {len(outliers)}")
        for r in outliers[:10]:
            z = (r[3] - mean) / stdev
            print(
                f"  {r[0][:8]} {r[1]:<10} velocity={r[3]:6.1f}s Z={z:+.1f} verdict={r[5]}"
            )
        if len(outliers) > 10:
            print(f"  ... +{len(outliers) - 10} more")
        print()

    # Subject breakdown
    by_subject: dict[str, list[float]] = {}
    for r in rows:
        if r[3] is not None:
            by_subject.setdefault(r[1] or "UNKNOWN", []).append(r[3])
    print("## By subject")
    for subj, vs in sorted(by_subject.items(), key=lambda x: -len(x[1])):
        m = statistics.mean(vs)
        print(f"  {subj:<12} n={len(vs):>4}  mean={m:5.1f}s")
    print()

    # Daily throughput
    by_day: dict[str, int] = {}
    for r in rows:
        if r[4] is not None:
            day = r[4].strftime("%Y-%m-%d")
            by_day[day] = by_day.get(day, 0) + 1
    print("## Daily throughput")
    for day in sorted(by_day.keys(), reverse=True)[:14]:
        print(f"  {day}: {by_day[day]:>4} verdicts")
    print()

    # Quota signal: target 30-50/day (Faz 7.4)
    daily_avg = len(rows) / max(since_days, 1)
    target = 40
    delta = (daily_avg - target) / target * 100
    status = (
        "✅" if 30 <= daily_avg <= 50 else ("⚠️ LOW" if daily_avg < 30 else "🔥 HIGH")
    )
    print("## Quota signal (Faz 7.4 target: 30-50/day)")
    print(f"  Daily avg: {daily_avg:.1f}/day  ({delta:+.0f}% vs target)  {status}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=int, default=30, help="Days lookback (default 30)")
    args = ap.parse_args()
    rows = fetch_velocities(args.since)
    report(rows, args.since)


if __name__ == "__main__":
    main()
