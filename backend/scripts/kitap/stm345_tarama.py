#!/usr/bin/env python
"""345 2025 Start Matematik: sayfa turu + capa + cevap seridi taramasi (yalniz olcer).

KAYNAK
------
FERNUS okuyucusunun 1920x1080 ekran goruntuleri, 320 sayfa. Kart (589, 43) -
(1331, 1020) = 742x977 (diger 345 kitaplariyla ayni, olculdu). Basili sayfa
= dosya - 1 (icindekiler 'Sayfa (3)' = dosya 4; dosya 11 altinda '10').

SAYFA TURU
----------
'SINAVA GECIS' test sayfasi: sayfa ustunde (kart y 5-52) sol (x 51-151) ya da
sag (x 551-651) kutuda >= 300 piksel teal izgara rengi (132,194,192; her
kanal +-25). Olculdu: 90 sayfa, hepsi ikiser sayfalik 45 testin sayfasi.
KAPSAM YALNIZ BU SAYFALAR (sahip karari 25 Eyl: konu sayfalarindaki acik uclu
alistirmalar ve 'Isindirma Kosesi' kapsam disi -- anahtarlari basili degil).

KANAL 1 -- OKUYUCU SIMGESI
--------------------------
mat345tyt_tarama.py ile ayni tanim: glif (69,39,160) L1 < 150, 7-12 px kutu,
22-55 piksel; cevresindeki 30x30 pencerenin >= %30'u lila disk
(240,238,247) L1 < 30. Baslik bandi (y < 130) disarida: 'SINAVA GECIS'
harfleri ve 'Simdi Sinava Isinalim' rozeti glif rengine yakin (s11 y 51,
s12 y 51-70 yanlis simge verdi).

KANAL 2 -- BASILI SORU NUMARASI
-------------------------------
Camgobegi (0,160,224) L1 < 110; sol serit x 55-85, sag serit x 375-410
(olculdu: tek sayfa sag numara x 380-399, cift sayfa 390-400), y 140-900.

KANAL 3 -- CEVAP SERIDI MUREKKEBI
---------------------------------
Sayfa altinda sutun basina basili satir ('1.C 2.B 3.E'), kart y 905-930;
sol x 55-330, sag x 400-700 (orta sayfa numarasi kutusu disarida). Murekkep
(min kanal < 225) bilesenleri x'e gore dizilir; bosluk >= GIRDI_BOSLUK (4)
px ise yeni girdi. Olculdu (90 sayfa, bos sutun araliklari): esik 225'te
bosluk dagilimi 1:542 2:85 3:1 4:56 5:134 6:5 -- 3 px'te vadi. Esik 160'ta
ince rakam kenarlari (3, 1) kopuyor, girdi ici 4 px bosluk olusuyordu (s13
'3.B' iki girdi sayildi). Girdi sayisi okumadan BAGIMSIZ bir piksel sayimidir; okuma
ve simge sayisiyla karsilastirilir.

CIKTI
-----
veriseti/zkitap/cikti/345_2025_start_matematik_capa_taramasi.json

KULLANIM
--------
    python backend/scripts/kitap/stm345_tarama.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
HEDEF = CIKTI / "345_2025_start_matematik_capa_taramasi.json"
KART = (589, 43, 1331, 1020)
BEKLENEN_BOYUT = (1920, 1080)
BEKLENEN_SAYFA = 320
GLIF = np.array([69, 39, 160])
DISK = np.array([240, 238, 247])
CAM = np.array([0, 160, 224])
TEAL = np.array([132, 194, 192])
NUMARA_SERIDI = {"L": (55, 85), "R": (375, 410)}
Y_ARALIK = (140, 900)
SERIT_Y = (905, 930)
SERIT_X = {"L": (55, 330), "R": (400, 700)}
GIRDI_BOSLUK = 4
SERIT_MUREKKEP = 225
SIMGE_Y_MIN = 130  # baslik bandindaki mor harfler / rozet (olculdu: y 51-70)
BASLIK_KUTU = {"L": (51, 151), "R": (551, 651)}


def kaynak_dizin() -> Path:
    """Kaynak dizini SECMEZ, DOGRULAR: tam ad, sayfa sayisi."""
    d = KOK / "veriseti" / "zkitap" / "screenshots" / "345 2025 Start Matematik"
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


def test_sayfasi(a: np.ndarray) -> str | None:
    """Baslik izgarasinin tarafi ('L'/'R') ya da None (test sayfasi degil)."""
    t = (np.abs(a[5:52] - TEAL) <= 25).all(axis=2)
    say = {k: int(t[:, x0:x1].sum()) for k, (x0, x1) in BASLIK_KUTU.items()}
    k = max(say, key=lambda s: say[s])
    return k if say[k] >= 300 else None


def simgeler(a: np.ndarray) -> list[list[int]]:
    """[y_ust, x_sol, cy, cx] -- glif halkasinin kutusu ve merkezi (kart koord.)."""
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
        if pen.mean() < 0.3 or cy < SIMGE_Y_MIN:
            continue
        out.append([int(sl[0].start), int(sl[1].start), int(cy), int(cx)])
    return out


def numaralar(a: np.ndarray) -> dict[str, list[list[int]]]:
    """Sutun basina [y0, y1, x0, x1] basili numara kutulari (yukaridan asagi)."""
    cm = np.abs(a - CAM).sum(axis=2) < 110
    r: dict[str, list[list[int]]] = {}
    y0, y1 = Y_ARALIK
    for t, (x0, x1) in NUMARA_SERIDI.items():
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


def serit(a: np.ndarray) -> dict[str, list[list[int]]]:
    """Sutun basina cevap seridi girdileri [x0, x1, y0, y1] (kart koord.)."""
    y0, y1 = SERIT_Y
    r: dict[str, list[list[int]]] = {}
    for t, (x0, x1) in SERIT_X.items():
        m = a[y0:y1, x0:x1].min(axis=2) < SERIT_MUREKKEP
        lab, _ = ndimage.label(m, np.ones((3, 3), bool))
        kutular = sorted(
            [
                sl[1].start + x0,
                sl[1].stop + x0,
                sl[0].start + y0,
                sl[0].stop + y0,
            ]
            for sl in ndimage.find_objects(lab)
        )
        girdi: list[list[int]] = []
        for k in kutular:
            if girdi and k[0] - girdi[-1][1] < GIRDI_BOSLUK:
                g = girdi[-1]
                girdi[-1] = [g[0], max(g[1], k[1]), min(g[2], k[2]), max(g[3], k[3])]
            else:
                girdi.append(list(k))
        r[t] = girdi
    return r


def main() -> None:
    kaynak = kaynak_dizin()
    sayfalar: dict[str, dict[str, object]] = {}
    n_test = n_simge = n_girdi = 0
    for n in range(1, BEKLENEN_SAYFA + 1):
        a = kart(kaynak, n)
        taraf = test_sayfasi(a)
        if taraf is None:
            continue
        sim, num, ser = simgeler(a), numaralar(a), serit(a)
        n_test += 1
        n_simge += len(sim)
        n_girdi += len(ser["L"]) + len(ser["R"])
        sayfalar[str(n)] = {
            "baslik_tarafi": taraf,
            "simge": sim,
            "numara": num,
            "serit": ser,
        }
    veri = {
        "kaynak": "345 2025 Start Matematik",
        "arac": "scripts/kitap/stm345_tarama.py",
        "kart": list(KART),
        "test_sayfasi": n_test,
        "simge_toplam": n_simge,
        "serit_girdi_toplam": n_girdi,
        "sayfalar": sayfalar,
    }
    HEDEF.write_text(
        json.dumps(veri, separators=(",", ":")) + "\n", encoding="ascii", newline="\n"
    )
    print(
        f"test sayfasi {n_test}  simge {n_simge}  serit girdi {n_girdi}  -> {HEDEF.name}"
    )


if __name__ == "__main__":
    main()
