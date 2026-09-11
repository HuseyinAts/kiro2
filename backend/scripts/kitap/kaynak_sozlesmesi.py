#!/usr/bin/env python
"""Kitap ithal sozlesmesi: `source_book` adlandirmasi + yabanci satir korumasi.

NEDEN BU MODUL VAR
------------------
`question_metadata.source_book` bu depoda bir etiket degil, bir KIMLIKTIR:

- toplu onay / aktiflestirme migration'lari hedef satirlari bu kolona gore
  secer (0011, 0012, 0014, 0016, 0018 -- hepsi `WHERE source_book = :kaynak`),
- ithal scriptlerinin "bu satir baska bir kitaba ait, DOKUNMA" korumasi da
  bu kolona bakar.

Kolon serbest metin oldugu icin bugune kadar her ithal araci kendi adini elle
yazdi. 11 Eyl 2026 olcumu (canli DB):

    192 farkli source_book degeri
      5 tanesi `pipeline_metadata.ithal_araci` tasiyor (modern ithaller)
        -> 3611 satir, hepsi ASCII, istisnasiz
    187 tanesi eski hattan kalma (5796 satir; 137'si Turkce karakterli)
      1 KITAP IKI FARKLI YAZIMLA BOLUNMUS -- fark tek harfte:
        "Aromat Tyt T<u>rkce Model Sorular"  8 satir, 'c'  = U+0063
        "Aromat Tyt T<u>rkce Model Sorular"  1 satir, 'c'  = U+00E7 (cedilla)
        Diskteki klasor adi U+0063'lu yazim; tek satirlik olan dizgi hatasi.

Bolunmus ad, `source_book` ile filtreleyen HER korumayi sessizce delik
birakir: koruma "benim kitabim" derken bir satiri disarida sayar. 0019
migration'i bu ciftligi birlestirir; bu modul de yeni ciftlerin olusmasini
onler.

AYRICA: 11 Eyl 2026'da olculdu ki PR #254'te mikro_geo_ithal.py'ye eklenen
yabanci-satir korumasi neofizik_ithal.py ve neofizik_tyt_ithal.py'ye
TASINMAMISTI -- ikisi de hala "SELECT id FROM question_bank WHERE id = ANY(...)"
ile yetiniyor ve --meta-guncelle ile baska bir kitabin satirini ezebiliyordu.
(Ayni acik 11 Eyl 2026'da 2 resmi OSYM satirinin metadata'sini ezmisti.)
Koruma artik kopyalanacak bir kalip degil, cagrilan tek fonksiyon: `ayristir`.

ADLANDIRMA SOZLESMESI (yeni ithaller icin)
------------------------------------------
1. Yalnizca yazdirilabilir ASCII. Gerekce: bu ad SQL parametresi, dosya adi,
   log satiri ve rapor basligi olarak dolasir; Turkce karakter her durakta bir
   kodlama riski ekler. Modern ithallerin 5'i de zaten boyle.
   DIKKAT: bu kural SORU METNINI KAPSAMAZ -- metin Turkce kalir.
2. Bas/son bosluk yok, ardisik cift bosluk yok.
3. Normalize anahtari (Turkce katlama + kucuk harf + alfanumerik disi atma)
   var olan hicbir kaynakla CAKISMAMALI. Cakisirsa ayni kitabin ikinci
   yazimini uretiyorsunuz demektir.
4. Ad bu modulun KAYNAK_KAYITLARI sozlugune eklenir; ithal script'i adi
   oradan okur, elle bir daha yazmaz.

tests/e2e/test_kaynak_sozlesmesi.py bu maddelerin dordunu de hem kod hem DB
uzerinde dogrular.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

# Turkce -> ASCII katlama. Yalnizca NORMALIZE ANAHTARI icin kullanilir;
# gercek metni duzlestirmek icin DEGIL (bkz. mikro_geo_ithal.py EKLER notu).
# Harfler kod noktasi olarak yazilir -- kaynak dosya ASCII kalir.
_KATLAMA = {
    chr(0x00E7): "c",  # c cedilla
    chr(0x00C7): "c",
    chr(0x011F): "g",  # g breve
    chr(0x011E): "g",
    chr(0x0131): "i",  # noktasiz i
    chr(0x0130): "i",  # noktali I
    chr(0x00F6): "o",
    chr(0x00D6): "o",
    chr(0x015F): "s",  # s cedilla
    chr(0x015E): "s",
    chr(0x00FC): "u",
    chr(0x00DC): "u",
}

_YAZDIRILABILIR_ASCII = re.compile(r"^[\x20-\x7e]+$")


class KaynakAdiError(ValueError):
    """source_book adi ev sozlesmesine uymuyor.

    Ad Ingilizce `Error` sonekiyle biter (ruff N818); govde Turkce.
    """


# Modern ithal araclarinin yazdigi kanonik adlar. Kaynak: canli DB'de
# `pipeline_metadata ? 'ithal_araci'` olan satirlarin source_book degerleri
# (11 Eyl 2026). Yeni kitap eklerken buraya da bir satir eklenir.
KAYNAK_KAYITLARI: dict[str, dict[str, str]] = {
    "Neofizik AYT Fizik Soru Bankasi 2025": {
        "onek": "NEOFIZIK_2025",
        "ithal_araci": "scripts/kitap/neofizik_ithal.py",
    },
    "Neofizik TYT Fizik Soru Bankasi": {
        "onek": "NEOFIZIK_TYT",
        "ithal_araci": "scripts/kitap/neofizik_tyt_ithal.py",
    },
    "Mikro Orijinal 2025 AYT Geometri Soru Bankasi": {
        "onek": "MIKRO_GEO",
        "ithal_araci": "scripts/kitap/mikro_geo_ithal.py",
    },
    "OSYM 2025 TYT": {
        "onek": "OSYM_2025_TYT",
        "ithal_araci": "scripts/osym/kitapcik_ithal.py",
    },
    "OSYM 2025 AYT": {
        "onek": "OSYM_2025_AYT",
        "ithal_araci": "scripts/osym/kitapcik_ithal.py",
    },
}


def katla(ad: str) -> str:
    """Turkce harfleri ASCII karsiliklarina indirger (yalniz karsilastirma icin)."""
    return "".join(_KATLAMA.get(ch, ch) for ch in ad)


def normalize_anahtar(ad: str) -> str:
    """Iki yazimin ayni kitap olup olmadigini soyleyen karsilastirma anahtari.

    Aromat ciftinin iki yazimi (U+0063 ve U+00E7) ayni anahtari verir --
    ikisinin de DB'de durmasi bir defalik hatadir, 0019 birlestirir.
    """
    return re.sub(r"[^a-z0-9]", "", katla(ad).lower())


def kaynak_adi_dogrula(ad: str, *, kayitli_olmali: bool = False) -> None:
    """Ad sozlesmeye uymuyorsa KaynakAdiError firlatir.

    kayitli_olmali=True ise ad ayrica KAYNAK_KAYITLARI'nda bulunmalidir.
    """
    if not isinstance(ad, str) or not ad:
        raise KaynakAdiError("source_book bos olamaz")
    if ad != ad.strip():
        raise KaynakAdiError(f"bas/son bosluk var: {ad!r}")
    if "  " in ad:
        raise KaynakAdiError(f"ardisik cift bosluk var: {ad!r}")
    if not _YAZDIRILABILIR_ASCII.match(ad):
        disarda = sorted({ch for ch in ad if not _YAZDIRILABILIR_ASCII.match(ch)})
        raise KaynakAdiError(
            "yalnizca yazdirilabilir ASCII olmali; sozlesme disi karakter(ler): "
            f"{disarda!r} -- ad: {ad!r}"
        )
    if kayitli_olmali and ad not in KAYNAK_KAYITLARI:
        raise KaynakAdiError(
            f"{ad!r} KAYNAK_KAYITLARI'nda yok -- yeni kitap once oraya eklenir"
        )


def cakisan_kaynak(ad: str, mevcut_adlar: Sequence[str]) -> str | None:
    """`ad` mevcut bir kaynagin baska bir yazimi ise o kaynagi dondurur."""
    anahtar = normalize_anahtar(ad)
    for var in mevcut_adlar:
        if var != ad and normalize_anahtar(var) == anahtar:
            return var
    return None


def ayristir(
    conn: Any,
    kayitlar: Sequence[dict[str, Any]],
    kaynak_adi: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[tuple[str, str | None]]]:
    """Ithal kayitlarini (yeni, bizim, yabanci) diye ayirir.

    NEDEN: `soru_hash` metin + 5 sik uzerinden hesaplandigi ve
    `id = uuid5(NAMESPACE_OID, soru_hash)` oldugu icin AYNI SORU baska bir
    kitapta da varsa ID AYNIDIR. Var olan satirlari kaynak kitaba gore
    ayirmadan --meta-guncelle calistirmak, baska bir kitabin satirini ezer.

    Donen degerler:
        yeni    -- DB'de hic olmayan kayitlar (INSERT edilecekler)
        bizim   -- DB'de var VE source_book bu kitap (guncellenebilir)
        yabanci -- [(id, oteki_source_book)] -- ASLA DOKUNULMAZ
    """
    kaynak_adi_dogrula(kaynak_adi)
    idler = [k["id"] for k in kayitlar]
    if not idler:
        return [], [], []

    var_kaynak: dict[str, str | None] = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT b.id, m.source_book FROM question_bank b "
            "  LEFT JOIN question_metadata m ON m.id = b.id "
            " WHERE b.id = ANY(%s)",
            (idler,),
        ).fetchall()
    }
    var = set(var_kaynak)
    yabanci_idler = {i for i, kitap in var_kaynak.items() if kitap != kaynak_adi}

    yeni = [k for k in kayitlar if k["id"] not in var]
    bizim = [k for k in kayitlar if k["id"] in var and k["id"] not in yabanci_idler]
    yabanci = [(i, var_kaynak[i]) for i in sorted(yabanci_idler)]
    return yeni, bizim, yabanci


def yabanci_yaz(yabanci: Sequence[tuple[str, str | None]]) -> None:
    """Yabanci satirlari stdout'a dokumler (ithal scriptlerinin ortak ciktisi)."""
    if not yabanci:
        return
    print(
        f"BASKA KAYNAKTA duran {len(yabanci)} soru (ayni soru_hash) "
        "-- dokunulmayacak:"
    )
    for soru_id, kitap in yabanci:
        print(f"    {soru_id}  <- {kitap}")
