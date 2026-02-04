# Main.py - FastAPI Backend Ana Uygulama
# Türkiye Üniversite Sınavları Hazırlık Platformu

"""
YKS (TYT/AYT/YDT) sınavlarına hazırlık için AI destekli eğitim platformu
"""

import os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# UTF-8 encoding ayarları
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlatma ve kapatma olayları"""
    print("[ROCKET] Türkiye Üniversite Sınavları Hazırlık Platformu başlatılıyor...")
    
    # Redis Cache Manager
    try:
        from core.cache import cache_manager
        cache_success = await cache_manager.initialize()
        if cache_success:
            print("[CHECK] Redis Cache Manager başlatıldı")
    except Exception as e:
        print(f"[X] Redis Cache başlatma hatası: {e}")
    
    # Database bağlantısı
    try:
        from core.database import init_database
        await init_database()
        print("[CHECK] Database bağlantısı başlatıldı")
    except Exception as e:
        print(f"[X] Database başlatma hatası: {e}")
    
    yield
    
    # Servisleri kapat
    print("👋 Platform kapatılıyor...")
    
    try:
        from core.cache import cache_manager
        await cache_manager.close()
        print("[CHECK] Redis Cache Manager kapatıldı")
    except:
        pass
    
    try:
        from core.database import close_database
        await close_database()
        print("[CHECK] Database bağlantısı kapatıldı")
    except:
        pass

# FastAPI uygulaması
app = FastAPI(
    title="Türkiye Üniversite Sınavları Hazırlık Platformu",
    description="YKS (TYT/AYT/YDT) sınavlarına hazırlık için AI destekli eğitim platformu",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router'ları dahil et
print("[BOOKS] API endpoint'leri yükleniyor...")

# Health Check
try:
    from api.health import router as health_router
    app.include_router(health_router)
    print("[CHECK] Health Check API'si yüklendi")
except:
    pass

# Sınav API
try:
    from api.sinav import router as sinav_router
    app.include_router(sinav_router)
    print("[CHECK] Sınav API'si yüklendi")
except:
    pass

# Öğrenme Stili API (64 Hibrit Profil)
try:
    from api.learning_style import router as learning_style_router
    app.include_router(learning_style_router)
    print("[CHECK] Hibrit Öğrenme Stili API'si yüklendi - 64 profil kombinasyonu hazır")
except:
    pass

# ZPD + Maarif API
try:
    from api.zpd_maarif import router as zpd_maarif_router
    app.include_router(zpd_maarif_router)
    print("[CHECK] ZPD + MEB Maarif API'si yüklendi")
except:
    pass

# IRT + Morfoloji API
try:
    from api.irt_morfoloji import router as irt_morfoloji_router
    app.include_router(irt_morfoloji_router)
    print("[CHECK] IRT + Türkçe Morfoloji API'si yüklendi")
except:
    pass

# Soru Bankası API
try:
    from api.soru_bankasi import router as soru_bankasi_router
    app.include_router(soru_bankasi_router)
    print("[CHECK] Soru Bankası API'si yüklendi - IRT parametreli adaptif soru seçimi")
except:
    pass

# Admin Panel API
try:
    from api.admin import router as admin_router
    app.include_router(admin_router)
    print("[CHECK] Admin Panel API'si yüklendi")
except:
    pass

# Öğretmen Paneli API
try:
    from api.ogretmen import router as ogretmen_router
    app.include_router(ogretmen_router)
    print("[CHECK] Öğretmen Paneli API'si yüklendi")
except:
    pass

# Veli Takip Sistemi API
try:
    from api.veli import router as veli_router
    app.include_router(veli_router)
    print("[CHECK] Veli Takip Sistemi API'si yüklendi")
except:
    pass

# EBA TV API
try:
    from api.ebatv import router as ebatv_router
    app.include_router(ebatv_router)
    print("[CHECK] EBA TV API'si yüklendi")
except:
    pass

# YouTube API
try:
    from fast_youtube_endpoint import router as fast_youtube_router
    app.include_router(fast_youtube_router)
    print("[CHECK] Fast YouTube API yüklendi - <200ms response time!")
except:
    pass

@app.get("/")
async def root():
    """Ana endpoint - sistem durumu"""
    return {
        "success": True,
        "message": "Türkiye Üniversite Sınavları Hazırlık Platformu aktif",
        "version": "1.0.0",
        "features": [
            "64 Hibrit Öğrenme Profili",
            "ÖSYM Uyumlu Sınav Motoru",
            "IRT + Türkçe Morfoloji",
            "ZPD + MEB Maarif Sistemi",
            "RAG ile Zenginleştirilmiş İçerik"
        ]
    }

@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    return {
        "success": True,
        "status": "healthy",
        "message": "Sistem çalışıyor"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )