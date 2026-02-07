"""Enhanced Chat API - AI sohbet sistemi."""
from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/v1/enhanced-chat", tags=["chat"])


# Module-level service references (for patching in tests)
turkish_nlp_service: Any = None
llm_service: Any = None


class ChatMessageType(str, Enum):
    """Chat message types."""

    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    SYSTEM = "system"
    ERROR = "error"


class ResponseMode(str, Enum):
    """AI response modes."""

    STANDARD = "standard"
    DETAILED = "detailed"
    SIMPLE = "simple"
    EXAM_MODE = "exam_mode"


class ChatContext(BaseModel):
    """Chat conversation context."""

    student_id: str = ""
    subject: str = ""
    topic: str = ""
    difficulty_level: float = 0.5
    session_id: str = ""
    history: list[dict[str, Any]] = Field(default_factory=list)


class EnhancedChatResponse(BaseModel):
    """Enhanced chat response with AI-generated content."""

    message: str = ""
    message_type: ChatMessageType = ChatMessageType.AI_RESPONSE
    confidence_score: float = 0.85
    suggestions: list[str] = Field(default_factory=list)
    context: Optional[ChatContext] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnhancedChatService:
    """AI-powered chat service for educational support."""

    def __init__(self) -> None:
        """Initialize chat service."""
        self.nlp_service = turkish_nlp_service
        self.llm = llm_service

    async def process_message(
        self,
        student_id: str,
        message: str,
        subject: str = "",
        context: Optional[ChatContext] = None,
        mode: ResponseMode = ResponseMode.STANDARD,
    ) -> EnhancedChatResponse:
        """
        Process a student message and generate AI response.

        Args:
            student_id: Student identifier
            message: User message text
            subject: Subject/topic area
            context: Conversation context
            mode: Response mode

        Returns:
            EnhancedChatResponse with AI-generated content
        """
        # Use module-level services (allows test mocking)
        llm = self.llm or llm_service

        response_text = ""
        if llm:
            result = llm.generate(message)
            if isinstance(result, dict) and result.get("success"):
                response_text = result.get("text", "")

        if not response_text:
            response_text = f"{subject} konusunda size yardımcı olabilirim."

        return EnhancedChatResponse(
            message=response_text,
            message_type=ChatMessageType.AI_RESPONSE,
            confidence_score=0.85,
            suggestions=[],
        )


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message."""

    student_id: str = Field(..., min_length=1, description="Student identifier")
    message: str = Field(..., min_length=1, description="Chat message text")
    subject: str = Field(default="", description="Subject/topic area")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    response_mode: Optional[str] = Field(default=None, description="Response mode")
    include_bionic: bool = Field(default=False, description="Include bionic reading")
    context_data: Optional[dict[str, Any]] = Field(default=None, description="Additional context")


@router.post("/message")
async def send_message(request: ChatMessageRequest) -> dict[str, Any]:
    """
    Send a chat message and get AI response.

    Args:
        request: Chat message request

    Returns:
        Chat response dictionary
    """
    service = EnhancedChatService()
    response = await service.process_message(
        student_id=request.student_id,
        message=request.message,
        subject=request.subject
    )
    return response.model_dump()


@router.get("/history/{student_id}")
async def get_history(student_id: str) -> dict[str, Any]:
    """
    Get chat history for a student.

    Args:
        student_id: Student identifier

    Returns:
        Chat history dictionary
    """
    return {"student_id": student_id, "messages": []}
