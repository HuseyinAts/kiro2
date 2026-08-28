"""Blind-solve dalga SPLIT adimi.
wave<N>_master.csv -> w<N>batches/g01..gNN.json (40'lik, KEY YOK = kor) + w<N>manifest.json

Kullanim:  python split_wave.py <N>
Master kolonlar: id,subject_area,q,oa,ob,oc,od,oe,key
Batch format (workflow'un okudugu): {"questions":[{"id","q","a","b","c","d","e"},...]}  (key + subject HARIC = korluk)
"""

import csv
import json
import sys
from pathlib import Path

D = Path(r"C:/Users/husey/kiro2/backend/scripts/quality/_blindsolve")
BATCH = 40


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python split_wave.py <N>")
        sys.exit(1)
    n = sys.argv[1]
    master = D / f"wave{n}_master.csv"
    if not master.exists():
        print(f"YOK: {master} (once export_wave{n}.sql calistir)")
        sys.exit(1)

    rows = []
    with master.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"BOS master: {master}")
        sys.exit(1)

    outdir = D / f"w{n}batches"
    outdir.mkdir(exist_ok=True)
    manifest = []
    for i in range(0, len(rows), BATCH):
        chunk = rows[i : i + BATCH]
        gi = i // BATCH + 1
        qs = [
            {
                "id": c["id"],
                "q": c["q"],
                "a": c["oa"],
                "b": c["ob"],
                "c": c["oc"],
                "d": c["od"],
                "e": c["oe"],
            }
            for c in chunk
        ]
        fp = outdir / f"g{gi:02d}.json"
        fp.write_text(
            json.dumps({"questions": qs}, ensure_ascii=False), encoding="utf-8"
        )
        manifest.append({"file": str(fp).replace("\\", "/"), "n": len(qs)})

    mf = D / f"w{n}manifest.json"
    mf.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    print(f"OK: {len(rows)} soru -> {len(manifest)} batch -> {mf}")
    print(f"Workflow args = bu dosyanin icerigi (JSON array): {mf}")


if __name__ == "__main__":
    main()
