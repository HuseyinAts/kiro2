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
