#!/usr/bin/env python
"""345 2025 TYT Matematik: soru kirpim kutularini uretir.

CAPA SECIMI -- KITABIN CEVAP SATIRI KARAR VERIR
-----------------------------------------------
Iki bagimsiz piksel kanali (`mat345tyt_tarama.py`): basili soru numarasi ve
FERNUS okuyucu simgesi. Bir sutunun capasi, sayisi o sutunun cevap satiri
girdi sayisina (kitabin kendi anahtari) ESIT olan kanaldir; once numara, o
tutmazsa simge. Ikisi de tutmazsa sutuna kutu URETILMEZ (tahmin yok).
Olculen: 798 sutunun 782'sinde iki kanal da, 14'unde yalniz numara, 2'sinde
yalniz simge tutuyor; ikisinin de tutmadigi sutun 0.

DIKEY KURAL
-----------
- Kutu ustu: capadan yukari, okuyucu katmani beyazlatilmis sayfada, numara
  seridinden (sol x 52, sag x 372) sutun sagina kadar, en az BOSLUK satirlik
  bos (koyu < MUREKKEP yok) bant aranir; kutu ustu o bandin alt ucu - UST_PAY
  (numaranin ustune tasan kesir/sekil de soruya aittir). Numara seridinin
  solu (Orijinal sayfalarinin yesil cerceve cizgisi, kutu kenarlari) bant
  aramasina katilmaz; ilk surumde bu cizgi bosluklari kapatip basligi kutuya
  soktu (7 soru). Tavan: ayni sutundaki onceki capanin alti ya da sayfanin
  bant tavani (mat345tyt_tarama.bant_tavani).
- 'OSYM KOSESI' logosu (turuncu ~(245,135,25), >= 150 piksel) capanin
  LOGO_PENCERE px ustundeyse kutu ustu logonun ustu - 6'dir. Ilk surumde bant
  aramasi logo ile onceki sorunun secenekleri arasinda 10 satir bulamayip
  onceki sorunun seceneklerini sonraki kutuya tasidi (s210, s288).
- Bant capadan UST_EN_COK px'ten daha yukarida kaliyorsa (onceki sorunun
  cercevesi bitisik), capanin 25 px ustune kadar >= 3 satirlik kisa bos bant
  aranir. Ilk surumde bu sinir yoktu: s359 ve s403'te bir sorunun govdesi
  sonraki kutuya gecti (T175_13/14, T196_11/12).
- OSYM Tadinda sayfalarinin acik mavi dikey cercevesi beyazlatilir
  (mat345tyt_tarama.cerceve_maskesi).
- Kutu alti: ayni sutundaki sonraki kutunun ustu - 1; sutunun son sorusunda
  SAYFA_ALTI (cevap satiri y 889'da basliyor).
- Olcum (kapi degil, rapor): kutu ustunun +-3 satirinda notr koyu metin
  varsa kutu 'kesim_metne_degen_kutu' listesine girer.

YATAY KURAL
-----------
Sutunlar arasi ara cizgi taramadan (cift sayfa x 369, tek sayfa x 372;
Orijinal Sorular sayfalarinda gri cizgi ayni yerde). Cizgi olculemezse
tek/cift varsayilani. Sayfanin renkli kenar seridi (cift sayfada sol x 0-28,
tek sayfada sag x 713-741) disarida birakilir:

    cift: sol [30, cizgi-2]  sag [cizgi+3, 738]
    tek : sol [4,  cizgi-2]  sag [cizgi+3, 711]

KULLANIM
--------
    python backend/scripts/kitap/mat345tyt_kutu.py
    python backend/scripts/kitap/mat345tyt_kutu.py --yaz
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
from mat345tyt_tarama import bant_tavani, cerceve_maskesi, kart, kaynak_dizin

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
TARAMA = CIKTI / "345_2025_tyt_matematik_capa_taramasi.json"
ANAHTAR = CIKTI / "345_2025_tyt_matematik_cevap_anahtari.json"
HEDEF = CIKTI / "345_2025_tyt_matematik_kirpim_kutulari.json"

KART_G, KART_Y = 742, 977
UST_PAY = 3
BOSLUK = 10
MUREKKEP = 170
UST_EN_COK = 70
NUMARA_X0 = {"L": 55, "R": 375}
LOGO = np.array([245, 135, 25])
LOGO_ESIK = 90
LOGO_EN_AZ = 150
LOGO_PENCERE = 80
SAYFA_ALTI = 886
EN_KISA = 30
BEKLENEN_KUTU = 2063
VARSAYILAN_CIZGI = {0: 369, 1: 372}
KENAR = {0: (30, 738), 1: (4, 711)}
SIMGE_X = {"L": (30, 80), "R": (350, 400)}


def sutun_siniri(d: int, t: str, cizgi: int | None) -> tuple[int, int]:
    c = cizgi if cizgi is not None else VARSAYILAN_CIZGI[d % 2]
    sol, sag = KENAR[d % 2]
    return (sol, c - 2) if t == "L" else (c + 3, sag)


def sutun_simgeleri(sayfa: dict, t: str) -> list[list[int]]:
    x0, x1 = SIMGE_X[t]
    return sorted(s for s in sayfa["simge"] if 110 < s[2] < 885 and x0 <= s[3] < x1)


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
    """Sayisi cevap satiri girdi sayisina (k) esit olan kanal: once numara, sonra simge."""
    num = s["numara"][t]
    if len(num) == k:
        return [[n[0], n[1]] for n in num], "numara"
    sim = sutun_simgeleri(s, t)
    if len(sim) == k:
        return [[m[0], m[0] + 10] for m in sim], "simge"
    return None


def _ustler(
    capa: list[list[int]],
    tavan0: int,
    murekkep: np.ndarray,
    turuncu: np.ndarray,
    sayac: Counter[str],
) -> list[int]:
    """Her capa icin kutu ustu (UST_PAY kirpmasi oncesi)."""
    out = []
    for i, (y, _) in enumerate(capa):
        tavan = capa[i - 1][1] + 1 if i else tavan0
        bas = max(tavan, y - LOGO_PENCERE)
        pen = turuncu[bas:y]
        satir = np.where(pen.sum(axis=1) >= 3)[0]
        if pen.sum() >= LOGO_EN_AZ and len(satir):
            u = max(tavan, bas + int(satir.min()) - 6)
            sayac["logo"] += 1
        else:
            u = _ust(y, tavan, murekkep)
            if u < y - UST_EN_COK:
                # Bant bulunamadi (onceki sorunun cercevesi/secenekleri bitisik):
                # capanin hemen ustunde >= 3 satirlik kisa bos bant ara (en cok 25 px).
                u = _ust(y, max(tavan, y - 25), murekkep, bosluk=3, pay=1)
                sayac["tavan_asimi"] += 1
        out.append(u)
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
    ek_ust = 0
    for d in sorted({k[0] for k in sutunlar}):
        s = tarama[str(d)]
        a = kart(kaynak, d).astype(np.uint8)
        a[okuyucu_maskesi(a, [[x[2], x[3]] for x in s["simge"]])] = 255
        a[cerceve_maskesi(a, d)] = 255
        tavan0 = bant_tavani(a)
        for t in "LR":
            qs = sorted(sutunlar.get((d, t), []), key=lambda c: c["serit_sira"])
            if not qs:
                continue
            k = len(qs)
            secim = _capa_sec(s, t, k)
            if secim is None:
                gerekce = (
                    f"capa sayisi numara {len(s['numara'][t])} / simge "
                    f"{len(sutun_simgeleri(s, t))} != cevap satiri {k}"
                )
                kutusuz += [
                    {
                        "birim": q["birim"],
                        "soru": q["soru"],
                        "dosya": d,
                        "sutun": t,
                        "gerekce": gerekce,
                    }
                    for q in qs
                ]
                continue
            capa, kaynak_kanal = secim
            kanal[kaynak_kanal] += 1
            x0, x1 = sutun_siniri(d, t, s["ara_cizgi"])
            xg = max(x0, NUMARA_X0[t] - 3)
            murekkep = (a[:, xg:x1].min(axis=2) < MUREKKEP).any(axis=1)
            turuncu = (
                np.abs(a[:, x0:x1].astype(np.int16) - LOGO).sum(axis=2) < LOGO_ESIK
            )
            ustler = _ustler(capa, tavan0, murekkep, turuncu, sayac)
            ek_ust += sum(
                1 for u, (y, _) in zip(ustler, capa, strict=True) if u < y - UST_PAY
            )
            ustler = [
                min(u, y - UST_PAY) for u, (y, _) in zip(ustler, capa, strict=True)
            ]
            b = a[:, x0:x1].astype(np.int16)
            notr = (((b.max(axis=2) - b.min(axis=2)) < 40) & (b.min(axis=2) < 140)).sum(
                axis=1
            )
            for i, q in enumerate(qs):
                if int(notr[ustler[i] - 3 : ustler[i] + 3].sum()):
                    kesim.append(f"{q['birim']}_{q['soru']:02d}")
                alt = ustler[i + 1] - 1 if i + 1 < k else SAYFA_ALTI
                kutular.append(
                    {
                        "birim": q["birim"],
                        "soru": q["soru"],
                        "dosya": d,
                        "sutun": t,
                        "serit_sira": q["serit_sira"],
                        "kutu": [x0, ustler[i], x1, alt],
                        "capa": capa[i],
                        "capa_kanali": kaynak_kanal,
                    }
                )
    kutular.sort(key=lambda k: (k["birim"], k["soru"]))
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutular)
    return {
        "kaynak": "345 2025 TYT Matematik Soru Bankasi",
        "kart": [589, 43, KART_G, KART_Y],
        "capa": "sutun basina: basili numara sayisi == cevap satiri girdi sayisi ise numara, degilse simge (345_2025_tyt_matematik_capa_taramasi.json)",
        "kural": (
            f"Kutu ustu: capadan yukari ilk {BOSLUK} satirlik bos bandin alt ucu - {UST_PAY} "
            "(tavan onceki capa / sayfanin bant tavani, mat345tyt_tarama.bant_tavani); "
            f"alti sonraki kutunun ustu - 1, sutun sonunda {SAYFA_ALTI}."
        ),
        "sutun_kanali": dict(kanal),
        "ust_kurali_sayaci": dict(sayac),
        "kesim_metne_degen_kutu": kesim,
        "capanin_ustune_uzayan_kutu": ek_ust,
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
    if veri["kutu_sayisi"] + veri["kutusuz_soru"] != BEKLENEN_KUTU:
        hata.append(
            f"kutu+kutusuz {veri['kutu_sayisi'] + veri['kutusuz_soru']} != {BEKLENEN_KUTU}"
        )
    for k in veri["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        ad = f"{k['dosya']}{k['sutun']}#{k['serit_sira']}"
        if not (0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y):
            hata.append(f"kart disi/ters: {ad} {k['kutu']}")
        if y1 - y0 < EN_KISA:
            hata.append(f"cok kisa: {ad} {y1 - y0}px")
        if y1 > SAYFA_ALTI:
            hata.append(f"cevap satiri sizintisi: {ad} {y1} > {SAYFA_ALTI}")
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
                hata.append(f"cakisma: {anahtar} {a['kutu']} {c['kutu']}")
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
    print(f"capanin ustune uzayan kutu: {veri['capanin_ustune_uzayan_kutu']}")
    print(
        f"ust kesimi +-3 satirda notr koyu metne degen kutu: {veri['kesim_metne_degen_kutu']}"
    )
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
