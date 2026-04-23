"""
Claude Diary Plugin - Pydantic Schemas

Agent gunluk tutma ve reflection sistemi icin request/response semalari.
Pydantic v2 ile tum validasyonlar.
"""

from __future__ import annotations

import datetime as dt
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

# ============================================================
# Enumerations
# ============================================================


class InsightCategory(str, Enum):
    """Insight kategorileri"""
    TECHNICAL = "technical"
    PROCESS = "process"
    COMMUNICATION = "communication"


class GoalStatus(str, Enum):
    """Hedef durumlari"""
    ACTIVE = "active"
    COMPLETED = "completed"
    AT_RISK = "at_risk"
    CANCELLED = "cancelled"


class ReflectionDepth(str, Enum):
    """Yansitma derinligi"""
    SURFACE = "surface"
    MODERATE = "moderate"
    DEEP = "deep"


class ExportFormat(str, Enum):
    """Export formatlari"""
    MARKDOWN = "markdown"
    PDF = "pdf"
    JSON = "json"


# ============================================================
# Task Summary (for diary entry aggregation)
# ============================================================


class TaskSummary(BaseModel):
    """Task ozet bilgisi"""
    task_id: str | None = Field(None, description="Task ID")
    title: str = Field(..., min_length=1, max_length=500, description="Task basligi")
    status: str = Field(..., description="success veya failure")
    duration_minutes: int = Field(0, ge=0, description="Sure (dakika)")
    task_type: str | None = Field(None, description="Task tipi")
    notes: str | None = Field(None, description="Notlar")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Status validasyonu"""
        allowed = {"success", "failure", "partial", "skipped"}
        if v.lower() not in allowed:
            raise ValueError(f"Status {allowed} olmali")
        return v.lower()


# ============================================================
# REQ-1: Diary Entry Schemas
# ============================================================


class DiaryEntryCreate(BaseModel):
    """Gunluk kaydi olusturma"""
    date: dt.date = Field(..., description="Kayit tarihi")
    tasks: list[TaskSummary] = Field(default_factory=list, description="Tasklar")
    notes: str | None = Field(None, description="Ek notlar")
    highlights: list[str] | None = Field(None, description="One cikan tasklar")
    learnings: list[str] | None = Field(None, description="Ogrenimler")
    challenges: list[str] | None = Field(None, description="Zorluklar")


class DiaryEntryResponse(BaseModel):
    """Gunluk kaydi yaniti"""
    id: UUID
    user_id: UUID
    date: dt.date
    success_count: int
    failure_count: int
    total_tasks: int
    total_duration_minutes: int
    highlights: list[str]
    learnings: list[str]
    challenges: list[str]
    markdown_content: str | None = None
    file_path: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime

    # Computed
    success_rate: float = Field(0.0, description="Basari orani (%)")

    model_config = {"from_attributes": True}


class DiaryEntryUpdate(BaseModel):
    """Gunluk kaydi guncelleme"""
    highlights: list[str] | None = None
    learnings: list[str] | None = None
    challenges: list[str] | None = None
    notes: str | None = None


# ============================================================
# REQ-2: Insight Schemas
# ============================================================


class InsightCreate(BaseModel):
    """Insight olusturma"""
    diary_entry_id: UUID = Field(..., description="Gunluk kaydi ID")
    category: InsightCategory = Field(
        InsightCategory.TECHNICAL,
        description="Kategori"
    )
    pattern: str = Field(..., min_length=10, description="Tespit edilen pattern")
    confidence: float = Field(..., ge=0.8, le=1.0, description="Guven skoru (min 0.8)")
    recommendation: str = Field(..., min_length=10, description="Oneri")
    root_cause: str | None = Field(None, description="Root cause")
    correlation: str | None = Field(None, description="Korelasyon")
    evidence_data: list[dict[str, Any]] | None = Field(None, description="Kanitlar")


class InsightResponse(BaseModel):
    """Insight yaniti"""
    id: UUID
    diary_entry_id: UUID
    user_id: UUID
    category: InsightCategory
    pattern: str
    confidence: float
    evidence_count: int
    recommendation: str
    priority: int
    root_cause: str | None = None
    correlation: str | None = None
    created_at: dt.datetime

    model_config = {"from_attributes": True}


# ============================================================
# REQ-3: Reflection Schemas
# ============================================================


class ReflectionCreate(BaseModel):
    """Yansitma olusturma"""
    diary_entry_id: UUID = Field(..., description="Gunluk kaydi ID")
    what_went_well: str | None = Field(None, description="Ne iyi gitti?")
    what_could_improve: str | None = Field(None, description="Ne gelistirilebilir?")
    what_did_i_learn: str | None = Field(None, description="Ne ogrendim?")
    what_will_i_do_differently: str | None = Field(
        None,
        description="Farkli ne yapacagim?"
    )
    additional_notes: str | None = Field(None, description="Ek notlar")


class ReflectionResponse(BaseModel):
    """Yansitma yaniti"""
    id: UUID
    diary_entry_id: UUID
    user_id: UUID
    what_went_well: str | None
    what_could_improve: str | None
    what_did_i_learn: str | None
    what_will_i_do_differently: str | None
    additional_notes: str | None
    depth: ReflectionDepth
    depth_score: float
    extracted_learnings: list[str]
    action_items: list[str]
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = {"from_attributes": True}


class ReflectionPromptsResponse(BaseModel):
    """Yansitma sorulari yaniti"""
    prompts: list[str] = Field(..., description="Rehberli sorular")
    context_hints: dict[str, str] | None = Field(None, description="Baglamsal ipuclari")


# ============================================================
# REQ-4: Learning Entry Schemas
# ============================================================


class LearningEntryCreate(BaseModel):
    """Ogrenme kaydi olusturma"""
    title: str = Field(..., min_length=3, max_length=255, description="Baslik")
    content: str = Field(..., min_length=10, description="Icerik")
    summary: str | None = Field(None, description="Kisa ozet")
    tags: list[str] = Field(default_factory=list, description="Etiketler")
    domain: str | None = Field(None, description="Alan (backend, frontend, vb.)")
    skill_type: str | None = Field(None, description="Yetenek tipi")
    related_concepts: list[str] | None = Field(None, description="Ilgili kavramlar")
    importance: int = Field(1, ge=1, le=5, description="Onem (1-5)")
    source_type: str | None = Field(None, description="Kaynak tipi")
    source_reference: str | None = Field(None, description="Kaynak referansi")


class LearningEntryResponse(BaseModel):
    """Ogrenme kaydi yaniti"""
    id: UUID
    user_id: UUID
    title: str
    content: str
    summary: str | None
    tags: list[str]
    domain: str | None
    skill_type: str | None
    related_concepts: list[str]
    next_review: datetime | None
    review_count: int
    retention_score: float
    mastery_level: float
    importance: int
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = {"from_attributes": True}


class LearningReviewRequest(BaseModel):
    """Ogrenme inceleme istegi"""
    entry_id: UUID = Field(..., description="Kayit ID")
    remembered: bool = Field(..., description="Hatirlandi mi?")
    quality: int = Field(..., ge=1, le=5, description="Kalite (1-5)")


class LearningReviewResponse(BaseModel):
    """Ogrenme inceleme yaniti"""
    entry_id: UUID
    next_review: dt.datetime
    new_interval_days: int
    retention_score: float
    mastery_level: float


# ============================================================
# REQ-5: Emotional State Schemas
# ============================================================


class EmotionalStateCreate(BaseModel):
    """Duygusal durum olusturma"""
    confidence_level: int = Field(..., ge=1, le=10, description="Guven seviyesi (1-10)")
    frustration_score: float = Field(0.0, ge=0.0, le=1.0, description="Hayal kirikli skoru")
    retry_count: int = Field(0, ge=0, description="Tekrar sayisi")
    error_count: int = Field(0, ge=0, description="Hata sayisi")
    flow_state: bool = Field(False, description="Flow durumunda mi?")
    productivity_score: float = Field(0.0, ge=0.0, le=1.0, description="Uretkenlik skoru")
    tasks_completed: int = Field(0, ge=0, description="Tamamlanan task sayisi")
    task_type: str | None = Field(None, description="Task tipi")
    trigger_factors: dict[str, Any] | None = Field(None, description="Tetikleyici faktorler")
    context_notes: str | None = Field(None, description="Baglam notlari")


class EmotionalStateResponse(BaseModel):
    """Duygusal durum yaniti"""
    id: UUID
    user_id: UUID
    timestamp: dt.datetime
    confidence_level: int
    frustration_score: float
    retry_count: int
    error_count: int
    flow_state: bool
    productivity_score: float
    tasks_completed: int
    task_type: str | None
    trigger_factors: dict[str, Any]
    self_awareness_score: float

    model_config = {"from_attributes": True}


class MoodTrendResponse(BaseModel):
    """Ruh hali trendi yaniti"""
    period_start: dt.date
    period_end: dt.date
    data_points: list[dict[str, Any]] = Field(..., description="Zaman serisi verileri")
    average_confidence: float
    flow_state_percentage: float
    frustration_events: int


# ============================================================
# REQ-6: Goal Schemas
# ============================================================


class MilestoneCreate(BaseModel):
    """Kilometre tasi olusturma"""
    percentage: int = Field(..., ge=0, le=100, description="Yuzde (0-100)")
    title: str = Field(..., min_length=1, max_length=255, description="Baslik")


class MilestoneResponse(BaseModel):
    """Kilometre tasi yaniti"""
    percentage: int
    title: str
    achieved: bool = False
    achieved_at: datetime | None = None


class GoalCreate(BaseModel):
    """Hedef olusturma"""
    title: str = Field(..., min_length=3, max_length=255, description="Hedef basligi")
    description: str | None = Field(None, description="Aciklama")
    target_value: float = Field(..., gt=0, description="Hedef deger")
    target_date: dt.datetime = Field(..., description="Hedef tarih")
    unit: str | None = Field(None, description="Birim (task, saat, puan)")
    category: str | None = Field(None, description="Kategori")
    priority: int = Field(2, ge=1, le=3, description="Oncelik (1=yuksek)")
    milestones: list[MilestoneCreate] = Field(
        default_factory=list,
        description="Kilometre taslari"
    )
    # SMART criteria
    specific: str | None = Field(None, description="Ozgu: Tam olarak ne?")
    measurable: str | None = Field(None, description="Olculebilir: Nasil olculecek?")
    achievable: str | None = Field(None, description="Ulasilabilir: Gercekci mi?")
    relevant: str | None = Field(None, description="Ilgili: Neden onemli?")

    @model_validator(mode="after")
    def validate_smart(self) -> GoalCreate:
        """SMART kriterleri kontrolu"""
        smart_fields = [self.specific, self.measurable, self.achievable, self.relevant]
        filled = sum(1 for f in smart_fields if f)
        if filled > 0 and filled < 4:
            # Uyari: Tum SMART alanlari doldurulmali
            pass  # Soft validation - uyari olarak birak
        return self


class GoalResponse(BaseModel):
    """Hedef yaniti"""
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    progress: int
    current_value: float
    target_value: float
    unit: str | None
    status: GoalStatus
    milestones: list[MilestoneResponse]
    is_at_risk: bool
    risk_factors: list[str]
    velocity: float
    predicted_completion: datetime | None
    start_date: dt.datetime
    target_date: dt.datetime
    completed_at: datetime | None
    category: str | None
    priority: int
    days_remaining: int = Field(0, description="Kalan gun sayisi")
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = {"from_attributes": True}


class GoalUpdate(BaseModel):
    """Hedef guncelleme"""
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    target_value: float | None = Field(None, gt=0)
    target_date: datetime | None = None
    status: GoalStatus | None = None
    milestones: list[MilestoneCreate] | None = None


class GoalProgressUpdate(BaseModel):
    """Hedef ilerleme guncelleme"""
    progress: int | None = Field(None, ge=0, le=100, description="Ilerleme (%)")
    current_value: float | None = Field(None, ge=0, description="Mevcut deger")
    note: str | None = Field(None, description="Ilerleme notu")


class GoalRiskResponse(BaseModel):
    """Hedef risk yaniti"""
    goal_id: UUID
    is_at_risk: bool
    risk_level: str = Field(..., description="low, medium, high")
    risk_factors: list[str]
    recommendations: list[str]
    predicted_completion: datetime | None
    on_track: bool


# ============================================================
# REQ-7: Peer Comparison Schemas
# ============================================================


class PeerComparisonResponse(BaseModel):
    """Akran karsilastirma yaniti"""
    id: UUID
    user_id: UUID
    period_start: dt.date
    period_end: dt.date
    success_rate_percentile: float | None
    speed_percentile: float | None
    quality_percentile: float | None
    overall_percentile: float | None
    strengths: list[dict[str, Any]]
    improvements: list[dict[str, Any]]
    best_practices: list[str]
    peer_group_size: int | None
    created_at: dt.datetime

    model_config = {"from_attributes": True}


# ============================================================
# REQ-8: Export Schemas
# ============================================================


class ExportRequest(BaseModel):
    """Export istegi"""
    format: ExportFormat = Field(ExportFormat.MARKDOWN, description="Format")
    date_from: dt.date = Field(..., description="Baslangic tarihi")
    date_to: dt.date = Field(..., description="Bitis tarihi")
    include_insights: bool = Field(True, description="Insightlari dahil et")
    include_reflections: bool = Field(True, description="Yansitmalari dahil et")
    include_learning: bool = Field(True, description="Ogrenmeleri dahil et")
    include_goals: bool = Field(True, description="Hedefleri dahil et")
    apply_privacy_filter: bool = Field(False, description="Gizlilik filtresi uygula")

    @model_validator(mode="after")
    def validate_dates(self) -> ExportRequest:
        """Tarih validasyonu"""
        if self.date_from > self.date_to:
            raise ValueError("date_from, date_to'dan once olmali")
        return self


class ExportResponse(BaseModel):
    """Export yaniti"""
    id: UUID
    user_id: UUID
    format: ExportFormat
    date_from: dt.date
    date_to: dt.date
    file_path: str | None
    file_size: int | None
    privacy_filter_applied: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class ShareLinkCreate(BaseModel):
    """Paylasim linki olusturma"""
    export_id: UUID = Field(..., description="Export ID")
    expires_in_days: int = Field(7, ge=1, le=30, description="Gecerlilik suresi (gun)")


class ShareLinkResponse(BaseModel):
    """Paylasim linki yaniti"""
    export_id: UUID
    share_token: str
    share_url: str
    expires_at: dt.datetime


# ============================================================
# Common Response Schemas
# ============================================================


class SuccessResponse(BaseModel):
    """Basari yaniti"""
    success: bool = True
    message: str
    data: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Hata yaniti"""
    success: bool = False
    error: str
    detail: str | None = None


class PaginatedResponse(BaseModel):
    """Sayfalanmis yanit"""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
