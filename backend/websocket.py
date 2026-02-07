"""
WebSocket connection handler
Real-time chat and exam functionality
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}
        self.exam_connections: Dict[str, List[WebSocket]] = {}  # sinav_id -> websockets
        self.exam_timers: Dict[str, asyncio.Task] = {}  # sinav_id -> timer task

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        if client_id:
            self.user_connections[client_id] = websocket

    def disconnect(self, websocket: WebSocket, client_id: str = None):
        """Remove connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if client_id and client_id in self.user_connections:
            del self.user_connections[client_id]

        # Remove from exam connections
        for sinav_id, connections in self.exam_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                if not connections:  # No more connections for this exam
                    del self.exam_connections[sinav_id]
                    # Cancel timer if exists
                    if sinav_id in self.exam_timers:
                        self.exam_timers[sinav_id].cancel()
                        del self.exam_timers[sinav_id]
                break

    async def connect_to_exam(self, websocket: WebSocket, sinav_id: str):
        """Connect to specific exam session"""
        if sinav_id not in self.exam_connections:
            self.exam_connections[sinav_id] = []
        self.exam_connections[sinav_id].append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_text(message)
        except (WebSocketDisconnect, ConnectionError, RuntimeError) as e:
            # Connection might be closed
            logger.debug(f"WebSocket send failed: {e}")
            pass

    async def send_json_message(self, data: dict, websocket: WebSocket):
        """Send JSON message to specific client"""
        try:
            await websocket.send_text(json.dumps(data))
        except (WebSocketDisconnect, ConnectionError, RuntimeError) as e:
            # Connection might be closed
            logger.debug(f"WebSocket JSON send failed: {e}")
            pass

    async def broadcast_to_exam(self, sinav_id: str, data: dict):
        """Broadcast message to all clients in specific exam"""
        if sinav_id in self.exam_connections:
            message = json.dumps(data)
            disconnected = []

            for websocket in self.exam_connections[sinav_id]:
                try:
                    await websocket.send_text(message)
                except (WebSocketDisconnect, ConnectionError, RuntimeError):
                    disconnected.append(websocket)

            # Remove disconnected websockets
            for ws in disconnected:
                self.exam_connections[sinav_id].remove(ws)

    async def broadcast(self, message: str):
        """Broadcast to all connected clients"""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except (WebSocketDisconnect, ConnectionError, RuntimeError):
                disconnected.append(connection)

        # Remove disconnected connections
        for ws in disconnected:
            self.active_connections.remove(ws)

    async def start_exam_timer(self, sinav_id: str, duration_seconds: int):
        """Start exam timer with periodic updates"""

        async def timer_task():
            remaining_time = duration_seconds

            while remaining_time > 0:
                await asyncio.sleep(1)
                remaining_time -= 1

                # Send time update every 10 seconds
                if remaining_time % 10 == 0:
                    await self.broadcast_to_exam(
                        sinav_id,
                        {
                            "type": "time_update",
                            "remaining_time": remaining_time,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                # Send warning at 5 minutes
                if remaining_time == 300:
                    await self.broadcast_to_exam(
                        sinav_id,
                        {
                            "type": "time_warning",
                            "message": "Sınav sürenizin 5 dakikası kaldı!",
                            "remaining_time": remaining_time,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                # Send final warning at 1 minute
                if remaining_time == 60:
                    await self.broadcast_to_exam(
                        sinav_id,
                        {
                            "type": "time_warning",
                            "message": "Sınav sürenizin 1 dakikası kaldı!",
                            "remaining_time": remaining_time,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

            # Time's up - auto submit
            await self.broadcast_to_exam(
                sinav_id,
                {
                    "type": "auto_submit",
                    "message": "Sınav süresi doldu. Sınavınız otomatik olarak gönderildi.",
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Clean up
            if sinav_id in self.exam_timers:
                del self.exam_timers[sinav_id]

        # Cancel existing timer if any
        if sinav_id in self.exam_timers:
            self.exam_timers[sinav_id].cancel()

        # Start new timer
        self.exam_timers[sinav_id] = asyncio.create_task(timer_task())

    def stop_exam_timer(self, sinav_id: str):
        """Stop exam timer"""
        if sinav_id in self.exam_timers:
            self.exam_timers[sinav_id].cancel()
            del self.exam_timers[sinav_id]

    async def send_exam_status_update(self, sinav_id: str, status_data: dict):
        """Send exam status update to all connected clients"""
        await self.broadcast_to_exam(
            sinav_id,
            {
                "type": "status_update",
                "data": status_data,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def get_exam_connection_count(self, sinav_id: str) -> int:
        """Get number of active connections for an exam"""
        return len(self.exam_connections.get(sinav_id, []))
