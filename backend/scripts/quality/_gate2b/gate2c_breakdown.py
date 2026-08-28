"""Breakdown of the 818 demote candidates by signal reliability (post Opus validation).

Opus validation (70-item sample) measured:
  - hard proxy (dup options / OCR-doubled prefix): ~100% precision  -> RELIABLE
  - qwen3 UNSOLVABLE (single model):               ~36% precision   -> NOISE
  - answer-wrong (both models != stored key):      ~27% precision   -> NOISE
                                                   (small models too weak on hard Q)

So: auto-demote ONLY the hard-proxy set. Everything else -> Opus/human review queue,
not auto-removal. This script counts each signal and writes the RELIABLE demote list.
No DB writes.
"""

import csv
import glob
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_gate2b")
ABCDE = ("A", "B", "C", "D", "E")


def load_preds(subdir):
    out = {}
    for fp in sorted(glob.glob(str(BASE / subdir / "preds_*.json"))):
        for p in json.loads(Path(fp).read_text(encoding="utf-8")):
            out[p.get("id")] = str(p.get("answer", "")).strip().upper()
    return out


master = {}
with (BASE / "master.csv").open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if rec:
            o = json.loads(rec[0])
            master[o["id"]] = o

gemma = load_preds("preds_gemma")
qwen = load_preds("preds_qwen")


def dup_opts(m):
    return len({m["a"], m["b"], m["c"], m["d"], m["e"]}) < 5


def ocr_prefix(m):
    return any(re.match(r"^[A-Ea-e]\)", str(m[k]) or "") for k in ("a", "b", "c", "d", "e"))


proxy, both_unsolv, g_only_unsolv, q_only_unsolv = [], [], [], []
aw_consensus, aw_split = [], []
for qid, m in master.items():
    g, q = gemma[qid], qwen[qid]
    key = str(m.get("key", "")).strip().upper()
    is_proxy = dup_opts(m) or ocr_prefix(m)
    g_ok, q_ok = g in ABCDE, q in ABCDE
    if is_proxy:
        proxy.append(qid)
        continue
    if not g_ok and not q_ok:
        both_unsolv.append(qid)
    elif not g_ok:
        g_only_unsolv.append(qid)
    elif not q_ok:
        q_only_unsolv.append(qid)
    elif key in ABCDE and g != key and q != key:
        (aw_consensus if g == q else aw_split).append(qid)

n = len(master)
print(f"master={n}\n")
print("--- COHERENCE signals ---")
print(f"hard proxy (dup/ocr)      = {len(proxy):4d}  [RELIABLE ~100%]  -> AUTO-DEMOTE")
print(f"both models UNSOLVABLE     = {len(both_unsolv):4d}  [check: rare, maybe reliable]")
print(f"gemma3-only UNSOLVABLE     = {len(g_only_unsolv):4d}  [noise]")
print(f"qwen3-only UNSOLVABLE      = {len(q_only_unsolv):4d}  [NOISE ~36%]  -> review, NOT auto")
print("\n--- ANSWER-WRONG signals (both A-E, both != key) ---")
print(f"models agree (g==q!=key)   = {len(aw_consensus):4d}  [NOISE ~27%]  -> review, NOT auto")
print(f"models split (g!=q, both!=key) = {len(aw_split):4d}  [NOISE]  -> review, NOT auto")

reliable = sorted(proxy)
(BASE / "demote_reliable.json").write_text(json.dumps({
    "proxy": sorted(proxy),
    "both_unsolvable": sorted(both_unsolv),
    "reliable_demote": reliable,
}), encoding="utf-8")
print(f"\ndemote_reliable.json yazıldı: proxy={len(proxy)} (auto), both_unsolv={len(both_unsolv)} (incele)")
print(f"RELIABLE auto-demote = {len(reliable)} ({100*len(reliable)/n:.1f}% of {n})")
print(f"REJECTED as noise = {n - len(reliable) - len(both_unsolv)} kept (would have been false-positive demotes)")
