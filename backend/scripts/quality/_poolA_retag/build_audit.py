"""Build subject-SHUFFLED blind batches for the anchoring/2nd-signal audit.
Agent files carry NO subject and NO key (open-ended classification, no leakage).
Keymap holds stored subject + key + srcset for the apply-side comparison."""

import csv
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent
CHUNK = 40

rows = list(csv.DictReader((HERE / "audit_master.csv").open(encoding="utf-8")))
# deterministic shuffle by md5(id) -> mixes subjects across batches (no anchoring/leak)
rows.sort(
    key=lambda r: hashlib.md5(r["id"].encode(), usedforsecurity=False).hexdigest()
)

keymap = {
    r["id"]: {"subject": r["subject_area"], "key": r["key"], "srcset": r["srcset"]}
    for r in rows
}
batches = []
for ci in range(0, len(rows), CHUNK):
    part = rows[ci : ci + CHUNK]
    bf = HERE / f"aud_{ci // CHUNK}.json"
    bf.write_text(
        json.dumps(
            {
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
    batches.append({"file": str(bf).replace("\\", "/"), "n": len(part)})

(HERE / "aud_keymap.json").write_text(
    json.dumps(keymap, ensure_ascii=False), encoding="utf-8"
)
(HERE / "aud_manifest.json").write_text(
    json.dumps(batches, ensure_ascii=False), encoding="utf-8"
)
print(
    f"Built {len(batches)} mixed batches, {len(rows)} questions, keymap {len(keymap)}"
)
