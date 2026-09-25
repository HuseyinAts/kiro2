#!/usr/bin/env python
"""345 2025 AYT Turk Edebiyati: capa taramasi (okuyucu simgesi + basili soru numarasi + ara cizgi).

Kirpim kutulari iki BAGIMSIZ piksel kanalindan birine dayanir; hangisinin
kullanilacagini sutunun soru sayisi (kitap sonu anahtar + bant okumasi) secer
(`edb345ayt_kutu.py`). Bu script yalniz olcer, karar vermez.

KANAL 1 -- FERNUS OKUYUCU SIMGESI (buyutec)
-------------------------------------------
Glif rengi (69,39,160)'a yakin (L1 < 150), 7-12 px kutulu, 22-55 piksellik
halka bilesenleri; etrafindaki 30x30 pencerenin >= %30'u lila disk rengi
(240,238,247, L1 < 30). Disk+glif BIRLESIK bileseni boyutla suzulmez:
kitabin 'UcDortBes' filigrani disk rengine yakin oldugu icin filigranla
ortusen disk buyuk bilesene donusur (345 AYT Matematik'te olculdu).
Bu kitapta 612 soru sutununun 1'inde (s293 sol) capa bu kanaldan alindi.

KANAL 2 -- BASILI SORU NUMARASI
-------------------------------
Camgobegi (0,160,224)'e yakin (L1 < 110) bilesenler, yalniz numara seridinde
(sol x 55-85, sag x 375-410, y 110-885). Ayni satirdaki rakam ve nokta
bilesenleri tek numaraya birlestirilir; 5 px'ten kisa satirlar atilir.

ARA CIZGI
---------
Sutunlar arasindaki dikey cizgi: x 360-380 araliginda y 130-880'de en dolu
(min kanal < 245) sutun; dolu orani < 0.6 ise cizgi yok sayilir (kutu araci
tek/cift varsayilanini kullanir).

KULLANIM
--------
    python backend/scripts/kitap/edb345ayt_tarama.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
HEDEF = CIKTI / "345_2025_ayt_edebiyat_capa_taramasi.json"
KART = (589, 43, 1331, 1020)
BEKLENEN_BOYUT = (1920, 1080)
BEKLENEN_SAYFA = 348
# 329-348: okuyucu son sayfada takili kalmis, s328'in piksel ozdes kopyalari (olculdu).
ICERIK_SAYFA = 328
GLIF = np.array([69, 39, 160])
DISK = np.array([240, 238, 247])
CAM = np.array([0, 160, 224])
NUMARA_SERIDI = {"L": (55, 85), "R": (375, 410)}
Y_ARALIK = (110, 885)


def kaynak_dizin() -> Path:
    """Kaynak dizini SECMEZ, DOGRULAR: dar desen, tek eslesme, sayfa sayisi."""
    adaylar = [
        p
        for p in (KOK / "veriseti" / "zkitap" / "screenshots").iterdir()
        if p.is_dir() and p.name.startswith("345 2025 Ayt Turk Edebiyat")
    ]
    if len(adaylar) != 1:
        raise SystemExit(f"Kaynak dizin tek degil: {[a.name for a in adaylar]}")
    sayfa = len(list(adaylar[0].glob("sayfa_*.png")))
    if sayfa != BEKLENEN_SAYFA:
        raise SystemExit(f"Kaynak sayfa sayisi {sayfa} != {BEKLENEN_SAYFA}")
    return adaylar[0]


def kart(kaynak: Path, n: int) -> np.ndarray:
    img = Image.open(kaynak / f"sayfa_{n:04d}.png").convert("RGB")
    if img.size != BEKLENEN_BOYUT:
        raise SystemExit(f"BOYUT UYUSMAZLIGI s{n}: {img.size}")
    return np.asarray(img.crop(KART)).astype(np.int16)


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
        if pen.mean() < 0.3:
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


def ara_cizgi(a: np.ndarray) -> int | None:
    dolu = (a[130:880, 360:381].min(axis=2) < 245).mean(axis=0)
    x = int(np.argmax(dolu))
    return 360 + x if dolu[x] >= 0.6 else None


CERCEVE = np.array([147, 216, 244])
CERCEVE_BANDI = {0: (26, 52), 1: (688, 716)}


def cerceve_maskesi(a: np.ndarray, d: int) -> np.ndarray:
    """OSYM Tadinda sayfalarinin dis kenarindaki acik mavi dikey cerceve cizgileri.

    Olculdu (s14 cift: x 31-34 ve 44-47; s15 tek: x 694-696 ve 707-710; renk
    ~(147,216,244)). Yalniz cerceve bandinda ve yalniz sayfada cerceve varsa
    (bandin bir x sutununun y 150-880'de >= %5'i bu renk = dikey cizgi): o
    zaman banttaki bu renge yakin (L1 < 45) tum pikseller; bandin disina ve
    cercevesiz sayfalara dokunulmaz.
    """
    m = np.zeros(a.shape[:2], bool)
    x0, x1 = CERCEVE_BANDI[d % 2]
    renk = np.abs(a[:, x0:x1].astype(np.int16) - CERCEVE).sum(axis=2) < 45
    cizgi = renk[150:880].mean(axis=0) >= 0.05
    if cizgi.any():
        # Sayfada cerceve VAR: banttaki tum cerceve rengi pikselleri (cercevenin
        # kisa cikintilari dahil; ilk surumde bunlar 87 kirpimin sol kenarinda
        # 4 piksel kalinti biraktirdi).
        m[:, x0:x1] = renk
    return m


def bant_tavani(a: np.ndarray) -> int:
    """Kutu tavani (kart y): sayfa ustu bandin/cercevenin alti + 3, en az 110, en cok 138.

    Bant satiri: y 95-135'te kart genisliginin >= %30'u koyu (< 235) YA DA
    >= %90'i beyaz degil (< 245; Orijinal Sorular bandinin acik yesil zemini).
    Son bant satirindan asagi, satirin > %5'i beyaz olmadigi surece (bandin alt
    parcalari: 'SORULAR 1' yazisi, R rozeti, 'MADE BY' damgasi) devam edilir.
    Olculdu: Klasiklesmis bandinin alt cizgisi y 105-107; OSYM Tadinda
    sayfalarinin ust cercevesi HER sayfada y 123-124; Orijinal bandinin zemini
    y <= 107, alt parcalari y 110-124. En ust capa y 143.
    """
    b = a[95:136, 30:710].min(axis=2)
    koyu = (b < 235).mean(axis=1)
    dolu = (b < 245).mean(axis=1)
    ys = np.where((koyu >= 0.3) | (dolu >= 0.9))[0]
    if not len(ys):
        return 110
    r = int(ys.max())
    while r + 1 < len(dolu) and dolu[r + 1] > 0.05:
        r += 1
    return min(138, max(110, r + 95 + 3))


def main() -> None:
    kaynak = kaynak_dizin()
    sayfalar: dict[str, dict[str, object]] = {}
    n_simge = n_numara = 0
    for n in range(1, ICERIK_SAYFA + 1):
        a = kart(kaynak, n)
        sim, num = simgeler(a), numaralar(a)
        n_simge += len(sim)
        n_numara += len(num["L"]) + len(num["R"])
        sayfalar[str(n)] = {"simge": sim, "numara": num, "ara_cizgi": ara_cizgi(a)}
    veri = {
        "kaynak": "345 2025 AYT Turk Edebiyati Soru Bankasi",
        "arac": "scripts/kitap/edb345ayt_tarama.py",
        "kart": list(KART),
        "simge_toplam": n_simge,
        "numara_toplam": n_numara,
        "sayfalar": sayfalar,
    }
    HEDEF.write_text(
        json.dumps(veri, separators=(",", ":")) + "\n", encoding="ascii", newline="\n"
    )
    print(
        f"simge {veri['simge_toplam']}  numara {veri['numara_toplam']}  -> {HEDEF.name}"
    )


if __name__ == "__main__":
    main()
