"""
Account Security Service - KIRO2 Authentication Enhancement

Hesap guvenligi servisi: supheli aktivite tespiti, cihaz dogrulama,
oturum yonetimi ve hesap kurtarma islemlerini yonetir.

Requirements:
- REQ-8.1: Suspicious activity detection with email alerts
- REQ-8.2: Device verification for new devices
- REQ-8.3: Password change invalidates all sessions
- REQ-8.4: Multi-step verification for account recovery
- REQ-8.5: Last 10 login attempts history
- REQ-8.6: Account lock with admin approval
"""

import hashlib
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from backend.core.structured_logger import get_logger

logger = get_logger(__name__)


# ==================== ENUMS ====================


class SuspiciousActivityReason(str, Enum):
    """Supheli aktivite nedenleri."""

    NEW_DEVICE = "new_device"
    UNUSUAL_IP = "unusual_ip"
    UNUSUAL_LOCATION = "unusual_location"
    MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"
    RAPID_LOGIN_ATTEMPTS = "rapid_login_attempts"
    UNUSUAL_TIME = "unusual_time"
    IP_REPUTATION = "ip_reputation"


class RecommendedAction(str, Enum):
    """Onerilen guvenlik aksiyonlari."""

    ALLOW = "allow"
    VERIFY_DEVICE = "verify_device"
    SEND_ALERT = "send_alert"
    BLOCK_LOGIN = "block_login"
    REQUIRE_MFA = "require_mfa"
    LOCK_ACCOUNT = "lock_account"


class RecoveryStep(str, Enum):
    """Hesap kurtarma adimlari."""

    EMAIL_VERIFICATION = "email_verification"
    SECURITY_QUESTIONS = "security_questions"
    PHONE_VERIFICATION = "phone_verification"
    IDENTITY_VERIFICATION = "identity_verification"
    ADMIN_APPROVAL = "admin_approval"


class AccountLockReason(str, Enum):
    """Hesap kilitleme nedenleri."""

    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    TOO_MANY_FAILED_LOGINS = "too_many_failed_logins"
    USER_REQUEST = "user_request"
    ADMIN_ACTION = "admin_action"
    SECURITY_BREACH = "security_breach"


class AlertType(str, Enum):
    """Guvenlik uyari tipleri."""

    NEW_DEVICE_LOGIN = "new_device_login"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    RECOVERY_INITIATED = "recovery_initiated"
    MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"


# ==================== DATA CLASSES ====================


@dataclass
class DeviceInfo:
    """
    Cihaz bilgilerini temsil eder.

    Attributes:
        device_id: Benzersiz cihaz tanimlayicisi
        fingerprint: Cihaz parmak izi (hash)
        ip_address: Son bilinen IP adresi
        user_agent: Tarayici/cihaz User-Agent bilgisi
        device_name: Kullanici dostu cihaz adi
        is_verified: Cihaz dogrulanmis mi
        first_seen: Ilk gorulen tarih
        last_seen: Son gorulen tarih
        login_count: Bu cihazdan yapilan giris sayisi
    """

    device_id: str
    fingerprint: str
    ip_address: str
    user_agent: str
    device_name: str = ""
    is_verified: bool = False
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    login_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Sozluk formatina donusturur."""
        return {
            "device_id": self.device_id,
            "fingerprint": self.fingerprint,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_name": self.device_name,
            "is_verified": self.is_verified,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "login_count": self.login_count,
        }


@dataclass
class LoginAttempt:
    """
    Giris denemesi kaydi.

    Attributes:
        attempt_id: Benzersiz deneme tanimlayicisi
        timestamp: Deneme zamani
        ip_address: IP adresi
        user_agent: User-Agent bilgisi
        device_fingerprint: Cihaz parmak izi
        success: Basarili mi
        failure_reason: Basarisizlik nedeni (varsa)
        location: Tahmin edilen konum (GeoIP)
        is_suspicious: Supheli mi
    """

    attempt_id: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    device_fingerprint: str
    success: bool
    failure_reason: Optional[str] = None
    location: Optional[str] = None
    is_suspicious: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Sozluk formatina donusturur."""
        return {
            "attempt_id": self.attempt_id,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint": self.device_fingerprint,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "location": self.location,
            "is_suspicious": self.is_suspicious,
        }


@dataclass
class SuspiciousActivityResult:
    """
    Supheli aktivite tespit sonucu.

    Attributes:
        is_suspicious: Aktivite supheli mi
        reasons: Tespit edilen supheli davranis nedenleri
        risk_score: Risk skoru (0-100)
        recommended_action: Onerilen aksiyon
        details: Ek detaylar
    """

    is_suspicious: bool
    reasons: list[SuspiciousActivityReason] = field(default_factory=list)
    risk_score: int = 0
    recommended_action: RecommendedAction = RecommendedAction.ALLOW
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Sozluk formatina donusturur."""
        return {
            "is_suspicious": self.is_suspicious,
            "reasons": [r.value for r in self.reasons],
            "risk_score": self.risk_score,
            "recommended_action": self.recommended_action.value,
            "details": self.details,
        }


@dataclass
class RecoveryResult:
    """
    Hesap kurtarma islemi sonucu.

    Attributes:
        recovery_id: Benzersiz kurtarma islemi tanimlayicisi
        user_id: Kullanici ID
        email: Kullanici email adresi
        steps_required: Gerekli adim sayisi
        current_step: Mevcut adim (0-indexed)
        completed_steps: Tamamlanan adimlar
        remaining_steps: Kalan adimlar
        expires_at: Son gecerlilik tarihi
        is_completed: Tamamlandi mi
    """

    recovery_id: str
    user_id: int
    email: str
    steps_required: int
    current_step: int = 0
    completed_steps: list[RecoveryStep] = field(default_factory=list)
    remaining_steps: list[RecoveryStep] = field(default_factory=list)
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=1)
    )
    is_completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Sozluk formatina donusturur."""
        return {
            "recovery_id": self.recovery_id,
            "user_id": self.user_id,
            "email": self.email,
            "steps_required": self.steps_required,
            "current_step": self.current_step,
            "completed_steps": [s.value for s in self.completed_steps],
            "remaining_steps": [s.value for s in self.remaining_steps],
            "expires_at": self.expires_at.isoformat(),
            "is_completed": self.is_completed,
        }


@dataclass
class AccountLockInfo:
    """
    Hesap kilitleme bilgisi.

    Attributes:
        user_id: Kullanici ID
        locked_at: Kilitleme zamani
        reason: Kilitleme nedeni
        locked_by: Kilitleyen (sistem veya admin ID)
        unlock_requires_admin: Admin onayi gerekli mi
        admin_notes: Admin notlari
    """

    user_id: int
    locked_at: datetime
    reason: AccountLockReason
    locked_by: str = "system"
    unlock_requires_admin: bool = True
    admin_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Sozluk formatina donusturur."""
        return {
            "user_id": self.user_id,
            "locked_at": self.locked_at.isoformat(),
            "reason": self.reason.value,
            "locked_by": self.locked_by,
            "unlock_requires_admin": self.unlock_requires_admin,
            "admin_notes": self.admin_notes,
        }


# ==================== ACCOUNT SECURITY SERVICE ====================


class AccountSecurityService:
    """
    Hesap Guvenligi Servisi.

    Supheli aktivite tespiti, cihaz dogrulama, oturum yonetimi ve
    hesap kurtarma islemlerini yonetir.

    Features:
        - Supheli aktivite tespiti (IP, cihaz, konum analizi)
        - Yeni cihaz dogrulama
        - Sifre degisikliginde tum oturumlari sonlandirma
        - Cok adimli hesap kurtarma
        - Son 10 giris denemesi gecmisi
        - Admin onayiyla hesap kilidi acma

    Attributes:
        MAX_LOGIN_HISTORY: Saklanacak maksimum giris gecmisi sayisi
        VERIFICATION_CODE_EXPIRY: Dogrulama kodu gecerlilik suresi (dakika)
        RECOVERY_EXPIRY_HOURS: Kurtarma islemi gecerlilik suresi (saat)
        SUSPICIOUS_IP_THRESHOLD: Supheli IP degisikligi esigi
    """

    MAX_LOGIN_HISTORY = 10
    VERIFICATION_CODE_EXPIRY = 15  # minutes
    RECOVERY_EXPIRY_HOURS = 1
    SUSPICIOUS_IP_THRESHOLD = 3
    RAPID_LOGIN_THRESHOLD_SECONDS = 30
    MAX_FAILED_ATTEMPTS_THRESHOLD = 5

    def __init__(self) -> None:
        """Servisi baslatir ve in-memory store'lari olusturur."""
        # In-memory stores (production'da Redis/DB kullanilmali)
        self._user_devices: dict[int, list[DeviceInfo]] = {}
        self._login_history: dict[int, list[LoginAttempt]] = {}
        self._verification_codes: dict[str, dict[str, Any]] = {}
        self._recovery_sessions: dict[str, RecoveryResult] = {}
        self._locked_accounts: dict[int, AccountLockInfo] = {}
        self._known_ips: dict[int, set[str]] = {}
        self._active_sessions: dict[int, set[str]] = {}  # user_id -> session_ids

        logger.info(
            "account_security_service_initialized",
            max_login_history=self.MAX_LOGIN_HISTORY,
            verification_expiry_minutes=self.VERIFICATION_CODE_EXPIRY,
        )

    # ==================== DEVICE FINGERPRINTING ====================

    def _generate_device_fingerprint(
        self,
        user_agent: str,
        screen_info: Optional[str] = None,
        additional_data: Optional[str] = None,
    ) -> str:
        """
        Cihaz parmak izi olusturur.

        User-Agent, ekran bilgisi ve ek verileri kullanarak benzersiz
        bir hash olusturur.

        Args:
            user_agent: Tarayici User-Agent bilgisi
            screen_info: Ekran cozunurlugu bilgisi (opsiyonel)
            additional_data: Ek veri (opsiyonel)

        Returns:
            32 karakterlik hex hash string
        """
        data_parts = [user_agent]

        if screen_info:
            data_parts.append(screen_info)

        if additional_data:
            data_parts.append(additional_data)

        combined = "|".join(data_parts)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:32]

    def _generate_device_name(self, user_agent: str) -> str:
        """
        User-Agent'tan kullanici dostu cihaz adi cikarir.

        Args:
            user_agent: Tarayici User-Agent bilgisi

        Returns:
            Kullanici dostu cihaz adi (orn: "Chrome on Windows")
        """
        ua_lower = user_agent.lower()

        # Browser detection
        browser = "Bilinmeyen Tarayici"
        if "chrome" in ua_lower and "edg" not in ua_lower:
            browser = "Chrome"
        elif "firefox" in ua_lower:
            browser = "Firefox"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            browser = "Safari"
        elif "edg" in ua_lower:
            browser = "Edge"
        elif "opera" in ua_lower or "opr" in ua_lower:
            browser = "Opera"

        # OS detection
        os_name = "Bilinmeyen Isletim Sistemi"
        if "windows" in ua_lower:
            os_name = "Windows"
        elif "mac" in ua_lower or "darwin" in ua_lower:
            os_name = "macOS"
        elif "linux" in ua_lower:
            os_name = "Linux"
        elif "android" in ua_lower:
            os_name = "Android"
        elif "iphone" in ua_lower or "ipad" in ua_lower:
            os_name = "iOS"

        return f"{browser} - {os_name}"

    # ==================== SUSPICIOUS ACTIVITY DETECTION ====================

    def detect_suspicious_activity(
        self,
        user_id: int,
        ip: str,
        user_agent: str,
        timestamp: Optional[datetime] = None,
    ) -> SuspiciousActivityResult:
        """
        Supheli aktivite tespiti yapar.

        IP adresi, cihaz bilgisi ve giris paterni analizine dayanarak
        supheli davranislari tespit eder.

        Args:
            user_id: Kullanici ID
            ip: IP adresi
            user_agent: User-Agent bilgisi
            timestamp: Islem zamani (varsayilan: simdi)

        Returns:
            SuspiciousActivityResult: Tespit sonucu ve onerilen aksiyonlar

        Example:
            >>> result = service.detect_suspicious_activity(
            ...     user_id=123,
            ...     ip="192.168.1.1",
            ...     user_agent="Mozilla/5.0..."
            ... )
            >>> if result.is_suspicious:
            ...     print(f"Supheli aktivite: {result.reasons}")
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        reasons: list[SuspiciousActivityReason] = []
        risk_score = 0
        details: dict[str, Any] = {}

        device_fingerprint = self._generate_device_fingerprint(user_agent)

        # Check 1: New device detection
        is_new_device = self._is_new_device(user_id, device_fingerprint)
        if is_new_device:
            reasons.append(SuspiciousActivityReason.NEW_DEVICE)
            risk_score += 20
            details["new_device"] = True

        # Check 2: Unusual IP detection
        is_unusual_ip = self._is_unusual_ip(user_id, ip)
        if is_unusual_ip:
            reasons.append(SuspiciousActivityReason.UNUSUAL_IP)
            risk_score += 25
            details["unusual_ip"] = True
            details["known_ips"] = list(self._known_ips.get(user_id, set()))[:5]

        # Check 3: Multiple failed login attempts
        failed_attempts = self._get_recent_failed_attempts(user_id, minutes=30)
        if failed_attempts >= self.MAX_FAILED_ATTEMPTS_THRESHOLD:
            reasons.append(SuspiciousActivityReason.MULTIPLE_FAILED_LOGINS)
            risk_score += 30
            details["failed_attempts"] = failed_attempts

        # Check 4: Rapid login attempts
        is_rapid = self._detect_rapid_login_attempts(user_id, timestamp)
        if is_rapid:
            reasons.append(SuspiciousActivityReason.RAPID_LOGIN_ATTEMPTS)
            risk_score += 25
            details["rapid_attempts"] = True

        # Check 5: Unusual time (optional - GeoIP based)
        # Placeholder for GeoIP-based time anomaly detection

        # Determine recommended action based on risk score
        recommended_action = self._determine_action(risk_score, reasons)

        is_suspicious = len(reasons) > 0 and risk_score >= 20

        result = SuspiciousActivityResult(
            is_suspicious=is_suspicious,
            reasons=reasons,
            risk_score=min(risk_score, 100),
            recommended_action=recommended_action,
            details=details,
        )

        logger.info(
            "suspicious_activity_check",
            user_id=user_id,
            ip=ip,
            is_suspicious=is_suspicious,
            risk_score=risk_score,
            reasons=[r.value for r in reasons],
            recommended_action=recommended_action.value,
        )

        return result

    def _is_new_device(self, user_id: int, fingerprint: str) -> bool:
        """Cihazin daha once kullanilip kullanilmadigini kontrol eder."""
        devices = self._user_devices.get(user_id, [])
        return not any(d.fingerprint == fingerprint for d in devices)

    def _is_unusual_ip(self, user_id: int, ip: str) -> bool:
        """IP adresinin daha once kullanilip kullanilmadigini kontrol eder."""
        known_ips = self._known_ips.get(user_id, set())

        # First login from this user - not unusual
        if not known_ips:
            return False

        return ip not in known_ips

    def _get_recent_failed_attempts(self, user_id: int, minutes: int = 30) -> int:
        """Son X dakikadaki basarisiz giris denemesi sayisini dondurur."""
        history = self._login_history.get(user_id, [])
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        return sum(
            1 for attempt in history
            if not attempt.success and attempt.timestamp > cutoff
        )

    def _detect_rapid_login_attempts(
        self,
        user_id: int,
        current_timestamp: datetime,
    ) -> bool:
        """Hizli ardisik giris denemelerini tespit eder."""
        history = self._login_history.get(user_id, [])

        if not history:
            return False

        # Check last attempt
        last_attempt = history[-1] if history else None
        if last_attempt:
            time_diff = (current_timestamp - last_attempt.timestamp).total_seconds()
            if time_diff < self.RAPID_LOGIN_THRESHOLD_SECONDS:
                return True

        return False

    def _determine_action(
        self,
        risk_score: int,
        reasons: list[SuspiciousActivityReason],
    ) -> RecommendedAction:
        """Risk skoruna gore onerilen aksiyonu belirler."""
        if risk_score >= 70:
            return RecommendedAction.LOCK_ACCOUNT
        elif risk_score >= 50:
            return RecommendedAction.BLOCK_LOGIN
        elif risk_score >= 40:
            return RecommendedAction.REQUIRE_MFA
        elif SuspiciousActivityReason.NEW_DEVICE in reasons:
            return RecommendedAction.VERIFY_DEVICE
        elif risk_score >= 20:
            return RecommendedAction.SEND_ALERT
        else:
            return RecommendedAction.ALLOW

    # ==================== DEVICE VERIFICATION ====================

    def register_device(
        self,
        user_id: int,
        ip: str,
        user_agent: str,
        screen_info: Optional[str] = None,
    ) -> DeviceInfo:
        """
        Yeni cihaz kaydeder.

        Args:
            user_id: Kullanici ID
            ip: IP adresi
            user_agent: User-Agent bilgisi
            screen_info: Ekran bilgisi (opsiyonel)

        Returns:
            DeviceInfo: Kaydedilen cihaz bilgisi
        """
        fingerprint = self._generate_device_fingerprint(user_agent, screen_info)
        device_name = self._generate_device_name(user_agent)

        device = DeviceInfo(
            device_id=str(uuid.uuid4()),
            fingerprint=fingerprint,
            ip_address=ip,
            user_agent=user_agent,
            device_name=device_name,
            is_verified=False,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            login_count=1,
        )

        # Add to user's devices
        if user_id not in self._user_devices:
            self._user_devices[user_id] = []

        # Check if device already exists
        existing = next(
            (d for d in self._user_devices[user_id] if d.fingerprint == fingerprint),
            None,
        )

        if existing:
            # Update existing device
            existing.last_seen = datetime.now(timezone.utc)
            existing.ip_address = ip
            existing.login_count += 1
            device = existing
        else:
            self._user_devices[user_id].append(device)

        # Track known IPs
        if user_id not in self._known_ips:
            self._known_ips[user_id] = set()
        self._known_ips[user_id].add(ip)

        logger.info(
            "device_registered",
            user_id=user_id,
            device_id=device.device_id,
            device_name=device_name,
            is_new=existing is None,
        )

        return device

    def verify_device(
        self,
        user_id: int,
        device_fingerprint: str,
        verification_code: str,
    ) -> bool:
        """
        Cihaz dogrulama kodunu kontrol eder.

        Args:
            user_id: Kullanici ID
            device_fingerprint: Cihaz parmak izi
            verification_code: Kullanicinin girdigi dogrulama kodu

        Returns:
            bool: Dogrulama basarili mi
        """
        # Find verification code entry
        code_key = f"{user_id}:{device_fingerprint}"
        code_entry = self._verification_codes.get(code_key)

        if not code_entry:
            logger.warning(
                "device_verification_failed",
                user_id=user_id,
                reason="no_verification_code_found",
            )
            return False

        # Check expiry
        if datetime.now(timezone.utc) > code_entry["expires_at"]:
            del self._verification_codes[code_key]
            logger.warning(
                "device_verification_failed",
                user_id=user_id,
                reason="verification_code_expired",
            )
            return False

        # Verify code
        if code_entry["code"] != verification_code:
            logger.warning(
                "device_verification_failed",
                user_id=user_id,
                reason="invalid_verification_code",
            )
            return False

        # Mark device as verified
        devices = self._user_devices.get(user_id, [])
        for device in devices:
            if device.fingerprint == device_fingerprint:
                device.is_verified = True
                break

        # Clean up verification code
        del self._verification_codes[code_key]

        logger.info(
            "device_verified",
            user_id=user_id,
            device_fingerprint=device_fingerprint[:8] + "...",
        )

        return True

    def generate_device_verification_code(
        self,
        user_id: int,
        device_fingerprint: str,
    ) -> str:
        """
        Cihaz dogrulama kodu olusturur.

        Args:
            user_id: Kullanici ID
            device_fingerprint: Cihaz parmak izi

        Returns:
            str: 6 haneli dogrulama kodu
        """
        code = f"{secrets.randbelow(1000000):06d}"
        code_key = f"{user_id}:{device_fingerprint}"

        self._verification_codes[code_key] = {
            "code": code,
            "user_id": user_id,
            "device_fingerprint": device_fingerprint,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(minutes=self.VERIFICATION_CODE_EXPIRY),
        }

        logger.info(
            "device_verification_code_generated",
            user_id=user_id,
            expires_minutes=self.VERIFICATION_CODE_EXPIRY,
        )

        return code

    # ==================== PASSWORD CHANGE SESSION INVALIDATION ====================

    def on_password_change(self, user_id: int) -> int:
        """
        Sifre degisikliginde tum oturumlari sonlandirir.

        Args:
            user_id: Kullanici ID

        Returns:
            int: Sonlandirilan oturum sayisi

        Note:
            REQ-8.3: Password change invalidates all sessions
        """
        sessions = self._active_sessions.get(user_id, set())
        count = len(sessions)

        # Clear all sessions
        if user_id in self._active_sessions:
            self._active_sessions[user_id].clear()

        # Send security alert
        self.send_security_alert(
            user_id=user_id,
            alert_type=AlertType.PASSWORD_CHANGED.value,
            details={
                "invalidated_sessions": count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(
            "sessions_invalidated_on_password_change",
            user_id=user_id,
            invalidated_count=count,
        )

        return count

    def register_session(self, user_id: int, session_id: str) -> None:
        """
        Yeni oturum kaydeder.

        Args:
            user_id: Kullanici ID
            session_id: Oturum ID
        """
        if user_id not in self._active_sessions:
            self._active_sessions[user_id] = set()

        self._active_sessions[user_id].add(session_id)

    def unregister_session(self, user_id: int, session_id: str) -> None:
        """
        Oturumu sonlandirir.

        Args:
            user_id: Kullanici ID
            session_id: Oturum ID
        """
        if user_id in self._active_sessions:
            self._active_sessions[user_id].discard(session_id)

    # ==================== ACCOUNT RECOVERY ====================

    def initiate_account_recovery(self, email: str, user_id: int = 0) -> RecoveryResult:
        """
        Hesap kurtarma islemini baslatir.

        Cok adimli dogrulama sureci icin recovery session olusturur.

        Args:
            email: Kullanici email adresi
            user_id: Kullanici ID (0 ise email'den bulunmali)

        Returns:
            RecoveryResult: Kurtarma islemi bilgileri

        Note:
            REQ-8.4: Multi-step verification for account recovery
        """
        recovery_id = str(uuid.uuid4())

        # Define required steps (can be customized based on security level)
        required_steps = [
            RecoveryStep.EMAIL_VERIFICATION,
            RecoveryStep.SECURITY_QUESTIONS,
        ]

        # For high-security accounts, add admin approval
        # This can be determined by checking user role or security settings

        result = RecoveryResult(
            recovery_id=recovery_id,
            user_id=user_id,
            email=email,
            steps_required=len(required_steps),
            current_step=0,
            completed_steps=[],
            remaining_steps=required_steps.copy(),
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=self.RECOVERY_EXPIRY_HOURS),
            is_completed=False,
        )

        self._recovery_sessions[recovery_id] = result

        # Send recovery initiated alert
        self.send_security_alert(
            user_id=user_id,
            alert_type=AlertType.RECOVERY_INITIATED.value,
            details={
                "recovery_id": recovery_id,
                "email": email,
                "steps_required": len(required_steps),
            },
        )

        logger.info(
            "account_recovery_initiated",
            recovery_id=recovery_id,
            email=email,
            steps_required=len(required_steps),
        )

        return result

    def verify_recovery_step(
        self,
        recovery_id: str,
        step: int,
        verification: str,
    ) -> bool:
        """
        Hesap kurtarma adimini dogrular.

        Args:
            recovery_id: Kurtarma islemi ID
            step: Adim numarasi (0-indexed)
            verification: Dogrulama verisi (kod, cevap vb.)

        Returns:
            bool: Dogrulama basarili mi
        """
        recovery = self._recovery_sessions.get(recovery_id)

        if not recovery:
            logger.warning(
                "recovery_verification_failed",
                recovery_id=recovery_id,
                reason="recovery_not_found",
            )
            return False

        # Check expiry
        if datetime.now(timezone.utc) > recovery.expires_at:
            del self._recovery_sessions[recovery_id]
            logger.warning(
                "recovery_verification_failed",
                recovery_id=recovery_id,
                reason="recovery_expired",
            )
            return False

        # Check step order
        if step != recovery.current_step:
            logger.warning(
                "recovery_verification_failed",
                recovery_id=recovery_id,
                reason="invalid_step_order",
                expected_step=recovery.current_step,
                provided_step=step,
            )
            return False

        # Verify step (simplified - in production, each step type has its own verification)
        # For now, we just check if verification is not empty
        if not verification or len(verification) < 4:
            logger.warning(
                "recovery_verification_failed",
                recovery_id=recovery_id,
                reason="invalid_verification_data",
            )
            return False

        # Mark step as completed
        current_step_type = recovery.remaining_steps[0]
        recovery.completed_steps.append(current_step_type)
        recovery.remaining_steps.pop(0)
        recovery.current_step += 1

        # Check if all steps completed
        if recovery.current_step >= recovery.steps_required:
            recovery.is_completed = True
            logger.info(
                "account_recovery_completed",
                recovery_id=recovery_id,
                user_id=recovery.user_id,
            )
        else:
            logger.info(
                "recovery_step_verified",
                recovery_id=recovery_id,
                step=step,
                step_type=current_step_type.value,
                remaining_steps=len(recovery.remaining_steps),
            )

        return True

    def get_recovery_status(self, recovery_id: str) -> Optional[RecoveryResult]:
        """
        Kurtarma islemi durumunu dondurur.

        Args:
            recovery_id: Kurtarma islemi ID

        Returns:
            RecoveryResult veya None
        """
        return self._recovery_sessions.get(recovery_id)

    # ==================== LOGIN HISTORY ====================

    def record_login_attempt(
        self,
        user_id: int,
        ip: str,
        user_agent: str,
        success: bool,
        failure_reason: Optional[str] = None,
    ) -> LoginAttempt:
        """
        Giris denemesini kaydeder.

        Args:
            user_id: Kullanici ID
            ip: IP adresi
            user_agent: User-Agent bilgisi
            success: Basarili mi
            failure_reason: Basarisizlik nedeni (varsa)

        Returns:
            LoginAttempt: Kaydedilen deneme bilgisi
        """
        fingerprint = self._generate_device_fingerprint(user_agent)

        # Detect if this attempt is suspicious
        activity_result = self.detect_suspicious_activity(user_id, ip, user_agent)

        attempt = LoginAttempt(
            attempt_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            ip_address=ip,
            user_agent=user_agent,
            device_fingerprint=fingerprint,
            success=success,
            failure_reason=failure_reason,
            location=None,  # Placeholder for GeoIP
            is_suspicious=activity_result.is_suspicious,
        )

        # Add to history
        if user_id not in self._login_history:
            self._login_history[user_id] = []

        self._login_history[user_id].append(attempt)

        # Keep only last MAX_LOGIN_HISTORY entries (REQ-8.5)
        if len(self._login_history[user_id]) > self.MAX_LOGIN_HISTORY:
            self._login_history[user_id] = self._login_history[user_id][
                -self.MAX_LOGIN_HISTORY :
            ]

        # Track IP
        if success:
            if user_id not in self._known_ips:
                self._known_ips[user_id] = set()
            self._known_ips[user_id].add(ip)

        logger.info(
            "login_attempt_recorded",
            user_id=user_id,
            success=success,
            is_suspicious=attempt.is_suspicious,
            ip=ip,
        )

        return attempt

    def get_login_history(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[LoginAttempt]:
        """
        Kullanicinin giris gecmisini dondurur.

        Args:
            user_id: Kullanici ID
            limit: Maksimum kayit sayisi (varsayilan: 10)

        Returns:
            list[LoginAttempt]: Giris denemeleri listesi (en yeniden en eskiye)

        Note:
            REQ-8.5: Last 10 login attempts history
        """
        history = self._login_history.get(user_id, [])

        # Return most recent first
        sorted_history = sorted(history, key=lambda x: x.timestamp, reverse=True)

        return sorted_history[:limit]

    # ==================== ACCOUNT LOCK ====================

    def lock_account(
        self,
        user_id: int,
        reason: str,
        locked_by: str = "system",
        admin_notes: str = "",
    ) -> bool:
        """
        Hesabi kilitler.

        Args:
            user_id: Kullanici ID
            reason: Kilitleme nedeni
            locked_by: Kilitleyen (sistem veya admin ID)
            admin_notes: Admin notlari

        Returns:
            bool: Kilitleme basarili mi

        Note:
            REQ-8.6: Account lock with admin approval required to unlock
        """
        # Convert reason string to enum
        try:
            lock_reason = AccountLockReason(reason)
        except ValueError:
            lock_reason = AccountLockReason.ADMIN_ACTION

        lock_info = AccountLockInfo(
            user_id=user_id,
            locked_at=datetime.now(timezone.utc),
            reason=lock_reason,
            locked_by=locked_by,
            unlock_requires_admin=True,
            admin_notes=admin_notes,
        )

        self._locked_accounts[user_id] = lock_info

        # Invalidate all sessions
        self.on_password_change(user_id)  # Reuse session invalidation

        # Send alert
        self.send_security_alert(
            user_id=user_id,
            alert_type=AlertType.ACCOUNT_LOCKED.value,
            details={
                "reason": lock_reason.value,
                "locked_by": locked_by,
                "admin_notes": admin_notes,
            },
        )

        logger.warning(
            "account_locked",
            user_id=user_id,
            reason=lock_reason.value,
            locked_by=locked_by,
        )

        return True

    def unlock_account(self, user_id: int, admin_id: int) -> bool:
        """
        Hesap kilidini acar (admin onayi ile).

        Args:
            user_id: Kullanici ID
            admin_id: Kilidi acan admin ID

        Returns:
            bool: Kilit acma basarili mi

        Note:
            REQ-8.6: Admin approval required for unlock
        """
        if user_id not in self._locked_accounts:
            logger.warning(
                "account_unlock_failed",
                user_id=user_id,
                reason="account_not_locked",
            )
            return False

        lock_info = self._locked_accounts[user_id]

        # Remove lock
        del self._locked_accounts[user_id]

        # Send alert
        self.send_security_alert(
            user_id=user_id,
            alert_type=AlertType.ACCOUNT_UNLOCKED.value,
            details={
                "unlocked_by_admin_id": admin_id,
                "was_locked_reason": lock_info.reason.value,
                "was_locked_at": lock_info.locked_at.isoformat(),
            },
        )

        logger.info(
            "account_unlocked",
            user_id=user_id,
            unlocked_by_admin_id=admin_id,
            was_locked_reason=lock_info.reason.value,
        )

        return True

    def is_account_locked(self, user_id: int) -> bool:
        """
        Hesabin kilitli olup olmadigini kontrol eder.

        Args:
            user_id: Kullanici ID

        Returns:
            bool: Hesap kilitli mi
        """
        return user_id in self._locked_accounts

    def get_lock_info(self, user_id: int) -> Optional[AccountLockInfo]:
        """
        Hesap kilidi bilgisini dondurur.

        Args:
            user_id: Kullanici ID

        Returns:
            AccountLockInfo veya None
        """
        return self._locked_accounts.get(user_id)

    # ==================== SECURITY ALERTS ====================

    def send_security_alert(
        self,
        user_id: int,
        alert_type: str,
        details: dict[str, Any],
    ) -> None:
        """
        Guvenlik uyarisi gonderir.

        Bu metod email gonderimi icin placeholder olarak calisir.
        Production'da email servisi ile entegre edilmelidir.

        Args:
            user_id: Kullanici ID
            alert_type: Uyari tipi (AlertType enum degeri)
            details: Uyari detaylari

        Note:
            REQ-8.1: Email alert on suspicious activity
        """
        alert_data = {
            "user_id": user_id,
            "alert_type": alert_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details,
        }

        # Log the alert (in production, this would send an email)
        logger.info(
            "security_alert_sent",
            **alert_data,
        )

        # TODO: Integrate with email service
        # Example:
        # await email_service.send_security_alert(
        #     user_email=user.email,
        #     alert_type=alert_type,
        #     details=details
        # )

    # ==================== USER DEVICES ====================

    def get_user_devices(self, user_id: int) -> list[DeviceInfo]:
        """
        Kullanicinin kayitli cihazlarini listeler.

        Args:
            user_id: Kullanici ID

        Returns:
            list[DeviceInfo]: Cihaz listesi
        """
        return self._user_devices.get(user_id, [])

    def remove_device(self, user_id: int, device_id: str) -> bool:
        """
        Kullanicinin cihazini kaldirir.

        Args:
            user_id: Kullanici ID
            device_id: Cihaz ID

        Returns:
            bool: Kaldirma basarili mi
        """
        devices = self._user_devices.get(user_id, [])

        for i, device in enumerate(devices):
            if device.device_id == device_id:
                devices.pop(i)
                logger.info(
                    "device_removed",
                    user_id=user_id,
                    device_id=device_id,
                )
                return True

        return False

    # ==================== STATISTICS ====================

    def get_security_stats(self, user_id: int) -> dict[str, Any]:
        """
        Kullanici guvenlik istatistiklerini dondurur.

        Args:
            user_id: Kullanici ID

        Returns:
            dict: Guvenlik istatistikleri
        """
        devices = self._user_devices.get(user_id, [])
        history = self._login_history.get(user_id, [])

        verified_devices = sum(1 for d in devices if d.is_verified)
        failed_logins_24h = sum(
            1
            for h in history
            if not h.success
            and h.timestamp > datetime.now(timezone.utc) - timedelta(hours=24)
        )
        suspicious_attempts = sum(1 for h in history if h.is_suspicious)

        return {
            "total_devices": len(devices),
            "verified_devices": verified_devices,
            "unverified_devices": len(devices) - verified_devices,
            "total_login_attempts": len(history),
            "failed_logins_24h": failed_logins_24h,
            "suspicious_attempts": suspicious_attempts,
            "known_ips_count": len(self._known_ips.get(user_id, set())),
            "is_account_locked": self.is_account_locked(user_id),
            "active_sessions": len(self._active_sessions.get(user_id, set())),
        }


# ==================== GLOBAL SERVICE INSTANCE ====================


_security_service: Optional[AccountSecurityService] = None


def get_account_security_service() -> AccountSecurityService:
    """
    Global AccountSecurityService instance'ini dondurur.

    Returns:
        AccountSecurityService: Singleton instance

    Example:
        >>> service = get_account_security_service()
        >>> result = service.detect_suspicious_activity(user_id=123, ip="...", user_agent="...")
    """
    global _security_service
    if _security_service is None:
        _security_service = AccountSecurityService()
    return _security_service


# ==================== EXPORTS ====================


__all__ = [
    # Enums
    "SuspiciousActivityReason",
    "RecommendedAction",
    "RecoveryStep",
    "AccountLockReason",
    "AlertType",
    # Data classes
    "DeviceInfo",
    "LoginAttempt",
    "SuspiciousActivityResult",
    "RecoveryResult",
    "AccountLockInfo",
    # Service
    "AccountSecurityService",
    "get_account_security_service",
]
