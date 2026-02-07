"""
Soru modeli - sorular tablosu için doğru mapping
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, MetaData
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

# Use a separate metadata to avoid conflicts
soru_metadata = MetaData()


class SoruBase(DeclarativeBase):
    """Base class for Soru model with separate metadata"""

    metadata = soru_metadata


class Soru(SoruBase):
    """Sorular tablosu modeli - Türkçe kolon adları ile"""

    __tablename__ = "sorular"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Soru içeriği
    kod: Mapped[Optional[str]] = mapped_column(String)
    metin: Mapped[str] = mapped_column(Text, nullable=False)
    secenekler: Mapped[dict] = mapped_column(JSONB, nullable=False)
    dogru_cevap: Mapped[str] = mapped_column(String, nullable=False)

    # Sınıf ve konu bilgileri
    sinav_tipi: Mapped[str] = mapped_column(String, nullable=False)
    konu: Mapped[str] = mapped_column(String, nullable=False)
    alt_konu: Mapped[Optional[str]] = mapped_column(String)
    kazanim: Mapped[Optional[str]] = mapped_column(String)

    # IRT parametreleri
    irt_discrimination: Mapped[Optional[float]] = mapped_column(Float)
    irt_difficulty: Mapped[Optional[float]] = mapped_column(Float)
    irt_guessing: Mapped[Optional[float]] = mapped_column(Float)
    irt_upper_asymptote: Mapped[Optional[float]] = mapped_column(Float)

    # Zorluk seviyesi
    zorluk: Mapped[Optional[str]] = mapped_column(String)

    # İstatistikler
    cozulme_sayisi: Mapped[Optional[int]] = mapped_column(Integer)
    dogru_cozulme_sayisi: Mapped[Optional[int]] = mapped_column(Integer)
    ortalama_sure: Mapped[Optional[float]] = mapped_column(Float)

    # Metin analizi
    morfoloji_skoru: Mapped[Optional[float]] = mapped_column(Float)
    kelime_sayisi: Mapped[Optional[int]] = mapped_column(Integer)
    cumle_karmasikligi: Mapped[Optional[float]] = mapped_column(Float)

    # Medya
    gorsel_url: Mapped[Optional[str]] = mapped_column(String)
    video_url: Mapped[Optional[str]] = mapped_column(String)

    # Kaynak bilgisi
    kaynak: Mapped[Optional[str]] = mapped_column(String)
    yil: Mapped[Optional[int]] = mapped_column(Integer)

    # Durum
    aktif: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Tarihler
    olusturma_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime)
    guncelleme_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Diğer metadata
    irt_confidence: Mapped[Optional[float]] = mapped_column(Float)
    calibration_sample_size: Mapped[Optional[int]] = mapped_column(Integer)
    last_calibration_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    plagiarism_score: Mapped[Optional[float]] = mapped_column(Float)
    plagiarism_check_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    knowledge_graph_id: Mapped[Optional[str]] = mapped_column(String)
    prerequisite_topics: Mapped[Optional[list]] = mapped_column(JSONB)
    ai_validation_confidence: Mapped[Optional[float]] = mapped_column(Float)
    expert_review_score: Mapped[Optional[int]] = mapped_column(Integer)
    expert_reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    review_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    bloom_level: Mapped[Optional[str]] = mapped_column(String)
    cognitive_skills: Mapped[Optional[list]] = mapped_column(JSONB)
    usage_count: Mapped[Optional[int]] = mapped_column(Integer)
    correct_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_response_time: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String)

    # Visual content support (Phase 1: Tables, Phase 2: Graphs, Phase 3: Geometry)
    visual_content: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Taxonomy fields (SOLO, Marzano, Webb DOK)
    solo_level: Mapped[Optional[str]] = mapped_column(String)
    marzano_system: Mapped[Optional[str]] = mapped_column(String)
    marzano_cognitive_level: Mapped[Optional[str]] = mapped_column(String)
    webb_dok_level: Mapped[Optional[str]] = mapped_column(String)
    taxonomy_consistency_score: Mapped[Optional[float]] = mapped_column(Float)

    # Quality enhancement fields
    cognitive_load_estimate: Mapped[Optional[float]] = mapped_column(Float)
    difficulty_trend: Mapped[Optional[str]] = mapped_column(String)
    linked_misconceptions: Mapped[Optional[list]] = mapped_column(JSONB)
    turkish_readability_index: Mapped[Optional[float]] = mapped_column(Float)
