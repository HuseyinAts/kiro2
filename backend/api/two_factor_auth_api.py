"""
Two-Factor Authentication (2FA) API Endpoints
PHASE 2 Sprint 4: Security Hardening

Implements TOTP-based 2FA with QR code setup and backup codes
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.two_factor_auth import two_factor_auth
from core.jwt_auth import get_current_user
from core.structured_logger import get_logger
from models.database import User

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth/2fa", tags=["2FA Authentication"])


# Request/Response Models
class TwoFactorSetupResponse(BaseModel):
    """2FA setup response with QR code"""
    secret: str
    qr_code: str  # Base64 encoded PNG
    backup_codes: List[str]


class TwoFactorVerifyRequest(BaseModel):
    """Request to verify TOTP token"""
    token: str


class TwoFactorEnableRequest(BaseModel):
    """Request to enable 2FA"""
    token: str  # Verification token


class BackupCodeVerifyRequest(BaseModel):
    """Request to verify backup code"""
    code: str


@router.post("/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate 2FA secret and QR code for user

    Returns:
        - secret: TOTP secret key
        - qr_code: Base64 encoded QR code image
        - backup_codes: List of backup recovery codes

    **Usage**: User scans QR code with authenticator app (Google Authenticator, Authy)
    """
    try:
        # Check if 2FA already enabled
        if current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled for this account"
            )

        # Generate new secret
        secret = two_factor_auth.generate_secret()

        # Generate QR code
        qr_code = two_factor_auth.generate_qr_code(
            secret=secret,
            user_email=current_user.email,
            issuer="Kiro2 Egitim"
        )

        # Generate backup codes
        backup_codes = two_factor_auth.generate_backup_codes(count=10)
        hashed_codes = [two_factor_auth.hash_backup_code(code) for code in backup_codes]

        # Store secret and backup codes in database (but don't enable yet)
        stmt = (
            update(User)
            .where(User.id == current_user.id)
            .values(
                secret_2fa=secret,
                backup_codes_hashed={"codes": hashed_codes}
            )
        )
        await db.execute(stmt)
        await db.commit()

        logger.info(
            "2fa_setup_initiated",
            user_id=current_user.id,
            email=current_user.email
        )

        return TwoFactorSetupResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("2fa_setup_error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup 2FA"
        )


@router.post("/enable")
async def enable_2fa(
    request: TwoFactorEnableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Enable 2FA after verifying token

    User must:
    1. Call /setup to get secret and QR code
    2. Add to authenticator app
    3. Call this endpoint with token to enable
    """
    try:
        # Check if already enabled
        if current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled"
            )

        # Check if secret exists
        if not current_user.secret_2fa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA setup not initiated. Call /setup first"
            )

        # Verify token
        is_valid = two_factor_auth.verify_token(
            secret=current_user.secret_2fa,
            token=request.token
        )

        if not is_valid:
            logger.warning(
                "2fa_enable_failed_invalid_token",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        # Enable 2FA
        stmt = (
            update(User)
            .where(User.id == current_user.id)
            .values(is_2fa_enabled=True)
        )
        await db.execute(stmt)
        await db.commit()

        logger.info("2fa_enabled", user_id=current_user.id, email=current_user.email)

        return {
            "success": True,
            "message": "2FA enabled successfully",
            "is_2fa_enabled": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("2fa_enable_error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable 2FA"
        )


@router.post("/disable")
async def disable_2fa(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable 2FA after verifying token

    Requires valid TOTP token to disable for security
    """
    try:
        # Check if 2FA is enabled
        if not current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled"
            )

        # Verify token before disabling
        is_valid = two_factor_auth.verify_token(
            secret=current_user.secret_2fa,
            token=request.token
        )

        if not is_valid:
            logger.warning(
                "2fa_disable_failed_invalid_token",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        # Disable 2FA and clear secret
        stmt = (
            update(User)
            .where(User.id == current_user.id)
            .values(
                is_2fa_enabled=False,
                secret_2fa=None,
                backup_codes_hashed=None
            )
        )
        await db.execute(stmt)
        await db.commit()

        logger.info("2fa_disabled", user_id=current_user.id, email=current_user.email)

        return {
            "success": True,
            "message": "2FA disabled successfully",
            "is_2fa_enabled": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("2fa_disable_error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )


@router.post("/verify")
async def verify_2fa_token(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Verify TOTP token

    Used during login flow or for testing
    """
    try:
        if not current_user.is_2fa_enabled or not current_user.secret_2fa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled for this account"
            )

        is_valid = two_factor_auth.verify_token(
            secret=current_user.secret_2fa,
            token=request.token
        )

        return {
            "valid": is_valid,
            "message": "Token is valid" if is_valid else "Token is invalid"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("2fa_verify_error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify token"
        )


@router.post("/verify-backup")
async def verify_backup_code(
    request: BackupCodeVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify backup recovery code

    Backup codes are single-use. After successful verification,
    the code is removed from the database.
    """
    try:
        if not current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled"
            )

        if not current_user.backup_codes_hashed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No backup codes available"
            )

        hashed_codes = current_user.backup_codes_hashed.get("codes", [])

        # Verify code
        is_valid, matched_hash = two_factor_auth.verify_backup_code(
            code=request.code.upper(),  # Normalize to uppercase
            hashed_codes=hashed_codes
        )

        if not is_valid:
            logger.warning(
                "2fa_backup_code_invalid",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid backup code"
            )

        # Remove used code (single-use)
        hashed_codes.remove(matched_hash)

        stmt = (
            update(User)
            .where(User.id == current_user.id)
            .values(backup_codes_hashed={"codes": hashed_codes})
        )
        await db.execute(stmt)
        await db.commit()

        logger.info(
            "2fa_backup_code_used",
            user_id=current_user.id,
            remaining_codes=len(hashed_codes)
        )

        return {
            "success": True,
            "valid": True,
            "message": "Backup code verified successfully",
            "remaining_codes": len(hashed_codes)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("2fa_backup_verify_error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify backup code"
        )


@router.get("/status")
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get current 2FA status for user
    """
    backup_codes_count = 0
    if current_user.backup_codes_hashed:
        backup_codes_count = len(current_user.backup_codes_hashed.get("codes", []))

    return {
        "is_2fa_enabled": current_user.is_2fa_enabled,
        "has_secret": bool(current_user.secret_2fa),
        "backup_codes_remaining": backup_codes_count
    }


@router.get("/backup-codes/regenerate")
async def regenerate_backup_codes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate backup codes

    **WARNING**: This invalidates all existing backup codes
    """
    try:
        if not current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA must be enabled to generate backup codes"
            )

        # Generate new backup codes
        backup_codes = two_factor_auth.generate_backup_codes(count=10)
        hashed_codes = [two_factor_auth.hash_backup_code(code) for code in backup_codes]

        # Update database
        stmt = (
            update(User)
            .where(User.id == current_user.id)
            .values(backup_codes_hashed={"codes": hashed_codes})
        )
        await db.execute(stmt)
        await db.commit()

        logger.info("2fa_backup_codes_regenerated", user_id=current_user.id)

        return {
            "success": True,
            "backup_codes": backup_codes,
            "message": "New backup codes generated. Save these securely!"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("2fa_backup_regenerate_error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate backup codes"
        )


__all__ = ["router"]
