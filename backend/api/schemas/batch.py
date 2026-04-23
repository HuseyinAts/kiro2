"""
Batch API Schemas - Request Batching for API Response Time Optimization.

Bu modul, birden fazla API isleminin tek bir istekte birlestirilmesini saglar.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class HTTPMethod(str, Enum):
    """Desteklenen HTTP metodlari."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class BatchOperation(BaseModel):
    """Tek bir batch islemi."""

    id: str | None = Field(default=None, max_length=100)
    method: HTTPMethod = Field(...)
    path: str = Field(..., min_length=1, max_length=500)
    body: dict[str, Any] | None = Field(default=None)
    headers: dict[str, str] | None = Field(default=None)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Path dogrulamasi."""
        v = v.strip()
        if not v.startswith("/"):
            v = "/" + v
        if ".." in v:
            raise ValueError("Path traversal karakterleri izin verilmez")
        return v


class BatchRequest(BaseModel):
    """Batch API istegi."""

    operations: list[BatchOperation] = Field(..., min_length=1, max_length=10)
    atomic: bool = Field(default=False)
    continue_on_error: bool = Field(default=True)

    @field_validator("operations")
    @classmethod
    def validate_operations_count(
        cls, v: list[BatchOperation]
    ) -> list[BatchOperation]:
        """Islem sayisi dogrulamasi (REQ-3.2)."""
        if len(v) > 10:
            raise ValueError(f"Maksimum 10 islem, {len(v)} gonderildi")
        return v

    @model_validator(mode="after")
    def validate_atomic_settings(self) -> "BatchRequest":
        """Atomic ve continue_on_error uyumlulugu."""
        if self.atomic and self.continue_on_error:
            object.__setattr__(self, "continue_on_error", False)
        return self


class OperationResult(BaseModel):
    """Tek bir batch isleminin sonucu (REQ-3.3)."""

    id: str | None = Field(default=None)
    index: int = Field(..., ge=0)
    status_code: int = Field(..., ge=100, le=599)
    success: bool = Field(...)
    data: Any | None = Field(default=None)
    error: str | None = Field(default=None)
    duration_ms: float = Field(..., ge=0)


class BatchResponse(BaseModel):
    """Batch API yaniti."""

    results: list[OperationResult] = Field(...)
    success_count: int = Field(..., ge=0)
    failure_count: int = Field(..., ge=0)
    total_count: int = Field(..., ge=1)
    execution_time_ms: float = Field(..., ge=0)
    atomic_success: bool | None = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def all_successful(self) -> bool:
        """Tum islemler basarili mi."""
        return self.failure_count == 0


class BatchErrorDetail(BaseModel):
    """Batch hata detayi (REQ-3.6)."""

    operation_index: int = Field(..., ge=0)
    operation_id: str | None = Field(default=None)
    error_code: str = Field(...)
    error_message: str = Field(...)
    path: str = Field(...)
