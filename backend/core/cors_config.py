"""
Advanced CORS Configuration
Production-ready CORS setup with security features and environment-based configuration
"""
import os
import re
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import get_settings
from core.structured_logger import get_logger


class CORSConfig(BaseModel):
    """CORS konfigürasyon modeli"""

    allow_origins: list[str] = []
    allow_origin_regex: str | None = None
    allow_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    allow_headers: list[str] = []
    allow_credentials: bool = True
    expose_headers: list[str] = []
    max_age: int = 600  # 10 dakika


class AdvancedCORSManager:
    """Gelişmiş CORS yönetimi"""

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("cors_manager")
        self.config = self._load_cors_config()

    def _load_cors_config(self) -> CORSConfig:
        """Environment'a göre CORS konfigürasyonu yükle"""
        environment = getattr(self.settings, "environment", "development")

        if environment == "production":
            return self._get_production_config()
        if environment == "testing":
            return self._get_testing_config()
        return self._get_development_config()

    def _get_production_config(self) -> CORSConfig:
        """Production CORS konfigürasyonu"""
        # Production'da sadece belirli domain'lere izin ver
        allowed_origins = []

        # Environment variable'dan allowed origins'i al
        env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        if env_origins:
            allowed_origins = [origin.strip() for origin in env_origins.split(",")]

        # Default production origins
        if not allowed_origins:
            allowed_origins = [
                "https://yourdomain.com",
                "https://www.yourdomain.com",
                "https://app.yourdomain.com",
            ]

        # Validate origins
        validated_origins = []
        for origin in allowed_origins:
            if self._validate_origin(origin):
                validated_origins.append(origin)
            else:
                self.logger.warning(f"Invalid origin in production config: {origin}")

        return CORSConfig(
            allow_origins=validated_origins,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=[
                "Accept",
                "Accept-Language",
                "Authorization",
                "Content-Type",
                "X-Requested-With",
                "X-CSRF-Token",
                "X-Request-ID",
                "X-API-Key",
            ],
            allow_credentials=True,
            expose_headers=[
                "X-Total-Count",
                "X-Page-Count",
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
            ],
            max_age=3600,  # 1 saat
        )

    def _get_development_config(self) -> CORSConfig:
        """Development CORS konfigürasyonu"""
        return CORSConfig(
            allow_origins=[
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:3002",
                "http://localhost:3003",
                "http://localhost:5173",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ],
            allow_origin_regex=r"http://localhost:\d+",
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
            expose_headers=["*"],
            max_age=600,
        )

    def _get_testing_config(self) -> CORSConfig:
        """Testing CORS konfigürasyonu"""
        return CORSConfig(
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=False,  # Testing'de credentials gerekli değil
            expose_headers=["*"],
            max_age=0,  # Cache yok
        )

    def _validate_origin(self, origin: str) -> bool:
        """Origin URL'ini validate et"""
        try:
            # Wildcard kontrolü
            if origin == "*":
                return True

            # URL parse et
            parsed = urlparse(origin)

            # Scheme kontrolü
            if parsed.scheme not in ["http", "https"]:
                return False

            # Host kontrolü
            if not parsed.netloc:
                return False

            # Güvenlik kontrolleri
            if self._is_suspicious_origin(origin):
                return False

            return True

        except Exception:
            return False

    def _is_suspicious_origin(self, origin: str) -> bool:
        """Şüpheli origin kontrolü"""
        suspicious_patterns = [
            r".*\.onion$",  # Tor network
            r".*localhost.*",  # Production'da localhost izin verilmemeli
            r".*127\.0\.0\.1.*",
            r".*\.\d+\.\d+\.\d+$",  # Raw IP addresses
            r".*[^a-zA-Z0-9\-\.].*",  # Invalid characters
        ]

        for pattern in suspicious_patterns:
            if re.match(pattern, origin, re.IGNORECASE):
                return True

        return False

    def configure_cors(self, app: FastAPI):
        """FastAPI uygulamasına CORS middleware'ini ekle"""
        # Mevcut CORS middleware'ini kaldır (varsa)
        self._remove_existing_cors_middleware(app)

        # Yeni CORS middleware ekle
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.allow_origins,
            allow_origin_regex=self.config.allow_origin_regex,
            allow_credentials=self.config.allow_credentials,
            allow_methods=self.config.allow_methods,
            allow_headers=self.config.allow_headers,
            expose_headers=self.config.expose_headers,
            max_age=self.config.max_age,
        )

        self.logger.info(
            f"CORS configured for {self.settings.environment} environment",
            extra_data={
                "allowed_origins": self.config.allow_origins,
                "allow_credentials": self.config.allow_credentials,
                "environment": getattr(self.settings, "environment", "unknown"),
            },
        )

    def _remove_existing_cors_middleware(self, app: FastAPI):
        """Mevcut CORS middleware'ini kaldır"""
        # Bu metot FastAPI'nin middleware stack'ini temizlemek için
        # Genellikle gerekli değil ama güvenlik için

    def add_trusted_origin(self, origin: str):
        """Güvenilir origin ekle"""
        if self._validate_origin(origin) and origin not in self.config.allow_origins:
            self.config.allow_origins.append(origin)
            self.logger.info(f"Added trusted origin: {origin}")

    def remove_origin(self, origin: str):
        """Origin'i kaldır"""
        if origin in self.config.allow_origins:
            self.config.allow_origins.remove(origin)
            self.logger.info(f"Removed origin: {origin}")

    def is_origin_allowed(self, origin: str) -> bool:
        """Origin'in izin verilip verilmediğini kontrol et"""
        # Wildcard kontrolü
        if "*" in self.config.allow_origins:
            return True

        # Direct match
        if origin in self.config.allow_origins:
            return True

        # Regex match
        if self.config.allow_origin_regex:
            try:
                if re.match(self.config.allow_origin_regex, origin):
                    return True
            except re.error:
                self.logger.error(
                    f"Invalid origin regex: {self.config.allow_origin_regex}"
                )

        return False

    def get_cors_headers(
        self, request_origin: str, request_method: str
    ) -> dict[str, str]:
        """CORS header'larını manuel olarak oluştur"""
        headers = {}

        # Origin kontrolü
        if self.is_origin_allowed(request_origin):
            headers["Access-Control-Allow-Origin"] = request_origin

        # Credentials
        if self.config.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        # Methods
        if request_method == "OPTIONS":
            headers["Access-Control-Allow-Methods"] = ", ".join(
                self.config.allow_methods
            )
            headers["Access-Control-Allow-Headers"] = ", ".join(
                self.config.allow_headers
            )
            headers["Access-Control-Max-Age"] = str(self.config.max_age)

        # Expose headers
        if self.config.expose_headers:
            headers["Access-Control-Expose-Headers"] = ", ".join(
                self.config.expose_headers
            )

        return headers

    def validate_preflight_request(
        self, origin: str, method: str, headers: list[str]
    ) -> bool:
        """Preflight request'i validate et"""
        # Origin kontrolü
        if not self.is_origin_allowed(origin):
            return False

        # Method kontrolü
        if (
            method not in self.config.allow_methods
            and "*" not in self.config.allow_methods
        ):
            return False

        # Headers kontrolü
        if "*" not in self.config.allow_headers:
            for header in headers:
                if header.lower() not in [h.lower() for h in self.config.allow_headers]:
                    return False

        return True


class SecureCORSMiddleware:
    """Güvenli CORS middleware (manuel implementation)"""

    def __init__(self, cors_manager: AdvancedCORSManager):
        self.cors_manager = cors_manager
        self.logger = get_logger("secure_cors")

    async def __call__(self, request, call_next):
        """Middleware handler"""
        origin = request.headers.get("origin")
        method = request.method

        # Preflight request kontrolü
        if method == "OPTIONS":
            return await self._handle_preflight(request, origin)

        # Normal request işle
        response = await call_next(request)

        # CORS header'larını ekle
        if origin:
            cors_headers = self.cors_manager.get_cors_headers(origin, method)
            for key, value in cors_headers.items():
                response.headers[key] = value

        return response

    async def _handle_preflight(self, request, origin: str):
        """Preflight request'i handle et"""
        from fastapi import Response

        # Requested method ve headers
        requested_method = request.headers.get("access-control-request-method", "")
        requested_headers = request.headers.get("access-control-request-headers", "")

        # Headers'ı parse et
        header_list = (
            [h.strip() for h in requested_headers.split(",")]
            if requested_headers
            else []
        )

        # Validation
        if not self.cors_manager.validate_preflight_request(
            origin, requested_method, header_list
        ):
            self.logger.warning(
                f"Invalid preflight request from {origin}",
                extra_data={
                    "origin": origin,
                    "method": requested_method,
                    "headers": header_list,
                },
            )
            return Response(status_code=403)

        # CORS headers oluştur
        headers = self.cors_manager.get_cors_headers(origin, "OPTIONS")

        return Response(status_code=200, headers=headers)


# Environment detection utility
def detect_environment() -> str:
    """Çalışma ortamını tespit et"""
    # Environment variable
    env = os.getenv("ENVIRONMENT", "").lower()
    if env in ["production", "prod"]:
        return "production"
    if env in ["testing", "test"]:
        return "testing"
    if env in ["development", "dev"]:
        return "development"

    # Debug mode kontrolü
    if os.getenv("DEBUG", "").lower() in ["true", "1"]:
        return "development"

    # Port kontrolü (basit heuristic)
    port = os.getenv("PORT", "8000")
    if port in ["80", "443", "8080"]:
        return "production"

    # Default
    return "development"


# Factory function
def create_cors_manager() -> AdvancedCORSManager:
    """CORS manager oluştur"""
    return AdvancedCORSManager()


# Global instance
cors_manager = create_cors_manager()


def get_cors_manager() -> AdvancedCORSManager:
    """CORS manager instance'ını döndür"""
    return cors_manager


def setup_cors(app: FastAPI):
    """FastAPI uygulamasına CORS setup'ı yap"""
    cors_manager.configure_cors(app)
