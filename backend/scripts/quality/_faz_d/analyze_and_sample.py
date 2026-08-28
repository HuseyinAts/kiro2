"""Faz D pilot: measure gemma3-agree rate (fresh pool) + build Opus validation sample.

Key question: on this NO-prior-qwen3-signal pool, is gemma3==stored reliable enough
to promote (D1), or do we need qwen3 too (D2)? Opus validates a sample of AGREES
(is gemma3==stored actually correct?) + DISPUTES.

Outputs:
  summary printed (per-subject agree rate)
  opus_d_blind.txt  -- 45 agrees + 15 disputes, key-stripped (Opus blind-solves)
  opus_d_key.csv    -- id, subject, db_key, gemma3, category  (score AFTER commit)
"""

import csv
import glob
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_faz_d")
MASTER = BASE / "master.csv"
PREDS_GLOB = str(BASE / "batches" / "preds_*.json")
random.seed(11)

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

agrees, disputes, unsolv = [], [], []
subj = defaultdict(lambda: {"a": 0, "d": 0, "u": 0})
for qid, m in master.items():
    p = preds.get(qid)
    if not p:
        continue
    g = str(p.get("answer", "")).strip().upper()
    key = str(m["key"]).strip().upper()
    s = subj[m["subject"]]
    if g in ("A", "B", "C", "D", "E"):
        if g == key:
            agrees.append((qid, m, g)); s["a"] += 1
        else:
            disputes.append((qid, m, g)); s["d"] += 1
    else:
        unsolv.append((qid, m, g)); s["u"] += 1

na, nd, nu = len(agrees), len(disputes), len(unsolv)
print("=== FAZ D PILOT — gemma3 on fresh thin-verbal pool ===")
print(f"predicted={na+nd+nu}  AGREE={na}  DISPUTE={nd}  UNSOLVABLE={nu}")
print(f"agree_rate(of predicted)={na/(na+nd+nu):.1%}  agree/solved={na/(na+nd):.1%}" if (na+nd) else "")
print("--- per subject ---")
for name in sorted(subj, key=lambda k: -(subj[k]['a']+subj[k]['d']+subj[k]['u'])):
    s = subj[name]; tot = s['a']+s['d']+s['u']
    print(f"  {name:10} n={tot:3} agree={s['a']:3} dispute={s['d']:3} unsolv={s['u']:2} agree%={100*s['a']/tot:4.1f}")

# Opus sample: 45 agrees + 15 disputes
sa = random.sample(agrees, min(45, na))
sd = random.sample(disputes, min(15, nd))
sample = [(*x, "AGREE") for x in sa] + [(*x, "DISPUTE") for x in sd]
random.shuffle(sample)

blind = ["=== OPUS BLIND SAMPLE — Faz D (NO key). Output '#N: <A-E>'.\n"]
keyrows = ["id,subject,db_key,gemma3,category"]
for i, (qid, m, g, cat) in enumerate(sample, 1):
    blind.append(
        f"#{i} [{m['subject']}]\n  Q: {m['q']}\n"
        f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n"
    )
    keyrows.append(f"{qid},{m['subject']},{m['key']},{g},{cat}")

(BASE / "opus_d_blind.txt").write_text("\n".join(blind), encoding="utf-8")
(BASE / "opus_d_key.csv").write_text("\n".join(keyrows), encoding="utf-8")
print(f"\nOpus sample -> opus_d_blind.txt ({len(sample)}: {len(sa)} agree + {len(sd)} dispute)")
