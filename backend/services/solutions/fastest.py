"""
Fastest Solution Analyzer - Extracted from alternative_solutions_service.py
Task 73.3: Fastest Solution Analysis

Author: KIRO2 Team
Date: 2025-01-24 (Refactored)
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FastestSolutionMixin:
    """
    Mixin class for fastest solution analysis.
    
    Bu mixin, AlternativeSolutionsService tarafindan kullanilir.
    get_fastest_solution() ve ilgili metodlari icerir.
    """

    async def get_fastest_solution(
        self, question_id: str
    ) -> dict[str, Any] | None:
        """En hizli cozumu getir (TASK 73.3)"""
        try:
            solutions = await self.get_solutions(question_id)
            if not solutions:
                return None

            # En hizli cozumu bul
            fastest = min(
                solutions,
                key=lambda x: x.get("estimated_time_seconds", float("inf"))
            )

            return {
                "solution": fastest,
                "time_saved": self._calculate_time_saved(solutions, fastest),
                "efficiency_ranking": self._rank_by_efficiency(solutions),
                "shortcuts": self._identify_shortcuts([fastest]),
            }
        except Exception as e:
            logger.error(f"En hizli cozum hatasi: {e}", exc_info=True)
            return None

    def _calculate_time_saved(
        self, solutions: list[dict], fastest: dict
    ) -> dict[str, Any]:
        """Kazanilan zamani hesapla"""
        if not solutions:
            return {}

        avg_time = sum(s.get("estimated_time_seconds", 0) for s in solutions) / len(solutions)
        fastest_time = fastest.get("estimated_time_seconds", 0)

        return {
            "average_time": avg_time,
            "fastest_time": fastest_time,
            "time_saved_seconds": avg_time - fastest_time,
            "percentage_faster": ((avg_time - fastest_time) / avg_time * 100) if avg_time > 0 else 0,
        }

    def _rank_by_efficiency(
        self, solutions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Verimlilige gore sirala"""
        def efficiency_score(sol):
            time = sol.get("estimated_time_seconds", 100)
            steps = len(sol.get("steps", []))
            return time + steps * 5  # Dusuk skor daha iyi

        sorted_solutions = sorted(solutions, key=efficiency_score)

        return [
            {
                "rank": i + 1,
                "solution_id": sol.get("id"),
                "title": sol.get("title"),
                "efficiency_score": efficiency_score(sol),
            }
            for i, sol in enumerate(sorted_solutions)
        ]

    def _identify_shortcuts(
        self, solutions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Kisayollari tanimla"""
        shortcuts = []

        for sol in solutions:
            steps = sol.get("steps", [])
            for step in steps:
                desc = step.get("description", "").lower()
                if any(word in desc for word in ["kisayol", "hizli", "pratik"]):
                    shortcuts.append({
                        "solution_id": sol.get("id"),
                        "step": step,
                    })

        return {
            "count": len(shortcuts),
            "shortcuts": shortcuts,
        }
