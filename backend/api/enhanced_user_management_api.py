"""
Enhanced User Management API - Using New Error Handling System
Demonstrates the new centralized error handling pattern consolidation

SPRINT 3 UPDATE: Email operations now use Celery background tasks
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from core.error_context import (
    SpanKind,
    add_database_query_to_context,
    annotate_error_context,
    async_error_context,
    error_context_decorator,
    trace_operation,
    tracing_span,
)
from core.error_monitoring import log_error, reset_consecutive_errors

# Import new error handling system
from core.exceptions import (
    BusinessLogicError,
    DatabaseError,
    EnhancedServiceError,
    ErrorFactory,
    ErrorSeverity,
    NotFoundError,
    ValidationError,
)
from core.response_models import (
    PaginatedResponse,
    SuccessResponse,
    turkish_success_response,
)
from models.database import StudentProfile, User
from models.gamification_db import ManipulativeProgress
from models.user import UserCreate

# SPRINT 3: Celery task imports
from tasks.email_tasks import send_welcome_email


# UserResponse placeholder
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    is_active: bool


from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from services.user_service import KullaniciServisi as UserService

router = APIRouter(prefix="/api/v1/users", tags=["Enhanced User Management"])


# ==================== ENHANCED DEPENDENCIES ====================


@error_context_decorator("user_authorization_check")
async def require_admin_or_self(
    user_id: str, current_user: User = Depends(get_current_user)
) -> User:
    """Enhanced authorization check with error context"""

    # Add context annotations
    annotate_error_context(f"Checking authorization for user {user_id}")

    # Check if user is admin or accessing their own data
    if current_user.role in ["admin", "super_admin"]:
        annotate_error_context("Admin access granted")
        return current_user

    if current_user.id == user_id:
        annotate_error_context("Self-access granted")
        return current_user

    # Use enhanced error with proper severity and context
    raise EnhancedServiceError(
        message=f"Insufficient permissions to access user {user_id}",
        error_code="AUTHORIZATION_ERROR",
        severity=ErrorSeverity.MEDIUM,
        user_message="Bu kullanıcının bilgilerine erişim yetkiniz yok",
        correlation_id=None,  # Will be set by context manager
        source_location=None,  # Will be auto-detected
        previous_error=None,
    )


@trace_operation("admin_check", SpanKind.INTERNAL)
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Enhanced admin check with tracing"""

    if (current_user.role or "").lower() not in ["admin", "super_admin"]:
        # Use error factory for consistent error creation
        raise ErrorFactory.authorization_error(
            required_role="admin",
            user_role=current_user.role,
            resource="user_management",
            message="Bu işlem için admin yetkisi gereklidir",
        )

    return current_user


# ==================== ENHANCED API ENDPOINTS ====================


@router.get(
    "",
    response_model=PaginatedResponse[list[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı Listesi (Gelişmiş Hata Yönetimi)",
    description="Enhanced user listing with comprehensive error handling",
)
@error_context_decorator("list_users", capture_args=True)
@trace_operation("api.users.list", SpanKind.SERVER)
async def list_users_enhanced(
    request: Request,
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    page_size: int = Query(20, ge=1, le=100, description="Sayfa boyutu"),
    search: str | None = Query(None, description="Arama terimi"),
    role_filter: str | None = Query(None, description="Rol filtresi"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[list[UserResponse]]:
    """
    Enhanced user listing with comprehensive error handling

    Demonstrates:
    - Error context tracking
    - Distributed tracing
    - Database error handling
    - Performance monitoring
    - Automatic error recovery
    """

    async with async_error_context(
        operation_name="list_users_enhanced",
        entity_type="user",
        business_operation="user_listing",
    ) as ctx:
        # Add business context
        ctx.tags.update(
            {
                "operation": "list_users",
                "page": str(page),
                "page_size": str(page_size),
                "has_search": str(bool(search)),
                "has_role_filter": str(bool(role_filter)),
            }
        )

        # Validate input parameters with enhanced errors
        if page_size > 100:
            raise ErrorFactory.validation_error(
                field="page_size",
                value=page_size,
                constraint="max_value_100",
                message="Sayfa boyutu 100'den büyük olamaz",
            )

        # Initialize service with error handling
        try:
            from sqlalchemy import String, cast, func, or_, select
            query = select(User)
            count_query = select(func.count()).select_from(User)

            if search:
                search_filter = or_(
                    User.email.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                )
                query = query.where(search_filter)
                count_query = count_query.where(search_filter)

            if role_filter:
                query = query.where(
                    func.lower(cast(User.role, String)) == role_filter.lower()
                )
                count_query = count_query.where(
                    func.lower(cast(User.role, String)) == role_filter.lower()
                )

            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0

            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            users_result = await db.execute(query)
            db_users = users_result.scalars().all()

            result = {"users": db_users, "total": total}

            # Track database performance
            if hasattr(result, "query_time"):
                add_database_query_to_context(
                    query="SELECT * FROM users WHERE ...",
                    duration_ms=result.query_time * 1000,
                    table="users",
                    operation="select_paginated",
                )

            # Annotate successful operation
            annotate_error_context(
                f"Successfully retrieved {len(result['users'])} users"
            )

            # Reset consecutive errors on success
            reset_consecutive_errors()

            # Convert to response models
            user_responses = [
                UserResponse.model_validate(user, from_attributes=True)
                for user in result["users"]
            ]

            # Build paginated response
            from core.response_models import paginated_response

            return paginated_response(
                data=user_responses,
                page=page,
                page_size=page_size,
                total_items=result["total"],
                message=f"{len(user_responses)} kullanıcı listelendi",
                request_id=getattr(request.state, "request_id", None),
                filters_applied={"search": search, "role_filter": role_filter},
            )

        except DatabaseError as e:
            # Enhanced database error handling
            annotate_error_context("Database error occurred during user listing")

            # Add specific database context
            enhanced_error = EnhancedServiceError(
                message="Kullanıcı listesi veritabanından alınamadı",
                error_code="DATABASE_ERROR",
                severity=ErrorSeverity.HIGH,
                user_message="Sistem geçici olarak kullanılamıyor. Lütfen tekrar deneyin.",
                retry_after=30,
                correlation_id=ctx.correlation_id,
                previous_error=e,
            )
            enhanced_error.details.update(
                {
                    "operation": "list_users_paginated",
                    "table": "users",
                    "page": page,
                    "page_size": page_size,
                }
            )

            # Log error with full context
            await log_error(enhanced_error, ctx.to_dict(), ErrorSeverity.HIGH)

            raise enhanced_error

        except ValidationError as e:
            # Re-raise validation errors as-is (they're already enhanced)
            raise e

        except Exception as e:
            # Handle unexpected errors
            annotate_error_context(f"Unexpected error: {type(e).__name__}")

            # Wrap in enhanced service error
            enhanced_error = EnhancedServiceError(
                message="Kullanıcı listesi alınırken beklenmeyen hata oluştu",
                error_code="INTERNAL_SERVER_ERROR",
                severity=ErrorSeverity.HIGH,
                user_message="Sistem hatası oluştu. Teknik ekip bilgilendirildi.",
                correlation_id=ctx.correlation_id,
                previous_error=e,
            )

            await log_error(enhanced_error, ctx.to_dict(), ErrorSeverity.HIGH)
            raise enhanced_error


@router.post(
    "",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Kullanıcı Oluşturma (Gelişmiş Hata Yönetimi)",
    description="Enhanced user creation with comprehensive error handling",
)
@error_context_decorator("create_user", capture_args=True)
@trace_operation("api.users.create", SpanKind.SERVER)
async def create_user_enhanced(
    user_data: UserCreate, request: Request, current_user: User = Depends(require_admin)
) -> SuccessResponse[UserResponse]:
    """
    Enhanced user creation with comprehensive error handling

    Demonstrates:
    - Input validation with enhanced errors
    - Business logic error handling
    - Database transaction error handling
    - Email service error handling with fallback
    """

    with tracing_span("validate_user_creation_request", SpanKind.INTERNAL) as span:
        span.set_tag("user.email", user_data.email)
        span.set_tag("user.role", user_data.role)

        # Enhanced input validation
        if not user_data.email or "@" not in user_data.email:
            span.set_tag("validation.failed", "email")
            raise ErrorFactory.validation_error(
                field="email",
                value=user_data.email,
                constraint="email_format",
                message="Geçerli bir e-posta adresi giriniz",
            )

        if len(user_data.password) < 8:
            span.set_tag("validation.failed", "password")
            raise ErrorFactory.validation_error(
                field="password",
                value="[REDACTED]",  # Don't log actual password
                constraint="min_length_8",
                message="Şifre en az 8 karakter olmalıdır",
            )

    async with async_error_context(
        operation_name="create_user_enhanced",
        entity_type="user",
        entity_id=user_data.username,
        business_operation="user_creation",
    ) as ctx:
        ctx.tags.update(
            {
                "operation": "create_user",
                "user_email": user_data.email,
                "user_role": user_data.role,
                "created_by": current_user.id,
            }
        )

        user_service = UserService()

        try:
            # Check if user already exists (business logic validation)
            with tracing_span("check_user_exists", SpanKind.INTERNAL) as span:
                existing_user = await user_service.get_user_by_email(user_data.email)
                if existing_user:
                    span.set_tag("user_exists", True)
                    raise ErrorFactory.business_logic_error(
                        rule_name="unique_email",
                        context={
                            "email": user_data.email,
                            "existing_user_id": existing_user.id,
                        },
                        message="Bu e-posta adresi zaten kullanımda",
                    )
                span.set_tag("user_exists", False)

            # Create user with database transaction
            with tracing_span("create_user_database", SpanKind.INTERNAL) as db_span:
                db_span.set_tag("db.operation", "insert")
                db_span.set_tag("db.table", "users")

                start_time = datetime.now()
                new_user = await user_service.create_user(user_data)
                end_time = datetime.now()

                db_duration = (end_time - start_time).total_seconds() * 1000
                db_span.set_tag("db.duration_ms", db_duration)

                add_database_query_to_context(
                    query="INSERT INTO users (...) VALUES (...)",
                    duration_ms=db_duration,
                    table="users",
                    operation="create_user",
                )

                if not new_user:
                    raise DatabaseError(
                        message="Kullanıcı oluşturulamadı - veritabanı hatası",
                        operation="create_user",
                    )

            # Send welcome email (SPRINT 3: Using Celery background task)
            with tracing_span("send_welcome_email", SpanKind.CLIENT) as email_span:
                email_span.set_tag("email.recipient", user_data.email)

                try:
                    # SPRINT 3 OPTIMIZATION: Email sent in background (3s → 50ms)
                    # Fire-and-forget: doesn't block API response
                    task = send_welcome_email.delay(
                        user_email=new_user.email,
                        user_name=f"{new_user.ad} {new_user.soyad}",
                    )
                    email_span.set_tag("email.task_id", task.id)
                    email_span.set_tag("email.queued", True)
                    annotate_error_context(f"Welcome email queued (task_id: {task.id})")

                except Exception as email_error:
                    email_span.set_tag("email.sent", False)
                    email_span.set_tag("email.error", str(email_error))

                    # Log email error but don't fail user creation
                    await log_error(
                        email_error,
                        {**ctx.to_dict(), "email_recipient": user_data.email},
                        ErrorSeverity.LOW,
                    )
                    annotate_error_context(
                        "Welcome email failed - user created successfully"
                    )

            # Success - reset consecutive errors
            reset_consecutive_errors()

            user_response = UserResponse.from_orm(new_user)

            return turkish_success_response(
                data=user_response,
                message_key="data_created",
                custom_message=f"Kullanıcı {user_response.username} başarıyla oluşturuldu",
                request_id=getattr(request.state, "request_id", None),
            )

        except ValidationError as e:
            # Validation errors are already enhanced
            raise e

        except BusinessLogicError as e:
            # Business logic errors are already enhanced
            annotate_error_context(f"Business logic error: {e.message}")
            raise e

        except DatabaseError as e:
            # Enhance database error with context
            annotate_error_context("Database error during user creation")

            enhanced_error = EnhancedServiceError(
                message="Kullanıcı oluşturulamadı - veritabanı hatası",
                error_code="DATABASE_ERROR",
                severity=ErrorSeverity.HIGH,
                user_message="Kullanıcı oluşturulamadı. Lütfen tekrar deneyin.",
                retry_after=60,
                correlation_id=ctx.correlation_id,
                previous_error=e,
            )
            enhanced_error.details.update(
                {
                    "operation": "create_user",
                    "user_email": user_data.email,
                    "user_role": user_data.role,
                }
            )

            await log_error(enhanced_error, ctx.to_dict(), ErrorSeverity.HIGH)
            raise enhanced_error

        except Exception as e:
            # Handle any other unexpected errors
            annotate_error_context(
                f"Unexpected error during user creation: {type(e).__name__}"
            )

            enhanced_error = EnhancedServiceError(
                message="Kullanıcı oluşturma sırasında beklenmeyen hata oluştu",
                error_code="INTERNAL_SERVER_ERROR",
                severity=ErrorSeverity.HIGH,
                user_message="Sistem hatası oluştu. Teknik ekip bilgilendirildi.",
                correlation_id=ctx.correlation_id,
                previous_error=e,
            )

            await log_error(enhanced_error, ctx.to_dict(), ErrorSeverity.HIGH)
            raise enhanced_error


@router.get("/export-data")
async def export_user_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Export user data — real implementation.
    Frontend: ModernSettingsPage.tsx (calls response.blob() for download)
    """
    from sqlalchemy import select, text

    # Load full User from DB (get_current_user returns Pydantic AuthenticatedUser with limited fields)
    user_result = await db.execute(select(User).where(User.id == str(current_user.id)))
    db_user = user_result.scalar_one_or_none()

    # Load student profile if exists
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == str(current_user.id))
    )
    profile = profile_result.scalar_one_or_none()

    # Get gamification progress (manipulative tools)
    manip_result = await db.execute(
        select(ManipulativeProgress).where(
            ManipulativeProgress.user_id == str(current_user.id)
        )
    )
    manipulative_progress = manip_result.scalars().all()

    # Get learning progress daily (last 90 days)
    from datetime import timedelta

    ninety_days_ago = (datetime.now().astimezone() - timedelta(days=90)).date()
    lp_result = await db.execute(
        text("""
            SELECT log_date, subject, minutes_spent, questions_done, correct_count, activity_type
            FROM learning_progress_daily
            WHERE user_id = :user_id AND log_date >= :since
            ORDER BY log_date DESC
            LIMIT 500
        """),
        {"user_id": str(current_user.id), "since": ninety_days_ago},
    )
    learning_progress_rows = lp_result.fetchall()

    # Build export sections
    # Fall back to current_user fields when db_user not found
    export_user = db_user if db_user else current_user
    user_info = {
        "id": str(export_user.id),
        "email": export_user.email,
        "username": export_user.username,
        "first_name": getattr(export_user, "first_name", None),
        "last_name": getattr(export_user, "last_name", None),
        "role": export_user.role.value
        if hasattr(export_user.role, "value")
        else str(export_user.role),
        "is_premium": getattr(export_user, "is_premium", None),
        "created_at": export_user.created_at.isoformat()
        if getattr(export_user, "created_at", None)
        else None,
    }

    profile_info = None
    if profile:
        profile_info = {
            "grade_level": profile.grade_level,
            "school_name": profile.school_name,
            "target_university": profile.target_university,
            "target_department": profile.target_department,
            "learning_style": str(profile.learning_style.value)
            if profile.learning_style
            else None,
            "study_hours_per_day": profile.study_hours_per_day,
            "total_study_hours": profile.total_study_hours,
            "total_questions_solved": profile.total_questions_solved,
            "correct_answers": profile.correct_answers,
        }

    gamification = {
        "total_xp": getattr(export_user, "total_xp", None),
        "level": getattr(export_user, "level", None),
        "last_level_up_at": export_user.last_level_up_at.isoformat()
        if getattr(export_user, "last_level_up_at", None)
        else None,
        "manipulative_progress": [
            {
                "type": mp.manipulative_type,
                "activity_type": mp.activity_type,
                "operation_count": mp.operation_count,
                "completion_count": mp.completion_count,
                "total_duration_seconds": mp.total_duration_seconds,
                "mastery_level": mp.mastery_level,
            }
            for mp in manipulative_progress
        ],
    }

    study_progress = {
        "total_sessions": len(learning_progress_rows),
        "recent_sessions": [
            {
                "date": str(row.log_date),
                "subject": row.subject,
                "minutes_spent": row.minutes_spent,
                "questions_done": row.questions_done,
                "correct_count": row.correct_count,
                "activity_type": row.activity_type,
            }
            for row in learning_progress_rows
        ],
    }

    export_payload = {
        "exported_at": datetime.now().isoformat(),
        "user": user_info,
        "profile": profile_info,
        "gamification": gamification,
        "study_progress": study_progress,
    }

    return JSONResponse(content=export_payload)


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı Detayı (Gelişmiş Hata Yönetimi)",
    description="Enhanced user detail retrieval with comprehensive error handling",
)
@error_context_decorator("get_user_detail", capture_args=True)
@trace_operation("api.users.get_detail", SpanKind.SERVER)
async def get_user_detail_enhanced(
    user_id: str, request: Request, current_user: User = Depends(require_admin_or_self)
) -> SuccessResponse[UserResponse]:
    """
    Enhanced user detail retrieval with comprehensive error handling

    Demonstrates:
    - Resource not found handling
    - Authorization with context
    - Caching with error recovery
    """

    # Validate user ID format
    if not user_id or len(user_id) < 3:
        raise ErrorFactory.validation_error(
            field="user_id",
            value=user_id,
            constraint="min_length_3",
            message="Geçersiz kullanıcı ID formatı",
        )

    async with async_error_context(
        operation_name="get_user_detail_enhanced",
        entity_type="user",
        entity_id=user_id,
        business_operation="user_detail_retrieval",
    ) as ctx:
        ctx.tags.update(
            {
                "operation": "get_user_detail",
                "target_user_id": user_id,
                "requester_id": current_user.id,
                "requester_role": current_user.role,
            }
        )

        user_service = UserService()

        try:
            # Try to get user with caching
            with tracing_span("get_user_from_cache", SpanKind.INTERNAL) as cache_span:
                # Simulated cache check
                cached_user = None  # Would check cache here
                cache_span.set_tag("cache.hit", bool(cached_user))

                if cached_user:
                    annotate_error_context("User data retrieved from cache")
                    return turkish_success_response(
                        data=UserResponse.from_orm(cached_user),
                        custom_message="Kullanıcı bilgileri getirildi (önbellek)",
                        request_id=getattr(request.state, "request_id", None),
                    )

            # Get from database
            with tracing_span("get_user_from_database", SpanKind.INTERNAL) as db_span:
                db_span.set_tag("db.operation", "select")
                db_span.set_tag("db.table", "users")
                db_span.set_tag("user.id", user_id)

                start_time = datetime.now()
                user = await user_service.get_user_by_id(user_id)
                end_time = datetime.now()

                db_duration = (end_time - start_time).total_seconds() * 1000
                db_span.set_tag("db.duration_ms", db_duration)

                add_database_query_to_context(
                    query="SELECT * FROM users WHERE id = ?",
                    duration_ms=db_duration,
                    table="users",
                    operation="get_user_by_id",
                    user_id=user_id,
                )

                if not user:
                    db_span.set_tag("user.found", False)
                    raise ErrorFactory.not_found_error(
                        resource_type="user",
                        resource_id=user_id,
                        message="Kullanıcı bulunamadı",
                    )

                db_span.set_tag("user.found", True)

            # Success
            annotate_error_context("User data retrieved successfully from database")
            reset_consecutive_errors()

            user_response = UserResponse.from_orm(user)

            return turkish_success_response(
                data=user_response,
                custom_message="Kullanıcı bilgileri başarıyla getirildi",
                request_id=getattr(request.state, "request_id", None),
            )

        except NotFoundError as e:
            # Not found errors are already enhanced
            annotate_error_context(f"User not found: {user_id}")
            raise e

        except DatabaseError as e:
            # Database error handling
            annotate_error_context("Database error during user retrieval")

            enhanced_error = EnhancedServiceError(
                message="Kullanıcı bilgileri alınamadı - veritabanı hatası",
                error_code="DATABASE_ERROR",
                severity=ErrorSeverity.HIGH,
                user_message="Kullanıcı bilgileri şu anda alınamıyor. Lütfen tekrar deneyin.",
                retry_after=30,
                correlation_id=ctx.correlation_id,
                previous_error=e,
            )
            enhanced_error.details.update(
                {"operation": "get_user_by_id", "user_id": user_id}
            )

            await log_error(enhanced_error, ctx.to_dict(), ErrorSeverity.HIGH)
            raise enhanced_error

        except Exception as e:
            # Handle unexpected errors
            annotate_error_context(
                f"Unexpected error during user retrieval: {type(e).__name__}"
            )

            enhanced_error = EnhancedServiceError(
                message="Kullanıcı bilgileri alınırken beklenmeyen hata oluştu",
                error_code="INTERNAL_SERVER_ERROR",
                severity=ErrorSeverity.MEDIUM,
                user_message="Sistem hatası oluştu. Lütfen tekrar deneyin.",
                correlation_id=ctx.correlation_id,
                previous_error=e,
            )

            await log_error(enhanced_error, ctx.to_dict(), ErrorSeverity.MEDIUM)
            raise enhanced_error


# ==================== ERROR MONITORING ENDPOINT ====================


@router.get(
    "/monitoring/health",
    response_model=SuccessResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Error Monitoring Health Check",
    description="Get error monitoring and system health status",
)
async def get_error_monitoring_health(
    request: Request, current_user: User = Depends(require_admin)
) -> SuccessResponse[dict[str, Any]]:
    """Get error monitoring and system health status"""

    from core.error_monitoring import get_health_status

    health_status = get_health_status()

    return turkish_success_response(
        data=health_status,
        custom_message="Sistem sağlık durumu başarıyla getirildi",
        request_id=getattr(request.state, "request_id", None),
    )
