"""
Service Dependencies for FastAPI Dependency Injection
======================================================
Centralized service factory functions for proper DI pattern.

This module provides factory functions for all services, enabling:
- Proper dependency injection in FastAPI endpoints
- Easy testing with mock services
- Clean separation of concerns

Usage:
    from core.service_dependencies import get_diary_service, get_exam_service

    @router.get("/summary")
    async def get_summary(service: DiaryService = Depends(get_diary_service)):
        return await service.get_summary()

Migration from Anti-Pattern:
    # BEFORE (Anti-pattern - direct instantiation)
    @router.get("/summary")
    async def get_summary(db: AsyncSession = Depends(get_db)):
        service = DiaryService(db)  # Hard to test!
        return await service.get_summary()

    # AFTER (Proper DI)
    @router.get("/summary")
    async def get_summary(service: DiaryService = Depends(get_diary_service)):
        return await service.get_summary()  # Easy to mock!
"""

from typing import TYPE_CHECKING

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db

if TYPE_CHECKING:
    # Type hints only - avoid circular imports
    from services.ai_chat_service import AIChatService
    from services.diary_service import DiaryService
    from services.exam_performance_service import ExamPerformanceService
    from services.learning_path_cache import LearningPathCacheService
    from services.question_bank_service import QuestionBankService
    from services.solutions import AlternativeSolutionsService  # Modular version
    from services.student_dashboard_service import StudentDashboardService
    from services.teacher_service import TeacherService
    from services.user_service import UserService
    from services.veli_service import VeliService
    from services.video_recommendation_service import VideoRecommendationService


# ============================================================================
# Core Services
# ============================================================================


def get_user_service(db: AsyncSession = Depends(get_db)) -> "UserService":
    """Get UserService instance for dependency injection."""
    from services.user_service import UserService

    return UserService(db)


def get_teacher_service(db: AsyncSession = Depends(get_db)) -> "TeacherService":
    """Get TeacherService instance for dependency injection."""
    from services.teacher_service import TeacherService

    return TeacherService(db)


def get_veli_service(db: AsyncSession = Depends(get_db)) -> "VeliService":
    """Get VeliService (Parent Service) instance for dependency injection."""
    from services.veli_service import VeliService

    return VeliService(db)


# ============================================================================
# Exam & Question Services
# ============================================================================


def get_question_bank_service(
    db: AsyncSession = Depends(get_db),
) -> "QuestionBankService":
    """Get QuestionBankService instance for dependency injection."""
    from services.question_bank_service import QuestionBankService

    return QuestionBankService(db)


def get_exam_performance_service(
    db: AsyncSession = Depends(get_db),
) -> "ExamPerformanceService":
    """Get ExamPerformanceService instance for dependency injection."""
    from services.exam_performance_service import ExamPerformanceService

    return ExamPerformanceService(db)


# ============================================================================
# Learning & Content Services
# ============================================================================


def get_learning_path_cache_service(
    db: AsyncSession = Depends(get_db),
) -> "LearningPathCacheService":
    """Get LearningPathCacheService instance for dependency injection."""
    from services.learning_path_cache import LearningPathCacheService

    return LearningPathCacheService(db)


def get_video_recommendation_service(
    db: AsyncSession = Depends(get_db),
) -> "VideoRecommendationService":
    """Get VideoRecommendationService instance for dependency injection."""
    from services.video_recommendation_service import VideoRecommendationService

    return VideoRecommendationService(db)


def get_alternative_solutions_service(
    db: AsyncSession = Depends(get_db),
) -> "AlternativeSolutionsService":
    """Get AlternativeSolutionsService instance for dependency injection."""
    from services.solutions import AlternativeSolutionsService

    return AlternativeSolutionsService(db)


# ============================================================================
# AI & Analytics Services
# ============================================================================


def get_ai_chat_service(db: AsyncSession = Depends(get_db)) -> "AIChatService":
    """Get AIChatService instance for dependency injection."""
    from services.ai_chat_service import AIChatService

    return AIChatService(db)


def get_student_dashboard_service(
    db: AsyncSession = Depends(get_db),
) -> "StudentDashboardService":
    """Get StudentDashboardService instance for dependency injection."""
    from services.student_dashboard_service import StudentDashboardService

    return StudentDashboardService(db)


# ============================================================================
# Diary & Personal Services
# ============================================================================


def get_diary_service(db: AsyncSession = Depends(get_db)) -> "DiaryService":
    """Get DiaryService instance for dependency injection."""
    from services.diary_service import DiaryService

    return DiaryService(db)


# ============================================================================
# Utility: Service Override for Testing
# ============================================================================


class ServiceOverrides:
    """
    Container for service overrides during testing.

    Usage in tests:
        from core.service_dependencies import service_overrides

        def test_endpoint(client):
            mock_service = MagicMock(spec=DiaryService)
            service_overrides.set(get_diary_service, mock_service)

            response = client.get("/api/diary/summary")

            service_overrides.clear()
    """

    _overrides: dict = {}

    @classmethod
    def set(cls, dependency_func, override_instance) -> None:
        """Set an override for a dependency function."""
        cls._overrides[dependency_func] = override_instance

    @classmethod
    def get(cls, dependency_func):
        """Get override if exists, otherwise None."""
        return cls._overrides.get(dependency_func)

    @classmethod
    def clear(cls) -> None:
        """Clear all overrides."""
        cls._overrides.clear()

    @classmethod
    def clear_specific(cls, dependency_func) -> None:
        """Clear a specific override."""
        cls._overrides.pop(dependency_func, None)


service_overrides = ServiceOverrides()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Core services
    "get_user_service",
    "get_teacher_service",
    "get_veli_service",
    # Exam services
    "get_question_bank_service",
    "get_exam_performance_service",
    # Learning services
    "get_learning_path_cache_service",
    "get_video_recommendation_service",
    "get_alternative_solutions_service",
    # AI services
    "get_ai_chat_service",
    "get_student_dashboard_service",
    # Diary services
    "get_diary_service",
    # Testing utilities
    "ServiceOverrides",
    "service_overrides",
]
