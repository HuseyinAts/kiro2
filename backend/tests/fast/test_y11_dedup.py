"""Y11 göç dedup'ı — SAF katman, DB'siz (FAZ B, 20 Ağu 2026).

NEDEN AYRI BİR MODÜL
--------------------
Bu, göçün en riskli parçası ve iki kez ölçülerek şekillendi:

1. **`soru_hash` dedup için KULLANILAMAZ.** Canlı `soru_hash`'lerin %100'ü UUID4
   (sürüm+varyant nibble 36.967/36.967) — içerik hash'i değil. İki DB arasında
   ortak hash **0**, ama ortak normalize metin **17.213**. Yani hash çapraz-DB
   kimlik taşımıyor ve `uq_qb_soru_hash_active` hiçbir mükerreri durduramaz.

2. **Kimlik, gövde TEK BAŞINA değildir.** S232-C'de "669 mükerrer + 118
   kendi-kendiyle çelişen çift" raporlandı; normalizasyon yalnız `question_text`'e
   bakıyordu. Şıklar dahil edilince gerçek sayı **153**, çelişki **0** —
   yani **516 meşru soru (%77) yanlışlıkla silinecekti.**

   Kanıt çifti (aynı üçgen sorusu, iki satır):
       A) 24  B) 30  C) 36 ...   anahtar = B
       A) 30  B) 40  C) 50 ...   anahtar = A
   İkisi de **30**'u işaret ediyor. Harfler farklı çünkü ŞIK SIRASI farklı.
   `correct_answer` bir DEĞER değil, şık listesine **konumsal referanstır**.

TASARIM KARARI — SIKI kimlik varsayılan
---------------------------------------
Kimlik = normalize gövde + normalize şıklar **SIRASIYLA**. Şıkları sıralamak
(`gevsek_kimlik`) daha çok grup bulur ama şıkları karıştırılmış meşru varyantları
da birleştirir. Bu depoda içerik silmenin bedeli, mükerrer bırakmanın bedelinden
**ağır** (5 Ağu: 187.835 → 2.304). Bu yüzden sıkı olan varsayılan; gevşek olan
yalnız **raporlama** için var ve asla silme kararı vermez.
"""

from __future__ import annotations

import sys
from pathlib import Path

DEPO_KOKU = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DEPO_KOKU / "backend" / "scripts" / "quality"))

from y11_dedup import (  # noqa: E402
    gevsek_kimlik,
    mukerrer_gruplar,
    normalize_metin,
    siki_kimlik,
)


def _soru(metin, *siklar, anahtar="A"):
    return {
        "question_text": metin,
        "option_a": siklar[0] if len(siklar) > 0 else None,
        "option_b": siklar[1] if len(siklar) > 1 else None,
        "option_c": siklar[2] if len(siklar) > 2 else None,
        "option_d": siklar[3] if len(siklar) > 3 else None,
        "option_e": siklar[4] if len(siklar) > 4 else None,
        "correct_answer": anahtar,
    }


# ---------------------------------------------------------------------------
# NORMALIZASYON — Turkce'ye ozgu tuzaklar
# ---------------------------------------------------------------------------


def test_bosluk_ve_satir_sonu_normalize_edilir():
    assert normalize_metin("  ac\n\tbir   sey  ") == normalize_metin("ac bir sey")


def test_turkce_i_dogru_kucultulur():
    """`I` -> `ı`, `İ` -> `i`. Naif `.lower()` bunu TERS yapar ve iki farkli
    soruyu ayni ya da ayni soruyu farkli gosterir (CLAUDE.md, non-negotiable)."""
    assert normalize_metin("ISI") == normalize_metin("ısı")
    assert normalize_metin("İSİ") == normalize_metin("isi")
    assert normalize_metin("ISI") != normalize_metin("isi")


def test_nfc_birlesik_ve_ayrik_ayni_sayilir():
    """U+0130 vs 'I'+birlesik nokta — NFC olmadan ayni metin FARKLI gorunur."""
    assert normalize_metin("İstanbul") == normalize_metin("İstanbul")


def test_matematik_isaretleri_korunur():
    """A3 olcumunde 'noktalama sil' yaklasimi +/- isaretlerini siliyordu ve
    (x-2)^2+(y+1)^2=16 ile (x+2)^2+(y-1)^2=16'yi AYNI sayiyordu (41 FP'nin 27'si).
    Normalizasyon ic noktalamaya DOKUNMAZ."""
    assert normalize_metin("(x-2)^2+(y+1)^2=16") != normalize_metin(
        "(x+2)^2+(y-1)^2=16"
    )


# ---------------------------------------------------------------------------
# KIMLIK — gövde TEK BASINA yetmez
# ---------------------------------------------------------------------------


def test_ayni_govde_farkli_siklar_ayni_degil():
    """S232-C'nin 516 meşru soruyu silecek olan kusuru. Kimligin cekirdegi."""
    a = _soru("Ucgenin alani kac?", "24", "30", "36", "42", "48", anahtar="B")
    b = _soru("Ucgenin alani kac?", "30", "40", "50", "60", "70", anahtar="A")
    assert siki_kimlik(a) != siki_kimlik(b)


def test_ayni_govde_ayni_siklar_ayni():
    a = _soru("Ucgenin alani kac?", "24", "30", "36", "42", "48", anahtar="B")
    b = _soru("Ucgenin  alani   kac?", "24", "30", "36", "42", "48", anahtar="B")
    assert siki_kimlik(a) == siki_kimlik(b)


def test_anahtar_harfi_kimlige_girmez():
    """Anahtar konumsal bir referans; ayni soru farkli harfle etiketlenmis
    olabilir ve bu onu FARKLI soru YAPMAZ. Anahtar celiskisi ayri bir olcumdur."""
    a = _soru("Soru?", "1", "2", "3", "4", "5", anahtar="A")
    b = _soru("Soru?", "1", "2", "3", "4", "5", anahtar="C")
    assert siki_kimlik(a) == siki_kimlik(b)


def test_sik_sirasi_siki_kimlikte_onemli():
    a = _soru("Soru?", "1", "2", "3", "4", "5")
    b = _soru("Soru?", "5", "4", "3", "2", "1")
    assert siki_kimlik(a) != siki_kimlik(b)


def test_sik_sirasi_gevsek_kimlikte_onemsiz():
    """Gevsek kimlik YALNIZ raporlama icin; silme karari vermez."""
    a = _soru("Soru?", "1", "2", "3", "4", "5")
    b = _soru("Soru?", "5", "4", "3", "2", "1")
    assert gevsek_kimlik(a) == gevsek_kimlik(b)


def test_eksik_sik_kimlikte_yer_tutar():
    """4 sikli soru ile 5 sikli soru AYNI olamaz; None'i atlamak onlari
    birlestirirdi."""
    a = _soru("Soru?", "1", "2", "3", "4")
    b = _soru("Soru?", "1", "2", "3", "4", "5")
    assert siki_kimlik(a) != siki_kimlik(b)


# ---------------------------------------------------------------------------
# GRUPLAMA
# ---------------------------------------------------------------------------


def test_gruplar_yalniz_mukerrerleri_dondurur():
    satirlar = [
        {"id": "1", **_soru("A?", "1", "2")},
        {"id": "2", **_soru("A?", "1", "2")},
        {"id": "3", **_soru("B?", "1", "2")},
    ]
    gruplar = mukerrer_gruplar(satirlar)
    assert len(gruplar) == 1
    assert sorted(gruplar[0]) == ["1", "2"]


def test_tekil_satirlar_grup_uretmez():
    """Kontrol kolu: her satiri grup sayan bir alet 'hepsi mukerrer' derdi."""
    satirlar = [{"id": str(i), **_soru(f"Soru {i}?", "1", "2")} for i in range(5)]
    assert mukerrer_gruplar(satirlar) == []


def test_grup_ilk_id_yi_korur_gerisini_isaretler():
    """Silme karari deterministik olmali: ayni girdi ayni sonucu vermeli."""
    satirlar = [
        {"id": "c", **_soru("A?", "1")},
        {"id": "a", **_soru("A?", "1")},
        {"id": "b", **_soru("A?", "1")},
    ]
    (grup,) = mukerrer_gruplar(satirlar)
    assert grup == ["a", "b", "c"], "grup ici sira deterministik degil"


def test_bos_govde_grup_uretmez():
    """Bos/None govdeli satirlar birbirine benzer gorunur ve TOPTAN silinirdi.

    Bunlar dedup'in degil ICERIK YARGISININ isi; burada kimlik URETILMEZ.
    """
    satirlar = [
        {"id": "1", **_soru("", "1", "2")},
        {"id": "2", **_soru("   ", "1", "2")},
        {"id": "3", **_soru(None, "1", "2")},
    ]
    assert mukerrer_gruplar(satirlar) == []


def test_yalniz_i_ailesi_birlestirilmez_regresyon():
    """Bulanik/benzerlik tabanli dedup eklenirse BU TEST DUSER — bilerek.

    OLCULDU (20 Agu, 3.666 KABUL uzerinde): govde-only dedup, siki dedup'in
    yakalamadigi 58 grup uretiyor. O 58 grup benzerlik oranina gore ayrilinca
    metrik TERS calisiyor:

        benzerlik >=0,95 -> 32 grup, ve bunlar FARKLI SORU
        benzerlik 0,80-0,95 -> 11 grup, ve bunlar AYNI SORU (\to vs \rightarrow)

    Yani en YUKSEK benzerlik farkli soruyu, ORTA benzerlik ayni soruyu gosteriyor.
    Sebep: "yalniz I / I ve II / I ve III" ailesinde siklar karakter olarak
    neredeyse ayni ama KUME olarak farkli. Ornek (gercek veri):

        A: yalniz ı | yalniz ıı | ı ve ıı | ı ve ııı   | ıı ve ııı
        B: yalniz ı | yalniz ıı | ı ve ıı | ıı ve ııı  | ı, ıı ve ııı

    Bu ikisi FARKLI sorudur; birlestirmek icerik siler.
    (`L-s232-mekanik-siralamayi-insan-yargisiyla-dogrula`: ucuz metrikle toplu
    eleme yapmadan once metrigin insan yargisini ONGORDUGUNU olc.)
    """
    govde = "Yukaridakilerden hangileri dogrudur?"
    a = _soru(govde, "yalniz I", "yalniz II", "I ve II", "I ve III", "II ve III")
    b = _soru(govde, "yalniz I", "yalniz II", "I ve II", "II ve III", "I, II ve III")
    assert siki_kimlik(a) != siki_kimlik(b), (
        "Iki FARKLI soru ayni kimlige dustu. Bulanik esleme eklendiyse GERI AL: "
        "bu ailede karakter benzerligi %95'in ustunde ama sik KUMESI farkli."
    )
    assert gevsek_kimlik(a) != gevsek_kimlik(
        b
    ), "Gevsek kimlik bile bunlari ayirmali — sik KUMELERI farkli, yalniz sira degil."
