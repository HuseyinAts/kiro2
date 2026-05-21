"""
Solution Voting Service - Extracted from alternative_solutions_service.py
Task 73.4: Voting and Statistics

Author: KIRO2 Team
Date: 2025-01-24 (Refactored)
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SolutionVotingMixin:
    """
    Mixin class for solution voting and statistics.
    
    Bu mixin, AlternativeSolutionsService tarafindan kullanilir.
    vote_solution(), get_statistics() ve ilgili metodlari icerir.
    """

    async def vote_solution(
        self,
        question_id: str,
        solution_id: str,
        user_id: str,
        vote_type: str,  # 'upvote' or 'downvote'
    ) -> dict[str, Any] | None:
        """Cozume oy ver"""
        try:
            solutions = await self.get_solutions(question_id)
            if not solutions:
                return None

            solution = next(
                (s for s in solutions if s.get("id") == solution_id),
                None
            )

            if not solution:
                return None

            votes = solution.get("votes", {"upvotes": 0, "downvotes": 0, "total": 0})

            if vote_type == "upvote":
                votes["upvotes"] = votes.get("upvotes", 0) + 1
            else:
                votes["downvotes"] = votes.get("downvotes", 0) + 1

            votes["total"] = votes["upvotes"] - votes["downvotes"]

            return {
                "solution_id": solution_id,
                "votes": votes,
                "user_id": user_id,
                "vote_type": vote_type,
            }
        except Exception as e:
            logger.error(f"Oy verme hatasi: {e}", exc_info=True)
            return None

    async def get_statistics(
        self, question_id: str
    ) -> dict[str, Any] | None:
        """Cozum istatistiklerini getir"""
        try:
            solutions = await self.get_solutions(question_id)
            if not solutions:
                return None

            total_votes = sum(s.get("votes", {}).get("total", 0) for s in solutions)
            total_usage = sum(s.get("usage_count", 0) for s in solutions)

            return {
                "question_id": question_id,
                "solution_count": len(solutions),
                "total_votes": total_votes,
                "total_usage": total_usage,
                "average_difficulty": self._calculate_average_difficulty(solutions),
                "most_popular": self._get_most_popular(solutions),
                "difficulty_distribution": self._get_difficulty_distribution(solutions),
            }
        except Exception as e:
            logger.error(f"Istatistik hatasi: {e}", exc_info=True)
            return None

    def _calculate_average_difficulty(
        self, solutions: list[dict[str, Any]]
    ) -> float:
        """Ortalama zorlugu hesapla"""
        if not solutions:
            return 0.0

        total = sum(self._get_difficulty_score(s.get("difficulty")) for s in solutions)
        return total / len(solutions)

    def _get_most_popular(
        self, solutions: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """En populer cozumu getir"""
        if not solutions:
            return None

        most_popular = max(
            solutions,
            key=lambda x: x.get("votes", {}).get("total", 0)
        )

        return {
            "id": most_popular.get("id"),
            "title": most_popular.get("title"),
            "votes": most_popular.get("votes", {}).get("total", 0),
        }

    def _get_difficulty_distribution(
        self, solutions: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Zorluk dagilimini getir"""
        distribution = {"kolay": 0, "orta": 0, "zor": 0}

        for sol in solutions:
            difficulty = sol.get("difficulty", "orta").lower()
            if difficulty in distribution:
                distribution[difficulty] += 1

        return distribution

    async def get_top_rated_solutions(
        self, question_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """En yuksek puanli cozumleri getir"""
        try:
            solutions = await self.get_solutions(question_id)
            if not solutions:
                return []

            sorted_solutions = sorted(
                solutions,
                key=lambda x: x.get("votes", {}).get("total", 0),
                reverse=True
            )

            return sorted_solutions[:limit]
        except Exception as e:
            logger.error(f"Top rated hatasi: {e}", exc_info=True)
            return []
