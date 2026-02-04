"""
Comprehensive Audit Logging System (Task 48.5)
Tracks all critical operations for security and compliance (KVKK)

Features:
- Automatic request/response logging
- User action tracking
- Data change history (before/after)
- 90-day retention policy
- Security event monitoring
- KVKK compliance logging

Author: Claude
Date: 2025-10-27
"""
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import delete
from sqlalchemy.orm import Session

from core.structured_logger import get_logger

logger = get_logger("audit_logger")


class AuditAction(str, Enum):
    """Audit edilebilir aksiyonlar"""

    # Authentication
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT_ALL = "auth.logout_all"
    TOKEN_REFRESH = "auth.token_refresh"

    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_VIEW = "user.view"
    PASSWORD_CHANGE = "user.password_change"
    PASSWORD_RESET = "user.password_reset"

    # Student Data
    STUDENT_PROFILE_CREATE = "student.profile_create"
    STUDENT_PROFILE_UPDATE = "student.profile_update"
    STUDENT_DATA_EXPORT = "student.data_export"
    STUDENT_DATA_VIEW = "student.data_view"

    # Exam Operations
    EXAM_CREATE = "exam.create"
    EXAM_START = "exam.start"
    EXAM_SUBMIT = "exam.submit"
    EXAM_RESULT_VIEW = "exam.result_view"
    EXAM_DELETE = "exam.delete"

    # Content Operations
    CONTENT_CREATE = "content.create"
    CONTENT_UPDATE = "content.update"
    CONTENT_DELETE = "content.delete"
    CONTENT_VIEW = "content.view"

    # Security Events
    PERMISSION_DENIED = "security.permission_denied"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    DATA_BREACH_ATTEMPT = "security.data_breach_attempt"
    RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"

    # API Operations
    API_KEY_CREATE = "api.key_create"
    API_KEY_REVOKE = "api.key_revoke"
    API_REQUEST = "api.request"
    API_ERROR = "api.error"

    # System Events
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"

    # Data Privacy (KVKK)
    DATA_ACCESS_REQUEST = "privacy.data_access_request"
    DATA_DELETE_REQUEST = "privacy.data_delete_request"
    DATA_EXPORT_REQUEST = "privacy.data_export_request"
    CONSENT_GIVEN = "privacy.consent_given"
    CONSENT_REVOKED = "privacy.consent_revoked"


class AuditResourceType(str, Enum):
    """Resource türleri"""

    USER = "user"
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    EXAM = "exam"
    QUESTION = "question"
    CONTENT = "content"
    PROFILE = "profile"
    API_KEY = "api_key"
    SYSTEM = "system"
    DATA = "data"


class AuditLogger:
    """
    Comprehensive Audit Logger (Task 48.5)

    Usage:
        audit = AuditLogger(db)
        audit.log_action(
            action=AuditAction.USER_CREATE,
            user_id="user_123",
            resource_type=AuditResourceType.USER,
            resource_id="new_user_456",
            new_values={"email": "user@example.com"}
        )
    """

    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        action: AuditAction,
        resource_type: AuditResourceType,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Audit log kaydı oluştur

        Args:
            action: Gerçekleştirilen aksiyon
            resource_type: Etkilenen resource türü
            user_id: İşlemi yapan kullanıcı ID (None = system/anonymous)
            resource_id: Etkilenen resource ID
            old_values: Değişiklik öncesi değerler (sensitive data filtered)
            new_values: Değişiklik sonrası değerler (sensitive data filtered)
            ip_address: İstek IP adresi
            user_agent: İstek user agent
            extra_data: Ek meta veriler
        """
        try:
            from models.database import AuditLog

            # Sensitive data filtering
            filtered_old = (
                self._filter_sensitive_data(old_values) if old_values else None
            )
            filtered_new = (
                self._filter_sensitive_data(new_values) if new_values else None
            )

            # Extra data enrichment
            enriched_extra = extra_data or {}
            enriched_extra["timestamp"] = datetime.utcnow().isoformat()
            enriched_extra["action_type"] = action.value

            # Create audit log entry
            audit_entry = AuditLog(
                user_id=user_id,
                action=action.value,
                resource_type=resource_type.value,
                resource_id=resource_id,
                old_values=filtered_old,
                new_values=filtered_new,
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else None,
            )

            self.db.add(audit_entry)
            self.db.commit()

            # Structured logging for monitoring
            logger.info(
                f"[AUDIT] {action.value}",
                extra_data={
                    "user_id": user_id,
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "ip_address": ip_address,
                    "action": action.value,
                },
            )

        except Exception as e:
            logger.error(
                f"[AUDIT ERROR] Failed to log action {action.value}: {e}",
                extra_data={"error": str(e), "action": action.value},
            )
            # Don't fail the main operation if audit logging fails
            self.db.rollback()

    def log_security_event(
        self,
        event_type: AuditAction,
        description: str,
        severity: str = "medium",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Güvenlik olayı kaydet (high priority)

        Args:
            event_type: Güvenlik olay türü
            description: Olay açıklaması
            severity: Önem seviyesi (low, medium, high, critical)
            user_id: İlgili kullanıcı ID
            ip_address: İstek IP adresi
            user_agent: İstek user agent
        """
        self.log_action(
            action=event_type,
            resource_type=AuditResourceType.SYSTEM,
            user_id=user_id,
            new_values={
                "description": description,
                "severity": severity,
                "security_event": True,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Critical events: Send alert
        if severity in ["high", "critical"]:
            logger.warning(
                f"[SECURITY ALERT] {event_type.value}: {description}",
                extra_data={
                    "severity": severity,
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "event_type": event_type.value,
                },
            )

    def log_data_access(
        self,
        user_id: str,
        resource_type: AuditResourceType,
        resource_id: str,
        access_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """
        Veri erişim kaydet (KVKK compliance)

        Args:
            user_id: Erişen kullanıcı ID
            resource_type: Erişilen veri türü
            resource_id: Erişilen veri ID
            access_reason: Erişim nedeni
            ip_address: İstek IP adresi
        """
        self.log_action(
            action=AuditAction.STUDENT_DATA_VIEW,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            new_values={"access_reason": access_reason} if access_reason else None,
            ip_address=ip_address,
        )

    def log_data_modification(
        self,
        user_id: str,
        resource_type: AuditResourceType,
        resource_id: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        ip_address: Optional[str] = None,
    ):
        """
        Veri değişikliği kaydet (before/after tracking)

        Args:
            user_id: Değiştiren kullanıcı ID
            resource_type: Değiştirilen veri türü
            resource_id: Değiştirilen veri ID
            old_data: Eski değerler
            new_data: Yeni değerler
            ip_address: İstek IP adresi
        """
        # Calculate diff
        changes = self._calculate_diff(old_data, new_data)

        self.log_action(
            action=AuditAction.USER_UPDATE,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            old_values=old_data,
            new_values=new_data,
            ip_address=ip_address,
            extra_data={"changes": changes},
        )

    def cleanup_old_logs(self, retention_days: int = 90):
        """
        90 günden eski audit log'ları sil (Task 48.5 requirement)

        Args:
            retention_days: Tutulacak gün sayısı (default: 90)
        """
        try:
            from models.database import AuditLog

            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            result = self.db.execute(
                delete(AuditLog).where(AuditLog.created_at < cutoff_date)
            )

            deleted_count = result.rowcount
            self.db.commit()

            logger.info(
                f"[AUDIT CLEANUP] Deleted {deleted_count} audit logs older than {retention_days} days",
                extra_data={
                    "deleted_count": deleted_count,
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat(),
                },
            )

            return deleted_count

        except Exception as e:
            logger.error(
                f"[AUDIT CLEANUP ERROR] Failed to cleanup old logs: {e}",
                extra_data={"error": str(e)},
            )
            self.db.rollback()
            return 0

    def get_user_audit_trail(self, user_id: str, limit: int = 100) -> list:
        """
        Kullanıcının audit log geçmişini getir (KVKK data access request)

        Args:
            user_id: Kullanıcı ID
            limit: Maksimum kayıt sayısı

        Returns:
            List of audit log entries
        """
        try:
            from models.database import AuditLog

            logs = (
                self.db.query(AuditLog)
                .filter(AuditLog.user_id == user_id)
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ]

        except Exception as e:
            logger.error(
                f"[AUDIT ERROR] Failed to get user audit trail: {e}",
                extra_data={"user_id": user_id, "error": str(e)},
            )
            return []

    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sensitive data'yı audit log'dan filtrele

        Args:
            data: Filtrelenecek veri

        Returns:
            Filtered data dictionary
        """
        if not data:
            return data

        sensitive_fields = [
            "password",
            "password_hash",
            "sifre",
            "credit_card",
            "ssn",
            "tc_no",
            "api_key",
            "secret",
            "token",
            "private_key",
        ]

        filtered = {}
        for key, value in data.items():
            # Check if field is sensitive
            is_sensitive = any(
                sensitive_field in key.lower() for sensitive_field in sensitive_fields
            )

            if is_sensitive:
                filtered[key] = "[REDACTED]"
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
            else:
                filtered[key] = value

        return filtered

    def _calculate_diff(
        self, old_data: Dict[str, Any], new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        İki veri seti arasındaki farkı hesapla

        Args:
            old_data: Eski veri
            new_data: Yeni veri

        Returns:
            Dictionary of changes
        """
        changes = {}

        # Find added/modified fields
        for key in new_data:
            if key not in old_data:
                changes[key] = {"type": "added", "new": new_data[key]}
            elif old_data[key] != new_data[key]:
                changes[key] = {
                    "type": "modified",
                    "old": old_data[key],
                    "new": new_data[key],
                }

        # Find removed fields
        for key in old_data:
            if key not in new_data:
                changes[key] = {"type": "removed", "old": old_data[key]}

        return changes


def get_audit_logger(db: Session) -> AuditLogger:
    """
    Audit logger instance'ını döndür

    Args:
        db: Database session

    Returns:
        AuditLogger instance
    """
    return AuditLogger(db)
