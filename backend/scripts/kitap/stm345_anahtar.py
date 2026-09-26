#!/usr/bin/env python
"""345 2025 Start Matematik: cevap anahtari + test -> unite eslemesi (ham okumalardan).

CEVAP KAYNAGI
-------------
Kitabin KENDI basili cevap seridi: her 'Sinava Gecis' test sayfasinin
altinda, sutun basina ayri satir ('1.C 2.B 3.E'). Hicbir soru cozulmedi,
hicbir cevap uretilmedi. Kapsam yalniz 45 testin sorulari (sahip karari 25
Eyl: konu sayfalarindaki acik uclu alistirmalar ve 'Isindirma Kosesi'
kapsam disi -- anahtarlari basili degil).

KANALLAR
--------
1. Okuma A ve okuma B (`345_2025_start_matematik_ham_okumalar.json`):
   bagimsiz iki gorsel okuma, farkli olcek ve TERS sira. A == B sart; '?'
   tasiyan girdi ancak digeri kesin ve numara surekliligi tutuyorsa kabul.
2. Piksel: serit harf glifi (9x8 pencere, gri) en-yakin-komsu,
   birini-disarida-birak (LOO). Glif, girdinin son murekkep kosusudur;
   yalniz piksel girdi sayisi okumayla esit olan sutunlarda.
3. Goz: pikselin tutmadigi ya da kapsamadigi girdiler 10x gozle
   (`goz_kararlari`); karar okumayla celismiyorsa kabul.

KAPILAR (hepsi sert; ihlal -> SystemExit)
-----------------------------------------
* A ve B ayni sutun kumesi, girdi girdi ayni numara ve harf.
* Sutundaki girdi sayisi == basili soru numarasi sayisi (capa taramasi).
* Numara kitap boyunca ya oncekinin +1'i ya da 1 (yeni test).
* Her test tam iki ardisik sayfa; bant test no'su unite icinde 1'den
  ardisik; bant unite adi == icindekiler araligindaki unite adi.

KULLANIM
--------
    python backend/scripts/kitap/stm345_anahtar.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK_DOSYA = CIKTI / "345_2025_start_matematik"
HAM = Path(f"{ONEK_DOSYA}_ham_okumalar.json")
TARAMA = Path(f"{ONEK_DOSYA}_capa_taramasi.json")
HEDEF = Path(f"{ONEK_DOSYA}_cevap_anahtari.json")
KAYNAK_DIZIN = KOK / "veriseti" / "zkitap" / "screenshots" / "345 2025 Start Matematik"
KART = (589, 43, 1331, 1020)
SERIT_Y = (905, 930)
SERIT_X = {"L": (55, 330), "R": (400, 700)}
MUREKKEP = 225
GIRDI_BOSLUK = 4
ONEK = "STM345"
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
    """A ve B'yi birlestirir; herhangi bir farkta durur."""
    a = ham["okumalar"]["A"]["serit"]
    b = ham["okumalar"]["B"]["serit"]
    if set(a) != set(b):
        raise SystemExit(f"A/B sutun kumesi farkli: {sorted(set(a) ^ set(b))}")
    out = {}
    for k in sorted(a, key=_anahtar):
        ga, gb = _girdiler(a[k]), _girdiler(b[k])
        if [(n, h) for n, h, _ in ga] != [(n, h) for n, h, _ in gb]:
            raise SystemExit(f"A/B farki {k}: {a[k]!r} / {b[k]!r}")
        out[k] = [
            (n, h, ta or tb) for (n, h, ta), (_, _, tb) in zip(ga, gb, strict=True)
        ]
    return out


def _kosular(col: np.ndarray) -> list[tuple[int, int]]:
    """Murekkepli sutunlarin ardisik kosulari [bas, son)."""
    kosu: list[tuple[int, int]] = []
    bas = None
    for x in range(len(col) + 1):
        c = bool(col[x]) if x < len(col) else False
        if c and bas is None:
            bas = x
        if not c and bas is not None:
            kosu.append((bas, x))
            bas = None
    return kosu


def _gruplar(kosu: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    """Bosluk < GIRDI_BOSLUK olan kosulari ayni girdiye topla."""
    grup: list[list[tuple[int, int]]] = []
    for r in kosu:
        if grup and r[0] - grup[-1][-1][1] < GIRDI_BOSLUK:
            grup[-1].append(r)
        else:
            grup.append([r])
    return grup


def _harf_glifi(b: np.ndarray, g: list[tuple[int, int]]) -> np.ndarray | None:
    """Girdinin son kosusu = harf; 9x8 gri pencere (0-1) ya da None."""
    lx0, lx1 = g[-1]
    if lx1 - lx0 < 4:
        return None
    ys = np.where((b[:, lx0:lx1] < MUREKKEP).any(axis=1))[0]
    cy, cx = (int(ys.min()) + int(ys.max())) // 2, (lx0 + lx1) // 2
    w = b[cy - 4 : cy + 5, cx - 4 : cx + 4]
    if w.shape != (9, 8):
        return None
    out: np.ndarray = (255 - w).ravel() / 255.0
    return out


def glif_kanali(
    sutunlar: dict[str, list[tuple[int, str, bool]]],
) -> dict[tuple[str, int], str]:
    """(sutun, sira) -> 'uyum' | 'uyumsuz' | 'kapsam_disi'."""
    glifler, etiket, yer = [], [], []
    durum: dict[tuple[str, int], str] = {}
    for k, gir in sutunlar.items():
        s, t = _anahtar(k)
        img = Image.open(KAYNAK_DIZIN / f"sayfa_{s:04d}.png").convert("L").crop(KART)
        x0, x1 = SERIT_X[t]
        b = np.asarray(img).astype(float)[SERIT_Y[0] : SERIT_Y[1], x0:x1]
        grup = _gruplar(_kosular(np.asarray((b < MUREKKEP).any(axis=0))))
        for i in range(len(gir)):
            durum[(k, i)] = "kapsam_disi"
        if len(grup) != len(gir):
            continue
        for i, (g, (_, h, _)) in enumerate(zip(grup, gir, strict=True)):
            w = _harf_glifi(b, g)
            if w is None:
                continue
            glifler.append(w)
            etiket.append(h)
            yer.append((k, i))
    m = np.array(glifler)
    d2 = ((m[:, None, :] - m[None, :, :]) ** 2).sum(axis=2)
    np.fill_diagonal(d2, np.inf)
    for i in range(len(m)):
        durum[yer[i]] = (
            "uyum" if etiket[int(np.argmin(d2[i]))] == etiket[i] else "uyumsuz"
        )
    return durum


def _kapsam_kapilari(
    sutunlar: dict[str, list[tuple[int, str, bool]]], tarama: dict
) -> None:
    """Sutun kumesi == test sayfalari x {L, R}; girdi sayisi == basili numara."""
    bek = {f"{s}{t}" for s in tarama for t in "LR"}
    if set(sutunlar) != bek:
        raise SystemExit(
            f"okuma sutunlari != test sayfalari: {sorted(set(sutunlar) ^ bek)[:6]}"
        )
    for k, gir in sutunlar.items():
        s, t = _anahtar(k)
        n = len(tarama[str(s)]["numara"][t])
        if n != len(gir):
            raise SystemExit(f"{k}: okuma {len(gir)} girdi, basili numara {n}")


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


def _unite_bulucu(ham: dict):
    bas_dosya = [(u[0], u[1], u[2] + 1) for u in ham["icindekiler"]["uniteler"]]

    def unite(dosya: int) -> tuple[int, str]:
        aday = [(no, ad) for no, ad, bd in bas_dosya if bd <= dosya]
        return aday[-1]

    return unite


def _cevaplar(sutunlar, glif, goz, unite):
    """Numara 1 -> yeni test; numara kopmasi durdurur."""
    cevaplar, tereddut = [], []
    test_no, onceki = 0, None
    test_sayfa: dict[int, set[int]] = {}
    for k in sorted(sutunlar, key=_anahtar):
        s, t = _anahtar(k)
        for i, (n, h, ter) in enumerate(sutunlar[k]):
            if n == 1:
                test_no += 1
            elif onceki is None or n != onceki + 1:
                raise SystemExit(f"numara kopmasi {k}: {onceki} -> {n}")
            onceki = n
            test_sayfa.setdefault(test_no, set()).add(s)
            kanal = _kanal(k, n, h, glif[(k, i)], goz)
            if ter:
                tereddut.append(f"{k} {n}.{h}")
                kanal += "+tereddut(numara_surekliligi)"
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


def _testler(test_sayfa, cevaplar, bant, unite) -> list[dict]:
    """Her test tam iki ardisik sayfa, tek unite; bant no ve adi tutarli."""
    unite_ici: Counter[int] = Counter()
    soru = Counter(c["birim"] for c in cevaplar)
    testler = []
    for tn in sorted(test_sayfa):
        sy = sorted(test_sayfa[tn])
        if len(sy) != 2 or sy[1] != sy[0] + 1:
            raise SystemExit(f"T{tn:03d} sayfalari iki ardisik degil: {sy}")
        no, ad = unite(sy[0])
        if unite(sy[1])[0] != no:
            raise SystemExit(f"T{tn:03d} iki uniteye yayiliyor")
        unite_ici[no] += 1
        for s in sy:
            bn, bad = bant[str(s)]
            if bn != unite_ici[no] or bad != ad:
                raise SystemExit(f"s{s}: bant ({bn}, {bad}) != ({unite_ici[no]}, {ad})")
        testler.append(
            {
                "birim": f"{ONEK}-T{tn:03d}",
                "unite": no,
                "unite_ici_test": unite_ici[no],
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
    unite = _unite_bulucu(ham)
    cevaplar, tereddut, test_sayfa = _cevaplar(
        sutunlar, glif, ham["goz_kararlari"]["girdiler"], unite
    )
    testler = _testler(test_sayfa, cevaplar, ham["bant_okumasi"]["sayfalar"], unite)

    uyumsuz = [k for k, v in glif.items() if v == "uyumsuz"]
    kapsam_disi = sum(1 for v in glif.values() if v == "kapsam_disi")
    veri = {
        "kaynak": "345 2025 Start Matematik",
        "arac": "scripts/kitap/stm345_anahtar.py",
        "nereden": (
            "Kitabin KENDI basili cevap seridinden (her 'Sinava Gecis' test sayfasinin "
            "altinda, sutun basina ayri satir; kart y 905-930). Hicbir soru cozulmedi, "
            "hicbir cevap uretilmedi."
        ),
        "nasil": (
            "Iki bagimsiz gorsel okuma: A (5x, sayfa sirasi) ve B (7x, TERS sira); "
            "okuyuculara girdi sayisi soylenmedi. A == B girdi girdi. Ucuncu kanal: "
            "serit harf glifi en-yakin-komsu LOO; tutmayan / kapsamayan girdiler 10x gozle."
        ),
        "dogrulama": {
            "a_esittir_b": True,
            "girdi_sayisi_esittir_basili_numara": True,
            "numara_surekliligi": "ya oncekinin +1'i ya da 1",
            "test_iki_ardisik_sayfa": True,
            "bant_unite_ve_test_no": True,
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
