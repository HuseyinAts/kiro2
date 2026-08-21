"""B3 FAZ 3 — `KonuPerformansi` ders kimligi + kovalama-degismez ortalama.

NEDEN BU DOSYA VAR (olculdu, 21 Agu 2026):
`KonuPerformansi` yalniz `konu: str` tasiyordu. B3 `konu`yu ders adindan konu
adina cevirince, ders kimligine ihtiyaci olan her tuketici diziyi ders sanmak
zorunda kaldi:
  advanced_reports.py:474/1167  _get_subject_irt_aggregate(kp.konu)
      "Kimyasal Denge" -> "KIMYASAL DENGE" -> 0 satir   (gercek 1262)
      "Kimya"          -> "KIMYA"          -> 3531 satir (gercek 263)
  advanced_reports.py:761/869   Sigma / len(kova) -- kova sayisina BAGIMLI
  advanced_reports.py:934/1051  "matematik" in normalize_tr(kp.konu) -> olu dal
"""

from __future__ import annotations

import pytest

from models import KonuPerformansi


def _kp(**ek) -> KonuPerformansi:
    """Varsayilan gecerli KonuPerformansi; `ek` ile alan ezilir."""
    alanlar = {
        "konu": "Fonksiyonlar",
        "toplam_soru": 3,
        "dogru_sayisi": 2,
        "yanlis_sayisi": 1,
        "bos_sayisi": 0,
        "basari_yuzdesi": 66.7,
    }
    alanlar.update(ek)
    return KonuPerformansi(**alanlar)


class TestKimlikAlanlari:
    def test_ders_ve_konu_kodu_alanlari_var(self):
        """Ders kimligi ARTIK ayri alanda -- `konu` dizesinden cikarilmaz."""
        kp = _kp(ders="matematik", konu_kodu="MAT.FON")
        assert kp.ders == "matematik"
        assert kp.konu_kodu == "MAT.FON"

    def test_alanlar_varsayilanli_geriye_uyumlu(self):
        """Eski cagri yerleri (6 test dosyasi) kirilmamali."""
        kp = _kp()
        assert kp.ders is None
        assert kp.konu_kodu is None

    def test_konu_ile_ders_ayri_kimliklerdir(self):
        """Level-1 konu adi ders adiyla CAKISABILIR (olculdu: KIM|Kimya)."""
        kp = _kp(konu="Kimya", ders="kimya", konu_kodu="KIM")
        assert kp.konu == "Kimya"
        assert kp.ders == "kimya"
        # Ayirt edici anahtar konu KODUDUR, konu ADI degil.
        assert kp.konu_kodu == "KIM"


class TestDersDali:
    """`advanced_reports` ogrenme-stili uyumu ders bazli dallanir.

    OLCULDU (21 Agu 2026): kanon subject_area kumesi {KIMYA, MATEMATIK} --
    ASCII, yani Turkce ders adi 'TURKCE' bicimindedir. Mevcut kodda
    `elif "turkce" in ...` yerine Turkce harfli dize yaziyordu ve kanon
    degerle HICBIR ZAMAN eslesemezdi.

    Canli DB'de TURKCE satiri YOK -- bu dal E2E ile dogrulanamaz, bu yuzden
    sentetik veriyle civilenir. Sinir denetim dokumanina yazildi.
    """

    @pytest.mark.parametrize(
        "ders_girdi",
        ["matematik", "MATEMATIK", "Matematik", "  matematik  "],
    )
    def test_matematik_dali_bicimden_bagimsiz_secilir(self, ders_girdi):
        from api.advanced_reports import _ders_uyum_skoru

        vark = {"visual": 0.8, "reading": 0.2, "auditory": 0.1, "kinesthetic": 0.1}
        felder = {"sequential_global": -0.4, "visual_verbal": 0.3}

        skor = _ders_uyum_skoru(ders_girdi, vark, felder)
        beklenen = (vark["visual"] + abs(felder["sequential_global"])) / 2
        assert skor == pytest.approx(
            beklenen
        ), f"matematik dali secilmedi (girdi={ders_girdi!r})"

    def test_turkce_dali_ascii_kanon_degerle_secilir(self):
        from api.advanced_reports import _ders_uyum_skoru

        vark = {"visual": 0.1, "reading": 0.9, "auditory": 0.1, "kinesthetic": 0.1}
        felder = {"sequential_global": -0.4, "visual_verbal": 0.3}

        skor = _ders_uyum_skoru("TURKCE", vark, felder)
        beklenen = (vark["reading"] + abs(felder["visual_verbal"])) / 2
        assert skor == pytest.approx(beklenen), "TURKCE dali secilmedi"

    def test_bilinmeyen_ders_ortalama_dala_duser(self):
        from api.advanced_reports import _ders_uyum_skoru

        vark = {"visual": 0.4, "reading": 0.4, "auditory": 0.4, "kinesthetic": 0.4}
        felder = {"sequential_global": -0.4, "visual_verbal": 0.3}

        assert _ders_uyum_skoru("KIMYA", vark, felder) == pytest.approx(0.4)
        assert _ders_uyum_skoru(None, vark, felder) == pytest.approx(0.4)

    def test_konu_adi_ders_dalini_secmez(self):
        """Regresyon civisi: dal `konu` degil `ders` okur -- konu adi SECMEZ.

        'Matematik' adli bir KONU (level-1, topic_hierarchy'de var) ders
        dalini tetiklememelidir -- ders kimligi ayri alandan gelir.
        """
        from api.advanced_reports import _ders_uyum_skoru

        vark = {"visual": 0.9, "reading": 0.1, "auditory": 0.1, "kinesthetic": 0.1}
        felder = {"sequential_global": -0.9, "visual_verbal": 0.3}

        # ders=None (kimlik yok) -> matematik dali SECILMEZ, ortalamaya duser
        ortalama = sum(vark.values()) / 4
        assert _ders_uyum_skoru(None, vark, felder) == pytest.approx(ortalama)


# --------------------------------------------------------------------------
# Kovalama-degismez ortalama icin ORTAK veri.
#
# AYNI 40 soru, iki farkli kovalama:
#   iki kova (DERS bazi) : matematik 10 soru @8.0 · kimya 30 soru @4.0
#   dort kova (KONU bazi): matematik 3 konuya bolundu (3+3+4 soru, hepsi @8.0)
#                          kimya tek konu olarak kaldi (30 soru @4.0)
# Ders basina konu SAYISI dersten derse degisir (B3'te matematik 14 konuya,
# kimya 13 konuya bolundu) -- bu asimetri gercek olanin ta kendisi.
#
# ARITMETIK (dogrulandi):
#   agirlikli : (8*10 + 4*30)/40 = 5.0  ==  (8*3+8*3+8*4+4*30)/40 = 5.0   AYNI
#   agirliksiz: (8+4)/2          = 6.0  !=  (8+8+8+4)/4          = 7.0   FARKLI
#
# Bu asimetri ZORUNLU: her iki tarafi da esit sayida alt-kovaya bolseydik
# agirliksiz ortalama da esit cikar, kontrol kolu HICBIR SEY kanitlamazdi.
# --------------------------------------------------------------------------
IKI_KOVA = [
    {"deger": 8.0, "agirlik": 10},
    {"deger": 4.0, "agirlik": 30},
]
DORT_KOVA = [
    {"deger": 8.0, "agirlik": 3},
    {"deger": 8.0, "agirlik": 3},
    {"deger": 8.0, "agirlik": 4},
    {"deger": 4.0, "agirlik": 30},
]


class TestAgirlikliOrtalama:
    """ZPD genel profili kova SAYISINDAN bagimsiz olmali.

    Eski bicim `Sigma / len(kova)` idi: kardinalite 1 -> 13 olunca ortalama
    sessizce kaydi (olculdu: +9,91 puan). Soru-agirlikli bicim ayni veriyi
    hangi kovalamayla verirsen ver AYNI sonucu uretir -- yani bir sonraki
    kardinalite degisiminde de kaymaz. Bu testin tasidigi iddia budur.
    """

    def test_agirlikli_ortalama_temel(self):
        from api.advanced_reports import _agirlikli_ortalama

        kayitlar = [
            {"deger": 10.0, "agirlik": 1},
            {"deger": 0.0, "agirlik": 3},
        ]
        # (10*1 + 0*3) / 4 = 2.5   (agirliksiz olsa 5.0 olurdu)
        assert _agirlikli_ortalama(kayitlar, "deger") == pytest.approx(2.5)

    def test_kovalama_degismez(self):
        """AYNI 40 soru, iki farkli kovalama -> AYNI ortalama.

        Bu, B3'un kirdigi invaryantin ta kendisidir.
        """
        from api.advanced_reports import _agirlikli_ortalama

        assert _agirlikli_ortalama(IKI_KOVA, "deger") == pytest.approx(
            _agirlikli_ortalama(DORT_KOVA, "deger")
        ), "ortalama kovalamaya BAGIMLI -- invaryant kirik"

    def test_agirliksiz_bicim_bu_invaryanti_kirar(self):
        """KONTROL KOLU: eski `Sigma/len` bicimi ayni veride FARKLI verir.

        Bu assert olmadan yukaridaki test 'her zaman gecen' bir test
        sanilabilirdi -- invaryantin ayirt edici oldugunu kanitlar.
        """
        from api.advanced_reports import _agirlikli_ortalama

        agirliksiz_iki = sum(k["deger"] for k in IKI_KOVA) / len(IKI_KOVA)
        agirliksiz_dort = sum(k["deger"] for k in DORT_KOVA) / len(DORT_KOVA)
        assert agirliksiz_iki != pytest.approx(agirliksiz_dort), (
            "kontrol kolu bozuk: bu veri agirliksiz bicimi ayirt etmiyor, "
            "test bir sey kanitlamiyor"
        )
        # ...ve agirlikli bicim ikisinde de ayni:
        assert _agirlikli_ortalama(IKI_KOVA, "deger") == pytest.approx(
            _agirlikli_ortalama(DORT_KOVA, "deger")
        )

    def test_ayni_soru_sayisi_kontrolu(self):
        """Iki kovalama GERCEKTEN ayni sinavi temsil ediyor mu?

        Toplam soru sayisi tutmuyorsa yukaridaki iki test farkli sinavlari
        karsilastiriyor demektir ve invaryant iddiasi anlamsiz olur.
        """
        assert (
            sum(k["agirlik"] for k in IKI_KOVA)
            == sum(k["agirlik"] for k in DORT_KOVA)
            == 40
        )

    def test_sifir_agirlik_sifira_bolmez(self):
        from api.advanced_reports import _agirlikli_ortalama

        assert _agirlikli_ortalama([], "deger") == 0.0
        assert _agirlikli_ortalama([{"deger": 5.0, "agirlik": 0}], "deger") == 0.0
