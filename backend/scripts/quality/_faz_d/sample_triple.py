"""Sample TRIPLE_AGREE (40) + TWO_VS_STORED (20) for Opus to blind-validate.
  TRIPLE_AGREE  -> if Opus==stored, the triple set is clean (D2 promotable).
  TWO_VS_STORED -> if Opus==(qwen3/gemma3 answer)!=stored, confirms DB error.
Outputs opus_t_blind.txt (no key) + opus_t_key.csv (id, cat, stored, model_ans)."""

import csv
import glob
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)
BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_faz_d")
random.seed(23)

def load(sub):
    d = {}
    for fp in sorted(glob.glob(str(BASE / sub / "preds_*.json"))):
        for p in json.loads(Path(fp).read_text(encoding="utf-8")):
            a = str(p.get("answer","")).strip().upper()
            d[p.get("id")] = a if a in ("A","B","C","D","E") else None
    return d

master = {}
with (BASE/"master.csv").open(encoding="utf-8", newline="") as f:
    for r in csv.reader(f):
        if r:
            o = json.loads(r[0]); master[o["id"]] = o
qw, gm = load("preds_qwen"), load("preds_gemma")

triple, two = [], []
for qid, m in master.items():
    q, g = qw.get(qid), gm.get(qid); key = str(m["key"]).strip().upper()
    if q is None or g is None: continue
    if q == g == key: triple.append((qid, m, key, "TRIPLE", key))
    elif q == g and q != key: two.append((qid, m, key, "TWO_VS_STORED", q))

sample = random.sample(triple, min(40, len(triple))) + random.sample(two, min(20, len(two)))
random.shuffle(sample)
blind = ["=== OPUS BLIND — Faz D validation (no key). '#N: <A-E>'.\n"]
keyrows = ["id,subject,category,stored_key,model_answer"]
for i,(qid,m,key,cat,mans) in enumerate(sample,1):
    blind.append(f"#{i} [{m['subject']}]\n  Q: {m['q']}\n  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n")
    keyrows.append(f"{qid},{m['subject']},{cat},{key},{mans}")
(BASE/"opus_t_blind.txt").write_text("\n".join(blind), encoding="utf-8")
(BASE/"opus_t_key.csv").write_text("\n".join(keyrows), encoding="utf-8")
print(f"sample={len(sample)} (triple={min(40,len(triple))} + two_vs_stored={min(20,len(two))}) -> opus_t_blind.txt")
