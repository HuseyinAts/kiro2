"""OER Integration Wrapper"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class OERIntegration:
    """Open Educational Resources integration wrapper"""

    def __init__(self, oer_service):
        self.service = oer_service
        logger.info("OERIntegration initialized")

    async def search_resources(
        self, query: str, subjects: list[str] | None = None
    ) -> list[Any]:
        """Search OER resources"""
        try:
            return await self.service.search(query=query, subjects=subjects)
        except Exception as e:
            logger.error(f"OER search error: {e!s}")
            return []
