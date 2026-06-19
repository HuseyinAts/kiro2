"""Answer-wrong WRONG-KEY hunt — phase 1: consensus subset (gemma3==qwen3 != stored).
Highest yield for wrong-key detection (two independent models agree, stored differs).

Writes BLIND batches (question+options only, no key, no model answers) so Opus solves
honestly, plus aw_key.csv (id,gemma3,qwen3,stored) read AFTER judging.
correct_answer is NOT modified anywhere — output is a candidate list for human review.
"""

import csv
import glob
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_gate2b")
OUT = BASE / "aw_batches"
OUT.mkdir(exist_ok=True)
ABCDE = ("A", "B", "C", "D", "E")
BATCH = 35


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
aw = set(json.loads((BASE / "demote_ids.json").read_text(encoding="utf-8"))["answer_wrong"])

consensus = []
for qid in aw:
    g, q = gemma[qid], qwen[qid]
    key = str(master[qid].get("key", "")).strip().upper()
    if g in ABCDE and g == q and g != key:
        consensus.append(qid)
consensus.sort()

key_rows = ["id,gemma3,qwen3,stored"]
for bi in range(0, len(consensus), BATCH):
    chunk = consensus[bi:bi + BATCH]
    lines = [f"=== AW CONSENSUS BATCH {bi//BATCH:02d} — her soru: sadece doğru şık (A-E). Anahtar gizli.\n"]
    for n, qid in enumerate(chunk, 1):
        m = master[qid]
        lines.append(f"#{n} [{m['subject']}]\n  Q: {m['q']}\n"
                     f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n")
        key_rows.append(f"{qid},{gemma[qid]},{qwen[qid]},{str(m.get('key','')).strip().upper()}")
    (OUT / f"aw_{bi//BATCH:02d}.txt").write_text("\n".join(lines), encoding="utf-8")

(BASE / "aw_key.csv").write_text("\n".join(key_rows), encoding="utf-8")
print(f"consensus answer-wrong = {len(consensus)}")
print(f"{(len(consensus)+BATCH-1)//BATCH} batch yazıldı -> aw_batches/aw_NN.txt  + aw_key.csv")
