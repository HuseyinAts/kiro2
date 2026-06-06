"""Wave-3 splitter: master.csv -> answer-free batch files for blind solver agents."""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_pool_growth_wave3")
MASTER = BASE / "master.csv"
OUT = BASE / "batches"
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

print(f"total_rows={len(rows)} batches={len(batches)} batch_size={BATCH_SIZE}")
