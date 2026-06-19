import csv, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_wave1")

# opus answers: idx -> letter
opus = {}
with (BASE/"opus_tierA_answers.csv").open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        opus[int(r["idx"])] = r["opus"].strip().upper()

# key: idx -> (id, stored)
rows = []
with (BASE/"opus_tierA_key.csv").open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append((int(r["idx"]), r["id"], r["stored_key"].strip().upper()))

agree, disagree = [], []
for idx, qid, stored in rows:
    o = opus.get(idx, "?")
    if o == stored:
        agree.append(qid)
    else:
        disagree.append((idx, qid, o, stored))

n = len(rows)
print(f"TIER-A total = {n}")
print(f"4-way AGREE (opus==stored) = {len(agree)} ({100*len(agree)/n:.1f}%)")
print(f"disagree/excluded = {len(disagree)} ({100*len(disagree)/n:.1f}%)")
(BASE/"promote_4way_ids.json").write_text(json.dumps(agree), encoding="utf-8")
print("\nExcluded (idx, opus, stored):")
for idx, qid, o, st in disagree:
    print(f"  #{idx}: opus={o} stored={st}")
print(f"\npromote_4way_ids.json yazildi ({len(agree)} id).")
