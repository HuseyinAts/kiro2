"""Faz D pilot splitter: master.csv -> answer-free batches for gemma3 blind-solve.
Fresh pool (no prior qwen3 signal). Pilot measures gemma3-agree quality on the
thin verbal subjects to decide D1 (gemma3-only + Opus) vs D2 (qwen3+gemma3)."""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_faz_d")
MASTER = BASE / "master.csv"
OUT = BASE / "batches"
OUT.mkdir(exist_ok=True)
BATCH_SIZE = 20

rows = []
with MASTER.open(encoding="utf-8", newline="") as f:
    for record in csv.reader(f):
        if not record:
            continue
        rows.append(json.loads(record[0]))

batches = [rows[i : i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
for idx, batch in enumerate(batches):
    stripped = [
        {k: r[k] for k in ("id", "subject", "exam", "q", "a", "b", "c", "d", "e")}
        for r in batch
    ]
    (OUT / f"batch_{idx:03d}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in stripped),
        encoding="utf-8",
    )

from collections import Counter

sd = Counter(r["subject"] for r in rows)
st = Counter(r.get("status") for r in rows)
print(f"total_rows={len(rows)} batches={len(batches)} subj={dict(sd)} status={dict(st)}")
