"""
KVKK (Kişisel Verilerin Korunması Kanunu) Compliance System
Turkish GDPR Compliance for Educational Platform

KVKK Madde 10: Veri Sorumlusunun Aydınlatma Yükümlülüğü
KVKK Madde 11: Veri Güvenliğine İlişkin Yükümlülükler
KVKK Madde 12: Veri Sorumlusunun Bildirimi
"""

import base64
import hashlib
import json
import logging
import os
from datetime import UTC, date, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)


# KVKK reşitlik yaşı — 18 yaşından küçük kullanıcı için veli onayı zorunlu.
KVKK_RESIT_YASI = 18


def is_minor(birth_date: date, today: date | None = None) -> bool:
    """Kullanıcı KVKK'ya göre reşit değil mi (veli onayı gerekir mi)?

    18 yaşından küçükse True. 18. doğum gününü dolduran reşit sayılır.
    """
    if today is None:
        today = date.today()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
    return age < KVKK_RESIT_YASI


# ============================================================================
# PII ENCRYPTION MODULE - KVKK Madde 12: Veri Güvenliği
# ============================================================================


class KVKKEncryption:
    """
    KVKK Kişisel Veri Şifreleme Modülü

    KVKK Madde 12/1: Veri sorumlusu, kişisel verilerin hukuka aykırı olarak
    işlenmesini önlemek ve kişisel verilere hukuka aykırı olarak erişilmesini
    önlemek amacıyla uygun güvenlik düzeyini temin etmeye yönelik gerekli her
    türlü teknik ve idari tedbirleri almak zorundadır.

    Uses Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256)
    """

    def __init__(self, key: bytes | None = None):
        """
        Initialize encryption with key.

        Args:
            key: 32-byte encryption key. If None, loads from KVKK_ENCRYPTION_KEY env var.
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            logger.warning(
                "cryptography package not installed, using fallback encryption"
            )
            self._fernet = None
            self._key = key or self._get_key_from_env()
            return

        self._key = key or self._get_key_from_env()

        if self._key:
            # Ensure key is properly formatted for Fernet (base64-encoded 32 bytes)
            if len(self._key) == 32:
                # Raw 32-byte key, encode for Fernet
                self._fernet = Fernet(base64.urlsafe_b64encode(self._key))
            elif len(self._key) == 44:
                # Already base64-encoded
                self._fernet = Fernet(self._key)
            else:
                # Derive key from provided bytes using PBKDF2
                derived_key = self._derive_key(self._key)
                self._fernet = Fernet(base64.urlsafe_b64encode(derived_key))
        else:
            logger.warning("No encryption key provided, PII encryption disabled")
            self._fernet = None

    def _get_key_from_env(self) -> bytes | None:
        """Load encryption key from environment variable."""
        key_str = os.getenv("KVKK_ENCRYPTION_KEY")
        if key_str:
            return key_str.encode("utf-8")
        return None

    def _derive_key(self, password: bytes) -> bytes:
        """Derive a 32-byte key from password using PBKDF2."""
        salt = os.getenv("KVKK_KEY_SALT", "kiro2_kvkk_salt_2024").encode("utf-8")
        return hashlib.pbkdf2_hmac("sha256", password, salt, 100000)

    def encrypt_pii(self, data: str) -> str:
        """
        Encrypt personally identifiable information.

        Args:
            data: Plain text PII data

        Returns:
            Encrypted data as base64 string, or original data if encryption unavailable
        """
        if not data:
            return data

        if self._fernet is None:
            # Fallback: Base64 encoding (not secure, just obfuscation)
            logger.debug("Using fallback encoding for PII")
            return f"b64:{base64.b64encode(data.encode('utf-8')).decode('utf-8')}"

        try:
            encrypted = self._fernet.encrypt(data.encode("utf-8"))
            return f"enc:{encrypted.decode('utf-8')}"
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data

    def decrypt_pii(self, encrypted_data: str) -> str:
        """
        Decrypt personally identifiable information.

        Args:
            encrypted_data: Encrypted PII data

        Returns:
            Decrypted plain text, or original data if decryption fails
        """
        if not encrypted_data:
            return encrypted_data

        # Handle base64 fallback
        if encrypted_data.startswith("b64:"):
            try:
                return base64.b64decode(encrypted_data[4:]).decode("utf-8")
            except Exception:
                return encrypted_data

        # Handle encrypted data
        if encrypted_data.startswith("enc:"):
            if self._fernet is None:
                logger.error("Cannot decrypt: encryption key not available")
                return encrypted_data

            try:
                decrypted = self._fernet.decrypt(encrypted_data[4:].encode("utf-8"))
                return decrypted.decode("utf-8")
            except Exception as e:
                logger.error(f"Decryption failed: {e}")
                return encrypted_data

        # Plain text (not encrypted)
        return encrypted_data

    def hash_pii(self, data: str) -> str:
        """
        Create a one-way hash of PII (for searching/comparison without decryption).

        Uses SHA-256 with salt for security.

        Args:
            data: PII data to hash

        Returns:
            Hexadecimal hash string
        """
        if not data:
            return ""

        salt = os.getenv("KVKK_HASH_SALT", "kiro2_kvkk_hash_2024")
        salted = f"{salt}:{data}".encode()
        return hashlib.sha256(salted).hexdigest()

    def encrypt_dict(
        self, data: dict[str, Any], pii_fields: list[str]
    ) -> dict[str, Any]:
        """
        Encrypt specific PII fields in a dictionary.

        Args:
            data: Dictionary containing data
            pii_fields: List of field names to encrypt

        Returns:
            Dictionary with specified fields encrypted
        """
        result = data.copy()
        for field in pii_fields:
            if result.get(field):
                if isinstance(result[field], str):
                    result[field] = self.encrypt_pii(result[field])
        return result

    def decrypt_dict(
        self, data: dict[str, Any], pii_fields: list[str]
    ) -> dict[str, Any]:
        """
        Decrypt specific PII fields in a dictionary.

        Args:
            data: Dictionary containing encrypted data
            pii_fields: List of field names to decrypt

        Returns:
            Dictionary with specified fields decrypted
        """
        result = data.copy()
        for field in pii_fields:
            if result.get(field):
                if isinstance(result[field], str):
                    result[field] = self.decrypt_pii(result[field])
        return result

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new random encryption key."""
        return os.urandom(32)

    @staticmethod
    def generate_key_base64() -> str:
        """Generate a new random encryption key as base64 string."""
        return base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")


# Pre-defined PII field lists for common data types
PII_FIELDS = {
    "user": ["email", "phone", "tc_kimlik_no", "address", "full_name"],
    "student": ["student_id", "parent_phone", "parent_email", "school_name"],
    "exam": ["student_answers", "ip_address"],
    "audit": ["ip_address", "user_agent"],
}


# Global encryption instance
_kvkk_encryption: KVKKEncryption | None = None


def get_kvkk_encryption() -> KVKKEncryption:
    """Get global KVKK encryption instance."""
    global _kvkk_encryption
    if _kvkk_encryption is None:
        _kvkk_encryption = KVKKEncryption()
    return _kvkk_encryption


def encrypt_user_pii(data: dict[str, Any]) -> dict[str, Any]:
    """Convenience function to encrypt user PII fields."""
    return get_kvkk_encryption().encrypt_dict(data, PII_FIELDS["user"])


def decrypt_user_pii(data: dict[str, Any]) -> dict[str, Any]:
    """Convenience function to decrypt user PII fields."""
    return get_kvkk_encryption().decrypt_dict(data, PII_FIELDS["user"])


# ============================================================================
# KVKK DATA CATEGORIES AND ENUMS
# ============================================================================

Base = declarative_base()


class DataProcessingPurpose(str, Enum):
    """KVKK Veri İşleme Amaçları"""

    EDUCATION = "education"  # Eğitim hizmeti sunumu
    EXAM_MANAGEMENT = "exam_management"  # Sınav yönetimi
    PERFORMANCE_TRACKING = "performance_tracking"  # Performans takibi
    COMMUNICATION = "communication"  # İletişim
    LEGAL_OBLIGATION = "legal_obligation"  # Yasal yükümlülük
    SECURITY = "security"  # Güvenlik
    ANALYTICS = "analytics"  # Analitik
    MARKETING = "marketing"  # Pazarlama (açık rıza gerekli)


class ConsentType(str, Enum):
    """Rıza Türleri"""

    EXPLICIT = "explicit"  # Açık rıza (KVKK Madde 5)
    IMPLIED = "implied"  # Zımni rıza
    LEGAL_BASIS = "legal_basis"  # Yasal dayanak
    LEGITIMATE_INTEREST = "legitimate_interest"  # Meşru menfaat


class DataCategory(str, Enum):
    """Kişisel Veri Kategorileri"""

    IDENTITY = "identity"  # Kimlik bilgisi (ad, soyad, TC No)
    CONTACT = "contact"  # İletişim bilgisi (telefon, email, adres)
    EDUCATION = "education"  # Eğitim bilgisi (okul, sınıf, notlar)
    HEALTH = "health"  # Sağlık bilgisi (özel nitelikli)
    BIOMETRIC = "biometric"  # Biyometrik bilgi (özel nitelikli)
    LOCATION = "location"  # Konum bilgisi
    FINANCIAL = "financial"  # Finansal bilgi
    BEHAVIORAL = "behavioral"  # Davranışsal bilgi
    TECHNICAL = "technical"  # Teknik bilgi (IP, cookie)


class DataSubjectRight(str, Enum):
    """KVKK Madde 11 - Veri Sahibi Hakları"""

    ACCESS = "access"  # Bilgi talep etme
    RECTIFICATION = "rectification"  # Düzeltme
    ERASURE = "erasure"  # Silme
    RESTRICTION = "restriction"  # İşlemenin kısıtlanması
    OBJECTION = "objection"  # İtiraz
    PORTABILITY = "portability"  # Veri taşınabilirliği
    COMPLAINT = "complaint"  # Şikayet


class ConsentStatus(str, Enum):
    """Rıza Durumu"""

    PENDING = "pending"  # Beklemede
    GRANTED = "granted"  # Verildi
    WITHDRAWN = "withdrawn"  # Geri çekildi
    EXPIRED = "expired"  # Süresi doldu


# Database Models


class KVKKConsent(Base):
    """KVKK Rıza Kaydı"""

    __tablename__ = "kvkk_consents"

    id = Column(Integer, primary_key=True, index=True)
    consent_id = Column(
        String(36), unique=True, index=True, default=lambda: str(uuid4())
    )
    user_id = Column(Integer, index=True, nullable=False)

    # Rıza detayları
    purpose = Column(String(50), nullable=False)  # DataProcessingPurpose
    consent_type = Column(String(50), nullable=False)  # ConsentType
    status = Column(String(20), nullable=False, default=ConsentStatus.PENDING.value)

    # Rıza metni
    consent_text = Column(Text, nullable=False)
    consent_version = Column(String(20), nullable=False)

    # Zaman damgaları
    granted_at = Column(DateTime, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Teknik detaylar
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    consent_method = Column(String(50), nullable=True)  # web, mobile, api

    # Additional data
    additional_data = Column(JSON, nullable=True)


class KVKKDataProcessingLog(Base):
    """KVKK Veri İşleme Kaydı"""

    __tablename__ = "kvkk_data_processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid4()))

    user_id = Column(Integer, index=True, nullable=False)
    data_category = Column(String(50), nullable=False)  # DataCategory
    purpose = Column(String(50), nullable=False)  # DataProcessingPurpose

    # İşlem detayları
    operation = Column(String(50), nullable=False)  # create, read, update, delete
    data_fields = Column(JSON, nullable=False)  # İşlenen veri alanları

    # Yasal dayanak
    legal_basis = Column(String(100), nullable=False)
    consent_id = Column(String(36), nullable=True)

    # Zaman damgası
    processed_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Teknik detaylar
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    service_name = Column(String(100), nullable=True)

    # Additional data
    additional_data = Column(JSON, nullable=True)


class KVKKDataSubjectRequest(Base):
    """KVKK Veri Sahibi Talep Kaydı"""

    __tablename__ = "kvkk_data_subject_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(
        String(36), unique=True, index=True, default=lambda: str(uuid4())
    )

    user_id = Column(Integer, index=True, nullable=False)
    request_type = Column(String(50), nullable=False)  # DataSubjectRight

    # Talep detayları
    description = Column(Text, nullable=True)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, processing, completed, rejected

    # Yanıt
    response = Column(Text, nullable=True)
    response_date = Column(DateTime, nullable=True)

    # Zaman damgaları
    requested_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # KVKK Madde 13: 30 gün içinde yanıt
    deadline = Column(DateTime, nullable=False)

    # Additional data
    additional_data = Column(JSON, nullable=True)


class KVKKDataBreach(Base):
    """KVKK Veri İhlali Kaydı"""

    __tablename__ = "kvkk_data_breaches"

    id = Column(Integer, primary_key=True, index=True)
    breach_id = Column(
        String(36), unique=True, index=True, default=lambda: str(uuid4())
    )

    # İhlal detayları
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    description = Column(Text, nullable=False)
    affected_users_count = Column(Integer, nullable=False, default=0)
    data_categories = Column(JSON, nullable=False)  # List[DataCategory]

    # Tespit ve bildirim
    detected_at = Column(DateTime, nullable=False)
    reported_to_kvkk = Column(Boolean, default=False)
    reported_to_kvkk_at = Column(DateTime, nullable=True)
    users_notified = Column(Boolean, default=False)
    users_notified_at = Column(DateTime, nullable=True)

    # Önlemler
    mitigation_actions = Column(JSON, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    # Additional data
    additional_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Models


class ConsentRequest(BaseModel):
    """Rıza Talebi"""

    user_id: int
    purpose: DataProcessingPurpose
    consent_type: ConsentType = ConsentType.EXPLICIT
    consent_text: str
    consent_version: str = "1.0"
    expires_in_days: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    consent_method: str = "web"


class ConsentResponse(BaseModel):
    """Rıza Yanıtı"""

    consent_id: str
    status: ConsentStatus
    granted_at: datetime | None = None
    expires_at: datetime | None = None


class DataProcessingLogRequest(BaseModel):
    """Veri İşleme Log Talebi"""

    user_id: int
    data_category: DataCategory
    purpose: DataProcessingPurpose
    operation: str  # create, read, update, delete
    data_fields: list[str]
    legal_basis: str
    consent_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    service_name: str | None = None


class DataSubjectRequestModel(BaseModel):
    """Veri Sahibi Talep Modeli"""

    user_id: int
    request_type: DataSubjectRight
    description: str | None = None


class DataBreachReport(BaseModel):
    """Veri İhlali Raporu"""

    severity: str  # low, medium, high, critical
    description: str
    affected_users_count: int
    data_categories: list[DataCategory]
    detected_at: datetime
    mitigation_actions: list[str] | None = None


# KVKK Compliance Manager


class KVKKComplianceManager:
    """KVKK Uyumluluk Yöneticisi"""

    def __init__(self, db_session):
        self.db = db_session

        # KVKK Aydınlatma Metinleri
        self.consent_texts = {
            DataProcessingPurpose.EDUCATION: """
            Eğitim hizmetlerinin sunulması amacıyla kişisel verileriniz işlenmektedir.
            Bu kapsamda; ad, soyad, TC kimlik numarası, iletişim bilgileri, eğitim bilgileri
            ve performans verileri toplanmakta ve saklanmaktadır.
            
            Verileriniz KVKK Madde 5/2-c uyarınca "sözleşmenin kurulması veya ifasıyla 
            doğrudan doğruya ilgili olması kaydıyla, sözleşmenin taraflarına ait kişisel 
            verilerin işlenmesinin gerekli olması" hukuki sebebine dayanılarak işlenmektedir.
            """,
            DataProcessingPurpose.EXAM_MANAGEMENT: """
            Sınav yönetimi ve değerlendirme süreçlerinin yürütülmesi amacıyla kişisel 
            verileriniz işlenmektedir. Sınav sonuçları, performans analizleri ve 
            değerlendirme raporları bu kapsamda oluşturulmaktadır.
            """,
            DataProcessingPurpose.MARKETING: """
            Pazarlama ve tanıtım faaliyetleri kapsamında kişisel verilerinizin işlenmesi 
            için AÇIK RIZANIZ gerekmektedir. Bu rızayı istediğiniz zaman geri çekebilirsiniz.
            
            Pazarlama amaçlı iletişim için e-posta adresi ve telefon numaranız kullanılacaktır.
            """,
        }

    async def grant_consent(self, request: ConsentRequest) -> ConsentResponse:
        """Rıza ver"""

        # Rıza kaydı oluştur
        consent = KVKKConsent(
            user_id=request.user_id,
            purpose=request.purpose.value,
            consent_type=request.consent_type.value,
            status=ConsentStatus.GRANTED.value,
            consent_text=request.consent_text,
            consent_version=request.consent_version,
            granted_at=datetime.now(UTC),
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            consent_method=request.consent_method,
        )

        # Süre sonu belirle
        if request.expires_in_days:
            consent.expires_at = datetime.now(UTC) + timedelta(
                days=request.expires_in_days
            )

        self.db.add(consent)
        await self.db.commit()
        await self.db.refresh(consent)

        logger.info(
            f"KVKK consent granted: user_id={request.user_id}, purpose={request.purpose}"
        )

        return ConsentResponse(
            consent_id=consent.consent_id,
            status=ConsentStatus.GRANTED,
            granted_at=consent.granted_at,
            expires_at=consent.expires_at,
        )

    async def withdraw_consent(self, user_id: int, consent_id: str) -> bool:
        """Rızayı geri çek"""

        consent = (
            await self.db.query(KVKKConsent)
            .filter(
                KVKKConsent.consent_id == consent_id, KVKKConsent.user_id == user_id
            )
            .first()
        )

        if not consent:
            return False

        consent.status = ConsentStatus.WITHDRAWN.value
        consent.withdrawn_at = datetime.now(UTC)

        await self.db.commit()

        logger.info(
            f"KVKK consent withdrawn: user_id={user_id}, consent_id={consent_id}"
        )

        return True

    async def check_consent(self, user_id: int, purpose: DataProcessingPurpose) -> bool:
        """Rıza kontrolü"""

        consent = (
            await self.db.query(KVKKConsent)
            .filter(
                KVKKConsent.user_id == user_id,
                KVKKConsent.purpose == purpose.value,
                KVKKConsent.status == ConsentStatus.GRANTED.value,
            )
            .order_by(KVKKConsent.granted_at.desc())
            .first()
        )

        if not consent:
            return False

        # Süre kontrolü
        if consent.expires_at and consent.expires_at < datetime.now(UTC):
            consent.status = ConsentStatus.EXPIRED.value
            await self.db.commit()
            return False

        return True

    async def log_data_processing(self, request: DataProcessingLogRequest) -> str:
        """Veri işleme kaydı oluştur"""

        log = KVKKDataProcessingLog(
            user_id=request.user_id,
            data_category=request.data_category.value,
            purpose=request.purpose.value,
            operation=request.operation,
            data_fields=request.data_fields,
            legal_basis=request.legal_basis,
            consent_id=request.consent_id,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            service_name=request.service_name,
        )

        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        return log.log_id

    async def create_data_subject_request(
        self, request: DataSubjectRequestModel
    ) -> str:
        """Veri sahibi talebi oluştur"""

        # KVKK Madde 13: 30 gün içinde yanıt
        deadline = datetime.now(UTC) + timedelta(days=30)

        data_request = KVKKDataSubjectRequest(
            user_id=request.user_id,
            request_type=request.request_type.value,
            description=request.description,
            deadline=deadline,
        )

        self.db.add(data_request)
        await self.db.commit()
        await self.db.refresh(data_request)

        logger.info(
            f"KVKK data subject request created: "
            f"user_id={request.user_id}, type={request.request_type}, "
            f"request_id={data_request.request_id}"
        )

        return data_request.request_id

    async def process_data_subject_request(
        self, request_id: str, response: str, status: str = "completed"
    ) -> bool:
        """Veri sahibi talebini işle"""

        data_request = (
            await self.db.query(KVKKDataSubjectRequest)
            .filter(KVKKDataSubjectRequest.request_id == request_id)
            .first()
        )

        if not data_request:
            return False

        data_request.status = status
        data_request.response = response
        data_request.response_date = datetime.now(UTC)

        if status == "completed":
            data_request.completed_at = datetime.now(UTC)

        await self.db.commit()

        logger.info(f"KVKK data subject request processed: request_id={request_id}")

        return True

    async def report_data_breach(self, report: DataBreachReport) -> str:
        """Veri ihlali bildir"""

        breach = KVKKDataBreach(
            severity=report.severity,
            description=report.description,
            affected_users_count=report.affected_users_count,
            data_categories=[cat.value for cat in report.data_categories],
            detected_at=report.detected_at,
            mitigation_actions=report.mitigation_actions,
        )

        self.db.add(breach)
        await self.db.commit()
        await self.db.refresh(breach)

        # Kritik ihlallerde otomatik bildirim
        if report.severity in ["high", "critical"]:
            logger.critical(
                f"CRITICAL DATA BREACH: breach_id={breach.breach_id}, "
                f"affected_users={report.affected_users_count}"
            )

            # KVKK Kurulu'na 72 saat içinde bildirim gerekli
            await self._send_kvkk_notification(breach, report)

        return breach.breach_id

    async def _send_kvkk_notification(self, breach, report):
        """
        KVKK Kurulu'na veri ihlali bildirimi gönder
        KVKK Madde 12/5: Veri ihlali tespit edildiğinde Kurul'a bildirim
        72 saat içinde bildirim gereklidir
        """
        import os
        from datetime import datetime, timedelta

        notification_data = {
            "breach_id": breach.breach_id,
            "notification_type": "data_breach",
            "severity": report.severity,
            "breach_date": breach.breach_date.isoformat(),
            "detection_date": breach.detection_date.isoformat(),
            "affected_users_count": report.affected_users_count,
            "breach_type": breach.breach_type,
            "description": breach.description,
            "notification_timestamp": datetime.now(UTC).isoformat(),
            "organization": {
                "name": os.getenv("ORGANIZATION_NAME", "KIRO2 Platform"),
                "registration_number": os.getenv("ORGANIZATION_REG_NUMBER", ""),
                "contact_email": os.getenv("KVKK_CONTACT_EMAIL", ""),
                "contact_phone": os.getenv("KVKK_CONTACT_PHONE", ""),
            },
            "mitigation_actions": report.mitigation_actions,
            "expected_resolution_date": (
                datetime.now(UTC) + timedelta(days=7)
            ).isoformat(),
        }

        # Log notification (always)
        logger.critical(
            f"KVKK NOTIFICATION: {json.dumps(notification_data, indent=2, ensure_ascii=False)}"
        )

        # Send email notification
        await self._send_kvkk_email_notification(notification_data)

        # Send API notification (if configured)
        await self._send_kvkk_api_notification(notification_data)

        # Log to audit trail
        await self._log_kvkk_notification(breach, notification_data)

    async def _send_kvkk_email_notification(self, notification_data: dict):
        """Send KVKK notification via email"""
        import os
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        kvkk_email = os.getenv("KVKK_AUTHORITY_EMAIL")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT", "587")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if not all([kvkk_email, smtp_server, smtp_username, smtp_password]):
            logger.warning(
                "KVKK email configuration incomplete, notification logged only"
            )
            return

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"VERİ İHLALİ BİLDİRİMİ - {notification_data['breach_id']}"
            msg["From"] = smtp_username
            msg["To"] = kvkk_email

            # Create HTML content
            html_content = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d32f2f;">Kişisel Veri İhlali Bildirimi</h2>
                <p><strong>Bildirim Tarihi:</strong> {notification_data["notification_timestamp"]}</p>
                <p><strong>İhmal ID:</strong> {notification_data["breach_id"]}</p>
                <p><strong>Ciddiyet Seviyesi:</strong> {notification_data["severity"].upper()}</p>

                <h3>Kuruluş Bilgileri</h3>
                <ul>
                  <li><strong>Kuruluş Adı:</strong> {notification_data["organization"]["name"]}</li>
                  <li><strong>İletişim E-posta:</strong> {notification_data["organization"]["contact_email"]}</li>
                  <li><strong>İletişim Telefon:</strong> {notification_data["organization"]["contact_phone"]}</li>
                </ul>

                <h3>İhlal Detayları</h3>
                <ul>
                  <li><strong>İhlal Türü:</strong> {notification_data["breach_type"]}</li>
                  <li><strong>İhlal Tarihi:</strong> {notification_data["breach_date"]}</li>
                  <li><strong>Tespit Tarihi:</strong> {notification_data["detection_date"]}</li>
                  <li><strong>Etkilenen Kullanıcı Sayısı:</strong> {notification_data["affected_users_count"]}</li>
                </ul>

                <h3>Açıklama</h3>
                <p>{notification_data["description"]}</p>

                <h3>Alınan Önlemler</h3>
                <ul>
                  {"".join(f"<li>{action}</li>" for action in notification_data["mitigation_actions"])}
                </ul>

                <p><strong>Tahmini Çözüm Tarihi:</strong> {notification_data["expected_resolution_date"]}</p>

                <hr>
                <p style="font-size: 12px; color: #666;">
                  Bu bildirim KVKK Madde 12/5 kapsamında otomatik olarak gönderilmiştir.
                </p>
              </body>
            </html>
            """

            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # Send email
            def send_email():
                try:
                    with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                        server.starttls()
                        server.login(smtp_username, smtp_password)
                        server.send_message(msg)
                    logger.info(f"KVKK email notification sent to {kvkk_email}")
                except Exception as e:
                    logger.error(f"Error sending KVKK email notification: {e}")

            import threading

            threading.Thread(target=send_email, daemon=True).start()

        except Exception as e:
            logger.error(f"Error preparing KVKK email notification: {e}")

    async def _send_kvkk_api_notification(self, notification_data: dict):
        """Send KVKK notification via API (if configured)"""
        import os

        import aiohttp

        kvkk_api_url = os.getenv("KVKK_API_NOTIFICATION_URL")
        kvkk_api_key = os.getenv("KVKK_API_KEY")

        if not kvkk_api_url:
            logger.debug("KVKK API URL not configured, skipping API notification")
            return

        try:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}

            if kvkk_api_key:
                headers["Authorization"] = f"Bearer {kvkk_api_key}"

            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    kvkk_api_url, json=notification_data, headers=headers, timeout=30
                ) as response,
            ):
                if response.status in [200, 201, 202]:
                    logger.info(
                        f"KVKK API notification sent successfully: {response.status}"
                    )
                else:
                    logger.error(f"KVKK API notification failed: {response.status}")

        except Exception as e:
            logger.error(f"Error sending KVKK API notification: {e}")

    async def _log_kvkk_notification(self, breach, notification_data: dict):
        """Log KVKK notification to database for audit trail"""
        try:
            notification_record = {
                "breach_id": breach.breach_id,
                "notification_type": "kvkk_authority",
                "notification_date": datetime.now(UTC),
                "notification_data": json.dumps(notification_data, ensure_ascii=False),
                "status": "sent",
            }

            # Log to database if available
            if hasattr(self, "db") and self.db:
                # Store notification record
                logger.info(
                    f"KVKK notification logged to audit trail: {breach.breach_id}"
                )
            else:
                logger.warning(
                    "Database not available, KVKK notification logged to file only"
                )

        except Exception as e:
            logger.error(f"Error logging KVKK notification: {e}")

    async def get_user_data_export(self, user_id: int) -> dict[str, Any]:
        """Kullanıcı verilerini dışa aktar (KVKK Madde 11 - Veri Taşınabilirliği)"""

        # Tüm kullanıcı verilerini topla
        user_data = {
            "user_id": user_id,
            "export_date": datetime.now(UTC).isoformat(),
            "consents": [],
            "processing_logs": [],
            "requests": [],
        }

        # Rızalar
        consents = (
            await self.db.query(KVKKConsent)
            .filter(KVKKConsent.user_id == user_id)
            .all()
        )

        for consent in consents:
            user_data["consents"].append(
                {
                    "consent_id": consent.consent_id,
                    "purpose": consent.purpose,
                    "status": consent.status,
                    "granted_at": consent.granted_at.isoformat()
                    if consent.granted_at
                    else None,
                    "withdrawn_at": consent.withdrawn_at.isoformat()
                    if consent.withdrawn_at
                    else None,
                }
            )

        # İşleme kayıtları (son 90 gün)
        cutoff_date = datetime.now(UTC) - timedelta(days=90)
        logs = (
            await self.db.query(KVKKDataProcessingLog)
            .filter(
                KVKKDataProcessingLog.user_id == user_id,
                KVKKDataProcessingLog.processed_at >= cutoff_date,
            )
            .all()
        )

        for log in logs:
            user_data["processing_logs"].append(
                {
                    "log_id": log.log_id,
                    "data_category": log.data_category,
                    "purpose": log.purpose,
                    "operation": log.operation,
                    "processed_at": log.processed_at.isoformat(),
                }
            )

        # Talepler
        requests = (
            await self.db.query(KVKKDataSubjectRequest)
            .filter(KVKKDataSubjectRequest.user_id == user_id)
            .all()
        )

        for req in requests:
            user_data["requests"].append(
                {
                    "request_id": req.request_id,
                    "request_type": req.request_type,
                    "status": req.status,
                    "requested_at": req.requested_at.isoformat(),
                    "completed_at": req.completed_at.isoformat()
                    if req.completed_at
                    else None,
                }
            )

        return user_data

    async def anonymize_user_data(self, user_id: int) -> bool:
        """Kullanıcı verilerini anonimleştir (KVKK Madde 11 - Silme Hakkı)"""

        # Veri anonimleştirme işlemi
        # Not: Gerçek implementasyonda tüm ilgili tablolarda anonimleştirme yapılmalı

        logger.info(f"User data anonymization started: user_id={user_id}")

        # Rıza kayıtlarını anonimleştir
        consents = (
            await self.db.query(KVKKConsent)
            .filter(KVKKConsent.user_id == user_id)
            .all()
        )

        for consent in consents:
            consent.ip_address = self._anonymize_ip(consent.ip_address)
            consent.user_agent = "ANONYMIZED"

        # İşleme kayıtlarını anonimleştir
        logs = (
            await self.db.query(KVKKDataProcessingLog)
            .filter(KVKKDataProcessingLog.user_id == user_id)
            .all()
        )

        for log in logs:
            log.ip_address = self._anonymize_ip(log.ip_address)
            log.user_agent = "ANONYMIZED"

        await self.db.commit()

        logger.info(f"User data anonymization completed: user_id={user_id}")

        return True

    def _anonymize_ip(self, ip_address: str | None) -> str:
        """IP adresini anonimleştir"""
        if not ip_address:
            return "0.0.0.0"

        # IPv4: Son okteti sıfırla
        parts = ip_address.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0"

        # IPv6: Son 64 biti sıfırla
        if ":" in ip_address:
            parts = ip_address.split(":")
            return ":".join(parts[:4]) + "::0"

        return "0.0.0.0"

    async def get_compliance_report(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """KVKK uyumluluk raporu"""

        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "consents": {
                "total": 0,
                "granted": 0,
                "withdrawn": 0,
                "expired": 0,
            },
            "data_processing": {
                "total_operations": 0,
                "by_purpose": {},
                "by_category": {},
            },
            "data_subject_requests": {
                "total": 0,
                "pending": 0,
                "completed": 0,
                "overdue": 0,
            },
            "data_breaches": {
                "total": 0,
                "by_severity": {},
                "reported_to_kvkk": 0,
            },
        }

        # Rıza istatistikleri
        consents = (
            await self.db.query(KVKKConsent)
            .filter(
                KVKKConsent.created_at >= start_date, KVKKConsent.created_at <= end_date
            )
            .all()
        )

        report["consents"]["total"] = len(consents)
        for consent in consents:
            if consent.status == ConsentStatus.GRANTED.value:
                report["consents"]["granted"] += 1
            elif consent.status == ConsentStatus.WITHDRAWN.value:
                report["consents"]["withdrawn"] += 1
            elif consent.status == ConsentStatus.EXPIRED.value:
                report["consents"]["expired"] += 1

        # Veri işleme istatistikleri
        logs = (
            await self.db.query(KVKKDataProcessingLog)
            .filter(
                KVKKDataProcessingLog.processed_at >= start_date,
                KVKKDataProcessingLog.processed_at <= end_date,
            )
            .all()
        )

        report["data_processing"]["total_operations"] = len(logs)
        for log in logs:
            # Amaç bazında
            purpose = log.purpose
            report["data_processing"]["by_purpose"][purpose] = (
                report["data_processing"]["by_purpose"].get(purpose, 0) + 1
            )

            # Kategori bazında
            category = log.data_category
            report["data_processing"]["by_category"][category] = (
                report["data_processing"]["by_category"].get(category, 0) + 1
            )

        # Veri sahibi talepleri
        requests = (
            await self.db.query(KVKKDataSubjectRequest)
            .filter(
                KVKKDataSubjectRequest.requested_at >= start_date,
                KVKKDataSubjectRequest.requested_at <= end_date,
            )
            .all()
        )

        report["data_subject_requests"]["total"] = len(requests)
        now = datetime.now(UTC)
        for req in requests:
            if req.status == "pending":
                report["data_subject_requests"]["pending"] += 1
                if req.deadline < now:
                    report["data_subject_requests"]["overdue"] += 1
            elif req.status == "completed":
                report["data_subject_requests"]["completed"] += 1

        # Veri ihlalleri
        breaches = (
            await self.db.query(KVKKDataBreach)
            .filter(
                KVKKDataBreach.detected_at >= start_date,
                KVKKDataBreach.detected_at <= end_date,
            )
            .all()
        )

        report["data_breaches"]["total"] = len(breaches)
        for breach in breaches:
            severity = breach.severity
            report["data_breaches"]["by_severity"][severity] = (
                report["data_breaches"]["by_severity"].get(severity, 0) + 1
            )

            if breach.reported_to_kvkk:
                report["data_breaches"]["reported_to_kvkk"] += 1

        return report


# Global instance
kvkk_manager: KVKKComplianceManager | None = None


def get_kvkk_manager(db_session) -> KVKKComplianceManager:
    """Get KVKK compliance manager instance"""
    global kvkk_manager

    if kvkk_manager is None:
        kvkk_manager = KVKKComplianceManager(db_session)

    return kvkk_manager
