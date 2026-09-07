"""Aday secicinin KIMYA'ya degil verilen SQL dilimine bagli oldugunu civiler.

DB'siz: secicinin saf parcalari (dilim SQL metni, konu-dengeli secim, haric
kumesi) burada olculur. Canliya karsi dogrulama ayri adim (PROVA).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "quality"))

from y11_aday_uret import (
    AYT_KONU_KODLARI,
    DILIMLER,
    KONU_BASI_TAVAN,
    ayt_konu_idleri,
    haric_kumesi,
    kapsam_suz,
    kirmizi_liste_oku,
    konu_dengeli_sec,
)


def test_dilim_sql_parametre_olarak_gelir() -> None:
    """Ders/kitap adi modulde SABIT olmamali; KIMYA yolu ayri durmali.

    KIMYA'yi buraya `None` degeriyle koymak tip kirliligi olurdu
    (`dict[str, str]` icinde `None`); onun adaylari verdikt TSV'sinden geliyor
    ve `y11_goc_kumesi_uret.py`'de duruyor. Gerileme korumasi o dosyanin
    VARLIGINI olcer.
    """
    assert set(DILIMLER) == {
        "mat_tyt",
        "tur_tyt",
    }, "beklenmeyen dilim -- sessiz genisletme"
    assert all(isinstance(v, str) for v in DILIMLER.values()), "deger str olmali"
    kimya = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "quality"
        / "y11_goc_kumesi_uret.py"
    )
    assert kimya.exists(), "KIMYA yolu silinmis -- gerileme"


def test_mat_dilimi_page_croplarini_disliyor() -> None:
    """_PAGE crop'lari basili cevap anahtari sizdiriyor (B4'te olculdu).

    Bu suzgec sizintinin BUYUK kismini kesiyor; kalan %2,54 onun artigi ve
    T3'te crop-basi kor okumayla eleniyor.
    """
    sql = DILIMLER["mat_tyt"]
    assert "_q[0-9]+" in sql, "soru-bazli crop suzgeci YOK -- _PAGE sizar"
    assert "auto_judged_high" in sql, "kalite suzgeci YOK"
    assert "option_e IS NOT NULL" in sql, "bos sik suzgeci YOK"


def test_tur_dilimi_konu_kapsamiyla_sinirli() -> None:
    """TURKCE dilimi konu koduyla SINIRLI olmali (7 Eyl 2026 olcumu).

    `subject_area='TURKCE'` etiketli temiz dilimde 28 soru MAT.PRB / KIM /
    GEN / COG konularina bagliydi. O kodlar canlida da var; suzgec olmasa
    yukleyici Turkce etiketli soruyu matematik konusu altina SESSIZCE yazardi.
    Kalite suzgeci MAT ile ayni olmali (tek kaynak: _q crop, high, sik E).
    """
    sql = DILIMLER["tur_tyt"]
    assert "th.code = 'TUR'" in sql and "TYT-TR-%" in sql, "konu kapsami suzgeci YOK"
    assert "subject_area = 'TURKCE'" in sql
    for parca in ("_q[0-9]+", "auto_judged_high", "option_e IS NOT NULL"):
        assert parca in sql, f"kalite suzgeci eksik: {parca}"


def test_haric_kumesi_birlesim_kullanir_cikarma_degil() -> None:
    """set-ici mukerrer ile capraz-DB ORTUSEBILIR; cikarma yanlis sayi verir.

    KIMYA'da kesisim 0 olctu ve naif cikarma TESADUFEN dogru cikti; MAT'ta
    ayni sansi varsayma.
    """
    assert haric_kumesi({"a", "b"}, {"b", "c"}) == {"a", "b", "c"}
    assert len(haric_kumesi({"a", "b"}, {"b", "c"})) == 3, "birlesim 3, cikarma 1"


def test_konu_dengeli_sec_tavani_asmaz() -> None:
    """Tek konu havuzu domine etmemeli -- A1 'konu kirilimi' vaat ediyor.

    Canli dagilimda en buyuk konu 975, en kucugu 43. Tavansiz secim 600'un
    yarisini tek konudan alirdi ve 'konu kirilimi' tek kovadan karsilanamaz.
    """
    adaylar = [(f"id{i}", "K1") for i in range(200)]
    adaylar += [(f"j{i}", "K2") for i in range(10)]
    secilen = konu_dengeli_sec(adaylar, tavan=50)
    k1 = [x for x in secilen if x[1] == "K1"]
    k2 = [x for x in secilen if x[1] == "K2"]
    assert len(k1) == 50, f"K1 tavani asti: {len(k1)}"
    assert len(k2) == 10, "tavanin ALTINDAKI konu kirpilmamali"


def test_konu_dengeli_sec_deterministik() -> None:
    """Iki kosum birebir ayni kumeyi vermeli -- `random` YOK.

    Nondeterministik olsaydi PROVA'da olculen kume ile KALICI'da yazilan kume
    AYRISIRDI ve prova hicbir sey kanitlamazdi.
    """
    adaylar = [(f"id{i}", "K1") for i in range(200)]
    assert konu_dengeli_sec(adaylar, tavan=50) == konu_dengeli_sec(adaylar, tavan=50)


def test_konu_dengeli_sec_girdi_sirasindan_bagimsiz() -> None:
    """Kaynak sorgu satir sirasini degistirse bile ayni kume cikmali.

    Postgres ORDER BY'siz sorguda sirayi garanti etmez; secim buna duyarli
    olsaydi iki kosum sessizce farklilasirdi.
    """
    adaylar = [(f"id{i}", "K1") for i in range(120)]
    assert konu_dengeli_sec(adaylar, tavan=50) == konu_dengeli_sec(
        list(reversed(adaylar)), tavan=50
    )


def test_konu_basi_tavan_makul() -> None:
    """600 hedefi konu x 50'den geliyor; sabit belgelenmis olmali."""
    assert KONU_BASI_TAVAN == 50


def test_ayt_konu_kodlari_s239_olcumuyle_ayni() -> None:
    """S239 ICERIK OKUYARAK 6 AYT konusu buldu; liste sessizce daralmamali.

    Her biri canlidan geri silinmis 179 sorunun kaynagi. Biri dusurulurse
    o konu R2'de yeniden secilir ve AYT sorusu TYT testine girer.
    """
    olculen = {"MAT.TRV", "MAT.INT", "MAT.LMT", "MAT.LOG", "MAT.TRG", "MAT.DIZ"}
    assert set(AYT_KONU_KODLARI) == olculen


def test_ayt_konu_idleri_kod_uzerinden_eler_metin_degil() -> None:
    """Yargi `primary_topic_id`'de; metin regex'i S239'da 0 verip yaniltmisti."""
    harita = {"t1": "MAT.TRV", "t2": "MAT.SAY", "t3": "MAT.DIZ", "t4": "KIM.ASI"}
    assert ayt_konu_idleri(harita) == {"t1", "t3"}
    assert ayt_konu_idleri({}) == set(), "bos harita bos kume"


def test_kirmizi_liste_birlesim_ve_bosluk_toleransi(tmp_path: Path) -> None:
    """Reddedilmis id'ler canlida YOK; capraz-DB elemesi onlari goremez.

    Iki dosya ortusebilir (ayni id hem sizdiran hem AYT olabilir) -- birlesim.
    Bos satir / bosluk id sayilmaz.
    """
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("x1\nx2\n\n", encoding="utf-8")
    b.write_text("x2\n  x3  \n", encoding="utf-8")
    assert kirmizi_liste_oku([a, b]) == {"x1", "x2", "x3"}
    assert kirmizi_liste_oku([]) == set()


def test_kapsam_kodla_olculur_uuid_drift_yanlis_negatif_vermez() -> None:
    """Kapsam KODLA olculur, id ile DEGIL (7 Eyl 2026, TURKCE olcumu).

    temp `TUR` ile canli `TUR` ayni kod, FARKLI id (UUID drift). Yukleyici
    kodla esler; secici id ile olcunce TUR kokundeki 673 soruyu "kapsam disi"
    diye atmisti. Kontrol kolu: canlida OLMAYAN kod hala eleniyor.
    """
    kaynak_kodu = {"temp-tur": "TUR", "temp-x": "TYT-TR-09", "temp-mat": "MAT.SAY"}
    canli_kodlar = {"TUR", "MAT.SAY"}  # canli TUR'un id'si FARKLI, kod ayni
    ham = [
        ("q1", "temp-tur", "h1"),
        ("q2", "temp-x", "h2"),
        ("q3", "temp-mat", None),
        ("q4", "temp-yok", "h4"),  # kaynakta bile olmayan konu id
    ]
    kalan = {i for i, _, _ in kapsam_suz(ham, kaynak_kodu, canli_kodlar)}
    assert kalan == {"q1", "q3"}, kalan
