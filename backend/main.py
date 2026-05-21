"""
KIRO2 Educational Platform - Main Application

Minimal main.py using application factory pattern.
All routers are dynamically loaded from the routers module.
"""

import io
import logging
import os
import sys
from pathlib import Path

# UTF-8 encoding fix for Windows
if sys.platform == "win32" and os.environ.get("TESTING") != "true":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend directory to Python path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("kiro2_backend.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

try:
    from core.application import create_app

    logger.info("Using modular application factory")
except ImportError as e:
    logger.warning(f"Falling back to minimal app: {e}")
    from collections.abc import AsyncGenerator
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    @asynccontextmanager
    async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("KIRO2 Backend Starting (Fallback Mode)...")
        yield
        logger.info("KIRO2 Backend Shutting Down...")

    def create_app() -> FastAPI:
        app = FastAPI(
            title="KIRO2 Educational Platform", version="1.0.0", lifespan=app_lifespan
        )
        # CORS origins from ALLOWED_ORIGINS env (comma-separated). Falls back to
        # localhost dev URLs only when running locally; production deploys MUST
        # set ALLOWED_ORIGINS or all browser requests will be silently rejected.
        _allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "").strip()
        if _allowed_origins_env:
            _allowed_origins = [
                origin.strip()
                for origin in _allowed_origins_env.split(",")
                if origin.strip()
            ]
        elif os.environ.get("ENVIRONMENT", "").lower() in ("production", "prod"):
            logger.error(
                "ALLOWED_ORIGINS unset in production — refusing to start with "
                "localhost-only CORS that would silently reject the real frontend."
            )
            raise RuntimeError("ALLOWED_ORIGINS env var required in production")
        else:
            _allowed_origins = ["http://localhost:3000", "http://localhost:3001"]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=_allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/")
        async def root():
            return {"app": "KIRO2", "status": "online"}

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        try:
            from routers.loader import setup_routers

            setup_routers(app)
            logger.info("Routers loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load routers: {e}")
        return app


# Create application instance
app = create_app()

# NOTE: CAT/FSRS/DAG/Placement/Estimator/Calibration routers are registered
# via core/application.py setup_routers(). No need to duplicate here.

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    uvicorn.run("main:app", host=host, port=port, reload=reload)
