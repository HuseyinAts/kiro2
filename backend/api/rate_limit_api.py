"""
Rate Limit Management API
PHASE 2 Sprint 6: Advanced Rate Limiting

Endpoints for:
- Checking rate limit status
- Admin rate limit management
- Rate limit statistics
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.advanced_rate_limiter import (
    UserTier,
    get_rate_limiter,
    resolve_user_tier_for_rate_limit,
)
from core.database import get_async_session
from core.jwt_auth import TokenPayload, get_current_user, require_admin
from core.rate_limit_middleware import get_rate_limit_status
from core.structured_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/rate-limit", tags=["Rate Limiting"])


# ============================================================================
# Response Models
# ============================================================================

class RateLimitStatusResponse(BaseModel):
    """Current rate limit status"""
    tier: str
    limit: int
    remaining: int
    reset: int
    reset_datetime: str
    window: int


class RateLimitConfigResponse(BaseModel):
    """Rate limit configuration for user tier"""
    tier: str
    limits: dict


class RateLimitResetResponse(BaseModel):
    """Rate limit reset confirmation"""
    success: bool
    message: str
    user_id: str | None = None
    endpoint: str | None = None


# ============================================================================
# User Endpoints
# ============================================================================

@router.get("/status", response_model=RateLimitStatusResponse)
async def get_current_rate_limit_status(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get current rate limit status

    Returns:
    - Current tier
    - Request limit for current endpoint
    - Remaining requests
    - Reset timestamp
    - Window duration

    Useful for displaying rate limit info in UI.
    """
    try:
        status_info = await get_rate_limit_status(request)
        return status_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_rate_limit_status_error", user_id=current_user.sub, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit status"
        )


@router.get("/config", response_model=RateLimitConfigResponse)
async def get_rate_limit_config(
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get rate limit configuration for user's tier

    Returns all rate limits applicable to user based on their tier.
    """
    try:
        limiter = get_rate_limiter()

        tier = resolve_user_tier_for_rate_limit(
            getattr(current_user, "role", None),
            is_premium=bool(getattr(current_user, "is_premium", False)),
        )

        # Get tier limits
        tier_limits = limiter.tier_limits.get(tier, limiter.tier_limits[UserTier.FREE])

        # Get endpoint-specific limits
        endpoint_limits = limiter.endpoint_limits

        return {
            "tier": tier.value,
            "limits": {
                "tier_limits": tier_limits,
                "endpoint_limits": endpoint_limits,
                "description": {
                    "default": "General API endpoints",
                    "auth": "Authentication endpoints (login, register, etc.)",
                    "export": "Data export and deletion endpoints",
                    "ai": "AI-powered features (chat, recommendations, etc.)"
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_rate_limit_config_error", user_id=current_user.sub, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit configuration"
        )


@router.get("/my-tier")
async def get_my_tier(
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get user's current tier

    Returns tier information and upgrade options.
    """
    try:
        tier = resolve_user_tier_for_rate_limit(
            getattr(current_user, "role", None),
            is_premium=bool(getattr(current_user, "is_premium", False)),
        )

        tier_info = {
            UserTier.FREE: {
                "name": "Ücretsiz",
                "description": "Temel özellikler",
                "requests_per_minute": 60,
                "can_upgrade": True
            },
            UserTier.PREMIUM: {
                "name": "Premium",
                "description": "Gelişmiş özellikler ve yüksek limit",
                "requests_per_minute": 300,
                "can_upgrade": False
            },
            UserTier.ADMIN: {
                "name": "Admin",
                "description": "Sınırsız erişim",
                "requests_per_minute": 10000,
                "can_upgrade": False
            }
        }

        return {
            "current_tier": tier.value,
            "tier_info": tier_info[tier],
            "upgrade_available": tier == UserTier.FREE
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_my_tier_error", user_id=current_user.sub, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tier information"
        )


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.post("/reset", response_model=RateLimitResetResponse)
async def reset_user_rate_limit(
    user_id: str,
    endpoint: str | None = None,
    current_user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Reset rate limit for specific user (Admin only)

    Args:
    - user_id: User ID to reset
    - endpoint: Specific endpoint (optional, resets all if not provided)

    Use cases:
    - Unblock user after false positive
    - Testing
    - Customer support
    """
    try:
        limiter = get_rate_limiter()

        # Determine tier for the user
        # (In real implementation, fetch user from DB)
        tier = UserTier.FREE  # Default, should be fetched from user record

        if endpoint:
            # Reset specific endpoint
            await limiter.reset_rate_limit(
                identifier=user_id,
                endpoint=endpoint,
                tier=tier
            )

            logger.info(
                "rate_limit_reset_by_admin",
                admin_id=current_user.sub,
                target_user_id=user_id,
                endpoint=endpoint
            )

            return {
                "success": True,
                "message": f"Rate limit reset for user {user_id} on endpoint {endpoint}",
                "user_id": user_id,
                "endpoint": endpoint
            }
        # Reset all endpoints for user
        # Get all endpoint patterns
        endpoints_to_reset = list(limiter.endpoint_limits.keys())

        for ep in endpoints_to_reset:
            await limiter.reset_rate_limit(
                identifier=user_id,
                endpoint=ep,
                tier=tier
            )

        logger.info(
            "rate_limit_full_reset_by_admin",
            admin_id=current_user.sub,
            target_user_id=user_id,
            endpoints_reset=len(endpoints_to_reset)
        )

        return {
            "success": True,
            "message": f"All rate limits reset for user {user_id}",
            "user_id": user_id,
            "endpoint": "all"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "reset_rate_limit_error",
            admin_id=current_user.sub,
            target_user_id=user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset rate limit"
        )


@router.get("/admin/statistics")
async def get_rate_limit_statistics(
    current_user: TokenPayload = Depends(require_admin)
):
    """
    Get rate limit statistics (Admin only)

    Returns:
    - Total rate limit violations
    - Top violators
    - Most limited endpoints
    - Tier distribution

    Note: This is a placeholder. Real implementation would
    query Redis or logging system for statistics.
    """
    try:
        # Placeholder statistics
        # Real implementation would aggregate from Redis/logs
        stats = {
            "period": "last_24_hours",
            "total_requests": 125000,
            "rate_limited_requests": 350,
            "rate_limit_percentage": 0.28,
            "top_endpoints": [
                {
                    "endpoint": "/api/v1/auth/login",
                    "violations": 120,
                    "limit": 5
                },
                {
                    "endpoint": "/api/v1/ai/chat",
                    "violations": 85,
                    "limit": 20
                },
                {
                    "endpoint": "/api/v1/kvkk/privacy/export",
                    "violations": 45,
                    "limit": 2
                }
            ],
            "tier_distribution": {
                "free": 245000,
                "premium": 78000,
                "admin": 2000
            }
        }

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_rate_limit_stats_error", admin_id=current_user.sub, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit statistics"
        )


__all__ = ["router"]
