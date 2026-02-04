# Video Recommendation System - Architecture Diagrams

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[React Application]
        B[VideoLoadingManager]
        C[NetworkStatusManager]
        D[VideoErrorHandler]
        E[OfflineModeManager]
    end
    
    subgraph "API Gateway"
        F[FastAPI Application]
        G[CORS Middleware]
        H[Rate Limiter]
        I[Circuit Breaker]
    end
    
    subgraph "Service Layer"
        J[VideoRecommendationService]
        K[TurkishContentFilter]
        L[HealthCheckService]
        M[AdvancedYouTubeSearch]
        N[SemanticYouTubeSearch]
    end
    
    subgraph "Data Layer"
        O[(SQLite Database)]
        P[(Redis Cache)]
        Q[YouTube Data API v3]
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    
    B --> F
    F --> G
    G --> H
    H --> I
    
    I --> J
    J --> K
    J --> M
    J --> N
    J --> L
    
    J --> O
    J --> P
    M --> Q
    N --> Q
    L --> O
    L --> P
    L --> Q
    
    style A fill:#e1f5ff
    style F fill:#fff4e1
    style J fill:#e8f5e9
    style O fill:#fce4ec
    style P fill:#fce4ec
    style Q fill:#fce4ec
```

## Request Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API Gateway
    participant S as VideoRecommendationService
    participant C as Cache (Redis)
    participant D as Database
    participant Y as YouTube API
    participant T as TurkishContentFilter
    
    U->>F: Open Learning Path
    F->>F: Initialize VideoLoadingManager
    F->>U: Show loading indicator
    
    F->>A: POST /api/youtube/recommendations
    A->>A: Validate request
    A->>A: Check rate limit
    A->>S: Get recommendations
    
    S->>C: Check cache (Layer 1: Memory)
    alt Cache Hit (Memory)
        C-->>S: Return cached data
        S-->>A: Return recommendations
    else Cache Miss (Memory)
        S->>C: Check cache (Layer 2: Redis)
        alt Cache Hit (Redis)
            C-->>S: Return cached data
            S->>C: Promote to memory cache
            S-->>A: Return recommendations
        else Cache Miss (Redis)
            S->>D: Check database cache
            alt Cache Hit (Database)
                D-->>S: Return cached data
                S->>C: Write to Redis
                S-->>A: Return recommendations
            else Cache Miss (Database)
                par Parallel Video Discovery
                    S->>Y: Search videos (Goal 1)
                    S->>Y: Search videos (Goal 2)
                    S->>Y: Search videos (Goal 3)
                end
                Y-->>S: Return video results
                S->>T: Filter Turkish content
                T-->>S: Return filtered videos
                S->>D: Cache in database
                S->>C: Cache in Redis
                S-->>A: Return recommendations
            end
        end
    end
    
    A-->>F: Return response
    F->>F: Update UI
    F->>U: Display videos
```

## Cache Architecture Diagram

```mermaid
graph LR
    subgraph "Cache Layers"
        A[Request] --> B{Layer 1: Memory Cache}
        B -->|Hit 40%| C[Return <10ms]
        B -->|Miss 60%| D{Layer 2: Redis Cache}
        D -->|Hit 40%| E[Return <100ms]
        D -->|Miss 60%| F{Layer 3: Database Cache}
        F -->|Hit 15%| G[Return <500ms]
        F -->|Miss 5%| H[YouTube API]
        H --> I[Return 2-5s]
    end
    
    I --> J[Write to all layers]
    G --> K[Promote to Redis]
    E --> L[Promote to Memory]
    
    style B fill:#e8f5e9
    style D fill:#fff3e0
    style F fill:#fce4ec
    style H fill:#ffebee
```

## Turkish Content Filtering Flow

```mermaid
flowchart TD
    A[Video Input] --> B[Language Detection]
    B --> C{Multi-Signal Check}
    
    C --> D[Title Language]
    C --> E[Description Language]
    C --> F[Turkish Characters]
    C --> G[Trusted Channel]
    
    D --> H{Language Score}
    E --> H
    F --> H
    G --> H
    
    H -->|Score >= 0.8| I[Relevance Scoring]
    H -->|Score < 0.8| Z[Reject]
    
    I --> J[MEB Curriculum Match]
    J --> K[Subject Keywords]
    J --> L[Sub-topic Keywords]
    
    K --> M{Relevance Score}
    L --> M
    
    M -->|Score >= 0.7| N[Difficulty Matching]
    M -->|Score < 0.7| Z
    
    N --> O[Student Level]
    N --> P[Video Difficulty]
    
    O --> Q{Difficulty Match}
    P --> Q
    
    Q -->|Match >= 0.5| R[Calculate Overall Score]
    Q -->|Match < 0.5| Z
    
    R --> S{Overall Score}
    S -->|Score >= 0.7| T[Accept Video]
    S -->|Score < 0.7| Z
    
    style T fill:#e8f5e9
    style Z fill:#ffebee
```

## Circuit Breaker State Machine

```mermaid
stateDiagram-v2
    [*] --> CLOSED: Initial State
    
    CLOSED --> OPEN: 5 Failures
    OPEN --> HALF_OPEN: 60s Timeout
    HALF_OPEN --> CLOSED: 2 Successes
    HALF_OPEN --> OPEN: 1 Failure
    
    note right of CLOSED
        Normal operation
        Requests pass through
        Track failures
    end note
    
    note right of OPEN
        Service failing
        Reject requests immediately
        Return cached data
    end note
    
    note right of HALF_OPEN
        Testing recovery
        Allow limited requests
        Monitor success rate
    end note
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx Load Balancer]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "Backend Pods"
            B1[Backend Pod 1]
            B2[Backend Pod 2]
            B3[Backend Pod 3]
        end
        
        subgraph "Data Services"
            R[Redis Service]
            D[Database Service]
        end
        
        subgraph "Monitoring"
            P[Prometheus]
            G[Grafana]
        end
    end
    
    subgraph "External Services"
        Y[YouTube Data API]
    end
    
    LB --> B1
    LB --> B2
    LB --> B3
    
    B1 --> R
    B2 --> R
    B3 --> R
    
    B1 --> D
    B2 --> D
    B3 --> D
    
    B1 --> Y
    B2 --> Y
    B3 --> Y
    
    B1 --> P
    B2 --> P
    B3 --> P
    
    P --> G
    
    style LB fill:#e1f5ff
    style B1 fill:#e8f5e9
    style B2 fill:#e8f5e9
    style B3 fill:#e8f5e9
    style R fill:#fff3e0
    style D fill:#fff3e0
    style Y fill:#fce4ec
```

## Error Handling Flow

```mermaid
flowchart TD
    A[Request] --> B{Try Execute}
    
    B -->|Success| C[Return Response]
    B -->|Error| D{Error Type}
    
    D -->|Timeout| E[Log Error]
    D -->|Network| E
    D -->|Server Error| E
    D -->|Cache Error| E
    
    E --> F{Retryable?}
    
    F -->|Yes| G{Retry Count < 2?}
    F -->|No| H[Return Error Response]
    
    G -->|Yes| I[Exponential Backoff]
    G -->|No| J{Fallback Available?}
    
    I --> K[Wait]
    K --> B
    
    J -->|Yes| L[Return Cached Data]
    J -->|No| H
    
    L --> M[Show Degraded Service Message]
    H --> N[Show Error Message]
    
    style C fill:#e8f5e9
    style L fill:#fff3e0
    style H fill:#ffebee
    style N fill:#ffebee
```

## Monitoring Architecture

```mermaid
graph TB
    subgraph "Application"
        A[FastAPI App]
        B[Structured Logger]
        C[Metrics Collector]
    end
    
    subgraph "Metrics Pipeline"
        D[Prometheus]
        E[Grafana]
    end
    
    subgraph "Logging Pipeline"
        F[Log Files]
        G[Elasticsearch]
        H[Kibana]
    end
    
    subgraph "Alerting"
        I[Alert Manager]
        J[Slack]
        K[PagerDuty]
    end
    
    A --> B
    A --> C
    
    B --> F
    F --> G
    G --> H
    
    C --> D
    D --> E
    D --> I
    
    I --> J
    I --> K
    
    style A fill:#e1f5ff
    style D fill:#e8f5e9
    style E fill:#e8f5e9
    style G fill:#fff3e0
    style H fill:#fff3e0
    style I fill:#fce4ec
```

## Data Model Diagram

```mermaid
erDiagram
    VIDEO_CACHE ||--o{ VIDEO_METADATA : contains
    VIDEO_CACHE {
        int id PK
        string video_id
        string subject
        string difficulty
        string exam_type
        string language
        float quality_score
        float relevance_score
        float language_score
        float difficulty_match
        float overall_score
        json metadata
        timestamp created_at
        timestamp last_updated
    }
    
    VIDEO_METADATA {
        string video_id
        string title
        string channel
        string channel_id
        string duration
        int view_count
        string upload_date
        string thumbnail
        string url
    }
    
    STUDENT_PROFILE ||--o{ RECOMMENDATION : generates
    STUDENT_PROFILE {
        array goals
        object currentLevel
        string learningStyle
        object preferences
    }
    
    RECOMMENDATION {
        string subject_exam
        array videos
        int total_count
        bool cache_hit
        int response_time_ms
        string request_id
    }
```

## Security Architecture

```mermaid
graph TB
    subgraph "Client"
        A[Browser/Mobile App]
    end
    
    subgraph "Security Layers"
        B[HTTPS/TLS]
        C[CORS Policy]
        D[Rate Limiter]
        E[Input Validation]
        F[API Key Validation]
    end
    
    subgraph "Application"
        G[FastAPI App]
    end
    
    subgraph "Data Protection"
        H[Encrypted Storage]
        I[Secure Connections]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    
    G --> H
    G --> I
    
    style B fill:#e8f5e9
    style C fill:#e8f5e9
    style D fill:#e8f5e9
    style E fill:#e8f5e9
    style F fill:#e8f5e9
```

## Startup Sequence Diagram

```mermaid
sequenceDiagram
    participant M as Main Application
    participant C as Configuration
    participant L as Logger
    participant H as HealthCheckService
    participant D as Database
    participant R as Redis
    participant Y as YouTube API
    participant S as Services
    participant A as API Routes
    
    M->>C: Load environment variables
    C-->>M: Configuration loaded
    
    M->>L: Initialize structured logging
    L-->>M: Logger ready
    
    M->>H: Create HealthCheckService
    
    H->>D: Check database connectivity
    alt Database Healthy
        D-->>H: Connection OK
        H->>L: Log INFO
    else Database Unhealthy
        D-->>H: Connection Failed
        H->>L: Log WARNING
    end
    
    H->>R: Check Redis connectivity
    alt Redis Healthy
        R-->>H: Connection OK
        H->>L: Log INFO
    else Redis Unhealthy
        R-->>H: Connection Failed
        H->>L: Log WARNING
    end
    
    H->>Y: Check YouTube API
    alt YouTube API Healthy
        Y-->>H: API OK
        H->>L: Log INFO
    else YouTube API Unhealthy
        Y-->>H: API Failed
        H->>L: Log WARNING
    end
    
    H-->>M: Startup health check complete
    
    M->>S: Initialize services
    S-->>M: Services ready
    
    M->>A: Register API routes
    A-->>M: Routes registered
    
    M->>M: Start metrics collection
    
    M->>L: Log startup summary
    
    Note over M: Application Ready
```

## Legend

### Colors
- 🔵 Blue: Frontend/Client Layer
- 🟡 Yellow: API/Gateway Layer
- 🟢 Green: Service/Business Logic Layer
- 🔴 Red: Data/External Services Layer
- 🟣 Purple: Monitoring/Alerting Layer

### Symbols
- Rectangle: Component/Service
- Cylinder: Database/Storage
- Diamond: Decision Point
- Circle: Start/End Point
- Arrow: Data Flow/Dependency

## Diagram Tools

Bu diyagramlar Mermaid syntax kullanılarak oluşturulmuştur. Görüntülemek için:

1. **GitHub/GitLab:** Otomatik render edilir
2. **VS Code:** Mermaid Preview extension
3. **Online:** https://mermaid.live/
4. **Documentation:** https://mermaid.js.org/

## Updating Diagrams

Diyagramları güncellemek için:

1. Mermaid syntax'ı düzenle
2. Online editor'da test et
3. Commit ve push yap
4. Documentation'da otomatik render edilir

## Additional Resources

- [Mermaid Documentation](https://mermaid.js.org/)
- [Architecture Decision Records](./ADR/)
- [API Documentation](./VIDEO_API.md)
- [System Design Document](./ARCHITECTURE.md)
