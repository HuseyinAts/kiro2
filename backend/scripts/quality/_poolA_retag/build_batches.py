"""Build per-subject batch JSON for Pool A combined re-tag+solve pilot.
Agent-facing batch files contain NO correct_answer (blindness). Keys kept separately."""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
TAX = HERE.parent / "_vp_unlock" / "taxonomy.tsv"
MASTER = HERE / "pilot_master.csv"

# subject -> list of unique topic names (preserve order)
topics_by_subject: dict[str, list[str]] = {}
topicid_by_key: dict[tuple[str, str], str] = {}
for line in TAX.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    subj, topic, tid = line.split("|")
    topics_by_subject.setdefault(subj, [])
    if topic not in topics_by_subject[subj]:
        topics_by_subject[subj].append(topic)
    topicid_by_key.setdefault((subj, topic), tid)  # first id wins

# read master, group by subject
rows = list(csv.DictReader(MASTER.open(encoding="utf-8")))
by_subj: dict[str, list[dict]] = {}
keymap: dict[str, dict] = {}
for r in rows:
    s = r["subject_area"]
    by_subj.setdefault(s, []).append(r)
    keymap[r["id"]] = {"key": r["key"], "subject": s}

batches = []
for subj, qs in sorted(by_subj.items()):
    bf = HERE / f"batch_{subj}.json"
    payload = {
        "subject": subj,
        "topics": topics_by_subject.get(subj, []),
        "questions": [
            {
                "id": r["id"],
                "q": r["q"],
                "a": r["oa"],
                "b": r["ob"],
                "c": r["oc"],
                "d": r["od"],
                "e": r["oe"],
            }
            for r in qs
        ],
    }
    bf.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    batches.append({"file": str(bf).replace("\\", "/"), "subject": subj, "n": len(qs)})

(HERE / "pilot_keymap.json").write_text(
    json.dumps(keymap, ensure_ascii=False), encoding="utf-8"
)
(HERE / "pilot_manifest.json").write_text(
    json.dumps(batches, ensure_ascii=False, indent=2), encoding="utf-8"
)

print(f"Built {len(batches)} batches, {sum(b['n'] for b in batches)} questions")
for b in batches:
    print(
        f"  {b['subject']:12s} n={b['n']:3d} topics={len(topics_by_subject.get(b['subject'], []))}"
    )
print(f"keymap: {len(keymap)} ids")
