"""Cift frontmatter onarimi.

12 Agu 2026: .claude/rules/ altindaki bazi dosyalarda ZATEN YAML frontmatter
vardi (name/description/trigger/priority). `paths:` eklerken ikinci bir `---`
blogu dosyanin GOVDESINE dustu -> Claude Code'un yol-kapsamli yuklemesi
CALISMAZ, ustelik govdede coplu metin kalir.

Bu script ikinci blogu soker ve `paths:` girdilerini BIRINCI frontmatter'in
sonuna tasir. CRLF/LF karisik dosyalarda satir sonlarini korur.

Idempotent: ikinci blok yoksa dosyaya dokunmaz.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RULES = Path(__file__).resolve().parents[1] / ".claude" / "rules"
HEDEFLER = ["testing.md", "security.md", "systematic-debugging.md"]


def satir_sonu(ham: bytes) -> str:
    return "\r\n" if b"\r\n" in ham.split(b"\n", 3)[0] + b"\n" else "\n"


def onar(yol: Path) -> str:
    ham = yol.read_bytes()
    eol = satir_sonu(ham)
    satirlar = ham.decode("utf-8").replace("\r\n", "\n").split("\n")

    if not satirlar or satirlar[0].strip() != "---":
        return "ATLANDI (frontmatter yok)"

    # 1. blogun kapanisi
    try:
        kapanis1 = next(i for i in range(1, len(satirlar)) if satirlar[i].strip() == "---")
    except StopIteration:
        return "ATLANDI (1. blok kapanmamis)"

    # kapanistan sonra bos satirlari atla, ikinci '---' var mi
    j = kapanis1 + 1
    while j < len(satirlar) and satirlar[j].strip() == "":
        j += 1
    if j >= len(satirlar) or satirlar[j].strip() != "---":
        return "ATLANDI (2. blok yok — zaten temiz)"

    try:
        kapanis2 = next(i for i in range(j + 1, len(satirlar)) if satirlar[i].strip() == "---")
    except StopIteration:
        return "ATLANDI (2. blok kapanmamis)"

    tasinacak = satirlar[j + 1 : kapanis2]
    if not any(s.startswith("paths:") for s in tasinacak):
        return "ATLANDI (2. blokta paths: yok)"

    # 2. bloktan sonraki bos satirlari da yut
    k = kapanis2 + 1
    while k < len(satirlar) and satirlar[k].strip() == "":
        k += 1

    yeni = satirlar[:kapanis1] + tasinacak + ["---", ""] + satirlar[k:]
    yol.write_bytes(eol.join(yeni).encode("utf-8"))
    return f"ONARILDI ({len(tasinacak)} satir tasindi, eol={'CRLF' if eol == chr(13)+chr(10) else 'LF'})"


def main() -> int:
    for ad in HEDEFLER:
        yol = RULES / ad
        if not yol.exists():
            print(f"{ad:28} YOK")
            continue
        print(f"{ad:28} {onar(yol)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
