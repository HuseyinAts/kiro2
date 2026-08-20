#!/usr/bin/env python
"""Aday id listesi → (id, kitap, container yolu, host yolu) TSV.

Kör okuma ajanları bu TSV'yi okur. Yol dönüşümü **TEK yerde**: iki ayrı ajanın
kendi başına yol kurması, S237'de 4 kez ısıran `/tmp` ad-alanı ve NFC-NFD
tuzaklarını tekrar üretirdi.

⚠️ DOSYA VARLIĞINI BASH `[ -f ]` İLE SORMA. NTFS'te Türkçe `İ/ı/ğ` NFC-NFD
farkı var olan dosyaya "yok" dedirtiyor (S237'de 8/8 yanlış-negatif ölçüldü).
Container'dan `os.path.isfile` ile sor — bu script container yolunu da yazıyor
tam bu yüzden.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from y11_aday_uret import dsn_coz

HOST_KOK = "C:/Users/husey/kiro2/d-dataset/output/crops"
CONTAINER_KOK = "/app/static/crops"
ONEK = "/static/crops/"


def yol_ciftleri(url: str | None) -> tuple[str, str]:
    """`question_image_url` → (container yolu, host yolu). Saf, test edilebilir."""
    ham = url or ""
    gorece = ham[len(ONEK) :] if ham.startswith(ONEK) else ham.lstrip("/")
    return f"{CONTAINER_KOK}/{gorece}", f"{HOST_KOK}/{gorece}"


async def _main(argv: list[str] | None = None) -> int:
    import asyncpg

    ap = argparse.ArgumentParser(description="Aday id -> crop yol TSV")
    ap.add_argument("--idler", required=True, type=Path)
    ap.add_argument("--cikti", required=True, type=Path)
    a = ap.parse_args(argv)

    idler = [s for s in a.idler.read_text(encoding="utf-8").split() if s]
    baglanti = await asyncpg.connect(dsn_coz("kiro2_temp"))
    try:
        satirlar = await baglanti.fetch(
            "SELECT id::text AS id, source_book AS kitap, "
            "question_image_url AS url FROM question_bank "
            "WHERE id::text = ANY($1::text[])",
            idler,
        )
    finally:
        await baglanti.close()

    # Aday sirasini KORU — ajan dilimleri deterministik olsun.
    sirada = {r["id"]: r for r in satirlar}
    with a.cikti.open("w", encoding="utf-8", newline="\n") as f:
        for id_ in idler:
            r = sirada.get(id_)
            if r is None:
                continue
            kap, host = yol_ciftleri(r["url"])
            f.write(f"{id_}\t{r['kitap']}\t{kap}\t{host}\n")

    eksik = len(idler) - len(satirlar)
    print(f"istenen: {len(idler)} | yazilan: {len(satirlar)} | eksik: {eksik}")
    print(f"cikti  : {a.cikti}")
    return 0 if eksik == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
