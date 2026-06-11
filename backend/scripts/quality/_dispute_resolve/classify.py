"""DISPUTE 3-sinyal sınıflama: qwen (farklı-model) vs Claude-blind vs DB.

correct_answer'a DOKUNMAZ — yalnız bucket'lar + curator worklist üretir.

Bucketlar:
  REAL_ERROR_CAND : qwen==claude  ∧ qwen!=db  → 2 bağımsız model DB'ye karşı → curator (yüksek öncelik)
  CLAUDE_ERROR    : qwen==db                   → Claude hatasıydı, DB durur → dispute düşür
  SPLIT           : qwen!=claude ∧ qwen!=db    → 3'lü ayrışma → curator
  UNSOLVABLE      : qwen çözemedi               → figür/garble defer
  PARSE_FAIL      : qwen parse hatası           → atla
"""

import csv
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_dispute_resolve")
MASTER = BASE / "master.csv"
PREDS = str(BASE / "batches" / "preds_*.json")

meta = {}
with MASTER.open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if not rec:
            continue
        o = json.loads(rec[0])
        meta[o["id"]] = o

qwen = {}
for fp in sorted(glob.glob(PREDS)):
    for p in json.load(open(fp, encoding="utf-8")):
        qwen[p["id"]] = p

buckets = defaultdict(list)
subj_real = Counter()
qwen_dist = Counter()
for qid, m in meta.items():
    p = qwen.get(qid)
    if not p:
        buckets["NO_PRED"].append(qid)
        continue
    a = str(p.get("answer", "")).strip().upper()
    db = (m.get("db") or "").strip().upper()
    cl = (m.get("claude") or "").strip().upper()
    conf = float(p.get("confidence", 0) or 0)
    if a not in ("A", "B", "C", "D", "E"):
        buckets[
            "UNSOLVABLE"
            if a in ("UNSOLVABLE", "UNSOLVED", "NONE", "SKIP")
            else "PARSE_FAIL"
        ].append(qid)
        continue
    qwen_dist[a] += 1
    if a == db:
        buckets["CLAUDE_ERROR"].append(qid)
    elif a == cl:
        buckets["REAL_ERROR_CAND"].append((qid, db, cl, conf, m.get("subject")))
        subj_real[m.get("subject")] += 1
    else:
        buckets["SPLIT"].append((qid, db, cl, a, conf, m.get("subject")))

tot = len(meta)
solved = sum(qwen_dist.values())
print(f"=== DISPUTE 3-SİNYAL SINIFLAMA ({tot} dispute) ===")
for k in (
    "REAL_ERROR_CAND",
    "CLAUDE_ERROR",
    "SPLIT",
    "UNSOLVABLE",
    "PARSE_FAIL",
    "NO_PRED",
):
    n = len(buckets[k])
    print(f"  {k:16} {n:5}  {100 * n / tot:5.1f}%")
print("\n--- qwen A-BIAS (çözülen) ---")
for opt in "ABCDE":
    print(
        f"  {opt}: {qwen_dist[opt]:5}  {100 * qwen_dist[opt] / solved:.0f}%"
        if solved
        else opt
    )
top = max(qwen_dist.values()) / solved if solved else 0
print(f"  max_bucket={top:.0%} ({'PATHOLOGICAL' if top > 0.40 else 'ok'})")

print("\n--- REAL_ERROR_CAND branş dağılımı (qwen==claude, ikisi DB'ye karşı) ---")
for s, n in subj_real.most_common(12):
    print(f"  {s:12} {n}")

# curator worklist: REAL_ERROR_CAND (correct_answer DEĞİŞTİRİLMEZ, öneri olarak)
real = buckets["REAL_ERROR_CAND"]
out = BASE / "real_error_candidates.tsv"
with out.open("w", encoding="utf-8") as f:
    f.write("id\tdb_answer\tsuggested(qwen==claude)\tqwen_conf\tsubject\n")
    for qid, db, cl, conf, subj in real:
        f.write(f"{qid}\t{db}\t{cl}\t{conf}\t{subj}\n")
print(f"\nworklist: {out} ({len(real)} satır)")

# stem vs sözel ayrımı (qwen STEM'de zayıf — güven farkı)
stem = {"MATEMATIK", "GEOMETRI", "FIZIK", "KIMYA"}
real_stem = sum(1 for r in real if r[4] in stem)
print(f"REAL_ERROR_CAND: STEM={real_stem}  sözel/sosyal={len(real) - real_stem}")
print(
    "  (NOT: qwen STEM'de zayıf → STEM real-error'lar daha temkinli, sözel daha güvenilir)"
)
