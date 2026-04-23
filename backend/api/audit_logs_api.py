"""
Audit Logs API
TASK 48.5: Audit log viewer and export

Admin-only endpoints for viewing and exporting audit logs.
"""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from core.audit_logging import AuditEventType, AuditLog
from core.database import get_db
from core.dependencies import AuthenticatedUser, get_current_admin_user

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin - Audit Logs"])


class AuditLogResponse(BaseModel):
    """Audit log response model"""

    id: int
    timestamp: datetime
    event_type: str
    severity: str
    user_id: str | None
    user_email: str | None
    user_role: str | None
    ip_address: str | None
    resource_type: str | None
    resource_id: str | None
    action: str | None
    description: str | None
    success: str
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Audit log list response"""

    total: int
    page: int
    per_page: int
    logs: list[AuditLogResponse]


class AuditStatsResponse(BaseModel):
    """Audit statistics response"""

    total_events: int
    total_users: int
    events_by_type: dict
    events_by_severity: dict
    login_failures_24h: int
    security_events_24h: int


@router.get("/", response_model=AuditLogListResponse)
def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    event_type: str | None = None,
    user_id: str | None = None,
    severity: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    Get audit logs with filtering and pagination

    **Admin only endpoint**

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50, max: 500)
        - event_type: Filter by event type
        - user_id: Filter by user ID
        - severity: Filter by severity (info, warning, error, critical)
        - start_date: Filter from this date
        - end_date: Filter until this date
        - search: Search in description and user email
    """
    query = db.query(AuditLog)

    # Apply filters
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if severity:
        query = query.filter(AuditLog.severity == severity)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (AuditLog.description.ilike(search_filter))
            | (AuditLog.user_email.ilike(search_filter))
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    logs = (
        query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(per_page).all()
    )

    return AuditLogListResponse(
        total=total,
        page=page,
        per_page=per_page,
        logs=[AuditLogResponse.from_orm(log) for log in logs],
    )


@router.get("/stats", response_model=AuditStatsResponse)
def get_audit_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    Get audit statistics

    **Admin only endpoint**

    Query Parameters:
        - days: Number of days to analyze (default: 7, max: 90)
    """
    start_date = datetime.now(UTC) - timedelta(days=days)

    # Total events
    total_events = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.timestamp >= start_date)
        .scalar()
    )

    # Unique users
    total_users = (
        db.query(func.count(func.distinct(AuditLog.user_id)))
        .filter(and_(AuditLog.timestamp >= start_date, AuditLog.user_id.isnot(None)))
        .scalar()
    )

    # Events by type
    events_by_type = {}
    type_results = (
        db.query(AuditLog.event_type, func.count(AuditLog.id))
        .filter(AuditLog.timestamp >= start_date)
        .group_by(AuditLog.event_type)
        .all()
    )

    for event_type, count in type_results:
        events_by_type[event_type] = count

    # Events by severity
    events_by_severity = {}
    severity_results = (
        db.query(AuditLog.severity, func.count(AuditLog.id))
        .filter(AuditLog.timestamp >= start_date)
        .group_by(AuditLog.severity)
        .all()
    )

    for severity, count in severity_results:
        events_by_severity[severity] = count

    # Login failures in last 24h
    login_failures_24h = (
        db.query(func.count(AuditLog.id))
        .filter(
            and_(
                AuditLog.timestamp >= datetime.now(UTC) - timedelta(hours=24),
                AuditLog.event_type == AuditEventType.LOGIN_FAILURE.value,
            )
        )
        .scalar()
    )

    # Security events in last 24h
    security_events_24h = (
        db.query(func.count(AuditLog.id))
        .filter(
            and_(
                AuditLog.timestamp >= datetime.now(UTC) - timedelta(hours=24),
                AuditLog.event_type.like("security_%"),
            )
        )
        .scalar()
    )

    return AuditStatsResponse(
        total_events=total_events,
        total_users=total_users,
        events_by_type=events_by_type,
        events_by_severity=events_by_severity,
        login_failures_24h=login_failures_24h,
        security_events_24h=security_events_24h,
    )


@router.get("/export")
def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|json)$"),
    event_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    Export audit logs

    **Admin only endpoint**

    Query Parameters:
        - format: Export format (csv or json)
        - event_type: Filter by event type
        - start_date: Filter from this date
        - end_date: Filter until this date

    Returns:
        File download (CSV or JSON)
    """
    import csv
    import io

    from fastapi.responses import StreamingResponse

    query = db.query(AuditLog)

    # Apply filters
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)

    logs = query.order_by(AuditLog.timestamp.desc()).limit(10000).all()  # Limit to 10k

    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Timestamp",
                "Event Type",
                "Severity",
                "User ID",
                "User Email",
                "IP Address",
                "Resource Type",
                "Resource ID",
                "Action",
                "Description",
                "Success",
                "Error Message",
            ]
        )

        # Data
        for log in logs:
            writer.writerow(
                [
                    log.timestamp.isoformat(),
                    log.event_type,
                    log.severity,
                    log.user_id or "",
                    log.user_email or "",
                    log.ip_address or "",
                    log.resource_type or "",
                    log.resource_id or "",
                    log.action or "",
                    log.description or "",
                    log.success,
                    log.error_message or "",
                ]
            )

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )

    # JSON format
    import json

    data = [
        {
            "timestamp": log.timestamp.isoformat(),
            "event_type": log.event_type,
            "severity": log.severity,
            "user_id": log.user_id,
            "user_email": log.user_email,
            "ip_address": log.ip_address,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "action": log.action,
            "description": log.description,
            "success": log.success,
            "error_message": log.error_message,
            "metadata": log.metadata,
        }
        for log in logs
    ]

    return StreamingResponse(
        iter([json.dumps(data, indent=2)]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        },
    )


@router.delete("/cleanup")
def cleanup_old_logs(
    days: int = Query(90, ge=30, le=365),
    db: Session = Depends(get_db),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    Delete audit logs older than specified days

    **Admin only endpoint**
    **WARNING:** This action cannot be undone!

    Query Parameters:
        - days: Delete logs older than this many days (minimum: 30, default: 90)

    Returns:
        Number of deleted records
    """
    cutoff_date = datetime.now(UTC) - timedelta(days=days)

    deleted_count = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()

    db.commit()

    return {
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat(),
        "message": f"Deleted {deleted_count} audit log(s) older than {days} days",
    }
