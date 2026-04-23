"""
Solutions Module - CRUD Operations
===================================
Create, Read, Update, Delete operations for alternative solutions.

Extracted from alternative_solutions_service.py (lines 36-316)
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseSolutionService

logger = logging.getLogger(__name__)


class SolutionCRUDService(BaseSolutionService):
    """
    CRUD operations for alternative solutions.
    Task 73.1: Multiple Solution Support
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)

    async def add_solution(
        self,
        question_id: str,
        solution_data: dict[str, Any],
        created_by: str,
    ) -> dict[str, Any]:
        """
        Add alternative solution to a question.

        Args:
            question_id: Question ID
            solution_data: Solution data
            created_by: Creator user ID

        Returns:
            Dict: Operation result with solution_id
        """
        try:
            question = await self._get_question(question_id)

            if not question:
                return {"success": False, "message": "Soru bulunamadı"}

            # Get existing solutions
            current_solutions = question.alternative_solutions or {}
            if not isinstance(current_solutions, dict):
                current_solutions = {}

            # Generate new solution ID
            solution_id = str(uuid.uuid4())

            # Create solution object
            new_solution = {
                "id": solution_id,
                "title": solution_data.get("title"),
                "category": solution_data.get("category"),
                "difficulty": solution_data.get("difficulty"),
                "estimated_time_seconds": solution_data.get("estimated_time_seconds"),
                "steps": solution_data.get("steps", []),
                "tips": solution_data.get("tips", []),
                "prerequisites": solution_data.get("prerequisites", []),
                "advantages": solution_data.get("advantages", []),
                "disadvantages": solution_data.get("disadvantages", []),
                "video_url": solution_data.get("video_url"),
                "created_by": created_by,
                "created_by_type": solution_data.get("created_by_type", "teacher"),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "votes": {"upvotes": 0, "downvotes": 0, "total": 0},
                "usage_count": 0,
                "is_active": True,
            }

            # Update solutions list
            if "solutions" not in current_solutions:
                current_solutions["solutions"] = []

            current_solutions["solutions"].append(new_solution)

            # Update database
            question.alternative_solutions = current_solutions
            question.updated_at = datetime.now()

            await self.db.commit()
            await self.db.refresh(question)

            logger.info(f"Alternative solution added: {solution_id} -> {question_id}")

            return {
                "success": True,
                "solution_id": solution_id,
                "message": "Çözüm başarıyla eklendi",
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Solution add error: {e!s}")
            raise

    async def get_solutions(
        self,
        question_id: str,
        category: str | None = None,
        difficulty: str | None = None,
        sort_by: str = "difficulty",
    ) -> list[dict[str, Any]] | None:
        """
        Get alternative solutions for a question.

        Args:
            question_id: Question ID
            category: Category filter
            difficulty: Difficulty filter
            sort_by: Sort criteria

        Returns:
            List[Dict]: Solutions list
        """
        try:
            solutions = await self._get_solutions_list(question_id, active_only=True)

            if solutions is None:
                return None

            # Apply filters
            solutions = self._filter_solutions(solutions, category, difficulty)

            # Sort
            solutions = self._sort_solutions(solutions, sort_by)

            return solutions

        except Exception as e:
            logger.error(f"Solution get error: {e!s}")
            return []

    async def get_solution_by_id(
        self, question_id: str, solution_id: str
    ) -> dict[str, Any] | None:
        """
        Get a specific solution by ID.

        Args:
            question_id: Question ID
            solution_id: Solution ID

        Returns:
            Dict: Solution details
        """
        try:
            solutions = await self.get_solutions(question_id)

            if not solutions:
                return None

            for solution in solutions:
                if solution.get("id") == solution_id:
                    return solution

            return None

        except Exception as e:
            logger.error(f"Solution detail error: {e!s}")
            return None

    async def update_solution(
        self,
        question_id: str,
        solution_id: str,
        update_data: dict[str, Any],
        updated_by: str,
    ) -> bool:
        """
        Update a solution.

        Args:
            question_id: Question ID
            solution_id: Solution ID
            update_data: Data to update
            updated_by: Updater user ID

        Returns:
            bool: Success status
        """
        try:
            question = await self._get_question(question_id)

            if not question:
                return False

            # Get solutions
            solutions_data = question.alternative_solutions or {}
            solutions = solutions_data.get("solutions", [])

            # Find and update solution
            updated = False
            for solution in solutions:
                if solution.get("id") == solution_id:
                    for key, value in update_data.items():
                        solution[key] = value

                    solution["updated_at"] = datetime.now().isoformat()
                    solution["updated_by"] = updated_by
                    updated = True
                    break

            if not updated:
                return False

            # Update database
            solutions_data["solutions"] = solutions
            question.alternative_solutions = solutions_data
            question.updated_at = datetime.now()

            await self.db.commit()

            logger.info(f"Solution updated: {solution_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Solution update error: {e!s}")
            return False

    async def delete_solution(
        self, question_id: str, solution_id: str, deleted_by: str
    ) -> bool:
        """
        Delete a solution (soft delete).

        Args:
            question_id: Question ID
            solution_id: Solution ID
            deleted_by: Deleter user ID

        Returns:
            bool: Success status
        """
        try:
            question = await self._get_question(question_id)

            if not question:
                return False

            # Get solutions
            solutions_data = question.alternative_solutions or {}
            solutions = solutions_data.get("solutions", [])

            # Find and deactivate solution
            deleted = False
            for solution in solutions:
                if solution.get("id") == solution_id:
                    solution["is_active"] = False
                    solution["deleted_at"] = datetime.now().isoformat()
                    solution["deleted_by"] = deleted_by
                    deleted = True
                    break

            if not deleted:
                return False

            # Update database
            solutions_data["solutions"] = solutions
            question.alternative_solutions = solutions_data
            question.updated_at = datetime.now()

            await self.db.commit()

            logger.info(f"Solution deleted: {solution_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Solution delete error: {e!s}")
            return False


__all__ = ["SolutionCRUDService"]
