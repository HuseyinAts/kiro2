"""
Database Package
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu
"""

from .connection import (
    cleanup_database,
    database_health_check,
    db_manager,
    get_async_session,
    get_async_session_context,
    get_sync_session,
    init_database,
)

# from .models import *  # Commented out - models are in models/ directory
from .repositories import (
    EgitimIcerigiRepository,
    KullaniciRepository,
    KulturelBaglamRepository,
    MaarifDegerleriRepository,
    MetrikRepository,
    OgrenciRepository,
    OgrenmeOturumuRepository,
    OgrenmeStiliRepository,
    SinavCevabiRepository,
    SinavRepository,
    SinavSonucuRepository,
    SoruRepository,
)

__all__ = [
    # Models
    "Base",
    "Kullanici",
    "OgrenciProfili",
    "OgretmenProfili",
    "VeliProfili",
    "SinavSablonu",
    "Sinav",
    "SoruBankasi",
    "SinavCevabi",
    "SinavSonucu",
    "OgrenmeStiliProfili",
    "KulturelBaglamProfili",
    "MaarifDegerleriProfili",
    "OgrenmeOturumu",
    "EgitimIcerigi",
    "SistemMetrikleri",
    "AgentPerformansMetrikleri",
    # Enums
    "KullaniciRolu",
    "SinavTipi",
    "ZorlukSeviyesi",
    "OgrenmeStili",
    # Connection
    "db_manager",
    "get_async_session",
    "get_async_session_context",
    "get_sync_session",
    "init_database",
    "cleanup_database",
    "database_health_check",
    # Repositories
    "KullaniciRepository",
    "OgrenciRepository",
    "SinavRepository",
    "SoruRepository",
    "SinavCevabiRepository",
    "SinavSonucuRepository",
    "OgrenmeStiliRepository",
    "KulturelBaglamRepository",
    "MaarifDegerleriRepository",
    "OgrenmeOturumuRepository",
    "EgitimIcerigiRepository",
    "MetrikRepository",
]
