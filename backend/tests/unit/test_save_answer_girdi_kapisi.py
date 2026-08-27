"""`SaveAnswerRequest` girdi kapisi sozlesmesi (S255 -- Katman A).

NEDEN VAR
---------
27 Agu 2026 canli olcumu (`backend/scripts/batch_zehirlenme_probu.py`):
`selected_answer` zincirin HICBIR katmaninda dogrulanmiyordu --
`SaveAnswerRequest` (`str | None`, desen yok) -> `SaveAnswerCommand`
(kisit yok) -> `save_answer` (yalniz `question_id` bos mu diye bakiyor).
Sonuc, uc de HTTP 200 donerken:

    selected_answer="F"   -> asyncpg CheckViolationError
                             (check_selected_answer: NULL veya 'A'..'E')
    selected_answer="AB"  -> asyncpg StringDataRightTruncationError
                             (selected_answer varchar(1))

Bu iki hata TOPLU yazim isleminde patliyor, `commit()`e hic ulasilmiyor ve
AYNI batch'teki 1000'e kadar cevap birlikte geri aliniyor. Kuyruk modul
duzeyinde tek nesnede (`core/osym_exam_engine.py:2180`), yani dusen cevaplar
BASKA OGRENCILERIN cevaplari olabiliyor.

SOZLESME
--------
1. `A`..`E` kabul (bosluk toleransli, kucuk harf toleransli -> BUYUK'e normalize).
2. Bos dizge ve `None` KABUL -- "cevabi temizle" semantigi (frontend'in mesru
   `clearAnswer`'i; S254'te `else None` ile civilendi). Reddedilirse ogrenci
   cevabini SILEMEZ.
3. Bunlarin disindaki her sey **422** -- sessizce NULL'a cevirmek veri kaybinin
   baska bir bicimi olurdu (kullanici karari, 27 Agu 2026).

Kardes sozlesmeler: `test_golden_flow_login_gate.py`,
`test_golden_flow_exam_setup_gate.py`.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.sinav import SaveAnswerRequest

pytestmark = [pytest.mark.unit]

SORU = "550e8400-e29b-41d4-a716-446655440000"


def _kur(**alanlar: object) -> SaveAnswerRequest:
    govde: dict[str, object] = {"question_id": SORU}
    govde.update(alanlar)
    return SaveAnswerRequest(**govde)  # type: ignore[arg-type]


@pytest.mark.parametrize("harf", ["A", "B", "C", "D", "E"])
def test_kontrol_kolu_gecerli_harfler_kabul_edilir(harf: str) -> None:
    """KONTROL KOLU: mutlu yol reddedilirse asagidaki testler anlamsiz."""
    assert _kur(selected_answer=harf).selected_answer == harf


def test_kucuk_harf_buyuge_normalize_edilir() -> None:
    """Motor zaten `.upper()` yapiyordu; kapi ayni sozlesmeyi bozmamali."""
    assert _kur(selected_answer="c").selected_answer == "C"


def test_bosluklu_harf_kabul_edilir() -> None:
    """`" A "` eskiden calisiyordu (motor `.strip()` ediyor) -- gerileme olmasin."""
    assert _kur(selected_answer=" a ").selected_answer == "A"


def test_bos_dizge_kabul_edilir() -> None:
    """`clearAnswer` MESRU: reddedilirse ogrenci cevabini geri alamaz.

    MUTASYON: dogrulayiciya `""` reddi eklenirse bu test DUSER.
    """
    assert _kur(selected_answer="").selected_answer == ""


def test_yalniz_bosluk_bos_dizgeye_normalize_edilir() -> None:
    """DORDUNCU TETIKLEYICI -- S254'un duzeltmesi bunu KACIRIYORDU.

    `core/osym_exam_engine.py`:

        normalized_answer = selected_answer.strip().upper() if selected_answer else None

    `"  "` **truthy**tir -> `else None` daline HIC girmez -> `.strip()` sonucu
    `""` batch'e girer ve `check_selected_answer` onu reddeder. Yani S254 bos
    dizgeyi kapatti ama BOSLUKLU bicimini acik birakti.

    Dogru davranis: bosluk-only = "cevabi temizle" (`" A "` -> `"A"` ile ayni
    strip semantigi). Kapida `""`e normalize edilir, motor `None`a cevirir.
    """
    assert _kur(selected_answer="  ").selected_answer == ""


def test_none_kabul_edilir() -> None:
    assert _kur(selected_answer=None).selected_answer is None


def test_alan_hic_gonderilmezse_kabul_edilir() -> None:
    """Alan opsiyonel; varsayilan `None` (cevabi temizle)."""
    assert _kur().selected_answer is None


@pytest.mark.parametrize(
    "deger",
    [
        "F",  # A-E disi harf   -> CheckViolationError
        "Z",
        "AB",  # 1 karakterden uzun -> StringDataRightTruncationError
        "A,B",
        "1",  # rakam
        "*",
    ],
)
def test_gecersiz_deger_reddedilir(deger: str) -> None:
    """Her biri CANLI olculmus bir batch zehirlenme tetikleyicisi.

    MUTASYON: dogrulayici kaldirilirsa bu testlerin hepsi DUSER.
    """
    with pytest.raises(ValidationError):
        _kur(selected_answer=deger)
