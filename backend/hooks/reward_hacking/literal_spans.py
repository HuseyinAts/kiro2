"""Bulgu bastirma politikasi: string literalleri ve yorumlar KOD DEGILDIR.

30 Tem 2026 — bekcinin 4. kusuru. Dedektorler ham metin uzerinde regex
kosuyordu; string literal, yorum ve gercek kod ayirt edilmiyordu. Sonuc: bekci
KENDI fixture korpusunu ihlal saydi ve o dosyalara dokunan her commit push'ta
bloklandi. Olculdu (kontrollu A/B, gercek yolda):

    test_detectors.py            -> exit 2   (12 critical, paket toplami)
    test_hook_manager.py         -> exit 2
    test_properties.py           -> exit 2
    test_severity_from_confidence.py -> exit 0

UC TASARIM KARARI, HEPSI OLCUMLE
================================

1) `tokenize`, `ast` DEGIL
   `ast` dugumlerinde `col_offset` UTF-8 BAYT cinsindendir. Bu depo Turkce
   karakterlerle dolu; bayt != karakter oldugu icin span kayar. Olculdu:

       satir: '    assert True, "ğüşiöç mesajı"'   -> 32 karakter / 38 bayt
       ast:     col=17  end_col=38    <- end_col SATIR UZUNLUGUNU ASIYOR
       tokenize: span=(108, 123)      -> content[108:123] == '"ğüşiöç mesajı"'

   tokenize karakter tabanlidir ve AST'nin aksine parse edilebilir bir program
   gerektirmez (yalnizca sozcuksel gecerlilik).

2) KARAKTER granulerligi, SATIR degil
   `assert True, "aciklama"` GERCEK ihlaldir ve satirinda string de vardir.
   Satiri komple bastiran filtre bu ihlali maskeler.

3) YORUM bastirma DESEN BAZLI
   Yorumu kosulsuz bastirmak `# pragma: no cover` / `# noqa` / `# TODO`
   kurallarini komple kor eder — o kurallarin KONUSU yorumdur. Desen
   gruplarinin fiili dagilimi olculdu:

       assert_true           8 desen, 1'i '#' iceriyor  (\bassert\\s+True\\s*#)
       placeholder          10 desen, 7'si '#' iceriyor
       coverage_manipulation 8 desen, 6'si '#' iceriyor
       echo_success/mock_abuse/empty_exception/hardcoded: 0

   Kural: bir desen '#' iceriyorsa YORUM KONULUDUR, yorumda eslesmesi mesrudur.
   Icermiyorsa yorumdaki eslesme calistirilamaz metindir -> bastirilir.
   Bu kural kendi kendini idame ettirir: yeni bir yorum kurali eklendiginde
   deseninde zaten '#' bulunur.

4) YALNIZCA .py
   tokenize bir PYTHON cozumleyicisidir. .sh/.yml/.js icerigi uzerinde
   verdigi sonuc anlamsizdir, bu yuzden filtre Python disi dosyalarda hic
   uygulanmaz (bastirma yok = bekci acik).

Sozlesme: tests/hooks/reward_hacking/test_string_literal_immunity.py
"""

from __future__ import annotations

import io
import tokenize
from functools import lru_cache

# 3.12+ f-string'leri FSTRING_START/MIDDLE/END olarak tokenize eder. Yalnizca
# MIDDLE (duz metin) literaldir; `{...}` icindeki ifadeler GERCEK KODDUR.
_LITERAL_TIPLERI = {tokenize.STRING}
if hasattr(tokenize, "FSTRING_MIDDLE"):
    _LITERAL_TIPLERI.add(tokenize.FSTRING_MIDDLE)


def _satir_baslangiclari(content: str) -> list[int]:
    """Her satirin (1-tabanli) mutlak karakter offseti."""
    offsetler = [0]
    for satir in content.split("\n"):
        offsetler.append(offsetler[-1] + len(satir) + 1)
    return offsetler


@lru_cache(maxsize=16)
def _araliklar(
    content: str,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    """(literal_araliklari, yorum_araliklari) — karakter offsetleri.

    Ayni icerik 8 dedektor x N desen tarafindan sorgulanir; onbellekli.

    FAIL-OPEN: sozcuksel hata varsa IKISI DE BOS doner, yani bastirma
    yapilmaz. Kapatilmamis bir ucgen tirnak dosyanin geri kalanini "literal"
    gosterip bekciyi tamamen atlatmaya yarardi; belirsizlikte bekci
    kordur DEGIL aciktir.
    """
    baslangic = _satir_baslangiclari(content)
    literaller: list[tuple[int, int]] = []
    yorumlar: list[tuple[int, int]] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(content).readline):
            bas = baslangic[tok.start[0] - 1] + tok.start[1]
            son = baslangic[tok.end[0] - 1] + tok.end[1]
            if tok.type in _LITERAL_TIPLERI:
                literaller.append((bas, son))
            elif tok.type == tokenize.COMMENT:
                yorumlar.append((bas, son))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return ((), ())
    return (tuple(literaller), tuple(yorumlar))


def _icinde(araliklar: tuple[tuple[int, int], ...], offset: int) -> bool:
    return any(bas <= offset < son for bas, son in araliklar)


def bulgu_bastirilmali(
    file_path: str, content: str, offset: int, desen: str = ""
) -> bool:
    """`offset`'teki eslesme calistirilamaz metin icinde mi (atilmali mi)?

    Args:
        file_path: analiz edilen dosya (filtre yalnizca .py'de calisir)
        content: dosya icerigi
        offset: eslesmenin mutlak karakter offseti
        desen: eslesen regex. '#' iceriyorsa desen YORUM KONULUDUR ve
               yorum icindeki eslesmesi bastirilmaz.
    """
    if not file_path.endswith(".py"):
        return False

    literaller, yorumlar = _araliklar(content)
    if _icinde(literaller, offset):
        return True
    if "#" in desen:
        return False
    return _icinde(yorumlar, offset)


def satir_bastirilmali(
    file_path: str, content: str, satir_no: int, desen: str = ""
) -> bool:
    """Satir-bazli tarayicilar icin: 1-tabanli satirin ILK KOD KARAKTERI."""
    satirlar = content.split("\n")
    if not 1 <= satir_no <= len(satirlar):
        return False
    satir = satirlar[satir_no - 1]
    girinti = len(satir) - len(satir.lstrip())
    offset = _satir_baslangiclari(content)[satir_no - 1] + girinti
    return bulgu_bastirilmali(file_path, content, offset, desen)
