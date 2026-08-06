"""
Veli (Parent) veri modelleri
Türkiye Üniversite Sınavları Hazırlık Platformu için veli takip sistemi
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class ParentNotification(Base):
    """Veli bildirimleri tablosu"""

    __tablename__ = "parent_notifications"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    parent_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    child_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(
        String(50), nullable=False
    )  # performance, exam, achievement
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    # İlişkiler
    parent = relationship("User", foreign_keys=[parent_id])
    child = relationship("User", foreign_keys=[child_id])


class WeeklyReport(Base):
    """Haftalık rapor tablosu"""

    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)

    # Performans metrikleri
    total_study_time = Column(Integer, default=0)  # dakika cinsinden
    exams_taken = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    subjects_studied = Column(String(500), default="")  # JSON string
    achievements = Column(Text, default="")  # JSON string

    # Durum
    generated_at = Column(DateTime, default=datetime.utcnow)
    sent_to_parents = Column(Boolean, default=False)

    # İlişkiler
    child = relationship("User", foreign_keys=[child_id])


# Pydantic modelleri
class ParentChildRelationCreate(BaseModel):
    """Veli-çocuk ilişkisi oluşturma modeli"""

    child_email: str = Field(..., description="Çocuğun email adresi")
    relation_type: str = Field(default="parent", description="İlişki türü")


class VerifyCodeRequest(BaseModel):
    """Veli 6-hane bağlantı kodu doğrulama isteği.

    Uzunluk/desen kısıtı YOK: geçersiz kod (yanlış/eksik/süresi geçmiş) servis
    tarafından {valid: false} ile HTTP 200 döner — Pydantic 422 ile kesilmez.
    """

    code: str = Field(..., description="6-hane bağlantı kodu")


class ParentChildRelationResponse(BaseModel):
    """Veli-çocuk ilişkisi yanıt modeli"""

    id: int
    parent_id: str
    child_id: str
    child_name: str
    child_email: str
    relation_type: str
    approved: bool
    created_at: datetime | None = None
    approved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ChildPerformanceData(BaseModel):
    """Çocuk performans verisi"""

    child_id: str
    child_name: str
    total_study_time: int  # dakika
    exams_taken: int
    average_score: float
    last_exam_date: datetime | None
    last_exam_score: float | None
    weak_subjects: list[str]
    strong_subjects: list[str]
    recent_achievements: list[str]

    # ------------------------------------------------------------------
    # Gerçek KPI alanları (additive, Optional — eski çağıranlar kırılmaz).
    # Veli paneli (VeliPaneliPage) getVeliDashboard adaptörü bunları okur.
    # Tümü ExamSession / StudentAnswer / StudyPlan gerçek verisinden hesaplanır.
    # ------------------------------------------------------------------
    # Son ~5 sınav: [{date, score, type, name}] (type = exam_type tyt/ayt)
    recent_exams: list[dict] = Field(default_factory=list)
    # Son 7 gün günlük çalışma dakikası: [{date, label, minutes}] (7 kayıt)
    weekly_activity: list[dict] = Field(default_factory=list)
    # Son 7 günün toplam çalışma saati (dakika/60, 1 ondalık)
    week_total_hours: float = 0.0
    # Son yarının ort. raw_score'u eksi önceki yarı (işaretli; <2 sınav → 0.0)
    net_change: float = 0.0
    # Bugüne (UTC) kadar kesintisiz ≥1 tamamlanmış sınav günü sayısı
    current_streak: int = 0
    # Bu hafta - geçen hafta tamamlanan sınav sayısı farkı
    exams_taken_delta: int = 0
    # Öğrencinin cevapladığı toplam soru sayısı (StudentAnswer, tüm zaman)
    solved_questions: int = 0
    # Bu hafta - geçen hafta çözülen soru sayısı farkı
    solved_questions_delta: int = 0
    # Ders bazlı doğruluk: [{subject, mastery, answered}] (question_bank.subject_area)
    subject_progress: list[dict] = Field(default_factory=list)
    # Aktif çalışma planı uyum yüzdesi (tamamlanan/hedef); plan yoksa None
    plan_adherence: float | None = None


class WeeklyReportData(BaseModel):
    """Haftalık rapor verisi"""

    child_id: str
    child_name: str
    week_start: datetime
    week_end: datetime
    total_study_time: int
    exams_taken: int
    average_score: float
    subjects_studied: list[str]
    achievements: list[str]
    performance_trend: str  # "improving", "stable", "declining"
    recommendations: list[str]


class ParentNotificationCreate(BaseModel):
    """Veli bildirimi oluşturma modeli"""

    child_id: str
    title: str = Field(..., max_length=200)
    message: str
    # FIX: Pydantic v2 uses 'pattern' instead of 'regex'
    notification_type: str = Field(
        ..., pattern="^(performance|exam|achievement|reminder)$"
    )


class ParentNotificationResponse(BaseModel):
    """Veli bildirimi yanıt modeli"""

    id: int
    child_id: str
    child_name: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ParentDashboardData(BaseModel):
    """Veli dashboard verisi"""

    children: list[ChildPerformanceData]
    unread_notifications: int
    recent_notifications: list[ParentNotificationResponse]
    weekly_summary: dict
    pending_approvals: list[ParentChildRelationResponse]
