#!/usr/bin/env python
"""Goc edilecek id kumesini uretir: KABUL - (set-ici mukerrer BIRLESIM capraz-DB).

`y11_ortusme_olc.py` ayni hesabi yapip RAPORLAR; bu script onu DOSYAYA yazar
(yukleyicinin `--idler` girdisi). Ikisi ayni fonksiyonlari kullanir, yani sayi
iki yerde ayri ayri hesaplanmaz -- tek kaynak.

Olculdu (20 Agu 2026):
    KABUL 3.666 | set-ici 16 | capraz-DB 34 | KESISIM 0 | BIRLESIM 50
    -> GOC KUMESI = 3.616

Cikti deterministik siralidir (kaynak sirasina sadik), yani iki kosum birebir
ayni dosyayi uretir -- `random` YOK.

Kullanim:
    python backend/scripts/quality/y11_goc_kumesi_uret.py --cikti <yol>
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Windows cp1254 konsol crash fix. `reconfigure` yalniz TextIOWrapper'da
# var; mypy `TextIO` icin bilmiyor -- bastirmak yerine VARLIGINI soruyoruz.
_yeniden_ayarla = getattr(sys.stdout, "reconfigure", None)
if _yeniden_ayarla and (sys.stdout.encoding or "").lower().startswith("cp"):
    _yeniden_ayarla(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from y11_dedup import mukerrer_gruplar, siki_kimlik  # noqa: E402
from y11_ortusme_olc import (  # noqa: E402
    SORGU_CANLI,
    SORGU_KAYNAK,
    _satirlari_cek,
    kabul_idleri,
)


async def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Y11 goc kumesi uretici")
    ap.add_argument("--cikti", required=True, type=Path)
    a = ap.parse_args(argv)

    idler = kabul_idleri()
    kaynak = await _satirlari_cek("kiro2_temp", SORGU_KAYNAK, {"idler": idler})
    if len(kaynak) != len(idler):
        raise SystemExit(
            f"HATA: {len(idler)} id istendi, {len(kaynak)} geldi. Eksik id sessizce atlanmaz."
        )

    haric: set[str] = set()
    for g in mukerrer_gruplar(kaynak):
        haric.update(g[1:])  # her gruptan ILKI kalir
    set_ici = len(haric)

    canli = await _satirlari_cek("kiro2", SORGU_CANLI)
    canli_kimlikler = {k for k in (siki_kimlik(s) for s in canli) if k}
    capraz = 0
    for s in kaynak:
        k = siki_kimlik(s)
        if k and k in canli_kimlikler and s["id"] not in haric:
            capraz += 1
        if k and k in canli_kimlikler:
            haric.add(s["id"])

    goc = [s["id"] for s in kaynak if s["id"] not in haric]
    if not goc:
        raise SystemExit("HATA: 0 id -- yanlis-sifir.")

    a.cikti.write_text("\n".join(goc) + "\n", encoding="utf-8")
    print(f"KABUL          : {len(kaynak)}")
    print(f"set-ici haric  : {set_ici}")
    print(f"capraz-DB haric: {capraz}  (set-ici ile ortusmeyen)")
    print(f"toplam haric   : {len(haric)}")
    print(f"GOC KUMESI     : {len(goc)}  -> {a.cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
