# -*- coding: utf-8 -*-
"""
Veli (Parent) veri modelleri
Türkiye Üniversite Sınavları Hazırlık Platformu için veli takip sistemi
"""

from datetime import datetime
from typing import List, Optional

from models.database import Base
from pydantic import BaseModel, Field
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


class ParentChildRelation(Base):
    """Veli-çocuk ilişki tablosu"""

    __tablename__ = "parent_child_relations"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    child_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    relation_type = Column(String(50), default="parent")  # parent, guardian, etc.
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    # İlişkiler
    # NOTE: back_populates commented out due to User model not having these relationships (import ordering issue)
    parent = relationship(
        "User", foreign_keys=[parent_id]  # back_populates="children_relations"
    )
    child = relationship(
        "User", foreign_keys=[child_id]  # back_populates="parent_relations"
    )


class ParentNotification(Base):
    """Veli bildirimleri tablosu"""

    __tablename__ = "parent_notifications"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    child_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
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
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
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


class ParentChildRelationResponse(BaseModel):
    """Veli-çocuk ilişkisi yanıt modeli"""

    id: int
    parent_id: int
    child_id: int
    child_name: str
    child_email: str
    relation_type: str
    approved: bool
    created_at: datetime
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True


class ChildPerformanceData(BaseModel):
    """Çocuk performans verisi"""

    child_id: int
    child_name: str
    total_study_time: int  # dakika
    exams_taken: int
    average_score: float
    last_exam_date: Optional[datetime]
    last_exam_score: Optional[float]
    weak_subjects: List[str]
    strong_subjects: List[str]
    recent_achievements: List[str]


class WeeklyReportData(BaseModel):
    """Haftalık rapor verisi"""

    child_id: int
    child_name: str
    week_start: datetime
    week_end: datetime
    total_study_time: int
    exams_taken: int
    average_score: float
    subjects_studied: List[str]
    achievements: List[str]
    performance_trend: str  # "improving", "stable", "declining"
    recommendations: List[str]


class ParentNotificationCreate(BaseModel):
    """Veli bildirimi oluşturma modeli"""

    child_id: int
    title: str = Field(..., max_length=200)
    message: str
    # FIX: Pydantic v2 uses 'pattern' instead of 'regex'
    notification_type: str = Field(
        ..., pattern="^(performance|exam|achievement|reminder)$"
    )


class ParentNotificationResponse(BaseModel):
    """Veli bildirimi yanıt modeli"""

    id: int
    child_id: int
    child_name: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True


class ParentDashboardData(BaseModel):
    """Veli dashboard verisi"""

    children: List[ChildPerformanceData]
    unread_notifications: int
    recent_notifications: List[ParentNotificationResponse]
    weekly_summary: dict
    pending_approvals: List[ParentChildRelationResponse]
