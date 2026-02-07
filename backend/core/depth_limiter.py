"""
Nested Object Depth Limiter - Payload Optimization

JSON serilestirmede nested object derinligini sinirlar.
Circular reference'lari onler ve buyuk payload'lari optimize eder.

Requirements:
    - REQ-7.4: Implement nested object depth limiting
    - REQ-7.5: Prevent circular references

Author: KIRO2 Team
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Varsayilan maksimum derinlik
DEFAULT_MAX_DEPTH: int = 5


@dataclass
class DepthLimitConfig:
    """
    Depth limiting konfigurasyonu.

    Attributes:
        max_depth: Maksimum nesne derinligi
        truncate_lists_at: Liste truncation limiti (None=sinir yok)
        placeholder: Derinlik asildiginda kullanilacak placeholder
        track_circular: Circular reference kontrolu
    """

    max_depth: int = DEFAULT_MAX_DEPTH
    truncate_lists_at: int | None = 100
    placeholder: str = "..."
    track_circular: bool = True


def limit_depth(
    obj: Any,
    max_depth: int = DEFAULT_MAX_DEPTH,
    current_depth: int = 0,
    seen: set[int] | None = None,
    config: DepthLimitConfig | None = None,
) -> Any:
    """
    Nesne derinligini sinirlar.

    Recursive olarak nesneyi traverse eder ve max_depth'e ulasinca
    placeholder ile degistirir. Circular reference'lari da tespit eder.

    Args:
        obj: Islenecek nesne
        max_depth: Maksimum derinlik
        current_depth: Mevcut derinlik (internal)
        seen: Gorulmus nesneler (circular detection icin)
        config: Depth limiting konfigurasyonu

    Returns:
        Derinlik sinirlandi nesne

    Example:
        >>> data = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        >>> limited = limit_depth(data, max_depth=3)
        >>> print(limited)  # {"a": {"b": {"c": "..."}}}
    """
    if config is None:
        config = DepthLimitConfig(max_depth=max_depth)

    if seen is None:
        seen = set()

    # None ve primitive tipler
    if obj is None:
        return None

    if isinstance(obj, (bool, int, float, str)):
        return obj

    # Derinlik kontrolu
    if current_depth >= config.max_depth:
        logger.debug(f"Depth limit reached at level {current_depth}")
        return config.placeholder

    # Circular reference kontrolu
    obj_id = id(obj)
    if config.track_circular and obj_id in seen:
        logger.warning(f"Circular reference detected at depth {current_depth}")
        return "[circular]"

    seen.add(obj_id)

    try:
        # Pydantic model
        if isinstance(obj, BaseModel):
            return limit_depth(
                obj.model_dump(),
                current_depth=current_depth,
                seen=seen,
                config=config,
            )

        # Dictionary / Mapping
        if isinstance(obj, Mapping):
            result = {}
            for key, value in obj.items():
                result[key] = limit_depth(
                    value,
                    current_depth=current_depth + 1,
                    seen=seen,
                    config=config,
                )
            return result

        # List / Sequence (string haric)
        if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
            items = list(obj)

            # Liste truncation
            if config.truncate_lists_at and len(items) > config.truncate_lists_at:
                logger.debug(f"List truncated from {len(items)} to {config.truncate_lists_at}")
                items = items[: config.truncate_lists_at]
                truncated = True
            else:
                truncated = False

            result = [
                limit_depth(
                    item,
                    current_depth=current_depth + 1,
                    seen=seen,
                    config=config,
                )
                for item in items
            ]

            if truncated:
                result.append(f"... ({len(obj) - config.truncate_lists_at} more items)")

            return result

        # Set / frozenset
        if isinstance(obj, (set, frozenset)):
            return limit_depth(
                list(obj),
                current_depth=current_depth,
                seen=seen,
                config=config,
            )

        # __dict__ olan nesneler
        if hasattr(obj, "__dict__"):
            return limit_depth(
                obj.__dict__,
                current_depth=current_depth,
                seen=seen,
                config=config,
            )

        # Diger tipler icin string conversion
        try:
            return str(obj)
        except Exception:
            return config.placeholder

    finally:
        # Circular reference tracking icin seen'den cikar
        seen.discard(obj_id)


def depth_limited_response(
    data: Any,
    max_depth: int = DEFAULT_MAX_DEPTH,
    truncate_lists: int | None = 100,
) -> Any:
    """
    API response icin depth limiting uygular.

    Convenience function - limit_depth'i kullanarak
    API response'larini optimize eder.

    Args:
        data: Response data
        max_depth: Maksimum derinlik
        truncate_lists: Liste truncation limiti

    Returns:
        Derinlik sinirlandi data

    Example:
        >>> @app.get("/users/{user_id}")
        >>> async def get_user(user_id: int):
        ...     user = await fetch_user(user_id)
        ...     return depth_limited_response(user, max_depth=4)
    """
    config = DepthLimitConfig(
        max_depth=max_depth,
        truncate_lists_at=truncate_lists,
        track_circular=True,
    )
    return limit_depth(data, config=config)


class DepthLimitedSerializer:
    """
    Depth-limited JSON serializer.

    Pydantic model'lar ve dict'ler icin derinlik sinirlama
    ile serilestirme saglar.

    Attributes:
        config: Depth limiting konfigurasyonu

    Example:
        >>> serializer = DepthLimitedSerializer(max_depth=4)
        >>> json_data = serializer.serialize(user_data)
    """

    def __init__(
        self,
        max_depth: int = DEFAULT_MAX_DEPTH,
        truncate_lists_at: int | None = 100,
    ):
        """
        DepthLimitedSerializer baslatici.

        Args:
            max_depth: Maksimum derinlik
            truncate_lists_at: Liste truncation limiti
        """
        self.config = DepthLimitConfig(
            max_depth=max_depth,
            truncate_lists_at=truncate_lists_at,
            track_circular=True,
        )

    def serialize(self, obj: Any) -> Any:
        """
        Nesneyi derinlik sinirli olarak serilestirir.

        Args:
            obj: Serilestirilecek nesne

        Returns:
            Derinlik sinirlandi nesne
        """
        return limit_depth(obj, config=self.config)

    def to_json_safe(self, obj: Any) -> dict | list | str | int | float | bool | None:
        """
        JSON-safe formata cevir.

        Args:
            obj: Cevrilecek nesne

        Returns:
            JSON-safe deger
        """
        limited = self.serialize(obj)

        # Ek JSON-safe donusumler
        return self._ensure_json_safe(limited)

    def _ensure_json_safe(self, obj: Any) -> Any:
        """JSON-safe oldugunu garantile."""
        if obj is None:
            return None

        if isinstance(obj, (bool, int, float, str)):
            return obj

        if isinstance(obj, dict):
            return {str(k): self._ensure_json_safe(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple)):
            return [self._ensure_json_safe(item) for item in obj]

        # Son care - string conversion
        return str(obj)


def get_object_depth(obj: Any, current_depth: int = 0, seen: set[int] | None = None) -> int:
    """
    Nesnenin maksimum derinligini hesaplar.

    Args:
        obj: Kontrol edilecek nesne
        current_depth: Mevcut derinlik
        seen: Gorulmus nesneler

    Returns:
        Maksimum derinlik

    Example:
        >>> data = {"a": {"b": {"c": 1}}}
        >>> depth = get_object_depth(data)
        >>> print(depth)  # 3
    """
    if seen is None:
        seen = set()

    # Primitive tipler
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return current_depth

    # Circular reference
    obj_id = id(obj)
    if obj_id in seen:
        return current_depth

    seen.add(obj_id)

    max_depth = current_depth

    try:
        # Pydantic model
        if isinstance(obj, BaseModel):
            return get_object_depth(obj.model_dump(), current_depth, seen)

        # Dictionary
        if isinstance(obj, Mapping):
            for value in obj.values():
                child_depth = get_object_depth(value, current_depth + 1, seen)
                max_depth = max(max_depth, child_depth)
            return max_depth

        # Sequence
        if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
            for item in obj:
                child_depth = get_object_depth(item, current_depth + 1, seen)
                max_depth = max(max_depth, child_depth)
            return max_depth

        # __dict__ olan nesneler
        if hasattr(obj, "__dict__"):
            return get_object_depth(obj.__dict__, current_depth, seen)

        return current_depth

    finally:
        seen.discard(obj_id)


__all__ = [
    "DEFAULT_MAX_DEPTH",
    "DepthLimitConfig",
    "DepthLimitedSerializer",
    "depth_limited_response",
    "get_object_depth",
    "limit_depth",
]
