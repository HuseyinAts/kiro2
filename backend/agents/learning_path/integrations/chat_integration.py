"""Chat Interface Integration for Learning Path.

This module provides chat-based interaction with the learning path system,
enabling students to ask questions, check progress, and receive recommendations
through natural language.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ..config import get_learning_path_config

logger = logging.getLogger(__name__)


class ChatIntent(Enum):
    """Chat message intents."""

    ASK_QUESTION = "ask_question"
    REQUEST_HELP = "request_help"
    CHECK_PROGRESS = "check_progress"
    GET_RECOMMENDATION = "get_recommendation"
    MARK_COMPLETE = "mark_complete"
    CHANGE_TOPIC = "change_topic"
    UNKNOWN = "unknown"


@dataclass
class ChatMessage:
    """Chat message from student."""

    text: str
    student_id: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    """Chat response to student."""

    text: str
    intent: ChatIntent
    suggestions: List[str] = field(default_factory=list)
    resources: List[Any] = field(default_factory=list)  # List[LearningResource]
    actions: List[Dict[str, Any]] = field(default_factory=list)


class ChatIntegrationService:
    """Service for chat-based learning path interaction.

    Enables students to interact with their learning path through
    natural language chat interface.
    """

    def __init__(
        self,
        llm_service: Optional[Any] = None,
        resource_finder: Optional[Any] = None,
        path_service: Optional[Any] = None,
    ):
        """Initialize chat integration service.

        Args:
            llm_service: Optional LLM service for question answering.
            resource_finder: Optional service to find learning resources.
            path_service: Optional service to manage learning paths.
        """
        self.config = get_learning_path_config()
        self.llm_service = llm_service
        self.resource_finder = resource_finder
        self.path_service = path_service

        # Intent patterns (Turkish)
        self.intent_patterns = self._load_intent_patterns()

    async def process_message(
        self,
        message: ChatMessage,
        current_path: Optional[Any] = None,  # Optional[LearningPath]
        student_profile: Optional[Any] = None,  # Optional[StudentProfile]
    ) -> ChatResponse:
        """Process a chat message and generate response.

        Args:
            message: Student's chat message.
            current_path: Student's active learning path.
            student_profile: Student's profile for personalization.

        Returns:
            ChatResponse with text, suggestions, and actions.
        """
        try:
            # Detect intent
            intent = self._detect_intent(message.text)
            logger.debug(
                f"Detected intent: {intent.value} for message: {message.text[:50]}..."
            )

            # Generate response based on intent
            response = await self._generate_response(
                intent=intent,
                message=message,
                current_path=current_path,
                student_profile=student_profile,
            )

            return response

        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            return ChatResponse(
                text="Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.",
                intent=ChatIntent.UNKNOWN,
            )

    def _detect_intent(self, text: str) -> ChatIntent:
        """Detect the intent of a message.

        Args:
            text: Message text to analyze.

        Returns:
            Detected ChatIntent.
        """
        text_lower = text.lower()

        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return intent

        # Default to asking question if contains question mark
        if "?" in text:
            return ChatIntent.ASK_QUESTION

        return ChatIntent.UNKNOWN

    async def _generate_response(
        self,
        intent: ChatIntent,
        message: ChatMessage,
        current_path: Optional[Any],
        student_profile: Optional[Any],
    ) -> ChatResponse:
        """Generate response based on intent.

        Args:
            intent: Detected message intent.
            message: Original message.
            current_path: Current learning path.
            student_profile: Student profile.

        Returns:
            Generated ChatResponse.
        """
        if intent == ChatIntent.CHECK_PROGRESS:
            return await self._handle_progress_check(current_path)

        elif intent == ChatIntent.GET_RECOMMENDATION:
            return await self._handle_recommendation(current_path, student_profile)

        elif intent == ChatIntent.MARK_COMPLETE:
            return await self._handle_mark_complete(message, current_path)

        elif intent == ChatIntent.REQUEST_HELP:
            return await self._handle_help_request(message, current_path)

        elif intent == ChatIntent.ASK_QUESTION:
            return await self._handle_question(message, current_path)

        elif intent == ChatIntent.CHANGE_TOPIC:
            return await self._handle_topic_change(message, current_path)

        else:
            return self._handle_unknown(message)

    async def _handle_progress_check(
        self, current_path: Optional[Any]
    ) -> ChatResponse:
        """Handle progress check request.

        Args:
            current_path: Current learning path.

        Returns:
            ChatResponse with progress information.
        """
        if not current_path:
            return ChatResponse(
                text=(
                    "Henüz aktif bir öğrenme yolunuz bulunmuyor. "
                    "Bir yol oluşturmak ister misiniz?"
                ),
                intent=ChatIntent.CHECK_PROGRESS,
                suggestions=["Yeni yol oluştur", "Konulara göz at"],
            )

        # Calculate progress
        total_nodes = len(current_path.nodes)
        completed = sum(1 for n in current_path.nodes if n.is_completed)
        progress_pct = (completed / total_nodes * 100) if total_nodes > 0 else 0

        # Current topic
        current_topic = None
        for node in current_path.nodes:
            if not node.is_completed:
                current_topic = node.topic
                break

        text = f"""📊 İlerleme Durumunuz:

• Tamamlanan: {completed}/{total_nodes} konu ({progress_pct:.0f}%)
• Şu anki konu: {current_topic or 'Tamamlandı!'}
• Toplam süre: {current_path.total_duration_minutes} dakika

Devam etmek için hazır mısınız?"""

        suggestions = []
        if current_topic:
            suggestions.append(f"'{current_topic}' konusuna devam et")
        else:
            suggestions.append("Yeni yol başlat")
        suggestions.append("Detaylı rapor göster")

        return ChatResponse(
            text=text, intent=ChatIntent.CHECK_PROGRESS, suggestions=suggestions
        )

    async def _handle_recommendation(
        self, current_path: Optional[Any], student_profile: Optional[Any]
    ) -> ChatResponse:
        """Handle recommendation request.

        Args:
            current_path: Current learning path.
            student_profile: Student profile.

        Returns:
            ChatResponse with resource recommendations.
        """
        resources = []

        if self.resource_finder and current_path:
            # Get current topic
            current_topic = None
            for node in current_path.nodes:
                if not node.is_completed:
                    current_topic = node.topic
                    break

            if current_topic:
                try:
                    resources = await self.resource_finder.find_resources(
                        query=current_topic, limit=3
                    )
                except Exception as e:
                    logger.warning(f"Resource finding failed: {e}")

        if resources:
            text = "🎯 Size önerdiğim kaynaklar:\n\n"
            for i, r in enumerate(resources, 1):
                text += f"{i}. {r.title} ({r.source}) - {r.estimated_time} dk\n"

            return ChatResponse(
                text=text,
                intent=ChatIntent.GET_RECOMMENDATION,
                resources=resources,
                suggestions=["İlk kaynağa başla", "Daha fazla göster"],
            )

        return ChatResponse(
            text=(
                "Şu an için önerebileceğim bir kaynak bulamadım. "
                "Hangi konuda yardım istersiniz?"
            ),
            intent=ChatIntent.GET_RECOMMENDATION,
            suggestions=["Matematik", "Fizik", "Kimya", "Biyoloji"],
        )

    async def _handle_mark_complete(
        self, message: ChatMessage, current_path: Optional[Any]
    ) -> ChatResponse:
        """Handle topic completion marking.

        Args:
            message: Original message.
            current_path: Current learning path.

        Returns:
            ChatResponse with completion confirmation.
        """
        if not current_path:
            return ChatResponse(
                text="Aktif bir öğrenme yolunuz yok.", intent=ChatIntent.MARK_COMPLETE
            )

        # Find current topic
        current_node = None
        for node in current_path.nodes:
            if not node.is_completed:
                current_node = node
                break

        if current_node:
            return ChatResponse(
                text=f"'{current_node.topic}' konusunu tamamladınız mı?",
                intent=ChatIntent.MARK_COMPLETE,
                actions=[
                    {
                        "type": "mark_complete",
                        "node_id": current_node.node_id,
                        "topic": current_node.topic,
                    }
                ],
                suggestions=["Evet, tamamladım", "Hayır, devam ediyorum"],
            )

        return ChatResponse(
            text="Tebrikler! Tüm konuları tamamladınız! 🎉",
            intent=ChatIntent.MARK_COMPLETE,
        )

    async def _handle_help_request(
        self, message: ChatMessage, current_path: Optional[Any]
    ) -> ChatResponse:
        """Handle help request.

        Args:
            message: Original message.
            current_path: Current learning path.

        Returns:
            ChatResponse with help information.
        """
        text = """🆘 Size nasıl yardımcı olabilirim?

• "İlerleme durumum" - Durumunuzu görün
• "Kaynak öner" - Yeni kaynaklar alın
• "Konuyu bitirdim" - Tamamlandı işaretleyin
• "Konuyu değiştir" - Farklı konuya geçin

Sorularınız için doğrudan yazabilirsiniz!"""

        return ChatResponse(
            text=text,
            intent=ChatIntent.REQUEST_HELP,
            suggestions=["İlerleme durumum", "Kaynak öner", "Konuyu bitirdim"],
        )

    async def _handle_question(
        self, message: ChatMessage, current_path: Optional[Any]
    ) -> ChatResponse:
        """Handle a question from student.

        Args:
            message: Original message with question.
            current_path: Current learning path.

        Returns:
            ChatResponse with answer or guidance.
        """
        # Use LLM if available
        if self.llm_service:
            try:
                context = ""
                if current_path:
                    current_topic = None
                    for node in current_path.nodes:
                        if not node.is_completed:
                            current_topic = node.topic
                            break
                    if current_topic:
                        context = f"Öğrenci şu an '{current_topic}' konusunu çalışıyor."

                prompt = f"""Öğrenci sorusu: {message.text}

Bağlam: {context}

Kısa ve öğretici bir yanıt ver. Türkçe yanıtla."""

                response_text = await self.llm_service.generate(prompt)

                return ChatResponse(
                    text=response_text,
                    intent=ChatIntent.ASK_QUESTION,
                    suggestions=[
                        "Daha fazla açıkla",
                        "Örnek göster",
                        "Farklı soru sor",
                    ],
                )
            except Exception as e:
                logger.warning(f"LLM response failed: {e}")

        # Fallback
        return ChatResponse(
            text=(
                "Sorunuzu aldım. Şu an detaylı yanıt veremiyorum, "
                "ancak kaynaklarımızdan faydalanabilirsiniz."
            ),
            intent=ChatIntent.ASK_QUESTION,
            suggestions=["Kaynak öner", "Yardım"],
        )

    async def _handle_topic_change(
        self, message: ChatMessage, current_path: Optional[Any]
    ) -> ChatResponse:
        """Handle topic change request.

        Args:
            message: Original message.
            current_path: Current learning path.

        Returns:
            ChatResponse with topic options.
        """
        if not current_path:
            return ChatResponse(
                text="Önce bir öğrenme yolu oluşturmalısınız.",
                intent=ChatIntent.CHANGE_TOPIC,
            )

        # List available topics
        topics = [node.topic for node in current_path.nodes if not node.is_completed]

        if not topics:
            return ChatResponse(
                text="Tüm konuları tamamladınız!", intent=ChatIntent.CHANGE_TOPIC
            )

        text = "Hangi konuya geçmek istersiniz?\n\n"
        for i, topic in enumerate(topics[:5], 1):
            text += f"{i}. {topic}\n"

        return ChatResponse(
            text=text, intent=ChatIntent.CHANGE_TOPIC, suggestions=topics[:3]
        )

    def _handle_unknown(self, message: ChatMessage) -> ChatResponse:
        """Handle unknown intent.

        Args:
            message: Original message.

        Returns:
            ChatResponse with fallback message.
        """
        return ChatResponse(
            text="Sizi tam anlayamadım. Size nasıl yardımcı olabilirim?",
            intent=ChatIntent.UNKNOWN,
            suggestions=["Yardım", "İlerleme durumum", "Kaynak öner"],
        )

    def _load_intent_patterns(self) -> Dict[ChatIntent, List[str]]:
        """Load intent detection patterns.

        Returns:
            Dictionary mapping intents to Turkish keyword patterns.
        """
        return {
            ChatIntent.CHECK_PROGRESS: [
                "ilerleme",
                "durum",
                "neredeyim",
                "progress",
                "ne kadar",
                "yüzde",
                "tamamladım mı",
                "kaldı",
            ],
            ChatIntent.GET_RECOMMENDATION: [
                "öner",
                "kaynak",
                "video",
                "materyal",
                "ne çalışayım",
                "ne izleyeyim",
                "recommendation",
            ],
            ChatIntent.MARK_COMPLETE: [
                "bitirdim",
                "tamamladım",
                "bitti",
                "finished",
                "done",
                "sonraki",
                "devam",
            ],
            ChatIntent.REQUEST_HELP: [
                "yardım",
                "help",
                "nasıl",
                "ne yapmalı",
                "anlamadım",
                "açıkla",
            ],
            ChatIntent.CHANGE_TOPIC: [
                "konu değiştir",
                "başka konu",
                "atla",
                "geç",
                "skip",
                "farklı",
            ],
        }


# Legacy compatibility wrapper
class ChatIntegration:
    """Legacy chat interface integration wrapper."""

    def __init__(self, chat_service: Any):
        """Initialize with chat service.

        Args:
            chat_service: Chat service instance.
        """
        self.service = chat_service
        logger.info("ChatIntegration initialized")

    async def process_message(
        self,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process chat message.

        Args:
            session_id: Session identifier.
            message: Message text.
            context: Optional context dictionary.

        Returns:
            Response dictionary.
        """
        try:
            return await self.service.process_message(
                session_id=session_id, message=message, context=context
            )
        except Exception as e:
            logger.error(f"Chat processing error: {str(e)}")
            return {"error": str(e)}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history.

        Args:
            session_id: Session identifier.

        Returns:
            List of conversation messages.
        """
        try:
            return self.service.get_conversation_history(session_id)
        except Exception as e:
            logger.error(f"Get history error: {str(e)}")
            return []
