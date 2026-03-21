"""
Sentry Error Tracking Demo Endpoints - Sprint 12
Demonstrates error tracking and monitoring capabilities

Examples show:
- Automatic error capture
- Manual error reporting
- Error categorization
- User context enrichment
- Business operation tracking
- Breadcrumbs for debugging
- Performance monitoring
"""
import random
import asyncio
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import AuthenticatedUser, get_current_user
from pydantic import BaseModel
from sentry_sdk import capture_exception, capture_message, add_breadcrumb, set_user, set_tag

from core.sentry_middleware import track_business_operation, capture_categorized_error

router = APIRouter(prefix="/api/v1/sentry-demo", tags=["Sentry Error Tracking Demo"])


# ==================== MODELS ====================


class ErrorTestRequest(BaseModel):
    """Error test request"""
    error_type: str = "generic"
    message: str = "Test error"
    user_id: Optional[str] = None


# ==================== AUTOMATIC ERROR CAPTURE ====================


@router.get("/automatic-error")
async def automatic_error_capture() -> Dict:
    """
    Automatic error capture example

    Sentry middleware automatically captures unhandled exceptions.
    Check Sentry dashboard for the error report.
    """
    # Add breadcrumb before error
    add_breadcrumb(
        message="User triggered automatic error test",
        category="test",
        level="info"
    )

    # Trigger error
    raise ValueError("This is an automatically captured error!")


@router.get("/http-error/{status_code}")
async def http_error_example(status_code: int) -> Dict:
    """
    HTTP error capture example

    Demonstrates automatic capture of HTTP exceptions.
    """
    add_breadcrumb(
        message=f"User requested HTTP error {status_code}",
        category="test",
        level="info"
    )

    raise HTTPException(status_code=status_code, detail=f"HTTP {status_code} error for testing")


# ==================== MANUAL ERROR CAPTURE ====================


@router.post("/manual-error")
async def manual_error_capture(request: ErrorTestRequest) -> Dict:
    """
    Manual error capture example

    Demonstrates manual error reporting with custom context.
    """
    try:
        # Simulate operation
        add_breadcrumb(
            message="Starting manual error test",
            category="test",
            level="info",
            data={"error_type": request.error_type}
        )

        # Create error based on type
        if request.error_type == "database":
            raise Exception("Database connection failed")
        elif request.error_type == "network":
            raise ConnectionError("Network timeout")
        elif request.error_type == "validation":
            raise ValueError("Invalid input data")
        else:
            raise Exception(request.message)

    except Exception as e:
        # Manually capture with context
        capture_exception(e)

        return {
            "status": "error_captured",
            "error_type": type(e).__name__,
            "message": "Error has been reported to Sentry",
            "sentry_dashboard": "Check your Sentry dashboard for details"
        }


@router.post("/categorized-error")
async def categorized_error_capture(request: ErrorTestRequest) -> Dict:
    """
    Categorized error capture example

    Demonstrates automatic error categorization.
    """
    try:
        # Simulate operation with breadcrumbs
        add_breadcrumb(
            message="Starting categorized error test",
            category="test",
            level="info"
        )

        # Create error
        if request.error_type == "database":
            error = Exception("DatabaseError: Connection pool exhausted")
        elif request.error_type == "auth":
            error = PermissionError("User not authorized")
        elif request.error_type == "validation":
            error = ValueError("Invalid email format")
        else:
            error = Exception(request.message)

        raise error

    except Exception as e:
        # Capture with automatic categorization
        capture_categorized_error(
            e,
            user_id=request.user_id,
            operation="error_demo",
            extra_info="This is a test error"
        )

        return {
            "status": "error_captured",
            "error_type": type(e).__name__,
            "message": "Error categorized and reported to Sentry"
        }


# ==================== USER CONTEXT ====================


@router.get("/user-context-error/{user_id}")
async def user_context_error(
    user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict:
    """
    Error with user context

    Demonstrates error tracking with user information.
    """
    # Set user context
    set_user({
        "id": user_id,
        "username": f"test_user_{user_id}",
        "role": "student"
    })

    # Add user activity breadcrumbs
    add_breadcrumb(
        message="User navigated to dashboard",
        category="navigation",
        level="info"
    )

    add_breadcrumb(
        message="User clicked on exam",
        category="user_action",
        level="info"
    )

    # Trigger error
    raise Exception(f"Error occurred for user {user_id}")


# ==================== BUSINESS OPERATION TRACKING ====================


@track_business_operation("exam_submission")
async def process_exam_submission(exam_id: str, user_id: str) -> Dict:
    """
    Simulated exam submission with error tracking

    Business operation is automatically tracked in Sentry.
    """
    # Add breadcrumbs for business logic steps
    add_breadcrumb(
        message="Validating exam data",
        category="business",
        level="info",
        data={"exam_id": exam_id, "user_id": user_id}
    )

    await asyncio.sleep(0.1)

    add_breadcrumb(
        message="Calculating exam score",
        category="business",
        level="info"
    )

    await asyncio.sleep(0.1)

    # Simulate random error (20% chance)
    if random.random() < 0.2:
        add_breadcrumb(
            message="Score calculation failed",
            category="error",
            level="error"
        )
        raise ValueError("Score calculation failed: Invalid answer format")

    add_breadcrumb(
        message="Exam submission completed",
        category="business",
        level="info"
    )

    return {
        "exam_id": exam_id,
        "user_id": user_id,
        "status": "completed",
        "score": random.randint(60, 100)
    }


@router.post("/exam-submission/{exam_id}")
async def submit_exam(exam_id: str, user_id: str = Query(...)) -> Dict:
    """
    Exam submission with business operation tracking

    Demonstrates error tracking in business operations.
    """
    try:
        result = await process_exam_submission(exam_id, user_id)
        return {
            **result,
            "message": "Check Sentry for business operation tracking"
        }
    except Exception as e:
        capture_exception(e)
        return {
            "status": "error",
            "message": "Exam submission failed - error reported to Sentry"
        }


# ==================== BREADCRUMBS ====================


@router.get("/breadcrumbs-demo")
async def breadcrumbs_demo() -> Dict:
    """
    Breadcrumbs demonstration

    Shows how breadcrumbs provide context for errors.
    """
    # Step 1: User logs in
    add_breadcrumb(
        message="User logged in",
        category="auth",
        level="info",
        data={"user_id": "user_123"}
    )

    await asyncio.sleep(0.05)

    # Step 2: User navigates
    add_breadcrumb(
        message="User navigated to exam list",
        category="navigation",
        level="info"
    )

    await asyncio.sleep(0.05)

    # Step 3: User selects exam
    add_breadcrumb(
        message="User selected exam",
        category="user_action",
        level="info",
        data={"exam_id": "tyt_2024"}
    )

    await asyncio.sleep(0.05)

    # Step 4: Load exam data
    add_breadcrumb(
        message="Loading exam data",
        category="database",
        level="info"
    )

    await asyncio.sleep(0.05)

    # Step 5: Error occurs
    add_breadcrumb(
        message="Exam data loading failed",
        category="error",
        level="error"
    )

    # Trigger error
    raise Exception("Failed to load exam data - check breadcrumbs in Sentry for full context")


# ==================== CUSTOM MESSAGES ====================


@router.post("/custom-message")
async def custom_message(
    message: str = Query(...),
    level: str = Query("info", regex="^(debug|info|warning|error|fatal)$")
) -> Dict:
    """
    Custom message capture

    Send custom messages to Sentry (not errors).
    """
    # Add context
    set_tag("message_source", "demo_endpoint")

    # Capture message
    capture_message(message, level=level)

    return {
        "status": "message_captured",
        "message": message,
        "level": level,
        "sentry_dashboard": "Check Sentry dashboard for the message"
    }


# ==================== PERFORMANCE MONITORING ====================


@router.get("/slow-operation")
async def slow_operation() -> Dict:
    """
    Slow operation for performance monitoring

    Sentry tracks operation duration in performance monitoring.
    """
    # Simulate slow operation
    add_breadcrumb(
        message="Starting slow operation",
        category="performance",
        level="info"
    )

    # Multiple slow steps
    for i in range(5):
        add_breadcrumb(
            message=f"Processing step {i + 1}/5",
            category="performance",
            level="info"
        )
        await asyncio.sleep(0.5)

    return {
        "status": "completed",
        "duration": "~2.5 seconds",
        "message": "Check Sentry Performance for transaction details"
    }


# ==================== ERROR STATISTICS ====================


@router.get("/error-stats")
async def error_statistics() -> Dict:
    """
    Simulated endpoint with multiple error types

    Generates various errors for statistics demonstration.
    """
    error_type = random.choice([
        "database",
        "network",
        "validation",
        "auth",
        "success"
    ])

    add_breadcrumb(
        message=f"Simulating {error_type} scenario",
        category="test",
        level="info"
    )

    if error_type == "database":
        raise Exception("DatabaseError: Connection timeout")
    elif error_type == "network":
        raise ConnectionError("Network error: Unable to reach external service")
    elif error_type == "validation":
        raise ValueError("Validation error: Invalid input format")
    elif error_type == "auth":
        raise PermissionError("Authentication error: Invalid credentials")
    else:
        return {
            "status": "success",
            "message": "Operation completed successfully"
        }


# ==================== INFO ENDPOINT ====================


@router.get("/")
async def sentry_demo_info() -> Dict:
    """
    Sentry Error Tracking Demo Information

    All endpoints demonstrate different Sentry features.
    Check your Sentry dashboard after calling these endpoints.
    """
    return {
        "title": "Sprint 12: Sentry Error Tracking Demo",
        "sentry_dashboard": "https://sentry.io/organizations/your-org/projects/kiro2/",
        "examples": {
            "automatic_errors": [
                "GET /api/sentry-demo/automatic-error",
                "GET /api/sentry-demo/http-error/500",
            ],
            "manual_capture": [
                "POST /api/sentry-demo/manual-error",
                "POST /api/sentry-demo/categorized-error",
            ],
            "user_context": [
                "GET /api/sentry-demo/user-context-error/{user_id}",
            ],
            "business_operations": [
                "POST /api/sentry-demo/exam-submission/{exam_id}?user_id=user_123",
            ],
            "breadcrumbs": [
                "GET /api/sentry-demo/breadcrumbs-demo",
            ],
            "custom_messages": [
                "POST /api/sentry-demo/custom-message?message=Test&level=info",
            ],
            "performance": [
                "GET /api/sentry-demo/slow-operation",
            ],
            "statistics": [
                "GET /api/sentry-demo/error-stats (call multiple times)",
            ],
        },
        "setup": {
            "step1": "Set SENTRY_DSN environment variable",
            "step2": "Restart backend: uvicorn main:app --reload",
            "step3": "Call demo endpoints",
            "step4": "Check Sentry dashboard for errors and performance data",
        },
        "features": {
            "automatic": "All errors automatically captured",
            "manual": "Manual error reporting with context",
            "categorization": "Automatic error categorization",
            "user_context": "User information in error reports",
            "breadcrumbs": "Step-by-step error context",
            "performance": "Transaction performance monitoring",
            "releases": "Release tracking and version comparison",
        },
    }
