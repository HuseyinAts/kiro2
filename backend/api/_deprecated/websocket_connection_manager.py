"""
WebSocket Connection Manager - Connection Limiting (REQ-2.6)
Teknofest 2025 - KIRO2 YKS Platformu

WebSocket baglanti yonetimi:
- Kullanici basina max 3 baglanti (REQ-2.6)
- Redis Set ile baglanti takibi
- FIFO: Limit asilinca en eski baglanti kapatilir
- Real-time connection metrics

Boris Cherny Standards: Verification feedback loops
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Configuration from spec REQ-2.6
MAX_CONNECTIONS_PER_USER = 3


@dataclass
class ConnectionInfo:
    """WebSocket baglanti bilgisi."""

    connection_id: str
    user_id: str
    websocket: WebSocket
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_open: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionResult:
    """Baglanti sonucu."""

    connected: bool
    connection_id: Optional[str] = None
    closed_connection: Optional[str] = None
    reason: Optional[str] = None
    current_count: int = 0


@dataclass
class ConnectionMetrics:
    """Baglanti metrikleri."""

    total_connections: int = 0
    active_connections: int = 0
    connections_closed_by_limit: int = 0
    peak_connections: int = 0
    total_users: int = 0


class WebSocketConnectionManager:
    """
    WebSocket Connection Manager (REQ-2.6)

    Kullanici basina baglanti limiti uygular.

    Attributes:
        max_connections_per_user: Kullanici basina max baglanti sayisi
    """

    def __init__(
        self,
        max_connections_per_user: int = MAX_CONNECTIONS_PER_USER,
        redis_client: Optional[Any] = None,
    ):
        """
        WebSocketConnectionManager olustur.

        Args:
            max_connections_per_user: Max baglanti/kullanici (REQ-2.6)
            redis_client: Redis client (opsiyonel, in-memory fallback)
        """
        self.max_connections_per_user = max_connections_per_user
        self.redis_client = redis_client

        # In-memory storage (used when Redis unavailable)
        self._connections: Dict[str, Dict[str, ConnectionInfo]] = defaultdict(dict)
        self._connection_order: Dict[str, List[str]] = defaultdict(list)

        # Metrics
        self.metrics = ConnectionMetrics()

        # Callbacks
        self._on_connect_callbacks: List[Callable] = []
        self._on_disconnect_callbacks: List[Callable] = []

        logger.info(
            f"WebSocketConnectionManager initialized: "
            f"max_per_user={max_connections_per_user}"
        )

    async def connect(
        self,
        user_id: str,
        websocket: WebSocket,
        connection_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConnectionResult:
        """
        Yeni WebSocket baglantisi kaydet (REQ-2.6).

        Args:
            user_id: Kullanici ID
            websocket: WebSocket instance
            connection_id: Baglanti ID (otomatik uretilir)
            metadata: Ek metadata

        Returns:
            ConnectionResult ile sonuc
        """
        connection_id = connection_id or str(uuid.uuid4())
        closed_connection = None

        # Get current connection count
        current_count = self.get_connection_count(user_id)

        # REQ-2.6: Enforce connection limit
        if current_count >= self.max_connections_per_user:
            # Close oldest connection (FIFO)
            oldest_id = await self._get_oldest_connection(user_id)
            if oldest_id:
                await self._close_connection(user_id, oldest_id, "limit_exceeded")
                closed_connection = oldest_id
                self.metrics.connections_closed_by_limit += 1
                logger.info(
                    f"Closed oldest connection {oldest_id} for user {user_id} "
                    f"(limit exceeded)"
                )

        # Create connection info
        conn_info = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            websocket=websocket,
            metadata=metadata or {},
        )

        # Store connection
        self._connections[user_id][connection_id] = conn_info
        self._connection_order[user_id].append(connection_id)

        # Update metrics
        self.metrics.total_connections += 1
        self.metrics.active_connections += 1

        if self.metrics.active_connections > self.metrics.peak_connections:
            self.metrics.peak_connections = self.metrics.active_connections

        if user_id not in self._get_all_user_ids() or current_count == 0:
            self.metrics.total_users += 1

        # Redis tracking (if available)
        if self.redis_client:
            try:
                await self._redis_track_connection(user_id, connection_id)
            except Exception as e:
                logger.warning(f"Redis tracking failed: {e}")

        # Trigger callbacks
        await self._trigger_connect_callbacks(conn_info)

        logger.debug(
            f"User {user_id} connected: {connection_id}, "
            f"total={self.get_connection_count(user_id)}"
        )

        return ConnectionResult(
            connected=True,
            connection_id=connection_id,
            closed_connection=closed_connection,
            current_count=self.get_connection_count(user_id),
        )

    async def disconnect(
        self,
        user_id: str,
        connection_id: str,
        reason: str = "client_disconnect",
    ) -> bool:
        """
        WebSocket baglantisini kaldir.

        Args:
            user_id: Kullanici ID
            connection_id: Baglanti ID
            reason: Kapatma nedeni

        Returns:
            Basarili ise True
        """
        if connection_id not in self._connections.get(user_id, {}):
            return False

        conn_info = self._connections[user_id][connection_id]

        # Close websocket if still open
        if conn_info.is_open:
            try:
                await conn_info.websocket.close()
            except Exception:
                pass  # Already closed
            conn_info.is_open = False

        # Remove from storage
        del self._connections[user_id][connection_id]
        if connection_id in self._connection_order[user_id]:
            self._connection_order[user_id].remove(connection_id)

        # Update metrics
        self.metrics.active_connections -= 1

        # Redis cleanup
        if self.redis_client:
            try:
                await self._redis_remove_connection(user_id, connection_id)
            except Exception as e:
                logger.warning(f"Redis cleanup failed: {e}")

        # Trigger callbacks
        await self._trigger_disconnect_callbacks(conn_info, reason)

        logger.debug(f"User {user_id} disconnected: {connection_id}, reason={reason}")

        return True

    async def _close_connection(
        self,
        user_id: str,
        connection_id: str,
        reason: str,
    ) -> None:
        """
        Baglantiyi kapat.

        Args:
            user_id: Kullanici ID
            connection_id: Baglanti ID
            reason: Kapatma nedeni
        """
        if connection_id in self._connections.get(user_id, {}):
            conn_info = self._connections[user_id][connection_id]
            if conn_info.is_open:
                try:
                    await conn_info.websocket.close(
                        code=1008,  # Policy Violation
                        reason=reason,
                    )
                except Exception:
                    pass
                conn_info.is_open = False

            await self.disconnect(user_id, connection_id, reason)

    async def _get_oldest_connection(self, user_id: str) -> Optional[str]:
        """
        En eski baglantiyi al (FIFO).

        Args:
            user_id: Kullanici ID

        Returns:
            Baglanti ID veya None
        """
        order = self._connection_order.get(user_id, [])
        return order[0] if order else None

    def get_connection_count(self, user_id: str) -> int:
        """
        Kullanici baglanti sayisini al.

        Args:
            user_id: Kullanici ID

        Returns:
            Baglanti sayisi
        """
        return len(self._connections.get(user_id, {}))

    def get_user_connections(self, user_id: str) -> List[str]:
        """
        Kullanici baglanti ID listesi.

        Args:
            user_id: Kullanici ID

        Returns:
            Baglanti ID listesi
        """
        return list(self._connections.get(user_id, {}).keys())

    def get_connection(
        self, user_id: str, connection_id: str
    ) -> Optional[ConnectionInfo]:
        """
        Baglanti bilgisini al.

        Args:
            user_id: Kullanici ID
            connection_id: Baglanti ID

        Returns:
            ConnectionInfo veya None
        """
        return self._connections.get(user_id, {}).get(connection_id)

    def get_total_connections(self) -> int:
        """Toplam aktif baglanti sayisi."""
        return sum(len(conns) for conns in self._connections.values())

    def _get_all_user_ids(self) -> Set[str]:
        """Tum kullanici ID'leri."""
        return set(self._connections.keys())

    async def broadcast_to_user(
        self,
        user_id: str,
        message: str,
        exclude_connection: Optional[str] = None,
    ) -> int:
        """
        Kullanicinin tum baglantilarina mesaj gonder.

        Args:
            user_id: Kullanici ID
            message: Mesaj
            exclude_connection: Haric tutulacak baglanti

        Returns:
            Gonderilen baglanti sayisi
        """
        sent_count = 0
        connections = self._connections.get(user_id, {})

        for conn_id, conn_info in connections.items():
            if conn_id == exclude_connection:
                continue
            if conn_info.is_open:
                try:
                    await conn_info.websocket.send_text(message)
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send to {conn_id}: {e}")
                    # Mark as closed if send fails
                    conn_info.is_open = False

        return sent_count

    async def broadcast_to_all(
        self,
        message: str,
        exclude_users: Optional[Set[str]] = None,
    ) -> int:
        """
        Tum baglantilara mesaj gonder.

        Args:
            message: Mesaj
            exclude_users: Haric tutulacak kullanicilar

        Returns:
            Gonderilen baglanti sayisi
        """
        exclude_users = exclude_users or set()
        sent_count = 0

        for user_id, connections in self._connections.items():
            if user_id in exclude_users:
                continue
            for conn_info in connections.values():
                if conn_info.is_open:
                    try:
                        await conn_info.websocket.send_text(message)
                        sent_count += 1
                    except Exception:
                        conn_info.is_open = False

        return sent_count

    def update_activity(self, user_id: str, connection_id: str) -> None:
        """
        Baglanti aktivitesini guncelle.

        Args:
            user_id: Kullanici ID
            connection_id: Baglanti ID
        """
        conn = self.get_connection(user_id, connection_id)
        if conn:
            conn.last_activity = datetime.now()

    # Redis integration methods
    async def _redis_track_connection(
        self, user_id: str, connection_id: str
    ) -> None:
        """Redis'te baglanti takibi."""
        if not self.redis_client:
            return

        key = f"ws:connections:{user_id}"
        time_key = f"ws:connection_times:{user_id}"

        await self.redis_client.sadd(key, connection_id)
        await self.redis_client.zadd(time_key, {connection_id: time.time()})

    async def _redis_remove_connection(
        self, user_id: str, connection_id: str
    ) -> None:
        """Redis'ten baglanti kaldir."""
        if not self.redis_client:
            return

        key = f"ws:connections:{user_id}"
        time_key = f"ws:connection_times:{user_id}"

        await self.redis_client.srem(key, connection_id)
        await self.redis_client.zrem(time_key, connection_id)

    # Callback management
    def on_connect(self, callback: Callable) -> None:
        """Connect callback kaydet."""
        self._on_connect_callbacks.append(callback)

    def on_disconnect(self, callback: Callable) -> None:
        """Disconnect callback kaydet."""
        self._on_disconnect_callbacks.append(callback)

    async def _trigger_connect_callbacks(self, conn_info: ConnectionInfo) -> None:
        """Connect callback'lerini calistir."""
        for callback in self._on_connect_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(conn_info)
                else:
                    callback(conn_info)
            except Exception as e:
                logger.error(f"Connect callback error: {e}")

    async def _trigger_disconnect_callbacks(
        self, conn_info: ConnectionInfo, reason: str
    ) -> None:
        """Disconnect callback'lerini calistir."""
        for callback in self._on_disconnect_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(conn_info, reason)
                else:
                    callback(conn_info, reason)
            except Exception as e:
                logger.error(f"Disconnect callback error: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Metrikleri al.

        Returns:
            Metrik sozlugu
        """
        return {
            "total_connections": self.metrics.total_connections,
            "active_connections": self.metrics.active_connections,
            "connections_closed_by_limit": self.metrics.connections_closed_by_limit,
            "peak_connections": self.metrics.peak_connections,
            "total_users": self.metrics.total_users,
            "max_per_user": self.max_connections_per_user,
        }


# Singleton instance
_connection_manager: Optional[WebSocketConnectionManager] = None


def get_connection_manager() -> WebSocketConnectionManager:
    """
    Singleton WebSocketConnectionManager instance al.

    Returns:
        WebSocketConnectionManager instance
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = WebSocketConnectionManager()
    return _connection_manager
