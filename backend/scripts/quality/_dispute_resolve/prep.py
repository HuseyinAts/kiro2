"""master.csv -> blind batch jsonl (db/claude/wave STRIP = qwen körlüğü)."""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_dispute_resolve")
MASTER = BASE / "master.csv"
BATCHES = BASE / "batches"
BATCHES.mkdir(exist_ok=True)
SIZE = 20

rows = []
with MASTER.open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if not rec:
            continue
        o = json.loads(rec[0])
        # blind: yalniz qwen'in cozecegi alanlar; db/claude/wave VERILMEZ
        rows.append({k: o[k] for k in ("id", "subject", "q", "a", "b", "c", "d", "e")})

for i in range(0, len(rows), SIZE):
    chunk = rows[i : i + SIZE]
    num = str(i // SIZE).zfill(3)
    (BATCHES / f"batch_{num}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in chunk), encoding="utf-8"
    )

print(
    f"{len(rows)} dispute -> {(len(rows) + SIZE - 1) // SIZE} blind batch (size {SIZE})"
)
