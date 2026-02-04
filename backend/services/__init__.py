"""
Servis katmanı - Türkiye Üniversite Sınavları Hazırlık Platformu
"""

# Lazy imports to avoid circular dependencies
admin_servisi = None
kullanici_servisi = None
soru_bankasi_servisi = None


def _get_admin_servisi():
    global admin_servisi
    if admin_servisi is None:
        from .admin_service import admin_servisi as _admin

        admin_servisi = _admin
    return admin_servisi


def _get_kullanici_servisi():
    global kullanici_servisi
    if kullanici_servisi is None:
        from .user_service import kullanici_servisi as _user

        kullanici_servisi = _user
    return kullanici_servisi


def _get_soru_bankasi_servisi():
    global soru_bankasi_servisi
    if soru_bankasi_servisi is None:
        try:
            from .soru_bankasi_service import soru_bankasi_servisi as _soru

            soru_bankasi_servisi = _soru
        except ImportError:
            pass
    return soru_bankasi_servisi


__all__ = ["admin_servisi", "kullanici_servisi", "soru_bankasi_servisi"]
