#!/usr/bin/env python
"""345 2025 AYT Turk Edebiyati: kirpim kutularindan soru ve ortak metin gorselleri uretir.

Gorseller git'e girmez; her kutu `345_2025_ayt_edebiyat_kirpim_kutulari.json`
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
Kirpimin sol/sag en dis 2 piksel sutununda koyu murekkep varsa rapor.

KULLANIM
--------
    python backend/scripts/kitap/edb345ayt_kirp.py
    python backend/scripts/kitap/edb345ayt_kirp.py --ornek 40
    python backend/scripts/kitap/edb345ayt_kirp.py --cikti <dizin> --rapor <json>
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
from edb345ayt_tarama import cerceve_maskesi, kart, kaynak_dizin

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KUTULAR = CIKTI / "345_2025_ayt_edebiyat_kirpim_kutulari.json"
TARAMA = CIKTI / "345_2025_ayt_edebiyat_capa_taramasi.json"
BEKLENEN_KUTU = 1384
KOYU = 160
KENAR_EN_COK = 3


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ornek", type=int, default=0, help="ilk N kutu (0=hepsi)")
    ap.add_argument(
        "--cikti", default=str(KOK / "backend" / "_e345_gecici" / "e_kirpim")
    )
    ap.add_argument(
        "--rapor",
        default=str(CIKTI / "345_2025_ayt_edebiyat_ortme_olcumu.json"),
        help="kenar/ortme raporu JSON yolu ('' = yazma)",
    )
    args = ap.parse_args()
    kutular = json.loads(KUTULAR.read_text("ascii"))["kutular"]
    if len(kutular) != BEKLENEN_KUTU:
        raise SystemExit(f"Kutu sayisi {len(kutular)} != {BEKLENEN_KUTU}")
    if args.ornek:
        kutular = kutular[: args.ornek]
    tarama = json.loads(TARAMA.read_text("ascii"))["sayfalar"]
    kaynak = kaynak_dizin()
    outdir = Path(args.cikti)
    outdir.mkdir(parents=True, exist_ok=True)
    sayfada: dict[int, list[dict]] = {}
    for k in kutular:
        sayfada.setdefault(k["dosya"], []).append(k)
    kenar, ortme = [], []
    for p in sorted(sayfada):
        a = kart(kaynak, p).astype(np.uint8)
        s = [[x[2], x[3]] for x in tarama[str(p)]["simge"]]
        halkalar = ortme_halkalari(a, s)
        a[okuyucu_maskesi(a, s)] = 255
        a[cerceve_maskesi(a, p)] = 255
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
            Image.fromarray(a[y0:y1, x0:x1]).save(
                outdir / f"{k['birim']}_{k['soru']:02d}.png"
            )
    # Ortak metin kutulari (kirmizi baslikli parca; edb345ayt_kutu.ortak_basliklari).
    ortaklar = json.loads(KUTULAR.read_text("ascii"))["ortak_metinler"]
    if not args.ornek:
        for o in ortaklar:
            a = kart(kaynak, o["dosya"]).astype(np.uint8)
            s = [[x[2], x[3]] for x in tarama[str(o["dosya"])]["simge"]]
            a[okuyucu_maskesi(a, s)] = 255
            x0, y0, x1, y1 = o["kutu"]
            Image.fromarray(a[y0:y1, x0:x1]).save(outdir / f"{o['ortak']}.png")
        print(f"ortak metin gorseli: {len(ortaklar)}")
    n_ortme = len({(o["birim"], o["soru"]) for o in ortme})
    print(f"uretildi {sum(len(v) for v in sayfada.values())} soru gorseli -> {outdir}")
    print(f"kenar kapisi: {len(kenar)} kutu")
    for x in kenar[:15]:
        print("   ", x)
    print(f"ortme suphesi: {len(ortme)} halka, {n_ortme} soru")
    if args.rapor:
        rapor = {
            "kaynak": "345 2025 AYT Turk Edebiyati Soru Bankasi",
            "arac": "scripts/kitap/edb345ayt_kirp.py",
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
