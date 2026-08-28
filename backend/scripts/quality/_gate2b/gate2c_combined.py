"""Gate2c COMBINED coherence + wrong-answer gate (gemma3 + qwen3, NO DB writes).

Two INDEPENDENT blind solvers over the 2,688 student_coherent served questions.
Stored answer key never shown to either model (blindness preserved).

Signals (defense in depth, no triple-agree math bias):
  COHERENCE_FAIL  = duplicate options OR OCR-doubled option prefix
                    OR gemma3 NOT in A-E OR qwen3 NOT in A-E
                    (either model declaring UNSOLVABLE = figure/broken/garble)
  ANSWER_WRONG    = both models in A-E AND gemma3 != key AND qwen3 != key
                    (two independent solvers both disagree with stored key
                     = likely wrong answer key; single disagreement is NOT
                     enough -> avoids penalising one model's weak subject)
  KEEP            = everything else

Coverage gate: if either model has not solved every master row, the script
PRINTS the gap and EXITS without writing a demote list (avoids acting on a
half-finished run -- the contaminated-data lesson).

Outputs (only when coverage complete):
  demote_ids.json        {"coherence": [...], "answer_wrong": [...], "all": [...]}
  opus_coherence.txt     blind sample (coherence fails + keeps) -> OK/GARBLE/FIGURE/DEGENERATE
  opus_coherence_key.csv id,gemma3,qwen3,bucket
  opus_answer.txt        answer-wrong cases, blind re-solve by Opus
  opus_answer_key.csv    id,gemma3,qwen3,stored_key
"""

import csv
import glob
import json
import random
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)
random.seed(3)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_gate2b")
ABCDE = ("A", "B", "C", "D", "E")


def load_preds(subdir):
    out = {}
    files = sorted(glob.glob(str(BASE / subdir / "preds_*.json")))
    for fp in files:
        for p in json.loads(Path(fp).read_text(encoding="utf-8")):
            out[p.get("id")] = str(p.get("answer", "")).strip().upper()
    return out, len(files)


# --- load master + both prediction sets ---
master = {}
with (BASE / "master.csv").open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if rec:
            o = json.loads(rec[0])
            master[o["id"]] = o

gemma, gfiles = load_preds("preds_gemma")
qwen, qfiles = load_preds("preds_qwen")

g_missing = [qid for qid in master if qid not in gemma]
q_missing = [qid for qid in master if qid not in qwen]

print("=== GATE2c COVERAGE ===")
print(f"master={len(master)}")
print(f"gemma3: files={gfiles} solved={len(gemma)} missing={len(g_missing)}")
print(f"qwen3 : files={qfiles} solved={len(qwen)} missing={len(q_missing)}")

if g_missing or q_missing:
    print("\n[!] Eksik tahmin var -- demote YAZILMADI.")
    if g_missing:
        print(f"    gemma3 eksik {len(g_missing)} (ilk 3: {g_missing[:3]})")
    if q_missing:
        print(f"    qwen3 eksik {len(q_missing)} (ilk 3: {q_missing[:3]})")
    print("    Eksik modeli bitir (solver resume eder), sonra bu script'i tekrar çalıştır.")
    sys.exit(0)


def dup_opts(m):
    o = [m["a"], m["b"], m["c"], m["d"], m["e"]]
    return len(set(o)) < 5


def ocr_prefix(m):
    return any(re.match(r"^[A-Ea-e]\)", str(m[k]) or "") for k in ("a", "b", "c", "d", "e"))


keep, coherence_fail, answer_wrong = [], [], []
for qid, m in master.items():
    g = gemma[qid]
    q = qwen[qid]
    key = str(m.get("key", "")).strip().upper()
    proxy = dup_opts(m) or ocr_prefix(m)
    g_ok = g in ABCDE
    q_ok = q in ABCDE
    if proxy or not g_ok or not q_ok:
        coherence_fail.append((qid, m, g, q))
    elif key in ABCDE and g != key and q != key:
        answer_wrong.append((qid, m, g, q))
    else:
        keep.append((qid, m, g, q))

n = len(master)
print("\n=== GATE2c RESULT ===")
print(f"KEEP={len(keep)} ({100*len(keep)/n:.1f}%)")
print(f"COHERENCE_FAIL={len(coherence_fail)} ({100*len(coherence_fail)/n:.1f}%)  "
      f"[either model UNSOLVABLE or dup/ocr proxy]")
print(f"ANSWER_WRONG={len(answer_wrong)} ({100*len(answer_wrong)/n:.1f}%)  "
      f"[both solvers disagree with stored key]")
demote_all = [x[0] for x in coherence_fail] + [x[0] for x in answer_wrong]
print(f"-> DEMOTE total={len(demote_all)} ({100*len(demote_all)/n:.1f}%)")

(BASE / "demote_ids.json").write_text(json.dumps({
    "coherence": [x[0] for x in coherence_fail],
    "answer_wrong": [x[0] for x in answer_wrong],
    "all": demote_all,
}), encoding="utf-8")

# --- Opus validation sample 1: coherence (judge garble/figure) ---
cf_sample = random.sample(coherence_fail, min(25, len(coherence_fail)))
keep_sample = random.sample(keep, min(15, len(keep)))
coh = [(*x, "FAIL") for x in cf_sample] + [(*x, "KEEP") for x in keep_sample]
random.shuffle(coh)
lines = ["=== OPUS COHERENCE — her soru için: OK / GARBLE / FIGURE / DEGENERATE\n"]
krows = ["id,gemma3,qwen3,bucket"]
for i, (qid, m, g, q, bucket) in enumerate(coh, 1):
    lines.append(f"#{i} [{m['subject']}]\n  Q: {m['q']}\n"
                 f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n")
    krows.append(f"{qid},{g},{q},{bucket}")
(BASE / "opus_coherence.txt").write_text("\n".join(lines), encoding="utf-8")
(BASE / "opus_coherence_key.csv").write_text("\n".join(krows), encoding="utf-8")

# --- Opus validation sample 2: answer-wrong (blind re-solve) ---
aw_sample = random.sample(answer_wrong, min(30, len(answer_wrong)))
alines = ["=== OPUS BLIND SOLVE — her soru için sadece doğru şıkkı ver (A-E). Anahtar gösterilmedi.\n"]
arows = ["id,gemma3,qwen3,stored_key"]
for i, (qid, m, g, q) in enumerate(aw_sample, 1):
    alines.append(f"#{i} [{m['subject']}]\n  Q: {m['q']}\n"
                  f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n")
    arows.append(f"{qid},{g},{q},{str(m.get('key','')).strip().upper()}")
(BASE / "opus_answer.txt").write_text("\n".join(alines), encoding="utf-8")
(BASE / "opus_answer_key.csv").write_text("\n".join(arows), encoding="utf-8")

print(f"\ndemote_ids.json yazıldı (coherence={len(coherence_fail)}, answer_wrong={len(answer_wrong)})")
print(f"opus_coherence.txt ({len(coh)} örnek) + opus_answer.txt ({len(aw_sample)} örnek) yazıldı.")
