"""
API Key Management System
TASK 48.6: Secure API key management and rotation

Manages API keys for external integrations with:
- Encrypted storage
- Automatic rotation
- Usage monitoring
- Audit trail
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import Session

from core.database import Base
from core.encryption_service import EncryptedString, get_encryption_service
from core.audit_logging import get_audit_logger, AuditEventType, AuditSeverity


class APIKeyScope(str, Enum):
    """API key scopes/permissions"""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    EXTERNAL_YOUTUBE = "external_youtube"
    EXTERNAL_OPENAI = "external_openai"
    EXTERNAL_ANTHROPIC = "external_anthropic"
    EXTERNAL_EBA = "external_eba"


class APIKeyStatus(str, Enum):
    """API key status"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATION_PENDING = "rotation_pending"


class APIKey(Base):
    """
    API Key database model

    Stores encrypted API keys with metadata for management.
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)

    # Key identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # The actual API key (encrypted)
    key_encrypted = Column(EncryptedString(500), nullable=False)

    # Key hash for validation (not encrypted, used for quick lookup)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)

    # Scope and permissions
    scope = Column(String(100), nullable=False, default=APIKeyScope.READ_ONLY.value)

    # Status
    status = Column(String(50), nullable=False, default=APIKeyStatus.ACTIVE.value)

    # Ownership
    owner_id = Column(String(50), nullable=True, index=True)
    service_name = Column(String(255), nullable=True)  # For external services

    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    last_rotated_at = Column(DateTime, nullable=True)

    # Auto-rotation
    auto_rotate = Column(Boolean, default=False)
    rotation_interval_days = Column(Integer, default=90)

    # Usage tracking
    usage_count = Column(Integer, default=0)
    rate_limit = Column(Integer, nullable=True)  # Requests per hour

    # Additional metadata
    metadata = Column(JSON, nullable=True)


class APIKeyManager:
    """
    API key management service

    Provides methods for creating, rotating, and managing API keys.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.encryption_service = get_encryption_service()
        self.audit_logger = get_audit_logger(db_session)

    def generate_api_key(self, prefix: str = "sk") -> str:
        """
        Generate a secure API key

        Args:
            prefix: Key prefix (e.g., 'sk' for secret key)

        Returns:
            Generated API key string
        """
        # Generate 32 bytes (256 bits) of random data
        random_bytes = secrets.token_bytes(32)

        # Convert to base64-like string
        key_part = secrets.token_urlsafe(32)

        # Format: prefix_randomstring
        return f"{prefix}_{key_part}"

    def create_api_key(
        self,
        name: str,
        scope: APIKeyScope,
        owner_id: Optional[str] = None,
        service_name: Optional[str] = None,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        auto_rotate: bool = False,
        rotation_interval_days: int = 90,
        rate_limit: Optional[int] = None,
    ) -> tuple[APIKey, str]:
        """
        Create a new API key

        Args:
            name: Key name
            scope: Key scope/permissions
            owner_id: Owner user ID (for internal keys)
            service_name: Service name (for external keys)
            description: Key description
            expires_in_days: Days until expiration (None = never)
            auto_rotate: Enable automatic rotation
            rotation_interval_days: Days between rotations
            rate_limit: Requests per hour limit

        Returns:
            Tuple of (APIKey model, plaintext key)
            WARNING: Plaintext key is returned only once!
        """
        # Generate key
        plaintext_key = self.generate_api_key()

        # Hash for quick lookup
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create API key record
        api_key = APIKey(
            name=name,
            description=description,
            key_encrypted=plaintext_key,  # Will be encrypted by EncryptedString
            key_hash=key_hash,
            scope=scope.value,
            status=APIKeyStatus.ACTIVE.value,
            owner_id=owner_id,
            service_name=service_name,
            expires_at=expires_at,
            auto_rotate=auto_rotate,
            rotation_interval_days=rotation_interval_days,
            rate_limit=rate_limit,
        )

        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        # Audit log
        self.audit_logger.log_admin_action(
            admin_id=owner_id or "system",
            action="create_api_key",
            description=f"Created API key: {name} ({scope.value})",
            metadata={"api_key_id": api_key.id, "scope": scope.value},
        )

        return api_key, plaintext_key

    def validate_api_key(self, plaintext_key: str) -> Optional[APIKey]:
        """
        Validate an API key

        Args:
            plaintext_key: Plaintext API key

        Returns:
            APIKey if valid, None otherwise
        """
        # Hash the key
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()

        # Find by hash
        api_key = self.db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

        if not api_key:
            return None

        # Check status
        if api_key.status != APIKeyStatus.ACTIVE.value:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            api_key.status = APIKeyStatus.EXPIRED.value
            self.db.commit()
            return None

        # Update last used
        api_key.last_used_at = datetime.utcnow()
        api_key.usage_count += 1
        self.db.commit()

        # Check if rotation needed
        if api_key.auto_rotate:
            self._check_rotation_needed(api_key)

        return api_key

    def rotate_api_key(self, api_key_id: int, admin_id: str) -> tuple[APIKey, str]:
        """
        Rotate an API key (generate new key, revoke old)

        Args:
            api_key_id: ID of key to rotate
            admin_id: ID of admin performing rotation

        Returns:
            Tuple of (new APIKey, new plaintext key)
        """
        old_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()

        if not old_key:
            raise ValueError("API key not found")

        # Create new key with same settings
        new_key, plaintext_key = self.create_api_key(
            name=old_key.name,
            scope=APIKeyScope(old_key.scope),
            owner_id=old_key.owner_id,
            service_name=old_key.service_name,
            description=old_key.description,
            expires_in_days=(old_key.expires_at - datetime.utcnow()).days
            if old_key.expires_at
            else None,
            auto_rotate=old_key.auto_rotate,
            rotation_interval_days=old_key.rotation_interval_days,
            rate_limit=old_key.rate_limit,
        )

        # Revoke old key
        old_key.status = APIKeyStatus.REVOKED.value
        self.db.commit()

        # Audit log
        self.audit_logger.log_event(
            event_type=AuditEventType.ADMIN_ENCRYPTION_KEY_ROTATION,
            user_id=admin_id,
            resource_type="api_key",
            resource_id=str(api_key_id),
            action="rotate",
            description=f"Rotated API key: {old_key.name}",
            metadata={"old_key_id": old_key.id, "new_key_id": new_key.id},
            severity=AuditSeverity.WARNING,
        )

        return new_key, plaintext_key

    def revoke_api_key(
        self, api_key_id: int, admin_id: str, reason: Optional[str] = None
    ):
        """
        Revoke an API key

        Args:
            api_key_id: ID of key to revoke
            admin_id: ID of admin performing revocation
            reason: Reason for revocation
        """
        api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()

        if not api_key:
            raise ValueError("API key not found")

        api_key.status = APIKeyStatus.REVOKED.value
        self.db.commit()

        # Audit log
        self.audit_logger.log_admin_action(
            admin_id=admin_id,
            action="revoke_api_key",
            target_user_id=str(api_key_id),
            description=f"Revoked API key: {api_key.name}"
            + (f" - Reason: {reason}" if reason else ""),
            metadata={"api_key_id": api_key.id, "reason": reason},
        )

    def list_api_keys(
        self,
        owner_id: Optional[str] = None,
        service_name: Optional[str] = None,
        status: Optional[APIKeyStatus] = None,
    ) -> List[APIKey]:
        """
        List API keys with filters

        Args:
            owner_id: Filter by owner
            service_name: Filter by service
            status: Filter by status

        Returns:
            List of APIKey objects
        """
        query = self.db.query(APIKey)

        if owner_id:
            query = query.filter(APIKey.owner_id == owner_id)
        if service_name:
            query = query.filter(APIKey.service_name == service_name)
        if status:
            query = query.filter(APIKey.status == status.value)

        return query.order_by(APIKey.created_at.desc()).all()

    def get_key_usage_stats(self, api_key_id: int) -> dict:
        """Get usage statistics for an API key"""
        api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()

        if not api_key:
            raise ValueError("API key not found")

        days_active = (datetime.utcnow() - api_key.created_at).days
        avg_daily_usage = api_key.usage_count / max(days_active, 1)

        return {
            "total_usage": api_key.usage_count,
            "days_active": days_active,
            "avg_daily_usage": round(avg_daily_usage, 2),
            "last_used_at": api_key.last_used_at.isoformat()
            if api_key.last_used_at
            else None,
            "rate_limit": api_key.rate_limit,
            "status": api_key.status,
        }

    def _check_rotation_needed(self, api_key: APIKey):
        """Check if automatic rotation is needed"""
        if not api_key.auto_rotate:
            return

        last_rotation = api_key.last_rotated_at or api_key.created_at
        days_since_rotation = (datetime.utcnow() - last_rotation).days

        if days_since_rotation >= api_key.rotation_interval_days:
            # Mark for rotation
            api_key.status = APIKeyStatus.ROTATION_PENDING.value
            self.db.commit()

            # Notify admin (would typically send email/notification)
            self.audit_logger.log_security_event(
                event_type=AuditEventType.SECURITY_SUSPICIOUS_ACTIVITY,
                description=f"API key rotation needed: {api_key.name}",
                metadata={
                    "api_key_id": api_key.id,
                    "days_since_rotation": days_since_rotation,
                },
                severity=AuditSeverity.WARNING,
            )


def get_api_key_manager(db: Session) -> APIKeyManager:
    """Factory function to get API key manager"""
    return APIKeyManager(db)
