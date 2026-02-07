"""
JSON Serileştirme Yardimcilari - orjson Tabanli Yuksek Performansli JSON Isleme.

Bu modul, FastAPI uygulamalari icin yuksek performansli JSON serilestirme
saglar. orjson kutuphanesi kullanilarak standart json modulune gore
3-10x daha hizli serilestirme gerceklestirilir.

Ozellikler:
    - orjson ile hizli JSON serilestirme/deserilestirme
    - datetime, UUID, Decimal icin ozel encoder destegi
    - FastAPI icin ORJSONResponse sinifi
    - exclude_none konfigurasyonu destegi
    - ISO 8601 datetime formati

Requirements: REQ-7.1, REQ-7.2, REQ-7.3, REQ-7.4

Example:
    >>> from backend.core.json_utils import ORJSONResponse, orjson_dumps
    >>>
    >>> # FastAPI endpoint'te kullanim
    >>> @app.get("/items", response_class=ORJSONResponse)
    >>> async def get_items():
    >>>     return {"items": [...]}
    >>>
    >>> # Manuel serilestirme
    >>> data = {"name": "test", "created_at": datetime.now()}
    >>> json_bytes = orjson_dumps(data)
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Callable, TypeVar
from uuid import UUID

import orjson
from fastapi import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


# orjson serilestirme secenekleri
ORJSON_OPTIONS: int = (
    orjson.OPT_SERIALIZE_NUMPY  # numpy array destegi
    | orjson.OPT_SERIALIZE_UUID  # UUID serilestirme
    | orjson.OPT_UTC_Z  # UTC timezone icin 'Z' suffix
    | orjson.OPT_NAIVE_UTC  # naive datetime'lari UTC olarak kabul et
)


def _default_serializer(obj: Any) -> Any:
    """
    orjson icin ozel tur serilestirici.

    orjson'un desteklemedigi Python turlerini JSON uyumlu turlere
    donusturur.

    Args:
        obj: Serilestirilecek nesne.

    Returns:
        JSON uyumlu deger.

    Raises:
        TypeError: Desteklenmeyen tur icin.

    Example:
        >>> _default_serializer(Decimal("123.45"))
        '123.45'
        >>> _default_serializer(UUID("550e8400-e29b-41d4-a716-446655440000"))
        '550e8400-e29b-41d4-a716-446655440000'
    """
    # Decimal destegi - string olarak serilestir (hassasiyet kaybi yok)
    if isinstance(obj, Decimal):
        return str(obj)

    # UUID destegi
    if isinstance(obj, UUID):
        return str(obj)

    # datetime destegi - ISO 8601 formati
    if isinstance(obj, datetime):
        return obj.isoformat()

    # date destegi - ISO 8601 formati
    if isinstance(obj, date):
        return obj.isoformat()

    # time destegi - ISO 8601 formati
    if isinstance(obj, time):
        return obj.isoformat()

    # timedelta destegi - toplam saniye olarak
    if isinstance(obj, timedelta):
        return obj.total_seconds()

    # Enum destegi
    if isinstance(obj, Enum):
        return obj.value

    # Path destegi
    if isinstance(obj, Path):
        return str(obj)

    # Pydantic model destegi
    if isinstance(obj, BaseModel):
        return obj.model_dump()

    # set ve frozenset destegi
    if isinstance(obj, (set, frozenset)):
        return list(obj)

    # bytes destegi - base64 encoding
    if isinstance(obj, bytes):
        import base64
        return base64.b64encode(obj).decode("utf-8")

    # __dict__ olan nesneler
    if hasattr(obj, "__dict__"):
        return obj.__dict__

    # Desteklenmeyen tur
    raise TypeError(
        f"Nesne JSON olarak serilestirilemedi: {type(obj).__name__}"
    )


def orjson_dumps(
    data: Any,
    *,
    default: Callable[[Any], Any] | None = None,
    exclude_none: bool = True,
    pretty: bool = False,
) -> bytes:
    """
    Veriyi orjson ile JSON byte dizisine serilestirir.

    Args:
        data: Serilestirilecek veri.
        default: Ozel turler icin fallback serilestirici.
            None ise varsayilan _default_serializer kullanilir.
        exclude_none: True ise None degerli alanlar cikarilir.
        pretty: True ise okunabilir formatta cikti uretir.

    Returns:
        UTF-8 kodlu JSON byte dizisi.

    Raises:
        orjson.JSONEncodeError: Serilestirme hatasi icin.

    Example:
        >>> data = {"name": "Ali", "age": None, "city": "Istanbul"}
        >>> orjson_dumps(data, exclude_none=True)
        b'{"name":"Ali","city":"Istanbul"}'
    """
    # None degerleri filtrele
    if exclude_none and isinstance(data, dict):
        data = _exclude_none_values(data)

    # Serilestirme secenekleri
    options = ORJSON_OPTIONS
    if pretty:
        options |= orjson.OPT_INDENT_2

    # Serilestir
    return orjson.dumps(
        data,
        default=default or _default_serializer,
        option=options,
    )


def orjson_loads(data: bytes | str) -> Any:
    """
    JSON verisini Python nesnesine deserilestrir.

    Args:
        data: JSON verisi (bytes veya string).

    Returns:
        Deserilestirilmis Python nesnesi.

    Raises:
        orjson.JSONDecodeError: Gecersiz JSON icin.

    Example:
        >>> orjson_loads(b'{"name":"Ali","age":25}')
        {'name': 'Ali', 'age': 25}
    """
    return orjson.loads(data)


def _exclude_none_values(data: dict[str, Any]) -> dict[str, Any]:
    """
    Sozlukten None degerli anahtarlari recursive olarak cikarir.

    Args:
        data: Islenecek sozluk.

    Returns:
        None degerleri cikarilmis sozluk.

    Example:
        >>> _exclude_none_values({"a": 1, "b": None, "c": {"d": None, "e": 2}})
        {'a': 1, 'c': {'e': 2}}
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, dict):
            filtered = _exclude_none_values(value)
            if filtered:  # Bos dict ekleme
                result[key] = filtered
        elif isinstance(value, list):
            result[key] = [
                _exclude_none_values(item) if isinstance(item, dict) else item
                for item in value
                if item is not None
            ]
        else:
            result[key] = value
    return result


class ORJSONResponse(Response):
    """
    FastAPI icin orjson tabanli JSON response sinifi.

    Standart JSONResponse'a gore 3-10x daha hizli serilestirme saglar.
    datetime, UUID, Decimal gibi turleri otomatik olarak serilestirir.

    Attributes:
        media_type: Response content type (application/json).
        exclude_none: True ise None degerler cikarilir. Varsayilan: True.

    Example:
        >>> from fastapi import FastAPI
        >>> from backend.core.json_utils import ORJSONResponse
        >>>
        >>> app = FastAPI(default_response_class=ORJSONResponse)
        >>>
        >>> @app.get("/items")
        >>> async def get_items():
        >>>     return {
        >>>         "id": UUID("550e8400-e29b-41d4-a716-446655440000"),
        >>>         "created_at": datetime.now(),
        >>>         "price": Decimal("99.99"),
        >>>         "description": None,  # Bu alan exclude edilir
        >>>     }
    """

    media_type: str = "application/json"
    charset: str = "utf-8"

    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        background: Any = None,
        exclude_none: bool = True,
    ) -> None:
        """
        ORJSONResponse baslatici.

        Args:
            content: Response body icerigi.
            status_code: HTTP durum kodu. Varsayilan: 200.
            headers: Ek HTTP header'lari.
            media_type: Content-Type. Varsayilan: application/json.
            background: Background task.
            exclude_none: True ise None degerler cikarilir.
        """
        self.exclude_none = exclude_none
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type or self.media_type,
            background=background,
        )

    def render(self, content: Any) -> bytes:
        """
        Icerigi JSON byte dizisine serilestirir.

        Args:
            content: Serilestirilecek icerik.

        Returns:
            UTF-8 kodlu JSON byte dizisi.
        """
        if content is None:
            return b""

        # Pydantic model ise dict'e cevir
        if isinstance(content, BaseModel):
            content = content.model_dump(
                exclude_none=self.exclude_none,
                by_alias=True,
            )

        return orjson_dumps(
            content,
            exclude_none=self.exclude_none,
        )


class PrettyORJSONResponse(ORJSONResponse):
    """
    Okunabilir formatli JSON response sinifi.

    Debug ve gelistirme ortamlari icin girintili JSON ciktisi uretir.
    Production'da ORJSONResponse kullanilmasi onerilir.

    Example:
        >>> @app.get("/debug/items", response_class=PrettyORJSONResponse)
        >>> async def debug_items():
        >>>     return {"items": [1, 2, 3]}
    """

    def render(self, content: Any) -> bytes:
        """
        Icerigi okunabilir formatta JSON byte dizisine serilestirir.

        Args:
            content: Serilestirilecek icerik.

        Returns:
            Girintili UTF-8 kodlu JSON byte dizisi.
        """
        if content is None:
            return b""

        if isinstance(content, BaseModel):
            content = content.model_dump(
                exclude_none=self.exclude_none,
                by_alias=True,
            )

        return orjson_dumps(
            content,
            exclude_none=self.exclude_none,
            pretty=True,
        )


def configure_fastapi_json(app: Any) -> None:
    """
    FastAPI uygulamasini orjson kullanacak sekilde yapilandirir.

    Bu fonksiyon, FastAPI'nin varsayilan JSON encoder'ini orjson
    ile degistirir ve tum JSON response'lari hizlandirir.

    Args:
        app: FastAPI uygulama instance'i.

    Example:
        >>> from fastapi import FastAPI
        >>> from backend.core.json_utils import configure_fastapi_json
        >>>
        >>> app = FastAPI()
        >>> configure_fastapi_json(app)
    """
    # Default response class'i degistir
    app.default_response_class = ORJSONResponse

    logger.info(
        "FastAPI orjson konfigurasyonu tamamlandi",
        extra={"response_class": "ORJSONResponse"},
    )


# Module-level exports
__all__ = [
    "ORJSON_OPTIONS",
    "ORJSONResponse",
    "PrettyORJSONResponse",
    "configure_fastapi_json",
    "orjson_dumps",
    "orjson_loads",
]
