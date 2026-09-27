#!/usr/bin/env python
"""345 2025 TYT Sosyal Bilgiler: soru kirpim kutularini uretir (kim345tyt_kutu.py deseni).

CAPA
----
Faz 1 olcumu: toplam okuyucu simgesi (1233) == anahtar tablosu hucre
sayisi; sorular sayfa sirasinda simgelere dagitilir (sutun_sira). Simge soru
numarasinin hemen solunda. Simge capa BIRINCIL kanaldir
(cift sayfa rozeti numara kanalini kirletir, bkz. _capa_sec); simge
tutmazsa basili numara denenir. Ikisi de tutmazsa sutuna kutu URETILMEZ
(tahmin yok).

DIKEY KURAL
-----------
- Tavan: kirmizi unite adi bandi varsa son satiri + BANT_PAY, yoksa TAVAN.
- Kutu ustu: capadan yukari ilk >= BOSLUK satirlik bos bandin alt ucu -
  UST_PAY (murekkep: min kanal < MUREKKEP); bant capadan UST_EN_COK px'ten
  yukarida kaliyorsa capanin 25 px ustune kadar >= 3 satirlik kisa bant.
- Kutu alti: sonraki kutunun ustu - 1; sutunun son sorusunda SAYFA_ALTI.
  Sayfa alti serit YOK; sayfa numarasi bandi SAYFA_NO_UST'ten asagida.

YATAY KURAL
-----------
Sutun ayraci dikey cizgisi (y 150-880, x 355-390'da en dolu sutun):
    sol [4, cizgi-2]   sag [cizgi+3, 738]

KULLANIM
--------
    python backend/scripts/kitap/sos345tyt_kutu.py
    python backend/scripts/kitap/sos345tyt_kutu.py --yaz
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
from sos345tyt_tarama import kart, kaynak_dizin

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
TARAMA = CIKTI / "345_2025_tyt_sosyal_capa_taramasi.json"
ANAHTAR = CIKTI / "345_2025_tyt_sosyal_cevap_anahtari.json"
HEDEF = CIKTI / "345_2025_tyt_sosyal_kirpim_kutulari.json"

KART_G, KART_Y = 742, 979
UST_PAY = 3
BOSLUK = 10
MUREKKEP = 170
UST_EN_COK = 70
NUMARA_X0 = {"L": 55, "R": 375}
BANT_PAY = 4
SAYFA_ALTI = 925
SAYFA_NO_UST = 930
TAVAN = 60
EN_KISA = 30
BEKLENEN_KUTU = 1233
# Sayfa ust bandi (rozet / 'OSYM TADINDA' basligi) bu satirin ustunde; soru
# capasi burada olamaz (olculdu: en yuksek gercek soru capasi cy 137).
UST_BANT_ALTI = 125
CIZGI_ARALIK = (355, 390)
CIZGI_DOLULUK = 0.6
VARSAYILAN_CIZGI = {0: 372, 1: 369}
KENAR = (4, 738)


def ara_cizgi(a: np.ndarray, d: int) -> int:
    """Sutun ayraci x'i (olculemezse parite varsayilani)."""
    x0, x1 = CIZGI_ARALIK
    dolu = (a[150:880, x0:x1].min(axis=2) < 245).mean(axis=0)
    x = int(np.argmax(dolu))
    return x0 + x if dolu[x] >= CIZGI_DOLULUK else VARSAYILAN_CIZGI[d % 2]


def bant_tavani(a: np.ndarray) -> int:
    """Unite adi bandinin (kirmizi) son satiri + BANT_PAY; bant yoksa TAVAN."""
    b = a[90:150].astype(np.int16)
    kir = ((b[..., 0] > 150) & (b[..., 1] < 90) & (b[..., 2] < 90)).sum(axis=1)
    ys = np.where(kir > 0)[0]
    return int(ys.max()) + 90 + BANT_PAY if len(ys) else TAVAN


def sutun_siniri(t: str, cizgi: int) -> tuple[int, int]:
    return (KENAR[0], cizgi - 2) if t == "L" else (cizgi + 3, KENAR[1])


def sutun_simgeleri(sayfa: dict, t: str) -> list[list[int]]:
    # Tarama simgeleri zaten sutuna ayirdi (SIMGE_X araliklari, kim345tyt_tarama).
    return sorted(sayfa["simge"][t])


def _tum_simgeler(s: dict, d: int, disari: list[list[int]]) -> list[list[int]]:
    """Beyazlatilacak TUM okuyucu simgeleri [cy, cx]: soru capalari + sutun disi + serit ustu."""
    out = [list(m) for t in "LR" for m in s["simge"][t]]
    return out + [[cy, cx] for n, cy, cx in disari if n == d]


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
    """Sayisi anahtardan sutuna dusen soru sayisina (k) esit olan kanal: ONCE simge, sonra numara.

    Bu kitapta cift sayfa sol sutunun ustundeki 'N. TEST' rozeti de camgobegi
    rakamdir ve numara kanalina girer (95 sutunda numara = simge + 1). Rozet +
    eksik bir numara sayiyi tutturabilecegi icin simge (534/534 sutunda serit
    girdi sayisina esit, Faz 1) birincil kanaldir.
    """
    sim = sutun_simgeleri(s, t)
    num = [n for n in s["numara"][t] if n[0] >= UST_BANT_ALTI]
    if len(sim) == k and all(m[0] >= UST_BANT_ALTI for m in sim):
        return [[m[0] - 6, m[0] + 6] for m in sim], "simge"
    # Simge ust bantta (3 sutun: s28 R, s226 R, s228 R -- OSYM TADINDA
    # sayfasinda simge sorunun degil basligin yaninda) ya da sayisi tutmuyor:
    # ust bandin altindaki basili numaralar.
    if len(num) == k:
        return [[n[0], n[1]] for n in num], "numara"
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


KOSE_RENK = np.array([240, 125, 25])
KOSE_BOY = (22, 40)  # 'OSYM KOSESI' etiketinin turuncu dairesi (olculdu: 30x30)


def _kose_duzelt(
    a: np.ndarray,
    x0: int,
    x1: int,
    *,
    capa: list[list[int]],
    ustler: list[int],
    sayac: Counter[str],
) -> list[int]:
    """'OSYM KOSESI' kutusu: kutu ustu etiketin ustu olur.

    Kose kutusu onceki sorunun son siklarina 10 px'ten yakin basilabildigi icin
    bos-bant kurali ust siniri onceki sorunun icine tasir (gozle: T046, T052,
    T086, T127, T128). Onceki capanin altinda, capanin ustunde ya da yaninda
    turuncu etiket dairesi varsa kutu ustu = min(etiket ustu, capa ustu) - 1
    (yalniz asagi kaydirir).
    """
    from scipy import ndimage

    b = a[:, x0:x1].astype(np.int16)
    tur = np.abs(b - KOSE_RENK).sum(axis=2) < 70
    lab, _ = ndimage.label(tur, np.ones((3, 3), bool))
    etiket = []
    for sl in ndimage.find_objects(lab):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if KOSE_BOY[0] <= h <= KOSE_BOY[1] and KOSE_BOY[0] <= w <= KOSE_BOY[1]:
            etiket.append(sl[0].start)
    out = list(ustler)
    for i in range(1, len(capa)):
        onceki = capa[i - 1][1]
        # etiket capanin ustunde ya da yaninda (sag tarafta, ayni satirda)
        adaylar = [y for y in etiket if onceki < y < capa[i][1] + 20]
        # Okuyucu diski (beyazlatilir) onceki sorunun son satirina degebilir:
        # sinir min(etiket, capa) - 1 (gozle: T046 E satiri capanin ~2 px
        # ustunde biter; - 3 satirin alt kenarini kesiyordu).
        ust = min([*adaylar, capa[i][0]]) - 1 if adaylar else None
        if ust is not None:
            # Onceki sorunun son satiri etiketin hemen ustune kadar inebilir
            # (T046: satir alti capa ustunden 1-2 px asagida): etiket ustune
            # kadar notr murekkep tasiyan son satirin bir alti.
            et = min(adaylar)
            # harf alt kenari kenar yumusatmasiyla acik gri: esik 200
            notr = ((b.max(axis=2) - b.min(axis=2)) < 50) & (b.min(axis=2) < 200)
            satir = np.where(notr[ust:et].any(axis=1))[0]
            if len(satir):
                ust = ust + int(satir.max()) + 1
        if ust is not None and ust > out[i]:
            out[i] = ust
            sayac["kose_etiketi"] += 1
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
    ustler = _kose_duzelt(a, x0, x1, capa=capa, ustler=ustler, sayac=sayac)
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
                "sutun_sira": q["sutun_sira"],
                "kutu": [x0, ustler[i], x1, alt],
                "capa": capa[i],
                "capa_kanali": kanal,
            }
        )
    return out


def kutulari_uret() -> dict[str, Any]:
    tt = json.loads(TARAMA.read_text("ascii"))
    tarama = tt["sayfalar"]
    disari = tt["sutun_disi_simge"] + tt["serit_simgesi"]
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
        a[okuyucu_maskesi(a, _tum_simgeler(s, d, disari))] = 255
        tavan0 = bant_tavani(a)
        cizgi = ara_cizgi(a, d)
        cizgiler[str(d)] = cizgi
        for t in "LR":
            qs = sorted(sutunlar.get((d, t), []), key=lambda c: c["sutun_sira"])
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
        "kaynak": "345 2025 TYT Sosyal Bilgiler Soru Bankasi",
        "arac": "scripts/kitap/sos345tyt_kutu.py",
        "kart": [589, 43, KART_G, KART_Y],
        "capa": "sutun basina okuyucu simgesi (toplam == anahtar hucre sayisi); yoksa basili numara",
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
        ad = f"{k['dosya']}{k['sutun']}#{k['sutun_sira']}"
        if not (0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y):
            hata.append(f"kart disi/ters: {ad} {k['kutu']}")
        if y1 - y0 < EN_KISA:
            hata.append(f"cok kisa: {ad} {y1 - y0}px")
        if y1 >= SAYFA_NO_UST:
            hata.append(f"sayfa numarasi sizintisi: {ad} {y1} >= {SAYFA_NO_UST}")
        # capa merkezi kutuda (kose kutusunda ust sinir capanin ustunden 1-3 px
        # asagida olabilir; disk beyazlatilir)
        if not y0 <= (k["capa"][0] + k["capa"][1]) // 2 < y1:
            hata.append(f"capa kutu disinda: {ad}")
    grup = defaultdict(list)
    for k in veri["kutular"]:
        grup[(k["dosya"], k["sutun"])].append(k)
    for anahtar, g in grup.items():
        g.sort(key=lambda k: k["kutu"][1])
        if [k["sutun_sira"] for k in g] != list(range(len(g))):
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
