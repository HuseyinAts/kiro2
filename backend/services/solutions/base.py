"""
Solutions Module - Base Classes and Utilities
==============================================
Shared functionality for alternative solutions service.

Part of the decomposition of alternative_solutions_service.py (2331 lines)
into modular components.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.question_bank import QuestionBankItem

logger = logging.getLogger(__name__)


class BaseSolutionService:
    """
    Base class for solution services.
    Provides common database operations and utilities.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def _get_question(self, question_id: str) -> Optional[QuestionBankItem]:
        """Get question by ID."""
        stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_solutions_data(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get solutions data from question."""
        question = await self._get_question(question_id)
        if not question:
            return None
        return question.alternative_solutions or {}

    async def _get_solutions_list(
        self, question_id: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get list of solutions for a question."""
        solutions_data = await self._get_solutions_data(question_id)
        if not solutions_data:
            return []

        solutions = solutions_data.get("solutions", [])

        if active_only:
            solutions = [s for s in solutions if s.get("is_active", True)]

        return solutions

    async def _update_solutions(
        self, question_id: str, solutions_data: Dict[str, Any]
    ) -> bool:
        """Update solutions data for a question."""
        try:
            question = await self._get_question(question_id)
            if not question:
                return False

            question.alternative_solutions = solutions_data
            question.updated_at = datetime.now()

            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Solutions update error: {str(e)}")
            return False

    def _sort_solutions(
        self, solutions: List[Dict[str, Any]], sort_by: str = "difficulty"
    ) -> List[Dict[str, Any]]:
        """
        Sort solutions by criteria.

        Args:
            solutions: List of solutions
            sort_by: Sort criteria (difficulty, time, votes, popularity)

        Returns:
            Sorted list
        """
        difficulty_order = {"kolay": 1, "orta": 2, "zor": 3, "easy": 1, "medium": 2, "hard": 3}

        if sort_by == "difficulty":
            return sorted(
                solutions,
                key=lambda x: difficulty_order.get(x.get("difficulty", "orta"), 2),
            )
        elif sort_by == "time":
            return sorted(
                solutions,
                key=lambda x: x.get("estimated_time_seconds", 999999),
            )
        elif sort_by == "votes":
            return sorted(
                solutions,
                key=lambda x: x.get("votes", {}).get("total", 0),
                reverse=True,
            )
        elif sort_by == "popularity":
            return sorted(
                solutions, key=lambda x: x.get("usage_count", 0), reverse=True
            )
        else:
            return solutions

    def _filter_solutions(
        self,
        solutions: List[Dict[str, Any]],
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filter solutions by category and/or difficulty."""
        result = solutions

        if category:
            result = [s for s in result if s.get("category") == category]

        if difficulty:
            result = [s for s in result if s.get("difficulty") == difficulty]

        return result


# Difficulty mapping for consistent ordering
DIFFICULTY_ORDER = {
    "kolay": 1,
    "orta": 2,
    "zor": 3,
    "easy": 1,
    "medium": 2,
    "hard": 3,
}

# Solution categories
SOLUTION_CATEGORIES = [
    "standard",
    "shortcut",
    "visual",
    "algebraic",
    "geometric",
    "logical",
    "creative",
]
