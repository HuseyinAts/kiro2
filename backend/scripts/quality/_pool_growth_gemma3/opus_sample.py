"""Produce a key-stripped sample of MATH+GEO disputes for an independent strong
model (Claude Opus 4.8, via the Cowork session) to BLIND-solve, to measure the
true accuracy of qwen3+answer-key on the disputed math (validates the Faz B
decision to promote ~1,265 math/geo on qwen3 alone).

Outputs:
  opus_blind.txt  -- numbered questions, NO key, NO gemma3 answer (for blind solve)
  opus_key.csv    -- id, subject, db_key, gemma3 (for scoring AFTER answers committed)
"""

import csv
import glob
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_pool_growth_gemma3")
MASTER = BASE / "master.csv"
PREDS_GLOB = str(BASE / "batches" / "preds_*.json")
N = 60
random.seed(42)

master = {}
with MASTER.open(encoding="utf-8", newline="") as f:
    for record in csv.reader(f):
        if not record:
            continue
        o = json.loads(record[0])
        master[o["id"]] = o

preds = {}
for fp in sorted(glob.glob(PREDS_GLOB)):
    for p in json.loads(Path(fp).read_text(encoding="utf-8")):
        if p.get("id") in master:
            preds[p["id"]] = p

disputes = []
for qid, m in master.items():
    if m.get("subject") not in ("MATEMATIK", "GEOMETRI"):
        continue
    p = preds.get(qid)
    if not p:
        continue
    g = str(p.get("answer", "")).strip().upper()
    key = str(m["key"]).strip().upper()
    if g in ("A", "B", "C", "D", "E") and g != key:
        disputes.append((qid, m, g))

sample = random.sample(disputes, min(N, len(disputes)))

blind = ["=== OPUS BLIND SAMPLE — math/geo disputes (NO answer key) ===",
         "Solve each. Output one line per #: '#N: <A-E>'.\n"]
keyrows = ["id,subject,db_key,gemma3"]
for i, (qid, m, g) in enumerate(sample, 1):
    blind.append(
        f"#{i} [{m['subject']}]\n  Q: {m['q']}\n"
        f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n"
    )
    keyrows.append(f"{qid},{m['subject']},{m['key']},{g}")

(BASE / "opus_blind.txt").write_text("\n".join(blind), encoding="utf-8")
(BASE / "opus_key.csv").write_text("\n".join(keyrows), encoding="utf-8")
print(f"sample={len(sample)} (math/geo disputes) -> opus_blind.txt + opus_key.csv")
