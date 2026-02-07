"""
Compression Middleware - Gzip Response Sikistirma

API yanitlarini gzip ile sikistirarak bant genisligi tasarrufu saglar.
P95 latency < 200ms hedefine katkida bulunur.

Ozellikler:
    - Minimum boyut esigi (1000 byte)
    - Accept-Encoding header kontrolu
    - Compression level 6 (hiz/boyut dengesi)
    - Otomatik Content-Encoding header ekleme
    - Zaten sikistirilmis icerik turleri haric tutma

Requirements:
    - REQ-2.1: 1KB ustu yanitlara gzip uygula
    - REQ-2.2: Compression level 6 kullan
    - REQ-2.3: Accept-Encoding header kontrolu
    - REQ-2.6: Content-Encoding: gzip header ekle
"""

from __future__ import annotations

import gzip
import io
import logging
import time
from typing import Callable, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


EXCLUDED_CONTENT_TYPES: Set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/bmp",
    "image/ico",
    "image/x-icon",
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "application/zip",
    "application/gzip",
    "application/x-gzip",
    "application/x-compressed",
    "application/x-zip-compressed",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
    "application/x-bzip",
    "application/x-bzip2",
    "application/pdf",
    "text/event-stream",
    "application/octet-stream",
}

COMPRESSIBLE_CONTENT_TYPES: Set[str] = {
    "application/json",
    "application/xml",
    "text/plain",
    "text/html",
    "text/css",
    "text/javascript",
    "application/javascript",
    "text/xml",
}


class GZipMiddleware(BaseHTTPMiddleware):
    """FastAPI icin Gzip sikistirma middleware'i."""

    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 1000,
        compression_level: int = 6,
        **kwargs
    ) -> None:
        super().__init__(app)
        if not 1 <= compression_level <= 9:
            raise ValueError(f"compression_level 1-9 arasinda olmali: {compression_level}")
        if minimum_size < 0:
            raise ValueError(f"minimum_size negatif olamaz: {minimum_size}")
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        logger.info(f"GZipMiddleware baslatildi: minimum_size={minimum_size}, compression_level={compression_level}")

    def _client_accepts_gzip(self, request: Request) -> bool:
        accept_encoding = request.headers.get("accept-encoding", "").lower()
        return "gzip" in accept_encoding

    def _should_compress(self, content_type: str | None) -> bool:
        if not content_type:
            return False
        base_content_type = content_type.split(";")[0].strip().lower()
        if base_content_type in EXCLUDED_CONTENT_TYPES:
            return False
        return base_content_type in COMPRESSIBLE_CONTENT_TYPES

    def _compress_content(self, content: bytes) -> bytes:
        buffer = io.BytesIO()
        with gzip.GzipFile(mode="wb", fileobj=buffer, compresslevel=self.compression_level) as gz_file:
            gz_file.write(content)
        return buffer.getvalue()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._client_accepts_gzip(request):
            return await call_next(request)
        response = await call_next(request)
        content_encoding = response.headers.get("content-encoding", "").lower()
        if content_encoding in ("gzip", "br", "deflate"):
            return response
        content_type = response.headers.get("content-type")
        if not self._should_compress(content_type):
            return response
        if isinstance(response, StreamingResponse):
            return response
        try:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
        except Exception as e:
            logger.warning(f"Response body okunamadi: {e}")
            return response
        original_size = len(body)
        if original_size < self.minimum_size:
            return Response(content=body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
        start_time = time.perf_counter()
        try:
            compressed_body = self._compress_content(body)
        except Exception as e:
            logger.error(f"Sikistirma hatasi: {e}")
            return Response(content=body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
        compression_time_ms = (time.perf_counter() - start_time) * 1000
        compressed_size = len(compressed_body)
        compression_ratio = 1 - (compressed_size / original_size) if original_size > 0 else 0
        if compressed_size >= original_size:
            return Response(content=body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
        new_headers = dict(response.headers)
        new_headers["content-encoding"] = "gzip"
        new_headers["content-length"] = str(compressed_size)
        new_headers["vary"] = "Accept-Encoding"
        new_headers["x-original-size"] = str(original_size)
        new_headers["x-compressed-size"] = str(compressed_size)
        new_headers["x-compression-ratio"] = f"{compression_ratio:.2%}"
        new_headers["x-compression-time-ms"] = f"{compression_time_ms:.2f}"
        return Response(content=compressed_body, status_code=response.status_code, headers=new_headers, media_type=response.media_type)


def get_gzip_middleware(minimum_size: int = 1000, compression_level: int = 6) -> type[GZipMiddleware]:
    class ConfiguredGZipMiddleware(GZipMiddleware):
        def __init__(self, app: ASGIApp) -> None:
            super().__init__(app, minimum_size=minimum_size, compression_level=compression_level)
    return ConfiguredGZipMiddleware


__all__ = ["GZipMiddleware", "get_gzip_middleware", "EXCLUDED_CONTENT_TYPES", "COMPRESSIBLE_CONTENT_TYPES"]
