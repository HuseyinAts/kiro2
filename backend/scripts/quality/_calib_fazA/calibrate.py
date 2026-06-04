"""Faz A kalibrasyon: qwen3:14b'yi known-good (verified_provisional) uzerinde
BLIND cozer, DB anahtariyla brans-bazli uyum olcer.

Cikti: brans bazinda qwen==DB dogrulugu + solvable orani + A-bias.
Eslik esigi >= %85 olan branslar Wave-4 auto-promote'a UYGUN.
"""

import asyncio
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

from ollama_blind_solve import solve_file  # noqa: E402

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_calib_fazA")
MASTER = BASE / "master.csv"
INPUT = BASE / "input.jsonl"
PREDS = BASE / "preds.json"


async def main():
    # 1) master.csv -> input.jsonl (key STRIP edilir = blindness) + key map
    key = {}
    rows = []
    with MASTER.open(encoding="utf-8", newline="") as f:
        for rec in csv.reader(f):
            if not rec:
                continue
            o = json.loads(rec[0])
            key[o["id"]] = o["key"]
            rows.append(
                {k: o[k] for k in ("id", "subject", "q", "a", "b", "c", "d", "e")}
            )
    INPUT.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8"
    )
    print(f"kalibrasyon: {len(rows)} known-good soru, anahtar strip edildi\n")

    # 2) solve
    t0 = time.time()
    n, solved = await solve_file(INPUT, PREDS)
    print(f"cozuldu: {solved}/{n}  {time.time() - t0:.0f}s\n")

    # 3) brans-bazli uyum
    preds = json.loads(PREDS.read_text(encoding="utf-8"))
    by_subj = defaultdict(lambda: {"n": 0, "solved": 0, "correct": 0})
    abias = defaultdict(int)
    for p in preds:
        a = p["answer"]
        s = by_subj[p["subject"]]
        s["n"] += 1
        if a in ("A", "B", "C", "D", "E"):
            s["solved"] += 1
            abias[a] += 1
            if a == key.get(p["id"]):
                s["correct"] += 1

    print(f"{'BRANS':12} {'N':>3} {'SOLV':>5} {'CORR':>5} {'qwen==DB':>9} {'AUTO?':>6}")
    print("-" * 48)
    eligible = []
    for subj in sorted(by_subj):
        d = by_subj[subj]
        acc = d["correct"] / d["solved"] if d["solved"] else 0
        ok = acc >= 0.85 and d["solved"] >= 10
        if ok:
            eligible.append(subj)
        print(
            f"{subj:12} {d['n']:>3} {d['solved']:>5} {d['correct']:>5} "
            f"{acc:>8.0%} {'YES' if ok else 'no':>6}"
        )

    tot_solved = sum(d["solved"] for d in by_subj.values())
    tot_corr = sum(d["correct"] for d in by_subj.values())
    print("-" * 48)
    print(
        f"{'TOPLAM':12} {sum(d['n'] for d in by_subj.values()):>3} "
        f"{tot_solved:>5} {tot_corr:>5} "
        f"{(tot_corr / tot_solved if tot_solved else 0):>8.0%}"
    )
    print("\n--- A-BIAS (qwen cevap dagilimi) ---")
    for opt in "ABCDE":
        print(
            f"  {opt}: {abias[opt]:>3}  {abias[opt] / tot_solved:.0%}"
            if tot_solved
            else opt
        )
    top = max(abias.values()) / tot_solved if tot_solved else 0
    print(f"  max_bucket={top:.0%} ({'PATHOLOGICAL' if top > 0.40 else 'ok'})")
    print(f"\n>>> AUTO-PROMOTE'a uygun branslar (>=85%, n>=10): {eligible}")


if __name__ == "__main__":
    asyncio.run(main())
