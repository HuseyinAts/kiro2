#!/usr/bin/env python
"""345 2025 Paragraf Sifir Risk: soru ve ortak metin kirpim kutularini uretir.

CAPA SECIMI -- SUTUNUN SORU SAYISI KARAR VERIR
----------------------------------------------
Iki bagimsiz piksel kanali (`prg345_tarama.py`): basili (siyah) soru numarasi
ve FERNUS okuyucu simgesi (13x13). Bir sutunun capasi, sayisi o sutunun soru
sayisina (kitap sonu anahtarin girdileri, bant okumasiyla sayfaya/sutuna
dagitilmis) ESIT olan kanaldir; once numara (genisligi <= NUMARA_EN_GENIS;
ortak metin basligi icindeki '1 - 2.' rakamlari capa degildir), o tutmazsa
simge, o da tutmazsa iki kanalin BIRLESIGI (ayni soruyu gosteren numara+simge
BIRLESIK_Y icinde tek capa); kanal sayisi fazlaysa en alttaki k tanesi
(numara_alt / simge_alt). Hicbiri tutmazsa sutuna kutu URETILMEZ (tahmin yok).
Olculen (673 soru sutunu): numara 614, simge 57, numara_alt 2 (4R, 201L;
gozle dogru); kutusuz soru 0. Numarasi okuyucu diski altinda kalan kutu 229
(DISK_NUMARA_EN_AZ). Sutun ustundeki simge (y ust 89) sayilir: s315R'de
'6.' numarasi basilmamis, capa yalniz simge.

DIKEY KURAL
-----------
- Kutu ustu: capadan yukari, okuyucu katmani beyazlatilmis sayfada, numara
  seridinden sutun sagina kadar, en az BOSLUK satirlik bos bant aranir; kutu
  ustu o bandin alt ucu - UST_PAY. Tavan: ayni sutundaki onceki capanin alti
  ya da sayfanin bant tavani (prg345_tarama.bant_tavani).
- Bant capadan UST_EN_COK px'ten daha yukarida kaliyorsa, capanin 25 px
  ustune kadar >= 3 satirlik kisa bos bant aranir (8 kutu, 'kisa_bant_kutu';
  gozle hepsi dogru).
- Bos bant icin murekkep = koyu VE doygun olmayan piksel (_murekkep): OSYM
  KOSESI'nin kirmizi dikey cerceve cizgisi aksi halde her satiri dolu
  gosterip cerceveli bolgede kutu ustunu ortak parcanin icine dusuruyordu
  (s154L T023_09; ikinci okuma 'kesik son satir' bildirimiyle bulundu).
- AYT hattindaki 'OSYM KOSESI' logo kurali bu kitapta YOK: turuncu kaynak
  etiketi ('2025 - MSU', 82x3-16 px) logo sanilip onceki sorunun etiketi
  sonraki kutuya giriyordu (8 kutu); kural kapatilinca logo ustu bos bant
  kuralina zaten dahil (gozle 36 degisen kutu).
- Konu kutusu kenari (ayrac_bandi_sonu) yalniz acik MAVI dolulukla sayilir
  (_mavi_dolu); bu kitapta kaydirma 0 (renksiz sayim s336/338'de resmi,
  s139/146/349'da sayfa zeminini bant sanip sag kutuyu numaranin sagina
  itiyordu).
- Kutu alti: ayni sutundaki sonraki kutunun ustu - 1; sutunun son sorusunda
  SAYFA_ALTI (metin en cok y 902, alt bilgi logosu 905'ten itibaren).
- Tek sutunlu (tam genislik) sayfalar (348, 350-353, 355; ara cizgi yok ve
  sag sutunda soru yok): kutu sayfa kenarlari (KENAR) arasinda.
- Olcum (kapi degil, rapor): kutu ustunun +-3 satirinda notr koyu metin
  varsa kutu 'kesim_metne_degen_kutu' listesine girer (105; gozle hepsi
  sayfa basligi / sure kutusu / kose susu, soru metni kesen yok).

ORTAK METIN
-----------
'7 - 8. sorulari asagidaki parcaya gore cevaplayiniz' basligi koyu (max <
130, doygunluk < 40) cerceveli kutu; `ortak_basliklari` bir sutunda >=
ORTAK_KOSU px koyu yatay kosu ciftini (ORTAK_ARALIK) baslik sayar (yan
kenarlar dolu, ic tablo ayraci yok, 45 px komsulukta baska uzun kenar yok).
Baslik sutun basindaysa ortak kutu = baslik ustu - UST_PAY .. ilk soru kutusu
ustu - 1; sutun ortasindaysa onceki sorunun kutusu basligin ustunde biter.
Cercevesiz yonerge ELLE_BASLIK'ta (s170L '18 - 20. sorularda ...').
Olculen: 29 cerceveli + 1 elle = 30; soru kutusu ICINDE baslik 0 (kapi).
Ikinci kanal: sutun tavani ile sutunun ilk sahipli ustu arasinda
SAHIPSIZ_ESIK px'ten uzun murekkep ('sutun_ustu_sahipsiz_murekkep'); 168
sutunun 168'i test ilk sayfasi (test tanitim paneli), baska sutun yok
(kapi). Bu kanal s324/326/328 L'deki kacirilmis basliklari buldu (simge
maskesi ust kenarin sag ucunu kisaltiyordu -> ORTAK_SAG_TOLERANS/_YAN).

YATAY KURAL
-----------
Sutunlar arasi ara cizgi taramadan; olculemezse tek/cift varsayilani.
Sayfanin renkli kenar seridi disarida birakilir:

    cift: sol [30, cizgi-2]  sag [cizgi+3, 738]
    tek : sol [4,  cizgi-2]  sag [cizgi+3, 711]

KULLANIM
--------
    python backend/scripts/kitap/prg345_kutu.py
    python backend/scripts/kitap/prg345_kutu.py --yaz
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
from prg345_tarama import bant_tavani, cerceve_maskesi, kart, kaynak_dizin

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
TARAMA = CIKTI / "345_2025_paragraf_capa_taramasi.json"
ANAHTAR = CIKTI / "345_2025_paragraf_cevap_anahtari.json"
HEDEF = CIKTI / "345_2025_paragraf_kirpim_kutulari.json"
HARITA = CIKTI / "345_2025_paragraf_konu_haritasi.json"

KART_G, KART_Y = 742, 977
UST_PAY = 3
BOSLUK = 10
MUREKKEP = 170
MUREKKEP_DOYGUNLUK = 90
UST_EN_COK = 70
NUMARA_X0 = {"L": 55, "R": 359}
DISK_NUMARA_EN_AZ = 16
SIMGE_PAY = 3
# Olculdu (673 sutun, notr koyu satir kosulari y 860-977): soru metni en cok
# y 902'de biter; alt bilgi (UcDortBes logosu) 905'te baslar. 896 iken 70+
# sutunun son satiri (sik D/E) yarim kesiliyordu (grup 1 okumasi: T001_16).
SAYFA_ALTI = 904
EN_KISA = 30
BEKLENEN_KUTU = 1012
VARSAYILAN_CIZGI = {0: 369, 1: 372}
KENAR = {0: (30, 738), 1: (4, 711)}
SAG_SOL_EN_COK = 373
SIMGE_X = {"L": (30, 80), "R": (350, 400)}
BIRLESIK_Y = 15
NUMARA_EN_GENIS = 12
AYRAC_EN_GENIS = 15
AYRAC_ORAN = 0.2
ORTAK_KOSU = 200
ORTAK_ARALIK = (15, 60)
# Ust kenarin sag ucu okuyucu simgesi maskesiyle kisalabilir (s324/326/328 L:
# ust kenar x 76-352, alt kenar 76-360; simge basligin sag ustunde).
ORTAK_SAG_TOLERANS = 12
ORTAK_SAG_YAN = 0.3
BEKLENEN_ORTAK = 30  # 29 cerceveli baslik + 1 ELLE_BASLIK
# Sutun tavani ile sutunun ilk sahipli ustu (ilk soru / ortak kutusu) arasinda
# SAHIPSIZ_ESIK px'ten uzun murekkep: kacirilmis ortak metin adayi (ikinci kanal).
SAHIPSIZ_ESIK = 40
# Cercevesiz ortak yonergeler (gozle olculdu) {(sayfa, sutun): [[y_ust, y_alt]]}.
# 170L: '18 - 20. sorularda, numaralanmis cumlelerin ...' yonergesi 18'in 25 px
# ustunde, cercevesiz; bos bant kurali onu hicbir kutuya koymuyordu. 18-20'nin
# ortak metni olarak kirpilir (baslik gibi: kutu = y_ust - UST_PAY .. 18 ustu - 1).
ELLE_BASLIK = {(170, "L"): [[146, 176]]}


def sutun_siniri(d: int, t: str, cizgi: int | None) -> tuple[int, int]:
    c = cizgi if cizgi is not None else VARSAYILAN_CIZGI[d % 2]
    sol, sag = KENAR[d % 2]
    # Sag sutun en cok SAG_SOL_EN_COK'tan baslar: OSYM KOSESI sayfalarinda
    # (110, 139, 146, 349) olculen 'ara cizgi' cercevenin sol kenari (x 379-380);
    # c + 3 sag sutunun soru numarasini (x ~377-390) kesiyordu (okuma: T021_07
    # vb. basili_no null).
    return (sol, c - 2) if t == "L" else (min(c + 3, SAG_SOL_EN_COK), sag)


def _mavi_dolu(sutun: np.ndarray) -> np.ndarray:
    """Acik mavi ayrac bandi pikseli: min kanal < 245 ve mavi, kirmizidan >= 40 fazla.

    Paragraf s336/338: tam genislikli resim y 200-440'ta x 373-388'i doldurup
    (%32 >= AYRAC_ORAN) renk kosulu olmadan sag kutuyu 17 px iceri itiyordu
    ('2.' numarasi kutu disinda kaliyordu).
    """
    s = sutun.astype(np.int16)
    dolu: np.ndarray = (s.min(axis=1) < 245) & (s[:, 2] - s[:, 0] >= 40)
    return dolu


def ayrac_bandi_sonu(a: np.ndarray, x0: int) -> int:
    """Sag sutun sol siniri: konu kutusunun kalin acik mavi sag kenari (x ~368-376, renk
    ~(141,215,247)) ara cizgi olarak olculdugunde sag kutu bu bandin icinden baslar. x0'dan
    saga, y 130-880'in >= AYRAC_ORAN'i dolu (min kanal < 245) sutunlari atla; en cok AYRAC_EN_GENIS.
    Konu kutusuz sayfada (tek ince cizgi) x0 degismez."""
    x = x0
    while x < x0 + AYRAC_EN_GENIS and _mavi_dolu(a[130:880, x]).mean() >= AYRAC_ORAN:
        x += 1
    return x if x == x0 else x + 2


def _kosular(v: np.ndarray) -> list[tuple[int, int]]:
    out, bas = [], None
    for i, x in enumerate([*v.tolist(), False]):
        if x and bas is None:
            bas = i
        elif not x and bas is not None:
            out.append((bas, i - 1))
            bas = None
    return out


def ortak_basliklari(a: np.ndarray, x0: int, x1: int) -> list[list[int]]:
    """Ortak metin basligi kutulari ('17 - 18. sorulari asagidaki parcaya gore
    cevaplayiniz'): koyu (max < 130, doygunluk < 40) cerceveli kutu. Sutun
    icinde >= ORTAK_KOSU px kesintisiz koyu yatay kosu bir kenardir (kalin
    cizginin sonraki <= 4 satiri ayni kenar); ust+alt kenar cifti ORTAK_ARALIK
    icinde, sol uclari +-5 px, sag uclari ORTAK_SAG_TOLERANS icinde ayni, iki yan kenar dikey cizgi (>= %80 dolu), ic
    bolumde tablo ayraci yok ve ciftin 45 px ust/altinda ayni hizada baska uzun
    kenar yok (tablo satiri degil). Donus: [[y_ust, y_alt], ...]."""
    b = a[:, x0:x1].astype(np.int16)
    k = (b.max(axis=2) < 130) & ((b.max(axis=2) - b.min(axis=2)) < 40)
    kenar: list[tuple[int, int, int]] = []
    for y in range(80, SAYFA_ALTI):
        for c0, c1 in _kosular(k[y]):
            if c1 - c0 < ORTAK_KOSU:
                continue
            if any(y - e[0] <= 4 and abs(e[1] - c0) < 5 for e in kenar[-4:]):
                continue
            kenar.append((y, c0, c1))
    out = []
    for i, (y, c0, c1) in enumerate(kenar):
        for y2, c2, c3 in kenar[i + 1 :]:
            if not (
                ORTAK_ARALIK[0] <= y2 - y <= ORTAK_ARALIK[1]
                and abs(c2 - c0) < 6
                and abs(c3 - c1) < ORTAK_SAG_TOLERANS
            ):
                continue
            komsu = [
                e
                for e in kenar
                if e not in ((y, c0, c1), (y2, c2, c3))
                and abs(e[1] - c0) < 40
                and (y - 45 <= e[0] < y or y2 < e[0] <= y2 + 45)
            ]
            ic = k[y + 3 : y2 - 2, c0 : max(c1, c3) + 1]
            yanlar = (
                ic[:, :4].any(axis=1).mean() > 0.8
                # sag kenar okuyucu simgesi maskesiyle kismen silinebilir (s324 L)
                and ic[:, -4:].any(axis=1).mean() > ORTAK_SAG_YAN
            )
            ayrac = bool((ic[:, 6:-6].mean(axis=0) > 0.8).any())
            if not komsu and yanlar and not ayrac:
                out.append([y, y2])
            break
    return out


def sutun_simgeleri(sayfa: dict, t: str) -> list[list[int]]:
    x0, x1 = SIMGE_X[t]
    return sorted(s for s in sayfa["simge"] if 90 <= s[2] < 900 and x0 <= s[3] < x1)


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
    capa: list[list[int]], tavan0: int, murekkep: np.ndarray, asim: list[int]
) -> list[int]:
    """Her capa icin kutu ustu (UST_PAY kirpmasi oncesi); asim: kisa bant sirasi."""
    out = []
    for i, (y, _) in enumerate(capa):
        tavan = capa[i - 1][1] + 1 if i else tavan0
        u = _ust(y, tavan, murekkep)
        if u < y - UST_EN_COK:
            # Bant bulunamadi (onceki sorunun cercevesi/secenekleri bitisik):
            # capanin hemen ustunde >= 3 satirlik kisa bos bant ara (en cok 25 px).
            u = _ust(y, max(tavan, y - 25), murekkep, bosluk=3, pay=1)
            asim.append(i)
        out.append(u)
    return out


def _sutun_x(
    a: np.ndarray, d: int, t: str, cizgi: int | None, *, tam: bool, sayac: Counter[str]
) -> tuple[int, int]:
    """Sutunun x siniri; tam: tek sutunlu (tam genislik) sayfa (348, 350-353, 355)."""
    if tam:
        sayac["tam_genislik"] += 1
        return KENAR[d % 2]
    x0, x1 = sutun_siniri(d, t, cizgi)
    if t == "R":
        x0b = ayrac_bandi_sonu(a, x0)
        if x0b != x0:
            sayac["ayrac_bandi"] += 1
        x0 = x0b
    return x0, x1


def _murekkep(b: np.ndarray) -> np.ndarray:
    """Bos bant icin murekkep: koyu (min < MUREKKEP) ve doygun OLMAYAN piksel.

    OSYM KOSESI'nin kirmizi dikey cerceve cizgisi (~(236,28,37), sutunun sag
    ucunda x 356-357) doygunluk kosulu olmadan her satiri dolu gosteriyor,
    cerceveli bolgede hic bos bant birakmiyordu (s154L T023_09 kutu ustu
    ortak parcanin son iki satiri arasina dustu).
    """
    b16 = b.astype(np.int16)
    m: np.ndarray = (b16.min(axis=2) < MUREKKEP) & (
        (b16.max(axis=2) - b16.min(axis=2)) < MUREKKEP_DOYGUNLUK
    )
    return m


def _sayfa(kaynak: Path, d: int, s: dict) -> np.ndarray:
    a: np.ndarray = kart(kaynak, d).astype(np.uint8)
    a[okuyucu_maskesi(a, [[x[2], x[3]] for x in s["simge"]])] = 255
    a[cerceve_maskesi(a, d)] = 255
    # Simge kutusu (+SIMGE_PAY) tamamen beyaz: renk maskesinden kalabilecek
    # kenar pikselleri bos bant olcumune girmesin (bu kitapta etkisi olculdu:
    # 0 kutu degisti; guvence olarak kalir).
    # simge = [y_ust, x_sol, y_merkez, x_merkez] (13x13 kutu).
    for y0, x0, cy, cx in s["simge"]:
        a[
            max(0, y0 - SIMGE_PAY) : 2 * cy - y0 + SIMGE_PAY + 1,
            max(0, x0 - SIMGE_PAY) : 2 * cx - x0 + SIMGE_PAY + 1,
        ] = 255
    return a


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
    ortak: list[dict] = []
    ortak_icte: list[str] = []
    sahipsiz: list[dict] = []
    tavan_asimi: list[str] = []
    ek_ust = 0
    for d in sorted({k[0] for k in sutunlar}):
        s = tarama[str(d)]
        a = _sayfa(kaynak, d, s)
        tavan0 = bant_tavani(a)
        for t in "LR":
            qs = sorted(sutunlar.get((d, t), []), key=lambda c: c["serit_sira"])
            if not qs:
                continue
            tam = t == "L" and s["ara_cizgi"] is None and not sutunlar.get((d, "R"))
            x0, x1 = _sutun_x(a, d, t, s["ara_cizgi"], tam=tam, sayac=sayac)
            basliklar = ortak_basliklari(a, x0, x1) + ELLE_BASLIK.get((d, t), [])
            k = len(qs)
            s_t = {
                **s,
                "numara": {
                    **s["numara"],
                    t: [
                        n
                        for n in s["numara"][t]
                        if not any(h[0] <= n[0] <= h[1] for h in basliklar)
                    ],
                },
            }
            secim = _capa_sec(s_t, t, k)
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
            xg = max(x0, NUMARA_X0[t] - 3)
            murekkep: np.ndarray = np.asarray(_murekkep(a[:, xg:x1]).any(axis=1))
            asim: list[int] = []
            ustler = _ustler(capa, tavan0, murekkep, asim)
            ek_ust += sum(
                1 for u, (y, _) in zip(ustler, capa, strict=True) if u < y - UST_PAY
            )
            ustler = [
                min(u, y - UST_PAY) for u, (y, _) in zip(ustler, capa, strict=True)
            ]
            alt_sinir: dict[int, int] = {}
            sahip_ust = ustler[0]
            for h in basliklar:
                j = next((i for i, (y, _) in enumerate(capa) if y > h[1]), None)
                if j is None or ustler[j] < h[0]:
                    ortak_icte.append(f"{d}{t} y{h[0]}")
                    continue
                if j:  # sutun ortasi: onceki sorunun kutusu basligin ustunde biter
                    alt_sinir[j - 1] = h[0] - UST_PAY - 1
                sahip_ust = min(sahip_ust, h[0] - UST_PAY)
                ortak.append(
                    {
                        "ortak": f"PRG345-O{d:03d}{t}{h[0]:03d}",
                        "dosya": d,
                        "sutun": t,
                        "kutu": [x0, h[0] - UST_PAY, x1, ustler[j] - 1],
                        "baslik": h,
                        "ilk_soru": {"birim": qs[j]["birim"], "soru": qs[j]["soru"]},
                    }
                )
            dolu = np.where(murekkep[tavan0:sahip_ust])[0]
            if len(dolu) and sahip_ust - (tavan0 + int(dolu.min())) > SAHIPSIZ_ESIK:
                sahipsiz.append(
                    {
                        "sutun": f"{d}{t}",
                        "murekkep_ust": tavan0 + int(dolu.min()),
                        "sahip_ust": sahip_ust,
                    }
                )
            b = a[:, x0:x1].astype(np.int16)
            notr = (((b.max(axis=2) - b.min(axis=2)) < 40) & (b.min(axis=2) < 140)).sum(
                axis=1
            )
            for i, q in enumerate(qs):
                if int(notr[ustler[i] - 3 : ustler[i] + 3].sum()):
                    kesim.append(f"{q['birim']}_{q['soru']:02d}")
                if i in asim:
                    tavan_asimi.append(f"{q['birim']}_{q['soru']:02d}")
                alt = ustler[i + 1] - 1 if i + 1 < k else SAYFA_ALTI
                alt = min(alt, alt_sinir.get(i, alt))
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
        "kaynak": "345 2025 Paragraf Sifir Risk Soru Bankasi",
        "kart": [589, 43, KART_G, KART_Y],
        "capa": "sutun basina: basili numara sayisi == sutunun soru sayisi (kitap sonu anahtar) ise numara, degilse simge (345_2025_paragraf_capa_taramasi.json)",
        "kural": (
            f"Kutu ustu: capadan yukari ilk {BOSLUK} satirlik bos bandin alt ucu - {UST_PAY} "
            "(tavan onceki capa / sayfanin bant tavani, prg345_tarama.bant_tavani); "
            f"alti sonraki kutunun ustu - 1, sutun sonunda {SAYFA_ALTI}."
        ),
        "sutun_kanali": dict(kanal),
        "ust_kurali_sayaci": dict(sayac),
        "kesim_metne_degen_kutu": kesim,
        "kisa_bant_kutu": tavan_asimi,
        "capanin_ustune_uzayan_kutu": ek_ust,
        "kutu_sayisi": len(kutular),
        "kutusuz_soru": len(kutusuz),
        "yukseklik": {"min": yuk[0], "medyan": yuk[len(yuk) // 2], "max": yuk[-1]}
        if yuk
        else None,
        "kutular": kutular,
        "kutusuz": kutusuz,
        "ortak_metin_kurali": (
            "Koyu cerceveli ortak metin basligi (ortak_basliklari) ya da ELLE_BASLIK: "
            "ortak metin kutusu baslik ustu - UST_PAY .. basligin altindaki ilk soru "
            "kutusu ustu - 1; sutun ortasinda onceki soru kutusu basligin ustunde biter."
        ),
        "ortak_metinler": ortak,
        "soru_kutusu_icinde_ortak_baslik": ortak_icte,
        "sutun_ustu_sahipsiz_murekkep": sahipsiz,
    }


def ortak_kapilari(veri: dict[str, Any]) -> list[str]:
    """Ortak metin sayisi BEKLENEN_ORTAK; soru kutusunun ICINDE ortak baslik yok;
    sutun ustu sahipsiz murekkep yalniz test ilk sayfasinda (tanitim paneli)."""
    hata = []
    ilk = {t["sayfalar"][0] for t in json.loads(HARITA.read_text("ascii"))["testler"]}
    for e in veri["sutun_ustu_sahipsiz_murekkep"]:
        if int(e["sutun"][:-1]) not in ilk:
            hata.append(f"sutun ustu sahipsiz murekkep (ortak adayi): {e}")
    if len(veri["ortak_metinler"]) != BEKLENEN_ORTAK:
        hata.append(f"ortak metin {len(veri['ortak_metinler'])} != {BEKLENEN_ORTAK}")
    if veri["soru_kutusu_icinde_ortak_baslik"]:
        hata.append(
            f"soru kutusu icinde ortak baslik: {veri['soru_kutusu_icinde_ortak_baslik']}"
        )
    return hata


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
    hata.extend(ortak_kapilari(veri))
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
    print(f"ortak metin: {len(veri['ortak_metinler'])}")
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
