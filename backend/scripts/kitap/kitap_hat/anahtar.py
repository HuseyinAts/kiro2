"""Cevap anahtari: kirpim hazirligi, glif ucuncu kanali, ham birlestirme, dogrulama.

KANALLAR (acil2021tyt_anahtar deseni)
-------------------------------------
* okuma A / okuma B: iki bagimsiz gorsel okuma (A ileri, B geri; hucre
  sayisi okuyucuya soylenmez). A == B hucre ve harf duzeyinde olmali.
* glif: anahtar bolgesindeki notr koyu harf glifleri, en-yakin-komsu
  birini-disarida-birak (etiket = okuma A). Uyumsuz hucre 5x goz teyidi
  (`goz_teyit`) tasimali; blob sayisi hucre sayisina esit olmayan test glif
  kapsami disidir ve 5x gozle (`goz_c`) okunur.
* Hucre sayisi == capa sayisi (tarama).
Hicbir soru cozulmez; tek kaynak kitabin basili anahtari.

ALT KOMUTLAR (backend dizininden)
---------------------------------
    python -m scripts.kitap.kitap_hat.anahtar --profil K hazirla
    python -m scripts.kitap.kitap_hat.anahtar --profil K glif
    python -m scripts.kitap.kitap_hat.anahtar --profil K ham --goz-teyit T005#3=C ...
    python -m scripts.kitap.kitap_hat.anahtar --profil K yaz
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage

from scripts.kitap.kitap_hat import ortak

HARFLER = set("ABCDE")


def serit_dizini(p: ModuleType) -> Path:
    return Path(ortak.VERAFILM / f"{p.VERAF}_serit")


def hazirla(p: ModuleType) -> None:
    """Anahtar bolgesi (3x Lanczos) ve test ilk sayfasi bandi (2x) kirpimlari."""
    tar = ortak.oku(p, "capa_taramasi")
    d = ortak.kaynak_dizin(p)
    o = serit_dizini(p)
    o.mkdir(parents=True, exist_ok=True)
    for t in tar["testler"]:
        i = t["test"]
        ilk = t["sayfalar"][0]
        # Anahtarli her sayfanin seridi (cogu kitapta yalniz son sayfa);
        # birden cok ise sayfa sirasiyla alt alta.
        parca = []
        for n in anahtarli_sayfalar(tar, t):
            y0, y1, x0, x1 = tar["sayfalar"][str(n)]["anahtar"]
            k = Image.open(d / f"sayfa_{n:04d}.png").convert("RGB").crop(p.KART)
            s = k.crop((max(0, x0 - 6), y0 - 6, min(k.width, x1 + 8), y1 + 6))
            parca.append(
                s.resize((s.width * 3, s.height * 3), Image.Resampling.LANCZOS)
            )
        m = Image.new(
            "RGB",
            (max(s.width for s in parca), sum(s.height + 12 for s in parca) - 12),
            (255, 255, 255),
        )
        yy = 0
        for s in parca:
            m.paste(s, (0, yy))
            yy += s.height + 12
        m.save(o / f"serit_{i:03d}.png")
        b = Image.open(d / f"sayfa_{ilk:04d}.png").convert("RGB").crop(p.KART)
        b = b.crop((0, 0, k.width, p.BANT_Y_ALT))
        b.resize((b.width * 2, b.height * 2), Image.Resampling.LANCZOS).save(
            o / f"bant_{i:03d}.png"
        )
    (o / "talimat.md").write_text(talimat(p, len(tar["testler"])), "utf-8")
    print(len(tar["testler"]), "test ->", o)


def anahtarli_sayfalar(tar: dict[str, Any], t: dict[str, Any]) -> list[int]:
    return [int(n) for n in t["sayfalar"] if tar["sayfalar"][str(n)]["anahtar"]]


def talimat(p: ModuleType, n: int) -> str:
    o = serit_dizini(p)
    return f"""# Cevap anahtari okuma talimati ({p.KAYNAK_ADI})

Bu bir OKUMA isidir. Soru COZULMEZ. Tek is: goruntude basili olani yazmak.

Dizin: `{o}\\`
* `serit_NNN.png` (NNN = 001..{n:03d}): bir testin cevap anahtari. Hucreler
  "1. C", "2. A" ... bicimindedir (renkli numara + siyah harf), bir ya da
  birden cok satir.
* `bant_NNN.png`: ayni testin ilk sayfasinin ust bandi. {p.BANT_TARIFI}

Her NNN icin (yalniz sana verilen ARALIK ve SIRA ile):
1. `serit_NNN.png` dosyasini read_file ile GORUNTU olarak ac. Hucreleri
   soldan saga, ustten alta oku. Her hucre icin basili numara ve harf.
   Harf yalniz A, B, C, D, E olabilir. Emin olamadigin harfe `?` yaz
   (tahmin ETME). Hucre sayisini sen say; bir sayi verilmedi.
2. `bant_NNN.png` dosyasini ac; `konu` alanina {p.BANT_KONU_TARIFI}
   aynen yaz (Turkce harflerle); `test_no` alanina "Test - " yazisindan
   sonraki isareti aynen yaz (ornek "I", "IV", "3"). Okunamazsa "".

Her dosyayi tek tek ac; bir dosyayi acmadan onun icin cikti yazma.

Cikti: sana verilen yola gecerli UTF-8 JSON:
```
{{"okuyucu": "<ad>", "testler": [
  {{"test": 1, "konu": "...", "test_no": "I", "hucreler": [[1, "C"], [2, "A"]]}}
]}}
```
`testler` test numarasina gore artan sirada olsun (okuma sirasi ne olursa
olsun). Bitince dosyayi python ile json.load et, araliktaki her testin
bulundugunu dogrula. Gecici dosyalar yalniz `{ortak.VERAFILM}\\{p.VERAF}_tmp\\<ad>`
altina.
"""


def _harf_bloblari(p: ModuleType, s: np.ndarray) -> list[tuple[slice, slice]]:
    mx, mn = s.max(axis=2), s.min(axis=2)
    siyah = (mn < p.GLIF_HARF_ESIK) & (mx - mn < 45)
    siyah = ndimage.binary_dilation(siyah, np.ones((2, 1), bool))
    lab, _ = ndimage.label(siyah)
    tum = list(ndimage.find_objects(lab))
    if getattr(p, "HARF_NOKTA_SONRASI", False):
        # Numara da harfle ayni renkte ('1.C 2.B'): harf = satirda NOKTADAN
        # (en fazla 3x3 blob) hemen sonraki blob.
        def nokta(o: tuple[slice, slice]) -> bool:
            return bool(o[0].stop - o[0].start <= 4 and o[1].stop - o[1].start <= 3)

        tum.sort(key=lambda o: (o[0].stop, o[1].start))
        sec = []
        for o in tum:
            if nokta(o):
                continue
            onceki = [
                q
                for q in tum
                if q[1].stop <= o[1].start
                and o[1].start - q[1].stop <= 4
                and abs(q[0].stop - o[0].stop) <= 3
            ]
            if onceki and nokta(max(onceki, key=lambda q: q[1].stop)):
                sec.append(o)
        tum = sec
    bl = [
        o
        for o in tum
        if p.GLIF_HARF_H[0] <= o[0].stop - o[0].start <= p.GLIF_HARF_H[1]
        and o[1].stop - o[1].start <= p.GLIF_HARF_W_EN_COK
    ]
    bl.sort(key=lambda o: (o[0].start, o[1].start))
    satir: list[list] = []
    for o in bl:
        if satir and abs(o[0].start - satir[-1][0][0].start) <= 4:
            satir[-1].append(o)
        else:
            satir.append([o])
    return [o for r in satir for o in sorted(r, key=lambda o: o[1].start)]


def glif(p: ModuleType) -> dict[str, Any]:
    """Ucuncu kanal: anahtar bolgesindeki harf glifleri, LOO en yakin komsu."""
    tar = ortak.oku(p, "capa_taramasi")
    d = ortak.kaynak_dizin(p)
    a_oku = json.loads((serit_dizini(p) / "okuma_A.json").read_text("utf-8"))
    A = {x["test"]: x for x in a_oku["testler"]}
    vek, etiket, yer, kapsam_disi = [], [], [], []
    for t in tar["testler"]:
        harf, siyahlar = [], []
        for n in anahtarli_sayfalar(tar, t):
            y0, y1, x0, x1 = tar["sayfalar"][str(n)]["anahtar"]
            a = ortak.kart(p, d, n)
            s = a[y0 + 1 : y1, x0 + 1 : x1]
            mx, mn = s.max(axis=2), s.min(axis=2)
            siyah = (mn < p.GLIF_HARF_ESIK) & (mx - mn < 45)
            for o in _harf_bloblari(p, s):
                harf.append(o)
                siyahlar.append(siyah)
        cells = A[t["test"]]["hucreler"]
        if len(harf) != len(cells):
            kapsam_disi.append([t["test"], len(harf), len(cells)])
            continue
        for o, siyah, (no, h) in zip(harf, siyahlar, cells, strict=True):
            g = siyah[o].astype(np.uint8) * 255
            v = (
                np.asarray(
                    Image.fromarray(g).resize((8, 9), Image.Resampling.BILINEAR), float
                ).ravel()
                / 255
            )
            vek.append(v)
            etiket.append(h)
            yer.append([t["test"], no])
    X = np.array(vek)
    uyum, uyumsuz = 0, []
    for i in range(len(X)):
        dd = ((X - X[i]) ** 2).sum(axis=1)
        dd[i] = 1e9
        j = int(dd.argmin())
        if etiket[j] == etiket[i]:
            uyum += 1
        else:
            uyumsuz.append([yer[i], etiket[i], etiket[j], round(float(dd[j]), 3)])
    sonuc = {
        "hucre": len(X),
        "uyum": uyum,
        "uyumsuz": uyumsuz,
        "kapsam_disi": kapsam_disi,
    }
    (serit_dizini(p) / "glif.json").write_text(json.dumps(sonuc), "utf-8")
    print("segment", len(X), "LOO uyum", uyum, "uyumsuz", uyumsuz)
    print("kapsam disi", kapsam_disi)
    return sonuc


def ab_karsilastir(p: ModuleType) -> list[str]:
    o = serit_dizini(p)
    A = {
        x["test"]: x
        for x in json.loads((o / "okuma_A.json").read_text("utf-8"))["testler"]
    }
    B = {
        x["test"]: x
        for x in json.loads((o / "okuma_B.json").read_text("utf-8"))["testler"]
    }
    tar = ortak.oku(p, "capa_taramasi")
    out = []
    if sorted(A) != sorted(B) or sorted(A) != [t["test"] for t in tar["testler"]]:
        out.append(f"test kumeleri: A {len(A)} B {len(B)}")
    for t in tar["testler"]:
        i = t["test"]
        if A.get(i, {}).get("hucreler") != B.get(i, {}).get("hucreler"):
            out.append(f"test {i}: hucre A != B")
        for k in ("konu", "test_no"):
            if A.get(i, {}).get(k) != B.get(i, {}).get(k):
                out.append(
                    f"test {i}: {k} A {A.get(i, {}).get(k)!r} B {B.get(i, {}).get(k)!r}"
                )
        if i in A and len(A[i]["hucreler"]) != len(t["capalar"]):
            out.append(
                f"test {i}: hucre {len(A[i]['hucreler'])} != capa {len(t['capalar'])}"
            )
    return out


def ham_yaz(p: ModuleType, goz_teyit: dict[str, str], goz_c: dict[str, str]) -> None:
    o = serit_dizini(p)
    A = json.loads((o / "okuma_A.json").read_text("utf-8"))
    B = json.loads((o / "okuma_B.json").read_text("utf-8"))
    G = json.loads((o / "glif.json").read_text("utf-8"))
    veri = {
        "kaynak": p.KAYNAK_ADI,
        "nereden": p.ANAHTAR_NEREDEN,
        "okuma_a": {
            "yontem": "3x Lanczos anahtar kirpimi; bagimsiz okuyucu (ileri); hucre sayisi SOYLENMEDI",
            "testler": A["testler"],
        },
        "okuma_b": {
            "yontem": "3x Lanczos anahtar kirpimi; bagimsiz okuyucu (geri), A'yi gormeden",
            "testler": B["testler"],
        },
        "glif": {
            "yontem": (
                "Anahtar bolgesinde notr koyu harf glifi (min < GLIF_HARF_ESIK, renk farki < 45, "
                "dikey 2 px genisletme), satir/sutun sirasiyla hucrelere; 8x9 vektor, "
                "en-yakin-komsu birini-disarida-birak. Blob sayisi hucreye esit olmayan test kapsam disi."
            ),
            "hucre": G["hucre"],
            "uyum": G["uyum"],
            "uyumsuz": G["uyumsuz"],
            "goz_teyit": goz_teyit,
            "goz_teyit_yontem": "5x nearest anahtar kirpimi, gozle",
            "kapsam_disi_test": [x[0] for x in G["kapsam_disi"]],
        },
        "goz_c": {
            "yontem": "glif kapsami disindaki testler 5x (nearest) anahtar kirpiminda gozle",
            "testler": goz_c,
        },
    }
    ortak.yaz(p, "ham_okumalar", veri, girinti=1)
    print("ham yazildi")


def dogrula(p: ModuleType, ham: dict[str, Any]) -> list[str]:
    hata = []
    a = {t["test"]: t["hucreler"] for t in ham["okuma_a"]["testler"]}
    b = {t["test"]: t["hucreler"] for t in ham["okuma_b"]["testler"]}
    if set(a) != set(b):
        hata.append("A ve B test kumeleri farkli")
    for t in sorted(a):
        if a[t] != b.get(t):
            hata.append(f"test {t}: A != B")
        if [n for n, _ in a[t]] != list(range(1, len(a[t]) + 1)):
            hata.append(f"test {t}: numaralar 1..N degil")
        if any(h not in HARFLER for _, h in a[t]):
            hata.append(f"test {t}: A-E disi harf")
    glif_disi = set(ham["glif"]["kapsam_disi_test"])
    teyit = ham["glif"].get("goz_teyit", {})
    uyumsuz = {f"T{u[0][0]:03d}#{u[0][1]}" for u in ham["glif"]["uyumsuz"]}
    if uyumsuz != set(teyit):
        hata.append(f"glif uyumsuz {sorted(uyumsuz)} != goz teyidi {sorted(teyit)}")
    for k, h in teyit.items():
        tn, no = (int(x) for x in k[1:].split("#"))
        if dict(a.get(tn, []))[no] != h:
            hata.append(f"{k}: goz teyidi {h} != okuma")
    kapsam = sum(len(a[t]) for t in a if t not in glif_disi)
    if (
        kapsam != ham["glif"]["hucre"]
        or ham["glif"]["uyum"] + len(teyit) != ham["glif"]["hucre"]
    ):
        hata.append(f"glif kapsami {ham['glif']['hucre']} != {kapsam}")
    goz = {int(k): v for k, v in ham["goz_c"]["testler"].items()}
    if set(goz) != glif_disi:
        hata.append(f"goz_c testleri {sorted(goz)} != glif disi {sorted(glif_disi)}")
    for t, s in goz.items():
        if s != "".join(h for _, h in a[t]):
            hata.append(f"test {t}: goz_c != okuma")
    return hata


def cevaplar_uret(
    p: ModuleType, ham: dict[str, Any], tarama: dict[str, Any]
) -> list[dict[str, Any]]:
    a = {t["test"]: t["hucreler"] for t in ham["okuma_a"]["testler"]}
    out = []
    for t in tarama["testler"]:
        capa = t["capalar"]
        if len(capa) != len(a[t["test"]]):
            raise ValueError(
                f"test {t['test']}: capa {len(capa)} != anahtar {len(a[t['test']])}"
            )
        sira: Counter[tuple[int, str]] = Counter()
        for (no, harf), c in zip(a[t["test"]], capa, strict=True):
            k = (c["dosya"], c["sutun"])
            out.append(
                {
                    "birim": ortak.birim_kodu(p, t["test"]),
                    "soru": no,
                    "cevap": harf,
                    "dosya": c["dosya"],
                    "sutun": c["sutun"],
                    "sutun_sira": sira[k],
                }
            )
            sira[k] += 1
    return out


def anahtar_yaz(p: ModuleType) -> None:
    ham = ortak.oku(p, "ham_okumalar")
    tarama = ortak.oku(p, "capa_taramasi")
    hata = dogrula(p, ham)
    print(f"kapi ihlali: {len(hata)}")
    for h in hata[:20]:
        print("   ", h)
    if hata:
        raise SystemExit(1)
    cev = cevaplar_uret(p, ham, tarama)
    dag = Counter(c["cevap"] for c in cev)
    print(
        f"{len(cev)} cevap, {len(tarama['testler'])} test, dagilim {dict(sorted(dag.items()))}"
    )
    veri = {
        "kaynak": p.KAYNAK_ADI,
        "arac": "scripts/kitap/kitap_hat/anahtar.py",
        "nereden": p.ANAHTAR_NEREDEN,
        "dogrulama": {
            "a_esittir_b_hucre": sum(
                len(t["hucreler"]) for t in ham["okuma_a"]["testler"]
            ),
            "glif_loo_uyum": ham["glif"]["uyum"],
            "glif_goz_teyit": len(ham["glif"].get("goz_teyit", {})),
            "goz_c_hucre": sum(len(v) for v in ham["goz_c"]["testler"].values()),
            "hucre_sayisi_esittir_capa": True,
        },
        "toplam_cevap": len(cev),
        "test_sayisi": len(tarama["testler"]),
        "harf_dagilimi": dict(sorted(dag.items())),
        "cevaplar": cev,
    }
    ortak.yaz(p, "cevap_anahtari", veri)
    print("yazildi")


def _anahtar_deger(ciftler: list[str]) -> dict[str, str]:
    out = {}
    for c in ciftler:
        k, v = c.split("=")
        out[k] = v
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    alt = ap.add_subparsers(dest="komut", required=True)
    alt.add_parser("hazirla")
    alt.add_parser("glif")
    alt.add_parser("karsilastir")
    h = alt.add_parser("ham")
    h.add_argument("--goz-teyit", nargs="*", default=[], help="T005#3=C")
    h.add_argument("--goz-c", nargs="*", default=[], help="16=ABCD...")
    alt.add_parser("yaz")
    a = ap.parse_args()
    p = ortak.profil(a.profil)
    if a.komut == "hazirla":
        hazirla(p)
    elif a.komut == "glif":
        glif(p)
    elif a.komut == "karsilastir":
        fark = ab_karsilastir(p)
        print("fark", len(fark))
        for f in fark:
            print("  ", f)
    elif a.komut == "ham":
        ham_yaz(p, _anahtar_deger(a.goz_teyit), _anahtar_deger(a.goz_c))
    else:
        anahtar_yaz(p)


if __name__ == "__main__":
    main()
