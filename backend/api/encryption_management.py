"""
Encryption Management API
TASK 48.3: Data encryption at rest - Management endpoints

Admin-only endpoints for encryption key management and rotation.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import os
from datetime import datetime, timedelta, timezone

from core.encryption_service import get_encryption_service, EncryptionService
from core.dependencies import get_current_user
from models.database import User

router = APIRouter(prefix="/admin/encryption", tags=["Admin - Encryption"])


class KeyRotationRequest(BaseModel):
    """Request model for key rotation"""

    new_key: Optional[str] = None  # If None, generate new key
    force: bool = False  # Force rotation even if recent


class KeyRotationResponse(BaseModel):
    """Response model for key rotation"""

    success: bool
    message: str
    new_key: str  # Return new key (should be stored securely!)
    old_key_count: int
    timestamp: datetime


class EncryptionStatusResponse(BaseModel):
    """Response model for encryption status"""

    enabled: bool
    primary_key_set: bool
    old_keys_count: int
    last_rotation: Optional[datetime]
    recommendation: str


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


@router.get("/status", response_model=EncryptionStatusResponse)
async def get_encryption_status(admin: User = Depends(require_admin)):
    """
    Get encryption service status

    **Admin only endpoint**

    Returns:
        - enabled: Whether encryption is enabled
        - primary_key_set: Whether primary key is set
        - old_keys_count: Number of old keys for rotation
        - recommendation: Recommendation for key rotation
    """
    service = get_encryption_service()

    # Check if encryption key is set
    encryption_key = os.getenv("ENCRYPTION_KEY")
    primary_key_set = encryption_key is not None

    # Get old keys count
    old_keys_count = len(service.old_keys)

    # Track in database - get last rotation timestamp
    last_rotation = None
    try:
        from core.database import get_async_session
        from sqlalchemy import text

        async for session in get_async_session():
            # Try to get last rotation from a simple key-value settings table
            # First ensure the settings table exists
            try:
                await session.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS system_settings (
                        key VARCHAR(255) PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                    )
                )
                await session.commit()
            except Exception:
                pass  # Table might already exist

            # Get last rotation
            result = await session.execute(
                text(
                    "SELECT value FROM system_settings WHERE key = 'encryption_last_rotation'"
                )
            )
            row = result.fetchone()
            if row and row[0]:
                try:
                    last_rotation = datetime.fromisoformat(row[0])
                except Exception:
                    pass
            break
    except Exception as e:
        # If database tracking fails, continue without it
        import logging

        logging.warning(f"Could not retrieve last rotation from database: {e}")

    # Determine recommendation
    recommendation = "Encryption is properly configured"
    if not primary_key_set:
        recommendation = (
            "⚠️ ENCRYPTION_KEY not set. Using temporary key (NOT FOR PRODUCTION!)"
        )
    elif old_keys_count == 0:
        recommendation = "Consider rotating encryption key (no rotation history)"
    elif last_rotation and datetime.now(timezone.utc) - last_rotation > timedelta(days=90):
        recommendation = (
            "⚠️ Encryption key hasn't been rotated in over 90 days. Consider rotation."
        )

    return EncryptionStatusResponse(
        enabled=True,
        primary_key_set=primary_key_set,
        old_keys_count=old_keys_count,
        last_rotation=last_rotation,
        recommendation=recommendation,
    )


@router.post("/rotate-key", response_model=KeyRotationResponse)
async def rotate_encryption_key(
    request: KeyRotationRequest, admin: User = Depends(require_admin)
):
    """
    Rotate encryption key

    **Admin only endpoint**

    **⚠️ IMPORTANT**:
    - Save the returned new_key to environment variable ENCRYPTION_KEY
    - Move old ENCRYPTION_KEY to ENCRYPTION_KEY_OLD_1
    - Restart application after rotation
    - Do NOT lose old keys - they're needed to decrypt existing data

    Args:
        request: Key rotation request
            - new_key: New encryption key (base64). If None, generates new key
            - force: Force rotation even if recent

    Returns:
        - success: Whether rotation succeeded
        - new_key: New encryption key (STORE SECURELY!)
        - old_key_count: Number of old keys
    """
    try:
        service = get_encryption_service()

        # Generate or use provided key
        if request.new_key:
            new_key = request.new_key.encode("utf-8")
        else:
            new_key = EncryptionService.generate_key()

        # Rotate key
        service.rotate_key(new_key)

        # Track rotation in database
        rotation_timestamp = datetime.now(timezone.utc)
        try:
            from core.database import get_async_session
            from sqlalchemy import text

            async for session in get_async_session():
                # Ensure settings table exists
                try:
                    await session.execute(
                        text(
                            """
                        CREATE TABLE IF NOT EXISTS system_settings (
                            key VARCHAR(255) PRIMARY KEY,
                            value TEXT,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """
                        )
                    )
                    await session.commit()
                except Exception:
                    pass  # Table might already exist

                # Insert or update last rotation timestamp
                await session.execute(
                    text(
                        """
                    INSERT INTO system_settings (key, value, updated_at)
                    VALUES ('encryption_last_rotation', :timestamp, :timestamp)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = EXCLUDED.updated_at
                """
                    ),
                    {"timestamp": rotation_timestamp.isoformat()},
                )
                await session.commit()
                break
        except Exception as e:
            import logging

            logging.warning(f"Could not track rotation in database: {e}")

        return KeyRotationResponse(
            success=True,
            message="Encryption key rotated successfully. IMPORTANT: Update ENCRYPTION_KEY in environment and restart!",
            new_key=new_key.decode("utf-8"),
            old_key_count=len(service.old_keys),
            timestamp=rotation_timestamp,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key rotation failed: {str(e)}",
        )


@router.post("/generate-key")
async def generate_new_key(admin: User = Depends(require_admin)) -> dict:
    """
    Generate a new encryption key

    **Admin only endpoint**

    Generates a new Fernet encryption key without rotating.
    Use this to get a new key before manual rotation.

    Returns:
        - key: New encryption key (base64 encoded)
        - instructions: Instructions for using the key
    """
    new_key = EncryptionService.generate_key()

    return {
        "key": new_key.decode("utf-8"),
        "instructions": (
            "1. Save this key securely (password manager, vault, etc.)\n"
            "2. Update ENCRYPTION_KEY environment variable\n"
            "3. Move old ENCRYPTION_KEY to ENCRYPTION_KEY_OLD_1\n"
            "4. Restart the application\n"
            "5. Verify encryption status with /admin/encryption/status\n"
            "\n"
            "⚠️ WARNING: Never lose encryption keys! They're required to decrypt data."
        ),
    }


@router.post("/test-encryption")
async def test_encryption(admin: User = Depends(require_admin)) -> dict:
    """
    Test encryption service

    **Admin only endpoint**

    Performs a test encryption/decryption cycle to verify service is working.

    Returns:
        - status: Test status
        - plaintext: Test plaintext
        - encrypted: Encrypted value
        - decrypted: Decrypted value
        - match: Whether decryption matches plaintext
    """
    try:
        service = get_encryption_service()

        plaintext = "test@example.com"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        return {
            "status": "success" if plaintext == decrypted else "failed",
            "plaintext": plaintext,
            "encrypted": encrypted[:50] + "..." if len(encrypted) > 50 else encrypted,
            "decrypted": decrypted,
            "match": plaintext == decrypted,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


# Add router to main application
# In backend/main.py:
# from api.encryption_management import router as encryption_router
# app.include_router(encryption_router)
