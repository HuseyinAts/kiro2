"""
KIRO2 Application Factory

FastAPI application factory pattern.
"""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from agents import initialize_agents, shutdown_agents
from core.config import settings
from core.database import db_manager
from core.openapi_config import (
    OPENAPI_METADATA,
    OPENAPI_SECURITY_SCHEMES,
    OPENAPI_SERVERS,
    OPENAPI_TAGS,
)
from routers.loader import setup_routers

# Rate limiting setup
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    Limiter = None

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan management.

    Startup ve shutdown event'lerini yönetir.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 KIRO2 Backend Starting...")
    logger.info(f"  Environment: {settings.environment}")
    logger.info(f"  Debug Mode: {settings.debug}")
    # S179 fix (B-P0-49): AGPL exposure warning. See
    # docs/compliance/AGPL_LICENSE_EXPOSURE.md. ultralytics + PyMuPDF
    # are AGPL-3.0; commercial production deployment without a
    import anyio
    try:
        limiter = anyio.to_thread.current_default_thread_limiter()
        limiter.total_tokens = 5000
        logger.info(f"✅ AnyIO thread pool expanded to {limiter.total_tokens} for high CCU sync endpoints")
    except Exception as e:
        logger.warning(f"⚠️ AnyIO thread pool expansion failed: {e}")
    # licensing decision risks copyleft trigger.
    import os as _os

    if _os.environ.get("ENVIRONMENT", "").lower() in (
        "production",
        "prod",
    ) and not _os.environ.get("KIRO2_LICENSE_DECISION"):
        logger.error(
            "[LICENSE][AGPL] ultralytics + PyMuPDF are AGPL-3.0; "
            "no KIRO2_LICENSE_DECISION env set in production. "
            "See docs/compliance/AGPL_LICENSE_EXPOSURE.md before going live."
        )

    # Initialize database connection
    await db_manager.initialize()
    logger.info("✅ Database initialized")

    # Connect JWT blacklist to Redis (graceful degradation if unavailable)
    try:
        from core.jwt_auth import get_jwt_manager

        jwt_mgr = get_jwt_manager()
        await jwt_mgr.connect_redis()
    except Exception as e:
        logger.warning(
            f"JWT Redis blacklist init failed (using in-memory fallback): {e}"
        )

    # Recover exam sessions from Redis L2 → L1 dict
    try:
        from core.exam_session_store import list_active_sessions
        from core.osym_exam_engine import osym_exam_engine

        recovered = await list_active_sessions()
        for session in recovered:
            osym_exam_engine.active_sessions[session.session_id] = session
        if recovered:
            logger.info(f"✅ Recovered {len(recovered)} exam sessions from Redis")
    except Exception as e:
        logger.warning(f"⚠️ Exam session recovery failed (non-fatal): {e}")

    # Orphan DB session recovery — in_progress kalan eski session'ları kapat
    try:
        from sqlalchemy import text

        from core.database import get_db_session_context

        async with get_db_session_context() as db:
            result = await db.execute(
                text("""
                    UPDATE exam_sessions
                    SET status = 'abandoned', updated_at = NOW()
                    WHERE status = 'in_progress'
                      AND updated_at < NOW() - INTERVAL '3 hours'
                    RETURNING id
                """)
            )
            abandoned = result.fetchall()
            await db.commit()
            if abandoned:
                logger.info(
                    f"🔧 Orphan session cleanup: {len(abandoned)} exam_sessions → abandoned"
                )
    except Exception as e:
        logger.warning(f"⚠️ Orphan session cleanup failed (non-fatal): {e}")

    # Initialize AI agents
    try:
        initialize_agents()
        logger.info("✅ AI agents initialized")
    except Exception as e:
        logger.warning(f"⚠️ Agent initialization failed (non-fatal): {e}")
        
    # Initialize CQRS Handlers
    try:
        from application.bootstrap import bootstrap_cqrs
        bootstrap_cqrs()
        logger.info("✅ CQRS Handlers initialized")
    except Exception as e:
        logger.warning(f"⚠️ CQRS initialization failed (non-fatal): {e}")

    # Register blackboard subscribers
    try:
        from services.blackboard_service import register_default_subscribers

        register_default_subscribers()
        logger.info("✅ Blackboard subscribers registered")
    except Exception as e:
        logger.warning(f"⚠️ Blackboard subscriber init failed (non-fatal): {e}")

    # Run ANALYZE on high-traffic tables so query planner has up-to-date stats.
    # Without this, a freshly populated question_bank (77K rows) shows n_live_tup=0
    # and last_analyze=NULL → planner ignores indexes → sequential scans everywhere.
    try:
        from sqlalchemy import text

        from core.database import get_db_session_context

        async with get_db_session_context() as db:
            await db.execute(text("ANALYZE question_bank, users, topic_prerequisites"))
            await db.commit()
        logger.info("✅ ANALYZE completed on question_bank, users, topic_prerequisites")
    except Exception as e:
        logger.warning(f"⚠️ ANALYZE failed (non-fatal, planner may be suboptimal): {e}")

    # Start IRT Daemon
    try:
        from core.irt_daemon import irt_daemon
        # DISABLED FOR LOAD TESTING: This daemon spawns heavy NLP threads
        # that hold the GIL and starve the asyncio event loop for HTTP requests.
        # await irt_daemon.start()
        logger.info("✅ IRT Daemon disabled for load testing stability")
    except Exception as e:
        logger.warning(f"⚠️ IRT Daemon startup failed (non-fatal): {e}")

    logger.info("✅ KIRO2 Backend Started Successfully!")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("🛑 KIRO2 Backend Shutting Down...")

    # Stop IRT Daemon
    try:
        from core.irt_daemon import irt_daemon
        await irt_daemon.stop()
        logger.info("✅ IRT Daemon stopped")
    except Exception as e:
        logger.error(f"Error stopping IRT Daemon: {e}")

    await shutdown_agents()
    logger.info("✅ AI agents shut down")

    # Close LLM client if it was initialized
    try:
        from core.llm_service import _llm_service

        if _llm_service is not None and hasattr(_llm_service, "close"):
            await _llm_service.close()
            logger.info("✅ LLM client closed")
    except Exception as e:
        logger.debug(f"LLM client close: {e}")

    await db_manager.close()
    logger.info("✅ Database closed")

    try:
        from core.cache.cache_manager import cache_manager

        if cache_manager is not None and hasattr(cache_manager, "close"):
            await cache_manager.close()
            logger.info("✅ Cache manager closed")
    except Exception as e:
        logger.debug(f"Cache manager close: {e}")

    # SRE Bulkhead: Shutdown worker pools
    try:
        from core.worker_pools import shutdown_pools
        shutdown_pools()
    except Exception as e:
        logger.error(f"Error shutting down SRE worker pools: {e}")

    logger.info("✅ KIRO2 Backend Shut Down Successfully!")


def setup_middleware(app: FastAPI) -> None:
    """
    Middleware setup.

    Tüm middleware'leri yapılandırır.
    Middleware sırası önemlidir (fastest first):
    1. Timing (ölçüm için en dışta)
    2. CORS (preflight handling)
    3. Cache Headers (ETag, If-None-Match)
    4. Compression (response sıkıştırma)

    Requirements: REQ-2.1.2, REQ-4.1.3, REQ-6.1.1
    """
    # 2. CORS Middleware
    # SECURITY: Validate production origins are configured
    localhost_only = all(
        "localhost" in o or "127.0.0.1" in o for o in settings.allowed_origins
    )
    if localhost_only:
        logger.warning(
            "⚠️ CORS: Only localhost origins configured. "
            "Set ALLOWED_ORIGINS env var for production (e.g. https://kiro2.com)"
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "X-CSRF-Token",
        ],
        expose_headers=["X-Response-Time", "X-Cache-Status", "ETag"],
    )
    logger.info(f"✅ CORS middleware added (origins: {len(settings.allowed_origins)})")

    # 3. Advanced Rate Limiters
    try:
        from core.auth_rate_limiting import AuthRateLimitMiddleware
        app.add_middleware(AuthRateLimitMiddleware)
        logger.info("✅ Auth Rate Limiting middleware added")
    except ImportError as e:
        logger.warning(f"⚠️ Auth rate limiter not available: {e}")

    try:
        from core.rate_limit_middleware import RateLimitMiddleware
        app.add_middleware(RateLimitMiddleware)
        logger.info("✅ Advanced Rate Limiting middleware added")
    except ImportError as e:
        logger.warning(f"⚠️ Advanced rate limiter not available: {e}")

    logger.info("✅ Middleware setup complete")


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Setup rate limiting with slowapi.

    Configures rate limit exception handler for 429 responses.
    Requirements: Plan Section 14.1 Task 1.4
    """
    if not SLOWAPI_AVAILABLE:
        logger.warning("⚠️ slowapi not available, rate limiting disabled")
        return

    # Create limiter instance
    limiter = Limiter(key_func=get_remote_address)

    # Store limiter in app state for access in decorators
    app.state.limiter = limiter

    # Add exception handler for rate limit exceeded
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    logger.info("✅ Rate limiting configured (slowapi)")


def create_app() -> FastAPI:
    """
    Application factory.

    FastAPI application instance'ı oluşturur ve yapılandırır.

    Returns:
        FastAPI: Yapılandırılmış FastAPI application
    """
    # Create FastAPI app with full OpenAPI configuration
    app = FastAPI(
        title=OPENAPI_METADATA["title"],
        description=OPENAPI_METADATA["description"],
        version=OPENAPI_METADATA["version"],
        contact=OPENAPI_METADATA.get("contact"),
        license_info=OPENAPI_METADATA.get("license_info"),
        terms_of_service=OPENAPI_METADATA.get("terms_of_service"),
        openapi_tags=OPENAPI_TAGS,
        servers=OPENAPI_SERVERS,
        debug=settings.debug,
        lifespan=app_lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Setup middleware
    setup_middleware(app)

    # Setup rate limiting
    setup_rate_limiting(app)

    # Global catch-all exception handler (prevent internal detail leaks)
    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        import sys
        import traceback
        sys.stderr.write("!!! EXCEPTION CAUGHT BY GLOBAL HANDLER !!!\n")
        sys.stderr.write(traceback.format_exc())
        sys.stderr.write("!!! END OF EXCEPTION !!!\n")
        
        # B-P0-52: Exception Swallowing. Bypass default HTTP & validation errors
        from fastapi.exception_handlers import (
            http_exception_handler,
            request_validation_exception_handler,
        )
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException as StarletteHTTPException

        if isinstance(exc, StarletteHTTPException):
            sys.stderr.write(f"!!! HTTP EXCEPTION CAUGHT: {exc.status_code} {exc.detail} !!!\n")
            sys.stderr.write(traceback.format_exc() + "\n")
            return await http_exception_handler(request, exc)
        if isinstance(exc, RequestValidationError):
            return await request_validation_exception_handler(request, exc)

        logger.error(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        if settings.debug:
            return JSONResponse(
                status_code=500,
                content={"detail": "Dahili sunucu hatasi", "error": str(exc)},
            )
        return JSONResponse(
            status_code=500,
            content={"detail": "Dahili sunucu hatasi"},
        )

    # Setup routers
    setup_routers(app)

    # Mount crop images as static files
    crop_dir = os.environ.get("CROP_IMAGE_DIR", "d-dataset/output/crops")
    if os.path.isdir(crop_dir):
        app.mount("/static/crops", StaticFiles(directory=crop_dir), name="crops")

    # Custom OpenAPI schema with security schemes
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=OPENAPI_TAGS,
            servers=OPENAPI_SERVERS,
            terms_of_service=app.terms_of_service,
            contact=app.contact,
            license_info=app.license_info,
        )

        # Add security schemes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        openapi_schema["components"]["securitySchemes"] = OPENAPI_SECURITY_SCHEMES

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Add root endpoint
    @app.get("/", tags=["Health & Monitoring"])
    async def root():
        """Root endpoint - Platform durumu."""
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "status": "online",
        }

    return app
