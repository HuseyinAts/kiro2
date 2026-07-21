"""Gate2b coherence analysis (gemma3-only). Reads master.csv + batches/preds_*.json.

Coherence signal (NO triple-agree -> no math bias):
  gemma3 answer not in A-E (UNSOLVABLE / PARSE_FAIL / ERROR) -> COHERENCE_FAIL (figure/broken)
  hard-proxy garble (duplicate options, option starts with 'A)'-style OCR doubling) -> PROXY_FAIL
  else -> KEEP (gemma3 could attempt it = coherent enough; answer-correctness is a separate gate)

Outputs: counts + demote_ids.json + opus_blind.txt/opus_key.csv (validate the FAIL set precision).
NO DB writes.
"""

import csv
import glob
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)
random.seed(3)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_gate2b")
ABCDE = ("A", "B", "C", "D", "E")

master = {}
with (BASE / "master.csv").open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if rec:
            o = json.loads(rec[0]); master[o["id"]] = o

preds = {}
for fp in sorted(glob.glob(str(BASE / "batches" / "preds_*.json"))):
    for p in json.loads(Path(fp).read_text(encoding="utf-8")):
        preds[p.get("id")] = str(p.get("answer", "")).strip().upper()

missing = [qid for qid in master if qid not in preds]


def dup_opts(m):
    o = [m["a"], m["b"], m["c"], m["d"], m["e"]]
    return len(set(o)) < 5


def ocr_prefix(m):
    import re
    return any(re.match(r"^[A-Ea-e]\)", str(m[k]) or "") for k in ("a", "b", "c", "d", "e"))


keep, fail_unsolv, fail_proxy = [], [], []
for qid, m in master.items():
    g = preds.get(qid)
    if g is None:
        continue  # not yet solved (chunked run incomplete)
    if dup_opts(m) or ocr_prefix(m):
        fail_proxy.append((qid, m, g))
    elif g not in ABCDE:
        fail_unsolv.append((qid, m, g))
    else:
        keep.append((qid, m, g))

solved = len(keep) + len(fail_unsolv) + len(fail_proxy)
print("=== GATE2b COHERENCE (gemma3-only) ===")
print(f"master={len(master)}  solved={solved}  not-yet-solved={len(missing)}")
if solved:
    print(f"KEEP(coherent)={len(keep)} ({100*len(keep)/solved:.1f}%)  "
          f"FAIL_unsolvable={len(fail_unsolv)}  FAIL_proxy={len(fail_proxy)}  "
          f"-> DEMOTE total={len(fail_unsolv)+len(fail_proxy)} ({100*(len(fail_unsolv)+len(fail_proxy))/solved:.1f}%)")

if missing:
    print(f"\n[!] {len(missing)} batch henüz çözülmedi — gemma3'ü bitir, sonra tekrar çalıştır.")

demote = [x[0] for x in fail_unsolv] + [x[0] for x in fail_proxy]
(BASE / "demote_ids.json").write_text(json.dumps(demote), encoding="utf-8")

# Opus validation sample: 30 FAIL + 15 KEEP -> confirm gemma3-UNSOLVABLE really = garble
fails = fail_unsolv + fail_proxy
sf = random.sample(fails, min(30, len(fails)))
sk = random.sample(keep, min(15, len(keep)))
sample = [(*x, "FAIL") for x in sf] + [(*x, "KEEP") for x in sk]
random.shuffle(sample)
blind = ["=== GATE2b OPUS VALIDATION — judge coherence: OK / GARBLE / FIGURE / DEGENERATE.\n"]
keyrows = ["id,gemma3,bucket"]
for i, (qid, m, g, bucket) in enumerate(sample, 1):
    blind.append(f"#{i} [{m['subject']}]\n  Q: {m['q']}\n"
                 f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n")
    keyrows.append(f"{qid},{g},{bucket}")
(BASE / "opus_blind.txt").write_text("\n".join(blind), encoding="utf-8")
(BASE / "opus_key.csv").write_text("\n".join(keyrows), encoding="utf-8")
print(f"demote_ids.json ({len(demote)}) + opus_blind.txt ({len(sample)}) written.")
