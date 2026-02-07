# KIRO2 Platform - Bileşen Mimarisi ve İlişkiler

**Teknofest 2025 - Eğitim Eylemcisi Kategorisi**
**Platform:** Türkiye Üniversite Sınavları Hazırlık Platformu
**Tarih:** 17 Kasım 2025

---

## İçindekiler

1. [Genel Mimari Bakış](#1-genel-mimari-bakış)
2. [10 Ana Bileşen Katmanı](#2-10-ana-bileşen-katmanı)
3. [Bileşen İlişki Matrisi](#3-bileşen-i̇lişki-matrisi)
4. [Veri Akış Diyagramları](#4-veri-akış-diyagramları)
5. [Bileşen Sorumlulukları](#5-bileşen-sorumlulukları)
6. [Kritik Bağımlılıklar](#6-kritik-bağımlılıklar)

---

## 1. GENEL MİMARİ BAKIŞ

### 1.1 Mimari Prensipler

KIRO2 platformu, aşağıdaki mimari prensiplere göre tasarlanmıştır:

1. **Katmanlı Mimari (Layered Architecture)**
   - Her katman sadece altındaki katmanla iletişim kurar
   - Bağımlılıklar tek yönlüdür (yukarıdan aşağıya)
   - Separation of Concerns prensibi

2. **Mikroservis Hazır (Microservice-Ready)**
   - Gevşek bağlı (loosely coupled) bileşenler
   - Her servis kendi sorumluluğuna odaklanır
   - API-first tasarım

3. **Event-Driven Communication**
   - Asenkron işlem desteği
   - Message queue kullanımı (Celery + Redis)
   - WebSocket desteği (opsiyonel)

4. **Domain-Driven Design (DDD)**
   - Business logic services katmanında
   - Rich domain models
   - Repository pattern

5. **12-Factor App Metodolojisi**
   - Configuration externalization
   - Stateless processes
   - Log streaming
   - Dev/prod parity

### 1.2 Genel Mimari Diyagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                          │
│                    (Browser / Mobile App)                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     1. FRONTEND LAYER                            │
│  React 18 + TypeScript + Vite + Material-UI + Zustand          │
│  Components │ Services │ Hooks │ Store │ Types                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ REST API (JSON)
                          │ WebSocket (optional)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     2. API GATEWAY LAYER                         │
│  FastAPI Routers (100+ endpoints)                               │
│  Authentication │ Rate Limiting │ Input Validation             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 3. BUSINESS  │ │  4. CORE     │ │  5. AI/ML    │
│ LOGIC LAYER  │ │ INFRA LAYER  │ │    LAYER     │
│              │ │              │ │              │
│ 80+ Services │ │ Database     │ │ LLM Service  │
│ Domain Logic │ │ Cache        │ │ BERTurk      │
│ Workflows    │ │ Security     │ │ Multi-Agent  │
│              │ │ Monitoring   │ │ IRT/FSRS     │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   6. ALGORITHM LAYER                             │
│  Turkish NLP │ Adaptive Learning │ Personalization             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   7. DATABASE LAYER                              │
│  PostgreSQL 15 (40+ models) │ SQLAlchemy │ Alembic             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 8. EXTERNAL  │ │  9. MONITOR  │ │10.INFRASTRUC │
│   SERVICES   │ │     LAYER    │ │  TURE LAYER  │
│              │ │              │ │              │
│ OpenAI       │ │ Prometheus   │ │ Docker       │
│ YouTube      │ │ Grafana      │ │ Redis        │
│ EBA TV       │ │ Jaeger       │ │ Nginx        │
│ Khan Academy │ │ Sentry       │ │ Kubernetes   │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 2. 10 ANA BİLEŞEN KATMANI

### 2.1 Frontend Layer (Katman 1)

**Teknolojiler:**
- React 18.2.0 (UI framework)
- TypeScript 5.3.0 (type safety)
- Vite 7.1.6 (build tool)
- Material-UI 5.14.0 (component library)
- Zustand 4.5.7 (state management)
- React Router 6.30.1 (routing)
- Axios 1.6.0 (HTTP client)

**Alt Bileşenler:**

#### 2.1.1 Components (UI Katmanı)
- **Dosya Konumu:** `frontend/src/components/`
- **Sayı:** 100+ React component
- **Sorumluluk:** Kullanıcı arayüzü render etme
- **Özellikler:**
  - Presentational components
  - Container components
  - HOC (Higher-Order Components)
  - Compound components

**Örnek Componentler:**
```
components/
├── Auth/              # Kimlik doğrulama UI
├── Dashboard/         # Dashboard componentleri
├── Exam/              # Sınav arayüzü
├── LearningPath/      # Öğrenme yolu
├── Accessibility/     # Erişilebilirlik özellikleri
├── Common/            # Paylaşılan componentler
└── ui/                # Temel UI primitives
```

#### 2.1.2 Services (API İletişim Katmanı)
- **Dosya Konumu:** `frontend/src/services/`
- **Sayı:** 30+ service modülleri
- **Sorumluluk:** Backend API ile iletişim
- **Özellikler:**
  - HTTP client wrapper (Axios)
  - Request/response interceptors
  - Error handling
  - Type-safe API calls

**Örnek Services:**
```typescript
// authService.ts
export const authService = {
  login: (credentials) => apiClient.post('/api/auth/login', credentials),
  register: (userData) => apiClient.post('/api/auth/register', userData),
  logout: () => apiClient.post('/api/auth/logout'),
  refreshToken: () => apiClient.post('/api/auth/refresh'),
};

// examService.ts
export const examService = {
  startExam: (examId) => apiClient.post(`/api/sinav/start/${examId}`),
  submitAnswer: (answerId, answer) => apiClient.post(`/api/sinav/answer/${answerId}`, answer),
  finishExam: (examId) => apiClient.post(`/api/sinav/finish/${examId}`),
};
```

#### 2.1.3 Hooks (Custom React Hooks)
- **Dosya Konumu:** `frontend/src/hooks/`
- **Sayı:** 40+ custom hooks
- **Sorumluluk:** Reusable logic extraction
- **Özellikler:**
  - State management hooks
  - Effect hooks
  - Ref hooks
  - Performance hooks

**Örnek Hooks:**
```typescript
// useAuth.ts
export const useAuth = () => {
  const { user, token } = useAuthStore();
  const login = async (credentials) => { /*...*/ };
  const logout = async () => { /*...*/ };
  return { user, token, login, logout, isAuthenticated: !!token };
};

// useExamTimer.ts
export const useExamTimer = (durationMinutes) => {
  const [timeLeft, setTimeLeft] = useState(durationMinutes * 60);
  // Timer logic...
  return { timeLeft, isExpired, pause, resume };
};
```

#### 2.1.4 Store (State Management)
- **Dosya Konumu:** `frontend/src/store/`
- **Sayı:** 5 Zustand stores
- **Sorumluluk:** Global state yönetimi
- **Özellikler:**
  - Zustand (lightweight state management)
  - Persistence (localStorage)
  - DevTools integration

**Stores:**
```typescript
// authStore.ts
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
}

// examStore.ts
interface ExamState {
  currentExam: Exam | null;
  answers: Answer[];
  timeLeft: number;
  submitAnswer: (answerId: string, answer: string) => void;
}
```

#### 2.1.5 Types (TypeScript Definitions)
- **Dosya Konumu:** `frontend/src/types/`
- **Önemli Dosyalar:**
  - `index.ts` - Core types
  - `api.generated.ts` - Auto-generated API types (41,701 satır!)
  - `revolutionary.ts` - Revolutionary feature types

**Type Safety Akışı:**
```
Backend Pydantic Models
  ↓
OpenAPI Schema (openapi.json)
  ↓
openapi-typescript generator
  ↓
frontend/src/types/api.generated.ts
  ↓
Frontend Services & Components
```

---

### 2.2 API Gateway Layer (Katman 2)

**Teknolojiler:**
- FastAPI 0.104.1
- Pydantic 2.5.0 (validation)
- Uvicorn 0.24.0 (ASGI server)

**Sorumluluk:** HTTP istekleri alma, routing, authentication, validation

**Alt Bileşenler:**

#### 2.2.1 Authentication & Security Routers
```
api/auth.py                    # Login, register, password reset
api/two_factor_auth_api.py     # 2FA with TOTP
api/api_key_api.py             # API key management
api/audit_api.py               # Audit trails
```

#### 2.2.2 Exam & Assessment Routers
```
api/sinav.py                   # Exam engine
api/exam_performance.py        # Performance analysis
api/adaptive_testing.py        # Adaptive difficulty
api/exam_answer_tracking.py    # Answer tracking
```

#### 2.2.3 Learning & Education Routers
```
api/learning_path.py           # Learning path generation
api/learning_style.py          # Learning style detection
api/zpd_maarif.py              # ZPD + Turkish education
api/irt_morfoloji.py           # IRT + morphology
api/fsrs.py                    # Spaced repetition
```

#### 2.2.4 Question Bank Routers
```
api/soru_bankasi.py            # Question bank
api/question_crud_api.py       # CRUD operations
api/questions_api.py           # Question API
api/question_generation.py     # AI generation
```

#### 2.2.5 Content & Resources Routers
```
api/ebatv.py                   # EBA TV integration
api/khan_routes.py             # Khan Academy
api/youtube_routes.py          # YouTube videos
api/rag.py                     # RAG system
```

#### 2.2.6 AI & Chat Routers
```
api/enhanced_chat.py           # Enhanced chat
api/streaming_chat.py          # SSE streaming
api/agents.py                  # AI agents
api/multi_agent.py             # Multi-agent coordination
```

#### 2.2.7 Accessibility Routers
```
api/bionic_reading.py          # Dyslexia support
api/text_simplification.py     # Text simplification
api/adhd_support_api.py        # ADHD features
api/osb_settings_api.py        # Autism support
```

**Middleware Pipeline (Sıralı):**
```
1. Logging Middleware (structured logging)
2. Distributed Tracing Middleware (OpenTelemetry)
3. Sentry Error Tracking Middleware
4. Query Monitoring Middleware
5. Security Middleware (JWT, CORS, rate limiting, validation)
6. Auth Rate Limiting Middleware (brute force protection)
7. CSRF Protection Middleware
8. DDoS Protection Middleware (SlowAPI + adaptive)
9. Advanced Rate Limit Middleware (Redis + tiers)
10. Performance Tracking Middleware
11. Timeout Middleware (30s default)
12. Metrics Middleware (Prometheus)
13. Elasticsearch Logging Middleware
```

---

### 2.3 Business Logic Layer (Katman 3)

**Teknolojiler:**
- Python 3.11+
- Domain-Driven Design patterns
- Service pattern
- Repository pattern

**Dosya Konumu:** `backend/services/`
**Sayı:** 80+ service modülleri

**Sorumluluk:** Business rules, workflows, domain logic

**Service Kategorileri:**

#### 2.3.1 Exam Services
```python
# services/sinav_motoru_service.py
class SinavMotoruService:
    async def create_exam_session(self, user_id, exam_type):
        # Business logic: Exam session creation
        # - Validate user eligibility
        # - Select questions based on IRT
        # - Create session in database
        # - Cache session data
        pass

    async def calculate_score(self, exam_id):
        # Business logic: Score calculation
        # - OSYM scoring algorithm
        # - IRT-based ability estimation
        # - Normalization
        pass
```

#### 2.3.2 Question Generation Services
```python
# services/question_generation_service.py
class QuestionGenerationService:
    async def generate_question(self, subject, difficulty, bloom_level):
        # Business logic: Question generation
        # 1. Select template based on subject
        # 2. Generate content with LLM
        # 3. Generate visuals if needed (graph, geometry)
        # 4. Quality evaluation (Wave 2B)
        # 5. If quality < threshold, regenerate
        # 6. Save to database
        # 7. Index in Elasticsearch
        pass
```

#### 2.3.3 Learning Path Services
```python
# services/learning_path_service.py
class LearningPathService:
    async def generate_personalized_path(self, user_id):
        # Business logic: Learning path generation
        # 1. Get user profile (performance, style, ZPD)
        # 2. Multi-agent coordination
        # 3. Content recommendation
        # 4. FSRS scheduling
        # 5. RAG enhancement
        pass
```

#### 2.3.4 Quality Evaluation Services
```python
# services/comprehensive_quality_evaluator.py
class ComprehensiveQualityEvaluator:
    async def evaluate_question(self, question):
        # Business logic: Quality evaluation
        # 1. BERTScore calculation
        # 2. Bloom taxonomy classification
        # 3. OSYM benchmark comparison
        # 4. Comprehensive score (0-100)
        pass
```

**Service Pattern Örneği:**
```python
class BaseService:
    def __init__(self, db: AsyncSession, cache: Redis):
        self.db = db
        self.cache = cache

    async def _cache_get(self, key):
        return await self.cache.get(key)

    async def _cache_set(self, key, value, ttl=3600):
        await self.cache.setex(key, ttl, value)

class ExamService(BaseService):
    async def start_exam(self, user_id, exam_type):
        # Check cache first
        cache_key = f"exam:{user_id}:{exam_type}"
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Business logic...
        result = await self._create_exam_session(user_id, exam_type)

        # Cache result
        await self._cache_set(cache_key, result)

        return result
```

---

### 2.4 Core Infrastructure Layer (Katman 4)

**Dosya Konumu:** `backend/core/`
**Sayı:** 150+ core modülleri

**Sorumluluk:** Cross-cutting concerns, infrastructure services

**Alt Bileşenler:**

#### 2.4.1 Database Management
```python
# core/database.py
class DatabaseManager:
    """
    PostgreSQL connection management
    - Async connection pooling (50 pool, 100 max overflow)
    - Connection lifecycle
    - Transaction management
    - Retry logic
    """

    async def get_session():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except:
                await session.rollback()
                raise

# core/database_optimizer.py
class DatabaseOptimizer:
    """
    Performance optimizations
    - Create indexes
    - Analyze slow queries
    - Suggest optimizations
    """
```

#### 2.4.2 Cache Management
```python
# core/cache.py
class CacheManager:
    """
    Redis cache with fallback mode
    - Get/Set operations
    - TTL management
    - Cache invalidation
    - Stampede prevention
    """

    async def get_or_set(self, key, factory, ttl=3600):
        # Check cache
        value = await self.get(key)
        if value:
            return value

        # Stampede prevention: distributed lock
        async with self.lock(f"lock:{key}"):
            # Double-check after lock
            value = await self.get(key)
            if value:
                return value

            # Generate value
            value = await factory()

            # Cache it
            await self.set(key, value, ttl)

            return value
```

#### 2.4.3 Security Management
```python
# core/security_middleware.py
class SecurityMiddleware:
    """
    Comprehensive security
    - JWT validation
    - Rate limiting
    - Input validation (XSS, SQL injection)
    - CORS configuration
    - CSRF protection
    - Bot detection
    """

# core/auth_rate_limiting.py
class AuthRateLimiter:
    """
    Brute force protection
    - Login attempt tracking
    - Account lockout (5 failed attempts)
    - IP-based limiting
    - CAPTCHA trigger
    """
```

#### 2.4.4 Monitoring & Logging
```python
# core/structured_logger.py
class StructuredLogger:
    """
    Production-grade logging
    - JSON structured logs
    - Context enrichment
    - Sensitive data filtering (KVKK compliant)
    - Multiple destinations (console, file, Elasticsearch)
    """

# core/application_metrics.py
class MetricsCollector:
    """
    Prometheus metrics
    - Counter (requests, errors)
    - Histogram (latency)
    - Gauge (active users, queue size)
    - Summary (quantiles)
    """
```

#### 2.4.5 Distributed Tracing
```python
# core/opentelemetry_config.py
class TracingConfig:
    """
    OpenTelemetry + Jaeger integration
    - Automatic instrumentation
    - Span creation
    - Context propagation
    - Sampling strategies
    """

# core/tracing_middleware.py
@app.middleware("http")
async def tracing_middleware(request, call_next):
    # Create span for request
    with tracer.start_as_current_span(
        f"{request.method} {request.url.path}",
        attributes={
            "http.method": request.method,
            "http.url": str(request.url),
            "user.id": request.state.user_id if hasattr(request.state, 'user_id') else None
        }
    ):
        response = await call_next(request)
        return response
```

#### 2.4.6 Error Tracking
```python
# core/sentry_config.py
class SentryConfig:
    """
    Sentry error tracking
    - Automatic error capture
    - Performance monitoring
    - Release tracking
    - Email notifications (KVKK-compliant)
    - Sampling rates (10% prod, 100% dev)
    """
```

#### 2.4.7 Circuit Breakers
```python
# core/circuit_breaker.py
class CircuitBreaker:
    """
    Cascading failure protection
    - Closed state: Normal operation
    - Open state: Fast failure
    - Half-open state: Test recovery
    - Fallback logic
    """

    async def call(self, func, *args, fallback=None, **kwargs):
        if self.state == "open":
            if fallback:
                return await fallback()
            raise CircuitBreakerOpenError()

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            if self.should_open():
                self.open()
            raise
```

---

### 2.5 AI/ML Layer (Katman 5)

**Teknolojiler:**
- OpenAI GPT-4 (text generation)
- Transformers (BERTurk, T5, BART)
- PyTorch 2.1.0
- scikit-learn 1.3.2
- LangChain

**Dosya Konumu:** `backend/services/`, `backend/agents/`, `backend/core/`

**Alt Bileşenler:**

#### 2.5.1 LLM Service
```python
# core/llm_service.py
class LLMService:
    """
    Large Language Model interface
    - OpenAI GPT-4 integration
    - Prompt engineering
    - Token counting
    - Cost tracking
    - Rate limiting
    - Retry logic
    """

    async def generate(self, prompt, max_tokens=1000, temperature=0.7):
        # Token counting
        token_count = self.count_tokens(prompt)

        # Cost estimation
        estimated_cost = self.estimate_cost(token_count, max_tokens)

        # Rate limiting check
        if not await self.rate_limiter.check():
            raise RateLimitExceeded()

        # Generate
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Track usage
        await self.track_usage(response)

        return response.choices[0].message.content
```

#### 2.5.2 BERTurk Service
```python
# core/berturk_service.py
class BERTurkService:
    """
    Turkish BERT model
    - Sentiment analysis
    - Motivation detection
    - Intent classification
    - Semantic similarity
    - Embeddings generation
    """

    async def analyze_sentiment(self, text):
        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)

        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Get predictions
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)

        return {
            "positive": probs[0][2].item(),
            "neutral": probs[0][1].item(),
            "negative": probs[0][0].item()
        }

    async def get_embeddings(self, text):
        # For semantic search
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Mean pooling
        embeddings = outputs.last_hidden_state.mean(dim=1)

        return embeddings.numpy()
```

#### 2.5.3 Multi-Agent System
```python
# agents/blackboard_coordinator.py
class BlackboardCoordinator:
    """
    Multi-agent coordination using blackboard architecture
    - Agent registration
    - Task distribution
    - Result aggregation
    - Conflict resolution
    """

    def __init__(self):
        self.blackboard = {}  # Shared memory
        self.agents = []      # Registered agents

    async def coordinate(self, task):
        # 1. Post task to blackboard
        self.blackboard['current_task'] = task

        # 2. Notify all agents
        agent_results = await asyncio.gather(*[
            agent.process(task) for agent in self.agents
        ])

        # 3. Aggregate results
        aggregated = self.aggregate_results(agent_results)

        # 4. Resolve conflicts
        resolved = self.resolve_conflicts(aggregated)

        return resolved

# agents/learning_path_agent.py
class LearningPathAgent:
    """
    Specialized agent for learning path generation
    - Analyzes student performance
    - Recommends learning resources
    - Schedules study sessions
    """

    async def process(self, task):
        if task['type'] != 'learning_path':
            return None

        # Agent-specific logic
        student_id = task['student_id']

        # 1. Get student profile
        profile = await self.get_profile(student_id)

        # 2. Analyze weak areas
        weak_areas = await self.analyze_weak_areas(profile)

        # 3. Recommend resources
        resources = await self.recommend_resources(weak_areas)

        # 4. Create schedule
        schedule = await self.create_schedule(resources, profile['available_time'])

        return {
            'agent': 'learning_path',
            'confidence': 0.95,
            'recommendations': resources,
            'schedule': schedule
        }
```

#### 2.5.4 IRT (Item Response Theory)
```python
# services/irt_service.py
class IRTService:
    """
    Item Response Theory analysis
    - 3PL model (a, b, c parameters)
    - Ability estimation (theta)
    - Item difficulty calibration
    - Turkish morphology-aware
    """

    def estimate_ability(self, responses, items):
        """
        Estimate student ability (theta) using MLE
        """
        # Maximum Likelihood Estimation
        def likelihood(theta):
            prob = 1.0
            for response, item in zip(responses, items):
                p = self.irt_3pl(theta, item['a'], item['b'], item['c'])
                if response == 1:
                    prob *= p
                else:
                    prob *= (1 - p)
            return prob

        # Optimize
        result = minimize(
            lambda theta: -np.log(likelihood(theta)),
            x0=0.0,
            bounds=[(-4, 4)]
        )

        return result.x[0]

    def irt_3pl(self, theta, a, b, c):
        """
        3-Parameter Logistic Model
        theta: ability
        a: discrimination
        b: difficulty
        c: guessing
        """
        return c + (1 - c) / (1 + np.exp(-a * (theta - b)))
```

#### 2.5.5 FSRS (Free Spaced Repetition Scheduler)
```python
# services/fsrs_service.py
class FSRSService:
    """
    Spaced repetition scheduling
    - 17 parameters optimized for Turkish students
    - Difficulty estimation
    - Stability calculation
    - Review scheduling
    """

    def __init__(self):
        # Turkish student-optimized parameters
        self.w = [
            0.4072,   # initial stability for easy
            1.1829,   # initial stability for good
            3.1262,   # initial stability for hard
            15.4722,  # initial stability for again
            7.2102,   # initial difficulty
            0.5316,   # difficulty increment for easy
            1.2503,   # difficulty increment for hard
            0.0234,   # stability increment for easy
            1.6255,   # stability increment for good
            0.8738,   # stability increment for hard
            0.9946,   # retrievability threshold
            # ... 6 more parameters
        ]

    def schedule_next_review(self, card):
        """
        Calculate next review date
        """
        stability = card['stability']
        difficulty = card['difficulty']

        # Calculate interval
        interval = self.calculate_interval(stability, difficulty)

        # Next review date
        next_review = datetime.now() + timedelta(days=interval)

        return next_review
```

---

### 2.6 Algorithm Layer (Katman 6)

**Dosya Konumu:** `backend/algorithms/`
**Sayı:** 17 algorithm modülleri

**Sorumluluk:** Domain-specific algorithms, Turkish-optimized logic

**Alt Bileşenler:**

#### 2.6.1 Turkish NLP Algorithms
```python
# algorithms/turkish_morphology_aware_irt.py
class TurkishMorphologyAwareIRT:
    """
    IRT + Turkish morphology integration
    - Zemberek-NLP for morphological analysis
    - Difficulty estimation based on:
      * Word complexity
      * Sentence structure
      * Morphological features (case, tense, etc.)
    """

    def calculate_linguistic_difficulty(self, text):
        # Morphological analysis
        words = self.zemberek.analyze(text)

        scores = []
        for word in words:
            # Root complexity
            root_score = self.root_complexity(word.root)

            # Affix complexity
            affix_score = len(word.affixes) * 0.1

            # Morphological features
            feature_score = self.feature_complexity(word.features)

            scores.append(root_score + affix_score + feature_score)

        return np.mean(scores)

# algorithms/turkish_text_simplification.py
class ThreeLevelTurkishSimplification:
    """
    World's first Turkish text simplification
    - Basic level (6th grade)
    - Intermediate level (9th grade)
    - Advanced level (12th grade)
    """

    async def simplify(self, text, level="basic"):
        # 1. Morphological analysis
        analyzed = self.zemberek.analyze(text)

        # 2. Identify complex words
        complex_words = self.identify_complex(analyzed, level)

        # 3. Find simpler alternatives
        simplified = []
        for word in analyzed:
            if word in complex_words:
                alternative = await self.find_alternative(word, level)
                simplified.append(alternative)
            else:
                simplified.append(word.surface)

        # 4. Reconstruct sentence
        return ' '.join(simplified)
```

#### 2.6.2 Adaptive Learning Algorithms
```python
# algorithms/adaptive_learning.py
class AdaptiveLearningAlgorithm:
    """
    Adaptive difficulty adjustment
    - Real-time performance tracking
    - Dynamic difficulty adjustment
    - Zone of Proximal Development (ZPD)
    """

    def adjust_difficulty(self, student_performance, current_difficulty):
        # Calculate success rate
        success_rate = student_performance['correct'] / student_performance['total']

        # Too easy: 80%+ success rate
        if success_rate >= 0.8:
            new_difficulty = current_difficulty + 0.5

        # Too hard: <50% success rate
        elif success_rate < 0.5:
            new_difficulty = current_difficulty - 0.5

        # Just right: 50-80% success rate (ZPD)
        else:
            new_difficulty = current_difficulty

        # Clamp to valid range
        return max(0.0, min(5.0, new_difficulty))

# algorithms/hybrid_learning_style_detector.py
class HybridLearningStyleDetector:
    """
    64-profile learning style detection
    - Visual/Auditory/Kinesthetic
    - Sequential/Global
    - Active/Reflective
    - Sensing/Intuitive
    """

    def detect_style(self, user_behavior):
        # Analyze behavior patterns
        visual_score = self.analyze_visual_preference(user_behavior)
        sequential_score = self.analyze_sequential_preference(user_behavior)
        active_score = self.analyze_active_preference(user_behavior)
        sensing_score = self.analyze_sensing_preference(user_behavior)

        # Create profile
        profile = {
            'visual': visual_score > 0.5,
            'sequential': sequential_score > 0.5,
            'active': active_score > 0.5,
            'sensing': sensing_score > 0.5
        }

        # Map to 64 profiles (2^6)
        profile_id = self.map_to_profile(profile)

        return {
            'profile_id': profile_id,
            'dimensions': profile,
            'confidence': self.calculate_confidence(user_behavior)
        }
```

#### 2.6.3 ZPD + Turkish Education System
```python
# algorithms/turkish_zpd_maarif_system.py
class TurkishZPDMaarifSystem:
    """
    Vygotsky's ZPD adapted for Turkish education
    - MEB (Ministry of Education) curriculum alignment
    - OSYM standards compliance
    - Cultural factors (family involvement, exam anxiety)
    """

    def calculate_zpd(self, student):
        # Current level (what student can do alone)
        current_level = student['current_ability']

        # Potential level (with help)
        potential_level = self.estimate_potential(student)

        # ZPD range
        zpd_range = {
            'lower_bound': current_level,
            'upper_bound': potential_level,
            'optimal_difficulty': (current_level + potential_level) / 2
        }

        # MEB curriculum alignment
        meb_level = self.map_to_meb_curriculum(zpd_range['optimal_difficulty'])

        # Cultural adaptation
        if student['exam_anxiety'] > 0.7:
            # Lower difficulty for high-anxiety students
            zpd_range['optimal_difficulty'] *= 0.9

        if student['family_pressure'] > 0.7:
            # Gradual progression for high-pressure students
            zpd_range['optimal_difficulty'] *= 0.95

        return zpd_range
```

---

### 2.7 Database Layer (Katman 7)

**Teknoloji:** PostgreSQL 15, SQLAlchemy 2.0 (async), Alembic

**Dosya Konumu:** `backend/models/`
**Sayı:** 40+ SQLAlchemy models

**Sorumluluk:** Data persistence, relationships, constraints

**Alt Bileşenler:**

#### 2.7.1 Core Models
```python
# models/base.py
class BaseModel:
    """
    Base model with common fields
    - id (UUID primary key)
    - created_at (timestamp with timezone)
    - updated_at (timestamp with timezone)
    - is_active (soft delete)
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

# models/user.py
class User(BaseModel, Base):
    __tablename__ = "users"

    # Identity
    email = Column(String, unique=True, nullable=False, index=True)
    ad_soyad = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Role
    rol = Column(Enum(UserRole), nullable=False, index=True)

    # 2FA (Sprint 4)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String, nullable=True)

    # Relationships
    exams = relationship("Exam", back_populates="user")
    learning_paths = relationship("LearningPath", back_populates="user")
    answers = relationship("Answer", back_populates="user")
```

#### 2.7.2 Exam Models
```python
# models/exam.py
class Exam(BaseModel, Base):
    __tablename__ = "exams"

    # Basic info
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    exam_type = Column(Enum(ExamType), nullable=False)  # TYT, AYT, YDT

    # Timing
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer, default=180)

    # Scoring
    total_score = Column(Float, nullable=True)
    net_score = Column(Float, nullable=True)

    # IRT
    estimated_ability = Column(Float, nullable=True)  # theta

    # Relationships
    user = relationship("User", back_populates="exams")
    questions = relationship("ExamQuestion", back_populates="exam")
    answers = relationship("Answer", back_populates="exam")

    # Indexes
    __table_args__ = (
        Index('ix_exam_user_type', 'user_id', 'exam_type'),
        Index('ix_exam_started_at', 'started_at'),
    )

class ExamQuestion(BaseModel, Base):
    __tablename__ = "exam_questions"

    exam_id = Column(UUID, ForeignKey("exams.id"), nullable=False)
    question_id = Column(UUID, ForeignKey("questions.id"), nullable=False)
    order = Column(Integer, nullable=False)

    # Relationships
    exam = relationship("Exam", back_populates="questions")
    question = relationship("Question")
```

#### 2.7.3 Question Models
```python
# models/soru_model.py
class Question(BaseModel, Base):
    __tablename__ = "questions"

    # Content
    question_text = Column(Text, nullable=False)
    options = Column(JSONB, nullable=False)  # {"A": "...", "B": "...", ...}
    correct_answer = Column(String(1), nullable=False)  # A, B, C, D, E

    # Classification
    subject = Column(Enum(Subject), nullable=False, index=True)
    difficulty = Column(Float, default=3.0)  # 1.0-5.0
    bloom_level = Column(Enum(BloomLevel), default=BloomLevel.UNDERSTANDING)

    # IRT Parameters
    irt_discrimination = Column(Float, nullable=True)  # a parameter
    irt_difficulty = Column(Float, nullable=True)      # b parameter
    irt_guessing = Column(Float, nullable=True)        # c parameter

    # Visual content
    has_image = Column(Boolean, default=False)
    image_url = Column(String, nullable=True)
    has_graph = Column(Boolean, default=False)
    graph_data = Column(JSONB, nullable=True)

    # Quality metrics (Wave 2B)
    bertscore = Column(Float, nullable=True)
    osym_similarity = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)

    # Source
    source = Column(Enum(QuestionSource), default=QuestionSource.AI_GENERATED)
    generation_method = Column(String, nullable=True)

    # Full-text search
    search_vector = Column(
        TSVectorType('question_text', regconfig='turkish')
    )

    # Indexes
    __table_args__ = (
        Index('ix_question_subject_difficulty', 'subject', 'difficulty'),
        Index('ix_question_quality_score', 'quality_score'),
        Index('ix_question_search_vector', 'search_vector', postgresql_using='gin'),
    )
```

#### 2.7.4 Learning Path Models
```python
# models/learning_path_models.py
class LearningPath(BaseModel, Base):
    __tablename__ = "learning_paths"

    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)

    # Goals
    target_exam = Column(Enum(ExamType), nullable=False)
    target_score = Column(Float, nullable=True)
    target_date = Column(Date, nullable=True)

    # Learning style (64 profiles)
    learning_style_profile = Column(Integer, nullable=True)  # 0-63

    # ZPD
    zpd_lower_bound = Column(Float, nullable=True)
    zpd_upper_bound = Column(Float, nullable=True)
    zpd_optimal_difficulty = Column(Float, nullable=True)

    # Progress
    completion_percentage = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="learning_paths")
    resources = relationship("LearningPathResource", back_populates="learning_path")
    reviews = relationship("Review", back_populates="learning_path")

class LearningPathResource(BaseModel, Base):
    __tablename__ = "learning_path_resources"

    learning_path_id = Column(UUID, ForeignKey("learning_paths.id"), nullable=False)
    resource_type = Column(Enum(ResourceType), nullable=False)  # VIDEO, ARTICLE, QUESTION
    resource_id = Column(UUID, nullable=False)

    # Scheduling (FSRS)
    due_date = Column(DateTime(timezone=True), nullable=True)
    stability = Column(Float, nullable=True)
    difficulty = Column(Float, nullable=True)

    # Progress
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
```

#### 2.7.5 Performance Indexes
```sql
-- backend/alembic/versions/002_performance_indexes.py

-- User queries
CREATE INDEX CONCURRENTLY ix_users_email_active
ON users(email) WHERE is_active = true;

CREATE INDEX CONCURRENTLY ix_users_rol
ON users(rol) WHERE is_active = true;

-- Exam queries
CREATE INDEX CONCURRENTLY ix_exams_user_started
ON exams(user_id, started_at DESC) WHERE is_active = true;

CREATE INDEX CONCURRENTLY ix_exam_questions_exam
ON exam_questions(exam_id, order);

-- Question queries
CREATE INDEX CONCURRENTLY ix_questions_subject_difficulty_quality
ON questions(subject, difficulty, quality_score DESC)
WHERE is_active = true;

CREATE INDEX CONCURRENTLY ix_questions_irt_params
ON questions(irt_discrimination, irt_difficulty)
WHERE irt_discrimination IS NOT NULL;

-- Full-text search (Turkish)
CREATE INDEX CONCURRENTLY ix_questions_search_vector_gin
ON questions USING gin(search_vector);

-- Learning path queries
CREATE INDEX CONCURRENTLY ix_learning_paths_user_active
ON learning_paths(user_id)
WHERE is_active = true AND completion_percentage < 100;

CREATE INDEX CONCURRENTLY ix_learning_path_resources_due
ON learning_path_resources(learning_path_id, due_date)
WHERE completed = false;
```

---

### 2.8 External Services Layer (Katman 8)

**Sorumluluk:** Third-party API entegrasyonları

**Alt Bileşenler:**

#### 2.8.1 OpenAI Integration
```python
# services/llm_service.py (continued)
class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.rate_limiter = RateLimiter(rpm=60, tpm=90000)

    async def generate_question(self, prompt):
        # Rate limiting
        await self.rate_limiter.wait_if_needed()

        # Generate
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sen bir OSYM sınav sorusu uzmanısın."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # Track cost
        cost = self.calculate_cost(response.usage)
        await self.track_cost(cost)

        return response.choices[0].message.content
```

#### 2.8.2 YouTube Integration
```python
# services/real_youtube_api.py
class YouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        self.rate_limiter = RateLimiter(qps=100)  # 100 queries per second

    async def search_videos(self, query, subject, max_results=10):
        # Rate limiting
        await self.rate_limiter.wait_if_needed()

        # Optimize query for Turkish education
        optimized_query = self.optimize_query(query, subject)

        # Search
        response = await self.youtube.search().list(
            q=optimized_query,
            part="snippet",
            maxResults=max_results,
            relevanceLanguage="tr",
            type="video",
            videoCaption="closedCaption",  # Only videos with Turkish subtitles
            videoDuration="medium"  # 4-20 minutes
        ).execute()

        # Filter and rank
        videos = self.filter_educational_videos(response['items'])
        ranked = self.rank_by_quality(videos)

        return ranked
```

#### 2.8.3 EBA TV Integration
```python
# services/eba_tv_client.py
class EBATVClient:
    """
    Turkish Ministry of Education's EBA TV platform
    """

    async def fetch_content(self, grade, subject):
        # EBA TV API call
        response = await self.client.get(
            f"{settings.EBA_TV_BASE_URL}/content",
            params={
                "grade": grade,
                "subject": subject,
                "language": "tr"
            }
        )

        # Parse response
        content = response.json()

        # Cache for 1 hour (EBA content doesn't change frequently)
        await self.cache.set(
            f"eba:{grade}:{subject}",
            content,
            ttl=3600
        )

        return content
```

#### 2.8.4 Khan Academy Integration
```python
# services/khan_academy_client.py
class KhanAcademyClient:
    async def get_resources(self, topic):
        # Khan Academy API
        response = await self.client.get(
            f"{settings.KHAN_ACADEMY_API}/topic/{topic}",
            params={"lang": "tr"}  # Turkish language
        )

        resources = response.json()

        # Filter for Turkish content
        turkish_resources = [
            r for r in resources
            if r.get('language') == 'tr' or r.get('has_turkish_subtitles')
        ]

        return turkish_resources
```

---

### 2.9 Monitoring & Observability Layer (Katman 9)

**Teknolojiler:**
- Prometheus (metrics)
- Grafana (visualization)
- Jaeger (distributed tracing)
- Sentry (error tracking)
- Elasticsearch (logs)

**Alt Bileşenler:**

#### 2.9.1 Metrics Collection (Prometheus)
```python
# core/application_metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_latency = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Business metrics
active_exams = Gauge(
    'active_exams_total',
    'Number of active exams'
)

question_generation_requests = Counter(
    'question_generation_requests_total',
    'Total question generation requests',
    ['subject', 'difficulty', 'status']
)

ai_api_cost = Counter(
    'ai_api_cost_usd',
    'Total AI API cost in USD',
    ['provider', 'model']
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    ['state']  # 'available', 'in_use'
)

# Cache metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']  # 'redis', 'memory'
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)
```

#### 2.9.2 Distributed Tracing (Jaeger)
```python
# core/tracing_middleware.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Setup tracer
tracer_provider = TracerProvider()
jaeger_exporter = JaegerExporter(
    agent_host_name=settings.JAEGER_HOST,
    agent_port=settings.JAEGER_PORT
)
tracer_provider.add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)
trace.set_tracer_provider(tracer_provider)

# Auto-instrumentation
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
RedisInstrumentor().instrument(redis_client=redis)

# Manual instrumentation example
tracer = trace.get_tracer(__name__)

async def generate_question(subject, difficulty):
    with tracer.start_as_current_span("generate_question") as span:
        span.set_attribute("subject", subject)
        span.set_attribute("difficulty", difficulty)

        # Step 1: Select template
        with tracer.start_as_current_span("select_template"):
            template = await select_template(subject)

        # Step 2: Generate with LLM
        with tracer.start_as_current_span("llm_generation") as llm_span:
            llm_span.set_attribute("model", "gpt-4")
            question = await llm_service.generate(template)

        # Step 3: Quality evaluation
        with tracer.start_as_current_span("quality_evaluation"):
            quality = await evaluate_quality(question)
            span.set_attribute("quality_score", quality)

        return question
```

#### 2.9.3 Error Tracking (Sentry)
```python
# core/sentry_config.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    release=settings.VERSION,

    # Integrations
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        RedisIntegration(),
    ],

    # Performance monitoring
    traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,

    # Error sampling
    sample_rate=1.0,

    # KVKK compliance: Don't send PII
    send_default_pii=False,

    # Before send hook (filter sensitive data)
    before_send=filter_sensitive_data,
)

def filter_sensitive_data(event, hint):
    # Remove email, phone, password from event
    if 'request' in event:
        if 'data' in event['request']:
            data = event['request']['data']
            if 'email' in data:
                data['email'] = '[FILTERED]'
            if 'phone' in data:
                data['phone'] = '[FILTERED]'
            if 'password' in data:
                data['password'] = '[FILTERED]'

    return event

# Usage
from sentry_sdk import capture_exception, capture_message

try:
    result = await risky_operation()
except Exception as e:
    capture_exception(e)
    # Add custom context
    sentry_sdk.set_context("exam", {
        "exam_id": exam_id,
        "user_id": user_id,
        "question_count": len(questions)
    })
    raise
```

#### 2.9.4 Logging (Elasticsearch)
```python
# core/elasticsearch_logger.py
class ElasticsearchLogger:
    def __init__(self):
        self.client = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
        self.index_prefix = "kiro2-logs"

    async def log(self, level, message, context=None):
        # Create log document
        doc = {
            "@timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "service": "kiro2-backend",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
        }

        # Add context
        if context:
            doc.update(context)

        # Filter sensitive data
        doc = self.filter_sensitive(doc)

        # Index to Elasticsearch
        index = f"{self.index_prefix}-{datetime.utcnow():%Y.%m.%d}"
        await self.client.index(
            index=index,
            document=doc
        )
```

---

### 2.10 Infrastructure Layer (Katman 10)

**Teknolojiler:**
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7
- Nginx
- Kubernetes (hazır)

**Alt Bileşenler:**

#### 2.10.1 Docker Compose Services
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: kiro2_db
      POSTGRES_USER: kiro2_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=tr_TR.UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kiro2_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Cache
  redis:
    image: redis:7-alpine
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Search
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/prometheus/alerts:/etc/prometheus/alerts
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
      - grafana_data:/var/lib/grafana
    ports:
      - "3001:3000"
    depends_on:
      - prometheus

  # Backend
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://kiro2_user:${DB_PASSWORD}@postgres:5432/kiro2_db
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - elasticsearch

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
  prometheus_data:
  grafana_data:
```

#### 2.10.2 Redis Configuration
```conf
# redis.conf
# Persistence
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000

# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Turkish character support
# UTF-8 encoding is default

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Security
requirepass ${REDIS_PASSWORD}
```

#### 2.10.3 Kubernetes Deployment (Hazır)
```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kiro2-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kiro2-backend
  template:
    metadata:
      labels:
        app: kiro2-backend
    spec:
      containers:
      - name: backend
        image: kiro2/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: kiro2-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 3. BİLEŞEN İLİŞKİ MATRİSİ

### 3.1 İlişki Türleri

- **S (Synchronous):** Senkron çağrı (HTTP, function call)
- **A (Asynchronous):** Asenkron işlem (message queue, event)
- **R (Read):** Veri okuma
- **W (Write):** Veri yazma
- **D (Depends):** Bağımlılık

### 3.2 Bileşenler Arası İlişki Tablosu

```
┌──────────────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│              │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │ 8  │ 9  │ 10 │
├──────────────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
│1. Frontend   │ -  │ S  │    │    │    │    │    │    │ R  │    │
│2. API Gateway│    │ -  │ S  │ D  │ S  │    │    │    │ W  │    │
│3. Business   │    │    │ -  │ S  │ S  │ S  │RW  │ S  │ W  │    │
│4. Core Infra │    │    │    │ -  │    │    │RW  │    │ W  │ D  │
│5. AI/ML      │    │    │    │ D  │ -  │ S  │ R  │ S  │ W  │    │
│6. Algorithm  │    │    │    │    │    │ -  │ R  │    │ W  │    │
│7. Database   │    │    │    │    │    │    │ -  │    │ W  │ D  │
│8. External   │    │    │    │ D  │    │    │ W  │ -  │ W  │    │
│9. Monitoring │    │    │    │    │    │    │    │    │ -  │    │
│10. Infra     │    │    │    │    │    │    │    │    │    │ -  │
└──────────────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

Legend:
S = Synchronous call    R = Read
A = Asynchronous call   W = Write
D = Dependency          - = Self
```

### 3.3 Detaylı İlişki Açıklamaları

#### Frontend → API Gateway (S)
- **İlişki Türü:** REST API çağrıları (HTTP/HTTPS)
- **Protokol:** JSON over HTTPS
- **Örnek:**
  ```typescript
  // Frontend: examService.ts
  const response = await apiClient.post('/api/sinav/start', { exam_type: 'TYT' });

  // Backend: api/sinav.py
  @router.post("/start")
  async def start_exam(exam_data: ExamStartRequest):
      return await sinav_service.create_exam_session(exam_data)
  ```

#### API Gateway → Business Logic (S)
- **İlişki Türü:** Function çağrıları
- **Örnek:**
  ```python
  # API Layer
  @router.post("/sinav/start")
  async def start_exam(exam_data: ExamStartRequest, db: AsyncSession = Depends(get_db)):
      # Call business logic
      result = await sinav_motoru_service.create_exam_session(
          db=db,
          user_id=exam_data.user_id,
          exam_type=exam_data.exam_type
      )
      return result
  ```

#### Business Logic → Core Infrastructure (S)
- **İlişki Türü:** Infrastructure services kullanımı
- **Örnekler:**
  ```python
  # Service uses database
  result = await db.execute(query)

  # Service uses cache
  cached = await cache.get(key)

  # Service logs
  logger.info("Exam started", extra={"exam_id": exam_id})

  # Service tracks metrics
  exam_start_counter.inc()
  ```

#### Business Logic → AI/ML (S)
- **İlişki Türü:** AI service çağrıları
- **Örnek:**
  ```python
  # Business logic calls LLM
  question = await llm_service.generate_question(
      subject="matematik",
      difficulty=3.5,
      bloom_level="analysis"
  )

  # Business logic calls BERTurk
  sentiment = await berturk_service.analyze_sentiment(student_response)
  ```

#### AI/ML → Algorithm (S)
- **İlişki Türü:** Algorithm kullanımı
- **Örnek:**
  ```python
  # LLM service uses Turkish text simplification
  simplified = await turkish_simplifier.simplify(text, level="basic")

  # IRT service uses morphology-aware algorithm
  difficulty = turkish_irt.calculate_linguistic_difficulty(question_text)
  ```

#### Core Infrastructure → Database (RW)
- **İlişki Türü:** CRUD operations
- **Örnek:**
  ```python
  # Database manager
  async with get_db() as session:
      result = await session.execute(query)
      await session.commit()
  ```

#### Business Logic → Database (RW)
- **İlişki Türü:** Direct database access
- **Örnek:**
  ```python
  # Service directly queries database
  exams = await db.execute(
      select(Exam)
      .where(Exam.user_id == user_id)
      .order_by(Exam.started_at.desc())
  )
  ```

#### Business Logic → External Services (S)
- **İlişki Türü:** API calls
- **Örnek:**
  ```python
  # OpenAI API call
  response = await openai_client.chat.completions.create(...)

  # YouTube API call
  videos = await youtube_service.search_videos(query)
  ```

#### All Layers → Monitoring (W)
- **İlişki Türü:** Metrics, logs, traces
- **Örnek:**
  ```python
  # Metrics
  request_counter.inc()
  request_latency.observe(duration)

  # Logs
  logger.info("Operation completed")

  # Traces
  with tracer.start_as_current_span("operation"):
      result = await do_operation()

  # Errors
  sentry_sdk.capture_exception(error)
  ```

---

## 4. VERİ AKIŞ DİYAGRAMLARI

### 4.1 Kullanıcı Girişi (Authentication Flow)

```
┌──────────┐
│ Frontend │
│  Login   │
│Component │
└────┬─────┘
     │ 1. POST /api/auth/login
     │    { email, password }
     ▼
┌────────────────┐
│  API Gateway   │
│   auth.py      │
└────┬───────────┘
     │ 2. Validate input (Pydantic)
     │ 3. Call auth service
     ▼
┌────────────────┐
│ Business Logic │
│  AuthService   │
└────┬───────────┘
     │ 4. Query user
     ▼
┌────────────────┐      5. Check password
│   Database     ├──────────────────────┐
│  users table   │                      │
└────────────────┘                      │
                                        ▼
                                   ┌─────────┐
                                   │ bcrypt  │
                                   │ verify  │
                                   └────┬────┘
                                        │ 6. Valid?
                                        ▼
┌────────────────┐              ┌──────────────┐
│     Redis      │◄─────────────┤ 2FA Check?   │
│  Session Cache │ 7. Create    │ (Sprint 4)   │
└────┬───────────┘    session   └──────────────┘
     │                                  │
     │ 8. Generate JWT                  │
     ▼                                  ▼
┌────────────────┐              ┌──────────────┐
│   JWT Token    │              │  TOTP Code   │
│   Generator    │              │  Generator   │
└────┬───────────┘              └──────┬───────┘
     │                                  │
     │ 9. Return token + user data      │
     ▼                                  ▼
┌────────────────┐
│   Frontend     │
│  authStore.ts  │
│ (Zustand)      │
└────┬───────────┘
     │ 10. Store token
     │ 11. Redirect to dashboard
     ▼
┌────────────────┐
│   Dashboard    │
│   Component    │
└────────────────┘
```

### 4.2 Sınav Başlatma (Exam Start Flow)

```
┌──────────┐
│ Frontend │
│   Exam   │
│Component │
└────┬─────┘
     │ 1. User clicks "Sınavı Başlat"
     │ 2. POST /api/sinav/start
     │    { exam_type: "TYT" }
     │    Authorization: Bearer <token>
     ▼
┌────────────────────┐
│   API Gateway      │
│ Middleware Stack   │
└────┬───────────────┘
     │ 3. JWT validation
     │ 4. Rate limiting check
     │ 5. Input validation
     ▼
┌────────────────────┐
│  Business Logic    │
│ SinavMotoruService │
└────┬───────────────┘
     │ 6. Check if user has active exam
     ▼
┌──────────────┐   7. Cache check
│    Redis     ├───────────────────┐
│  Exam Cache  │                   │
└──────────────┘                   │ Cache miss
                                   ▼
                          ┌──────────────────┐
                          │   Database       │
                          │ Check active exam│
                          └────────┬─────────┘
                                   │ No active exam
                                   │ 8. Get user profile
                                   ▼
┌─────────────────────────────────────────────┐
│           AI/ML Layer                        │
│  ┌──────────────┐  ┌─────────────────────┐ │
│  │ IRT Service  │  │ Learning Style      │ │
│  │ Get ability  │  │ Detector            │ │
│  └──────┬───────┘  └─────────┬───────────┘ │
│         │ theta              │ profile      │
│         └──────────┬─────────┘              │
│                    │ 9. User context        │
└────────────────────┼────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│       Question Selection Algorithm           │
│  ┌───────────────────────────────────────┐  │
│  │  Adaptive Item Selection (IRT-based)  │  │
│  │  - Difficulty matching (ZPD)          │  │
│  │  - Content balancing (TYT subjects)   │  │
│  │  - Bloom taxonomy distribution        │  │
│  └───────────────┬───────────────────────┘  │
│                  │ 10. Select 40 questions  │
└──────────────────┼──────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│          Database                         │
│  ┌────────────────────────────────────┐  │
│  │ 1. Create exam record              │  │
│  │ 2. Create exam_questions records   │  │
│  │ 3. Begin transaction                │  │
│  └─────────────────┬──────────────────┘  │
└────────────────────┼─────────────────────┘
                     │ 11. Commit
                     ▼
┌──────────────────────────────────────────┐
│          Redis Cache                      │
│  exam:{user_id}:{exam_id} = {            │
│    questions: [...],                     │
│    started_at: timestamp,                │
│    time_left: 180 * 60,                  │
│    answers: {}                           │
│  }                                       │
│  TTL: 4 hours                            │
└───────────────────┬──────────────────────┘
                    │ 12. Cache exam session
                    ▼
┌──────────────────────────────────────────┐
│        Monitoring                         │
│  - Metrics: exam_start_counter.inc()     │
│  - Logs: "Exam started"                  │
│  - Trace: span "create_exam_session"     │
└───────────────────┬──────────────────────┘
                    │
                    │ 13. Return response
                    ▼
┌──────────────────────────────────────────┐
│         API Gateway                       │
│  Response: {                             │
│    exam_id: "...",                       │
│    questions: [...],                     │
│    time_limit: 180,                      │
│    started_at: "..."                     │
│  }                                       │
└───────────────────┬──────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│         Frontend                          │
│  1. examStore.setCurrentExam(data)       │
│  2. Navigate to /exam/:exam_id           │
│  3. Start timer countdown                │
│  4. Display first question               │
└──────────────────────────────────────────┘
```

### 4.3 Soru Cevaplama (Answer Submission Flow)

```
┌──────────────┐
│   Frontend   │
│ Exam Component│
└──────┬───────┘
       │ 1. User selects answer (A/B/C/D/E)
       │ 2. POST /api/sinav/answer
       │    { exam_id, question_id, answer }
       ▼
┌──────────────────────┐
│   API Gateway        │
│ Timeout Middleware   │
│ (30s timeout)        │
└──────┬───────────────┘
       │ 3. Validate
       ▼
┌──────────────────────┐
│  Business Logic      │
│  ExamService         │
└──────┬───────────────┘
       │ 4. Optimistic locking check
       ▼
┌──────────────────────┐      5. Get exam session
│      Redis           ├─────────────────────────┐
│   Exam Cache         │                         │
└──────────────────────┘                         │
                                                 ▼
                                        ┌────────────────┐
                                        │ Update answer  │
                                        │ in cache       │
                                        └────┬───────────┘
                                             │ 6. Save to DB (async)
                                             ▼
┌──────────────────────────────────────────────────────┐
│              Celery Task Queue                        │
│  Task: save_answer_to_database                       │
│  - exam_id, question_id, answer, timestamp          │
│  - Retry policy: 3 attempts, exponential backoff    │
└───────────────────┬──────────────────────────────────┘
                    │ 7. Async execution
                    ▼
┌──────────────────────────────────────────┐
│          Database                         │
│  INSERT INTO answers (...)                │
│  - Deferred commit                        │
│  - Batch processing (every 10s or 100)   │
└───────────────────┬──────────────────────┘
                    │
                    │ 8. Return immediate response
                    ▼
┌──────────────────────────────────────────┐
│         Frontend                          │
│  1. Show "✓ Kaydedildi" animation        │
│  2. Move to next question                │
│  3. Update progress bar                  │
└──────────────────────────────────────────┘
```

### 4.4 Soru Üretimi (Question Generation Flow)

```
┌──────────────┐
│   Frontend   │
│ Admin Panel  │
└──────┬───────┘
       │ 1. POST /api/question-generation/hybrid
       │    { subject: "matematik",
       │      difficulty: 3.5,
       │      bloom_level: "analysis",
       │      count: 10 }
       ▼
┌──────────────────────────────────────┐
│      API Gateway                      │
│  rate_limit: 10 requests/minute      │
└──────┬───────────────────────────────┘
       │ 2. Check quota & validate
       ▼
┌──────────────────────────────────────┐
│     Business Logic                    │
│  HybridQuestionGenerator              │
└──────┬───────────────────────────────┘
       │ 3. Select generation method
       │    (OSYM-inspired, template-based, or hybrid)
       ▼
┌──────────────────────────────────────────────────────┐
│               Template Selection                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ enhanced_question_templates.py                 │  │
│  │ - Get templates for subject                    │  │
│  │ - Filter by difficulty & Bloom level           │  │
│  │ - Select template randomly                     │  │
│  └──────────────────┬─────────────────────────────┘  │
│                     │ 4. Template selected            │
└─────────────────────┼─────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          Subject-Specific Prompts                │
│  subject_specific_prompts.py                    │
│  - Mathematics prompt engineering               │
│  - Include: formulas, graphs, equations         │
│  - Turkish education terminology                │
│  - OSYM question patterns                       │
└─────────────────────┬───────────────────────────┘
                      │ 5. Prompt ready
                      ▼
┌─────────────────────────────────────────────────┐
│            LLM Service (GPT-4)                   │
│  ┌──────────────────────────────────────────┐   │
│  │ 1. Token counting (optimize cost)        │   │
│  │ 2. Rate limiting check                   │   │
│  │ 3. Generate question                     │   │
│  │ 4. Parse response (JSON)                 │   │
│  └──────────────────┬───────────────────────┘   │
│                     │ 6. Question generated      │
└─────────────────────┼────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ Visual Generator │    │  Text Question   │
│ (if needed)      │    │   (plain text)   │
└────┬─────────────┘    └────┬─────────────┘
     │                       │
     │ 7a. Generate graph    │ 7b. Format text
     │     or geometry       │
     ▼                       ▼
┌──────────────────────────────────────────┐
│        Quality Evaluation                 │
│  ┌────────────────────────────────────┐  │
│  │ Wave 2B Quality Evaluator          │  │
│  │                                    │  │
│  │ 1. BERTScore (semantic similarity)│  │
│  │    - Compare with OSYM corpus     │  │
│  │    - Score: 0-100                 │  │
│  │                                    │  │
│  │ 2. Bloom Taxonomy Classifier      │  │
│  │    - Verify cognitive level       │  │
│  │    - Match requested level?       │  │
│  │                                    │  │
│  │ 3. OSYM Benchmark Comparator      │  │
│  │    - Structure similarity         │  │
│  │    - Difficulty alignment          │  │
│  │                                    │  │
│  │ 4. Comprehensive Quality Score    │  │
│  │    = (BERTScore * 0.4 +           │  │
│  │       BloomMatch * 0.3 +           │  │
│  │       OSYMSimilarity * 0.3)       │  │
│  └────────────────┬───────────────────┘  │
│                   │ 8. Quality: 85/100    │
└───────────────────┼──────────────────────┘
                    │
                    ▼
              ┌──────────┐
              │ Quality  │
              │ >= 75?   │
              └─────┬────┘
                    │
         ┌──────────┴──────────┐
         │ YES               NO│
         ▼                     ▼
┌─────────────────┐  ┌──────────────────┐
│   Save to DB    │  │ Regenerate       │
│   & Elastic     │  │ (max 3 attempts) │
└────┬────────────┘  └───────┬──────────┘
     │                       │
     │                       └──────► Back to LLM
     │
     │ 9. Save question
     ▼
┌──────────────────────────────────────┐
│         Database                      │
│  INSERT INTO questions (              │
│    question_text,                    │
│    options,                          │
│    correct_answer,                   │
│    subject,                          │
│    difficulty,                       │
│    bloom_level,                      │
│    bertscore,                        │
│    quality_score,                    │
│    source = 'AI_GENERATED',          │
│    generation_method = 'hybrid'      │
│  )                                   │
└───────────────┬──────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│       Elasticsearch                   │
│  Index for full-text search          │
│  - Turkish analyzer                  │
│  - Subject facets                    │
│  - Difficulty range filters          │
└───────────────┬──────────────────────┘
                │
                │ 10. Calculate IRT parameters
                │     (background task)
                ▼
┌──────────────────────────────────────┐
│      IRT Calibration Service          │
│  - Collect response data              │
│  - Estimate discrimination (a)        │
│  - Estimate difficulty (b)            │
│  - Estimate guessing (c)              │
│  - Update question record             │
└───────────────┬──────────────────────┘
                │
                │ 11. Monitor quality
                ▼
┌──────────────────────────────────────┐
│   Production Quality Monitor          │
│  - Track quality metrics              │
│  - Send to Prometheus                 │
│  - Alert if quality drops < 70        │
│  - Daily quality report               │
└───────────────┬──────────────────────┘
                │
                │ 12. Return response
                ▼
┌──────────────────────────────────────┐
│         Frontend                      │
│  Display: "✓ 10 soru başarıyla       │
│            oluşturuldu"              │
│  Show: Quality scores, preview       │
└──────────────────────────────────────┘
```

### 4.5 Öğrenme Yolu Oluşturma (Learning Path Generation Flow)

```
┌──────────────┐
│   Frontend   │
│ LearningPath │
│  Component   │
└──────┬───────┘
       │ 1. POST /api/learning-path
       │    { user_id, target_exam: "TYT",
       │      target_score: 450 }
       ▼
┌──────────────────────────────────────┐
│         API Gateway                   │
└──────┬───────────────────────────────┘
       │ 2. Auth & validate
       ▼
┌──────────────────────────────────────┐
│      Business Logic                   │
│   LearningPathService                 │
└──────┬───────────────────────────────┘
       │ 3. Get user context
       ▼
┌────────────────────────────────────────────────────┐
│               User Profile Assembly                 │
│  ┌──────────────────────────────────────────────┐  │
│  │ 1. Get exam history (last 10 exams)         │  │
│  │ 2. Calculate average performance             │  │
│  │ 3. Identify weak subjects                    │  │
│  │ 4. Get learning style profile                │  │
│  │ 5. Get ZPD parameters                        │  │
│  └──────────────────┬───────────────────────────┘  │
│                     │ 4. User context ready         │
└─────────────────────┼─────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│        Multi-Agent Blackboard Coordination           │
│  ┌────────────────────────────────────────────────┐ │
│  │        Blackboard (Shared Memory)              │ │
│  │  {                                             │ │
│  │    task: "generate_learning_path",            │ │
│  │    user_context: {...},                       │ │
│  │    agent_results: [],                         │ │
│  │    conflicts: []                              │ │
│  │  }                                             │ │
│  └────────────────────┬───────────────────────────┘ │
│                       │ 5. Post task                │
└───────────────────────┼─────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌───────────────┐
│Learning Path │ │Study Buddy  │ │Accessibility  │
│    Agent     │ │   Agent     │ │    Agent      │
└──────┬───────┘ └──────┬──────┘ └───────┬───────┘
       │                │                 │
       │ 6a. Analyze    │ 6b. Recommend   │ 6c. Check
       │     weak       │      study      │     needs
       │     areas      │      strategies │
       │                │                 │
       └────────────────┴─────────┬───────┘
                                  │ 7. Aggregate results
                                  ▼
┌─────────────────────────────────────────────────────┐
│            Blackboard Coordinator                    │
│  1. Collect agent results                           │
│  2. Resolve conflicts (voting, priority)            │
│  3. Create unified learning path                    │
└─────────────────────┬───────────────────────────────┘
                      │ 8. Learning path plan
                      ▼
┌─────────────────────────────────────────────────────┐
│         Content Recommendation Engine                │
│  ┌────────────────────────────────────────────────┐ │
│  │ For each weak subject:                         │ │
│  │                                                │ │
│  │ 1. Search Elasticsearch                        │ │
│  │    - Filter by subject, difficulty             │ │
│  │    - Turkish full-text search                  │ │
│  │                                                │ │
│  │ 2. YouTube API                                 │ │
│  │    - Search educational videos                 │ │
│  │    - Filter: Turkish, subtitles, length        │ │
│  │    - Rank by quality & relevance               │ │
│  │                                                │ │
│  │ 3. EBA TV Integration                          │ │
│  │    - Get MEB-approved content                  │ │
│  │    - Match grade level                         │ │
│  │                                                │ │
│  │ 4. Khan Academy                                │ │
│  │    - Get Turkish resources                     │ │
│  │    - Match curriculum                          │ │
│  │                                                │ │
│  │ 5. Question Bank                               │ │
│  │    - Select practice questions                 │ │
│  │    - IRT-based difficulty matching             │ │
│  └────────────────────┬───────────────────────────┘ │
│                       │ 9. Resources collected       │
└───────────────────────┼─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              RAG Enhancement                         │
│  ┌────────────────────────────────────────────────┐ │
│  │ Query Expansion (3 variants):                  │ │
│  │ - Original query: "trigonometri"              │ │
│  │ - Variant 1: "trigonometri sin cos tan"       │ │
│  │ - Variant 2: "üçgen açı hesaplama"            │ │
│  │ - Variant 3: "sinüs kosinüs tanjant"          │ │
│  │                                                │ │
│  │ Hybrid Search:                                 │ │
│  │ - Semantic search (embeddings, HNSW)           │ │
│  │ - Keyword search (BM25)                        │ │
│  │ - Combine scores (0.7 * semantic + 0.3 * BM25)│ │
│  │                                                │ │
│  │ Cross-Encoder Reranking:                       │ │
│  │ - Rerank top 100 results                       │ │
│  │ - +20% accuracy improvement                    │ │
│  │                                                │ │
│  │ Deduplication:                                 │ │
│  │ - Remove duplicate content                     │ │
│  │ - Cosine similarity threshold: 0.95            │ │
│  └────────────────────┬───────────────────────────┘ │
│                       │ 10. Enhanced resources       │
└───────────────────────┼─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│            FSRS Scheduling                           │
│  ┌────────────────────────────────────────────────┐ │
│  │ For each resource:                             │ │
│  │                                                │ │
│  │ 1. Calculate initial difficulty                │ │
│  │    - Based on subject, user level              │ │
│  │                                                │ │
│  │ 2. Calculate initial stability                 │ │
│  │    - 17 parameters (Turkish-optimized)         │ │
│  │    - Consider: exam anxiety, family pressure   │ │
│  │                                                │ │
│  │ 3. Schedule first review                       │ │
│  │    - Interval = f(stability, difficulty)       │ │
│  │    - Next review date                          │ │
│  │                                                │ │
│  │ 4. Create study schedule                       │ │
│  │    - Distribute over available time            │ │
│  │    - Respect cognitive load limits             │ │
│  │    - Mix subjects (interleaving)               │ │
│  └────────────────────┬───────────────────────────┘ │
│                       │ 11. Schedule ready           │
└───────────────────────┼─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Cache & Save                                 │
│  ┌────────────────────────────────────────────────┐ │
│  │ Redis Cache:                                   │ │
│  │ - Key: learning_path:{user_id}                 │ │
│  │ - TTL: 7 days                                  │ │
│  │ - Value: Complete learning path                │ │
│  │                                                │ │
│  │ Database:                                      │ │
│  │ - INSERT INTO learning_paths (...)             │ │
│  │ - INSERT INTO learning_path_resources (...)    │ │
│  │ - BEGIN TRANSACTION, COMMIT                    │ │
│  └────────────────────┬───────────────────────────┘ │
│                       │ 12. Saved                    │
└───────────────────────┼─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Monitoring                                   │
│  - Metrics: learning_path_generation_counter.inc()  │
│  - Logs: "Learning path generated for user X"       │
│  - Trace: span "generate_learning_path" (5.2s)      │
└─────────────────────┬───────────────────────────────┘
                      │
                      │ 13. Return response
                      ▼
┌─────────────────────────────────────────────────────┐
│         Frontend                                     │
│  1. learningPathStore.setPath(data)                 │
│  2. Display learning path                           │
│  3. Show: Resources, schedule, progress tracking    │
│  4. Enable: Video player, question solver, tracking │
└─────────────────────────────────────────────────────┘
```

---

## 5. BİLEŞEN SORUMLULUKLARI

### 5.1 Frontend Layer Sorumlulukları

**Ana Sorumluluklar:**
1. Kullanıcı arayüzü render etme
2. Kullanıcı etkileşimlerini yakalama
3. Form validasyonu (client-side)
4. State yönetimi (local & global)
5. Routing ve navigasyon
6. API ile iletişim
7. Hata gösterimi
8. Loading states
9. Responsive design
10. Accessibility (a11y)

**Yapmaması Gerekenler:**
- ❌ Business logic
- ❌ Direct database access
- ❌ Sensitive data storage (except JWT token)
- ❌ Server-side validation yerine geçmek
- ❌ Heavy computation

**Bağımlılıklar:**
- ✅ API Gateway (REST API)
- ✅ Browser APIs (LocalStorage, SessionStorage)
- ✅ CDN (static assets)

---

### 5.2 API Gateway Layer Sorumlulukları

**Ana Sorumluluklar:**
1. HTTP istekleri alma
2. Routing (endpoint matching)
3. Authentication (JWT validation)
4. Authorization (RBAC)
5. Input validation (Pydantic)
6. Rate limiting
7. CORS handling
8. Request/response transformation
9. Error handling & formatting
10. API documentation (OpenAPI)

**Yapmaması Gerekenler:**
- ❌ Business logic
- ❌ Direct database queries
- ❌ Heavy computation
- ❌ State yönetimi (stateless olmalı)

**Bağımlılıklar:**
- ✅ Business Logic Layer
- ✅ Core Infrastructure Layer (auth, cache)
- ✅ Monitoring Layer (metrics, logs)

---

### 5.3 Business Logic Layer Sorumlulukları

**Ana Sorumluluklar:**
1. Business rules enforcement
2. Workflow orchestration
3. Domain logic
4. Data validation (business rules)
5. Transaction management
6. Integration coordination
7. Error handling & recovery
8. Caching strategy
9. Event publishing
10. Audit logging

**Yapmaması Gerekenler:**
- ❌ HTTP request handling
- ❌ Direct infrastructure management
- ❌ Frontend concerns (rendering, UI state)

**Bağımlılıklar:**
- ✅ Core Infrastructure Layer
- ✅ AI/ML Layer
- ✅ Algorithm Layer
- ✅ Database Layer
- ✅ External Services Layer

---

### 5.4 Core Infrastructure Layer Sorumlulukları

**Ana Sorumluluklar:**
1. Database connection management
2. Cache management
3. Security enforcement
4. Monitoring & logging
5. Error tracking
6. Distributed tracing
7. Circuit breaking
8. Health checking
9. Configuration management
10. Middleware pipeline

**Yapmaması Gerekenler:**
- ❌ Business logic
- ❌ Domain-specific algorithms
- ❌ API routing

**Bağımlılıklar:**
- ✅ Database Layer
- ✅ Infrastructure Layer (Docker, Redis, PostgreSQL)
- ✅ External Services (Sentry, Jaeger)

---

### 5.5 AI/ML Layer Sorumlulukları

**Ana Sorumluluklar:**
1. LLM integration (GPT-4)
2. Model inference (BERTurk, T5)
3. Embeddings generation
4. Sentiment analysis
5. Question generation
6. Quality evaluation
7. Multi-agent coordination
8. IRT analysis
9. FSRS scheduling
10. Cost optimization

**Yapmaması Gerekenler:**
- ❌ Database direct access (use services)
- ❌ API routing
- ❌ User authentication

**Bağımlılıklar:**
- ✅ External Services (OpenAI API)
- ✅ Algorithm Layer
- ✅ Database Layer (for training data)
- ✅ Core Infrastructure (caching models)

---

### 5.6 Algorithm Layer Sorumlulukları

**Ana Sorumluluklar:**
1. Turkish NLP algorithms
2. Adaptive learning algorithms
3. ZPD calculation
4. Learning style detection
5. Text simplification
6. Morphology analysis
7. Cultural adaptation
8. Difficulty estimation
9. Performance prediction
10. Optimization algorithms

**Yapmaması Gerekenler:**
- ❌ API communication
- ❌ Database operations (return data for services to save)
- ❌ External service calls

**Bağımlılıklar:**
- ✅ AI/ML Layer (for models)
- ✅ Database Layer (for historical data)
- ✅ External Services (Zemberek NLP)

---

### 5.7 Database Layer Sorumlulukları

**Ana Sorumluluklar:**
1. Data persistence
2. Data integrity (constraints)
3. Relationships (foreign keys)
4. Indexing
5. Migrations
6. Query optimization
7. Full-text search
8. Backup & recovery
9. Replication
10. Connection pooling

**Yapmaması Gerekenler:**
- ❌ Business logic (use triggers sparingly)
- ❌ External API calls
- ❌ Heavy computation

**Bağımlılıklar:**
- ✅ Infrastructure Layer (PostgreSQL server)

---

### 5.8 External Services Layer Sorumlulukları

**Ana Sorumluluklar:**
1. API integration (OpenAI, YouTube, etc.)
2. Rate limiting (per service)
3. Error handling & retry
4. Response parsing
5. Cost tracking
6. Fallback strategies
7. Circuit breaking
8. Timeout handling
9. Data transformation
10. Caching responses

**Yapmaması Gerekenler:**
- ❌ Database direct access
- ❌ Business logic
- ❌ User authentication

**Bağımlılıklar:**
- ✅ Core Infrastructure (circuit breaker, cache)
- ✅ Monitoring Layer (track API usage)

---

### 5.9 Monitoring & Observability Layer Sorumlulukları

**Ana Sorumluluklar:**
1. Metrics collection (Prometheus)
2. Log aggregation (Elasticsearch)
3. Distributed tracing (Jaeger)
4. Error tracking (Sentry)
5. Alerting (Prometheus Alertmanager)
6. Dashboards (Grafana)
7. Performance monitoring
8. Cost tracking
9. SLA monitoring
10. Incident management

**Yapmaması Gerekenler:**
- ❌ Application logic
- ❌ Data modification
- ❌ User interaction

**Bağımlılıklar:**
- ✅ All layers (receive metrics/logs/traces)
- ✅ Infrastructure Layer

---

### 5.10 Infrastructure Layer Sorumlulukları

**Ana Sorumluluklar:**
1. Container orchestration (Docker)
2. Database hosting (PostgreSQL)
3. Cache hosting (Redis)
4. Search hosting (Elasticsearch)
5. Load balancing (Nginx)
6. Network configuration
7. Volume management
8. Service discovery
9. Health checks
10. Auto-scaling (Kubernetes)

**Yapmaması Gerekenler:**
- ❌ Application logic
- ❌ Business rules
- ❌ Data transformation

**Bağımlılıklar:**
- ✅ Host machine (Docker host)
- ✅ Network infrastructure

---

## 6. KRİTİK BAĞIMLILIKLAR

### 6.1 Başlatma Sırası (Startup Order)

Bileşenlerin başlatılması MUTLAKA aşağıdaki sırada olmalıdır:

```
1. Infrastructure Layer (Docker containers)
   ├── PostgreSQL ⏱ 10s
   ├── Redis ⏱ 3s
   └── Elasticsearch ⏱ 30s

2. Database Migration (Alembic)
   └── Apply pending migrations ⏱ 5s

3. Core Infrastructure
   ├── Database connection pool ⏱ 2s
   ├── Redis connection ⏱ 1s
   └── Elasticsearch client ⏱ 2s

4. Monitoring Services
   ├── Prometheus metrics ⏱ 1s
   ├── Structured logger ⏱ 1s
   └── Sentry SDK ⏱ 1s

5. Security Services
   ├── JWT manager ⏱ 1s
   └── RBAC system ⏱ 1s

6. AI/ML Services
   ├── LLM client ⏱ 1s
   ├── BERTurk model (lazy load) ⏱ 0s
   └── Multi-agent system ⏱ 2s

7. Business Logic Services
   └── All service singletons ⏱ 2s

8. API Gateway
   ├── Middleware pipeline ⏱ 1s
   ├── Router registration ⏱ 3s
   └── OpenAPI docs ⏱ 1s

9. Frontend (after backend ready)
   └── React app build & serve ⏱ 10s

Total startup time: ~60s
```

### 6.2 Kritik Bağımlılık Zinciri

```
Frontend
  ↓ depends on
API Gateway
  ↓ depends on
Core Infrastructure (Auth)
  ↓ depends on
Database & Redis
  ↓ depends on
Infrastructure Layer

---

Business Logic
  ↓ depends on
AI/ML Layer
  ↓ depends on
External Services (OpenAI)
  ↓ depends on
Internet connectivity

---

All Layers
  ↓ depends on
Monitoring Layer
  ↓ depends on
Infrastructure Layer (Prometheus, Grafana)
```

### 6.3 Circular Dependency Prevention

**YASAK: Circular Dependencies**
```
❌ Frontend → API Gateway → Frontend (WebSocket push)
   Çözüm: WebSocket ayrı endpoint, stateless

❌ Service A → Service B → Service A
   Çözüm: Extract common logic to shared utility

❌ Database Layer → Business Logic → Database Layer
   Çözüm: Repository pattern, clear separation
```

### 6.4 Fallback Stratejileri

**Redis Cache Failure:**
```python
try:
    cached = await redis.get(key)
except RedisConnectionError:
    logger.warning("Redis unavailable, falling back to database")
    cached = None  # Continue without cache
```

**OpenAI API Failure:**
```python
try:
    result = await openai_client.generate()
except OpenAIError:
    # Fallback to template-based generation
    result = await template_generator.generate()
```

**Database Failure:**
```python
try:
    result = await db.execute(query)
except DatabaseError:
    # Return cached data if available
    return await cache.get_last_known_good(key)
```

**Elasticsearch Failure:**
```python
try:
    results = await es.search(query)
except ElasticsearchError:
    # Fallback to PostgreSQL full-text search
    results = await db.execute(text_search_query)
```

---

## 7. SONUÇ

Bu dokümantasyon, KIRO2 platformunun 10 ana bileşen katmanını, aralarındaki ilişkileri, veri akışlarını ve sorumlulukları detaylı olarak açıklamaktadır.

**Önemli Noktalar:**
1. ✅ Katmanlı mimari (Layered Architecture)
2. ✅ Tek yönlü bağımlılıklar (unidirectional)
3. ✅ Separation of Concerns
4. ✅ Mikroservis hazır (loosely coupled)
5. ✅ Comprehensive monitoring
6. ✅ Production-ready
7. ✅ Scalable & maintainable

**Devam Eden Dokümantasyon:**
- [INTEGRATION_CHECKLISTS.md](./INTEGRATION_CHECKLISTS.md) - Her bileşen için detaylı kontrol listeleri

---

**Teknofest 2025 - Eğitim Eylemcisi Kategorisi**
**KIRO2 Platform - Türkiye Üniversite Sınavları Hazırlık Platformu**
