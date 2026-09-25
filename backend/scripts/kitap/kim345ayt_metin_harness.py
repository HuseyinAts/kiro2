#!/usr/bin/env python
"""345 2025 AYT Kimya: transkripsiyon harness'i (hazirla / topla / kapi).

Transkripsiyon bir OKUMA isidir: kirpim goruntusu okunur, kitapta ne yaziyorsa
o yazilir; soru cozulmez, cevap anahtari okuyucuya gosterilmez. Bu script
okumayi yapmaz, etrafini kurar (acil25_geo_metin_harness.py deseni):

  hazirla : kirpimlari 2x buyutup okuma dizinine kopyalar, test sinirina
            hizali okuyucu gruplarini ve grup basina dosya listesini yazar.
  topla   : gruplardan donen JSON parcalarini tek dosyada birlestirir.
  kapi    : birlesik ciktiyi BAGIMSIZ yapisal olcumle karsilastirir.

KAPILAR (okuyucuya SOYLENMEYEN yapidan)
---------------------------------------
1. Her kirpim tam bir kez okunmus olmali (1304 dosya, eksik/fazla yok).
2. Okunan BASILI numara == test ici sira (kitabin cevap satiri
   numaralandirmasi). Tek istisna: numarasi okuyucu diskinin ALTINDA kalan
   kutular (`numarasi_ortulu`: capasi basili numaradan alinmayanlar --
   simge / birlesik / simge_alt -- ya da diskin
   numaranin ilk rakamini ortugu olculenler); orada okuyucu null yazabilir,
   sayi yazarsa yine esit olmali.
3. Her soruda bes sik (A-E) bos olmayan metin tasimali.
4. Toplam soru sayisi 1304.

KULLANIM
--------
    python backend/scripts/kitap/kim345ayt_metin_harness.py hazirla
    python backend/scripts/kitap/kim345ayt_metin_harness.py topla
    python backend/scripts/kitap/kim345ayt_metin_harness.py kapi
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KUTULAR = CIKTI / "345_2025_ayt_kimya_kirpim_kutulari.json"
HEDEF = CIKTI / "345_2025_ayt_kimya_metin.json"
KIRPIM = KOK / "backend" / "_k345_gecici" / "k_kirpim"
OKUMA_KOKU = Path(r"C:\Users\husey\VeraFilm\k_okuma_kirpim")
PARCA_DIZINI = Path(r"C:\Users\husey\VeraFilm\k_metin_parca")
NORMALIZASYON = CIKTI / "345_2025_ayt_kimya_kusur_normalizasyonu.json"
BEKLENEN_SORU = 1304
GRUP_SORU = 60
OLCEK = 2
SIK_OKUNAMADI = "[okunamad\u0131]"  # "[okunamadi]" -- noktasiz i, kaynak ASCII kalsin


def _ad(birim: str, soru: int) -> str:
    return f"{birim}_{soru:02d}"


def _kutular() -> list[dict]:
    kutular: list[dict] = json.loads(KUTULAR.read_text("ascii"))["kutular"]
    return kutular


def gruplar() -> list[dict]:
    """Test sinirina hizali okuyucu gruplari (~GRUP_SORU soru)."""
    out: list[dict] = []
    simdi: list[str] = []
    onceki = None
    for k in _kutular():
        if k["birim"] != onceki and len(simdi) >= GRUP_SORU:
            out.append({"no": len(out) + 1, "dosyalar": simdi})
            simdi = []
        simdi.append(_ad(k["birim"], k["soru"]))
        onceki = k["birim"]
    if simdi:
        out.append({"no": len(out) + 1, "dosyalar": simdi})
    return out


def numarasi_ortulu() -> set[str]:
    """Numarasi okuyucu diskinin altinda kalan kutular.

    (a) capasi simgeden ya da numara+simge birlesiminden alinanlar; (b) capasi basili numaradan alinan ama
    diskin numaranin ilk rakam(lar)ini ortugu olculenler
    (`kim345ayt_kutu.numara_disk_ortulu`, kutuda `numara_disk_ortulu`).
    """
    return {
        _ad(k["birim"], k["soru"])
        for k in _kutular()
        if k["capa_kanali"] not in ("numara", "numara_alt")
        or k.get("numara_disk_ortulu")
    }


def hazirla() -> None:
    from PIL import Image

    OKUMA_KOKU.mkdir(parents=True, exist_ok=True)
    PARCA_DIZINI.mkdir(parents=True, exist_ok=True)
    g = gruplar()
    n = 0
    for x in g:
        for ad in x["dosyalar"]:
            im = Image.open(KIRPIM / f"{ad}.png")
            im.resize(
                (im.width * OLCEK, im.height * OLCEK), Image.Resampling.LANCZOS
            ).save(OKUMA_KOKU / f"{ad}.png")
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
    """Parcalari birlestirir; varsa duzeltme.json kayitlari ilk okumanin yerine gecer.

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
            yeni["okuma"] = f"duzeltme ({s['okuma']} yerine)"
            sorular[i] = yeni
    # Kusur notu normalizasyonu (depodaki kayit dosyasi): ilk 6 grubun 'soluk
    # ama okunan isaret' notlari ve numara-disk notlari. Yalniz not metni
    # BIREBIR eslesirse bosaltilir; okunan metin degismez.
    dusur = {}
    if NORMALIZASYON.exists():
        dusur = {
            k["dosya"]: k["dusurulen_not"]
            for k in json.loads(NORMALIZASYON.read_text("ascii"))["kayitlar"]
        }
    for s in sorular:
        if isinstance(s.get("basili_no"), str):
            s["basili_no"] = int(s["basili_no"].strip().rstrip("."))
        if s.get("kaynak_kusuru") and dusur.get(s["dosya"]) == s["kaynak_kusuru"]:
            s["kaynak_kusuru"] = None
        if s.get("kaynak_kusuru"):
            for h in "ABCDE":
                if not str(s["sikler"].get(h, "")).strip():
                    s["sikler"][h] = SIK_OKUNAMADI
    sorular.sort(key=lambda s: s["dosya"])
    HEDEF.write_text(
        json.dumps(
            {
                "kaynak": "345 2025 AYT Kimya Soru Bankasi",
                "nereden": (
                    "Soru kirpimlarindan okundu (kim345ayt_kirp.py, 2x Lanczos). Sorular "
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
    ortulu = numarasi_ortulu()
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
        no = s.get("basili_no")
        if not (no == sira or (no is None and ad in ortulu)):
            hata.append(f"KAPI2 {ad}: basili no {no} != test ici sira {sira}")
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
