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
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:3001"],
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

# ── KIRO2 CAT/FSRS/DAG/Placement/Estimator Router'lar ───────────────────────
try:
    from app.api.cat import router as cat_router

    app.include_router(cat_router)
    from app.api.fsrs import router as fsrs_router

    app.include_router(fsrs_router)
    from app.api.dag import router as dag_router

    app.include_router(dag_router)
    from app.api.placement import router as placement_router

    app.include_router(placement_router)
    from app.api.estimator import router as estimator_router

    app.include_router(estimator_router)
    from app.api.calibration_api import router as calibration_router

    app.include_router(calibration_router)
    logger.info(
        "KIRO2 CAT+FSRS+DAG+Placement+Estimator+Calibration routerlari yuklendi"
    )
except Exception as e:
    logger.warning(f"KIRO2 router yukleme hatasi (non-critical): {e}")

# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    uvicorn.run("main:app", host=host, port=port, reload=reload)
