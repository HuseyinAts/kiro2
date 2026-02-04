"""
4-Parametreli IRT (Item Response Theory) Model Implementasyonu  
Adaptif Test Sistemi (CAT) icin temel IRT modeli

Turk Egitim Sistemi icin optimize edilmis:
- YKS/TYT/AYT standardizasyonu
- MEB mufredati alignment
- Kulturel adaptasyon faktorleri

Author: KIRO2 AI Team
Date: 2025-01
Version: 1.0.0
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
from scipy.optimize import minimize
from scipy.stats import norm
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class IRTItem:
    """IRT soru/item modeli"""
    item_id: str
    discrimination: float  # a parameter
    difficulty: float      # b parameter
    guessing: float        # c parameter  
    upper_asymptote: float = 1.0  # d parameter

    subject: str = ""
    topic: str = ""
    meb_grade_level: int = 9
    bloom_taxonomy: str = "knowledge"
    yks_question_type: str = "TYT"

    sample_size: int = 0
    calibration_date: Optional[datetime] = None
    se_a: float = 0.0
    se_b: float = 0.0


@dataclass  
class StudentAbility:
    """Ogrenci yetenek tahmini"""
    student_id: str
    ability: float
    se: float
    estimation_method: str
    n_items: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    yks_predicted_score: Optional[float] = None
    confidence_interval_95: Tuple[float, float] = (-3.0, 3.0)


@dataclass
class IRTResponse:
    """Ogrenci cevap kaydi"""
    student_id: str
    item_id: str
    response: int
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)


class FourParameterIRTModel:
    """4PL IRT Model: P(theta) = c + (d - c) / (1 + exp(-a(theta - b)))"""

    def __init__(self, scaling_constant: float = 1.0):
        self.D = scaling_constant
        self.items: Dict[str, IRTItem] = {}
        self.student_abilities: Dict[str, StudentAbility] = {}
        self.responses: List[IRTResponse] = []

    def probability(self, theta: float, item: IRTItem) -> float:
        a, b, c, d = item.discrimination, item.difficulty, item.guessing, item.upper_asymptote
        exponent = np.clip(-self.D * a * (theta - b), -20, 20)
        prob = c + (d - c) / (1 + np.exp(exponent))
        return np.clip(prob, 1e-10, 1 - 1e-10)

    def information(self, theta: float, item: IRTItem) -> float:
        a, b, c, d = item.discrimination, item.difficulty, item.guessing, item.upper_asymptote
        P = self.probability(theta, item)
        Q = 1 - P
        exp_val = np.exp(np.clip(-self.D * a * (theta - b), -20, 20))
        P_prime = (d - c) * self.D * a * exp_val / ((1 + exp_val) ** 2)
        return (P_prime ** 2) / (P * Q) if P * Q >= 1e-10 else 0.0

    def test_information(self, theta: float, items: List[IRTItem]) -> float:
        return sum(self.information(theta, item) for item in items)

    def standard_error(self, theta: float, items: List[IRTItem]) -> float:
        info = self.test_information(theta, items)
        return 1.0 / np.sqrt(info) if info >= 1e-10 else 999.0

    def estimate_ability_mle(
        self, responses: List[IRTResponse], initial_theta: float = 0.0,
        max_iterations: int = 50, convergence_threshold: float = 0.001
    ) -> StudentAbility:
        if not responses:
            return StudentAbility(
                student_id="unknown", ability=0.0, se=999.0, 
                estimation_method="MLE", n_items=0
            )

        theta = initial_theta
        for _ in range(max_iterations):
            items = [self.items[r.item_id] for r in responses if r.item_id in self.items]
            if not items:
                break

            first_deriv, second_deriv = 0.0, 0.0
            for response, item in zip(responses, items):
                P, Q = self.probability(theta, item), 1 - self.probability(theta, item)
                if P < 1e-10 or Q < 1e-10:
                    continue

                exp_val = np.exp(np.clip(-self.D * item.discrimination * (theta - item.difficulty), -20, 20))
                P_prime = (item.upper_asymptote - item.guessing) * self.D * item.discrimination * exp_val / ((1 + exp_val) ** 2)
                P_double_prime = -(item.upper_asymptote - item.guessing) * (self.D * item.discrimination) ** 2 * exp_val * (exp_val - 1) / ((1 + exp_val) ** 3)

                u = response.response
                first_deriv += (u - P) * P_prime / (P * Q)
                second_deriv += (P_prime ** 2 * (Q - P) - P * Q * P_double_prime) / (P * Q) ** 2

            if abs(second_deriv) < 1e-10:
                break

            theta_new = np.clip(theta - first_deriv / second_deriv, -4.0, 4.0)
            if abs(theta_new - theta) < convergence_threshold:
                theta = theta_new
                break
            theta = theta_new

        items_used = [self.items[r.item_id] for r in responses if r.item_id in self.items]
        se = self.standard_error(theta, items_used)
        return StudentAbility(
            student_id=responses[0].student_id, ability=theta, se=se,
            estimation_method="MLE", n_items=len(responses),
            yks_predicted_score=300 + theta * 66.67,
            confidence_interval_95=(theta - 1.96 * se, theta + 1.96 * se)
        )

    def select_next_item_cat(self, current_theta: float, available_items: List[IRTItem], answered_items: List[str]) -> Optional[IRTItem]:
        candidates = [i for i in available_items if i.item_id not in answered_items]
        return max(candidates, key=lambda i: self.information(current_theta, i)) if candidates else None


class TurkishIRTUtils:
    YKS_ITEM_DEFAULTS = {
        "TYT": {"discrimination_range": (0.8, 2.0), "difficulty_range": (-2.0, 2.0), "guessing": 0.25, "upper_asymptote": 0.97},
        "AYT-SAY": {"discrimination_range": (1.0, 2.5), "difficulty_range": (-1.5, 3.0), "guessing": 0.20, "upper_asymptote": 0.98}
    }
