"""B2B DPA + Lisanslama/Faturalama MVP — Faz 1.

Tasarım: docs/audits/2026-07-03_b2b_readiness_design.md.
- plans: global plan kataloğu (org-scoped DEĞİL, referans).
- organization_licenses: okul lisansı (koltuk/dönem/durum).
- data_processing_agreements: KVKK DPA (okul=veri sorumlusu, KIRO2=işleyen).
  DPA-signed gate: DPA imzalanmadan okul aktive edilMEZ (design gate).
- invoices: minimum fatura (havale/PO, kart YOK — YAGNI).

Hard rules: VARCHAR PK (users.id deseni), String enum, FK String.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from .base import Base

# plan.code: free | okul_basic | okul_pro | kurumsal
# license.status: trial | active | expired | suspended
# dpa.status: draft | signed | revoked
# invoice.status: draft | sent | paid | void   invoice.method: havale | po | manual


class Plan(Base):
    """Global plan kataloğu (tenant-scoped DEĞİL — referans tablosu)."""

    __tablename__ = "plans"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price_try: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )
    billing_period: Mapped[str] = mapped_column(
        String(12), nullable=False, server_default="yearly"
    )
    seat_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    features: Mapped[dict | None] = mapped_column(JSON, nullable=True, deferred=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OrganizationLicense(Base):
    """Okul lisansı — koltuk (seat), dönem, durum. Tenant-scoped."""

    __tablename__ = "organization_licenses"
    __table_args__ = (
        Index("idx_org_license_org", "organization_id"),
        Index("idx_org_license_status", "status"),
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    organization_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[str] = mapped_column(
        String, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )
    seat_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="trial"
    )
    term_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    term_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DataProcessingAgreement(Base):
    """KVKK DPA — okul (veri sorumlusu) ↔ KIRO2 (veri işleyen).

    DPA-signed gate: okul aktive edilmeden önce status='signed' olmalı.

    TABLO ADI ``billing_data_processing_agreements`` — ÖNEK ZORUNLU. Sade
    ``data_processing_agreements`` adını FERPA/COPPA üçüncü-taraf sözleşme
    tablosu tutuyor (``models/ferpa_coppa_models.py:197``, göç
    ``20260406_ferpa_coppa.py``). ``faz1_billing_20260704`` bu adı almaya
    çalıştı, çakıştı; şema ``cff60c64b93`` ile önekli ada taşındı ama bu model
    ve ``services/billing_service.py`` eski adda kaldı → iki uç 6 hafta boyunca
    500 döndü (S252 ölçümü). ``extend_existing`` KASITLI OLARAK YOK: çakışmayı
    susturan buydu; bundan sonra çakışma ``InvalidRequestError`` ile bağırsın.
    Bekçi: ``tests/integration/test_billing_schema_contract.py``.
    """

    __tablename__ = "billing_data_processing_agreements"
    __table_args__ = (Index("idx_billing_dpa_org", "organization_id"),)

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    organization_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="v1"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    signer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    signer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Invoice(Base):
    """Minimum fatura — havale/PO (kart/metered YOK, YAGNI). Tenant-scoped."""

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_no", name="uq_invoice_no"),
        Index("idx_invoice_org", "organization_id"),
        Index("idx_invoice_status", "status"),
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    organization_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    license_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("organization_licenses.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_no: Mapped[str] = mapped_column(String(40), nullable=False)
    amount_try: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="TRY"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    method: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="havale"
    )
    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    organization: Mapped["object"] = relationship(
        "Organization", viewonly=True, foreign_keys=[organization_id]
    )
