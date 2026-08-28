"""Re-gate splitter: blind_solve bulk (16.344) -> blind batch'ler (anahtar YOK).
master.csv -> batches/batch_NNN.jsonl  (ollama_blind_solve.py için)."""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_blindsolve/regate")
OUT = BASE / "batches"
OUT.mkdir(parents=True, exist_ok=True)
BATCH_SIZE = 20

rows = []
with (BASE / "master.csv").open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if rec:
            rows.append(json.loads(rec[0]))

batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
for idx, batch in enumerate(batches):
    stripped = [{k: r[k] for k in ("id", "subject", "q", "a", "b", "c", "d", "e")} for r in batch]
    (OUT / f"batch_{idx:04d}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in stripped), encoding="utf-8")

print(f"total_rows={len(rows)} batches={len(batches)}")
