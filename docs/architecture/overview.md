# Architecture Overview

This document provides a comprehensive overview of Kiro2's system architecture.

---

## 🏗️ System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Application<br/>React/Next.js]
        MOBILE[Mobile App<br/>React Native]
        ADMIN[Admin Panel<br/>React]
    end

    subgraph "API Gateway Layer"
        LB[Load Balancer<br/>Nginx]
        RATELIMIT[Rate Limiter<br/>Redis]
        AUTH[Auth Middleware<br/>JWT]
    end

    subgraph "Application Layer"
        API[FastAPI Backend<br/>Python 3.11]
        AGENTS[AI Agents<br/>Multi-Agent System]
        WORKERS[Background Workers<br/>Celery]
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL<br/>Primary DB)]
        REDIS[(Redis<br/>Cache/Queue)]
        ES[(Elasticsearch<br/>Search)]
        S3[(S3<br/>File Storage)]
    end

    subgraph "AI/ML Layer"
        GPT4[GPT-4<br/>OpenAI]
        BERTURK[BERTurk<br/>NLP]
        FSRS[FSRS Engine<br/>Spaced Repetition]
        IRT[IRT Model<br/>Ability Estimation]
    end

    subgraph "External Services"
        EBA[EBA API]
        KHAN[Khan Academy]
        YOUTUBE[YouTube API]
        ZEMBEREK[Zemberek NLP]
    end

    subgraph "Monitoring Layer"
        PROM[Prometheus]
        GRAFANA[Grafana]
        SENTRY[Sentry]
    end

    WEB --> LB
    MOBILE --> LB
    ADMIN --> LB

    LB --> RATELIMIT
    RATELIMIT --> AUTH
    AUTH --> API

    API --> AGENTS
    API --> WORKERS
    API --> POSTGRES
    API --> REDIS
    API --> ES
    API --> S3

    AGENTS --> GPT4
    AGENTS --> BERTURK
    AGENTS --> FSRS
    AGENTS --> IRT

    API --> EBA
    API --> KHAN
    API --> YOUTUBE
    API --> ZEMBEREK

    API --> PROM
    PROM --> GRAFANA
    API --> SENTRY
```

---

## 📊 Component Architecture

### Backend Components

```mermaid
graph LR
    subgraph "Core Layer"
        CONFIG[Configuration]
        DATABASE[Database]
        CACHE[Cache Manager]
        AUTH_CORE[Authentication]
        SECURITY[Security]
    end

    subgraph "API Layer"
        AUTH_API[Auth API]
        USER_API[User API]
        EXAM_API[Exam API]
        CONTENT_API[Content API]
        ANALYTICS_API[Analytics API]
    end

    subgraph "Service Layer"
        USER_SVC[User Service]
        EXAM_SVC[Exam Service]
        LEARNING_SVC[Learning Path Service]
        ANALYTICS_SVC[Analytics Service]
        AI_SVC[AI Service]
    end

    subgraph "Algorithm Layer"
        FSRS_ALG[FSRS Algorithm]
        IRT_ALG[IRT Algorithm]
        ZPD_ALG[ZPD Algorithm]
        CAT_ALG[CAT Algorithm]
    end

    subgraph "Model Layer"
        USER_MODEL[User Model]
        EXAM_MODEL[Exam Model]
        QUESTION_MODEL[Question Model]
        LEARNING_MODEL[Learning Model]
    end

    AUTH_API --> AUTH_CORE
    USER_API --> USER_SVC
    EXAM_API --> EXAM_SVC
    CONTENT_API --> AI_SVC
    ANALYTICS_API --> ANALYTICS_SVC

    USER_SVC --> USER_MODEL
    EXAM_SVC --> EXAM_MODEL
    LEARNING_SVC --> LEARNING_MODEL

    LEARNING_SVC --> FSRS_ALG
    EXAM_SVC --> IRT_ALG
    LEARNING_SVC --> ZPD_ALG
    EXAM_SVC --> CAT_ALG

    USER_SVC --> DATABASE
    EXAM_SVC --> DATABASE
    AI_SVC --> CACHE
```

---

## 🔄 Request Flow

### Authenticated API Request

```mermaid
sequenceDiagram
    participant Client
    participant LoadBalancer
    participant RateLimiter
    participant AuthMiddleware
    participant API
    participant Service
    participant Database
    participant Cache

    Client->>LoadBalancer: HTTPS Request
    LoadBalancer->>RateLimiter: Forward Request

    RateLimiter->>RateLimiter: Check Rate Limit
    alt Rate Limit Exceeded
        RateLimiter-->>Client: 429 Too Many Requests
    end

    RateLimiter->>AuthMiddleware: Continue
    AuthMiddleware->>AuthMiddleware: Verify JWT Token

    alt Invalid Token
        AuthMiddleware-->>Client: 401 Unauthorized
    end

    AuthMiddleware->>API: Authenticated Request
    API->>Cache: Check Cache

    alt Cache Hit
        Cache-->>API: Return Cached Data
        API-->>Client: 200 OK (from cache)
    else Cache Miss
        API->>Service: Process Request
        Service->>Database: Query Data
        Database-->>Service: Return Data
        Service->>Service: Apply Business Logic
        Service-->>API: Return Result
        API->>Cache: Store in Cache
        API-->>Client: 200 OK (from DB)
    end
```

---

## 🧠 AI Agent Architecture

### Multi-Agent System

```mermaid
graph TB
    subgraph "Blackboard System"
        BB[Blackboard<br/>Shared Knowledge Base]
    end

    subgraph "Agents"
        STUDY[Study Buddy Agent]
        LEARNING[Learning Path Agent]
        ACCESSIBILITY[Accessibility Agent]
        PRODUCTION[Production Ready Agent]
    end

    subgraph "AI Services"
        GPT[GPT-4 API]
        BERTURK[BERTurk]
        EMBED[Embeddings]
    end

    subgraph "Data Sources"
        STUDENT[Student Profile]
        PROGRESS[Learning Progress]
        QUESTIONS[Question Bank]
        CONTENT[Content Library]
    end

    STUDY --> BB
    LEARNING --> BB
    ACCESSIBILITY --> BB
    PRODUCTION --> BB

    BB --> GPT
    BB --> BERTURK
    BB --> EMBED

    STUDY --> STUDENT
    LEARNING --> PROGRESS
    STUDY --> QUESTIONS
    LEARNING --> CONTENT
```

### Agent Communication Flow

```mermaid
sequenceDiagram
    participant User
    participant StudyBuddy
    participant Blackboard
    participant LearningPath
    participant Database

    User->>StudyBuddy: Ask question
    StudyBuddy->>Blackboard: Post query
    Blackboard->>LearningPath: Notify relevant agent
    LearningPath->>Database: Get student context
    Database-->>LearningPath: Student data
    LearningPath->>Blackboard: Post recommendation
    Blackboard->>StudyBuddy: Get recommendation
    StudyBuddy->>StudyBuddy: Generate response
    StudyBuddy-->>User: Return answer + suggestions
```

---

## 💾 Database Architecture

### Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ EXAM : takes
    USER ||--o{ LEARNING_PATH : has
    USER ||--o{ CONSENT : gives
    USER ||--o{ AUDIT_LOG : generates

    EXAM ||--o{ EXAM_ANSWER : contains
    EXAM ||--|{ EXAM_TYPE : is

    QUESTION ||--o{ EXAM_ANSWER : answered_in
    QUESTION ||--|{ SUBJECT : belongs_to
    QUESTION ||--|| DIFFICULTY : has

    LEARNING_PATH ||--o{ LEARNING_ITEM : contains
    LEARNING_ITEM ||--|| QUESTION : references

    USER {
        uuid id PK
        string email UK
        string password_hash
        string name
        enum role
        boolean is_premium
        timestamp created_at
    }

    EXAM {
        uuid id PK
        uuid user_id FK
        enum exam_type
        integer duration
        timestamp started_at
        timestamp finished_at
        float score
    }

    QUESTION {
        uuid id PK
        string subject
        string content
        json options
        string correct_answer
        float irt_a
        float irt_b
        float irt_c
    }

    LEARNING_PATH {
        uuid id PK
        uuid user_id FK
        float theta
        json preferences
        timestamp updated_at
    }
```

### Database Sharding Strategy

```mermaid
graph TB
    subgraph "Application"
        APP[FastAPI App]
        SHARD_ROUTER[Shard Router]
    end

    subgraph "User Shards"
        SHARD1[(Shard 1<br/>Users A-H)]
        SHARD2[(Shard 2<br/>Users I-P)]
        SHARD3[(Shard 3<br/>Users Q-Z)]
    end

    subgraph "Content Shard"
        CONTENT_DB[(Content DB<br/>Questions/Exams)]
    end

    subgraph "Analytics Shard"
        ANALYTICS_DB[(Analytics DB<br/>Statistics/Reports)]
    end

    APP --> SHARD_ROUTER
    SHARD_ROUTER --> SHARD1
    SHARD_ROUTER --> SHARD2
    SHARD_ROUTER --> SHARD3
    APP --> CONTENT_DB
    APP --> ANALYTICS_DB
```

---

## 🚀 Deployment Architecture

### Container Architecture

```mermaid
graph TB
    subgraph "Docker Swarm / Kubernetes"
        subgraph "Frontend Services"
            WEB1[Web App 1]
            WEB2[Web App 2]
            WEB3[Web App 3]
        end

        subgraph "Backend Services"
            API1[API Server 1]
            API2[API Server 2]
            API3[API Server 3]
            API4[API Server 4]
        end

        subgraph "Worker Services"
            WORKER1[Worker 1]
            WORKER2[Worker 2]
        end

        subgraph "Data Services"
            PG_PRIMARY[(PostgreSQL Primary)]
            PG_REPLICA1[(PostgreSQL Replica 1)]
            PG_REPLICA2[(PostgreSQL Replica 2)]
            REDIS_CLUSTER[(Redis Cluster)]
        end
    end

    LB[Load Balancer]

    LB --> WEB1
    LB --> WEB2
    LB --> WEB3

    WEB1 --> API1
    WEB2 --> API2
    WEB3 --> API3

    API1 --> PG_PRIMARY
    API2 --> PG_REPLICA1
    API3 --> PG_REPLICA2
    API4 --> PG_PRIMARY

    API1 --> REDIS_CLUSTER
    API2 --> REDIS_CLUSTER
    API3 --> REDIS_CLUSTER

    WORKER1 --> REDIS_CLUSTER
    WORKER2 --> REDIS_CLUSTER
    WORKER1 --> PG_PRIMARY
    WORKER2 --> PG_PRIMARY
```

---

## 🔐 Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "Layer 1: Network Security"
        FIREWALL[Firewall]
        WAF[Web Application Firewall]
        DDOS[DDoS Protection]
    end

    subgraph "Layer 2: Application Security"
        TLS[TLS 1.3]
        CORS[CORS Policy]
        CSP[Content Security Policy]
    end

    subgraph "Layer 3: Authentication"
        JWT_AUTH[JWT Authentication]
        TFA[Two-Factor Auth]
        OAUTH[OAuth 2.0]
    end

    subgraph "Layer 4: Authorization"
        RBAC[Role-Based Access Control]
        PERMISSIONS[Permission System]
    end

    subgraph "Layer 5: Data Security"
        ENCRYPTION[Data Encryption]
        HASHING[Password Hashing]
        SENSITIVE[Sensitive Data Filter]
    end

    subgraph "Layer 6: Monitoring"
        AUDIT[Audit Logging]
        SENTRY_SEC[Sentry Error Tracking]
        SECURITY_SCAN[Security Scanning]
    end

    FIREWALL --> WAF
    WAF --> DDOS
    DDOS --> TLS
    TLS --> CORS
    CORS --> CSP
    CSP --> JWT_AUTH
    JWT_AUTH --> TFA
    TFA --> OAUTH
    OAUTH --> RBAC
    RBAC --> PERMISSIONS
    PERMISSIONS --> ENCRYPTION
    ENCRYPTION --> HASHING
    HASHING --> SENSITIVE
    SENSITIVE --> AUDIT
    AUDIT --> SENTRY_SEC
    SENTRY_SEC --> SECURITY_SCAN
```

---

## 📈 Scalability Strategy

### Horizontal Scaling

```mermaid
graph LR
    subgraph "Load Balancing"
        LB[Nginx Load Balancer]
    end

    subgraph "API Instances"
        API1[API Server 1]
        API2[API Server 2]
        API3[API Server 3]
        APIN[API Server N]
    end

    subgraph "Caching Layer"
        REDIS1[Redis Master]
        REDIS2[Redis Replica 1]
        REDIS3[Redis Replica 2]
    end

    subgraph "Database Layer"
        PG_M[(PG Master)]
        PG_R1[(PG Replica 1)]
        PG_R2[(PG Replica 2)]
    end

    LB --> API1
    LB --> API2
    LB --> API3
    LB -.-> APIN

    API1 --> REDIS1
    API2 --> REDIS2
    API3 --> REDIS3

    REDIS1 --> REDIS2
    REDIS1 --> REDIS3

    API1 --> PG_M
    API2 --> PG_R1
    API3 --> PG_R2

    PG_M -.replication.-> PG_R1
    PG_M -.replication.-> PG_R2
```

---

## 🔄 Cache Strategy

### Multi-Layer Caching

```mermaid
graph TB
    REQUEST[API Request]

    subgraph "L1: Application Cache"
        APP_CACHE[In-Memory Cache<br/>LRU Cache]
    end

    subgraph "L2: Redis Cache"
        REDIS_CACHE[Redis Cache<br/>Distributed]
    end

    subgraph "L3: Database"
        DB[(PostgreSQL)]
    end

    REQUEST --> APP_CACHE
    APP_CACHE -->|Cache Miss| REDIS_CACHE
    REDIS_CACHE -->|Cache Miss| DB
    DB -->|Store| REDIS_CACHE
    REDIS_CACHE -->|Store| APP_CACHE
    APP_CACHE -->|Return| REQUEST
```

### Cache Invalidation Strategy

```mermaid
graph LR
    subgraph "Write Operations"
        UPDATE[Update Data]
        DELETE[Delete Data]
        CREATE[Create Data]
    end

    subgraph "Cache Invalidation"
        INVALIDATE[Invalidate Cache]
        PATTERN_DELETE[Pattern-Based Delete]
        TAG_DELETE[Tag-Based Delete]
    end

    subgraph "Cache Warming"
        WARM[Warm Cache]
        PRELOAD[Preload Popular Data]
    end

    UPDATE --> INVALIDATE
    DELETE --> PATTERN_DELETE
    CREATE --> TAG_DELETE

    INVALIDATE --> WARM
    PATTERN_DELETE --> WARM
    TAG_DELETE --> PRELOAD
```

---

## 📊 Technology Stack

### Backend Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | FastAPI 0.104+ | High-performance async API |
| **ORM** | SQLAlchemy 2.0 | Database abstraction |
| **Validation** | Pydantic V2 | Data validation |
| **Database** | PostgreSQL 15+ | Primary data store |
| **Cache** | Redis 7+ | Distributed caching |
| **Search** | Elasticsearch 8+ | Full-text search |
| **Task Queue** | Celery | Background jobs |
| **Message Broker** | RabbitMQ | Async messaging |

### AI/ML Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | GPT-4 | Question generation, chat |
| **NLP** | BERTurk | Turkish language processing |
| **Morphology** | Zemberek | Turkish morphological analysis |
| **Embeddings** | OpenAI Ada-002 | Semantic search |
| **Framework** | PyTorch | Custom ML models |

### DevOps Stack

| Tool | Purpose |
|------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Local development |
| **GitHub Actions** | CI/CD pipeline |
| **Prometheus** | Metrics collection |
| **Grafana** | Metrics visualization |
| **Sentry** | Error tracking |
| **ELK Stack** | Log aggregation |

---

## 🎯 Design Principles

### 1. **Scalability**
- Horizontal scaling for API servers
- Database read replicas
- Redis clustering
- CDN for static assets

### 2. **Reliability**
- Circuit breakers for external services
- Retry logic with exponential backoff
- Graceful degradation
- Health checks

### 3. **Performance**
- Multi-layer caching
- Database query optimization
- Lazy loading
- Async processing

### 4. **Security**
- Defense in depth
- Least privilege principle
- Input validation
- KVKK compliance

### 5. **Maintainability**
- Clean architecture
- SOLID principles
- Comprehensive testing
- Documentation

---

## 📖 Related Documentation

- [System Design](system-design.md) - Detailed design decisions
- [Database Schema](database-schema.md) - Complete schema documentation
- [API Design](api-design.md) - API design principles
- [Security Architecture](security.md) - Security implementation details
- [Performance](performance.md) - Performance optimization techniques

---

**Last Updated**: 2025-11-12 | **Sprint**: 9 - Documentation
