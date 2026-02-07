"""
Task 93: OSB Settings Model
OSB (Otizm Spektrum Bozukluğu) kullanıcı tercihlerini saklayan model
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class OSBSettings(Base):
    """
    OSB kullanıcı ayarları
    Öngörülebilir arayüz tercihlerini saklar
    """

    __tablename__ = "osb_settings"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)

    # Genel OSB modu
    osb_mode_enabled = Column(Boolean, default=True, nullable=False)

    # Tutarlı düzen tercihleri (Task 93.1)
    consistent_layout_enabled = Column(Boolean, default=True, nullable=False)
    layout_type = Column(
        String(20), default="default", nullable=False
    )  # default, centered, wide
    predictable_elements = Column(Boolean, default=True, nullable=False)

    # Sabit menü tercihleri (Task 93.2)
    fixed_navigation_enabled = Column(Boolean, default=True, nullable=False)
    navigation_position = Column(
        String(20), default="top", nullable=False
    )  # top, left, bottom
    navigation_variant = Column(
        String(20), default="horizontal", nullable=False
    )  # horizontal, vertical

    # Renk şeması tercihleri (Task 93.3)
    consistent_colors_enabled = Column(Boolean, default=True, nullable=False)
    theme_changes_disabled = Column(
        Boolean, default=True, nullable=False
    )  # OSB modunda tema değişikliği yok
    high_contrast_mode = Column(Boolean, default=False, nullable=False)

    # İkon tercihleri (Task 93.4)
    standard_icons_enabled = Column(Boolean, default=True, nullable=False)
    show_icon_labels = Column(
        Boolean, default=True, nullable=False
    )  # İkonlarda label göster
    icon_size = Column(
        String(10), default="24", nullable=False
    )  # 16, 20, 24, 32, 40, 48

    # Erişilebilirlik
    reduced_motion = Column(Boolean, default=True, nullable=False)
    no_animations = Column(Boolean, default=False, nullable=False)
    no_shadows = Column(Boolean, default=True, nullable=False)  # OSB için shadows yok

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<OSBSettings user_id={self.user_id} osb_mode={self.osb_mode_enabled}>"
