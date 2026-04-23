"""
Müfredat Uyumluluk Modelleri
MEB ve ÖSYM müfredat standartları için veri modelleri
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SubjectType(str, Enum):
    """Ders türleri"""

    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN_BILIMLERI = "fen_bilimleri"
    SOSYAL_BILGILER = "sosyal_bilgiler"
    TARIH = "tarih"
    COGRAFYA = "cografya"
    FELSEFE = "felsefe"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    GEOMETRI = "geometri"
    YABANCI_DIL = "yabanci_dil"


class ExamType(str, Enum):
    """Sınav türleri"""

    TYT = "tyt"
    AYT = "ayt"
    YDT = "ydt"
    LGS = "lgs"


class GradeLevel(str, Enum):
    """Sınıf seviyeleri"""

    GRADE_9 = "9"
    GRADE_10 = "10"
    GRADE_11 = "11"
    GRADE_12 = "12"


class MEBCurriculumStandard(BaseModel):
    """MEB Müfredat Standardı"""

    id: str = Field(..., description="Müfredat standardı ID")
    subject: SubjectType = Field(..., description="Ders türü")
    grade_level: GradeLevel = Field(..., description="Sınıf seviyesi")
    unit_name: str = Field(..., description="Ünite adı")
    topic_name: str = Field(..., description="Konu adı")
    learning_outcomes: list[str] = Field(
        default_factory=list, description="Öğrenme kazanımları"
    )
    key_concepts: list[str] = Field(
        default_factory=list, description="Anahtar kavramlar"
    )
    skills: list[str] = Field(default_factory=list, description="Beceriler")
    duration_hours: int = Field(default=0, description="Önerilen süre (saat)")
    prerequisites: list[str] = Field(
        default_factory=list, description="Ön koşul konular"
    )
    assessment_criteria: list[str] = Field(
        default_factory=list, description="Değerlendirme kriterleri"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True, description="Aktif durumu")


class OSYMStandard(BaseModel):
    """ÖSYM Sınav Standardı"""

    id: str = Field(..., description="ÖSYM standardı ID")
    exam_type: ExamType = Field(..., description="Sınav türü")
    subject: SubjectType = Field(..., description="Ders türü")
    topic_code: str = Field(..., description="Konu kodu")
    topic_name: str = Field(..., description="Konu adı")
    priority_level: int = Field(..., ge=1, le=5, description="Öncelik seviyesi (1-5)")
    question_count_range: dict[str, int] = Field(..., description="Soru sayısı aralığı")
    difficulty_distribution: dict[str, float] = Field(
        ..., description="Zorluk dağılımı"
    )
    cognitive_levels: list[str] = Field(
        default_factory=list, description="Bilişsel seviyeler"
    )
    exam_frequency: float = Field(default=0.0, description="Sınavlarda çıkma sıklığı")
    last_exam_appearance: str | None = Field(None, description="Son çıktığı sınav")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True, description="Aktif durumu")


class CurriculumAlignment(BaseModel):
    """Müfredat Uyumluluk Eşleştirmesi"""

    id: str = Field(..., description="Eşleştirme ID")
    meb_standard_id: str = Field(..., description="MEB standardı ID")
    osym_standard_id: str = Field(..., description="ÖSYM standardı ID")
    alignment_score: float = Field(..., ge=0.0, le=1.0, description="Uyumluluk skoru")
    alignment_type: str = Field(..., description="Uyumluluk türü")
    gaps_identified: list[str] = Field(
        default_factory=list, description="Tespit edilen boşluklar"
    )
    recommendations: list[str] = Field(default_factory=list, description="Öneriler")
    verified_by: str | None = Field(None, description="Doğrulayan uzman")
    verification_date: datetime | None = Field(None, description="Doğrulama tarihi")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LearningOutcome(BaseModel):
    """Öğrenme Kazanımı"""

    id: str = Field(..., description="Kazanım ID")
    code: str = Field(..., description="Kazanım kodu")
    description: str = Field(..., description="Kazanım açıklaması")
    subject: SubjectType = Field(..., description="Ders türü")
    grade_level: GradeLevel = Field(..., description="Sınıf seviyesi")
    cognitive_level: str = Field(..., description="Bilişsel seviye")
    bloom_taxonomy: str = Field(..., description="Bloom taksonomisi")
    meb_standard_id: str = Field(..., description="Bağlı MEB standardı")
    assessment_methods: list[str] = Field(
        default_factory=list, description="Değerlendirme yöntemleri"
    )
    sample_activities: list[str] = Field(
        default_factory=list, description="Örnek etkinlikler"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class QuestionBankCompliance(BaseModel):
    """Soru Bankası Uyumluluk"""

    id: str = Field(..., description="Uyumluluk ID")
    topic_id: str = Field(..., description="Konu ID")
    subject: SubjectType = Field(..., description="Ders türü")
    total_questions: int = Field(default=0, description="Toplam soru sayısı")
    osym_format_questions: int = Field(
        default=0, description="ÖSYM formatında soru sayısı"
    )
    meb_aligned_questions: int = Field(default=0, description="MEB uyumlu soru sayısı")
    difficulty_distribution: dict[str, int] = Field(
        default_factory=dict, description="Zorluk dağılımı"
    )
    compliance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Uyumluluk skoru"
    )
    minimum_required: int = Field(
        default=1000, description="Minimum gerekli soru sayısı"
    )
    compliance_status: str = Field(
        default="insufficient", description="Uyumluluk durumu"
    )
    last_updated: datetime = Field(default_factory=datetime.now)
    next_review_date: datetime = Field(default_factory=datetime.now)


class CurriculumComplianceReport(BaseModel):
    """Müfredat Uyumluluk Raporu"""

    id: str = Field(..., description="Rapor ID")
    report_type: str = Field(..., description="Rapor türü")
    subject: SubjectType | None = Field(None, description="Ders türü")
    exam_type: ExamType | None = Field(None, description="Sınav türü")
    overall_compliance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Genel uyumluluk skoru"
    )
    meb_compliance_score: float = Field(
        ..., ge=0.0, le=1.0, description="MEB uyumluluk skoru"
    )
    osym_compliance_score: float = Field(
        ..., ge=0.0, le=1.0, description="ÖSYM uyumluluk skoru"
    )

    # Detaylı analiz
    compliant_topics: list[str] = Field(
        default_factory=list, description="Uyumlu konular"
    )
    non_compliant_topics: list[str] = Field(
        default_factory=list, description="Uyumsuz konular"
    )
    missing_topics: list[str] = Field(default_factory=list, description="Eksik konular")

    # Soru bankası durumu
    question_bank_status: dict[str, QuestionBankCompliance] = Field(
        default_factory=dict
    )

    # Öneriler
    recommendations: list[str] = Field(
        default_factory=list, description="İyileştirme önerileri"
    )
    priority_actions: list[str] = Field(
        default_factory=list, description="Öncelikli aksiyonlar"
    )

    # Meta bilgiler
    generated_by: str = Field(..., description="Raporu oluşturan")
    generated_at: datetime = Field(default_factory=datetime.now)
    report_period: dict[str, datetime] = Field(
        default_factory=dict, description="Rapor dönemi"
    )

    model_config = ConfigDict()


class CurriculumUpdateRequest(BaseModel):
    """Müfredat Güncelleme Talebi"""

    id: str = Field(..., description="Güncelleme talebi ID")
    update_type: str = Field(..., description="Güncelleme türü")
    subject: SubjectType = Field(..., description="Ders türü")
    affected_standards: list[str] = Field(..., description="Etkilenen standartlar")
    changes_description: str = Field(..., description="Değişiklik açıklaması")
    source_document: str | None = Field(None, description="Kaynak doküman")
    requested_by: str = Field(..., description="Talep eden")
    requested_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="pending", description="Durum")
    reviewed_by: str | None = Field(None, description="İnceleyen")
    reviewed_at: datetime | None = Field(None, description="İnceleme tarihi")
    implementation_date: datetime | None = Field(None, description="Uygulama tarihi")
    notes: str | None = Field(None, description="Notlar")
