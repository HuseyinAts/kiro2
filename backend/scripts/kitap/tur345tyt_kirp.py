#!/usr/bin/env python
"""345 2025 TYT Turkce: kirpim kutularindan soru gorselleri uretir (prg345_kirp deseni).

Gorseller git'e girmez; her kutu `345_2025_tyt_turkce_kirpim_kutulari.json`
icinde durdugu icin her ortamda yeniden uretilebilir (acil25_geo_kirp.py
deseni; okuyucu maskesi ve ortme halkasi olcumu oradan ORTAK kullanilir).

OKUYUCU DISKI BEYAZLATILIR
--------------------------
Sayfadaki TUM tarama simgeleri (soru simgeleri + sutun disindaki / kutu
kenarindaki simgeler) etrafinda, yalniz okuyucu RENKLERINDE beyazlatma.

ORTME OLCUMU
------------
Beyazlatmadan ONCE diskin disindaki halkada kitap murekkebi aranir
(acil25_geo_kirp.ortme_halkalari); kirpimin icine >= ORTME_ESIK halka
pikseli dusen soru 'ortme suphesi' ile raporlanir. Disk opaktir; altindaki
icerik goruntude YOKTUR, tahmin edilmez.

KENAR KAPISI
------------
Kirpimin sol/sag en dis 2 piksel sutununda koyu NOTR murekkep (doygunluk <
NOTR_DOYGUNLUK) varsa rapor; renkli sekil / cerceve sayilmaz.

KULLANIM
--------
    python backend/scripts/kitap/tur345tyt_kirp.py
    python backend/scripts/kitap/tur345tyt_kirp.py --ornek 40
    python backend/scripts/kitap/tur345tyt_kirp.py --cikti <dizin> --rapor <json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acil25_geo_kirp import ORTME_ESIK, okuyucu_maskesi, ortme_halkalari
from tur345tyt_tarama import kart, kaynak_dizin

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KUTULAR = CIKTI / "345_2025_tyt_turkce_kirpim_kutulari.json"
TARAMA = CIKTI / "345_2025_tyt_turkce_capa_taramasi.json"
BEKLENEN_KUTU = 2070
KOYU = 160
KENAR_EN_COK = 3
NOTR_DOYGUNLUK = 60


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ornek", type=int, default=0, help="ilk N kutu (0=hepsi)")
    ap.add_argument(
        "--cikti", default=str(KOK / "backend" / "_p345_gecici" / "tt" / "kirpim")
    )
    ap.add_argument(
        "--rapor",
        default=str(CIKTI / "345_2025_tyt_turkce_ortme_olcumu.json"),
        help="kenar/ortme raporu JSON yolu ('' = yazma)",
    )
    args = ap.parse_args()
    kutular = json.loads(KUTULAR.read_text("ascii"))["kutular"]
    if len(kutular) != BEKLENEN_KUTU:
        raise SystemExit(f"Kutu sayisi {len(kutular)} != {BEKLENEN_KUTU}")
    if args.ornek:
        kutular = kutular[: args.ornek]
    tt = json.loads(TARAMA.read_text("ascii"))
    tarama = tt["sayfalar"]
    disari = tt["sutun_disi_simge"] + tt["serit_simgesi"]
    kaynak = kaynak_dizin()
    outdir = Path(args.cikti)
    outdir.mkdir(parents=True, exist_ok=True)
    sayfada: dict[int, list[dict]] = {}
    for k in kutular:
        sayfada.setdefault(k["dosya"], []).append(k)
    kenar, ortme = [], []
    onbellek: dict[int, np.ndarray] = {}

    def maskeli(n: int) -> np.ndarray:
        if n not in onbellek:
            b = kart(kaynak, n).astype(np.uint8)
            s2 = [list(m) for t in "LR" for m in tarama[str(n)]["simge"][t]]
            s2 += [[cy, cx] for q, cy, cx in disari if q == n]
            b[okuyucu_maskesi(b, s2)] = 255
            onbellek[n] = b
        return onbellek[n]

    for p in sorted(sayfada):
        a = kart(kaynak, p).astype(np.uint8)
        s = [list(m) for t in "LR" for m in tarama[str(p)]["simge"][t]]
        s += [[cy, cx] for n, cy, cx in disari if n == p]
        halkalar = ortme_halkalari(a, s)
        a[okuyucu_maskesi(a, s)] = 255
        # Notr (siyah/gri) murekkep; renkli sekil kenarlari kapi disi.
        doy = a.max(axis=2).astype(np.int16) - a.min(axis=2)
        g = np.where(doy < NOTR_DOYGUNLUK, a.min(axis=2), 255)
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
            gorsel = a[y0:y1, x0:x1]
            o = k.get("ortak_parca")
            if o:
                # Ortak parca (grubun ilk sorusunun ust bolgesi) sorunun ustune
                # eklenir; aradaki 8 px beyaz.
                px0, py0, px1, py1 = o["kutu"]
                pa = maskeli(o["dosya"])[py0:py1, px0:px1]
                gen = max(pa.shape[1], gorsel.shape[1])
                tuval = np.full(
                    (pa.shape[0] + 8 + gorsel.shape[0], gen, 3), 255, np.uint8
                )
                tuval[: pa.shape[0], : pa.shape[1]] = pa
                tuval[pa.shape[0] + 8 :, : gorsel.shape[1]] = gorsel
                gorsel = tuval
            Image.fromarray(gorsel).save(outdir / f"{k['birim']}_{k['soru']:02d}.png")
    n_ortme = len({(o["birim"], o["soru"]) for o in ortme})
    print(f"uretildi {sum(len(v) for v in sayfada.values())} soru gorseli -> {outdir}")
    print(f"kenar kapisi: {len(kenar)} kutu")
    for x in kenar[:15]:
        print("   ", x)
    print(f"ortme suphesi: {len(ortme)} halka, {n_ortme} soru")
    if args.rapor:
        rapor = {
            "kaynak": "345 2025 TYT Turkce Soru Bankasi",
            "arac": "scripts/kitap/tur345tyt_kirp.py",
            "ne_olculdu": (
                "Beyazlatmadan ONCE her okuyucu diskinin disindaki halkada koyu kitap murekkebi "
                "(acil25_geo_kirp.ortme_halkalari). Kirpimin icine >= "
                f"{ORTME_ESIK} halka pikseli dusen soru 'ortme suphesi' tasir. Disk opak; altindaki "
                "icerik goruntude yoktur."
            ),
            "tam_kitap": not args.ornek,
            "kenar_kapisi_ihlali": len(kenar),
            "ortme_suphesi_soru": n_ortme,
            "kenar": kenar,
            "ortme": ortme,
        }
        Path(args.rapor).write_text(
            json.dumps(rapor, indent=0) + "\n", encoding="ascii", newline="\n"
        )


if __name__ == "__main__":
    main()
