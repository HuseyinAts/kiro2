"""
CORS Security Configuration Modülü
Task 23: Security Hardening - CORS policy güncelleme

Bu modül güvenli CORS yapılandırması sağlar.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.structured_logger import get_logger

logger = get_logger("cors_security")


class CORSConfig:
    """CORS yapılandırma sınıfı"""

    # Production origins (whitelist)
    PRODUCTION_ORIGINS = [
        "https://kiro2.app",
        "https://www.kiro2.app",
        "https://api.kiro2.app",
        "https://teknofest-egitim.com",
        "https://www.teknofest-egitim.com",
    ]

    # Development origins
    DEVELOPMENT_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ]

    # Test origins
    TEST_ORIGINS = ["http://testserver", "http://localhost:8000"]

    @staticmethod
    def get_allowed_origins() -> list[str]:
        """
        Environment'a göre izin verilen origin'leri döndür

        Returns:
            İzin verilen origin listesi
        """
        environment = os.getenv("ENVIRONMENT", "development").lower()

        if environment == "production":
            # Production: Sadece whitelist'teki domain'ler
            origins = CORSConfig.PRODUCTION_ORIGINS.copy()

            # Environment variable'dan ek origin'ler
            extra_origins = os.getenv("EXTRA_CORS_ORIGINS", "")
            if extra_origins:
                origins.extend([o.strip() for o in extra_origins.split(",")])

            logger.info("CORS configured for PRODUCTION", allowed_origins=origins)

        elif environment == "test":
            # Test: Test origin'leri
            origins = CORSConfig.TEST_ORIGINS.copy()

            logger.info("CORS configured for TEST", allowed_origins=origins)

        else:
            # Development: Localhost origin'leri
            origins = CORSConfig.DEVELOPMENT_ORIGINS.copy()

            logger.info("CORS configured for DEVELOPMENT", allowed_origins=origins)

        return origins

    @staticmethod
    def get_allowed_methods() -> list[str]:
        """
        İzin verilen HTTP metodları

        Returns:
            İzin verilen method listesi
        """
        return ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

    @staticmethod
    def get_allowed_headers() -> list[str]:
        """
        İzin verilen HTTP header'ları

        Returns:
            İzin verilen header listesi
        """
        return [
            "Authorization",
            "Content-Type",
            "Accept",
            "X-Request-ID",
            "X-API-Key",
            "X-CSRF-Token",
        ]

    @staticmethod
    def get_exposed_headers() -> list[str]:
        """
        Client'a expose edilecek header'lar

        Returns:
            Expose edilecek header listesi
        """
        return [
            "X-Request-ID",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Response-Time",
        ]

    @staticmethod
    def should_allow_credentials() -> bool:
        """
        Credential'lara izin verilmeli mi?

        Returns:
            True if credentials allowed
        """
        # Production'da credential'lar için daha dikkatli olmalıyız
        environment = os.getenv("ENVIRONMENT", "development").lower()

        if environment == "production":
            # Production'da sadece specific origin'ler için credential
            return True
        # Development'ta credential'lara izin ver
        return True

    @staticmethod
    def get_max_age() -> int:
        """
        Preflight request cache süresi (saniye)

        Returns:
            Max age in seconds
        """
        return 3600  # 1 saat


def setup_cors(app: FastAPI) -> None:
    """
    CORS middleware'ini yapılandır ve ekle

    Args:
        app: FastAPI application
    """
    config = CORSConfig()

    # CORS middleware ekle
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get_allowed_origins(),
        allow_credentials=config.should_allow_credentials(),
        allow_methods=config.get_allowed_methods(),
        allow_headers=config.get_allowed_headers(),
        expose_headers=config.get_exposed_headers(),
        max_age=config.get_max_age(),
    )

    logger.info(
        "CORS middleware configured",
        origins_count=len(config.get_allowed_origins()),
        allow_credentials=config.should_allow_credentials(),
        methods=config.get_allowed_methods(),
    )


def validate_origin(origin: str) -> bool:
    """
    Origin'in izin verilen listede olup olmadığını kontrol et

    Args:
        origin: Request origin

    Returns:
        True if allowed, False otherwise
    """
    allowed_origins = CORSConfig.get_allowed_origins()

    # Exact match
    if origin in allowed_origins:
        return True

    # Wildcard subdomain match (*.example.com)
    for allowed in allowed_origins:
        if allowed.startswith("*."):
            domain = allowed[2:]  # Remove *.
            if origin.endswith(domain):
                return True

    return False


# CORS preflight response helper
def create_preflight_response():
    """
    CORS preflight request için response oluştur

    Returns:
        Preflight response
    """
    from fastapi.responses import Response

    config = CORSConfig()

    response = Response(status_code=200)
    response.headers["Access-Control-Allow-Methods"] = ", ".join(
        config.get_allowed_methods()
    )
    response.headers["Access-Control-Allow-Headers"] = ", ".join(
        config.get_allowed_headers()
    )
    response.headers["Access-Control-Max-Age"] = str(config.get_max_age())

    return response


# Example usage:
"""
from fastapi import FastAPI
from core.cors_security import setup_cors

app = FastAPI()

# CORS'u yapılandır
setup_cors(app)

# Veya manuel kontrol
from core.cors_security import validate_origin

@app.middleware("http")
async def cors_validation_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    
    if origin and not validate_origin(origin):
        return JSONResponse(
            status_code=403,
            content={"detail": "Origin not allowed"}
        )
    
    response = await call_next(request)
    return response
"""
