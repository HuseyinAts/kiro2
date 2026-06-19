"""Wave1 PROMOTE gate (AYT-Edebiyat pool-growth). Adapted from _gate2b/gate2c_combined.py.

Two INDEPENDENT blind solvers (gemma3 + qwen3) over the wave1 pilot candidates.
Stored answer key never shown to either model (blindness preserved; key lives only
in master.csv, read here for comparison).

Polarity vs gate2c: gate2c hunts BAD questions to demote. wave1 hunts GOOD questions
to PROMOTE into v_safe_for_beta. So:
  - coherence gate is LENIENT: broken only if BOTH models abstain (or dup/OCR proxy).
  - promotion is STRICT: a model must actively MATCH the stored key to give a signal.

Pipeline order (HANDOFF SS3-4): coherence gate first (DROP broken), THEN TIER on survivors.

Categories:
  DROP_broken    = dup options OR OCR-doubled prefix OR BOTH models UNSOLVABLE/abstain
  PROMOTE_A      = gemma == qwen == key   (3-way agreement, high confidence)
  PROMOTE_B      = exactly one model == key, other in A-E and different (one confirm, one disagree)
  PROMOTE_Babs   = exactly one model == key, other abstains (one confirm, one abstain)
                   -> folded into promote_B for Opus validation but tracked separately
  DROP_wrongkey  = both in A-E AND gemma != key AND qwen != key (likely wrong key OR hard)
  DROP_unresolved= one abstains, other in A-E but != key (no confirmation, conservative drop)

Coverage gate: operate only on the id-set BOTH models have solved (pilot subset of master).
If the two solved-sets differ, print the gap and EXIT (no half-finished action).

Outputs (only when coverage consistent):
  wave1_breakdown.json   full category id-lists + counts
  promote_A_ids.json     [...]
  promote_B_ids.json     [...]
  opus_A.txt             blind sample (~20 TIER-A) -> Opus solves, then opus_A_key.csv opened
  opus_A_key.csv         id,gemma3,qwen3,stored_key
  opus_B.txt             blind sample (~30 TIER-B) -> Opus solves, then opus_B_key.csv opened
  opus_B_key.csv         id,gemma3,qwen3,stored_key,subtype
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

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_wave1")
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

g_ids = set(gemma)
q_ids = set(qwen)
solved = (g_ids & q_ids) & set(master)

print("=== WAVE1 GATE COVERAGE ===")
print(f"master={len(master)}")
print(f"gemma3: files={gfiles} solved={len(gemma)}")
print(f"qwen3 : files={qfiles} solved={len(qwen)}")
print(f"intersection (both solved, in master) = {len(solved)}")

g_only = (g_ids - q_ids) & set(master)
q_only = (q_ids - g_ids) & set(master)
if g_only or q_only:
    print(
        f"\n[!] Solved-set mismatch: gemma-only={len(g_only)} qwen-only={len(q_only)}"
    )
    print("    (Pilot = ilk 60 batch her iki modelde de dolu olmali.)")
    if g_only:
        print(f"    gemma-only ilk 3: {list(g_only)[:3]}")
    if q_only:
        print(f"    qwen-only ilk 3: {list(q_only)[:3]}")
    print("    Eksik modeli bitir (solver resume eder), sonra tekrar calistir.")
    sys.exit(0)

if not solved:
    print("\n[!] Hic ortak cozulmus soru yok -- DUR.")
    sys.exit(0)


def dup_opts(m):
    o = [m["a"], m["b"], m["c"], m["d"], m["e"]]
    return len(set(o)) < 5


def ocr_prefix(m):
    return any(
        re.match(r"^[A-Ea-e]\)", str(m[k]) or "") for k in ("a", "b", "c", "d", "e")
    )


drop_broken, promote_A, promote_B_dis, promote_B_abs = [], [], [], []
drop_wrongkey, drop_unresolved = [], []

for qid in solved:
    m = master[qid]
    g = gemma[qid]
    q = qwen[qid]
    key = str(m.get("key", "")).strip().upper()
    g_ok = g in ABCDE
    q_ok = q in ABCDE
    proxy = dup_opts(m) or ocr_prefix(m)

    # --- coherence gate first ---
    if proxy or (not g_ok and not q_ok):
        drop_broken.append((qid, m, g, q))
        continue

    # --- TIER on survivors ---
    g_match = g_ok and g == key
    q_match = q_ok and q == key
    if g_match and q_match:
        promote_A.append((qid, m, g, q))
    elif g_match != q_match:  # exactly one confirms the key
        other_ok = q_ok if g_match else g_ok
        if other_ok:
            promote_B_dis.append((qid, m, g, q))  # other in A-E, different
        else:
            promote_B_abs.append((qid, m, g, q))  # other abstains
    elif g_ok and q_ok:  # both A-E, neither == key
        drop_wrongkey.append((qid, m, g, q))
    else:  # one abstains, other A-E but != key -> no confirmation
        drop_unresolved.append((qid, m, g, q))

n = len(solved)
promote_B = promote_B_dis + promote_B_abs


def pct(x):
    return f"{100 * len(x) / n:.1f}%"


print("\n=== WAVE1 GATE RESULT ===")
print(f"solved(judged)         = {n}")
print(
    f"DROP_broken            = {len(drop_broken)} ({pct(drop_broken)})  [dup/OCR or both-abstain]"
)
print(f"PROMOTE_A (g==q==key)   = {len(promote_A)} ({pct(promote_A)})")
print(
    f"PROMOTE_B (one==key)    = {len(promote_B)} ({pct(promote_B)})  "
    f"[disagree={len(promote_B_dis)} abstain={len(promote_B_abs)}]"
)
print(
    f"DROP_wrongkey          = {len(drop_wrongkey)} ({pct(drop_wrongkey)})  [both A-E, neither==key]"
)
print(
    f"DROP_unresolved        = {len(drop_unresolved)} ({pct(drop_unresolved)})  [one abstain, one!=key]"
)
promote_total = len(promote_A) + len(promote_B)
print(f"-> PROMOTE candidate total = {promote_total} ({100 * promote_total / n:.1f}%)")

breakdown = {
    "counts": {
        "solved": n,
        "drop_broken": len(drop_broken),
        "promote_A": len(promote_A),
        "promote_B_disagree": len(promote_B_dis),
        "promote_B_abstain": len(promote_B_abs),
        "drop_wrongkey": len(drop_wrongkey),
        "drop_unresolved": len(drop_unresolved),
    },
    "promote_A_ids": [x[0] for x in promote_A],
    "promote_B_ids": [x[0] for x in promote_B],
    "drop_broken_ids": [x[0] for x in drop_broken],
    "drop_wrongkey_ids": [x[0] for x in drop_wrongkey],
    "drop_unresolved_ids": [x[0] for x in drop_unresolved],
}
(BASE / "wave1_breakdown.json").write_text(
    json.dumps(breakdown, ensure_ascii=False), encoding="utf-8"
)
(BASE / "promote_A_ids.json").write_text(
    json.dumps([x[0] for x in promote_A]), encoding="utf-8"
)
(BASE / "promote_B_ids.json").write_text(
    json.dumps([x[0] for x in promote_B]), encoding="utf-8"
)


def write_blind(sample, txt_path, key_path, key_header, key_row):
    lines = [
        "=== OPUS BLIND SOLVE — her soru icin SADECE dogru sikki ver (A-E). Anahtar gosterilmedi.\n"
    ]
    krows = [key_header]
    for i, item in enumerate(sample, 1):
        qid, m, g, q = item[0], item[1], item[2], item[3]
        lines.append(
            f"#{i} [{m['subject']}]\n  Q: {m['q']}\n"
            f"  A) {m['a']}\n  B) {m['b']}\n  C) {m['c']}\n  D) {m['d']}\n  E) {m['e']}\n"
        )
        krows.append(key_row(item))
    (BASE / txt_path).write_text("\n".join(lines), encoding="utf-8")
    (BASE / key_path).write_text("\n".join(krows), encoding="utf-8")


# --- Opus sample 1: TIER-A (~20) ---
a_sample = random.sample(promote_A, min(20, len(promote_A)))
write_blind(
    a_sample,
    "opus_A.txt",
    "opus_A_key.csv",
    "id,gemma3,qwen3,stored_key",
    lambda it: f"{it[0]},{it[2]},{it[3]},{str(it[1].get('key', '')).strip().upper()}",
)

# --- Opus sample 2: TIER-B (~30), stratified to include disagree-heavy cases ---
b_pool = [(*x, "disagree") for x in promote_B_dis] + [
    (*x, "abstain") for x in promote_B_abs
]
b_sample = random.sample(b_pool, min(30, len(b_pool)))
write_blind(
    b_sample,
    "opus_B.txt",
    "opus_B_key.csv",
    "id,gemma3,qwen3,stored_key,subtype",
    lambda it: f"{it[0]},{it[2]},{it[3]},{str(it[1].get('key', '')).strip().upper()},{it[4]}",
)

print(
    f"\nwave1_breakdown.json + promote_A_ids.json ({len(promote_A)}) + promote_B_ids.json ({len(promote_B)}) yazildi."
)
print(
    f"opus_A.txt ({len(a_sample)} ornek) + opus_B.txt ({len(b_sample)} ornek) yazildi (blind)."
)
