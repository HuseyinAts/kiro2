"""
KIRO2 Router Registry

Tüm router'ların merkezi yönetimi ve organizasyonu.
"""

from typing import Dict, List, Tuple, Optional
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

# Router kategorileri ve açıklamaları
ROUTER_CATEGORIES = {
    "health": "Sistem sağlık kontrolleri",
    "auth": "Kimlik doğrulama ve yetkilendirme",
    "exam": "Sınav yönetimi ve değerlendirme",
    "learning": "Öğrenme yolları ve stil analizleri",
    "content": "İçerik yönetimi ve soru bankası",
    "ai": "Yapay zeka ve NLP servisleri",
    "integrations": "Dış servis entegrasyonları",
    "admin": "Yönetici paneli işlemleri",
    "accessibility": "Erişilebilirlik özellikleri",
    "analytics": "Analitik ve raporlama",
    "security": "Güvenlik ve uyumluluk",
}

class RouterRegistry:
    """Router kayıt ve yönetim sistemi."""
    
    def __init__(self):
        self.routers: Dict[str, List[Tuple[str, APIRouter, str]]] = {
            category: [] for category in ROUTER_CATEGORIES
        }
        self.failed_imports: List[str] = []
    
    def register(self, category: str, name: str, router: APIRouter, prefix: str = None):
        """Router'ı kaydet."""
        if category not in self.routers:
            logger.warning(f"Unknown category: {category}")
            category = "misc"
            if category not in self.routers:
                self.routers[category] = []
        
        if prefix is None:
            prefix = f"/api/{name.replace('_', '-')}"
        
        self.routers[category].append((name, router, prefix))
        logger.info(f"✅ Registered {category}/{name} at {prefix}")
    
    def register_failed(self, name: str, error: str):
        """Başarısız import'u kaydet."""
        self.failed_imports.append(f"{name}: {error}")
        logger.warning(f"⚠️ Failed to import {name}: {error}")
    
    def get_all_routers(self) -> List[Tuple[str, APIRouter, str]]:
        """Tüm router'ları düz liste olarak döndür."""
        all_routers = []
        for category_routers in self.routers.values():
            all_routers.extend(category_routers)
        return all_routers
    
    def get_summary(self) -> Dict[str, int]:
        """Özet istatistikleri döndür."""
        return {
            "total": sum(len(r) for r in self.routers.values()),
            "categories": len([c for c in self.routers if len(self.routers[c]) > 0]),
            "failed": len(self.failed_imports),
            **{f"{cat}_count": len(self.routers[cat]) for cat in self.routers}
        }

# Global registry instance
router_registry = RouterRegistry()