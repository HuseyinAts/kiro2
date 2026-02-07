"""
Sparse Fieldset Destegi - Dinamik Alan Secimi icin Pydantic Mixin.

Bu modul, API response'larinda sadece istenen alanlarin donmesini saglayan
sparse fieldset destegi sunar. JSON:API sparse fieldsets standardina
uygun olarak ?fields= query parametresi ile alan filtreleme yapilabilir.

Ozellikler:
    - SparseFieldsetMixin: Pydantic modelleri icin mixin sinifi
    - ?fields= query parametresi destegi
    - Dinamik alan secimi ve validasyonu
    - Payload boyutu optimizasyonu

Requirements: REQ-7.2

Example:
    >>> from backend.api.schemas.sparse_fieldset import SparseFieldsetMixin
    >>>
    >>> class UserResponse(SparseFieldsetMixin):
    >>>     id: int
    >>>     name: str
    >>>     email: str
    >>>     created_at: datetime
    >>>
    >>> # Sadece id ve name alanlarini don
    >>> # GET /users/1?fields=id,name
    >>> user = UserResponse(id=1, name="Ali", email="ali@test.com", created_at=...)
    >>> filtered = user.filter_fields(["id", "name"])
    >>> # {"id": 1, "name": "Ali"}
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="SparseFieldsetMixin")


def parse_fields_param(
    fields: str | None = Query(
        default=None,
        description="Virgul ile ayrilmis alan listesi (ornek: id,name,email)",
        examples=["id,name", "id,name,created_at"],
    )
) -> list[str] | None:
    """
    FastAPI dependency olarak ?fields= query parametresini parse eder.

    Args:
        fields: Virgul ile ayrilmis alan isimleri.

    Returns:
        Alan isimlerinin listesi veya None.

    Example:
        >>> @app.get("/users/{user_id}")
        >>> async def get_user(
        >>>     user_id: int,
        >>>     fields: list[str] | None = Depends(parse_fields_param)
        >>> ):
        >>>     user = await get_user_by_id(user_id)
        >>>     if fields:
        >>>         return user.filter_fields(fields)
        >>>     return user
    """
    if fields is None:
        return None

    # Bosluk ve virgulleri temizle
    field_list = [f.strip() for f in fields.split(",") if f.strip()]

    if not field_list:
        return None

    return field_list


class SparseFieldsetMixin(BaseModel):
    """
    Pydantic modelleri icin sparse fieldset destegi ekleyen mixin.

    Bu mixin, API response'larinda sadece belirli alanlarin
    donmesini saglar. JSON:API sparse fieldsets standardina uygundur.

    Attributes:
        _allowed_sparse_fields: Filtrelenebilir alan isimleri seti.
            None ise tum alanlar filtrelenebilir.

    Example:
        >>> class QuestionResponse(SparseFieldsetMixin):
        >>>     id: UUID
        >>>     text: str
        >>>     difficulty: float
        >>>     subject: str
        >>>     options: list[str]
        >>>     answer: str
        >>>     explanation: str | None = None
        >>>
        >>>     # Sadece belirli alanlari filtrelemeye izin ver
        >>>     _allowed_sparse_fields: ClassVar[set[str] | None] = {
        >>>         "id", "text", "difficulty", "subject", "options"
        >>>     }
        >>>
        >>> question = QuestionResponse(...)
        >>> # Sadece id, text ve difficulty alanlarini don
        >>> filtered = question.filter_fields(["id", "text", "difficulty"])
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    # Alt siniflar tarafindan override edilebilir
    _allowed_sparse_fields: ClassVar[set[str] | None] = None

    def filter_fields(self, fields: list[str] | None) -> dict[str, Any]:
        """
        Modelden sadece belirtilen alanlari icerir.

        Args:
            fields: Dahil edilecek alan isimleri listesi.
                None ise tum alanlar dahil edilir.

        Returns:
            Filtrelenmis alanlar sozlugu.

        Raises:
            ValueError: Gecersiz alan ismi belirtilirse.

        Example:
            >>> user = UserResponse(id=1, name="Ali", email="ali@test.com")
            >>> user.filter_fields(["id", "name"])
            {'id': 1, 'name': 'Ali'}
        """
        if fields is None:
            return self.model_dump(exclude_none=True, by_alias=True)

        # Alan validasyonu
        valid_fields = self._get_valid_fields()
        invalid_fields = set(fields) - valid_fields

        if invalid_fields:
            logger.warning(
                "Gecersiz alan isimleri: %s. Izin verilen: %s",
                invalid_fields,
                valid_fields,
            )
            # Gecersiz alanlari atla (hata vermek yerine)
            fields = [f for f in fields if f in valid_fields]

        if not fields:
            # Hic gecerli alan yoksa tum alanlari don
            return self.model_dump(exclude_none=True, by_alias=True)

        # Include seti olustur
        include_set = set(fields)

        return self.model_dump(
            include=include_set,
            exclude_none=True,
            by_alias=True,
        )

    def _get_valid_fields(self) -> set[str]:
        """
        Filtreleme icin gecerli alan isimlerini doner.

        Returns:
            Gecerli alan isimleri seti.
        """
        # Model field isimlerini al
        model_fields = set(self.model_fields.keys())

        # Alias isimlerini de ekle
        for field_name, field_info in self.model_fields.items():
            if field_info.alias:
                model_fields.add(field_info.alias)

        # _allowed_sparse_fields ayarliysa onunla kesisim al
        if self._allowed_sparse_fields is not None:
            return model_fields & self._allowed_sparse_fields

        return model_fields

    @classmethod
    def get_filterable_fields(cls) -> set[str]:
        """
        Filtrelenebilir alan isimlerini doner.

        Returns:
            Filtrelenebilir alan isimleri seti.

        Example:
            >>> UserResponse.get_filterable_fields()
            {'id', 'name', 'email', 'created_at'}
        """
        model_fields = set(cls.model_fields.keys())

        if cls._allowed_sparse_fields is not None:
            return model_fields & cls._allowed_sparse_fields

        return model_fields

    def to_sparse_response(
        self,
        fields: list[str] | None = None,
        exclude_none: bool = True,
    ) -> dict[str, Any]:
        """
        Sparse fieldset filtrelemesi ile response sozlugu doner.

        Args:
            fields: Dahil edilecek alanlar. None ise tum alanlar.
            exclude_none: True ise None degerleri cikarilir.

        Returns:
            Filtrelenmis response sozlugu.

        Example:
            >>> user.to_sparse_response(fields=["id", "name"], exclude_none=True)
            {'id': 1, 'name': 'Ali'}
        """
        if fields is None:
            return self.model_dump(exclude_none=exclude_none, by_alias=True)

        return self.filter_fields(fields)


class SparseFieldsetResponse(SparseFieldsetMixin):
    """
    Standart sparse fieldset response modeli.

    Bu sinif, tum response modellerinin temel sinifi olarak kullanilabilir.
    Otomatik olarak exclude_none=True davranisi icerir.

    Example:
        >>> class ItemResponse(SparseFieldsetResponse):
        >>>     id: int
        >>>     name: str
        >>>     description: str | None = None
        >>>     price: Decimal
        >>>
        >>> item = ItemResponse(id=1, name="Kalem", price=Decimal("5.99"))
        >>> item.model_dump()  # description dahil edilmez
        {'id': 1, 'name': 'Kalem', 'price': '5.99'}
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        # Response modeli icin varsayilan davranislar
        validate_default=True,
        from_attributes=True,
    )


def create_sparse_response(
    model: SparseFieldsetMixin,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """
    Model'den sparse fieldset response olusturur.

    Args:
        model: SparseFieldsetMixin'i implement eden model.
        fields: Dahil edilecek alan listesi.

    Returns:
        Filtrelenmis response sozlugu.

    Example:
        >>> from fastapi import Depends
        >>>
        >>> @app.get("/users/{user_id}")
        >>> async def get_user(
        >>>     user_id: int,
        >>>     fields: list[str] | None = Depends(parse_fields_param)
        >>> ):
        >>>     user = await get_user_by_id(user_id)
        >>>     return create_sparse_response(user, fields)
    """
    return model.filter_fields(fields)


# Ust duzey export'lar
__all__ = [
    "SparseFieldsetMixin",
    "SparseFieldsetResponse",
    "create_sparse_response",
    "parse_fields_param",
]
