"""Dump the 30 gemma-flagged-unsolvable questions (28 gemma-only + 2 both)
for Opus coherence review. These are NOT auto-demoted; Opus decides each.
Blind (no key shown). No DB writes."""

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


sel = []
for qid, m in master.items():
    if dup_opts(m) or ocr_prefix(m):
        continue  # already in reliable proxy set
    g, q = gemma[qid], qwen[qid]
    if g not in ABCDE:  # gemma-only or both unsolvable
        sel.append((qid, m, g, q))

lines = ["=== OPUS EXTRA REVIEW — gemma3 'unsolvable' dedi. Her biri: OK / GARBLE / FIGURE / DEGENERATE\n"]
rows = ["id,gemma3,qwen3"]
for i, (qid, m, g, q) in enumerate(sel, 1):
    lines.append(f"#{i} [{m['subject']}]\n  Q: {m['q']}\n"
                 f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n")
    rows.append(f"{qid},{g},{q}")
(BASE / "opus_extra.txt").write_text("\n".join(lines), encoding="utf-8")
(BASE / "opus_extra_key.csv").write_text("\n".join(rows), encoding="utf-8")
print(f"opus_extra.txt yazıldı: {len(sel)} soru (gemma-unsolvable, proxy hariç).")
