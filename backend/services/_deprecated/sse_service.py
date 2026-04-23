"""
SSE (Server-Sent Events) Service — Redis pub/sub broadcast layer.

Bu servis birden fazla istemciye Redis pub/sub üzerinden gerçek zamanlı
olaylar yayınlamak için kullanılır. FastAPI endpoint'leri bu servisi
StreamingResponse üretmek için kullanır.

Desteklenen kanallar:
  duel:{session_id}       — düello olayları (F1 duel feature)
  coaching:{student_id}  — proaktif koçluk bildirimleri
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import redis.asyncio as aioredis
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)

# Heartbeat aralığı — istemci bağlantısının canlı kalmasını sağlar
_HEARTBEAT_INTERVAL: int = 30  # saniye

# Pub/sub mesaj bekleme zaman aşımı (non-blocking poll)
_PUBSUB_TIMEOUT: float = 1.0  # saniye


def _format_sse(event_type: str, data: dict[str, Any]) -> str:
    """Tek bir SSE olayını wire formatına dönüştür.

    Çıktı:
        event: {event_type}\\n
        data: {json_data}\\n
        \\n

    Args:
        event_type: SSE olay adı (ör. "answer_submitted").
        data: JSON serileştirilebilir sözlük.

    Returns:
        SSE protokolüne uygun ham string.
    """
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


def _format_heartbeat() -> str:
    """Bağlantıyı canlı tutmak için SSE yorum satırı (heartbeat)."""
    return ": heartbeat\n\n"


class SSEManager:
    """Redis pub/sub tabanlı SSE yayın yöneticisi (singleton).

    Kullanım:
        manager = SSEManager()

        # Yayıncı tarafı (ör. bir API işleyici veya arka plan görevi):
        await manager.publish("duel:abc123", "answer_submitted", {"student_id": 42})

        # Abone tarafı (ör. bir StreamingResponse generator'ı):
        async for chunk in manager.subscribe("duel:abc123"):
            yield chunk
    """

    _instance: SSEManager | None = None

    def __init__(self) -> None:
        self._redis_url: str = _resolve_redis_url()
        # Yayıncı için ayrı bir bağlantı havuzu kullan
        self._publisher: aioredis.Redis | None = None
        self._publisher_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Singleton fabrika
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> SSEManager:
        """Uygulama genelinde tek SSEManager örneğini döndür."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # İç yardımcılar
    # ------------------------------------------------------------------

    async def _get_publisher(self) -> aioredis.Redis:
        """Tembel başlatma ile paylaşılan yayıncı bağlantısını al.

        Thread-safe başlatma için asyncio.Lock kullanır.
        """
        if self._publisher is None:
            async with self._publisher_lock:
                if self._publisher is None:  # çift kontrol
                    self._publisher = aioredis.from_url(
                        self._redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                    )
                    logger.info("SSEManager: yayıncı Redis bağlantısı oluşturuldu")
        return self._publisher

    async def _create_subscriber_connection(self) -> aioredis.Redis:
        """Her abone için bağımsız bir Redis bağlantısı oluştur.

        Redis pub/sub durumlu olduğundan aboneler kendi bağlantılarına
        sahip olmalıdır.
        """
        return aioredis.from_url(
            self._redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    # ------------------------------------------------------------------
    # Genel API
    # ------------------------------------------------------------------

    def send_event(self, event_type: str, data: dict[str, Any]) -> str:
        """Tek bir SSE olay string'ini formatla (I/O yok).

        Args:
            event_type: SSE olay adı.
            data: JSON-serileştirilebilir yük.

        Returns:
            SSE wire-format string'i.
        """
        return _format_sse(event_type, data)

    async def publish(
        self,
        channel: str,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        """Olayı Redis kanalına yayınla.

        Args:
            channel: Redis kanalı (ör. "duel:abc123").
            event_type: SSE olay adı (ör. "opponent_joined").
            data: Olayla birlikte gönderilecek yük sözlüğü.

        Raises:
            Bağlantı hataları yakalanır ve loglara yazılır; istisnalar
            çağıran koda iletilmez (fire-and-forget anlambilimi).
        """
        message = json.dumps(
            {"event_type": event_type, "data": data},
            ensure_ascii=False,
        )
        try:
            pub = await self._get_publisher()
            await pub.publish(channel, message)
            logger.debug("SSEManager.publish: kanal=%s olay=%s", channel, event_type)
        except Exception:
            logger.exception(
                "SSEManager.publish başarısız: kanal=%s olay=%s", channel, event_type
            )

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        """Redis kanalına abone ol ve SSE-formatlı chunk'lar üret.

        Bağlantı koptuğunda veya generator iptal edildiğinde kaynakları
        temizler. Her 30 saniyede bir heartbeat yorum satırı gönderir;
        bu sayede nginx/proxy'ler ve istemciler bağlantıyı canlı tutar.

        Args:
            channel: Dinlenecek Redis kanalı.

        Yields:
            SSE wire-format string'leri (olaylar ve heartbeat'ler).
        """
        conn = await self._create_subscriber_connection()
        pubsub = conn.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.info("SSEManager.subscribe: kanal=%s dinleniyor", channel)

            last_heartbeat = asyncio.get_event_loop().time()

            while True:
                now = asyncio.get_event_loop().time()

                # Heartbeat — uzun sessizliklerde bağlantıyı canlı tut
                if now - last_heartbeat >= _HEARTBEAT_INTERVAL:
                    yield _format_heartbeat()
                    last_heartbeat = now

                # Redis'ten sonraki mesajı non-blocking olarak al
                try:
                    raw = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=_PUBSUB_TIMEOUT,
                    )
                except TimeoutError:
                    # Zaman asimi normaldir; donguye devam et
                    continue

                if raw is None:
                    continue

                msg_type = raw.get("type")
                if msg_type != "message":
                    continue

                raw_data = raw.get("data", "")
                if not isinstance(raw_data, str):
                    continue

                try:
                    envelope = json.loads(raw_data)
                    event_type: str = envelope.get("event_type", "message")
                    payload: dict[str, Any] = envelope.get("data", {})
                    yield _format_sse(event_type, payload)
                    last_heartbeat = now  # mesaj göndermek heartbeat sayılır
                except (json.JSONDecodeError, TypeError):
                    logger.warning(
                        "SSEManager.subscribe: geçersiz mesaj formatı, atlandı. "
                        "Kanal=%s ham=%r",
                        channel,
                        raw_data[:200],
                    )

        except asyncio.CancelledError:
            # Generator iptal edildi (istemci bağlantısını kesti)
            logger.info("SSEManager.subscribe iptal edildi: kanal=%s", channel)
            raise
        except Exception:
            logger.exception(
                "SSEManager.subscribe beklenmeyen hata: kanal=%s", channel
            )
        finally:
            # Her durumda aboneliği temizle ve bağlantıyı kapat
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception:
                pass
            try:
                await conn.aclose()
            except Exception:
                pass
            logger.info("SSEManager.subscribe temizlendi: kanal=%s", channel)

    async def close(self) -> None:
        """Yayıncı bağlantısını kapat (uygulama kapatma sırasında çağrılır)."""
        if self._publisher is not None:
            try:
                await self._publisher.aclose()
                logger.info("SSEManager: yayıncı bağlantısı kapatıldı")
            except Exception:
                logger.exception("SSEManager.close: yayıncı kapatılırken hata")
            finally:
                self._publisher = None


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar — FastAPI dependency injection
# ---------------------------------------------------------------------------


def get_sse_manager() -> SSEManager:
    """FastAPI Depends() için SSEManager singleton'ını döndür.

    Kullanım::

        @router.get("/stream/{session_id}")
        async def stream(
            session_id: str,
            manager: SSEManager = Depends(get_sse_manager),
        ) -> StreamingResponse:
            return create_sse_response(f"duel:{session_id}", manager)
    """
    return SSEManager.get_instance()


def create_sse_response(
    channel: str,
    manager: SSEManager | None = None,
) -> StreamingResponse:
    """Verilen Redis kanalı için hazır bir SSE StreamingResponse oluştur.

    Args:
        channel: Dinlenecek Redis kanalı (ör. "duel:abc123").
        manager: SSEManager örneği; None ise singleton kullanılır.

    Returns:
        Uygun SSE başlıklarıyla yapılandırılmış StreamingResponse.
    """
    if manager is None:
        manager = SSEManager.get_instance()

    return StreamingResponse(
        manager.subscribe(channel),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # nginx proxy buffering'i devre dışı bırak — gerçek zamanlı akış için kritik
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Kanal adı yardımcıları — tutarlı adlandırma için
# ---------------------------------------------------------------------------


def duel_channel(session_id: str) -> str:
    """Düello oturumu için Redis kanal adını döndür.

    Args:
        session_id: Düello oturumu UUID'si.

    Returns:
        ``"duel:{session_id}"`` biçiminde kanal adı.
    """
    return f"duel:{session_id}"


def coaching_channel(student_id: int | str) -> str:
    """Öğrenci koçluk bildirimleri için Redis kanal adını döndür.

    Args:
        student_id: Öğrenci veritabanı kimliği.

    Returns:
        ``"coaching:{student_id}"`` biçiminde kanal adı.
    """
    return f"coaching:{student_id}"


# ---------------------------------------------------------------------------
# İç yardımcılar
# ---------------------------------------------------------------------------


def _resolve_redis_url() -> str:
    """Redis URL'sini settings modülünden veya ortam değişkeninden çöz.

    config.py'yi import edemezse çevresel değişkene geri döner; bu sayede
    servis, tam uygulama yığını olmadan (ör. bağımsız testlerde) çalışır.
    """
    try:
        from core.config import settings  # type: ignore[import]

        url: str = getattr(settings, "redis_url", None) or "redis://localhost:6379/0"
        return url
    except Exception:
        import os

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        logger.debug(
            "SSEManager: core.config.settings yüklenemedi, "
            "REDIS_URL=%s kullanılıyor",
            url,
        )
        return url
