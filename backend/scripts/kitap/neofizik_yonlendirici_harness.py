#!/usr/bin/env python
"""Neofizik ciktisini etiketli benchmark'a cevirir; yonlendirici adaylarini puanlar.

NEDEN
-----
Ikinci okumayi herkese degil secici uygulamak hattin en buyuk zaman blogunu
(iki okuma gecisi, ~1 s 40 dk) kisaltir. Ama secici yapmak icin bir
YONLENDIRICI sinyal lazim ve yanlis sinyal = kalite kaybi. Neofizik kosumu
simdi etiketli bir veri seti: iki bagimsiz okuma, 18 hakem karari, 471
bagimsiz cozum. Her aday sinyal bir sonraki kitapta korlemesine degil, BURADA
cevrimdisi test edilir.

KABUL KURALI (sifir tolerans)
-----------------------------
Aday, ikinci okumaya gonderdigi kume hakeme giden 18 sorunun 18'ini de
iceriyorsa VE bu kume %100'den kucukse KABUL. Ek olarak raporlanir:
  - okuma1_yanlis (12): hakemin okuma-1'i YANLIS buldugu kume -- yonlendirme
    olmasaydi ogrenciye hatali giderdi; asil korunmasi gereken kume bu.
  - dusuk_uyum (141): iki okuma normalize uyumu < 0,995.
  - cozum_uyusmaz (15): bagimsiz cozucu != basili anahtar.

ADAYLAR YALNIZCA OKUMA-1'DEN TURETILIR
--------------------------------------
Uretimde yonlendirici okuma-2'yi gormez. Bu yuzden her ozellik okuma-1 ham
metni, okuma-1 bayraklari ve kutu geometrisinden hesaplanir. Birlestirilmis
v2 metni KULLANILMAZ: 18 hakemli sorunun 12'sinde okuma-1'den farkli, yani
onu kullanmak etiketten ozellige sizinti olurdu.

Cozucu tabanli iki sinyal (cozucu_metin_sorunu, cozucu_guven_orta) okuma-2
degil ama bir COZUM kosumu gerektirir; ayri isaretlenir ve kapsamlari (471)
raporlanir -- kapsam disi kayit "yonlendirilmedi" sayilir.

EK SINYAL ARAYUZU
-----------------
--ek-sinyal <json>  {kayit_id: {sinyal_adi: sayi}}
Bu kosumda uretilmemis sinyaller (okuma-1'in k=2 oz-tutarliligi, ucuz model
logprob'u, ...) bir sonraki kosumdan buraya baglanir ve ayni kuralla puanlanir.

KULLANIM
--------
    python backend/scripts/kitap/neofizik_yonlendirici_harness.py
        [--cikti veriseti/zkitap/cikti] [--ham veriseti/zkitap/ham]
        [--ek-sinyal ek.json] [--rapor cikti/yonlendirici_rapor.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any

UYUM_ESIGI = 0.995  # YONTEM.md / uyum_olc.py ile ayni: "birebir ayni" esigi
# Alt simge 0-9 (U+2080..2089) ve ust simge 0-9 (U+2070, U+00B9, U+00B2, U+00B3,
# U+2074..2079). Kaynak dosya ASCII kalsin diye kacisla yazildi; dize aynidir.
ALT_UST = "".join(chr(0x2080 + i) for i in range(10)) + (
    "\u2070\u00b9\u00b2\u00b3" + "".join(chr(0x2074 + i) for i in range(6))
)
SAYISAL_SIK = re.compile(
    r"^[\s\d.,/+\-\u00d7x\u00b7^()]+(?:[a-zA-Z\u00b5\u00b0%/\u00b2\u00b3]{0,6}\s*)*$"
)
ONDALIK = re.compile(r"\d[.,]\d")
O_KARISMA = re.compile(r"(?:\d[oO]|[oO]\d)")


# ----------------------------------------------------------------------------
# veri yukleme
# ----------------------------------------------------------------------------


@dataclass
class Kayit:
    id: str
    sayfa: int
    sira: int
    metin: str
    secenekler: dict[str, str]
    bayraklar: list[str]
    kutu: list[float] | None
    ozellik: dict[str, float] = field(default_factory=dict)
    etiket: dict[str, bool] = field(default_factory=dict)


def _okuma1(ham: Path) -> dict[str, Kayit]:
    kayitlar: dict[str, Kayit] = {}
    for dosya in sorted((ham / "veri" / "okuma").glob("s*.json")):
        for x in json.loads(dosya.read_text(encoding="utf-8")):
            kayitlar[x["id"]] = Kayit(
                id=x["id"],
                sayfa=int(x["sayfa"]),
                sira=int(x["sira"]),
                metin=x.get("metin") or "",
                secenekler=dict(x.get("secenekler") or {}),
                bayraklar=list(x.get("bayraklar") or []),
                kutu=None,
            )
    return kayitlar


def _kutulari_ekle(ham: Path, kayitlar: dict[str, Kayit]) -> None:
    for x in json.loads(
        (ham / "veri" / "sorular_iskelet.json").read_text(encoding="utf-8")
    ):
        k = kayitlar.get(x["id"])
        if k is not None:
            k.kutu = x.get("kutu")


def _etiketle(ham: Path, kayitlar: dict[str, Kayit]) -> dict[str, int]:
    """Dort etiket kumesini ham ara ciktilardan kurar; boyutlarini dondurur."""
    hakem = {}
    for dosya in (ham / "hakem" / "kararlar").glob("*.json"):
        d = json.loads(dosya.read_text(encoding="utf-8"))
        hakem[d["id"]] = d["karar"]
    uyusmaz = {
        d["id"]
        for d in json.loads(
            (ham / "veri" / "cevap_uyusmazlik.json").read_text(encoding="utf-8")
        )
    }
    uyum = json.loads((ham / "veri" / "uyum.json").read_text(encoding="utf-8"))
    dusuk = {
        (int(u["sayfa"]), int(u["sira"]))
        for u in uyum
        if float(u["toplam"]) < UYUM_ESIGI
    }

    for k in kayitlar.values():
        k.etiket = {
            "hakem": k.id in hakem,
            "okuma1_yanlis": hakem.get(k.id) in ("okuma2", "duzeltme"),
            "dusuk_uyum": (k.sayfa, k.sira) in dusuk,
            "cozum_uyusmaz": k.id in uyusmaz,
        }
    return {
        ad: sum(1 for k in kayitlar.values() if k.etiket[ad])
        for ad in ("hakem", "okuma1_yanlis", "dusuk_uyum", "cozum_uyusmaz")
    }


# ----------------------------------------------------------------------------
# ozellikler -- YALNIZCA okuma-1 + geometri (+ istege bagli cozucu)
# ----------------------------------------------------------------------------


def ozellik_cikar(
    metin: str,
    secenekler: dict[str, str],
    bayraklar: Iterable[str],
    kutu: list[float] | None,
) -> dict[str, float]:
    tum = metin + "\n" + "\n".join(secenekler.values())
    n = max(1, len(tum))
    rakam = sum(ch.isdigit() for ch in tum)
    ozellik: dict[str, float] = {
        "metin_uzunlugu": float(len(tum)),
        "rakam_sayisi": float(rakam),
        "rakam_yogunlugu": rakam / n,
        "ondalik_sayisi": float(len(ONDALIK.findall(tum))),
        "alt_ust_simge_sayisi": float(sum(ch in ALT_UST for ch in tum)),
        "sayisal_sik_sayisi": float(
            sum(
                1
                for s in secenekler.values()
                if s.strip() and SAYISAL_SIK.match(s.strip())
            )
        ),
        "oO_karisma_sayisi": float(len(O_KARISMA.findall(tum))),
        "satir_sayisi": float(tum.count("\n") + 1),
    }
    for b in ("gorsel", "formul", "alt_ust_simge", "roma", "tablo_sik", "sik_bos"):
        ozellik[f"bayrak_{b}"] = 1.0 if b in bayraklar else 0.0
    if kutu and len(kutu) == 4:
        w, h = float(kutu[2] - kutu[0]), float(kutu[3] - kutu[1])
        ozellik["kutu_alani"] = w * h
        ozellik["kutu_yukseklik"] = h
        ozellik["kutu_karakter_basina_alan"] = (w * h) / n
    return ozellik


def _cozucu_sinyalleri(ham: Path, kayitlar: dict[str, Kayit]) -> int:
    """Cozum kosulmus kayitlara cozucu sinyallerini ekler; kapsam sayisini dondurur."""
    klasor = ham / "coz" / "cevaplar"
    kapsam = 0
    for dosya in klasor.glob("*.json"):
        d = json.loads(dosya.read_text(encoding="utf-8"))
        k = kayitlar.get(d["id"])
        if k is None:
            continue
        kapsam += 1
        k.ozellik["cozucu_metin_sorunu"] = 1.0 if d.get("metin_sorunu") else 0.0
        k.ozellik["cozucu_guven_orta"] = 1.0 if d.get("guven") == "orta" else 0.0
    return kapsam


def _ek_sinyal(yol: Path | None, kayitlar: dict[str, Kayit]) -> list[str]:
    if yol is None:
        return []
    ek = json.loads(yol.read_text(encoding="utf-8"))
    adlar: set[str] = set()
    for kid, sinyaller in ek.items():
        k = kayitlar.get(kid)
        if k is None:
            continue
        for ad, deger in sinyaller.items():
            k.ozellik[f"ek_{ad}"] = float(deger)
            adlar.add(f"ek_{ad}")
    return sorted(adlar)


# ----------------------------------------------------------------------------
# puanlama -- 18/18 kurali
# ----------------------------------------------------------------------------


@dataclass
class Sonuc:
    aday: str
    yon: str  # ">=" (buyuk riskli) ya da "<=" (kucuk riskli)
    esik: float
    yonlendirme_orani: float
    recall: dict[str, str]
    gecti: bool
    kapsam: int
    loo: tuple[int, int] | None = (
        None  # leave-one-out hakem recall (yalnizca gecenlerde)
    )


def _secim(kayitlar: list[Kayit], ad: str, yon: str, esik: float) -> set[str]:
    """Verilen esikte ikinci okumaya gidecek id kumesi. Ozelligi olmayan kayit gitmez."""
    secilen: set[str] = set()
    for k in kayitlar:
        v = k.ozellik.get(ad)
        if v is None:
            continue
        if (yon == ">=" and v >= esik) or (yon == "<=" and v <= esik):
            secilen.add(k.id)
    return secilen


def _recall(secilen: set[str], kayitlar: list[Kayit], etiket: str) -> tuple[int, int]:
    hedef = [k.id for k in kayitlar if k.etiket[etiket]]
    return sum(1 for i in hedef if i in secilen), len(hedef)


ETIKETLER = ("hakem", "okuma1_yanlis", "dusuk_uyum", "cozum_uyusmaz")


def _degerlendir(
    secilen: set[str], kayitlar: list[Kayit]
) -> tuple[dict[str, str], float, bool]:
    """Secilen kume icin recall sozlugu, yonlendirme orani ve 18/18 karari."""
    rec = {}
    gecti = True
    for et in ETIKETLER:
        b, t = _recall(secilen, kayitlar, et)
        rec[et] = f"{b}/{t}"
        if et == "hakem" and b < t:
            gecti = False
    oran = len(secilen) / max(1, len(kayitlar))
    if oran >= 1.0:
        gecti = False  # herkesi gondermek yonlendirme degil
    return rec, oran, gecti


def _sonuc(
    kayitlar: list[Kayit],
    ad: str,
    yon: str,
    esik: float,
    kapsam: int,
    etiket: str | None = None,
) -> Sonuc:
    rec, oran, gecti = _degerlendir(_secim(kayitlar, ad, yon, esik), kayitlar)
    return Sonuc(etiket or ad, yon, esik, oran, rec, gecti, kapsam)


def _ikili(v: float) -> bool:
    return v in (0.0, 1.0)


def _esik_tek(hakemli: list[float], yon: str) -> float:
    """18/18 kisitini saglayan en siki esik: '>=' icin min, '<=' icin max."""
    return min(hakemli) if yon == ">=" else max(hakemli)


def _payli(pop: list[float], esik: float, yon: str) -> float:
    """Esigi bir populasyon adimi gevsetir (guvenlik payi).

    Siki esik hakemli 18'in tam sinirinda durur; LOO'da sinirdaki vaka her
    zaman duser (17/18). Bir adim pay, 'bir sonraki hatali soru sinirin hemen
    altina duserse' durumunu kapsar. Pop sirali ve tekil olmali.
    """
    if yon == ">=":
        altta = [v for v in pop if v < esik]
        return max(altta) if altta else esik
    ustte = [v for v in pop if v > esik]
    return min(ustte) if ustte else esik


def _loo_tek(kayitlar: list[Kayit], ad: str, yon: str, pay: bool) -> tuple[int, int]:
    """Leave-one-out: her hakem vakasi cikarilip esik kalan 17'de kurulur.

    Esik ayni 18 uzerinde secildigi icin orneklem-ici 18/18 iyimserdir; LOO,
    'yeni bir hatali soru gelse yakalar miydik' sorusunun durust tahminidir.
    pay=True ise kalan 17'de kurulan esige de ayni pay uygulanir.
    """
    hakemli = [k for k in kayitlar if k.etiket["hakem"] and ad in k.ozellik]
    pop = sorted({k.ozellik[ad] for k in kayitlar if ad in k.ozellik})
    yakalanan = 0
    for h in hakemli:
        digerleri = [k.ozellik[ad] for k in hakemli if k.id != h.id]
        if not digerleri:
            continue
        esik = _esik_tek(digerleri, yon)
        if pay:
            esik = _payli(pop, esik, yon)
        v = h.ozellik[ad]
        if (yon == ">=" and v >= esik) or (yon == "<=" and v <= esik):
            yakalanan += 1
    return yakalanan, len(hakemli)


def tek_aday_puanla(kayitlar: list[Kayit], ad: str) -> list[Sonuc]:
    """Tek ozellik icin 18/18'i saglayan EN KUCUK yonlendirme oranini bulur.

    Sayisal ozellikte '>=' yonunde esik = hakemli 18'in en kucuk degeri, '<='
    yonunde en buyuk degeri; baska esik 18/18'i koruyamaz, daha gevsek esik
    gereksiz yonlendirir. Ikili (0/1) ozellikte anlamli tek soru 'bayrakli
    olanlari gonder' (>=1) oldugu icin yalnizca o satir uretilir. Ozelligi
    olmayan kayitlar (kismi kapsam) yonlendirilmez.
    """
    hakemli = [k.ozellik[ad] for k in kayitlar if k.etiket["hakem"] and ad in k.ozellik]
    kapsam = sum(1 for k in kayitlar if ad in k.ozellik)
    if not hakemli:
        return []
    if all(_ikili(k.ozellik[ad]) for k in kayitlar if ad in k.ozellik):
        s = _sonuc(kayitlar, ad, ">=", 1.0, kapsam)
        s.loo = _loo_tek(kayitlar, ad, ">=", pay=False) if s.gecti else None
        return [s]
    pop = sorted({k.ozellik[ad] for k in kayitlar if ad in k.ozellik})
    sonuclar = []
    for yon in (">=", "<="):
        siki = _esik_tek(hakemli, yon)
        s = _sonuc(kayitlar, ad, yon, siki, kapsam)
        s.loo = _loo_tek(kayitlar, ad, yon, pay=False) if s.gecti else None
        sonuclar.append(s)
        payli = _payli(pop, siki, yon)
        if payli != siki:
            sp = _sonuc(kayitlar, ad, yon, payli, kapsam, etiket=f"{ad} (payli)")
            sp.loo = _loo_tek(kayitlar, ad, yon, pay=True) if sp.gecti else None
            sonuclar.append(sp)
    return sonuclar


def _esik_ikili(
    hakemli: list[Kayit], kayitlar: list[Kayit], a: str, b: str, pay: bool
) -> tuple[float, float] | None:
    """A(>=ta) U B(>=tb) icin 18/18'i koruyan en kucuk birlesim oranini veren (ta, tb).

    ta hakemli A degerleri uzerinde taranir; A'nin kapsamadigi hakemliler B'ye
    kalir ve tb onlarin minimumu olur. B'ye is dusmeyen (kalan yok) durumlar
    tekli sonucu tekrarladigi icin elenir. pay=True ise iki esik de bir adim
    gevsetilir.
    """
    pop_a = sorted({k.ozellik[a] for k in kayitlar if a in k.ozellik})
    pop_b = sorted({k.ozellik[b] for k in kayitlar if b in k.ozellik})
    en_iyi: tuple[float, float] | None = None
    en_iyi_oran = 2.0
    for ta in sorted({k.ozellik[a] for k in hakemli if a in k.ozellik}, reverse=True):
        ta_kullan = _payli(pop_a, ta, ">=") if pay else ta
        sec_a = _secim(kayitlar, a, ">=", ta_kullan)
        kalan_hakem = [k for k in hakemli if k.id not in sec_a]
        if not kalan_hakem or any(b not in k.ozellik for k in kalan_hakem):
            continue
        tb = min(k.ozellik[b] for k in kalan_hakem)
        tb_kullan = _payli(pop_b, tb, ">=") if pay else tb
        oran = len(sec_a | _secim(kayitlar, b, ">=", tb_kullan)) / max(1, len(kayitlar))
        if oran < en_iyi_oran:
            en_iyi, en_iyi_oran = (ta_kullan, tb_kullan), oran
    return en_iyi


def _loo_ikili(
    hakemli: list[Kayit], kayitlar: list[Kayit], x: str, y: str, pay: bool
) -> tuple[int, int]:
    yakalanan = 0
    for h in hakemli:
        digerleri = [k for k in hakemli if k.id != h.id]
        fit = _esik_ikili(digerleri, kayitlar, x, y, pay)
        if fit is None:
            continue
        if (
            h.ozellik.get(x, float("-inf")) >= fit[0]
            or h.ozellik.get(y, float("-inf")) >= fit[1]
        ):
            yakalanan += 1
    return yakalanan, len(hakemli)


def ikili_birlesim_puanla(kayitlar: list[Kayit], adlar: list[str]) -> list[Sonuc]:
    """Ikili birlesimleri (siki ve payli) puanlar; gecenler icin LOO hesaplar."""
    hakemli = [k for k in kayitlar if k.etiket["hakem"]]
    sonuclar: list[Sonuc] = []
    for a, b in combinations(adlar, 2):
        for x, y in ((a, b), (b, a)):
            for pay in (False, True):
                fit = _esik_ikili(hakemli, kayitlar, x, y, pay)
                if fit is None:
                    continue
                ta, tb = fit
                secilen = _secim(kayitlar, x, ">=", ta) | _secim(kayitlar, y, ">=", tb)
                rec, oran, gecti = _degerlendir(secilen, kayitlar)
                ad = f"{x}>={ta:g} U {y}>={tb:g}" + (" (payli)" if pay else "")
                s = Sonuc(ad, "U", ta, oran, rec, gecti, len(kayitlar))
                if gecti:
                    s.loo = _loo_ikili(hakemli, kayitlar, x, y, pay)
                sonuclar.append(s)
    return sonuclar


# ----------------------------------------------------------------------------
# varlik kurallari -- esik uydurmadan, "ozellik hic var mi" (>=1) birlesimleri
# ----------------------------------------------------------------------------


def varlik_kurali_puanla(
    kayitlar: list[Kayit], adlar: list[str], en_fazla: int = 3
) -> list[Sonuc]:
    """Yalnizca >=1 (varlik) esigiyle 1..en_fazla ozellikli birlesimleri puanlar.

    Neden ayri bir arama: sayisal esik uydurmak 18'e asiri uyar (LOO 17/18).
    Varlik kurali ise mekanizmaya baglidir -- 'metinde ondalik sayi var mi',
    'okuyucu tablo-sik bayragi koydu mu' -- ve esigi 18'den ogrenmez.

    DURUSTLUK NOTU: esik ogrenilmese de HANGI ozelliklerin birlestirilecegi
    18 goruldukten sonra secildi; bu da bir tur test-kumesi secimidir. Bu
    yuzden LOO yazilmaz ('-'), ve asil sinama bir sonraki kitaptir.
    """
    sonuclar: list[Sonuc] = []
    for n in range(1, en_fazla + 1):
        for kume in combinations(adlar, n):
            secilen: set[str] = set()
            for ad in kume:
                secilen |= _secim(kayitlar, ad, ">=", 1.0)
            rec, oran, gecti = _degerlendir(secilen, kayitlar)
            sonuclar.append(
                Sonuc(
                    " U ".join(f"{ad}>=1" for ad in kume),
                    "VARLIK",
                    1.0,
                    oran,
                    rec,
                    gecti,
                    len(kayitlar),
                )
            )
    return sonuclar


# ----------------------------------------------------------------------------
# rapor
# ----------------------------------------------------------------------------


def _tablo(sonuclar: list[Sonuc], baslik: str) -> None:
    print(f"\n### {baslik}")
    print(
        "| aday | yon | esik | yonlendirme | hakem | LOO | okuma1_yanlis | dusuk_uyum | cozum_uyusmaz | kapsam | karar |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for s in sonuclar:
        loo = f"{s.loo[0]}/{s.loo[1]}" if s.loo else "-"
        print(
            f"| {s.aday} | {s.yon} | {s.esik:g} | %{100 * s.yonlendirme_orani:.1f} | "
            f"{s.recall['hakem']} | {loo} | {s.recall['okuma1_yanlis']} | {s.recall['dusuk_uyum']} | "
            f"{s.recall['cozum_uyusmaz']} | {s.kapsam} | {'GECTI' if s.gecti else 'kaldi'} |"
        )


def yukle(
    ham: Path, ek_sinyal: Path | None
) -> tuple[list[Kayit], dict[str, int], int, list[str]]:
    """Ham ara ciktilardan etiketli, ozellikli kayit listesini kurar."""
    kayitlar = _okuma1(ham)
    _kutulari_ekle(ham, kayitlar)
    boyut = _etiketle(ham, kayitlar)
    for k in kayitlar.values():
        k.ozellik = ozellik_cikar(k.metin, k.secenekler, k.bayraklar, k.kutu)
    cozucu_kapsam = _cozucu_sinyalleri(ham, kayitlar)
    ek_adlar = _ek_sinyal(ek_sinyal, kayitlar)
    liste = sorted(kayitlar.values(), key=lambda k: (k.sayfa, k.sira))
    return liste, boyut, cozucu_kapsam, ek_adlar


@dataclass
class Puanlama:
    gecen: list[Sonuc]
    kalan: list[Sonuc]
    ikili: list[Sonuc]
    varlik: list[Sonuc]

    @property
    def en_iyi_ici(self) -> Sonuc | None:
        ogrenilmis = self.gecen + self.ikili
        return (
            min(ogrenilmis, key=lambda s: s.yonlendirme_orani) if ogrenilmis else None
        )

    @property
    def en_iyi_loo(self) -> Sonuc | None:
        tam = [s for s in self.gecen + self.ikili if s.loo and s.loo[0] == s.loo[1]]
        return min(tam, key=lambda s: s.yonlendirme_orani) if tam else None

    @property
    def en_iyi_varlik(self) -> Sonuc | None:
        return self.varlik[0] if self.varlik else None


def _hakem_sayisi(s: Sonuc) -> int:
    return int(s.recall["hakem"].split("/")[0])


def puanla(liste: list[Kayit]) -> Puanlama:
    """Uc aday sinifini puanlar: tekli (esik ogrenilmis), ikili birlesim, varlik kurali."""
    tum_adlar = sorted({ad for k in liste for ad in k.ozellik})
    tekli: list[Sonuc] = []
    for ad in tum_adlar:
        tekli.extend(tek_aday_puanla(liste, ad))
    gecen = sorted((s for s in tekli if s.gecti), key=lambda s: s.yonlendirme_orani)
    kalan = sorted((s for s in tekli if not s.gecti), key=lambda s: -_hakem_sayisi(s))

    # birlesim adaylari: gecen tekliler + 18'in en az yarisini yakalayan kalanlar.
    # cozucu_* kismi kapsamli (471) -- birlesimde eksik kapsam sizdirmasin diye disarida.
    aday_adlar = sorted(
        {s.aday for s in gecen} | {s.aday for s in kalan if _hakem_sayisi(s) >= 9}
    )
    aday_adlar = [
        a for a in aday_adlar if not a.startswith("cozucu_") and "(payli)" not in a
    ]
    ikili = sorted(
        (s for s in ikili_birlesim_puanla(liste, aday_adlar) if s.gecti),
        key=lambda s: s.yonlendirme_orani,
    )

    # varlik kurallari: sayac/bayrak ozellikleri, >=1 esigiyle, en fazla 3'lu birlesim.
    varlik_adaylari = [
        a
        for a in tum_adlar
        if (a.startswith("bayrak_") or a.endswith("_sayisi"))
        and not a.startswith("cozucu_")
    ]
    varlik = sorted(
        (s for s in varlik_kurali_puanla(liste, varlik_adaylari, 3) if s.gecti),
        key=lambda s: s.yonlendirme_orani,
    )
    return Puanlama(gecen, kalan, ikili, varlik)


def _sonuc_yaz(pu: Puanlama) -> None:
    # Karar uc katmanli:
    #  1) esik ogrenilmis adaylarda orneklem-ici 18/18 YETMEZ, LOO da tam olmali;
    #  2) varlik kurallari LOO'suz raporlanir -- esik ogrenilmedi ama ozellik secimi
    #     18 goruldukten sonra yapildi; asil sinama bir sonraki kitap;
    #  3) hicbiri yoksa secici okuma guvenli degil, N=2 herkese kalir.
    print("\n### SONUC")
    ici, loo, var = pu.en_iyi_ici, pu.en_iyi_loo, pu.en_iyi_varlik
    if ici:
        loo_m = f"{ici.loo[0]}/{ici.loo[1]}" if ici.loo else "-"
        print(
            f"esik ogrenilmis, orneklem-ici en kucuk 18/18 : {ici.aday} -> %{100 * ici.yonlendirme_orani:.1f} (LOO {loo_m})"
        )
    if loo:
        print(
            f"esik ogrenilmis, LOO'da da tam, en kucuk       : {loo.aday} -> %{100 * loo.yonlendirme_orani:.1f}"
        )
    else:
        print("esik ogrenilmis adaylarda LOO'da tam kalan YOK")
    if var:
        print(
            f"varlik kurali (esik yok), en kucuk 18/18       : {var.aday} -> %{100 * var.yonlendirme_orani:.1f}"
            f" (okuma1_yanlis {var.recall['okuma1_yanlis']}) <- ADAY; sinama: sonraki kitap"
        )
    if not loo and not var:
        print("secici okuma henuz kalite-guvenli degil; N=2 herkese kalsin")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--cikti", default="veriseti/zkitap/cikti")
    p.add_argument("--ham", default="veriseti/zkitap/ham")
    p.add_argument("--ek-sinyal", default=None)
    p.add_argument(
        "--rapor",
        default=None,
        help="JSON rapor yolu (varsayilan: <cikti>/yonlendirici_rapor.json)",
    )
    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    liste, boyut, cozucu_kapsam, ek_adlar = yukle(
        Path(args.ham), Path(args.ek_sinyal) if args.ek_sinyal else None
    )
    print(
        f"kayit: {len(liste)} (okuma-1) | etiketler: {boyut} | cozucu kapsami: {cozucu_kapsam}"
    )
    print(
        "kural: hakem 18/18 saglayan EN KUCUK yonlendirme orani; %100 = yonlendirme degil"
    )

    pu = puanla(liste)
    _tablo(
        pu.gecen, "TEK OZELLIK -- 18/18 saglayanlar (en az yonlendirenden baslayarak)"
    )
    _tablo(pu.kalan, "TEK OZELLIK -- saglayamayanlar (metadata bayraklari burada)")
    _tablo(
        pu.ikili[:10], "IKILI BIRLESIM (esik ogrenilmis) -- 18/18 saglayanlar (ilk 10)"
    )
    _tablo(
        pu.varlik[:10], "VARLIK KURALI (esik yok, >=1) -- 18/18 saglayanlar (ilk 10)"
    )
    if ek_adlar:
        print(f"\nek sinyaller puanlandi: {ek_adlar}")
    _sonuc_yaz(pu)

    rapor_yolu = (
        Path(args.rapor) if args.rapor else Path(args.cikti) / "yonlendirici_rapor.json"
    )
    rapor: dict[str, Any] = {
        "kayit": len(liste),
        "etiket_boyutlari": boyut,
        "cozucu_kapsami": cozucu_kapsam,
        "uyum_esigi": UYUM_ESIGI,
        "tekli": [s.__dict__ for s in pu.gecen + pu.kalan],
        "ikili": [s.__dict__ for s in pu.ikili],
        "varlik": [s.__dict__ for s in pu.varlik],
        "en_iyi_loo": pu.en_iyi_loo.__dict__ if pu.en_iyi_loo else None,
        "en_iyi_varlik": pu.en_iyi_varlik.__dict__ if pu.en_iyi_varlik else None,
        "etiketli_set": {
            k.id: {"etiket": k.etiket, "ozellik": k.ozellik} for k in liste
        },
    }
    rapor_yolu.parent.mkdir(parents=True, exist_ok=True)
    rapor_yolu.write_text(
        json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"rapor: {rapor_yolu}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
