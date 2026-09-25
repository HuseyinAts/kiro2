#!/usr/bin/env python
"""345 2025 Start Matematik: soru kirpim kutularini uretir (mat345tyt_kutu.py deseni).

CAPA -- BASILI SORU NUMARASI
----------------------------
Faz 1 olcumu: 180/180 sutunda basili numara sayisi == kitabin cevap seridi
girdi sayisi. Okuyucu simgesi soru BASI DEGIL (s266 sagda soru ortasinda
simge, s83 sagda sekil icinde yanlis simge, s137 solda simgesiz soru);
simge yalniz numara tutmazsa yedek kanal. Ikisi de tutmazsa sutuna kutu
URETILMEZ (tahmin yok).

DIKEY KURAL
-----------
- Tavan: sayfanin unite adi bandinin (kirmizi, r > 150, g/b < 90; y 90-150)
  son satiri + BANT_PAY. Olculdu: 90 sayfada bant alti y 120 (52) / 123 (38);
  ilk numara y >= 140.
- Kutu ustu: capadan yukari, okuyucu katmani beyazlatilmis sayfada, numara
  seridinden sutun sagina kadar ilk >= BOSLUK satirlik bos bandin alt ucu -
  UST_PAY; bant capadan UST_EN_COK px'ten yukarida kaliyorsa capanin 25 px
  ustune kadar >= 3 satirlik kisa bos bant (mat345tyt kurali).
- Kutu alti: ayni sutundaki sonraki kutunun ustu - 1; sutunun son sorusunda
  SAYFA_ALTI. Olculdu: 90 sayfada cevap seridi murekkebi y >= 914, sutun
  icerigi (orta sayfa numarasi kutusu haric) en alt y 883.

YATAY KURAL
-----------
Sutunlar arasi dikey cizgi (y 150-880'de x 355-390 araliginda en dolu
sutun): cift dosya x 372, tek dosya x 369 (90/90 sayfa, doluluk >= 0.8).
Test sayfalarinda renkli kenar seridi YOK (x 0-30 ve 712-742 murekkep orani
0.0, 90/90). Sag sutunun okuyucu simgesi cizginin SOLUNDA (x 363-371) durur;
beyazlatilir.

    sol [4, cizgi-2]   sag [cizgi+3, 738]

KULLANIM
--------
    python backend/scripts/kitap/stm345_kutu.py
    python backend/scripts/kitap/stm345_kutu.py --yaz
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acil25_geo_kirp import okuyucu_maskesi
from stm345_tarama import kart, kaynak_dizin

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
TARAMA = CIKTI / "345_2025_start_matematik_capa_taramasi.json"
ANAHTAR = CIKTI / "345_2025_start_matematik_cevap_anahtari.json"
HEDEF = CIKTI / "345_2025_start_matematik_kirpim_kutulari.json"

KART_G, KART_Y = 742, 977
UST_PAY = 3
BOSLUK = 10
MUREKKEP = 170
UST_EN_COK = 70
NUMARA_X0 = {"L": 55, "R": 375}
BANT_PAY = 4
SAYFA_ALTI = 900
SERIT_UST = 905
EN_KISA = 30
BEKLENEN_KUTU = 371
CIZGI_ARALIK = (355, 390)
CIZGI_DOLULUK = 0.6
VARSAYILAN_CIZGI = {0: 372, 1: 369}
KENAR = (4, 738)
SIMGE_X = {"L": (30, 80), "R": (350, 400)}


def ara_cizgi(a: np.ndarray, d: int) -> int:
    """Sutun ayraci x'i (olculemezse parite varsayilani)."""
    x0, x1 = CIZGI_ARALIK
    dolu = (a[150:880, x0:x1].min(axis=2) < 245).mean(axis=0)
    x = int(np.argmax(dolu))
    return x0 + x if dolu[x] >= CIZGI_DOLULUK else VARSAYILAN_CIZGI[d % 2]


def bant_tavani(a: np.ndarray) -> int:
    """Unite adi bandinin (kirmizi) son satiri + BANT_PAY; bant yoksa 130."""
    b = a[90:150].astype(np.int16)
    kir = ((b[..., 0] > 150) & (b[..., 1] < 90) & (b[..., 2] < 90)).sum(axis=1)
    ys = np.where(kir > 0)[0]
    return int(ys.max()) + 90 + BANT_PAY if len(ys) else 130


def sutun_siniri(t: str, cizgi: int) -> tuple[int, int]:
    return (KENAR[0], cizgi - 2) if t == "L" else (cizgi + 3, KENAR[1])


def sutun_simgeleri(sayfa: dict, t: str) -> list[list[int]]:
    x0, x1 = SIMGE_X[t]
    return sorted(s for s in sayfa["simge"] if x0 <= s[3] < x1)


def _ust(
    y: int, tavan: int, murekkep: np.ndarray, bosluk: int = BOSLUK, pay: int = UST_PAY
) -> int:
    """Capadan yukari: ilk >= bosluk satirlik bos bandin alt ucu - pay."""
    bos = 0
    r = y - 1
    while r >= tavan:
        if murekkep[r]:
            bos = 0
        else:
            bos += 1
            if bos >= bosluk:
                return max(tavan, r + bosluk - pay)
        r -= 1
    return tavan


def _capa_sec(s: dict, t: str, k: int) -> tuple[list[list[int]], str] | None:
    """Sayisi cevap seridi girdi sayisina (k) esit olan kanal: once numara, sonra simge."""
    num = s["numara"][t]
    if len(num) == k:
        return [[n[0], n[1]] for n in num], "numara"
    sim = sutun_simgeleri(s, t)
    if len(sim) == k:
        return [[m[0], m[0] + 10] for m in sim], "simge"
    return None


def _ustler(
    capa: list[list[int]], tavan0: int, murekkep: np.ndarray, sayac: Counter[str]
) -> list[int]:
    out = []
    for i, (y, _) in enumerate(capa):
        tavan = capa[i - 1][1] + 1 if i else tavan0
        u = _ust(y, tavan, murekkep)
        if u < y - UST_EN_COK:
            u = _ust(y, max(tavan, y - 25), murekkep, bosluk=3, pay=1)
            sayac["tavan_asimi"] += 1
        out.append(min(u, y - UST_PAY))
    return out


def _sutun_kutulari(
    qs: list[dict],
    capa: list[list[int]],
    kanal: str,
    a: np.ndarray,
    t: str,
    *,
    cizgi: int,
    tavan0: int,
    sayac: Counter[str],
    kesim: list[str],
) -> list[dict]:
    x0, x1 = sutun_siniri(t, cizgi)
    xg = max(x0, NUMARA_X0[t] - 3)
    murekkep = (a[:, xg:x1].min(axis=2) < MUREKKEP).any(axis=1)
    ustler = _ustler(capa, tavan0, murekkep, sayac)
    b = a[:, x0:x1].astype(np.int16)
    notr = (((b.max(axis=2) - b.min(axis=2)) < 40) & (b.min(axis=2) < 140)).sum(axis=1)
    out = []
    for i, q in enumerate(qs):
        if int(notr[ustler[i] - 3 : ustler[i] + 3].sum()):
            kesim.append(f"{q['birim']}_{q['soru']:02d}")
        alt = ustler[i + 1] - 1 if i + 1 < len(qs) else SAYFA_ALTI
        out.append(
            {
                "birim": q["birim"],
                "soru": q["soru"],
                "dosya": q["dosya"],
                "sutun": t,
                "serit_sira": q["serit_sira"],
                "kutu": [x0, ustler[i], x1, alt],
                "capa": capa[i],
                "capa_kanali": kanal,
            }
        )
    return out


def kutulari_uret() -> dict[str, Any]:
    tarama = json.loads(TARAMA.read_text("ascii"))["sayfalar"]
    anahtar = json.loads(ANAHTAR.read_text("ascii"))["cevaplar"]
    kaynak = kaynak_dizin()
    sutunlar: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for c in anahtar:
        sutunlar[(c["dosya"], c["sutun"])].append(c)
    kutular: list[dict] = []
    kutusuz: list[dict] = []
    kanal: Counter[str] = Counter()
    sayac: Counter[str] = Counter()
    kesim: list[str] = []
    cizgiler: dict[str, int] = {}
    for d in sorted({k[0] for k in sutunlar}):
        s = tarama[str(d)]
        a = kart(kaynak, d).astype(np.uint8)
        a[okuyucu_maskesi(a, [[x[2], x[3]] for x in s["simge"]])] = 255
        tavan0 = bant_tavani(a)
        cizgi = ara_cizgi(a, d)
        cizgiler[str(d)] = cizgi
        for t in "LR":
            qs = sorted(sutunlar.get((d, t), []), key=lambda c: c["serit_sira"])
            if not qs:
                continue
            secim = _capa_sec(s, t, len(qs))
            if secim is None:
                kutusuz += [
                    {"birim": q["birim"], "soru": q["soru"], "dosya": d, "sutun": t}
                    for q in qs
                ]
                continue
            capa, kaynak_kanal = secim
            kanal[kaynak_kanal] += 1
            kutular += _sutun_kutulari(
                qs,
                capa,
                kaynak_kanal,
                a,
                t,
                cizgi=cizgi,
                tavan0=tavan0,
                sayac=sayac,
                kesim=kesim,
            )
    kutular.sort(key=lambda k: (k["birim"], k["soru"]))
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutular)
    return {
        "kaynak": "345 2025 Start Matematik",
        "arac": "scripts/kitap/stm345_kutu.py",
        "kart": [589, 43, KART_G, KART_Y],
        "capa": "sutun basina basili numara (sayisi == cevap seridi girdi sayisi); yedek simge",
        "kural": (
            f"Kutu ustu: capadan yukari ilk {BOSLUK} satirlik bos bandin alt ucu - {UST_PAY} "
            f"(tavan onceki capa / unite adi bandi + {BANT_PAY}); alti sonraki kutunun "
            f"ustu - 1, sutun sonunda {SAYFA_ALTI}."
        ),
        "sutun_kanali": dict(kanal),
        "ust_kurali_sayaci": dict(sayac),
        "kesim_metne_degen_kutu": kesim,
        "ara_cizgi": cizgiler,
        "kutu_sayisi": len(kutular),
        "kutusuz_soru": len(kutusuz),
        "yukseklik": {"min": yuk[0], "medyan": yuk[len(yuk) // 2], "max": yuk[-1]}
        if yuk
        else None,
        "kutular": kutular,
        "kutusuz": kutusuz,
    }


def kapilar(veri: dict[str, Any]) -> list[str]:
    hata = []
    if veri["kutu_sayisi"] != BEKLENEN_KUTU or veri["kutusuz_soru"]:
        hata.append(f"kutu {veri['kutu_sayisi']} / kutusuz {veri['kutusuz_soru']}")
    for k in veri["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        ad = f"{k['dosya']}{k['sutun']}#{k['serit_sira']}"
        if not (0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y):
            hata.append(f"kart disi/ters: {ad} {k['kutu']}")
        if y1 - y0 < EN_KISA:
            hata.append(f"cok kisa: {ad} {y1 - y0}px")
        if y1 >= SERIT_UST:
            hata.append(f"cevap seridi sizintisi: {ad} {y1} >= {SERIT_UST}")
        if not y0 <= k["capa"][0] < y1:
            hata.append(f"capa kutu disinda: {ad}")
    grup = defaultdict(list)
    for k in veri["kutular"]:
        grup[(k["dosya"], k["sutun"])].append(k)
    for anahtar, g in grup.items():
        g.sort(key=lambda k: k["kutu"][1])
        if [k["serit_sira"] for k in g] != list(range(len(g))):
            hata.append(f"sira bozuk: {anahtar}")
        for a, c in itertools.pairwise(g):
            if a["kutu"][3] >= c["kutu"][1]:
                hata.append(f"cakisma: {anahtar}")
            if a["kutu"][3] >= c["capa"][0]:
                hata.append(f"sonraki capa ustteki kutuda: {anahtar}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true", help="JSON dosyasini guncelle")
    args = ap.parse_args()
    veri = kutulari_uret()
    hata = kapilar(veri)
    print(f"kutu sayisi: {veri['kutu_sayisi']}  kutusuz: {veri['kutusuz_soru']}")
    print(
        f"sutun kanali: {veri['sutun_kanali']}  ust kurali: {veri['ust_kurali_sayaci']}"
    )
    print(f"ust kesimi notr metne degen kutu: {veri['kesim_metne_degen_kutu']}")
    print(f"yukseklik: {veri['yukseklik']}")
    print(f"kapi ihlali: {len(hata)}")
    for h in hata[:20]:
        print("   ", h)
    if hata:
        raise SystemExit(1)
    if args.yaz:
        HEDEF.write_text(
            json.dumps(veri, indent=1) + "\n", encoding="ascii", newline="\n"
        )
        print("yazildi:", HEDEF)


if __name__ == "__main__":
    main()
