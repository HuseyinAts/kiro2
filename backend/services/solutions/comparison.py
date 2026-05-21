"""
Solution Comparison Service - Extracted from alternative_solutions_service.py
Task 73.2: Enhanced Comparison

Author: KIRO2 Team
Date: 2025-01-24 (Refactored)
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SolutionComparisonMixin:
    """
    Mixin class for solution comparison functionality.
    
    Bu mixin, AlternativeSolutionsService tarafindan kullanilir.
    compare_solutions() ve ilgili yardimci metodlari icerir.
    """

    async def compare_solutions(
        self, question_id: str, solution_ids: list[str]
    ) -> dict[str, Any] | None:
        """Birden fazla cozumu karsilastir (TASK 73.2)"""
        try:
            solutions = await self.get_solutions(question_id)
            if not solutions:
                return None

            selected = [s for s in solutions if s.get("id") in solution_ids]
            if not selected:
                return None

            comparison = {
                "question_id": question_id,
                "solutions": [],
                "side_by_side": {},
                "summary": {},
            }

            for sol in selected:
                comparison["solutions"].append({
                    "id": sol.get("id"),
                    "title": sol.get("title"),
                    "difficulty": sol.get("difficulty"),
                    "estimated_time_seconds": sol.get("estimated_time_seconds"),
                    "step_count": len(sol.get("steps", [])),
                })

            return comparison
        except Exception as e:
            logger.error(f"Karsilastirma hatasi: {e}", exc_info=True)
            return None

    def _build_side_by_side_comparison(
        self, solutions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Yan yana karsilastirma tablosu"""
        return {
            "headers": [s["title"] for s in solutions],
            "metrics": {
                "Zorluk": [s["difficulty"] for s in solutions],
                "Sure": [s["estimated_time_seconds"] for s in solutions],
            },
        }
