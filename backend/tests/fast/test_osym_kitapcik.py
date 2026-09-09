"""OSYM kitapcik cikarici/ithalci bekcileri (9 Eyl 2026, rapor madde 10 / karar 2).

Saf parcalar DB'siz ve PDF'siz olculur; gercek kitapcik (data/osym/tyt_2025.pdf,
gitignore'da: telif) varsa uctan uca sayim da olculur (CI'da atlanir).

Sozlesme
--------
1. Sik parcalayici: tek satirda "A) I B) II ..." bes sikka ayrilir; sik yoksa bos.
2. Satir kumeleme: ayni `top`taki kelimeler tek satir, x'e gore sirali.
3. Roma etiketi: tek basina "I" satiri, ustundeki ortusen kelimeye etiket olur
   ve satir tuketilir; cikti `$\\underline{\\text{kelime}}^{\\text{I}}$`.
4. TYT alt ders: SOS 1-5 TARIH ... 21-25 FELSEFE; FEN 1-7 FIZIK ... 15-20 BIYOLOJI.
5. soru_hash, scripts/pipeline/pilot_500p.py::_hash_question ile birebir
   (uq_qb_soru_hash_active ayni formulu bekler).
6. Ithal SQL'i is_active=FALSE, is_public=FALSE, review_status='pending' yazar.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.osym import kitapcik_cikar as kc
from scripts.osym import kitapcik_ithal as ki


def _k(metin: str, x0: float, top: float = 10.0, **ek) -> kc.Kelime:
    return kc.Kelime(metin, x0, x0 + 5 * len(metin), top, top + 8, **ek)


def test_sik_parcala_tek_satirda_bes_sik() -> None:
    assert kc._sik_parcala("A) I B) II C) III D) IV E) V") == [
        ("A", "I"),
        ("B", "II"),
        ("C", "III"),
        ("D", "IV"),
        ("E", "V"),
    ]
    assert kc._sik_parcala("A) 9 B) 16 C) 24 D) 30 E) 36")[4] == ("E", "36")
    assert kc._sik_parcala("Bu parcada altı çizili sözle") == []
    assert kc._sik_parcala("A) B) C) D) E)") == [(h, "") for h in "ABCDE"]


def test_satirlar_top_ile_kumelenir_ve_x_ile_siralanir() -> None:
    kelimeler = [_k("ikinci", 40, 10), _k("birinci", 10, 11), _k("alt", 10, 30)]
    satirlar = kc._satirlar(kelimeler)
    assert [[w.metin for w in s] for s in satirlar] == [["birinci", "ikinci"], ["alt"]]


def test_roma_etiketi_ustteki_kelimeye_yapisir() -> None:
    ust = [_k("toplumsal", 10, 10), _k("bir", 60, 10), _k("özellik", 80, 10)]
    roma = [_k("I", 84, 20)]
    satirlar = [ust, roma]
    kc._roma_etiketle(satirlar)
    assert satirlar[1] == []  # tuketildi
    assert ust[2].etiket == "I" and ust[0].etiket is None
    assert kc._satir_metni(ust).endswith("$\\underline{\\text{özellik}}^{\\text{I}}$")


def test_soru_no_tek_basina_da_baslangic() -> None:
    assert kc._SORU_NO.match("2.") is not None
    assert kc._SORU_NO.match("12. Bir tabletin") is not None
    assert kc._SORU_NO.match("A) 12. cümle") is None


def test_talimat_ve_baslik_satirlari_atlanir() -> None:
    for satir in (
        "1. Bu testte 40 soru vardır.",
        "2. Cevaplarınızı, cevap kâğıdının Türkçe Testi için ayrılan kısmına işaretleyiniz.",
        "22 Diğer sayfaya geçiniz.",
        "TÜRKÇE TESTİ",
        "E TESTİ",
        "14",
    ):
        assert kc._ATLA.match(satir), satir
    assert kc._BASLIK.match("2025-TYT/TEM TEMEL MATEMATİK TESTİ").group(2) == "TEM"
    assert kc.TEST_TAKMA_AD["TEM"] == "MAT"


@pytest.mark.parametrize(
    ("test", "no", "ders"),
    [
        ("SOS", 1, "TARIH"),
        ("SOS", 10, "COGRAFYA"),
        ("SOS", 15, "FELSEFE"),
        ("SOS", 18, "DIN"),
        ("SOS", 23, "FELSEFE"),
        ("FEN", 7, "FIZIK"),
        ("FEN", 8, "KIMYA"),
        ("FEN", 20, "BIYOLOJI"),
        ("TÜR", 40, "TURKCE"),
        ("MAT", 1, "MATEMATIK"),
    ],
)
def test_tyt_alt_ders(test: str, no: int, ders: str) -> None:
    assert kc.ders_alani("TYT", test, no) == ders


@pytest.mark.parametrize(
    ("test", "no", "ders"),
    [
        ("TDE-SB1", 24, "EDEBIYAT"),
        ("TDE-SB1", 25, "TARIH"),
        ("TDE-SB1", 40, "COGRAFYA"),
        ("SB2", 11, "TARIH"),
        ("SB2", 22, "COGRAFYA"),
        ("SB2", 34, "FELSEFE"),
        ("SB2", 40, "DIN"),
        ("SB2", 46, "FELSEFE"),
        ("FEN", 14, "FIZIK"),
        ("FEN", 27, "KIMYA"),
        ("FEN", 28, "BIYOLOJI"),
        ("MAT", 40, "MATEMATIK"),
    ],
)
def test_ayt_alt_ders(test: str, no: int, ders: str) -> None:
    assert kc.ders_alani("AYT", test, no) == ders
    assert kc.AYT_BEKLENEN == {"TDE-SB1": 40, "SB2": 46, "MAT": 40, "FEN": 40}
    assert kc._BASLIK.match("2025-AYT/TDE-SB1 TÜRK DİLİ").group(2) == "TDE-SB1"


def test_govdedeki_c_parantezi_sik_sayilmaz() -> None:
    """'( 1H, 6C)' govde parcasi ilk sik olamaz: siklar A'dan baslar, artan gider (AYT FEN-25)."""
    assert kc._sik_baslangici(None, "C") is False
    assert kc._sik_baslangici(None, "A") is True
    assert kc._sik_baslangici("B", "C") is True
    assert (
        kc._sik_baslangici("C", "B") is False
    )  # sik icindeki 'B)' metni yeni sik degil


def test_soru_hash_pilot_formulu_ile_birebir() -> None:
    from scripts.pipeline.pilot_500p import _hash_question

    q = {
        "question_text": " Soru  metni ",
        "options": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
    }
    assert ki.soru_hash(q) == _hash_question(" Soru  metni ", "a", "b", "c", "d", "e")


def test_ithal_sql_pasif_yazar() -> None:
    assert re.search(
        r"VALUES \(%\(id\)s, %\(soru_hash\)s, %\(kok_id\)s, FALSE, FALSE", ki._QB
    )
    assert "'pending'" in ki._QB and "'pending'" in ki._QS


_PDF = Path(__file__).resolve().parents[2] / "data" / "osym" / "tyt_2025.pdf"


@pytest.mark.skipif(
    not _PDF.exists(), reason="gercek kitapcik yerel (telif, gitignore)"
)
def test_gercek_tyt_2025_uctan_uca_sayim() -> None:
    """125 soru (40/25/40/20), 125 anahtar, hepsi 5 sikli -- yerel olcum."""
    sonuc = kc.cikar(_PDF)
    oz = kc.ozet(sonuc)
    assert oz["test_basina"] == kc.TYT_BEKLENEN, oz
    assert oz["anahtari_olan"] == oz["toplam_soru"] == 125
    assert oz["bes_sikli"] == 125


_AYT = _PDF.with_name("ayt_2025.pdf")


@pytest.mark.skipif(
    not _AYT.exists(), reason="gercek kitapcik yerel (telif, gitignore)"
)
def test_gercek_ayt_2025_uctan_uca_sayim() -> None:
    """166 soru (40/46/40/40), 166 anahtar, hepsi 5 sikli -- yerel olcum."""
    sonuc = kc.cikar(_AYT)
    oz = kc.ozet(sonuc)
    assert oz["test_basina"] == kc.AYT_BEKLENEN, oz
    assert oz["anahtari_olan"] == oz["toplam_soru"] == 166
    assert oz["bes_sikli"] == 166
