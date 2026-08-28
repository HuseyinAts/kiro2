#!/usr/bin/env python
"""FAZ D'nin ON KOSULU: goc edilecek satir sayisini TEK SAYI olarak olcer (salt okunur).

Devir notu (S236) sunu birakti ve olcumu YAPMADI:

    "3.666 - 16 (siki set-ici mukerrer) - 34 (capraz-DB) +- ortusme.
     **Ortusme OLCULMEDI** - 16'nin kaci 34'un icinde?"

Iki kume ORTUSEBILIR: set-ici mukerrer bir satir, ayni zamanda canli DB'de de
bulunuyor olabilir. Ortusme olculmeden cikarma yapmak sayiyi ya fazla ya eksik
gosterir. Bu script birlesimi (union) olcer, yani dogru sayiyi verir.

Ayrica S236'da olculdu: `y11_dedup_olc.py` docstring'i hala "78 satir / 73 grup,
siki" diyor -- o rakam GOVDE-ONLY olcumune ait, SIKI kimlige degil. Bu script
sayilari yeniden uretir, docstring'e guvenmez.

Kullanim (postgres trust, parola gerekmez):
    python backend/scripts/quality/y11_ortusme_olc.py
"""

from __future__ import annotations

import asyncio
import csv
import os
import sys
from pathlib import Path

# Windows cp1254 konsol crash fix. `reconfigure` yalniz TextIOWrapper'da
# var; mypy `TextIO` icin bilmiyor -- bastirmak yerine VARLIGINI soruyoruz.
_yeniden_ayarla = getattr(sys.stdout, "reconfigure", None)
if _yeniden_ayarla and (sys.stdout.encoding or "").lower().startswith("cp"):
    _yeniden_ayarla(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402
from y11_dedup import mukerrer_gruplar, siki_kimlik  # noqa: E402

TSV = Path(__file__).resolve().parent / "y11_kimya_verdikt_TAM.tsv"
VARSAYILAN_KOK = "postgresql+asyncpg://postgres@localhost:5434"


def kabul_idleri() -> list[str]:
    """TSV'den verdikti KABUL olan id'ler. Kolon adi TAHMIN EDILMEZ, basliktan bulunur."""
    with TSV.open(encoding="utf-8", newline="") as f:
        okuyucu = csv.reader(f, delimiter="\t")
        basliklar = next(okuyucu)
        try:
            i_id = next(i for i, b in enumerate(basliklar) if b.strip().lower() == "id")
            i_v = next(
                i
                for i, b in enumerate(basliklar)
                if b.strip().lower() in ("sinif", "verdikt", "karar")
            )
        except StopIteration:
            raise SystemExit(
                f"HATA: id/verdikt kolonu yok. Basliklar: {basliklar}"
            ) from None
        return [s[i_id].strip() for s in okuyucu if s and s[i_v].strip() == "KABUL"]


SORGU_KAYNAK = text(
    "SELECT id::text AS id, question_text, option_a, option_b, option_c, "
    "option_d, option_e, correct_answer "
    "FROM question_bank WHERE id::text = ANY(:idler)"
)

# Canli DB SPLIT: metin ve siklar question_content'te, question_bank'ta DEGIL.
SORGU_CANLI = text(
    "SELECT qb.id::text AS id, qc.question_text, qc.option_a, qc.option_b, "
    "qc.option_c, qc.option_d, qc.option_e, qc.correct_answer "
    "FROM question_bank qb JOIN question_content qc ON qc.id = qb.id"
)


async def _satirlari_cek(db: str, sorgu, parametre: dict | None = None) -> list[dict]:
    motor = create_async_engine(f"{_kok()}/{db}", poolclass=NullPool)
    try:
        async with motor.connect() as baglanti:
            sonuc = await baglanti.execute(sorgu, parametre or {})
            return [dict(r._mapping) for r in sonuc.all()]
    finally:
        await motor.dispose()


def _kok() -> str:
    kok = os.environ.get("Y11_DSN_KOK", VARSAYILAN_KOK)
    if "sqlite" in kok.lower():
        raise SystemExit(
            "HATA: postgres olmayan DSN reddedildi (sessizce sqlite'a dusme)."
        )
    return kok.rstrip("/")


async def main() -> int:
    idler = kabul_idleri()
    print(f"TSV'den KABUL id            : {len(idler)}")
    if not idler:
        raise SystemExit("HATA: 0 KABUL id -- ayristirici bozuk (yanlis-sifir).")

    kaynak = await _satirlari_cek("kiro2_temp", SORGU_KAYNAK, {"idler": idler})
    print(f"kiro2_temp'ten cekilen satir: {len(kaynak)}")
    if len(kaynak) != len(idler):
        print(f"  UYARI: {len(idler) - len(kaynak)} id kaynakta BULUNAMADI")

    # --- 1) SET-ICI mukerrerler (siki kimlik: govde + 5 sik, sirasiyla) ---
    gruplar = mukerrer_gruplar(kaynak)
    set_ici_fazlalik: set[str] = set()
    for g in gruplar:
        set_ici_fazlalik.update(g[1:])  # her gruptan ILKI kalir
    print(f"\nSET-ICI  : {len(gruplar)} grup | {len(set_ici_fazlalik)} fazlalik satir")

    # --- 2) CAPRAZ-DB: canli DB'de ayni kimlikte satir var mi ---
    canli = await _satirlari_cek("kiro2", SORGU_CANLI)
    print(f"canli DB'den cekilen satir  : {len(canli)}")
    canli_kimlikler = {k for k in (siki_kimlik(s) for s in canli) if k}
    print(f"canli benzersiz kimlik      : {len(canli_kimlikler)}")

    capraz: set[str] = set()
    kimliksiz = 0
    for s in kaynak:
        k = siki_kimlik(s)
        if k is None:
            kimliksiz += 1
            continue
        if k in canli_kimlikler:
            capraz.add(s["id"])
    print(
        f"CAPRAZ-DB: {len(capraz)} satir"
        + (f"  (kimlik uretilemeyen: {kimliksiz})" if kimliksiz else "")
    )

    # --- 3) ORTUSME + TEK SAYI ---
    ortusme = set_ici_fazlalik & capraz
    birlesim = set_ici_fazlalik | capraz
    print("\n=== ORTUSME (devir notunun olculmemis sorusu) ===")
    print(f"  set-ici  KESISIM  capraz : {len(ortusme)}")
    print(f"  set-ici  BIRLESIM  capraz : {len(birlesim)}")
    print(
        f"  naif cikarma     : {len(kaynak)} - {len(set_ici_fazlalik)} - {len(capraz)}"
        f" = {len(kaynak) - len(set_ici_fazlalik) - len(capraz)}  <- ORTUSME KADAR YANLIS"
    )
    print(f"\n>>> GOC EDILECEK TEK SAYI : {len(kaynak) - len(birlesim)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
