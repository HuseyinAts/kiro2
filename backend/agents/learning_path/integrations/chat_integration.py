"""Chat Interface Integration Wrapper"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ChatIntegration:
    """Chat interface integration wrapper"""

    def __init__(self, chat_service):
        self.service = chat_service
        logger.info("ChatIntegration initialized")

    async def process_message(
        self, session_id: str, message: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process chat message"""
        try:
            return await self.service.process_message(
                session_id=session_id, message=message, context=context
            )
        except Exception as e:
            logger.error(f"Chat processing error: {str(e)}")
            return {"error": str(e)}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        try:
            return self.service.get_conversation_history(session_id)
        except Exception as e:
            logger.error(f"Get history error: {str(e)}")
            return []
