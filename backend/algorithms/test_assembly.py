import math
import random
from typing import Any, ClassVar


class YksBellCurveAssembler:
    """
    Phase 8: Deneme Sınavı Kalibrasyonu (Test Assembly)
    Ensures that the generated exams adhere to the YKS normal distribution (Bell Curve):
    - 10% Very Easy (Çok Kolay)
    - 20% Easy (Kolay)
    - 40% Medium (Orta)
    - 20% Hard (Zor)
    - 10% Very Hard (Çok Zor)
    """

    # Target distribution ratios for YKS
    DISTRIBUTION_RATIOS: ClassVar[dict[str, float]] = {
        "cok_kolay": 0.10,
        "kolay": 0.20,
        "orta": 0.40,
        "zor": 0.20,
        "cok_zor": 0.10,
    }

    @classmethod
    def calculate_difficulty_distribution(cls, total_questions: int) -> dict[str, int]:
        """
        Calculates the exact number of questions needed per difficulty level for a given total.
        Handles rounding by distributing the remainder to the 'orta' (medium) category.
        """
        distribution = {}
        allocated = 0

        # Calculate initial floor allocations
        for diff, ratio in cls.DISTRIBUTION_RATIOS.items():
            count = math.floor(total_questions * ratio)
            distribution[diff] = count
            allocated += count

        # Allocate remainder to 'orta' to preserve the peak of the bell curve
        remainder = total_questions - allocated
        if remainder > 0:
            distribution["orta"] += remainder

        return distribution

    @staticmethod
    def _normalize_zorluk(question: dict[str, Any]) -> str:
        """'zorluk' degerini kanonik anahtara indirge.

        Enum olarak gelebilir ('SoruZorluk.KOLAY' -> 'kolay'); eksikse 'orta'.
        Iki cagri yerinde birebir tekrarlaniyordu.
        """
        diff = str(question.get("zorluk") or "orta").lower()
        return diff.split(".")[-1] if "." in diff else diff

    @classmethod
    def assemble_test(
        cls,
        question_pool: list[dict[str, Any]],
        total_questions: int,
        min_anchor_count: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Assembles a test from the available question pool matching the Bell Curve.
        Includes `min_anchor_count` anchor questions (if available) for equating.
        question_pool should be a list of dictionaries/objects containing at least a 'zorluk' key.
        If the pool lacks enough questions for a specific difficulty, it tries to fallback to adjacent difficulties.
        """
        target_distribution = cls.calculate_difficulty_distribution(total_questions)

        # Extract and shuffle anchor questions
        anchor_pool = [q for q in question_pool if q.get("is_anchor")]
        random.shuffle(anchor_pool)

        drawn_anchors = anchor_pool[:min_anchor_count]
        assembled_test = []
        assembled_test.extend(drawn_anchors)

        # Deduct drawn anchors from target distribution
        for q in drawn_anchors:
            diff = cls._normalize_zorluk(q)
            if diff in target_distribution and target_distribution[diff] > 0:
                target_distribution[diff] -= 1
            elif "orta" in target_distribution and target_distribution["orta"] > 0:
                target_distribution["orta"] -= 1

        # Group remaining questions by difficulty
        remaining_pool = [q for q in question_pool if q not in drawn_anchors]

        grouped_pool = {
            "cok_kolay": [],
            "kolay": [],
            "orta": [],
            "zor": [],
            "cok_zor": [],
        }

        for q in remaining_pool:
            diff = cls._normalize_zorluk(q)
            if diff in grouped_pool:
                grouped_pool[diff].append(q)
            else:
                grouped_pool["orta"].append(q)  # fallback to orta

        # Shuffle the pools to ensure randomness
        for diff in grouped_pool:
            random.shuffle(grouped_pool[diff])

        # Fallback hierarchy if a difficulty is missing
        fallback_map = {
            "cok_kolay": ["kolay", "orta"],
            "kolay": ["cok_kolay", "orta"],
            "orta": ["kolay", "zor"],
            "zor": ["orta", "cok_zor"],
            "cok_zor": ["zor", "orta"],
        }

        for diff, needed_count in target_distribution.items():
            current_diff_pool = grouped_pool[diff]

            # Draw as many as possible from the exact difficulty
            draw_count = min(needed_count, len(current_diff_pool))
            assembled_test.extend(current_diff_pool[:draw_count])

            # Remove drawn questions
            grouped_pool[diff] = current_diff_pool[draw_count:]

            missing = needed_count - draw_count

            # If still missing questions, use fallback difficulties
            if missing > 0:
                for fallback_diff in fallback_map[diff]:
                    if missing == 0:
                        break
                    fallback_pool = grouped_pool[fallback_diff]
                    f_draw = min(missing, len(fallback_pool))
                    assembled_test.extend(fallback_pool[:f_draw])
                    grouped_pool[fallback_diff] = fallback_pool[f_draw:]
                    missing -= f_draw

        # Final shuffle of the assembled test so difficulties aren't clustered
        random.shuffle(assembled_test)

        return assembled_test[:total_questions]
