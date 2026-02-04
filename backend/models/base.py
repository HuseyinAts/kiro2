"""
SQLAlchemy Base Declarative
Circular import'u önlemek için Base ayrı dosyada
"""

from sqlalchemy.orm import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()
