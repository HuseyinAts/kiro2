#!/usr/bin/env python
"""ACIL 2025 KURS Geometri: transkripsiyon harness'i (hazirla / topla / kapi).

Transkripsiyon bir OKUMA isidir: kirpim goruntusu okunur, kitapta ne yaziyorsa
o yazilir; soru cozulmez, cevap anahtari okuyucuya gosterilmez. Bu script
okumayi yapmaz, etrafini kurar:

  hazirla : kirpimlari okunabilir dizine kopyalar, birim sinirina hizali
            okuyucu gruplarini ve grup basina dosya listesini yazar.
  topla   : gruplardan donen JSON parcalarini tek dosyada birlestirir.
  kapi    : birlesik ciktiyi BAGIMSIZ yapisal olcumle karsilastirir.

KAPILAR (okuyucuya SOYLENMEYEN yapidan)
---------------------------------------
1. Her kirpim tam bir kez okunmus olmali (1948 dosya, eksik/fazla yok).
2. Okunan BASILI numara == birim ici sira. Kirpim kutulari basili numara
   blob'larindan turetildigi icin bu kapi capalarin dogru blob'a oturdugunu
   ayrica dogrular (yanlis blob -> yanlis numara ya da bos kirpim).
3. Her soruda bes sik (A-E) bos olmayan metin tasimali.
4. Toplam soru sayisi 1948.

KULLANIM
--------
    python backend/scripts/kitap/acil25_geo_metin_harness.py hazirla
    python backend/scripts/kitap/acil25_geo_metin_harness.py topla
    python backend/scripts/kitap/acil25_geo_metin_harness.py kapi
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KUTULAR = CIKTI / "acil_2025_geometri_kirpim_kutulari.json"
BIRIMLER = CIKTI / "acil_2025_geometri_birim_haritasi.json"
HEDEF = CIKTI / "acil_2025_geometri_metin.json"
KIRPIM = KOK / "backend" / "_geo1_gecici" / "a25_kirpim"
OKUMA_KOKU = Path(r"C:\Users\husey\VeraFilm\a25_okuma_kirpim")
PARCA_DIZINI = Path(r"C:\Users\husey\VeraFilm\a25_metin_parca")
BEKLENEN_SORU = 1948
GRUP_SORU = 60
OLCEK = 2
SIK_OKUNAMADI = "[okunamad\u0131]"  # "[okunamadi]" -- noktasiz i, kaynak ASCII kalsin


def _ad(birim: str, soru: int) -> str:
    return f"{birim}_{soru:02d}"


def gruplar() -> list[dict]:
    """Birim sinirina hizali okuyucu gruplari (~GRUP_SORU soru)."""
    birim = json.loads(BIRIMLER.read_text("utf-8"))["birimler"]
    out: list[dict] = []
    simdi: list[str] = []
    for b in birim:
        simdi += [_ad(b["kod"], i + 1) for i in range(b["soru_sayisi"])]
        if len(simdi) >= GRUP_SORU:
            out.append({"no": len(out) + 1, "dosyalar": simdi})
            simdi = []
    if simdi:
        out.append({"no": len(out) + 1, "dosyalar": simdi})
    return out


def hazirla() -> None:
    """Okuma kopyalari 2x Lanczos: kaynak ekran goruntusunde eksi isareti ve
    kesir cizgisi 1 px; pilot okumada (grup 32) 'soluk' diye isaretlendi."""
    from PIL import Image

    OKUMA_KOKU.mkdir(parents=True, exist_ok=True)
    PARCA_DIZINI.mkdir(parents=True, exist_ok=True)
    g = gruplar()
    n = 0
    for x in g:
        for ad in x["dosyalar"]:
            im = Image.open(KIRPIM / f"{ad}.png")
            im.resize((im.width * OLCEK, im.height * OLCEK), Image.LANCZOS).save(
                OKUMA_KOKU / f"{ad}.png"
            )
            n += 1
        (PARCA_DIZINI / f"liste_{x['no']:02d}.txt").write_text(
            "\n".join(x["dosyalar"]) + "\n", encoding="ascii"
        )
    print(f"kirpim kopyalandi: {n} -> {OKUMA_KOKU}")
    print(f"grup sayisi: {len(g)}")
    for x in g:
        print(
            f"  grup {x['no']:2d}: {len(x['dosyalar'])} soru  {x['dosyalar'][0]} .. {x['dosyalar'][-1]}"
        )


def topla() -> None:
    """Parcalari birlestirir.

    DUZELTME OKUMASI: ilk 8 grup, kutu ustu kurali duzeltilmeden ONCEKI
    kirpimlardan okundu; o gruplarda okuyucunun kaynak kusuru isaretledigi 38
    soru yeni kirpimdan AYRI bir okuyucuyla yeniden okundu (duzeltme.json) ve
    onlarin yerine gecer. 32/38 birebir ayni cikti; farklarin 3'u E sikkinda
    ilk okuyucunun yari gorunen rakami TAHMIN etmesi (ikinci okuyucu bos
    birakti), 3'u govdede tek karakter.

    OKUNAMAYAN SIK: okuyucu sikki bos biraktiysa VE kaynak kusuru yazdiysa sik
    SIK_OKUNAMADI isaretini alir; sessiz bos sik KAPI3'e takilir.
    """
    parca = sorted(PARCA_DIZINI.glob("grup_*.json"))
    sorular: list[dict] = []
    for p in parca:
        for s in json.loads(p.read_text("utf-8"))["sorular"]:
            s["okuma"] = p.stem
            sorular.append(s)
    duz_yolu = PARCA_DIZINI / "duzeltme.json"
    duzeltme = {}
    if duz_yolu.exists():
        duzeltme = {
            s["dosya"]: s for s in json.loads(duz_yolu.read_text("utf-8"))["sorular"]
        }
    for i, s in enumerate(sorular):
        if s["dosya"] in duzeltme:
            yeni = dict(duzeltme[s["dosya"]])
            yeni["okuma"] = f"duzeltme ({s['okuma']} yerine, yeni kirpim)"
            sorular[i] = yeni
    for s in sorular:
        if isinstance(s.get("basili_no"), str):
            s["basili_no"] = int(s["basili_no"].strip().rstrip("."))
        if s.get("kaynak_kusuru"):
            for h in "ABCDE":
                if not str(s["sikler"].get(h, "")).strip():
                    s["sikler"][h] = SIK_OKUNAMADI
    sorular.sort(key=lambda s: s["dosya"])
    HEDEF.write_text(
        json.dumps(
            {
                "kaynak": "ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi",
                "nereden": (
                    "Soru kirpimlarindan okundu (acil25_geo_kirp.py). Sorular "
                    "cozulmedi, cevap anahtari okuyucuya gosterilmedi."
                ),
                "parca_sayisi": len(parca),
                "soru_sayisi": len(sorular),
                "sorular": sorular,
            },
            ensure_ascii=True,
            indent=1,
        )
        + "\n",
        encoding="ascii",
        newline="\n",
    )
    print(f"{len(parca)} parca -> {len(sorular)} soru -> {HEDEF}")


def kapi(sorular: list[dict] | None = None) -> list[str]:
    if sorular is None:
        sorular = json.loads(HEDEF.read_text("ascii"))["sorular"]
    hata = []
    beklenen = [ad for g in gruplar() for ad in g["dosyalar"]]
    okunan: dict[str, dict] = {}
    for s in sorular:
        if s["dosya"] in okunan:
            hata.append(f"KAPI1 {s['dosya']}: iki kez okunmus")
        okunan[s["dosya"]] = s
    for ad in beklenen:
        if ad not in okunan:
            hata.append(f"KAPI1 {ad}: okunmamis")
    for ad in okunan:
        if ad not in set(beklenen):
            hata.append(f"KAPI1 {ad}: kirpimi olmayan kayit")
    for ad, s in okunan.items():
        sira = int(ad.rsplit("_", 1)[1])
        if s.get("basili_no") != sira:
            hata.append(
                f"KAPI2 {ad}: basili no {s.get('basili_no')} != birim ici sira {sira}"
            )
        for h in "ABCDE":
            if not str((s.get("sikler") or {}).get(h, "")).strip():
                hata.append(f"KAPI3 {ad}: {h} sikki bos")
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
