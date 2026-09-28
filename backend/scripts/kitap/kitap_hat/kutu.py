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
kapsamadigi koyu murekkep satiri (> ARTIK_ESIK piksel) yok.

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.kutu --profil K [--yaz]
"""

from __future__ import annotations

import argparse
import itertools
from collections import defaultdict
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


def _satirlar(a: np.ndarray, x0: int, x1: int) -> np.ndarray:
    m: np.ndarray = (a[:, x0:x1].min(axis=2) < MUREKKEP).any(axis=1)
    return m


def _ust(y: int, tavan: int, murekkep: np.ndarray) -> int:
    bos = 0
    r = y - 1
    while r >= tavan:
        if murekkep[r]:
            bos = 0
        else:
            bos += 1
            if bos >= BOSLUK:
                return max(tavan, r + BOSLUK - UST_PAY)
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


def _alt_sinir(p: ModuleType, sayfa: dict, x0: int, x1: int) -> int:
    s = sayfa.get("anahtar")
    if s and min(x1, s[3]) - max(x0, s[2]) > 20:
        return int(s[0]) - int(p.SERIT_PAY)
    return int(p.SAYFA_ALTI)


def kutulari_uret(p: ModuleType) -> tuple[dict[str, Any], list[str]]:
    tarama = ortak.oku(p, "capa_taramasi")
    anahtar = ortak.oku(p, "cevap_anahtari")
    cevap = {(c["dosya"], c["sutun"], c["sutun_sira"]): c for c in anahtar["cevaplar"]}
    kaynak = ortak.kaynak_dizin(p)
    sutun: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for t in tarama["testler"]:
        for c in t["capalar"]:
            sutun[(c["dosya"], c["sutun"])].append(c)
    kutular, artik = [], []
    cache: dict[int, np.ndarray] = {}
    for (d, s), sutun_capa in sorted(sutun.items()):
        if d not in cache:
            cache.clear()
            cache[d] = beyaz_sayfa(p, kaynak, d, tarama["sayfalar"][str(d)]["glif"])[0]
        a = cache[d]
        x0, x1 = p.SUTUNLAR[d % 2][s]
        mur = _satirlar(a, x0, x1)
        capa = sorted(sutun_capa, key=lambda c: c["y"])
        alt_sinir = _alt_sinir(p, tarama["sayfalar"][str(d)], x0, x1)
        ustler = []
        cizgi = _yatay_cizgiler(a, x0, x1) if getattr(p, "AYRAC_TAVAN", False) else []
        for i, c in enumerate(capa):
            tavan = capa[i - 1]["y"] + 12 if i else p.UST_BANT
            # Konu sayfasi ayrac cizgisi (ORNEK bolumu ile sorular arasi):
            # numaranin ustundeki en yakin sutun-genisligi yatay cizgi tavandir.
            ust_cizgi = [y for y in cizgi if tavan <= y < c["y"]]
            if ust_cizgi:
                tavan = max(ust_cizgi) + 2
            ustler.append(min(_ust(c["y"], tavan, mur), c["y"] - UST_PAY))
        for i, c in enumerate(capa):
            alt = ustler[i + 1] - 1 if i + 1 < len(capa) else alt_sinir
            cv = cevap[(d, s, i)]
            kutular.append(
                {
                    "birim": cv["birim"],
                    "soru": cv["soru"],
                    "dosya": d,
                    "sutun": s,
                    "sutun_sira": i,
                    "kutu": [x0, ustler[i], x1, alt],
                    "capa": [c["y"], c["x"]],
                }
            )
        kapsanan = np.zeros(a.shape[0], bool)
        for k in kutular[-len(capa) :]:
            kapsanan[k["kutu"][1] : k["kutu"][3]] = True
        koyu = (a[:, x0:x1].min(axis=2) < 160).sum(axis=1)
        bas_y = p.UST_BANT
        if getattr(p, "ARTIK_ILK_KUTUDAN", False):
            bas_y = ustler[0]
        for y in range(bas_y, alt_sinir):
            if not kapsanan[y] and koyu[y] > ARTIK_ESIK:
                artik.append(f"artik murekkep s{d}{s} y{y} ({int(koyu[y])} px)")
                break
    kutular.sort(key=lambda k: (k["birim"], k["soru"]))
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
        if s and min(x1, s[3]) - max(x0, s[2]) > 20 and y1 > s[0]:
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
