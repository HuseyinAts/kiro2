#!/usr/bin/env python
"""345 2025 TYT Fizik: transkripsiyon harness'i (hazirla / topla / kapi).

Transkripsiyon bir OKUMA isidir: kirpim goruntusu okunur, kitapta ne yaziyorsa
o yazilir; soru cozulmez, cevap anahtari okuyucuya gosterilmez. Bu script
okumayi yapmaz, etrafini kurar (stm345_metin_harness.py deseni):

  hazirla : kirpimlari 2x buyutup okuma dizinine kopyalar, test sinirina
            hizali okuyucu gruplarini ve grup basina dosya listesini yazar.
  topla   : gruplardan donen JSON parcalarini tek dosyada birlestirir.
  kapi    : birlesik ciktiyi BAGIMSIZ yapisal olcumle karsilastirir.

KAPILAR (okuyucuya SOYLENMEYEN yapidan)
---------------------------------------
1. Her kirpim tam bir kez okunmus olmali (1397 dosya, eksik/fazla yok).
2. Okunan BASILI numara == test ici sira (kitabin cevap satiri
   numaralandirmasi). Tek istisna: okuyucu diski numaranin solunu ortebilir
   (ortme olcumu; olcumun kacirdigi tam ortmeler gozle listelenir:
   `345_2025_tyt_fizik_numara_goz.json`) ya da capa simgeden alinmistir
   (capa_kanali == 'simge');
   orada okuyucu null yazabilir, sayi yazarsa yine esit olmali.
3. Her soruda bes sik (A-E) bos olmayan metin tasimali.
4. Toplam soru sayisi 1397.

ORTME BILDIRIMI
---------------
hazirla, okuyucu diski halkasinda kitap murekkebi olculen sorulari
(`345_2025_tyt_fizik_ortme_olcumu.json`) grup listesinin yanina
`ortme_NN.txt` olarak yazar; okuyucu o sorularda disk kenarindaki
harflerin gorunup gorunmedigini `kaynak_kusuru`na yazar.

KULLANIM
--------
    python backend/scripts/kitap/fiz345tyt_metin_harness.py hazirla
    python backend/scripts/kitap/fiz345tyt_metin_harness.py topla
    python backend/scripts/kitap/fiz345tyt_metin_harness.py kapi
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KUTULAR = CIKTI / "345_2025_tyt_fizik_kirpim_kutulari.json"
ORTME = CIKTI / "345_2025_tyt_fizik_ortme_olcumu.json"
HEDEF = CIKTI / "345_2025_tyt_fizik_metin.json"
NUMARA_GOZ = CIKTI / "345_2025_tyt_fizik_numara_goz.json"
KIRPIM = KOK / "backend" / "_p345_gecici" / "tf" / "kirpim"
OKUMA_KOKU = Path(r"C:\Users\husey\VeraFilm\f_okuma_kirpim")
PARCA_DIZINI = Path(r"C:\Users\husey\VeraFilm\f_metin_parca")
BEKLENEN_SORU = 1397
GRUP_SORU = 40
OLCEK = 2
SIK_OKUNAMADI = "[okunamad\u0131]"
KIVRIK_KESME = "\u2019"  # "[okunamadi]" -- noktasiz i, kaynak ASCII kalsin


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
    return {
        _ad(k["birim"], k["soru"]) for k in _kutular() if k["capa_kanali"] == "simge"
    }


def ortme_listesi() -> set[str]:
    """Okuyucu diski halkasinda kitap murekkebi olculen sorular (fiz345tyt_kirp)."""
    return {
        _ad(o["birim"], o["soru"])
        for o in json.loads(ORTME.read_text("ascii"))["ortme"]
    }


def numara_goz_listesi() -> set[str]:
    """Diskin numarayi tamamen orttugu, gozle dogrulanan sorular."""
    return set(json.loads(NUMARA_GOZ.read_text("ascii"))["dosyalar"])


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
        ortme = sorted(ortme_listesi() & set(x["dosyalar"]))
        if ortme:
            (PARCA_DIZINI / f"ortme_{x['no']:02d}.txt").write_text(
                "\n".join(ortme) + "\n", encoding="ascii"
            )
    print(f"kirpim kopyalandi: {n} -> {OKUMA_KOKU}")
    print(f"grup sayisi: {len(g)}")
    for x in g:
        print(
            f"  grup {x['no']:2d}: {len(x['dosyalar'])} soru  {x['dosyalar'][0]} .. {x['dosyalar'][-1]}"
        )


NUMARA_NOTU = re.compile(
    r"numara|basili_no|bas\u0131l\u0131 no"
    r"|rakam\u0131n|rakam (okunam|kesin)|rakam '?\d'? (ya da|veya|olarak)"
    r"|(g\u00f6r\u00fcnen|yaln\u0131z)[^;]*"
    r"(par\u00e7a|k\u0131s\u0131m|k\u0131sm\u0131|kenar|\u00e7izgi|k\u0131vr\u0131m|yar\u0131s\u0131)"
    r"|^\s*en iyi okuma \d\s*$",
    re.IGNORECASE,
)


def numara_notu_ayikla(kusur: str) -> str | None:
    """Okuyucu diskinin numarayi kesmesi kitap kusuru degildir (talimat: 'bunu
    YAZMA'); yine de yazilan numara notlari ';' parcasi bazinda ayiklanir
    (kalan parcalar ayni ayiracla, bosluk eklenmeden birlesir: tirnak icindeki
    ';' bozulmaz). Numara bilgisinin yeri KAPI2 + ortme olcumu + numara_goz."""
    parca = kusur.split(";")
    kalan = [p for p in parca if not NUMARA_NOTU.search(p)]
    if len(kalan) == len(parca):
        return kusur
    metin = ";".join(kalan).strip()
    return metin or None


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
            yeni.pop("hukum", None)  # hukum kaydi ikinci_okuma.json'da
            yeni["okuma"] = f"duzeltme ({s['okuma']} yerine)"
            sorular[i] = yeni
    for s in sorular:
        # KESME ISARETI: iki okuma ' ve \u2019 karisik yazdi (ikinci okuma 38
        # farkin 38'i); kitapta kivrik basili ama cozunurlukte ayirt edilmiyor.
        # Onceki kitaplarin sozlesmesi: kesme ASCII "'" (PRG talimati).
        s["govde"] = s["govde"].replace(KIVRIK_KESME, "'")
        s["sikler"] = {
            h: str(v).replace(KIVRIK_KESME, "'") for h, v in s["sikler"].items()
        }
        if isinstance(s.get("basili_no"), str):
            s["basili_no"] = int(s["basili_no"].strip().rstrip("."))
        if s.get("kaynak_kusuru"):
            s["kaynak_kusuru"] = numara_notu_ayikla(s["kaynak_kusuru"])
        if s.get("kaynak_kusuru"):
            for h in "ABCDE":
                if not str(s["sikler"].get(h, "")).strip():
                    s["sikler"][h] = SIK_OKUNAMADI
    sorular.sort(key=lambda s: s["dosya"])
    HEDEF.write_text(
        json.dumps(
            {
                "kaynak": "345 2025 TYT Fizik Soru Bankasi",
                "nereden": (
                    "Soru kirpimlarindan okundu (fiz345tyt_kirp.py, 2x Lanczos). Sorular "
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
    ortulu = numarasi_ortulu() | ortme_listesi() | numara_goz_listesi()
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
