"""
IRT Psychometric Analysis Service
Task 57: IRT Parametreleri ve Psikometrik Analiz
Requirements: REQ-48.65-48.80

4 parametreli IRT model, ICC, TIF ve adaptive calibration implementasyonu.
"""

import logging
from dataclasses import dataclass

import matplotlib
import numpy as np
from scipy.optimize import minimize

matplotlib.use("Agg")  # Non-interactive backend
import base64
from io import BytesIO

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


@dataclass
class IRTParameters:
    """4 Parametreli IRT Model Parametreleri"""

    a: float  # Discrimination (ayırt edicilik) - 0 ile 2 arası
    b: float  # Difficulty (zorluk) - -3 ile +3 arası
    c: float  # Guessing (tahmin) - 0 ile 1 arası
    d: float  # Upper asymptote - 0 ile 1 arası

    def __post_init__(self):
        """Parametre sınırlarını kontrol et (REQ-48.65-48.68)"""
        self.a = np.clip(self.a, 0.0, 2.0)
        self.b = np.clip(self.b, -3.0, 3.0)
        self.c = np.clip(self.c, 0.0, 1.0)
        self.d = np.clip(self.d, 0.0, 1.0)


@dataclass
class CalibrationResult:
    """Kalibrasyon sonucu"""

    parameters: IRTParameters
    convergence: bool
    iterations: int
    log_likelihood: float
    standard_errors: dict[str, float]
    confidence_intervals: dict[str, tuple[float, float]]


@dataclass
class ICCAnalysis:
    """Item Characteristic Curve Analizi"""

    theta_range: np.ndarray
    probabilities: np.ndarray
    inflection_point: float
    optimal_difficulty_range: tuple[float, float]
    discrimination_quality: str
    plot_base64: str | None = None


@dataclass
class TIFAnalysis:
    """Test Information Function Analizi"""

    theta_range: np.ndarray
    information_values: np.ndarray
    max_information_theta: float
    max_information_value: float
    reliability_estimate: float
    standard_errors: np.ndarray
    plot_base64: str | None = None


class IRTPsychometricAnalysis:
    """
    IRT Psikometrik Analiz Servisi

    REQ-48.65-48.68: 4 parametreli IRT model implementasyonu
    REQ-48.69-48.72: Item Characteristic Curve (ICC)
    REQ-48.73-48.76: Test Information Function (TIF)
    REQ-48.77-48.80: Adaptive calibration
    """

    def __init__(self):
        """IRT Psychometric Analysis başlat."""
        self.convergence_criterion = 0.001  # REQ-48.68
        self.max_iterations = 100
        self.theta_range = np.linspace(-3, 3, 61)  # -3 ile +3 arası, 0.1 adımlarla

        logger.info("IRT Psychometric Analysis Service başlatıldı")

    # ==================== SUBTASK 57.1: 4 Parametreli IRT Model ====================

    def calculate_probability(self, theta: float, params: IRTParameters) -> float:
        """
        4PL IRT modelinde doğru cevap olasılığını hesapla.

        REQ-48.65: 4 parametreli IRT model
        P(θ) = c + (d - c) / (1 + exp(-a(θ - b)))

        Args:
            theta: Öğrenci yetenek seviyesi
            params: IRT parametreleri

        Returns:
            Doğru cevap olasılığı (0-1 arası)
        """
        a, b, c, d = params.a, params.b, params.c, params.d

        # 4PL formülü
        exponent = -a * (theta - b)
        probability = c + (d - c) / (1 + np.exp(exponent))

        return float(np.clip(probability, 0.0, 1.0))

    def estimate_parameters_mle(
        self,
        theta_values: np.ndarray,
        responses: np.ndarray,
        initial_params: IRTParameters | None = None,
    ) -> CalibrationResult:
        """
        Maximum Likelihood Estimation ile IRT parametrelerini tahmin et.

        REQ-48.66: Parameter estimation algorithms
        REQ-48.67: Maximum likelihood estimation
        REQ-48.68: Convergence kriteri %0.001

        Args:
            theta_values: Öğrenci yetenek seviyeleri
            responses: Doğru/yanlış yanıtlar (0/1)
            initial_params: Başlangıç parametreleri

        Returns:
            Kalibrasyon sonucu
        """
        if initial_params is None:
            initial_params = IRTParameters(a=1.0, b=0.0, c=0.25, d=1.0)

        # Başlangıç değerleri
        x0 = np.array(
            [initial_params.a, initial_params.b, initial_params.c, initial_params.d]
        )

        # Negatif log-likelihood fonksiyonu
        def neg_log_likelihood(params_array):
            a, b, c, d = params_array

            # Parametreleri sınırla
            a = np.clip(a, 0.01, 2.5)
            b = np.clip(b, -3.5, 3.5)
            c = np.clip(c, 0.0, 0.5)
            d = np.clip(d, 0.5, 1.0)

            # 4PL probability
            exponent = -a * (theta_values - b)
            prob = c + (d - c) / (1 + np.exp(exponent))

            # Numerical stability
            prob = np.clip(prob, 1e-10, 1 - 1e-10)

            # Log-likelihood
            ll = np.sum(responses * np.log(prob) + (1 - responses) * np.log(1 - prob))

            return -ll  # Minimize için negatif

        # Parametre sınırları (REQ-48.65-48.68)
        bounds = [
            (0.1, 2.0),  # a: discrimination
            (-3.0, 3.0),  # b: difficulty
            (0.0, 0.5),  # c: guessing
            (0.5, 1.0),  # d: upper asymptote
        ]

        # Newton-Raphson benzeri optimizasyon (REQ-48.67)
        result = minimize(
            neg_log_likelihood,
            x0,
            method="L-BFGS-B",
            bounds=bounds,
            options={
                "ftol": self.convergence_criterion,  # REQ-48.68
                "maxiter": self.max_iterations,
            },
        )

        # Sonuçları çıkar
        a_est, b_est, c_est, d_est = result.x
        estimated_params = IRTParameters(a=a_est, b=b_est, c=c_est, d=d_est)

        # Standard errors hesapla (Fisher Information Matrix'ten)
        standard_errors = self._calculate_standard_errors(
            theta_values, responses, estimated_params
        )

        # Confidence intervals hesapla (95%)
        confidence_intervals = {
            "a": (
                a_est - 1.96 * standard_errors["a"],
                a_est + 1.96 * standard_errors["a"],
            ),
            "b": (
                b_est - 1.96 * standard_errors["b"],
                b_est + 1.96 * standard_errors["b"],
            ),
            "c": (
                c_est - 1.96 * standard_errors["c"],
                c_est + 1.96 * standard_errors["c"],
            ),
            "d": (
                d_est - 1.96 * standard_errors["d"],
                d_est + 1.96 * standard_errors["d"],
            ),
        }

        calibration_result = CalibrationResult(
            parameters=estimated_params,
            convergence=result.success,
            iterations=result.nit,
            log_likelihood=-result.fun,
            standard_errors=standard_errors,
            confidence_intervals=confidence_intervals,
        )

        logger.info(
            f"MLE tamamlandı - Convergence: {result.success}, "
            f"Iterations: {result.nit}, "
            f"Params: a={a_est:.3f}, b={b_est:.3f}, c={c_est:.3f}, d={d_est:.3f}"
        )

        return calibration_result

    def _calculate_standard_errors(
        self, theta_values: np.ndarray, responses: np.ndarray, params: IRTParameters
    ) -> dict[str, float]:
        """
        Fisher Information Matrix'ten standard error'ları hesapla.

        Args:
            theta_values: Yetenek seviyeleri
            responses: Yanıtlar
            params: Tahmin edilen parametreler

        Returns:
            Her parametre için standard error
        """
        # Basitleştirilmiş hesaplama - gerçek implementasyonda Hessian matrix kullanılır
        n = len(theta_values)

        # Information matrix diagonal'ını tahmin et
        info_a = n * params.a / 4
        info_b = n / 4
        info_c = n / (params.c * (1 - params.c))
        info_d = n / (params.d * (1 - params.d))

        return {
            "a": float(1 / np.sqrt(max(info_a, 1e-6))),
            "b": float(1 / np.sqrt(max(info_b, 1e-6))),
            "c": float(1 / np.sqrt(max(info_c, 1e-6))),
            "d": float(1 / np.sqrt(max(info_d, 1e-6))),
        }

    # ==================== SUBTASK 57.2: Item Characteristic Curve (ICC) ====================

    def plot_icc(
        self, params: IRTParameters, title: str = "Item Characteristic Curve"
    ) -> ICCAnalysis:
        """
        Item Characteristic Curve çiz ve analiz et.

        REQ-48.69: ICC plotting theta (-3, +3) aralığında
        REQ-48.70: ICC curve analysis - inflection point
        REQ-48.71: Optimal difficulty range identification
        REQ-48.72: Soru ayırt ediciliğini değerlendirme

        Args:
            params: IRT parametreleri
            title: Grafik başlığı

        Returns:
            ICC analiz sonuçları
        """
        # Theta aralığında olasılıkları hesapla (REQ-48.69)
        probabilities = np.array(
            [self.calculate_probability(theta, params) for theta in self.theta_range]
        )

        # Inflection point hesapla (REQ-48.70)
        # 4PL modelde inflection point b parametresine yakındır
        inflection_point = params.b

        # Optimal difficulty range belirle (REQ-48.71)
        # Hedef öğrenci grubuna göre - burada orta seviye öğrenciler için
        target_theta_range = (-1.0, 1.0)
        optimal_difficulty_range = (
            params.b - 1.0 / params.a,
            params.b + 1.0 / params.a,
        )

        # Discrimination quality değerlendir (REQ-48.72)
        if params.a < 0.5:
            discrimination_quality = "Düşük"
        elif params.a < 1.0:
            discrimination_quality = "Orta"
        elif params.a < 1.5:
            discrimination_quality = "Yüksek"
        else:
            discrimination_quality = "Çok Yüksek"

        # Grafik oluştur
        plt.figure(figsize=(10, 6))
        plt.plot(self.theta_range, probabilities, "b-", linewidth=2, label="ICC")
        plt.axvline(
            x=inflection_point,
            color="r",
            linestyle="--",
            label=f"Inflection Point (b={inflection_point:.2f})",
        )
        plt.axhline(
            y=params.c, color="g", linestyle=":", label=f"Guessing (c={params.c:.2f})"
        )
        plt.axhline(
            y=params.d,
            color="m",
            linestyle=":",
            label=f"Upper Asymptote (d={params.d:.2f})",
        )

        plt.xlabel("Yetenek Seviyesi (θ)", fontsize=12)
        plt.ylabel("Doğru Cevap Olasılığı P(θ)", fontsize=12)
        plt.title(title, fontsize=14, fontweight="bold")
        plt.grid(True, alpha=0.3)
        plt.legend(loc="best")
        plt.xlim(-3, 3)
        plt.ylim(0, 1)

        # Grafik'i base64'e çevir
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        buffer.seek(0)
        plot_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        icc_analysis = ICCAnalysis(
            theta_range=self.theta_range,
            probabilities=probabilities,
            inflection_point=inflection_point,
            optimal_difficulty_range=optimal_difficulty_range,
            discrimination_quality=discrimination_quality,
            plot_base64=plot_base64,
        )

        logger.info(
            f"ICC analizi tamamlandı - Inflection: {inflection_point:.2f}, "
            f"Discrimination: {discrimination_quality}"
        )

        return icc_analysis

    # ==================== SUBTASK 57.3: Test Information Function (TIF) ====================

    def calculate_information(self, theta: float, params: IRTParameters) -> float:
        """
        Fisher Information hesapla.

        I(θ) = [P'(θ)]² / [P(θ)(1 - P(θ))]

        Args:
            theta: Yetenek seviyesi
            params: IRT parametreleri

        Returns:
            Information değeri
        """
        a, b, c, d = params.a, params.b, params.c, params.d

        # Probability
        exponent = -a * (theta - b)
        exp_term = np.exp(exponent)
        P = c + (d - c) / (1 + exp_term)

        # Derivative of P with respect to theta
        P_prime = a * (d - c) * exp_term / ((1 + exp_term) ** 2)

        # Information
        denominator = P * (1 - P)
        if denominator < 1e-10:  # Numerical stability
            return 0.0

        information = (P_prime**2) / denominator

        return float(information)

    def calculate_tif(
        self,
        items_params: list[IRTParameters],
        title: str = "Test Information Function",
    ) -> TIFAnalysis:
        """
        Test Information Function hesapla ve analiz et.

        REQ-48.73: TIF calculation - tüm soruların bilgi fonksiyonlarını toplama
        REQ-48.74: Information maximization - en bilgilendirici soruları seçme
        REQ-48.75: Test reliability estimation - Cronbach's Alpha
        REQ-48.76: Minimum 0.80 güvenilirlik hedefleme

        Args:
            items_params: Tüm soruların IRT parametreleri
            title: Grafik başlığı

        Returns:
            TIF analiz sonuçları
        """
        # Her theta değeri için toplam information hesapla (REQ-48.73)
        information_values = np.zeros_like(self.theta_range)

        for params in items_params:
            item_info = np.array(
                [
                    self.calculate_information(theta, params)
                    for theta in self.theta_range
                ]
            )
            information_values += item_info

        # Maximum information theta bul (REQ-48.74)
        max_info_idx = np.argmax(information_values)
        max_information_theta = self.theta_range[max_info_idx]
        max_information_value = information_values[max_info_idx]

        # Standard errors hesapla
        standard_errors = np.array(
            [1 / np.sqrt(info) if info > 0 else np.inf for info in information_values]
        )

        # Test reliability tahmin et (REQ-48.75)
        # Reliability = 1 - (1 / Information)
        # Ortalama information kullanarak genel güvenilirlik
        mean_information = np.mean(information_values[information_values > 0])
        reliability_estimate = (
            1 - (1 / mean_information) if mean_information > 1 else 0.0
        )
        reliability_estimate = max(0.0, min(1.0, reliability_estimate))

        # Grafik oluştur
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

        # TIF grafiği
        ax1.plot(self.theta_range, information_values, "b-", linewidth=2)
        ax1.axvline(
            x=max_information_theta,
            color="r",
            linestyle="--",
            label=f"Max Info at θ={max_information_theta:.2f}",
        )
        ax1.axhline(
            y=max_information_value,
            color="g",
            linestyle=":",
            label=f"Max Info={max_information_value:.2f}",
        )
        ax1.set_xlabel("Yetenek Seviyesi (θ)", fontsize=12)
        ax1.set_ylabel("Test Information I(θ)", fontsize=12)
        ax1.set_title(
            f"{title}\nReliability: {reliability_estimate:.3f}",
            fontsize=14,
            fontweight="bold",
        )
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="best")
        ax1.set_xlim(-3, 3)

        # Standard Error grafiği
        ax2.plot(self.theta_range, standard_errors, "r-", linewidth=2)
        ax2.axhline(y=0.3, color="g", linestyle="--", label="Target SE=0.3")
        ax2.set_xlabel("Yetenek Seviyesi (θ)", fontsize=12)
        ax2.set_ylabel("Standard Error SE(θ)", fontsize=12)
        ax2.set_title("Measurement Precision", fontsize=12, fontweight="bold")
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc="best")
        ax2.set_xlim(-3, 3)
        ax2.set_ylim(0, 1)

        plt.tight_layout()

        # Grafik'i base64'e çevir
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        buffer.seek(0)
        plot_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        tif_analysis = TIFAnalysis(
            theta_range=self.theta_range,
            information_values=information_values,
            max_information_theta=max_information_theta,
            max_information_value=max_information_value,
            reliability_estimate=reliability_estimate,
            standard_errors=standard_errors,
            plot_base64=plot_base64,
        )

        # Güvenilirlik kontrolü (REQ-48.76)
        if reliability_estimate < 0.80:
            logger.warning(
                f"Test güvenilirliği hedefin altında: {reliability_estimate:.3f} < 0.80"
            )
        else:
            logger.info(
                f"Test güvenilirliği hedefte: {reliability_estimate:.3f} >= 0.80"
            )

        logger.info(
            f"TIF analizi tamamlandı - Max Info: {max_information_value:.2f} "
            f"at θ={max_information_theta:.2f}, Reliability: {reliability_estimate:.3f}"
        )

        return tif_analysis

    # ==================== SUBTASK 57.4: Adaptive Calibration ====================

    def adaptive_calibration(
        self,
        question_id: str,
        current_params: IRTParameters,
        new_responses: list[dict[str, any]],
        min_sample_size: int = 200,
    ) -> CalibrationResult:
        """
        Online adaptive calibration - gerçek zamanlı parametre güncelleme.

        REQ-48.77: Online calibration algorithm
        REQ-48.78: Real-time parameter updates - her 100 yanıtta güncelleme
        REQ-48.79: Calibration sample size optimization - minimum 200 öğrenci
        REQ-48.80: Parametre güven aralıklarını hesaplama

        Args:
            question_id: Soru ID'si
            current_params: Mevcut IRT parametreleri
            new_responses: Yeni öğrenci yanıtları
            min_sample_size: Minimum örnek boyutu (REQ-48.79)

        Returns:
            Güncellenmiş kalibrasyon sonucu
        """
        # Sample size kontrolü (REQ-48.79)
        if len(new_responses) < min_sample_size:
            logger.warning(
                f"Yetersiz örnek boyutu: {len(new_responses)} < {min_sample_size}. "
                f"Mevcut parametreler korunuyor."
            )
            return CalibrationResult(
                parameters=current_params,
                convergence=False,
                iterations=0,
                log_likelihood=0.0,
                standard_errors={"a": 0.0, "b": 0.0, "c": 0.0, "d": 0.0},
                confidence_intervals={
                    "a": (current_params.a, current_params.a),
                    "b": (current_params.b, current_params.b),
                    "c": (current_params.c, current_params.c),
                    "d": (current_params.d, current_params.d),
                },
            )

        # Veriyi hazırla
        theta_values = np.array([r["student_ability"] for r in new_responses])
        responses = np.array([1 if r["is_correct"] else 0 for r in new_responses])

        # Online calibration (REQ-48.77, REQ-48.78)
        # Mevcut parametreleri başlangıç noktası olarak kullan
        updated_result = self.estimate_parameters_mle(
            theta_values=theta_values,
            responses=responses,
            initial_params=current_params,
        )

        # Parametre değişimini logla
        param_changes = {
            "a": abs(updated_result.parameters.a - current_params.a),
            "b": abs(updated_result.parameters.b - current_params.b),
            "c": abs(updated_result.parameters.c - current_params.c),
            "d": abs(updated_result.parameters.d - current_params.d),
        }

        logger.info(
            f"Adaptive calibration tamamlandı - Question: {question_id}, "
            f"Sample size: {len(new_responses)}, "
            f"Param changes: a={param_changes['a']:.4f}, b={param_changes['b']:.4f}"
        )

        # REQ-48.80: Güven aralıklarını hesapla
        logger.info(
            f"Confidence intervals (95%): "
            f"a={updated_result.confidence_intervals['a']}, "
            f"b={updated_result.confidence_intervals['b']}"
        )

        return updated_result

    def batch_adaptive_calibration(
        self, questions_data: list[dict[str, any]], update_threshold: int = 100
    ) -> dict[str, CalibrationResult]:
        """
        Toplu adaptive calibration - birden fazla soru için.

        REQ-48.78: Her 100 yanıtta parametreleri güncelleme

        Args:
            questions_data: Her soru için mevcut params ve yeni responses
            update_threshold: Güncelleme eşiği (varsayılan 100)

        Returns:
            Her soru için güncellenmiş kalibrasyon sonuçları
        """
        results = {}

        for question_data in questions_data:
            question_id = question_data["question_id"]
            current_params = question_data["current_params"]
            all_responses = question_data["responses"]

            # Her 100 yanıtta güncelleme yap (REQ-48.78)
            if len(all_responses) >= update_threshold:
                # Son 100+ yanıtı kullan
                recent_responses = all_responses[-update_threshold:]

                result = self.adaptive_calibration(
                    question_id=question_id,
                    current_params=current_params,
                    new_responses=recent_responses,
                    min_sample_size=update_threshold,
                )

                results[question_id] = result
            else:
                logger.debug(
                    f"Question {question_id}: {len(all_responses)} responses, "
                    f"waiting for {update_threshold}"
                )

        logger.info(
            f"Batch adaptive calibration tamamlandı - {len(results)} soru güncellendi"
        )

        return results

    def optimize_calibration_sample_size(
        self, target_se: float = 0.3, params: IRTParameters = None
    ) -> int:
        """
        Hedef standard error için optimal örnek boyutunu hesapla.

        REQ-48.79: Calibration sample size optimization

        Args:
            target_se: Hedef standard error
            params: IRT parametreleri (tahmin için)

        Returns:
            Optimal örnek boyutu
        """
        if params is None:
            params = IRTParameters(a=1.0, b=0.0, c=0.25, d=1.0)

        # Basitleştirilmiş hesaplama
        # SE ≈ 1 / sqrt(n * I(θ))
        # n ≈ (1 / (SE² * I(θ)))

        # Ortalama information tahmin et
        avg_theta = 0.0  # Orta seviye öğrenciler için
        avg_information = self.calculate_information(avg_theta, params)

        if avg_information < 1e-6:
            return 200  # Varsayılan minimum

        optimal_n = int(np.ceil(1 / (target_se**2 * avg_information)))

        # Minimum 200, maksimum 1000 sınırları
        optimal_n = max(200, min(1000, optimal_n))

        logger.info(
            f"Optimal sample size: {optimal_n} "
            f"(target SE={target_se}, avg info={avg_information:.3f})"
        )

        return optimal_n
