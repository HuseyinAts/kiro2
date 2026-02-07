"""
EBA TV İçerik Veri Modelleri

TRT EBA TV platformu için özel veri modelleri ve şemalar.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from .question_generation import DifficultyLevel


class EBAContentCategory(str, Enum):
    """EBA TV içerik kategorileri"""

    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN_BILIMLERI = "fen_bilimleri"
    SOSYAL_BILGILER = "sosyal_bilgiler"
    INGILIZCE = "ingilizce"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    TARIH = "tarih"
    COGRAFYA = "cografya"
    FELSEFE = "felsefe"
    EDEBIYAT = "edebiyat"


class EBAGradeLevel(str, Enum):
    """EBA TV sınıf seviyeleri"""

    SINIF_5 = "5"
    SINIF_6 = "6"
    SINIF_7 = "7"
    SINIF_8 = "8"  # LGS
    SINIF_9 = "9"
    SINIF_10 = "10"
    SINIF_11 = "11"
    SINIF_12 = "12"  # YKS


class EBAVideoQuality(str, Enum):
    """EBA video kalite seviyeleri"""

    LOW = "low"  # 0-4 puan
    MEDIUM = "medium"  # 4-7 puan
    HIGH = "high"  # 7-10 puan


class EBACurriculumAlignment(BaseModel):
    """EBA içerik müfredat uyumu"""

    alignment_score: float = Field(..., ge=0, le=1, description="Müfredat uyum skoru")
    matched_topics: List[str] = Field(
        default_factory=list, description="Eşleşen konular"
    )
    missing_topics: List[str] = Field(default_factory=list, description="Eksik konular")
    suggestions: List[str] = Field(default_factory=list, description="Öneriler")
    curriculum_coverage: str = Field(..., description="Müfredat kapsama oranı")

    model_config = ConfigDict(from_attributes=True)


class EBAVideoMetadata(BaseModel):
    """EBA TV video metadata"""

    # Temel Bilgiler
    title: str = Field(..., min_length=1, max_length=200, description="Video başlığı")
    description: str = Field(..., max_length=1000, description="Video açıklaması")
    duration_minutes: int = Field(
        ..., ge=1, le=180, description="Video süresi (dakika)"
    )

    # Kategorilendirme
    category: EBAContentCategory = Field(..., description="İçerik kategorisi")
    grade_level: EBAGradeLevel = Field(..., description="Sınıf seviyesi")
    subject_topics: List[str] = Field(
        default_factory=list, description="Konu başlıkları"
    )
    difficulty_level: DifficultyLevel = Field(..., description="Zorluk seviyesi")

    # URL ve Medya
    video_url: HttpUrl = Field(..., description="Video URL'i")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Küçük resim URL'i")
    transcript: Optional[str] = Field(None, description="Video transkripti")

    # Kalite ve Değerlendirme
    quality_score: float = Field(0.0, ge=0, le=10, description="Kalite skoru")
    curriculum_alignment: Dict[str, Any] = Field(
        default_factory=dict, description="Müfredat uyumu"
    )

    # Erişilebilirlik
    accessibility_features: List[str] = Field(
        default_factory=list, description="Erişilebilirlik özellikleri"
    )

    # Zaman Damgaları
    created_date: datetime = Field(
        default_factory=datetime.now, description="Oluşturma tarihi"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Son güncelleme"
    )

    @field_validator("quality_score")
    @classmethod
    def validate_quality_score(cls, v):
        """Kalite skorunu doğrula"""
        return round(v, 2)

    @field_validator("accessibility_features")
    @classmethod
    def validate_accessibility_features(cls, v):
        """Erişilebilirlik özelliklerini doğrula"""
        valid_features = [
            "altyazi",
            "transkript",
            "sesli_betimleme",
            "buyuk_yazi",
            "yuksek_kontrast",
            "yavas_oynatim",
        ]
        return [feature for feature in v if feature in valid_features]

    model_config = ConfigDict(from_attributes=True)


class EBAContentCollection(BaseModel):
    """EBA TV içerik koleksiyonu"""

    videos: List[EBAVideoMetadata] = Field(
        default_factory=list, description="Video listesi"
    )
    total_count: int = Field(0, ge=0, description="Toplam video sayısı")
    categories: Dict[str, int] = Field(
        default_factory=dict, description="Kategori dağılımı"
    )
    grade_levels: Dict[str, int] = Field(
        default_factory=dict, description="Sınıf seviyesi dağılımı"
    )
    quality_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Kalite dağılımı"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Son güncelleme"
    )

    @field_validator("total_count")
    @classmethod
    def validate_total_count(cls, v, values):
        """Toplam sayıyı doğrula"""
        if "videos" in values:
            return len(values["videos"])
        return v

    model_config = ConfigDict(from_attributes=True)


class EBAVideoSearchRequest(BaseModel):
    """EBA video arama isteği"""

    query: str = Field(..., min_length=1, max_length=100, description="Arama sorgusu")
    grade_level: Optional[EBAGradeLevel] = Field(
        None, description="Sınıf seviyesi filtresi"
    )
    category: Optional[EBAContentCategory] = Field(
        None, description="Kategori filtresi"
    )
    min_quality: float = Field(6.0, ge=0, le=10, description="Minimum kalite skoru")
    max_duration: Optional[int] = Field(
        None, ge=1, le=180, description="Maksimum süre (dakika)"
    )
    accessibility_required: bool = Field(
        False, description="Erişilebilirlik gerekli mi"
    )

    model_config = ConfigDict(from_attributes=True)


class EBAVideoSearchResponse(BaseModel):
    """EBA video arama yanıtı"""

    videos: List[EBAVideoMetadata] = Field(
        default_factory=list, description="Bulunan videolar"
    )
    total_results: int = Field(0, ge=0, description="Toplam sonuç sayısı")
    search_query: str = Field(..., description="Arama sorgusu")
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict, description="Uygulanan filtreler"
    )
    search_time_ms: float = Field(0.0, ge=0, description="Arama süresi (ms)")

    model_config = ConfigDict(from_attributes=True)


class EBAContentRecommendationRequest(BaseModel):
    """EBA içerik öneri isteği"""

    student_id: str = Field(..., description="Öğrenci ID")
    grade_level: EBAGradeLevel = Field(..., description="Öğrenci sınıf seviyesi")
    weak_subjects: List[EBAContentCategory] = Field(
        default_factory=list, description="Zayıf konular"
    )
    learning_style: str = Field("visual", description="Öğrenme stili")
    max_recommendations: int = Field(
        10, ge=1, le=50, description="Maksimum öneri sayısı"
    )

    model_config = ConfigDict(from_attributes=True)


class EBAContentRecommendationResponse(BaseModel):
    """EBA içerik öneri yanıtı"""

    recommendations: List[EBAVideoMetadata] = Field(
        default_factory=list, description="Önerilen videolar"
    )
    student_id: str = Field(..., description="Öğrenci ID")
    recommendation_reasons: Dict[str, str] = Field(
        default_factory=dict, description="Öneri nedenleri"
    )
    personalization_score: float = Field(
        0.0, ge=0, le=10, description="Kişiselleştirme skoru"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now, description="Oluşturma zamanı"
    )

    model_config = ConfigDict(from_attributes=True)


class EBAContentStatistics(BaseModel):
    """EBA içerik istatistikleri"""

    total_videos: int = Field(0, ge=0, description="Toplam video sayısı")
    categories: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Kategori istatistikleri"
    )
    quality_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Kalite dağılımı"
    )
    grade_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Sınıf dağılımı"
    )
    average_quality: float = Field(0.0, ge=0, le=10, description="Ortalama kalite")
    average_duration: float = Field(0.0, ge=0, description="Ortalama süre (dakika)")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Son güncelleme"
    )
    cache_status: str = Field("empty", description="Cache durumu")

    model_config = ConfigDict(from_attributes=True)


class EBAVideoQualityAnalysis(BaseModel):
    """EBA video kalite analizi"""

    video_id: str = Field(..., description="Video ID")
    overall_score: float = Field(..., ge=0, le=10, description="Genel kalite skoru")

    # Detaylı Skorlar
    duration_score: float = Field(..., ge=0, le=10, description="Süre uygunluğu")
    title_clarity_score: float = Field(..., ge=0, le=10, description="Başlık netliği")
    description_quality_score: float = Field(
        ..., ge=0, le=10, description="Açıklama kalitesi"
    )
    curriculum_alignment_score: float = Field(
        ..., ge=0, le=10, description="Müfredat uyumu"
    )
    accessibility_score: float = Field(..., ge=0, le=10, description="Erişilebilirlik")

    # Öneriler
    improvement_suggestions: List[str] = Field(
        default_factory=list, description="İyileştirme önerileri"
    )
    quality_category: EBAVideoQuality = Field(..., description="Kalite kategorisi")

    # Analiz Detayları
    analysis_date: datetime = Field(
        default_factory=datetime.now, description="Analiz tarihi"
    )
    analyzer_version: str = Field("1.0", description="Analiz algoritması versiyonu")

    model_config = ConfigDict(from_attributes=True)


class EBAContentModerationRequest(BaseModel):
    """EBA içerik moderasyon isteği"""

    video_id: str = Field(..., description="Video ID")
    moderator_id: str = Field(..., description="Moderatör ID")
    action: str = Field(..., description="Moderasyon aksiyonu")  # approve, reject, flag
    reason: Optional[str] = Field(None, description="Moderasyon nedeni")
    notes: Optional[str] = Field(None, max_length=500, description="Moderatör notları")

    model_config = ConfigDict(from_attributes=True)


class EBAContentModerationResponse(BaseModel):
    """EBA içerik moderasyon yanıtı"""

    video_id: str = Field(..., description="Video ID")
    status: str = Field(..., description="Yeni durum")  # approved, rejected, flagged
    moderator_id: str = Field(..., description="Moderatör ID")
    moderation_date: datetime = Field(
        default_factory=datetime.now, description="Moderasyon tarihi"
    )
    action_taken: str = Field(..., description="Alınan aksiyon")

    model_config = ConfigDict(from_attributes=True)


class EBAContentUsageAnalytics(BaseModel):
    """EBA içerik kullanım analitikleri"""

    video_id: str = Field(..., description="Video ID")

    # Kullanım Metrikleri
    total_views: int = Field(0, ge=0, description="Toplam görüntülenme")
    unique_viewers: int = Field(0, ge=0, description="Benzersiz izleyici")
    average_watch_time: float = Field(0.0, ge=0, description="Ortalama izleme süresi")
    completion_rate: float = Field(0.0, ge=0, le=100, description="Tamamlama oranı")

    # Etkileşim Metrikleri
    likes: int = Field(0, ge=0, description="Beğeni sayısı")
    shares: int = Field(0, ge=0, description="Paylaşım sayısı")
    bookmarks: int = Field(0, ge=0, description="Yer imi sayısı")

    # Demografik Dağılım
    grade_level_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Sınıf seviyesi dağılımı"
    )
    subject_interest_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Konu ilgisi dağılımı"
    )

    # Zaman Analizi
    peak_viewing_hours: List[int] = Field(
        default_factory=list, description="Yoğun izlenme saatleri"
    )
    weekly_trend: Dict[str, int] = Field(
        default_factory=dict, description="Haftalık trend"
    )

    # Performans Metrikleri
    engagement_score: float = Field(0.0, ge=0, le=10, description="Etkileşim skoru")
    educational_effectiveness: float = Field(
        0.0, ge=0, le=10, description="Eğitsel etkinlik"
    )

    # Meta Veriler
    analytics_period: str = Field(..., description="Analiz dönemi")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Son güncelleme"
    )

    model_config = ConfigDict(from_attributes=True)
