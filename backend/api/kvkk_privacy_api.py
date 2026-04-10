"""
KVKK Privacy Dashboard API
PHASE 2 Sprint 5: KVKK Compliance

Endpoints for:
- Data export (Right to Data Portability - KVKK Article 11)
- Data deletion (Right to Erasure - KVKK Article 7)
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
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

            # TODO: Implement actual data collection
            # For now, create a placeholder export
            user_data = {
                "user_id": user_id,
                "export_date": datetime.now(UTC).isoformat(),
                "format": export_format,
                "categories": data_categories or ["all"],
                "data": {"profile": {}, "exams": [], "progress": [], "consents": []},
            }

            # Simulated file creation
            file_path = f"/exports/{user_id}/{request_id}.{export_format}"
            download_url = f"https://api.kiro2.com/downloads/{request_id}"
            file_size = len(json.dumps(user_data).encode())
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
            db_url=str(settings.DATABASE_URL),
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
        logger.error("data_export_request_error", user_id=current_user.sub, error=str(e))
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

    except Exception as e:
        logger.error("get_export_requests_error", user_id=current_user.sub, error=str(e))
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
            "deletion_request_cancelled", user_id=current_user.sub, request_id=request_id
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
