"""
API Schemas Package
Shared Pydantic models for API contracts
"""

from .learning_path_schemas import (
    LearningPathCreateRequest,
    StudentProfileData,
    ResourceSearchRequest,
)

__all__ = [
    "LearningPathCreateRequest",
    "StudentProfileData",
    "ResourceSearchRequest",
]
