"""
FERPA/COPPA Compliance API Endpoints
Educational privacy and children's online privacy protection

Author: KIRO2 AI Team
Date: 2025-01
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, validator

from core.dependencies import get_db
from models.ferpa_coppa_models import (
    FERPAConsent, COPPAParentalConsent, EducationalRecordAccess,
    ParentalConsentStatus
)


router = APIRouter(prefix="/api/v1/compliance", tags=["FERPA/COPPA Compliance"])


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
    parent_id: Optional[int] = None
    record_types: List[str]
    allow_third_party_disclosure: bool = False
    third_party_institutions: Optional[str] = None


class ConsentVerification(BaseModel):
    consent_id: str
    verification_method: str
    verification_document: Optional[str] = None


@router.post("/coppa/parental-consent", status_code=status.HTTP_201_CREATED)
async def request_coppa_parental_consent(
    request: COPPAConsentRequest,
    db: Session = Depends(get_db)
):
    """Request COPPA parental consent for under-13 user"""
    
    # Check if consent already exists
    existing = db.query(COPPAParentalConsent).filter(
        COPPAParentalConsent.child_id == request.child_id,
        COPPAParentalConsent.consent_status == ParentalConsentStatus.VERIFIED
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active parental consent already exists"
        )
    
    consent = COPPAParentalConsent(
        child_id=request.child_id,
        parent_id=request.parent_id,
        child_date_of_birth=request.child_date_of_birth,
        verification_method=request.verification_method,
        allow_data_collection=request.allow_data_collection,
        allow_marketing_communication=request.allow_marketing_communication,
        allow_third_party_sharing=request.allow_third_party_sharing,
        consent_status=ParentalConsentStatus.PENDING
    )
    
    db.add(consent)
    db.commit()
    db.refresh(consent)
    
    return {
        "message": "Parental consent request created",
        "consent_id": consent.consent_id,
        "status": consent.consent_status,
        "next_steps": "Parent verification required"
    }


@router.post("/coppa/verify-consent/{consent_id}")
async def verify_coppa_consent(
    consent_id: str,
    verification: ConsentVerification,
    db: Session = Depends(get_db)
):
    """Verify COPPA parental consent"""
    
    consent = db.query(COPPAParentalConsent).filter(
        COPPAParentalConsent.consent_id == consent_id
    ).first()
    
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    
    if consent.consent_status != ParentalConsentStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Consent already {consent.consent_status}"
        )
    
    consent.consent_status = ParentalConsentStatus.VERIFIED
    consent.verification_date = datetime.now()
    consent.consent_given_date = datetime.now()
    consent.verification_document_path = verification.verification_document
    
    db.commit()
    
    return {
        "message": "Parental consent verified",
        "consent_id": consent.consent_id,
        "status": "verified"
    }


@router.post("/ferpa/consent", status_code=status.HTTP_201_CREATED)
async def request_ferpa_consent(
    request: FERPAConsentRequest,
    db: Session = Depends(get_db)
):
    """Request FERPA consent for educational records access"""
    
    consent = FERPAConsent(
        student_id=request.student_id,
        parent_id=request.parent_id,
        record_types=",".join(request.record_types),
        allow_third_party_disclosure=request.allow_third_party_disclosure,
        third_party_institutions=request.third_party_institutions,
        consent_status=ParentalConsentStatus.PENDING
    )
    
    db.add(consent)
    db.commit()
    db.refresh(consent)
    
    return {
        "message": "FERPA consent request created",
        "consent_id": consent.consent_id,
        "status": consent.consent_status
    }


@router.get("/coppa/consent/{child_id}")
async def get_coppa_consent_status(
    child_id: int,
    db: Session = Depends(get_db)
):
    """Get COPPA consent status for a child"""
    
    consent = db.query(COPPAParentalConsent).filter(
        COPPAParentalConsent.child_id == child_id
    ).order_by(COPPAParentalConsent.created_at.desc()).first()
    
    if not consent:
        return {
            "child_id": child_id,
            "has_consent": False,
            "status": "no_consent_found"
        }
    
    return {
        "child_id": child_id,
        "has_consent": consent.consent_status == ParentalConsentStatus.VERIFIED,
        "status": consent.consent_status,
        "consent_id": consent.consent_id,
        "verification_date": consent.verification_date,
        "allow_data_collection": consent.allow_data_collection
    }


@router.delete("/coppa/withdraw-consent/{consent_id}")
async def withdraw_coppa_consent(
    consent_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Withdraw COPPA parental consent"""
    
    consent = db.query(COPPAParentalConsent).filter(
        COPPAParentalConsent.consent_id == consent_id
    ).first()
    
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    
    consent.consent_status = ParentalConsentStatus.WITHDRAWN
    consent.withdrawal_date = datetime.now()
    consent.withdrawal_reason = reason
    
    db.commit()
    
    return {
        "message": "Parental consent withdrawn",
        "consent_id": consent_id,
        "data_deletion_initiated": True
    }


@router.get("/ferpa/access-log/{student_id}")
async def get_ferpa_access_log(
    student_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get FERPA educational records access log"""
    
    access_logs = db.query(EducationalRecordAccess).filter(
        EducationalRecordAccess.student_id == student_id
    ).order_by(EducationalRecordAccess.access_timestamp.desc()).limit(limit).all()
    
    return {
        "student_id": student_id,
        "total_accesses": len(access_logs),
        "access_logs": [
            {
                "log_id": log.log_id,
                "accessor_role": log.accessor_role,
                "record_type": log.record_type,
                "access_purpose": log.access_purpose,
                "timestamp": log.access_timestamp
            }
            for log in access_logs
        ]
    }
