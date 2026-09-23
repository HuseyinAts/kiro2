#!/usr/bin/env python
"""Orijinal 2024 Geometri: transkripsiyon harness'i (hazirla / topla / kapi).

NE ISE YARAR
------------
Transkripsiyon bu depoda bir OKUMA isidir: sayfa goruntusu okunur, kitapta ne
yaziyorsa o yazilir. Bu script okumayi yapmaz; okumanin ETRAFINI kurar:

  hazirla : sayfa kartlarini (593,46)+734x968 okunabilir bir dizine cikarir ve
            okuyucu GRUPLARINI birim sinirina hizali olarak tanimlar.
  topla   : gruplardan donen JSON parcalarini tek dosyada birlestirir.
  kapi    : birlesik ciktiyi YAPISAL olcumle karsilastirir.

KAPILAR (okuyucuya SOYLENMEYEN, bagimsiz olculmus yapidan gelir)
----------------------------------------------------------------
1. Her (sayfa, sutun) icin okunan soru sayisi == kirpim kutusu sayisi.
   Kutular okuyucu simgesinden turetildi; okuyucuya sayilar verilmez.
2. Her birimde BASILI soru numaralari 1..N kesintisiz ve okuma sirasina
   (once SOL sutun yukaridan asagiya, sonra SAG) gore artan olmali.
3. Her soruda bes sik (A-E) bos olmayan metin tasimali.
4. Toplam soru sayisi 2072.

Bu kapilarin hicbiri cevap anahtarina bakmaz: anahtar AYRI bir kanaldir
(bkz. GEO_ORIJINAL_2024_FAZ1.md bolum 16) ve transkripsiyon onu gormez.

KULLANIM
--------
    python backend/scripts/kitap/orijinal_geo_metin_harness.py hazirla
    python backend/scripts/kitap/orijinal_geo_metin_harness.py topla
    python backend/scripts/kitap/orijinal_geo_metin_harness.py kapi
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KUTULAR = CIKTI / "orijinal_2024_geometri_kirpim_kutulari.json"
BIRIMLER = CIKTI / "orijinal_2024_geometri_birim_haritasi.json"
HEDEF = CIKTI / "orijinal_2024_geometri_metin.json"

KART = (593, 46, 593 + 734, 46 + 968)
BEKLENEN_BOYUT = (1920, 1080)
BEKLENEN_SORU = 2072
# Okunabilir dizin: filesystem MCP yalniz bu koke izin veriyor.
OKUMA_KOKU = Path(r"C:\Users\husey\VeraFilm\_kiro2_gecici_okuma")
SAYFA_DIZINI = OKUMA_KOKU / "orj24_sayfa"
PARCA_DIZINI = Path(r"C:\Users\husey\_orj24_metin_parca")
GRUP_SAYFA = 14  # grup basina hedef sayfa sayisi (birim sinirina yuvarlanir)


def _kaynak_dizin() -> Path:
    adaylar = sorted(
        (KOK / "veriseti" / "zkitap" / "screenshots").glob(
            "Orijinal-2024-Geometri Soru Bank*"
        )
    )
    if len(adaylar) != 1:
        raise SystemExit(f"Kaynak dizin tek degil: {[a.name for a in adaylar]}")
    return adaylar[0]


def yapisal_sayim() -> dict[tuple[int, str], int]:
    kutular = json.loads(KUTULAR.read_text("ascii"))["kutular"]
    sayim: dict[tuple[int, str], int] = {}
    for k in kutular:
        sayim[(k["sayfa"], k["sutun"])] = sayim.get((k["sayfa"], k["sutun"]), 0) + 1
    return sayim


def gruplar() -> list[dict]:
    """Birim sinirina hizali okuyucu gruplari."""
    birim = json.loads(BIRIMLER.read_text("ascii"))["birimler"]
    grup: list[dict] = []
    simdi: list[dict] = []
    for b in birim:
        simdi.append(b)
        bas = simdi[0]["bas_sayfa"]
        son = simdi[-1]["son_sayfa"]
        if son - bas + 1 >= GRUP_SAYFA:
            grup.append({"no": len(grup) + 1, "bas": bas, "son": son})
            simdi = []
    if simdi:
        grup.append(
            {
                "no": len(grup) + 1,
                "bas": simdi[0]["bas_sayfa"],
                "son": simdi[-1]["son_sayfa"],
            }
        )
    return grup


def hazirla() -> None:
    from PIL import Image

    kaynak = _kaynak_dizin()
    SAYFA_DIZINI.mkdir(parents=True, exist_ok=True)
    PARCA_DIZINI.mkdir(parents=True, exist_ok=True)
    sayim = yapisal_sayim()
    sayfalar = sorted({s for s, _ in sayim})
    for s in sayfalar:
        img = Image.open(kaynak / f"sayfa_{s:04d}.png").convert("RGB")
        if img.size != BEKLENEN_BOYUT:
            raise SystemExit(f"BOYUT UYUSMAZLIGI s{s}: {img.size}")
        img.crop(KART).save(SAYFA_DIZINI / f"sayfa_{s:04d}.png")
    g = gruplar()
    print(f"sayfa karti yazildi: {len(sayfalar)} -> {SAYFA_DIZINI}")
    print(f"grup sayisi: {len(g)} (hedef {GRUP_SAYFA} sayfa/grup)")
    for x in g:
        n = sum(v for (p, _), v in sayim.items() if x["bas"] <= p <= x["son"])
        print(
            f"  grup {x['no']:2d}: s{x['bas']}-{x['son']}  ({x['son'] - x['bas'] + 1} sayfa, {n} soru)"
        )


def topla() -> None:
    parca = sorted(PARCA_DIZINI.glob("grup_*.json"))
    sorular: list[dict] = []
    for p in parca:
        sorular.extend(json.loads(p.read_text("utf-8"))["sorular"])
    for s in sorular:
        if isinstance(s.get("basili_no"), str):
            s["basili_no"] = int(s["basili_no"].strip().rstrip("."))
    sorular.sort(key=lambda s: (s["sayfa"], s["sutun"] == "sag", s["sira"]))
    HEDEF.write_text(
        json.dumps(
            {
                "kaynak": "Orijinal 2024 TYT-AYT Geometri Soru Bankasi",
                "nereden": (
                    "FERNUS okuyucu sayfa kartindan okundu. Sorular cozulmedi, "
                    "cevap anahtari okuyucuya gosterilmedi."
                ),
                "parca_sayisi": len(parca),
                "soru_sayisi": len(sorular),
                "sorular": sorular,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"{len(parca)} parca -> {len(sorular)} soru -> {HEDEF}")


def _kapi1(okunan: dict, sayim: dict) -> list[str]:
    """Okunan soru sayisi, kutu sayisina esit olmali (sutun bazinda)."""
    hata = []
    for anahtar, adet in sayim.items():
        var = len(okunan.get(anahtar, []))
        if var != adet:
            hata.append(
                f"KAPI1 s{anahtar[0]} {anahtar[1]}: okunan {var} != kutu {adet}"
            )
    for anahtar in okunan:
        if anahtar not in sayim:
            hata.append(f"KAPI1 s{anahtar[0]} {anahtar[1]}: kutusu olmayan sutun")
    return hata


def _kapi2(okunan: dict) -> list[str]:
    """Birim icinde basili numaralar okuma sirasina gore 1..N olmali."""
    hata = []
    for b in json.loads(BIRIMLER.read_text("ascii"))["birimler"]:
        dizi = []
        for p in range(b["bas_sayfa"], b["son_sayfa"] + 1):
            for sut in ("sol", "sag"):
                dizi += [
                    s.get("basili_no")
                    for s in sorted(okunan.get((p, sut), []), key=lambda x: x["sira"])
                ]
        if dizi != list(range(1, len(dizi) + 1)):
            hata.append(f"KAPI2 {b['kod']}: basili numaralar 1..N degil -> {dizi}")
    return hata


def _kapi3(sorular: list[dict]) -> list[str]:
    """Bes sik da bos olmayan metin tasimali."""
    hata = []
    for s in sorular:
        for h in "ABCDE":
            if not str(s.get("sikler", {}).get(h, "")).strip():
                hata.append(
                    f"KAPI3 s{s['sayfa']} {s['sutun']} {s['sira']}: {h} sikki bos"
                )
    return hata


def kapi() -> list[str]:
    sorular = json.loads(HEDEF.read_text("utf-8"))["sorular"]
    okunan: dict[tuple[int, str], list[dict]] = {}
    for s in sorular:
        okunan.setdefault((s["sayfa"], s["sutun"]), []).append(s)
    hata = _kapi1(okunan, yapisal_sayim()) + _kapi2(okunan) + _kapi3(sorular)
    if len(sorular) != BEKLENEN_SORU:
        hata.append(f"KAPI4 toplam soru {len(sorular)} != {BEKLENEN_SORU}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("eylem", choices=["hazirla", "topla", "kapi"])
    args = ap.parse_args()
    if args.eylem == "hazirla":
        hazirla()
    elif args.eylem == "topla":
        topla()
    else:
        hata = kapi()
        print(f"kapi ihlali: {len(hata)}")
        for h in hata[:40]:
            print("   ", h)
        if hata:
            raise SystemExit(1)
        print("TUM KAPILAR YESIL")


if __name__ == "__main__":
    main()
