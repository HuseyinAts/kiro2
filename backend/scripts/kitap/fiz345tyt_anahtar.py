#!/usr/bin/env python
"""345 2025 TYT Fizik: cevap anahtari + test -> unite eslemesi (ham okumalardan).

CEVAP KAYNAGI
-------------
Kitabin KENDI basili cevap seridi: her soru sayfasinin altinda (kart y
899-904), sutun basina ayri satir ('7.C 8.C 9.E'). Hicbir soru cozulmedi,
hicbir cevap uretilmedi.

KANALLAR
--------
1. Okuma A ve okuma B (`345_2025_tyt_fizik_ham_okumalar.json`): bagimsiz
   iki gorsel okuma, farkli olcek ve TERS sira, 8'er ayri okuyucu; girdi
   sayisi soylenmedi. A == B sart; tek istisna `goz_kararlari.farklar`
   (10x gozle karar + numara surekliligi; karar A ya da B'den biri olmali).
2. Piksel: serit harf glifi en-yakin-komsu, birini-disarida-birak (LOO).
   Sutunun gri murekkep bilesenleri okumadaki girdi sayisina (N) N-1 en
   genis bosluktan bolunur; her girdinin en sagdaki 7 px x 12 px'i harf.
3. Goz: pikselin tutmadigi, '?' tasiyan ya da A/B farkli sutunlarin TUM
   girdileri 10x gozle (`goz_kararlari.girdiler`); karar okumayla ayni olmali.

KAPILAR (hepsi sert; ihlal -> SystemExit)
-----------------------------------------
* A ve B ayni sutun kumesi; girdi girdi ayni (farklar haric).
* Sutun kumesi == soru sayfalari x {L, R} (capa taramasi).
* Sutundaki girdi sayisi == o sutundaki okuyucu simgesi sayisi.
* Numara kitap boyunca ya oncekinin +1'i ya da 1 (yeni test).
* Her test tek unitenin sayfa araligi icinde (icindekiler).

KULLANIM
--------
    python backend/scripts/kitap/fiz345tyt_anahtar.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK_DOSYA = CIKTI / "345_2025_tyt_fizik"
HAM = Path(f"{ONEK_DOSYA}_ham_okumalar.json")
TARAMA = Path(f"{ONEK_DOSYA}_capa_taramasi.json")
HEDEF = Path(f"{ONEK_DOSYA}_cevap_anahtari.json")
KAYNAK_DIZIN = (
    KOK / "veriseti" / "zkitap" / "screenshots" / "345 2025 Tyt Fizik Soru Bankas\u0131"
)
KART = (589, 43, 1331, 1022)
SERIT_Y = (895, 909)
SERIT_X = {"L": (20, 371), "R": (371, 722)}
ONEK = "FZT345"
GIRDI = re.compile(r"(\d+)\.([A-E])(\?)?")


def _girdiler(metin: str) -> list[tuple[int, str, bool]]:
    out = []
    for x in metin.split():
        m = GIRDI.fullmatch(x)
        if not m:
            raise SystemExit(f"bicim disi girdi: {x!r}")
        out.append((int(m.group(1)), m.group(2), bool(m.group(3))))
    return out


def _anahtar(k: str) -> tuple[int, str]:
    return int(k[:-1]), k[-1]


def iki_okuma(ham: dict) -> dict[str, list[tuple[int, str, bool]]]:
    """A ve B'yi birlestirir; goz karari olmayan herhangi bir farkta durur."""
    a = ham["okumalar"]["A"]["serit"]
    b = ham["okumalar"]["B"]["serit"]
    fark = ham["goz_kararlari"]["farklar"]
    if set(a) != set(b):
        raise SystemExit(f"A/B sutun kumesi farkli: {sorted(set(a) ^ set(b))}")
    out = {}
    for k in sorted(a, key=_anahtar):
        ga, gb = _girdiler(a[k]), _girdiler(b[k])
        sa, sb = [(n, h) for n, h, _ in ga], [(n, h) for n, h, _ in gb]
        if sa != sb:
            if k not in fark:
                raise SystemExit(f"A/B farki {k}: {a[k]!r} / {b[k]!r}")
            karar = _girdiler(fark[k]["karar"])
            sk = [(n, h) for n, h, _ in karar]
            if sk not in (sa, sb):
                raise SystemExit(f"{k}: goz karari ne A ne B")
            out[k] = [(n, h, True) for n, h, _ in karar]
            continue
        if k in fark:
            raise SystemExit(f"{k}: A == B ama fark karari kayitli")
        out[k] = [
            (n, h, ta or tb) for (n, h, ta), (_, _, tb) in zip(ga, gb, strict=True)
        ]
    return out


def _kapsam_kapilari(
    sutunlar: dict[str, list[tuple[int, str, bool]]], tarama: dict
) -> None:
    """Sutun kumesi == soru sayfalari x {L, R}; girdi sayisi == simge sayisi."""
    bek = {f"{s}{t}" for s in tarama for t in "LR"}
    if set(sutunlar) != bek:
        raise SystemExit(
            f"okuma sutunlari != soru sayfalari: {sorted(set(sutunlar) ^ bek)[:6]}"
        )
    for k, gir in sutunlar.items():
        s, t = _anahtar(k)
        n = len(tarama[str(s)]["simge"][t])
        if n != len(gir):
            raise SystemExit(f"{k}: okuma {len(gir)} girdi, simge {n}")


def _gri(a: np.ndarray) -> np.ndarray:
    m: np.ndarray = (a.min(axis=2) < 200) & (a.max(axis=2) - a.min(axis=2) < 40)
    return m


def _harf_pencereleri(rgb: np.ndarray, t: str, adet: int) -> list[np.ndarray] | None:
    """Sutun seridini `adet` girdiye bol; her girdinin son 7 px'i (12x7, 0-1)."""
    x0, x1 = SERIT_X[t]
    c = rgb[SERIT_Y[0] : SERIT_Y[1], x0:x1]
    g = c.mean(axis=2)
    lab, _ = ndimage.label(_gri(c), np.ones((3, 3), bool))
    kos = sorted([sl[1].start, sl[1].stop] for sl in ndimage.find_objects(lab))
    birl: list[list[int]] = []
    for q in kos:
        if birl and q[0] <= birl[-1][1]:
            birl[-1][1] = max(birl[-1][1], q[1])
        else:
            birl.append(list(q))
    if len(birl) < adet:
        return None
    bos = sorted(
        sorted(range(len(birl) - 1), key=lambda i: -(birl[i + 1][0] - birl[i][1]))[
            : adet - 1
        ]
    )
    sonlar = [birl[i][1] for i in bos] + [birl[-1][1]]
    out = []
    for s in sonlar:
        w = g[1:13, s - 7 : s]
        if w.shape != (12, 7):
            return None
        out.append(((255 - w) / 255.0).ravel())
    return out


def glif_kanali(
    sutunlar: dict[str, list[tuple[int, str, bool]]],
) -> dict[tuple[str, int], str]:
    """(sutun, sira) -> 'uyum' | 'uyumsuz' | 'kapsam_disi'."""
    glifler, etiket, yer = [], [], []
    durum: dict[tuple[str, int], str] = {}
    for k, gir in sutunlar.items():
        s, t = _anahtar(k)
        img = Image.open(KAYNAK_DIZIN / f"sayfa_{s:04d}.png").convert("RGB").crop(KART)
        rgb = np.asarray(img).astype(float)
        for i in range(len(gir)):
            durum[(k, i)] = "kapsam_disi"
        pen = _harf_pencereleri(rgb, t, len(gir))
        if pen is None:
            continue
        for i, (w, (_, h, _)) in enumerate(zip(pen, gir, strict=True)):
            glifler.append(w)
            etiket.append(h)
            yer.append((k, i))
    m = np.array(glifler)
    for i in range(len(m)):
        d = ((m - m[i]) ** 2).sum(axis=1)
        d[i] = np.inf
        durum[yer[i]] = "uyum" if etiket[int(np.argmin(d))] == etiket[i] else "uyumsuz"
    return durum


def _kanal(k: str, n: int, h: str, g: str, goz: dict[str, list[str]]) -> str:
    """Ucuncu kanal: goz karari varsa o (okumayla ayni olmali), yoksa piksel uyumu."""
    goz_no = {int(x.split(".")[0]): x for x in goz.get(k, [])}
    if n in goz_no:
        if goz_no[n] != f"{n}.{h}":
            raise SystemExit(f"goz karari okumayla celisiyor {k} {goz_no[n]} / {n}.{h}")
        return "iki_okuma+goz(10x)"
    if g == "uyum":
        return "iki_okuma+piksel"
    raise SystemExit(f"{k} {n}.{h}: piksel {g}, goz karari yok")


def unite_bulucu(ham: dict):
    bas = [(u[0], u[1], u[2]) for u in ham["icindekiler"]["uniteler"]]

    def unite(dosya: int) -> tuple[int, str]:
        aday = [(no, ad) for no, ad, b in bas if b <= dosya]
        if not aday:
            raise SystemExit(f"s{dosya}: ilk unitenin basindan once")
        return aday[-1]

    return unite


def cevaplar_uret(sutunlar, glif, goz, fark, unite):
    """Numara 1 -> yeni test; numara kopmasi durdurur."""
    cevaplar, tereddut = [], []
    test_no, onceki = 0, None
    test_sayfa: dict[int, list[int]] = {}
    for k in sorted(sutunlar, key=_anahtar):
        s, t = _anahtar(k)
        for i, (n, h, ter) in enumerate(sutunlar[k]):
            if n == 1:
                test_no += 1
            elif onceki is None or n != onceki + 1:
                raise SystemExit(f"numara kopmasi {k}: {onceki} -> {n}")
            onceki = n
            test_sayfa.setdefault(test_no, []).append(s)
            kanal = _kanal(k, n, h, glif[(k, i)], goz)
            if k in fark:
                kanal = "iki_okuma_farkli+goz(10x)+numara_surekliligi"
            elif ter:
                tereddut.append(f"{k} {n}.{h}")
                kanal += "+tereddut"
            cevaplar.append(
                {
                    "birim": f"{ONEK}-T{test_no:03d}",
                    "soru": n,
                    "cevap": h,
                    "kaynak": kanal,
                    "dosya": s,
                    "sutun": t,
                    "serit_sira": i,
                    "unite": unite(s)[0],
                }
            )
    return cevaplar, tereddut, test_sayfa


def testler_uret(test_sayfa, cevaplar, unite) -> list[dict]:
    """Her test tek unite icinde; sayfalar ardisik."""
    soru = Counter(c["birim"] for c in cevaplar)
    testler = []
    for tn in sorted(test_sayfa):
        sy = sorted(set(test_sayfa[tn]))
        if sy != list(range(sy[0], sy[-1] + 1)):
            raise SystemExit(f"T{tn:03d} sayfalari ardisik degil: {sy}")
        no, _ = unite(sy[0])
        if unite(sy[-1])[0] != no:
            raise SystemExit(f"T{tn:03d} iki uniteye yayiliyor: {sy}")
        testler.append(
            {
                "birim": f"{ONEK}-T{tn:03d}",
                "unite": no,
                "sayfalar": sy,
                "soru_sayisi": soru[f"{ONEK}-T{tn:03d}"],
            }
        )
    return testler


def main() -> None:
    ham = json.loads(HAM.read_text("ascii"))
    tarama = json.loads(TARAMA.read_text("ascii"))["sayfalar"]
    sutunlar = iki_okuma(ham)
    _kapsam_kapilari(sutunlar, tarama)
    glif = glif_kanali(sutunlar)
    unite = unite_bulucu(ham)
    goz = ham["goz_kararlari"]
    cevaplar, tereddut, test_sayfa = cevaplar_uret(
        sutunlar, glif, goz["girdiler"], goz["farklar"], unite
    )
    testler = testler_uret(test_sayfa, cevaplar, unite)
    uyumsuz = [k for k, v in glif.items() if v == "uyumsuz"]
    kapsam_disi = sum(1 for v in glif.values() if v == "kapsam_disi")
    veri = {
        "kaynak": "345 2025 TYT Fizik Soru Bankasi",
        "arac": "scripts/kitap/fiz345tyt_anahtar.py",
        "nereden": (
            "Kitabin KENDI basili cevap seridinden (her soru sayfasinin altinda, sutun "
            "basina ayri satir; kart y 899-904). Hicbir soru cozulmedi, hicbir cevap "
            "uretilmedi."
        ),
        "nasil": (
            "Iki bagimsiz gorsel okuma: A (5x, sayfa sirasi) ve B (7x, TERS sira), 8'er "
            "okuyucu; girdi sayisi soylenmedi. A == B girdi girdi (1 fark goz + sureklilik). "
            "Ucuncu kanal: serit harf glifi en-yakin-komsu LOO; tutmayan, tereddutlu ve "
            "farkli sutunlar 10x gozle."
        ),
        "dogrulama": {
            "a_esittir_b_sutun": sum(1 for k in sutunlar if k not in goz["farklar"]),
            "a_b_farkli_sutun": sorted(goz["farklar"]),
            "girdi_sayisi_esittir_simge": True,
            "numara_surekliligi": "ya oncekinin +1'i ya da 1",
            "test_tek_unitede": True,
            "glif_loo_uyum": sum(1 for v in glif.values() if v == "uyum"),
            "glif_loo_uyumsuz": [f"{k}#{i}" for k, i in uyumsuz],
            "glif_kapsam_disi": kapsam_disi,
            "tereddutlu_girdi": tereddut,
        },
        "toplam_cevap": len(cevaplar),
        "test_sayisi": len(testler),
        "kaynak_dagilimi": dict(sorted(Counter(c["kaynak"] for c in cevaplar).items())),
        "harf_dagilimi": dict(sorted(Counter(c["cevap"] for c in cevaplar).items())),
        "testler": testler,
        "cevaplar": cevaplar,
    }
    HEDEF.write_text(
        json.dumps(veri, ensure_ascii=True, indent=1) + "\n",
        encoding="ascii",
        newline="\n",
    )
    print(
        f"test {len(testler)}  cevap {len(cevaplar)}"
        f"  glif uyum {veri['dogrulama']['glif_loo_uyum']}  uyumsuz {len(uyumsuz)}"
        f"  kapsam disi {kapsam_disi}  tereddut {len(tereddut)}"
    )
    print("kaynak:", veri["kaynak_dagilimi"])
    print("harf:", veri["harf_dagilimi"])


if __name__ == "__main__":
    main()
