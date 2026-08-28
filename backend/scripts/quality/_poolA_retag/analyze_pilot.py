"""Analyze Pool A combined-pass pilot: funnel from 150 candidates to net-promotable.
Reads pilot_solved.json (workflow rows) + pilot_keymap.json (stored keys)."""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent

rows = json.loads((HERE / "pilot_solved.json").read_text(encoding="utf-8"))
keymap = json.loads((HERE / "pilot_keymap.json").read_text(encoding="utf-8"))

# load topic lists for resolvability check
TAX = HERE.parent / "_vp_unlock" / "taxonomy.tsv"
topics_by_subject = defaultdict(set)
for line in TAX.read_text(encoding="utf-8").splitlines():
    if line.strip():
        s, t, _ = line.split("|")
        topics_by_subject[s].add(t.strip().lower())

CONF = 0.80
per = defaultdict(lambda: defaultdict(int))
seen = set()
funnel = {
    "parsed": 0,
    "subj_ok": 0,
    "topic_ok": 0,
    "agree": 0,
    "unsolvable": 0,
    "promotable": 0,
}
for r in rows:
    rid = r["id"]
    if rid not in keymap or rid in seen:
        continue
    seen.add(rid)
    subj = keymap[rid]["subject"]
    key = keymap[rid]["key"]
    funnel["parsed"] += 1
    per[subj]["n"] += 1
    if r["ans"] == "X":
        funnel["unsolvable"] += 1
        per[subj]["unsolvable"] += 1
    subj_ok = r["subjOk"] == "Y"
    topic_ok = (
        subj_ok
        and r["topic"]
        and r["topic"].lower() not in ("yok", "x")
        and r["topic"].strip().lower() in topics_by_subject.get(subj, set())
    )
    agree = r["ans"] == key and r["ans"] != "X"
    if subj_ok:
        funnel["subj_ok"] += 1
        per[subj]["subj_ok"] += 1
    if topic_ok:
        funnel["topic_ok"] += 1
        per[subj]["topic_ok"] += 1
    if agree:
        funnel["agree"] += 1
        per[subj]["agree"] += 1
    if subj_ok and topic_ok and agree and r["conf"] >= CONF:
        funnel["promotable"] += 1
        per[subj]["promotable"] += 1

n = funnel["parsed"] or 1
print(f"=== Pool A pilot funnel (n={funnel['parsed']}/150, conf>={CONF}) ===")
for k in ("subj_ok", "topic_ok", "agree", "unsolvable", "promotable"):
    print(f"  {k:12s} {funnel[k]:3d}  ({100 * funnel[k] / n:5.1f}%)")
print("\n=== per-subject (n / subj_ok / topic_ok / AGREE / promotable) ===")
for s in sorted(per):
    p = per[s]
    print(
        f"  {s:12s} n={p['n']:2d}  subjOK={p['subj_ok']:2d}  topicOK={p['topic_ok']:2d}  "
        f"AGREE={p['agree']:2d}  promote={p['promotable']:2d}"
    )
proj = round(16000 * funnel["promotable"] / n)
print(
    f"\n=== projection: {funnel['promotable']}/{n} = {100 * funnel['promotable'] / n:.1f}% "
    f"=> ~{proj} v_safe on full 16K pool ==="
)
