"""
Centralized Agent Management with Singleton Pattern
Teknofest 2025 - Eitim Eylemci Projesi

Bu modül tüm AI agent'lar1 yönetir ve singleton pattern ile
tek instance garantisi salar.
"""

import logging
from functools import lru_cache
from typing import Optional

from .learning_path_agent import LearningPathAgent

logger = logging.getLogger(__name__)

# Global instances (thread-safe lazy initialization)
_learning_path_agent: Optional[LearningPathAgent] = None


@lru_cache(maxsize=1)
def get_learning_path_agent() -> LearningPathAgent:
    """
    Get singleton Learning Path Agent instance

    Thread-safe singleton with lazy initialization.
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
        logger.info("Initializing Learning Path Agent (singleton)")
        _learning_path_agent = LearningPathAgent()
    return _learning_path_agent


def initialize_agents():
    """
    Initialize all agents on application startup

    Called from main.py lifespan event.
    Ensures agents are ready before handling requests.

    Returns:
        dict: Dictionary of initialized agents
    """
    logger.info("> Initializing AI agents...")

    agents = {"learning_path": get_learning_path_agent()}

    logger.info(f" Initialized {len(agents)} agent(s)")

    return agents


async def shutdown_agents():
    """
    Cleanup agents on application shutdown

    Called from main.py lifespan event.
    Ensures graceful cleanup of resources.
    """
    global _learning_path_agent

    logger.info("=Ñ Shutting down AI agents...")

    if _learning_path_agent:
        # Cleanup resources if needed
        logger.info("Cleaned up Learning Path Agent")
        _learning_path_agent = None

    # Clear lru_cache
    get_learning_path_agent.cache_clear()

    logger.info(" All agents shut down")


__all__ = [
    "LearningPathAgent",
    "get_learning_path_agent",
    "initialize_agents",
    "shutdown_agents",
]
