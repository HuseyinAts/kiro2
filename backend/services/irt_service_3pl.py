"""
IRT 3PL (Three-Parameter Logistic) Model Servisi

FAZ-1 Gorev 1.2 — Master Plan v2.0
3PL model: ICC, Fisher bilgi, EAP theta, CAT soru secimi.

Not: Detayli 4PL + morfoloji servisi icin irt_service.py kullanin.
Bu dosya master plan'in gerektirdigi sade 3PL + CAT implementasyonu.
"""

from __future__ import annotations

import logging
import math

import numpy as np

logger = logging.getLogger(__name__)

# IRT parametre kisitlari
IRT_A_MIN, IRT_A_MAX = 0.2, 2.5  # ayirt edicilik
IRT_B_MIN, IRT_B_MAX = -3.0, 3.0  # zorluk
IRT_C_MIN, IRT_C_MAX = 0.0, 0.35  # rastgele tahmin (guessing)


class IRTService3PL:
    """
    3PL IRT model.
    Parametreler: a (ayirt edicilik), b (zorluk), c (guessing).
    """

    # ---------------------------------------------------------------------------
    # 1. ICC (Item Characteristic Curve)
    # ---------------------------------------------------------------------------

    @staticmethod
    def icc(theta: float, a: float, b: float, c: float) -> float:
        """
        3PL ICC: P(X=1|theta) = c + (1-c) / (1 + exp(-a*(theta - b)))

        Args:
            theta: Ogrenci yetenek parametresi [-4, 4]
            a: Ayirt edicilik [0.2, 2.5]
            b: Zorluk [-3, 3]
            c: Guessing [0, 0.35]

        Returns:
            Dogru cevap olasiligi [c, 1.0]
        """
        return c + (1 - c) / (1 + math.exp(-a * (theta - b)))

    # ---------------------------------------------------------------------------
    # 2. Fisher Bilgi Fonksiyonu
    # ---------------------------------------------------------------------------

    @staticmethod
    def information(theta: float, a: float, b: float, c: float) -> float:
        """
        Fisher bilgi fonksiyonu.
        I(theta) = a^2 * (P - c)^2 / ((1-c)^2 * P * Q)
        """
        P = IRTService3PL.icc(theta, a, b, c)
        Q = 1 - P
        if c >= P or Q <= 1e-10:
            return 0.0
        return a**2 * (P - c) ** 2 / ((1 - c) ** 2 * P * Q)

    # ---------------------------------------------------------------------------
    # 3. EAP Theta Tahmini
    # ---------------------------------------------------------------------------

    @staticmethod
    def eap_theta(
        answered_questions: list[dict],
        responses: list[bool],
        prior_mean: float = 0.0,
        prior_var: float = 1.0,
    ) -> tuple[float, float]:
        """
        Expected A Posteriori (EAP) theta tahmini.

        Args:
            answered_questions: [{"irt_a": float, "irt_b": float, "irt_c": float}, ...]
            responses: [True/False, ...] (dogru/yanlis)
            prior_mean: On bilgi ortalamasi (default 0.0)
            prior_var: On bilgi varyans (default 1.0)

        Returns:
            (theta_eap, theta_se)
        """
        if not answered_questions:
            return 0.0, 1.0

        quad_points = np.linspace(-4, 4, 41)

        # Log prior (normal dagilim)
        log_prior = -0.5 * ((quad_points - prior_mean) ** 2 / prior_var)

        # Log likelihood
        log_likelihood = np.zeros(41)
        for q, r in zip(answered_questions, responses):
            a = float(q.get("irt_a", 1.0))
            b = float(q.get("irt_b", 0.0))
            c = float(q.get("irt_c", 0.20))
            for j, theta in enumerate(quad_points):
                p = max(1e-10, min(1 - 1e-10, IRTService3PL.icc(theta, a, b, c)))
                log_likelihood[j] += r * math.log(p) + (1 - r) * math.log(1 - p)

        log_posterior = log_prior + log_likelihood
        log_posterior -= log_posterior.max()  # numerik stabilite
        posterior = np.exp(log_posterior)
        posterior /= posterior.sum()

        theta_eap = float(np.sum(quad_points * posterior))
        theta_se = float(np.sqrt(np.sum((quad_points - theta_eap) ** 2 * posterior)))

        return round(theta_eap, 4), round(theta_se, 4)

    # ---------------------------------------------------------------------------
    # 4. CAT Soru Secimi
    # ---------------------------------------------------------------------------

    @staticmethod
    def select_next_question(
        theta: float,
        answered_ids: set[int],
        item_bank: list[dict],
    ) -> int | None:
        """
        CAT: Maksimum bilgi kriterine gore sonraki soruyu sec.

        Args:
            theta: Mevcut theta tahmini
            answered_ids: Zaten cevaplanmis soru ID'leri
            item_bank: [{"id": int, "irt_a": float, "irt_b": float, "irt_c": float}, ...]

        Returns:
            En yuksek bilgi degerine sahip soru ID'si veya None
        """
        best_id, best_info = None, -1.0

        for q in item_bank:
            if q["id"] in answered_ids:
                continue
            info = IRTService3PL.information(theta, q["irt_a"], q["irt_b"], q["irt_c"])
            if info > best_info:
                best_info, best_id = info, q["id"]

        return best_id

    # ---------------------------------------------------------------------------
    # Parametre dogrulama
    # ---------------------------------------------------------------------------

    @staticmethod
    def validate_params(a: float, b: float, c: float) -> bool:
        """IRT parametrelerinin gecerli aralikta olup olmadigini kontrol et."""
        return (
            IRT_A_MIN <= a <= IRT_A_MAX
            and IRT_B_MIN <= b <= IRT_B_MAX
            and IRT_C_MIN <= c <= IRT_C_MAX
        )
