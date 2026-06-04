"""Smoke-test: qwen3:14b YKS sorularini BLIND cozer, DB anahtariyla karsilastirir.

Amac: Faz A gate — qwen YKS cozebiliyor mu? (anahtar prompt'a GIRMEZ)
"""

import json
import re
import sys
import time
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OLLAMA = "http://localhost:11434/api/generate"
MODEL = "qwen3:14b"
SAMPLE = Path("C:/Users/husey/AppData/Local/Temp/smoke_known_good.tsv")

PROMPT_TMPL = """Asagidaki YKS coktan secmeli sorusunu coz. Adim adim dusunme, sadece dogru sikki bul.

Soru: {q}

A) {a}
B) {b}
C) {c}
D) {d}
E) {e}

SADECE su formatta TEK SATIR cevap ver, baska hicbir sey yazma:
ANSWER: <A|B|C|D|E|NONE> | SOLVABLE: <yes|no>
SOLVABLE=no sadece soru eksik/bozuk/figur-gerektiriyorsa."""

LINE_RE = re.compile(
    r"ANSWER:\s*([A-E]|NONE).*?SOLVABLE:\s*(yes|no)", re.IGNORECASE | re.DOTALL
)


def solve(o):
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
    r = httpx.post(OLLAMA, json=payload, timeout=180.0)
    r.raise_for_status()
    txt = r.json().get("response", "")
    m = LINE_RE.search(txt)
    if not m:
        return None, None, txt[:120]
    letter = m.group(1).upper()
    solvable = m.group(2).lower() == "yes"
    return letter, solvable, txt.strip()[:120]


def main():
    rows = [
        json.loads(line.split("\t")[0])
        for line in SAMPLE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(f"smoke sample: {len(rows)} soru\n")
    correct = solved = 0
    t0 = time.time()
    for i, o in enumerate(rows, 1):
        try:
            letter, solvable, raw = solve(o)
        except Exception as e:
            print(f"{i}. [{o['subject']:10}] HATA: {e}")
            continue
        db = o["key"]
        if letter in ("A", "B", "C", "D", "E"):
            solved += 1
            hit = "OK " if letter == db else "XX "
            if letter == db:
                correct += 1
        else:
            hit = "?? "
        print(
            f"{i}. [{o['subject']:10}] qwen={letter} db={db} solvable={solvable} {hit} | {raw[:60]}"
        )
    dt = time.time() - t0
    print(
        f"\n=== SMOKE: solved={solved}/{len(rows)}  correct={correct}/{solved if solved else 1}"
        f"  ({correct / len(rows):.0%} of all)  {dt:.0f}s  ({dt / len(rows):.1f}s/soru) ==="
    )


if __name__ == "__main__":
    main()
