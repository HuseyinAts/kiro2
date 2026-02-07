"""
Cursor-Based Pagination - API Response Time Optimization

Bu modül, offset pagination yerine cursor-based pagination sağlar.
Büyük veri setlerinde performans için optimize edilmiştir.

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-5.2
"""

import base64
import json
import logging
from datetime import datetime
from typing import TypeVar, Generic, Optional, Any
from dataclasses import dataclass

from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=DeclarativeBase)


@dataclass
class CursorPage(Generic[T]):
    """
    Cursor-based pagination sonucu.

    Attributes:
        items: Sayfa içeriği
        next_cursor: Sonraki sayfa cursor'ı
        prev_cursor: Önceki sayfa cursor'ı
        has_next: Sonraki sayfa var mı
        has_prev: Önceki sayfa var mı
        total_count: Toplam item sayısı (opsiyonel)
    """
    items: list[T]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_next: bool = False
    has_prev: bool = False
    total_count: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Dictionary'e dönüştürür."""
        return {
            "items": self.items,
            "pagination": {
                "next_cursor": self.next_cursor,
                "prev_cursor": self.prev_cursor,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
                "total_count": self.total_count
            }
        }


class CursorPaginator(Generic[T]):
    """
    Cursor-based pagination helper class.

    created_at + id kullanarak keyset pagination sağlar.
    Offset pagination'a göre çok daha performanslıdır.

    Attributes:
        model: SQLAlchemy model class
        cursor_field: Cursor için kullanılacak field (default: created_at)
        id_field: Unique ID field (default: id)

    Example:
        paginator = CursorPaginator(Question)
        page = await paginator.paginate(
            session=db,
            limit=10,
            cursor=request.query_params.get("cursor")
        )
    """

    def __init__(
        self,
        model: type[T],
        cursor_field: str = "created_at",
        id_field: str = "id"
    ):
        """
        CursorPaginator başlatır.

        Args:
            model: SQLAlchemy model class
            cursor_field: Cursor field adı (default: created_at)
            id_field: ID field adı (default: id)
        """
        self.model = model
        self.cursor_field = cursor_field
        self.id_field = id_field

        logger.info(
            f"CursorPaginator initialized for {model.__name__}: "
            f"cursor_field={cursor_field}, id_field={id_field}"
        )

    def _encode_cursor(self, cursor_value: Any, id_value: Any) -> str:
        """
        Cursor değerini encode eder.

        Args:
            cursor_value: Cursor field değeri
            id_value: ID değeri

        Returns:
            Base64 encoded cursor string
        """
        # Handle datetime
        if isinstance(cursor_value, datetime):
            cursor_value = cursor_value.isoformat()

        data = {
            "v": cursor_value,
            "id": str(id_value)
        }

        json_str = json.dumps(data, separators=(',', ':'))
        return base64.urlsafe_b64encode(json_str.encode()).decode()

    def _decode_cursor(self, cursor: str) -> tuple[Any, Any]:
        """
        Cursor string'i decode eder.

        Args:
            cursor: Base64 encoded cursor

        Returns:
            (cursor_value, id_value) tuple

        Raises:
            ValueError: Invalid cursor format
        """
        try:
            json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
            data = json.loads(json_str)

            cursor_value = data["v"]
            id_value = data["id"]

            # Try to parse as datetime
            try:
                cursor_value = datetime.fromisoformat(cursor_value)
            except (ValueError, TypeError):
                pass

            return cursor_value, id_value

        except Exception as e:
            logger.error(f"Failed to decode cursor: {e}")
            raise ValueError(f"Invalid cursor format: {cursor}")

    async def paginate(
        self,
        session: AsyncSession,
        limit: int = 10,
        cursor: Optional[str] = None,
        direction: str = "forward",
        filters: Optional[list] = None,
        order_desc: bool = True,
        include_total: bool = False
    ) -> CursorPage[T]:
        """
        Cursor-based pagination uygular.

        Args:
            session: AsyncSession instance
            limit: Sayfa başına item sayısı (max: 100)
            cursor: Cursor string (None = first page)
            direction: Pagination yönü (forward/backward)
            filters: Ek SQLAlchemy filter'ları
            order_desc: Azalan sıralama (True) veya artan (False)
            include_total: Toplam sayıyı dahil et (performans etkisi var)

        Returns:
            CursorPage with items and pagination info
        """
        # Validate limit
        limit = min(max(1, limit), 100)

        # Get model attributes
        cursor_col = getattr(self.model, self.cursor_field)
        id_col = getattr(self.model, self.id_field)

        # Build base query
        query = select(self.model)

        # Apply filters
        if filters:
            for filter_condition in filters:
                query = query.where(filter_condition)

        # Apply cursor condition
        if cursor:
            try:
                cursor_value, cursor_id = self._decode_cursor(cursor)

                if direction == "forward":
                    if order_desc:
                        # Forward + DESC: cursor_value < x OR (cursor_value == x AND id < cursor_id)
                        query = query.where(
                            (cursor_col < cursor_value) |
                            ((cursor_col == cursor_value) & (id_col < cursor_id))
                        )
                    else:
                        # Forward + ASC: cursor_value > x OR (cursor_value == x AND id > cursor_id)
                        query = query.where(
                            (cursor_col > cursor_value) |
                            ((cursor_col == cursor_value) & (id_col > cursor_id))
                        )
                else:  # backward
                    if order_desc:
                        # Backward + DESC: cursor_value > x OR (cursor_value == x AND id > cursor_id)
                        query = query.where(
                            (cursor_col > cursor_value) |
                            ((cursor_col == cursor_value) & (id_col > cursor_id))
                        )
                    else:
                        # Backward + ASC: cursor_value < x OR (cursor_value == x AND id < cursor_id)
                        query = query.where(
                            (cursor_col < cursor_value) |
                            ((cursor_col == cursor_value) & (id_col < cursor_id))
                        )

            except ValueError:
                logger.warning("Invalid cursor, starting from beginning")

        # Apply ordering
        if direction == "forward":
            if order_desc:
                query = query.order_by(desc(cursor_col), desc(id_col))
            else:
                query = query.order_by(asc(cursor_col), asc(id_col))
        else:  # backward - reverse order
            if order_desc:
                query = query.order_by(asc(cursor_col), asc(id_col))
            else:
                query = query.order_by(desc(cursor_col), desc(id_col))

        # Fetch limit + 1 to check if there are more items
        query = query.limit(limit + 1)

        # Execute query
        result = await session.execute(query)
        items = list(result.scalars().all())

        # Check if there are more items
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]

        # Reverse items if backward pagination
        if direction == "backward":
            items = list(reversed(items))

        # Generate cursors
        next_cursor = None
        prev_cursor = None

        if items:
            # Get cursor values from first and last items
            first_item = items[0]
            last_item = items[-1]

            first_cursor_val = getattr(first_item, self.cursor_field)
            first_id = getattr(first_item, self.id_field)

            last_cursor_val = getattr(last_item, self.cursor_field)
            last_id = getattr(last_item, self.id_field)

            if direction == "forward":
                if has_more:
                    next_cursor = self._encode_cursor(last_cursor_val, last_id)
                if cursor:  # Only set prev_cursor if we had a cursor
                    prev_cursor = self._encode_cursor(first_cursor_val, first_id)
            else:  # backward
                next_cursor = self._encode_cursor(last_cursor_val, last_id)
                if has_more:
                    prev_cursor = self._encode_cursor(first_cursor_val, first_id)

        # Get total count if requested (expensive!)
        total_count = None
        if include_total:
            from sqlalchemy import func
            count_query = select(func.count()).select_from(self.model)
            if filters:
                for filter_condition in filters:
                    count_query = count_query.where(filter_condition)
            count_result = await session.execute(count_query)
            total_count = count_result.scalar()

        return CursorPage(
            items=items,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_more if direction == "forward" else bool(next_cursor),
            has_prev=bool(cursor) if direction == "forward" else has_more,
            total_count=total_count
        )


def create_cursor_paginator(model: type[T]) -> CursorPaginator[T]:
    """
    Model için CursorPaginator oluşturur.

    Args:
        model: SQLAlchemy model class

    Returns:
        CursorPaginator instance
    """
    return CursorPaginator(model)
