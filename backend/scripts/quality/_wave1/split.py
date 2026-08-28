"""Wave1 splitter: AYT-Edebiyat promote adaylarini blind batch'lere ayirir.
master.csv -> batches/batch_NNN.jsonl (id,subject,q,a..e; ANAHTAR YOK).
ollama_blind_solve.py bu batch'leri gemma3 + qwen3 ile cozer (resume-safe)."""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_wave1")
OUT = BASE / "batches"
OUT.mkdir(parents=True, exist_ok=True)
BATCH_SIZE = 20

rows = []
with (BASE / "master.csv").open(encoding="utf-8", newline="") as f:
    for record in csv.reader(f):
        if record:
            rows.append(json.loads(record[0]))

batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
for idx, batch in enumerate(batches):
    stripped = [{k: r[k] for k in ("id", "subject", "q", "a", "b", "c", "d", "e")} for r in batch]
    (OUT / f"batch_{idx:03d}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in stripped), encoding="utf-8")

print(f"total_rows={len(rows)} batches={len(batches)}")
