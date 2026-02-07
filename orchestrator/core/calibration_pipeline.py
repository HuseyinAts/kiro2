"""Content Calibration Pipeline - IRT parametre kalibrasyonu.

Öğrenci yanıtlarından IRT parametrelerini otomatik kalibre eder:
- Minimum N yanıt toplama kontrolü
- MLE ile parametre tahmini
- Parametre sınır doğrulama
- Kalite bayrakları ve expert review kuyruğu
- Kalibrasyon geçmişi takibi
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class CalibrationStatus(Enum):
    """Kalibrasyon durumları."""

    PENDING = "pending"             # Yeterli yanıt bekleniyor
    CALIBRATING = "calibrating"     # Kalibrasyon devam ediyor
    CALIBRATED = "calibrated"       # Başarıyla kalibre edildi
    FLAGGED = "flagged"             # Expert review gerekli
    FAILED = "failed"               # Kalibrasyon başarısız


class CalibrationFlag(Enum):
    """Kalibrasyon uyarı bayrakları."""

    LOW_DISCRIMINATION = "low_discrimination"       # a < 0.5
    EXTREME_DIFFICULTY = "extreme_difficulty"        # |b| > 3.0
    HIGH_GUESSING = "high_guessing"                 # c > 0.3
    LOW_RESPONSE_COUNT = "low_response_count"       # N < min_responses
    POOR_FIT = "poor_fit"                           # Chi-square kötü
    NEGATIVE_DISCRIMINATION = "negative_discrimination"  # a < 0


@dataclass
class ResponseData:
    """Bir soruya verilen yanıt verisi."""

    student_theta: float      # Yanıtlayan öğrencinin theta değeri
    is_correct: bool
    response_time_seconds: float = 0.0


@dataclass
class CalibrationResult:
    """Kalibrasyon sonucu."""

    question_id: str
    status: CalibrationStatus = CalibrationStatus.PENDING
    difficulty: float = 0.0       # b
    discrimination: float = 1.0   # a
    guessing: float = 0.2         # c
    response_count: int = 0
    flags: list[CalibrationFlag] = field(default_factory=list)
    fit_statistic: float = 0.0    # Chi-square fit
    calibrated_at: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "status": self.status.value,
            "params": {
                "difficulty": round(self.difficulty, 4),
                "discrimination": round(self.discrimination, 4),
                "guessing": round(self.guessing, 4),
            },
            "response_count": self.response_count,
            "flags": [f.value for f in self.flags],
            "fit_statistic": round(self.fit_statistic, 4),
            "calibrated_at": self.calibrated_at,
            "message": self.message,
        }


@dataclass
class CalibrationConfig:
    """Kalibrasyon konfigürasyonu."""

    min_responses: int = 30            # Minimum yanıt sayısı
    ideal_responses: int = 100         # İdeal yanıt sayısı
    max_iterations: int = 50           # MLE iterasyon limiti
    convergence_threshold: float = 0.001

    # Parametre sınırları
    min_discrimination: float = 0.2
    max_discrimination: float = 4.0
    min_difficulty: float = -4.0
    max_difficulty: float = 4.0
    max_guessing: float = 0.35

    # Flag eşikleri
    flag_low_discrimination: float = 0.5
    flag_extreme_difficulty: float = 3.0
    flag_high_guessing: float = 0.3

    # Depolama
    storage_path: Path = field(default_factory=lambda: Path(".claude/calibration"))


@dataclass
class CalibrationPipeline:
    """IRT parametre kalibrasyon pipeline'ı.

    Yeterli yanıt toplandığında MLE ile IRT parametrelerini
    kalibre eder ve kalite kontrolü yapar.

    Example:
        >>> pipeline = CalibrationPipeline()
        >>> responses = [ResponseData(theta=0.5, is_correct=True), ...]
        >>> result = pipeline.calibrate("Q001", responses)
    """

    config: CalibrationConfig = field(default_factory=CalibrationConfig)

    def calibrate(
        self, question_id: str, responses: list[ResponseData],
    ) -> CalibrationResult:
        """Bir soru için IRT kalibrasyonu çalıştır.

        Args:
            question_id: Soru ID'si.
            responses: Öğrenci yanıtları.

        Returns:
            CalibrationResult with estimated parameters.
        """
        result = CalibrationResult(question_id=question_id, response_count=len(responses))

        # 1. Yeterli yanıt var mı?
        if len(responses) < self.config.min_responses:
            result.status = CalibrationStatus.PENDING
            result.flags.append(CalibrationFlag.LOW_RESPONSE_COUNT)
            result.message = f"Yetersiz yanıt: {len(responses)}/{self.config.min_responses}"
            return result

        result.status = CalibrationStatus.CALIBRATING

        # 2. MLE ile parametre tahmini
        try:
            b, a, c = self._estimate_parameters(responses)
        except ValueError as e:
            result.status = CalibrationStatus.FAILED
            result.message = f"Tahmin hatası: {e}"
            return result

        result.difficulty = b
        result.discrimination = a
        result.guessing = c

        # 3. Parametre doğrulama ve clipping
        result.discrimination = max(
            self.config.min_discrimination,
            min(self.config.max_discrimination, a),
        )
        result.difficulty = max(
            self.config.min_difficulty,
            min(self.config.max_difficulty, b),
        )
        result.guessing = max(0.0, min(self.config.max_guessing, c))

        # 4. Fit istatistiği
        result.fit_statistic = self._calculate_fit(responses, result)

        # 5. Flag kontrolü
        self._check_flags(result)

        # 6. Final durum
        if result.flags:
            result.status = CalibrationStatus.FLAGGED
            result.message = f"Expert review gerekli: {[f.value for f in result.flags]}"
        else:
            result.status = CalibrationStatus.CALIBRATED
            result.message = "Kalibrasyon başarılı"

        result.calibrated_at = datetime.now(timezone.utc).isoformat()
        return result

    def _estimate_parameters(
        self, responses: list[ResponseData],
    ) -> tuple[float, float, float]:
        """MLE ile b, a, c parametrelerini tahmin et.

        Basitleştirilmiş Joint MLE:
        - c sabit tutulur (proportion correct / 5)
        - b ve a iteratif güncellenir
        """
        n = len(responses)
        correct_rate = sum(1 for r in responses if r.is_correct) / n

        # c tahmini: çok düşük thetalardan gelen doğru cevap oranı
        low_theta = sorted(responses, key=lambda r: r.student_theta)[:max(n // 5, 1)]
        c = sum(1 for r in low_theta if r.is_correct) / len(low_theta)
        c = min(c, self.config.max_guessing)

        # b başlangıç tahmini: ortalama theta (doğru ve yanlışlar arası)
        correct_thetas = [r.student_theta for r in responses if r.is_correct]
        wrong_thetas = [r.student_theta for r in responses if not r.is_correct]

        if correct_thetas and wrong_thetas:
            b = (sum(wrong_thetas) / len(wrong_thetas) + sum(correct_thetas) / len(correct_thetas)) / 2
        else:
            b = sum(r.student_theta for r in responses) / n

        # a tahmini: point-biserial correlation bazlı
        a = 1.0  # Default
        D = 1.7

        for _ in range(self.config.max_iterations):
            # E-step: beklenen değerler
            gradient_b = 0.0
            gradient_a = 0.0
            hessian_b = 0.0

            for r in responses:
                exp_val = math.exp(D * a * (r.student_theta - b))
                p = c + (1 - c) * (exp_val / (1 + exp_val))
                p = max(min(p, 0.999), 0.001)

                u = 1.0 if r.is_correct else 0.0
                gradient_b += -D * a * (u - p) * (p - c) / (1 - c)
                gradient_a += D * (r.student_theta - b) * (u - p) * (p - c) / (1 - c)
                hessian_b += (D * a) ** 2 * p * (1 - p) * ((p - c) / (1 - c)) ** 2

            # M-step: güncelle
            if abs(hessian_b) > 1e-10:
                b_new = b - gradient_b / hessian_b
                if abs(b_new - b) < self.config.convergence_threshold:
                    b = b_new
                    break
                b = max(self.config.min_difficulty, min(self.config.max_difficulty, b_new))

            # a güncelleme (basit gradient)
            a = max(self.config.min_discrimination, min(self.config.max_discrimination, a + 0.01 * gradient_a))

        return b, a, c

    def _calculate_fit(
        self, responses: list[ResponseData], result: CalibrationResult,
    ) -> float:
        """Chi-square fit istatistiği hesapla."""
        D = 1.7
        chi_sq = 0.0

        for r in responses:
            exp_val = math.exp(
                D * result.discrimination * (r.student_theta - result.difficulty)
            )
            p = result.guessing + (1 - result.guessing) * (exp_val / (1 + exp_val))
            p = max(min(p, 0.999), 0.001)

            observed = 1.0 if r.is_correct else 0.0
            chi_sq += (observed - p) ** 2 / (p * (1 - p))

        return chi_sq / max(len(responses) - 3, 1)  # df = N - params

    def _check_flags(self, result: CalibrationResult) -> None:
        """Kalite bayraklarını kontrol et."""
        if result.discrimination < self.config.flag_low_discrimination:
            result.flags.append(CalibrationFlag.LOW_DISCRIMINATION)
        if result.discrimination < 0:
            result.flags.append(CalibrationFlag.NEGATIVE_DISCRIMINATION)
        if abs(result.difficulty) > self.config.flag_extreme_difficulty:
            result.flags.append(CalibrationFlag.EXTREME_DIFFICULTY)
        if result.guessing > self.config.flag_high_guessing:
            result.flags.append(CalibrationFlag.HIGH_GUESSING)
        if result.fit_statistic > 3.0:
            result.flags.append(CalibrationFlag.POOR_FIT)
