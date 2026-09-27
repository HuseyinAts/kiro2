#!/usr/bin/env python
"""2020-2021 ACIL TYT Matematik: kirpim kutularindan soru gorselleri + ortme olcumu.

Gorseller git'e girmez; her kutu `acil_2021_tyt_matematik_kirpim_kutulari.json`
icinde durdugu icin her ortamda yeniden uretilir (acil25_geo_kirp.py deseni).

OKUYUCU DISKI BEYAZLATILIR
--------------------------
Sayfa zemini krem (255,254,247). FERNUS diski (lila 240,238,247 / glif
69,39,160 / notr gri golge / mor-lila kenar karisimlari) simge merkezi
etrafinda BEYAZ_YARICAP icinde ve YALNIZ okuyucu renklerinde beyazlatilir;
kitabin siyah metnine ve kirmizi/mavi cizimlerine dokunulmaz. Disk
geometrisi acil1920tyt'de olculdu (s37, s56): merkez (gy + 5, gx), yaricap
26; bu kitapta ayni okuyucu ve ayni simge -- beyazlatilmis kirpimlar gozle
kontrol edildi (s6, s54; kenar kapisi 0).

ORTME OLCUMU
------------
Disk opaktir; altinda kalan kitap icerigi goruntude YOKTUR. Beyazlatmadan
ONCE diskin disindaki halkada (yaricap HALKA) kitap murekkebi aranir;
diskin sagindaki 90 derece haric (sorunun kendi numarasi). Bu kitapta sag
sutun simgesi sutunlar arasinda durdugu icin SOL sutun metninin satir
sonlarini ortuyor (316 soru). Halka pikseli >= ORTME_ESIK dusen kirpim
`ortme` ile raporlanir; okuyucu ortulen karakteri [??] yazar, tahmin etmez.

KULLANIM
--------
    python backend/scripts/kitap/acil2021tyt_kirp.py [--ornek N] [--cikti DIZIN]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK = "acil_2021_tyt_matematik_"
KUTULAR = CIKTI / f"{ONEK}kirpim_kutulari.json"
TARAMA = CIKTI / f"{ONEK}capa_taramasi.json"
RAPOR = CIKTI / f"{ONEK}ortme_olcumu.json"
KLASOR = "2020-2021-AC\u0130L-TYT Matematik Soru Bankas\u0131"
KART = (589, 43, 1331, 1022)
BEKLENEN_BOYUT = (1920, 1080)
BEKLENEN_SAYFA = 448
BEKLENEN_KUTU = 2113
MERKEZ = (5, 0)  # simge glifinin sol-ust kosesine gore disk merkezi (dy, dx)
BEYAZ_YARICAP = 26
GLIF_RENK = (69, 39, 160)
DISK_RENK = (240, 238, 247)
GLIF_ESIK = 120
DISK_ESIK = 40
GOLGE_EN_AZ = 215
GOLGE_FARK = 12
MOR_FARK = 18
SOL_GRI = 185
KOYU = 160
KENAR_EN_COK = 3
HALKA = (17, 21)
ORTME_ESIK = 4
LEKE = (880, 320, 440)  # sayfa no lekesi penceresi: y >= 880, x 320..440 (kart koord.)
LEKE_DOYGUN = 60


def kaynak_dizin() -> Path:
    d = KOK / "veriseti" / "zkitap" / "screenshots" / KLASOR
    n = len(list(d.glob("sayfa_*.png")))
    if n != BEKLENEN_SAYFA:
        raise SystemExit(f"kaynak sayfa sayisi {n} != {BEKLENEN_SAYFA}")
    return d


def merkezler(glif: list[list[int]]) -> list[list[int]]:
    return [[gy + MERKEZ[0], gx + MERKEZ[1]] for gy, gx in glif]


def _okuyucu_rengi(a: np.ndarray) -> np.ndarray:
    ai = a.astype(np.int16)
    fark_glif = np.abs(ai - np.array(GLIF_RENK)).sum(axis=2)
    fark_disk = np.abs(ai - np.array(DISK_RENK)).sum(axis=2)
    enb, enk = ai.max(axis=2), ai.min(axis=2)
    golge = (enb - enk < GOLGE_FARK) & (enb >= GOLGE_EN_AZ)
    r, gg, bb = ai[..., 0], ai[..., 1], ai[..., 2]
    mor = (bb - r > MOR_FARK) & (bb - gg > MOR_FARK) & (r >= gg - 8)
    renk: np.ndarray = (fark_glif < GLIF_ESIK) | (fark_disk < DISK_ESIK) | golge | mor
    return renk


def _pencere(shape: tuple[int, ...], gy: int, gx: int, r: int):
    y0, y1 = max(0, gy - r), min(shape[0], gy + r + 1)
    x0, x1 = max(0, gx - r), min(shape[1], gx + r + 1)
    yy, xx = np.ogrid[y0:y1, x0:x1]
    return (
        (slice(y0, y1), slice(x0, x1)),
        np.hypot(yy - gy, xx - gx),
        np.arctan2(yy - gy, xx - gx),
        (xx - gx) + 0 * yy,
    )


def okuyucu_maskesi(a: np.ndarray, merkez: list[list[int]]) -> np.ndarray:
    """Kart koordinatli goruntude okuyucu katmani pikselleri (konum + renk)."""
    maske = np.zeros(a.shape[:2], bool)
    renk = _okuyucu_rengi(a)
    ai = a.astype(np.int16)
    notr = (ai.max(axis=2) - ai.min(axis=2) < GOLGE_FARK) & (ai.max(axis=2) >= SOL_GRI)
    for gy, gx in merkez:
        sl, r, _, dx = _pencere(a.shape, gy, gx, BEYAZ_YARICAP + 2)
        maske[sl] |= (r <= BEYAZ_YARICAP) & (renk[sl] | ((dx < -5) & notr[sl]))
    return maske


def ortme_halkalari(a: np.ndarray, merkez: list[list[int]]) -> list[dict]:
    """Beyazlatmadan ONCE: diskin disindaki halkada kitap murekkebi."""
    koyu = (a.min(axis=2) < KOYU) & ~_okuyucu_rengi(a)
    out = []
    for gy, gx in merkez:
        sl, r, aci, _ = _pencere(a.shape, gy, gx, HALKA[1] + 1)
        halka = (r >= HALKA[0]) & (r <= HALKA[1]) & (np.abs(aci) > np.pi / 4)
        ys, xs = np.where(halka & koyu[sl])
        if len(ys) >= ORTME_ESIK:
            out.append(
                {
                    "simge": [gy, gx],
                    "ys": (ys + sl[0].start).tolist(),
                    "xs": (xs + sl[1].start).tolist(),
                }
            )
    return out


def beyaz_sayfa(
    kaynak: Path, n: int, glif: list[list[int]]
) -> tuple[np.ndarray, list[dict]]:
    img = Image.open(kaynak / f"sayfa_{n:04d}.png").convert("RGB")
    if img.size != BEKLENEN_BOYUT:
        raise SystemExit(f"BOYUT UYUSMAZLIGI s{n}: {img.size}")
    a = np.array(img.crop(KART))
    m = merkezler(glif)
    halka = ortme_halkalari(a, m)
    a[okuyucu_maskesi(a, m)] = 255
    a[sayfa_no_lekesi(a)] = 255
    return a, halka


def sayfa_no_lekesi(a: np.ndarray) -> np.ndarray:
    """Sayfa numarasi rozetinin mavi/kirmizi firca lekesi (susleme, icerik degil).

    Olculdu (s6, s7): leke uclari y ~895'e kadar cikar, SAYFA_ALTI 904 oldugu
    icin sutun sonundaki kirpimin altina girer. Yalniz LEKE penceresinde ve
    yalniz doygun renkli (max-min > LEKE_DOYGUN) pikseller beyazlatilir.
    """
    ai = a.astype(np.int16)
    m = np.zeros(a.shape[:2], bool)
    y0, x0, x1 = LEKE
    m[y0:, x0:x1] = (ai.max(axis=2) - ai.min(axis=2))[y0:, x0:x1] > LEKE_DOYGUN
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ornek", type=int, default=0)
    ap.add_argument("--cikti", default=str(KOK / "backend" / "_a21_gecici" / "kirpim"))
    ap.add_argument("--rapor", default=str(RAPOR))
    args = ap.parse_args()
    veri = json.loads(KUTULAR.read_text("ascii"))
    kutular = veri["kutular"]
    if len(kutular) != BEKLENEN_KUTU:
        raise SystemExit(f"kutu sayisi {len(kutular)} != {BEKLENEN_KUTU}")
    if args.ornek:
        kutular = kutular[: args.ornek]
    tarama = json.loads(TARAMA.read_text("ascii"))
    kaynak = kaynak_dizin()
    out = Path(args.cikti)
    out.mkdir(parents=True, exist_ok=True)
    sayfada: dict[int, list[dict]] = {}
    for k in kutular:
        sayfada.setdefault(k["dosya"], []).append(k)
    kenar, ortme = [], []
    for p in sorted(sayfada):
        a, halkalar = beyaz_sayfa(kaynak, p, tarama["sayfalar"][str(p)]["glif"])
        g = a.min(axis=2)
        for k in sayfada[p]:
            x0, y0, x1, y1 = k["kutu"]
            sol = int((g[y0:y1, x0 : x0 + 2] < KOYU).sum())
            sag = int((g[y0:y1, x1 - 2 : x1] < KOYU).sum())
            if sol > KENAR_EN_COK or sag > KENAR_EN_COK:
                kenar.append(
                    {
                        "birim": k["birim"],
                        "soru": k["soru"],
                        "dosya": p,
                        "sol": sol,
                        "sag": sag,
                    }
                )
            for h in halkalar:
                icte = sum(
                    1
                    for yy, xx in zip(h["ys"], h["xs"], strict=True)
                    if x0 <= xx < x1 and y0 <= yy < y1
                )
                if icte >= ORTME_ESIK:
                    ortme.append(
                        {
                            "birim": k["birim"],
                            "soru": k["soru"],
                            "dosya": p,
                            "simge": h["simge"],
                            "piksel": icte,
                        }
                    )
            Image.fromarray(a[y0:y1, x0:x1]).save(
                out / f"{k['birim']}_{k['soru']:02d}.png"
            )
    n = sum(len(v) for v in sayfada.values())
    osoru = len({(o["birim"], o["soru"]) for o in ortme})
    print(
        f"uretildi {n} gorsel -> {out}; kenar {len(kenar)}; ortme {len(ortme)} halka / {osoru} soru"
    )
    for x in kenar[:15]:
        print("   kenar", x)
    if args.rapor and not args.ornek:
        Path(args.rapor).write_text(
            json.dumps(
                {
                    "kaynak": "2020-2021 ACIL TYT Matematik Soru Bankasi",
                    "arac": "scripts/kitap/acil2021tyt_kirp.py",
                    "ne_olculdu": (
                        f"Beyazlatmadan ONCE her okuyucu diskinin disindaki halkada (yaricap {HALKA[0]}-"
                        f"{HALKA[1]}, sag 90 derece haric) koyu (< {KOYU}) kitap murekkebi. Kirpima >= "
                        f"{ORTME_ESIK} halka pikseli dusen soru 'ortme' tasir. Disk opak; altindaki icerik "
                        "goruntude yoktur."
                    ),
                    "kenar_kapisi_ihlali": len(kenar),
                    "ortme_soru": osoru,
                    "kenar": kenar,
                    "ortme": ortme,
                },
                indent=0,
            )
            + "\n",
            "ascii",
        )


if __name__ == "__main__":
    main()
