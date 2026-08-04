"""
FERPA/COPPA Compliance Models
US Education Privacy and Children's Online Privacy Protection

FERPA: Family Educational Rights and Privacy Act
COPPA: Children's Online Privacy Protection Act

Author: KIRO2 AI Team
Date: 2025-01
"""

import uuid
from uuid6 import uuid7
from enum import Enum

from sqlalchemy import (
    String,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class ParentalConsentStatus(str, Enum):
    """COPPA parental consent status"""

    PENDING = "pending"
    VERIFIED = "verified"
    DENIED = "denied"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class EducationalRecordType(str, Enum):
    """FERPA educational record types"""

    ACADEMIC_PERFORMANCE = "academic_performance"
    ATTENDANCE = "attendance"
    BEHAVIORAL_RECORDS = "behavioral_records"
    HEALTH_RECORDS = "health_records"
    SPECIAL_EDUCATION = "special_education"
    DISCIPLINARY_RECORDS = "disciplinary_records"
    STANDARDIZED_TEST_SCORES = "standardized_test_scores"


class FERPAConsent(Base):
    """FERPA consent for educational records access"""

    __tablename__ = "ferpa_consents"

    id = Column(Integer, primary_key=True)
    consent_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Student information
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    parent_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Consent details
    consent_status = Column(
        SQLEnum(ParentalConsentStatus), default=ParentalConsentStatus.PENDING
    )
    record_types = Column(String(500))  # Comma-separated record types

    # Third party disclosure
    allow_third_party_disclosure = Column(Boolean, default=False)
    third_party_institutions = Column(Text, nullable=True)

    # Verification
    parent_verification_method = Column(String(100))  # email, id_verification, etc.
    verification_date = Column(DateTime, nullable=True)
    verification_ip = Column(String(50), nullable=True)

    # Audit
    consent_given_date = Column(DateTime, nullable=True)
    consent_expiry_date = Column(DateTime, nullable=True)
    last_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id], lazy="selectin")
    parent = relationship("User", foreign_keys=[parent_id], lazy="selectin")


class COPPAParentalConsent(Base):
    """COPPA parental consent for under-13 users"""

    __tablename__ = "coppa_parental_consents"

    id = Column(Integer, primary_key=True)
    consent_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Child and parent information
    child_id = Column(String, ForeignKey("users.id"), nullable=False)
    parent_id = Column(String, ForeignKey("users.id"), nullable=False)
    child_date_of_birth = Column(Date, nullable=False)

    # Consent status
    consent_status = Column(
        SQLEnum(ParentalConsentStatus), default=ParentalConsentStatus.PENDING
    )

    # Verification method (COPPA requires verifiable consent)
    verification_method = Column(
        String(100)
    )  # credit_card, id_scan, video_conference, etc.
    verification_date = Column(DateTime, nullable=True)
    verification_document_path = Column(String(500), nullable=True)

    # Data collection permissions
    allow_data_collection = Column(Boolean, default=False)
    allow_marketing_communication = Column(Boolean, default=False)
    allow_third_party_sharing = Column(Boolean, default=False)

    # Consent details
    consent_given_date = Column(DateTime, nullable=True)
    consent_expiry_date = Column(DateTime, nullable=True)
    withdrawal_date = Column(DateTime, nullable=True)
    withdrawal_reason = Column(Text, nullable=True)

    # Audit
    parent_ip_address = Column(String(50))
    parent_user_agent = Column(String(500))
    consent_form_version = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    last_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    child = relationship("User", foreign_keys=[child_id], lazy="selectin")
    parent = relationship("User", foreign_keys=[parent_id], lazy="selectin")


class EducationalRecordAccess(Base):
    """FERPA educational record access log"""

    __tablename__ = "educational_record_access_logs"

    id = Column(Integer, primary_key=True)
    log_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Record access details
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    accessor_id = Column(String, ForeignKey("users.id"), nullable=False)
    accessor_role = Column(String(50))  # parent, teacher, admin, student

    # Access information
    record_type = Column(SQLEnum(EducationalRecordType))
    access_purpose = Column(String(200))
    access_timestamp = Column(DateTime, server_default=func.now())

    # Technical details
    ip_address = Column(String(50))
    user_agent = Column(String(500))

    # FERPA compliance
    legitimate_educational_interest = Column(Boolean, default=True)
    consent_id = Column(String(36), nullable=True)  # Reference to FERPAConsent

    # Relationships
    student = relationship("User", foreign_keys=[student_id], lazy="selectin")
    accessor = relationship("User", foreign_keys=[accessor_id], lazy="selectin")


class DataRetentionPolicy(Base):
    """FERPA/COPPA data retention policies"""

    __tablename__ = "data_retention_policies"

    id = Column(Integer, primary_key=True)
    policy_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Policy details
    policy_name = Column(String(200), nullable=False)
    data_category = Column(String(100))  # educational_records, coppa_data, etc.
    retention_period_days = Column(Integer, nullable=False)

    # Compliance framework
    compliance_framework = Column(String(50))  # FERPA, COPPA, KVKK, GDPR

    # Auto-deletion
    auto_delete_enabled = Column(Boolean, default=False)
    deletion_grace_period_days = Column(Integer, default=30)

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    last_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))


class DataProcessingAgreement(Base):
    """FERPA/COPPA data processing agreements with third parties"""

    __tablename__ = "data_processing_agreements"

    id = Column(Integer, primary_key=True)
    agreement_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Agreement details
    third_party_name = Column(String(200), nullable=False)
    third_party_contact = Column(String(500))
    agreement_type = Column(String(50))  # vendor, partner, contractor

    # Compliance
    ferpa_compliant = Column(Boolean, default=False)
    coppa_compliant = Column(Boolean, default=False)

    # Data handling
    data_types_shared = Column(Text)  # JSON or comma-separated
    data_usage_purpose = Column(Text)
    data_retention_period = Column(Integer)  # days

    # Agreement lifecycle
    agreement_start_date = Column(Date, nullable=False)
    agreement_end_date = Column(Date, nullable=True)
    agreement_status = Column(String(50), default="active")

    # Documents
    agreement_document_path = Column(String(500))

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    last_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())
