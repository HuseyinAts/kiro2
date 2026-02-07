"""
KIRO2 Educational Platform - Main Application

Minimal main.py using application factory pattern.
All routers are dynamically loaded from the routers module.
"""

import logging
import sys
import os
import io
from pathlib import Path

# UTF-8 encoding fix for Windows (skip during testing to preserve pytest capture)
if sys.platform == 'win32' and os.environ.get('TESTING') != 'true':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend directory to Python path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('kiro2_backend.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Import application factory
try:
    from core.application import create_app
    logger.info("✅ Using modular application factory")
except ImportError as e:
    logger.error(f"❌ Could not import application factory: {e}")
    logger.info("⚠️ Using fallback application configuration")
    
    # Fallback for compatibility
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from contextlib import asynccontextmanager
    from typing import AsyncGenerator
    
    @asynccontextmanager
    async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Application lifespan management."""
        logger.info("=" * 60)
        logger.info("🚀 KIRO2 Backend Starting (Fallback Mode)...")
        logger.info("=" * 60)
        yield
        logger.info("🛑 KIRO2 Backend Shutting Down...")
    
    def create_app() -> FastAPI:
        """Fallback application factory."""
        app = FastAPI(
            title="KIRO2 Educational Platform",
            version="1.0.0",
            description="AI-powered educational platform for Turkish students",
            lifespan=app_lifespan
        )
        
        # Basic CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:3001"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Basic endpoints
        @app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "app": "KIRO2 Educational Platform",
                "version": "1.0.0",
                "status": "online",
                "mode": "fallback"
            }
        
        @app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy"}
        
        @app.get("/health/ready")
        async def ready():
            """Readiness check endpoint."""
            return {"status": "ready"}
        
        @app.get("/health/live")
        async def live():
            """Liveness check endpoint."""
            return {"status": "alive"}
        
        # Try to load routers if available
        try:
            from routers.loader import setup_routers
            setup_routers(app)
            logger.info("✅ Routers loaded successfully")
        except ImportError as e:
            logger.warning(f"⚠️ Could not load routers: {e}")
            logger.info("Running in minimal mode with basic endpoints only")
        
        return app

# Create application instance
app = create_app()

# Add custom event handlers if needed
@app.on_event("startup")
async def startup_event():
    """Additional startup tasks."""
    logger.info("✅ Custom startup tasks completed")

@app.on_event("shutdown") 
async def shutdown_event():
    """Additional shutdown tasks."""
    logger.info("✅ Custom shutdown tasks completed")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    logger.info("=" * 60)
    logger.info("🚀 Starting KIRO2 Backend Server")
    logger.info(f"  Host: {host}")
    logger.info(f"  Port: {port}")
    logger.info(f"  Reload: {reload}")
    logger.info(f"  API Docs: http://localhost:{port}/docs")
    logger.info("=" * 60)
    
    # Run server
    uvicorn.run(
        "main:app" if not reload else "main_new:app",
        host=host,
        port=port,
        reload=reload,
        access_log=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )