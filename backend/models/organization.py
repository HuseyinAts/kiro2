"""Multi-tenancy kök varlıkları — Faz 0 Step 1.

organizations = tenant kök (okul/dershane/kurum).
org_memberships = user ↔ organization bağı + kurum-içi rol (org_role).

Tasarım: docs/audits/2026-07-03_b2b_readiness_design.md.
Hard rules (CLAUDE.md): VARCHAR PK (users.id deseni), org_type/status/org_role String
(sa.Enum create_type=False güvenilmez), FK kolonları String.
Bu STEP additive — mevcut tablolara dokunmaz; organization_id FK retrofit'i Step 2.
"""

import uuid
from uuid6 import uuid7
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# org_type: dershane | ozel_okul | meb_okul | kurumsal (String, enum değil)
# status: active | suspended | trial | closed
# kvkk_role: controller (okul=veri sorumlusu) | processor
# org_role (membership): SCHOOL_ADMIN | TEACHER | STUDENT | PARENT | OBSERVER


class Organization(Base):
    """Tenant kök varlığı. Tüm kurumsal veri izolasyonunun sahibi."""

    __tablename__ = "organizations"
    __table_args__ = (
        Index("idx_org_status", "status"),
        Index("idx_org_type", "org_type"),
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    org_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ozel_okul",
        comment="dershane | ozel_okul | meb_okul | kurumsal",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="trial",
        comment="active | suspended | trial | closed",
    )
    # KVKK B2B: okul=veri sorumlusu (controller), KIRO2=veri işleyen (processor)
    kvkk_role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="controller"
    )
    kvkk_verbis_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Lisanslama (minimum): koltuk sayısı + bitiş
    license_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    license_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # DPA imzalanmadan okul aktive edilmemeli (design gate)
    dpa_signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    memberships: Mapped[list["OrgMembership"]] = relationship(
        "OrgMembership", back_populates="organization", cascade="all, delete-orphan"
    , lazy="selectin")


class OrgMembership(Base):
    """user ↔ organization bağı + kurum-içi rol. Bir kullanıcı birden çok
    kuruma üye olabilir; (org, user) çifti tekil."""

    __tablename__ = "org_memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_membership"),
        Index("idx_org_membership_org", "organization_id"),
        Index("idx_org_membership_user", "user_id"),
        Index("idx_org_membership_role", "organization_id", "org_role"),
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    org_role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="STUDENT",
        comment="SCHOOL_ADMIN | TEACHER | STUDENT | PARENT | OBSERVER",
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="memberships"
    , lazy="selectin")
