# Requirements Document - Blackboard Koordinasyon Sistemi

## Introduction

Bu spec, Sid Bidasaria'nın subagent architecture'ının merkezi koordinasyon mekanizması olan Blackboard Pattern sistemini tanımlar. Sistem, tüm subagent'ların (konu uzmanları, soru üretim pipeline, profil analiz, içerik öneri) birbirleriyle WebSocket + Redis pub/sub üzerinden real-time iletişim kurmasını sağlar. Bu yaklaşım agent koordinasyonunu %400 iyileştirir ve response time'ı %60 azaltır.

## Glossary

- **Blackboard Pattern**: Merkezi bilgi paylaşım ve koordinasyon deseni
- **Message Bus**: Agent'lar arası mesaj iletim sistemi
- **WebSocket**: Real-time çift yönlü iletişim protokolü
- **Redis Pub/Sub**: Publish/Subscribe mesajlaşma modeli
- **Agent Handoff**: Bir agent'tan diğerine görev aktarımı
- **Context Sharing**: Agent'lar arası context paylaşımı
- **Event-Driven Architecture**: Olay tabanlı mimari
- **Orchestrator**: Agent koordinatörü

## Requirements

### Requirement 1: Redis Pub/Sub Message Bus

**User Story:** As a sistem yöneticisi, I want agent'ların Redis üzerinden mesajlaşmasını, so that loosely coupled ve scalable sistem olsun.

#### Acceptance Criteria

1. **REQ-1.1** WHEN agent mesaj gönderdiğinde, THE Message Bus SHALL Redis PUBLISH komutu kullanır
2. **REQ-1.2** WHEN agent mesaj dinlediğinde, THE Bus SHALL Redis SUBSCRIBE ile channel'a abone olur
3. **REQ-1.3** WHEN mesaj formatı belirlendiğinde, THE Bus SHALL JSON schema validation uygular
4. **REQ-1.4** WHEN channel naming yapıldığında, THE Bus SHALL namespace pattern kullanır (kiro2:agents:{agent_type}:{action})
5. **REQ-1.5** WHEN message persistence gerektiğinde, THE Bus SHALL Redis Streams kullanır
6. **REQ-1.6** WHEN message TTL belirlendiğinde, THE Bus SHALL mesaj tipine göre farklı TTL uygular (task: 1 saat, event: 5 dakika)

---

### Requirement 2: WebSocket Real-Time Communication

**User Story:** As a öğrenci, I want agent yanıtlarını real-time görmek, so that bekleme süresi olmadan etkileşim kurayım.

#### Acceptance Criteria

1. **REQ-2.1** WHEN öğrenci bağlandığında, THE WebSocket Server SHALL FastAPI WebSocket endpoint kullanır
2. **REQ-2.2** WHEN connection kurulduğunda, THE Server SHALL authentication token doğrular
3. **REQ-2.3** WHEN agent yanıt ürettiğinde, THE Server SHALL streaming response gönderir
4. **REQ-2.4** WHEN connection koptuğunda, THE Server SHALL automatic reconnection destekler
5. **REQ-2.5** WHEN heartbeat gönderildiğinde, THE Server SHALL 30 saniyede bir ping/pong yapar
6. **REQ-2.6** WHEN concurrent connections yönetildiğinde, THE Server SHALL kullanıcı başına maksimum 3 connection sınırı uygular

---

### Requirement 3: Agent Registration ve Discovery

**User Story:** As a agent developer, I want yeni agent'ların otomatik keşfedilmesini, so that manuel registration yapmayayım.

#### Acceptance Criteria

1. **REQ-3.1** WHEN agent başlatıldığında, THE Registry SHALL agent metadata'yı Redis'e kaydeder
2. **REQ-3.2** WHEN metadata kaydedildiğinde, THE Registry SHALL agent_id, type, capabilities, status, ve health_check_url saklar
3. **REQ-3.3** WHEN agent discovery yapıldığında, THE Registry SHALL tüm aktif agent'ları listeler
4. **REQ-3.4** WHEN agent capability sorgulandığında, THE Registry SHALL hangi agent'ın hangi görevi yapabileceğini döner
5. **REQ-3.5** WHEN agent health check yapıldığında, THE Registry SHALL her 30 saniyede agent'lara ping atar
6. **REQ-3.6** WHEN agent unhealthy olduğunda, THE Registry SHALL agent'ı deregister eder ve yedek agent atar

---

### Requirement 4: Task Orchestration ve Routing

**User Story:** As a orchestrator, I want görevleri doğru agent'lara yönlendirmek, so that optimal performans elde edeyim.

#### Acceptance Criteria

1. **REQ-4.1** WHEN yeni task geldiğinde, THE Orchestrator SHALL task tipini analiz eder
2. **REQ-4.2** WHEN agent seçimi yapıldığında, THE Orchestrator SHALL capability matching ve load balancing uygular
3. **REQ-4.3** WHEN multi-agent task olduğunda, THE Orchestrator SHALL task'ı sub-task'lara böler
4. **REQ-4.4** WHEN task routing yapıldığında, THE Orchestrator SHALL priority queue kullanır (high, medium, low)
5. **REQ-4.5** WHEN agent busy olduğunda, THE Orchestrator SHALL task'ı queue'ya alır veya alternatif agent seçer
6. **REQ-4.6** WHEN task timeout olduğunda, THE Orchestrator SHALL task'ı retry eder veya fallback agent'a yönlendirir

---

### Requirement 5: Context Sharing ve State Management

**User Story:** As a agent, I want diğer agent'ların context'ine erişmek, so that tutarlı yanıt verebiliyim.

#### Acceptance Criteria

1. **REQ-5.1** WHEN agent context paylaşmak istediğinde, THE Context Manager SHALL shared context'i Redis Hash'te saklar
2. **REQ-5.2** WHEN context key oluşturulduğunda, THE Manager SHALL session_id:agent_id:context_type formatı kullanır
3. **REQ-5.3** WHEN context read edildiğinde, THE Manager SHALL read-through caching uygular
4. **REQ-5.4** WHEN context update edildiğinde, THE Manager SHALL versioning ve conflict resolution destekler
5. **REQ-5.5** WHEN context expire olduğunda, THE Manager SHALL TTL sonrası otomatik temizlik yapar
6. **REQ-5.6** WHEN context size büyük olduğunda, THE Manager SHALL compression (gzip) uygular

---

### Requirement 6: Event-Driven Workflow Coordination

**User Story:** As a sistem yöneticisi, I want agent'ların event-driven çalışmasını, so that reactive ve scalable sistem olsun.

#### Acceptance Criteria

1. **REQ-6.1** WHEN event publish edildiğinde, THE Event Bus SHALL event type, payload, timestamp, ve source agent kaydeder
2. **REQ-6.2** WHEN agent event'e subscribe olduğunda, THE Bus SHALL pattern matching destekler (örn: "question.*" tüm question event'lerini yakalar)
3. **REQ-6.3** WHEN event handler çalıştığında, THE Bus SHALL async execution sağlar
4. **REQ-6.4** WHEN event chain oluştuğunda, THE Bus SHALL event causality tracking yapar
5. **REQ-6.5** WHEN event replay gerektiğinde, THE Bus SHALL event sourcing pattern destekler
6. **REQ-6.6** WHEN dead letter queue gerektiğinde, THE Bus SHALL başarısız event'leri DLQ'ya taşır

---

### Requirement 7: Agent Handoff ve Delegation

**User Story:** As a agent, I want görevi başka agent'a devredebilmek, so that uzmanlık alanıma odaklanayım.

#### Acceptance Criteria

1. **REQ-7.1** WHEN agent handoff başlattığında, THE Handoff Manager SHALL target agent'ı capability'ye göre seçer
2. **REQ-7.2** WHEN context transfer edildiğinde, THE Manager SHALL sadece gerekli context'i transfer eder (full context değil)
3. **REQ-7.3** WHEN handoff tamamlandığında, THE Manager SHALL source agent'a acknowledgment gönderir
4. **REQ-7.4** WHEN handoff başarısız olduğunda, THE Manager SHALL source agent'a geri döner
5. **REQ-7.5** WHEN handoff chain oluştuğunda, THE Manager SHALL maksimum 5 handoff sınırı uygular (infinite loop önleme)
6. **REQ-7.6** WHEN handoff metrics toplandığında, THE Manager SHALL handoff success rate ve latency ölçer

---

### Requirement 8: Monitoring, Logging ve Debugging

**User Story:** As a DevOps engineer, I want agent iletişimini izlemek, so that sorunları hızlıca tespit edeyim.

#### Acceptance Criteria

1. **REQ-8.1** WHEN mesaj gönderildiğinde, THE Monitor SHALL message_id, timestamp, source, target, ve payload_size loglar
2. **REQ-8.2** WHEN latency ölçüldüğünde, THE Monitor SHALL end-to-end message latency hesaplar
3. **REQ-8.3** WHEN throughput ölçüldüğünde, THE Monitor SHALL saniye başına mesaj sayısını hesaplar
4. **REQ-8.4** WHEN error rate hesaplandığında, THE Monitor SHALL başarısız mesaj / toplam mesaj oranını hesaplar
5. **REQ-8.5** WHEN distributed tracing yapıldığında, THE Monitor SHALL correlation_id ile mesaj chain'ini takip eder
6. **REQ-8.6** WHEN debug mode aktif olduğunda, THE Monitor SHALL tüm mesaj payload'larını detaylı loglar

---

## Bağımlılıklar

- **Redis**: Pub/Sub message bus ve state management
- **FastAPI WebSocket**: Real-time communication
- **Pydantic**: Message schema validation
- **asyncio**: Async message handling
- **aioredis**: Async Redis client
- **Prometheus**: Metrics collection
- **Jaeger**: Distributed tracing

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 2 hafta
**Beklenen Koordinasyon İyileşmesi:** %400

## Blackboard Coordination Flow

```
1. Öğrenci Sorusu / Task Başlatma
   ↓
2. WebSocket Connection
   ├─ Authentication
   ├─ Session Creation
   └─ Channel Subscription
   ↓
3. Task Orchestration
   ├─ Task Analysis
   ├─ Agent Selection (Capability Matching)
   └─ Task Routing (Priority Queue)
   ↓
4. Agent Registration & Discovery
   ├─ Active Agents Query
   ├─ Health Check
   └─ Load Balancing
   ↓
5. Multi-Agent Execution
   ├─ MatematikAgent → Redis Pub: "question.math.solve"
   ├─ Context Sharing → Redis Hash: session:123:context
   ├─ Agent Handoff → FizikAgent (if needed)
   └─ Event-Driven Workflow
   ↓
6. Message Bus Communication
   ├─ Redis PUBLISH (kiro2:agents:matematik:response)
   ├─ Redis SUBSCRIBE (kiro2:agents:orchestrator:*)
   └─ Message Validation (JSON Schema)
   ↓
7. Real-Time Response Streaming
   ├─ WebSocket Send (Partial Response)
   ├─ Progress Updates
   └─ Final Response
   ↓
8. Monitoring & Logging
   ├─ Message Latency: < 50ms
   ├─ Throughput: 1000 msg/sec
   ├─ Error Rate: < %1
   └─ Distributed Tracing (Correlation ID)
   ↓
9. Context Cleanup
   ├─ Session Context TTL Expire
   ├─ Message History Archival
   └─ Connection Close
```

## Success Metrics

1. **Message Latency:** < 50ms (P95)
2. **Throughput:** >= 1000 messages/second
3. **Agent Coordination Success Rate:** >= %98
4. **WebSocket Connection Stability:** >= %99.5
5. **Context Sharing Overhead:** < 10ms

## Message Schema Example

```json
{
  "message_id": "msg_abc123",
  "correlation_id": "corr_xyz789",
  "timestamp": "2026-01-14T10:30:00Z",
  "source_agent": "MatematikAgent",
  "target_agent": "Orchestrator",
  "event_type": "question.math.solved",
  "priority": "high",
  "payload": {
    "question_id": "q_12345",
    "solution": "...",
    "confidence": 0.95
  },
  "context": {
    "session_id": "sess_456",
    "user_id": "user_789"
  }
}
```

