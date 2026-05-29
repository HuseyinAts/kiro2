"""KVKK Faz 2: Veli (parental) onay kaydı.

Reşit olmayan öğrenci için veli açık rızası. Token plaintext sadece email
linkinde bulunur; DB'de yalnızca SHA-256 hash saklanır.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text

from .base import Base

CONSENT_TOKEN_TTL_DAYS = 7
CONSENT_VERSION = "kvkk-veli-1.0"


def generate_token() -> str:
    """Kriptografik güvenli, tek-kullanımlık token (passwordless deseni)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Token'ın SHA-256 hex hash'i — DB'de bu saklanır, plaintext değil."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def default_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=CONSENT_TOKEN_TTL_DAYS)


class VeliConsent(Base):
    """Veli onay kaydı (KVKK açık rıza)."""

    __tablename__ = "veli_consent"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    child_user_id = Column(String, index=True, nullable=False)
    veli_email = Column(String(255), nullable=False)
    # pending / granted / withdrawn / expired
    status = Column(String(20), nullable=False, default="pending")
    # sha256(token); granted'da KORUNUR (idempotency + withdraw-by-token), withdrawn/expired'da NULL
    token_hash = Column(String(64), index=True, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    requested_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    granted_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    consent_text = Column(Text, nullable=False, default="")
    consent_version = Column(String(20), nullable=False, default=CONSENT_VERSION)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
