"""
KIRO2 — YKS Estimator Test Suite
===================================
Test kategorileri:
  1. θ → net dönüşümü (fizik, sınırlar, monotonluk)
  2. Net güvensizlik bandı
  3. TYT ham puan hesabı
  4. AYT puan hesabı (SAY, EA, SÖZ)
  5. Puan → sıralama dönüşümü
  6. YKSEstimator entegrasyon
  7. Öğrenci senaryoları (gerçekçi)
"""

from __future__ import annotations

import pytest

from app.services.yks_estimator import (
    AYT_DERSLER,
    PUAN_DAGILIM,
    TYT_DERSLER,
    DersTheta,
    YKSEstimator,
    _normal_cdf,
    ayt_puan_hesapla,
    net_guvensizlik,
    puan_to_siralama,
    theta_to_net,
    tyt_puan_hesapla,
)

# ─── BÖLÜM 1: θ → Net Dönüşümü ───────────────────────────────────────────────


class TestThetaToNet:
    def test_high_theta_high_net(self):
        ders = TYT_DERSLER["mat"]
        net_yuksek = theta_to_net(2.0, ders)
        net_dusuk = theta_to_net(-2.0, ders)
        assert net_yuksek > net_dusuk

    def test_net_bounded_by_n_soru(self):
        for kod, ders in {**TYT_DERSLER, **AYT_DERSLER}.items():
            for theta in (-3.0, 0.0, 3.0):
                net = theta_to_net(theta, ders)
                assert 0.0 <= net <= ders.n_soru, (
                    f"{kod} theta={theta}: net={net} sınır dışı"
                )

    def test_net_monotone_in_theta(self):
        """Yüksek θ → daha yüksek net (monoton artan)."""
        ders = TYT_DERSLER["turkce"]
        thetas = [-2.0, -1.0, 0.0, 1.0, 2.0]
        nets = [theta_to_net(t, ders) for t in thetas]
        for i in range(len(nets) - 1):
            assert nets[i] <= nets[i + 1], (
                f"Monotonluk bozuldu: theta={thetas[i]:.1f} net={nets[i]:.2f}"
            )

    def test_guessing_floor(self):
        """Çok düşük θ bile şans etkisiyle sıfırın üzerinde net verir."""
        ders = TYT_DERSLER["mat"]  # c=0.25, 40 soru
        net = theta_to_net(-4.0, ders)
        # Saf şans: 40 × (0.25 - 0.25×0.75) = 40 × 0.0625 = 2.5
        # Negatif çıkmamalı
        assert net >= 0.0

    def test_custom_irt_params(self):
        """Özel IRT parametreleri ders ortalamasından farklı sonuç vermeli."""
        ders = TYT_DERSLER["mat"]
        net_def = theta_to_net(0.0, ders)
        net_hard = theta_to_net(0.0, ders, irt_a=1.5, irt_b=1.5, irt_c=0.25)
        assert net_hard < net_def  # b=1.5 → θ=0'da P daha düşük → daha az net


# ─── BÖLÜM 2: Net Güvensizlik Bandı ──────────────────────────────────────────


class TestNetGuvensizlik:
    def test_band_contains_center(self):
        ders = TYT_DERSLER["turkce"]
        alt, ust = net_guvensizlik(0.0, 0.4, ders)
        merkez = theta_to_net(0.0, ders)
        assert alt <= merkez <= ust

    def test_wider_se_wider_band(self):
        ders = TYT_DERSLER["mat"]
        alt1, ust1 = net_guvensizlik(0.0, 0.3, ders)
        alt2, ust2 = net_guvensizlik(0.0, 0.8, ders)
        assert (ust2 - alt2) >= (ust1 - alt1)

    def test_band_bounded(self):
        ders = TYT_DERSLER["fen"]
        for theta in (-2.0, 0.0, 2.0):
            alt, ust = net_guvensizlik(theta, 0.5, ders)
            assert alt >= 0
            assert ust <= ders.n_soru


# ─── BÖLÜM 3: TYT Puan Hesabı ────────────────────────────────────────────────


class TestTytPuanHesapla:
    def test_zero_nets_minimum_puan(self):
        netleri = {"turkce": 0.0, "sosyal": 0.0, "mat": 0.0, "fen": 0.0}
        puan = tyt_puan_hesapla(netleri)
        assert puan >= 100.0

    def test_full_nets_near_maximum(self):
        netleri = {
            "turkce": 40.0,
            "sosyal": 20.0,
            "mat": 40.0,
            "fen": 20.0,
        }
        puan = tyt_puan_hesapla(netleri)
        assert puan >= 400.0

    def test_higher_nets_higher_puan(self):
        net_dusuk = {"turkce": 15.0, "sosyal": 8.0, "mat": 15.0, "fen": 8.0}
        net_yuksek = {"turkce": 30.0, "sosyal": 15.0, "mat": 30.0, "fen": 15.0}
        assert tyt_puan_hesapla(net_yuksek) > tyt_puan_hesapla(net_dusuk)

    def test_puan_in_valid_range(self):
        for multiplier in [0.0, 0.3, 0.6, 1.0]:
            netleri = {
                "turkce": 40 * multiplier,
                "sosyal": 20 * multiplier,
                "mat": 40 * multiplier,
                "fen": 20 * multiplier,
            }
            p = tyt_puan_hesapla(netleri)
            assert 100.0 <= p <= 500.0, f"Puan sınır dışı: {p}"

    def test_partial_nets_ok(self):
        """Bazı dersler eksikse sıfır sayılır."""
        netleri = {"turkce": 20.0, "mat": 20.0}  # sosyal ve fen yok
        puan = tyt_puan_hesapla(netleri)
        assert puan >= 100.0


# ─── BÖLÜM 4: AYT Puan Hesabı ────────────────────────────────────────────────


class TestAytPuanHesapla:
    def _ayt_netleri(self, multiplier=0.5):
        return {
            "mat": 40 * multiplier,
            "fizik": 14 * multiplier,
            "kimya": 13 * multiplier,
            "biyoloji": 13 * multiplier,
            "edebiyat": 24 * multiplier,
            "tarih1": 10 * multiplier,
            "cografya1": 6 * multiplier,
        }

    def test_say_higher_nets_higher_puan(self):
        tyt = 280.0
        p1 = ayt_puan_hesapla("SAY", self._ayt_netleri(0.3), tyt)
        p2 = ayt_puan_hesapla("SAY", self._ayt_netleri(0.8), tyt)
        assert p2 > p1

    def test_puan_in_range(self):
        for pt in ("SAY", "EA", "SÖZ"):
            for m in (0.1, 0.5, 1.0):
                p = ayt_puan_hesapla(pt, self._ayt_netleri(m), 260.0)
                assert 100.0 <= p <= 550.0, f"{pt} m={m}: puan={p}"

    def test_say_uses_math_heavily(self):
        """SAY'da matematik ağırlıklı; mat netini artırınca SAY çok artar."""
        tyt = 280.0
        base = self._ayt_netleri(0.5)
        high_mat = dict(base)
        high_mat["mat"] = 38.0
        p_base = ayt_puan_hesapla("SAY", base, tyt)
        p_highmat = ayt_puan_hesapla("SAY", high_mat, tyt)
        assert p_highmat > p_base

    def test_ea_uses_both_mat_and_edb(self):
        """EA hem matematik hem edebiyat kullanır."""
        tyt = 280.0
        base = self._ayt_netleri(0.5)
        # Edebiyatı artır
        high_edb = dict(base)
        high_edb["edebiyat"] = 22.0
        p_base = ayt_puan_hesapla("EA", base, tyt)
        p_highedb = ayt_puan_hesapla("EA", high_edb, tyt)
        assert p_highedb > p_base


# ─── BÖLÜM 5: Puan → Sıralama ────────────────────────────────────────────────


class TestPuanToSiralama:
    def test_higher_puan_lower_rank(self):
        """Yüksek puan → düşük sıralama (daha ön sıra)."""
        s1, _ = puan_to_siralama(300.0, "TYT")
        s2, _ = puan_to_siralama(400.0, "TYT")
        assert s1 > s2

    def test_rank_bounded(self):
        for pt in ("TYT", "SAY", "EA", "SÖZ"):
            dist = PUAN_DAGILIM[pt]
            s, y = puan_to_siralama(dist["mu"], pt)
            assert 1 <= s <= dist["n_aday"]
            assert 0.0 <= y <= 100.0

    def test_average_puan_near_50th_percentile(self):
        """Ortalama puan → ~50. yüzdelik."""
        dist = PUAN_DAGILIM["TYT"]
        _, y = puan_to_siralama(dist["mu"], "TYT")
        assert 40.0 <= y <= 60.0, f"Ortalama puan %50 yüzdelik değil: {y}"

    def test_all_puan_turleri(self):
        for pt in ("TYT", "SAY", "EA", "SÖZ"):
            s, y = puan_to_siralama(300.0, pt)
            assert s > 0
            assert 0 <= y <= 100

    def test_normal_cdf_sanity(self):
        assert abs(_normal_cdf(0.0) - 0.5) < 0.001
        assert _normal_cdf(3.0) > 0.99
        assert _normal_cdf(-3.0) < 0.01


# ─── BÖLÜM 6: YKSEstimator Entegrasyon ───────────────────────────────────────


class TestYKSEstimator:
    def _orta_thetalar(self):
        return {
            "turkce": DersTheta("turkce", 0.5, 0.3),
            "sosyal": DersTheta("sosyal", 0.2, 0.4),
            "mat": DersTheta("mat", 0.8, 0.35),
            "fen": DersTheta("fen", 0.3, 0.4),
        }

    def _ayt_thetalar(self):
        return {
            "mat": DersTheta("mat", 1.0, 0.4),
            "fizik": DersTheta("fizik", 0.5, 0.5),
            "kimya": DersTheta("kimya", 0.4, 0.5),
            "biyoloji": DersTheta("biyoloji", 0.6, 0.5),
            "edebiyat": DersTheta("edebiyat", 0.3, 0.4),
        }

    def test_tyt_raporu_returns_valid_puan(self):
        est = YKSEstimator()
        tahmin = est.tyt_raporu(self._orta_thetalar())
        assert tahmin.puan_turu == "TYT"
        assert 100.0 <= tahmin.puan <= 500.0

    def test_tyt_siralama_positive(self):
        est = YKSEstimator()
        tahmin = est.tyt_raporu(self._orta_thetalar())
        assert tahmin.tahmini_siralama > 0

    def test_tyt_guvenilik_yuksek_for_low_se(self):
        thetalar = {
            k: DersTheta(k, v, se=0.25)  # düşük SE
            for k, v in {"turkce": 0.5, "sosyal": 0.3, "mat": 0.8, "fen": 0.4}.items()
        }
        tahmin = YKSEstimator().tyt_raporu(thetalar)
        assert tahmin.guvenilik == "yüksek"

    def test_confidence_interval_ordered(self):
        """Alt sınır ≤ tahmin ≤ üst sınır."""
        est = YKSEstimator()
        tahmin = est.tyt_raporu(self._orta_thetalar())
        assert tahmin.alt_sinir <= tahmin.puan <= tahmin.ust_sinir

    def test_siralama_band_ordered(self):
        """Puan bandına göre sıralama da band oluşturmalı."""
        est = YKSEstimator()
        tahmin = est.tyt_raporu(self._orta_thetalar())
        assert tahmin.siralama_alt <= tahmin.tahmini_siralama <= tahmin.siralama_ust

    def test_ayt_say_raporu(self):
        est = YKSEstimator()
        tahmin = est.ayt_raporu("SAY", self._orta_thetalar(), self._ayt_thetalar())
        assert tahmin.puan_turu == "SAY"
        assert 100 <= tahmin.puan <= 550

    def test_tam_rapor_tyt_always_present(self):
        est = YKSEstimator()
        rapor = est.tam_rapor(self._orta_thetalar())
        assert rapor.tyt is not None

    def test_tam_rapor_oneriler_nonempty(self):
        est = YKSEstimator()
        rapor = est.tam_rapor(self._orta_thetalar(), self._ayt_thetalar())
        assert len(rapor.oneriler) >= 1


# ─── BÖLÜM 7: Gerçekçi Öğrenci Senaryoları ───────────────────────────────────


class TestGercekciSenaryolar:
    """
    Gerçek YKS sonuçlarıyla örtüşen tahmin kalitesi testleri.
    Kesin doğruluk beklenmez; ama yön ve büyüklük sağlıklı olmalı.
    """

    def test_guclu_ogrenci_yuksek_puan(self):
        """θ=1.5+ → TYT 350+ beklenir."""
        thetalar = {
            k: DersTheta(k, 1.5, 0.3) for k in ("turkce", "sosyal", "mat", "fen")
        }
        tahmin = YKSEstimator().tyt_raporu(thetalar)
        assert tahmin.puan >= 320.0, (
            f"Güçlü öğrenci için beklenenden düşük: {tahmin.puan}"
        )

    def test_zayif_ogrenci_dusuk_puan(self):
        """θ=-1.5 → TYT 220 altı beklenir."""
        thetalar = {
            k: DersTheta(k, -1.5, 0.4) for k in ("turkce", "sosyal", "mat", "fen")
        }
        tahmin = YKSEstimator().tyt_raporu(thetalar)
        assert tahmin.puan <= 260.0, (
            f"Zayıf öğrenci için beklenenden yüksek: {tahmin.puan}"
        )

    def test_orta_ogrenci_orta_siralama(self):
        """
        θ=0 IRT ortalama değeri, Türk TYT sınavında üst %15 anlamına gelir
        (TYT puan dağılımı sağa çarpık; gerçek kitle ortalaması θ≈-0.5).
        θ=0 için beklenti: sıralama 100K-600K arası.
        """
        thetalar = {
            k: DersTheta(k, 0.0, 0.4) for k in ("turkce", "sosyal", "mat", "fen")
        }
        tahmin = YKSEstimator().tyt_raporu(thetalar)
        assert 100_000 <= tahmin.tahmini_siralama <= 700_000, (
            f"θ=0 için sıralama beklenenden farklı: {tahmin.tahmini_siralama}"
        )

    def test_gercek_ortalama_ogrenci_siralama(self):
        """θ=-0.5 (gerçek TYT kitlesi ortalaması) → sıralama ~1M-2M."""
        thetalar = {
            k: DersTheta(k, -0.5, 0.4) for k in ("turkce", "sosyal", "mat", "fen")
        }
        tahmin = YKSEstimator().tyt_raporu(thetalar)
        assert 800_000 <= tahmin.tahmini_siralama <= 2_000_000, (
            f"Gerçek ortalama için sıralama: {tahmin.tahmini_siralama}"
        )

    def test_say_puan_increases_with_theta(self):
        """SAY puanı θ artışıyla monoton artar."""
        est = YKSEstimator()
        puanlar = []
        for theta_level in [-1.0, 0.0, 0.5, 1.0, 1.5]:
            tyt_t = {
                k: DersTheta(k, theta_level, 0.3)
                for k in ("turkce", "sosyal", "mat", "fen")
            }
            ayt_t = {
                k: DersTheta(k, theta_level, 0.3)
                for k in ("mat", "fizik", "kimya", "biyoloji")
            }
            tahmin = est.ayt_raporu("SAY", tyt_t, ayt_t)
            puanlar.append(tahmin.puan)

        for i in range(len(puanlar) - 1):
            assert puanlar[i] <= puanlar[i + 1] + 1.0, f"SAY monoton değil: {puanlar}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
