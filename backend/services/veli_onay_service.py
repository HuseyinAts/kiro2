"""KVKK Faz 2: Veli onay (parental consent) iş mantığı."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.veli_consent import (
    CONSENT_VERSION,
    VeliConsent,
    default_expiry,
    generate_token,
    hash_token,
)

logger = logging.getLogger(__name__)

CONSENT_TEXT = (
    "Velisi olduğunuz öğrencinin KIRO2 eğitim platformunu kullanabilmesi için "
    "kişisel verilerinin (kimlik, iletişim, eğitim/performans verileri) eğitim "
    "hizmeti amacıyla işlenmesine açık rıza veriyorsunuz. Bu onayı dilediğiniz "
    "zaman geri çekebilirsiniz (KVKK Madde 11)."
)


@dataclass
class VeliOnayResult:
    success: bool
    status: str | None = None
    error_code: str | None = None
    message: str | None = None


def _as_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


class VeliOnayService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def request_consent(self, child_user_id: str, veli_email: str) -> str:
        """Pending kayıt + token üret. Eski pending expire. Plaintext token döner."""
        existing = (
            (
                await self.db.execute(
                    select(VeliConsent).where(
                        VeliConsent.child_user_id == child_user_id,
                        VeliConsent.status == "pending",
                    )
                )
            )
            .scalars()
            .all()
        )
        for c in existing:
            c.status = "expired"
            c.token_hash = None

        token = generate_token()
        consent = VeliConsent(
            child_user_id=child_user_id,
            veli_email=veli_email,
            status="pending",
            token_hash=hash_token(token),
            token_expires_at=default_expiry(),
            consent_text=CONSENT_TEXT,
            consent_version=CONSENT_VERSION,
        )
        self.db.add(consent)
        await self.db.commit()
        logger.info("veli_onay_requested child=%s", child_user_id)
        return token

    async def verify_and_grant(
        self, token: str, ip: str | None = None, ua: str | None = None
    ) -> VeliOnayResult:
        consent = (
            await self.db.execute(
                select(VeliConsent).where(VeliConsent.token_hash == hash_token(token))
            )
        ).scalar_one_or_none()

        if consent is None:
            return VeliOnayResult(
                False,
                error_code="INVALID_TOKEN",
                message="Geçersiz veya süresi dolmuş onay bağlantısı",
            )
        if consent.status == "granted":
            return VeliOnayResult(True, status="granted", message="Onay zaten alınmış")
        if consent.status in ("withdrawn", "expired"):
            return VeliOnayResult(
                False,
                error_code="TOKEN_INVALID",
                message="Bu bağlantı artık geçerli değil",
            )
        if consent.token_expires_at and datetime.now(UTC) > _as_aware(
            consent.token_expires_at
        ):
            consent.status = "expired"
            consent.token_hash = None
            await self.db.commit()
            return VeliOnayResult(
                False,
                error_code="TOKEN_EXPIRED",
                message="Bağlantı süresi dolmuş. Öğrenci yeniden gönderebilir.",
            )

        consent.status = "granted"
        consent.granted_at = datetime.now(UTC)
        consent.ip_address = ip
        consent.user_agent = ua
        await self.db.execute(
            text(
                "UPDATE student_profiles SET veli_onay = TRUE, updated_at = NOW() "
                "WHERE user_id = :uid"
            ),
            {"uid": consent.child_user_id},
        )
        await self.db.commit()
        logger.info("veli_onay_granted child=%s", consent.child_user_id)
        return VeliOnayResult(True, status="granted", message="Veli onayı alındı")

    async def withdraw(self, token: str) -> bool:
        consent = (
            await self.db.execute(
                select(VeliConsent).where(VeliConsent.token_hash == hash_token(token))
            )
        ).scalar_one_or_none()
        if consent is None or consent.status not in ("granted", "pending"):
            return False
        consent.status = "withdrawn"
        consent.withdrawn_at = datetime.now(UTC)
        consent.token_hash = None
        await self.db.execute(
            text(
                "UPDATE student_profiles SET veli_onay = FALSE, updated_at = NOW() "
                "WHERE user_id = :uid"
            ),
            {"uid": consent.child_user_id},
        )
        await self.db.commit()
        logger.info("veli_onay_withdrawn child=%s", consent.child_user_id)
        return True

    async def get_status(self, child_user_id: str) -> str:
        """En güncel kaydın durumu: pending/granted/withdrawn/expired veya 'none'."""
        consent = (
            (
                await self.db.execute(
                    select(VeliConsent)
                    .where(VeliConsent.child_user_id == child_user_id)
                    .order_by(VeliConsent.requested_at.desc())
                )
            )
            .scalars()
            .first()
        )
        return consent.status if consent else "none"

    async def resend(self, child_user_id: str, veli_email: str) -> str:
        """Eski pending'i invalidate edip yeni token üretir (request_consent reuse)."""
        return await self.request_consent(child_user_id, veli_email)
