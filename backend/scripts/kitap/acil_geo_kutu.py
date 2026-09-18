#!/usr/bin/env python
"""ACIL 2023-2024 TYT-AYT Geometri: soru kirpim kutularini SIMGEDEN turetir.

NEDEN SIMGEDEN
--------------
Bu kitapta okuyucu her sorunun soluna bir buyutec simgesi koyuyor. Faz 0'da
olculdu: simge sayisi soru sayisina esit (1881) ve her testin anahtar girdisi
sayisiyla birebir tutuyor. Sabit bir izgara varsaymak yerine kutular bu
simgelerden turetilir.

OLCULEN KURALLAR (bkz. GEO_ACIL_2324_KESIF.md, GEO_ACIL_2324_YONTEM.md)
----------------------------------------------------------------------
* Simge sutunlari TEK/CIFT sayfada 18 px kayiyor: tek gx 14/346, cift 32/361.
* Kutu ustu  = simge_y - 6
* Kutu alti  = ayni sutundaki bir SONRAKI simgenin y'si - 9; sonuncuysa
  sayfanin alt siniri.
* Sayfa alt siniri: cevap kutusu olan sayfada kutunun ustu - 4 (sizinti
  kapisi), olmayanda 902 (govde 899'a kadar iniyor, sayfa numarasi 917).
* Kutunun SOL kenari simgenin SAGINDAN baslar (gx + 24): disk okuyucunun
  kendi katmani, kitabin icerigi degil.
* Sol sutunun metni TAM gx_sag'da bitiyor, bu yuzden sol kutu gx_sag + 1'e
  kadar uzar. Yan etkisi sag simgenin diskinden ~10 px sizmasidir; disa
  aktarimda disk beyaza boyanir (disk 240,238,247 / glif 69,39,160).
* Sag sutunun sag kenari 706 (olculen en genis murekkep 688).
* TAM GENISLIK sayfa: sag sutunda hic simge yok ama govde ayiricinin sagina
  tasiyorsa sol kutu sayfanin tamamini kaplar (olculen tek ornek: s47).

KULLANIM
--------
    python backend/scripts/kitap/acil_geo_kutu.py            # uret + dogrula
    python backend/scripts/kitap/acil_geo_kutu.py --cikti X  # baska yol
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from itertools import pairwise
from pathlib import Path

import numpy as np
from PIL import Image

KLASOR_DESENI = "2023-2024-AC*TYT-AYT Geometri Soru Bank*"
KART = (593, 46, 1327, 1014)
ILK_SAYFA, SON_SAYFA = 5, 446
BEKLENEN_KUTU = 1881
SAG_KENAR = 706
KUTUSUZ_ALT = 902
SIMGE_GENISLIGI = 24
GLIF = np.array([69, 39, 160])
DISK = np.array([240, 238, 247])


def _murekkep(a: np.ndarray) -> np.ndarray:
    """Kitap murekkebi maskesi: koyu VE notr (renkli sekil dolgusu degil)."""
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    maske: np.ndarray = (mx < 170) & ((mx - mn) < 60)
    return maske


def _kart(yol: Path) -> np.ndarray:
    return np.asarray(Image.open(yol).convert("RGB")).astype(int)[
        KART[1] : KART[3], KART[0] : KART[2]
    ]


def kutulari_turet(kok: Path, yerler: dict, anahtar: dict) -> list[dict]:
    kutular: list[dict] = []
    for n in range(ILK_SAYFA, SON_SAYFA + 1):
        r = anahtar[n]
        alt_sinir = min(r["cerceve_ust"], r["y0"]) - 4 if r["var"] else KUTUSUZ_ALT
        sol = sorted([p for p in yerler[n] if p[0] < 180], key=lambda p: p[1])
        sag = sorted([p for p in yerler[n] if p[0] >= 180], key=lambda p: p[1])
        gx_sol = min((p[0] for p in sol), default=(14 if n % 2 else 32))
        gx_sag = min((p[0] for p in sag), default=(346 if n % 2 else 361))

        tam_genislik = False
        if not sag:
            mur = _murekkep(_kart(kok / f"sayfa_{n:04d}.png"))
            tam_genislik = bool(mur[130:850, 400:SAG_KENAR].sum() > 500)

        sol_x1 = SAG_KENAR if tam_genislik else gx_sag + 1
        for etiket, grup, x0, x1 in (
            ("sol", sol, gx_sol + SIMGE_GENISLIGI, sol_x1),
            ("sag", sag, gx_sag + SIMGE_GENISLIGI, SAG_KENAR),
        ):
            for i, (gx, gy) in enumerate(grup):
                alt = grup[i + 1][1] - 9 if i + 1 < len(grup) else alt_sinir
                kutular.append(
                    {
                        "sayfa": n,
                        "sutun": etiket,
                        "sira": i + 1,
                        "kirpim_kutusu": [x0, gy - 6, x1, alt],
                        "simge": [gx, gy],
                        "tam_genislik": tam_genislik,
                    }
                )
    return kutular


def dogrula(kok: Path, kutular: list[dict], anahtar: dict) -> list[str]:
    """Dort kapi. Hicbiri 'gecti' demek kutular DOGRU demek degildir; yalniz
    bilinen dort hata sinifinin olmadigini soyler (gozle ornekleme ayrica
    yapildi, bkz. YONTEM belgesi)."""
    hatalar = []
    if len(kutular) != BEKLENEN_KUTU:
        hatalar.append(f"KAPI1 sayi: {len(kutular)} != {BEKLENEN_KUTU}")

    sizinti = [
        b
        for b in kutular
        if anahtar[b["sayfa"]]["var"]
        and b["kirpim_kutusu"][3]
        >= min(anahtar[b["sayfa"]]["cerceve_ust"], anahtar[b["sayfa"]]["y0"])
    ]
    if sizinti:
        hatalar.append(f"KAPI2 cevap sizintisi: {len(sizinti)} kutu")

    g = defaultdict(list)
    for b in kutular:
        g[(b["sayfa"], b["sutun"])].append(b)
    ortusme = 0
    for v in g.values():
        v.sort(key=lambda b: b["kirpim_kutusu"][1])
        for a1, a2 in pairwise(v):
            if a1["kirpim_kutusu"][3] > a2["kirpim_kutusu"][1]:
                ortusme += 1
    kisa = sum(1 for b in kutular if b["kirpim_kutusu"][3] - b["kirpim_kutusu"][1] < 40)
    if ortusme or kisa:
        hatalar.append(f"KAPI3 ortusme {ortusme}, 40 px alti {kisa}")

    sayfa = defaultdict(list)
    for b in kutular:
        sayfa[b["sayfa"]].append(b)
    bos = 0
    for n in sorted(sayfa):
        mur = _murekkep(_kart(kok / f"sayfa_{n:04d}.png"))
        for b in sayfa[n]:
            x0, y0, x1, y1 = b["kirpim_kutusu"]
            if mur[y0:y1, x0:x1].sum() < 120:
                bos += 1
    if bos:
        hatalar.append(f"KAPI4 bos/zayif kutu: {bos}")
    return hatalar


def ana() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", default="veriseti/zkitap/screenshots")
    ap.add_argument("--yerler", default="backend/_geo1_gecici/faz0b.json")
    ap.add_argument("--anahtar-geo", default="backend/_geo1_gecici/k03b.json")
    ap.add_argument(
        "--cikti",
        default="veriseti/zkitap/cikti/acil_2324_geometri_kirpim_kutulari.json",
    )
    a = ap.parse_args()

    kok = sorted(Path(a.kok).glob(KLASOR_DESENI))
    if not kok:
        print(f"HATA: klasor bulunamadi: {KLASOR_DESENI}", file=sys.stderr)
        return 2
    yerler = {
        x["sayfa"]: x["yer"] for x in json.loads(Path(a.yerler).read_text("utf-8"))
    }
    anahtar = {
        x["sayfa"]: x for x in json.loads(Path(a.anahtar_geo).read_text("utf-8"))
    }

    kutular = kutulari_turet(kok[0], yerler, anahtar)
    hatalar = dogrula(kok[0], kutular, anahtar)
    for h in hatalar:
        print("HATA:", h, file=sys.stderr)
    if hatalar:
        return 1

    Path(a.cikti).write_text(
        json.dumps(
            {
                "kaynak": "ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi",
                "kirpim_koordinat_sistemi": "sayfa_karti_593_46_1327_1014",
                "kutu": len(kutular),
                "kutular": kutular,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"{len(kutular)} kutu yazildi -> {a.cikti}  (dort kapi da gecti)")
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
