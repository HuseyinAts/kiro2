"""
Öğrenme Modelleri
Devrimsel AI özellikler için veri modelleri

Requirements: 10.1-10.7
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LearningStyleType(Enum):
    """Öğrenme stili türleri"""

    VISUAL = "visual"
    AUDITORY = "auditory"
    READING = "reading"
    KINESTHETIC = "kinesthetic"


class FelderDimension(Enum):
    """Felder-Silverman boyutları"""

    ACTIVE_REFLECTIVE = "active_reflective"
    SENSING_INTUITIVE = "sensing_intuitive"
    VISUAL_VERBAL = "visual_verbal"
    SEQUENTIAL_GLOBAL = "sequential_global"


@dataclass
class HybridLearningProfile:
    """VARK + Felder-Silverman hibrit öğrenme profili"""

    student_id: str
    vark_profile: dict[str, float]  # visual, auditory, reading, kinesthetic
    felder_profile: dict[str, float]  # 4 boyut skoru
    hybrid_code: str  # 64 kombinasyondan biri
    confidence_level: float  # 0-1 arası güven seviyesi
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_dominant_vark_style(self) -> str:
        """Baskın VARK stilini döndür"""
        return max(self.vark_profile, key=self.vark_profile.get)

    def get_learning_preferences(self) -> dict[str, Any]:
        """Öğrenme tercihlerini döndür"""
        return {
            "dominant_vark": self.get_dominant_vark_style(),
            "vark_scores": self.vark_profile,
            "felder_scores": self.felder_profile,
            "hybrid_code": self.hybrid_code,
            "confidence": self.confidence_level,
        }


@dataclass
class TurkishZPDRange:
    """Türk kültürüne uyarlanmış ZPD aralığı"""

    student_id: str
    subject: str
    lower_bound: float  # Mevcut seviye
    upper_bound: float  # Potansiyel seviye
    optimal_challenge: float  # Optimal zorluk seviyesi
    cultural_factors: dict[str, float]  # Kültürel faktörler
    maarif_alignment: float  # MEB Maarif uyumluluğu
    created_at: datetime = field(default_factory=datetime.now)

    def get_zpd_width(self) -> float:
        """ZPD genişliğini döndür"""
        return self.upper_bound - self.lower_bound

    def is_in_zpd(self, difficulty_level: float) -> bool:
        """Zorluk seviyesi ZPD içinde mi?"""
        return self.lower_bound <= difficulty_level <= self.upper_bound


@dataclass
class Question:
    """Soru modeli"""

    text: str
    difficulty: float  # IRT difficulty parameter
    discrimination: float  # IRT discrimination parameter
    subject: str
    topic: str
    id: str | None = None
    guessing_parameter: float = 0.2  # IRT guessing parameter
    morphology_complexity: float | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def get_irt_parameters(self) -> dict[str, float]:
        """IRT parametrelerini döndür"""
        return {
            "difficulty": self.difficulty,
            "discrimination": self.discrimination,
            "guessing": self.guessing_parameter,
        }


@dataclass
class Student:
    """Öğrenci modeli"""

    id: str
    ability: float  # IRT ability parameter
    morphology_awareness: float  # Morfolojik farkındalık seviyesi
    name: str | None = None
    grade_level: int | None = None
    learning_profile: HybridLearningProfile | None = None
    zpd_ranges: dict[str, TurkishZPDRange] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def get_zpd_for_subject(self, subject: str) -> TurkishZPDRange | None:
        """Belirli ders için ZPD aralığını döndür"""
        return self.zpd_ranges.get(subject)

    def update_ability(self, new_ability: float):
        """Yetenek seviyesini güncelle"""
        self.ability = max(-3.0, min(3.0, new_ability))  # -3 ile +3 arası sınırla


@dataclass
class Flashcard:
    """Flashcard modeli (FSRS için)"""

    id: str
    content: str
    answer: str
    difficulty: float
    last_review: datetime
    review_count: int
    success_rate: float
    stability: float = 1.0  # FSRS stability
    retrievability: float = 1.0  # FSRS retrievability
    created_at: datetime = field(default_factory=datetime.now)

    def calculate_retention(self, days_since_review: int) -> float:
        """Hafızada kalma oranını hesapla"""
        if self.stability <= 0:
            return 0.0
        return (1 + days_since_review / (9 * self.stability)) ** -1

    def needs_review(self, threshold: float = 0.8) -> bool:
        """Tekrar gerekli mi?"""
        days_since = (datetime.now() - self.last_review).days
        retention = self.calculate_retention(days_since)
        return retention < threshold


@dataclass
class LearningSession:
    """Öğrenme oturumu"""

    student_id: str
    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    questions_answered: list[str] = field(default_factory=list)
    correct_answers: int = 0
    total_questions: int = 0
    subject: str | None = None
    topic: str | None = None

    def get_success_rate(self) -> float:
        """Başarı oranını döndür"""
        if self.total_questions == 0:
            return 0.0
        return self.correct_answers / self.total_questions

    def get_duration_minutes(self) -> float:
        """Oturum süresini dakika olarak döndür"""
        if not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds() / 60


@dataclass
class CulturalContext:
    """Kültürel bağlam modeli"""

    student_id: str
    group_learning_preference: float  # 0-1 arası
    teacher_respect_level: float
    family_involvement: float
    peer_competition: float
    authority_acceptance: float
    ramadan_period: bool = False
    exam_season: bool = False
    summer_break: bool = False

    def get_cultural_adjustment_factor(self) -> float:
        """Kültürel ayarlama faktörü"""
        factors = [
            self.group_learning_preference,
            self.teacher_respect_level,
            self.family_involvement,
            self.peer_competition,
            self.authority_acceptance,
        ]
        return sum(factors) / len(factors)


@dataclass
class MorphologyAnalysis:
    """Morfolojik analiz sonucu"""

    word: str
    root: str
    suffixes: list[str]
    derivational_depth: int
    is_compound: bool
    compound_parts: list[str] = field(default_factory=list)
    complexity_score: float = 0.0

    def get_suffix_count(self) -> int:
        """Ek sayısını döndür"""
        return len(self.suffixes)

    def is_complex_word(self, threshold: float = 0.7) -> bool:
        """Karmaşık kelime mi?"""
        return self.complexity_score > threshold


@dataclass
class FSRSCard:
    """FSRS algoritması için kart modeli"""

    id: str
    content: str
    difficulty: float = 0.0  # FSRS difficulty
    stability: float = 0.0  # FSRS stability
    retrievability: float = 1.0  # FSRS retrievability
    last_review: datetime | None = None
    due_date: datetime | None = None
    review_count: int = 0
    lapses: int = 0  # Unutma sayısı
    state: str = "new"  # new, learning, review, relearning

    def is_due(self) -> bool:
        """Tekrar zamanı geldi mi?"""
        if not self.due_date:
            return True
        return datetime.now() >= self.due_date

    def days_overdue(self) -> int:
        """Kaç gün gecikmiş?"""
        if not self.due_date or not self.is_due():
            return 0
        return (datetime.now() - self.due_date).days


@dataclass
class SimplificationLevel:
    """Metin basitleştirme seviyesi"""

    level: int  # 1, 2, 3
    name: str  # "lexical", "syntactic", "semantic"
    description: str
    rules_applied: list[str] = field(default_factory=list)
    complexity_reduction: float = 0.0

    def add_rule(self, rule: str, reduction: float = 0.0):
        """Kural ekle"""
        self.rules_applied.append(rule)
        self.complexity_reduction += reduction


@dataclass
class BionicReadingResult:
    """Bionic Reading sonucu"""

    original_text: str
    bionic_text: str
    bold_ratio: float  # Bold yapılan karakter oranı
    processing_time_ms: float
    word_count: int
    morphology_aware: bool = True  # Türkçe morfoloji farkında mı?

    def get_bold_character_count(self) -> int:
        """Bold karakter sayısını döndür"""
        return self.bionic_text.count("**") // 2  # Açılış ve kapanış


@dataclass
class AgentMessage:
    """Agent mesaj modeli"""

    agent_name: str
    message_type: str  # "data_update", "request", "response"
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    target_agents: list[str] = field(default_factory=list)

    def is_broadcast(self) -> bool:
        """Tüm agentlara gönderilecek mi?"""
        return len(self.target_agents) == 0


@dataclass
class BlackboardEntry:
    """Blackboard giriş modeli"""

    key: str
    value: Any
    source_agent: str
    timestamp: datetime = field(default_factory=datetime.now)
    subscribers_notified: list[str] = field(default_factory=list)

    def add_subscriber_notification(self, agent_name: str):
        """Abone bildirimini ekle"""
        if agent_name not in self.subscribers_notified:
            self.subscribers_notified.append(agent_name)


# Utility functions
def create_sample_hybrid_profile(student_id: str) -> HybridLearningProfile:
    """Örnek hibrit profil oluştur"""
    return HybridLearningProfile(
        student_id=student_id,
        vark_profile={
            "visual": 0.8,
            "auditory": 0.3,
            "reading": 0.6,
            "kinesthetic": 0.4,
        },
        felder_profile={
            "active_reflective": 0.7,
            "sensing_intuitive": 0.6,
            "visual_verbal": 0.8,
            "sequential_global": 0.5,
        },
        hybrid_code="V-A-S-S",  # Visual-Active-Sensing-Sequential
        confidence_level=0.85,
    )


def create_sample_zpd_range(student_id: str, subject: str) -> TurkishZPDRange:
    """Örnek ZPD aralığı oluştur"""
    return TurkishZPDRange(
        student_id=student_id,
        subject=subject,
        lower_bound=5.0,
        upper_bound=7.5,
        optimal_challenge=6.2,
        cultural_factors={
            "group_learning_preference": 0.8,
            "teacher_respect_level": 0.9,
            "family_involvement": 0.7,
        },
        maarif_alignment=0.85,
    )


def create_sample_student(student_id: str) -> Student:
    """Örnek öğrenci oluştur"""
    profile = create_sample_hybrid_profile(student_id)
    zpd_math = create_sample_zpd_range(student_id, "Matematik")

    return Student(
        id=student_id,
        ability=1.5,
        morphology_awareness=0.7,
        name=f"Öğrenci {student_id}",
        grade_level=11,
        learning_profile=profile,
        zpd_ranges={"Matematik": zpd_math},
    )
