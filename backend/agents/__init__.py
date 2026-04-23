"""
Centralized Agent Management with Singleton Pattern
Teknofest 2025 - Egitim Eylemci Projesi

Bu modul tum AI agent'lari yonetir ve singleton pattern ile
tek instance garantisi saglar.

P0 FIX: RAGSearchService entegrasyonu eklendi (2026-01-27)
P1 FIX: Thread safety, lru_cache/global conflict çözüldü (2026-02-03)
"""

import logging
import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .learning_path.core.rag_search import RAGSearchService
    from .learning_path_agent import LearningPathAgent

logger = logging.getLogger(__name__)

# Thread-safe singleton management
_lock = threading.RLock()
_learning_path_agent: Optional["LearningPathAgent"] = None
_rag_service: Optional["RAGSearchService"] = None


def _get_rag_service() -> Optional["RAGSearchService"]:
    """
    Get singleton RAGSearchService instance (thread-safe).

    Returns:
        RAGSearchService or None if initialization fails
    """
    global _rag_service
    if _rag_service is None:
        with _lock:
            if _rag_service is None:  # Double-check after lock
                try:
                    from .learning_path.core.rag_search import RAGSearchService
                    _rag_service = RAGSearchService()
                    logger.info("RAGSearchService initialized for Learning Path Agent")
                except Exception as e:
                    logger.warning(f"Failed to initialize RAGSearchService: {e}")
    return _rag_service


def get_learning_path_agent() -> "LearningPathAgent":
    """
    Get singleton Learning Path Agent instance (thread-safe).

    FastAPI Depends() compatible.

    Returns:
        LearningPathAgent: Singleton agent instance

    Example:
        ```python
        from agents import get_learning_path_agent
        from fastapi import Depends

        @router.post("/create-path")
        async def create_path(
            agent: LearningPathAgent = Depends(get_learning_path_agent)
        ):
            path = await agent.create_learning_path(...)
        ```
    """
    global _learning_path_agent
    if _learning_path_agent is None:
        with _lock:
            if _learning_path_agent is None:  # Double-check after lock
                logger.info("Initializing Learning Path Agent (singleton)")
                from .learning_path_agent import LearningPathAgent

                rag_service = _get_rag_service()
                _learning_path_agent = LearningPathAgent(rag_service=rag_service)
    return _learning_path_agent


def initialize_agents() -> dict:
    """
    Initialize all agents on application startup.

    Called from app_lifespan in core/application.py.
    Ensures agents are ready before handling requests.

    Returns:
        dict: Dictionary of initialized agents
    """
    logger.info("> Initializing AI agents...")

    agents = {"learning_path": get_learning_path_agent()}

    logger.info(f"Initialized {len(agents)} agent(s)")

    return agents


async def shutdown_agents() -> None:
    """
    Cleanup agents on application shutdown.

    Called from app_lifespan in core/application.py.
    Ensures graceful cleanup of resources.
    """
    global _learning_path_agent, _rag_service

    logger.info("Shutting down AI agents...")

    with _lock:
        if _rag_service is not None:
            if hasattr(_rag_service, "close"):
                try:
                    await _rag_service.close()
                except Exception as e:
                    logger.warning(f"RAG service close error: {e}")
            _rag_service = None
            logger.info("Cleaned up RAG Service")

        if _learning_path_agent is not None:
            _learning_path_agent = None
            logger.info("Cleaned up Learning Path Agent")

    logger.info("All agents shut down")


def __getattr__(name: str):
    """Lazy import for module-level names."""
    if name == "LearningPathAgent":
        from .learning_path_agent import LearningPathAgent
        return LearningPathAgent
    if name == "RAGSearchService":
        from .learning_path.core.rag_search import RAGSearchService
        return RAGSearchService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "LearningPathAgent",
    "get_learning_path_agent",
    "initialize_agents",
    "shutdown_agents",
]
