#!/usr/bin/env python
"""Tekrarlayan kayitli derslerin SAF dedektorleri.

NEDEN AYRI MODUL: iki hook da kullaniyor (`post-edit-format.py`,
`pre-commit-check.py`) ve hook'larin kendisi stdin/subprocess'e bagli oldugu
icin pahali test ediliyor. Buradaki fonksiyonlar IO'suz -> pytest ile ve
mutasyonla civilenebilir.

DOKTRIN (`.claude/rules/verification.md`): "1. kez fix, 2. kez enforcement,
3. kez ASLA olmasin". Buradaki uc ders 20 Agu 2026 oturumunda 4 kez tekrar
etti; N802 sekizinci kez. Ders defterine YAZMAK yetmedi cunku sinyal ihlal
anindan cok sonra geliyordu.

Bekci: backend/tests/unit/test_hooks/test_ders_dedektorleri.py
"""

from __future__ import annotations

import re

# Ters tirnak bu kaynakta CIPLAK yazilmaz — dosyanin kendisi tuzaga girmesin.
TERS_TIRNAK = chr(96)

# `git commit` + (-m / -am / -ma). `-F` KASITLI olarak disarida: cozum odur.
#
# ⚠️ SEGMENT BASI SART (S240'ta ILK GERCEK KULLANIMDA isirdi): ilk surum
# `\bgit\s+commit\b` diyordu ve dizeyi NEREDE gecerse gecsin esliyordu. Kendi
# defter-guncelleme komutumu blokladi: heredoc icinde ders METNI olarak
# "git commit -m" ve ters tirnak geciyordu. Dedektor VERIYI KOMUT sandi.
# Mevcut `is_git_commit_or_add` zaten dogrusunu yapiyor (`startswith`).
# Artik yalniz komut segmentinin BASINDAKI git commit sayilir:
# dize basi, `&&`, `||`, `;`, `|` veya satir sonu.
_COMMIT_M = re.compile(
    r"(?:^|&&|\|\||;|\||\n)\s*git\s+commit\b[^\n;|&]*?(?<!\w)-(?:m|am|ma)\b"
)


def ters_tirnak_riski(komut: str) -> str | None:
    """`git commit -m` mesajinda ters tirnak varsa uyari dizesi dondurur.

    OLCULDU (`d03674d9d`, 20 Agu 2026): bash cift tirnak icindeki ters tirnagi
    KOMUT olarak calistirdi; defter kimligi mesaj govdesinden silindi, commit
    EXIT=0 verdi, push gecti. Sessiz kayip — hicbir kapi otmedi.

    YALNIZ `git commit -m`e bakar. Genel bir ters-tirnak polisi OLMAK ISTEMEZ:
    oyle olsaydi her kabuk komutunda oterdi ve UYARI KORLUGU yaratirdi.
    Susturulan kontrol, olu kontroldur.
    """
    if TERS_TIRNAK not in komut or not _COMMIT_M.search(komut):
        return None
    return (
        "TERS TIRNAK: git commit -m mesajinda ters tirnak var. Bash onu KOMUT "
        "olarak calistirir ve mesajdan sessizce siler (olculdu: d03674d9d). "
        "COZUM: mesaji dosyaya yaz, 'git commit -F <dosya>' ile ver."
    )


# Host kabugundan gecen /tmp. `docker exec` / `docker run` icindekiler
# KONTEYNER yolu — ayri ad alani sorunu yok, onlar disarida.
_TMP = re.compile(r"(?<![\w/])/tmp/")
_KONTEYNER = re.compile(r"\bdocker\s+(?:exec|run)\b")


def tmp_ad_alani_riski(komut: str) -> str | None:
    """Host komutunda `/tmp/` gecerse uyarir.

    Git Bash `/tmp` = `%LOCALAPPDATA%\\Temp`; Python `/tmp` = `C:\\tmp`. Bir
    adimda yazip digerinde okumak "dosya yok" verir. 20 Agu oturumunda gate
    listesi bu yuzden bos kaldi ve pytest TUM depoyu toplamaya kalkip 2 dk'da
    zaman asimina ugradi.
    """
    if not _TMP.search(komut) or _KONTEYNER.search(komut):
        return None
    return (
        "/tmp AD-ALANI: bash /tmp = AppData\\Local\\Temp, Python /tmp = C:\\tmp "
        "- AYRI iki yer. Bir adimda yazip digerinde okursan 'dosya yok' alirsin. "
        "COZUM: ara dosyayi DEPO ICINDE tut."
    )


# ruff metinsel cikti satiri: yol:satir:sutun: KOD mesaj
# "Found N errors." ve "[*] N fixable..." ozet satirlari BILEREK eslenmiyor.
_BULGU = re.compile(r"^\S+:\d+:\d+:\s+[A-Z]+\d+\s")


def duzeltilemeyen_bulgular(ruff_ciktisi: str) -> list[str]:
    """`ruff check` (--fix'siz) ciktisindan bulgu satirlarini ayiklar.

    ASIL KUSUR BURADA: `post-edit-format.py` `ruff check --fix --quiet`
    kosuyordu. N802 auto-fixable DEGIL (fonksiyon yeniden adlandirma guvenli
    otomatik duzeltme sayilmaz), `--quiet` de raporu yutuyordu. Yani ruff
    ihlali HER yazimda goruyor ve SUSUYORDU; sinyal ancak commit aninda,
    kapinin FARKLI ruff surumuyle geliyordu. Sekiz tekrarin sebebi bu.

    TAM SATIR dondurulur — yalniz on ek donerse mesaj kural KODUNU tasimaz ve
    okuyana hicbir sey soylemez.
    """
    return [
        satir.strip() for satir in ruff_ciktisi.splitlines() if _BULGU.match(satir)
    ]
