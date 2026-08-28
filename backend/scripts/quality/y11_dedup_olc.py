#!/usr/bin/env python
"""Dedup modulunu GERCEK KABUL kumesine karsi olcer (kontrol kolu, salt okunur).

S233 olcum turu bagimsiz olarak sunu raporladi:
    3.666 KABUL -> 3.588 benzersiz metin  (78 satir / 73 grup, siki)
    gevsek normalizasyonda              -> 281 satir / 137 grup

Bu script `y11_dedup.py`'nin AYNI sayilari uretip uretmedigini olcer.
Uretmiyorsa modul ya da o olcum yanlis -- ikisi birden dogru olamaz.

Kullanim:
    KVKK_VERIFY_DSN=postgresql://... python backend/scripts/quality/y11_dedup_olc.py
"""

from __future__ import annotations

import asyncio
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from y11_dedup import gevsek_kimlik, mukerrer_gruplar

TSV = Path(__file__).resolve().parent / "y11_kimya_verdikt_TAM.tsv"


def kabul_idleri() -> list[str]:
    """TSV'den verdikti KABUL olan id'ler. Kolon adi tahmin EDILMEZ, baslik okunur."""
    with TSV.open(encoding="utf-8", newline="") as f:
        okuyucu = csv.reader(f, delimiter="\t")
        basliklar = next(okuyucu)
        # id ve verdikt kolonlarini basliktan bul; bulunamazsa GURULTULU dur.
        try:
            i_id = next(i for i, b in enumerate(basliklar) if b.strip().lower() == "id")
        except StopIteration:
            raise SystemExit(f"HATA: 'id' kolonu yok. Basliklar: {basliklar}") from None
        i_v = next(
            (
                i
                for i, b in enumerate(basliklar)
                if b.strip().lower() in ("sinif", "verdikt", "karar")
            ),
            None,
        )
        if i_v is None:
            raise SystemExit(f"HATA: verdikt kolonu yok. Basliklar: {basliklar}")
        return [s[i_id].strip() for s in okuyucu if s and s[i_v].strip() == "KABUL"]


async def main() -> int:
    dsn = os.environ.get("KVKK_VERIFY_DSN") or os.environ.get("DATABASE_URL_SYNC")
    if not dsn or "sqlite" in dsn.lower():
        raise SystemExit("HATA: gercek postgres DSN yok (KVKK_VERIFY_DSN).")
    for onek in ("postgresql+psycopg2://", "postgresql://"):
        if dsn.startswith(onek):
            dsn = dsn.replace(onek, "postgresql+asyncpg://", 1)
            break
    # Kaynak KIMYA icerigi kiro2_temp'te; canli DB'de degil.
    dsn = dsn.rsplit("/", 1)[0] + "/kiro2_temp"

    idler = kabul_idleri()
    print(f"TSV'den KABUL id: {len(idler)}")
    if not idler:
        raise SystemExit("HATA: 0 KABUL id -- ayristirici bozuk (yanlis-sifir).")

    motor = create_async_engine(dsn, poolclass=NullPool)
    try:
        async with motor.connect() as baglanti:
            satirlar = [
                dict(r._mapping)
                for r in (
                    await baglanti.execute(
                        text(
                            "SELECT id::text AS id, question_text, "
                            "option_a, option_b, option_c, option_d, option_e, "
                            "correct_answer FROM question_bank "
                            "WHERE id::text = ANY(:idler)"
                        ),
                        {"idler": idler},
                    )
                ).all()
            ]
    finally:
        await motor.dispose()

    print(f"DB'den cekilen satir: {len(satirlar)}")
    if len(satirlar) != len(idler):
        print(f"  UYARI: {len(idler) - len(satirlar)} id kaynakta BULUNAMADI")

    for ad, kimlik in (("SIKI", None), ("GEVSEK", gevsek_kimlik)):
        gruplar = (
            mukerrer_gruplar(satirlar)
            if kimlik is None
            else mukerrer_gruplar(satirlar, kimlik=kimlik)
        )
        fazlalik = sum(len(g) - 1 for g in gruplar)
        print(
            f"{ad:7s}: {len(gruplar)} grup | {fazlalik} fazlalik satir | "
            f"benzersiz {len(satirlar) - fazlalik}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
