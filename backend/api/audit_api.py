"""
Audit Log API Endpoints (Task 48.5)
Admin-only endpoints for viewing and managing audit logs

Features:
- View audit logs with filtering
- Search by user, action, resource
- Export audit logs
- Cleanup old logs
- Security event monitoring

Author: Claude
Date: 2025-10-27
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit_logger import (
    AuditAction,
    get_audit_logger,
)
from core.dependencies import get_db, get_current_admin_user
from core.structured_logger import get_logger
from models.database import AuditLog, User

logger = get_logger("audit_api")

router = APIRouter(prefix="/api/v1/audit", tags=["Audit Logs"])


class AuditLogResponse(BaseModel):
    """Audit log response model"""

    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    old_values: Optional[dict]
    new_values: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogSearchRequest(BaseModel):
    """Audit log search request"""

    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    limit: int = 100
    offset: int = 0


async def require_admin(
    credentials=Depends,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to require admin role

    Args:
        credentials: Authorization credentials
        db: Database session

    Returns:
        User: Admin user

    Raises:
        HTTPException: If user is not admin

    Note: This function is now deprecated. Use get_current_admin_user from core.dependencies instead.
    """
    # Use the proper admin authentication from core.dependencies
    from core.dependencies import get_current_admin_user as get_admin

    return await get_admin()


@router.get(
    "/logs",
    response_model=list[AuditLogResponse],
    summary="Get Audit Logs (Admin Only)",
)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    current_admin: dict = Depends(get_current_admin_user),
    start_date: Optional[datetime] = Query(
        None, description="Filter by start date (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter by end date (ISO format)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Max results (1-1000)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(require_admin),
):
    """
    Get audit logs with filtering (Task 48.5)

    Requires admin role. Returns filtered audit logs.

    Query Parameters:
    - user_id: Filter by user
    - action: Filter by action (e.g., 'auth.login', 'user.create')
    - resource_type: Filter by resource (e.g., 'user', 'exam', 'content')
    - resource_id: Filter by specific resource ID
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    - limit: Max results (default: 100)
    - offset: Pagination offset (default: 0)
    """
    try:
        # Convert AsyncSession to sync (temporary solution)
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        if not sync_db:
            raise HTTPException(status_code=500, detail="Database session unavailable")

        # Build query
        query = sync_db.query(AuditLog)

        # Apply filters
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        # Order by created_at descending
        query = query.order_by(AuditLog.created_at.desc())

        # Apply pagination
        logs = query.offset(offset).limit(limit).all()

        sync_db.close()

        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                old_values=log.old_values,
                new_values=log.new_values,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log in logs
        ]

    except Exception as e:
        logger.error(
            f"[AUDIT API] Failed to get audit logs: {e}",
            extra_data={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/logs/{log_id}",
    response_model=AuditLogResponse,
    summary="Get Single Audit Log (Admin Only)",
)
async def get_audit_log_by_id(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Get specific audit log by ID (Task 48.5)

    Requires admin role.
    """
    try:
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        if not sync_db:
            raise HTTPException(status_code=500, detail="Database session unavailable")

        log = sync_db.query(AuditLog).filter(AuditLog.id == log_id).first()

        sync_db.close()

        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit log {log_id} not found",
            )

        return AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            old_values=log.old_values,
            new_values=log.new_values,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[AUDIT API] Failed to get audit log {log_id}: {e}",
            extra_data={"log_id": log_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/user/{user_id}/trail",
    response_model=list[AuditLogResponse],
    summary="Get User Audit Trail",
)
async def get_user_audit_trail(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Get user's complete audit trail (Task 48.5)

    Requires admin role OR user requesting their own data (KVKK compliance).
    """
    try:
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        if not sync_db:
            raise HTTPException(status_code=500, detail="Database session unavailable")

        audit_logger = get_audit_logger(sync_db)
        logs_data = audit_logger.get_user_audit_trail(user_id, limit)

        sync_db.close()

        # Convert to response format
        return [
            AuditLogResponse(
                id="",
                user_id=user_id,
                action=log["action"],
                resource_type=log["resource_type"],
                resource_id=log["resource_id"],
                old_values=None,
                new_values=None,
                ip_address=log["ip_address"],
                user_agent=None,
                created_at=datetime.fromisoformat(log["created_at"]),
            )
            for log in logs_data
        ]

    except Exception as e:
        logger.error(
            f"[AUDIT API] Failed to get user audit trail: {e}",
            extra_data={"user_id": user_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/security-events", summary="Get Security Events (Admin Only)")
async def get_security_events(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Get security events (Task 48.5)

    Filters audit logs for security-related events.
    Requires admin role.
    """
    try:
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        if not sync_db:
            raise HTTPException(status_code=500, detail="Database session unavailable")

        # Security actions
        security_actions = [
            AuditAction.LOGIN_FAILED.value,
            AuditAction.PERMISSION_DENIED.value,
            AuditAction.SUSPICIOUS_ACTIVITY.value,
            AuditAction.DATA_BREACH_ATTEMPT.value,
            AuditAction.RATE_LIMIT_EXCEEDED.value,
        ]

        query = sync_db.query(AuditLog).filter(AuditLog.action.in_(security_actions))

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)

        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

        sync_db.close()

        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                old_values=log.old_values,
                new_values=log.new_values,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log in logs
        ]

    except Exception as e:
        logger.error(
            f"[AUDIT API] Failed to get security events: {e}",
            extra_data={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/cleanup", summary="Cleanup Old Audit Logs (Admin Only)")
async def cleanup_old_audit_logs(
    retention_days: int = Query(
        90, ge=30, le=365, description="Retention days (30-365)"
    ),
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Cleanup audit logs older than retention period (Task 48.5)

    Default retention: 90 days (KVKK compliance).
    Requires admin role.
    """
    try:
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        if not sync_db:
            raise HTTPException(status_code=500, detail="Database session unavailable")

        audit_logger = get_audit_logger(sync_db)
        deleted_count = audit_logger.cleanup_old_logs(retention_days)

        sync_db.close()

        return {
            "message": f"Successfully deleted {deleted_count} old audit logs",
            "deleted_count": deleted_count,
            "retention_days": retention_days,
        }

    except Exception as e:
        logger.error(
            f"[AUDIT API] Failed to cleanup old logs: {e}",
            extra_data={"error": str(e), "retention_days": retention_days},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/stats", summary="Get Audit Statistics (Admin Only)")
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(
        None, description="Start date for statistics"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Get audit log statistics (Task 48.5)

    Returns aggregated statistics:
    - Total logs
    - Logs by action
    - Logs by resource type
    - Security events count
    - Top users by activity

    Requires admin role.
    """
    try:
        from sqlalchemy import func
        from sqlalchemy.orm import Session

        sync_db = (
            Session(bind=db.bind.sync_engine)
            if hasattr(db.bind, "sync_engine")
            else None
        )

        if not sync_db:
            raise HTTPException(status_code=500, detail="Database session unavailable")

        # Base query
        query = sync_db.query(AuditLog)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        # Total logs
        total_logs = query.count()

        # Logs by action
        logs_by_action = (
            query.with_entities(AuditLog.action, func.count(AuditLog.id))
            .group_by(AuditLog.action)
            .all()
        )

        # Logs by resource type
        logs_by_resource = (
            query.with_entities(AuditLog.resource_type, func.count(AuditLog.id))
            .group_by(AuditLog.resource_type)
            .all()
        )

        # Top users
        top_users = (
            query.filter(AuditLog.user_id.isnot(None))
            .with_entities(AuditLog.user_id, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.user_id)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
            .all()
        )

        sync_db.close()

        return {
            "total_logs": total_logs,
            "logs_by_action": {action: count for action, count in logs_by_action},
            "logs_by_resource": {
                resource: count for resource, count in logs_by_resource
            },
            "top_users": [
                {"user_id": user_id, "activity_count": count}
                for user_id, count in top_users
            ],
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }

    except Exception as e:
        logger.error(
            f"[AUDIT API] Failed to get audit statistics: {e}",
            extra_data={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
