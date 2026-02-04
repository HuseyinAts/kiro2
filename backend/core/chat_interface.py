"""
Chat Interface System
Teknofest 2025 - Eğitim Eylemci Projesi

Bu modül:
- Natural language conversation handler
- Goal setting conversation flows
- Assessment conversation workflows
- Progress discussion capabilities
- Context-aware response generation
"""

import logging
import os
import re

# Core services
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm_service import llm_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Konuşma durumları"""

    GREETING = "greeting"  # Karşılama
    GOAL_SETTING = "goal_setting"  # Hedef belirleme
    PROFILE_CREATION = "profile_creation"  # Profil oluşturma
    ASSESSMENT = "assessment"  # Değerlendirme
    LEARNING_STYLE_DETECTION = "learning_style_detection"  # Öğrenme stili tespiti
    PATH_CREATION = "path_creation"  # Öğrenme yolu oluşturma
    PROGRESS_DISCUSSION = "progress_discussion"  # İlerleme tartışması
    RESOURCE_RECOMMENDATION = "resource_recommendation"  # Kaynak önerisi
    HELP = "help"  # Yardım
    GENERAL_CHAT = "general_chat"  # Genel sohbet
    COMPLETED = "completed"  # Tamamlandı


class MessageType(Enum):
    """Mesaj türleri"""

    USER = "user"  # Kullanıcı mesajı
    ASSISTANT = "assistant"  # Asistan mesajı
    SYSTEM = "system"  # Sistem mesajı
    ACTION = "action"  # Eylem mesajı


class IntentType(Enum):
    """Niyet türleri"""

    GREETING = "greeting"
    SET_GOAL = "set_goal"
    CREATE_PROFILE = "create_profile"
    TAKE_ASSESSMENT = "take_assessment"
    DETECT_LEARNING_STYLE = "detect_learning_style"
    CREATE_LEARNING_PATH = "create_learning_path"
    CHECK_PROGRESS = "check_progress"
    GET_RECOMMENDATIONS = "get_recommendations"
    ASK_HELP = "ask_help"
    GENERAL_QUESTION = "general_question"
    UNKNOWN = "unknown"


@dataclass
class ChatMessage:
    """Chat mesajı"""

    message_id: str
    session_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    metadata: dict[str, Any]


@dataclass
class ConversationContext:
    """Konuşma bağlamı"""

    session_id: str
    student_id: str | None
    current_state: ConversationState
    conversation_history: list[ChatMessage]
    user_profile: dict[str, Any]
    current_task: dict[str, Any] | None
    collected_data: dict[str, Any]
    last_activity: datetime
    metadata: dict[str, Any]


@dataclass
class ChatResponse:
    """Chat yanıtı"""

    message: str
    message_type: MessageType
    suggested_actions: list[dict[str, Any]]
    next_state: ConversationState | None
    requires_input: bool
    metadata: dict[str, Any]


class ChatInterface:
    """Chat Arayüz Sistemi"""

    def __init__(self):
        self.conversations = {}  # session_id -> ConversationContext
        self.intent_patterns = self._load_intent_patterns()
        self.conversation_flows = self._load_conversation_flows()
        self.response_templates = self._load_response_templates()

    def _load_intent_patterns(self) -> dict[IntentType, list[str]]:
        """Niyet tanıma kalıpları"""
        return {
            IntentType.GREETING: [
                r"merhaba|selam|hey|hi|hello",
                r"nasılsın|naber|ne haber",
                r"başla|başlayalım|başlayabilir miyiz",
            ],
            IntentType.SET_GOAL: [
                r"hedef|amaç|istiyorum|öğrenmek istiyorum",
                r"LGS|YKS|sınav|üniversite|lise",
                r"matematik|fen|fizik|kimya|biyoloji|türkçe|tarih|coğrafya",
                r"öğrenme.*plan|çalışma.*plan",
            ],
            IntentType.CREATE_PROFILE: [
                r"profil|bilgi|kendim hakkında",
                r"sınıf|yaş|seviye",
                r"hangi.*sınıf|kaçıncı.*sınıf",
            ],
            IntentType.TAKE_ASSESSMENT: [
                r"test|değerlendirme|ölçme|sınav",
                r"bilgi.*seviye|ne.*kadar.*biliyorum",
                r"değerlendir|test.*et",
            ],
            IntentType.DETECT_LEARNING_STYLE: [
                r"öğrenme.*stil|nasıl.*öğren",
                r"görsel|işitsel|okuma|uygulama",
                r"hangi.*yöntem|nasıl.*çalış",
            ],
            IntentType.CREATE_LEARNING_PATH: [
                r"öğrenme.*yol|çalışma.*program",
                r"plan.*yap|program.*hazırla",
                r"nasıl.*çalış|ne.*yapmalı",
            ],
            IntentType.CHECK_PROGRESS: [
                r"ilerleme|gelişim|durum",
                r"nerede.*kaldım|ne.*kadar.*tamamladım",
                r"başarı|sonuç",
            ],
            IntentType.GET_RECOMMENDATIONS: [
                r"öneri|tavsiye|kaynak",
                r"ne.*izle|ne.*oku|hangi.*video",
                r"materyal|içerik",
            ],
            IntentType.ASK_HELP: [
                r"yardım|help|nasıl",
                r"anlamadım|bilmiyorum",
                r"açıkla|anlat",
            ],
            IntentType.GENERAL_QUESTION: [
                r"nedir|ne.*demek|açıkla",
                r"nasıl.*yapılır|nasıl.*çözülür",
                r"örnek|örnekle",
            ],
        }

    def _load_conversation_flows(self) -> dict[ConversationState, dict[str, Any]]:
        """Konuşma akışları"""
        return {
            ConversationState.GREETING: {
                "welcome_message": "Merhaba! Ben senin kişisel öğrenme asistanınım. Sana özel bir öğrenme yolu oluşturmak için buradayım. Hangi konuda yardımcı olabilirim?",
                "next_states": [
                    ConversationState.GOAL_SETTING,
                    ConversationState.PROFILE_CREATION,
                ],
                "suggested_actions": [
                    {
                        "text": "Öğrenme hedefimi belirlemek istiyorum",
                        "action": "set_goal",
                    },
                    {"text": "Profil oluşturmak istiyorum", "action": "create_profile"},
                    {
                        "text": "Bilgi seviyemi test etmek istiyorum",
                        "action": "take_assessment",
                    },
                ],
            },
            ConversationState.GOAL_SETTING: {
                "questions": [
                    "Hangi konuda öğrenme hedefin var? (Örn: Matematik, Fen Bilimleri, YKS hazırlığı)",
                    "Bu hedefe ulaşmak için ne kadar zamanın var?",
                    "Hangi sınav için hazırlanıyorsun? (LGS, YKS, KPSS vb.)",
                    "Bu konuda şu anki seviyeni nasıl değerlendiriyorsun?",
                ],
                "required_fields": ["subject", "goal", "timeline", "exam_target"],
                "next_state": ConversationState.PROFILE_CREATION,
            },
            ConversationState.PROFILE_CREATION: {
                "questions": [
                    "Hangi sınıftasın?",
                    "Günde ne kadar çalışma zamanın var?",
                    "En çok hangi derslerde zorlanıyorsun?",
                    "En başarılı olduğun dersler hangileri?",
                ],
                "required_fields": [
                    "grade",
                    "available_time",
                    "weak_subjects",
                    "strong_subjects",
                ],
                "next_state": ConversationState.LEARNING_STYLE_DETECTION,
            },
            ConversationState.LEARNING_STYLE_DETECTION: {
                "intro_message": "Şimdi senin öğrenme stilini belirleyelim. Bu, sana en uygun kaynakları önermem için önemli.",
                "questions": [
                    "Yeni bir konuyu öğrenirken hangi yöntemi tercih edersin?",
                    "Bilgiyi en iyi nasıl hatırlarsın?",
                    "Ders çalışırken hangi ortamı tercih edersin?",
                    "Problem çözerken nasıl yaklaşırsın?",
                ],
                "next_state": ConversationState.PATH_CREATION,
            },
            ConversationState.PATH_CREATION: {
                "intro_message": "Harika! Artık sana özel bir öğrenme yolu oluşturabilirim.",
                "confirmation_message": "Topladığım bilgilere göre senin için bir öğrenme planı hazırladım. İnceleyelim mi?",
                "next_state": ConversationState.PROGRESS_DISCUSSION,
            },
            ConversationState.PROGRESS_DISCUSSION: {
                "questions": [
                    "Öğrenme planın nasıl gidiyor?",
                    "Hangi konularda zorlanıyorsun?",
                    "Hangi kaynaklar daha faydalı oluyor?",
                    "Çalışma programında değişiklik yapmak ister misin?",
                ],
                "next_states": [
                    ConversationState.RESOURCE_RECOMMENDATION,
                    ConversationState.ASSESSMENT,
                ],
            },
        }

    def _load_response_templates(self) -> dict[str, list[str]]:
        """Yanıt şablonları"""
        return {
            "greeting": [
                "Merhaba! Öğrenme yolculuğunda sana yardımcı olmak için buradayım.",
                "Selam! Bugün hangi konuda öğrenme hedefin var?",
                "Hey! Sana özel bir öğrenme planı oluşturmaya hazırım.",
            ],
            "goal_confirmation": [
                "Anladım, {goal} konusunda çalışmak istiyorsun. Bu harika bir hedef!",
                "{goal} için öğrenme planı oluşturalım. Bu konuda ne kadar deneyimin var?",
                "Süper! {goal} konusunda sana yardımcı olabilirim.",
            ],
            "encouragement": [
                "Harika gidiyorsun! Devam et.",
                "Bu çok iyi bir ilerleme. Tebrikler!",
                "Mükemmel! Bu tempoda devam edersen hedefine ulaşacaksın.",
            ],
            "help": [
                "Tabii ki yardımcı olabilirim. Ne konuda yardıma ihtiyacın var?",
                "Hangi konuda açıklama istiyorsun?",
                "Sana nasıl yardımcı olabilirim?",
            ],
            "clarification": [
                "Bu konuyu biraz daha açıklayabilir misin?",
                "Tam olarak ne demek istediğini anlayamadım. Tekrar söyleyebilir misin?",
                "Daha spesifik olabilir misin?",
            ],
        }

    async def process_message(
        self, session_id: str, message: str, user_id: str | None = None
    ) -> ChatResponse:
        """
        Mesajı işle ve yanıt oluştur

        Args:
            session_id: Oturum ID
            message: Kullanıcı mesajı
            user_id: Kullanıcı ID (opsiyonel)

        Returns:
            Chat yanıtı
        """
        try:
            # Konuşma bağlamını al veya oluştur
            context = self._get_or_create_context(session_id, user_id)

            # Kullanıcı mesajını kaydet
            user_message = ChatMessage(
                message_id=f"msg_{datetime.now().timestamp()}",
                session_id=session_id,
                message_type=MessageType.USER,
                content=message,
                timestamp=datetime.now(),
                metadata={},
            )
            context.conversation_history.append(user_message)

            # Niyeti tespit et
            intent = self._detect_intent(message, context)

            # Yanıt oluştur
            response = await self._generate_response(message, intent, context)

            # Asistan mesajını kaydet
            assistant_message = ChatMessage(
                message_id=f"msg_{datetime.now().timestamp()}",
                session_id=session_id,
                message_type=MessageType.ASSISTANT,
                content=response.message,
                timestamp=datetime.now(),
                metadata={"intent": intent.value, "state": context.current_state.value},
            )
            context.conversation_history.append(assistant_message)

            # Konuşma durumunu güncelle
            if response.next_state:
                context.current_state = response.next_state

            context.last_activity = datetime.now()

            logger.info(
                f"Processed message for session {session_id}: {intent.value} -> {context.current_state.value}"
            )
            return response

        except Exception as e:
            logger.error(f"Error processing message: {e!s}")
            return ChatResponse(
                message="Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.",
                message_type=MessageType.ASSISTANT,
                suggested_actions=[],
                next_state=None,
                requires_input=True,
                metadata={"error": str(e)},
            )

    def _get_or_create_context(
        self, session_id: str, user_id: str | None = None
    ) -> ConversationContext:
        """Konuşma bağlamını al veya oluştur"""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationContext(
                session_id=session_id,
                student_id=user_id,
                current_state=ConversationState.GREETING,
                conversation_history=[],
                user_profile={},
                current_task=None,
                collected_data={},
                last_activity=datetime.now(),
                metadata={},
            )

        return self.conversations[session_id]

    def _detect_intent(self, message: str, context: ConversationContext) -> IntentType:
        """
        Mesajdan niyeti tespit et

        Args:
            message: Kullanıcı mesajı
            context: Konuşma bağlamı

        Returns:
            Tespit edilen niyet
        """
        message_lower = message.lower()

        # Mevcut duruma göre öncelikli niyet kontrolü
        if context.current_state == ConversationState.GOAL_SETTING:
            if any(
                subject in message_lower
                for subject in [
                    "matematik",
                    "fen",
                    "fizik",
                    "kimya",
                    "biyoloji",
                    "türkçe",
                ]
            ):
                return IntentType.SET_GOAL

        # Genel niyet tespiti
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent

        return IntentType.UNKNOWN

    async def _generate_response(
        self, message: str, intent: IntentType, context: ConversationContext
    ) -> ChatResponse:
        """
        Yanıt oluştur

        Args:
            message: Kullanıcı mesajı
            intent: Tespit edilen niyet
            context: Konuşma bağlamı

        Returns:
            Chat yanıtı
        """
        try:
            # Durum bazlı yanıt oluşturma
            if context.current_state == ConversationState.GREETING:
                return await self._handle_greeting(message, intent, context)
            if context.current_state == ConversationState.GOAL_SETTING:
                return await self._handle_goal_setting(message, intent, context)
            if context.current_state == ConversationState.PROFILE_CREATION:
                return await self._handle_profile_creation(message, intent, context)
            if context.current_state == ConversationState.LEARNING_STYLE_DETECTION:
                return await self._handle_learning_style_detection(
                    message, intent, context
                )
            if context.current_state == ConversationState.PATH_CREATION:
                return await self._handle_path_creation(message, intent, context)
            if context.current_state == ConversationState.PROGRESS_DISCUSSION:
                return await self._handle_progress_discussion(message, intent, context)
            return await self._handle_general_chat(message, intent, context)

        except Exception as e:
            logger.error(f"Error generating response: {e!s}")
            return ChatResponse(
                message="Bir sorun oluştu. Devam edelim, hangi konuda yardımcı olabilirim?",
                message_type=MessageType.ASSISTANT,
                suggested_actions=[],
                next_state=None,
                requires_input=True,
                metadata={"error": str(e)},
            )

    async def _handle_greeting(
        self, message: str, intent: IntentType, context: ConversationContext
    ) -> ChatResponse:
        """Karşılama durumunu işle"""
        flow = self.conversation_flows[ConversationState.GREETING]

        return ChatResponse(
            message=flow["welcome_message"],
            message_type=MessageType.ASSISTANT,
            suggested_actions=flow["suggested_actions"],
            next_state=ConversationState.GOAL_SETTING,
            requires_input=True,
            metadata={"flow": "greeting"},
        )

    async def _handle_goal_setting(
        self, message: str, intent: IntentType, context: ConversationContext
    ) -> ChatResponse:
        """Hedef belirleme durumunu işle"""
        # Mesajdan hedef bilgilerini çıkar
        extracted_info = await self._extract_goal_information(message)
        context.collected_data.update(extracted_info)

        flow = self.conversation_flows[ConversationState.GOAL_SETTING]
        required_fields = flow["required_fields"]

        # Eksik bilgileri kontrol et
        missing_fields = [
            field for field in required_fields if field not in context.collected_data
        ]

        if missing_fields:
            # Eksik bilgi için soru sor
            next_question = self._get_next_question_for_field(missing_fields[0])
            return ChatResponse(
                message=next_question,
                message_type=MessageType.ASSISTANT,
                suggested_actions=[],
                next_state=None,  # Aynı durumda kal
                requires_input=True,
                metadata={"missing_fields": missing_fields},
            )
        # Tüm bilgiler toplandı, profil oluşturmaya geç
        confirmation = f"Anladım! {context.collected_data.get('subject', 'Bu konu')} için {context.collected_data.get('timeline', 'belirlenen sürede')} çalışmak istiyorsun. Şimdi senin hakkında biraz daha bilgi alalım."

        return ChatResponse(
            message=confirmation,
            message_type=MessageType.ASSISTANT,
            suggested_actions=[
                {"text": "Profil oluşturmaya devam et", "action": "continue_profile"}
            ],
            next_state=ConversationState.PROFILE_CREATION,
            requires_input=True,
            metadata={"goals_collected": context.collected_data},
        )

    async def _handle_profile_creation(
        self, message: str, intent: IntentType, context: ConversationContext
    ) -> ChatResponse:
        """Profil oluşturma durumunu işle"""
        # Mesajdan profil bilgilerini çıkar
        extracted_info = await self._extract_profile_information(message)
        context.collected_data.update(extracted_info)

        flow = self.conversation_flows[ConversationState.PROFILE_CREATION]
        required_fields = flow["required_fields"]

        # Eksik bilgileri kontrol et
        missing_fields = [
            field for field in required_fields if field not in context.collected_data
        ]

        if missing_fields:
            next_question = self._get_next_question_for_field(missing_fields[0])
            return ChatResponse(
                message=next_question,
                message_type=MessageType.ASSISTANT,
                suggested_actions=[],
                next_state=None,
                requires_input=True,
                metadata={"missing_fields": missing_fields},
            )
        # Profil tamamlandı, öğrenme stili tespitine geç
        return ChatResponse(
            message="Harika! Profilin hazır. Şimdi senin öğrenme stilini belirleyelim. Bu sayede sana en uygun kaynakları önerebilirim.",
            message_type=MessageType.ASSISTANT,
            suggested_actions=[
                {
                    "text": "Öğrenme stili testine başla",
                    "action": "start_learning_style_test",
                }
            ],
            next_state=ConversationState.LEARNING_STYLE_DETECTION,
            requires_input=True,
            metadata={"profile_completed": True},
        )

    async def _handle_learning_style_detection(
        self, message: str, intent: IntentType, context: ConversationContext
    ) -> ChatResponse:
        """Öğrenme stili tespiti durumunu işle"""
        # Bu durumda öğrenme stili anketi başlatılabilir
        return ChatResponse(
            message="Öğrenme stili anketini başlatıyorum. Birkaç soru soracağım, en doğal hissettiğin seçeneği seç.",
            message_type=MessageType.ASSISTANT,
            suggested_actions=[
                {"text": "Anketi başlat", "action": "start_style_questionnaire"}
            ],
            next_state=ConversationState.PATH_CREATION,
            requires_input=False,
            metadata={"action_required": "start_learning_style_questionnaire"},
        )

    async def _handle_path_creation(
        self, message: str, intent: IntentType, context: ConversationContext
    ) -> ChatResponse:
        """Öğrenme yolu oluşturma durumunu işle"""
        return ChatResponse(
            message="Mükemmel! Topladığım bilgilere göre sana özel bir öğrenme yolu oluşturuyorum. Bu birkaç saniye sürebilir...",
            message_type=MessageType.ASSISTANT,
            suggested_actions=[],
            next_state=ConversationState.PROGRESS_DISCUSSION,
            requires_input=False,
            metadata={
                "action_required": "create_learning_path",
                "collected_data": context.collected_data,
            },
        )

    async def _handle_progress_discussion(
        self, message: str, intent: IntentType, context: ConversationContext
    ) -> ChatResponse:
        """İlerleme tartışması durumunu işle"""
        # İlerleme ile ilgili sorular sor ve öneriler sun
        return ChatResponse(
            message="Öğrenme yolun hazır! Nasıl gidiyor? Herhangi bir sorun yaşıyor musun?",
            message_type=MessageType.ASSISTANT,
            suggested_actions=[
                {"text": "İyi gidiyor", "action": "progress_good"},
                {"text": "Zorlanıyorum", "action": "progress_struggling"},
                {"text": "Kaynak önerisi istiyorum", "action": "need_resources"},
            ],
            next_state=None,
            requires_input=True,
            metadata={"discussion_type": "progress"},
        )

    async def _handle_general_chat(
        self, message: str, intent: IntentType, context: ConversationContext
    ) -> ChatResponse:
        """Genel sohbet durumunu işle"""
        # LLM ile genel yanıt oluştur
        prompt = f"""
        Kullanıcı mesajı: {message}
        Konuşma geçmişi: {[msg.content for msg in context.conversation_history[-3:]]}
        
        Sen bir eğitim asistanısın. Kullanıcıya yardımcı, samimi ve motive edici bir yanıt ver.
        Yanıt Türkçe olsun ve 2-3 cümleyi geçmesin.
        """

        result = await llm_service.generate(prompt=prompt, temperature=0.7)

        response_text = (
            result.get("text", "Anlıyorum. Başka nasıl yardımcı olabilirim?")
            if result.get("success")
            else "Başka nasıl yardımcı olabilirim?"
        )

        return ChatResponse(
            message=response_text,
            message_type=MessageType.ASSISTANT,
            suggested_actions=[
                {"text": "Yeni hedef belirle", "action": "set_new_goal"},
                {"text": "İlerleme kontrolü", "action": "check_progress"},
                {"text": "Kaynak önerisi", "action": "get_recommendations"},
            ],
            next_state=None,
            requires_input=True,
            metadata={"chat_type": "general"},
        )

    async def _extract_goal_information(self, message: str) -> dict[str, Any]:
        """Mesajdan hedef bilgilerini çıkar"""
        extracted = {}
        message_lower = message.lower()

        # Ders konuları
        subjects = {
            "matematik": ["matematik", "math", "sayısal"],
            "fen": ["fen", "science", "fen bilimleri"],
            "fizik": ["fizik", "physics"],
            "kimya": ["kimya", "chemistry"],
            "biyoloji": ["biyoloji", "biology"],
            "türkçe": ["türkçe", "turkish", "dil"],
            "tarih": ["tarih", "history"],
            "coğrafya": ["coğrafya", "geography"],
        }

        for subject, keywords in subjects.items():
            if any(keyword in message_lower for keyword in keywords):
                extracted["subject"] = subject
                break

        # Sınav türleri
        if any(exam in message_lower for exam in ["lgs", "liselere geçiş"]):
            extracted["exam_target"] = "LGS"
        elif any(exam in message_lower for exam in ["yks", "üniversite", "tyt", "ayt"]):
            extracted["exam_target"] = "YKS"
        elif "kpss" in message_lower:
            extracted["exam_target"] = "KPSS"

        # Zaman ifadeleri
        if any(time in message_lower for time in ["1 ay", "bir ay", "1 aylık"]):
            extracted["timeline"] = "1 ay"
        elif any(time in message_lower for time in ["3 ay", "üç ay", "3 aylık"]):
            extracted["timeline"] = "3 ay"
        elif any(time in message_lower for time in ["6 ay", "altı ay", "6 aylık"]):
            extracted["timeline"] = "6 ay"
        elif any(time in message_lower for time in ["1 yıl", "bir yıl", "yıllık"]):
            extracted["timeline"] = "1 yıl"

        return extracted

    async def _extract_profile_information(self, message: str) -> dict[str, Any]:
        """Mesajdan profil bilgilerini çıkar"""
        extracted = {}
        message_lower = message.lower()

        # Sınıf seviyesi
        import re

        grade_match = re.search(r"(\d+)\.?\s*sınıf", message_lower)
        if grade_match:
            extracted["grade"] = grade_match.group(1)

        # Çalışma zamanı
        time_patterns = [
            (r"(\d+)\s*saat", "hours"),
            (r"(\d+)\s*dakika", "minutes"),
            (r"yarım\s*saat", "half_hour"),
            (r"bir\s*saat", "one_hour"),
        ]

        for pattern, time_type in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if time_type == "hours":
                    extracted["available_time"] = (
                        int(match.group(1)) * 60
                    )  # Dakikaya çevir
                elif time_type == "minutes":
                    extracted["available_time"] = int(match.group(1))
                elif time_type == "half_hour":
                    extracted["available_time"] = 30
                elif time_type == "one_hour":
                    extracted["available_time"] = 60
                break

        return extracted

    def _get_next_question_for_field(self, field: str) -> str:
        """Eksik alan için soru oluştur"""
        questions = {
            "subject": "Hangi konuda çalışmak istiyorsun? (Matematik, Fen, Fizik, Kimya, vb.)",
            "goal": "Öğrenme hedefin nedir? Hangi sınavı hedefliyorsun?",
            "timeline": "Bu hedefe ulaşmak için ne kadar zamanın var?",
            "exam_target": "Hangi sınav için hazırlanıyorsun? (LGS, YKS, KPSS vb.)",
            "grade": "Hangi sınıftasın?",
            "available_time": "Günde ne kadar çalışma zamanın var?",
            "weak_subjects": "Hangi derslerde zorlanıyorsun?",
            "strong_subjects": "En başarılı olduğun dersler hangileri?",
        }

        return questions.get(field, "Bu konuda biraz daha bilgi verebilir misin?")

    def get_conversation_context(self, session_id: str) -> ConversationContext | None:
        """Konuşma bağlamını getir"""
        return self.conversations.get(session_id)

    def clear_conversation(self, session_id: str):
        """Konuşmayı temizle"""
        if session_id in self.conversations:
            del self.conversations[session_id]

    def get_active_conversations(self) -> list[str]:
        """Aktif konuşmaları getir"""
        return list(self.conversations.keys())


# Singleton instance
chat_interface = ChatInterface()
