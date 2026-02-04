"""
Trkiye niversite Snavlar Hazrlk Platformu - Ana Uygulama
FastAPI tabanl backend servisi
"""
import sys
import io
from pathlib import Path

# UTF-8 encoding fix for Windows (fixes emoji and Turkish character issues in console)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# sys.path fix - QUICK FIX for import issues
# Add backend directory to Python path so routers can import from core, models, etc.
backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
    print(f"[QUICK FIX] Backend path added to sys.path: {backend_path}")

import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Trke karakter destei iin UTF-8 encoding
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
# Windows konsolu iin encoding ayar
os.environ.setdefault("PYTHONLEGACYWINDOWSSTDIO", "utf-8")

from core.logging_config import setup_production_logging
from core.logging_middleware import setup_logging_middleware

# Structured Logging Setup
from core.structured_logger import get_logger

# Production logging'i balat
setup_production_logging()

# SECURITY FIX: Global sensitive data filtering
from core.sensitive_data_filter import setup_global_sensitive_data_filter

# ✅ KVKK/GDPR Compliance: Enable email and phone redaction in logs
setup_global_sensitive_data_filter(redact_email=True, redact_phone=True)

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama balatma ve kapatma olaylar"""
    logger.info(
        "[ROCKET] Trkiye niversite Snavlar Hazrlk Platformu balatlyor...",
        extra_data={"component": "startup", "version": "1.0.0"},
    )

    # Redis Cache Manager' balat
    try:
        from core.cache import cache_manager

        # Ana cache manager' balat
        cache_success = await cache_manager.initialize()
        if cache_success:
            logger.info("[OK] Redis Cache Manager balatld")
        else:
            logger.warning("[WARNING] Redis Cache Manager fallback modda alyor")

    except Exception as e:
        logger.error(f"[ERROR] Redis Cache balatma hatas: {e}")

    # SPRINT 6: Advanced Rate Limiter' balat
    try:
        from core.advanced_rate_limiter import get_rate_limiter

        rate_limiter = get_rate_limiter()
        await rate_limiter.connect()
        logger.info("[OK] Sprint 6: Advanced Rate Limiter (Redis) balatld")
    except Exception as e:
        logger.error(f"[ERROR] Advanced Rate Limiter balatma hatas: {e}")

    # Database balantsn balat
    try:
        from core.database import init_database

        await init_database()
        logger.info("[OK] Database balants balatld")
    except Exception as e:
        logger.error(f"[ERROR] Database balatma hatas: {e}")

    # TASK 16: Startup Health Check (Requirements 0.1, 0.2, 0.6, 0.7, 1.9, 4.6, 4.9)
    try:
        from services.health_check_service import get_health_check_service

        logger.info("[HOSPITAL] Sistem başlangıç sağlık kontrolü yapılıyor...")
        health_service = get_health_check_service()
        startup_result = await health_service.startup_health_check()

        # Store health service in app state for later use
        app.state.health_service = health_service

        # Log summary based on result
        if startup_result.success:
            logger.info(
                f"[OK] [HOSPITAL] Sistem başlangıç sağlık kontrolü BAŞARILI - "
                f"{len([c for c in startup_result.components if c.status.value == 'healthy'])}/{len(startup_result.components)} servis healthy"
            )
        else:
            logger.warning(
                f"[WARNING] [HOSPITAL] Sistem başlangıç sağlık kontrolü UYARI - "
                f"Bazı servisler erişilebilir değil ancak uygulama başlatılıyor"
            )

        # Log warnings and errors if any
        if startup_result.warnings:
            for warning in startup_result.warnings:
                logger.warning(f"[WARNING] Startup: {warning}")

        if startup_result.errors:
            for error in startup_result.errors:
                logger.error(f"[ERROR] Startup: {error}")

    except Exception as e:
        logger.error(f"[ERROR] Startup health check failed: {e}")
        logger.warning("[WARNING] Uygulama health check olmadan başlatılıyor")

    # P1.4: Initialize Learning Path Circuit Breakers
    try:
        from core.learning_path_circuit_breakers import (
            initialize_learning_path_circuit_breakers,
        )

        initialize_learning_path_circuit_breakers()
        logger.info(
            "[OK] [SHIELD] Learning Path Circuit Breakers initialized - Cascading failure protection active"
        )
    except Exception as e:
        logger.error(f"[ERROR] Circuit Breaker initialization failed: {e}")
        logger.warning(
            "[WARNING] Application starting without circuit breaker protection"
        )

    # Performance tracking balat
    try:
        from core.performance_middleware import system_monitor

        system_monitor.start_monitoring(interval=30)
        logger.info("[OK] System Performance Monitor balatld")
    except Exception as e:
        logger.error(f"[ERROR] Performance Monitor balatma hatas: {e}")

    # Revolutionary features optimizer balat
    try:
        from core.revolutionary_optimizer import optimize_all_revolutionary_features

        await optimize_all_revolutionary_features()
        logger.info("[OK] Revolutionary Features Optimizer balatld")
    except Exception as e:
        logger.error(f"[ERROR] Revolutionary Optimizer balatma hatas: {e}")

    # Database performance indexes olutur
    try:
        from core.database import get_async_session
        from core.database_optimizer import create_performance_indexes

        async with get_async_session() as session:
            await create_performance_indexes(session)
        logger.info("[OK] Database Performance Indexes oluturuldu")
    except Exception as e:
        logger.error(f"[ERROR] Database Indexes oluturma hatas: {e}")

    # Monitoring servislerini balat
    try:
        from core.monitoring import monitoring_service

        await monitoring_service.start()
        logger.info("[OK] Advanced monitoring service balatld")
    except Exception as e:
        logger.error(f"[ERROR] Monitoring service balatma hatas: {e}")

    # Production Health Monitor' balat
    try:
        from core.production_health_monitor import production_health_monitor

        await production_health_monitor.start_monitoring()
        logger.info(
            "[OK] [HOSPITAL] Production Health Monitor balatld - API/DB/System monitoring aktif!"
        )
    except Exception as e:
        logger.error(f"[ERROR] Production Health Monitor balatma hatas: {e}")

    # AI Agents' balat (BUG FIX #1: Agent-API Integration)
    try:
        from agents import initialize_agents

        agents = initialize_agents()
        app.state.agents = agents
        logger.info(
            f"[OK] [ROBOT] AI Agents balatld - {len(agents)} agent aktif (Learning Path Agent: READY)"
        )
    except Exception as e:
        logger.error(f"[ERROR] AI Agents balatma hatas: {e}")

    # Elasticsearch'i balat
    try:
        from core.elasticsearch_config import initialize_elasticsearch

        es_service = await initialize_elasticsearch()
        if es_service:
            logger.info("[OK] Elasticsearch service balatld")
        else:
            logger.warning("[WARNING] Elasticsearch service balatlamad")
    except Exception as e:
        logger.error(f"[ERROR] Elasticsearch balatma hatas: {e}")

    # Elasticsearch logger' balat
    try:
        from core.elasticsearch_logger import get_elasticsearch_logger

        es_logger = get_elasticsearch_logger()
        await es_logger.start()
        logger.info("[OK] Elasticsearch logger balatld")
    except Exception as e:
        logger.error(f"[ERROR] Elasticsearch logger balatma hatas: {e}")

    # Analytics manager' balat
    try:
        from core.analytics_monitoring import get_analytics_manager

        analytics_manager = get_analytics_manager()
        await analytics_manager.initialize()
        logger.info("[OK] Analytics manager balatld")
    except Exception as e:
        logger.error(f"[ERROR] Analytics manager balatma hatas: {e}")

    # YouTube Rate Limiter' balat (Task 12)
    try:
        from services.youtube_rate_limiter import get_youtube_rate_limiter

        youtube_rate_limiter = get_youtube_rate_limiter()
        await youtube_rate_limiter.initialize()
        quota_info = await youtube_rate_limiter.get_quota_info()
        logger.info(
            f"[OK] YouTube Rate Limiter balatld - Quota: {quota_info.remaining_quota}/{quota_info.daily_limit}",
            extra_data={
                "remaining_quota": quota_info.remaining_quota,
                "daily_limit": quota_info.daily_limit,
            },
        )
    except Exception as e:
        logger.error(f"[ERROR] YouTube Rate Limiter balatma hatas: {e}")

    # SPRINT 11: Initialize Distributed Tracing
    try:
        from core.opentelemetry_config import init_tracing
        from core.database import engine

        otel_config = init_tracing(app, engine)
        app.state.otel_config = otel_config
        logger.info(
            "[OK] [ROCKET] Sprint 11: Distributed Tracing initialized - OpenTelemetry + Jaeger active!"
        )
    except Exception as e:
        logger.error(f"[ERROR] Distributed Tracing initialization failed: {e}")
        logger.warning("[WARNING] Application starting without distributed tracing")

    # SPRINT 12: Initialize Sentry Error Tracking
    try:
        from core.sentry_config import init_sentry

        sentry_config = init_sentry()
        app.state.sentry_config = sentry_config
        logger.info(
            "[OK] [SHIELD] Sprint 12: Sentry Error Tracking initialized - Comprehensive error monitoring active!"
        )
    except Exception as e:
        logger.error(f"[ERROR] Sentry Error Tracking initialization failed: {e}")
        logger.warning("[WARNING] Application starting without Sentry error tracking")

    # Initialize Wave 2B Quality Evaluation System
    try:
        from api.wave2b_quality_routes import initialize_wave2b

        await initialize_wave2b()
        logger.info(
            "[OK] Wave 2B Quality Evaluation initialized - BERTScore + Bloom + ÖSYM Benchmark active!"
        )
    except Exception as e:
        logger.error(f"[ERROR] Wave 2B initialization failed: {e}")
        logger.warning("[WARNING] Application starting without Wave 2B quality evaluation")

    yield

    # Servisleri kapat
    logger.info(" Platform kapatlyor...")

    # SPRINT 6: Rate Limiter' kapat
    try:
        from core.advanced_rate_limiter import get_rate_limiter

        rate_limiter = get_rate_limiter()
        await rate_limiter.disconnect()
        logger.info("[OK] Advanced Rate Limiter kapatld")
    except Exception as e:
        logger.error(f"[ERROR] Rate Limiter kapatma hatas: {e}")

    try:
        from core.cache import cache_manager, cache_invalidation_manager

        # Cache invalidation' durdur
        await cache_invalidation_manager.stop_scheduled_invalidation()
        logger.info("[OK] Cache Invalidation Manager durduruldu")

        # Cache manager' kapat
        await cache_manager.close()
        logger.info("[OK] Redis Cache Manager kapatld")

    except Exception as e:
        logger.error(f"[ERROR] Cache kapatma hatas: {e}")

    try:
        from core.performance_middleware import system_monitor

        system_monitor.stop_monitoring()
        logger.info("[OK] System Performance Monitor kapatld")
    except Exception as e:
        logger.error(f"[ERROR] Performance Monitor kapatma hatas: {e}")

    try:
        from core.database import close_database

        await close_database()
        logger.info("[OK] Database balants kapatld")
    except Exception as e:
        logger.error(f"[ERROR] Database kapatma hatas: {e}")

    try:
        await monitoring_service.stop()
        logger.info("[OK] Monitoring service kapatld")
    except Exception as e:
        logger.error(f"[ERROR] Monitoring service kapatma hatas: {e}")

    try:
        from core.production_health_monitor import production_health_monitor

        await production_health_monitor.stop_monitoring()
        logger.info("[OK] Production Health Monitor kapatld")
    except Exception as e:
        logger.error(f"[ERROR] Production Health Monitor kapatma hatas: {e}")

    # AI Agents' kapat (BUG FIX #1: Agent-API Integration)
    try:
        from agents import shutdown_agents

        await shutdown_agents()
        logger.info("[OK] [ROBOT] AI Agents kapatld - Tüm agent'lar temizlendi")
    except Exception as e:
        logger.error(f"[ERROR] AI Agents kapatma hatas: {e}")

    try:
        from core.elasticsearch_config import (
            get_global_elasticsearch_service,
            shutdown_elasticsearch,
        )

        es_service = await get_global_elasticsearch_service()
        await shutdown_elasticsearch(es_service)
        logger.info("[OK] Elasticsearch service kapatld")
    except Exception as e:
        logger.error(f"[ERROR] Elasticsearch kapatma hatas: {e}")

    try:
        es_logger = get_elasticsearch_logger()
        await es_logger.stop()
        logger.info("[OK] Elasticsearch logger kapatld")
    except Exception as e:
        logger.error(f"[ERROR] Elasticsearch logger kapatma hatas: {e}")

    try:
        analytics_manager = get_analytics_manager()
        await analytics_manager.shutdown()
        logger.info("[OK] Analytics manager kapatld")
    except Exception as e:
        logger.error(f"[ERROR] Analytics manager kapatma hatas: {e}")


# SPRINT 9: Enhanced OpenAPI Documentation
from core.openapi_config import get_openapi_config, get_openapi_tags

# FastAPI uygulamas with enhanced OpenAPI configuration
openapi_config = get_openapi_config()
app = FastAPI(
    title=openapi_config["title"],
    description=openapi_config["description"],
    version=openapi_config["version"],
    contact=openapi_config["contact"],
    license_info=openapi_config["license_info"],
    terms_of_service=openapi_config["terms_of_service"],
    openapi_tags=openapi_config["openapi_tags"],
    servers=openapi_config["servers"],
    docs_url=openapi_config["docs_url"],
    redoc_url=openapi_config["redoc_url"],
    openapi_url=openapi_config["openapi_url"],
    lifespan=lifespan,
)

# Global Exception Handlers Setup (must be before other middleware)
try:
    from core.global_exception_handler import (
        ExceptionHandlerConfig,
        HandlerMode,
        setup_global_exception_handlers,
    )

    config = ExceptionHandlerConfig(
        mode=HandlerMode.GRACEFUL,
        enable_error_recovery=True,
        enable_detailed_logging=True,
        enable_circuit_breaker=True,
        enable_turkish_messages=True,
        circuit_breaker_threshold=10,
        circuit_breaker_timeout=300,
        expose_internal_errors=os.getenv("DEBUG", "false").lower() == "true",
    )

    exception_handler = setup_global_exception_handlers(app, config)
    app.state.global_exception_handler = exception_handler
    logger.info(
        "[OK] Global Exception Handlers registered - Circuit Breaker, Error Recovery, Turkish Messages"
    )

except Exception as e:
    logger.error(f"[ERROR] Exception handlers setup failed: {e}")

# Structured Logging Middleware (en nce ekle)
setup_logging_middleware(app)

# SPRINT 11: Distributed Tracing Middleware
try:
    from core.tracing_middleware import DistributedTracingMiddleware

    app.add_middleware(
        DistributedTracingMiddleware,
        excluded_paths=[
            "/health",
            "/health/live",
            "/health/ready",
            "/health/startup",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ],
    )
    logger.info(
        "[OK] [ROCKET] Sprint 11: Distributed Tracing Middleware enabled - Request tracing active!"
    )
except Exception as e:
    logger.error(f"[ERROR] Distributed Tracing Middleware setup failed: {e}")

# SPRINT 12: Sentry Error Tracking Middleware
try:
    from core.sentry_middleware import SentryErrorTrackingMiddleware

    app.add_middleware(
        SentryErrorTrackingMiddleware,
        excluded_paths=[
            "/health",
            "/health/live",
            "/health/ready",
            "/health/startup",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ],
    )
    logger.info(
        "[OK] [SHIELD] Sprint 12: Sentry Error Tracking Middleware enabled - Automatic error capture active!"
    )
except Exception as e:
    logger.error(f"[ERROR] Sentry Error Tracking Middleware setup failed: {e}")

# ==================== PERFORMANCE MIDDLEWARE ====================

# Query Monitoring Middleware (PERFORMANCE FIX)
try:
    from core.query_monitoring import QueryMonitoringMiddleware

    app.add_middleware(QueryMonitoringMiddleware)
    logger.info(
        "[OK] [CHART] Query Monitoring Middleware enabled - Tracking DB performance!"
    )
except Exception as e:
    logger.error(f"[ERROR] Query Monitoring setup failed: {e}")

# ==================== SECURITY MIDDLEWARE STACK ====================

# API Versioning Middleware (ARCHITECTURE FIX)
try:
    from core.api_versioning import VersionMiddleware

    app.add_middleware(VersionMiddleware)
    logger.info(
        "[OK] [PACKAGE] API Versioning enabled - v1 active, deprecation support!"
    )
except Exception as e:
    logger.error(f"[ERROR] API versioning setup failed: {e}")

# Auth Rate Limiting Middleware (SECURITY FIX)
try:
    from core.auth_rate_limiting import AuthRateLimitMiddleware

    app.add_middleware(AuthRateLimitMiddleware)
    logger.info(
        "[OK] [SHIELD] Auth Rate Limiting enabled - Brute force protection active!"
    )
except Exception as e:
    logger.error(f"[ERROR] Auth rate limiting setup failed: {e}")

# CSRF Protection Middleware (SECURITY FIX)
try:
    from core.csrf_protection import CSRFProtectionMiddleware

    # SECURITY FIX: Enable CSRF on ALL endpoints including auth
    if os.getenv("ENABLE_CSRF", "true").lower() == "true":
        csrf_exempt_paths = [
            "/health",
            "/health/live",
            "/health/ready",
            "/health/startup",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
            # Auth endpoints are NOW PROTECTED by CSRF
            # Learning Path API - exempt for frontend integration
            "/api/learning-path",
            # YouTube Video Discovery API - exempt for frontend integration
            "/api/youtube/test",
            "/api/youtube/recommendations",
            "/api/youtube/search",
            # Wave 2B Quality Evaluation API - exempt for testing and integration
            "/api/v2/quality",
        ]

        app.add_middleware(
            CSRFProtectionMiddleware,
            secret_key=os.getenv("SECRET_KEY"),
            exempt_paths=csrf_exempt_paths,
        )
        logger.info(
            "[OK] [SHIELD] CSRF Protection enabled - Double-submit cookie pattern!"
        )
    else:
        logger.warning("[WARNING] CSRF Protection disabled (development mode)")
except Exception as e:
    logger.error(f"[ERROR] CSRF protection setup failed: {e}")

# ==================== SECURITY MIDDLEWARE STACK ====================

# 1. Comprehensive Security Middleware (JWT, Rate Limiting, Input Validation, CORS)
try:
    from core.security_middleware import (
        ComprehensiveSecurityMiddleware,
        SecurityMiddlewareConfig,
    )
    from core.rate_limiting import RateLimitMiddleware, create_rate_limiter

    # Environment-based CORS configuration
    environment = os.getenv("ENVIRONMENT", "development").lower()

    # Define allowed origins based on environment with security validation
    if environment == "production":
        # Production: ONLY specific production domains - NO localhost, NO wildcards
        cors_origins = [
            "https://kiro2.app",
            "https://www.kiro2.app",
            "https://api.kiro2.app",
        ]
        # Allow environment variable override for production
        env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        if env_origins:
            cors_origins = [origin.strip() for origin in env_origins.split(",")]

        # CRITICAL: Validate no wildcards or localhost in production
        if "*" in cors_origins:
            logger.error(
                "[CRITICAL SECURITY ERROR] Wildcard CORS detected in PRODUCTION! Removing wildcard."
            )
            cors_origins = [origin for origin in cors_origins if origin != "*"]

        # Remove localhost from production
        cors_origins = [
            origin
            for origin in cors_origins
            if "localhost" not in origin and "127.0.0.1" not in origin
        ]

        if not cors_origins:
            logger.error(
                "[CRITICAL ERROR] No valid CORS origins in production! Using safe defaults."
            )
            cors_origins = ["https://kiro2.app", "https://www.kiro2.app"]

    elif environment == "testing":
        # Testing: Localhost only - no external domains
        cors_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
        ]
    else:
        # Development: Localhost + common dev ports
        cors_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:3003",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]

    logger.info(
        f"[SECURITY] CORS configured for '{environment}' environment with {len(cors_origins)} allowed origins"
    )
    logger.info(
        f"[SECURITY] Allowed origins: {', '.join(cors_origins[:3])}{'...' if len(cors_origins) > 3 else ''}"
    )

    # Security configuration with environment-aware CORS
    security_config = SecurityMiddlewareConfig(
        # Authentication
        enable_authentication=True,
        authentication_required_paths=["/api/"],
        authentication_exempt_paths=[
            "/health",
            "/docs",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/reset-password",
        ],
        # Rate Limiting
        enable_rate_limiting=True,
        global_rate_limit_per_minute=1000,
        user_rate_limit_per_minute=100,
        ip_rate_limit_per_minute=200,
        burst_threshold=50,
        # CORS - Environment-based Configuration with Security Validation
        enable_cors=True,
        allowed_origins=cors_origins,
        allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allowed_headers=[
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Request-ID",
            "X-Session-ID",
            "Accept",
            "Origin",
        ],
        allow_credentials=True,
        # Security Headers
        enable_security_headers=True,
        # Input Validation
        enable_input_validation=True,
        max_request_size=10 * 1024 * 1024,  # 10MB
        max_json_depth=10,
        # IP Filtering
        enable_ip_filtering=True,
        ip_whitelist=set(),  # Production'da admin IP'leri eklenebilir
        ip_blacklist=set(),
        # Bot Detection
        enable_bot_detection=True,
        # Logging
        log_security_events=True,
        log_failed_auth=True,
    )

    # Add comprehensive security middleware
    app.add_middleware(ComprehensiveSecurityMiddleware, config=security_config)
    logger.info(
        "[OK] [SHIELD] Comprehensive Security Middleware enabled - JWT, Rate Limiting, Input Validation, CORS!"
    )

except Exception as e:
    logger.error(f"[ERROR] Security middleware setup failed: {e}")

    # Fallback to basic CORS - still environment-aware!
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == "production":
        fallback_origins = [
            "https://kiro2.app",
            "https://www.kiro2.app",
            "https://api.kiro2.app",
        ]
        logger.warning(
            "[FALLBACK] Using basic CORS middleware for PRODUCTION with restricted origins"
        )
    else:
        fallback_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:3003",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
        ]
        logger.warning(
            f"[FALLBACK] Using basic CORS middleware for {environment.upper()}"
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=fallback_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
    )
    logger.info(f"[FALLBACK CORS] {len(fallback_origins)} origins allowed")

# 2. Advanced Rate Limiting & DDoS Protection Middleware
try:
    # SPRINT 6: Advanced Redis-based rate limiter with tier support
    from core.rate_limit_middleware import RateLimitMiddleware as AdvancedRateLimitMiddleware
    from core.advanced_rate_limiter import get_rate_limiter

    advanced_rate_limiter = get_rate_limiter()
    app.add_middleware(AdvancedRateLimitMiddleware, rate_limiter=advanced_rate_limiter)
    logger.info("[OK] Sprint 6: Advanced Rate Limiter (Redis + Tiers) yklendi")

    # NEW: SlowAPI + Adaptive DDoS Protection
    from core.ddos_protection import setup_ddos_protection

    ddos_components = setup_ddos_protection(
        app,
        redis_url=os.getenv("REDIS_URL"),
        enable_slowapi=True,
        enable_adaptive=True,
        enable_pattern_analysis=True,
    )

    # Add DDoS middleware
    app.add_middleware(
        type(ddos_components["middleware"]),
        app=app,
        redis_client=ddos_components.get("redis"),
        enable_adaptive=True,
        enable_pattern_analysis=True,
    )

    logger.info(
        "[OK] [SHIELD] Advanced DDoS Protection enabled - SlowAPI, Adaptive Limiting, Pattern Analysis!"
    )
    logger.info(
        f"[DDoS PROTECTION] Redis: {'OK' if ddos_components.get('redis') else 'FAIL'}"
    )

except Exception as e:
    logger.error(f"[ERROR] DDoS protection setup failed: {e}")
    logger.warning("[FALLBACK] Using basic rate limiting only")

# Performance monitoring middleware'leri ekle
try:
    from core.performance_middleware import (
        PerformanceTrackingMiddleware,
        setup_performance_monitoring,
    )

    # Timeout middleware (must be before performance tracking)
    from core.middleware.timeout_middleware import TimeoutMiddleware
    default_timeout = int(os.getenv("TIMEOUT_DEFAULT", "30"))
    app.add_middleware(TimeoutMiddleware, default_timeout=default_timeout)
    logger.info(f"[OK] [CLOCK] Timeout Middleware enabled - Default: {default_timeout}s")

    # Performance tracking middleware
    app.add_middleware(PerformanceTrackingMiddleware, enable_detailed_logging=True)

    # Setup comprehensive performance monitoring
    setup_performance_monitoring(app)

    logger.info(
        "Performance Monitoring Middleware'leri eklendi - API, Database, System Metrics!"
    )
except Exception as e:
    logger.error(f"[ERROR] Performance monitoring middleware ekleme hatas: {e}")

# Legacy performance middleware (fallback) - DISABLED
# PerformanceMiddleware ve RateLimiter bu dosyada mevcut deil
# Bu middleware'lar yerine PerformanceTrackingMiddleware kullanlyor

# Monitoring middleware'leri ekle
try:
    from core.elasticsearch_logger import (
        ElasticsearchLoggingMiddleware,
        get_elasticsearch_logger,
    )
    from core.monitoring import MetricsMiddleware

    # Metrics middleware
    app.add_middleware(MetricsMiddleware)

    # Elasticsearch logging middleware
    es_logger = get_elasticsearch_logger()
    app.add_middleware(ElasticsearchLoggingMiddleware, logger=es_logger)

    logger.info("[OK] Monitoring middleware'leri eklendi")
except Exception as e:
    logger.error(f"[ERROR] Monitoring middleware ekleme hatas: {e}")

# Gvenlik middleware (test ortamnda devre d)
if os.getenv("TESTING") != "true":
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
    )

# API Router'lar dahil et
try:
    from api.health import router as health_router

    app.include_router(health_router)
    logger.info("[OK] Health Check API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] Health API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Health API router ykleme hatas: {e}")

try:
    from api.auth import router as auth_router

    app.include_router(auth_router)
    logger.info("[OK] Kimlik dorulama API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] Auth API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Auth API router ykleme hatas: {e}")

# SPRINT 4: Two-Factor Authentication API
try:
    from api.two_factor_auth_api import router as two_factor_auth_router

    app.include_router(two_factor_auth_router)
    logger.info("[OK] Sprint 4: 2FA (Two-Factor Authentication) API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] 2FA API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] 2FA API router ykleme hatas: {e}")

# SPRINT 5: KVKK Compliance APIs
try:
    from api.kvkk_consent_api import router as kvkk_consent_router

    app.include_router(kvkk_consent_router)
    logger.info("[OK] Sprint 5: KVKK Consent Management API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] KVKK Consent API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] KVKK Consent API router ykleme hatas: {e}")

try:
    from api.kvkk_privacy_api import router as kvkk_privacy_router

    app.include_router(kvkk_privacy_router)
    logger.info("[OK] Sprint 5: KVKK Privacy Dashboard API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] KVKK Privacy API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] KVKK Privacy API router ykleme hatas: {e}")

# SPRINT 6: Advanced Rate Limiting API
try:
    from api.rate_limit_api import router as rate_limit_router

    app.include_router(rate_limit_router)
    logger.info("[OK] Sprint 6: Rate Limit Management API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] Rate Limit API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Rate Limit API router ykleme hatas: {e}")

try:
    from api.sinav import router as sinav_router

    app.include_router(sinav_router)
    logger.info("[OK] Snav API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] Snav API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Snav API router ykleme hatas: {e}")

try:
    from api.exam_performance import router as exam_performance_router

    app.include_router(exam_performance_router)
    logger.info(
        "[OK] [CHART] Snav Performans Analizi API'si yklendi - Detayl analiz, zayflk tespiti ve alma nerileri!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Exam Performance API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Exam Performance API router ykleme hatas: {e}")

try:
    from api.monitoring import router as monitoring_router

    app.include_router(monitoring_router)
    logger.info(
        "[OK] [CHART] Production Monitoring API'si yklendi - Performance Metrics, Health Checks, Log Analysis!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Monitoring API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Monitoring API router ykleme hatas: {e}")

# Advanced Analytics API'si (TASK 66.2)
try:
    from api.analytics import router as analytics_router

    app.include_router(analytics_router)
    logger.info(
        "[OK] [CHART] Advanced Analytics API'si yklendi - KAPSAMLI ANALYTICS VE EXPORT!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Analytics API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Analytics API router ykleme hatas: {e}")

# SPRINT 11: Distributed Tracing Demo API
try:
    from api.tracing_example import router as tracing_demo_router

    app.include_router(tracing_demo_router)
    logger.info(
        "[OK] [ROCKET] Sprint 11: Distributed Tracing Demo API yklendi - OpenTelemetry + Jaeger examples!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Tracing Demo API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Tracing Demo API router ykleme hatas: {e}")

# SPRINT 12: Sentry Error Tracking Demo API
try:
    from api.sentry_demo import router as sentry_demo_router

    app.include_router(sentry_demo_router)
    logger.info(
        "[OK] [SHIELD] Sprint 12: Sentry Error Tracking Demo API yklendi - Error monitoring examples!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Sentry Demo API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Sentry Demo API router ykleme hatas: {e}")

try:
    from api.learning_style import router as learning_style_router

    app.include_router(learning_style_router)
    logger.info("[OK] Hibrit renme Stili API'si yklendi - 64 profil kombinasyonu hazr")
except ImportError as e:
    logger.warning(f"[WARNING] Learning Style API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Learning Style API router ykleme hatas: {e}")

try:
    from api.learning_path import router as learning_path_router
    from api.learning_path_v2 import router as learning_path_v2_router

    app.include_router(learning_path_router)
    app.include_router(
        learning_path_v2_router
    )  # P0 Fix: Database + Auth + Fallback videos
    logger.info(
        "[OK] Learning Path API'si yklendi - Kiiselletirilmi renme yolu oluturma aktif"
    )
    logger.info(
        "[OK] Learning Path API v2 yklendi - Database + Authentication + Fallback videos aktif"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Learning Path API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Learning Path API router ykleme hatas: {e}")

try:
    from api.zpd_maarif import router as zpd_maarif_router

    app.include_router(zpd_maarif_router)
    logger.info(
        "[OK] ZPD + MEB Maarif API'si yklendi - Trk eitim kltrne uyarlanm sistem hazr"
    )
except ImportError as e:
    logger.warning(f"[WARNING] ZPD Maarif API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] ZPD Maarif API router ykleme hatas: {e}")

try:
    from api.irt_morfoloji import router as irt_morfoloji_router

    app.include_router(irt_morfoloji_router)
    logger.info(
        "[OK] IRT + Trke Morfoloji API'si yklendi - SYM/ETS standartlarn aan sistem hazr"
    )
except ImportError as e:
    logger.warning(f"[WARNING] IRT Morfoloji API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] IRT Morfoloji API router ykleme hatas: {e}")

try:
    from api.student_dashboard import router as student_dashboard_router

    app.include_router(student_dashboard_router)
    logger.info("[OK] renci Dashboard API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] Student Dashboard API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Student Dashboard API router ykleme hatas: {e}")

# SPRINT 3: Celery Background Tasks API
try:
    from api.celery_tasks_api import router as celery_tasks_router

    app.include_router(celery_tasks_router)
    logger.info("[OK] Celery Background Tasks API'si yklendi - Async processing ready")
except ImportError as e:
    logger.warning(f"[WARNING] Celery Tasks API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Student Dashboard API router ykleme hatas: {e}")

# Batch Question Generation API
try:
    from api.batch_generation_api import router as batch_generation_router

    app.include_router(batch_generation_router)
    logger.info("[OK] [ROCKET] Batch Question Generation API'si yklendi - Parallel processing, 500 soru/saat!")
except ImportError as e:
    logger.warning(f"[WARNING] Batch Generation API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Batch Generation API router ykleme hatas: {e}")

# PDF Processing API
try:
    from api.pdf_processing_api import router as pdf_processing_router

    app.include_router(pdf_processing_router)
    logger.info("[OK] [DOCUMENT] PDF Processing API'si yklendi - OCR, Layout Analysis, Question Extraction!")
except ImportError as e:
    logger.warning(f"[WARNING] PDF Processing API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] PDF Processing API router ykleme hatas: {e}")

# Wave 2B: Advanced Quality Evaluation API
try:
    from api.wave2b_quality_routes import router as wave2b_router

    app.include_router(wave2b_router)
    # Note: initialize_wave2b() is called in lifespan context for proper async handling
    logger.info(
        "[OK] Wave 2B Quality Evaluation API yüklendi - BERTScore + Bloom + ÖSYM Benchmark (initialization in lifespan)"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Wave 2B Quality API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Wave 2B Quality API router yükleme hatası: {e}")

try:
    from api.cache import router as cache_router

    app.include_router(cache_router)
    logger.info("[OK] Redis Cache Management API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] Cache API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Cache API router ykleme hatas: {e}")

try:
    from api.agents import router as agents_router

    app.include_router(agents_router)
    logger.info("[OK] AI Agents API'si yklendi")
except ImportError as e:
    logger.warning(f"[WARNING] Agents API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Agents API router ykleme hatas: {e}")

try:
    from api.soru_bankasi import router as soru_bankasi_router

    app.include_router(soru_bankasi_router)
    logger.info(
        "[OK] Soru Bankas API'si yklendi - IRT parametreli adaptif soru seimi hazr"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Soru Bankas API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Soru Bankas API router ykleme hatas: {e}")

# Task 71: Soru CRUD İşlemleri API
try:
    from api.question_crud_api import router as question_crud_router

    app.include_router(question_crud_router)
    logger.info(
        "[OK] [ROCKET] Soru CRUD API'si yklendi - Rich Text, Image Upload, Version Control, Archive/Restore, Advanced Search!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Question CRUD API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Question CRUD API router ykleme hatas: {e}")

# Questions API - 141 soru için REST API
try:
    from api.questions_api import router as questions_api_router

    app.include_router(questions_api_router)
    logger.info(
        "[OK] [ROCKET] Questions API yklendi - 141 soru filtreleme, arama, statistikler hazr!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Questions API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Questions API router ykleme hatas: {e}")

try:
    from api.content_management import router as content_management_router

    app.include_router(content_management_router)
    logger.info(
        "[OK] erik Ynetim API'si yklendi - Soru bankas ve eitim materyali CRUD ilemleri hazr"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Content Management API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Content Management API router ykleme hatas: {e}")

try:
    from api.admin import router as admin_router

    app.include_router(admin_router)
    logger.info(
        "[OK] Admin Panel API'si yklendi - Kullanc ynetimi ve dashboard istatistikleri hazr"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Admin API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Admin API router ykleme hatas: {e}")

try:
    from api.adhd_task_management_api import router as adhd_task_management_router

    app.include_router(adhd_task_management_router)
    logger.info(
        "[OK] [BRAIN] ADHD Task Management API'si yklendi - ncelik Sralaması, Renk Kodlama, Eisenhower Matrix!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] ADHD Task Management API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] ADHD Task Management API router ykleme hatas: {e}")

try:
    from api.text_simplification import router as text_simplification_router

    app.include_router(text_simplification_router)
    logger.info(
        "[OK] [ROCKET] 3 Seviyeli Trke Metin Basitletirme API'si yklendi - DNYADA LK!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Text Simplification API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Text Simplification API router ykleme hatas: {e}")

try:
    from api.ogretmen import router as ogretmen_router

    app.include_router(ogretmen_router)
    logger.info(
        "[OK] retmen Paneli API'si yklendi - Snf ynetimi ve performans takibi hazr"
    )
except ImportError as e:
    logger.warning(f"[WARNING] retmen API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] retmen API router ykleme hatas: {e}")

try:
    from api.advanced_reports import router as advanced_reports_router

    app.include_router(advanced_reports_router)
    logger.info(
        "[OK] [ROCKET] Gelimi Snav Raporlama API'si yklendi - IRT + Morfoloji + ZPD + Hibrit renme Stili!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Advanced Reports API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Advanced Reports API router ykleme hatas: {e}")

try:
    from api.performance import router as performance_router

    app.include_router(performance_router)
    logger.info(
        "[OK] [ROCKET] Performance Optimization API'si yklendi - Cache, Database, Revolutionary Features!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Performance API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Performance API router ykleme hatas: {e}")

try:
    from api.fsrs import router as fsrs_router

    app.include_router(fsrs_router)
    logger.info(
        "[OK] [ROCKET] FSRS API'si yklendi - 17 Parametreli Trk renci Davranlar Optimize Edilmi Sistem!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] FSRS API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] FSRS API router ykleme hatas: {e}")

# Zemberek-NLP API'si (Türkçe Morfolojik Analiz)
try:
    from api.zemberek import router as zemberek_router

    app.include_router(zemberek_router)
    logger.info(
        "[OK] [ROCKET] Zemberek-NLP API'si yüklendi - Türkçe Morfolojik Analiz, Tokenization, Spell Check!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Zemberek API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Zemberek API router yükleme hatası: {e}")

# Token Monitoring & OSYM Question Generation APIs (Frontend Dashboards)
try:
    from api.monitoring_routes import router as monitoring_router

    app.include_router(monitoring_router)
    logger.info(
        "[OK] [CHART] Token Monitoring API'si yüklendi - Token stats, A/B test results, CSV export!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Monitoring routes API yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Monitoring routes API yükleme hatası: {e}")

try:
    from api.osym_routes import router as osym_router

    app.include_router(osym_router)
    logger.info(
        "[OK] [ROCKET] OSYM Question Generation API'si yüklendi - AI-powered question generation!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] OSYM routes API yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] OSYM routes API yükleme hatası: {e}")

try:
    from api.berturk_api import router as berturk_router

    app.include_router(berturk_router)
    logger.info(
        "[OK] [ROCKET] BERTurk API'si yklendi - Duygu Analizi, Motivasyon Tespiti ve Intent Detection!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] BERTurk API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] BERTurk API router ykleme hatas: {e}")

# Multi-Agent Blackboard API'si (DEVRMSEL ZELLK #7)
# Multi-Agent Blackboard API'si - DISABLED (duplicate router)

# RAG (Retrieval-Augmented Generation) API'si
try:
    from api.rag import router as rag_router

    app.include_router(rag_router)
    logger.info(
        "[OK] [ROCKET] RAG API'si yüklendi - Document Indexing, Semantic Search, LLM Context Retrieval!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] RAG API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] RAG API router yükleme hatası: {e}")

# Enhanced Chat API'si (TASK 22 - AI sohbet sistemi ve NLP entegrasyonu)
try:
    from api.enhanced_chat import router as enhanced_chat_router

    app.include_router(enhanced_chat_router)
    logger.info(
        "[OK] [ROCKET] Enhanced Chat API'si yklendi - ZPD + renme Stili + IRT Morfoloji + Agent Koordinasyonu!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Enhanced Chat API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Enhanced Chat API router ykleme hatas: {e}")

# Kltrel Adaptasyon Motoru API'si (TASK 70 - Trk Kltr Faktrleri Dinamik Ayarlama)
try:
    from api.cultural_adaptation_api import router as cultural_adaptation_router

    app.include_router(cultural_adaptation_router)
    logger.info(
        "[OK] [ROCKET] Kltrel Adaptasyon Motoru API'si yklendi - Trk Kltr Faktrleri Dinamik Ayarlama!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Cultural Adaptation API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Cultural Adaptation API router ykleme hatas: {e}")

# PHASE 1 FIX: DUPLICATE EXCEPTION HANDLER REMOVED (lines 822-823 were orphaned)

# Bionic Reading API'si (DEVRMSEL ZELLK #6)
try:
    from api.bionic_reading import router as bionic_reading_router

    app.include_router(bionic_reading_router)
    logger.info(
        "[OK] [ROCKET] Bionic Reading API'si yklendi - Disleksi iin Trke'ye zel Okuma Destei!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Bionic Reading API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Bionic Reading API router ykleme hatas: {e}")

# Turkish NLP API'si
try:
    from api.turkish_nlp import router as turkish_nlp_router

    app.include_router(turkish_nlp_router)
    logger.info(
        "[OK] [ROCKET] Turkish NLP API'si yklendi - Zemberek Entegrasyonu ile Morfolojik Analiz!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Turkish NLP API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Turkish NLP API router ykleme hatas: {e}")
# Curriculum Compliance API'si (TASK 8 - MEB ve SYM Mfredat Uyumluluk Sistemi)
try:
    from api.curriculum_compliance import router as curriculum_compliance_router

    app.include_router(curriculum_compliance_router)
    logger.info(
        "[OK] [ROCKET] Curriculum Compliance API'si yklendi - MEB ve SYM Mfredat Uyumluluk Sistemi!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Curriculum Compliance API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Curriculum Compliance API router ykleme hatas: {e}")

try:
    from api.multi_agent import router as multi_agent_router

    app.include_router(multi_agent_router)

    logger.info(
        "[OK] [ROCKET] Multi-Agent Blackboard API'si yklendi - GEREK ZAMANLI AGENT KOORDNASYONU!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Multi-Agent API yklenemedi: {e}")

# Duplicate Bionic Reading API removed - already included above

# Elasticsearch API'si (KRTK ENTEGRASYON)
try:
    from api.elasticsearch import router as elasticsearch_router

    app.include_router(elasticsearch_router)

    logger.info(
        "[OK] [SEARCH] Elasticsearch API'si yklendi - TRKE FULL-TEXT SEARCH VE ANALYTICS!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Elasticsearch API yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Elasticsearch API ykleme hatas: {e}")

# Duplicate Turkish NLP API removed - already included above

# Veli Takip Sistemi API'si (TASK 26)
try:
    from api.veli import router as veli_router

    app.include_router(veli_router)

    logger.info(
        "[OK] [FAMILY] Veli Takip Sistemi API'si yklendi - OCUK PERFORMANS TAKB VE HAFTALIK RAPORLAR!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Veli API yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Veli API ykleme hatas: {e}")

# Parent Tracking System API (TASK 26 - Enhanced)
try:
    from api.parent import router as parent_router

    app.include_router(parent_router)

    logger.info(
        "[OK] [FAMILY] Parent Tracking System API'si yklendi - ENHANCED PARENT-CHILD RELATIONSHIP MANAGEMENT!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Parent API yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Parent API ykleme hatas: {e}")

# EBA TV API'sini ekle
try:
    from api.ebatv import router as ebatv_router

    app.include_router(ebatv_router)

    logger.info(
        "[OK] [MOVIE] EBA TV API'si yklendi - TRT EBA TV erik Entegrasyonu, Kalite Analizi ve Kiiselletirilmi neriler!"
    )
except ImportError as e:
    logger.error(f"[ERROR] EBA TV API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] EBA TV API ykleme hatas: {e}")

# ADHD Focus Mode API'si (TASK 89 - Odak Modu)
try:
    from api.adhd_focus_mode_api import router as adhd_focus_mode_router

    app.include_router(adhd_focus_mode_router)

    logger.info(
        "[OK] [FOCUS] ADHD Focus Mode API'si yklendi - Dikkat Datc Unsurlar Gizleme, Minimal Arayz, Tek Grev Odaklanma!"
    )
except ImportError as e:
    logger.error(f"[ERROR] ADHD Focus Mode API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] ADHD Focus Mode API ykleme hatas: {e}")

# Turkish NLP Chat API'sini ekle
try:
    from api.turkish_nlp_chat import router as turkish_nlp_chat_router

    app.include_router(turkish_nlp_chat_router)

    logger.info(
        "[OK] [ROBOT] Trke NLP Chat API'si yklendi - Balamsal Konuma, Eitim Terminolojisi ve Adm Adm zmler!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Trke NLP Chat API router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Trke NLP Chat API ykleme hatas: {e}")

# Math Solution Steps API'sini ekle (TASK 84.1)
try:
    from api.math_solution_steps import router as math_solution_steps_router

    app.include_router(math_solution_steps_router)

    logger.info(
        "[OK] [MATH] Matematik Adım Adım Çözüm API'si yüklendi - Progressive Disclosure, Hint System, Error Highlighting!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Math Solution Steps API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Math Solution Steps API yükleme hatası: {e}")

# Video Solution API'sini ekle (TASK 72.1)
try:
    from api.video_solution import router as video_solution_router

    app.include_router(video_solution_router)

    logger.info(
        "[OK] [VIDEO] Video Çözüm Sistemi API'si yüklendi - Video Upload, Format Validation, Compression!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Video Solution API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Video Solution API yükleme hatası: {e}")

# TASK 73.4: Alternative Solutions API - Student Submissions & Peer Review
try:
    from api.alternative_solutions_api import router as alternative_solutions_router

    app.include_router(alternative_solutions_router)

    logger.info(
        "[OK] [STAR] Alternative Solutions API'si yüklendi - Student Submissions, Peer Review, Upvote/Downvote!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Alternative Solutions API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Alternative Solutions API yükleme hatası: {e}")

# TASK 79: Text-to-Speech API - Fallback TTS Service
try:
    from api.tts_api import router as tts_router

    app.include_router(tts_router)

    logger.info(
        "[OK] [SPEAKER] Text-to-Speech API'si yüklendi - Türkçe TTS, Fallback Service, Voice Control!"
    )
except ImportError as e:
    logger.error(f"[ERROR] TTS API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] TTS API yükleme hatası: {e}")

# TASK 87: Manipulatives API - Diskalkuli Desteği
try:
    from api.manipulatives_api import router as manipulatives_router

    app.include_router(manipulatives_router)

    logger.info(
        "[OK] [PUZZLE] Manipülatifler API'si yüklendi - Sanal Bloklar, GeoGebra, İnteraktif Geometri, Dijital Tangram!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Manipulatives API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Manipulatives API yükleme hatası: {e}")

# TASK 88: ADHD Support API - Dikkat Yönetimi
try:
    from api.adhd_support_api import router as adhd_support_router

    app.include_router(adhd_support_router)

    logger.info(
        "[OK] [BRAIN] DEHB Desteği API'si yüklendi - Pomodoro Timer, Görsel Zamanlayıcı, Dikkat Dağınıklığı Tespiti, Konsantrasyon Egzersizleri!"
    )
except ImportError as e:
    logger.error(f"[ERROR] ADHD Support API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] ADHD Support API yükleme hatası: {e}")

# PHASE 1 FIX: DUPLICATE REMOVED - ADHD Task Management already loaded at line 699
# Original: TASK 90: ADHD Task Management API - Görev Bölme ve Organizasyon

# TASK 92: Instant Feedback API - Anında Geri Bildirim (ADHD Support)
try:
    from api.instant_feedback_api import router as instant_feedback_router

    app.include_router(instant_feedback_router)

    logger.info(
        "[OK] [CELEBRATION] DEHB Anında Geri Bildirim API'si yüklendi - Başarı Animasyonları, Puan Kazanma, Seri Takibi, Başarı Grafiği!"
    )
except ImportError as e:
    logger.error(f"[ERROR] Instant Feedback API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Instant Feedback API yükleme hatası: {e}")

# TASK 93: OSB Settings API - Öngörülebilir Arayüz (OSB Support)
try:
    from api.osb_settings_api import router as osb_settings_router

    app.include_router(osb_settings_router)

    logger.info(
        "[OK] [PREDICTABLE] OSB Ayarları API'si yüklendi - Tutarlı Düzen, Sabit Menü, Değişmeyen Renkler, Standart İkonlar!"
    )
except ImportError as e:
    logger.error(f"[ERROR] OSB Settings API router yüklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] OSB Settings API yükleme hatası: {e}")

# PERFORMANCE OPTIMIZED YouTube API - Real Data + Enhanced Security
try:
    # SECURITY FIX: Remove hard-coded API key (os already imported at top)
    if not os.getenv("YOUTUBE_API_KEY"):
        logger.warning(
            "YOUTUBE_API_KEY environment variable not set - using curated fallback"
        )
        # Use empty key to trigger secure fallback behavior
        os.environ.setdefault("YOUTUBE_API_KEY", "")

    # Import performance optimized endpoint
    try:
        from .fast_youtube_endpoint import router as fast_youtube_router

        app.include_router(fast_youtube_router)
        logger.info(
            "[OK] [ROCKET] Fast YouTube API loaded - <200ms response time target!"
        )
    except ImportError as import_error:
        logger.error(f"[ERROR] Fast YouTube endpoint import failed: {import_error}")
        logger.warning("[FALLBACK] Fast YouTube API disabled - using legacy endpoints")

    # Legacy compatibility endpoint (kept for backward compatibility)
    import random
    import time

    from fastapi import APIRouter

    youtube_router_legacy = APIRouter(prefix="/api/youtube", tags=["YouTube Legacy"])

    @youtube_router_legacy.get("/test")
    async def youtube_test():
        """Legacy test endpoint"""
        return {
            "status": "OK",
            "message": "YouTube Legacy API çalışıyor!",
            "redirect": "Use /api/youtube-fast for better performance",
        }

    @youtube_router_legacy.post("/recommendations")
    async def get_legacy_recommendations(request: dict):
        """Legacy endpoint - redirects to fast version"""
        start_time = time.time()

        # Simple curated response for compatibility
        video_pool = [
            {
                "id": "J9lS14nM1xg",
                "title": "TYT Matematik - Fonksiyonlar",
                "ch": "TonguçAkademi",
                "s": "matematik",
            },
            {
                "id": "kJQP7kiw5Fk",
                "title": "TYT Fizik - Hareket",
                "ch": "Fizik Öğretmeni",
                "s": "fizik",
            },
            {
                "id": "BvV6rq9V7xQ",
                "title": "TYT Kimya - Atom Yapısı",
                "ch": "TonguçAkademi",
                "s": "kimya",
            },
        ]

        random.seed(int(time.time() * 1000))
        selected = random.choice(video_pool)

        response_time = round((time.time() - start_time) * 1000, 2)

        return [
            {
                "subject_exam": f"{selected['s']}_TYT",
                "videos": [
                    {
                        "video_id": selected["id"],
                        "title": selected["title"],
                        "channel": selected["ch"],
                        "channel_id": f"UC_{selected['ch'].replace(' ', '_')}",
                        "duration": "20:00",
                        "view_count": random.randint(50000, 200000),
                        "upload_date": "2023-08-01",
                        "thumbnail": f"https://img.youtube.com/vi/{selected['id']}/maxresdefault.jpg",
                        "quality_score": 8.5,
                        "subject": selected["s"],
                        "difficulty": "orta",
                        "exam_type": "TYT",
                        "url": f"https://www.youtube.com/embed/{selected['id']}",
                    }
                ],
                "total_count": 1,
                "performance_note": f"Legacy endpoint: {response_time}ms - Use /api/youtube-fast for better performance",
            }
        ]

    app.include_router(youtube_router_legacy)
    logger.info(
        "[OK] [LEGACY] YouTube Legacy API loaded - Consider migrating to /api/youtube-fast"
    )

except Exception as e:
    logger.error(f"[ERROR] YouTube API setup hatası: {e}")
    logger.warning(
        "[FALLBACK] YouTube API running in fallback mode - check YOUTUBE_API_KEY environment variable"
    )

# WebSocket Router'lar dahil et
try:
    from .websocket_exam import websocket_router

    app.include_router(websocket_router)
    logger.info(
        "[OK] Snav WebSocket API'si yklendi - Gerek zamanl snav durumu gncellemeleri hazr"
    )
except ImportError as e:
    logger.warning(f"[WARNING] WebSocket Exam router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] WebSocket Exam router ykleme hatas: {e}")

# Streaming Chat API Router - Server-Sent Events (SSE)
try:
    from api.streaming_chat import router as streaming_router

    app.include_router(streaming_router)
    logger.info(
        "[OK] [ROCKET] Streaming Chat API yklendi - SSE ile gerek zamanl token streaming aktif!"
    )
except ImportError as e:
    logger.warning(f"[WARNING] Streaming Chat router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Streaming Chat router ykleme hatas: {e}")

# Performance Monitoring API Router
try:
    from api.performance_monitoring import router as perf_monitoring_router

    app.include_router(perf_monitoring_router)
    logger.info(
        "[OK] [CHART] Performance Monitoring API yklendi - LLM Pool, Vector Store, Cache metrikleri hazr!"
    )
except Exception as e:
    logger.error(f"[ERROR] Performance Monitoring API yklenemedi: {str(e)}")

# YouTube Video Discovery API Router
try:
    from api.youtube_routes import router as youtube_routes_router

    app.include_router(youtube_routes_router)
    logger.info(
        "[OK] [ROCKET] YouTube Video Discovery API yklendi - Semantic/Hybrid Search, Personalized Recommendations!"
    )
except Exception as e:
    logger.error(f"[ERROR] YouTube Video Discovery API yklenemedi: {str(e)}")
except ImportError as e:
    logger.warning(f"[WARNING] Performance Monitoring router yklenemedi: {e}")
except Exception as e:
    logger.error(f"[ERROR] Performance Monitoring router ykleme hatas: {e}")

# Task 100: Video Analytics API Router
try:
    from api.video_analytics_routes import router as video_analytics_router

    app.include_router(video_analytics_router)
    logger.info(
        "[OK] [ANALYTICS] Video Analytics API yklendi - Watch Tracking, Notes, Bookmarks, Completion Milestones!"
    )
except Exception as e:
    logger.error(f"[ERROR] Video Analytics API yklenemedi: {str(e)}")

# Task 101: University Advisory API Router
try:
    from api.university_advisory_routes import router as university_advisory_router

    app.include_router(university_advisory_router)
    logger.info(
        "[OK] [UNIVERSITY] University Advisory API yklendi - Base Scores, Quotas, Recommendations!"
    )
except Exception as e:
    logger.error(f"[ERROR] University Advisory API yklenemedi: {str(e)}")

# Task 102: Preference Simulation API Router
try:
    from api.preference_simulation_routes import router as preference_simulation_router

    app.include_router(preference_simulation_router)
    logger.info(
        "[OK] [SIMULATION] Preference Simulation API yklendi - Score Calculation, Placement Prediction, Recommendations!"
    )
except Exception as e:
    logger.error(f"[ERROR] Preference Simulation API yklenemedi: {str(e)}")

# Task 103: Department Information API Router
try:
    from api.department_info_routes import router as department_info_router

    app.include_router(department_info_router)
    logger.info(
        "[OK] [DEPARTMENT] Department Information API yklendi - Curriculum, Careers, Salaries, Sector Analysis!"
    )
except Exception as e:
    logger.error(f"[ERROR] Department Information API yklenemedi: {str(e)}")

# Task 104: University Information API Router
try:
    from api.university_info_routes import router as university_info_router

    app.include_router(university_info_router)
    logger.info(
        "[OK] [UNIVERSITY INFO] University Information API yklendi - Campus, Living Costs, Dormitories, Scholarships!"
    )
except Exception as e:
    logger.error(f"[ERROR] University Information API yklenemedi: {str(e)}")

# Task 105: Student Reviews API Router
try:
    from api.student_review_routes import router as student_review_router

    app.include_router(student_review_router)
    logger.info(
        "[OK] [REVIEWS] Student Reviews API yklendi - Submission, Ratings, Moderation, Filtering!"
    )
except Exception as e:
    logger.error(f"[ERROR] Student Reviews API yklenemedi: {str(e)}")

# Task 106: AI Chat Assistant API Router
try:
    from api.ai_chat_routes import router as ai_chat_router

    app.include_router(ai_chat_router)
    logger.info(
        "[OK] [AI CHAT] AI Chat Assistant API yklendi - Enhanced Chat, Image Upload, OCR, Solutions!"
    )
except Exception as e:
    logger.error(f"[ERROR] AI Chat Assistant API yklenemedi: {str(e)}")

# Task 107: Teacher Pool API Router
try:
    from api.teacher_routes import router as teacher_router

    app.include_router(teacher_router)
    logger.info(
        "[OK] [TEACHER] Teacher Pool API yklendi - Registration, Expertise, Availability, Appointments!"
    )
except Exception as e:
    logger.error(f"[ERROR] Teacher Pool API yklenemedi: {str(e)}")

# Task 108: Live Q&A Sessions API Router
try:
    from api.live_session_routes import router as live_session_router

    app.include_router(live_session_router)
    logger.info(
        "[OK] [LIVE] Live Q&A Sessions API yklendi - Video Conference, Screen Share, Whiteboard, Recording!"
    )
except Exception as e:
    logger.error(f"[ERROR] Live Q&A Sessions API yklenemedi: {str(e)}")

# PHASE 1 CRITICAL FIX: Security-Critical APIs
# API Key Management API
try:
    from api.api_key_api import router as api_key_router

    app.include_router(api_key_router)
    logger.info(
        "[OK] [SECURITY] API Key Management API yklendi - API key validation and management!"
    )
except Exception as e:
    logger.error(f"[ERROR] API Key Management API yklenemedi: {str(e)}")

# Audit API
try:
    from api.audit_api import router as audit_router

    app.include_router(audit_router)
    logger.info("[OK] [SECURITY] Audit API yklendi - System audit logging!")
except Exception as e:
    logger.error(f"[ERROR] Audit API yklenemedi: {str(e)}")

# Audit Logs API
try:
    from api.audit_logs_api import router as audit_logs_router

    app.include_router(audit_logs_router)
    logger.info("[OK] [SECURITY] Audit Logs API yklendi - Audit trail and compliance!")
except Exception as e:
    logger.error(f"[ERROR] Audit Logs API yklenemedi: {str(e)}")

# DDoS Management API
try:
    from api.ddos_management_api import router as ddos_management_router

    app.include_router(ddos_management_router)
    logger.info(
        "[OK] [SECURITY] DDoS Management API yklendi - DDoS monitoring and mitigation!"
    )
except Exception as e:
    logger.error(f"[ERROR] DDoS Management API yklenemedi: {str(e)}")

# Encryption Management API
try:
    from api.encryption_management import router as encryption_router

    app.include_router(encryption_router)
    logger.info(
        "[OK] [SECURITY] Encryption Management API yklendi - Encryption key management!"
    )
except Exception as e:
    logger.error(f"[ERROR] Encryption Management API yklenemedi: {str(e)}")

# KVKK Compliance API
try:
    from api.kvkk_api import router as kvkk_router

    app.include_router(kvkk_router)
    logger.info(
        "[OK] [SECURITY] KVKK Compliance API yklendi - Turkish privacy law compliance!"
    )
except Exception as e:
    logger.error(f"[ERROR] KVKK Compliance API yklenemedi: {str(e)}")

# PHASE 2 CRITICAL FIX: Major Feature APIs
# EBA TV Integration API (FIXED IMPORTS IN PHASE 1)
try:
    from api.eba_routes import router as eba_router

    app.include_router(eba_router)
    logger.info(
        "[OK] [VIDEO] EBA TV Integration API yklendi - Video catalog, watch tracking, curriculum alignment!"
    )
except Exception as e:
    logger.error(f"[ERROR] EBA TV API yklenemedi: {str(e)}")

# Khan Academy Integration API (FIXED IMPORTS IN PHASE 1)
try:
    from api.khan_routes import router as khan_router

    app.include_router(khan_router)
    logger.info(
        "[OK] [EDUCATION] Khan Academy Integration API yklendi - OAuth, content, progress sync, badges!"
    )
except Exception as e:
    logger.error(f"[ERROR] Khan Academy API yklenemedi: {str(e)}")

# Gamification System API
try:
    from api.gamification_api import router as gamification_router

    app.include_router(gamification_router)
    logger.info(
        "[OK] [GAME] Gamification System API yklendi - Badges, leaderboards, experience points, streaks!"
    )
except Exception as e:
    logger.error(f"[ERROR] Gamification API yklenemedi: {str(e)}")

# Question Bank v2.0 API (Next-Gen: CAT, Knowledge Graph, HITL)
try:
    from api.question_bank_v2_routes import router as question_bank_v2_router

    app.include_router(question_bank_v2_router)
    logger.info(
        "[OK] [V2] Question Bank v2.0 API yklendi - CAT, Knowledge Graph, HITL, Plagiarism Detection!"
    )
except Exception as e:
    logger.error(f"[ERROR] Question Bank v2.0 API yklenemedi: {str(e)}")

# OSYM Original Questions API (Authentic OSYM Exam Questions)
try:
    from api.osym_questions_api import router as osym_questions_router

    app.include_router(osym_questions_router)
    logger.info(
        "[OK] [GOLD] OSYM Original Questions API loaded - Authentic OSYM exam questions from PDF archives!"
    )
except Exception as e:
    logger.error(f"[ERROR] OSYM Questions API failed to load: {str(e)}")

# OSYM-Inspired Question Generation API (AI with Real OSYM Examples)
try:
    from api.osym_inspired_routes import router as osym_inspired_router

    app.include_router(osym_inspired_router)
    logger.info(
        "[OK] [STAR] OSYM-Inspired Question Generation API loaded - AI powered by 1988 real OSYM questions!"
    )
except Exception as e:
    logger.error(f"[ERROR] OSYM-Inspired API failed to load: {str(e)}")

# Hybrid Question Generation API (ÖSYM-Guided + Multi-Method)
try:
    from api.hybrid_question_generation import router as hybrid_question_router

    app.include_router(hybrid_question_router)
    logger.info(
        "[OK] [ROCKET] [STAR] Hybrid Question Generation API loaded - ÖSYM-guided AI with quality metrics!"
    )
except Exception as e:
    logger.error(f"[ERROR] Hybrid Question Generation API failed to load: {str(e)}")

# Production Quality Monitoring API (Wave 2B Enhanced Templates Monitoring)
try:
    from api.production_monitoring import router as production_monitoring_router

    app.include_router(production_monitoring_router)
    logger.info(
        "[OK] [CHART] Production Quality Monitoring API loaded - Real-time Wave 2B quality tracking!"
    )
except Exception as e:
    logger.error(f"[ERROR] Production Monitoring API failed to load: {str(e)}")


@app.get("/")
async def root():
    """Ana endpoint - sistem durumu"""
    return {
        "success": True,
        "message": "Trkiye niversite Snavlar Hazrlk Platformu aktif",
        "version": "1.0.0",
    }


# Health endpoint moved to api/health.py for comprehensive health checks
# See: backend/api/health.py for /health/ endpoint with full system monitoring


@app.get("/api/agents")
async def get_agents_direct():
    """Direct agents endpoint without router"""
    return [
        {
            "id": "matematik_uzman",
            "name": "Matematik Uzman",
            "description": "TYT ve AYT matematik sorularnda uzman AI asistan",
            "type": "subject_expert",
            "available": True,
            "specialties": ["matematik", "geometri"],
            "model": "gpt-4",
        }
    ]


# PHASE 2 FIX: Frontend-Backend Endpoint Mismatches
@app.post("/api/chat")
async def chat_redirect(request: dict):
    """Redirect to enhanced chat API (frontend compatibility)"""
    from fastapi import HTTPException

    # This is a compatibility endpoint that redirects to /api/v1/enhanced-chat/message
    # Frontend should be updated to use the correct endpoint
    raise HTTPException(
        status_code=301,
        detail="Please use /api/v1/enhanced-chat/message instead",
        headers={"Location": "/api/v1/enhanced-chat/message"},
    )


@app.delete("/api/clear")
async def clear_sessions(user_id: str = Query(...)):
    """Clear user sessions (frontend compatibility)"""
    try:
        from core.unified.auth_system import get_auth_manager

        # Get auth manager
        auth_manager = get_auth_manager()

        # Clear all sessions for the user
        cleared_count = auth_manager.end_all_user_sessions(user_id)

        # Also clear from Redis cache if available
        try:
            from core.cache import cache_manager

            if cache_manager._initialized:
                # Clear session-related cache keys
                session_keys = [
                    f"session:{user_id}:*",
                    f"user_sessions:{user_id}",
                    f"auth_context:{user_id}",
                ]
                for key_pattern in session_keys:
                    await cache_manager.delete(key_pattern)

                logger.info(
                    "user_sessions_cleared",
                    user_id=user_id,
                    cleared_count=cleared_count,
                    cache_cleared=True,
                )
        except Exception as cache_error:
            logger.warning(f"Cache clearing error: {cache_error}")

        return {
            "success": True,
            "message": f"Sessions cleared for user {user_id}",
            "cleared_count": cleared_count,
        }
    except Exception as e:
        logger.error(f"Session clearing error: {e}")
        return {
            "success": False,
            "message": f"Error clearing sessions: {str(e)}",
            "cleared_count": 0,
        }


# WebSocket balant yneticisi - DISABLED FOR NOW
# from websocket import ConnectionManager
# from fastapi import WebSocket, WebSocketDisconnect
# import json

# manager = ConnectionManager()

# @app.websocket("/ws/chat/{client_id}")
# async def websocket_chat_endpoint(websocket: WebSocket, client_id: str):
#     """Chat WebSocket endpoint"""
#     pass

# @app.websocket("/ws/sinav/{sinav_id}")
# async def websocket_exam_endpoint(websocket: WebSocket, sinav_id: str):
#     """Snav WebSocket endpoint - gerek zamanl snav gncellemeleri"""
#     pass

if __name__ == "__main__":
    uvicorn.run(
        app,  # Pass app object directly (not string) to avoid reimport
        host="0.0.0.0",
        port=8000,  # Port 8000 to match docker-compose config
        reload=False,  # DISABLED RELOAD TO FIX INFINITE LOOPS
        log_level="info",
    )
