"""
Optimize edilmiş Repository Base Pattern implementasyonu.

Bu modül, veritabanı sorgularını optimize etmek için özel metodlar sağlar:
- Sadece gerekli kolonların seçilmesi (SELECT * yasak)
- load_only() ile kısmi obje yükleme
- Sorgu sonuç boyutu limitleri
- 5 saniyelik sorgu timeout

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-5.1, REQ-5.5
"""

import asyncio
import logging
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Column, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, load_only
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

# Varsayılan sorgu timeout (saniye) - REQ-5.5
DEFAULT_QUERY_TIMEOUT: float = 5.0

# Varsayılan maksimum sonuç limiti
DEFAULT_MAX_RESULTS: int = 1000

# Varsayılan minimum sonuç limiti
DEFAULT_MIN_RESULTS: int = 1


class QueryTimeoutError(Exception):
    """
    Sorgu timeout hatası.

    Sorgu belirlenen süre içinde tamamlanmadığında fırlatılır.

    Attributes:
        timeout: Timeout süresi (saniye)
        query_info: Sorgu bilgisi
    """

    def __init__(self, timeout: float, query_info: str = ""):
        self.timeout = timeout
        self.query_info = query_info
        message = f"Sorgu {timeout} saniye içinde tamamlanamadı"
        if query_info:
            message += f": {query_info}"
        super().__init__(message)


class QueryLimitExceededError(Exception):
    """
    Sorgu limit aşımı hatası.

    İstenen sonuç sayısı maksimum limiti aştığında fırlatılır.

    Attributes:
        requested: İstenen sonuç sayısı
        maximum: Maksimum izin verilen limit
    """

    def __init__(self, requested: int, maximum: int):
        self.requested = requested
        self.maximum = maximum
        super().__init__(
            f"Sorgu limiti aşıldı: {requested} istendi, maksimum {maximum}"
        )


class OptimizedBaseRepository(Generic[ModelType]):
    """
    Optimize edilmiş generic repository base class.

    Bu class, SELECT * yerine sadece gerekli kolonları seçen,
    sorgu timeout ve limit kontrolü yapan metodlar sağlar.

    Attributes:
        model: SQLAlchemy model class
        session: Async veritabanı session
        default_columns: Varsayılan olarak seçilecek kolonlar
        query_timeout: Sorgu timeout süresi (saniye)
        max_results: Maksimum izin verilen sonuç sayısı

    Example:
        class UserRepository(OptimizedBaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(
                    model=User,
                    session=session,
                    default_columns=[User.id, User.email, User.name]
                )
    """

    def __init__(
        self,
        model: type[ModelType],
        session: AsyncSession,
        default_columns: list[Column[Any]] | None = None,
        query_timeout: float = DEFAULT_QUERY_TIMEOUT,
        max_results: int = DEFAULT_MAX_RESULTS,
    ):
        """
        Repository oluştur.

        Args:
            model: SQLAlchemy model class
            session: Async veritabanı session
            default_columns: Varsayılan olarak seçilecek kolonlar
            query_timeout: Sorgu timeout süresi saniye cinsinden (varsayılan: 5.0)
            max_results: Maksimum izin verilen sonuç sayısı (varsayılan: 1000)
        """
        self.model = model
        self.session = session
        self.default_columns = default_columns
        self.query_timeout = query_timeout
        self.max_results = max_results

    def _validate_limit(self, limit: int) -> int:
        """
        Sorgu limitini doğrula ve normalleştir.

        Args:
            limit: İstenen sonuç limiti

        Returns:
            Doğrulanmış limit değeri

        Raises:
            QueryLimitExceededError: Limit maksimum değeri aşarsa
        """
        if limit < DEFAULT_MIN_RESULTS:
            logger.warning(
                f"Limit {limit} minimum {DEFAULT_MIN_RESULTS} altında, "
                f"{DEFAULT_MIN_RESULTS} kullanılıyor"
            )
            return DEFAULT_MIN_RESULTS

        if limit > self.max_results:
            raise QueryLimitExceededError(requested=limit, maximum=self.max_results)

        return limit

    async def _execute_with_timeout(
        self,
        query: Select[tuple[Any, ...]],
        timeout: float | None = None,
    ) -> Sequence[Any]:
        """
        Sorguyu timeout ile çalıştır.

        Args:
            query: SQLAlchemy Select sorgusu
            timeout: Timeout süresi (saniye). None ise varsayılan kullanılır.

        Returns:
            Sorgu sonuçları

        Raises:
            QueryTimeoutError: Sorgu timeout süresini aşarsa
        """
        effective_timeout = timeout if timeout is not None else self.query_timeout

        try:
            result = await asyncio.wait_for(
                self.session.execute(query),
                timeout=effective_timeout,
            )
            return result.scalars().all()

        except TimeoutError:
            logger.error(
                f"Sorgu timeout: {effective_timeout}s - Model: {self.model.__name__}"
            )
            raise QueryTimeoutError(
                timeout=effective_timeout,
                query_info=f"Model: {self.model.__name__}",
            )

    async def select_columns(
        self,
        columns: list[Column[Any]],
        filters: dict[str, Any] | None = None,
        order_by: Column[Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        timeout: float | None = None,
    ) -> Sequence[tuple[Any, ...]]:
        """
        Sadece belirtilen kolonları seç (SELECT * YERİNE).

        Bu metod, SELECT * yerine sadece ihtiyaç duyulan kolonları seçer
        ve veri transferini minimize eder. REQ-5.1 gereksinimini karşılar.

        Args:
            columns: Seçilecek kolon listesi
            filters: Filtre koşulları dict olarak (field_name: value)
            order_by: Sıralama kolonu
            limit: Sonuç limiti (varsayılan: 100, maksimum: max_results)
            offset: Sonuç başlangıç noktası
            timeout: Sorgu timeout süresi (saniye)

        Returns:
            Seçilen kolonların tuple listesi

        Raises:
            QueryLimitExceededError: Limit maksimum değeri aşarsa
            QueryTimeoutError: Sorgu timeout süresini aşarsa
            ValueError: Kolonlar boş listeyse
        """
        if not columns:
            raise ValueError("En az bir kolon seçilmelidir")

        validated_limit = self._validate_limit(limit)
        query = select(*columns)

        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(offset).limit(validated_limit)

        logger.debug(
            f"select_columns: {[c.name for c in columns]}, "
            f"limit={validated_limit}, offset={offset}"
        )

        try:
            effective_timeout = timeout if timeout is not None else self.query_timeout
            result = await asyncio.wait_for(
                self.session.execute(query),
                timeout=effective_timeout,
            )
            return result.all()

        except TimeoutError:
            raise QueryTimeoutError(
                timeout=self.query_timeout,
                query_info=f"select_columns - Model: {self.model.__name__}",
            )

    async def select_with_load_only(
        self,
        columns: list[Column[Any]],
        filters: dict[str, Any] | None = None,
        order_by: Column[Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        timeout: float | None = None,
    ) -> Sequence[ModelType]:
        """
        load_only() ile kısmi obje yükleme.

        Bu metod, model objelerini döndürür ancak sadece belirtilen
        kolonları yükler. Diğer kolonlar lazy load edilir.

        Args:
            columns: Yüklenecek kolon listesi
            filters: Filtre koşulları dict olarak
            order_by: Sıralama kolonu
            limit: Sonuç limiti (varsayılan: 100)
            offset: Sonuç başlangıç noktası
            timeout: Sorgu timeout süresi (saniye)

        Returns:
            Kısmi yüklenmiş model obje listesi
        """
        if not columns:
            raise ValueError("En az bir kolon seçilmelidir")

        validated_limit = self._validate_limit(limit)
        column_names = [col.name for col in columns]

        query = select(self.model).options(load_only(*column_names))

        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(offset).limit(validated_limit)

        logger.debug(
            f"select_with_load_only: {column_names}, "
            f"limit={validated_limit}, offset={offset}"
        )

        return await self._execute_with_timeout(query, timeout)

    async def get_by_id_partial(
        self,
        id_value: Any,
        columns: list[Column[Any]] | None = None,
        timeout: float | None = None,
    ) -> ModelType | None:
        """
        ID ile kısmi obje yükle.

        Args:
            id_value: Kayıt ID değeri
            columns: Yüklenecek kolonlar. None ise default_columns kullanılır.
            timeout: Sorgu timeout süresi (saniye)

        Returns:
            Kısmi yüklenmiş model objesi veya None
        """
        effective_columns = columns or self.default_columns

        if not effective_columns:
            logger.warning(
                f"get_by_id_partial: Varsayılan kolonlar yok, "
                f"tüm model yükleniyor - Model: {self.model.__name__}"
            )
            query = select(self.model).where(self.model.id == id_value)
        else:
            column_names = [col.name for col in effective_columns]
            query = (
                select(self.model)
                .options(load_only(*column_names))
                .where(self.model.id == id_value)
            )

        try:
            effective_timeout = timeout if timeout is not None else self.query_timeout
            result = await asyncio.wait_for(
                self.session.execute(query),
                timeout=effective_timeout,
            )
            return result.scalar_one_or_none()

        except TimeoutError:
            raise QueryTimeoutError(
                timeout=self.query_timeout,
                query_info=f"get_by_id_partial - Model: {self.model.__name__}",
            )

    async def count_with_timeout(
        self,
        filters: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> int:
        """
        Kayıt sayısını timeout ile say.

        Args:
            filters: Filtre koşulları
            timeout: Sorgu timeout süresi (saniye)

        Returns:
            Kayıt sayısı
        """
        query = select(func.count(self.model.id))

        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)

        try:
            effective_timeout = timeout if timeout is not None else self.query_timeout
            result = await asyncio.wait_for(
                self.session.execute(query),
                timeout=effective_timeout,
            )
            return result.scalar() or 0

        except TimeoutError:
            raise QueryTimeoutError(
                timeout=self.query_timeout,
                query_info=f"count - Model: {self.model.__name__}",
            )

    async def exists_with_timeout(
        self,
        filters: dict[str, Any],
        timeout: float | None = None,
    ) -> bool:
        """
        Kayıt varlığını timeout ile kontrol et.

        Args:
            filters: Filtre koşulları
            timeout: Sorgu timeout süresi (saniye)

        Returns:
            Kayıt varsa True, yoksa False
        """
        query = select(self.model.id)

        for field_name, value in filters.items():
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                query = query.where(field == value)

        query = query.limit(1)

        try:
            effective_timeout = timeout if timeout is not None else self.query_timeout
            result = await asyncio.wait_for(
                self.session.execute(query),
                timeout=effective_timeout,
            )
            return result.scalar() is not None

        except TimeoutError:
            raise QueryTimeoutError(
                timeout=self.query_timeout,
                query_info=f"exists - Model: {self.model.__name__}",
            )

    def create_optimized_query(
        self,
        columns: list[Column[Any]] | None = None,
    ) -> Select[tuple[Any, ...]]:
        """
        Optimize edilmiş sorgu başlat.

        Args:
            columns: Seçilecek kolonlar. None ise model seçilir.

        Returns:
            SQLAlchemy Select objesi
        """
        if columns:
            return select(*columns)
        return select(self.model)


__all__ = [
    "DEFAULT_MAX_RESULTS",
    "DEFAULT_QUERY_TIMEOUT",
    "OptimizedBaseRepository",
    "QueryLimitExceededError",
    "QueryTimeoutError",
]
