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
GUTTER_OFSETI = 18
# Simge diskinin sayfa uzerindeki ayak izi (beyazlatmada da ayni degerler).
D_SOL, D_UST, D_ALT = 13, 14, 28
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
        sayfa_kutu: list[dict] = []
        r = anahtar[n]
        # Cevap kutusu SAYFANIN TAMAMINI degil, yalniz uzerine geldigi sutunu
        # sinirlar: olculdu, kutu x 377-393 ile 637-660 arasinda, yani SAG
        # sutunda. Ilk surum limiti iki sutuna da uyguladi ve s43 gibi
        # sayfalarda SOL sutunun sik satirini (y~892) kutunun disinda birakti.
        kutu_alt = min(r["cerceve_ust"], r["y0"]) - 4 if r["var"] else KUTUSUZ_ALT
        sol = sorted([p for p in yerler[n] if p[0] < 180], key=lambda p: p[1])
        sag = sorted([p for p in yerler[n] if p[0] >= 180], key=lambda p: p[1])
        gx_sol = min((p[0] for p in sol), default=(14 if n % 2 else 32))
        gx_sag = min((p[0] for p in sag), default=(346 if n % 2 else 361))

        mur = _murekkep(_kart(kok / f"sayfa_{n:04d}.png"))
        tam_genislik = bool(not sag and mur[130:850, 400:SAG_KENAR].sum() > 500)
        # Sol sutunun sag siniri OLUK'tur (iki sutun arasindaki bos serit).
        # Simgeler beyazlatildiktan sonra olculdu: oluk her sayfada
        # gx_sag + 18 ile gx_sag + 47 arasinda, tam 30 px. Yani sol sutunun
        # metni en fazla gx_sag + 17'ye kadar geliyor.
        #
        # Iki yanlis deneme belgeleniyor:
        #  * gx_sag + 1  -> 664 kirpimda son sik kesildi.
        #  * "ayirici cizgiyi dedektorle bul" -> cizgi HER SAYFADA YOK
        #    (s44, s53, s57'de 340-430 arasinda en uzun dikey kolon 10 px);
        #    dedektor s44'te bir seklin kenarina takilip siniri 329'a cekti
        #    ve E sikkini tamamen kesti.
        #  Ilk olcumlerin "metin gx_sag'da bitiyor" demesinin sebebi, simge
        #  diskinin pikselleri metin sanilmasiydi.
        sol_ust_sinir = SAG_KENAR if tam_genislik else gx_sag + GUTTER_OFSETI
        for etiket, grup, x0, ust_sinir in (
            ("sol", sol, gx_sol + SIMGE_GENISLIGI, sol_ust_sinir),
            ("sag", sag, gx_sag + SIMGE_GENISLIGI, SAG_KENAR),
        ):
            # Bu sutun cevap kutusuyla yatayda ortusuyor mu? (20 px'ten fazla)
            ortusme = r["var"] and min(ust_sinir, r["x1"]) - max(x0, r["x0"]) > 20
            alt_sinir = kutu_alt if ortusme else KUTUSUZ_ALT
            for i, (gx, gy) in enumerate(grup):
                y0 = gy - 6
                # Alt sinir: bir sonraki simgeye 2 px kalana kadar uzatilabilir;
                # 32 kirpimda murekkep alt kenara degiyordu (sik satiri kesikti).
                # -7: bir sonraki kutunun ustu (simge_y - 6) ile cakismasin
                alt_tavan = grup[i + 1][1] - 7 if i + 1 < len(grup) else alt_sinir
                pencere = mur[y0:alt_tavan, x0:ust_sinir]
                satir = np.nonzero(pencere.any(axis=1))[0]
                y1 = (
                    min(alt_tavan, y0 + int(satir.max()) + 7)
                    if len(satir)
                    else alt_tavan
                )
                # Sag sinir: icerige gore daralt, ayiriciya/sayfa kenarina dayanma.
                kolon = np.nonzero(mur[y0:y1, x0:ust_sinir].any(axis=0))[0]
                x1 = (
                    min(ust_sinir, x0 + int(kolon.max()) + 5)
                    if len(kolon)
                    else ust_sinir
                )
                sayfa_kutu.append(
                    {
                        "sayfa": n,
                        "sutun": etiket,
                        "sira": i + 1,
                        "kirpim_kutusu": [x0, y0, x1, y1],
                        "tavan": [ust_sinir, alt_tavan],
                        "simge": [gx, gy],
                        "tam_genislik": tam_genislik,
                        "ortulu": False,
                    }
                )

        # ORTME: sag sutun simgesinin diski, SOL sutundaki bir metin satirinin
        # uzerine biniyorsa o sorunun son sikki diskin altinda kaliyor. Disk
        # opak oldugu icin "disk icinde murekkep var mi" diye bakmak bunu
        # bulamaz (Faz 0'daki K0.4 bu yuzden yanlisti); dogru olcum "satir
        # diskin SOLUNDA bitiyor mu".
        # Sahip karari: bu sorular islenmez, disarida birakilir.
        H = mur.shape[0]
        for gx, gy in sag:
            y0 = max(0, gy - D_UST)
            y1 = min(H, gy + D_ALT)
            x1 = max(0, gx - D_SOL)
            x0 = max(0, x1 - 6)
            if x1 <= x0 or mur[y0:y1, x0:x1].sum() < 4:
                continue
            for b in sayfa_kutu:
                if b["sutun"] != "sol":
                    continue
                if b["kirpim_kutusu"][1] <= gy <= b["kirpim_kutusu"][3]:
                    b["ortulu"] = True
                    break
        kutular.extend(sayfa_kutu)
    return kutular


def _kapi1(kutular: list[dict]) -> str | None:
    if len(kutular) != BEKLENEN_KUTU:
        return f"KAPI1 sayi: {len(kutular)} != {BEKLENEN_KUTU}"
    return None


def _kapi2(kutular: list[dict], anahtar: dict) -> str | None:
    """Kirpim cevap kutusuna giriyor mu? Yalniz kutuyla YATAYDA ortusen
    sutunlar icin anlamli: cevap kutusu sag sutunun altinda duruyor, sol
    sutunun icerigi onun hizasinda asagi devam edebiliyor."""
    n = 0
    for b in kutular:
        r = anahtar[b["sayfa"]]
        if not r["var"]:
            continue
        x0, _, x1, y1 = b["kirpim_kutusu"]
        if min(x1, r["x1"]) - max(x0, r["x0"]) <= 20:
            continue
        if y1 >= min(r["cerceve_ust"], r["y0"]):
            n += 1
    return f"KAPI2 cevap sizintisi: {n} kutu" if n else None


def _kapi3(kutular: list[dict]) -> str | None:
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
        return f"KAPI3 ortusme {ortusme}, 40 px alti {kisa}"
    return None


def _kapi45(kok: Path, sayfa: dict) -> list[str]:
    """KAPI4 (bos kutu) ve KAPI5 (kutu disinda kalan icerik).

    KAPI5 ilk surumde YOKTU; 664 kirpimda son sik kesilmisti ve dort kapi da
    yesildi. Dogru soru "kenarda murekkep var mi" degil -- icerik oluga kadar
    gidebiliyor -- "kutunun DISINDA ama ayni sutunun icinde murekkep kaldi mi".
    """
    bos = kesik_sag = kesik_alt = 0
    for n in sorted(sayfa):
        mur = _murekkep(_kart(kok / f"sayfa_{n:04d}.png"))
        for b in sayfa[n]:
            x0, y0, x1, y1 = b["kirpim_kutusu"]
            tx, ty = b["tavan"]
            if mur[y0:y1, x0:x1].sum() < 120:
                bos += 1
            if x1 < tx and mur[y0:y1, x1:tx].sum() >= 6:
                kesik_sag += 1
            if y1 < ty and mur[y1:ty, x0:x1].sum() >= 6:
                kesik_alt += 1
    h = []
    if bos:
        h.append(f"KAPI4 bos/zayif kutu: {bos}")
    if kesik_sag or kesik_alt:
        h.append(f"KAPI5 kutu disinda kalan icerik: sag {kesik_sag}, alt {kesik_alt}")
    return h


def dogrula(kok: Path, kutular: list[dict], anahtar: dict) -> list[str]:
    """Bes kapi. Hicbiri 'gecti' demek kutular DOGRU demek degildir; yalniz
    bilinen bes hata sinifinin olmadigini soyler (gozle ornekleme ayrica
    yapildi, bkz. YONTEM belgesi)."""
    sayfa = defaultdict(list)
    for b in kutular:
        sayfa[b["sayfa"]].append(b)
    hatalar = [
        h for h in (_kapi1(kutular), _kapi2(kutular, anahtar), _kapi3(kutular)) if h
    ]
    hatalar.extend(_kapi45(kok, sayfa))
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
                "ortulu": sum(1 for b in kutular if b["ortulu"]),
                "islenecek": sum(1 for b in kutular if not b["ortulu"]),
                "kutular": kutular,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    ort = sum(1 for b in kutular if b["ortulu"])
    print(
        f"{len(kutular)} kutu yazildi -> {a.cikti}  (bes kapi da gecti); "
        f"ortulu {ort}, islenecek {len(kutular) - ort}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
