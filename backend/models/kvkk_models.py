"""
KVKK (Turkish GDPR) Compliance Models
PHASE 2 Sprint 5: KVKK Compliance

Models for:
- Consent management
- Data export requests
- Data deletion requests
- Privacy policy versions
- Audit logging
"""
import uuid
from datetime import datetime
from typing import Optional, Dict
from enum import Enum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLEnum,
    ForeignKey, Integer, JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class ConsentStatus(str, Enum):
    """Consent status enum"""
    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class DataProcessingPurpose(str, Enum):
    """KVKK data processing purposes"""
    # Temel hizmet sunumu
    SERVICE_PROVISION = "service_provision"  # Hizmet sunumu
    ACCOUNT_MANAGEMENT = "account_management"  # Hesap yönetimi
    AUTHENTICATION = "authentication"  # Kimlik doğrulama

    # İletişim
    COMMUNICATION = "communication"  # İletişim
    NOTIFICATIONS = "notifications"  # Bildirimler
    SUPPORT = "support"  # Destek hizmetleri

    # Analitik ve iyileştirme
    ANALYTICS = "analytics"  # Analitik
    PERFORMANCE_MONITORING = "performance_monitoring"  # Performans izleme
    PRODUCT_IMPROVEMENT = "product_improvement"  # Ürün geliştirme

    # Pazarlama
    MARKETING = "marketing"  # Pazarlama
    PERSONALIZATION = "personalization"  # Kişiselleştirme

    # Yasal yükümlülükler
    LEGAL_COMPLIANCE = "legal_compliance"  # Yasal uyumluluk
    FRAUD_PREVENTION = "fraud_prevention"  # Dolandırıcılık önleme

    # Eğitim özel
    EXAM_EVALUATION = "exam_evaluation"  # Sınav değerlendirme
    PROGRESS_TRACKING = "progress_tracking"  # İlerleme takibi
    CONTENT_RECOMMENDATION = "content_recommendation"  # İçerik önerisi


class ExportRequestStatus(str, Enum):
    """Data export request status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class DeletionRequestStatus(str, Enum):
    """Data deletion request status"""
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"


# ============================================================================
# KVKK Consent Management
# ============================================================================

class KVKKConsent(Base):
    """
    KVKK user consent records

    Tracks user consent for specific data processing purposes
    """
    __tablename__ = "kvkk_consents"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Consent details
    purpose: Mapped[DataProcessingPurpose] = mapped_column(
        SQLEnum(DataProcessingPurpose), nullable=False
    )
    status: Mapped[ConsentStatus] = mapped_column(
        SQLEnum(ConsentStatus), nullable=False, default=ConsentStatus.GIVEN
    )

    # Consent metadata
    consent_text: Mapped[str] = mapped_column(Text, nullable=False)  # Shown to user
    privacy_policy_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # Timestamps
    given_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    additional_data: Mapped[Optional[dict]] = mapped_column(JSON)

    # Indexes
    __table_args__ = (
        {"extend_existing": True}
    )


class KVKKPrivacyPolicyVersion(Base):
    """
    Privacy policy versions for KVKK compliance

    Tracks different versions of privacy policy
    """
    __tablename__ = "kvkk_privacy_policy_versions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    version: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    effective_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id")
    )


# ============================================================================
# Data Subject Rights
# ============================================================================

class KVKKDataExportRequest(Base):
    """
    User data export requests (KVKK Right to Data Portability)

    Users can request export of their personal data
    """
    __tablename__ = "kvkk_data_export_requests"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Request details
    status: Mapped[ExportRequestStatus] = mapped_column(
        SQLEnum(ExportRequestStatus),
        nullable=False,
        default=ExportRequestStatus.PENDING
    )
    request_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Export details
    export_format: Mapped[str] = mapped_column(
        String(20), nullable=False, default="json"
    )  # json, csv, pdf
    data_categories: Mapped[Optional[dict]] = mapped_column(JSON)  # Which data to export

    # File details
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    download_url: Mapped[Optional[str]] = mapped_column(String(500))
    download_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Processing details
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class KVKKDataDeletionRequest(Base):
    """
    User data deletion requests (KVKK Right to Erasure)

    Users can request deletion of their personal data
    """
    __tablename__ = "kvkk_data_deletion_requests"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Request details
    status: Mapped[DeletionRequestStatus] = mapped_column(
        SQLEnum(DeletionRequestStatus),
        nullable=False,
        default=DeletionRequestStatus.PENDING
    )
    request_reason: Mapped[str] = mapped_column(Text, nullable=False)
    deletion_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="full"
    )  # full, partial

    # Data to delete
    data_categories: Mapped[Optional[dict]] = mapped_column(JSON)

    # Review details
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id")
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )


# ============================================================================
# Audit Logging
# ============================================================================

class KVKKAuditLog(Base):
    """
    KVKK audit log for data access and processing

    Tracks all personal data access for compliance
    """
    __tablename__ = "kvkk_audit_logs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Who accessed data
    user_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id"), index=True
    )  # User whose data was accessed
    accessed_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id"), index=True
    )  # Who accessed (admin, system, etc.)

    # What was accessed
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    # Actions: view, export, modify, delete, consent_given, consent_withdrawn

    resource_type: Mapped[str] = mapped_column(String(100))  # user, exam, question
    resource_id: Mapped[Optional[str]] = mapped_column(String)

    # Processing purpose
    purpose: Mapped[Optional[DataProcessingPurpose]] = mapped_column(
        SQLEnum(DataProcessingPurpose)
    )

    # Metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    request_method: Mapped[Optional[str]] = mapped_column(String(10))
    request_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Additional data
    details: Mapped[Optional[dict]] = mapped_column(JSON)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


__all__ = [
    "ConsentStatus",
    "DataProcessingPurpose",
    "ExportRequestStatus",
    "DeletionRequestStatus",
    "KVKKConsent",
    "KVKKPrivacyPolicyVersion",
    "KVKKDataExportRequest",
    "KVKKDataDeletionRequest",
    "KVKKAuditLog",
]
