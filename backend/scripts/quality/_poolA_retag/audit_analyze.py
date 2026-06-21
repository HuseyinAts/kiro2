"""Analyze the open-ended reclassification audit.
Reads aud_solved.json (open subj/ans/conf) + aud_keymap.json (stored subj/key/srcset).
Buckets promotes (anchoring/wrong-subject + 2nd-signal) and lowconf (recovery)."""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent

TRMAP = str.maketrans("İIŞĞÜÖÇ", "IISGUOC")


def norm(s):  # ASCII-upper subject key for comparison
    return (s or "").upper().translate(TRMAP).replace(" ", "")


rows = json.loads((HERE / "aud_solved.json").read_text(encoding="utf-8"))
keymap = json.loads((HERE / "aud_keymap.json").read_text(encoding="utf-8"))

buckets = defaultdict(list)
seen = set()
miss = 0
for r in rows:
    rid = r["id"]
    if rid not in keymap or rid in seen:
        continue
    seen.add(rid)
    km = keymap[rid]
    subj_match = norm(r["subj"]) == norm(km["subject"])
    ans_match = r["ans"] == km["key"] and r["ans"] != "X"
    if km["srcset"] == "promote":
        if not subj_match:
            buckets["promote_WRONG_SUBJECT"].append(
                (rid, km["subject"], r["subj"], r["conf"])
            )
        elif ans_match:
            buckets["promote_2signal_CONFIRM"].append((rid,))  # subj+ans both confirmed
        else:
            buckets["promote_answer_DISPUTE"].append(
                (rid, km["key"], r["ans"], r["conf"])
            )
    elif subj_match and ans_match:
        buckets["lowconf_RECOVER"].append((rid,))  # 3-way agree (book+solve1+solve2)
    elif not subj_match:
        buckets["lowconf_wrong_subject"].append((rid,))
    else:
        buckets["lowconf_still_dispute"].append((rid,))
# the keymap ids the audit failed to reclassify (parse drop) -> untouched
keymap_ids = set(keymap)
reclassified = seen
missing = keymap_ids - reclassified

print(
    f"=== Audit reclassify: {len(reclassified)}/{len(keymap_ids)} (missing {len(missing)}) ===\n"
)
print("PROMOTE set (1829):")
for k in ("promote_2signal_CONFIRM", "promote_WRONG_SUBJECT", "promote_answer_DISPUTE"):
    print(f"  {k:28s} {len(buckets[k]):4d}")
print("\nLOWCONF set (548):")
for k in ("lowconf_RECOVER", "lowconf_wrong_subject", "lowconf_still_dispute"):
    print(f"  {k:28s} {len(buckets[k]):4d}")


# write candidate id lists for apply / phase-B verify
def dump(name, items, cols):
    p = HERE / f"aud_{name}.tsv"
    with p.open("w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for it in items:
            f.write("\t".join(str(x) for x in it) + "\n")
    return len(items)


dump(
    "wrong_subject", buckets["promote_WRONG_SUBJECT"], ["id", "stored", "open", "conf"]
)
dump(
    "answer_dispute",
    buckets["promote_answer_DISPUTE"],
    ["id", "key", "open_ans", "conf"],
)
dump("recover", buckets["lowconf_RECOVER"], ["id"])
dump("2signal_confirm", buckets["promote_2signal_CONFIRM"], ["id"])
print(
    "\nWrote candidate TSVs: aud_wrong_subject / aud_answer_dispute / aud_recover / aud_2signal_confirm"
)

# wrong-subject direction (which stored subjects are most contested?)
print("\nWrong-subject stored→open transitions (top):")
trans = Counter((km, op) for _, km, op, _ in buckets["promote_WRONG_SUBJECT"])
for (a, b), n in trans.most_common(12):
    print(f"  {a:12s} -> {b:12s} {n}")
