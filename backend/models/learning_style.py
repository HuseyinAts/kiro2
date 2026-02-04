"""
VARK + Felder-Silverman Hibrit Öğrenme Stili Sistemi
Dünya çapında ilk 64 farklı öğrenme profili kombinasyonu
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VARKDimension(str, Enum):
    """VARK duyusal tercih boyutları"""

    VISUAL = "visual"  # Görsel
    AUDITORY = "auditory"  # İşitsel
    READING = "reading"  # Okuma/Yazma
    KINESTHETIC = "kinesthetic"  # Kinestetik


class FelderDimension(str, Enum):
    """Felder-Silverman bilişsel süreç boyutları"""

    ACTIVE_REFLECTIVE = "active_reflective"  # Aktif ↔ Yansıtıcı
    SENSING_INTUITIVE = "sensing_intuitive"  # Algısal ↔ Sezgisel
    VISUAL_VERBAL = "visual_verbal"  # Görsel ↔ Sözel
    SEQUENTIAL_GLOBAL = "sequential_global"  # Sıralı ↔ Bütünsel


class LearningStyleConfidence(str, Enum):
    """Öğrenme stili tespit güven seviyeleri"""

    LOW = "low"  # Düşük güven (< 0.6)
    MEDIUM = "medium"  # Orta güven (0.6-0.8)
    HIGH = "high"  # Yüksek güven (> 0.8)


class VARKProfile(BaseModel):
    """VARK duyusal tercih profili"""

    visual: float = Field(..., ge=0.0, le=1.0, description="Görsel tercih skoru")
    auditory: float = Field(..., ge=0.0, le=1.0, description="İşitsel tercih skoru")
    reading: float = Field(..., ge=0.0, le=1.0, description="Okuma/yazma tercih skoru")
    kinesthetic: float = Field(
        ..., ge=0.0, le=1.0, description="Kinestetik tercih skoru"
    )

    @property
    def dominant_vark(self) -> VARKDimension:
        """En baskın VARK boyutunu döndür"""
        scores = {
            VARKDimension.VISUAL: self.visual,
            VARKDimension.AUDITORY: self.auditory,
            VARKDimension.READING: self.reading,
            VARKDimension.KINESTHETIC: self.kinesthetic,
        }
        return max(scores, key=scores.get)


class FelderProfile(BaseModel):
    """Felder-Silverman bilişsel süreç profili"""

    active_reflective: float = Field(
        ..., ge=-1.0, le=1.0, description="Aktif(-1) ↔ Yansıtıcı(+1) skoru"
    )
    sensing_intuitive: float = Field(
        ..., ge=-1.0, le=1.0, description="Algısal(-1) ↔ Sezgisel(+1) skoru"
    )
    visual_verbal: float = Field(
        ..., ge=-1.0, le=1.0, description="Görsel(-1) ↔ Sözel(+1) skoru"
    )
    sequential_global: float = Field(
        ..., ge=-1.0, le=1.0, description="Sıralı(-1) ↔ Bütünsel(+1) skoru"
    )

    @property
    def learning_preferences(self) -> Dict[str, str]:
        """Öğrenme tercihlerini döndür"""
        return {
            "processing": "active" if self.active_reflective < 0 else "reflective",
            "perception": "sensing" if self.sensing_intuitive < 0 else "intuitive",
            "input": "visual" if self.visual_verbal < 0 else "verbal",
            "understanding": "sequential" if self.sequential_global < 0 else "global",
        }


class HybridLearningProfile(BaseModel):
    """64 farklı kombinasyonlu hibrit öğrenme profili"""

    student_id: str = Field(..., description="Öğrenci ID")

    # VARK ve Felder profilleri
    vark_profile: VARKProfile = Field(..., description="VARK duyusal tercih profili")
    felder_profile: FelderProfile = Field(
        ..., description="Felder-Silverman bilişsel profil"
    )

    # Hibrit profil bilgileri
    hybrid_code: str = Field(
        ..., description="64 kombinasyondan birini temsil eden kod"
    )
    confidence_level: LearningStyleConfidence = Field(
        ..., description="Tespit güven seviyesi"
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Güven skoru")

    # Meta veriler
    detection_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    data_points_used: int = Field(
        ..., description="Analiz için kullanılan veri noktası sayısı"
    )

    class Config:
        from_attributes = True


class BehavioralData(BaseModel):
    """Davranışsal veri analizi için model"""

    student_id: str = Field(..., description="Öğrenci ID")

    # Etkileşim verileri
    video_watch_time: float = Field(0.0, description="Video izleme süresi (dakika)")
    text_reading_time: float = Field(0.0, description="Metin okuma süresi (dakika)")
    interactive_engagement: float = Field(
        0.0, description="Etkileşimli içerik kullanım süresi"
    )
    quiz_completion_rate: float = Field(
        0.0, ge=0.0, le=1.0, description="Quiz tamamlama oranı"
    )

    # Öğrenme davranışları
    note_taking_frequency: int = Field(0, description="Not alma sıklığı")
    question_asking_frequency: int = Field(0, description="Soru sorma sıklığı")
    peer_interaction_count: int = Field(0, description="Akran etkileşim sayısı")
    help_seeking_behavior: int = Field(0, description="Yardım arama davranışı")

    # Performans verileri
    visual_content_performance: float = Field(
        0.0, ge=0.0, le=1.0, description="Görsel içerik performansı"
    )
    auditory_content_performance: float = Field(
        0.0, ge=0.0, le=1.0, description="İşitsel içerik performansı"
    )
    text_content_performance: float = Field(
        0.0, ge=0.0, le=1.0, description="Metin içerik performansı"
    )
    hands_on_performance: float = Field(
        0.0, ge=0.0, le=1.0, description="Uygulamalı içerik performansı"
    )

    # Zaman damgası
    recorded_at: datetime = Field(default_factory=datetime.now)


class QuestionnaireResponse(BaseModel):
    """Öğrenme stili anketi yanıtları"""

    student_id: str = Field(..., description="Öğrenci ID")
    questionnaire_type: str = Field(..., description="Anket türü (VARK/Felder)")

    # Anket yanıtları
    responses: Dict[str, Any] = Field(..., description="Anket yanıtları")
    completion_time: float = Field(..., description="Anket tamamlama süresi (dakika)")

    # Meta veriler
    completed_at: datetime = Field(default_factory=datetime.now)
    version: str = Field("1.0", description="Anket versiyonu")


class ContentRecommendation(BaseModel):
    """Öğrenme stiline göre içerik önerisi"""

    student_id: str = Field(..., description="Öğrenci ID")
    hybrid_code: str = Field(..., description="Hibrit profil kodu")

    # Önerilen içerik türleri
    recommended_content_types: List[str] = Field(
        ..., description="Önerilen içerik türleri"
    )
    content_weights: Dict[str, float] = Field(
        ..., description="İçerik türü ağırlıkları"
    )

    # Öğrenme stratejileri
    learning_strategies: List[str] = Field(
        ..., description="Önerilen öğrenme stratejileri"
    )
    study_techniques: List[str] = Field(..., description="Önerilen çalışma teknikleri")

    # Kişiselleştirme parametreleri
    difficulty_adjustment: float = Field(
        0.0, ge=-0.5, le=0.5, description="Zorluk ayarlaması"
    )
    pace_adjustment: float = Field(0.0, ge=-0.5, le=0.5, description="Hız ayarlaması")

    # Meta veriler
    generated_at: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Öneri güven skoru"
    )


class LearningStyleUpdate(BaseModel):
    """Öğrenme stili güncelleme modeli"""

    student_id: str = Field(..., description="Öğrenci ID")

    # Güncelleme nedeni
    update_reason: str = Field(..., description="Güncelleme nedeni")
    new_behavioral_data: Optional[BehavioralData] = Field(
        None, description="Yeni davranışsal veri"
    )

    # Güncelleme sonucu
    previous_hybrid_code: str = Field(..., description="Önceki hibrit kod")
    new_hybrid_code: str = Field(..., description="Yeni hibrit kod")
    confidence_change: float = Field(..., description="Güven seviyesi değişimi")

    # Meta veriler
    updated_at: datetime = Field(default_factory=datetime.now)
    update_significance: float = Field(
        ..., ge=0.0, le=1.0, description="Güncelleme önem derecesi"
    )
