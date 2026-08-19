#!/usr/bin/env python
"""Y11 göç dedup'ı — soru kimliği ve mükerrer gruplama (saf, DB'siz).

NEDEN `soru_hash` KULLANILMIYOR
-------------------------------
Ölçüldü (S233): canlı `soru_hash`'lerin **%100'ü UUID4** — sürüm nibble'ı `4`
ve varyant nibble'ı `8/9/a/b` olan satır sayısı 36.967/36.967. Yani içerik
hash'i değil, rastgele kimlik. İki DB arasında **ortak hash 0**, ama **ortak
normalize metin 17.213**. Dolayısıyla:

  - hash çapraz-DB kimlik TAŞIMAZ,
  - `uq_qb_soru_hash_active` kısmi UNIQUE indeksi hiçbir mükerreri DURDURAMAZ,
  - "script iki kez koşarsa DB korur" iddiası YANLIŞTIR.

Dedup metin üzerinden yapılmak ZORUNDA.

NEDEN GÖVDE TEK BAŞINA YETMEZ
-----------------------------
S232-C'de "669 mükerrer + 118 kendi-kendiyle çelişen çift" raporlandı ve bu,
"bedava anahtar-hatası dedektörü" diye sunuldu. Normalizasyon yalnız
`question_text`'e bakıyordu. Şıklar dahil edilince:

    yalniz govde        -> 669 fazlalik
    govde + SIKLAR      -> 153 fazlalik      (516 mesru soru = %77 KURTARILDI)
    anahtar celiskisi   -> 0                 (118 iddiasi TAMAMEN FANTOM)

Kanıt çifti (aynı üçgen sorusu, iki satır):

    A) 24  B) 30  C) 36 ...   anahtar = B
    A) 30  B) 40  C) 50 ...   anahtar = A

İkisi de **30**'u işaret ediyor; harfler farklı çünkü **şık sırası** farklı.
`correct_answer` bir DEĞER değil, şık listesine **konumsal referanstır** —
o iki alan birbirinden ayrılamaz (`L-s232-cevap-harfi-sik-listesi-olmadan-anlamsizdir`).

SIKI vs GEVŞEK
--------------
`siki_kimlik`   = gövde + şıklar **sırasıyla**  -> silme kararı BUNA dayanır
`gevsek_kimlik` = gövde + şıklar **sıralanmış** -> YALNIZ raporlama

Gevşek olan şıkları karıştırılmış meşru varyantları da birleştirir. Bu depoda
içerik silmenin bedeli mükerrer bırakmanın bedelinden ağırdır (5 Ağu 2026:
187.835 → 2.304), o yüzden varsayılan sıkı olandır.

Bekçi: `backend/tests/fast/test_y11_dedup.py`
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

_SIK_ALANLARI = ("option_a", "option_b", "option_c", "option_d", "option_e")

# Var olmayan sikkin YER TUTUCUSU. Bos dize kullanilsaydi 4 sikli bir soru ile
# 5 sikli bir soru ayni kimligi alabilirdi.
_YOK = "\x00"

_BOSLUK = re.compile(r"\s+")


def normalize_metin(s: str | None) -> str:
    """Karşılaştırma için normalize et — İÇ NOKTALAMAYA DOKUNMADAN.

    1. NFC (birleşik/ayrık `İ` aynı olsun)
    2. Türkçe küçültme: `İ`→`i`, `I`→`ı`  (standart `.lower()` bunu TERS yapar)
    3. `.lower()`
    4. boşluk dizisi tek boşluğa

    ⚠️ Noktalama ve işaretler KORUNUR. A3 ölçümünde "noktalama sil" yaklaşımı
    `+`/`-` işaretlerini siliyor ve `(x-2)²+(y+1)²=16` ile `(x+2)²+(y-1)²=16`'yı
    AYNI sayıyordu — 41 yanlış-pozitifin 27'si bu alet arızasıydı.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("İ", "i").replace("I", "ı")
    return _BOSLUK.sub(" ", s.lower()).strip()


def _siklar(satir: dict) -> list[str]:
    return [normalize_metin(satir.get(a)) or _YOK for a in _SIK_ALANLARI]


def _hash(parcalar: list[str]) -> str:
    ham = "\x1f".join(parcalar)
    return hashlib.sha256(ham.encode("utf-8")).hexdigest()


def siki_kimlik(satir: dict) -> str | None:
    """Gövde + şıklar SIRASIYLA. Silme kararı yalnız buna dayanır.

    `correct_answer` kimliğe GİRMEZ: aynı soru farklı harfle etiketlenmiş
    olabilir ve bu onu farklı soru yapmaz. Anahtar çelişkisi AYRI bir ölçümdür.

    Gövde boş/None ise `None` döner — boş gövdeli satırlar birbirine benzer
    görünür ve toptan silinirdi. Onlar dedup'ın değil İÇERİK YARGISININ işi.
    """
    govde = normalize_metin(satir.get("question_text"))
    if not govde:
        return None
    return _hash([govde, *_siklar(satir)])


def gevsek_kimlik(satir: dict) -> str | None:
    """Şıklar SIRALANMIŞ — yalnız RAPORLAMA. Silme kararı vermez.

    Şıkları karıştırılmış meşru varyantları da birleştirir; bu yüzden
    "kaç yakın-kopya var" sorusunu yanıtlar, "hangisi silinsin"i değil.
    """
    govde = normalize_metin(satir.get("question_text"))
    if not govde:
        return None
    return _hash([govde, *sorted(_siklar(satir))])


def mukerrer_gruplar(satirlar: list[dict], *, kimlik=siki_kimlik) -> list[list[str]]:
    """Mükerrer id gruplarını döndür (tek satırlık gruplar ATLANIR).

    Grup içi sıra ve grupların sırası deterministik — aynı girdi aynı çıktıyı
    verir, yoksa "hangisi korunacak" kararı koşuma göre değişirdi.
    """
    kova: dict[str, list[str]] = {}
    for satir in satirlar:
        k = kimlik(satir)
        if k is None:
            continue
        kova.setdefault(k, []).append(str(satir["id"]))
    return sorted(
        (sorted(idler) for idler in kova.values() if len(idler) > 1),
        key=lambda g: g[0],
    )
