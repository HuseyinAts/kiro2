#!/usr/bin/env python
"""Y11 FAZ C — 50 satırlık pilot örneklemini ÖLÇEREK seçer (salt okunur).

Rastgele 50 satır kör nokta bırakır (`L-s219-test-paketi-dilim-olcer`): göçün
riskli davranışları azınlıkta. Bu seçici her riski en az bir kez örnekleme
sokar ve **deterministiktir** (id'ye göre sıralı seçim; `random` yok).

KOTALAR — plandan, ama ölçülerek düzeltildi
--------------------------------------------
| kota | plan | ölçüm (KABUL 3.666) |
|---|---|---|
| remap gereken (kaynak id != canlı id) | >=5 | aşağıda hesaplanır |
| kapıdan elenecek (`match_tier` page_inline) | >=3 | 274 (178 + 96) |
| set-içi mükerrer grubundan | >=2 | 16 grup / 16 fazlalık (SIKI) |
| çapraz-DB mükerrer | >=1 | aşağıda hesaplanır |
| ~~`created_by` yetimi~~ | ~~>=1~~ | **0 — KOTA DÜŞTÜ** |

`created_by` kotası **karşılanamaz**: KABUL kümesinde 3.666/3.666 satırda
`created_by IS NULL` (ölçüldü). Plandaki "65 yetim FK" rakamı **4.419'luk tam
küme** içindi; KABUL'e giren alt kümede yetim kalmamış. Dönüşüm zaten koşulsuz
`None` bastığı için bu kotanın koruduğu davranış (yetim FK'yi geçirme) test
tarafında sentetik olarak çivili — örneklemde temsil edilmesi gerekmiyor.

Kullanım:
    python backend/scripts/quality/y11_pilot_ornek.py --cikti C:/tmp/y11_pilot50.txt
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from y11_dedup import mukerrer_gruplar, siki_kimlik
from y11_yukleyici import dsn_coz, json_kodegi_kaydet

TSV = Path(__file__).resolve().parent / "y11_kimya_verdikt_TAM.tsv"
KAPI_DISI_TIER = ("tier1_page_inline", "tier1b_position_page_inline")
HEDEF_BOYUT = 50


def kabul_idleri() -> list[str]:
    with TSV.open(encoding="utf-8", newline="") as f:
        okuyucu = csv.reader(f, delimiter="\t")
        basliklar = next(okuyucu)
        i_id = basliklar.index("id")
        i_sinif = basliklar.index("sinif")
        return [s[i_id].strip() for s in okuyucu if s and s[i_sinif].strip() == "KABUL"]


def siniflandir(
    satirlar: list[dict[str, Any]],
    harita: dict[str, str],
    canli_kimlikler: set[str],
) -> dict[str, list[str]]:
    """Her satiri ait oldugu risk sinif(lar)ina yazar (bir satir birden fazla
    sinifta olabilir). Siralama `id`'ye gore SABIT: ayni girdi ayni ornegi verir.
    """
    grup_uyeleri = {i for g in mukerrer_gruplar(satirlar) for i in g}
    kimlik_ile = {s["id"]: siki_kimlik(s) for s in satirlar}
    sinif: dict[str, list[str]] = defaultdict(list)
    for s in sorted(satirlar, key=lambda r: str(r["id"])):
        sid = s["id"]
        url = s["question_image_url"]
        # `bool(...)`: sozlukler `dict[str, Any]`, karsilastirma mypy'a `Any`
        # gorunuyor (no-any-return).
        if bool(harita.get(s["topic_code"]) != s["primary_topic_id"]):
            sinif["remap"].append(sid)
        if s["match_tier"] in KAPI_DISI_TIER:
            sinif["kapi_disi"].append(sid)
        if sid in grup_uyeleri:
            sinif["mukerrer"].append(sid)
        if kimlik_ile[sid] in canli_kimlikler:
            sinif["capraz_db"].append(sid)
        if url:
            sinif["gorsel_PAGE" if "_PAGE" in url else "gorsel_crop"].append(sid)
    return sinif


async def main() -> int:
    import asyncpg

    ap = argparse.ArgumentParser()
    ap.add_argument("--cikti", type=Path, required=True)
    a = ap.parse_args()

    idler = kabul_idleri()
    print(f"KABUL id: {len(idler)}")

    kaynak = await asyncpg.connect(dsn_coz("kiro2_temp"))
    canli = await asyncpg.connect(dsn_coz("kiro2"))
    try:
        await json_kodegi_kaydet(kaynak)
        satirlar = [
            dict(s)
            for s in await kaynak.fetch(
                "SELECT q.id, q.question_text, q.option_a, q.option_b, q.option_c, "
                "q.option_d, q.option_e, q.primary_topic_id, q.question_image_url, "
                "q.source_book, q.pipeline_metadata->>'match_tier' AS match_tier, "
                "t.code AS topic_code "
                "FROM question_bank q "
                "JOIN topic_hierarchy t ON t.id = q.primary_topic_id "
                "WHERE q.id = ANY($1::text[])",
                idler,
            )
        ]
        harita = {
            s["code"]: s["id"]
            for s in await canli.fetch("SELECT code, id FROM topic_hierarchy")
        }
        canli_kimlikler = set()
        for s in await canli.fetch(
            "SELECT id, question_text, option_a, option_b, option_c, option_d, option_e "
            "FROM question_content"
        ):
            k = siki_kimlik(dict(s))
            if k:
                canli_kimlikler.add(k)
    finally:
        await kaynak.close()
        await canli.close()

    print(
        f"kaynaktan cekilen: {len(satirlar)}  |  canli kimlik: {len(canli_kimlikler)}"
    )
    if len(satirlar) != len(idler):
        raise SystemExit(f"HATA: {len(idler)} istendi, {len(satirlar)} geldi.")

    sinif = siniflandir(satirlar, harita, canli_kimlikler)

    print("\n=== SINIF BUYUKLUKLERI (KABUL evreni) ===")
    for ad, uyeler in sorted(sinif.items()):
        print(f"  {ad:14s}: {len(uyeler)}")

    # --- kotalari doldur ----------------------------------------------------
    kotalar = {
        "remap": 5,
        "kapi_disi": 3,
        "mukerrer": 2,
        "capraz_db": 1,
        "gorsel_PAGE": 2,
        "gorsel_crop": 2,
    }
    secim: list[str] = []
    karsilanmayan: dict[str, int] = {}
    for ad, adet in kotalar.items():
        havuz = [i for i in sinif[ad] if i not in secim]
        if len(havuz) < adet:
            karsilanmayan[ad] = adet - len(havuz)
        secim.extend(havuz[:adet])

    # kalanı deterministik doldur
    for s in sorted(satirlar, key=lambda r: r["id"]):
        if len(secim) >= HEDEF_BOYUT:
            break
        if s["id"] not in secim:
            secim.append(s["id"])

    print("\n=== ORNEKLEM ===")
    for ad, adet in kotalar.items():
        var = sum(1 for i in secim if i in sinif[ad])
        isaret = "OK " if var >= adet else "EKSIK"
        print(f"  {isaret} {ad:14s} kota>={adet}  orneklemde={var}")
    if karsilanmayan:
        print(f"  UYARI karsilanmayan kotalar: {karsilanmayan}")
    print(f"  toplam: {len(secim)}")

    a.cikti.write_text("\n".join(secim), encoding="utf-8", newline="\n")
    print(f"\nyazildi: {a.cikti}")

    ozet = {ad: sum(1 for i in secim if i in sinif[ad]) for ad in sinif}
    print("orneklem sinif dagilimi: " + json.dumps(ozet, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
