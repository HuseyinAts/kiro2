"""
KVKK Consent Management API
PHASE 2 Sprint 5: KVKK Compliance

Endpoints for managing user consent (KVKK Article 7)
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from core.database import get_async_session
from core.jwt_auth import TokenPayload, get_current_user
from core.structured_logger import get_logger
from models.kvkk_models import (
    ConsentStatus,
    DataProcessingPurpose,
    KVKKAuditLog,
    KVKKConsent,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/kvkk/consent", tags=["KVKK Consent"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ConsentGiveRequest(BaseModel):
    """Request to give consent"""

    purpose: DataProcessingPurpose
    consent_text: str
    privacy_policy_version: str


class ConsentWithdrawRequest(BaseModel):
    """Request to withdraw consent"""

    purpose: DataProcessingPurpose
    reason: str | None = None


class ConsentResponse(BaseModel):
    """Consent record response"""

    id: str
    user_id: str
    purpose: DataProcessingPurpose
    status: ConsentStatus
    consent_text: str
    privacy_policy_version: str
    given_at: datetime
    withdrawn_at: datetime | None = None
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BulkConsentRequest(BaseModel):
    """Request to give multiple consents at once"""

    consents: list[ConsentGiveRequest]


# ============================================================================
# Helper Functions
# ============================================================================


async def log_consent_action(
    db: AsyncSession,
    user_id: str,
    action: str,
    purpose: DataProcessingPurpose,
    request: Request,
    details: dict | None = None,
):
    """Log consent action to audit log"""
    audit_log = KVKKAuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        accessed_by=user_id,
        action=action,
        resource_type="consent",
        purpose=purpose,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_method=request.method,
        request_path=str(request.url),
        details=details,
    )
    db.add(audit_log)


# ============================================================================
# Consent Endpoints
# ============================================================================


@router.post("/give", response_model=ConsentResponse)
async def give_consent(
    consent_req: ConsentGiveRequest,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Give consent for data processing

    User explicitly consents to specific data processing purpose.
    Required by KVKK Article 7 (Explicit Consent).
    """
    try:
        # Check if consent already exists and is active
        stmt = select(KVKKConsent).where(
            KVKKConsent.user_id == current_user.sub,
            KVKKConsent.purpose == consent_req.purpose,
            KVKKConsent.status == ConsentStatus.GIVEN,
        )
        result = await db.execute(stmt)
        existing_consent = result.scalar_one_or_none()

        if existing_consent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Active consent already exists for purpose: {consent_req.purpose}",
            )

        # Create new consent
        new_consent = KVKKConsent(
            id=str(uuid.uuid4()),
            user_id=current_user.sub,
            purpose=consent_req.purpose,
            status=ConsentStatus.GIVEN,
            consent_text=consent_req.consent_text,
            privacy_policy_version=consent_req.privacy_policy_version,
            given_at=datetime.now(UTC),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        db.add(new_consent)

        # Log action
        await log_consent_action(
            db=db,
            user_id=current_user.sub,
            action="consent_given",
            purpose=consent_req.purpose,
            request=request,
            details={
                "privacy_policy_version": consent_req.privacy_policy_version,
                "consent_id": new_consent.id,
            },
        )

        await db.commit()
        await db.refresh(new_consent)
        # GF16: consent_text modelde deferred (models/kvkk_models.py). Normal
        # refresh deferred kolonu yuklemez; response_model=ConsentResponse
        # serializasyonu erisince AsyncSession'da MissingGreenlet -> 500
        # oluyordu. Kolonu acikca yukle.
        await db.refresh(new_consent, attribute_names=["consent_text"])

        logger.info(
            "consent_given",
            user_id=current_user.sub,
            purpose=consent_req.purpose.value,
            consent_id=new_consent.id,
        )

        return new_consent

    except HTTPException:
        raise
    except Exception as e:
        logger.error("consent_give_error", user_id=current_user.sub, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to give consent",
        )


@router.post("/give-bulk")
async def give_bulk_consent(
    bulk_req: BulkConsentRequest,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Give multiple consents at once

    Useful during registration/onboarding when user accepts
    multiple data processing purposes.
    """
    try:
        created_consents = []

        for consent_req in bulk_req.consents:
            # Check if already exists
            stmt = select(KVKKConsent).where(
                KVKKConsent.user_id == current_user.sub,
                KVKKConsent.purpose == consent_req.purpose,
                KVKKConsent.status == ConsentStatus.GIVEN,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                continue  # Skip if already exists

            # Create consent
            new_consent = KVKKConsent(
                id=str(uuid.uuid4()),
                user_id=current_user.sub,
                purpose=consent_req.purpose,
                status=ConsentStatus.GIVEN,
                consent_text=consent_req.consent_text,
                privacy_policy_version=consent_req.privacy_policy_version,
                given_at=datetime.now(UTC),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

            db.add(new_consent)
            created_consents.append(new_consent)

            # Log action
            await log_consent_action(
                db=db,
                user_id=current_user.sub,
                action="consent_given",
                purpose=consent_req.purpose,
                request=request,
                details={"consent_id": new_consent.id},
            )

        await db.commit()

        logger.info(
            "bulk_consent_given", user_id=current_user.sub, count=len(created_consents)
        )

        return {
            "success": True,
            "consents_created": len(created_consents),
            "message": f"{len(created_consents)} consent(s) recorded",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("bulk_consent_error", user_id=current_user.sub, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to give bulk consent",
        )


@router.post("/withdraw")
async def withdraw_consent(
    withdraw_req: ConsentWithdrawRequest,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Withdraw consent for data processing

    User can withdraw consent at any time (KVKK Article 11).
    System must stop processing data for that purpose.
    """
    try:
        # Find active consent
        stmt = select(KVKKConsent).where(
            KVKKConsent.user_id == current_user.sub,
            KVKKConsent.purpose == withdraw_req.purpose,
            KVKKConsent.status == ConsentStatus.GIVEN,
        )
        result = await db.execute(stmt)
        consent = result.scalar_one_or_none()

        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active consent found for purpose: {withdraw_req.purpose}",
            )

        # Withdraw consent
        stmt = (
            update(KVKKConsent)
            .where(KVKKConsent.id == consent.id)
            .values(status=ConsentStatus.WITHDRAWN, withdrawn_at=datetime.now(UTC))
        )
        await db.execute(stmt)

        # Log action
        await log_consent_action(
            db=db,
            user_id=current_user.sub,
            action="consent_withdrawn",
            purpose=withdraw_req.purpose,
            request=request,
            details={"consent_id": consent.id, "reason": withdraw_req.reason},
        )

        await db.commit()

        logger.info(
            "consent_withdrawn",
            user_id=current_user.sub,
            purpose=withdraw_req.purpose.value,
            consent_id=consent.id,
        )

        return {
            "success": True,
            "message": "Consent withdrawn successfully",
            "purpose": withdraw_req.purpose,
            "withdrawn_at": datetime.now(UTC),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("consent_withdraw_error", user_id=current_user.sub, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to withdraw consent",
        )


@router.get("/my-consents", response_model=list[ConsentResponse])
async def get_my_consents(
    status_filter: ConsentStatus | None = None,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get all consents for current user

    Returns user's consent history with optional status filter.
    """
    try:
        # GF16 kardes yolu: consent_text deferred — response_model listesi
        # serializasyonda kolona erisir; undefer olmadan kayit VARKEN 500.
        stmt = (
            select(KVKKConsent)
            .options(undefer(KVKKConsent.consent_text))
            .where(KVKKConsent.user_id == current_user.sub)
        )

        if status_filter:
            stmt = stmt.where(KVKKConsent.status == status_filter)

        stmt = stmt.order_by(KVKKConsent.given_at.desc())

        result = await db.execute(stmt)
        consents = result.scalars().all()

        return consents

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_consents_error", user_id=current_user.sub, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consents",
        )


@router.get("/check/{purpose}")
async def check_consent(
    purpose: DataProcessingPurpose,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Check if user has given consent for specific purpose

    Used by system to verify consent before processing data.
    """
    try:
        stmt = select(KVKKConsent).where(
            KVKKConsent.user_id == current_user.sub,
            KVKKConsent.purpose == purpose,
            KVKKConsent.status == ConsentStatus.GIVEN,
        )
        result = await db.execute(stmt)
        consent = result.scalar_one_or_none()

        has_consent = consent is not None

        return {
            "purpose": purpose,
            "has_consent": has_consent,
            "consent_given_at": consent.given_at if consent else None,
            "privacy_policy_version": consent.privacy_policy_version
            if consent
            else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("check_consent_error", user_id=current_user.sub, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check consent",
        )


@router.get("/required-consents")
async def get_required_consents():
    """
    Get list of required consents for platform usage

    Returns all data processing purposes that require user consent.
    """
    required_consents = [
        {
            "purpose": DataProcessingPurpose.SERVICE_PROVISION,
            "title": "Hizmet Sunumu",
            "description": "Platform hizmetlerini kullanabilmeniz için gerekli.",
            "required": True,
        },
        {
            "purpose": DataProcessingPurpose.ACCOUNT_MANAGEMENT,
            "title": "Hesap Yönetimi",
            "description": "Hesabınızı yönetmek ve güvenliğini sağlamak için gerekli.",
            "required": True,
        },
        {
            "purpose": DataProcessingPurpose.AUTHENTICATION,
            "title": "Kimlik Doğrulama",
            "description": "Giriş yapabilmeniz için gerekli.",
            "required": True,
        },
        {
            "purpose": DataProcessingPurpose.EXAM_EVALUATION,
            "title": "Sınav Değerlendirme",
            "description": "Sınavlarınızı değerlendirmek için gerekli.",
            "required": True,
        },
        {
            "purpose": DataProcessingPurpose.PROGRESS_TRACKING,
            "title": "İlerleme Takibi",
            "description": "Öğrenme ilerlemenizi takip etmek için.",
            "required": False,
        },
        {
            "purpose": DataProcessingPurpose.ANALYTICS,
            "title": "Analitik",
            "description": "Platform performansını iyileştirmek için.",
            "required": False,
        },
        {
            "purpose": DataProcessingPurpose.PERSONALIZATION,
            "title": "Kişiselleştirme",
            "description": "Size özel içerik önerileri için.",
            "required": False,
        },
        {
            "purpose": DataProcessingPurpose.MARKETING,
            "title": "Pazarlama",
            "description": "Yeni özellikler ve kampanyalardan haberdar olmak için.",
            "required": False,
        },
    ]

    return {
        "required_consents": required_consents,
        "total_count": len(required_consents),
    }


__all__ = ["router"]
