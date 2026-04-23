"""Khan Academy Integration Wrapper"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class KhanIntegration:
    """Khan Academy API integration wrapper"""

    def __init__(self, khan_service):
        self.service = khan_service
        logger.info("KhanIntegration initialized")

    async def search_content(
        self, query: str, subjects: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Search Khan Academy content"""
        try:
            return await self.service.search(query=query, subjects=subjects)
        except Exception as e:
            logger.error(f"Khan Academy search error: {e!s}")
            return []
