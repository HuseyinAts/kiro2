"""
Learning Path Router Registry

This module provides backward-compatible router registration for the Learning Path API.
It allows gradual migration from v1 (monolithic agent) to v2 (facade-based).

Usage in main.py:
    from api.learning_path_router import get_learning_path_routers

    for router in get_learning_path_routers():
        app.include_router(router)

Migration Path:
1. Phase 1 (Current): Both v1 and v2 routers active, v2 at /api/learning-path-v2
2. Phase 2: v2 router at /api/learning-path, v1 at /api/learning-path-legacy
3. Phase 3: Remove v1 router entirely
"""

import logging
from typing import List
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Feature flags for router selection
ENABLE_V1_ROUTER = True  # Legacy monolithic agent
ENABLE_V2_ROUTER = True  # New facade-based implementation


def get_learning_path_routers() -> List[APIRouter]:
    """
    Get list of active Learning Path routers.

    Returns both v1 and v2 routers for backward compatibility.
    V2 router is mounted at /api/learning-path-v2 during transition.

    Returns:
        List of FastAPI routers to include in the application.
    """
    routers = []

    if ENABLE_V1_ROUTER:
        try:
            from api.learning_path import router as v1_router
            routers.append(v1_router)
            logger.info("Learning Path v1 router enabled at /api/learning-path")
        except ImportError as e:
            logger.warning(f"Failed to load Learning Path v1 router: {e}")

    if ENABLE_V2_ROUTER:
        try:
            from api.learning_path_v2 import router as v2_router
            # During transition, mount at different prefix
            # Change v2_router.prefix to /api/learning-path when ready
            v2_router_prefixed = APIRouter(prefix="/api/learning-path-v2")

            # Re-register all routes from v2
            for route in v2_router.routes:
                # Preserve route attributes
                v2_router_prefixed.routes.append(route)

            routers.append(v2_router)  # Use v2 as-is with its original prefix
            logger.info("Learning Path v2 router enabled at /api/learning-path")
        except ImportError as e:
            logger.warning(f"Failed to load Learning Path v2 router: {e}")

    return routers


def get_primary_router() -> APIRouter:
    """
    Get the primary (preferred) Learning Path router.

    Returns v2 (facade-based) router if available, falls back to v1.

    Returns:
        Primary APIRouter instance.
    """
    if ENABLE_V2_ROUTER:
        try:
            from api.learning_path_v2 import router
            return router
        except ImportError:
            pass

    if ENABLE_V1_ROUTER:
        try:
            from api.learning_path import router
            return router
        except ImportError:
            pass

    raise ImportError("No Learning Path router available")


# Export for direct import
__all__ = [
    "get_learning_path_routers",
    "get_primary_router",
    "ENABLE_V1_ROUTER",
    "ENABLE_V2_ROUTER",
]
