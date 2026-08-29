"""
Empirical IRT Calibration Engine (Multi-Feature Domain-Informed Prior Derivation)

Calculates non-dummy, continuous 4PL IRT parameters (a, b, c, d) for questions based on:
1. Base Difficulty Level (VERY_EASY to VERY_HARD)
2. Bloom Taxonomy Level & Category
3. Subject & Exam Weights (AYT vs TYT vs LGS)
4. Text Length & LaTeX Formula Complexity
5. Option Count Awareness (5-option vs 4-option MCQ)
6. Deterministic Dithering for Continuous Parameter Distribution
"""

import hashlib
import re
from typing import Any

# Difficulty level base b parameter mapping
DIFFICULTY_B_MAP: dict[str, float] = {
    "VERY_EASY": -1.8,
    "EASY": -0.9,
    "MEDIUM": 0.0,
    "HARD": 0.9,
    "VERY_HARD": 1.8,
}

# Exam & Subject IRT b shifts (cognitive difficulty expectation)
EXAM_SUBJECT_SHIFTS: dict[str, float] = {
    "AYT_MAT": 0.40,
    "AYT_FIZ": 0.45,
    "AYT_KIM": 0.25,
    "AYT_BIO": 0.20,
    "AYT_EDEB": 0.15,
    "TYT_MAT": 0.10,
    "TYT_TUR": -0.15,
    "TYT_SOS": -0.20,
    "LGS_MAT": -0.30,
    "LGS_TUR": -0.40,
}

# Bloom Category Discrimination (a parameter) factors
BLOOM_A_MAP: dict[str, float] = {
    "KNOWLEDGE": 0.85,
    "COMPREHENSION": 1.00,
    "APPLICATION": 1.25,
    "ANALYSIS": 1.45,
    "EVALUATION": 1.65,
    "CREATION": 1.80,
}


class EmpiricalIRTCalibrator:
    """
    Domain-Informed IRT Parameter Calibration Engine.
    Converts question metadata & content features into continuous 4PL IRT parameters.
    """

    @staticmethod
    def _deterministic_dither(question_id: str, scale: float = 0.25) -> float:
        """Derives a deterministic pseudo-random float in [-scale, +scale] from question_id."""
        if not question_id:
            return 0.0
        digest = hashlib.md5(
            question_id.encode("utf-8"), usedforsecurity=False
        ).hexdigest()
        val = int(digest[:8], 16) / 0xFFFFFFFF  # [0, 1]
        return (val - 0.5) * 2.0 * scale

    @classmethod
    def calibrate_item(cls, item_data: dict[str, Any]) -> dict[str, float]:
        """
        Derives continuous 4PL IRT parameters (irt_a, irt_b, irt_c, irt_d) for a question.

        item_data fields accepted:
        - id: str
        - difficulty_level: str ("VERY_EASY", "EASY", "MEDIUM", "HARD", "VERY_HARD")
        - bloom_level: int (1..6)
        - bloom_category: str
        - question_text: str
        - option_e: str or None
        - subject: str or None
        - exam_type: str or None
        """
        qid = str(item_data.get("id") or "")
        diff_str = str(item_data.get("difficulty_level") or "MEDIUM").upper()
        bloom_lvl = item_data.get("bloom_level")
        bloom_cat = str(item_data.get("bloom_category") or "COMPREHENSION").upper()
        qtext = str(item_data.get("question_text") or "")
        has_option_e = bool(item_data.get("option_e"))
        subject = str(item_data.get("subject") or "").upper()
        exam_type = str(item_data.get("exam_type") or "").upper()

        # ---------------------------------------------------------------------
        # 1. Difficulty (b parameter) Calculation
        # ---------------------------------------------------------------------
        b_base = DIFFICULTY_B_MAP.get(diff_str, 0.0)

        # Bloom step adjustment: (bloom_level - 3) * 0.15
        b_bloom = 0.0
        if isinstance(bloom_lvl, int | float) and 1 <= bloom_lvl <= 6:
            b_bloom = (float(bloom_lvl) - 3.0) * 0.15

        # Exam & Subject shift
        exam_subj_key = f"{exam_type}_{subject[:3]}" if exam_type and subject else ""
        b_exam = EXAM_SUBJECT_SHIFTS.get(
            exam_subj_key, EXAM_SUBJECT_SHIFTS.get(exam_type, 0.0)
        )

        # Text & LaTeX Complexity shift
        latex_count = len(re.findall(r"\\\(|\$|\\[a-zA-Z]+", qtext))
        text_length = len(qtext.strip())
        b_complexity = min(0.35, (latex_count * 0.04) + (text_length / 1000.0) * 0.15)

        # Dither for continuous uniqueness
        b_dither = cls._deterministic_dither(qid, scale=0.20)

        b_final = b_base + b_bloom + b_exam + b_complexity + b_dither
        b_final = max(-3.5, min(3.5, b_final))

        # ---------------------------------------------------------------------
        # 2. Discrimination (a parameter) Calculation
        # ---------------------------------------------------------------------
        a_base = BLOOM_A_MAP.get(bloom_cat, 1.05)
        a_dither = cls._deterministic_dither(qid + "_a", scale=0.15)
        # Questions with formula density or moderate length have higher discrimination
        a_text_factor = 0.05 if latex_count > 0 or text_length > 150 else 0.0
        a_final = a_base + a_dither + a_text_factor
        a_final = max(0.4, min(2.5, a_final))

        # ---------------------------------------------------------------------
        # 3. Guessing (c parameter) Calculation
        # ---------------------------------------------------------------------
        # 5-option MCQ -> 0.20, 4-option MCQ -> 0.25
        c_final = 0.20 if has_option_e else 0.25
        c_dither = cls._deterministic_dither(qid + "_c", scale=0.02)
        c_final = max(0.05, min(0.30, c_final + c_dither))

        # ---------------------------------------------------------------------
        # 4. Upper Asymptote (d parameter) Calculation
        # ---------------------------------------------------------------------
        # Slip probability: high complexity items have d=0.96; simple items d=1.0
        d_final = 0.96 if (bloom_lvl and bloom_lvl >= 5) or latex_count > 3 else 1.0

        return {
            "irt_a": round(a_final, 4),
            "irt_b": round(b_final, 4),
            "irt_c": round(c_final, 4),
            "irt_d": round(d_final, 4),
            "irt_discrimination": round(a_final, 4),
            "irt_difficulty": round(b_final, 4),
            "irt_guessing": round(c_final, 4),
            "irt_upper_asymptote": round(d_final, 4),
        }
