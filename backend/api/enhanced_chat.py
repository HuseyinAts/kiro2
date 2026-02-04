"""
Gelişmiş AI Sohbet API - Devrimsel Özelliklerle Entegre
Teknofest 2025 - Eğitim Eylemci Projesi

Bu API şu devrimsel özellikleri entegre eder:
- ZPD tabanlı adaptif yanıt üretimi
- Öğrenme stili bazlı sohbet kişiselleştirmesi  
- IRT morfoloji analizine dayalı soru zorluk ayarlaması
- Agent koordinasyonu ile sohbet deneyimi iyileştirme
- Türkçe NLP ve morfolojik analiz
- Bionic Reading desteği
- Multi-agent blackboard koordinasyonu
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from agents.accessibility_agent import AccessibilityAgent
from agents.learning_path_agent import LearningPathAgent
from agents.study_buddy_agent import StudyBuddyAgent
from algorithms.hybrid_learning_style_detector import (
    HybridLearningProfile,
    HybridLearningStyleDetector,
)
from algorithms.irt_morfoloji_service import IRTMorfolojiService
from algorithms.turkish_bionic_reading import TurkishBionicReading
from algorithms.turkish_zpd_maarif_system import TurkishZPDMaarifSystem, TurkishZPDRange
from core.llm_service import llm_service

# Core services
from core.turkish_nlp_service import turkish_nlp_service
from services.learning_style_service import LearningStyleService

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/api/v1/enhanced-chat", tags=["Enhanced Chat"])

# Service instances
learning_style_service = LearningStyleService()
zpd_maarif_system = TurkishZPDMaarifSystem()
hybrid_detector = HybridLearningStyleDetector()
bionic_reader = TurkishBionicReading()
irt_service = IRTMorfolojiService()

# Agent instances
learning_path_agent = LearningPathAgent()
study_buddy_agent = StudyBuddyAgent()
accessibility_agent = AccessibilityAgent()


class ChatMessageType(Enum):
    """Sohbet mesaj tipleri"""

    USER_QUESTION = "user_question"
    AI_RESPONSE = "ai_response"
    SYSTEM_INFO = "system_info"
    LEARNING_SUGGESTION = "learning_suggestion"
    QUIZ_QUESTION = "quiz_question"
    FEEDBACK = "feedback"


class ResponseMode(Enum):
    """Yanıt modları"""

    ADAPTIVE = "adaptive"  # ZPD tabanlı adaptif
    LEARNING_STYLE = "learning_style"  # Öğrenme stili bazlı
    SIMPLIFIED = "simplified"  # Basitleştirilmiş
    BIONIC = "bionic"  # Bionic Reading
    COMPREHENSIVE = "comprehensive"  # Kapsamlı


@dataclass
class ChatContext:
    """Sohbet bağlamı"""

    student_id: str
    session_id: str
    subject: str = "genel"
    current_topic: str = ""
    learning_style_profile: Optional[HybridLearningProfile] = None
    zpd_range: Optional[TurkishZPDRange] = None
    difficulty_level: float = 0.5  # 0.0-1.0
    response_mode: ResponseMode = ResponseMode.ADAPTIVE
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    agent_insights: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class EnhancedChatResponse:
    """Gelişmiş sohbet yanıtı"""

    response_id: str
    message: str
    bionic_message: Optional[str] = None
    message_type: ChatMessageType = ChatMessageType.AI_RESPONSE
    confidence_score: float = 0.8
    learning_insights: Dict[str, Any] = field(default_factory=dict)
    agent_contributions: Dict[str, Any] = field(default_factory=dict)
    suggested_actions: List[str] = field(default_factory=list)
    difficulty_adjusted: bool = False
    zpd_applied: bool = False
    morphology_analysis: Optional[Dict[str, Any]] = None
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# Pydantic models for API
class ChatMessageRequest(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    message: str = Field(..., description="Kullanıcı mesajı")
    subject: Optional[str] = Field("genel", description="Konu/ders")
    session_id: Optional[str] = Field(None, description="Oturum ID")
    response_mode: Optional[ResponseMode] = Field(
        ResponseMode.ADAPTIVE, description="Yanıt modu"
    )
    include_bionic: Optional[bool] = Field(False, description="Bionic Reading dahil et")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Ek bağlam verisi")


class ChatHistoryRequest(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    session_id: Optional[str] = Field(None, description="Oturum ID")
    limit: Optional[int] = Field(20, description="Maksimum mesaj sayısı")


class ChatAnalyticsRequest(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    time_range_days: Optional[int] = Field(7, description="Analiz zaman aralığı (gün)")


# Global chat contexts
chat_contexts: Dict[str, ChatContext] = {}


class EnhancedChatService:
    """Gelişmiş AI Sohbet Servisi"""

    def __init__(self):
        self.contexts = chat_contexts
        self.blackboard = {}  # Multi-agent blackboard

    async def process_message(
        self,
        student_id: str,
        message: str,
        subject: str = "genel",
        session_id: Optional[str] = None,
        response_mode: ResponseMode = ResponseMode.ADAPTIVE,
        include_bionic: bool = False,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> EnhancedChatResponse:
        """
        Mesajı işle ve gelişmiş yanıt oluştur
        """
        start_time = datetime.now()

        try:
            # Session ID oluştur veya al
            if not session_id:
                session_id = f"session_{student_id}_{datetime.now().timestamp()}"

            context_key = f"{student_id}_{session_id}"

            # Context'i al veya oluştur
            if context_key not in self.contexts:
                self.contexts[context_key] = ChatContext(
                    student_id=student_id,
                    session_id=session_id,
                    subject=subject,
                    response_mode=response_mode,
                )

            context = self.contexts[context_key]
            context.last_updated = datetime.now()

            # 1. Türkçe NLP analizi
            nlp_analysis = await self._analyze_message_nlp(message)

            # 2. Öğrenci profilini al/güncelle
            await self._update_student_profile(context, context_data)

            # 3. ZPD hesaplama
            await self._calculate_zpd_range(context, message)

            # 4. Agent koordinasyonu
            agent_insights = await self._coordinate_agents(
                context, message, nlp_analysis
            )

            # 5. Adaptif yanıt oluşturma
            response_content = await self._generate_adaptive_response(
                context, message, nlp_analysis, agent_insights
            )

            # 6. Bionic Reading uygula (istenirse)
            bionic_content = None
            if include_bionic:
                bionic_result = await bionic_reader.apply_bionic_reading(
                    response_content
                )
                if bionic_result.success:
                    bionic_content = bionic_result.bionic_text

            # 7. Zorluk seviyesi ayarlama
            difficulty_adjusted = await self._adjust_difficulty(context, nlp_analysis)

            # 8. Önerilen eylemler
            suggested_actions = await self._generate_suggested_actions(
                context, agent_insights
            )

            # 9. Sohbet geçmişine ekle
            context.conversation_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "user_message": message,
                    "ai_response": response_content,
                    "nlp_analysis": nlp_analysis,
                    "agent_insights": agent_insights,
                }
            )

            # Processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Enhanced response oluştur
            response = EnhancedChatResponse(
                response_id=str(uuid.uuid4()),
                message=response_content,
                bionic_message=bionic_content,
                message_type=ChatMessageType.AI_RESPONSE,
                confidence_score=0.85,
                learning_insights={
                    "learning_style": context.learning_style_profile.hybrid_code
                    if context.learning_style_profile
                    else None,
                    "zpd_level": context.zpd_range.optimal_challenge
                    if context.zpd_range
                    else None,
                    "difficulty_level": context.difficulty_level,
                },
                agent_contributions=agent_insights,
                suggested_actions=suggested_actions,
                difficulty_adjusted=difficulty_adjusted,
                zpd_applied=context.zpd_range is not None,
                morphology_analysis=nlp_analysis,
                processing_time_ms=processing_time,
                metadata={
                    "session_id": session_id,
                    "subject": subject,
                    "response_mode": response_mode.value,
                },
            )

            logger.info(
                f"Enhanced chat response generated for student {student_id} in {processing_time:.2f}ms"
            )
            return response

        except Exception as e:
            logger.error(f"Process message error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Mesaj işleme hatası: {str(e)}"
            )

    async def _analyze_message_nlp(self, message: str) -> Dict[str, Any]:
        """Mesajın Türkçe NLP analizi"""
        try:
            # Metin normalizasyonu
            normalization_result = await turkish_nlp_service.normalize_text(message)

            # Karmaşıklık analizi
            complexity_analysis = await turkish_nlp_service.analyze_text_complexity(
                message
            )

            # Kelime bazlı morfolojik analiz
            words = message.split()
            morphology_results = []

            for word in words[:10]:  # İlk 10 kelime
                analysis = await turkish_nlp_service.analyze_morphology(word)
                if analysis:
                    morphology_results.append(
                        {
                            "word": analysis.word,
                            "root": analysis.root,
                            "suffixes": analysis.suffixes,
                            "complexity_score": analysis.complexity_score,
                        }
                    )

            return {
                "original_message": message,
                "normalized_text": normalization_result.normalized_text,
                "corrections": normalization_result.corrections,
                "complexity": complexity_analysis,
                "morphology": morphology_results,
                "word_count": len(words),
                "avg_word_complexity": sum(
                    r["complexity_score"] for r in morphology_results
                )
                / len(morphology_results)
                if morphology_results
                else 0,
            }

        except Exception as e:
            logger.error(f"NLP analysis error: {str(e)}")
            return {"original_message": message, "error": str(e)}

    async def _update_student_profile(
        self, context: ChatContext, context_data: Optional[Dict[str, Any]]
    ):
        """Öğrenci profilini güncelle"""
        try:
            # Öğrenme stili profili al
            if not context.learning_style_profile:
                behavioral_data = (
                    context_data.get("behavioral_data", {}) if context_data else {}
                )

                # Mock behavioral data for learning style detection
                mock_behavioral_data = (
                    []
                )  # Gerçek implementasyonda veri tabanından alınacak
                mock_questionnaire_responses = (
                    []
                )  # Gerçek implementasyonda veri tabanından alınacak

                try:
                    # Hibrit öğrenme stili tespit et
                    if mock_behavioral_data:  # Sadece veri varsa
                        context.learning_style_profile = (
                            await hybrid_detector.detect_hybrid_profile(
                                context.student_id,
                                mock_behavioral_data,
                                mock_questionnaire_responses,
                            )
                        )
                except Exception as e:
                    logger.warning(f"Learning style detection failed: {str(e)}")
                    # Fallback: basit profil oluştur
                    context.learning_style_profile = None

        except Exception as e:
            logger.error(f"Update student profile error: {str(e)}")

    async def _calculate_zpd_range(self, context: ChatContext, message: str):
        """ZPD aralığını hesapla"""
        try:
            # Öğrencinin mevcut seviyesini tahmin et (basitleştirilmiş)
            current_level = context.difficulty_level

            # Kültürel bağlam (mock data)
            from algorithms.turkish_zpd_maarif_system import TurkishCulturalContext

            cultural_context = TurkishCulturalContext(
                student_id=context.student_id,
                group_learning_preference=0.8,
                teacher_respect_level=0.9,
                family_involvement=0.7,
            )

            # ZPD hesapla
            context.zpd_range = await zpd_maarif_system.calculate_turkish_zpd(
                student_id=context.student_id,
                subject=context.subject,
                current_level=current_level,
                cultural_context=cultural_context,
                content_description=message,
            )

        except Exception as e:
            logger.error(f"ZPD calculation error: {str(e)}")

    async def _coordinate_agents(
        self, context: ChatContext, message: str, nlp_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Agent koordinasyonu - Multi-agent blackboard pattern"""
        try:
            agent_insights = {}

            # Blackboard'a mesaj bilgisini yaz
            self.blackboard[f"message_{context.student_id}"] = {
                "message": message,
                "nlp_analysis": nlp_analysis,
                "timestamp": datetime.now(),
                "context": context,
            }

            # Learning Path Agent insights
            try:
                # Öğrenme yolu önerileri
                if "soru" in message.lower() or "nasıl" in message.lower():
                    learning_suggestions = await self._get_learning_path_suggestions(
                        context, message
                    )
                    agent_insights["learning_path"] = learning_suggestions

                    # Blackboard'a yaz
                    self.blackboard[
                        f"learning_suggestions_{context.student_id}"
                    ] = learning_suggestions
            except Exception as e:
                logger.warning(f"Learning Path Agent error: {str(e)}")

            # Study Buddy Agent insights
            try:
                # Soru ve quiz önerileri
                if any(
                    word in message.lower()
                    for word in ["test", "sınav", "quiz", "soru"]
                ):
                    study_suggestions = await self._get_study_buddy_suggestions(
                        context, message
                    )
                    agent_insights["study_buddy"] = study_suggestions

                    # Blackboard'a yaz
                    self.blackboard[
                        f"study_suggestions_{context.student_id}"
                    ] = study_suggestions
            except Exception as e:
                logger.warning(f"Study Buddy Agent error: {str(e)}")

            # Accessibility Agent insights
            try:
                # Erişilebilirlik önerileri
                complexity_score = nlp_analysis.get("complexity", {}).get(
                    "overall_complexity", 0
                )
                if complexity_score > 0.7:
                    accessibility_suggestions = (
                        await self._get_accessibility_suggestions(context, message)
                    )
                    agent_insights["accessibility"] = accessibility_suggestions

                    # Blackboard'a yaz
                    self.blackboard[
                        f"accessibility_suggestions_{context.student_id}"
                    ] = accessibility_suggestions
            except Exception as e:
                logger.warning(f"Accessibility Agent error: {str(e)}")

            # Agent sinerji analizi
            agent_insights["synergy"] = await self._analyze_agent_synergy(
                context.student_id
            )

            return agent_insights

        except Exception as e:
            logger.error(f"Agent coordination error: {str(e)}")
            return {}

    async def _get_learning_path_suggestions(
        self, context: ChatContext, message: str
    ) -> Dict[str, Any]:
        """Learning Path Agent önerileri"""
        try:
            # Basit öneriler (gerçek implementasyonda daha karmaşık)
            suggestions = {
                "recommended_topics": [],
                "difficulty_adjustment": "maintain",
                "learning_resources": [],
                "next_steps": [],
            }

            # Mesaj analizi
            if "matematik" in message.lower():
                suggestions["recommended_topics"] = ["Cebir", "Geometri", "Analiz"]
                suggestions["learning_resources"] = [
                    "Khan Academy Matematik",
                    "YouTube Matematik Kanalları",
                ]
            elif "fen" in message.lower() or "fizik" in message.lower():
                suggestions["recommended_topics"] = [
                    "Mekanik",
                    "Termodinamik",
                    "Elektrik",
                ]
                suggestions["learning_resources"] = [
                    "Fen Bilimleri Videoları",
                    "Deney Örnekleri",
                ]

            # ZPD'ye göre zorluk ayarlaması
            if context.zpd_range:
                if context.difficulty_level < context.zpd_range.optimal_challenge:
                    suggestions["difficulty_adjustment"] = "increase"
                elif context.difficulty_level > context.zpd_range.upper_bound:
                    suggestions["difficulty_adjustment"] = "decrease"

            suggestions["next_steps"] = [
                "Konuyu pekiştirmek için pratik yapın",
                "İlgili videoları izleyin",
                "Konu testini çözün",
            ]

            return suggestions

        except Exception as e:
            logger.error(f"Learning path suggestions error: {str(e)}")
            return {}

    async def _get_study_buddy_suggestions(
        self, context: ChatContext, message: str
    ) -> Dict[str, Any]:
        """Study Buddy Agent önerileri"""
        try:
            suggestions = {
                "quiz_available": False,
                "flashcards_available": False,
                "practice_questions": [],
                "study_tips": [],
            }

            # Quiz önerisi
            if "test" in message.lower() or "sınav" in message.lower():
                suggestions["quiz_available"] = True
                suggestions["practice_questions"] = [
                    "Bu konuda 5 soruluk hızlı test çözmek ister misiniz?",
                    "Zorluk seviyenizi test etmek için adaptif sınav önerebilirim",
                ]

            # Flashcard önerisi
            if "ezberle" in message.lower() or "hatırla" in message.lower():
                suggestions["flashcards_available"] = True

            # Çalışma ipuçları
            suggestions["study_tips"] = [
                "Konuyu küçük parçalara bölün",
                "Düzenli tekrar yapın",
                "Örneklerle pekiştirin",
            ]

            return suggestions

        except Exception as e:
            logger.error(f"Study buddy suggestions error: {str(e)}")
            return {}

    async def _get_accessibility_suggestions(
        self, context: ChatContext, message: str
    ) -> Dict[str, Any]:
        """Accessibility Agent önerileri"""
        try:
            suggestions = {
                "simplification_needed": False,
                "bionic_reading_recommended": False,
                "alternative_formats": [],
                "accessibility_score": 0.8,
            }

            # Karmaşıklık kontrolü
            complexity = await turkish_nlp_service.analyze_text_complexity(message)
            if complexity.get("overall_complexity", 0) > 0.7:
                suggestions["simplification_needed"] = True
                suggestions["bionic_reading_recommended"] = True
                suggestions["alternative_formats"] = [
                    "Basitleştirilmiş metin",
                    "Görsel açıklama",
                    "Ses kaydı",
                ]

            return suggestions

        except Exception as e:
            logger.error(f"Accessibility suggestions error: {str(e)}")
            return {}

    async def _analyze_agent_synergy(self, student_id: str) -> Dict[str, Any]:
        """Agent sinerji analizi"""
        try:
            synergy_data = {
                "coordination_score": 0.8,
                "active_agents": [],
                "shared_insights": [],
                "recommendations": [],
            }

            # Blackboard'dan veri al
            learning_data = self.blackboard.get(f"learning_suggestions_{student_id}")
            study_data = self.blackboard.get(f"study_suggestions_{student_id}")
            accessibility_data = self.blackboard.get(
                f"accessibility_suggestions_{student_id}"
            )

            # Aktif agent'ları belirle
            if learning_data:
                synergy_data["active_agents"].append("learning_path")
            if study_data:
                synergy_data["active_agents"].append("study_buddy")
            if accessibility_data:
                synergy_data["active_agents"].append("accessibility")

            # Ortak öneriler
            if len(synergy_data["active_agents"]) > 1:
                synergy_data["shared_insights"] = [
                    "Çoklu agent koordinasyonu aktif",
                    "Kişiselleştirilmiş öğrenme yolu oluşturuluyor",
                    "Adaptif zorluk ayarlaması yapılıyor",
                ]

                synergy_data["recommendations"] = [
                    "Öğrenme stilinize uygun içerik öneriliyor",
                    "ZPD tabanlı zorluk ayarlaması uygulanıyor",
                    "Erişilebilirlik optimizasyonu yapılıyor",
                ]

            return synergy_data

        except Exception as e:
            logger.error(f"Agent synergy analysis error: {str(e)}")
            return {}

    async def _generate_adaptive_response(
        self,
        context: ChatContext,
        message: str,
        nlp_analysis: Dict[str, Any],
        agent_insights: Dict[str, Any],
    ) -> str:
        """Adaptif yanıt oluştur"""
        try:
            # Yanıt moduna göre prompt oluştur
            if context.response_mode == ResponseMode.ADAPTIVE:
                prompt = await self._create_adaptive_prompt(
                    context, message, nlp_analysis, agent_insights
                )
            elif context.response_mode == ResponseMode.LEARNING_STYLE:
                prompt = await self._create_learning_style_prompt(
                    context, message, agent_insights
                )
            elif context.response_mode == ResponseMode.SIMPLIFIED:
                prompt = await self._create_simplified_prompt(
                    context, message, nlp_analysis
                )
            else:
                prompt = await self._create_comprehensive_prompt(
                    context, message, agent_insights
                )

            # LLM ile yanıt oluştur
            result = await llm_service.generate(
                prompt=prompt, temperature=0.7, max_tokens=500
            )

            if result["success"]:
                response = result["text"].strip()

                # ZPD'ye göre ayarlama
                if context.zpd_range:
                    response = await self._adjust_response_to_zpd(
                        response, context.zpd_range
                    )

                return response
            else:
                return "Üzgünüm, şu anda yanıt oluşturamıyorum. Lütfen tekrar deneyin."

        except Exception as e:
            logger.error(f"Generate adaptive response error: {str(e)}")
            return "Bir hata oluştu. Lütfen tekrar deneyin."

    async def _create_adaptive_prompt(
        self,
        context: ChatContext,
        message: str,
        nlp_analysis: Dict[str, Any],
        agent_insights: Dict[str, Any],
    ) -> str:
        """Adaptif prompt oluştur"""

        # Öğrenci profil bilgileri
        profile_info = ""
        if context.learning_style_profile:
            profile_info = (
                f"Öğrenme stili: {context.learning_style_profile.hybrid_code}"
            )

        # ZPD bilgileri
        zpd_info = ""
        if context.zpd_range:
            zpd_info = (
                f"Optimal zorluk seviyesi: {context.zpd_range.optimal_challenge:.2f}"
            )

        # Agent önerileri
        agent_info = ""
        if agent_insights:
            agent_info = f"Agent önerileri: {json.dumps(agent_insights, ensure_ascii=False)[:200]}"

        # Morfoloji bilgileri
        morphology_info = ""
        if nlp_analysis.get("morphology"):
            avg_complexity = nlp_analysis.get("avg_word_complexity", 0)
            morphology_info = f"Mesaj karmaşıklığı: {avg_complexity:.2f}"

        prompt = f"""
Sen Türk öğrenciler için özel geliştirilmiş bir AI eğitim asistanısın.

Öğrenci Profili:
{profile_info}
{zpd_info}

Mesaj Analizi:
{morphology_info}

Agent Önerileri:
{agent_info}

Öğrenci Sorusu: "{message}"

Yanıt Kuralları:
1. Türkçe eğitim terminolojisi kullan
2. Öğrencinin seviyesine uygun açıklama yap
3. Motivasyonel ve destekleyici ol
4. Somut örnekler ver
5. Agent önerilerini dikkate al
6. ZPD seviyesine uygun zorluk kullan

Yanıt:
"""

        return prompt

    async def _create_learning_style_prompt(
        self, context: ChatContext, message: str, agent_insights: Dict[str, Any]
    ) -> str:
        """Öğrenme stili bazlı prompt"""

        style_guidance = ""
        if context.learning_style_profile:
            vark_profile = context.learning_style_profile.vark_profile
            dominant_style = vark_profile.dominant_vark.value

            if dominant_style == "visual":
                style_guidance = "Görsel örnekler, diyagramlar ve şemalar kullan"
            elif dominant_style == "auditory":
                style_guidance = "Sesli açıklamalar ve ritimli örnekler ver"
            elif dominant_style == "reading":
                style_guidance = "Detaylı metin açıklamaları ve okuma önerileri sun"
            elif dominant_style == "kinesthetic":
                style_guidance = "Uygulamalı örnekler ve deneyim odaklı açıklamalar yap"

        prompt = f"""
Öğrencinin öğrenme stiline uygun yanıt ver.

Öğrenme Stili Rehberi: {style_guidance}

Öğrenci Sorusu: "{message}"

Bu öğrenme stiline uygun, kişiselleştirilmiş yanıt ver:
"""

        return prompt

    async def _create_simplified_prompt(
        self, context: ChatContext, message: str, nlp_analysis: Dict[str, Any]
    ) -> str:
        """Basitleştirilmiş prompt"""

        complexity_level = nlp_analysis.get("complexity", {}).get(
            "overall_complexity", 0.5
        )

        prompt = f"""
Öğrencinin sorusuna basit ve anlaşılır yanıt ver.

Mesaj karmaşıklığı: {complexity_level:.2f}

Basitleştirme Kuralları:
1. Kısa cümleler kullan
2. Basit kelimeler tercih et
3. Teknik terimleri açıkla
4. Adım adım açıkla
5. Örneklerle destekle

Öğrenci Sorusu: "{message}"

Basit ve anlaşılır yanıt:
"""

        return prompt

    async def _create_comprehensive_prompt(
        self, context: ChatContext, message: str, agent_insights: Dict[str, Any]
    ) -> str:
        """Kapsamlı prompt"""

        prompt = f"""
Öğrencinin sorusuna kapsamlı ve detaylı yanıt ver.

Tüm agent önerileri: {json.dumps(agent_insights, ensure_ascii=False)}

Öğrenci Sorusu: "{message}"

Kapsamlı yanıt (öğrenme yolu, pratik önerileri ve kaynak önerileri dahil):
"""

        return prompt

    async def _adjust_response_to_zpd(
        self, response: str, zpd_range: TurkishZPDRange
    ) -> str:
        """Yanıtı ZPD'ye göre ayarla"""
        try:
            # ZPD seviyesine göre yanıtı ayarla
            if zpd_range.optimal_challenge < 0.3:
                # Çok kolay - daha detaylı açıklama ekle
                response += "\n\nEk açıklama: Bu konuyu daha iyi anlamak için temel kavramları gözden geçirebilirsiniz."
            elif zpd_range.optimal_challenge > 0.7:
                # Zor - daha ileri seviye bilgi ekle
                response += "\n\nİleri seviye: Bu konuyla ilgili daha derinlemesine araştırma yapabilirsiniz."

            return response

        except Exception as e:
            logger.error(f"Adjust response to ZPD error: {str(e)}")
            return response

    async def _adjust_difficulty(
        self, context: ChatContext, nlp_analysis: Dict[str, Any]
    ) -> bool:
        """Zorluk seviyesini ayarla"""
        try:
            # Mesaj karmaşıklığına göre zorluk ayarla
            message_complexity = nlp_analysis.get("avg_word_complexity", 0.5)

            # ZPD'ye göre ayarlama
            if context.zpd_range:
                target_difficulty = context.zpd_range.optimal_challenge

                # Mevcut zorluk ile hedef arasındaki fark
                difficulty_diff = abs(context.difficulty_level - target_difficulty)

                if difficulty_diff > 0.1:  # %10'dan fazla fark varsa ayarla
                    # Yavaş ayarlama (0.05 adımlarla)
                    if context.difficulty_level < target_difficulty:
                        context.difficulty_level = min(
                            1.0, context.difficulty_level + 0.05
                        )
                    else:
                        context.difficulty_level = max(
                            0.0, context.difficulty_level - 0.05
                        )

                    return True

            return False

        except Exception as e:
            logger.error(f"Adjust difficulty error: {str(e)}")
            return False

    async def _generate_suggested_actions(
        self, context: ChatContext, agent_insights: Dict[str, Any]
    ) -> List[str]:
        """Önerilen eylemleri oluştur"""
        try:
            actions = []

            # Learning Path Agent önerileri
            if "learning_path" in agent_insights:
                learning_suggestions = agent_insights["learning_path"]
                if learning_suggestions.get("quiz_available"):
                    actions.append("Konu testi çöz")
                if learning_suggestions.get("recommended_topics"):
                    actions.append("İlgili konuları keşfet")

            # Study Buddy Agent önerileri
            if "study_buddy" in agent_insights:
                study_suggestions = agent_insights["study_buddy"]
                if study_suggestions.get("flashcards_available"):
                    actions.append("Bilgi kartları oluştur")
                if study_suggestions.get("practice_questions"):
                    actions.append("Pratik soruları çöz")

            # Accessibility Agent önerileri
            if "accessibility" in agent_insights:
                accessibility_suggestions = agent_insights["accessibility"]
                if accessibility_suggestions.get("bionic_reading_recommended"):
                    actions.append("Bionic Reading'i dene")
                if accessibility_suggestions.get("simplification_needed"):
                    actions.append("Basitleştirilmiş açıklama al")

            # Genel öneriler
            if not actions:
                actions = ["Konuyu pekiştir", "İlgili videoları izle", "Pratik yap"]

            return actions[:5]  # Maksimum 5 öneri

        except Exception as e:
            logger.error(f"Generate suggested actions error: {str(e)}")
            return ["Çalışmaya devam et"]

    async def get_chat_history(
        self, student_id: str, session_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Sohbet geçmişini getir"""
        try:
            if session_id:
                context_key = f"{student_id}_{session_id}"
                context = self.contexts.get(context_key)
                if context:
                    return context.conversation_history[-limit:]
            else:
                # Tüm oturumlardan geçmişi topla
                all_history = []
                for key, context in self.contexts.items():
                    if key.startswith(f"{student_id}_"):
                        all_history.extend(context.conversation_history)

                # Tarihe göre sırala ve limit uygula
                all_history.sort(key=lambda x: x["timestamp"], reverse=True)
                return all_history[:limit]

            return []

        except Exception as e:
            logger.error(f"Get chat history error: {str(e)}")
            return []

    async def get_chat_analytics(
        self, student_id: str, time_range_days: int = 7
    ) -> Dict[str, Any]:
        """Sohbet analitikleri"""
        try:
            analytics = {
                "total_messages": 0,
                "total_sessions": 0,
                "avg_session_length": 0,
                "most_discussed_topics": [],
                "learning_progress": {},
                "agent_usage": {},
                "difficulty_trend": [],
            }

            # Belirtilen zaman aralığındaki veriler
            cutoff_date = datetime.now() - timedelta(days=time_range_days)

            sessions = []
            for key, context in self.contexts.items():
                if (
                    key.startswith(f"{student_id}_")
                    and context.created_at >= cutoff_date
                ):
                    sessions.append(context)

            analytics["total_sessions"] = len(sessions)

            # Mesaj sayısı ve ortalama oturum uzunluğu
            total_messages = 0
            session_lengths = []

            for context in sessions:
                messages_in_session = len(context.conversation_history)
                total_messages += messages_in_session
                session_lengths.append(messages_in_session)

            analytics["total_messages"] = total_messages
            if session_lengths:
                analytics["avg_session_length"] = sum(session_lengths) / len(
                    session_lengths
                )

            # En çok tartışılan konular
            topic_counts = {}
            for context in sessions:
                topic = context.subject
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

            analytics["most_discussed_topics"] = sorted(
                topic_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]

            # Zorluk trendi
            for context in sessions:
                analytics["difficulty_trend"].append(
                    {
                        "date": context.created_at.isoformat(),
                        "difficulty": context.difficulty_level,
                    }
                )

            return analytics

        except Exception as e:
            logger.error(f"Get chat analytics error: {str(e)}")
            return {}


# Service instance
enhanced_chat_service = EnhancedChatService()


# API Endpoints
@router.post("/message", response_model=Dict[str, Any])
async def send_message(request: ChatMessageRequest):
    """
    Gelişmiş AI sohbet mesajı gönder
    """
    try:
        response = await enhanced_chat_service.process_message(
            student_id=request.student_id,
            message=request.message,
            subject=request.subject,
            session_id=request.session_id,
            response_mode=request.response_mode,
            include_bionic=request.include_bionic,
            context_data=request.context_data,
        )

        return {
            "success": True,
            "data": {
                "response_id": response.response_id,
                "message": response.message,
                "bionic_message": response.bionic_message,
                "message_type": response.message_type.value,
                "confidence_score": response.confidence_score,
                "learning_insights": response.learning_insights,
                "agent_contributions": response.agent_contributions,
                "suggested_actions": response.suggested_actions,
                "difficulty_adjusted": response.difficulty_adjusted,
                "zpd_applied": response.zpd_applied,
                "morphology_analysis": response.morphology_analysis,
                "processing_time_ms": response.processing_time_ms,
                "metadata": response.metadata,
            },
        }

    except Exception as e:
        logger.error(f"Send message API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=Dict[str, Any])
async def get_chat_history(request: ChatHistoryRequest = Depends()):
    """
    Sohbet geçmişini getir
    """
    try:
        history = await enhanced_chat_service.get_chat_history(
            student_id=request.student_id,
            session_id=request.session_id,
            limit=request.limit,
        )

        return {"success": True, "data": {"history": history, "count": len(history)}}

    except Exception as e:
        logger.error(f"Get chat history API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=Dict[str, Any])
async def get_chat_analytics(request: ChatAnalyticsRequest = Depends()):
    """
    Sohbet analitikleri getir
    """
    try:
        analytics = await enhanced_chat_service.get_chat_analytics(
            student_id=request.student_id, time_range_days=request.time_range_days
        )

        return {"success": True, "data": analytics}

    except Exception as e:
        logger.error(f"Get chat analytics API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class BionicReadingRequest(BaseModel):
    text: str = Field(..., description="Bionic Reading uygulanacak metin")


@router.post("/bionic-reading", response_model=Dict[str, Any])
async def apply_bionic_reading(request: BionicReadingRequest):
    """
    Metne Bionic Reading uygula
    """
    try:
        result = await bionic_reader.apply_bionic_reading(request.text)

        return {
            "success": result.success,
            "data": {
                "original_text": result.original_text,
                "bionic_text": result.bionic_text,
                "processing_time_ms": result.processing_time_ms,
                "word_count": result.word_count,
                "bold_ratio": result.bold_ratio,
            },
            "error": result.error_message,
        }

    except Exception as e:
        logger.error(f"Apply bionic reading API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{student_id}/{session_id}", response_model=Dict[str, Any])
async def get_chat_context(student_id: str, session_id: str):
    """
    Sohbet bağlamını getir
    """
    try:
        context_key = f"{student_id}_{session_id}"
        context = enhanced_chat_service.contexts.get(context_key)

        if not context:
            raise HTTPException(status_code=404, detail="Sohbet bağlamı bulunamadı")

        return {
            "success": True,
            "data": {
                "student_id": context.student_id,
                "session_id": context.session_id,
                "subject": context.subject,
                "current_topic": context.current_topic,
                "difficulty_level": context.difficulty_level,
                "response_mode": context.response_mode.value,
                "learning_style_profile": context.learning_style_profile.hybrid_code
                if context.learning_style_profile
                else None,
                "zpd_range": {
                    "current_level": context.zpd_range.current_level,
                    "optimal_challenge": context.zpd_range.optimal_challenge,
                    "upper_bound": context.zpd_range.upper_bound,
                }
                if context.zpd_range
                else None,
                "conversation_count": len(context.conversation_history),
                "created_at": context.created_at.isoformat(),
                "last_updated": context.last_updated.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get chat context API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/context/{student_id}/{session_id}")
async def clear_chat_context(student_id: str, session_id: str):
    """
    Sohbet bağlamını temizle
    """
    try:
        context_key = f"{student_id}_{session_id}"
        if context_key in enhanced_chat_service.contexts:
            del enhanced_chat_service.contexts[context_key]

            return {"success": True, "message": "Sohbet bağlamı temizlendi"}
        else:
            raise HTTPException(status_code=404, detail="Sohbet bağlamı bulunamadı")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear chat context API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
