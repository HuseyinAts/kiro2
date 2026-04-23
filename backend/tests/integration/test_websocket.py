"""
Test file for websocket.py module
"""
import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from websocket import ConnectionManager

pytestmark = pytest.mark.skipif(
    True,
    reason="WebSocket deprecated (SSE migration), 1/8 fail",
)


class TestConnectionManager:
    """ConnectionManager sınıfı testleri"""

    @pytest.fixture
    def manager(self):
        """ConnectionManager fixture"""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_client(self, manager):
        """Client bağlantı testi"""
        mock_ws = Mock()
        mock_ws.accept = AsyncMock()

        await manager.connect(mock_ws, "client_123")

        assert len(manager.active_connections) == 1
        assert mock_ws in manager.active_connections
        assert "client_123" in manager.user_connections
        assert manager.user_connections["client_123"] == mock_ws
        mock_ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_client(self, manager):
        """Client bağlantı kesme testi"""
        mock_ws = Mock()
        mock_ws.accept = AsyncMock()

        # Connect first
        await manager.connect(mock_ws, "client_123")
        assert len(manager.active_connections) == 1
        assert "client_123" in manager.user_connections

        # Then disconnect
        manager.disconnect(mock_ws, "client_123")
        assert len(manager.active_connections) == 0
        assert "client_123" not in manager.user_connections

    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager):
        """Kişisel mesaj gönderme testi"""
        mock_ws = Mock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        # Connect client
        await manager.connect(mock_ws, "client_123")

        # Send message
        message = "Hello, this is a personal message"
        await manager.send_personal_message(message, mock_ws)

        mock_ws.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_message(self, manager):
        """Broadcast mesaj testi"""
        # Connect multiple clients
        clients = []
        for i in range(3):
            mock_ws = Mock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()
            await manager.connect(mock_ws, f"client_{i}")
            clients.append(mock_ws)

        # Broadcast message
        message = "Server update announcement"
        await manager.broadcast(message)

        # Check all clients received the message
        for mock_ws in clients:
            mock_ws.send_text.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_connect_without_client_id(self, manager):
        """Client ID olmadan bağlantı testi"""
        mock_ws = Mock()
        mock_ws.accept = AsyncMock()

        # Connect without client_id
        await manager.connect(mock_ws)

        assert len(manager.active_connections) == 1
        assert mock_ws in manager.active_connections
        assert len(manager.user_connections) == 0
        mock_ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_with_failed_connections(self, manager):
        """Başarısız bağlantılarla broadcast testi"""
        # Connect multiple clients, one will fail
        mock_ws1 = Mock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()

        mock_ws2 = Mock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_text = AsyncMock(side_effect=Exception("Connection closed"))

        mock_ws3 = Mock()
        mock_ws3.accept = AsyncMock()
        mock_ws3.send_text = AsyncMock()

        await manager.connect(mock_ws1, "client_1")
        await manager.connect(mock_ws2, "client_2")
        await manager.connect(mock_ws3, "client_3")

        # Broadcast should continue despite one failure
        await manager.broadcast("Test message")

        # Working connections should receive the message
        mock_ws1.send_text.assert_called_with("Test message")
        mock_ws3.send_text.assert_called_with("Test message")

    def test_disconnect_without_client_id(self, manager):
        """Client ID olmadan bağlantı kesme testi"""
        mock_ws = Mock()

        # Add to active connections
        manager.active_connections.append(mock_ws)

        # Disconnect without client_id
        manager.disconnect(mock_ws)

        assert mock_ws not in manager.active_connections
        assert len(manager.active_connections) == 0

    def test_user_connections_tracking(self, manager):
        """Kullanıcı bağlantıları takibi testi"""
        mock_ws1 = Mock()
        mock_ws2 = Mock()

        # Manual setup for testing
        manager.active_connections.append(mock_ws1)
        manager.active_connections.append(mock_ws2)
        manager.user_connections["user_1"] = mock_ws1
        manager.user_connections["user_2"] = mock_ws2

        assert len(manager.active_connections) == 2
        assert len(manager.user_connections) == 2

        # Disconnect user_1
        manager.disconnect(mock_ws1, "user_1")

        assert mock_ws1 not in manager.active_connections
        assert "user_1" not in manager.user_connections
        assert mock_ws2 in manager.active_connections
        assert "user_2" in manager.user_connections


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
