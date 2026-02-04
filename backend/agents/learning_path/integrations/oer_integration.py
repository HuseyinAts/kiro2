"""OER Integration Wrapper"""
import logging
from typing import List, Any, Optional

logger = logging.getLogger(__name__)


class OERIntegration:
    """Open Educational Resources integration wrapper"""

    def __init__(self, oer_service):
        self.service = oer_service
        logger.info("OERIntegration initialized")

    async def search_resources(
        self, query: str, subjects: Optional[List[str]] = None
    ) -> List[Any]:
        """Search OER resources"""
        try:
            return await self.service.search(query=query, subjects=subjects)
        except Exception as e:
            logger.error(f"OER search error: {str(e)}")
            return []
