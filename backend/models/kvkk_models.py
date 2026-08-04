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
from uuid6 import uuid7
from datetime import datetime
from enum import Enum

from sqlalchemy import String, JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


def _pg_enum(py_enum, name: str) -> SQLEnum:
    """Bind a Python enum to an existing PostgreSQL enum type.

    The live DB was migrated with snake_case type names (`data_processing_purpose`,
    `consent_status`, ...) and lowercase values (`service_provision`, `given`, ...).
    SQLAlchemy's default ``SQLEnum(PyEnum)`` would instead use
    ``pyenum.__name__.lower()`` as the type name and ``member.name`` (UPPERCASE)
    as the value, which breaks at query time with
    ``type "dataprocessingpurpose" does not exist``.

    Always use this helper for KVKK enums so ORM and DB stay aligned.
    ``create_type=False`` prevents Alembic/SQLAlchemy from trying to CREATE an
    already-present type when metadata.create_all() runs in tests.
    """
    return SQLEnum(
        py_enum,
        name=name,
        values_callable=lambda members: [m.value for m in members],
        create_type=False,
        native_enum=True,
    )


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


class DataRetentionPeriod(str, Enum):
    """KVKK data retention periods (in days)"""

    # Student data - 2 years after graduation (KVKK requirement)
    STUDENT_DATA = "730"  # 2 years
    # Exam results - 5 years for educational records
    EXAM_RESULTS = "1825"  # 5 years
    # Temporary data - 90 days
    TEMPORARY_DATA = "90"
    # Audit logs - 5 years (legal requirement)
    AUDIT_LOGS = "1825"
    # Session data - 30 days
    SESSION_DATA = "30"
    # Consent records - permanent (for legal proof)
    CONSENT_RECORDS = "0"  # 0 = permanent
    # Export files - 7 days after creation
    EXPORT_FILES = "7"
    # Marketing data - until consent withdrawn
    MARKETING_DATA = "365"  # 1 year renewal required


# Data Retention Policy Configuration
DATA_RETENTION_CONFIG = {
    "student_profiles": {
        "retention_days": 730,  # 2 years after graduation
        "deletion_type": "anonymize",  # Keep statistical data
        "notification_days": 30,  # Notify 30 days before deletion
    },
    "exam_results": {
        "retention_days": 1825,  # 5 years
        "deletion_type": "anonymize",
        "notification_days": 90,
    },
    "temporary_files": {
        "retention_days": 90,
        "deletion_type": "hard_delete",
        "notification_days": 0,
    },
    "audit_logs": {
        "retention_days": 1825,  # 5 years (KVKK minimum)
        "deletion_type": "archive",
        "notification_days": 30,
    },
    "session_data": {
        "retention_days": 30,
        "deletion_type": "hard_delete",
        "notification_days": 0,
    },
    "consent_records": {
        "retention_days": 0,  # Never delete (legal proof)
        "deletion_type": "none",
        "notification_days": 0,
    },
    "export_files": {
        "retention_days": 7,
        "deletion_type": "hard_delete",
        "notification_days": 1,
    },
    "marketing_preferences": {
        "retention_days": 365,
        "deletion_type": "reset",
        "notification_days": 30,
    },
}


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

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Consent details
    purpose: Mapped[DataProcessingPurpose] = mapped_column(
        _pg_enum(DataProcessingPurpose, "data_processing_purpose"), nullable=False
    )
    status: Mapped[ConsentStatus] = mapped_column(
        _pg_enum(ConsentStatus, "consent_status"),
        nullable=False,
        default=ConsentStatus.GIVEN,
    )

    # Consent metadata
    consent_text: Mapped[str] = mapped_column(Text, nullable=False, deferred=True)  # Shown to user
    privacy_policy_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # Timestamps
    given_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Metadata
    ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[str | None] = mapped_column(String(500))
    additional_data: Mapped[dict | None] = mapped_column(JSON, deferred=True)

    # Indexes
    __table_args__ = {"extend_existing": True}


class KVKKPrivacyPolicyVersion(Base):
    """
    Privacy policy versions for KVKK compliance

    Tracks different versions of privacy policy
    """

    __tablename__ = "kvkk_privacy_policy_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    version: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, deferred=True)

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    effective_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"))


# ============================================================================
# Data Subject Rights
# ============================================================================


class KVKKDataExportRequest(Base):
    """
    User data export requests (KVKK Right to Data Portability)

    Users can request export of their personal data
    """

    __tablename__ = "kvkk_data_export_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Request details
    status: Mapped[ExportRequestStatus] = mapped_column(
        _pg_enum(ExportRequestStatus, "export_request_status"),
        nullable=False,
        default=ExportRequestStatus.PENDING,
    )
    request_reason: Mapped[str | None] = mapped_column(Text, deferred=True)

    # Export details
    export_format: Mapped[str] = mapped_column(
        String(20), nullable=False, default="json"
    )  # json, csv, pdf
    data_categories: Mapped[dict | None] = mapped_column(JSON, deferred=True)  # Which data to export

    # File details
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    download_url: Mapped[str | None] = mapped_column(String(500))
    download_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Processing details
    error_message: Mapped[str | None] = mapped_column(Text, deferred=True)


class KVKKDataDeletionRequest(Base):
    """
    User data deletion requests (KVKK Right to Erasure)

    Users can request deletion of their personal data
    """

    __tablename__ = "kvkk_data_deletion_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Request details
    status: Mapped[DeletionRequestStatus] = mapped_column(
        _pg_enum(DeletionRequestStatus, "deletion_request_status"),
        nullable=False,
        default=DeletionRequestStatus.PENDING,
    )
    request_reason: Mapped[str] = mapped_column(Text, nullable=False, deferred=True)
    deletion_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="full"
    )  # full, partial

    # Data to delete
    data_categories: Mapped[dict | None] = mapped_column(JSON, deferred=True)

    # Review details
    reviewed_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"))
    review_notes: Mapped[str | None] = mapped_column(Text, deferred=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, deferred=True)

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ============================================================================
# Audit Logging
# ============================================================================


class KVKKAuditLog(Base):
    """
    KVKK audit log for data access and processing

    Tracks all personal data access for compliance
    """

    __tablename__ = "kvkk_audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Who accessed data
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), index=True
    )  # User whose data was accessed
    accessed_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), index=True
    )  # Who accessed (admin, system, etc.)

    # What was accessed
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    # Actions: view, export, modify, delete, consent_given, consent_withdrawn

    resource_type: Mapped[str] = mapped_column(String(100))  # user, exam, question
    resource_id: Mapped[str | None] = mapped_column(String)

    # Processing purpose
    purpose: Mapped[DataProcessingPurpose | None] = mapped_column(
        _pg_enum(DataProcessingPurpose, "data_processing_purpose")
    )

    # Metadata
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    request_method: Mapped[str | None] = mapped_column(String(10))
    request_path: Mapped[str | None] = mapped_column(String(500))

    # Additional data
    details: Mapped[dict | None] = mapped_column(JSON, deferred=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


__all__ = [
    "DATA_RETENTION_CONFIG",
    "ConsentStatus",
    "DataProcessingPurpose",
    "DataRetentionPeriod",
    "DeletionRequestStatus",
    "ExportRequestStatus",
    "KVKKAuditLog",
    "KVKKConsent",
    "KVKKDataDeletionRequest",
    "KVKKDataExportRequest",
    "KVKKPrivacyPolicyVersion",
]
