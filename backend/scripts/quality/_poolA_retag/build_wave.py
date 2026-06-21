"""Build per-subject chunked batches for a Pool A wave.
Usage: python build_wave.py <master_csv> <out_prefix> [chunk_size=40]
Agent-facing batch files contain NO correct_answer (blindness). Keys kept separately."""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent
TAX = HERE.parent / "_vp_unlock" / "taxonomy.tsv"

master_csv = Path(sys.argv[1])
prefix = sys.argv[2]
chunk = int(sys.argv[3]) if len(sys.argv) > 3 else 40

topics_by_subject: dict[str, list[str]] = {}
for line in TAX.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    subj, topic, _tid = line.split("|")
    topics_by_subject.setdefault(subj, [])
    if topic not in topics_by_subject[subj]:
        topics_by_subject[subj].append(topic)

rows = list(csv.DictReader(master_csv.open(encoding="utf-8")))
by_subj: dict[str, list[dict]] = {}
keymap: dict[str, dict] = {}
for r in rows:
    by_subj.setdefault(r["subject_area"], []).append(r)
    keymap[r["id"]] = {"key": r["key"], "subject": r["subject_area"]}

batches = []
for subj, qs in sorted(by_subj.items()):
    topics = topics_by_subject.get(subj, [])
    for ci in range(0, len(qs), chunk):
        part = qs[ci : ci + chunk]
        idx = ci // chunk
        bf = HERE / f"{prefix}_{subj}_{idx}.json"
        bf.write_text(
            json.dumps(
                {
                    "subject": subj,
                    "topics": topics,
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
                        for r in part
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        batches.append(
            {"file": str(bf).replace("\\", "/"), "subject": subj, "n": len(part)}
        )

(HERE / f"{prefix}_keymap.json").write_text(
    json.dumps(keymap, ensure_ascii=False), encoding="utf-8"
)
(HERE / f"{prefix}_manifest.json").write_text(
    json.dumps(batches, ensure_ascii=False), encoding="utf-8"
)
print(
    f"Built {len(batches)} batches, {sum(b['n'] for b in batches)} questions, keymap {len(keymap)}"
)
from collections import Counter

for s, c in sorted(Counter(r["subject_area"] for r in rows).items()):
    print(f"  {s:12s} {c}")
