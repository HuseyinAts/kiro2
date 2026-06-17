"""student_coherent=true audit: master.csv -> blind.txt (NO key) + key.csv.
Opus assesses BOTH: (1) coherence (readable/solvable?), (2) answer (Opus==stored?).
Measures the wrong-answer rate WITHIN the coherent subset before tightening v_safe."""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_coherent_audit")
rows = []
with (BASE / "master.csv").open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if rec:
            rows.append(json.loads(rec[0]))

blind = ["=== student_coherent AUDIT (NO key). Per #N: coherence (OK/GARBLE/FIGURE) + answer (A-E).\n"]
key = ["id,subject,db_key"]
for i, r in enumerate(rows, 1):
    blind.append(f"#{i} [{r['subject']}]\n  Q: {r['q']}\n"
                 f"  A) {r['a']}\n  B) {r['b']}\n  C) {r['c']}\n  D) {r['d']}\n  E) {r['e']}\n")
    key.append(f"{r['id']},{r['subject']},{r['key']}")

(BASE / "blind.txt").write_text("\n".join(blind), encoding="utf-8")
(BASE / "key.csv").write_text("\n".join(key), encoding="utf-8")
print(f"rows={len(rows)} subj={dict(Counter(r['subject'] for r in rows))} -> blind.txt + key.csv")
