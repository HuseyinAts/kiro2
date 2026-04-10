"""
Task 106: AI Chat Assistant Service

Service layer for enhanced chat with image upload, OCR, and step-by-step solutions
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ai_chat import (
    ChatAnalytics,
    ChatMessage,
    ChatSession,
    ImageProcessingStatus,
    ImageUpload,
    MessageRole,
    SessionStatus,
    SolutionStep,
    SubjectType,
)


class AIChatService:
    """Service for AI chat operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Task 106.1: Enhanced Chat Sessions
    # ============================================================

    async def create_session(
        self,
        user_id: UUID,
        title: str | None = None,
        subject_type: SubjectType = SubjectType.GENERAL,
        **kwargs,
    ) -> ChatSession:
        """Create a new chat session"""
        # chat_sessions.user_id is VARCHAR; asyncpg rejects UUID objects.
        session = ChatSession(
            user_id=str(user_id),
            title=title or "New Chat",
            subject_type=subject_type,
            **kwargs,
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: UUID) -> ChatSession | None:
        """Get a chat session"""
        query = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self, user_id: UUID, status: SessionStatus | None = None, limit: int = 50
    ) -> list[ChatSession]:
        """Get user's chat sessions"""
        conditions = [ChatSession.user_id == user_id]

        if status:
            conditions.append(ChatSession.status == status)

        query = (
            select(ChatSession)
            .where(and_(*conditions))
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_session(self, session_id: UUID, **updates) -> ChatSession | None:
        """Update a chat session"""
        session = await self.get_session(session_id)
        if not session:
            return None

        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a chat session"""
        session = await self.get_session(session_id)
        if not session:
            return False

        await self.db.delete(session)
        await self.db.commit()
        return True

    # ============================================================
    # Task 106.1: Chat Messages
    # ============================================================

    async def add_message(
        self,
        session_id: UUID,
        role: MessageRole,
        content: str,
        image_id: UUID | None = None,
        **kwargs,
    ) -> ChatMessage:
        """Add a message to the chat session"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            image_id=image_id,
            **kwargs,
        )

        self.db.add(message)

        # Update session
        session = await self.get_session(session_id)
        if session:
            session.message_count += 1
            session.last_message_at = datetime.now(UTC)
            if kwargs.get("tokens_used"):
                session.total_tokens += kwargs["tokens_used"]
            if kwargs.get("cost"):
                session.total_cost += kwargs["cost"]

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(
        self, session_id: UUID, limit: int | None = None
    ) -> list[ChatMessage]:
        """Get messages for a session"""
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_conversation_context(
        self, session_id: UUID, max_messages: int = 10
    ) -> list[dict[str, str]]:
        """Get conversation context for AI (last N messages)"""
        messages = await self.get_messages(session_id)

        # Get last N messages
        recent_messages = (
            messages[-max_messages:] if len(messages) > max_messages else messages
        )

        # Format for AI
        context = []
        for msg in recent_messages:
            context.append({"role": msg.role.value, "content": msg.content})

        return context

    async def rate_message(
        self,
        message_id: UUID,
        rating: int,
        is_helpful: bool,
        feedback_comment: str | None = None,
    ) -> ChatMessage | None:
        """Rate a message"""
        query = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            return None

        message.user_rating = rating
        message.is_helpful = is_helpful
        message.feedback_comment = feedback_comment

        await self.db.commit()
        await self.db.refresh(message)
        return message

    # ============================================================
    # Task 106.2: Image Upload
    # ============================================================

    async def create_image_upload(
        self, session_id: UUID, user_id: UUID, filename: str, file_path: str, **kwargs
    ) -> ImageUpload:
        """Create an image upload record"""
        image = ImageUpload(
            session_id=session_id,
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            **kwargs,
        )

        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def get_image_upload(self, image_id: UUID) -> ImageUpload | None:
        """Get an image upload"""
        query = select(ImageUpload).where(ImageUpload.id == image_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_session_images(self, session_id: UUID) -> list[ImageUpload]:
        """Get all images for a session"""
        query = (
            select(ImageUpload)
            .where(ImageUpload.session_id == session_id)
            .order_by(ImageUpload.created_at)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============================================================
    # Task 106.3: OCR Processing
    # ============================================================

    async def update_ocr_results(
        self, image_id: UUID, ocr_text: str, ocr_confidence: float, **kwargs
    ) -> ImageUpload | None:
        """Update OCR processing results"""
        image = await self.get_image_upload(image_id)
        if not image:
            return None

        image.processing_status = ImageProcessingStatus.COMPLETED
        image.ocr_text = ocr_text
        image.ocr_confidence = ocr_confidence
        image.processed_at = datetime.now(UTC)

        # Update optional fields
        for key, value in kwargs.items():
            if hasattr(image, key):
                setattr(image, key, value)

        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def mark_ocr_failed(
        self, image_id: UUID, error_message: str
    ) -> ImageUpload | None:
        """Mark OCR processing as failed"""
        image = await self.get_image_upload(image_id)
        if not image:
            return None

        image.processing_status = ImageProcessingStatus.FAILED
        image.error_message = error_message
        image.processed_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(image)
        return image

    # ============================================================
    # Task 106.4: Solution Steps
    # ============================================================

    async def add_solution_steps(
        self, message_id: UUID, steps: list[dict[str, Any]]
    ) -> list[SolutionStep]:
        """Add step-by-step solution to a message"""
        solution_steps = []

        for step_data in steps:
            step = SolutionStep(message_id=message_id, **step_data)
            self.db.add(step)
            solution_steps.append(step)

        await self.db.commit()

        for step in solution_steps:
            await self.db.refresh(step)

        return solution_steps

    async def get_solution_steps(self, message_id: UUID) -> list[SolutionStep]:
        """Get solution steps for a message"""
        query = (
            select(SolutionStep)
            .where(SolutionStep.message_id == message_id)
            .order_by(SolutionStep.step_number)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============================================================
    # Enhanced AI Response Generation
    # ============================================================

    async def generate_ai_response(
        self, session_id: UUID, user_message: str, image_text: str | None = None
    ) -> dict[str, Any]:
        """
        Generate AI response with enhanced context

        This is a placeholder - in production, this would call
        OpenAI API or other LLM service
        """
        # Get conversation context
        context = await self.get_conversation_context(session_id)

        # Get session details for subject context
        session = await self.get_session(session_id)

        # Build prompt
        system_prompt = self._build_system_prompt(
            session.subject_type if session else SubjectType.GENERAL
        )

        # Add image text if available
        full_message = user_message
        if image_text:
            full_message = f"[Image contains: {image_text}]\n\n{user_message}"

        # In production, call OpenAI API here
        # For now, return a mock response
        response = {
            "content": "This is a placeholder AI response. In production, this would call the OpenAI API.",
            "model": "gpt-4",
            "tokens_used": 150,
            "cost": 0.003,
            "response_time_ms": 1200,
            "confidence_score": 0.85,
            "relevance_score": 0.90,
        }

        return response

    def _build_system_prompt(self, subject_type: SubjectType) -> str:
        """Build system prompt based on subject"""
        prompts = {
            SubjectType.MATHEMATICS: "You are an expert mathematics tutor. Provide clear, step-by-step solutions with explanations.",
            SubjectType.PHYSICS: "You are an expert physics tutor. Explain concepts clearly with real-world examples.",
            SubjectType.CHEMISTRY: "You are an expert chemistry tutor. Break down chemical concepts and reactions clearly.",
            SubjectType.BIOLOGY: "You are an expert biology tutor. Explain biological concepts with clarity and accuracy.",
            SubjectType.TURKISH: "You are an expert Turkish language tutor. Help with grammar, literature, and writing.",
            SubjectType.HISTORY: "You are an expert history tutor. Provide context and connections between historical events.",
            SubjectType.GEOGRAPHY: "You are an expert geography tutor. Explain geographical concepts and relationships.",
            SubjectType.ENGLISH: "You are an expert English language tutor. Help with grammar, vocabulary, and comprehension.",
            SubjectType.GENERAL: "You are a helpful educational assistant. Provide clear and accurate answers.",
        }

        return prompts.get(subject_type, prompts[SubjectType.GENERAL])

    async def generate_step_by_step_solution(
        self, problem: str, subject_type: SubjectType
    ) -> list[dict[str, Any]]:
        """
        Generate step-by-step solution

        In production, this would use AI to break down the problem
        """
        # Mock solution steps
        steps = [
            {
                "step_number": 1,
                "title": "Understand the problem",
                "content": "Identify what is being asked and what information is given.",
                "step_type": "explanation",
            },
            {
                "step_number": 2,
                "title": "Set up the equation",
                "content": "Write down the relevant formula or equation.",
                "step_type": "formula",
                "latex_formula": "E = mc^2",
            },
            {
                "step_number": 3,
                "title": "Solve",
                "content": "Perform the calculations step by step.",
                "step_type": "calculation",
            },
            {
                "step_number": 4,
                "title": "Verify the answer",
                "content": "Check if the answer makes sense in the context of the problem.",
                "step_type": "conclusion",
            },
        ]

        return steps

    # ============================================================
    # Analytics
    # ============================================================

    async def get_chat_statistics(self, user_id: UUID) -> dict[str, Any]:
        """Get chat statistics for a user"""
        # Get total sessions
        session_query = select(func.count(ChatSession.id)).where(
            ChatSession.user_id == user_id
        )
        session_result = await self.db.execute(session_query)
        total_sessions = session_result.scalar()

        # Get total messages
        message_query = (
            select(func.count(ChatMessage.id))
            .join(ChatSession)
            .where(ChatSession.user_id == user_id)
        )
        message_result = await self.db.execute(message_query)
        total_messages = message_result.scalar()

        # Get total images
        image_query = select(func.count(ImageUpload.id)).where(
            ImageUpload.user_id == user_id
        )
        image_result = await self.db.execute(image_query)
        total_images = image_result.scalar()

        # Get subject distribution
        subject_query = (
            select(ChatSession.subject_type, func.count(ChatSession.id))
            .where(ChatSession.user_id == user_id)
            .group_by(ChatSession.subject_type)
        )
        subject_result = await self.db.execute(subject_query)
        subject_rows = subject_result.all()

        subject_distribution = {row[0].value: row[1] for row in subject_rows}

        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_images": total_images,
            "subject_distribution": subject_distribution,
        }

    async def generate_chat_analytics(
        self, user_id: UUID, date: datetime, period_type: str = "daily"
    ) -> ChatAnalytics:
        """Generate chat analytics for a period"""
        # Calculate statistics for the period
        # This is a simplified version - in production, would filter by date range

        stats = await self.get_chat_statistics(user_id)

        analytics = ChatAnalytics(
            user_id=user_id,
            date=date,
            period_type=period_type,
            total_sessions=stats["total_sessions"],
            total_messages=stats["total_messages"],
            total_images=stats["total_images"],
            subject_distribution=stats["subject_distribution"],
        )

        self.db.add(analytics)
        await self.db.commit()
        await self.db.refresh(analytics)
        return analytics
