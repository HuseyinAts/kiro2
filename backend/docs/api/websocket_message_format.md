# WebSocket Message Format - Blackboard Koordinasyon

Bu dokuman, KIRO2 Multi-Agent Blackboard sisteminin WebSocket mesaj formatini tanimlar.

## Baglanti

### Endpoint

```
WS /api/v1/multi-agent/ws/{client_id}
```

### Baglanti Ornegi

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/multi-agent/ws/client_123');

ws.onopen = () => {
    console.log('Connected to blackboard');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
    console.log('Disconnected:', event.code, event.reason);
};
```

## Mesaj Yapisi

### Temel Mesaj Formati

```json
{
    "message_id": "uuid-v4",
    "type": "message_type",
    "source": "agent_id",
    "target": "agent_id | null",
    "payload": {},
    "timestamp": "ISO-8601",
    "correlation_id": "uuid-v4"
}
```

### Alanlar

| Alan | Tip | Zorunlu | Aciklama |
|------|-----|---------|----------|
| `message_id` | string (UUID) | Evet | Benzersiz mesaj ID |
| `type` | string | Evet | Mesaj tipi (asagida listelenmistir) |
| `source` | string | Evet | Gonderen agent ID |
| `target` | string | null | Hayir | Hedef agent ID (null = broadcast) |
| `payload` | object | Evet | Mesaj icerigi |
| `timestamp` | string | Evet | ISO-8601 formatinda zaman damgasi |
| `correlation_id` | string (UUID) | Hayir | Distributed tracing ID |

## Mesaj Tipleri

### 1. data_written

Blackboard'a veri yazildiginda.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "data_written",
    "source": "matematik_agent",
    "target": null,
    "payload": {
        "key": "soru_123",
        "value": {
            "soru_metni": "2x + 3 = 7 denklemini cozunuz",
            "zorluk": 0.5
        },
        "priority": "medium"
    },
    "timestamp": "2026-01-18T14:30:00.000Z",
    "correlation_id": "abc123-def456"
}
```

### 2. data_read

Blackboard'dan veri okunurken.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440001",
    "type": "data_read",
    "source": "fizik_agent",
    "target": null,
    "payload": {
        "key": "soru_123",
        "reader": "fizik_agent"
    },
    "timestamp": "2026-01-18T14:30:01.000Z"
}
```

### 3. data_deleted

Veri silindiginde.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440002",
    "type": "data_deleted",
    "source": "admin_agent",
    "target": null,
    "payload": {
        "key": "soru_123"
    },
    "timestamp": "2026-01-18T14:30:02.000Z"
}
```

### 4. agent_registered

Yeni agent kayit oldugunda.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440003",
    "type": "agent_registered",
    "source": "registry",
    "target": null,
    "payload": {
        "agent_id": "yeni_matematik_agent",
        "capabilities": ["matematik", "geometri"],
        "domain": "matematik"
    },
    "timestamp": "2026-01-18T14:30:03.000Z"
}
```

### 5. agent_unregistered

Agent kayittan cikarildiginda.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440004",
    "type": "agent_unregistered",
    "source": "registry",
    "target": null,
    "payload": {
        "agent_id": "eski_agent",
        "reason": "health_check_failed"
    },
    "timestamp": "2026-01-18T14:30:04.000Z"
}
```

### 6. coordination_request

Agent koordinasyon istegi.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440005",
    "type": "coordination_request",
    "source": "orchestrator",
    "target": "matematik_agent",
    "payload": {
        "task_id": "task_456",
        "question": "Integral hesaplama",
        "context": {
            "student_level": "orta",
            "previous_attempts": 2
        },
        "priority": "high"
    },
    "timestamp": "2026-01-18T14:30:05.000Z",
    "correlation_id": "task-chain-789"
}
```

### 7. coordination_response

Koordinasyon istegine yanit.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440006",
    "type": "coordination_response",
    "source": "matematik_agent",
    "target": "orchestrator",
    "payload": {
        "task_id": "task_456",
        "status": "completed",
        "result": {
            "cozum": "Integral sonucu: x^2 + C",
            "adimlar": ["...", "..."]
        },
        "latency_ms": 45.2
    },
    "timestamp": "2026-01-18T14:30:06.000Z",
    "correlation_id": "task-chain-789"
}
```

### 8. handoff_request

Agent-to-agent handoff istegi.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440007",
    "type": "handoff_request",
    "source": "matematik_agent",
    "target": "fizik_agent",
    "payload": {
        "handoff_id": "handoff_001",
        "capability_needed": "fizik",
        "context": {
            "soru": "Enerji korunumu problemi",
            "ogrenci_id": "student_123"
        },
        "chain_depth": 1
    },
    "timestamp": "2026-01-18T14:30:07.000Z",
    "correlation_id": "task-chain-789"
}
```

### 9. handoff_ack

Handoff onay mesaji.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440008",
    "type": "handoff_ack",
    "source": "fizik_agent",
    "target": "matematik_agent",
    "payload": {
        "handoff_id": "handoff_001",
        "accepted": true
    },
    "timestamp": "2026-01-18T14:30:08.000Z",
    "correlation_id": "task-chain-789"
}
```

### 10. error

Hata mesaji.

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440009",
    "type": "error",
    "source": "system",
    "target": "matematik_agent",
    "payload": {
        "error_code": "CHAIN_LIMIT_EXCEEDED",
        "message": "Handoff chain limit (5) exceeded",
        "details": {
            "current_depth": 5,
            "max_depth": 5
        }
    },
    "timestamp": "2026-01-18T14:30:09.000Z"
}
```

## Hata Kodlari

| Kod | Aciklama |
|-----|----------|
| `INVALID_MESSAGE` | Gecersiz mesaj formati |
| `AGENT_NOT_FOUND` | Agent bulunamadi |
| `CHAIN_LIMIT_EXCEEDED` | Handoff zincir limiti asildi (max 5) |
| `CONNECTION_LIMIT_EXCEEDED` | Baglanti limiti asildi (max 3/kullanici) |
| `TIMEOUT` | Islem zaman asimi |
| `UNAUTHORIZED` | Yetkilendirme hatasi |
| `INTERNAL_ERROR` | Sunucu hatasi |

## Heartbeat

Baglanti canliligini kontrol etmek icin ping/pong mekanizmasi kullanilir.

### Ping (Server -> Client)

```json
{
    "type": "ping",
    "timestamp": "2026-01-18T14:30:10.000Z"
}
```

### Pong (Client -> Server)

```json
{
    "type": "pong",
    "timestamp": "2026-01-18T14:30:10.500Z"
}
```

**Not:** 30 saniye icerisinde pong alinmazsa baglanti kapatilir.

## Baglanti Limitleri

- **Kullanici basina:** Max 3 concurrent baglanti (REQ-2.6)
- **Heartbeat araligi:** 30 saniye
- **Timeout:** 60 saniye

Limit asildiginda en eski baglanti FIFO prensibine gore kapatilir.

## Ornek: Tam Istek/Yanit Akisi

```
Client                    Server                    Agent
   |                         |                         |
   |-- connect ------------->|                         |
   |<-- connected ---------->|                         |
   |                         |                         |
   |-- coordination_req ---->|                         |
   |                         |-- route to agent ------>|
   |                         |<-- process -------------|
   |<-- coordination_res ----|                         |
   |                         |                         |
   |<-- ping ----------------|                         |
   |-- pong ---------------->|                         |
   |                         |                         |
   |-- disconnect ---------->|                         |
```

## TypeScript Tipleri

```typescript
interface BlackboardMessage {
    message_id: string;
    type: MessageType;
    source: string;
    target: string | null;
    payload: Record<string, unknown>;
    timestamp: string;
    correlation_id?: string;
}

type MessageType =
    | 'data_written'
    | 'data_read'
    | 'data_deleted'
    | 'agent_registered'
    | 'agent_unregistered'
    | 'coordination_request'
    | 'coordination_response'
    | 'handoff_request'
    | 'handoff_ack'
    | 'error'
    | 'ping'
    | 'pong';

type Priority = 'low' | 'medium' | 'high' | 'critical';
```

## Python Tipleri

```python
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class MessageType(str, Enum):
    DATA_WRITTEN = "data_written"
    DATA_READ = "data_read"
    DATA_DELETED = "data_deleted"
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    COORDINATION_REQUEST = "coordination_request"
    COORDINATION_RESPONSE = "coordination_response"
    HANDOFF_REQUEST = "handoff_request"
    HANDOFF_ACK = "handoff_ack"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class BlackboardMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    source: str
    target: Optional[str] = None
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
```
