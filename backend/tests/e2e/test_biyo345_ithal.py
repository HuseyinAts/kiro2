"""345 2025 AYT Biyoloji Soru Bankasi ithal hatti -- koruma testleri.

Bu dosya UC sinif seyi dogrular:

1. SOZLESME: kaynak adi ASCII ve KAYNAK_KAYITLARI'nda kayitli; konu
   kodlari 0021'in kurdugu BIO-U<n> desenine uyuyor.
2. HESAP: soru_hash formulu pilot_500p ile birebir; id = uuid5(hash).
3. KILITLENME KORUMASI: SAYISAL_SIK deseni geri izlemeye girmiyor.
   Bu testin MUTASYON KARSILIGI var -- eski (ic ice nicelenmis) desen
   ayni girdide sureyi patlatir; test bunu ayrica olcer ve eski desenin
   GERCEKTEN yavas oldugunu dogrular. Yani test, olmayan bir hatayi
   kollamiyor.
"""

from __future__ import annotations

import hashlib
import re
import sys
import time
import unicodedata
import uuid
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import biyo345_ithal as biyo  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    kaynak_adi_dogrula,
)

# Eski (bozuk) desen -- YALNIZCA mutasyon olcumu icin burada duruyor.
_ESKI_SAYISAL = re.compile("^[\\s\\d.,/+\\-x*^()−√·]+(?:[a-zA-Z°%/²³]{0,6}\\s*)*$")
# Kitaptan gelen gercek sik; ithali kilitleyen girdi buydu.
_PATLATAN = "2, karbondioksit olabilir."


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(biyo.KAYNAK_ADI, kayitli_olmali=True)
    assert KAYNAK_KAYITLARI[biyo.KAYNAK_ADI]["onek"] == "BIYO345"
    assert (
        KAYNAK_KAYITLARI[biyo.KAYNAK_ADI]["ithal_araci"]
        == "scripts/kitap/biyo345_ithal.py"
    )


def test_kaynak_dosyalari_ascii() -> None:
    """Ev kurali: ithal/kirp kaynaklari ASCII kalir (Turkce \\u kacisiyla)."""
    for ad in ("biyo345_ithal.py", "biyo345_kirp.py"):
        ham = (KOK / "scripts" / "kitap" / ad).read_bytes()
        disi = sorted({b for b in ham if b > 126})
        assert not disi, f"{ad} ASCII disi bayt tasiyor: {disi[:8]}"


def test_soru_hash_pilot_formuluyle_ayni() -> None:
    metin = "İnsanda spermatogenez ne zaman başlar?"
    sec = {"A": "Doğumda", "B": "Ergenlikte", "C": "1", "D": "2", "E": "3"}
    beklenen = hashlib.md5(  # nosec B324
        "|".join(
            [unicodedata.normalize("NFC", metin).strip().lower()]
            + [unicodedata.normalize("NFC", sec[h]).strip() for h in "ABCDE"]
        ).encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()
    assert biyo.soru_hash(metin, sec) == beklenen


def test_id_hashten_tureiyor() -> None:
    h = biyo.soru_hash("a", {h: h for h in "ABCDE"})
    assert str(uuid.uuid5(uuid.NAMESPACE_OID, h)) == str(
        uuid.uuid5(uuid.NAMESPACE_OID, h)
    )


def test_sikkin_turkce_karakteri_duzlestirilmiyor() -> None:
    """Hash girdi metnini ASCII'ye indirmez -- 'n\\u0131n' ile 'nin' ayri."""
    a = biyo.soru_hash("kanın yolu", dict.fromkeys("ABCDE", "x"))
    b = biyo.soru_hash("kanin yolu", dict.fromkeys("ABCDE", "x"))
    assert a != b


@pytest.mark.parametrize(
    "sik",
    ["12", "3,5 cm", "45°", "2√3", "1/2", "100 m²"],
)
def test_sayisal_sik_kabul(sik: str) -> None:
    assert biyo.SAYISAL_SIK.match(sik)


@pytest.mark.parametrize(
    "sik",
    [
        _PATLATAN,
        "Yalnız I",
        "I ve II",
        "Küçük polipeptiler",
        "1. damar oksijence zengin kan taşır.",
    ],
)
def test_sayisal_sik_reddediyor(sik: str) -> None:
    assert not biyo.SAYISAL_SIK.match(sik)


def test_sayisal_sik_geri_izlemeye_girmiyor() -> None:
    """Gercek kitap sikkinda desen ANINDA sonuclanmali."""
    t = time.perf_counter()
    biyo.SAYISAL_SIK.match(_PATLATAN)
    sure = time.perf_counter() - t
    assert sure < 0.05, f"desen {sure:.3f}s surdu -- geri izleme geri geldi"


def test_mutasyon_eski_desen_gercekten_patliyor() -> None:
    """Koruma bos degil: eski desen AYNI girdide kat kat yavas.

    Olcut mutlak sure degil ORAN -- makineden bagimsiz olsun diye.
    (Olculen: yeni ~4 us, eski ~294 ms; gercek oran ~65000, esik 50.)
    """
    t = time.perf_counter()
    biyo.SAYISAL_SIK.match(_PATLATAN)
    yeni_sure = max(time.perf_counter() - t, 1e-7)

    # DIKKAT: dizginin SONUNDAKI NOKTA sart. Nokta ilk karakter sinifina
    # ait oldugu icin motoru harfleri yeniden bolmeye zorluyor; noktasiz
    # 25 karakterlik hali 0.001 ms'de bitiyor, noktali 26 karakterlik hali
    # 294 ms suruyor (olculdu). Kisaltilmis girdiyle yazilan ilk surum bu
    # yuzden bos bir test olmustu.
    t = time.perf_counter()
    _ESKI_SAYISAL.match(_PATLATAN)
    eski_sure = time.perf_counter() - t

    assert eski_sure > yeni_sure * 50, (
        "eski desen bu girdide yavaslamadi -- mutasyon testi bir sey "
        f"kollamiyor olabilir (eski {eski_sure:.6f}s, yeni {yeni_sure:.6f}s)"
    )


def test_bloom_dar_kural() -> None:
    sayisal = {h: str(i) for i, h in enumerate("ABCDE", 1)}
    metin_sayi = "Bu değerin büyüklüğü ne kadardır?"
    seviye, ad, kaynak = biyo.bloom_belirle(metin_sayi, sayisal)
    assert (seviye, ad) == (3, "application")
    assert kaynak.startswith("kural")

    metinsel = dict.fromkeys("ABCDE", "Yalnız I")
    seviye, ad, kaynak = biyo.bloom_belirle(metin_sayi, metinsel)
    assert (seviye, ad) == (2, "comprehension")
    assert kaynak.startswith("varsayilan")


def test_konu_kodu_0021_desenine_uyuyor() -> None:
    r = {
        "bolum_no": 7,
        "bolum_adi": "Solunum Sistemi",
        "question_text": "soru",
        "a": "1",
        "b": "2",
        "c": "3",
        "d": "4",
        "e": "5",
        "correct_answer": "A",
        "id": "x",
        "sayfa": "0150",
        "sutun": "sol",
        "soru_no": 1,
        "kutu": [92, 200, 740, 900],
    }
    k = biyo.kayit_uret(r)
    assert k["konu_kodu"] == "BIO-U7"
    assert k["konu_kodu"].startswith(biyo.KOD_ONEKI)
    assert k["question_image_url"] == "/static/crops/BIYO345/x.png"
    assert k["source_page"] == 150
    assert k["pipeline_metadata"]["konu_eslesme_duzeyi"] == "unite"
    assert k["pipeline_metadata"]["gorsel_kaynagi"] == "tam_soru_kirpimi"
    assert k["pipeline_metadata"]["kirpim_kutusu"] == r["kutu"]


def test_bayrak_sik_bos_ve_tekrar() -> None:
    temel = {
        "bolum_no": 1,
        "bolum_adi": "Sinir Sistemi",
        "question_text": "soru",
        "correct_answer": "A",
        "id": "x",
        "sayfa": "0010",
        "sutun": "sol",
        "soru_no": 1,
        "kutu": [0, 0, 1, 1],
    }
    bos = {**temel, "a": "1", "b": "", "c": "3", "d": "4", "e": "5"}
    assert "sik_bos" in biyo.kayit_uret(bos)["pipeline_metadata"]["bayraklar"]
    tekrar = {**temel, "a": "1", "b": "1", "c": "3", "d": "4", "e": "5"}
    assert "sik_tekrar" in biyo.kayit_uret(tekrar)["pipeline_metadata"]["bayraklar"]
    temiz = {**temel, "a": "1", "b": "2", "c": "3", "d": "4", "e": "5"}
    assert biyo.kayit_uret(temiz)["pipeline_metadata"]["bayraklar"] == []


def test_osym_damgasi_yalniz_rozetli_soruda() -> None:
    temel = {
        "bolum_no": 1,
        "bolum_adi": "Sinir Sistemi",
        "question_text": "soru",
        "a": "1",
        "b": "2",
        "c": "3",
        "d": "4",
        "e": "5",
        "correct_answer": "A",
        "id": "x",
        "sayfa": "0010",
        "sutun": "sol",
        "soru_no": 1,
        "kutu": [0, 0, 1, 1],
    }
    yayinevi = biyo.kayit_uret(temel)
    assert yayinevi["osym_year"] is None
    assert yayinevi["osym_format_compliant"] is False

    cikmis = biyo.kayit_uret({**temel, "osym_yil": 2019, "osym_sinav": "AYT"})
    assert cikmis["osym_year"] == 2019
    assert cikmis["osym_format_compliant"] is True
    assert cikmis["pipeline_metadata"]["sinav_kaynagi"] == "AYT"


def test_on_kontrol_bos_anahtar_sikkini_yakaliyor() -> None:
    k = {
        "id": "x",
        "soru_hash": "h",
        "question_text": "soru",
        "correct_answer": "B",
        "secenekler": {"A": "1", "B": "  ", "C": "3", "D": "4", "E": "5"},
    }
    hata = biyo._on_kontrol([k])
    assert any("sikki bos" in h for h in hata)
