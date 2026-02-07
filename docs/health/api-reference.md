# Health Dashboard API Reference

## Base URL

```
/health-dashboard
```

## Endpoints

### GET /endpoints

Tum izlenen endpoint'lerin listesini dondurur.

**Response:**
```json
[
  {
    "path": "/api/v1/users",
    "method": "GET",
    "handler": "get_users",
    "requires_auth": true,
    "is_critical": false,
    "expected_status_codes": [200]
  },
  {
    "path": "/health",
    "method": "GET",
    "handler": "health_check",
    "requires_auth": false,
    "is_critical": true,
    "expected_status_codes": [200]
  }
]
```

**Status Codes:**
- `200 OK`: Basarili

---

### GET /metrics

Genel saglik metriklerini dondurur.

**Response:**
```json
{
  "total_endpoints": 45,
  "healthy_count": 42,
  "unhealthy_count": 1,
  "degraded_count": 2,
  "health_percentage": 93.3,
  "avg_response_time_ms": 85.5,
  "p95_response_time_ms": 180.0,
  "last_check_at": "2024-01-15T10:30:00Z"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total_endpoints` | integer | Toplam endpoint sayisi |
| `healthy_count` | integer | Saglikli endpoint sayisi |
| `unhealthy_count` | integer | Sagliksiz endpoint sayisi |
| `degraded_count` | integer | Degraded endpoint sayisi |
| `health_percentage` | float | Saglik yuzdesi (0-100) |
| `avg_response_time_ms` | float | Ortalama response time (ms) |
| `p95_response_time_ms` | float | P95 response time (ms) |
| `last_check_at` | string | Son kontrol zamani (ISO 8601) |

---

### GET /sla-report

SLA uyumluluk raporunu dondurur.

**Response:**
```json
{
  "period_start": "2024-01-14T00:00:00Z",
  "period_end": "2024-01-15T00:00:00Z",
  "overall_compliance": 99.5,
  "endpoints": [
    {
      "endpoint": "GET:/api/v1/users",
      "target_uptime": 99.0,
      "actual_uptime": 99.8,
      "target_response_time_ms": 200,
      "actual_p95_response_time_ms": 150,
      "is_compliant": true,
      "violations": []
    },
    {
      "endpoint": "POST:/api/v1/orders",
      "target_uptime": 99.0,
      "actual_uptime": 98.5,
      "target_response_time_ms": 500,
      "actual_p95_response_time_ms": 480,
      "is_compliant": false,
      "violations": ["uptime_below_target"]
    }
  ]
}
```

**Violation Types:**
- `uptime_below_target`: Uptime hedefin altinda
- `response_time_exceeded`: Response time hedefi asildi
- `error_rate_exceeded`: Error rate hedefi asildi

---

### GET /history

Belirli bir zaman araligindaki saglik gecmisini dondurur.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hours` | integer | 24 | Kac saatlik gecmis |
| `endpoint` | string | null | Belirli endpoint filtresi |

**Request:**
```
GET /health-dashboard/history?hours=12&endpoint=GET:/api/v1/users
```

**Response:**
```json
[
  {
    "timestamp": "2024-01-15T10:00:00Z",
    "endpoint": "GET:/api/v1/users",
    "status": "healthy",
    "response_time_ms": 45.5,
    "status_code": 200,
    "error_message": null
  },
  {
    "timestamp": "2024-01-15T09:30:00Z",
    "endpoint": "GET:/api/v1/users",
    "status": "degraded",
    "response_time_ms": 350.0,
    "status_code": 200,
    "error_message": null
  }
]
```

**Status Values:**
- `healthy`: Response time < 200ms, dogru status code
- `degraded`: 200ms <= Response time < 500ms
- `unhealthy`: Response time >= 500ms veya hata

---

### GET /alerts

Aktif alert'lerin listesini dondurur.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `severity` | string | null | Severity filtresi (critical, warning, info) |
| `resolved` | boolean | false | Cozulmus alert'leri dahil et |

**Request:**
```
GET /health-dashboard/alerts?severity=critical&resolved=false
```

**Response:**
```json
[
  {
    "id": "alert-123",
    "endpoint": "GET:/api/v1/payments",
    "type": "endpoint_down",
    "severity": "critical",
    "message": "Endpoint 3 dakikadir yanit vermiyor",
    "created_at": "2024-01-15T10:25:00Z",
    "resolved_at": null,
    "acknowledged": false,
    "acknowledged_by": null
  }
]
```

**Alert Types:**
- `endpoint_down`: Endpoint erisilemez
- `high_response_time`: Response time cok yuksek
- `high_error_rate`: Error rate cok yuksek
- `sla_violation`: SLA ihlali
- `circuit_open`: Circuit breaker acildi

**Severity Levels:**
- `critical`: Acil mudahale gerekli
- `warning`: Dikkat edilmeli
- `info`: Bilgilendirme

---

### POST /alerts/{alert_id}/acknowledge

Bir alert'i onayla.

**Request:**
```json
{
  "acknowledged_by": "admin@kiro2.com",
  "notes": "Inceleniyor"
}
```

**Response:**
```json
{
  "id": "alert-123",
  "acknowledged": true,
  "acknowledged_by": "admin@kiro2.com",
  "acknowledged_at": "2024-01-15T10:30:00Z"
}
```

---

### POST /alerts/{alert_id}/resolve

Bir alert'i cozuldu olarak isaretle.

**Request:**
```json
{
  "resolved_by": "admin@kiro2.com",
  "resolution_notes": "Database baglantisi duzeltildi"
}
```

**Response:**
```json
{
  "id": "alert-123",
  "resolved": true,
  "resolved_by": "admin@kiro2.com",
  "resolved_at": "2024-01-15T10:45:00Z"
}
```

---

## Error Responses

Tum endpoint'ler asagidaki hata formatini kullanir:

```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "hours parametresi pozitif olmali",
    "field": "hours"
  }
}
```

**Common Error Codes:**
- `VALIDATION_ERROR`: Parametre dogrulama hatasi
- `NOT_FOUND`: Kaynak bulunamadi
- `UNAUTHORIZED`: Yetkilendirme hatasi
- `INTERNAL_ERROR`: Sunucu hatasi

---

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| GET endpoints | 100/dakika |
| GET metrics | 100/dakika |
| GET history | 50/dakika |
| POST actions | 20/dakika |

Rate limit asildiginda `429 Too Many Requests` doner.

---

## Webhook Integration

Alert webhook'lari icin asagidaki payload gonderilir:

```json
{
  "event": "alert.created",
  "timestamp": "2024-01-15T10:25:00Z",
  "data": {
    "id": "alert-123",
    "endpoint": "GET:/api/v1/payments",
    "type": "endpoint_down",
    "severity": "critical",
    "message": "Endpoint 3 dakikadir yanit vermiyor"
  }
}
```

**Event Types:**
- `alert.created`: Yeni alert olusturuldu
- `alert.resolved`: Alert cozuldu
- `alert.acknowledged`: Alert onaylandi
- `health.degraded`: Saglik durumu kotulespi
- `health.recovered`: Saglik durumu duzelpti
