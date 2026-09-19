#!/usr/bin/env python
"""Okuyucu simgesi ORTMESINI olcer -- dogru metrikle.

NEDEN BU SCRIPT VAR
-------------------
Faz 0'da uc kitapta ayni olcum kullanildi: "diskin ICINDE kitap murekkebi
var mi". Bu metrik ORTMEYI GOREMEZ. Disk opak; altinda kalan murekkep
goruntude zaten YOK. Metrik ancak diskin kenarindan tasan seyi (sutun
cizgisi, kutu kenari, filigran) sayar. ACIL 2023-2024'te bu yuzden
"soru icerigi 0" denildi; sonra dogru metrikle olculdu: 154 olay,
151 soru. 151 soru bu yuzden isleme alinamadi.

DOGRU METRIK: diskin hemen SOLUNDA/SAGINDA metin nerede bitiyor/basliyor.
Bir metin satiri diske 0-2 px kala bitiyorsa satir diskin ALTINA giriyor
demektir. Bol bir bosluk (ornek 9 px) varsa girmiyor.

NE URETIR
---------
Her simge icin iki uzaklik:
  sol_bosluk = (disk sol kenari) - (solundaki en yakin murekkep sutunu)
  sag_bosluk = (sagindaki en yakin murekkep sutunu) - (disk sag kenari)
ve bunlarin dagilimi. Dagilimin en kucuk degeri kitabin dizgi payidir;
0-2 px'e inen kuyruk ORTMEDIR.

Ayrica beyazlatma payi icin tavsiye uretir: disk sag kenari ile ilk
metin arasindaki en kucuk bosluk, `acil_geo_kirp.py` KAPI6'nin
dayanagidir (o kitapta pay 27 iken numaranin ilk 2 sutunu siliniyordu).

SIMGE GIRDISI
-------------
JSON, iki bicimden biri:
  * [{"sayfa": 9, "yer": [[gx, gy], ...]}, ...]                (faz0_*.json)
  * {"kutular": [{"sayfa": 9, "simge": [gx, gy], ...}, ...]}   (kirpim kutulari)
Koordinatlar SAYFA KARTI icidir.

KULLANIM
--------
    python backend/scripts/kitap/ortme_olc.py \
        --kok "veriseti/zkitap/screenshots/<klasor>" \
        --simge backend/_geo1_gecici/faz0_acil25.json \
        --kart 593 46 --ilk 7 --son 398 --disk -5 -5 21 19
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

# Metin murekkebi: koyu VE doygunlugu dusuk. Kitabin renkli cizimlerini
# (sari kutu, kirmizi baslik, mor glif) disarida birakir.
MUREKKEP_ESIGI = 170
DOYGUNLUK_ESIGI = 60


def simgeleri_oku(yol: Path) -> dict[int, list[tuple[int, int]]]:
    ham = json.loads(yol.read_text("utf-8"))
    yer: dict[int, list[tuple[int, int]]] = defaultdict(list)
    if isinstance(ham, dict) and "kutular" in ham:
        for b in ham["kutular"]:
            gx, gy = b["simge"]
            yer[int(b["sayfa"])].append((int(gx), int(gy)))
    else:
        for k in ham:
            for gx, gy in k.get("yer", []):
                yer[int(k["sayfa"])].append((int(gx), int(gy)))
    return yer


def _murekkep(kart: np.ndarray) -> np.ndarray:
    ust = kart.max(axis=2)
    alt = kart.min(axis=2)
    mask: np.ndarray = (ust < MUREKKEP_ESIGI) & ((ust - alt) < DOYGUNLUK_ESIGI)
    return mask


def _bant_ortme(
    mur: np.ndarray, gx: int, gy: int, disk: tuple[int, int, int, int], en_az: int
) -> bool:
    """DOGRULANMIS dedektor: diskin hemen SOLUNDAKI bantta metin var mi.

    Bant, diskin SOL KENARINA gore tanimlanir: 13 px ile 7 px arasi.
    Neden bu aralik: 0-6 px diskin kendi golgesi/antialiasi, 14 px ve
    otesi sutunun normal sag payi. ACIL 2023-2024'te bu bant 154 olay /
    151 soru buldu ve dordu gozle dogrulandi (s43, s50, s68, s71
    kirpimlari duzeltmeden sonra son sik satirini geri kazandi).
    Satir araligi diskin kendi yuksekligine gore: 9 px yukari, 4 px asagi.
    """
    dsol, dust, dsag, dalt = disk
    sol_kenar = gx + dsol
    x0 = max(sol_kenar - 13, 0)
    x1 = max(sol_kenar - 7, 0)
    if x1 <= x0:
        return False
    y0 = max(gy + dust - 9, 0)
    y1 = gy + dalt + 4
    return bool(mur[y0:y1, x0:x1].sum() >= en_az)


def _sag_bosluk(
    mur: np.ndarray, gx: int, gy: int, disk: tuple[int, int, int, int]
) -> int | None:
    """Diskin sag kenari ile sagindaki ilk murekkep arasindaki bosluk.

    Beyazlatma payinin ust siniri burasidir (bkz. acil_geo_kirp.py KAPI6:
    pay bu boslugu asarsa soru numarasinin ilk sutunlari siliniyor).
    """
    dsol, dust, dsag, dalt = disk
    sag_kenar = gx + dsag
    serit = mur[max(gy + dust, 0) : gy + dalt + 1, sag_kenar + 1 :]
    sut = np.nonzero(serit.any(axis=0))[0]
    return int(sut.min() + 1) if len(sut) else None


def olc(a: argparse.Namespace) -> dict[str, Any]:
    kok = Path(a.kok)
    yerler = simgeleri_oku(Path(a.simge))
    kx, ky = a.kart
    gw, gh = a.kart_boyutu
    disk = (a.disk[0], a.disk[1], a.disk[2], a.disk[3])

    sag_dag: Counter[int] = Counter()
    icerde = 0
    toplam = 0
    sag_simge = 0
    olaylar: list[tuple[int, int, int]] = []

    for n in sorted(yerler):
        if not (a.ilk <= n <= a.son):
            continue
        yol = kok / f"sayfa_{n:04d}.png"
        if not yol.exists():
            print(f"UYARI: {yol} yok -- atlandi", file=sys.stderr)
            continue
        tam = np.asarray(Image.open(yol).convert("RGB"), dtype=int)
        kart = tam[ky : ky + gh, kx : kx + gw].copy()
        ham_mur = _murekkep(kart)
        # Butun simgeleri beyazlat: komsu simge "metin" sanilmasin.
        for gx, gy in yerler[n]:
            kart[
                max(gy + disk[1] - 2, 0) : gy + disk[3] + 3,
                max(gx + disk[0] - 2, 0) : gx + disk[2] + 3,
            ] = 255
        mur = _murekkep(kart)

        for gx, gy in yerler[n]:
            toplam += 1
            bosluk = _sag_bosluk(mur, gx, gy, disk)
            sag_dag[bosluk if bosluk is not None else -1] += 1
            if (
                ham_mur[
                    max(gy + disk[1], 0) : gy + disk[3] + 1,
                    max(gx + disk[0], 0) : gx + disk[2] + 1,
                ].sum()
                >= 4
            ):
                icerde += 1
            # ORTME yalniz SAG sutun simgesi icin sorulur: solundaki sutun
            # baska bir sorunun metnidir. SOL sutun simgesinin solunda
            # sayfa kenar boslugu vardir, orada ortecek metin yoktur.
            if gx < a.sag_sutun_esigi:
                continue
            sag_simge += 1
            if _bant_ortme(mur, gx, gy, disk, a.en_az_piksel):
                olaylar.append((n, gx, gy))

    return {
        "toplam_simge": toplam,
        "sag_sutun_simgesi": sag_simge,
        "ortme_olayi": len(olaylar),
        "ortme_yerleri": olaylar,
        "sag_bosluk_dagilimi": dict(sorted(sag_dag.items())),
        "eski_metrik_disk_icinde_murekkep": icerde,
    }


def _en_kucuk(dag: dict[int, int]) -> int | None:
    pozitif = [k for k in dag if k >= 0]
    return min(pozitif) if pozitif else None


def ana() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--kok", required=True, help="sayfa PNG'lerinin klasoru")
    p.add_argument("--simge", required=True, help="simge konumlarini tasiyan JSON")
    p.add_argument("--kart", nargs=2, type=int, default=[593, 46], metavar=("X", "Y"))
    p.add_argument(
        "--kart-boyutu", nargs=2, type=int, default=[734, 968], metavar=("W", "H")
    )
    p.add_argument("--ilk", type=int, required=True)
    p.add_argument("--son", type=int, required=True)
    p.add_argument(
        "--disk",
        nargs=4,
        type=int,
        default=[-5, -5, 21, 19],
        metavar=("SOL", "UST", "SAG", "ALT"),
        help="disk kutusu, simge merkezine gore",
    )
    p.add_argument(
        "--sag-sutun-esigi",
        type=int,
        default=200,
        help="bu x'ten buyuk simge SAG sutundur (ortme yalniz onlarda sorulur)",
    )
    p.add_argument(
        "--en-az-piksel",
        type=int,
        default=4,
        help="bantta bu kadar murekkep pikseli ORTME sayilir",
    )
    p.add_argument(
        "--beklenen-olay",
        type=int,
        default=-1,
        help="kalibrasyon: olculen olay sayisi bunu tutmazsa 1 ile doner",
    )
    p.add_argument("--json-yaz", default="")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    s = olc(a)
    print(f"toplam simge              : {s['toplam_simge']}")
    print(f"sag sutun simgesi         : {s['sag_sutun_simgesi']}")
    print(f"ORTME olayi               : {s['ortme_olayi']}")
    print(
        f"etkilenen sayfa           : "
        f"{len({n for n, _gx, _gy in s['ortme_yerleri']})}"
    )
    sag_min = _en_kucuk(s["sag_bosluk_dagilimi"])
    print(f"disk SAGINDA en kucuk bosluk : {sag_min} px")
    if sag_min is not None:
        print(
            f"beyazlatma payi tavsiyesi : sag pay en fazla "
            f"gx+{a.disk[2] + sag_min - 1} (ilk metin gx+{a.disk[2] + sag_min})"
        )
    print(
        "ESKI metrik (disk icinde murekkep): "
        f"{s['eski_metrik_disk_icinde_murekkep']} "
        "-- bu sayi ORTME OLCUSU DEGILDIR"
    )
    if a.beklenen_olay >= 0 and s["ortme_olayi"] != a.beklenen_olay:
        print(
            f"HATA: beklenen {a.beklenen_olay} olay, olculen {s['ortme_olayi']}",
            file=sys.stderr,
        )
        return 1
    if a.json_yaz:
        Path(a.json_yaz).write_text(
            json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"json -> {a.json_yaz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
