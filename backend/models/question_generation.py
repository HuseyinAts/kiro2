"""
Otomatik Soru Üretim Modelleri
ÖSYM formatında soru üretimi için veri modelleri
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .curriculum import ExamType, GradeLevel, SubjectType


class QuestionType(str, Enum):
    """Soru türleri"""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"
    MATCHING = "matching"
    ORDERING = "ordering"


class DifficultyLevel(str, Enum):
    """Zorluk seviyeleri (5 seviyeli ÖSYM standardı)"""

    COK_KOLAY = "cok_kolay"  # Çok Kolay - Direkt formül
    KOLAY = "kolay"          # Kolay - Tek adım
    ORTA = "orta"            # Orta - Çok adım, standart
    ZOR = "zor"              # Zor - Kavram birleştirme
    COK_ZOR = "cok_zor"      # Çok Zor - Yaratıcı çözüm


class CognitiveLevel(str, Enum):
    """Bilişsel seviyeler (Bloom Taksonomisi)"""

    BILGI = "bilgi"  # C1 - Hatırlama
    KAVRAMA = "kavrama"  # C2 - Anlama
    UYGULAMA = "uygulama"  # C3 - Uygulama
    ANALIZ = "analiz"  # C4 - Analiz
    SENTEZ = "sentez"  # C5 - Değerlendirme
    DEGERLENDIRME = "degerlendirme"  # C6 - Yaratma


class SOLOLevel(str, Enum):
    """SOLO Taksonomi Seviyeleri (Biggs & Collis)"""

    PRESTRUCTURAL = "yapi_oncesi"
    UNISTRUCTURAL = "tek_yapili"
    MULTISTRUCTURAL = "cok_yapili"
    RELATIONAL = "iliskisel"
    EXTENDED_ABSTRACT = "genisletilmis_soyut"


class MarzanoProcessLevel(str, Enum):
    """Marzano Bilissel Islem Seviyeleri"""

    RETRIEVAL = "geri_cagirma"
    COMPREHENSION = "kavrama"
    ANALYSIS = "analiz"
    KNOWLEDGE_UTILIZATION = "bilgi_kullanimi"


class MarzanoSystem(str, Enum):
    """Marzano Taksonomi Sistemleri"""

    COGNITIVE = "bilissel"
    METACOGNITIVE = "ustbilissel"
    SELF_SYSTEM = "oz_sistem"


class WebbDOKLevel(str, Enum):
    """Webb Depth of Knowledge Seviyeleri"""

    RECALL = "hatirlama"
    SKILL = "beceri"
    STRATEGIC = "stratejik"
    EXTENDED = "genisletilmis"


class OSYMQuestionFormat(BaseModel):
    """ÖSYM Soru Format Standardı"""

    question_number: int = Field(..., description="Soru numarası")
    question_text: str = Field(..., description="Soru metni")
    options: List[str] = Field(..., min_length=4, max_length=5, description="Seçenekler")
    correct_answer: str = Field(..., description="Doğru cevap (A, B, C, D, E)")
    explanation: Optional[str] = Field(None, description="Çözüm açıklaması")

    # ÖSYM Format Kontrolleri
    has_visual: bool = Field(default=False, description="Görsel içeriyor mu")
    visual_description: Optional[str] = Field(None, description="Görsel açıklaması")
    reading_time_seconds: int = Field(default=60, description="Okuma süresi (saniye)")
    solution_time_seconds: int = Field(default=120, description="Çözüm süresi (saniye)")


class GeneratedQuestion(BaseModel):
    """Üretilen Soru"""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Soru ID")

    # Temel Bilgiler
    subject: SubjectType = Field(..., description="Ders")
    topic_id: str = Field(..., description="Konu ID")
    topic_name: str = Field(..., description="Konu adı")
    subtopic: Optional[str] = Field(None, description="Alt konu")

    # Soru İçeriği
    question_type: QuestionType = Field(..., description="Soru türü")
    question_text: str = Field(..., description="Soru metni")
    options: List[str] = Field(default_factory=list, description="Seçenekler")
    correct_answer: Union[str, int, List[str]] = Field(..., description="Doğru cevap")
    explanation: str = Field(..., description="Çözüm açıklaması")

    # Zorluk ve Seviye
    difficulty_level: DifficultyLevel = Field(..., description="Zorluk seviyesi")
    cognitive_level: CognitiveLevel = Field(..., description="Bilişsel seviye")
    estimated_time_seconds: int = Field(default=120, description="Tahmini çözüm süresi")

    # ÖSYM Uyumluluk
    osym_format: OSYMQuestionFormat = Field(..., description="ÖSYM format bilgileri")
    osym_compliance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="ÖSYM uyumluluk skoru"
    )

    # MEB Uyumluluk
    meb_standard_id: Optional[str] = Field(None, description="MEB standardı ID")
    learning_outcome_ids: List[str] = Field(
        default_factory=list, description="Öğrenme kazanımları"
    )
    meb_compliance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="MEB uyumluluk skoru"
    )

    # Kalite Metrikleri
    quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Kalite skoru"
    )
    readability_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Okunabilirlik skoru"
    )
    uniqueness_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Benzersizlik skoru"
    )

    # Meta Bilgiler
    generation_method: str = Field(..., description="Üretim yöntemi")
    generation_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Üretim parametreleri"
    )
    source_materials: List[str] = Field(
        default_factory=list, description="Kaynak materyaller"
    )

    # Durum Bilgileri
    is_validated: bool = Field(default=False, description="Doğrulandı mı")
    validation_errors: List[str] = Field(
        default_factory=list, description="Doğrulama hataları"
    )
    is_approved: bool = Field(default=False, description="Onaylandı mı")
    approved_by: Optional[str] = Field(None, description="Onaylayan")

    # Tarihler
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = Field(None, description="Son kullanım tarihi")

    model_config = ConfigDict()


class QuestionGenerationRequest(BaseModel):
    """Soru Üretim Talebi"""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Talep ID")

    # Hedef Kriterler
    subject: SubjectType = Field(..., description="Ders")
    topic_id: str = Field(..., description="Konu ID")
    exam_type: ExamType = Field(..., description="Sınav türü")
    grade_level: Optional[GradeLevel] = Field(None, description="Sınıf seviyesi")

    # Üretim Parametreleri
    question_count: int = Field(
        ..., ge=1, le=10000, description="Üretilecek soru sayısı"
    )
    question_types: List[QuestionType] = Field(..., description="Soru türleri")
    difficulty_distribution: Dict[DifficultyLevel, float] = Field(
        ..., description="Zorluk dağılımı"
    )
    cognitive_distribution: Dict[CognitiveLevel, float] = Field(
        ..., description="Bilişsel seviye dağılımı"
    )

    # Kalite Gereksinimleri
    min_quality_score: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum kalite skoru"
    )
    min_osym_compliance: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum ÖSYM uyumluluk"
    )
    min_meb_compliance: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum MEB uyumluluk"
    )

    # Üretim Ayarları
    generation_method: str = Field(default="ai_assisted", description="Üretim yöntemi")
    use_existing_templates: bool = Field(
        default=True, description="Mevcut şablonları kullan"
    )
    allow_duplicates: bool = Field(default=False, description="Tekrarlara izin ver")

    # Talep Bilgileri
    requested_by: str = Field(..., description="Talep eden")
    priority: str = Field(default="normal", description="Öncelik")
    deadline: Optional[datetime] = Field(None, description="Teslim tarihi")

    # Durum
    status: str = Field(default="pending", description="Durum")
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict()


class QuestionTemplate(BaseModel):
    """Soru Şablonu"""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Şablon ID")

    # Şablon Bilgileri
    name: str = Field(..., description="Şablon adı")
    description: str = Field(..., description="Şablon açıklaması")
    subject: SubjectType = Field(..., description="Ders")
    topic_pattern: str = Field(..., description="Konu deseni")

    # Şablon İçeriği
    question_template: str = Field(..., description="Soru şablonu metni")
    options_template: List[str] = Field(..., description="Seçenek şablonları")
    explanation_template: str = Field(..., description="Açıklama şablonu")

    # Parametreler
    template_variables: Dict[str, str] = Field(
        default_factory=dict, description="Şablon değişkenleri"
    )
    difficulty_level: DifficultyLevel = Field(..., description="Zorluk seviyesi")
    cognitive_level: CognitiveLevel = Field(..., description="Bilişsel seviye")

    # Kullanım İstatistikleri
    usage_count: int = Field(default=0, description="Kullanım sayısı")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Başarı oranı")

    # Meta Bilgiler
    created_by: str = Field(..., description="Oluşturan")
    is_active: bool = Field(default=True, description="Aktif mi")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class QuestionValidationResult(BaseModel):
    """Soru Doğrulama Sonucu"""

    question_id: str = Field(..., description="Soru ID")
    is_valid: bool = Field(..., description="Geçerli mi")

    # Doğrulama Skorları
    osym_compliance_score: float = Field(
        ..., ge=0.0, le=1.0, description="ÖSYM uyumluluk skoru"
    )
    meb_compliance_score: float = Field(
        ..., ge=0.0, le=1.0, description="MEB uyumluluk skoru"
    )
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Kalite skoru")
    readability_score: float = Field(
        ..., ge=0.0, le=1.0, description="Okunabilirlik skoru"
    )

    # Doğrulama Detayları
    validation_checks: Dict[str, bool] = Field(
        default_factory=dict, description="Doğrulama kontrolleri"
    )
    errors: List[str] = Field(default_factory=list, description="Hatalar")
    warnings: List[str] = Field(default_factory=list, description="Uyarılar")
    suggestions: List[str] = Field(default_factory=list, description="Öneriler")

    # Doğrulama Bilgileri
    validated_by: str = Field(..., description="Doğrulayan")
    validation_method: str = Field(..., description="Doğrulama yöntemi")
    validated_at: datetime = Field(default_factory=datetime.now)


class QuestionBankStatus(BaseModel):
    """Soru Bankası Durumu"""

    topic_id: str = Field(..., description="Konu ID")
    topic_name: str = Field(..., description="Konu adı")
    subject: SubjectType = Field(..., description="Ders")

    # Soru Sayıları
    total_questions: int = Field(default=0, description="Toplam soru sayısı")
    validated_questions: int = Field(default=0, description="Doğrulanmış soru sayısı")
    approved_questions: int = Field(default=0, description="Onaylanmış soru sayısı")

    # Hedef ve Durum
    target_question_count: int = Field(default=1000, description="Hedef soru sayısı")
    completion_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Tamamlanma yüzdesi"
    )

    # Kalite Metrikleri
    average_quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ortalama kalite skoru"
    )
    average_osym_compliance: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ortalama ÖSYM uyumluluk"
    )
    average_meb_compliance: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ortalama MEB uyumluluk"
    )

    # Dağılımlar
    difficulty_distribution: Dict[DifficultyLevel, int] = Field(
        default_factory=dict, description="Zorluk dağılımı"
    )
    cognitive_distribution: Dict[CognitiveLevel, int] = Field(
        default_factory=dict, description="Bilişsel dağılım"
    )
    type_distribution: Dict[QuestionType, int] = Field(
        default_factory=dict, description="Tür dağılımı"
    )

    # Durum Bilgileri
    status: str = Field(default="insufficient", description="Durum")
    last_updated: datetime = Field(default_factory=datetime.now)
    next_generation_date: Optional[datetime] = Field(
        None, description="Sonraki üretim tarihi"
    )


class QuestionGenerationReport(BaseModel):
    """Soru Üretim Raporu"""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Rapor ID")

    # Rapor Bilgileri
    report_type: str = Field(..., description="Rapor türü")
    subject: Optional[SubjectType] = Field(None, description="Ders")
    period_start: datetime = Field(..., description="Dönem başlangıcı")
    period_end: datetime = Field(..., description="Dönem sonu")

    # Üretim İstatistikleri
    total_requests: int = Field(default=0, description="Toplam talep sayısı")
    completed_requests: int = Field(default=0, description="Tamamlanan talep sayısı")
    total_questions_generated: int = Field(
        default=0, description="Toplam üretilen soru sayısı"
    )
    total_questions_validated: int = Field(
        default=0, description="Toplam doğrulanmış soru sayısı"
    )

    # Kalite Metrikleri
    average_generation_time: float = Field(
        default=0.0, description="Ortalama üretim süresi (saniye)"
    )
    average_quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ortalama kalite skoru"
    )
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Başarı oranı")

    # Konu Bazlı Durum
    topic_status: List[QuestionBankStatus] = Field(
        default_factory=list, description="Konu bazlı durum"
    )

    # Öneriler
    recommendations: List[str] = Field(default_factory=list, description="Öneriler")
    priority_topics: List[str] = Field(
        default_factory=list, description="Öncelikli konular"
    )

    # Rapor Meta Bilgileri
    generated_by: str = Field(..., description="Raporu oluşturan")
    generated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict()
