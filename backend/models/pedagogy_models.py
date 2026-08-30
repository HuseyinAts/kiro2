"""
Pedagogy Models
Teknofest 2025 Eğitim Eylemci Platformu & KIRO2 İçerik Master Planı

İçerik Zehirlenmesi filtreleri (MEBCurriculumNode) ve Kavram Yanılgısı (MisconceptionMatrix) altyapısı.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from uuid6 import uuid7

from .base import Base
from .enums_db import SubjectArea


class MEBCurriculumNode(Base):
    """MEB Kazanım Listesi (Golden Knowledge Base) - Müfredat Dışı Bilgi Filtresi"""

    __tablename__ = "meb_curriculum_nodes"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )  # Örn: 11.2.1.a
    description: Mapped[str] = mapped_column(Text, nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)

    # Yasaklı/Müfredat dışı kelimeler (Örn: ["türev", "integral"] 2024 sonrası 12. sınıf mat için)
    forbidden_keywords: Mapped[list | None] = mapped_column(JSON)
    mandatory_keywords: Mapped[list | None] = mapped_column(JSON)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MisconceptionMatrix(Base):
    """Sık Yapılan Hatalar (Misconception) Sözlüğü - Çeldirici Mühendisliği"""

    __tablename__ = "misconception_matrix"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )  # Örn: MATH_EXP_ADD_BASE
    title: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Örn: Üslü Sayılarda Tabanları Toplama Yanılgısı
    description: Mapped[str] = mapped_column(Text, nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)

    # BKT (Knowledge Tracing) modeli için bu yanılgıya düşen öğrencinin p_T (Öğrenme) katsayısı düşürülür
    # (canlı DB'de gerçekten `integer` -- 30 Ağu 2026 ölçümü; tip ipucu buna göre düzeltildi,
    # önceki `Mapped[float]` gerçek kolon tipiyle uyuşmuyordu)
    severity_weight: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    remedies: Mapped[list["MisconceptionRemedy"]] = relationship(
        "MisconceptionRemedy", back_populates="misconception"
    )


class MisconceptionRemedy(Base):
    """Kavram Yanılgısı Tedavisi (Hap Bilgi / Mikro-Learning)"""

    __tablename__ = "misconception_remedies"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    misconception_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("misconception_matrix.id", ondelete="CASCADE"),
        nullable=False,
    )

    remedy_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # TEXT, IMAGE, VIDEO_CLIP
    content_text: Mapped[str | None] = mapped_column(Text)
    content_url: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[int] = mapped_column(Integer, default=45)  # Max 45 saniye

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    misconception: Mapped["MisconceptionMatrix"] = relationship(
        "MisconceptionMatrix", back_populates="remedies"
    )
