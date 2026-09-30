"""Soru kirpim kutulari (profil gudumlu; acil2021tyt_kutu deseni).

YATAY: profilin SUTUNLAR sinirlari (sayfa paritesine gore; sutun ayraci ve
murekkep projeksiyonundan olculur).

DIKEY
-----
- ust : numaradan yukari, okuyucu diski beyazlatilmis sayfada en az BOSLUK
        satirlik bos bandin alt ucu - UST_PAY; tavan onceki numaranin alti
        ya da UST_BANT (test bandi alti).
- alt : ayni sutundaki sonraki kutunun ustu - 1; sutunun sonuncusunda
        SAYFA_ALTI ya da cevap anahtari o sutunla yatayda ortusuyorsa
        anahtarin ustu - SERIT_PAY.

KAPILAR
-------
kutu sayisi == BEKLENEN_SORU == anahtar; kart ici; >= EN_KISA; ayni sutunda
cakisma yok; numara kutunun icinde; kutu anahtara girmiyor; SUTUN ICI ARTIK
MUREKKEP: sutun sinirlari icinde UST_BANT..alt sinir arasinda hicbir kutunun
kapsamadigi koyu murekkep satiri (> ARTIK_ESIK piksel) yok; ALT SINIR ALTI:
alt sinir ile sayfa altligi (ilk tam genislik satir) arasinda, serit satirlari
haric, koyu satir yok (`alt_sinir_alti`; SAYFA_ALTI yanlis olculmusse kesik
soru burada, kirpim ve okumadan ONCE yakalanir).

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.kutu --profil K [--yaz]
"""

from __future__ import annotations

import argparse
import itertools
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np

from scripts.kitap.kitap_hat import ortak
from scripts.kitap.kitap_hat.kirp import beyaz_sayfa

UST_PAY = 3
BOSLUK = 10
EN_KISA = 40
MUREKKEP = 200
ARTIK_ESIK = 6
ALTLIK_GENISLIK = 250  # sayfa cizgisi / serit cercevesi: tam genislik satir
SERIT_DISI_EN_AZ = 40  # serit sutun icinde basliyorsa seritten onceki kisim taranir
SUTUN_KENAR_PAY = 12  # o dar taramada sutunun sol kenar payi (sayfa susu)
# Dislama blogu ile kutu siniri arasinda birakilan bos px. 4 fazla: BS24AF
# dosya 57'de son sik satiri ile 'UNUTMA' kutusu arasi yalniz ~4 px.
DIS_PAY = 2


def ust_bant(p: ModuleType, a: np.ndarray) -> int:
    """Ust bandin alt siniri: profil `ust_bant(a)` kancasi (sayfaya gore
    olcum; Aktif duzeninde testin ilk sayfasi 99, devam sayfasi 85) ya da
    sabit UST_BANT."""
    f = getattr(p, "ust_bant", None)
    return int(f(a)) if f is not None else int(p.UST_BANT)


def _satirlar(a: np.ndarray, x0: int, x1: int) -> np.ndarray:
    m: np.ndarray = (a[:, x0:x1].min(axis=2) < MUREKKEP).any(axis=1)
    return m


def dislama(p: ModuleType, a: np.ndarray, n: int) -> list[tuple[int, int, int, int]]:
    """Profil `dislama_bolgeleri(a, n)`: SORU OLMAYAN, kutulara girmemesi
    gereken bloklar [(y0, y1, x0, x1)] -- BS24FZ 'AKILLI NOT' bilgi kutusu.
    Bloklar hem artik murekkep taramasindan dusulur hem de komsu kutularin
    sinirlarini kirpar (yoksa blok onceki sorunun kirpimina girer)."""
    f = getattr(p, "dislama_bolgeleri", None)
    if f is None:
        return []
    return [(int(r[0]), int(r[1]), int(r[2]), int(r[3])) for r in f(a, n)]


def _kutu_kirp(
    kutu_: list[int], capa_y: int, dis: list[tuple[int, int, int, int]]
) -> list[int]:
    """Kutunun ust / alt sinirini dislama bloklarina gore kirp."""
    x0, y0, x1, y1 = kutu_
    for ry0, ry1, _, _ in dis:
        if ry0 <= capa_y <= ry1:
            continue
        # ry0 dahil, ry1 haric (find_objects dilimi); DIS_PAY: blogun cerceve
        # kenari kutunun kenar seridine dusmesin (kirp 'kesik' yanlis alarmi).
        if ry0 > capa_y:
            y1 = max(capa_y + 1, min(y1, ry0 - DIS_PAY))
        else:
            y0 = min(capa_y, max(y0, ry1 + DIS_PAY))
    return [x0, y0, x1, y1]


def _ust(y: int, tavan: int, murekkep: np.ndarray, bosluk: int = BOSLUK) -> int:
    """bosluk: profil BOSLUK (sik satirlari arasi bosluk sorular arasi bosluktan
    buyuk olan sikisik dizgide kucuk tutulur; yoksa ust sinir onceki sorunun
    son sik satirinin ustune cikar)."""
    bos = 0
    r = y - 1
    while r >= tavan:
        if murekkep[r]:
            bos = 0
        else:
            bos += 1
            if bos >= bosluk:
                return max(tavan, r + bosluk - UST_PAY)
        r -= 1
    return tavan


def _yatay_cizgiler(a: np.ndarray, x0: int, x1: int) -> list[int]:
    """Sutun genisliginin >= %60'i boyunca koyu (< 200), en fazla 3 satir
    kalinliginda yatay cizgiler (dolu resim alanlari cizgi degil)."""
    k = (a[:, x0:x1].max(axis=2) < 200).sum(axis=1) >= 0.6 * (x1 - x0)
    out, bas = [], None
    for y in range(len(k) + 1):
        on = y < len(k) and bool(k[y])
        if on and bas is None:
            bas = y
        elif not on and bas is not None:
            if y - bas <= 3:
                out.append(y - 1)
            bas = None
    return out


def _alt_sinir(p: ModuleType, sayfa: dict, x0: int, x1: int) -> tuple[int, str | None]:
    """Sutunun alt siniri ve (varsa) uyari: serit sutunla ortusuyor ama
    SERIT_ORTUSME_EN_AZ'in altinda -> sinir SAYFA_ALTI alindi; serit
    sutunun altina kadar iniyorsa son soru seridin yanina uzayabilir."""
    s = sayfa.get("anahtar")
    if not s:
        return int(p.SAYFA_ALTI), None
    ortusme = min(x1, s[3]) - max(x0, s[2])
    if ortusme > getattr(p, "SERIT_ORTUSME_EN_AZ", 20):
        sinir = int(s[0]) - int(p.SERIT_PAY)
        if getattr(p, "SERIT_ALTLIKTA", False):
            # Serit sayfa altliginda (APO19FZ: cizgi + sayfa no bloku seridin
            # ustunde, y 879-888): sinir SAYFA_ALTI'ni gecmez.
            sinir = min(sinir, int(p.SAYFA_ALTI))
        return sinir, None
    if ortusme > 0:
        return int(
            p.SAYFA_ALTI
        ), f"serit sutunla {ortusme} px ortusuyor, sinir SAYFA_ALTI"
    return int(p.SAYFA_ALTI), None


def alt_sinir_alti(
    a: np.ndarray,
    x0: int,
    x1: int,
    alt: int,
    *,
    serit: list[int] | None,
    serit_pay: int,
    altlik_y: int | None = None,
) -> tuple[int, int] | None:
    """Sutunun alt sinirinin ALTINDA kutu icine girmemis koyu satir: (y, px).

    Tarama alt'tan asagi iner. Sayfada serit varsa seridin altinda (serit[1]+2)
    durur: orasi sayfa altligi. Serit sutunla yatayda ORTUSUYORSA serit
    satirlari (serit[0]-serit_pay ..) atlanir; ortusmuyorsa atlanmaz -- serit
    pikselleri zaten sutun disindadir, sutunun serit hizasina inen metni ise
    tam bu satirlarda kesilir (acl24mg s29/104/113: SAYFA_ALTI 885, metin
    889'a kadar; D/E siklari kesik, okuyucu 'kesik' notu dusmustu). Serit yoksa
    ilk GENIS satirda (> ALTLIK_GENISLIK px: sayfa cizgisi) durur. Aradaki
    > ARTIK_ESIK piksellik ilk satir kesik icerik. Sayilar-1'de SAYFA_ALTI 878
    sol sutunun son sorusunu 10 sayfada kesmisti; bu olcum onu kutu asamasinda
    yakalar.

    Serit sutunla ortusuyor ama sutunun ICINDE basliyorsa (serit[2] > x0 +
    2 * SERIT_DISI_EN_AZ) serit satirlarinda sutunun seritten ONCEKI kismi
    (seride SERIT_DISI_EN_AZ px kalana kadar) yine taranir: acl24am s114'te
    serit x araligi sol sutuna kadar (x0 300) olculdu, sol sutun siniri serit
    ustune cekildi ve D/E siklari (y 889-900) kesildi; satir atlamak bunu
    gizliyordu. Bu dar taramada sutunun sol kenarindan SUTUN_KENAR_PAY px
    atlanir: acl25pl sag sutun (x0 390) serit hizasinda x 387-401 capraz
    sayfa susu tasir.

    altlik_y (profil SAYFA_ALTLIGI_Y): seritsiz duzende sayfa altligi (sayfa no
    kutusu, noktalar; tam genislik cizgi YOK) bu satirdan baslar; tarama orada
    durur (Apotemi: altlik y 887-907, 110 px)."""
    son = a.shape[0] if altlik_y is None else min(a.shape[0], altlik_y)
    atla_y = son  # serit sutunla ortusuyorsa bu satirdan itibaren dar tarama
    dar_x1 = x1
    if serit:
        son = min(son, serit[1] + 3)
        if min(x1, serit[3]) > max(x0, serit[2]):
            atla_y = serit[0] - serit_pay
            # seridin solunda SERIT_DISI_EN_AZ px pay: seridi saran cerceve
            # (acl23kc s53/s139 mavi kutu, serit x 432, cerceve x 392) sayilmaz
            dar_x1 = serit[2] - SERIT_DISI_EN_AZ
            if dar_x1 - x0 <= SERIT_DISI_EN_AZ:
                dar_x1 = x0
    g = a[alt:son].min(axis=2) < 160
    for i in range(g.shape[0]):
        y = alt + i
        xa, xb = (x0 + SUTUN_KENAR_PAY, dar_x1) if y >= atla_y else (x0, x1)
        px = int(g[i, xa:xb].sum()) if xb > xa else 0
        if px > ALTLIK_GENISLIK:
            break
        if px > ARTIK_ESIK:
            return y, px
    return None


def _ustler(
    p: ModuleType,
    a: np.ndarray,
    sinir: tuple[int, int],
    capa: list[dict],
    mur: np.ndarray,
) -> list[int]:
    """Sutundaki her capanin kutu ust siniri (numaradan yukari bos bant; tavan
    onceki numara / UST_BANT / konu sayfasi ayrac cizgisi)."""
    x0, x1 = sinir
    cizgi = _yatay_cizgiler(a, x0, x1) if getattr(p, "AYRAC_TAVAN", False) else []
    ustler = []
    for i, c in enumerate(capa):
        tavan = capa[i - 1]["y"] + 12 if i else ust_bant(p, a)
        # Konu sayfasi ayrac cizgisi (ORNEK bolumu ile sorular arasi):
        # numaranin ustundeki en yakin sutun-genisligi yatay cizgi tavandir.
        ust_cizgi = [y for y in cizgi if tavan <= y < c["y"]]
        if ust_cizgi:
            tavan = max(ust_cizgi) + getattr(p, "AYRAC_PAY", 2)
        bosluk = int(getattr(p, "BOSLUK", BOSLUK))
        ustler.append(min(_ust(c["y"], tavan, mur, bosluk), c["y"] - UST_PAY))
    return ustler


def _kutu_ust(p: ModuleType, d: int, s: str, ustler: list[int]) -> list[int]:
    """KUTU_UST {(dosya, sutun, sutun_sira): y}: sorunun ustundeki numarasiz
    ORTAK bilgi (grafik / tablo, 'x-y. sorulari ... gore') o sorunun kutusuna
    katilir (gozle, profilde listeli); yoksa kutu artik murekkep kapisi."""
    for (kd, ks, ki), ky in getattr(p, "KUTU_UST", {}).items():
        if (kd, ks) == (d, s):
            ustler[ki] = min(ustler[ki], int(ky))
    # KUTU_UST_KESIN: iki soru arasindaki bos bant BOSLUK'tan dar oldugu icin
    # ust sinir onceki numaraya kadar cikiyorsa (kutu 'cok kisa' kapisi), sinir
    # gozle olculen y'ye sabitlenir (asagi da inebilir).
    for (kd, ks, ki), ky in getattr(p, "KUTU_UST_KESIN", {}).items():
        if (kd, ks) == (d, s):
            ustler[ki] = int(ky)
    return ustler


def _sutun_alt_siniri(
    p: ModuleType,
    sayfa: dict,
    a: np.ndarray,
    yer: tuple[int, str, int, int],
    *,
    artik: list[str],
    uyarilar: list[str],
) -> int:
    """Sutunun alt siniri; kismi serit ortusmesi uyarisi ve alt sinir altinda
    kalan murekkep (kesik) kaydi yan etki olarak listelere eklenir."""
    d, s, x0, x1 = yer
    alt_sinir, uyari = _alt_sinir(p, sayfa, x0, x1)
    if uyari:
        uyarilar.append(f"s{d}{s}: {uyari}")
    kesik = alt_sinir_alti(
        a,
        x0,
        x1,
        alt_sinir,
        serit=sayfa.get("anahtar"),
        serit_pay=int(p.SERIT_PAY),
        altlik_y=getattr(p, "SAYFA_ALTLIGI_Y", None),
    )
    if kesik:
        artik.append(f"alt sinir altinda murekkep s{d}{s} y{kesik[0]} ({kesik[1]} px)")
    return alt_sinir


def _sayfa_kutu(
    arg: tuple[str, str, int, dict, list[tuple[str, list[dict]]], dict],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Bir sayfanin sutunlari (havuz isi): beyazlat, sinirlar, kutular, artik."""
    kod, kaynak, d, sayfa, sutunlar, cevap = arg
    p = ortak.profil(kod)
    a = beyaz_sayfa(p, Path(kaynak), d, sayfa["glif"])[0]
    kutular: list[dict[str, Any]] = []
    artik: list[str] = []
    uyarilar: list[str] = []
    dis_hepsi = dislama(p, a, d)
    for s, sutun_capa in sutunlar:
        x0, x1 = p.SUTUNLAR[ortak.parite(p, d)][s]
        ox0, ox1 = ortak.olcum_sinir(p, d, s, x0, x1)
        dis = [r for r in dis_hepsi if r[3] > ox0 and r[2] < ox1]
        mur = _satirlar(a, ox0, ox1)
        capa = sorted(sutun_capa, key=lambda c: c["y"])
        alt_sinir = _sutun_alt_siniri(
            p, sayfa, a, (d, s, x0, x1), artik=artik, uyarilar=uyarilar
        )
        ustler = _kutu_ust(p, d, s, _ustler(p, a, (ox0, ox1), capa, mur))
        yeni: list[dict[str, Any]] = []
        for i, c in enumerate(capa):
            alt = ustler[i + 1] - 1 if i + 1 < len(capa) else alt_sinir
            cv = cevap[f"{s}|{i}"]
            yeni.append(
                {
                    "birim": cv["birim"],
                    "soru": cv["soru"],
                    "dosya": d,
                    "sutun": s,
                    "sutun_sira": i,
                    "kutu": _kutu_kirp([x0, ustler[i], x1, alt], c["y"], dis),
                    "capa": [c["y"], c["x"]],
                }
            )
        kutular += yeni
        kapsanan = np.zeros(a.shape[0], bool)
        for k in yeni:
            kapsanan[k["kutu"][1] : k["kutu"][3]] = True
        for ry0, ry1, _, _ in dis:
            kapsanan[max(0, ry0 - DIS_PAY) : ry1 + DIS_PAY] = True
        koyu = (a[:, ox0:ox1].min(axis=2) < 160).sum(axis=1)
        bas_y = ust_bant(p, a)
        if getattr(p, "ARTIK_ILK_KUTUDAN", False):
            bas_y = ustler[0]
        for y in range(bas_y, alt_sinir):
            if not kapsanan[y] and koyu[y] > ARTIK_ESIK:
                artik.append(f"artik murekkep s{d}{s} y{y} ({int(koyu[y])} px)")
                break
    return kutular, artik, uyarilar


def kutulari_uret(p: ModuleType) -> tuple[dict[str, Any], list[str]]:
    tarama = ortak.oku(p, "capa_taramasi")
    anahtar = ortak.oku(p, "cevap_anahtari")
    kaynak = ortak.kaynak_dizin(p)
    sutun: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for t in tarama["testler"]:
        for c in t["capalar"]:
            sutun[(c["dosya"], c["sutun"])].append(c)
    sayfa_sutun: dict[int, list[tuple[str, list[dict]]]] = defaultdict(list)
    for (d, s), sutun_capa in sorted(sutun.items()):
        sayfa_sutun[d].append((s, sutun_capa))
    cevap: dict[int, dict[str, dict]] = defaultdict(dict)
    for c in anahtar["cevaplar"]:
        cevap[c["dosya"]][f"{c['sutun']}|{c['sutun_sira']}"] = c
    isler = [
        (
            ortak.profil_kodu(p),
            str(kaynak),
            d,
            tarama["sayfalar"][str(d)],
            sut,
            cevap[d],
        )
        for d, sut in sorted(sayfa_sutun.items())
    ]
    kutular: list[dict[str, Any]] = []
    artik: list[str] = []
    uyarilar: list[str] = []
    # Sayfalar bagimsiz; sonuc sirasi (sayfa, sutun) -- sirali surumle ayni.
    for k, a_, u in ortak.paralel(_sayfa_kutu, isler):
        kutular += k
        artik += a_
        uyarilar += u
    kutular.sort(key=lambda k: (k["birim"], k["soru"]))
    if uyarilar:
        print(f"uyari {len(uyarilar)} (serit-sutun kismi ortusme; kapi degil):")
        for uy in uyarilar[:20]:
            print("   ", uy)
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutular)
    veri = {
        "kaynak": p.KAYNAK_ADI,
        "arac": "scripts/kitap/kitap_hat/kutu.py",
        "capa": "kirmizi basili soru numarasi (capa_taramasi.json)",
        "sutun_sinirlari": {"tek": p.SUTUNLAR[1], "cift": p.SUTUNLAR[0]},
        "kutu_sayisi": len(kutular),
        "yukseklik": {"min": yuk[0], "medyan": yuk[len(yuk) // 2], "max": yuk[-1]},
        "kutular": kutular,
    }
    return veri, artik


def kapilar(p: ModuleType, veri: dict[str, Any], tarama: dict[str, Any]) -> list[str]:
    hata = []
    kg, ky = p.KART[2] - p.KART[0], p.KART[3] - p.KART[1]
    if veri["kutu_sayisi"] != p.BEKLENEN_SORU:
        hata.append(f"kutu sayisi {veri['kutu_sayisi']} != {p.BEKLENEN_SORU}")
    for k in veri["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        if not (0 <= x0 < x1 <= kg and 0 <= y0 < y1 <= ky):
            hata.append(f"kart disi/ters: {k['birim']}_{k['soru']}")
        if y1 - y0 < EN_KISA:
            hata.append(f"cok kisa: {k['birim']}_{k['soru']} {y1 - y0}px")
        if not y0 <= k["capa"][0] < y1:
            hata.append(f"numara kutu disinda: {k['birim']}_{k['soru']}")
        s = tarama["sayfalar"][str(k["dosya"])].get("anahtar")
        ortusme = min(x1, s[3]) - max(x0, s[2]) if s else 0
        if s and ortusme > getattr(p, "SERIT_ORTUSME_EN_AZ", 20) and y1 > s[0]:
            hata.append(f"anahtara giriyor: {k['birim']}_{k['soru']}")
    grup = defaultdict(list)
    for k in veri["kutular"]:
        grup[(k["dosya"], k["sutun"])].append(k)
    for anahtar, g in grup.items():
        g.sort(key=lambda k: k["kutu"][1])
        for a, c in itertools.pairwise(g):
            if a["kutu"][3] > c["kutu"][1]:
                hata.append(f"cakisma: {anahtar}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    ap.add_argument("--yaz", action="store_true")
    args = ap.parse_args()
    p = ortak.profil(args.profil)
    veri, artik = kutulari_uret(p)
    hata = kapilar(p, veri, ortak.oku(p, "capa_taramasi")) + artik
    print(
        f"kutu {veri['kutu_sayisi']}, yukseklik {veri['yukseklik']}, kapi ihlali {len(hata)}"
    )
    for h in hata[:40]:
        print("   ", h)
    if hata:
        raise SystemExit(1)
    if args.yaz:
        ortak.yaz(p, "kirpim_kutulari", veri)
        print("yazildi")


if __name__ == "__main__":
    main()
