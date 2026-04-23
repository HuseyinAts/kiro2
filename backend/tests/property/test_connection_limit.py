"""
Property-Based Tests - WebSocket Connection Limit (REQ-2.6)

Bu modul, hypothesis kullanarak WebSocket connection limit icin
property-based testler icerir.

Property 4: Connection Limit - Max 3 concurrent WebSocket connections per user

Boris Cherny Standards: Minimum 100 iterations per property test
"""

import asyncio
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

sys.path.insert(0, "c:/Users/husey/kiro2/backend")


# Configuration from spec REQ-2.6
MAX_CONNECTIONS_PER_USER = 3


@dataclass
class MockWebSocket:
    """Mock WebSocket for testing."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    connected_at: datetime = field(default_factory=datetime.now)
    is_open: bool = True

    async def close(self):
        """Close the connection."""
        self.is_open = False


@dataclass
class ConnectionResult:
    """Result of connection attempt."""
    connected: bool
    connection_id: str | None = None
    closed_connection: str | None = None
    reason: str | None = None


class WebSocketConnectionManager:
    """
    WebSocket Connection Manager (REQ-2.6)

    Enforces per-user connection limits.
    Max 3 concurrent connections per user.
    FIFO: Oldest connection closed when limit exceeded.
    """

    def __init__(self, max_connections: int = MAX_CONNECTIONS_PER_USER):
        self.max_connections = max_connections
        self._connections: dict[str, dict[str, MockWebSocket]] = defaultdict(dict)
        self._connection_order: dict[str, list[str]] = defaultdict(list)

    async def connect(
        self,
        user_id: str,
        websocket: MockWebSocket
    ) -> ConnectionResult:
        """
        Register new WebSocket connection with limit enforcement.

        Args:
            user_id: User identifier
            websocket: WebSocket instance

        Returns:
            ConnectionResult with status
        """
        connection_id = websocket.id
        closed_connection = None

        # Check current connection count
        current_count = len(self._connections[user_id])

        if current_count >= self.max_connections:
            # Close oldest connection (FIFO)
            if self._connection_order[user_id]:
                oldest_id = self._connection_order[user_id][0]
                oldest_ws = self._connections[user_id].get(oldest_id)
                if oldest_ws:
                    await oldest_ws.close()
                    del self._connections[user_id][oldest_id]
                    self._connection_order[user_id].pop(0)
                    closed_connection = oldest_id

        # Add new connection
        websocket.user_id = user_id
        self._connections[user_id][connection_id] = websocket
        self._connection_order[user_id].append(connection_id)

        return ConnectionResult(
            connected=True,
            connection_id=connection_id,
            closed_connection=closed_connection
        )

    async def disconnect(self, user_id: str, connection_id: str) -> bool:
        """
        Remove a WebSocket connection.

        Args:
            user_id: User identifier
            connection_id: Connection to remove

        Returns:
            True if removed, False if not found
        """
        if connection_id in self._connections[user_id]:
            ws = self._connections[user_id][connection_id]
            await ws.close()
            del self._connections[user_id][connection_id]
            if connection_id in self._connection_order[user_id]:
                self._connection_order[user_id].remove(connection_id)
            return True
        return False

    def get_user_connections(self, user_id: str) -> list[str]:
        """Get list of connection IDs for a user."""
        return list(self._connections[user_id].keys())

    def get_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user."""
        return len(self._connections[user_id])

    def get_total_connections(self) -> int:
        """Get total number of connections across all users."""
        return sum(len(conns) for conns in self._connections.values())


class TestConnectionLimitProperties:
    """Connection limit property-based testleri (REQ-2.6)."""

    def setup_method(self):
        """Test setup."""
        self.manager = WebSocketConnectionManager()

    @given(
        user_id=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=5,
            max_size=20
        ),
        connection_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_connection_limit_enforced(self, user_id: str, connection_count: int):
        """
        Property 1: Connection limit enforced (REQ-2.6)

        For any user, connection count MUST NOT exceed MAX_CONNECTIONS_PER_USER.
        """
        assume(len(user_id) >= 5)
        manager = WebSocketConnectionManager()

        loop = asyncio.new_event_loop()
        try:
            for i in range(connection_count):
                ws = MockWebSocket()
                loop.run_until_complete(manager.connect(user_id, ws))

            # Property: Never exceed limit
            actual_count = manager.get_connection_count(user_id)
            assert actual_count <= MAX_CONNECTIONS_PER_USER, (
                f"User {user_id} has {actual_count} connections, "
                f"exceeds limit {MAX_CONNECTIONS_PER_USER}"
            )
        finally:
            loop.close()

    @given(
        user_id=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=5,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_oldest_connection_closed_first(self, user_id: str):
        """
        Property 2: FIFO - Oldest connection closed when limit exceeded (REQ-2.6)

        When a 4th connection is made, the 1st connection MUST be closed.
        """
        assume(len(user_id) >= 5)
        manager = WebSocketConnectionManager()

        loop = asyncio.new_event_loop()
        try:
            # Create 4 connections
            connections = []
            for i in range(4):
                ws = MockWebSocket()
                result = loop.run_until_complete(manager.connect(user_id, ws))
                connections.append((result.connection_id, ws))

            # Property: First connection should be closed
            first_ws = connections[0][1]
            assert not first_ws.is_open, "Oldest connection should be closed"

            # Property: Latest 3 should be open
            for conn_id, ws in connections[1:]:
                assert ws.is_open, f"Connection {conn_id} should be open"

            # Property: Count should be 3
            assert manager.get_connection_count(user_id) == 3
        finally:
            loop.close()

    @given(
        user_ids=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("L", "N")),
                min_size=5,
                max_size=10
            ),
            min_size=2,
            max_size=5,
            unique=True
        ),
        connections_per_user=st.integers(min_value=1, max_value=6)
    )
    @settings(max_examples=50)
    def test_limit_per_user_not_global(
        self, user_ids: list[str], connections_per_user: int
    ):
        """
        Property 3: Limit is per-user, not global (REQ-2.6)

        Each user has their own limit of 3 connections.
        """
        assume(all(len(uid) >= 5 for uid in user_ids))
        manager = WebSocketConnectionManager()

        loop = asyncio.new_event_loop()
        try:
            for user_id in user_ids:
                for _ in range(connections_per_user):
                    ws = MockWebSocket()
                    loop.run_until_complete(manager.connect(user_id, ws))

            # Property: Each user has at most 3 connections
            for user_id in user_ids:
                count = manager.get_connection_count(user_id)
                assert count <= MAX_CONNECTIONS_PER_USER, (
                    f"User {user_id} exceeded limit with {count} connections"
                )

            # Property: Total can exceed 3 (multiple users)
            total = manager.get_total_connections()
            max_possible = len(user_ids) * MAX_CONNECTIONS_PER_USER
            assert total <= max_possible
        finally:
            loop.close()

    @given(
        user_id=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=5,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_disconnect_reduces_count(self, user_id: str):
        """
        Property 4: Disconnect reduces connection count (REQ-2.6)

        After disconnecting, the count should decrease by 1.
        """
        assume(len(user_id) >= 5)
        manager = WebSocketConnectionManager()

        loop = asyncio.new_event_loop()
        try:
            # Create 2 connections
            ws1 = MockWebSocket()
            ws2 = MockWebSocket()

            result1 = loop.run_until_complete(manager.connect(user_id, ws1))
            result2 = loop.run_until_complete(manager.connect(user_id, ws2))

            initial_count = manager.get_connection_count(user_id)
            assert initial_count == 2

            # Disconnect one
            loop.run_until_complete(
                manager.disconnect(user_id, result1.connection_id)
            )

            # Property: Count decreased
            final_count = manager.get_connection_count(user_id)
            assert final_count == initial_count - 1
        finally:
            loop.close()


class TestConnectionLimitEdgeCases:
    """Edge case testleri for connection limit."""

    def test_exactly_three_connections_allowed(self):
        """Exactly 3 connections should be allowed."""
        manager = WebSocketConnectionManager()
        user_id = "test_user_123"

        loop = asyncio.new_event_loop()
        try:
            for i in range(3):
                ws = MockWebSocket()
                result = loop.run_until_complete(manager.connect(user_id, ws))
                assert result.connected
                assert result.closed_connection is None  # No closure needed

            assert manager.get_connection_count(user_id) == 3
        finally:
            loop.close()

    def test_fourth_connection_closes_first(self):
        """Fourth connection should close the first."""
        manager = WebSocketConnectionManager()
        user_id = "test_user_456"

        loop = asyncio.new_event_loop()
        try:
            connections = []
            for i in range(4):
                ws = MockWebSocket()
                result = loop.run_until_complete(manager.connect(user_id, ws))
                connections.append((result, ws))

            # Fourth connection should report closure
            fourth_result = connections[3][0]
            assert fourth_result.closed_connection is not None

            # First should be closed
            assert not connections[0][1].is_open

            # Count should still be 3
            assert manager.get_connection_count(user_id) == 3
        finally:
            loop.close()

    def test_rapid_connect_disconnect_cycle(self):
        """Rapid connect/disconnect should maintain invariant."""
        manager = WebSocketConnectionManager()
        user_id = "rapid_user"

        loop = asyncio.new_event_loop()
        try:
            for _ in range(20):
                # Connect
                ws = MockWebSocket()
                result = loop.run_until_complete(manager.connect(user_id, ws))

                # Immediately disconnect
                loop.run_until_complete(
                    manager.disconnect(user_id, result.connection_id)
                )

            # Property: Count should be 0 after all disconnects
            assert manager.get_connection_count(user_id) == 0
        finally:
            loop.close()

    def test_nonexistent_user_disconnect(self):
        """Disconnecting from nonexistent user should return False."""
        manager = WebSocketConnectionManager()

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                manager.disconnect("nonexistent_user", "fake_connection")
            )
            assert result is False
        finally:
            loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-seed=0"])
