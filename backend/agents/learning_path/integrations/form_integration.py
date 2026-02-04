"""Form Interface Integration Wrapper"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FormIntegration:
    """Form interface integration wrapper"""

    def __init__(self, form_service):
        self.service = form_service
        logger.info("FormIntegration initialized")

    def get_form(self, form_type: str) -> Dict[str, Any]:
        """Get form definition"""
        try:
            return self.service.get_form(form_type=form_type)
        except Exception as e:
            logger.error(f"Get form error: {str(e)}")
            return {}

    async def submit_form(
        self, form_type: str, student_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit form data"""
        try:
            return await self.service.submit_form(
                form_type=form_type, student_id=student_id, form_data=data
            )
        except Exception as e:
            logger.error(f"Submit form error: {str(e)}")
            return {"error": str(e)}
