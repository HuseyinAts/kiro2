#!/usr/bin/env python
"""345 2025 TYT Fizik: sayfa turu + capa + cevap seridi taramasi (yalniz olcer).

KAYNAK
------
FERNUS okuyucusunun 1920x1080 ekran goruntuleri, 368 sayfa. Sayfa karti
cercevesi 10 ornek sayfada ayni olculdu: dikey cizgiler x 586-588 ve
1331-1334, yatay y 42 ve 1022 -> ic kart (589, 43) - (1331, 1022) = 742x979.
Basili sayfa = dosya (s7 altinda '7'; icindekiler 'Fizik Bilimine Giris 6').

SORU SAYFASI
------------
Cevap seridi kart y 899-904 bandinda (olculdu: 342 sayfada tam bu bant).
Bandi olmayan 11 sayfa: kapak/kunye/icindekiler (1-5) ve bolum ayraclari
(43, 99, 161, 225, 273, 315). Seritli sayfa = SERIT_Y bandinda gri murekkep.

KANAL 1 -- OKUYUCU SIMGESI (stm345_tarama ile ayni tanim)
--------------------------------------------------------
Glif (69,39,160) + lila disk (240,238,247), halka orani >= 0.6. Soru simgesi
sol x 30-80, sag x 350-400 (merkez); disindaki simgeler (metin ici, x 520 /
630) soru capasi SAYILMAZ, ayri raporlanir.

KANAL 2 -- BASILI SORU NUMARASI
-------------------------------
Camgobegi (0,160,224) L1 < 110; sol x 55-100, sag x 375-420.

KANAL 3 -- CEVAP SERIDI MUREKKEBI
---------------------------------
Gri (doygunluk < 40, min kanal < 200) murekkep, kart y 895-909. Font 6 px;
girdi sayisi pikselden guvenilir CIKMAZ (bosluk histogrami 3-5 px'te
vadisiz), yalniz serit VARLIGI ve kaba sayim raporlanir. Girdi sayisi
iki gorsel okumadan gelir, simge / numara sayisiyla kapilanir.

CIKTI
-----
veriseti/zkitap/cikti/345_2025_tyt_fizik_capa_taramasi.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
HEDEF = CIKTI / "345_2025_tyt_fizik_capa_taramasi.json"
KAYNAK_ADI = "345 2025 Tyt Fizik Soru Bankas\u0131"
KART = (589, 43, 1331, 1022)
BEKLENEN_BOYUT = (1920, 1080)
BEKLENEN_SAYFA = 368
GLIF = np.array([69, 39, 160])
DISK = np.array([240, 238, 247])
CAM = np.array([0, 160, 224])
SIMGE_X = {"L": (30, 80), "R": (350, 400)}
NUMARA_X = {"L": (55, 100), "R": (375, 420)}
Y_ARALIK = (60, 895)
SERIT_Y = (895, 909)
SERIT_X = {"L": (20, 371), "R": (371, 722)}
_YY, _XX = np.mgrid[-16:17, -16:17]
HALKA = (np.sqrt(_YY**2 + _XX**2) >= 9) & (np.sqrt(_YY**2 + _XX**2) <= 13)
HALKA_ESIK = 0.6
# Serit bandinin ustunde (cy >= 890) duran simge soru capasi DEGILDIR:
# olculdu, 17 sutunda (s48 L, s292 R ...) cy 898-928, soru metni yok.
SIMGE_Y_MAX = 890


def kaynak_dizin() -> Path:
    """Kaynak dizini SECMEZ, DOGRULAR: tam ad, sayfa sayisi."""
    d = KOK / "veriseti" / "zkitap" / "screenshots" / KAYNAK_ADI
    if not d.is_dir():
        raise SystemExit(f"Kaynak dizin yok: {d}")
    sayfa = len(list(d.glob("sayfa_*.png")))
    if sayfa != BEKLENEN_SAYFA:
        raise SystemExit(f"Kaynak sayfa sayisi {sayfa} != {BEKLENEN_SAYFA}")
    return d


def kart(kaynak: Path, n: int) -> np.ndarray:
    img = Image.open(kaynak / f"sayfa_{n:04d}.png").convert("RGB")
    if img.size != BEKLENEN_BOYUT:
        raise SystemExit(f"BOYUT UYUSMAZLIGI s{n}: {img.size}")
    a: np.ndarray = np.asarray(img.crop(KART)).astype(np.int16)
    return a


def gri(a: np.ndarray) -> np.ndarray:
    """Gri metin murekkebi maskesi (renkli sus / zemin disarida)."""
    m: np.ndarray = (a.min(axis=2) < 200) & (a.max(axis=2) - a.min(axis=2) < 40)
    return m


def serit(a: np.ndarray) -> dict[str, list[list[int]]]:
    """Sutun basina serit bilesenleri [x0, x1] (kart koord.) -- varlik ve kaba sayim."""
    y0, y1 = SERIT_Y
    m = gri(a[y0:y1])
    r: dict[str, list[list[int]]] = {}
    for t, (x0, x1) in SERIT_X.items():
        lab, _ = ndimage.label(m[:, x0:x1], np.ones((3, 3), bool))
        r[t] = sorted(
            [sl[1].start + x0, sl[1].stop + x0] for sl in ndimage.find_objects(lab)
        )
    return r


def simgeler(a: np.ndarray) -> list[list[int]]:
    """[cy, cx] -- okuyucu simgesi merkezleri (glif halkasi + lila disk)."""
    gm = np.abs(a - GLIF).sum(axis=2) < 150
    dm = np.abs(a - DISK).sum(axis=2) < 30
    lab, _ = ndimage.label(gm)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        c = int((lab[sl] == i + 1).sum())
        if not (7 <= h <= 12 and 7 <= w <= 12 and 22 <= c <= 55):
            continue
        cy, cx = (sl[0].start + sl[0].stop) // 2, (sl[1].start + sl[1].stop) // 2
        pen = dm[max(0, cy - 14) : cy + 16, max(0, cx - 14) : cx + 16]
        if pen.mean() < 0.3:
            continue
        w2 = dm[cy - 16 : cy + 17, cx - 16 : cx + 17]
        if w2.shape != HALKA.shape or w2[HALKA].mean() < HALKA_ESIK:
            continue
        out.append([int(cy), int(cx)])
    return sorted(out)


def simge_sutunu(cx: int) -> str | None:
    for t, (x0, x1) in SIMGE_X.items():
        if x0 <= cx < x1:
            return t
    return None


def numaralar(a: np.ndarray) -> dict[str, list[list[int]]]:
    """Sutun basina [y0, y1, x0, x1] basili numara kutulari (yukaridan asagi)."""
    cm = np.abs(a - CAM).sum(axis=2) < 110
    r: dict[str, list[list[int]]] = {}
    y0, y1 = Y_ARALIK
    for t, (x0, x1) in NUMARA_X.items():
        lab, _ = ndimage.label(cm[y0:y1, x0:x1], np.ones((3, 3), bool))
        bl = []
        for i, sl in enumerate(ndimage.find_objects(lab)):
            c = int((lab[sl] == i + 1).sum())
            if c < 4 or sl[0].stop - sl[0].start > 12:
                continue
            bl.append(
                [sl[0].start + y0, sl[0].stop + y0, sl[1].start + x0, sl[1].stop + x0]
            )
        bl.sort()
        satir: list[list[int]] = []
        for b in bl:
            if satir and b[0] <= satir[-1][1] + 1 and b[1] >= satir[-1][0] - 1:
                s = satir[-1]
                satir[-1] = [
                    min(s[0], b[0]),
                    max(s[1], b[1]),
                    min(s[2], b[2]),
                    max(s[3], b[3]),
                ]
            else:
                satir.append(b)
        r[t] = [s for s in satir if s[1] - s[0] >= 5]
    return r


def main() -> None:
    kaynak = kaynak_dizin()
    sayfalar: dict[str, dict[str, object]] = {}
    seritsiz = []
    n_simge = n_numara = 0
    disari = []
    serit_simgesi: list[list[int]] = []
    simgesiz: list[int] = []
    for n in range(1, BEKLENEN_SAYFA + 1):
        a = kart(kaynak, n)
        ser = serit(a)
        if not (ser["L"] or ser["R"]):
            seritsiz.append(n)
            continue
        sim: dict[str, list[list[int]]] = {"L": [], "R": []}
        for cy, cx in simgeler(a):
            t = simge_sutunu(cx)
            if cy >= SIMGE_Y_MAX:
                serit_simgesi.append([n, cy, cx])
            elif t is None:
                disari.append([n, cy, cx])
            else:
                sim[t].append([cy, cx])
        if not (sim["L"] or sim["R"]):
            simgesiz.append(n)  # kapak / kunye: gri yazi serit bandina dusuyor
            continue
        num = numaralar(a)
        n_simge += len(sim["L"]) + len(sim["R"])
        n_numara += len(num["L"]) + len(num["R"])
        sayfalar[str(n)] = {"simge": sim, "numara": num, "serit": ser}
    veri = {
        "kaynak": "345 2025 TYT Fizik Soru Bankasi",
        "arac": "scripts/kitap/fiz345tyt_tarama.py",
        "kart": list(KART),
        "seritli_sayfa": len(sayfalar),
        "seritsiz_sayfa": seritsiz,
        "seritli_simgesiz_sayfa": simgesiz,
        "simge_toplam": n_simge,
        "numara_toplam": n_numara,
        "sutun_disi_simge": disari,
        "serit_simgesi": serit_simgesi,
        "sayfalar": sayfalar,
    }
    HEDEF.write_text(
        json.dumps(veri, separators=(",", ":")) + "\n", encoding="ascii", newline="\n"
    )
    print(
        f"soru sayfasi {len(sayfalar)} seritsiz {seritsiz} simgesiz {simgesiz}  simge {n_simge}  "
        f"numara {n_numara}  sutun disi simge {len(disari)} -> {HEDEF.name}"
    )


if __name__ == "__main__":
    main()
