"""
Learning Style Detection System
Teknofest 2025 - Eğitim Eylemci Projesi

Bu modül:
- Behavioral analysis for learning style detection
- Learning preference questionnaire
- Style-based content filtering and ranking
- Learning style adaptation algorithms
"""

import json
import logging
import os
import statistics

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


class LearningStyle(Enum):
    """Öğrenme stilleri"""

    VISUAL = "visual"  # Görsel öğrenme (video, infografik)
    AUDITORY = "auditory"  # İşitsel öğrenme (podcast, anlatım)
    READING = "reading"  # Okuma-yazma (metin, makale)
    KINESTHETIC = "kinesthetic"  # Uygulamalı öğrenme (pratik, proje)
    MIXED = "mixed"  # Karma


class BehavioralIndicator(Enum):
    """Davranışsal göstergeler"""

    CONTENT_PREFERENCE = "content_preference"  # İçerik tercihi
    TIME_SPENT = "time_spent"  # Harcanan zaman
    ENGAGEMENT_LEVEL = "engagement_level"  # Etkileşim seviyesi
    COMPLETION_RATE = "completion_rate"  # Tamamlama oranı
    INTERACTION_PATTERN = "interaction_pattern"  # Etkileşim kalıbı
    FEEDBACK_RESPONSE = "feedback_response"  # Geri bildirim tepkisi


@dataclass
class BehavioralData:
    """Davranışsal veri"""

    student_id: str
    indicator: BehavioralIndicator
    content_type: str  # video, text, interactive, audio
    value: float  # Ölçüm değeri (0-1 arası normalize)
    timestamp: datetime
    context: dict[str, Any]  # Ek bağlam bilgisi


@dataclass
class LearningStyleProfile:
    """Öğrenme stili profili"""

    student_id: str
    primary_style: LearningStyle
    secondary_style: LearningStyle | None
    style_scores: dict[LearningStyle, float]  # Her stil için skor (0-1)
    confidence_level: float  # Tespit güven seviyesi (0-1)
    behavioral_patterns: dict[str, Any]  # Davranışsal kalıplar
    preferences: dict[str, Any]  # Tercihler
    created_at: datetime
    last_updated: datetime
    metadata: dict[str, Any]


@dataclass
class StyleBasedRecommendation:
    """Stil tabanlı öneri"""

    content_type: str
    priority: float  # Öncelik skoru (0-1)
    reasoning: str  # Öneri gerekçesi
    adaptation_suggestions: list[str]  # Adaptasyon önerileri


class LearningStyleDetector:
    """Öğrenme Stili Tespit Sistemi"""

    def __init__(self):
        self.behavioral_data = {}  # student_id -> List[BehavioralData]
        self.style_profiles = {}  # student_id -> LearningStyleProfile
        self.questionnaire_templates = self._load_questionnaire_templates()
        self.content_type_mapping = self._load_content_type_mapping()

    def _load_questionnaire_templates(self) -> dict[str, list[dict[str, Any]]]:
        """Öğrenme stili anketi şablonları"""
        return {
            "visual_indicators": [
                {
                    "question": "Yeni bir konuyu öğrenirken hangi yöntemi tercih edersiniz?",
                    "options": [
                        {
                            "text": "Diyagramlar ve grafikler",
                            "style": "visual",
                            "weight": 1.0,
                        },
                        {
                            "text": "Sesli açıklamalar",
                            "style": "auditory",
                            "weight": 1.0,
                        },
                        {
                            "text": "Yazılı materyaller",
                            "style": "reading",
                            "weight": 1.0,
                        },
                        {
                            "text": "Uygulamalı deneyimler",
                            "style": "kinesthetic",
                            "weight": 1.0,
                        },
                    ],
                },
                {
                    "question": "Bir problemi çözerken nasıl yaklaşırsınız?",
                    "options": [
                        {
                            "text": "Görsel şemalar çizerim",
                            "style": "visual",
                            "weight": 0.9,
                        },
                        {
                            "text": "Kendimle konuşurum",
                            "style": "auditory",
                            "weight": 0.9,
                        },
                        {
                            "text": "Adım adım yazarım",
                            "style": "reading",
                            "weight": 0.9,
                        },
                        {
                            "text": "Deneme yanılma yaparım",
                            "style": "kinesthetic",
                            "weight": 0.9,
                        },
                    ],
                },
                {
                    "question": "Bilgiyi en iyi nasıl hatırlarsınız?",
                    "options": [
                        {
                            "text": "Görsel imgeler halinde",
                            "style": "visual",
                            "weight": 1.0,
                        },
                        {
                            "text": "Sesli tekrarlar yaparak",
                            "style": "auditory",
                            "weight": 1.0,
                        },
                        {"text": "Notlar alarak", "style": "reading", "weight": 1.0},
                        {"text": "Uygulayarak", "style": "kinesthetic", "weight": 1.0},
                    ],
                },
                {
                    "question": "Grup çalışmasında hangi rolü tercih edersiniz?",
                    "options": [
                        {"text": "Sunum hazırlayıcı", "style": "visual", "weight": 0.8},
                        {"text": "Tartışma lideri", "style": "auditory", "weight": 0.8},
                        {
                            "text": "Araştırmacı/yazıcı",
                            "style": "reading",
                            "weight": 0.8,
                        },
                        {
                            "text": "Uygulama sorumlusu",
                            "style": "kinesthetic",
                            "weight": 0.8,
                        },
                    ],
                },
                {
                    "question": "Boş zamanınızda hangi aktiviteyi tercih edersiniz?",
                    "options": [
                        {
                            "text": "Film/video izlemek",
                            "style": "visual",
                            "weight": 0.7,
                        },
                        {
                            "text": "Müzik dinlemek/podcast",
                            "style": "auditory",
                            "weight": 0.7,
                        },
                        {"text": "Kitap okumak", "style": "reading", "weight": 0.7},
                        {
                            "text": "Spor/oyun oynamak",
                            "style": "kinesthetic",
                            "weight": 0.7,
                        },
                    ],
                },
            ]
        }

    def _load_content_type_mapping(self) -> dict[str, LearningStyle]:
        """İçerik türü - öğrenme stili eşleştirmesi"""
        return {
            "video": LearningStyle.VISUAL,
            "animation": LearningStyle.VISUAL,
            "infographic": LearningStyle.VISUAL,
            "image": LearningStyle.VISUAL,
            "diagram": LearningStyle.VISUAL,
            "audio": LearningStyle.AUDITORY,
            "podcast": LearningStyle.AUDITORY,
            "lecture": LearningStyle.AUDITORY,
            "music": LearningStyle.AUDITORY,
            "article": LearningStyle.READING,
            "text": LearningStyle.READING,
            "book": LearningStyle.READING,
            "pdf": LearningStyle.READING,
            "blog": LearningStyle.READING,
            "interactive": LearningStyle.KINESTHETIC,
            "simulation": LearningStyle.KINESTHETIC,
            "project": LearningStyle.KINESTHETIC,
            "quiz": LearningStyle.KINESTHETIC,
            "exercise": LearningStyle.KINESTHETIC,
        }

    async def create_learning_style_questionnaire(
        self, student_id: str
    ) -> list[dict[str, Any]]:
        """
        Öğrenme stili anketi oluştur

        Args:
            student_id: Öğrenci ID

        Returns:
            Anket soruları
        """
        try:
            questions = []

            # Template sorularını ekle
            for question_data in self.questionnaire_templates["visual_indicators"]:
                questions.append(
                    {
                        "question_id": f"style_q_{len(questions)}_{student_id}",
                        "question_text": question_data["question"],
                        "question_type": "multiple_choice",
                        "options": [opt["text"] for opt in question_data["options"]],
                        "metadata": {
                            "style_weights": {
                                opt["text"]: {
                                    "style": opt["style"],
                                    "weight": opt["weight"],
                                }
                                for opt in question_data["options"]
                            }
                        },
                    }
                )

            # LLM ile ek sorular oluştur
            additional_questions = await self._generate_additional_style_questions(
                student_id
            )
            questions.extend(additional_questions)

            logger.info(
                f"Created {len(questions)} learning style questionnaire for student {student_id}"
            )
            return questions

        except Exception as e:
            logger.error(f"Create learning style questionnaire error: {e!s}")
            return []

    async def _generate_additional_style_questions(
        self, student_id: str
    ) -> list[dict[str, Any]]:
        """LLM ile ek stil soruları oluştur"""
        try:
            prompt = """
            Öğrenme stili tespiti için 3 ek soru oluştur.
            Her soru farklı öğrenme stillerini (görsel, işitsel, okuma/yazma, kinestetik) ayırt etmeye yardımcı olsun.
            
            JSON formatında yanıtla:
            {
                "questions": [
                    {
                        "question": "Soru metni",
                        "options": [
                            {"text": "Seçenek 1", "style": "visual"},
                            {"text": "Seçenek 2", "style": "auditory"},
                            {"text": "Seçenek 3", "style": "reading"},
                            {"text": "Seçenek 4", "style": "kinesthetic"}
                        ]
                    }
                ]
            }
            """

            result = await llm_service.generate(prompt=prompt, temperature=0.6)

            questions = []
            if result["success"]:
                try:
                    data = json.loads(result["text"])
                    for i, q_data in enumerate(data.get("questions", [])):
                        questions.append(
                            {
                                "question_id": f"style_llm_q_{i}_{student_id}",
                                "question_text": q_data["question"],
                                "question_type": "multiple_choice",
                                "options": [opt["text"] for opt in q_data["options"]],
                                "metadata": {
                                    "style_weights": {
                                        opt["text"]: {
                                            "style": opt["style"],
                                            "weight": 0.8,
                                        }
                                        for opt in q_data["options"]
                                    },
                                    "generated_by": "llm",
                                },
                            }
                        )
                except json.JSONDecodeError:
                    pass

            return questions

        except Exception as e:
            logger.error(f"Generate additional style questions error: {e!s}")
            return []

    async def analyze_questionnaire_responses(
        self, student_id: str, questions: list[dict[str, Any]], answers: list[str]
    ) -> LearningStyleProfile:
        """
        Anket cevaplarını analiz et ve öğrenme stilini belirle

        Args:
            student_id: Öğrenci ID
            questions: Sorular
            answers: Cevaplar

        Returns:
            Öğrenme stili profili
        """
        try:
            style_scores = {
                LearningStyle.VISUAL: 0.0,
                LearningStyle.AUDITORY: 0.0,
                LearningStyle.READING: 0.0,
                LearningStyle.KINESTHETIC: 0.0,
            }

            total_weight = 0.0

            # Her cevabı değerlendir
            for question, answer in zip(questions, answers, strict=False):
                metadata = question.get("metadata", {})
                style_weights = metadata.get("style_weights", {})

                if answer in style_weights:
                    style_info = style_weights[answer]
                    style = LearningStyle(style_info["style"])
                    weight = style_info["weight"]

                    style_scores[style] += weight
                    total_weight += weight

            # Skorları normalize et
            if total_weight > 0:
                for style in style_scores:
                    style_scores[style] = style_scores[style] / total_weight

            # Birincil ve ikincil stilleri belirle
            sorted_styles = sorted(
                style_scores.items(), key=lambda x: x[1], reverse=True
            )
            primary_style = sorted_styles[0][0]
            secondary_style = sorted_styles[1][0] if sorted_styles[1][1] > 0.2 else None

            # Güven seviyesini hesapla
            confidence_level = sorted_styles[0][1] - sorted_styles[1][1]
            confidence_level = min(confidence_level * 2, 1.0)  # 0-1 arası normalize et

            # Davranışsal kalıpları analiz et
            behavioral_patterns = self._analyze_behavioral_patterns(
                student_id, style_scores
            )

            # Tercihleri belirle
            preferences = self._determine_preferences(
                primary_style, secondary_style, style_scores
            )

            # Profil oluştur
            profile = LearningStyleProfile(
                student_id=student_id,
                primary_style=primary_style,
                secondary_style=secondary_style,
                style_scores=style_scores,
                confidence_level=confidence_level,
                behavioral_patterns=behavioral_patterns,
                preferences=preferences,
                created_at=datetime.now(),
                last_updated=datetime.now(),
                metadata={
                    "questionnaire_based": True,
                    "total_questions": len(questions),
                    "analysis_method": "weighted_scoring",
                },
            )

            # Profili kaydet
            self.style_profiles[student_id] = profile

            logger.info(
                f"Learning style profile created for student {student_id}: {primary_style.value} (confidence: {confidence_level:.2f})"
            )
            return profile

        except Exception as e:
            logger.error(f"Analyze questionnaire responses error: {e!s}")
            raise

    def record_behavioral_data(
        self,
        student_id: str,
        indicator: BehavioralIndicator,
        content_type: str,
        value: float,
        context: dict[str, Any] | None = None,
    ):
        """
        Davranışsal veri kaydet

        Args:
            student_id: Öğrenci ID
            indicator: Davranışsal gösterge
            content_type: İçerik türü
            value: Ölçüm değeri
            context: Ek bağlam
        """
        try:
            if student_id not in self.behavioral_data:
                self.behavioral_data[student_id] = []

            behavioral_data = BehavioralData(
                student_id=student_id,
                indicator=indicator,
                content_type=content_type,
                value=max(0.0, min(1.0, value)),  # 0-1 arası normalize et
                timestamp=datetime.now(),
                context=context or {},
            )

            self.behavioral_data[student_id].append(behavioral_data)

            # Veri sayısı çok fazlaysa eski verileri temizle
            if len(self.behavioral_data[student_id]) > 1000:
                self.behavioral_data[student_id] = self.behavioral_data[student_id][
                    -500:
                ]

            logger.debug(
                f"Recorded behavioral data for student {student_id}: {indicator.value} = {value}"
            )

        except Exception as e:
            logger.error(f"Record behavioral data error: {e!s}")

    async def analyze_behavioral_patterns(
        self, student_id: str, min_data_points: int = 10
    ) -> LearningStyleProfile | None:
        """
        Davranışsal kalıpları analiz ederek öğrenme stilini belirle

        Args:
            student_id: Öğrenci ID
            min_data_points: Minimum veri noktası sayısı

        Returns:
            Öğrenme stili profili (yeterli veri varsa)
        """
        try:
            if student_id not in self.behavioral_data:
                return None

            data_points = self.behavioral_data[student_id]
            if len(data_points) < min_data_points:
                logger.info(
                    f"Insufficient behavioral data for student {student_id}: {len(data_points)} < {min_data_points}"
                )
                return None

            # İçerik türü tercihlerini analiz et
            content_preferences = {}
            engagement_by_type = {}
            completion_by_type = {}
            time_by_type = {}

            for data in data_points:
                content_type = data.content_type

                if content_type not in content_preferences:
                    content_preferences[content_type] = []
                    engagement_by_type[content_type] = []
                    completion_by_type[content_type] = []
                    time_by_type[content_type] = []

                if data.indicator == BehavioralIndicator.CONTENT_PREFERENCE:
                    content_preferences[content_type].append(data.value)
                elif data.indicator == BehavioralIndicator.ENGAGEMENT_LEVEL:
                    engagement_by_type[content_type].append(data.value)
                elif data.indicator == BehavioralIndicator.COMPLETION_RATE:
                    completion_by_type[content_type].append(data.value)
                elif data.indicator == BehavioralIndicator.TIME_SPENT:
                    time_by_type[content_type].append(data.value)

            # Her içerik türü için ortalama skorları hesapla
            style_scores = {
                LearningStyle.VISUAL: 0.0,
                LearningStyle.AUDITORY: 0.0,
                LearningStyle.READING: 0.0,
                LearningStyle.KINESTHETIC: 0.0,
            }

            for content_type in content_preferences:
                if content_type in self.content_type_mapping:
                    style = self.content_type_mapping[content_type]

                    # Farklı metrikleri birleştir
                    scores = []
                    if content_preferences[content_type]:
                        scores.append(
                            statistics.mean(content_preferences[content_type])
                        )
                    if engagement_by_type[content_type]:
                        scores.append(statistics.mean(engagement_by_type[content_type]))
                    if completion_by_type[content_type]:
                        scores.append(statistics.mean(completion_by_type[content_type]))
                    if time_by_type[content_type]:
                        scores.append(statistics.mean(time_by_type[content_type]))

                    if scores:
                        style_scores[style] += statistics.mean(scores)

            # Skorları normalize et
            max_score = max(style_scores.values()) if style_scores.values() else 1.0
            if max_score > 0:
                for style in style_scores:
                    style_scores[style] = style_scores[style] / max_score

            # Birincil ve ikincil stilleri belirle
            sorted_styles = sorted(
                style_scores.items(), key=lambda x: x[1], reverse=True
            )
            primary_style = sorted_styles[0][0]
            secondary_style = sorted_styles[1][0] if sorted_styles[1][1] > 0.3 else None

            # Güven seviyesini hesapla (davranışsal veri daha güvenilir)
            confidence_level = min(
                (sorted_styles[0][1] - sorted_styles[1][1]) * 1.5, 1.0
            )

            # Davranışsal kalıpları analiz et
            behavioral_patterns = self._analyze_behavioral_patterns(
                student_id, style_scores
            )

            # Tercihleri belirle
            preferences = self._determine_preferences(
                primary_style, secondary_style, style_scores
            )

            # Profil oluştur
            profile = LearningStyleProfile(
                student_id=student_id,
                primary_style=primary_style,
                secondary_style=secondary_style,
                style_scores=style_scores,
                confidence_level=confidence_level,
                behavioral_patterns=behavioral_patterns,
                preferences=preferences,
                created_at=datetime.now(),
                last_updated=datetime.now(),
                metadata={
                    "behavioral_based": True,
                    "data_points": len(data_points),
                    "analysis_method": "behavioral_analysis",
                },
            )

            # Profili kaydet
            self.style_profiles[student_id] = profile

            logger.info(
                f"Behavioral learning style profile created for student {student_id}: {primary_style.value} (confidence: {confidence_level:.2f})"
            )
            return profile

        except Exception as e:
            logger.error(f"Analyze behavioral patterns error: {e!s}")
            return None

    def _analyze_behavioral_patterns(
        self, student_id: str, style_scores: dict[LearningStyle, float]
    ) -> dict[str, Any]:
        """Davranışsal kalıpları analiz et"""
        patterns = {
            "dominant_style": max(style_scores, key=style_scores.get).value,
            "style_distribution": {
                style.value: score for style, score in style_scores.items()
            },
            "learning_consistency": self._calculate_consistency(student_id),
            "content_type_preferences": self._get_content_preferences(student_id),
            "engagement_patterns": self._get_engagement_patterns(student_id),
        }
        return patterns

    def _calculate_consistency(self, student_id: str) -> float:
        """Öğrenme tutarlılığını hesapla"""
        if student_id not in self.behavioral_data:
            return 0.5

        data_points = self.behavioral_data[student_id]
        if len(data_points) < 5:
            return 0.5

        # Son 20 veri noktasının tutarlılığını kontrol et
        recent_data = data_points[-20:]
        engagement_values = [
            d.value
            for d in recent_data
            if d.indicator == BehavioralIndicator.ENGAGEMENT_LEVEL
        ]

        if len(engagement_values) < 3:
            return 0.5

        # Standart sapma ile tutarlılığı ölç
        std_dev = statistics.stdev(engagement_values)
        consistency = max(0.0, 1.0 - std_dev)  # Düşük sapma = yüksek tutarlılık

        return consistency

    def _get_content_preferences(self, student_id: str) -> dict[str, float]:
        """İçerik türü tercihlerini getir"""
        if student_id not in self.behavioral_data:
            return {}

        preferences = {}
        for data in self.behavioral_data[student_id]:
            if data.indicator == BehavioralIndicator.CONTENT_PREFERENCE:
                if data.content_type not in preferences:
                    preferences[data.content_type] = []
                preferences[data.content_type].append(data.value)

        # Ortalama skorları hesapla
        avg_preferences = {}
        for content_type, values in preferences.items():
            avg_preferences[content_type] = statistics.mean(values)

        return avg_preferences

    def _get_engagement_patterns(self, student_id: str) -> dict[str, Any]:
        """Etkileşim kalıplarını getir"""
        if student_id not in self.behavioral_data:
            return {}

        engagement_data = [
            d
            for d in self.behavioral_data[student_id]
            if d.indicator == BehavioralIndicator.ENGAGEMENT_LEVEL
        ]

        if not engagement_data:
            return {}

        engagement_values = [d.value for d in engagement_data]

        return {
            "average_engagement": statistics.mean(engagement_values),
            "engagement_trend": self._calculate_trend(engagement_values),
            "peak_engagement_times": self._find_peak_times(engagement_data),
            "low_engagement_content": self._find_low_engagement_content(
                engagement_data
            ),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """Trend hesapla"""
        if len(values) < 3:
            return "stable"

        # Basit trend analizi
        first_half = statistics.mean(values[: len(values) // 2])
        second_half = statistics.mean(values[len(values) // 2 :])

        if second_half > first_half + 0.1:
            return "increasing"
        if second_half < first_half - 0.1:
            return "decreasing"
        return "stable"

    def _find_peak_times(self, engagement_data: list[BehavioralData]) -> list[str]:
        """Yüksek etkileşim zamanlarını bul"""
        # Basit implementasyon - gerçek uygulamada zaman analizi yapılabilir
        high_engagement = [d for d in engagement_data if d.value > 0.8]
        times = [d.timestamp.strftime("%H:%M") for d in high_engagement]
        return list(set(times))[:5]  # En fazla 5 zaman dilimi

    def _find_low_engagement_content(
        self, engagement_data: list[BehavioralData]
    ) -> list[str]:
        """Düşük etkileşim içerik türlerini bul"""
        low_engagement = [d for d in engagement_data if d.value < 0.3]
        content_types = [d.content_type for d in low_engagement]
        return list(set(content_types))

    def _determine_preferences(
        self,
        primary_style: LearningStyle,
        secondary_style: LearningStyle | None,
        style_scores: dict[LearningStyle, float],
    ) -> dict[str, Any]:
        """Tercihleri belirle"""
        preferences = {
            "primary_content_types": self._get_content_types_for_style(primary_style),
            "secondary_content_types": self._get_content_types_for_style(
                secondary_style
            )
            if secondary_style
            else [],
            "recommended_formats": self._get_recommended_formats(primary_style),
            "interaction_preferences": self._get_interaction_preferences(primary_style),
            "pacing_preferences": self._get_pacing_preferences(primary_style),
        }
        return preferences

    def _get_content_types_for_style(self, style: LearningStyle) -> list[str]:
        """Stil için uygun içerik türlerini getir"""
        style_content_map = {
            LearningStyle.VISUAL: [
                "video",
                "infographic",
                "diagram",
                "animation",
                "image",
            ],
            LearningStyle.AUDITORY: [
                "audio",
                "podcast",
                "lecture",
                "music",
                "discussion",
            ],
            LearningStyle.READING: ["article", "text", "book", "pdf", "blog"],
            LearningStyle.KINESTHETIC: [
                "interactive",
                "simulation",
                "project",
                "quiz",
                "exercise",
            ],
        }
        return style_content_map.get(style, [])

    def _get_recommended_formats(self, style: LearningStyle) -> list[str]:
        """Önerilen formatları getir"""
        format_map = {
            LearningStyle.VISUAL: [
                "short_videos",
                "infographics",
                "mind_maps",
                "flowcharts",
            ],
            LearningStyle.AUDITORY: [
                "podcasts",
                "audio_books",
                "discussions",
                "verbal_explanations",
            ],
            LearningStyle.READING: [
                "articles",
                "textbooks",
                "written_summaries",
                "note_taking",
            ],
            LearningStyle.KINESTHETIC: [
                "hands_on_activities",
                "simulations",
                "role_playing",
                "experiments",
            ],
        }
        return format_map.get(style, [])

    def _get_interaction_preferences(self, style: LearningStyle) -> list[str]:
        """Etkileşim tercihlerini getir"""
        interaction_map = {
            LearningStyle.VISUAL: [
                "visual_feedback",
                "progress_bars",
                "color_coding",
                "spatial_organization",
            ],
            LearningStyle.AUDITORY: [
                "audio_feedback",
                "verbal_instructions",
                "group_discussions",
                "music_integration",
            ],
            LearningStyle.READING: [
                "text_feedback",
                "written_instructions",
                "note_sharing",
                "text_highlighting",
            ],
            LearningStyle.KINESTHETIC: [
                "interactive_elements",
                "drag_drop",
                "touch_gestures",
                "physical_movement",
            ],
        }
        return interaction_map.get(style, [])

    def _get_pacing_preferences(self, style: LearningStyle) -> dict[str, Any]:
        """Tempo tercihlerini getir"""
        pacing_map = {
            LearningStyle.VISUAL: {
                "preferred_duration": "10-15 minutes",
                "break_frequency": "every 20 minutes",
            },
            LearningStyle.AUDITORY: {
                "preferred_duration": "15-20 minutes",
                "break_frequency": "every 25 minutes",
            },
            LearningStyle.READING: {
                "preferred_duration": "20-30 minutes",
                "break_frequency": "every 30 minutes",
            },
            LearningStyle.KINESTHETIC: {
                "preferred_duration": "5-10 minutes",
                "break_frequency": "every 15 minutes",
            },
        }
        return pacing_map.get(
            style,
            {"preferred_duration": "15 minutes", "break_frequency": "every 20 minutes"},
        )

    def get_style_based_recommendations(
        self, student_id: str, content_types: list[str]
    ) -> list[StyleBasedRecommendation]:
        """
        Stil tabanlı içerik önerileri

        Args:
            student_id: Öğrenci ID
            content_types: Mevcut içerik türleri

        Returns:
            Stil tabanlı öneriler
        """
        try:
            profile = self.style_profiles.get(student_id)
            if not profile:
                logger.warning(
                    f"No learning style profile found for student {student_id}"
                )
                return []

            recommendations = []

            # Birincil stil için öneriler
            primary_content_types = self._get_content_types_for_style(
                profile.primary_style
            )
            for content_type in content_types:
                if content_type in primary_content_types:
                    priority = 1.0
                    reasoning = f"Bu içerik türü ({content_type}) birincil öğrenme stiliniz ({profile.primary_style.value}) ile mükemmel uyum sağlıyor."
                    adaptations = self._get_adaptation_suggestions(
                        profile.primary_style, content_type
                    )

                    recommendations.append(
                        StyleBasedRecommendation(
                            content_type=content_type,
                            priority=priority,
                            reasoning=reasoning,
                            adaptation_suggestions=adaptations,
                        )
                    )

            # İkincil stil için öneriler
            if profile.secondary_style:
                secondary_content_types = self._get_content_types_for_style(
                    profile.secondary_style
                )
                for content_type in content_types:
                    if (
                        content_type in secondary_content_types
                        and content_type not in primary_content_types
                    ):
                        priority = 0.7
                        reasoning = f"Bu içerik türü ({content_type}) ikincil öğrenme stiliniz ({profile.secondary_style.value}) ile uyumlu."
                        adaptations = self._get_adaptation_suggestions(
                            profile.secondary_style, content_type
                        )

                        recommendations.append(
                            StyleBasedRecommendation(
                                content_type=content_type,
                                priority=priority,
                                reasoning=reasoning,
                                adaptation_suggestions=adaptations,
                            )
                        )

            # Diğer içerik türleri için düşük öncelikli öneriler
            for content_type in content_types:
                if not any(rec.content_type == content_type for rec in recommendations):
                    priority = 0.3
                    reasoning = f"Bu içerik türü ({content_type}) öğrenme stilinizle tam uyumlu olmasa da faydalı olabilir."
                    adaptations = ["İçeriği kendi öğrenme stilinize uyarlayın"]

                    recommendations.append(
                        StyleBasedRecommendation(
                            content_type=content_type,
                            priority=priority,
                            reasoning=reasoning,
                            adaptation_suggestions=adaptations,
                        )
                    )

            # Öncelik sırasına göre sırala
            recommendations.sort(key=lambda x: x.priority, reverse=True)

            logger.info(
                f"Generated {len(recommendations)} style-based recommendations for student {student_id}"
            )
            return recommendations

        except Exception as e:
            logger.error(f"Get style-based recommendations error: {e!s}")
            return []

    def _get_adaptation_suggestions(
        self, style: LearningStyle, content_type: str
    ) -> list[str]:
        """Stil ve içerik türüne göre adaptasyon önerileri"""
        suggestions = []

        if style == LearningStyle.VISUAL:
            if content_type in ["article", "text", "book"]:
                suggestions.extend(
                    [
                        "Metni okurken zihinsel görüntüler oluşturun",
                        "Önemli noktaları renkli kalemlerle işaretleyin",
                        "Kavram haritaları ve diyagramlar çizin",
                        "Bilgileri görsel şemalara dönüştürün",
                    ]
                )
            elif content_type in ["audio", "podcast"]:
                suggestions.extend(
                    [
                        "Dinlerken notlar alın ve çizimler yapın",
                        "Ses içeriğini görsel materyallerle destekleyin",
                        "Zihinsel resimler oluşturun",
                    ]
                )

        elif style == LearningStyle.AUDITORY:
            if content_type in ["article", "text", "book"]:
                suggestions.extend(
                    [
                        "Metni yüksek sesle okuyun",
                        "Önemli kısımları kendinize anlatın",
                        "Ses kayıtları alın ve tekrar dinleyin",
                        "Başkalarıyla tartışın",
                    ]
                )
            elif content_type == "video":
                suggestions.extend(
                    [
                        "Videoyu dinlemeye odaklanın",
                        "Ses kalitesini artırın",
                        "Notları sesli olarak alın",
                    ]
                )

        elif style == LearningStyle.READING:
            if content_type == "video":
                suggestions.extend(
                    [
                        "Video altyazılarını açın",
                        "İzledikten sonra özet yazın",
                        "Anahtar noktaları not alın",
                        "İlgili yazılı kaynakları araştırın",
                    ]
                )
            elif content_type in ["audio", "podcast"]:
                suggestions.extend(
                    [
                        "Transkriptini bulun ve okuyun",
                        "Dinlerken detaylı notlar alın",
                        "Önemli kavramları araştırıp yazın",
                    ]
                )

        elif style == LearningStyle.KINESTHETIC:
            if content_type in ["article", "text", "book"]:
                suggestions.extend(
                    [
                        "Okurken hareket edin (yürüyün)",
                        "Bilgileri uygulama fırsatları arayın",
                        "Fiziksel objelerle örnekler oluşturun",
                        "Rol yapma teknikleri kullanın",
                    ]
                )
            elif content_type == "video":
                suggestions.extend(
                    [
                        "Videodaki hareketleri taklit edin",
                        "İzlediklerinizi hemen uygulayın",
                        "Interaktif öğeler arayın",
                    ]
                )

        if not suggestions:
            suggestions.append(
                "İçeriği aktif olarak kullanın ve kendi deneyimlerinizle bağlantı kurun"
            )

        return suggestions

    async def update_learning_style_profile(
        self,
        student_id: str,
        new_behavioral_data: list[BehavioralData] | None = None,
        force_update: bool = False,
    ) -> LearningStyleProfile | None:
        """
        Öğrenme stili profilini güncelle

        Args:
            student_id: Öğrenci ID
            new_behavioral_data: Yeni davranışsal veriler
            force_update: Zorla güncelleme

        Returns:
            Güncellenmiş profil
        """
        try:
            current_profile = self.style_profiles.get(student_id)
            if not current_profile and not force_update:
                return None

            # Yeni davranışsal verileri ekle
            if new_behavioral_data:
                if student_id not in self.behavioral_data:
                    self.behavioral_data[student_id] = []
                self.behavioral_data[student_id].extend(new_behavioral_data)

            # Yeterli veri varsa davranışsal analiz yap
            updated_profile = await self.analyze_behavioral_patterns(
                student_id, min_data_points=5
            )

            if updated_profile:
                # Mevcut profil ile karşılaştır
                if current_profile:
                    # Güven seviyesi artışını kontrol et
                    if (
                        updated_profile.confidence_level
                        > current_profile.confidence_level
                    ):
                        logger.info(
                            f"Learning style confidence improved for student {student_id}: {current_profile.confidence_level:.2f} -> {updated_profile.confidence_level:.2f}"
                        )

                    # Stil değişikliğini kontrol et
                    if updated_profile.primary_style != current_profile.primary_style:
                        logger.info(
                            f"Learning style changed for student {student_id}: {current_profile.primary_style.value} -> {updated_profile.primary_style.value}"
                        )

                return updated_profile

            return current_profile

        except Exception as e:
            logger.error(f"Update learning style profile error: {e!s}")
            return None

    def get_learning_style_summary(self, student_id: str) -> dict[str, Any]:
        """
        Öğrenci için öğrenme stili özeti

        Args:
            student_id: Öğrenci ID

        Returns:
            Öğrenme stili özeti
        """
        try:
            profile = self.style_profiles.get(student_id)
            if not profile:
                return {"error": "Öğrenme stili profili bulunamadı"}

            summary = {
                "student_id": student_id,
                "primary_style": {
                    "style": profile.primary_style.value,
                    "score": profile.style_scores[profile.primary_style],
                    "description": self._get_style_description(profile.primary_style),
                },
                "secondary_style": None,
                "confidence_level": profile.confidence_level,
                "recommendations": {
                    "preferred_content_types": profile.preferences.get(
                        "primary_content_types", []
                    ),
                    "recommended_formats": profile.preferences.get(
                        "recommended_formats", []
                    ),
                    "interaction_preferences": profile.preferences.get(
                        "interaction_preferences", []
                    ),
                    "pacing_preferences": profile.preferences.get(
                        "pacing_preferences", {}
                    ),
                },
                "behavioral_insights": {
                    "learning_consistency": profile.behavioral_patterns.get(
                        "learning_consistency", 0.5
                    ),
                    "engagement_trend": profile.behavioral_patterns.get(
                        "engagement_patterns", {}
                    ).get("engagement_trend", "stable"),
                    "content_preferences": profile.behavioral_patterns.get(
                        "content_type_preferences", {}
                    ),
                },
                "last_updated": profile.last_updated.isoformat(),
                "data_source": "behavioral"
                if profile.metadata.get("behavioral_based")
                else "questionnaire",
            }

            if profile.secondary_style:
                summary["secondary_style"] = {
                    "style": profile.secondary_style.value,
                    "score": profile.style_scores[profile.secondary_style],
                    "description": self._get_style_description(profile.secondary_style),
                }

            return summary

        except Exception as e:
            logger.error(f"Get learning style summary error: {e!s}")
            return {"error": str(e)}

    def _get_style_description(self, style: LearningStyle) -> str:
        """Öğrenme stili açıklaması"""
        descriptions = {
            LearningStyle.VISUAL: "Görsel öğrenme - Diyagramlar, grafikler, videolar ve görsel materyallerle daha iyi öğrenirsiniz.",
            LearningStyle.AUDITORY: "İşitsel öğrenme - Sesli açıklamalar, tartışmalar ve müzikle daha iyi öğrenirsiniz.",
            LearningStyle.READING: "Okuma/Yazma öğrenme - Metinler, notlar ve yazılı materyallerle daha iyi öğrenirsiniz.",
            LearningStyle.KINESTHETIC: "Kinestetik öğrenme - Uygulamalı çalışma, deneyimler ve fiziksel aktivitelerle daha iyi öğrenirsiniz.",
            LearningStyle.MIXED: "Karma öğrenme - Farklı öğrenme yöntemlerini birleştirerek daha iyi öğrenirsiniz.",
        }
        return descriptions.get(style, "Bilinmeyen öğrenme stili")

    def _generate_adaptation_suggestions(
        self, content_type: str, primary_style: LearningStyle
    ) -> list[str]:
        """Adaptasyon önerileri oluştur"""
        suggestions = []

        if primary_style == LearningStyle.VISUAL:
            if content_type in ["audio", "podcast"]:
                suggestions.extend(
                    [
                        "Dinlerken görsel notlar alın",
                        "Zihin haritaları oluşturun",
                        "İlgili görselleri araştırın",
                    ]
                )
            elif content_type in ["text", "article"]:
                suggestions.extend(
                    [
                        "Önemli kısımları renkli kalemlerle işaretleyin",
                        "Diyagramlar çizin",
                        "Görsel özetler oluşturun",
                    ]
                )

        elif primary_style == LearningStyle.AUDITORY:
            if content_type in ["text", "article"]:
                suggestions.extend(
                    [
                        "Metni sesli okuyun",
                        "Özetleri sesli kaydedin",
                        "Başkalarıyla tartışın",
                    ]
                )
            elif content_type in ["video"]:
                suggestions.extend(
                    [
                        "Ses kalitesine odaklanın",
                        "Notları sesli alın",
                        "İçeriği başkalarına anlatın",
                    ]
                )

        elif primary_style == LearningStyle.READING:
            if content_type in ["video", "audio"]:
                suggestions.extend(
                    [
                        "Transkript varsa okuyun",
                        "Detaylı notlar alın",
                        "Ek kaynakları araştırın",
                    ]
                )

        elif primary_style == LearningStyle.KINESTHETIC:
            if content_type in ["text", "video"]:
                suggestions.extend(
                    [
                        "Öğrendiklerinizi uygulayın",
                        "Örnekler oluşturun",
                        "Fiziksel aktivitelerle pekiştirin",
                    ]
                )

        return suggestions

    def filter_and_rank_content(
        self, student_id: str, content_list: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        İçerikleri öğrenme stiline göre filtrele ve sırala

        Args:
            student_id: Öğrenci ID
            content_list: İçerik listesi (her içerik dict olarak)

        Returns:
            Filtrelenmiş ve sıralanmış içerik listesi
        """
        try:
            if student_id not in self.style_profiles:
                # Profil yoksa orijinal listeyi döndür
                return content_list

            profile = self.style_profiles[student_id]
            filtered_content = []

            for content in content_list:
                content_type = content.get("content_type", "unknown")

                # İçerik türünü öğrenme stiline göre skorla
                style_score = self._calculate_content_style_score(content_type, profile)

                # Minimum eşik kontrolü (0.2 altındaki içerikleri filtrele)
                if style_score >= 0.2:
                    content_copy = content.copy()
                    content_copy["style_score"] = style_score
                    content_copy["style_match"] = self._get_style_match_level(
                        style_score
                    )
                    content_copy[
                        "adaptation_suggestions"
                    ] = self._generate_adaptation_suggestions(
                        content_type, profile.primary_style
                    )
                    filtered_content.append(content_copy)

            # Stil skoruna göre sırala (yüksekten düşüğe)
            filtered_content.sort(key=lambda x: x["style_score"], reverse=True)

            logger.info(
                f"Filtered {len(content_list)} content items to {len(filtered_content)} for student {student_id}"
            )
            return filtered_content

        except Exception as e:
            logger.error(f"Filter and rank content error: {e!s}")
            return content_list

    def _calculate_content_style_score(
        self, content_type: str, profile: LearningStyleProfile
    ) -> float:
        """İçerik türü için stil skoru hesapla"""
        if content_type not in self.content_type_mapping:
            return 0.5  # Bilinmeyen içerik türleri için orta skor

        mapped_style = self.content_type_mapping[content_type]

        # Birincil stil ile tam uyum
        if mapped_style == profile.primary_style:
            base_score = 1.0
        # İkincil stil ile uyum
        elif profile.secondary_style and mapped_style == profile.secondary_style:
            base_score = 0.8
        else:
            # Stil skorlarından al
            base_score = profile.style_scores.get(mapped_style, 0.3)

        # Güven seviyesi ile ağırlıklandır
        confidence_weight = profile.confidence_level
        final_score = (base_score * confidence_weight) + (0.5 * (1 - confidence_weight))

        return min(final_score, 1.0)

    def _get_style_match_level(self, score: float) -> str:
        """Stil uyum seviyesini belirle"""
        if score >= 0.8:
            return "excellent"
        if score >= 0.6:
            return "good"
        if score >= 0.4:
            return "moderate"
        return "low"

    def rank_content_by_learning_style(
        self,
        student_id: str,
        content_list: list[dict[str, Any]],
        include_all: bool = False,
    ) -> list[dict[str, Any]]:
        """
        İçerikleri öğrenme stiline göre sırala (filtreleme yapmadan)

        Args:
            student_id: Öğrenci ID
            content_list: İçerik listesi
            include_all: Tüm içerikleri dahil et (filtreleme yapma)

        Returns:
            Sıralanmış içerik listesi
        """
        try:
            if student_id not in self.style_profiles:
                return content_list

            profile = self.style_profiles[student_id]
            ranked_content = []

            for content in content_list:
                content_type = content.get("content_type", "unknown")
                style_score = self._calculate_content_style_score(content_type, profile)

                content_copy = content.copy()
                content_copy["style_score"] = style_score
                content_copy["style_match"] = self._get_style_match_level(style_score)
                content_copy["primary_style_match"] = (
                    content_type in self.content_type_mapping
                    and self.content_type_mapping[content_type] == profile.primary_style
                )
                ranked_content.append(content_copy)

            # Stil skoruna göre sırala
            ranked_content.sort(key=lambda x: x["style_score"], reverse=True)

            return ranked_content

        except Exception as e:
            logger.error(f"Rank content by learning style error: {e!s}")
            return content_list

    def get_learning_style_profile(
        self, student_id: str
    ) -> LearningStyleProfile | None:
        """Öğrenci öğrenme stili profilini getir"""
        return self.style_profiles.get(student_id)

    def update_style_profile(
        self, student_id: str, new_data: dict[str, Any]
    ) -> LearningStyleProfile | None:
        """Öğrenme stili profilini güncelle"""
        try:
            if student_id not in self.style_profiles:
                return None

            profile = self.style_profiles[student_id]

            # Güncelleme verilerini uygula
            if "style_scores" in new_data:
                profile.style_scores.update(new_data["style_scores"])

                # Yeni birincil ve ikincil stilleri belirle
                sorted_styles = sorted(
                    profile.style_scores.items(), key=lambda x: x[1], reverse=True
                )
                profile.primary_style = sorted_styles[0][0]
                profile.secondary_style = (
                    sorted_styles[1][0] if sorted_styles[1][1] > 0.2 else None
                )

            if "preferences" in new_data:
                profile.preferences.update(new_data["preferences"])

            if "behavioral_patterns" in new_data:
                profile.behavioral_patterns.update(new_data["behavioral_patterns"])

            profile.last_updated = datetime.now()
            profile.metadata["last_update_reason"] = new_data.get(
                "update_reason", "manual_update"
            )

            logger.info(f"Updated learning style profile for student {student_id}")
            return profile

        except Exception as e:
            logger.error(f"Update style profile error: {e!s}")
            return None


# Singleton instance
learning_style_detector = LearningStyleDetector()
