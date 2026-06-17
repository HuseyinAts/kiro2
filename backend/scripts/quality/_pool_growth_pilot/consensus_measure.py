"""Pilot consensus MEASUREMENT (no DB writes).

Background:
  These 300 rows are all `verified_provisional` -> signal-1 (qwen3:14b) ALREADY
  agreed with the stored correct_answer (that is what verified_provisional means).
  So 2/2 consensus reduces to: does the INDEPENDENT 2nd signal (gemma3:12b) ALSO
  blind-solve to the stored answer? agree = (gemma3_answer == correct_answer).

  This script only MEASURES the agree-rate (overall + per subject). It writes
  NOTHING to the DB. Promotion happens later, on the full 3,960, only if the
  pilot rate justifies it.

Usage:
  python consensus_measure.py
"""

import csv
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_pool_growth_pilot")
MASTER = BASE / "master.csv"
PREDS_GLOB = str(BASE / "batches" / "preds_*.json")
MIN_CONF = 0.6

# id -> {key, subject}
meta = {}
with MASTER.open(encoding="utf-8", newline="") as f:
    for record in csv.reader(f):
        if not record:
            continue
        o = json.loads(record[0])
        meta[o["id"]] = {"key": o["key"], "subject": o.get("subject", "?")}

preds = {}
for fp in sorted(glob.glob(PREDS_GLOB)):
    try:
        data = json.loads(Path(fp).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"WARN unreadable {fp}: {e}")
        continue
    for p in data:
        if p.get("id") in meta:
            preds[p["id"]] = p

# Per-subject tallies
subj = defaultdict(lambda: {"n": 0, "solved": 0, "agree": 0, "agree_lowconf": 0,
                            "dispute": 0, "unsolvable": 0})
ans_dist = Counter()
tot = {"n": 0, "solved": 0, "agree": 0, "agree_lowconf": 0, "dispute": 0,
       "unsolvable": 0, "no_pred": 0}

for qid, m in meta.items():
    s = subj[m["subject"]]
    s["n"] += 1
    tot["n"] += 1
    p = preds.get(qid)
    if not p:
        tot["no_pred"] += 1
        continue
    a = str(p.get("answer", "")).strip().upper()
    conf = float(p.get("confidence", 0) or 0)
    if a in ("A", "B", "C", "D", "E"):
        ans_dist[a] += 1
        s["solved"] += 1
        tot["solved"] += 1
        if a == m["key"]:
            if conf >= MIN_CONF:
                s["agree"] += 1
                tot["agree"] += 1
            else:
                s["agree_lowconf"] += 1
                tot["agree_lowconf"] += 1
        else:
            s["dispute"] += 1
            tot["dispute"] += 1
    else:  # UNSOLVABLE / PARSE_FAIL / ERROR
        s["unsolvable"] += 1
        tot["unsolvable"] += 1


def rate(a, b):
    return f"{100*a/b:.1f}%" if b else "-"


print("=== PILOT CONSENSUS MEASUREMENT (gemma3:12b 2nd signal, no DB writes) ===")
print(f"total={tot['n']}  predicted={tot['n']-tot['no_pred']}  no_pred={tot['no_pred']}")
print(
    f"AGREE(conf>={MIN_CONF})={tot['agree']}  agree_lowconf={tot['agree_lowconf']}  "
    f"DISPUTE={tot['dispute']}  UNSOLVABLE={tot['unsolvable']}"
)
print(
    f"PROMOTABLE rate (agree/total) = {rate(tot['agree'], tot['n'])}   "
    f"agree/solved = {rate(tot['agree'], tot['solved'])}"
)
print("\n--- A-BIAS GUARD (gemma3 answer distribution, solved only) ---")
solved = sum(ans_dist.values())
for opt in "ABCDE":
    print(f"  {opt}: {ans_dist[opt]:4d}  {rate(ans_dist[opt], solved)}")
if solved:
    top = max(ans_dist.values()) / solved
    print(f"  max_bucket={100*top:.1f}%  ({'PATHOLOGICAL' if top > 0.45 else 'ok'})")

print("\n--- PER SUBJECT (agree = promotable consensus) ---")
print(f"{'subject':12} {'n':>4} {'solved':>7} {'agree':>6} {'agree%':>7} {'dispute':>8} {'unsolv':>7}")
for name in sorted(subj, key=lambda k: -subj[k]["n"]):
    s = subj[name]
    print(
        f"{name:12} {s['n']:>4} {s['solved']:>7} {s['agree']:>6} "
        f"{rate(s['agree'], s['n']):>7} {s['dispute']:>8} {s['unsolvable']:>7}"
    )

print(
    "\nNOTE: math subjects are expected LOW-yield (no 16GB-fit model solves Turkish "
    "math well) — that is the SAFE outcome (single-model-solvable != double-confirmed). "
    "The harvest is the non-math agree count. Decide full-3960 run on the per-subject table."
)
