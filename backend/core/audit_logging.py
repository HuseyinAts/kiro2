"""
Comprehensive Audit Logging System
TASK 48.5: Comprehensive audit logging

Logs all security-relevant events for compliance and forensics:
- Authentication events (login, logout, failures)
- Data access and modifications (CRUD)
- Admin actions
- Permission changes
- Security events
"""
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON

from core.database import Base

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Audit event types"""

    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # Authorization
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGED = "role_changed"

    # Data Access
    DATA_READ = "data_read"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # Admin Actions
    ADMIN_USER_CREATE = "admin_user_create"
    ADMIN_USER_UPDATE = "admin_user_update"
    ADMIN_USER_DELETE = "admin_user_delete"
    ADMIN_SYSTEM_CONFIG = "admin_system_config"
    ADMIN_ENCRYPTION_KEY_ROTATION = "admin_encryption_key_rotation"

    # Security Events
    SECURITY_TOKEN_REVOKED = "security_token_revoked"
    SECURITY_IP_BLOCKED = "security_ip_blocked"
    SECURITY_RATE_LIMIT_EXCEEDED = "security_rate_limit_exceeded"
    SECURITY_SUSPICIOUS_ACTIVITY = "security_suspicious_activity"
    SECURITY_SQL_INJECTION_ATTEMPT = "security_sql_injection_attempt"
    SECURITY_XSS_ATTEMPT = "security_xss_attempt"

    # Exam Events
    EXAM_START = "exam_start"
    EXAM_SUBMIT = "exam_submit"
    EXAM_AUTO_SAVE = "exam_auto_save"

    # KVKK/Privacy
    KVKK_CONSENT_GIVEN = "kvkk_consent_given"
    KVKK_CONSENT_WITHDRAWN = "kvkk_consent_withdrawn"
    KVKK_DATA_EXPORT_REQUEST = "kvkk_data_export_request"
    KVKK_DATA_DELETION_REQUEST = "kvkk_data_deletion_request"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base):
    """
    Audit log database model

    Stores all audit events for compliance and forensics.
    Retention: 90 days minimum (configurable)
    """

    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default=AuditSeverity.INFO.value)

    # User information
    user_id = Column(String(50), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)

    # Request information
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)

    # Resource information
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)

    # Event details
    action = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Before/After state (for data modifications)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)

    # Additional metadata
    meta_data = Column(JSON, nullable=True)

    # Result
    success = Column(String(10), nullable=False, default="true")
    error_message = Column(Text, nullable=True)


class AuditLogger:
    """
    Audit logging service

    Provides methods to log various types of audit events.
    """

    def __init__(self, db_session=None):
        """Initialize audit logger"""
        self.db_session = db_session
        self.logger = logging.getLogger("audit")

        # Configure audit logger with file handler
        if not self.logger.handlers:
            handler = logging.FileHandler("logs/audit.log")
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        description: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        request_id: Optional[str] = None,
    ):
        """
        Log an audit event

        Args:
            event_type: Type of event
            user_id: User ID performing the action
            user_email: User email
            user_role: User role
            ip_address: IP address
            user_agent: User agent string
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            action: Action performed
            description: Human-readable description
            before_state: State before modification
            after_state: State after modification
            metadata: Additional metadata
            success: Whether action succeeded
            error_message: Error message if failed
            severity: Event severity
            request_id: Request ID for correlation
        """
        try:
            # Create audit log entry
            audit_log = AuditLog(
                event_type=event_type.value,
                severity=severity.value,
                user_id=user_id,
                user_email=user_email,
                user_role=user_role,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                description=description,
                before_state=before_state,
                after_state=after_state,
                metadata=metadata,
                success="true" if success else "false",
                error_message=error_message,
            )

            # Save to database
            if self.db_session:
                self.db_session.add(audit_log)
                self.db_session.commit()

            # Log to file
            log_message = self._format_log_message(
                event_type, user_id, resource_type, resource_id, action, success
            )

            if severity == AuditSeverity.CRITICAL:
                self.logger.critical(log_message)
            elif severity == AuditSeverity.ERROR:
                self.logger.error(log_message)
            elif severity == AuditSeverity.WARNING:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)

        except Exception as e:
            # Never fail the main operation due to audit logging
            logger.error(f"Audit logging failed: {e}")

    def _format_log_message(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        resource_type: Optional[str],
        resource_id: Optional[str],
        action: Optional[str],
        success: bool,
    ) -> str:
        """Format audit log message"""
        status = "SUCCESS" if success else "FAILURE"
        parts = [f"[{event_type.value.upper()}]", f"[{status}]"]

        if user_id:
            parts.append(f"User: {user_id}")
        if resource_type and resource_id:
            parts.append(f"Resource: {resource_type}/{resource_id}")
        if action:
            parts.append(f"Action: {action}")

        return " | ".join(parts)

    # Convenience methods for common events

    def log_login_success(
        self, user_id: str, user_email: str, ip_address: str, user_agent: str
    ):
        """Log successful login"""
        self.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"User {user_email} logged in successfully",
            severity=AuditSeverity.INFO,
        )

    def log_login_failure(self, email: str, ip_address: str, reason: str):
        """Log failed login attempt"""
        self.log_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            user_email=email,
            ip_address=ip_address,
            description=f"Login failed for {email}: {reason}",
            success=False,
            error_message=reason,
            severity=AuditSeverity.WARNING,
        )

    def log_logout(self, user_id: str, user_email: str):
        """Log user logout"""
        self.log_event(
            event_type=AuditEventType.LOGOUT,
            user_id=user_id,
            user_email=user_email,
            description=f"User {user_email} logged out",
            severity=AuditSeverity.INFO,
        )

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: Optional[str] = None,
    ):
        """Log data access"""
        self.log_event(
            event_type=AuditEventType.DATA_READ,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            description=f"User {user_id} accessed {resource_type}/{resource_id}",
            severity=AuditSeverity.INFO,
        )

    def log_data_modification(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None,
        ip_address: Optional[str] = None,
    ):
        """Log data modification"""
        event_type = {
            "create": AuditEventType.DATA_CREATE,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
        }.get(action.lower(), AuditEventType.DATA_UPDATE)

        self.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            description=f"User {user_id} {action}d {resource_type}/{resource_id}",
            severity=AuditSeverity.INFO,
        )

    def log_admin_action(
        self,
        admin_id: str,
        action: str,
        target_user_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Log admin action"""
        self.log_event(
            event_type=AuditEventType.ADMIN_SYSTEM_CONFIG,
            user_id=admin_id,
            action=action,
            resource_id=target_user_id,
            description=description or f"Admin {admin_id} performed {action}",
            metadata=metadata,
            severity=AuditSeverity.WARNING,
        )

    def log_security_event(
        self,
        event_type: AuditEventType,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict] = None,
        severity: AuditSeverity = AuditSeverity.WARNING,
    ):
        """Log security event"""
        self.log_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            description=description,
            metadata=metadata,
            severity=severity,
        )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(db_session=None) -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(db_session)
    return _audit_logger


# Decorator for automatic audit logging
def audit_log(
    event_type: AuditEventType,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
):
    """
    Decorator to automatically log function calls

    Usage:
        @audit_log(AuditEventType.DATA_CREATE, resource_type="user", action="create")
        def create_user(user_data: dict, current_user: User):
            # ... function implementation
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            audit = get_audit_logger()

            # Extract user from kwargs if available
            current_user = kwargs.get("current_user")
            user_id = getattr(current_user, "id", None) if current_user else None

            try:
                result = func(*args, **kwargs)

                audit.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    action=action or func.__name__,
                    description=f"Function {func.__name__} executed successfully",
                    success=True,
                )

                return result

            except Exception as e:
                audit.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    action=action or func.__name__,
                    description=f"Function {func.__name__} failed",
                    success=False,
                    error_message=str(e),
                    severity=AuditSeverity.ERROR,
                )
                raise

        return wrapper

    return decorator
