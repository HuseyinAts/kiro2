"""
API Key Management Endpoints (Task 48.6)
CRUD operations for API keys

Session 153 (GF117 real fix): `core.api_key_manager` has been ported to
AsyncSession, so the `Session(bind=db.bind.sync_engine)` shim, the
`_is_async_sync_mismatch` / `_degrade_async_mismatch` helpers, and the 503
degradation path that Session 149 installed are no longer needed. Handlers
now call the async manager directly with the AsyncSession from
`core.dependencies.get_db`. The `except HTTPException: raise` guard
(rule-of-eight, Session 146) is preserved so legitimate 4xx's (401/403/404/429
from the manager) propagate unchanged instead of being re-wrapped as 500s.

Author: Claude
Date: 2025-10-27 (original) / 2026-04-12 (async rewrite)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_key_manager import APIKeyScope, get_api_key_manager
from core.dependencies import AuthenticatedUser, get_current_user, get_db
from core.structured_logger import get_logger
from models.database import APIKey

logger = get_logger("api_key_api")

router = APIRouter(prefix="/api/v1/api-keys", tags=["API Keys"])


class APIKeyCreateRequest(BaseModel):
    """API key creation request"""

    name: str
    description: str | None = None
    scopes: list[str]
    rate_limit: int = 1000
    expires_in_days: int | None = None
    allowed_ips: list[str] | None = None


class APIKeyResponse(BaseModel):
    """API key response (without plaintext key)"""

    id: str
    name: str
    description: str | None
    prefix: str
    scopes: list[str]
    rate_limit: int
    is_active: bool
    usage_count: int
    last_used_at: str | None
    expires_at: str | None
    created_at: str


@router.post("/create", summary="Create API Key")
async def create_api_key(
    request_body: APIKeyCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Create new API key (Task 48.6)

    **IMPORTANT**: API key is shown only once! Store it securely.
    **Requires authentication**: Only authenticated users can create API keys.
    """
    try:
        manager = get_api_key_manager(db)
        scopes = [APIKeyScope(s) for s in request_body.scopes]

        return await manager.create_api_key(
            user_id=current_user.id,
            name=request_body.name,
            scopes=scopes,
            description=request_body.description,
            rate_limit=request_body.rate_limit,
            expires_in_days=request_body.expires_in_days,
            allowed_ips=request_body.allowed_ips,
            request=request,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API KEY API] Create failed: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/list", response_model=list[APIKeyResponse], summary="List API Keys")
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    List all API keys for current user (Task 48.6)
    **Requires authentication**: Only shows keys owned by the authenticated user.
    """
    try:
        result = await db.execute(
            select(APIKey).where(APIKey.user_id == current_user.id)
        )
        keys = result.scalars().all()

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API KEY API] List failed: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/{key_id}/revoke", summary="Revoke API Key")
async def revoke_api_key(
    key_id: str,
    reason: str = Query("manual_revoke", description="Revocation reason"),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Revoke API key (Task 48.6)
    **Requires authentication**: Only the owner can revoke their API keys.
    """
    try:
        # Ownership check — only key owner can revoke
        result = await db.execute(select(APIKey).where(APIKey.id == key_id))
        key_obj = result.scalar_one_or_none()
        if not key_obj:
            raise HTTPException(status_code=404, detail="API key bulunamadi")
        if str(key_obj.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Bu API key size ait degil")

        manager = get_api_key_manager(db)
        await manager.revoke_api_key(key_id, reason)

        return {"message": f"API key {key_id} revoked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API KEY API] Revoke failed: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/{key_id}/rotate", summary="Rotate API Key")
async def rotate_api_key(
    key_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Rotate API key (generates new, revokes old) (Task 48.6)
    **Requires authentication**: Only the owner can rotate their API keys.
    """
    try:
        # Ownership check — only key owner can rotate
        result = await db.execute(select(APIKey).where(APIKey.id == key_id))
        key_obj = result.scalar_one_or_none()
        if not key_obj:
            raise HTTPException(status_code=404, detail="API key bulunamadi")
        if str(key_obj.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Bu API key size ait degil")

        manager = get_api_key_manager(db)
        return await manager.rotate_api_key(key_id, request)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API KEY API] Rotate failed: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
