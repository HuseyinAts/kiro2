"""
Devrimsel AI Özellikler için Veri Modelleri
7 devrimsel özelliğin tamamı için model tanımları

Requirements: 10.1-10.7, 11.1-11.6, 12.1-12.6
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# Enums
class SimplificationLevel(Enum):
    """Basitleştirme seviyeleri"""

    LEXICAL = "lexical"
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"


class AgentType(Enum):
    """Agent türleri"""

    LEARNING_PATH = "learning_path"
    STUDY_BUDDY = "study_buddy"
    ACCESSIBILITY = "accessibility"


class MessageType(Enum):
    """Mesaj türleri"""

    DATA_UPDATE = "data_update"
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


# Basitleştirme Modelleri
@dataclass
class SimplificationResult:
    """3 seviyeli basitleştirme sonucu"""

    original_text: str
    level1_lexical: str
    level2_syntactic: str
    level3_semantic: str
    complexity_reduction: float  # 0-1 arası
    readability_score: float  # 0-10 arası
    processing_time_ms: float = 0.0
    applied_rules: List[str] = field(default_factory=list)

    def get_final_text(self) -> str:
        """Final basitleştirilmiş metni döndür"""
        return self.level3_semantic

    def get_improvement_percentage(self) -> float:
        """İyileştirme yüzdesini döndür"""
        return self.complexity_reduction * 100


@dataclass
class LexicalReplacement:
    """Kelime değiştirme kuralı"""

    original: str
    replacement: str
    category: str  # "ottoman", "academic", "foreign"
    confidence: float
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye çevir"""
        return {
            "original": self.original,
            "replacement": self.replacement,
            "category": self.category,
            "confidence": self.confidence,
            "context": self.context,
        }


@dataclass
class SyntacticPattern:
    """Cümle yapısı kalıbı"""

    pattern: str
    replacement_template: str
    description: str
    complexity_reduction: float
    examples: List[str] = field(default_factory=list)

    def matches(self, text: str) -> bool:
        """Metin bu kalıba uyuyor mu?"""
        import re

        return bool(re.search(self.pattern, text, re.IGNORECASE))


# Bionic Reading Modelleri
@dataclass
class BionicReadingConfig:
    """Bionic Reading yapılandırması"""

    root_bold_ratio: float = 0.4  # Kökün %40'ı bold
    suffix_bold_ratio: float = 0.0  # Ekler hiç bold değil
    min_bold_chars: int = 2  # Minimum 2 karakter bold
    max_bold_chars: int = 4  # Maksimum 4 karakter bold
    dyslexia_mode: bool = False  # Disleksi modu
    high_contrast: bool = False  # Yüksek kontrast

    def adjust_for_dyslexia(self):
        """Disleksi için ayarla"""
        self.dyslexia_mode = True
        self.root_bold_ratio = 0.5
        self.min_bold_chars = 3
        self.high_contrast = True


@dataclass
class BionicReadingResult:
    """Bionic Reading sonucu"""

    original_text: str
    bionic_text: str
    config: BionicReadingConfig
    word_analysis: List[Dict[str, Any]] = field(default_factory=list)
    processing_time_ms: float = 0.0
    morphology_aware: bool = True

    def get_bold_ratio(self) -> float:
        """Bold karakter oranını hesapla"""
        total_chars = len(self.original_text.replace(" ", ""))
        bold_chars = self.bionic_text.count("**") // 2
        return bold_chars / total_chars if total_chars > 0 else 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikleri döndür"""
        return {
            "word_count": len(self.original_text.split()),
            "bold_ratio": self.get_bold_ratio(),
            "processing_time_ms": self.processing_time_ms,
            "morphology_aware": self.morphology_aware,
            "dyslexia_optimized": self.config.dyslexia_mode,
        }


# FSRS Modelleri
@dataclass
class FSRSParameters:
    """FSRS parametreleri (17 parametre)"""

    w: List[float] = field(
        default_factory=lambda: [
            0.4,
            0.7,
            2.4,
            5.8,
            4.93,
            0.94,
            0.86,
            0.01,
            1.49,
            0.14,
            0.94,
            2.18,
            0.05,
            0.34,
            1.26,
            0.29,
            2.61,
        ]
    )

    def __post_init__(self):
        """17 parametre kontrolü"""
        if len(self.w) != 17:
            raise ValueError("FSRS requires exactly 17 parameters")

    def get_parameter(self, index: int) -> float:
        """Belirli parametreyi al"""
        if 0 <= index < 17:
            return self.w[index]
        raise IndexError("Parameter index must be between 0 and 16")


@dataclass
class FSRSCard:
    """FSRS kart modeli"""

    id: str
    content: str
    answer: str
    difficulty: float = 0.0
    stability: float = 0.0
    retrievability: float = 1.0
    last_review: Optional[datetime] = None
    due_date: Optional[datetime] = None
    review_count: int = 0
    lapses: int = 0
    state: str = "new"  # new, learning, review, relearning

    def is_due(self) -> bool:
        """Tekrar zamanı geldi mi?"""
        if not self.due_date:
            return True
        return datetime.now() >= self.due_date

    def update_after_review(
        self, grade: int, new_stability: float, new_difficulty: float
    ):
        """Tekrar sonrası güncelle"""
        self.last_review = datetime.now()
        self.stability = new_stability
        self.difficulty = new_difficulty
        self.review_count += 1

        if grade == 1:  # Again
            self.lapses += 1


@dataclass
class CulturalAdjustments:
    """Kültürel ayarlamalar"""

    ramadan_factor: float = 0.8  # Ramazan ayı unutma hızı
    exam_season_stress: float = 1.3  # Sınav dönemi stres faktörü
    summer_break_decay: float = 0.6  # Yaz tatili unutma
    group_study_bonus: float = 1.2  # Grup çalışması bonusu
    family_pressure: float = 1.1  # Aile baskısı faktörü

    def get_adjustment_factor(self, context: Dict[str, Any]) -> float:
        """Bağlama göre ayarlama faktörü"""
        factor = 1.0

        if context.get("ramadan_period", False):
            factor *= self.ramadan_factor
        if context.get("exam_season", False):
            factor *= self.exam_season_stress
        if context.get("summer_break", False):
            factor *= self.summer_break_decay
        if context.get("group_study", False):
            factor *= self.group_study_bonus
        if context.get("family_pressure_high", False):
            factor *= self.family_pressure

        return factor


# Multi-Agent Blackboard Modelleri
@dataclass
class BlackboardMessage:
    """Blackboard mesajı"""

    id: str
    key: str
    value: Any
    source_agent: str
    target_agents: List[str] = field(default_factory=list)
    message_type: MessageType = MessageType.DATA_UPDATE
    timestamp: datetime = field(default_factory=datetime.now)
    processed_by: List[str] = field(default_factory=list)

    def is_broadcast(self) -> bool:
        """Broadcast mesajı mı?"""
        return len(self.target_agents) == 0

    def mark_processed(self, agent_name: str):
        """Agent tarafından işlendiğini işaretle"""
        if agent_name not in self.processed_by:
            self.processed_by.append(agent_name)

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye çevir"""
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "source_agent": self.source_agent,
            "target_agents": self.target_agents,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "processed_by": self.processed_by,
        }


@dataclass
class AgentState:
    """Agent durumu"""

    agent_name: str
    agent_type: AgentType
    is_active: bool = True
    last_activity: datetime = field(default_factory=datetime.now)
    subscriptions: List[str] = field(default_factory=list)
    message_queue: List[BlackboardMessage] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

    def subscribe_to(self, event_type: str):
        """Olay tipine abone ol"""
        if event_type not in self.subscriptions:
            self.subscriptions.append(event_type)

    def unsubscribe_from(self, event_type: str):
        """Olay tipinden aboneliği iptal et"""
        if event_type in self.subscriptions:
            self.subscriptions.remove(event_type)

    def add_message(self, message: BlackboardMessage):
        """Mesaj kuyruğuna ekle"""
        self.message_queue.append(message)
        self.last_activity = datetime.now()

    def get_pending_messages(self) -> List[BlackboardMessage]:
        """Bekleyen mesajları al"""
        return [
            msg for msg in self.message_queue if self.agent_name not in msg.processed_by
        ]


@dataclass
class BlackboardEvent:
    """Blackboard olayı"""

    event_id: str
    event_type: str
    data: Any
    source_agent: str
    timestamp: datetime = field(default_factory=datetime.now)
    subscribers_notified: List[str] = field(default_factory=list)

    def notify_subscriber(self, agent_name: str):
        """Aboneyi bilgilendir"""
        if agent_name not in self.subscribers_notified:
            self.subscribers_notified.append(agent_name)


# ZPD + Maarif Modelleri
@dataclass
class MaarifValues:
    """MEB Maarif değerleri"""

    national_values: List[str] = field(
        default_factory=lambda: ["vatan", "millet", "aile"]
    )
    universal_values: List[str] = field(
        default_factory=lambda: ["adalet", "dostluk", "dürüstlük"]
    )
    root_values: List[str] = field(default_factory=lambda: ["sabır", "saygı", "sevgi"])

    def get_alignment_score(self, subject: str) -> float:
        """Ders ile değer uyumluluğu"""
        alignment_map = {
            "Tarih": 0.9,  # Milli değerlerle yüksek uyum
            "Türkçe": 0.85,  # Kültürel değerlerle uyum
            "Matematik": 0.6,  # Evrensel değerlerle uyum
            "Fen": 0.65,  # Evrensel değerlerle uyum
            "Sosyal": 0.8,  # Toplumsal değerlerle uyum
        }
        return alignment_map.get(subject, 0.7)


@dataclass
class ZPDCalculationResult:
    """ZPD hesaplama sonucu"""

    student_id: str
    subject: str
    current_level: float
    zpd_lower: float
    zpd_upper: float
    optimal_challenge: float
    cultural_adjustment: float
    maarif_alignment: float
    confidence: float
    calculation_time_ms: float = 0.0

    def get_zpd_width(self) -> float:
        """ZPD genişliği"""
        return self.zpd_upper - self.zpd_lower

    def is_appropriate_difficulty(self, difficulty: float) -> bool:
        """Zorluk seviyesi uygun mu?"""
        return self.zpd_lower <= difficulty <= self.zpd_upper

    def get_recommendation(self) -> str:
        """Öneri oluştur"""
        if self.cultural_adjustment > 1.1:
            return "Grup çalışması ve sosyal öğrenme aktiviteleri önerilir."
        elif self.cultural_adjustment < 0.9:
            return "Bireysel çalışma ve kişisel rehberlik önerilir."
        else:
            return "Mevcut öğrenme yaklaşımı uygun."


# Morfoloji IRT Modelleri
@dataclass
class MorphologyComplexity:
    """Morfolojik karmaşıklık"""

    word: str
    suffix_count: int
    derivational_depth: int
    compound_complexity: float
    phonetic_changes: int
    semantic_ambiguity: float
    total_complexity: float

    def is_highly_complex(self, threshold: float = 0.7) -> bool:
        """Yüksek karmaşıklıkta mı?"""
        return self.total_complexity > threshold

    def get_complexity_category(self) -> str:
        """Karmaşıklık kategorisi"""
        if self.total_complexity < 0.3:
            return "Basit"
        elif self.total_complexity < 0.7:
            return "Orta"
        else:
            return "Karmaşık"


@dataclass
class IRTAnalysisResult:
    """IRT analiz sonucu"""

    question_id: str
    student_id: str
    standard_probability: float
    morphology_aware_probability: float
    morphology_advantage: float
    complexity_score: float
    recommendation: str
    analysis_time_ms: float = 0.0

    def has_morphology_advantage(self) -> bool:
        """Morfoloji avantajı var mı?"""
        return self.morphology_advantage > 0.05

    def needs_morphology_practice(self) -> bool:
        """Morfoloji pratiği gerekli mi?"""
        return self.morphology_advantage < -0.1


# Hibrit Öğrenme Stili Modelleri
@dataclass
class VARKProfile:
    """VARK profili"""

    visual: float
    auditory: float
    reading: float
    kinesthetic: float

    def get_dominant_style(self) -> str:
        """Baskın stili döndür"""
        scores = {
            "visual": self.visual,
            "auditory": self.auditory,
            "reading": self.reading,
            "kinesthetic": self.kinesthetic,
        }
        return max(scores, key=scores.get)

    def is_multimodal(self, threshold: float = 0.6) -> bool:
        """Çok modlu öğrenme tercihi var mı?"""
        high_scores = sum(
            1
            for score in [self.visual, self.auditory, self.reading, self.kinesthetic]
            if score > threshold
        )
        return high_scores >= 2


@dataclass
class FelderSilvermanProfile:
    """Felder-Silverman profili"""

    active_reflective: float  # Aktif ↔ Yansıtıcı
    sensing_intuitive: float  # Algısal ↔ Sezgisel
    visual_verbal: float  # Görsel ↔ Sözel
    sequential_global: float  # Sıralı ↔ Bütünsel

    def get_learning_preferences(self) -> Dict[str, str]:
        """Öğrenme tercihlerini döndür"""
        return {
            "processing": "active" if self.active_reflective > 0.5 else "reflective",
            "perception": "sensing" if self.sensing_intuitive > 0.5 else "intuitive",
            "input": "visual" if self.visual_verbal > 0.5 else "verbal",
            "understanding": "sequential" if self.sequential_global > 0.5 else "global",
        }


@dataclass
class HybridLearningAnalysis:
    """Hibrit öğrenme analizi"""

    student_id: str
    vark_profile: VARKProfile
    felder_profile: FelderSilvermanProfile
    hybrid_code: str
    confidence_level: float
    behavioral_consistency: float
    questionnaire_alignment: float
    analysis_time_ms: float = 0.0

    def get_learning_recommendations(self) -> List[str]:
        """Öğrenme önerileri"""
        recommendations = []

        # VARK önerileri
        dominant_vark = self.vark_profile.get_dominant_style()
        if dominant_vark == "visual":
            recommendations.append(
                "Görsel materyaller, diyagramlar ve grafikler kullanın"
            )
        elif dominant_vark == "auditory":
            recommendations.append("Sesli açıklamalar ve tartışmalar yapın")
        elif dominant_vark == "reading":
            recommendations.append("Metin tabanlı materyaller ve notlar kullanın")
        elif dominant_vark == "kinesthetic":
            recommendations.append("Uygulamalı aktiviteler ve deneyimler yapın")

        # Felder-Silverman önerileri
        preferences = self.felder_profile.get_learning_preferences()
        if preferences["processing"] == "active":
            recommendations.append("Grup çalışması ve tartışma yapın")
        if preferences["perception"] == "sensing":
            recommendations.append("Somut örnekler ve uygulamalar kullanın")
        if preferences["understanding"] == "global":
            recommendations.append("Büyük resmi görmeye odaklanın")

        return recommendations

    def is_reliable_analysis(self, threshold: float = 0.7) -> bool:
        """Analiz güvenilir mi?"""
        return (
            self.confidence_level > threshold
            and self.behavioral_consistency > threshold
            and self.questionnaire_alignment > threshold
        )


# Utility Functions
def create_sample_simplification_result() -> SimplificationResult:
    """Örnek basitleştirme sonucu"""
    return SimplificationResult(
        original_text="Bu mütalaa çok önemli bir tetkik gerektiriyor.",
        level1_lexical="Bu okuma çok önemli bir inceleme gerektiriyor.",
        level2_syntactic="Bu okuma çok önemlidir. Bir inceleme gerektirir.",
        level3_semantic="Bu yazıyı okumak çok önemlidir. Detaylı bir inceleme yapılmalıdır.",
        complexity_reduction=0.65,
        readability_score=7.8,
        processing_time_ms=125.5,
        applied_rules=[
            "Ottoman word replacement",
            "Sentence splitting",
            "Semantic restructuring",
        ],
    )


def create_sample_bionic_result() -> BionicReadingResult:
    """Örnek Bionic Reading sonucu"""
    config = BionicReadingConfig()
    return BionicReadingResult(
        original_text="Çocuklar bahçede oynuyorlar",
        bionic_text="**Çoc**uklar **bah**çede **oyn**uyorlar",
        config=config,
        processing_time_ms=45.2,
        morphology_aware=True,
    )


if __name__ == "__main__":
    # Test örnekleri
    print("Devrimsel AI Modelleri Test")
    print("=" * 40)

    # Basitleştirme testi
    simplification = create_sample_simplification_result()
    print(f"Basitleştirme: {simplification.complexity_reduction:.1%} iyileştirme")

    # Bionic Reading testi
    bionic = create_sample_bionic_result()
    print(f"Bionic Reading: {bionic.get_bold_ratio():.1%} bold oran")

    # VARK profil testi
    vark = VARKProfile(visual=0.8, auditory=0.3, reading=0.6, kinesthetic=0.4)
    print(f"Baskın VARK stili: {vark.get_dominant_style()}")

    print("\nTüm modeller başarıyla yüklendi!")
