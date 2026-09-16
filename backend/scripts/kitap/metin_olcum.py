#!/usr/bin/env python
"""Ithal araclarinin ortak metin olcumleri: hash, morfoloji, okunabilirlik, Bloom.

NEDEN BU MODUL VAR
------------------
neofizik / neofizik_tyt / mikro_geo / biyo345 / geo345 / biyo345tyt ithal
araclarinin HER BIRI ayni EKLER listesini, ayni `soru_hash` formulunu ve ayni
morfoloji/okunabilirlik heuristigini KENDI icine kopyalamis durumda (6 kopya).
Formul degisirse alti dosyanin altisini da degistirmek gerekiyor; birini
atlamak sessiz bir ayrisma uretir.

BU MODUL YENI ITHALLER ICIN TEK KAYNAKTIR. Var olan 6 script'i bu modulu
kullanacak sekilde tasimak MEKANIK ve AYRI bir istir (her biri kendi
regresyon testine sahip); bu PR'da yapilmadi -- borc burada kayitli.
Formuller kopyalardan BIREBIR alindi, tek satir davranis degisikligi yok.

KAYNAK ESLESMESI
----------------
soru_hash                -> scripts/pipeline/pilot_500p.py::_hash_question
morfoloji_karmasikligi   -> core/turkish_nlp_service._simple_root_suffix_split
                            (Zemberek YOKKEN dusulen heuristik yol)
okunabilirlik            -> services/turkish_readability_service (Atesman)
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from services.turkish_readability_service import TurkishReadabilityService

# core/turkish_nlp_service._simple_root_suffix_split ile BIREBIR ayni liste.
# Turkce harfler \u kacisiyla yazilir (kaynak dosya ASCII kalsin diye);
# ASCII'ye duzlestirmek YANLIS olur -- gercek metinde "nin" gecer.
EKLER: tuple[str, ...] = (
    "lar",
    "ler",
    "dan",
    "den",
    "tan",
    "ten",
    "n\u0131n",
    "nin",
    "nun",
    "n\u00fcn",
    "nda",
    "nde",
    "n\u0131",
    "ni",
    "nu",
    "n\u00fc",
    "ya",
    "ye",
    "yla",
    "yle",
    "d\u0131r",
    "dir",
    "dur",
    "d\u00fcr",
    "t\u0131r",
    "tir",
    "tur",
    "t\u00fcr",
)
W_EK, W_TURETIM, W_BIRLESIK = 0.15, 0.20, 0.25

# DIKKAT -- KATASTROFIK GERI IZLEME ONARIMI (PR #266/#269 ile ayni desen).
# Desen ic ice NICELEMEZ; eslesmeyen girdilerde ustel geri izleme uretmez.
SAYISAL_SIK = re.compile(
    "^[\\s\\d.,/+\\-x*^()\u2212\u221a\u00b7]+[a-zA-Z\u00b0%/\u00b2\u00b3\\s]{0,12}$"
)
NICELIK = re.compile(
    "ka\u00e7|b\u00fcy\u00fckl\u00fc\u011f\u00fc\\s+ne|de\u011feri\\s+ne|ka\u00e7t\u0131r",
    re.IGNORECASE,
)


def nfc(t: str) -> str:
    """NFC normalize + bas/son bosluk atma."""
    return unicodedata.normalize("NFC", t or "").strip()


def soru_hash(metin: str, secenekler: dict[str, str]) -> str:
    """scripts/pipeline/pilot_500p.py::_hash_question ile birebir.

    DIKKAT: metin KUCUK HARFE indirilir, sikler INDIRILMEZ. Biyoloji
    genetik sorularinda sik harfi anlam tasir (alel gosterimi: 'A' baskin,
    'a' cekinik); kucultmek yanlis pozitif uretir.
    """
    payload = "|".join(
        [nfc(metin).lower()] + [nfc(secenekler.get(h, "")) for h in "ABCDE"]
    )
    return hashlib.md5(payload.encode("utf-8"), usedforsecurity=False).hexdigest()


def kelime_istatistik(metin: str) -> tuple[int, int, float]:
    """(kelime sayisi, benzersiz kelime sayisi, ortalama kelime uzunlugu)."""
    kelimeler = metin.split()
    if not kelimeler:
        return 0, 0, 0.0
    return (
        len(kelimeler),
        len(set(kelimeler)),
        sum(len(k) for k in kelimeler) / len(kelimeler),
    )


def ek_ayikla(kelime: str) -> list[str]:
    """core/turkish_nlp_service._simple_root_suffix_split'in ek toplama adimi.

    DIKKAT: kaynak dongu ilk eslesmede BREAK eder -- kelime basina EN FAZLA
    BIR ek ayiklanir. Bu davranis birebir korunur.
    """
    kalan = kelime.lower()
    for ek in sorted(EKLER, key=len, reverse=True):
        if kalan.endswith(ek) and len(kalan) > len(ek):
            return [ek]
    return []


def morfoloji_karmasikligi(metin: str) -> float:
    """Zemberek YOKKEN repo'nun dustugu heuristik yolun aynisi."""
    turkce = "\u00e7\u011f\u0131\u00f6\u015f\u00fc\u00c7\u011e\u0130\u00d6\u015e\u00dc"
    kelimeler = [
        "".join(c for c in k if c.isalnum() or c in turkce) for k in metin.split()
    ]
    kelimeler = [k for k in kelimeler if len(k) >= 2]
    if not kelimeler:
        return 0.3  # servisin bos-metin varsayilani
    en = 0.0
    for k in kelimeler:
        n = len(ek_ayikla(k))
        en = max(en, min(1.0, n * W_EK + min(3, n) * W_TURETIM))
    return round(en, 4)


def okunabilirlik(metin: str, secenekler: dict[str, str]) -> float:
    """Atesman indeksi (repo'nun kendi servisi), 0-100'e kirpilir."""
    tam = metin + "\n" + "\n".join(secenekler.values())
    ol = TurkishReadabilityService.analyze_text(tam)
    return round(max(0.0, min(100.0, float(ol["atesman_index"]))), 2)


def bloom_belirle(metin: str, secenekler: dict[str, str]) -> tuple[int, str, str]:
    """Dar kural: sayisal sonuc istenen + besi de sayisal sik -> uygulama."""
    sayisal = sum(
        1 for s in secenekler.values() if s.strip() and SAYISAL_SIK.match(s.strip())
    )
    if sayisal == 5 and NICELIK.search(metin):
        return 3, "application", "kural:sayisal_sonuc"
    return 2, "comprehension", "varsayilan:ev_sozlesmesi"


def sik_bayraklari(secenekler: dict[str, str]) -> list[str]:
    """Her kitapta gecerli olan iki sik bayragi.

    DIKKAT: `sik_tekrar` kiyasi HARF BUYUKLUGUNE DUYARLI (bkz. soru_hash
    notu). geo345/biyo345'te .lower() ile yapiliyordu ve biyolojide yanlis
    pozitif uretiyordu.
    """
    b: list[str] = []
    if any(not (secenekler.get(h) or "").strip() for h in "ABCDE"):
        b.append("sik_bos")
    if len({(secenekler.get(h) or "").strip() for h in "ABCDE"}) < 5:
        b.append("sik_tekrar")
    return b


__all__ = [
    "EKLER",
    "NICELIK",
    "SAYISAL_SIK",
    "W_BIRLESIK",
    "W_EK",
    "W_TURETIM",
    "bloom_belirle",
    "ek_ayikla",
    "kelime_istatistik",
    "morfoloji_karmasikligi",
    "nfc",
    "okunabilirlik",
    "sik_bayraklari",
    "soru_hash",
]
