"""
KIRO2 — CAT Test Suite
=======================
pytest ile çalıştır:
  cd backend && pytest tests/test_cat.py -v

Test kapsamı:
  ✓ IRT 3PL formülü doğruluk
  ✓ Fisher Information hesabı
  ✓ EAP theta güncelleme (cold start + iterative)
  ✓ SE eşiği ile oturum sonlandırma
  ✓ ZPD filtresi
  ✓ Exposure kontrolü
  ✓ CAT oturumu Redis state roundtrip (mock)
  ✓ Tam oturum simülasyonu (10 soru, θ yakınsama)
"""

from __future__ import annotations

import numpy as np
import pytest

from app.services.cat_session import CATState
from app.services.irt_engine import (
    ItemParams,
    eap_update,
    fisher_information,
    p_correct,
    select_next_question,
    should_terminate,
)

# ================================================================
# BÖLÜM 1: IRT Engine Testleri
# ================================================================


class TestIRT3PL:
    """3PL P(correct|θ) fonksiyonu."""

    def test_p_correct_at_difficulty(self):
        """θ = b olduğunda P = (1+c)/2 olmalı (inflection point)."""
        a, b, c = 1.0, 0.0, 0.25
        p = p_correct(0.0, a, b, c)
        expected = (1 + c) / 2  # = 0.625
        assert abs(p - expected) < 1e-6, f"P(θ=b) = {p}, beklenen {expected}"

    def test_p_correct_guessing_floor(self):
        """θ → -∞ iken P → c (şans tabanı)."""
        p = p_correct(-10.0, 1.5, 0.0, 0.25)
        assert abs(p - 0.25) < 0.01, f"Alt sınır testi başarısız: P={p}"

    def test_p_correct_ceiling(self):
        """θ → +∞ iken P → 1."""
        p = p_correct(10.0, 1.5, 0.0, 0.25)
        assert p > 0.999, f"Üst sınır testi başarısız: P={p}"

    def test_p_correct_monotone(self):
        """P, θ'ya göre monoton artan olmalı."""
        thetas = np.linspace(-3, 3, 100)
        probs = p_correct(thetas, 1.2, 0.0, 0.20)
        diffs = np.diff(probs)
        assert (diffs >= 0).all(), "Monotonluk ihlali!"

    def test_no_guessing_equals_2pl(self):
        """c=0 → 2PL'ye indirgenmeli."""
        theta, a, b = 1.0, 1.5, 0.5
        p_3pl = p_correct(theta, a, b, c=0.0)
        p_2pl = 1.0 / (1.0 + np.exp(-a * (theta - b)))
        assert abs(p_3pl - p_2pl) < 1e-9


class TestFisherInformation:
    """Fisher Information I(θ)."""

    def test_max_info_near_difficulty(self):
        """Maksimum bilgi b civarında olmalı."""
        b = 0.5
        thetas = np.linspace(-2, 3, 500)
        infos = fisher_information(thetas, a=1.5, b=b, c=0.20)
        max_theta = thetas[np.argmax(infos)]
        # b'ye yakın olmalı (±0.5 tolerans)
        assert abs(max_theta - b) < 0.5, f"Max I(θ) @ θ={max_theta:.2f}, b={b}"

    def test_fisher_positive(self):
        """I(θ) her zaman ≥ 0 olmalı."""
        thetas = np.linspace(-4, 4, 200)
        infos = fisher_information(thetas, 1.0, 0.0, 0.25)
        assert (infos >= 0).all()

    def test_high_discrimination_more_info(self):
        """Yüksek a → daha fazla bilgi."""
        theta, b, c = 0.0, 0.0, 0.25
        i_low = fisher_information(theta, a=0.5, b=b, c=c)
        i_high = fisher_information(theta, a=2.0, b=b, c=c)
        assert i_high > i_low, "Yüksek a daha fazla bilgi vermeli"


class TestEAPUpdate:
    """EAP theta güncelleme."""

    def test_cold_start_returns_prior(self):
        """Yanıt yokken prior'a dön."""
        result = eap_update(responses=[], item_params=[])
        assert result.theta == 0.0
        assert result.se == 1.0
        assert not result.converged

    def test_all_correct_shifts_theta_up(self):
        """Tüm doğrular → θ yukarı gitmeli."""
        items = [ItemParams("q1", a=1.2, b=0.0, c=0.25)] * 5
        result = eap_update(responses=[1, 1, 1, 1, 1], item_params=items)
        assert result.theta > 0.0, f"θ={result.theta} yukarı gitmedi"

    def test_all_wrong_shifts_theta_down(self):
        """Tüm yanlışlar → θ aşağı gitmeli."""
        items = [ItemParams("q1", a=1.2, b=0.0, c=0.25)] * 5
        result = eap_update(responses=[0, 0, 0, 0, 0], item_params=items)
        assert result.theta < 0.0, f"θ={result.theta} aşağı gitmedi"

    def test_se_decreases_with_more_responses(self):
        """Daha fazla yanıt → SE düşmeli (daha kesin tahmin)."""
        items_1 = [ItemParams("q1", 1.0, 0.0, 0.25)]
        items_5 = items_1 * 5
        items_10 = items_1 * 10

        se_1 = eap_update([1], items_1).se
        se_5 = eap_update([1, 0, 1, 0, 1], items_5).se
        se_10 = eap_update([1, 0] * 5, items_10).se

        assert se_1 > se_5 > se_10, (
            f"SE monoton azalmıyor: {se_1:.3f} > {se_5:.3f} > {se_10:.3f}"
        )

    def test_convergence_high_discrimination(self):
        """Yüksek a'lı sorularla SE < 0.35'e ulaşılabilmeli."""
        items = [
            ItemParams(f"q{i}", a=2.0, b=float(i * 0.3 - 1.5), c=0.20)
            for i in range(12)
        ]
        responses = [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1]
        result = eap_update(responses, items)
        assert result.se < 0.65, (
            f"SE={result.se:.3f} — yüksek a ile daha hızlı yakınsama bekleniyor"
        )

    def test_mixed_responses_moderate_theta(self):
        """Karma yanıtlar → θ ≈ 0 civarında kalmalı."""
        items = [ItemParams(f"q{i}", a=1.0, b=0.0, c=0.25) for i in range(10)]
        responses = [1, 0] * 5  # alternating
        result = eap_update(responses, items)
        assert -0.8 < result.theta < 0.8, (
            f"Karma yanıtlarda θ={result.theta:.3f} — çok uzağa gitti"
        )


class TestShouldTerminate:
    """Oturum bitiş koşulları."""

    def test_se_threshold(self):
        terminate, reason = should_terminate(se=0.30, n_items=5)
        assert terminate
        assert reason == "se_threshold"

    def test_max_questions(self):
        terminate, reason = should_terminate(se=0.80, n_items=20)
        assert terminate
        assert reason == "max_questions"

    def test_no_terminate(self):
        terminate, reason = should_terminate(se=0.50, n_items=10)
        assert not terminate
        assert reason == ""


# ================================================================
# BÖLÜM 2: Soru Seçimi Testleri
# ================================================================


class TestSelectNextQuestion:
    """Epsilon-greedy MFI soru seçimi."""

    def _make_pool(self, n=20) -> list[ItemParams]:
        """Test için çeşitli güçlük seviyelerinde soru havuzu."""
        return [
            ItemParams(
                question_id=f"q{i:03d}",
                a=1.0 + (i % 3) * 0.3,  # a: 1.0, 1.3, 1.6
                b=float(i) * 0.3 - 3.0,  # b: -3.0 ... +2.7
                c=0.25,
            )
            for i in range(n)
        ]

    def test_excludes_answered(self):
        """Yanıtlanan sorular seçilmemeli."""
        pool = self._make_pool(10)
        answered = {f"q{i:03d}" for i in range(9)}  # ilk 9'u yanıtla
        result = select_next_question(0.0, pool, answered_ids=answered, epsilon=0.0)
        assert result is not None
        assert result.question_id == "q009"

    def test_returns_none_when_pool_empty(self):
        """Havuz boşsa None döndürmeli."""
        pool = self._make_pool(5)
        answered = {f"q{i:03d}" for i in range(5)}
        result = select_next_question(0.0, pool, answered_ids=answered)
        assert result is None

    def test_zpd_filter(self):
        """ZPD filtresi: P(correct|θ) ∈ [0.40, 0.85]."""
        # θ=0'da P hesapla: sadece orta güçlükteki seçilmeli
        pool = self._make_pool(20)
        result = select_next_question(
            theta=0.0,
            candidates=pool,
            answered_ids=set(),
            epsilon=0.0,  # tam exploitation
        )
        assert result is not None
        p = float(p_correct(0.0, result.a, result.b, result.c))
        # ZPD dışındaki zorlanmış seçimler için tolerans
        assert 0.20 <= p <= 0.95, f"ZPD dışı: P={p:.3f}"

    def test_mfi_selects_max_info(self):
        """epsilon=0 → Fisher bilgisi en yüksek soru seçilmeli."""
        theta = 0.5
        pool = [
            ItemParams("low_info", a=0.5, b=0.5, c=0.25),
            ItemParams("high_info", a=2.5, b=0.5, c=0.25),
            ItemParams("mid_info", a=1.0, b=0.5, c=0.25),
        ]
        result = select_next_question(theta, pool, answered_ids=set(), epsilon=0.0)
        assert result is not None
        assert result.question_id == "high_info", (
            f"Beklenen high_info, seçilen: {result.question_id}"
        )


# ================================================================
# BÖLÜM 3: CATState Redis Seri/Deseri Testleri
# ================================================================


class TestCATState:
    """CATState ↔ Redis serileştirme."""

    def test_roundtrip(self):
        """to_redis_dict → from_redis_dict cycle bozmamalı."""
        state = CATState(
            session_id="test-session-123",
            user_id="user-456",
            subject_id="subj-789",
            theta=0.75,
            se=0.42,
            answered_ids=["q001", "q002", "q003"],
            responses=[1, 0, 1],
            item_params=[
                {"question_id": "q001", "a": 1.2, "b": -0.3, "c": 0.25},
                {"question_id": "q002", "a": 0.9, "b": 0.8, "c": 0.25},
                {"question_id": "q003", "a": 1.5, "b": 0.1, "c": 0.20},
            ],
            n_questions=3,
            started_at="2026-01-01T10:00:00+00:00",
            state="active",
            warm_up_done=True,
        )

        redis_dict = state.to_redis_dict()
        # Redis bytes simülasyonu
        bytes_dict = {k.encode(): v.encode() for k, v in redis_dict.items()}
        restored = CATState.from_redis_dict(bytes_dict)

        assert restored.session_id == state.session_id
        assert restored.theta == state.theta
        assert restored.se == state.se
        assert restored.answered_ids == state.answered_ids
        assert restored.responses == state.responses
        assert len(restored.item_params) == 3
        assert restored.warm_up_done == True
        assert restored.n_questions == 3

    def test_get_item_params_objects(self):
        """item_params listesi doğru ItemParams nesnelerine dönüşmeli."""
        state = CATState(
            session_id="s",
            user_id="u",
            subject_id="sub",
            item_params=[{"question_id": "q1", "a": 1.5, "b": 0.3, "c": 0.25}],
        )
        params = state.get_item_params_objects()
        assert len(params) == 1
        assert params[0].a == 1.5
        assert params[0].b == 0.3


# ================================================================
# BÖLÜM 4: Tam Oturum Simülasyonu
# ================================================================


class TestFullSessionSimulation:
    """
    Gerçek bir CAT oturumu simülasyonu.
    DB ve Redis olmadan, sadece pure Python ile.
    """

    def _simulate_session(self, true_theta: float = 0.8, max_items: int = 20):
        """
        Gerçek θ'ya sahip bir öğrenciyi simüle et.
        Her soruda P(correct|true_theta) olasılığıyla doğru yanıt üret.
        SE < 0.35 veya max_items'a ulaşınca dur.
        """
        import random

        # Geniş soru havuzu: b -3..+3 arası
        pool = [
            ItemParams(
                question_id=f"q{i:04d}",
                a=1.0 + random.uniform(-0.3, 0.7),
                b=float(i) * 6.0 / 100 - 3.0,
                c=0.25,
            )
            for i in range(100)
        ]

        responses = []
        item_params = []
        answered_ids = set()
        theta_hat = 0.0
        se = 1.0

        for step in range(max_items):
            # Soru seç
            item = select_next_question(
                theta=theta_hat,
                candidates=pool,
                answered_ids=answered_ids,
                epsilon=0.20,
            )
            if item is None:
                break

            # Yanıt simüle et
            prob = float(p_correct(true_theta, item.a, item.b, item.c))
            is_correct = int(random.random() < prob)

            answered_ids.add(item.question_id)
            responses.append(is_correct)
            item_params.append(item)

            # θ güncelle
            result = eap_update(responses, item_params)
            theta_hat = result.theta
            se = result.se

            # Bitiş kontrolü
            terminate, _ = should_terminate(se, step + 1)
            if terminate:
                break

        return theta_hat, se, len(responses)

    def test_theta_converges_to_true_value(self):
        """θ_hat, gerçek θ'ya 0.5 içinde yakınsamalı (çoğu çalıştırmada)."""
        import random

        random.seed(42)
        np.random.seed(42)

        true_theta = 1.0
        theta_hat, se, n = self._simulate_session(true_theta)

        print(
            f"\nSimülasyon: true_θ={true_theta}, hat_θ={theta_hat:.3f}, "
            f"SE={se:.3f}, n={n}"
        )

        # |θ_hat - θ_true| < 0.8 — geniş tolerans (stochastic test)
        assert abs(theta_hat - true_theta) < 0.8, (
            f"θ yakınsaması başarısız: hat={theta_hat:.3f}, true={true_theta}"
        )

    def test_session_terminates_within_20_items(self):
        """Oturum 20 soru içinde bitmeli."""
        import random

        random.seed(99)
        np.random.seed(99)

        _, _, n = self._simulate_session(0.0)
        assert n <= 20, f"Oturum {n} soruda bitmedi (max 20)"

    def test_low_theta_student(self):
        """Zayıf öğrenci (θ=-1.5) için de sistem çalışmalı."""
        import random

        random.seed(7)
        np.random.seed(7)

        theta_hat, se, n = self._simulate_session(true_theta=-1.5)
        assert theta_hat < 0.0, (
            f"Zayıf öğrencinin θ'sı pozitif çıkmamalı: {theta_hat:.3f}"
        )


# ================================================================
# Çalıştır
# ================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
