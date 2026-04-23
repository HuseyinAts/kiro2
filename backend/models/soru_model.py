"""
Soru modeli - sorular tablosu için doğru mapping
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, MetaData, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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
        String, primary_key=True, default=uuid.uuid4
    )

    # Soru içeriği
    kod: Mapped[str | None] = mapped_column(String)
    metin: Mapped[str] = mapped_column(Text, nullable=False)
    secenekler: Mapped[dict] = mapped_column(JSONB, nullable=False)
    dogru_cevap: Mapped[str] = mapped_column(String, nullable=False)

    # Sınıf ve konu bilgileri
    sinav_tipi: Mapped[str] = mapped_column(String, nullable=False)
    konu: Mapped[str] = mapped_column(String, nullable=False)
    alt_konu: Mapped[str | None] = mapped_column(String)
    kazanim: Mapped[str | None] = mapped_column(String)

    # IRT parametreleri
    irt_discrimination: Mapped[float | None] = mapped_column(Float)
    irt_difficulty: Mapped[float | None] = mapped_column(Float)
    irt_guessing: Mapped[float | None] = mapped_column(Float)
    irt_upper_asymptote: Mapped[float | None] = mapped_column(Float)

    # Zorluk seviyesi
    zorluk: Mapped[str | None] = mapped_column(String)

    # İstatistikler
    cozulme_sayisi: Mapped[int | None] = mapped_column(Integer)
    dogru_cozulme_sayisi: Mapped[int | None] = mapped_column(Integer)
    ortalama_sure: Mapped[float | None] = mapped_column(Float)

    # Metin analizi
    morfoloji_skoru: Mapped[float | None] = mapped_column(Float)
    kelime_sayisi: Mapped[int | None] = mapped_column(Integer)
    cumle_karmasikligi: Mapped[float | None] = mapped_column(Float)

    # Medya
    gorsel_url: Mapped[str | None] = mapped_column(String)
    video_url: Mapped[str | None] = mapped_column(String)

    # Kaynak bilgisi
    kaynak: Mapped[str | None] = mapped_column(String)
    yil: Mapped[int | None] = mapped_column(Integer)

    # Durum
    aktif: Mapped[bool | None] = mapped_column(Boolean)

    # Tarihler
    olusturma_tarihi: Mapped[datetime | None] = mapped_column(DateTime)
    guncelleme_tarihi: Mapped[datetime | None] = mapped_column(DateTime)

    # Diğer metadata
    irt_confidence: Mapped[float | None] = mapped_column(Float)
    calibration_sample_size: Mapped[int | None] = mapped_column(Integer)
    last_calibration_date: Mapped[datetime | None] = mapped_column(DateTime)
    plagiarism_score: Mapped[float | None] = mapped_column(Float)
    plagiarism_check_date: Mapped[datetime | None] = mapped_column(DateTime)
    knowledge_graph_id: Mapped[str | None] = mapped_column(String)
    prerequisite_topics: Mapped[list | None] = mapped_column(JSONB)
    ai_validation_confidence: Mapped[float | None] = mapped_column(Float)
    expert_review_score: Mapped[int | None] = mapped_column(Integer)
    expert_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(String)
    review_date: Mapped[datetime | None] = mapped_column(DateTime)
    bloom_level: Mapped[str | None] = mapped_column(String)
    cognitive_skills: Mapped[list | None] = mapped_column(JSONB)
    usage_count: Mapped[int | None] = mapped_column(Integer)
    correct_rate: Mapped[float | None] = mapped_column(Float)
    avg_response_time: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String)

    # Visual content support (Phase 1: Tables, Phase 2: Graphs, Phase 3: Geometry)
    visual_content: Mapped[dict | None] = mapped_column(JSONB)

    # Taxonomy fields (SOLO, Marzano, Webb DOK)
    solo_level: Mapped[str | None] = mapped_column(String)
    marzano_system: Mapped[str | None] = mapped_column(String)
    marzano_cognitive_level: Mapped[str | None] = mapped_column(String)
    webb_dok_level: Mapped[str | None] = mapped_column(String)
    taxonomy_consistency_score: Mapped[float | None] = mapped_column(Float)

    # Quality enhancement fields
    cognitive_load_estimate: Mapped[float | None] = mapped_column(Float)
    difficulty_trend: Mapped[str | None] = mapped_column(String)
    linked_misconceptions: Mapped[list | None] = mapped_column(JSONB)
    turkish_readability_index: Mapped[float | None] = mapped_column(Float)
