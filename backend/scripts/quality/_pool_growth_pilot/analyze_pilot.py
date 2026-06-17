"""Deep line-by-line pilot analysis (no DB writes).

Cross-joins master.csv (DB key + question + options) with gemma3 preds.
For these verified_provisional rows qwen3 ALREADY == DB key, so:
  - AGREE  = gemma3 == DB key  -> 2-model blind consensus (promotable)
  - DISPUTE = gemma3 != DB key  -> gemma3 contradicts (qwen3 == DB)

Writes:
  summary.txt        -- counts, confidence stats, dispute conf histogram, per-subject
  disputes_full.txt  -- EVERY dispute, full question+options+key+gemma3+conf,
                        sorted by gemma3 confidence DESC (high-conf = DB-error candidates)
  agrees_sample.txt  -- 15 highest-conf agrees (sanity)
"""

import csv
import glob
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_pool_growth_pilot")
MASTER = BASE / "master.csv"
PREDS_GLOB = str(BASE / "batches" / "preds_*.json")
MIN_CONF = 0.6

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

agree, dispute = [], []
for qid, m in master.items():
    p = preds.get(qid)
    if not p:
        continue
    a = str(p.get("answer", "")).strip().upper()
    conf = float(p.get("confidence", 0) or 0)
    key = str(m["key"]).strip().upper()
    row = {"id": qid, "subject": m.get("subject"), "key": key, "g": a, "conf": conf, "m": m}
    if a == key:
        agree.append(row)
    else:
        dispute.append(row)

agree.sort(key=lambda r: -r["conf"])
dispute.sort(key=lambda r: -r["conf"])


def fmt(r):
    m = r["m"]
    lines = [
        f"[{r['subject']}] id={r['id']}  DB_key={r['key']}  gemma3={r['g']}  conf={r['conf']}",
        f"  Q: {m['q']}",
        f"  A) {m['a']}",
        f"  B) {m['b']}",
        f"  C) {m['c']}",
        f"  D) {m['d']}",
        f"  E) {m['e']}",
    ]
    return "\n".join(lines)


# summary.txt
out = []
out.append("=== PILOT DEEP ANALYSIS ===")
out.append(f"total_with_pred={len(agree)+len(dispute)}  AGREE={len(agree)}  DISPUTE={len(dispute)}")
ac = [r["conf"] for r in agree]
dc = [r["conf"] for r in dispute]
if ac:
    out.append(f"AGREE conf: mean={st.mean(ac):.3f} median={st.median(ac):.3f} min={min(ac)} max={max(ac)}")
if dc:
    out.append(f"DISPUTE conf: mean={st.mean(dc):.3f} median={st.median(dc):.3f} min={min(dc)} max={max(dc)}")
out.append("\n--- DISPUTE confidence histogram (high conf = DB-error OR confident-gemma3-error) ---")
buckets = [(0.9, 1.01), (0.8, 0.9), (0.7, 0.8), (0.6, 0.7), (0.0, 0.6)]
for lo, hi in buckets:
    n = sum(1 for c in dc if lo <= c < hi)
    out.append(f"  conf [{lo:.1f},{hi:.1f}): {n}")
out.append("\n--- per subject: agree / dispute / mean-dispute-conf ---")
subj = defaultdict(lambda: {"a": 0, "d": 0, "dc": []})
for r in agree:
    subj[r["subject"]]["a"] += 1
for r in dispute:
    subj[r["subject"]]["d"] += 1
    subj[r["subject"]]["dc"].append(r["conf"])
for name in sorted(subj, key=lambda k: -(subj[k]["a"] + subj[k]["d"])):
    s = subj[name]
    tot = s["a"] + s["d"]
    mdc = st.mean(s["dc"]) if s["dc"] else 0
    out.append(f"  {name:12} n={tot:3} agree={s['a']:3} dispute={s['d']:3} agree%={100*s['a']/tot:4.1f} mean_disp_conf={mdc:.2f}")
(BASE / "summary.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))

# disputes_full.txt — EVERY dispute, full text, high-conf first
disp_txt = ["=== ALL DISPUTES (gemma3 != DB key), sorted by gemma3 confidence DESC ===",
            "High confidence at top = gemma3 most sure it disagrees = DB-error candidates.\n"]
for i, r in enumerate(dispute, 1):
    disp_txt.append(f"#{i}  " + fmt(r) + "\n")
(BASE / "disputes_full.txt").write_text("\n".join(disp_txt), encoding="utf-8")

# agrees_sample.txt — top 15 conf agrees
ag_txt = ["=== TOP 15 HIGH-CONF AGREES (2-model consensus sanity) ===\n"]
for i, r in enumerate(agree[:15], 1):
    ag_txt.append(f"#{i}  " + fmt(r) + "\n")
(BASE / "agrees_sample.txt").write_text("\n".join(ag_txt), encoding="utf-8")

print(f"\nWrote: summary.txt, disputes_full.txt ({len(dispute)} cases), agrees_sample.txt")
