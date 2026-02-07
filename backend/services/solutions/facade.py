"""
Solutions Module - Facade
==========================
Backward-compatible facade for AlternativeSolutionsService.

This module provides the same interface as the original
alternative_solutions_service.py but delegates to modular components.

Usage:
    # Same as before
    from services.solutions import AlternativeSolutionsService

    service = AlternativeSolutionsService(db)
    result = await service.add_solution(question_id, data, user_id)
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .crud import SolutionCRUDService
from .voting import SolutionVotingService
from .comparison import SolutionComparisonService

logger = logging.getLogger(__name__)


class AlternativeSolutionsService:
    """
    Facade for alternative solutions services.

    This class maintains backward compatibility with the original
    2331-line monolithic service by delegating to specialized
    modular services.

    Components:
    - SolutionCRUDService: Create, Read, Update, Delete
    - SolutionVotingService: Voting and rating
    - SolutionComparisonService: Comparison and analysis
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._crud = SolutionCRUDService(db_session)
        self._voting = SolutionVotingService(db_session)
        self._comparison = SolutionComparisonService(db_session)

    # ========================================================================
    # CRUD Operations (delegated to SolutionCRUDService)
    # ========================================================================

    async def add_solution(
        self,
        question_id: str,
        solution_data: Dict[str, Any],
        created_by: str,
    ) -> Dict[str, Any]:
        """Add alternative solution to a question."""
        return await self._crud.add_solution(question_id, solution_data, created_by)

    async def get_solutions(
        self,
        question_id: str,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        sort_by: str = "difficulty",
    ) -> Optional[List[Dict[str, Any]]]:
        """Get alternative solutions for a question."""
        return await self._crud.get_solutions(question_id, category, difficulty, sort_by)

    async def get_solution_by_id(
        self, question_id: str, solution_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific solution by ID."""
        return await self._crud.get_solution_by_id(question_id, solution_id)

    async def update_solution(
        self,
        question_id: str,
        solution_id: str,
        update_data: Dict[str, Any],
        updated_by: str,
    ) -> bool:
        """Update a solution."""
        return await self._crud.update_solution(
            question_id, solution_id, update_data, updated_by
        )

    async def delete_solution(
        self, question_id: str, solution_id: str, deleted_by: str
    ) -> bool:
        """Delete a solution (soft delete)."""
        return await self._crud.delete_solution(question_id, solution_id, deleted_by)

    # ========================================================================
    # Voting Operations (delegated to SolutionVotingService)
    # ========================================================================

    async def vote_solution(
        self,
        question_id: str,
        solution_id: str,
        user_id: str,
        vote_type: str,
    ) -> Dict[str, Any]:
        """Vote on a solution."""
        return await self._voting.vote_solution(
            question_id, solution_id, user_id, vote_type
        )

    async def remove_vote(
        self,
        question_id: str,
        solution_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Remove a vote from a solution."""
        return await self._voting.remove_vote(question_id, solution_id, user_id)

    async def get_top_rated_solutions(
        self,
        question_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get top rated solutions."""
        return await self._voting.get_top_rated_solutions(question_id, limit)

    async def get_user_vote(
        self,
        question_id: str,
        solution_id: str,
        user_id: str,
    ) -> Optional[str]:
        """Get user's vote for a solution."""
        return await self._voting.get_user_vote(question_id, solution_id, user_id)

    # ========================================================================
    # Comparison Operations (delegated to SolutionComparisonService)
    # ========================================================================

    async def compare_solutions(
        self, question_id: str, solution_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Compare multiple solutions."""
        return await self._comparison.compare_solutions(question_id, solution_ids)

    async def get_fastest_solution(
        self, question_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the fastest solution for a question."""
        return await self._comparison.get_fastest_solution(question_id)

    async def get_easiest_solution(
        self, question_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the easiest solution for a question."""
        return await self._comparison.get_easiest_solution(question_id)

    async def get_statistics(
        self, question_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get statistics for solutions."""
        return await self._comparison.get_statistics(question_id)

    # ========================================================================
    # Utility Methods (from base)
    # ========================================================================

    def _sort_solutions(
        self, solutions: List[Dict[str, Any]], sort_by: str = "difficulty"
    ) -> List[Dict[str, Any]]:
        """Sort solutions by criteria."""
        return self._crud._sort_solutions(solutions, sort_by)


__all__ = ["AlternativeSolutionsService"]
