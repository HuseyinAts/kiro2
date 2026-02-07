"""
SQLAlchemy Base Declarative
Circular import'u onlemek icin Base ayri dosyada

IMPORTANT: models/ icindeki dosyalar SADECE relative import kullanmali:
    from .base import Base        # DOGRU
    from .database import Base    # DOGRU
    from models.base import Base  # YANLIS - cift MetaData olusturur!

Bu kural scripts/check_model_imports.py ile CI'da kontrol edilir.
"""

from sqlalchemy.orm import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()
