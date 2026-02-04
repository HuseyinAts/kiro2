"""
API Key Management Endpoints (Task 48.6)
CRUD operations for API keys

Author: Claude
Date: 2025-10-27
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_key_manager import APIKeyManager, APIKeyScope, get_api_key_manager
from core.dependencies import get_db, get_current_user
from core.structured_logger import get_logger
from models.database import APIKey, User

logger = get_logger("api_key_api")

router = APIRouter(prefix="/api/v1/api-keys", tags=["API Keys"])


class APIKeyCreateRequest(BaseModel):
    """API key creation request"""

    name: str
    description: Optional[str] = None
    scopes: List[str]
    rate_limit: int = 1000
    expires_in_days: Optional[int] = None
    allowed_ips: Optional[List[str]] = None


class APIKeyResponse(BaseModel):
    """API key response (without plaintext key)"""

    id: str
    name: str
    description: Optional[str]
    prefix: str
    scopes: List[str]
    rate_limit: int
    is_active: bool
    usage_count: int
    last_used_at: Optional[str]
    expires_at: Optional[str]
    created_at: str


@router.post("/create", summary="Create API Key")
async def create_api_key(
    request_body: APIKeyCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create new API key (Task 48.6)

    **IMPORTANT**: API key is shown only once! Store it securely.
    **Requires authentication**: Only authenticated users can create API keys.
    """
    try:
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        # Get user_id from authenticated user
        user_id = current_user.get("user_id") or current_user.get("id")

        manager = get_api_key_manager(sync_db)
        scopes = [APIKeyScope(s) for s in request_body.scopes]

        result = manager.create_api_key(
            user_id=user_id,
            name=request_body.name,
            scopes=scopes,
            description=request_body.description,
            rate_limit=request_body.rate_limit,
            expires_in_days=request_body.expires_in_days,
            allowed_ips=request_body.allowed_ips,
            request=request,
        )

        if sync_db:
            sync_db.close()

        return result

    except Exception as e:
        logger.error(f"[API KEY API] Create failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[APIKeyResponse], summary="List API Keys")
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all API keys for current user (Task 48.6)
    **Requires authentication**: Only shows keys owned by the authenticated user.
    """
    try:
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        # Get user_id from authenticated user
        user_id = current_user.get("user_id") or current_user.get("id")

        keys = sync_db.query(APIKey).filter(APIKey.user_id == user_id).all()

        if sync_db:
            sync_db.close()

        return [
            APIKeyResponse(
                id=key.id,
                name=key.name,
                description=key.description,
                prefix=key.key_prefix,
                scopes=key.scopes.get("scopes", []),
                rate_limit=key.rate_limit,
                is_active=key.is_active,
                usage_count=key.usage_count,
                last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                expires_at=key.expires_at.isoformat() if key.expires_at else None,
                created_at=key.created_at.isoformat(),
            )
            for key in keys
        ]

    except Exception as e:
        logger.error(f"[API KEY API] List failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{key_id}/revoke", summary="Revoke API Key")
async def revoke_api_key(
    key_id: str,
    reason: str = Query("manual_revoke", description="Revocation reason"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Revoke API key (Task 48.6)
    **Requires authentication**: Only the owner can revoke their API keys.
    """
    try:
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        manager = get_api_key_manager(sync_db)
        manager.revoke_api_key(key_id, reason)

        if sync_db:
            sync_db.close()

        return {"message": f"API key {key_id} revoked successfully"}

    except Exception as e:
        logger.error(f"[API KEY API] Revoke failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{key_id}/rotate", summary="Rotate API Key")
async def rotate_api_key(
    key_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Rotate API key (generates new, revokes old) (Task 48.6)
    **Requires authentication**: Only the owner can rotate their API keys.
    """
    try:
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        manager = get_api_key_manager(sync_db)
        new_key = manager.rotate_api_key(key_id, request)

        if sync_db:
            sync_db.close()

        return new_key

    except Exception as e:
        logger.error(f"[API KEY API] Rotate failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
