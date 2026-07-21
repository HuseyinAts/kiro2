"""Key-stripped sample of VERBAL+SCIENCE disputes (non math/geo) for Opus 4.8 to
BLIND-adjudicate. Here gemma3 is COMPETENT, so its disagreement is real signal:
Opus solves blind, then we compare to BOTH db_key and gemma3:
  Opus == db_key            -> gemma3 slip (promotable)
  Opus == gemma3 (!= db)    -> DB-error candidate (2 independent models vs DB)
  Opus == neither           -> hard/ambiguous

Outputs:
  opus_v_blind.txt  -- numbered questions, NO key, NO gemma3 (blind solve)
  opus_v_key.csv    -- id, subject, db_key, gemma3 (for scoring AFTER commit)
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
random.seed(7)
MATHGEO = ("MATEMATIK", "GEOMETRI")

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
    if m.get("subject") in MATHGEO:
        continue
    p = preds.get(qid)
    if not p:
        continue
    g = str(p.get("answer", "")).strip().upper()
    key = str(m["key"]).strip().upper()
    if g in ("A", "B", "C", "D", "E") and g != key:
        disputes.append((qid, m, g))

sample = random.sample(disputes, min(N, len(disputes)))

blind = ["=== OPUS BLIND SAMPLE — verbal/science disputes (NO answer key) ===",
         "Solve each. Output one line per #: '#N: <A-E>'.\n"]
keyrows = ["id,subject,db_key,gemma3"]
for i, (qid, m, g) in enumerate(sample, 1):
    blind.append(
        f"#{i} [{m['subject']}]\n  Q: {m['q']}\n"
        f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n"
    )
    keyrows.append(f"{qid},{m['subject']},{m['key']},{g}")

(BASE / "opus_v_blind.txt").write_text("\n".join(blind), encoding="utf-8")
(BASE / "opus_v_key.csv").write_text("\n".join(keyrows), encoding="utf-8")
from collections import Counter

dist = Counter(m["subject"] for _, m, _ in sample)
print(f"sample={len(sample)} -> opus_v_blind.txt + opus_v_key.csv  dist={dict(dist)}")
