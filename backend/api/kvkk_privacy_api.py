"""
KVKK Privacy Dashboard API
PHASE 2 Sprint 5: KVKK Compliance

Endpoints for:
- Data export (Right to Data Portability - KVKK Article 11)
- Data deletion (Right to Erasure - KVKK Article 7)
"""

import json
import os
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.jwt_auth import TokenPayload, get_current_user
from core.structured_logger import get_logger
from models.kvkk_models import (
    DeletionRequestStatus,
    ExportRequestStatus,
    KVKKAuditLog,
    KVKKDataDeletionRequest,
    KVKKDataExportRequest,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/kvkk/privacy", tags=["KVKK Privacy"])


# ============================================================================
# Request/Response Models
# ============================================================================


class DataExportRequest(BaseModel):
    """Request to export user data"""

    export_format: str = "json"  # json, csv, pdf
    data_categories: list[str] | None = None  # None = all data
    reason: str | None = None


class DataDeletionRequest(BaseModel):
    """Request to delete user data"""

    deletion_type: str = "full"  # full, partial
    data_categories: list[str] | None = None
    reason: str  # Required by KVKK


class ExportRequestResponse(BaseModel):
    """Data export request response"""

    id: str
    status: ExportRequestStatus
    export_format: str
    requested_at: datetime
    download_url: str | None = None
    download_expires_at: datetime | None = None
    file_size_bytes: int | None = None

    model_config = ConfigDict(from_attributes=True)


class DeletionRequestResponse(BaseModel):
    """Data deletion request response"""

    id: str
    status: DeletionRequestStatus
    deletion_type: str
    requested_at: datetime
    reviewed_at: datetime | None = None
    completed_at: datetime | None = None
    rejection_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Background Tasks
# ============================================================================

# Dışa aktarma dosyalarının geçici (private) dizini — StaticFiles ile SERVE EDİLMEZ,
# yalnız kimlik-doğrulamalı download endpoint'i okur (KVKK verisi public URL'de sızmaz).
EXPORT_DIR = "/app/kvkk_exports"


async def _collect_user_data(db: AsyncSession, user_id: str) -> dict:
    """KVKK Md.11 — kullanıcının kişisel verisini şema genelinden toplar (generic).

    information_schema'dan `user_id` kolonu olan tüm public tabloları bulur ve her
    birinden yalnız bu kullanıcının satırlarını çeker (tablo başına LIMIT). `users`
    tablosu `id` ile eklenir. Tablo adları information_schema'dan geldiği + güvenli
    desenle süzüldüğü için identifier-injection yok.

    RLS: process_data_export kendi engine'ini açar (GUC set EDİLMEZ → permissive),
    WHERE user_id filtresi veriyi kullanıcının kendisine sınırlar.
    """
    import re

    from sqlalchemy import text as _t

    out: dict = {
        "exported_at": datetime.now(UTC).isoformat(),
        "user_id": user_id,
        "tables": {},
    }
    try:
        r = (
            (await db.execute(_t("SELECT * FROM users WHERE id = :u"), {"u": user_id}))
            .mappings()
            .first()
        )
        out["tables"]["users"] = [dict(r)] if r else []
    except Exception:
        out["tables"]["users"] = []

    tabs = (
        (
            await db.execute(
                _t(
                    "SELECT table_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND column_name='user_id' "
                    "ORDER BY table_name"
                )
            )
        )
        .scalars()
        .all()
    )
    safe = re.compile(r"^[a-z_][a-z0-9_]*$")
    for t in tabs:
        if not safe.match(t):
            continue
        try:
            rows = (
                (
                    await db.execute(
                        _t(f'SELECT * FROM "{t}" WHERE user_id = :u LIMIT 5000'),
                        {"u": user_id},
                    )
                )
                .mappings()
                .all()
            )
            if rows:
                out["tables"][t] = [dict(x) for x in rows]
        except Exception:
            continue
    return out


async def process_data_export(
    request_id: str,
    user_id: str,
    export_format: str,
    data_categories: list[str] | None,
    db_url: str,
):
    """
    Background task to process data export

    This would typically:
    1. Collect all user data from database
    2. Format as JSON/CSV/PDF
    3. Upload to secure storage
    4. Generate download URL
    5. Send email notification
    """
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # Update status to processing
            stmt = (
                update(KVKKDataExportRequest)
                .where(KVKKDataExportRequest.id == request_id)
                .values(
                    status=ExportRequestStatus.PROCESSING,
                    processed_at=datetime.now(UTC),
                )
            )
            await db.execute(stmt)
            await db.commit()

            # Gerçek veri toplama — kullanıcının şema genelindeki tüm PII'ı.
            user_data = await _collect_user_data(db, user_id)
            user_data["format"] = export_format
            user_data["categories"] = data_categories or ["all"]

            # Private dizine yaz (StaticFiles ile serve EDİLMEZ; authed download okur).
            os.makedirs(EXPORT_DIR, exist_ok=True)
            file_path = f"{EXPORT_DIR}/{request_id}.json"
            payload = json.dumps(user_data, default=str, ensure_ascii=False)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(payload)
            file_size = len(payload.encode("utf-8"))
            # Public URL DEĞİL — kimlik-doğrulamalı endpoint (KVKK verisi sızmasın).
            download_url = f"/api/v1/kvkk/privacy/export/{request_id}/download"
            expires_at = datetime.now(UTC) + timedelta(days=7)

            # Update request as completed
            stmt = (
                update(KVKKDataExportRequest)
                .where(KVKKDataExportRequest.id == request_id)
                .values(
                    status=ExportRequestStatus.COMPLETED,
                    file_path=file_path,
                    file_size_bytes=file_size,
                    download_url=download_url,
                    download_expires_at=expires_at,
                    completed_at=datetime.now(UTC),
                )
            )
            await db.execute(stmt)
            await db.commit()

            logger.info(
                "data_export_completed",
                request_id=request_id,
                user_id=user_id,
                file_size=file_size,
            )

        except Exception as e:
            logger.error("data_export_failed", request_id=request_id, error=str(e))

            # Update as failed
            stmt = (
                update(KVKKDataExportRequest)
                .where(KVKKDataExportRequest.id == request_id)
                .values(
                    status=ExportRequestStatus.FAILED,
                    error_message=str(e),
                    completed_at=datetime.now(UTC),
                )
            )
            await db.execute(stmt)
            await db.commit()


# ============================================================================
# Data Export Endpoints
# ============================================================================


@router.post("/export", response_model=ExportRequestResponse)
async def request_data_export(
    export_req: DataExportRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Request data export (KVKK Article 11 - Right to Data Portability)

    User can request export of all their personal data.
    Export will be processed in background and download link
    will be provided (valid for 7 days).
    """
    try:
        # Check for pending/processing requests
        stmt = select(KVKKDataExportRequest).where(
            KVKKDataExportRequest.user_id == current_user.sub,
            KVKKDataExportRequest.status.in_(
                [ExportRequestStatus.PENDING, ExportRequestStatus.PROCESSING]
            ),
        )
        result = await db.execute(stmt)
        pending_request = result.scalar_one_or_none()

        if pending_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a pending export request",
            )

        # Create export request
        new_request = KVKKDataExportRequest(
            id=str(uuid.uuid4()),
            user_id=current_user.sub,
            status=ExportRequestStatus.PENDING,
            request_reason=export_req.reason,
            export_format=export_req.export_format,
            data_categories={"categories": export_req.data_categories}
            if export_req.data_categories
            else None,
            requested_at=datetime.now(UTC),
        )

        db.add(new_request)

        # Log action
        audit_log = KVKKAuditLog(
            id=str(uuid.uuid4()),
            user_id=current_user.sub,
            accessed_by=current_user.sub,
            action="data_export_requested",
            resource_type="user_data",
            resource_id=current_user.sub,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details={"request_id": new_request.id, "format": export_req.export_format},
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(new_request)

        # Process in background
        from core.config import settings

        background_tasks.add_task(
            process_data_export,
            request_id=new_request.id,
            user_id=current_user.sub,
            export_format=export_req.export_format,
            data_categories=export_req.data_categories,
            db_url=str(settings.database_url),
        )

        logger.info(
            "data_export_requested",
            user_id=current_user.sub,
            request_id=new_request.id,
            format=export_req.export_format,
        )

        return new_request

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "data_export_request_error", user_id=current_user.sub, error=str(e)
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request data export",
        )


@router.get("/export/requests", response_model=list[ExportRequestResponse])
async def get_export_requests(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get all data export requests for current user"""
    try:
        stmt = (
            select(KVKKDataExportRequest)
            .where(KVKKDataExportRequest.user_id == current_user.sub)
            .order_by(KVKKDataExportRequest.requested_at.desc())
        )
        result = await db.execute(stmt)
        requests = result.scalars().all()

        return requests

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_export_requests_error", user_id=current_user.sub, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve export requests",
        )


@router.get("/export/{request_id}", response_model=ExportRequestResponse)
async def get_export_request(
    request_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get specific export request status"""
    try:
        stmt = select(KVKKDataExportRequest).where(
            KVKKDataExportRequest.id == request_id,
            KVKKDataExportRequest.user_id == current_user.sub,
        )
        result = await db.execute(stmt)
        export_request = result.scalar_one_or_none()

        if not export_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Export request not found"
            )

        return export_request

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_export_request_error", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve export request",
        )


@router.get("/export/{request_id}/download")
async def download_export(
    request_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Tamamlanmış dışa aktarmayı indir (KVKK Md.11).

    Kimlik-doğrulamalı + sahiplik kontrollü — public URL YOK (veri sızmaz). Dosya
    (7 gün) mevcutsa okunur; container yeniden yaratılıp dosya kaybolduysa veri
    anlık yeniden toplanır (fallback). JSON attachment olarak döner.
    """
    stmt = select(KVKKDataExportRequest).where(
        KVKKDataExportRequest.id == request_id,
        KVKKDataExportRequest.user_id == current_user.sub,
    )
    export_request = (await db.execute(stmt)).scalar_one_or_none()
    if not export_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export request not found"
        )
    if export_request.status != ExportRequestStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Export not ready (status: {export_request.status})",
        )
    if export_request.download_expires_at and export_request.download_expires_at < (
        datetime.now(UTC)
    ):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Export expired")

    payload: str | None = None
    fp = export_request.file_path
    if fp and os.path.exists(fp):
        with open(fp, encoding="utf-8") as f:
            payload = f.read()
    else:
        # Dosya kaybolmuş (ephemeral) → anlık yeniden topla (sahiplik zaten doğrulandı).
        data = await _collect_user_data(db, current_user.sub)
        payload = json.dumps(data, default=str, ensure_ascii=False)

    return Response(
        content=payload,
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="kvkk_export_{request_id}.json"'
            )
        },
    )


# ============================================================================
# Data Deletion Endpoints
# ============================================================================


@router.post("/delete", response_model=DeletionRequestResponse)
async def request_data_deletion(
    deletion_req: DataDeletionRequest,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Request data deletion (KVKK Article 7 - Right to Erasure)

    User can request deletion of their personal data.
    Request will be reviewed by admin before processing.

    Note: Some data may be retained for legal compliance.
    """
    try:
        # Check for pending requests
        stmt = select(KVKKDataDeletionRequest).where(
            KVKKDataDeletionRequest.user_id == current_user.sub,
            KVKKDataDeletionRequest.status.in_(
                [
                    DeletionRequestStatus.PENDING,
                    DeletionRequestStatus.APPROVED,
                    DeletionRequestStatus.PROCESSING,
                ]
            ),
        )
        result = await db.execute(stmt)
        pending_request = result.scalar_one_or_none()

        if pending_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a pending deletion request",
            )

        # Create deletion request
        new_request = KVKKDataDeletionRequest(
            id=str(uuid.uuid4()),
            user_id=current_user.sub,
            status=DeletionRequestStatus.PENDING,
            request_reason=deletion_req.reason,
            deletion_type=deletion_req.deletion_type,
            data_categories={"categories": deletion_req.data_categories}
            if deletion_req.data_categories
            else None,
            requested_at=datetime.now(UTC),
        )

        db.add(new_request)

        # Log action
        audit_log = KVKKAuditLog(
            id=str(uuid.uuid4()),
            user_id=current_user.sub,
            accessed_by=current_user.sub,
            action="data_deletion_requested",
            resource_type="user_data",
            resource_id=current_user.sub,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details={
                "request_id": new_request.id,
                "type": deletion_req.deletion_type,
                "reason": deletion_req.reason,
            },
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(new_request)

        logger.info(
            "data_deletion_requested",
            user_id=current_user.sub,
            request_id=new_request.id,
            deletion_type=deletion_req.deletion_type,
        )

        return new_request

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "data_deletion_request_error", user_id=current_user.sub, error=str(e)
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request data deletion",
        )


@router.get("/delete/requests", response_model=list[DeletionRequestResponse])
async def get_deletion_requests(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get all data deletion requests for current user"""
    try:
        stmt = (
            select(KVKKDataDeletionRequest)
            .where(KVKKDataDeletionRequest.user_id == current_user.sub)
            .order_by(KVKKDataDeletionRequest.requested_at.desc())
        )
        result = await db.execute(stmt)
        requests = result.scalars().all()

        return requests

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_deletion_requests_error", user_id=current_user.sub, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve deletion requests",
        )


@router.delete("/delete/{request_id}")
async def cancel_deletion_request(
    request_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Cancel pending deletion request"""
    try:
        # Find request
        stmt = select(KVKKDataDeletionRequest).where(
            KVKKDataDeletionRequest.id == request_id,
            KVKKDataDeletionRequest.user_id == current_user.sub,
            KVKKDataDeletionRequest.status == DeletionRequestStatus.PENDING,
        )
        result = await db.execute(stmt)
        deletion_request = result.scalar_one_or_none()

        if not deletion_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending deletion request not found",
            )

        # Delete request
        await db.delete(deletion_request)
        await db.commit()

        logger.info(
            "deletion_request_cancelled",
            user_id=current_user.sub,
            request_id=request_id,
        )

        return {"success": True, "message": "Deletion request cancelled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("cancel_deletion_error", request_id=request_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel deletion request",
        )


__all__ = ["router"]
