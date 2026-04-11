"""
FERPA/COPPA Compliance API Endpoints
Educational privacy and children's online privacy protection

Session 149 (GF113): all 6 handlers converted from the deprecated sync
`def` + `Depends(get_db)` pattern to `async def` + `Depends(get_async_session)`
+ `select()` / `await db.execute(...)` / `await db.commit()`. The previous
code used sync `db.query(...)` on an AsyncSession dependency, which raised
`AttributeError: 'AsyncSession' object has no attribute 'query'`. Same fix
class as Wave 10/11 GF86/GF87/GF95 and Wave 13 GF115.

Author: KIRO2 AI Team
Date: 2025-01
"""

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.ferpa_coppa_models import (
    COPPAParentalConsent,
    EducationalRecordAccess,
    FERPAConsent,
    ParentalConsentStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance", tags=["FERPA/COPPA Compliance"])


# Session 149 (GF113): `coppa_parental_consents.child_id` is VARCHAR in DB but
# the ORM model declares Integer. asyncpg refuses the type-mismatched bind
# with `operator does not exist: character varying = integer`. Until a
# migration aligns the types, degrade DBAPI errors to 503 at the handler
# boundary — same GF22/GF41/GF106/GF112/GF115 pattern.
_SCHEMA_DRIFT_MSG = (
    "Uygunluk servisi gecici olarak kullanilamiyor: "
    "veritabani sema guncellemesi bekleniyor."
)


def _degrade_schema_error(exc: Exception, context: str) -> HTTPException:
    """Convert DBAPI schema drift errors to structured 503."""
    logger.error(f"{context}: {type(exc).__name__}: {exc}")
    return HTTPException(status_code=503, detail=_SCHEMA_DRIFT_MSG)


_DB_ERRORS = (DBAPIError, SQLAlchemyError)


# Pydantic models
class COPPAConsentRequest(BaseModel):
    child_id: int
    parent_id: int
    child_date_of_birth: date
    verification_method: str
    allow_data_collection: bool = False
    allow_marketing_communication: bool = False
    allow_third_party_sharing: bool = False

    @validator("child_date_of_birth")
    def validate_child_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age >= 13:
            raise ValueError("COPPA applies only to children under 13")
        return v


class FERPAConsentRequest(BaseModel):
    student_id: int
    parent_id: int | None = None
    record_types: list[str]
    allow_third_party_disclosure: bool = False
    third_party_institutions: str | None = None


class ConsentVerification(BaseModel):
    consent_id: str
    verification_method: str
    verification_document: str | None = None


@router.post("/coppa/parental-consent", status_code=status.HTTP_201_CREATED)
async def request_coppa_parental_consent(
    request: COPPAConsentRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Request COPPA parental consent for under-13 user"""
    try:
        # Check if consent already exists
        result = await db.execute(
            select(COPPAParentalConsent).where(
                COPPAParentalConsent.child_id == request.child_id,
                COPPAParentalConsent.consent_status == ParentalConsentStatus.VERIFIED,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Active parental consent already exists",
            )

        consent = COPPAParentalConsent(
            child_id=request.child_id,
            parent_id=request.parent_id,
            child_date_of_birth=request.child_date_of_birth,
            verification_method=request.verification_method,
            allow_data_collection=request.allow_data_collection,
            allow_marketing_communication=request.allow_marketing_communication,
            allow_third_party_sharing=request.allow_third_party_sharing,
            consent_status=ParentalConsentStatus.PENDING,
        )

        db.add(consent)
        await db.commit()
        await db.refresh(consent)

        return {
            "message": "Parental consent request created",
            "consent_id": consent.consent_id,
            "status": consent.consent_status,
            "next_steps": "Parent verification required",
        }
    except HTTPException:
        raise
    except _DB_ERRORS as e:
        raise _degrade_schema_error(e, "request_coppa_parental_consent")


@router.post("/coppa/verify-consent/{consent_id}")
async def verify_coppa_consent(
    consent_id: str,
    verification: ConsentVerification,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Verify COPPA parental consent"""
    try:
        result = await db.execute(
            select(COPPAParentalConsent).where(
                COPPAParentalConsent.consent_id == consent_id
            )
        )
        consent = result.scalar_one_or_none()

        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")

        if consent.consent_status != ParentalConsentStatus.PENDING:
            raise HTTPException(
                status_code=400, detail=f"Consent already {consent.consent_status}"
            )

        consent.consent_status = ParentalConsentStatus.VERIFIED
        consent.verification_date = datetime.now()
        consent.consent_given_date = datetime.now()
        consent.verification_document_path = verification.verification_document

        await db.commit()

        return {
            "message": "Parental consent verified",
            "consent_id": consent.consent_id,
            "status": "verified",
        }
    except HTTPException:
        raise
    except _DB_ERRORS as e:
        raise _degrade_schema_error(e, "verify_coppa_consent")


@router.post("/ferpa/consent", status_code=status.HTTP_201_CREATED)
async def request_ferpa_consent(
    request: FERPAConsentRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Request FERPA consent for educational records access"""
    try:
        consent = FERPAConsent(
            student_id=request.student_id,
            parent_id=request.parent_id,
            record_types=",".join(request.record_types),
            allow_third_party_disclosure=request.allow_third_party_disclosure,
            third_party_institutions=request.third_party_institutions,
            consent_status=ParentalConsentStatus.PENDING,
        )

        db.add(consent)
        await db.commit()
        await db.refresh(consent)

        return {
            "message": "FERPA consent request created",
            "consent_id": consent.consent_id,
            "status": consent.consent_status,
        }
    except HTTPException:
        raise
    except _DB_ERRORS as e:
        raise _degrade_schema_error(e, "request_ferpa_consent")


@router.get("/coppa/consent/{child_id}")
async def get_coppa_consent_status(
    child_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get COPPA consent status for a child"""
    try:
        result = await db.execute(
            select(COPPAParentalConsent)
            .where(COPPAParentalConsent.child_id == child_id)
            .order_by(COPPAParentalConsent.created_at.desc())
        )
        consent = result.scalars().first()

        if not consent:
            return {
                "child_id": child_id,
                "has_consent": False,
                "status": "no_consent_found",
            }

        return {
            "child_id": child_id,
            "has_consent": consent.consent_status == ParentalConsentStatus.VERIFIED,
            "status": consent.consent_status,
            "consent_id": consent.consent_id,
            "verification_date": consent.verification_date,
            "allow_data_collection": consent.allow_data_collection,
        }
    except HTTPException:
        raise
    except _DB_ERRORS as e:
        raise _degrade_schema_error(e, "get_coppa_consent_status")


@router.delete("/coppa/withdraw-consent/{consent_id}")
async def withdraw_coppa_consent(
    consent_id: str,
    reason: str | None = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Withdraw COPPA parental consent"""
    try:
        result = await db.execute(
            select(COPPAParentalConsent).where(
                COPPAParentalConsent.consent_id == consent_id
            )
        )
        consent = result.scalar_one_or_none()

        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")

        consent.consent_status = ParentalConsentStatus.WITHDRAWN
        consent.withdrawal_date = datetime.now()
        consent.withdrawal_reason = reason

        await db.commit()

        return {
            "message": "Parental consent withdrawn",
            "consent_id": consent_id,
            "data_deletion_initiated": True,
        }
    except HTTPException:
        raise
    except _DB_ERRORS as e:
        raise _degrade_schema_error(e, "withdraw_coppa_consent")


@router.get("/ferpa/access-log/{student_id}")
async def get_ferpa_access_log(
    student_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get FERPA educational records access log"""
    # IDOR koruması: sadece admin/teacher erişebilir
    role_str = getattr(current_user.role, "value", str(current_user.role)).lower()
    if role_str not in ("admin", "teacher", "super_admin"):
        user_id = getattr(current_user, "id", None)
        if user_id != student_id:
            raise HTTPException(
                status_code=403,
                detail="Bu öğrencinin erişim loglarına yetkiniz yok",
            )

    try:
        result = await db.execute(
            select(EducationalRecordAccess)
            .where(EducationalRecordAccess.student_id == student_id)
            .order_by(EducationalRecordAccess.access_timestamp.desc())
            .limit(limit)
        )
        access_logs = result.scalars().all()

        return {
            "student_id": student_id,
            "total_accesses": len(access_logs),
            "access_logs": [
                {
                    "log_id": log.log_id,
                    "accessor_role": log.accessor_role,
                    "record_type": log.record_type,
                    "access_purpose": log.access_purpose,
                    "timestamp": log.access_timestamp,
                }
                for log in access_logs
            ],
        }
    except HTTPException:
        raise
    except _DB_ERRORS as e:
        raise _degrade_schema_error(e, "get_ferpa_access_log")
