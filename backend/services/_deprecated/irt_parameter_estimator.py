"""
IRT Parameter Estimator
Task 53.4: IRT parametre tahmin modeli
Requirements: REQ-48.13-48.16

4 parametreli IRT modeli ile soru parametrelerini tahmin eder.
"""

import logging

import numpy as np
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class IRTParameterEstimator:
    """
    4 Parametreli IRT Model

    REQ-48.13: 4 parametreli IRT model kullanımı
    REQ-48.14: Difficulty (b) parametresi -3 ile +3 arası
    REQ-48.15: Discrimination (a) parametresi 0 ile 2 arası
    REQ-48.16: Guessing (c) ve upper asymptote (d) parametreleri 0 ile 1 arası
    """

    def __init__(self):
        """IRT Parameter Estimator başlat."""
        self.calibrated_items = {}
        logger.info("IRTParameterEstimator başlatıldı")

    def estimate_parameters(
        self, question_id: str, student_responses: list[dict[str, any]]
    ) -> dict[str, float]:
        """
        Soru için IRT parametrelerini tahmin et.

        REQ-48.13: 4 parametreli IRT model
        REQ-48.14-48.16: Parametre aralıkları

        Args:
            question_id: Soru ID'si
            student_responses: [{'student_ability': theta, 'is_correct': bool}, ...]

        Returns:
            {'a': discrimination, 'b': difficulty, 'c': guessing, 'd': upper_asymptote}
        """
        if len(student_responses) < 30:
            logger.warning(
                f"Yetersiz veri: {len(student_responses)} yanıt (minimum 30 gerekli)"
            )
            return self._default_parameters()

        # Veriyi hazırla
        theta_values = np.array([r["student_ability"] for r in student_responses])
        responses = np.array([1 if r["is_correct"] else 0 for r in student_responses])

        # Parametreleri tahmin et
        params = self._estimate_4pl_parameters(theta_values, responses)

        # Parametreleri sınırla (REQ-48.14-48.16)
        params = self._constrain_parameters(params)

        # Kaydet
        self.calibrated_items[question_id] = params

        logger.info(f"IRT parametreleri tahmin edildi: {question_id} -> {params}")

        return params

    def _estimate_4pl_parameters(
        self, theta: np.ndarray, responses: np.ndarray
    ) -> dict[str, float]:
        """
        4PL IRT modelini fit et.

        4PL Model: P(θ) = c + (d - c) / (1 + exp(-a(θ - b)))

        Args:
            theta: Öğrenci yetenek seviyeleri
            responses: Doğru/yanlış yanıtlar (0/1)

        Returns:
            IRT parametreleri
        """
        # Başlangıç değerleri
        initial_params = [
            1.0,  # a (discrimination)
            0.0,  # b (difficulty)
            0.25,  # c (guessing)
            1.0,  # d (upper asymptote)
        ]

        # Negatif log-likelihood fonksiyonu
        def neg_log_likelihood(params):
            a, b, c, d = params

            # 4PL probability
            prob = c + (d - c) / (1 + np.exp(-a * (theta - b)))

            # Olasılıkları sınırla (numerical stability)
            prob = np.clip(prob, 1e-10, 1 - 1e-10)

            # Log-likelihood
            ll = np.sum(responses * np.log(prob) + (1 - responses) * np.log(1 - prob))

            return -ll  # Minimize etmek için negatif

        # Parametre sınırları
        bounds = [
            (0.1, 2.5),  # a: discrimination
            (-3.0, 3.0),  # b: difficulty
            (0.0, 0.5),  # c: guessing
            (0.5, 1.0),  # d: upper asymptote
        ]

        # Optimize et
        result = minimize(
            neg_log_likelihood, initial_params, method="L-BFGS-B", bounds=bounds
        )

        if not result.success:
            logger.warning(f"IRT optimization başarısız: {result.message}")
            return self._default_parameters()

        a, b, c, d = result.x

        return {
            "a": float(a),  # discrimination
            "b": float(b),  # difficulty
            "c": float(c),  # guessing
            "d": float(d),  # upper asymptote
        }

    def _constrain_parameters(self, params: dict[str, float]) -> dict[str, float]:
        """
        Parametreleri gereksinim aralıklarına sınırla.

        REQ-48.14: b parametresi -3 ile +3 arası
        REQ-48.15: a parametresi 0 ile 2 arası
        REQ-48.16: c ve d parametreleri 0 ile 1 arası
        """
        constrained = {
            "a": np.clip(params["a"], 0.0, 2.0),  # REQ-48.15
            "b": np.clip(params["b"], -3.0, 3.0),  # REQ-48.14
            "c": np.clip(params["c"], 0.0, 1.0),  # REQ-48.16
            "d": np.clip(params["d"], 0.0, 1.0),  # REQ-48.16
        }

        return constrained

    def _default_parameters(self) -> dict[str, float]:
        """
        Varsayılan IRT parametreleri.

        Returns:
            Orta zorlukta, orta ayırt edicilikte parametreler
        """
        return {
            "a": 1.0,  # Orta ayırt edicilik
            "b": 0.0,  # Orta zorluk
            "c": 0.25,  # %25 tahmin şansı (4 seçenekli soru)
            "d": 1.0,  # Tam doğru yapma olasılığı
        }

    def calculate_probability(self, theta: float, params: dict[str, float]) -> float:
        """
        Belirli yetenek seviyesinde soruyu doğru yapma olasılığını hesapla.

        4PL Model: P(θ) = c + (d - c) / (1 + exp(-a(θ - b)))

        Args:
            theta: Öğrenci yetenek seviyesi
            params: IRT parametreleri

        Returns:
            Doğru yapma olasılığı (0-1)
        """
        a = params["a"]
        b = params["b"]
        c = params["c"]
        d = params["d"]

        prob = c + (d - c) / (1 + np.exp(-a * (theta - b)))

        return float(prob)

    def calculate_information(self, theta: float, params: dict[str, float]) -> float:
        """
        Fisher Information hesapla.

        I(θ) = [P'(θ)]² / [P(θ)(1 - P(θ))]

        Args:
            theta: Yetenek seviyesi
            params: IRT parametreleri

        Returns:
            Information değeri
        """
        a = params["a"]
        b = params["b"]
        c = params["c"]
        d = params["d"]

        # Probability
        exp_term = np.exp(-a * (theta - b))
        P = c + (d - c) / (1 + exp_term)

        # Derivative of P
        P_prime = a * (d - c) * exp_term / ((1 + exp_term) ** 2)

        # Information
        if P * (1 - P) < 1e-10:  # Numerical stability
            return 0.0

        information = (P_prime**2) / (P * (1 - P))

        return float(information)

    def get_difficulty_category(self, b_param: float) -> str:
        """
        Zorluk parametresine göre kategori belirle.

        Args:
            b_param: Difficulty parametresi

        Returns:
            Zorluk kategorisi
        """
        if b_param < -1.5:
            return "çok kolay"
        if b_param < -0.5:
            return "kolay"
        if b_param < 0.5:
            return "orta"
        if b_param < 1.5:
            return "zor"
        return "çok zor"

    def get_discrimination_category(self, a_param: float) -> str:
        """
        Ayırt edicilik parametresine göre kategori belirle.

        Args:
            a_param: Discrimination parametresi

        Returns:
            Ayırt edicilik kategorisi
        """
        if a_param < 0.5:
            return "düşük ayırt edicilik"
        if a_param < 1.0:
            return "orta ayırt edicilik"
        if a_param < 1.5:
            return "yüksek ayırt edicilik"
        return "çok yüksek ayırt edicilik"

    def estimate_student_ability(self, responses: list[dict[str, any]]) -> float:
        """
        Öğrenci yetenek seviyesini (theta) tahmin et.

        Args:
            responses: [{'question_id': str, 'is_correct': bool, 'params': dict}, ...]

        Returns:
            Tahmin edilen theta değeri
        """
        if not responses:
            return 0.0  # Orta seviye

        # Maximum Likelihood Estimation
        def neg_log_likelihood(theta):
            ll = 0
            for response in responses:
                params = response["params"]
                is_correct = response["is_correct"]

                prob = self.calculate_probability(theta, params)
                prob = np.clip(prob, 1e-10, 1 - 1e-10)

                if is_correct:
                    ll += np.log(prob)
                else:
                    ll += np.log(1 - prob)

            return -ll

        # Optimize
        result = minimize(
            neg_log_likelihood,
            x0=[0.0],  # Başlangıç: orta seviye
            method="L-BFGS-B",
            bounds=[(-3.0, 3.0)],
        )

        return float(result.x[0])
