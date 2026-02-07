# OpenAPI Documentation - Multi-Agent Blackboard API

Bu dokuman, KIRO2 Multi-Agent Blackboard sisteminin REST API'sini tanimlar.

## Base URL

```
http://localhost:8000/api/v1/multi-agent
```

## Endpoints

### 1. Write to Blackboard

Blackboard'a veri yazar.

**Endpoint:** `POST /write`

**Request Body:**

```json
{
    "key": "string",
    "value": "any",
    "source_agent": "string",
    "priority": "low | medium | high | critical",
    "ttl_seconds": 3600
}
```

**Response (200 OK):**

```json
{
    "success": true,
    "message_id": "uuid-v4",
    "timestamp": "2026-01-18T14:30:00.000Z"
}
```

**cURL Ornegi:**

```bash
curl -X POST http://localhost:8000/api/v1/multi-agent/write \
  -H "Content-Type: application/json" \
  -d '{
    "key": "soru_123",
    "value": {"soru": "2+2=?", "cevap": "4"},
    "source_agent": "matematik_agent",
    "priority": "medium"
  }'
```

---

### 2. Read from Blackboard

Blackboard'dan veri okur.

**Endpoint:** `GET /read/{key}`

**Query Parameters:**

| Parametre | Tip | Zorunlu | Aciklama |
|-----------|-----|---------|----------|
| `reader_agent` | string | Evet | Okuyan agent ID |

**Response (200 OK):**

```json
{
    "key": "soru_123",
    "value": {"soru": "2+2=?", "cevap": "4"},
    "source_agent": "matematik_agent",
    "timestamp": "2026-01-18T14:30:00.000Z",
    "version": 1
}
```

**Response (404 Not Found):**

```json
{
    "error": "KEY_NOT_FOUND",
    "message": "Key 'soru_123' not found"
}
```

**cURL Ornegi:**

```bash
curl "http://localhost:8000/api/v1/multi-agent/read/soru_123?reader_agent=fizik_agent"
```

---

### 3. Delete from Blackboard

Blackboard'dan veri siler.

**Endpoint:** `DELETE /delete/{key}`

**Query Parameters:**

| Parametre | Tip | Zorunlu | Aciklama |
|-----------|-----|---------|----------|
| `source_agent` | string | Evet | Silen agent ID |

**Response (200 OK):**

```json
{
    "success": true,
    "key": "soru_123",
    "deleted_at": "2026-01-18T14:30:00.000Z"
}
```

**cURL Ornegi:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/multi-agent/delete/soru_123?source_agent=admin_agent"
```

---

### 4. Subscribe to Events

Event'lere abone olur.

**Endpoint:** `POST /subscribe`

**Request Body:**

```json
{
    "agent_name": "string",
    "event_types": ["data_written", "data_deleted"],
    "key_patterns": ["soru_*", "cevap_*"]
}
```

**Response (200 OK):**

```json
{
    "success": true,
    "subscription_id": "uuid-v4",
    "subscribed_events": ["data_written", "data_deleted"],
    "key_patterns": ["soru_*", "cevap_*"]
}
```

**cURL Ornegi:**

```bash
curl -X POST http://localhost:8000/api/v1/multi-agent/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "fizik_agent",
    "event_types": ["data_written"],
    "key_patterns": ["*"]
  }'
```

---

### 5. Coordination Request

Agent koordinasyon istegi gonderir.

**Endpoint:** `POST /coordination/request`

**Request Body:**

```json
{
    "source_agent": "string",
    "target_capability": "string",
    "task": {
        "question": "string",
        "context": {}
    },
    "priority": "low | medium | high | critical",
    "timeout_seconds": 60
}
```

**Response (200 OK):**

```json
{
    "task_id": "uuid-v4",
    "status": "pending | processing | completed | failed",
    "assigned_agent": "matematik_agent",
    "estimated_completion_ms": 500
}
```

**cURL Ornegi:**

```bash
curl -X POST http://localhost:8000/api/v1/multi-agent/coordination/request \
  -H "Content-Type: application/json" \
  -d '{
    "source_agent": "orchestrator",
    "target_capability": "matematik",
    "task": {
        "question": "Integral hesapla: x^2 dx",
        "context": {"student_level": "orta"}
    },
    "priority": "high"
  }'
```

---

### 6. Coordination Response

Koordinasyon istegine yanit gonderir.

**Endpoint:** `POST /coordination/respond`

**Request Body:**

```json
{
    "task_id": "uuid-v4",
    "source_agent": "string",
    "status": "completed | failed",
    "result": {},
    "error": null
}
```

**Response (200 OK):**

```json
{
    "success": true,
    "task_id": "uuid-v4",
    "acknowledged_at": "2026-01-18T14:30:00.000Z"
}
```

**cURL Ornegi:**

```bash
curl -X POST http://localhost:8000/api/v1/multi-agent/coordination/respond \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-123",
    "source_agent": "matematik_agent",
    "status": "completed",
    "result": {"cozum": "x^3/3 + C"}
  }'
```

---

### 7. Get Metrics

Sistem metriklerini getirir.

**Endpoint:** `GET /metrics`

**Response (200 OK):**

```json
{
    "total_messages": 15432,
    "messages_per_second": 1250.5,
    "active_agents": 8,
    "healthy_agents": 7,
    "unhealthy_agents": 1,
    "latency": {
        "p50_ms": 2.5,
        "p95_ms": 12.3,
        "p99_ms": 45.2
    },
    "coordination": {
        "total_requests": 5000,
        "success_rate": 98.5,
        "average_latency_ms": 35.2
    },
    "handoffs": {
        "total": 250,
        "successful": 245,
        "failed": 5,
        "chain_limit_rejections": 3
    },
    "connections": {
        "active_websocket": 45,
        "connection_limit_enforcements": 12
    },
    "uptime_seconds": 86400,
    "timestamp": "2026-01-18T14:30:00.000Z"
}
```

**cURL Ornegi:**

```bash
curl http://localhost:8000/api/v1/multi-agent/metrics
```

---

### 8. Get Agent Status

Tum agent'larin durumunu getirir.

**Endpoint:** `GET /agents/status`

**Response (200 OK):**

```json
{
    "agents": [
        {
            "agent_id": "matematik_agent",
            "domain": "matematik",
            "status": "healthy",
            "capabilities": ["matematik", "geometri", "cebir"],
            "last_seen": "2026-01-18T14:29:55.000Z",
            "load": 0.45,
            "response_time_ms": 12.5
        },
        {
            "agent_id": "fizik_agent",
            "domain": "fizik",
            "status": "healthy",
            "capabilities": ["mekanik", "elektrik", "optik"],
            "last_seen": "2026-01-18T14:29:58.000Z",
            "load": 0.32,
            "response_time_ms": 15.2
        }
    ],
    "total": 2,
    "healthy": 2,
    "unhealthy": 0
}
```

**cURL Ornegi:**

```bash
curl http://localhost:8000/api/v1/multi-agent/agents/status
```

---

### 9. Get Event History

Event gecmisini getirir.

**Endpoint:** `GET /events/history`

**Query Parameters:**

| Parametre | Tip | Default | Aciklama |
|-----------|-----|---------|----------|
| `limit` | int | 100 | Max sonuc sayisi |
| `offset` | int | 0 | Baslangic offset |
| `event_type` | string | null | Event tipi filtresi |
| `source_agent` | string | null | Kaynak agent filtresi |
| `since` | datetime | null | Bu tarihten sonraki eventler |

**Response (200 OK):**

```json
{
    "events": [
        {
            "event_id": "evt_001",
            "type": "data_written",
            "source": "matematik_agent",
            "key": "soru_123",
            "timestamp": "2026-01-18T14:30:00.000Z",
            "correlation_id": "corr_001"
        }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0,
    "has_more": false
}
```

**cURL Ornegi:**

```bash
curl "http://localhost:8000/api/v1/multi-agent/events/history?limit=50&event_type=data_written"
```

---

### 10. Health Check

Sistem saglik kontrolu.

**Endpoint:** `GET /health`

**Response (200 OK):**

```json
{
    "status": "healthy",
    "components": {
        "blackboard": "healthy",
        "redis": "healthy",
        "agents": "healthy"
    },
    "version": "1.0.0",
    "uptime_seconds": 86400,
    "timestamp": "2026-01-18T14:30:00.000Z"
}
```

**Response (503 Service Unavailable):**

```json
{
    "status": "unhealthy",
    "components": {
        "blackboard": "healthy",
        "redis": "unhealthy",
        "agents": "degraded"
    },
    "error": "Redis connection failed",
    "timestamp": "2026-01-18T14:30:00.000Z"
}
```

**cURL Ornegi:**

```bash
curl http://localhost:8000/api/v1/multi-agent/health
```

---

### 11. WebSocket Connection

Real-time mesajlasma icin WebSocket baglantisi.

**Endpoint:** `WS /ws/{client_id}`

**Baglanti:**

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/multi-agent/ws/client_123');
```

Detayli mesaj formati icin: [WebSocket Message Format](websocket_message_format.md)

---

## Error Responses

Tum hata yanitlari asagidaki formatta doner:

```json
{
    "error": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {},
    "timestamp": "2026-01-18T14:30:00.000Z"
}
```

### HTTP Status Codes

| Code | Anlam |
|------|-------|
| 200 | Basarili |
| 400 | Gecersiz istek |
| 401 | Yetkilendirme gerekli |
| 403 | Erisim engellendi |
| 404 | Kaynak bulunamadi |
| 409 | Conflict (ornegin duplicate key) |
| 429 | Rate limit asildi |
| 500 | Sunucu hatasi |
| 503 | Servis kullanim disi |

### Error Codes

| Code | Aciklama |
|------|----------|
| `INVALID_REQUEST` | Gecersiz istek formati |
| `KEY_NOT_FOUND` | Anahtar bulunamadi |
| `AGENT_NOT_FOUND` | Agent bulunamadi |
| `UNAUTHORIZED` | Yetkilendirme hatasi |
| `RATE_LIMIT_EXCEEDED` | Hiz limiti asildi |
| `CHAIN_LIMIT_EXCEEDED` | Handoff zincir limiti asildi |
| `CONNECTION_LIMIT_EXCEEDED` | Baglanti limiti asildi |
| `TIMEOUT` | Islem zaman asimi |
| `INTERNAL_ERROR` | Ic sunucu hatasi |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /write | 1000/dakika |
| GET /read | 5000/dakika |
| POST /coordination/* | 500/dakika |
| GET /metrics | 60/dakika |
| WS /ws/* | 3 concurrent/kullanici |

---

## Authentication

Tum API istekleri JWT token gerektirir (production'da).

**Header:**

```
Authorization: Bearer <jwt_token>
```

---

## OpenAPI Specification (Swagger)

```yaml
openapi: 3.0.3
info:
  title: KIRO2 Multi-Agent Blackboard API
  version: 1.0.0
  description: Agent koordinasyon ve iletisim API'si

servers:
  - url: http://localhost:8000/api/v1/multi-agent
    description: Development server

paths:
  /write:
    post:
      summary: Write to blackboard
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WriteRequest'
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WriteResponse'

  /read/{key}:
    get:
      summary: Read from blackboard
      parameters:
        - name: key
          in: path
          required: true
          schema:
            type: string
        - name: reader_agent
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReadResponse'

  /health:
    get:
      summary: Health check
      responses:
        '200':
          description: Healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'

components:
  schemas:
    WriteRequest:
      type: object
      required:
        - key
        - value
        - source_agent
      properties:
        key:
          type: string
        value:
          type: object
        source_agent:
          type: string
        priority:
          type: string
          enum: [low, medium, high, critical]
          default: medium

    WriteResponse:
      type: object
      properties:
        success:
          type: boolean
        message_id:
          type: string
        timestamp:
          type: string
          format: date-time

    ReadResponse:
      type: object
      properties:
        key:
          type: string
        value:
          type: object
        source_agent:
          type: string
        timestamp:
          type: string
          format: date-time

    HealthResponse:
      type: object
      properties:
        status:
          type: string
          enum: [healthy, unhealthy, degraded]
        components:
          type: object
        timestamp:
          type: string
          format: date-time
```
