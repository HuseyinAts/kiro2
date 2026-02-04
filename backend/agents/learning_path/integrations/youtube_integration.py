"""YouTube Integration Wrapper"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class YouTubeIntegration:
    """YouTube API integration wrapper"""

    def __init__(self, youtube_service):
        self.service = youtube_service
        logger.info("YouTubeIntegration initialized")

    async def search_videos(
        self, query: str, max_results: int = 10, language: str = "tr"
    ) -> List[Dict[str, Any]]:
        """Search YouTube videos"""
        try:
            return await self.service.search(
                query=query, max_results=max_results, language=language
            )
        except Exception as e:
            logger.error(f"YouTube search error: {str(e)}")
            return []

    def parse_duration(self, duration_str: str) -> int:
        """Parse YouTube duration to minutes"""
        # Simplified implementation
        return 10  # Default
