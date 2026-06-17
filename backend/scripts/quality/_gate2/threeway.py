"""Gate2 pilot 3-way: qwen3 + gemma3 + stored, on 300 student_coherent served questions.

Categories:
  TRIPLE_AGREE   q==g==stored   -> KEEP (coherent + answer-correct)
  UNSOLVABLE     either model UNSOLVABLE -> garble/broken/figure -> DEMOTE candidate
  TWO_VS_STORED  q==g != stored -> wrong-answer/degenerate -> review
  PARTIAL/ALL_DIFFER -> uncertain

Measures what fraction of the student_coherent served subset is truly clean
(triple-agree), to size the 2,688 full run and the keep/demote policy.
Reads preds_qwen/ and preds_gemma/. NO DB writes.
"""

import csv
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_gate2")


def load(subdir):
    d = {}
    for fp in sorted(glob.glob(str(BASE / subdir / "preds_*.json"))):
        for p in json.loads(Path(fp).read_text(encoding="utf-8")):
            a = str(p.get("answer", "")).strip().upper()
            d[p.get("id")] = a
    return d


master = {}
with (BASE / "master.csv").open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if rec:
            o = json.loads(rec[0]); master[o["id"]] = o

qw, gm = load("preds_qwen"), load("preds_gemma")
ABCDE = ("A", "B", "C", "D", "E")
cat = defaultdict(list)
for qid, m in master.items():
    q, g = qw.get(qid), gm.get(qid)
    key = str(m["key"]).strip().upper()
    if q not in ABCDE or g not in ABCDE:
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

tot = sum(len(v) for v in cat.values())
print(f"=== GATE2 PILOT 3-WAY (student_coherent served, n={tot}) ===")
for c in ("TRIPLE_AGREE", "UNSOLVABLE", "TWO_VS_STORED", "PARTIAL", "ALL_DIFFER"):
    n = len(cat[c]); print(f"  {c:14} {n:4}  {100*n/tot:5.1f}%")
print(f"\nKEEP (triple-agree) = {len(cat['TRIPLE_AGREE'])}  "
      f"DEMOTE-candidate (unsolvable) = {len(cat['UNSOLVABLE'])}  "
      f"REVIEW (two_vs_stored+differ) = {len(cat['TWO_VS_STORED'])+len(cat['ALL_DIFFER'])}")

# write category id lists for the apply step
out = {c: [x[0] for x in cat[c]] for c in cat}
(BASE / "categories.json").write_text(json.dumps(out), encoding="utf-8")
print("categories.json written.")
