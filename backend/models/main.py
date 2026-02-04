"""
Main Application - FastAPI Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# API Router'ları import et
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.content_api import router as content_router

# FastAPI app oluştur
app = FastAPI(
    title="YKS Hazırlık Platformu API",
    description="Teknofest 2025 - Eğitim Teknolojileri",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da güncelle
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(content_router)


# Root endpoint
@app.get("/")
async def root():
    """Ana endpoint"""
    return {
        "success": True,
        "message": "YKS Hazırlık Platformu API aktif",
        "version": "1.0.0",
        "endpoints": ["/docs - API Dokümantasyonu", "/api/v1/content - İçerik API'si"],
    }


# Health check
@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    return {"status": "healthy", "service": "main_api"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
