"""Workflow journal.jsonl'den ajan sonuclarini cikar.

Bildirimdeki `result` alani uzun kanitlarda KESILIR. Kesilmis bir sonuctan
kutuge yama yazmak, kanitin yarisini kaybetmek demektir. Bu script tam
donus degerini journal'dan okur.

KULLANIM:
    python scripts/read_workflow_journal.py <run_id> [iddia_id]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TRANSCRIPTS = Path.home() / ".claude" / "projects" / "C--Users-husey-kiro2"


def bul(run_id: str) -> Path:
    hits = list(TRANSCRIPTS.glob(f"*/subagents/workflows/{run_id}*/journal.jsonl"))
    if not hits:
        raise SystemExit(f"journal bulunamadi: {run_id}")
    return hits[0]


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    run_id = sys.argv[1]
    filtre = sys.argv[2] if len(sys.argv) > 2 else None

    yol = bul(run_id)
    print(f"# {yol}\n")

    for satir in yol.read_text(encoding="utf-8", errors="replace").splitlines():
        if not satir.strip():
            continue
        try:
            kayit = json.loads(satir)
        except json.JSONDecodeError:
            continue
        if kayit.get("type") != "result":
            continue

        etiket = kayit.get("label") or kayit.get("agentId") or "?"
        deger = kayit.get("result")
        # Sonuc cogu zaman duz metin (JSON zorunlu degil); JSON-benzer
        # gorunmeyen string'ler icin parse'i hic denemeyerek gereksiz
        # istisna-tabanli akistan kacinilir.
        if isinstance(deger, str) and deger.strip()[:1] in ("{", "["):
            try:
                deger = json.loads(deger)
            except json.JSONDecodeError as e:
                print(f"# uyari: {etiket} JSON-benzer ama parse edilemedi: {e}", file=sys.stderr)

        kimlik = deger.get("id") if isinstance(deger, dict) else None
        if filtre and filtre not in str(etiket) and filtre != kimlik:
            continue

        print("=" * 78)
        print(f"AJAN: {etiket}")
        if isinstance(deger, dict):
            for k, v in deger.items():
                print(f"\n--- {k} ---")
                print(v)
        else:
            print(deger)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
