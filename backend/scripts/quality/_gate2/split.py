"""Gate2 pilot splitter: master.csv -> answer-free batches (qwen3 + gemma3 will both solve).
Goal: measure TRIPLE_AGREE rate on the student_coherent served subset, to decide the
keep-criterion (triple-agree = coherent+answer-correct) before the 2,688 full run."""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_gate2")
MASTER = BASE / "master.csv"
OUT = BASE / "batches"
OUT.mkdir(exist_ok=True)
BATCH_SIZE = 20

rows = []
with MASTER.open(encoding="utf-8", newline="") as f:
    for record in csv.reader(f):
        if record:
            rows.append(json.loads(record[0]))

batches = [rows[i : i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
for idx, batch in enumerate(batches):
    stripped = [{k: r[k] for k in ("id", "subject", "q", "a", "b", "c", "d", "e")} for r in batch]
    (OUT / f"batch_{idx:03d}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in stripped), encoding="utf-8")

from collections import Counter

print(f"total_rows={len(rows)} batches={len(batches)} subj={dict(Counter(r['subject'] for r in rows))}")
