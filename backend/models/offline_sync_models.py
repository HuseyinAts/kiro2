"""
Offline Sync — ORM model for offline_sync_packages.

F4-S2 kok-neden fix: bu tablo raw-SQL (op.execute) ile olusturulmustu, hicbir
ORM modeli yoktu. Alembic autogenerate onu "yetim" tablo sanip migration
c555a10f4b93_sync_db_changes (2026-06-11) ile DUSURDU ve hic geri
olusturulmadi — tum offline-sync ozelligi sessizce devre disi kaldi.
Bu model + eslesen migration tabloyu ORIJINAL semasiyla geri getirir VE
autogenerate'in onu bir daha yetim sanmasini onler.
"""

from __future__ import annotations

import uuid
from uuid6 import uuid7
from datetime import datetime

from sqlalchemy import String, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB

from .database import Base


class OfflineSyncPackage(Base):
    """Bir ogrencinin cevrimdisi calisma paketi (soru id listesi + tuketim durumu)."""

    __tablename__ = "offline_sync_packages"

    package_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    consumed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    question_ids = Column(JSONB, nullable=True)
