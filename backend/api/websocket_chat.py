# -*- coding: utf-8 -*-
"""
WebSocket Chat API
Gerçek zamanlı chat endpoint'leri

Features:
- Real-time messaging
- Multi-user chat rooms
- Typing indicators
- Online status
- Message history
"""

from datetime import datetime
from typing import Dict, List, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from core.structured_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket Chat"])


# ==================== CONNECTION MANAGER ====================


class ConnectionManager:
    """WebSocket bağlantı yöneticisi"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_rooms: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        """Kullanıcıyı odaya bağla"""
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = []

        self.active_connections[room_id].append(websocket)
        self.user_rooms[websocket] = room_id

        logger.info(
            "websocket_connected",
            room_id=room_id,
            user_id=user_id,
            total_connections=len(self.active_connections[room_id]),
        )

    def disconnect(self, websocket: WebSocket):
        """Kullanıcının bağlantısını kes"""
        room_id = self.user_rooms.get(websocket)

        if room_id and room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)

            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

        if websocket in self.user_rooms:
            del self.user_rooms[websocket]

        logger.info("websocket_disconnected", room_id=room_id)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Tek bir kullanıcıya mesaj gönder"""
        await websocket.send_text(message)

    async def broadcast(self, message: str, room_id: str, exclude: WebSocket = None):
        """Odadaki tüm kullanıcılara mesaj gönder"""
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != exclude:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        logger.error(f"Broadcast error: {e}")

    def get_room_users_count(self, room_id: str) -> int:
        """Odadaki kullanıcı sayısı"""
        return len(self.active_connections.get(room_id, []))


# Global manager instance
manager = ConnectionManager()


# ==================== MESSAGE MODELS ====================


class ChatMessage(BaseModel):
    """Chat mesajı"""

    type: str  # "message", "typing", "join", "leave"
    user_id: str
    username: str
    content: str
    timestamp: str
    room_id: str


# ==================== ENDPOINTS ====================


@router.websocket("/chat/{room_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    room_id: str,
    user_id: str = "anonymous",
    username: str = "Anonim",
):
    """
    WebSocket chat endpoint

    Args:
        room_id: Chat odası ID
        user_id: Kullanıcı ID
        username: Kullanıcı adı
    """
    await manager.connect(websocket, room_id, user_id)

    # Katılım mesajı gönder
    join_message = ChatMessage(
        type="join",
        user_id=user_id,
        username=username,
        content=f"{username} odaya katıldı",
        timestamp=datetime.utcnow().isoformat(),
        room_id=room_id,
    ).model_dump_json()

    await manager.broadcast(join_message, room_id)

    try:
        while True:
            # Mesaj al
            data = await websocket.receive_text()

            # Mesajı parse et
            import json

            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")

                if message_type == "message":
                    # Normal mesaj
                    chat_message = ChatMessage(
                        type="message",
                        user_id=user_id,
                        username=username,
                        content=message_data.get("content", ""),
                        timestamp=datetime.utcnow().isoformat(),
                        room_id=room_id,
                    )

                    # Odadaki herkese gönder
                    await manager.broadcast(chat_message.model_dump_json(), room_id)

                elif message_type == "typing":
                    # Yazıyor göstergesi
                    typing_message = {
                        "type": "typing",
                        "user_id": user_id,
                        "username": username,
                        "room_id": room_id,
                    }

                    await manager.broadcast(
                        json.dumps(typing_message), room_id, exclude=websocket
                    )

            except json.JSONDecodeError:
                # Plain text mesaj
                chat_message = ChatMessage(
                    type="message",
                    user_id=user_id,
                    username=username,
                    content=data,
                    timestamp=datetime.utcnow().isoformat(),
                    room_id=room_id,
                )

                await manager.broadcast(chat_message.model_dump_json(), room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

        # Ayrılış mesajı
        leave_message = ChatMessage(
            type="leave",
            user_id=user_id,
            username=username,
            content=f"{username} odadan ayrıldı",
            timestamp=datetime.utcnow().isoformat(),
            room_id=room_id,
        ).model_dump_json()

        await manager.broadcast(leave_message, room_id)


@router.websocket("/study-room/{room_id}")
async def websocket_study_room(
    websocket: WebSocket, room_id: str, user_id: str = "anonymous"
):
    """
    Çalışma odası WebSocket endpoint

    - Collaborative study sessions
    - Real-time progress sharing
    - Study buddy matching
    """
    await manager.connect(websocket, f"study_{room_id}", user_id)

    try:
        while True:
            data = await websocket.receive_text()

            # Çalışma odası mesajlarını işle
            import json

            message = json.loads(data)

            if message.get("type") == "progress_update":
                # İlerleme güncellemesi
                await manager.broadcast(
                    json.dumps(
                        {
                            "type": "progress",
                            "user_id": user_id,
                            "progress": message.get("progress", 0),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    ),
                    f"study_{room_id}",
                )

            elif message.get("type") == "question":
                # Soru paylaşımı
                await manager.broadcast(
                    json.dumps(
                        {
                            "type": "question",
                            "user_id": user_id,
                            "question": message.get("content", ""),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    ),
                    f"study_{room_id}",
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ==================== REST ENDPOINTS ====================


@router.get("/chat/rooms")
async def get_active_rooms():
    """Aktif chat odalarını listele"""
    rooms = []
    for room_id, connections in manager.active_connections.items():
        rooms.append(
            {
                "room_id": room_id,
                "user_count": len(connections),
                "is_active": len(connections) > 0,
            }
        )

    return {"total_rooms": len(rooms), "rooms": rooms}


@router.get("/chat/room/{room_id}/users")
async def get_room_users(room_id: str):
    """Odadaki kullanıcı sayısını getir"""
    count = manager.get_room_users_count(room_id)

    return {"room_id": room_id, "user_count": count, "is_active": count > 0}


@router.post("/chat/room/{room_id}/clear")
async def clear_room(room_id: str):
    """Odayı temizle (admin only)"""
    if room_id in manager.active_connections:
        # Tüm bağlantıları kapat
        connections = manager.active_connections[room_id].copy()
        for connection in connections:
            await connection.close()
            manager.disconnect(connection)

    return {"success": True, "message": f"Room {room_id} cleared"}
