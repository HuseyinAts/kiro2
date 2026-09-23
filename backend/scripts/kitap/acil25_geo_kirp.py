#!/usr/bin/env python
"""ACIL 2025 KURS TYT-AYT Geometri: kirpim kutularindan soru gorselleri uretir.

Gorseller git'e girmez (`veriseti/` .gitignore'da); her kutu
`acil_2025_geometri_kirpim_kutulari.json` icinde durdugu icin her ortamda
yeniden uretilebilir (orijinal_geo_kirp.py ile ayni desen).

OKUYUCU DISKI BEYAZLATILIR
--------------------------
FERNUS okuyucu diski (lila 240,238,247 / glif 69,39,160 / acik gri golge /
mor-lila kenar karisimlari) bilinen simge KONUMLARININ etrafindaki daire
icinde ve yalniz okuyucu RENKLERINDE beyazlatilir; kitabin siyah metnine ve
kirmizi/mavi cizimlerine dokunulmaz. Olculen disk: glif merkezine gore
y -15..+14, x -14..+13; golge yaricapi cogunlukla 22-26 -> BEYAZ_YARICAP 26.

ORTME OLCUMU (sahip karari: yeniden yakalama yok, ortulen satir isaretlenir)
--------------------------------------------------------------------------
Disk opaktir; altinda kalan kitap icerigi goruntude YOKTUR. Beyazlatmadan
ONCE, diskin hemen disindaki halkada (yaricap 15-19) kitap murekkebi aranir;
diskin sagindaki 90 derecelik dilim haric (orada sorunun kendi numarasi
durur). Halkada >= ORTME_ESIK koyu piksel varsa metin/sekil diskin altina
giriyor demektir ve halkanin dustugu kirpim `ortme_suphesi` ile raporlanir.

KENAR KAPISI
------------
Kirpimin sol/sag en dis 2 piksel sutununda koyu murekkep varsa (metin ya
da sekil kutu sinirindan tasiyor olabilir) kutu raporlanir.

KULLANIM
--------
    python backend/scripts/kitap/acil25_geo_kirp.py
    python backend/scripts/kitap/acil25_geo_kirp.py --ornek 40
    python backend/scripts/kitap/acil25_geo_kirp.py --cikti <dizin> --rapor <json>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KUTULAR = CIKTI / "acil_2025_geometri_kirpim_kutulari.json"
SIMGELER = CIKTI / "acil_2025_geometri_simge_taramasi.json"

KART = (593, 46, 593 + 734, 46 + 968)
BEKLENEN_BOYUT = (1920, 1080)
BEKLENEN_SAYFA = 400
BEKLENEN_KUTU = 1948
BEYAZ_YARICAP = 26
GLIF_RENK = (69, 39, 160)
DISK_RENK = (240, 238, 247)
GLIF_ESIK = 120
DISK_ESIK = 40
GOLGE_EN_AZ = 225
GOLGE_FARK = 12
MOR_FARK = 18
SOL_GRI = 185
KOYU = 160
KENAR_EN_COK = 3
HALKA = (15, 19)
ORTME_ESIK = 4


def _kaynak_dizin() -> Path:
    """Kaynak dizini SECMEZ, DOGRULAR: dar desen, tek eslesme, sayfa sayisi."""
    adaylar = [
        p
        for p in (KOK / "veriseti" / "zkitap" / "screenshots").iterdir()
        if p.is_dir()
        and p.name.startswith("AC")
        and p.name.endswith("TYT-AYT-Geometri Soru Bankas\u0131")
    ]
    if len(adaylar) != 1:
        raise SystemExit(f"Kaynak dizin tek degil: {[a.name for a in adaylar]}")
    sayfa = len(list(adaylar[0].glob("sayfa_*.png")))
    if sayfa != BEKLENEN_SAYFA:
        raise SystemExit(f"Kaynak sayfa sayisi {sayfa} != {BEKLENEN_SAYFA}")
    return adaylar[0]


def _okuyucu_rengi(a: np.ndarray) -> np.ndarray:
    ai = a.astype(np.int16)
    fark_glif = np.abs(ai - np.array(GLIF_RENK)).sum(axis=2)
    fark_disk = np.abs(ai - np.array(DISK_RENK)).sum(axis=2)
    enb, enk = ai.max(axis=2), ai.min(axis=2)
    golge = (enb - enk < GOLGE_FARK) & (enb >= GOLGE_EN_AZ)
    # Glif/disk kenarinin anti-alias karisimlari: mor-lila ton ailesi (mavi
    # baskin, kirmizi >= yesil). Mavi/camgobegi cizgiler (yesil > kirmizi)
    # ve kirmizi/pembe girmez. Olculdu: d7 sol #2 kirpiminin sag kenarinda
    # (145,128,198) / (209,202,231) kalintisi.
    r, gg, bb = ai[..., 0], ai[..., 1], ai[..., 2]
    mor = (bb - r > MOR_FARK) & (bb - gg > MOR_FARK) & (r >= gg - 8)
    return (fark_glif < GLIF_ESIK) | (fark_disk < DISK_ESIK) | golge | mor


def _pencere(shape: tuple[int, ...], gy: int, gx: int, r: int):
    """Simge etrafindaki yerel pencere: dilim + pencere-ici uzaklik/aci/dx."""
    y0, y1 = max(0, gy - r), min(shape[0], gy + r + 1)
    x0, x1 = max(0, gx - r), min(shape[1], gx + r + 1)
    yy, xx = np.ogrid[y0:y1, x0:x1]
    return (
        (slice(y0, y1), slice(x0, x1)),
        np.hypot(yy - gy, xx - gx),
        np.arctan2(yy - gy, xx - gx),
        (xx - gx) + 0 * yy,
    )


def okuyucu_maskesi(a: np.ndarray, simgeler: list[list[int]]) -> np.ndarray:
    """Kart koordinatli goruntude okuyucu katmani pikselleri (konum + renk).

    Ek kural (yalniz diskin SOL yarisinda, dx < -5): golgenin daha koyu
    notr gri kenari (max >= SOL_GRI). Diskin saginda sorunun kendi numarasi
    oldugu icin orada uygulanmaz. Olculdu: d18/d19 sol sutun kirpimlarinin
    sag kenarinda sag sutun diskinin gri yay kalintisi.
    """
    maske = np.zeros(a.shape[:2], bool)
    renk = _okuyucu_rengi(a)
    ai = a.astype(np.int16)
    notr = (ai.max(axis=2) - ai.min(axis=2) < GOLGE_FARK) & (ai.max(axis=2) >= SOL_GRI)
    for gy, gx in simgeler:
        sl, r, _, dx = _pencere(a.shape, gy, gx, BEYAZ_YARICAP + 2)
        maske[sl] |= (r <= BEYAZ_YARICAP) & (renk[sl] | ((dx < -5) & notr[sl]))
    return maske


def ortme_halkalari(a: np.ndarray, simgeler: list[list[int]]) -> list[dict]:
    """Beyazlatmadan ONCE: diskin disindaki halkada kitap murekkebi."""
    koyu = (a.min(axis=2) < KOYU) & ~_okuyucu_rengi(a)
    out = []
    for gy, gx in simgeler:
        sl, r, aci, _ = _pencere(a.shape, gy, gx, HALKA[1] + 1)
        halka = (r >= HALKA[0]) & (r <= HALKA[1]) & (np.abs(aci) > np.pi / 4)
        ys, xs = np.where(halka & koyu[sl])
        if len(ys) >= ORTME_ESIK:
            # Pikseller tek tek dondurulur: halka iki kirpima birden dusebilir
            # (sag sutun diskinin solu SOL sutun kirpiminda). Medyan konum
            # kullanmak d35'te isareti sutun arasina dusurup kaybetti.
            out.append(
                {
                    "simge": [gy, gx],
                    "ys": (ys + sl[0].start).tolist(),
                    "xs": (xs + sl[1].start).tolist(),
                }
            )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ornek", type=int, default=0, help="ilk N kutu (0=hepsi)")
    ap.add_argument(
        "--cikti", default=str(KOK / "backend" / "_geo1_gecici" / "a25_kirpim")
    )
    ap.add_argument(
        "--rapor",
        default=str(CIKTI / "acil_2025_geometri_ortme_olcumu.json"),
        help="kenar/ortme raporu JSON yolu ('' = yazma)",
    )
    args = ap.parse_args()

    veri = json.loads(KUTULAR.read_text("ascii"))
    kutular = veri["kutular"]
    if len(kutular) != BEKLENEN_KUTU:
        raise SystemExit(f"Kutu sayisi {len(kutular)} != {BEKLENEN_KUTU}")
    if args.ornek:
        kutular = kutular[: args.ornek]
    simge = json.loads(SIMGELER.read_text("ascii"))["sayfalar"]
    kaynak = _kaynak_dizin()
    outdir = Path(args.cikti)
    outdir.mkdir(parents=True, exist_ok=True)

    sayfada: dict[int, list[dict]] = {}
    for k in kutular:
        sayfada.setdefault(k["dosya"], []).append(k)
    kenar, ortme = [], []
    for p in sorted(sayfada):
        img = Image.open(kaynak / f"sayfa_{p:04d}.png").convert("RGB")
        if img.size != BEKLENEN_BOYUT:
            raise SystemExit(f"BOYUT UYUSMAZLIGI d{p}: {img.size}")
        a = np.array(img.crop(KART))
        s = simge.get(str(p), [])
        halkalar = ortme_halkalari(a, s)
        a[okuyucu_maskesi(a, s)] = 255
        g = a.min(axis=2)
        for k in sayfada[p]:
            x0, y0, x1, y1 = k["kutu"]
            c = a[y0:y1, x0:x1]
            sol = int((g[y0:y1, x0 : x0 + 2] < KOYU).sum())
            sag = int((g[y0:y1, x1 - 2 : x1] < KOYU).sum())
            if sol > KENAR_EN_COK or sag > KENAR_EN_COK:
                kenar.append(
                    {
                        "birim": k["birim"],
                        "soru": k["soru"],
                        "dosya": p,
                        "sutun": k["sutun"],
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
                            "sutun": k["sutun"],
                            "simge": h["simge"],
                            "piksel": icte,
                        }
                    )
            Image.fromarray(c).save(outdir / f"{k['birim']}_{k['soru']:02d}.png")
    print(f"uretildi {sum(len(v) for v in sayfada.values())} soru gorseli -> {outdir}")
    print(f"kenar kapisi: {len(kenar)} kutu")
    for x in kenar[:15]:
        print("   ", x)
    print(
        f"ortme suphesi: {len(ortme)} halka, "
        f"{len({(o['birim'], o['soru']) for o in ortme})} soru"
    )
    if args.rapor:
        rapor = {
            "kaynak": "ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi",
            "arac": "scripts/kitap/acil25_geo_kirp.py",
            "ne_olculdu": (
                "Beyazlatmadan ONCE, her okuyucu diskinin disindaki halkada (yaricap "
                f"{HALKA[0]}-{HALKA[1]} px, diskin sagindaki 90 derece haric) koyu (< {KOYU}) "
                "kitap murekkebi. Bir kirpimin icine >= "
                f"{ORTME_ESIK} halka pikseli dusuyorsa o soru 'ortme suphesi' tasir: metin ya "
                "da sekil diskin altina giriyor olabilir. Disk opak; altindaki icerik "
                "goruntude yoktur."
            ),
            "tam_kitap": not args.ornek,
            "kenar_kapisi_ihlali": len(kenar),
            "ortme_suphesi_soru": len({(o["birim"], o["soru"]) for o in ortme}),
            "kenar": kenar,
            "ortme": ortme,
        }
        Path(args.rapor).write_text(
            json.dumps(rapor, indent=0) + "\n", encoding="ascii", newline="\n"
        )


if __name__ == "__main__":
    main()
