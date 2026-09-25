#!/usr/bin/env python
"""345 2025 AYT Kimya: soru kirpim kutularini uretir.

CAPA SECIMI -- KITABIN CEVAP SATIRI KARAR VERIR
-----------------------------------------------
Iki bagimsiz piksel kanali (`kim345ayt_tarama.py`): basili soru numarasi ve
FERNUS okuyucu simgesi. Bir sutunun capasi, sayisi o sutunun cevap satiri
girdi sayisina (kitabin kendi anahtari) ESIT olan kanaldir; once numara
(genisligi <= NUMARA_EN_GENIS; konu kutusundaki genis mavi rakamlar capa
degildir), o tutmazsa simge, o da tutmazsa iki kanalin BIRLESIGI (ayni
soruyu gosteren numara+simge BIRLESIK_Y icinde tek capa); kanal sayisi
girdiden fazlaysa en alttaki k tanesi (numara_alt / simge_alt). Hicbiri
tutmazsa sutuna kutu URETILMEZ (tahmin yok).
Olculen (553 soru sutunu): numara 524, simge 25, birlesik 3, numara_alt 1;
kutusuz sutun 0. Numarasi okuyucu diski altinda kalan soru 57
(DISK_NUMARA_EN_AZ: numara bolgesinde >= 16 koyu piksel yoksa ortulu).

DIKEY KURAL
-----------
- Kutu ustu: capadan yukari, okuyucu katmani beyazlatilmis sayfada, numara
  seridinden (sol x 52, sag x 372) sutun sagina kadar, en az BOSLUK satirlik
  bos (koyu < MUREKKEP yok) bant aranir; kutu ustu o bandin alt ucu - UST_PAY
  (numaranin ustune tasan kesir/sekil de soruya aittir). Numara seridinin
  solu (cerceve cizgisi, kutu kenarlari) bant aramasina katilmaz. Tavan: ayni
  sutundaki onceki capanin alti ya da sayfanin bant tavani
  (kim345ayt_tarama.bant_tavani).
- 'OSYM KOSESI' logosu (turuncu ~(245,135,25), >= 150 piksel) capanin
  LOGO_PENCERE px ustundeyse kutu ustu logonun ustu - 6'dir (90 kutu).
- Bant capadan UST_EN_COK px'ten daha yukarida kaliyorsa (onceki sorunun
  cercevesi bitisik), capanin 25 px ustune kadar >= 3 satirlik kisa bos bant
  aranir.
- Konu anlatimi kutusunun yanindaki sag sutun (Orijinal / konu sayfalari):
  kalin acik mavi kutu kenari ara cizgi sanilir; sol sinir bandin sonuna
  kaydirilir (ayrac_bandi_sonu, 95 kutu). Ilk surumde kutu kenari kirpima
  giriyordu (250 kenar kapisi isabeti; simdi 3).
- OSYM Tadinda sayfalarinin acik mavi dikey cercevesi beyazlatilir
  (kim345ayt_tarama.cerceve_maskesi).
- Kutu alti: ayni sutundaki sonraki kutunun ustu - 1; sutunun son sorusunda
  SAYFA_ALTI (cevap satiri y 899-904; murekkebi bir kac satir yukari tasar).
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
    python backend/scripts/kitap/kim345ayt_kutu.py
    python backend/scripts/kitap/kim345ayt_kutu.py --yaz
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
from kim345ayt_tarama import bant_tavani, cerceve_maskesi, kart, kaynak_dizin

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
TARAMA = CIKTI / "345_2025_ayt_kimya_capa_taramasi.json"
ANAHTAR = CIKTI / "345_2025_ayt_kimya_cevap_anahtari.json"
HEDEF = CIKTI / "345_2025_ayt_kimya_kirpim_kutulari.json"

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
LOGO_ALT_PENCERE = 25
DISK_NUMARA_EN_AZ = 16
SAYFA_ALTI = 896
EN_KISA = 30
BEKLENEN_KUTU = 1304
VARSAYILAN_CIZGI = {0: 369, 1: 372}
KENAR = {0: (30, 738), 1: (4, 711)}
SIMGE_X = {"L": (30, 80), "R": (350, 400)}
BIRLESIK_Y = 15
NUMARA_EN_GENIS = 12
AYRAC_EN_GENIS = 15
AYRAC_ORAN = 0.2


def sutun_siniri(d: int, t: str, cizgi: int | None) -> tuple[int, int]:
    c = cizgi if cizgi is not None else VARSAYILAN_CIZGI[d % 2]
    sol, sag = KENAR[d % 2]
    return (sol, c - 2) if t == "L" else (c + 3, sag)


def ayrac_bandi_sonu(a: np.ndarray, x0: int) -> int:
    """Sag sutun sol siniri: konu kutusunun kalin acik mavi sag kenari (x ~368-376, renk
    ~(141,215,247)) ara cizgi olarak olculdugunde sag kutu bu bandin icinden baslar. x0'dan
    saga, y 130-880'in >= AYRAC_ORAN'i dolu (min kanal < 245) sutunlari atla; en cok AYRAC_EN_GENIS.
    Konu kutusuz sayfada (tek ince cizgi) x0 degismez."""
    x = x0
    while (
        x < x0 + AYRAC_EN_GENIS
        and (a[130:880, x].min(axis=1) < 245).mean() >= AYRAC_ORAN
    ):
        x += 1
    return x if x == x0 else x + 2


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


def _birlesik(num: list[list[int]], sim: list[list[int]]) -> list[list[int]]:
    """Numara ve simge capalarinin birlesimi: ayni soruya ait olanlar (y farki <= BIRLESIK_Y) tek capa."""
    out = [[n[0], n[1]] for n in num]
    for m in sim:
        if not any(abs(m[0] - o[0]) <= BIRLESIK_Y for o in out):
            out.append([m[0], m[0] + 10])
    return sorted(out)


def _capa_sec(s: dict, t: str, k: int) -> tuple[list[list[int]], str] | None:
    """Cevap satiri girdi sayisina (k) gore capa kanali; sira ve gerekce modul belgesinde."""
    num = [n for n in s["numara"][t] if n[3] - n[2] <= NUMARA_EN_GENIS]
    if len(num) == k:
        return [[n[0], n[1]] for n in num], "numara"
    sim = sutun_simgeleri(s, t)
    if len(sim) == k:
        return [[m[0], m[0] + 10] for m in sim], "simge"
    bir = _birlesik(num, sim)
    if len(bir) == k:
        return bir, "birlesik"
    if len(num) > k:
        return [[n[0], n[1]] for n in num[-k:]], "numara_alt"
    if len(sim) > k:
        return [[m[0], m[0] + 10] for m in sim[-k:]], "simge_alt"
    return None


def numara_disk_ortulu(s: dict, t: str, capa_y0: int) -> bool:
    """Numara capali kutuda okuyucu diski numaranin ilk rakam(lar)ini ortuyor mu.

    Disk merkezi ile numara kutusunun sol ucu arasindaki yatay mesafe
    DISK_NUMARA_EN_AZ'dan kucukse evet. Olculdu (1835 numara capali kutunun
    diski eslesen 1720'si): medyan 17, 1697'si 14-26; transkripsiyonda
    numarasi okunamayan 10 kutunun 10'unda <= 13 (piksel kanali yalniz
    diskin sag kenarindan cikan numara parcasini saymis).
    """
    num = [n for n in s["numara"][t] if n[0] == capa_y0]
    if len(num) != 1:
        return False
    y0, y1, x0, _ = num[0]
    cy = (y0 + y1) / 2
    return any(
        abs(m[2] - cy) <= 16 and -10 <= x0 - m[3] < DISK_NUMARA_EN_AZ
        for m in s["simge"]
    )


def _ustler(
    capa: list[list[int]],
    tavan0: int,
    murekkep: np.ndarray,
    turuncu: np.ndarray,
    sayac: Counter[str],
    *,
    murekkep2d: np.ndarray,
    sol_kayma: int,
) -> list[int]:
    """Her capa icin kutu ustu (UST_PAY kirpmasi oncesi)."""
    out = []
    for i, (y, _) in enumerate(capa):
        tavan = capa[i - 1][1] + 1 if i else tavan0
        bas = max(tavan, y - LOGO_PENCERE)
        pen = turuncu[bas:y]
        satir = np.where(pen.sum(axis=1) >= 3)[0]
        if pen.sum() >= LOGO_EN_AZ and len(satir):
            ust_logo = bas + int(satir.min())
            u = max(tavan, ust_logo - 6)
            # AYT: onceki sorunun secenek satiri logoya 6 px'ten yakin, hatta
            # logonun ust kenarindan ASAGI sarkabilir (T114_04, T143_05, T157_10:
            # secenegin alt kenari / integralin alt siniri sonraki kutuya gecti).
            # Logonun SOLUNDA, logo ustu - 6 ile capa - 10 arasindaki son murekkep
            # satirinin 2 px altina in (logo ve 'KOSESI' yazisi bu bolgenin disinda).
            lx = int(np.where(pen.sum(axis=0) >= 3)[0].min()) - sol_kayma
            alt = min(y - 10, ust_logo + LOGO_ALT_PENCERE)
            dolu = np.where(murekkep2d[u:alt, : max(0, lx - 4)].any(axis=1))[0]
            if len(dolu):
                u = min(y - UST_PAY - 1, u + int(dolu.max()) + 2)
                sayac["logo_yakin_secenek"] += 1
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
            if t == "R":
                x0b = ayrac_bandi_sonu(a, x0)
                if x0b != x0:
                    sayac["ayrac_bandi"] += 1
                x0 = x0b
            xg = max(x0, NUMARA_X0[t] - 3)
            murekkep2d = a[:, xg:x1].min(axis=2) < MUREKKEP
            murekkep = murekkep2d.any(axis=1)
            turuncu = (
                np.abs(a[:, x0:x1].astype(np.int16) - LOGO).sum(axis=2) < LOGO_ESIK
            )
            ustler = _ustler(
                capa,
                tavan0,
                murekkep,
                turuncu,
                sayac,
                murekkep2d=murekkep2d,
                sol_kayma=xg - x0,
            )
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
                        "numara_disk_ortulu": kaynak_kanal != "simge"
                        and numara_disk_ortulu(s, t, capa[i][0]),
                    }
                )
    kutular.sort(key=lambda k: (k["birim"], k["soru"]))
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutular)
    return {
        "kaynak": "345 2025 AYT Kimya Soru Bankasi",
        "kart": [589, 43, KART_G, KART_Y],
        "capa": "sutun basina: basili numara sayisi == cevap satiri girdi sayisi ise numara, degilse simge (345_2025_ayt_kimya_capa_taramasi.json)",
        "kural": (
            f"Kutu ustu: capadan yukari ilk {BOSLUK} satirlik bos bandin alt ucu - {UST_PAY} "
            "(tavan onceki capa / sayfanin bant tavani, kim345ayt_tarama.bant_tavani); "
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
