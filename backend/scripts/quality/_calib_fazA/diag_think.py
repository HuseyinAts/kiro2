"""Tani: think:false STEM'i mi sakatliyor? MAT+GEO'yu thinking ACIK coz, karsilastir."""

import asyncio
import csv
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

OLLAMA = "http://localhost:11434/api/generate"
MODEL = "qwen3:14b"
MASTER = Path("C:/Users/husey/kiro2/backend/scripts/quality/_calib_fazA/master.csv")
SUBJECTS = {"MATEMATIK", "GEOMETRI"}

PROMPT = """Asagidaki YKS coktan secmeli matematik sorusunu dikkatlice coz. Adim adim hesapla, sonra dogru sikki sec.

Soru: {q}

A) {a}
B) {b}
C) {c}
D) {d}
E) {e}

Cozumunden sonra EN SON satira tam su formatta yaz:
ANSWER: <A|B|C|D|E|NONE>"""

ANS_RE = re.compile(r"ANSWER:\s*([A-E]|NONE)", re.IGNORECASE)


async def solve(client, sem, o):
    async with sem:
        try:
            r = await client.post(
                OLLAMA,
                json={
                    "model": MODEL,
                    "prompt": PROMPT.format(**o),
                    "stream": False,
                    "think": True,
                    "options": {"temperature": 0.0, "num_predict": 2048},
                },
                timeout=300.0,
            )
            txt = r.json().get("response", "")
        except Exception as e:
            return o["id"], None, str(e)[:60]
    ms = ANS_RE.findall(txt)
    return o["id"], (ms[-1].upper() if ms else None), ""


async def main():
    key, rows = {}, []
    with MASTER.open(encoding="utf-8", newline="") as f:
        for rec in csv.reader(f):
            if not rec:
                continue
            o = json.loads(rec[0])
            if o["subject"] in SUBJECTS:
                key[o["id"]] = (o["subject"], o["key"])
                rows.append({k: o[k] for k in ("id", "q", "a", "b", "c", "d", "e")})
    print(f"think=ON tani: {len(rows)} MAT+GEO sorusu\n")
    sem = asyncio.Semaphore(4)
    t0 = time.time()
    async with httpx.AsyncClient() as client:
        res = await asyncio.gather(*(solve(client, sem, o) for o in rows))
    by = defaultdict(lambda: {"n": 0, "solved": 0, "corr": 0})
    for pid, letter, err in res:
        subj, db = key[pid]
        d = by[subj]
        d["n"] += 1
        if letter in ("A", "B", "C", "D", "E"):
            d["solved"] += 1
            if letter == db:
                d["corr"] += 1
    print(
        f"{'BRANS':12} {'N':>3} {'SOLV':>5} {'CORR':>5} {'think=ON':>9}  (think=OFF onceki)"
    )
    prev = {"MATEMATIK": "34%", "GEOMETRI": "42%"}
    for subj in sorted(by):
        d = by[subj]
        acc = d["corr"] / d["solved"] if d["solved"] else 0
        print(
            f"{subj:12} {d['n']:>3} {d['solved']:>5} {d['corr']:>5} {acc:>8.0%}   (was {prev.get(subj)})"
        )
    print(
        f"\nsure {time.time() - t0:.0f}s ({(time.time() - t0) / len(rows):.1f}s/soru)"
    )


if __name__ == "__main__":
    asyncio.run(main())
