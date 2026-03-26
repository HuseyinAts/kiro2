"""
Multi-Agent Blackboard API Endpoints
Teknofest 2025 - Eğitim Eylemci Projesi

Bu API:
- Multi-agent blackboard sistemine HTTP erişimi sağlar
- WebSocket tabanlı gerçek zamanlı senkronizasyon sunar
- Agent koordinasyonu için REST endpoint'leri içerir
- Performans metrikleri ve monitoring sağlar
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field

from algorithms.multi_agent_blackboard import EventType, Priority, get_blackboard
from core.dependencies import get_current_user, AuthenticatedUser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(prefix="/api/v1/multi-agent", tags=["Multi-Agent Blackboard"])


# Pydantic modelleri
class WriteDataRequest(BaseModel):
    """Veri yazma isteği"""

    key: str = Field(..., description="Veri anahtarı")
    value: Any = Field(..., description="Veri değeri")
    ttl_seconds: Optional[int] = Field(None, description="Yaşam süresi (saniye)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Ek metadata")
    priority: str = Field(
        "MEDIUM", description="Olay önceliği (LOW, MEDIUM, HIGH, CRITICAL)"
    )


class ReadDataRequest(BaseModel):
    """Veri okuma isteği"""

    key: str = Field(..., description="Veri anahtarı")


class DeleteDataRequest(BaseModel):
    """Veri silme isteği"""

    key: str = Field(..., description="Veri anahtarı")


class SubscriptionRequest(BaseModel):
    """Abonelik isteği"""

    agent_name: str = Field(..., description="Agent adı")
    event_types: List[str] = Field(..., description="Olay tipleri")
    key_patterns: Optional[List[str]] = Field(None, description="Key pattern'leri")
    priority_filter: Optional[str] = Field(None, description="Minimum öncelik seviyesi")


class CoordinationRequest(BaseModel):
    """Koordinasyon isteği"""

    target_agents: List[str] = Field(..., description="Hedef agent'lar")
    coordination_type: str = Field(..., description="Koordinasyon tipi")
    parameters: Dict[str, Any] = Field(..., description="Koordinasyon parametreleri")
    timeout_seconds: int = Field(30, description="Timeout süresi")


class CoordinationResponse(BaseModel):
    """Koordinasyon yanıtı"""

    coordination_id: str = Field(..., description="Koordinasyon ID'si")
    response_data: Dict[str, Any] = Field(..., description="Yanıt verisi")


class BlackboardResponse(BaseModel):
    """Genel blackboard yanıtı"""

    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Utility fonksiyonları
def _get_priority_enum(priority_str: str) -> Priority:
    """String'den Priority enum'a çevir"""
    try:
        return Priority[priority_str.upper()]
    except KeyError:
        return Priority.MEDIUM


def _get_event_types(event_type_strings: List[str]) -> List[EventType]:
    """String listesinden EventType listesine çevir"""
    event_types = []
    for event_str in event_type_strings:
        try:
            event_types.append(EventType[event_str.upper()])
        except KeyError:
            logger.warning(f"Unknown event type: {event_str}")
    return event_types


# API Endpoints


@router.post("/write", response_model=BlackboardResponse)
async def write_data(request: WriteDataRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Blackboard'a veri yaz

    Bu endpoint agent'ların blackboard'a veri yazmasını sağlar.
    Yazılan veri abone olan tüm agent'lara gerçek zamanlı olarak bildirilir.
    """
    try:
        blackboard = get_blackboard()

        # Agent adını user'dan al (gerçek implementasyonda agent authentication olacak)
        source_agent = getattr(current_user, "username", "unknown_agent")

        priority = _get_priority_enum(request.priority)

        success = await blackboard.write(
            key=request.key,
            value=request.value,
            source_agent=source_agent,
            ttl_seconds=request.ttl_seconds,
            metadata=request.metadata,
            priority=priority,
        )

        if success:
            return BlackboardResponse(
                success=True,
                message=f"Data written successfully: {request.key}",
                data={"key": request.key, "source_agent": source_agent},
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to write data")

    except Exception as e:
        logger.error(f"Write data API error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/read/{key}", response_model=BlackboardResponse)
async def read_data(key: str, current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Blackboard'dan veri oku

    Bu endpoint agent'ların blackboard'dan veri okumasını sağlar.
    """
    try:
        blackboard = get_blackboard()

        # Agent adını user'dan al
        reader_agent = getattr(current_user, "username", "unknown_agent")

        value = blackboard.read(key, reader_agent)

        if value is not None:
            return BlackboardResponse(
                success=True,
                message=f"Data read successfully: {key}",
                data={"key": key, "value": value, "reader_agent": reader_agent},
            )
        else:
            return BlackboardResponse(
                success=False, message=f"Data not found: {key}", data=None
            )

    except Exception as e:
        logger.error(f"Read data API error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.delete("/delete/{key}", response_model=BlackboardResponse)
async def delete_data(key: str, current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Blackboard'dan veri sil

    Bu endpoint agent'ların blackboard'dan veri silmesini sağlar.
    """
    try:
        blackboard = get_blackboard()

        # Agent adını user'dan al
        source_agent = getattr(current_user, "username", "unknown_agent")

        success = await blackboard.delete(key, source_agent)

        if success:
            return BlackboardResponse(
                success=True,
                message=f"Data deleted successfully: {key}",
                data={"key": key, "source_agent": source_agent},
            )
        else:
            return BlackboardResponse(
                success=False,
                message=f"Data not found or delete failed: {key}",
                data=None,
            )

    except Exception as e:
        logger.error(f"Delete data API error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/subscribe", response_model=BlackboardResponse)
async def subscribe_agent(
    request: SubscriptionRequest, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Agent'ı blackboard olaylarına abone et

    Bu endpoint agent'ların belirli olay tiplerine abone olmasını sağlar.
    """
    try:
        blackboard = get_blackboard()

        event_types = _get_event_types(request.event_types)
        priority_filter = (
            _get_priority_enum(request.priority_filter)
            if request.priority_filter
            else None
        )

        success = blackboard.subscribe(
            agent_name=request.agent_name,
            event_types=event_types,
            key_patterns=request.key_patterns,
            priority_filter=priority_filter,
        )

        if success:
            return BlackboardResponse(
                success=True,
                message=f"Agent subscribed successfully: {request.agent_name}",
                data={
                    "agent_name": request.agent_name,
                    "event_types": request.event_types,
                    "key_patterns": request.key_patterns,
                },
            )
        else:
            raise HTTPException(
                status_code=400, detail="Subscription failed - agent not registered"
            )

    except Exception as e:
        logger.error(f"Subscribe API error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/coordination/request", response_model=BlackboardResponse)
async def request_coordination(
    request: CoordinationRequest, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Agent koordinasyonu talep et

    Bu endpoint agent'ların diğer agent'larla koordinasyon kurmasını sağlar.
    """
    try:
        blackboard = get_blackboard()

        # Agent adını user'dan al
        requester_agent = getattr(current_user, "username", "unknown_agent")

        result = await blackboard.request_coordination(
            requester_agent=requester_agent,
            target_agents=request.target_agents,
            coordination_type=request.coordination_type,
            parameters=request.parameters,
            timeout_seconds=request.timeout_seconds,
        )

        return BlackboardResponse(
            success=result.get("success", False),
            message="Coordination request processed",
            data=result,
        )

    except Exception as e:
        logger.error(f"Coordination request API error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/coordination/respond", response_model=BlackboardResponse)
async def respond_coordination(
    response: CoordinationResponse, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Koordinasyon talebine yanıt ver

    Bu endpoint agent'ların koordinasyon taleplerine yanıt vermesini sağlar.
    """
    try:
        blackboard = get_blackboard()

        # Agent adını user'dan al
        responding_agent = getattr(current_user, "username", "unknown_agent")

        success = await blackboard.respond_to_coordination(
            coordination_id=response.coordination_id,
            responding_agent=responding_agent,
            response_data=response.response_data,
        )

        if success:
            return BlackboardResponse(
                success=True,
                message="Coordination response sent successfully",
                data={
                    "coordination_id": response.coordination_id,
                    "responding_agent": responding_agent,
                },
            )
        else:
            raise HTTPException(status_code=400, detail="Coordination response failed")

    except Exception as e:
        logger.error(f"Coordination response API error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/metrics", response_model=BlackboardResponse)
async def get_metrics(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Blackboard performans metriklerini al

    Bu endpoint blackboard sisteminin performans metriklerini döndürür.
    """
    try:
        blackboard = get_blackboard()
        metrics = blackboard.get_metrics()

        return BlackboardResponse(
            success=True, message="Metrics retrieved successfully", data=metrics
        )

    except Exception as e:
        logger.error(f"Metrics API error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/agents/status", response_model=BlackboardResponse)
async def get_agent_status(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Agent durumlarını al

    Bu endpoint kayıtlı agent'ların durumlarını döndürür.
    """
    try:
        blackboard = get_blackboard()
        status = blackboard.get_agent_status()

        return BlackboardResponse(
            success=True, message="Agent status retrieved successfully", data=status
        )

    except Exception as e:
        logger.error(f"Agent status API error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/events/history")
async def get_event_history(
    limit: int = Query(100, description="Maksimum olay sayısı"),
    event_type: Optional[str] = Query(None, description="Olay tipi filtresi"),
    agent_name: Optional[str] = Query(None, description="Agent adı filtresi"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Olay geçmişini al

    Bu endpoint blackboard olay geçmişini döndürür.
    """
    try:
        blackboard = get_blackboard()
        events = blackboard.event_history[-limit:]  # Son N olayı al

        # Filtreleme
        if event_type:
            events = [e for e in events if e.event_type.value == event_type.upper()]

        if agent_name:
            events = [e for e in events if e.source_agent == agent_name]

        # JSON serializable hale getir
        events_data = []
        for event in events:
            event_dict = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "key": event.key,
                "value": event.value,
                "source_agent": event.source_agent,
                "target_agents": event.target_agents,
                "priority": event.priority.value,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata,
                "requires_response": event.requires_response,
                "correlation_id": event.correlation_id,
            }
            events_data.append(event_dict)

        return BlackboardResponse(
            success=True,
            message=f"Event history retrieved: {len(events_data)} events",
            data=events_data,
        )

    except Exception as e:
        logger.error(f"Event history API error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


# WebSocket endpoint for real-time synchronization
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time blackboard synchronization

    Bu endpoint gerçek zamanlı blackboard olaylarını WebSocket üzerinden yayınlar.
    """
    await websocket.accept()

    blackboard = get_blackboard()
    blackboard.add_websocket_connection(client_id, websocket)

    try:
        logger.info(f"WebSocket client connected: {client_id}")

        # Bağlantı mesajı gönder
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Connected to Multi-Agent Blackboard",
                }
            )
        )

        # Bağlantıyı canlı tut
        while True:
            try:
                # Client'dan mesaj bekle (ping/pong için)
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "timestamp": datetime.now().isoformat()}
                        )
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        blackboard.remove_websocket_connection(client_id)


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Blackboard sistem sağlık kontrolü
    """
    try:
        blackboard = get_blackboard()
        metrics = blackboard.get_metrics()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "registered_agents": metrics["registered_agents"],
                "active_data_entries": metrics["active_data_entries"],
                "websocket_connections": metrics["websocket_connections"],
                "average_response_time": metrics["average_response_time"],
            },
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }
