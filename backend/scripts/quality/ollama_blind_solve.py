"""No-key blind solver: qwen3:14b (Ollama) coktan secmeli soru cozer.

DB cevap anahtari prompt'a GIRMEZ (blindness). Cikti apply.py'nin bekledigi
preds_*.json formatinda: [{id, subject, answer, confidence, solvable}].

Kullanim:
  # Tek girdi dosyasi -> tek preds dosyasi (kalibrasyon icin):
  python ollama_blind_solve.py --in path/in.jsonl --out path/preds.json
  # Bir batch klasoru -> her batch_NNN.jsonl icin preds_NNN.json:
  python ollama_blind_solve.py --batch-dir path/batches [--limit N]

Girdi jsonl satiri: {"id","subject","q","a","b","c","d","e"}
"""

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OLLAMA = "http://localhost:11434/api/generate"
MODEL = "qwen3:14b"
CONCURRENCY = 4
TIMEOUT = 180.0

PROMPT_TMPL = """Asagidaki YKS coktan secmeli sorusunu coz. Adim adim dusunme, sadece dogru sikki bul.

Soru: {q}

A) {a}
B) {b}
C) {c}
D) {d}
E) {e}

SADECE su formatta TEK SATIR cevap ver, baska hicbir sey yazma:
ANSWER: <A|B|C|D|E|NONE> | SOLVABLE: <yes|no> | CONF: <0.0-1.0>
SOLVABLE=no yalniz soru eksik/bozuk/figur-gerektiriyorsa. CONF kendi eminligin."""

LINE_RE = re.compile(
    r"ANSWER:\s*([A-E]|NONE).*?SOLVABLE:\s*(yes|no)(?:.*?CONF:\s*([01](?:\.\d+)?))?",
    re.IGNORECASE | re.DOTALL,
)


async def solve_one(client, sem, o):
    prompt = PROMPT_TMPL.format(
        q=o["q"], a=o["a"], b=o["b"], c=o["c"], d=o["d"], e=o["e"]
    )
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {"temperature": 0.0, "num_predict": 64},
    }
    async with sem:
        try:
            r = await client.post(OLLAMA, json=payload, timeout=TIMEOUT)
            r.raise_for_status()
            txt = r.json().get("response", "")
        except Exception as e:
            return {
                "id": o["id"],
                "subject": o.get("subject"),
                "answer": "ERROR",
                "confidence": 0.0,
                "solvable": None,
                "err": str(e)[:80],
            }
    m = LINE_RE.search(txt)
    if not m:
        return {
            "id": o["id"],
            "subject": o.get("subject"),
            "answer": "PARSE_FAIL",
            "confidence": 0.0,
            "solvable": None,
            "raw": txt.strip()[:80],
        }
    letter = m.group(1).upper()
    solvable = m.group(2).lower() == "yes"
    conf = float(m.group(3)) if m.group(3) else (0.7 if solvable else 0.0)
    if letter == "NONE" or not solvable:
        answer = "UNSOLVABLE"
    else:
        answer = letter
    return {
        "id": o["id"],
        "subject": o.get("subject"),
        "answer": answer,
        "confidence": round(conf, 2),
        "solvable": solvable,
    }


async def solve_file(in_path: Path, out_path: Path):
    rows = [
        json.loads(l)
        for l in in_path.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        preds = await asyncio.gather(*(solve_one(client, sem, o) for o in rows))
    out_path.write_text(json.dumps(preds, ensure_ascii=False), encoding="utf-8")
    solved = sum(1 for p in preds if p["answer"] in ("A", "B", "C", "D", "E"))
    return len(preds), solved


async def main():
    global MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp")
    ap.add_argument("--out")
    ap.add_argument("--batch-dir")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default=MODEL, help="Ollama model tag (default qwen3:14b)")
    ap.add_argument("--cooldown", type=float, default=0, help="sleep seconds between batches (GPU cool-down)")
    ap.add_argument("--max-new", dest="max_new", type=int, default=0, help="stop after N newly-solved batches (chunking)")
    args = ap.parse_args()

    MODEL = args.model
    print(f"[solver] MODEL={MODEL}", flush=True)

    t0 = time.time()
    if args.inp:
        n, s = await solve_file(Path(args.inp), Path(args.out))
        print(f"done {Path(args.inp).name}: {s}/{n} solved  {time.time() - t0:.0f}s")
        return

    bdir = Path(args.batch_dir)
    batches = sorted(bdir.glob("batch_*.jsonl"))
    if args.limit:
        batches = batches[: args.limit]
    tot = tot_solved = new_done = 0
    for i, b in enumerate(batches, 1):
        out = b.parent / f"preds_{b.stem.split('_')[1]}.json"
        if out.exists():
            print(f"[{i}/{len(batches)}] {b.name} SKIP (preds var)")
            continue
        n, s = await solve_file(b, out)
        tot += n
        tot_solved += s
        new_done += 1
        el = time.time() - t0
        eta = el / i * (len(batches) - i)
        print(
            f"[{i}/{len(batches)}] {b.name}: {s}/{n} solved | "
            f"cum {tot_solved}/{tot} | {el:.0f}s eta {eta:.0f}s",
            flush=True,
        )
        if args.max_new and new_done >= args.max_new:
            print(f"[chunk] {new_done} yeni batch bitti, durdum (--max-new). Tekrar çalıştır: kaldığından devam eder.", flush=True)
            break
        if args.cooldown:
            await asyncio.sleep(args.cooldown)
    print(
        f"\n=== DONE: {tot_solved}/{tot} solved across {len(batches)} batches "
        f"in {time.time() - t0:.0f}s ==="
    )


if __name__ == "__main__":
    asyncio.run(main())
