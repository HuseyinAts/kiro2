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
    logger.info(f"  Database: {settings.database_url[:30]}...")

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

    logger.info("✅ KIRO2 Backend Started Successfully!")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("🛑 KIRO2 Backend Shutting Down...")
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
    # 1. Timing Middleware (en dışta - tüm request süresini ölçer)
    try:
        from core.middleware.timing import TimingMiddleware, get_timing_stats_manager

        app.add_middleware(
            TimingMiddleware,
            stats_manager=get_timing_stats_manager(),
            exclude_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"],
        )
        logger.info("✅ Timing middleware added")
    except ImportError as e:
        logger.warning(f"⚠️ Timing middleware not available: {e}")

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

    # 2.5. CSRF Protection Middleware
    # ANALIZ (02.04.2026): Phase 2 (X-CSRF-Token) GEREKSIZ.
    # Neden: auth cookie'ler samesite="lax" + httponly=True kullanıyor.
    # SameSite=Lax: cross-site POST/AJAX isteklerinde cookie gönderilmez
    #   → CSRF saldırıları zaten başarısız olur.
    # API JSON tabanlı (form submit değil) → klasik CSRF de geçersiz.
    # 80+ dosya X-CSRF-Token göndermek için değiştirilmek zorunda kalmaz.
    # Middleware devrede ama /api/v1/ exempt — bu yeterli.
    try:
        from core.csrf_protection import CSRFProtectionMiddleware

        app.add_middleware(
            CSRFProtectionMiddleware,
            exempt_paths=[
                "/api/v1/",  # SameSite=Lax zaten koruyor — exempt kalabilir
                "/docs",
                "/redoc",
                "/openapi.json",
                "/health",
            ],
        )
        logger.info("✅ CSRF middleware aktif (SameSite=Lax birincil koruma)")
    except ImportError as e:
        logger.warning(f"⚠️ CSRF middleware not available: {e}")

    # 3. Cache Headers Middleware (ETag, If-None-Match)
    try:
        from core.middleware.cache_headers import CacheMiddleware

        app.add_middleware(
            CacheMiddleware,
            skip_paths=["/health", "/metrics", "/docs", "/api/v1/auth"],
            enable_metrics=True,
        )
        logger.info("✅ Cache headers middleware added")
    except ImportError as e:
        logger.warning(f"⚠️ Cache headers middleware not available: {e}")

    # 4. GZip Compression Middleware
    try:
        from core.middleware.compression import GZipMiddleware

        app.add_middleware(
            GZipMiddleware,
            minimum_size=1000,  # 1KB minimum
            compression_level=6,  # Balance speed/size
        )
        logger.info("✅ GZip compression middleware added")
    except ImportError as e:
        logger.warning(f"⚠️ Compression middleware not available: {e}")

    # 5. Version Redirect Middleware (legacy /api/xxx → /api/v1/xxx)
    try:
        from core.middleware.version_redirect import VersionRedirectMiddleware

        app.add_middleware(VersionRedirectMiddleware)
        logger.info("✅ Version redirect middleware added")
    except ImportError as e:
        logger.warning(f"⚠️ Version redirect middleware not available: {e}")

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
        logger.error(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
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
