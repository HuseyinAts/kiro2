# Design Document - Centralized Logging ELK

## Architecture Overview

ELK stack ile centralized logging sistemi: Filebeat → Logstash → Elasticsearch → Kibana pipeline. Structured logging, log aggregation, parsing, visualization, alerting sağlar.

## Components

### 1. Structured Logger (backend/core/structured_logger.py) ✅ IMPLEMENTED
- **Purpose**: JSON format structured logging with Turkish support
- **Dependencies**: structlog==24.1.0
- **Key Features**:
  - JSON formatter via structlog.processors.JSONRenderer
  - Processor chain: add_log_level → TimeStamper → add_app_context → censor_sensitive_data
  - Correlation ID via OpenTelemetry integration
  - User context enrichment (user_id, session_id)
  - Log level filtering (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - PII masking (password, token, secret, api_key, credit_card, ssn, sifre, parola)
  - Windows compatibility (color detection disabled)
  - **KIRO2 Domain Helpers**:
    - `log_exam_event()`: Exam session logging
    - `log_api_request()` / `log_api_response()`: HTTP tracking
    - `log_database_query()`: DB operation logging
    - `log_cache_operation()`: Cache hit/miss logging
    - `log_error_with_context()`: Rich error context

### 1b. Distributed Tracing Middleware (backend/core/tracing_middleware.py) ✅ IMPLEMENTED
- **Purpose**: Request tracing with correlation IDs
- **Dependencies**: opentelemetry-api==1.21.0
- **Key Features**:
  - X-Trace-ID header injection
  - Request/response attribute tracking
  - Performance classification (fast/normal/slow/very_slow)
  - Business logic span managers

### 2. Logstash Pipeline (deployment/logstash/pipeline/main.conf) ⏳ TODO
- **Purpose**: Log processing ve enrichment
- **Dependencies**: logstash==8.11.0
- **Key Features**:
  - Input: beats, file, syslog
  - Filters: grok, json, mutate, geoip, user_agent
  - Output: Elasticsearch
  - Worker threads: 4
  - Batch size: 125

### 3. Elasticsearch Index Manager (backend/services/elasticsearch_service.py) ✅ PARTIAL
- **Purpose**: Index lifecycle management
- **Dependencies**: elasticsearch==8.11.0 (Docker'da çalışıyor)
- **Key Features**:
  - Time-based indices (logs-YYYY.MM.DD)
  - Index templates (mapping, settings) ✅
  - ILM policy (hot-warm-cold) ⏳ TODO
  - Rollover (50GB or 1 day) ⏳ TODO
  - Retention (30 days) ⏳ TODO

### 4. Kibana Dashboard (deployment/kibana/dashboards/) ⏳ TODO
- **Purpose**: Log visualization
- **Dependencies**: kibana==8.11.0
- **Key Features**:
  - Log volume, error rate, top errors
  - KQL search
  - Time range, log level, service filters
  - Line/bar/pie charts, tables
  - Saved searches, dashboard export

### 5. Alert Manager (backend/services/alert_service.py) ⏳ TODO
- **Purpose**: Critical log alerting
- **Dependencies**: elasticsearch==8.11.0
- **Key Features**:
  - Elasticsearch Watcher
  - Error spike detection (threshold-based)
  - Notification channels (email, Slack, PagerDuty)
  - Alert throttling (5 min)
  - Acknowledge/silence

### 6. Log Security (backend/core/structured_logger.py) ✅ IMPLEMENTED
- **Purpose**: Sensitive data protection (same file as Structured Logger)
- **Dependencies**: structlog==24.1.0
- **Key Features**:
  - PII masking via censor_sensitive_data() processor ✅
  - Password redaction (sifre, parola, password, pwd) ✅
  - Role-based access control (Kibana) ⏳ TODO
  - Audit trail ⏳ TODO
  - At-rest encryption (AES-256) ⏳ TODO
  - KVKK/GDPR compliance ✅

## Data Flow

```
                            CURRENT STATE (✅ Implemented)
┌─────────────────────────────────────────────────────────────────┐
│  Application (FastAPI)                                          │
│       ↓                                                         │
│  StructuredLogger (structlog) → stdout/file                     │
│       ↓                                                         │
│  TracingMiddleware (OpenTelemetry) → X-Trace-ID headers         │
└─────────────────────────────────────────────────────────────────┘

                            TARGET STATE (⏳ TODO)
┌─────────────────────────────────────────────────────────────────┐
│  Application → StructuredLogger → Filebeat → Logstash           │
│                                                   ↓             │
│                                           Elasticsearch (8.11.0)│
│                                              ↓         ↓        │
│                                          Kibana   AlertManager  │
└─────────────────────────────────────────────────────────────────┘
```

## Correctness Properties

### Property 1: Log Completeness
```python
@given(log_entry=st.dictionaries(
    keys=st.sampled_from(['timestamp', 'level', 'message', 'correlation_id']),
    values=st.text()
))
def test_log_completeness(log_entry):
    logged = structured_logger.log(log_entry)
    assert all(k in logged for k in ['timestamp', 'level', 'message'])
```

### Property 2: Correlation ID Propagation
```python
@given(correlation_id=st.uuids())
def test_correlation_propagation(correlation_id):
    logs = generate_request_logs(correlation_id)
    assert all(log['correlation_id'] == str(correlation_id) for log in logs)
```

### Property 3: PII Masking
```python
@given(email=st.emails(), phone=st.text(regex=r'\d{10}'))
def test_pii_masking(email, phone):
    log = structured_logger.log({'email': email, 'phone': phone})
    assert '***' in log['email'] and '***' in log['phone']
```

### Property 4: Index Rollover
```python
@given(index_size=st.integers(min_value=0, max_value=100))
def test_index_rollover(index_size):
    should_rollover = index_size >= 50  # 50GB threshold
    assert elasticsearch_service.check_rollover(index_size) == should_rollover
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Log ingestion | >= 10000/sec | >= 5000/sec |
| Query latency | < 2s | < 5s |
| Storage efficiency | >= 70% | >= 50% |
| Cluster availability | >= 99.9% | >= 99% |

## Security Considerations

- TLS encryption (Filebeat → Logstash → Elasticsearch)
- Role-based access control (Kibana)
- PII masking (automatic)
- Audit logging (who accessed what)
- At-rest encryption (AES-256)
- KVKK/GDPR compliance

## Scalability

- Horizontal scaling (Elasticsearch cluster)
- Redis buffering (high load)
- Index sharding (5 primary, 1 replica)
- Hot-warm-cold architecture
- Compression (70% efficiency)

## Monitoring

- Cluster health (green/yellow/red)
- Ingestion rate (logs/sec)
- Query performance (latency)
- Storage usage (GB)
- Alert frequency (alerts/hour)
