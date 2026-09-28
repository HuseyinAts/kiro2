"""Transkripsiyon harness'i (hazirla / topla / kapi) -- profil gudumlu.

Transkripsiyon bir OKUMA isidir: kirpim goruntusu okunur, kitapta ne yaziyorsa
o yazilir; soru cozulmez, cevap anahtari okuyucuya gosterilmez. Bu modul
okumayi yapmaz, etrafini kurar (acil2021tyt_metin_harness deseni). Iki okuma
+ hakem adimlari `scripts/kitap/metin_iki_okuma.py` ile yapilir.

  hazirla : kirpimlari 2x buyutup okuma dizinine kopyalar, test sinirina
            hizali okuyucu gruplarini, grup listelerini, ortme listelerini ve
            okuma talimatini (VeraFilm/a2 sablonundan) yazar.
  topla   : grup JSON parcalarini (+ varsa duzeltme.json) tek dosyada birlestirir.
  kapi    : birlesik ciktiyi BAGIMSIZ yapisal olcumle karsilastirir.

KAPILAR
-------
1. Her kirpim tam bir kez okunmus (BEKLENEN_SORU).
2. Okunan BASILI numara == test ici sira; istisna yalniz profilde gozle
   listelenmis numarasiz capa (numara basilmamis) -> null.
3. Her soruda bes sik bos olmayan metin tasir.
4. Toplam soru sayisi BEKLENEN_SORU.

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.metin --profil K hazirla|topla|kapi
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from types import ModuleType

from scripts.kitap.kitap_hat import ortak

GRUP_SORU = 12
OLCEK = 2
SIK_OKUNAMADI = "[okunamad\u0131]"
KIVRIK_KESME = "\u2019"
SABLON = ortak.VERAFILM / "a2_metin_talimat.md"
SABLON_KITAP = "2020-2021 AC\u0130L TYT Matematik"


def okuma_koku(p: ModuleType) -> Path:
    return Path(ortak.VERAFILM / f"{p.VERAF}_okuma_kirpim")


def parca_dizini(p: ModuleType) -> Path:
    return Path(ortak.VERAFILM / f"{p.VERAF}_metin_parca")


def kirpim_dizini(p: ModuleType) -> Path:
    return Path(ortak.KOK / "backend" / f"_{p.VERAF}_gecici" / "kirpim")


def _kutular(p: ModuleType) -> list[dict]:
    kutular: list[dict] = ortak.oku(p, "kirpim_kutulari")["kutular"]
    return kutular


def gruplar(p: ModuleType) -> list[dict]:
    """Test sinirina hizali okuyucu gruplari (~GRUP_SORU soru)."""
    grup_soru = getattr(p, "GRUP_SORU", GRUP_SORU)
    out: list[dict] = []
    simdi: list[str] = []
    onceki = None
    for k in _kutular(p):
        if k["birim"] != onceki and len(simdi) >= grup_soru:
            out.append({"no": len(out) + 1, "dosyalar": simdi})
            simdi = []
        simdi.append(ortak.dosya_adi(k["birim"], k["soru"]))
        onceki = k["birim"]
    if simdi:
        out.append({"no": len(out) + 1, "dosyalar": simdi})
    return out


def numarasiz(p: ModuleType) -> set[str]:
    """Numarasi basilmamis (profilde gozle listelenmis) sorular."""
    tar = ortak.oku(p, "capa_taramasi")
    out = set()
    for t in tar["testler"]:
        for i, c in enumerate(t["capalar"], 1):
            if c.get("numarasiz"):
                out.add(ortak.dosya_adi(ortak.birim_kodu(p, t["test"]), i))
    return out


def ortme_listesi(p: ModuleType) -> set[str]:
    return {
        ortak.dosya_adi(o["birim"], o["soru"])
        for o in ortak.oku(p, "ortme_olcumu")["ortme"]
    }


def talimat(p: ModuleType) -> str:
    s = SABLON.read_text("utf-8")
    s = s.replace(SABLON_KITAP, p.KITAP_BASLIGI).replace("a2_", f"{p.VERAF}_")
    s = s.replace("ACL21T", p.KOD)
    ek = getattr(p, "TALIMAT_EK", "")
    return str(s + ("\n" + ek + "\n" if ek else ""))


def hazirla(p: ModuleType) -> None:
    from PIL import Image

    ok, pd = okuma_koku(p), parca_dizini(p)
    ok.mkdir(parents=True, exist_ok=True)
    pd.mkdir(parents=True, exist_ok=True)
    g = gruplar(p)
    ortme = ortme_listesi(p)
    n = 0
    for x in g:
        for ad in x["dosyalar"]:
            im = Image.open(kirpim_dizini(p) / f"{ad}.png")
            im.resize(
                (im.width * OLCEK, im.height * OLCEK), Image.Resampling.LANCZOS
            ).save(ok / f"{ad}.png")
            n += 1
        (pd / f"liste_{x['no']:02d}.txt").write_text(
            "\n".join(x["dosyalar"]) + "\n", encoding="ascii"
        )
        o = sorted(ortme & set(x["dosyalar"]))
        if o:
            (pd / f"ortme_{x['no']:02d}.txt").write_text(
                "\n".join(o) + "\n", encoding="ascii"
            )
    (ortak.VERAFILM / f"{p.VERAF}_metin_talimat.md").write_text(talimat(p), "utf-8")
    print(f"kirpim kopyalandi: {n} -> {ok}; grup {len(g)}")
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
    """Okuyucu diskinin numarayi kesmesi kitap kusuru degildir; ';' parcasi bazinda ayiklanir."""
    parca = kusur.split(";")
    kalan = [x for x in parca if not NUMARA_NOTU.search(x)]
    if len(kalan) == len(parca):
        return kusur
    metin = ";".join(kalan).strip()
    return metin or None


def topla(p: ModuleType) -> None:
    """Parcalari birlestirir; varsa duzeltme.json kayitlari ilk okumanin yerine gecer.

    OKUNAMAYAN SIK: okuyucu sikki bos biraktiysa VE kaynak kusuru yazdiysa sik
    SIK_OKUNAMADI isaretini alir; sessiz bos sik KAPI3'e takilir.
    """
    pd = parca_dizini(p)
    parca = sorted(pd.glob("grup_*.json"))
    sorular: list[dict] = []
    for f in parca:
        for s in json.loads(f.read_text("utf-8"))["sorular"]:
            s["okuma"] = f.stem
            sorular.append(s)
    duz_yolu = pd / "duzeltme.json"
    duzeltme = {}
    if duz_yolu.exists():
        duzeltme = {
            s["dosya"]: s for s in json.loads(duz_yolu.read_text("utf-8"))["sorular"]
        }
    for i, s in enumerate(sorular):
        if s["dosya"] in duzeltme:
            yeni = dict(duzeltme[s["dosya"]])
            yeni.pop("hukum", None)
            yeni["okuma"] = f"duzeltme ({s['okuma']} yerine)"
            sorular[i] = yeni
    for s in sorular:
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
    ortak.yaz(
        p,
        "metin",
        {
            "kaynak": p.KAYNAK_ADI,
            "nereden": (
                "Soru kirpimlarindan okundu (kitap_hat/kirp.py, 2x Lanczos). Sorular "
                "cozulmedi, cevap anahtari okuyucuya gosterilmedi."
            ),
            "parca_sayisi": len(parca),
            "soru_sayisi": len(sorular),
            "sorular": sorular,
        },
        girinti=1,
    )
    print(f"{len(parca)} parca -> {len(sorular)} soru")


def kapi(p: ModuleType, sorular: list[dict] | None = None) -> list[str]:
    if sorular is None:
        sorular = ortak.oku(p, "metin")["sorular"]
    hata = []
    beklenen = [ad for g in gruplar(p) for ad in g["dosyalar"]]
    bos_no = numarasiz(p)
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
        # Baski hatasi: kitapta yanlis numara basilmis (gozle, profilde listeli).
        hatali = getattr(p, "BASKI_NUMARA_HATASI", {})
        if not (no == sira or (no is None and ad in bos_no) or hatali.get(ad) == no):
            hata.append(f"KAPI2 {ad}: basili no {no} != test ici sira {sira}")
        for h in "ABCDE":
            if not str((s.get("sikler") or {}).get(h, "")).strip():
                hata.append(f"KAPI3 {ad}: {h} sikki bos")
    if len(sorular) != p.BEKLENEN_SORU:
        hata.append(f"KAPI4 toplam soru {len(sorular)} != {p.BEKLENEN_SORU}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    ap.add_argument("eylem", choices=["hazirla", "topla", "kapi"])
    args = ap.parse_args()
    p = ortak.profil(args.profil)
    if args.eylem == "hazirla":
        hazirla(p)
    elif args.eylem == "topla":
        topla(p)
    else:
        hata = kapi(p)
        print(f"kapi ihlali: {len(hata)}")
        for h in hata[:40]:
            print("   ", h)
        if hata:
            raise SystemExit(1)
        print("TUM KAPILAR YESIL")


if __name__ == "__main__":
    main()
