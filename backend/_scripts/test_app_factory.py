"""
Test App Factory
Test için minimal FastAPI app oluşturma factory
Circular import sorunlarını önler
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_test_app(include_db=False, include_auth=False, routers=None):
    """
    Test için minimal FastAPI app oluştur

    Args:
        include_db: Database bağlantısı ekle
        include_auth: Authentication middleware ekle
        routers: Include edilecek router listesi

    Returns:
        FastAPI app instance
    """
    app = FastAPI(
        title="Test App",
        description="Minimal app for testing",
        version="1.0.0",
        docs_url=None,  # Swagger UI kapalı
        redoc_url=None,  # ReDoc kapalı
    )

    # CORS middleware ekle
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Router'ları ekle
    if routers:
        for router in routers:
            app.include_router(router)

    return app


def create_api_test_app(api_module_name: str):
    """
    Belirli bir API modülü için test app oluştur

    Args:
        api_module_name: API modül adı (örn: 'health', 'auth', 'admin')

    Returns:
        FastAPI app with router included
    """
    app = create_test_app()

    try:
        # Dinamik import
        api_module = __import__(f"api.{api_module_name}", fromlist=["router"])

        if hasattr(api_module, "router"):
            app.include_router(api_module.router)

    except ImportError as e:
        print(f"Warning: Could not import api.{api_module_name}: {e}")

    return app


# Commonly used test apps
def create_health_test_app():
    """Health API için test app"""
    return create_api_test_app("health")


def create_auth_test_app():
    """Auth API için test app"""
    return create_api_test_app("auth")


def create_admin_test_app():
    """Admin API için test app"""
    return create_api_test_app("admin")


def create_agents_test_app():
    """Agents API için test app"""
    return create_api_test_app("agents")
