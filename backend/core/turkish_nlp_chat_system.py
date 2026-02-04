"""
Türkçe NLP Chat Sistemi - Bağlamsal konuşma ve eğitim desteği
Requirements: 2.1, 2.2, 2.3, 2.5, 2.6
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .berturk_service import BERTurkService
from .llm_service import llm_service
from .turkish_nlp_service import turkish_nlp_service

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Konuşma bağlamı"""

    student_id: str
    session_id: str
    subject: str
    current_topic: str | None = None
    difficulty_level: float = 0.5  # 0.0 - 1.0
    learning_style: str | None = None
    conversation_history: list[dict[str, Any]] = None
    context_keywords: list[str] = None
    last_activity: datetime = None
    motivation_level: float = 0.5
    confusion_indicators: list[str] = None

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.context_keywords is None:
            self.context_keywords = []
        if self.last_activity is None:
            self.last_activity = datetime.now()
        if self.confusion_indicators is None:
            self.confusion_indicators = []


@dataclass
class EducationalResponse:
    """Eğitim odaklı yanıt"""

    response_text: str
    explanation_type: str  # definition, example, step_by_step, clarification
    difficulty_level: float
    related_concepts: list[str]
    follow_up_questions: list[str]
    motivational_elements: list[str]
    bionic_reading_text: str | None = None
    confidence_score: float = 0.0


@dataclass
class StepByStepSolution:
    """Adım adım çözüm"""

    problem: str
    steps: list[dict[str, Any]]
    final_answer: str
    explanation: str
    difficulty_level: float
    estimated_time_minutes: int
    related_topics: list[str]


class TurkishNLPChatSystem:
    """
    Türkçe NLP Chat Sistemi
    Bağlamsal konuşmalar, eğitim terminolojisi ve adım adım çözümler
    """

    def __init__(self):
        self.nlp_service = turkish_nlp_service
        self.berturk_service = BERTurkService()

        # Aktif konuşma bağlamları
        self.active_contexts: dict[str, ConversationContext] = {}

        # Eğitim terminolojisi sözlüğü
        self.educational_terminology = self._load_educational_terminology()

        # Konu hiyerarşisi
        self.subject_hierarchy = self._load_subject_hierarchy()

        # Çözüm şablonları
        self.solution_templates = self._load_solution_templates()

        # Motivasyonel ifadeler
        self.motivational_phrases = self._load_motivational_phrases()

        # Bağlam yönetimi ayarları
        self.context_settings = {
            "max_history_length": 20,
            "context_timeout_minutes": 30,
            "min_confidence_threshold": 0.6,
            "max_response_length": 500,
        }

        # Performans metrikleri
        self.performance_stats = {
            "total_conversations": 0,
            "successful_responses": 0,
            "context_switches": 0,
            "step_by_step_requests": 0,
        }

    async def initialize(self) -> bool:
        """Chat sistemini başlat"""
        try:
            logger.info("Türkçe NLP Chat Sistemi başlatılıyor...")

            # NLP servislerini başlat
            nlp_initialized = await self.nlp_service.initialize()
            berturk_initialized = await self.berturk_service.initialize()

            if not nlp_initialized:
                logger.warning(
                    "Turkish NLP servisi başlatılamadı, fallback modda çalışılacak"
                )

            if not berturk_initialized:
                logger.warning(
                    "BERTurk servisi başlatılamadı, basit duygu analizi kullanılacak"
                )

            logger.info("Türkçe NLP Chat Sistemi başarıyla başlatıldı")
            return True

        except Exception as e:
            logger.error(f"Chat sistemi başlatılırken hata: {e}")
            return False

    async def process_message(
        self,
        student_id: str,
        message: str,
        session_id: str | None = None,
        subject: str = "genel",
        context_data: dict[str, Any] | None = None,
    ) -> EducationalResponse:
        """
        Öğrenci mesajını işle ve eğitim odaklı yanıt üret

        Args:
            student_id: Öğrenci ID'si
            message: Öğrenci mesajı
            session_id: Oturum ID'si
            subject: Konu alanı
            context_data: Ek bağlam verisi

        Returns:
            EducationalResponse: Eğitim odaklı yanıt
        """
        try:
            self.performance_stats["total_conversations"] += 1

            # Konuşma bağlamını al veya oluştur
            context = await self._get_or_create_context(
                student_id, session_id, subject, context_data
            )

            # Mesajı analiz et
            message_analysis = await self._analyze_message(message, context)

            # Bağlamı güncelle
            await self._update_context(context, message, message_analysis)

            # Yanıt türünü belirle
            response_type = await self._determine_response_type(
                message_analysis, context
            )

            # Yanıt üret
            response = await self._generate_educational_response(
                message, message_analysis, context, response_type
            )

            # Bağlamı kaydet
            await self._save_context(context)

            self.performance_stats["successful_responses"] += 1

            return response

        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {e}")
            return self._create_error_response(message, str(e))

    async def _get_or_create_context(
        self,
        student_id: str,
        session_id: str | None,
        subject: str,
        context_data: dict[str, Any] | None,
    ) -> ConversationContext:
        """Konuşma bağlamını al veya oluştur"""

        context_key = f"{student_id}_{session_id or 'default'}"

        if context_key in self.active_contexts:
            context = self.active_contexts[context_key]

            # Bağlam timeout kontrolü
            if datetime.now() - context.last_activity > timedelta(
                minutes=self.context_settings["context_timeout_minutes"]
            ):
                # Eski bağlamı temizle ve yeni oluştur
                logger.info(
                    f"Bağlam timeout oldu, yeni bağlam oluşturuluyor: {context_key}"
                )
                context = self._create_new_context(
                    student_id, session_id, subject, context_data
                )
                self.performance_stats["context_switches"] += 1
            else:
                # Mevcut bağlamı güncelle
                context.last_activity = datetime.now()
                if context_data:
                    context.learning_style = context_data.get(
                        "learning_style", context.learning_style
                    )
                    context.difficulty_level = context_data.get(
                        "difficulty_level", context.difficulty_level
                    )
        else:
            # Yeni bağlam oluştur
            context = self._create_new_context(
                student_id, session_id, subject, context_data
            )

        self.active_contexts[context_key] = context
        return context

    def _create_new_context(
        self,
        student_id: str,
        session_id: str | None,
        subject: str,
        context_data: dict[str, Any] | None,
    ) -> ConversationContext:
        """Yeni konuşma bağlamı oluştur"""

        return ConversationContext(
            student_id=student_id,
            session_id=session_id or f"session_{datetime.now().timestamp()}",
            subject=subject,
            difficulty_level=context_data.get("difficulty_level", 0.5)
            if context_data
            else 0.5,
            learning_style=context_data.get("learning_style") if context_data else None,
            last_activity=datetime.now(),
        )

    async def _analyze_message(
        self, message: str, context: ConversationContext
    ) -> dict[str, Any]:
        """Mesajı analiz et"""

        analysis = {
            "original_message": message,
            "normalized_message": "",
            "intent": "general",
            "sentiment": None,
            "educational_terms": [],
            "complexity_level": 0.5,
            "question_type": None,
            "confusion_indicators": [],
            "help_request": False,
        }

        try:
            # Metni normalize et
            normalization_result = await self.nlp_service.normalize_text(message)
            analysis["normalized_message"] = normalization_result.normalized_text

            # Duygu analizi
            if hasattr(self.berturk_service, "analyze_sentiment"):
                sentiment_result = await self.berturk_service.analyze_sentiment(
                    message, include_emotions=True, educational_context=True
                )
                analysis["sentiment"] = sentiment_result

            # Intent tespiti
            if hasattr(self.berturk_service, "detect_intent"):
                intent_result = await self.berturk_service.detect_intent(message)
                analysis["intent"] = intent_result.intent
                analysis["help_request"] = intent_result.intent in [
                    "help_request",
                    "confusion",
                ]

            # Eğitim terminolojisi tespiti
            analysis["educational_terms"] = self._detect_educational_terms(message)

            # Soru türü analizi
            analysis["question_type"] = self._analyze_question_type(message)

            # Karışıklık göstergeleri
            analysis["confusion_indicators"] = self._detect_confusion_indicators(
                message
            )

            # Metin karmaşıklığı
            complexity_result = await self.nlp_service.analyze_text_complexity(message)
            analysis["complexity_level"] = complexity_result.get(
                "overall_complexity", 0.5
            )

        except Exception as e:
            logger.error(f"Mesaj analizi hatası: {e}")

        return analysis

    def _detect_educational_terms(self, message: str) -> list[str]:
        """Eğitim terminolojisi tespit et"""

        detected_terms = []
        message_lower = message.lower()

        for category, terms in self.educational_terminology.items():
            for term in terms:
                if term.lower() in message_lower:
                    detected_terms.append(term)

        return list(set(detected_terms))

    def _analyze_question_type(self, message: str) -> str | None:
        """Soru türünü analiz et"""

        message_lower = message.lower()

        # Soru kalıpları
        question_patterns = {
            "definition": ["nedir", "ne demek", "tanımı", "anlamı"],
            "explanation": ["nasıl", "neden", "niçin", "açıkla"],
            "example": ["örnek", "misal", "örnekle"],
            "step_by_step": ["adım adım", "nasıl çözülür", "çözüm", "yöntem"],
            "comparison": ["fark", "karşılaştır", "benzer", "aynı"],
            "application": ["kullan", "uygula", "yap", "hesapla"],
        }

        for question_type, patterns in question_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return question_type

        # Soru işareti kontrolü
        if "?" in message:
            return "general_question"

        return None

    def _detect_confusion_indicators(self, message: str) -> list[str]:
        """Karışıklık göstergelerini tespit et"""

        confusion_patterns = [
            "anlamadım",
            "karışık",
            "zor",
            "anlayamadım",
            "kafam karıştı",
            "net değil",
            "belirsiz",
            "açık değil",
            "anlaşılmıyor",
        ]

        message_lower = message.lower()
        detected = []

        for pattern in confusion_patterns:
            if pattern in message_lower:
                detected.append(pattern)

        return detected

    async def _update_context(
        self, context: ConversationContext, message: str, analysis: dict[str, Any]
    ):
        """Konuşma bağlamını güncelle"""

        # Konuşma geçmişine ekle
        context.conversation_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "analysis": analysis,
            }
        )

        # Geçmiş uzunluğunu sınırla
        if (
            len(context.conversation_history)
            > self.context_settings["max_history_length"]
        ):
            context.conversation_history = context.conversation_history[
                -self.context_settings["max_history_length"] :
            ]

        # Bağlam anahtar kelimelerini güncelle
        if analysis["educational_terms"]:
            context.context_keywords.extend(analysis["educational_terms"])
            context.context_keywords = list(set(context.context_keywords))[
                -10:
            ]  # Son 10 anahtar kelime

        # Mevcut konuyu güncelle
        if analysis["educational_terms"]:
            context.current_topic = analysis["educational_terms"][0]

        # Motivasyon seviyesini güncelle
        if analysis["sentiment"]:
            sentiment_data = analysis["sentiment"]
            if hasattr(sentiment_data, "educational_context"):
                motivation = sentiment_data.educational_context.get("motivation", 0.5)
                frustration = sentiment_data.educational_context.get("frustration", 0.0)
                context.motivation_level = max(
                    0.0, min(1.0, motivation - frustration * 0.5)
                )

        # Karışıklık göstergelerini güncelle
        if analysis["confusion_indicators"]:
            context.confusion_indicators.extend(analysis["confusion_indicators"])
            context.confusion_indicators = context.confusion_indicators[
                -5:
            ]  # Son 5 gösterge

        context.last_activity = datetime.now()

    async def _determine_response_type(
        self, analysis: dict[str, Any], context: ConversationContext
    ) -> str:
        """Yanıt türünü belirle"""

        # Adım adım çözüm talebi
        if analysis["question_type"] == "step_by_step":
            return "step_by_step_solution"

        # Tanım talebi
        if analysis["question_type"] == "definition":
            return "definition"

        # Açıklama talebi
        if analysis["question_type"] == "explanation":
            return "explanation"

        # Örnek talebi
        if analysis["question_type"] == "example":
            return "example"

        # Karışıklık durumu
        if analysis["confusion_indicators"] or context.confusion_indicators:
            return "clarification"

        # Yardım talebi
        if analysis["help_request"]:
            return "help"

        # Motivasyon desteği
        if context.motivation_level < 0.4:
            return "motivational_support"

        # Genel konuşma
        return "general_conversation"

    async def _generate_educational_response(
        self,
        message: str,
        analysis: dict[str, Any],
        context: ConversationContext,
        response_type: str,
    ) -> EducationalResponse:
        """Eğitim odaklı yanıt üret"""

        try:
            if response_type == "step_by_step_solution":
                return await self._generate_step_by_step_solution(
                    message, analysis, context
                )
            if response_type == "definition":
                return await self._generate_definition_response(
                    message, analysis, context
                )
            if response_type == "explanation":
                return await self._generate_explanation_response(
                    message, analysis, context
                )
            if response_type == "example":
                return await self._generate_example_response(message, analysis, context)
            if response_type == "clarification":
                return await self._generate_clarification_response(
                    message, analysis, context
                )
            if response_type == "help":
                return await self._generate_help_response(message, analysis, context)
            if response_type == "motivational_support":
                return await self._generate_motivational_response(
                    message, analysis, context
                )
            return await self._generate_general_response(message, analysis, context)

        except Exception as e:
            logger.error(f"Yanıt üretme hatası: {e}")
            return self._create_error_response(message, str(e))

    async def _generate_step_by_step_solution(
        self, message: str, analysis: dict[str, Any], context: ConversationContext
    ) -> EducationalResponse:
        """Adım adım çözüm üret"""

        self.performance_stats["step_by_step_requests"] += 1

        # Konu alanına göre çözüm şablonu seç
        template = self.solution_templates.get(
            context.subject, self.solution_templates["genel"]
        )

        # LLM ile adım adım çözüm üret
        prompt = f"""
        Türkçe eğitim asistanı olarak, aşağıdaki soruya adım adım çözüm üret:
        
        Soru: {message}
        Konu: {context.subject}
        Öğrenci seviyesi: {context.difficulty_level}
        Bağlam: {', '.join(context.context_keywords) if context.context_keywords else 'Yok'}
        
        Lütfen şu formatta yanıt ver:
        1. Problemin anlaşılması
        2. Çözüm adımları (her adımı açıkla)
        3. Final cevap
        4. Kontrol ve doğrulama
        
        Türkçe eğitim terminolojisi kullan ve öğrencinin anlayabileceği seviyede açıkla.
        """

        try:
            llm_response = await llm_service.generate(
                prompt=prompt, temperature=0.3, max_tokens=800
            )

            if llm_response.get("success"):
                response_text = llm_response.get(
                    "response", llm_response.get("text", "")
                )

                # Bionic Reading uygula
                bionic_text = await self._apply_bionic_reading(response_text)

                return EducationalResponse(
                    response_text=response_text,
                    explanation_type="step_by_step",
                    difficulty_level=context.difficulty_level,
                    related_concepts=analysis["educational_terms"],
                    follow_up_questions=self._generate_follow_up_questions(
                        message, context
                    ),
                    motivational_elements=self._get_motivational_elements(),
                    bionic_reading_text=bionic_text,
                    confidence_score=0.8,
                )
            return self._create_fallback_step_solution(message, context)

        except Exception as e:
            logger.error(f"Adım adım çözüm üretme hatası: {e}")
            return self._create_fallback_step_solution(message, context)

    async def _generate_definition_response(
        self, message: str, analysis: dict[str, Any], context: ConversationContext
    ) -> EducationalResponse:
        """Tanım yanıtı üret"""

        # Eğitim terminolojisinden tanım bul
        terms = analysis["educational_terms"]

        if terms:
            term = terms[0]
            definition = self._get_term_definition(term, context.subject)

            if definition:
                response_text = f"**{term}**: {definition}"

                # Ek açıklama ekle
                response_text += f"\n\n[BOOKS] Bu kavram {context.subject} alanında önemli bir terimdir."

                # Bionic Reading uygula
                bionic_text = await self._apply_bionic_reading(response_text)

                return EducationalResponse(
                    response_text=response_text,
                    explanation_type="definition",
                    difficulty_level=context.difficulty_level,
                    related_concepts=self._get_related_concepts(term),
                    follow_up_questions=[
                        f"{term} ile ilgili örnek verebilir misin?",
                        f"{term} nasıl kullanılır?",
                        f"{term} ile benzer kavramlar nelerdir?",
                    ],
                    motivational_elements=[
                        "Harika soru! Bu kavramı öğrenmek önemli bir adım."
                    ],
                    bionic_reading_text=bionic_text,
                    confidence_score=0.9,
                )

        # Fallback: Genel tanım yanıtı
        return await self._generate_general_response(message, analysis, context)

    async def _generate_explanation_response(
        self, message: str, analysis: dict[str, Any], context: ConversationContext
    ) -> EducationalResponse:
        """Açıklama yanıtı üret"""

        prompt = f"""
        Türkçe eğitim asistanı olarak, aşağıdaki soruyu açıkla:
        
        Soru: {message}
        Konu: {context.subject}
        Öğrenci seviyesi: {context.difficulty_level}
        
        Açıklamayı şu şekilde yap:
        - Basit ve anlaşılır Türkçe kullan
        - Örneklerle destekle
        - Adım adım açıkla
        - Öğrencinin seviyesine uygun ol
        
        Maksimum 300 kelime kullan.
        """

        try:
            llm_response = await llm_service.generate(
                prompt=prompt, temperature=0.4, max_tokens=600
            )

            if llm_response.get("success"):
                response_text = llm_response.get(
                    "response", llm_response.get("text", "")
                )
                bionic_text = await self._apply_bionic_reading(response_text)

                return EducationalResponse(
                    response_text=response_text,
                    explanation_type="explanation",
                    difficulty_level=context.difficulty_level,
                    related_concepts=analysis["educational_terms"],
                    follow_up_questions=self._generate_follow_up_questions(
                        message, context
                    ),
                    motivational_elements=self._get_motivational_elements(),
                    bionic_reading_text=bionic_text,
                    confidence_score=0.7,
                )
            return self._create_fallback_explanation(message, context)

        except Exception as e:
            logger.error(f"Açıklama yanıtı üretme hatası: {e}")
            return self._create_fallback_explanation(message, context)

    async def _generate_example_response(
        self, message: str, analysis: dict[str, Any], context: ConversationContext
    ) -> EducationalResponse:
        """Örnek yanıtı üret"""

        prompt = f"""
        Türkçe eğitim asistanı olarak, aşağıdaki konu için örnekler ver:
        
        Konu: {message}
        Alan: {context.subject}
        Seviye: {context.difficulty_level}
        
        3 farklı örnek ver:
        1. Basit örnek
        2. Orta seviye örnek  
        3. İleri seviye örnek
        
        Her örneği açıkla ve neden önemli olduğunu belirt.
        """

        try:
            llm_response = await llm_service.generate(
                prompt=prompt, temperature=0.5, max_tokens=500
            )

            if llm_response.get("success"):
                response_text = llm_response.get(
                    "response", llm_response.get("text", "")
                )
                bionic_text = await self._apply_bionic_reading(response_text)

                return EducationalResponse(
                    response_text=response_text,
                    explanation_type="example",
                    difficulty_level=context.difficulty_level,
                    related_concepts=analysis["educational_terms"],
                    follow_up_questions=[
                        "Bu örnekleri anladın mı?",
                        "Başka örnekler de verebilir misin?",
                        "Bu örnekleri nasıl uygulayabilirim?",
                    ],
                    motivational_elements=["Örneklerle öğrenmek harika bir yöntem!"],
                    bionic_reading_text=bionic_text,
                    confidence_score=0.8,
                )
            return self._create_fallback_example(message, context)

        except Exception as e:
            logger.error(f"Örnek yanıtı üretme hatası: {e}")
            return self._create_fallback_example(message, context)

    async def _generate_clarification_response(
        self, message: str, analysis: dict[str, Any], context: ConversationContext
    ) -> EducationalResponse:
        """Açıklığa kavuşturma yanıtı üret"""

        confusion_indicators = (
            analysis["confusion_indicators"] + context.confusion_indicators
        )

        response_text = "Anlıyorum, bu konu karışık gelmiş. Hadi birlikte açıklığa kavuşturalım! 🤔\n\n"

        # Basitleştirilmiş açıklama
        if context.current_topic:
            response_text += f"**{context.current_topic}** konusunu daha basit şekilde açıklayayım:\n\n"

            # Zorluk seviyesini düşür
            simplified_level = max(0.1, context.difficulty_level - 0.3)

            prompt = f"""
            Türkçe eğitim asistanı olarak, {context.current_topic} konusunu çok basit şekilde açıkla.
            
            Öğrenci karışıklık yaşıyor. Şu göstergeleri kullandı: {', '.join(confusion_indicators)}
            
            Açıklamayı şöyle yap:
            - Çok basit kelimeler kullan
            - Kısa cümleler kur
            - Günlük hayattan örnekler ver
            - Adım adım ilerle
            - Sabırlı ve destekleyici ol
            
            Maksimum 200 kelime.
            """

            try:
                llm_response = await llm_service.generate_response(
                    prompt=prompt, temperature=0.2, max_tokens=400
                )

                if llm_response.get("success"):
                    response_text += llm_response["response"]
                else:
                    response_text += "Bu konuyu daha basit şekilde açıklayayım..."

            except Exception:
                response_text += "Bu konuyu daha basit şekilde açıklayayım..."

        response_text += "\n\n[BULB] Eğer hala anlaşılmayan yerler varsa, lütfen bana söyle. Birlikte çözeriz!"

        bionic_text = await self._apply_bionic_reading(response_text)

        return EducationalResponse(
            response_text=response_text,
            explanation_type="clarification",
            difficulty_level=max(0.1, context.difficulty_level - 0.3),
            related_concepts=analysis["educational_terms"],
            follow_up_questions=[
                "Şimdi daha anlaşılır mı?",
                "Hangi kısmı daha detaylı açıklayayım?",
                "Başka bir örnek verebilir misin?",
            ],
            motivational_elements=[
                "Merak etme, herkes bazen karışıklık yaşar!",
                "Soru sormak çok güzel, böyle öğreniyoruz!",
                "Adım adım ilerleyeceğiz, acele yok!",
            ],
            bionic_reading_text=bionic_text,
            confidence_score=0.6,
        )

    async def _generate_help_response(
        self, message: str, analysis: dict[str, Any], context: ConversationContext
    ) -> EducationalResponse:
        """Yardım yanıtı üret"""

        response_text = "Tabii ki yardım edebilirim! 🤝\n\n"

        # Yardım türünü belirle
        if analysis["educational_terms"]:
            topic = analysis["educational_terms"][0]
            response_text += (
                f"**{topic}** konusunda size nasıl yardımcı olabilirim?\n\n"
            )
        else:
            response_text += "Size nasıl yardımcı olabilirim?\n\n"

        # Yardım seçenekleri sun
        help_options = [
            "📖 Konuyu baştan açıklayayım",
            "[MAG] Örneklerle göstereyim",
            "[MEMO] Adım adım çözüm vereyim",
            "❓ Sorularınızı yanıtlayayım",
            "[TARGET] Pratik sorular sorayım",
        ]

        response_text += "İşte size yardım edebileceğim yollar:\n\n"
        for option in help_options:
            response_text += f"• {option}\n"

        response_text += "\nHangisini tercih edersiniz? Veya başka bir şekilde yardım istiyorsanız söyleyin!"

        bionic_text = await self._apply_bionic_reading(response_text)

        return EducationalResponse(
            response_text=response_text,
            explanation_type="help",
            difficulty_level=context.difficulty_level,
            related_concepts=analysis["educational_terms"],
            follow_up_questions=[
                "Hangi konuda yardım istiyorsun?",
                "Neyi anlamakta zorlanıyorsun?",
                "Nasıl açıklamamı istiyorsun?",
            ],
            motivational_elements=[
                "Yardım istemek çok akıllıca!",
                "Birlikte her şeyi çözebiliriz!",
                "Öğrenmek için buradayım!",
            ],
            bionic_reading_text=bionic_text,
            confidence_score=0.9,
        )

    async def _generate_motivational_response(
        self, message: str, analysis: dict[str, Any], context: ConversationContext
    ) -> EducationalResponse:
        """Motivasyonel yanıt üret"""

        motivational_messages = [
            "Harika gidiyorsun! [GLOWING_STAR] Her soru sormak seni daha da güçlendiriyor.",
            "Öğrenme yolculuğunda çok iyisin! 💪 Devam et, başarıyorsun!",
            "Merak ettiğin her şey seni daha bilgili yapıyor! [BRAIN] Gurur duyuyorum.",
            "Zorluklarla karşılaştığında pes etmiyorsun, bu harika! [ROCKET]",
            "Her adımda gelişiyorsun! [TRENDING_UP] Kendine güven, çok yeteneklisin!",
        ]

        import random

        base_message = random.choice(motivational_messages)

        response_text = f"{base_message}\n\n"

        # Kişiselleştirilmiş motivasyon
        if context.current_topic:
            response_text += (
                f"**{context.current_topic}** konusunda çok iyi ilerliyorsun. "
            )

        response_text += "Şimdi hangi konuda devam etmek istiyorsun?\n\n"

        # Başarı önerileri
        success_tips = [
            "[BULB] İpucu: Küçük adımlarla ilerlemek en etkili yöntem!",
            "[TARGET] Hedef: Her gün biraz daha öğrenmek bile büyük fark yaratır!",
            "[STAR] Hatırla: Her uzman bir zamanlar başlangıçtaydı!",
            "[FIRE] Motivasyon: Öğrenme arzun seni başarıya götürecek!",
        ]

        response_text += random.choice(success_tips)

        bionic_text = await self._apply_bionic_reading(response_text)

        return EducationalResponse(
            response_text=response_text,
            explanation_type="motivational_support",
            difficulty_level=context.difficulty_level,
            related_concepts=analysis["educational_terms"],
            follow_up_questions=[
                "Hangi konuda devam etmek istiyorsun?",
                "Neyi öğrenmeye meraklısın?",
                "Başka soruların var mı?",
            ],
            motivational_elements=[
                "Sen harikasın!",
                "Başarıyorsun!",
                "Devam et!",
                "Gurur duyuyorum!",
            ],
            bionic_reading_text=bionic_text,
            confidence_score=0.95,
        )

    async def _generate_general_response(
        self, message: str, analysis: dict[str, Any], context: ConversationContext
    ) -> EducationalResponse:
        """Genel konuşma yanıtı üret"""

        prompt = f"""
        Türkçe eğitim asistanı olarak, öğrenci ile doğal bir konuşma yap:
        
        Öğrenci mesajı: {message}
        Konu alanı: {context.subject}
        Bağlam: {', '.join(context.context_keywords) if context.context_keywords else 'Yok'}
        
        Yanıtını şöyle hazırla:
        - Samimi ve destekleyici ol
        - Eğitim odaklı kalmaya çalış
        - Öğrencinin seviyesine uygun konuş
        - Merak uyandırıcı ol
        - Türkçe eğitim terminolojisi kullan
        
        Maksimum 250 kelime.
        """

        try:
            llm_response = await llm_service.generate(
                prompt=prompt, temperature=0.6, max_tokens=500
            )

            if llm_response.get("success"):
                response_text = llm_response.get(
                    "response", llm_response.get("text", "")
                )
            else:
                response_text = "Merhaba! Size nasıl yardımcı olabilirim? Hangi konuda soru sormak istiyorsunuz?"

        except Exception:
            response_text = "Merhaba! Size nasıl yardımcı olabilirim? Hangi konuda soru sormak istiyorsunuz?"

        bionic_text = await self._apply_bionic_reading(response_text)

        return EducationalResponse(
            response_text=response_text,
            explanation_type="general_conversation",
            difficulty_level=context.difficulty_level,
            related_concepts=analysis["educational_terms"],
            follow_up_questions=self._generate_follow_up_questions(message, context),
            motivational_elements=self._get_motivational_elements(),
            bionic_reading_text=bionic_text,
            confidence_score=0.7,
        )

    async def _apply_bionic_reading(self, text: str) -> str:
        """Bionic Reading uygula"""
        try:
            # Basit Bionic Reading implementasyonu
            words = text.split()
            bionic_words = []

            for word in words:
                # Noktalama işaretlerini ayır
                clean_word = re.sub(r"[^\w\sçğıöşüÇĞIİÖŞÜ]", "", word)
                punctuation = re.findall(r"[^\w\sçğıöşüÇĞIİÖŞÜ]", word)

                if len(clean_word) > 3:
                    # İlk %40'ı bold yap
                    bold_length = max(2, int(len(clean_word) * 0.4))
                    bionic_word = (
                        f"**{clean_word[:bold_length]}**{clean_word[bold_length:]}"
                    )

                    # Noktalama işaretlerini geri ekle
                    if punctuation:
                        bionic_word += "".join(punctuation)

                    bionic_words.append(bionic_word)
                else:
                    bionic_words.append(word)

            return " ".join(bionic_words)

        except Exception as e:
            logger.error(f"Bionic Reading hatası: {e}")
            return text

    def _generate_follow_up_questions(
        self, message: str, context: ConversationContext
    ) -> list[str]:
        """Takip soruları üret"""

        base_questions = [
            "Bu konuda başka sorularınız var mı?",
            "Daha detaylı açıklamamı istediğiniz bir kısım var mı?",
            "Örneklerle pekiştirmek ister misiniz?",
        ]

        # Konu bazlı sorular
        if context.current_topic:
            topic_questions = [
                f"{context.current_topic} ile ilgili başka ne öğrenmek istiyorsunuz?",
                f"{context.current_topic} konusunda pratik yapmak ister misiniz?",
                f"{context.current_topic} ile ilgili zorlandığınız başka yerler var mı?",
            ]
            base_questions.extend(topic_questions)

        return base_questions[:3]  # İlk 3 soru

    def _get_motivational_elements(self) -> list[str]:
        """Motivasyonel öğeler al"""
        return [
            "Harika soru!",
            "Çok iyi düşünüyorsunuz!",
            "Öğrenme isteğiniz muhteşem!",
            "Devam edin, başarıyorsunuz!",
        ]

    def _create_error_response(self, message: str, error: str) -> EducationalResponse:
        """Hata yanıtı oluştur"""
        return EducationalResponse(
            response_text="Üzgünüm, mesajınızı işlerken bir sorun yaşadım. Lütfen tekrar dener misiniz?",
            explanation_type="error",
            difficulty_level=0.5,
            related_concepts=[],
            follow_up_questions=["Tekrar dener misiniz?"],
            motivational_elements=["Sorun değil, tekrar deneyelim!"],
            confidence_score=0.0,
        )

    def _create_fallback_step_solution(
        self, message: str, context: ConversationContext
    ) -> EducationalResponse:
        """Fallback adım adım çözüm"""

        response_text = f"""
        **Adım Adım Çözüm Yaklaşımı:**
        
        1. **Problemi Anlayalım**: {message}
        2. **Bilinen Bilgileri Listeleyelim**: Konuyla ilgili ne biliyoruz?
        3. **Çözüm Yolunu Planlayalım**: Hangi adımları izleyeceğiz?
        4. **Adım Adım İlerleyelim**: Her adımı dikkatli yapalım
        5. **Sonucu Kontrol Edelim**: Cevabımız mantıklı mı?
        
        Bu genel yaklaşımı kullanarak probleminizi çözmeye çalışalım!
        """

        return EducationalResponse(
            response_text=response_text,
            explanation_type="step_by_step",
            difficulty_level=context.difficulty_level,
            related_concepts=[],
            follow_up_questions=["Hangi adımdan başlayalım?"],
            motivational_elements=["Adım adım ilerleyeceğiz!"],
            confidence_score=0.5,
        )

    def _create_fallback_explanation(
        self, message: str, context: ConversationContext
    ) -> EducationalResponse:
        """Fallback açıklama"""

        response_text = f"""
        Bu konuyu açıklamaya çalışayım:
        
        {message} hakkında genel olarak şunları söyleyebilirim:
        - Bu {context.subject} alanında önemli bir konudur
        - Temel kavramları anlamak önemlidir
        - Örneklerle pekiştirmek faydalıdır
        - Pratik yaparak öğrenmek en etkili yöntemdir
        
        Daha spesifik sorularınız varsa, lütfen sorun!
        """

        return EducationalResponse(
            response_text=response_text,
            explanation_type="explanation",
            difficulty_level=context.difficulty_level,
            related_concepts=[],
            follow_up_questions=["Hangi kısmını daha detaylı açıklayayım?"],
            motivational_elements=["Birlikte öğreneceğiz!"],
            confidence_score=0.4,
        )

    def _create_fallback_example(
        self, message: str, context: ConversationContext
    ) -> EducationalResponse:
        """Fallback örnek"""

        response_text = f"""
        {message} için örnek vermeye çalışayım:
        
        **Basit Örnek**: Günlük hayattan bir durum
        **Orta Örnek**: Biraz daha karmaşık bir senaryo  
        **İleri Örnek**: Daha detaylı bir uygulama
        
        Hangi seviyede örnek istediğinizi belirtirseniz, daha spesifik örnekler verebilirim!
        """

        return EducationalResponse(
            response_text=response_text,
            explanation_type="example",
            difficulty_level=context.difficulty_level,
            related_concepts=[],
            follow_up_questions=["Hangi seviyede örnek istiyorsunuz?"],
            motivational_elements=["Örneklerle öğrenmek harika!"],
            confidence_score=0.4,
        )

    async def _save_context(self, context: ConversationContext):
        """Bağlamı kaydet"""
        try:
            # Burada veritabanına veya cache'e kaydetme işlemi yapılabilir
            # Şimdilik memory'de tutuyoruz
            pass
        except Exception as e:
            logger.error(f"Bağlam kaydetme hatası: {e}")

    def _load_educational_terminology(self) -> dict[str, list[str]]:
        """Eğitim terminolojisi sözlüğünü yükle"""
        return {
            "matematik": [
                "toplama",
                "çıkarma",
                "çarpma",
                "bölme",
                "kesir",
                "ondalık",
                "geometri",
                "alan",
                "çevre",
                "hacim",
                "açı",
                "üçgen",
                "kare",
                "daire",
                "fonksiyon",
                "denklem",
                "grafik",
                "koordinat",
            ],
            "fen": [
                "atom",
                "molekül",
                "element",
                "bileşik",
                "reaksiyon",
                "enerji",
                "kuvvet",
                "hareket",
                "hız",
                "ivme",
                "kütle",
                "ağırlık",
                "elektrik",
                "manyetizma",
                "ışık",
                "ses",
                "ısı",
            ],
            "türkçe": [
                "özne",
                "yüklem",
                "nesne",
                "tümleç",
                "sıfat",
                "zarf",
                "fiil",
                "isim",
                "zamir",
                "edat",
                "bağlaç",
                "ünlem",
                "cümle",
                "paragraf",
                "metin",
                "anlam",
                "sözcük",
            ],
            "sosyal": [
                "tarih",
                "coğrafya",
                "kültür",
                "medeniyet",
                "devlet",
                "toplum",
                "ekonomi",
                "siyaset",
                "harita",
                "iklim",
                "nüfus",
                "şehir",
                "köy",
                "ülke",
                "kıta",
            ],
        }

    def _load_subject_hierarchy(self) -> dict[str, dict[str, list[str]]]:
        """Konu hiyerarşisini yükle"""
        return {
            "matematik": {
                "sayılar": ["doğal sayılar", "tam sayılar", "rasyonel sayılar"],
                "geometri": ["düzlem geometri", "katı geometri", "analitik geometri"],
                "cebir": ["denklemler", "eşitsizlikler", "fonksiyonlar"],
            },
            "fen": {
                "fizik": ["mekanik", "termodinamik", "elektrik", "optik"],
                "kimya": ["atomlar", "moleküller", "reaksiyonlar", "çözeltiler"],
                "biyoloji": ["hücre", "genetik", "ekoloji", "evrim"],
            },
        }

    def _load_solution_templates(self) -> dict[str, dict[str, str]]:
        """Çözüm şablonlarını yükle"""
        return {
            "matematik": {
                "problem_solving": "1. Verilenler, 2. İstenen, 3. Çözüm, 4. Kontrol",
                "proof": "1. Hipotez, 2. Adımlar, 3. Sonuç",
            },
            "fen": {
                "experiment": "1. Amaç, 2. Malzemeler, 3. Yöntem, 4. Gözlem, 5. Sonuç",
                "theory": "1. Tanım, 2. Açıklama, 3. Örnekler, 4. Uygulama",
            },
            "genel": {"explanation": "1. Giriş, 2. Açıklama, 3. Örnekler, 4. Özet"},
        }

    def _load_motivational_phrases(self) -> list[str]:
        """Motivasyonel ifadeleri yükle"""
        return [
            "Harika gidiyorsun! [GLOWING_STAR]",
            "Çok iyi soru! 🤔",
            "Öğrenme isteğin muhteşem! [BOOKS]",
            "Devam et, başarıyorsun! 💪",
            "Merak etmek güzel! [MAG]",
            "Adım adım ilerliyoruz! 👣",
            "Sen çok yeteneklisin! [STAR]",
            "Birlikte çözeceğiz! 🤝",
        ]

    def _get_term_definition(self, term: str, subject: str) -> str | None:
        """Terim tanımını al"""
        # Basit tanım sözlüğü
        definitions = {
            "toplama": "İki veya daha fazla sayının birleştirilmesi işlemi",
            "çıkarma": "Bir sayıdan başka bir sayının alınması işlemi",
            "çarpma": "Bir sayının kendisiyle belirli sayıda toplanması işlemi",
            "bölme": "Bir sayının eşit parçalara ayrılması işlemi",
            "atom": "Maddenin en küçük yapı taşı",
            "molekül": "İki veya daha fazla atomun birleşmesiyle oluşan yapı",
            "özne": "Cümlede eylemi yapan varlık",
            "yüklem": "Cümlede öznenin yaptığı eylemi bildiren kelime",
        }

        return definitions.get(term.lower())

    def _get_related_concepts(self, term: str) -> list[str]:
        """İlgili kavramları al"""
        relations = {
            "toplama": ["çıkarma", "sayı", "işlem"],
            "atom": ["molekül", "element", "elektron"],
            "özne": ["yüklem", "cümle", "fiil"],
        }

        return relations.get(term.lower(), [])

    async def get_conversation_history(
        self, student_id: str, session_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Konuşma geçmişini al"""

        context_key = f"{student_id}_{session_id or 'default'}"

        if context_key in self.active_contexts:
            context = self.active_contexts[context_key]
            return context.conversation_history

        return []

    async def clear_conversation_context(
        self, student_id: str, session_id: str | None = None
    ) -> bool:
        """Konuşma bağlamını temizle"""

        try:
            context_key = f"{student_id}_{session_id or 'default'}"

            if context_key in self.active_contexts:
                del self.active_contexts[context_key]
                logger.info(f"Bağlam temizlendi: {context_key}")
                return True

            return False

        except Exception as e:
            logger.error(f"Bağlam temizleme hatası: {e}")
            return False

    def get_performance_stats(self) -> dict[str, Any]:
        """Performans istatistiklerini al"""
        return {
            **self.performance_stats,
            "active_contexts": len(self.active_contexts),
            "avg_context_age_minutes": self._calculate_avg_context_age(),
        }

    def _calculate_avg_context_age(self) -> float:
        """Ortalama bağlam yaşını hesapla"""
        if not self.active_contexts:
            return 0.0

        now = datetime.now()
        total_age = sum(
            (now - context.last_activity).total_seconds() / 60
            for context in self.active_contexts.values()
        )

        return total_age / len(self.active_contexts)

    async def close(self):
        """Servisi kapat"""
        try:
            await self.nlp_service.close()
            if hasattr(self.berturk_service, "close"):
                await self.berturk_service.close()

            # Aktif bağlamları temizle
            self.active_contexts.clear()

            logger.info("Türkçe NLP Chat Sistemi kapatıldı")

        except Exception as e:
            logger.error(f"Chat sistemi kapatılırken hata: {e}")


# Global instance
turkish_nlp_chat_system = TurkishNLPChatSystem()
