"""
Telemetry stub endpoints.

Frontend'in web-vitals ve error report isteklerini kabul eder.
Henuz backend'de islenmiyor — 404 console hatalarini onlemek icin stub.
"""

import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["telemetry"])


@router.post("/analytics/web-vitals", status_code=204)
async def receive_web_vitals(request: Request):
    """Web Vitals metrikleri — kabul et, logla."""
    try:
        body = await request.body()
        logger.debug("Web Vitals: %s", body[:500])
    except Exception:
        pass


@router.post("/errors/report", status_code=204)
async def receive_error_report(request: Request):
    """Frontend hata raporu — kabul et, logla."""
    try:
        body = await request.body()
        logger.warning("Frontend error: %s", body[:1000])
    except Exception:
        pass
