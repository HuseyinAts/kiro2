"""Faz D 3-way analysis: qwen3 + gemma3 + stored key, on the same 300 pilot.

Reads preds_qwen/ and preds_gemma/ (run separately to avoid collision) + master key.
Categorizes each question:
  TRIPLE_AGREE   q==g==stored      -> clean; D2 promotion candidate
  TWO_VS_STORED  q==g != stored    -> 2 independent models agree on a DIFFERENT
                                       answer -> HIGH-confidence DB-error (bad key)
  PARTIAL        q==stored != g  OR g==stored != q   -> single model confirms key
  ALL_DIFFER     q != g != stored

Outputs counts + per-subject + writes db_error_candidates.csv (TWO_VS_STORED).
NO DB writes.
"""

import csv
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_faz_d")
MASTER = BASE / "master.csv"


def load_preds(subdir):
    d = {}
    for fp in sorted(glob.glob(str(BASE / subdir / "preds_*.json"))):
        for p in json.loads(Path(fp).read_text(encoding="utf-8")):
            a = str(p.get("answer", "")).strip().upper()
            d[p.get("id")] = a if a in ("A", "B", "C", "D", "E") else None
    return d


master = {}
with MASTER.open(encoding="utf-8", newline="") as f:
    for record in csv.reader(f):
        if not record:
            continue
        o = json.loads(record[0])
        master[o["id"]] = o

qw = load_preds("preds_qwen")
gm = load_preds("preds_gemma")

cat = defaultdict(list)
subj = defaultdict(lambda: defaultdict(int))
for qid, m in master.items():
    q, g = qw.get(qid), gm.get(qid)
    key = str(m["key"]).strip().upper()
    if q is None or g is None:
        c = "UNSOLVABLE"
    elif q == g == key:
        c = "TRIPLE_AGREE"
    elif q == g and q != key:
        c = "TWO_VS_STORED"
    elif q == key or g == key:
        c = "PARTIAL"
    else:
        c = "ALL_DIFFER"
    cat[c].append((qid, m, q, g, key))
    subj[m["subject"]][c] += 1

tot = sum(len(v) for v in cat.values())
print("=== FAZ D 3-WAY (qwen3 + gemma3 + stored) — 300 pilot ===")
for c in ("TRIPLE_AGREE", "TWO_VS_STORED", "PARTIAL", "ALL_DIFFER", "UNSOLVABLE"):
    n = len(cat[c])
    print(f"  {c:14} {n:4}  {100*n/tot:5.1f}%")
print("\n--- per subject ---")
for s in sorted(subj, key=lambda k: -sum(subj[k].values())):
    d = subj[s]
    print(f"  {s:10} triple={d['TRIPLE_AGREE']:3} two_vs_stored={d['TWO_VS_STORED']:3} "
          f"partial={d['PARTIAL']:3} all_differ={d['ALL_DIFFER']:3} unsolv={d['UNSOLVABLE']:2}")

# DB-error candidates (TWO_VS_STORED): 2 models agree key is wrong
rows = ["id,subject,stored_key,qwen3_gemma3_answer,question"]
for qid, m, q, g, key in cat["TWO_VS_STORED"]:
    qt = m["q"].replace("\n", " ").replace(",", " ")[:90]
    rows.append(f"{qid},{m['subject']},{key},{q},{qt}")
(BASE / "db_error_candidates.csv").write_text("\n".join(rows), encoding="utf-8")
print(f"\nTWO_VS_STORED (DB-error candidates) -> db_error_candidates.csv ({len(cat['TWO_VS_STORED'])})")
print("TRIPLE_AGREE = D2 promotion candidates (clean if Opus confirms).")
