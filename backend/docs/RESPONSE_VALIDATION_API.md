# Response Validation API Documentation

AI Agent Yanit Dogrulama Sistemi API Dokumantasyonu

## Overview

Bu API, AI agent yanitlarini 3 katmanli dogrulama sisteminden gecirir:
- **Agent-specific validation** (30% weight): Agent tipine ozgu kurallar
- **Fact-checking** (40% weight): MEB, RAG, Wikipedia kaynakli dogrulama
- **Consistency checking** (30% weight): Gecmis yanitlarla tutarlilik

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### 1. Validate Response

Bir AI agent yanitini tam dogrulama pipeline'indan gecirir.

```
POST /validate-response
```

#### Request Body

```json
{
  "agent_type": "study_buddy",
  "response_id": "resp_123",
  "user_id": "user_456",
  "query": "Osmanli Imparatorlugu ne zaman kuruldu?",
  "response_text": "Osmanli Imparatorlugu 1299 yilinda kuruldu.",
  "response_data": {},
  "context": {"grade_level": 10}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agent_type | string | Yes | Agent tipi: `learning_path`, `study_buddy`, `exam` |
| response_id | string | Yes | Yanit unique ID'si |
| user_id | string | Yes | Kullanici ID'si |
| query | string | Yes | Kullanici sorusu/istegi |
| response_text | string | Yes | Agent'in metin yaniti |
| response_data | object | No | Agent'a ozgu yapilandirilmis veri |
| context | object | No | Ek baglam bilgisi |

#### Response (200 OK)

```json
{
  "response_id": "resp_123",
  "confidence_score": 0.87,
  "action": "approve",
  "action_description": "Yanit yuksek guvenle onaylandi",
  "errors": [],
  "warnings": ["Bazi kaynaklar dogrulanamadi"],
  "suggestions": ["Kaynak cesitliligini artirin"],
  "duration_seconds": 0.45,
  "timestamp": "2026-01-20T12:30:45.123456"
}
```

| Field | Type | Description |
|-------|------|-------------|
| response_id | string | Yanit ID'si |
| confidence_score | float | Guven skoru (0-1) |
| action | string | Aksiyon: `approve`, `review`, `reject` |
| action_description | string | Aksiyon aciklamasi |
| errors | array | Hata listesi |
| warnings | array | Uyari listesi |
| suggestions | array | Oneri listesi |
| duration_seconds | float | Dogrulama suresi (saniye) |
| timestamp | string | ISO 8601 zaman damgasi |

#### Error Responses

| Status | Description |
|--------|-------------|
| 400 | Gecersiz agent tipi |
| 500 | Dogrulama hatasi |

---

### 2. Quick Validate

Sadece agent-specific dogrulama yapar (hizli sonuc).

```
POST /validate-quick
```

#### Request Body

Ayni `POST /validate-response` gibi.

#### Response (200 OK)

```json
{
  "response_id": "resp_123",
  "confidence_score": 0.85,
  "action": "approve",
  "quick_validation": true
}
```

---

### 3. Get Validation Report

Belirli bir yanitin dogrulama raporunu getirir.

```
GET /validation-report/{response_id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| response_id | string | Yanit ID'si |

#### Response (200 OK)

Tam dogrulama raporu (validate-response sonucu).

#### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Rapor bulunamadi |

---

### 4. Get Validation Stats (Admin)

Sistem genelindeki dogrulama istatistiklerini getirir.

```
GET /validation-stats?period=all
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| period | string | "all" | Istatistik periyodu: `all`, `today`, `week`, `month` |

#### Response (200 OK)

```json
{
  "total_validations": 1250,
  "average_confidence": 0.856,
  "approval_rate": 87.5,
  "review_rate": 10.2,
  "rejection_rate": 2.3,
  "average_duration": 0.42,
  "by_agent_type": {
    "study_buddy": {"total": 600, "approved": 520, "review": 70, "rejected": 10},
    "learning_path": {"total": 400, "approved": 360, "review": 35, "rejected": 5},
    "exam": {"total": 250, "approved": 220, "review": 25, "rejected": 5}
  },
  "period": "all"
}
```

---

### 5. Get Validation Errors (Admin)

Belirli donemdeki dogrulama hatalarini getirir.

```
GET /validation-errors?period_hours=24
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| period_hours | int | 24 | Son kac saatteki hatalar |

#### Response (200 OK)

```json
{
  "period_hours": 24,
  "error_frequency": {
    "model": 15,
    "data": 8,
    "fact_check": 5,
    "consistency": 3
  },
  "trends": [
    {
      "category": "model",
      "count": 15,
      "percentage_change": -12.5,
      "period": "daily",
      "top_sources": ["study_buddy_validator", "learning_path_validator"]
    }
  ]
}
```

---

### 6. Get Validation Error Report (Admin)

Kapsamli hata analiz raporu olusturur.

```
GET /validation-error-report?period_hours=24
```

#### Response (200 OK)

```json
{
  "report_id": "rpt_abc123",
  "generated_at": "2026-01-20T12:30:45.123456",
  "period_start": "2026-01-19T12:30:45.123456",
  "period_end": "2026-01-20T12:30:45.123456",
  "total_errors": 31,
  "errors_by_category": {"model": 15, "data": 8, "fact_check": 5, "consistency": 3},
  "errors_by_severity": {"critical": 5, "high": 12, "medium": 10, "low": 4},
  "errors_by_agent": {"study_buddy": 15, "learning_path": 10, "exam": 6},
  "trends": [...],
  "suggestions": [
    {
      "category": "model",
      "suggestion": "LLM model parametrelerini optimize edin",
      "priority": 5,
      "examples": ["Temperature degeri dusuruldu (0.7 -> 0.5)"],
      "estimated_impact": "high"
    }
  ],
  "top_error_messages": [
    {"message": "LLM inference timeout", "count": 8},
    {"message": "Redis connection failed", "count": 5}
  ]
}
```

---

### 7. Get Improvement Suggestions

Hata analizine dayali iyilestirme onerileri.

```
GET /validation-suggestions?period_hours=24
```

#### Response (200 OK)

```json
{
  "period_hours": 24,
  "suggestions": [
    {
      "category": "model",
      "suggestion": "LLM model parametrelerini optimize edin",
      "priority": 5,
      "examples": ["Temperature degeri dusuruldu (0.7 -> 0.5)"],
      "estimated_impact": "high"
    }
  ]
}
```

---

### 8. Hook Management

#### Enable Validation Hook

```
POST /validation-hook/enable
```

#### Disable Validation Hook

```
POST /validation-hook/disable
```

#### Get Hook Stats

```
GET /validation-hook/stats
```

#### Response

```json
{
  "enabled": true,
  "stats": {
    "total_triggered": 1250,
    "approved": 1094,
    "review": 128,
    "rejected": 28,
    "errors": 0
  }
}
```

---

## Confidence Score Interpretation

| Score Range | Action | Description |
|-------------|--------|-------------|
| >= 0.80 | approve | Yanit yuksek guvenle onaylandi |
| 0.50 - 0.79 | review | Yanit manuel inceleme icin isaretlendi |
| < 0.50 | reject | Yanit reddedildi, yeniden olusturulmali |

## Validation Weights

| Component | Weight | Description |
|-----------|--------|-------------|
| Agent-specific | 30% | Agent tipine ozgu kurallar |
| Fact-checking | 40% | MEB, RAG, Wikipedia dogrulama |
| Consistency | 30% | Gecmis yanitlarla tutarlilik |

## Fact-Checking Priority

| Source | Weight | Description |
|--------|--------|-------------|
| MEB | 60% | Milli Egitim Bakanligi kaynaklari |
| RAG | 30% | Vector database (pgvector) |
| Wikipedia | 10% | Turkce Wikipedia |

## Error Categories

| Category | Description |
|----------|-------------|
| agent | Agent-specific hatalar |
| model | LLM model hatalari |
| data | Veri kaynakli hatalar |
| validation | Dogrulama hatalari |
| consistency | Tutarlilik hatalari |
| fact_check | Fact-checking hatalari |

## Error Severity

| Severity | Description |
|----------|-------------|
| critical | Sistemin calismasini etkileyen |
| high | Kullanici deneyimini ciddi etkileyen |
| medium | Orta duzey etkili |
| low | Dusuk etkili |

## Performance Requirements

- **Ortalama Dogrulama Suresi:** < 2 saniye
- **Ortalama Confidence Score:** >= 0.85
- **Otomatik Onay Orani:** >= 85%
- **Hata Tespit Orani:** >= 90%
- **Yanlis Pozitif Orani:** < 5%

## Example Usage

### Python

```python
import httpx

async def validate_response():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/validate-response",
            json={
                "agent_type": "study_buddy",
                "response_id": "resp_123",
                "user_id": "user_456",
                "query": "2+2 kac eder?",
                "response_text": "2+2 = 4 eder.",
            }
        )
        result = response.json()
        print(f"Confidence: {result['confidence_score']}")
        print(f"Action: {result['action']}")
```

### cURL

```bash
curl -X POST http://localhost:8000/api/v1/validate-response \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "study_buddy",
    "response_id": "resp_123",
    "user_id": "user_456",
    "query": "Osmanli ne zaman kuruldu?",
    "response_text": "Osmanli 1299 yilinda kuruldu."
  }'
```

## Related Files

- `backend/api/response_validation_api.py` - API endpoints
- `backend/orchestrator/response_validation_orchestrator.py` - Orchestrator
- `backend/validators/` - Agent-specific validators
- `backend/fact_checking/` - Fact-checking modules
- `backend/consistency/` - Consistency checking modules
- `backend/scoring/confidence_scorer.py` - Confidence scoring
- `backend/hooks/response_validation_hook.py` - Stop hook
- `backend/validators/error_reporter.py` - Error reporting
