"""Build blind TIER-A file: all 199 promote_A ids, questions only (no key).
Opus solves opus_tierA_*.txt, then opus_tierA_key.csv opened for 4-way intersection.
Chunks of 50 for manageable solving."""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)
BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_wave1")

master = {}
with (BASE / "master.csv").open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if rec:
            o = json.loads(rec[0])
            master[o["id"]] = o

ids = json.loads((BASE / "promote_A_ids.json").read_text(encoding="utf-8"))
rows = [master[i] for i in ids if i in master]
print(f"TIER-A ids={len(ids)} resolved={len(rows)}")

key_lines = ["idx,id,stored_key"]
CHUNK = 50
for ci in range(0, len(rows), CHUNK):
    chunk = rows[ci : ci + CHUNK]
    part = ci // CHUNK + 1
    lines = [
        f"=== TIER-A BLIND chunk {part} (#{ci + 1}-{ci + len(chunk)}) — SADECE dogru sik (A-E).\n"
    ]
    for j, m in enumerate(chunk):
        idx = ci + j + 1
        lines.append(
            f"#{idx}\n  Q: {m['q']}\n"
            f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n"
        )
        key_lines.append(f"{idx},{m['id']},{str(m.get('key', '')).strip().upper()}")
    (BASE / f"opus_tierA_{part}.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"  opus_tierA_{part}.txt ({len(chunk)} soru)")

(BASE / "opus_tierA_key.csv").write_text("\n".join(key_lines), encoding="utf-8")
print(f"opus_tierA_key.csv ({len(rows)} satir) yazildi.")
