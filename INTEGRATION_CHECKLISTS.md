# KIRO2 Platform - Entegrasyon Kontrol Listeleri

**Teknofest 2025 - Eğitim Eylemcisi Kategorisi**
**Platform:** Türkiye Üniversite Sınavları Hazırlık Platformu
**Tarih:** 17 Kasım 2025

---

## İçindekiler

1. [Frontend Layer Kontrol Listeleri](#1-frontend-layer-kontrol-li̇steleri̇)
2. [API Gateway Layer Kontrol Listeleri](#2-api-gateway-layer-kontrol-li̇steleri̇)
3. [Business Logic Layer Kontrol Listeleri](#3-business-logic-layer-kontrol-li̇steleri̇)
4. [Core Infrastructure Layer Kontrol Listeleri](#4-core-infrastructure-layer-kontrol-li̇steleri̇)
5. [AI/ML Layer Kontrol Listeleri](#5-aiml-layer-kontrol-li̇steleri̇)
6. [Algorithm Layer Kontrol Listeleri](#6-algorithm-layer-kontrol-li̇steleri̇)
7. [Database Layer Kontrol Listeleri](#7-database-layer-kontrol-li̇steleri̇)
8. [External Services Layer Kontrol Listeleri](#8-external-services-layer-kontrol-li̇steleri̇)
9. [Monitoring Layer Kontrol Listeleri](#9-monitoring-layer-kontrol-li̇steleri̇)
10. [Infrastructure Layer Kontrol Listeleri](#10-infrastructure-layer-kontrol-li̇steleri̇)
11. [Bileşenler Arası Entegrasyon Matrisi](#11-bi̇leşenler-arasi-entegrasyon-matri̇si̇)
12. [Kritik Senaryo Kontrolleri](#12-kri̇ti̇k-senaryo-kontrollleri̇)

---

## KONTROL LİSTESİ KULLANIM KILAVUZU

### Semboller
- ✅ **ZORUNLU** - Mutlaka yapılmalı
- ⚠️ **ÖNEMLİ** - Yapılması şiddetle tavsiye edilir
- 📋 **ÖNERILIR** - İyi pratik, yapılması iyi olur
- 🔄 **PERİYODİK** - Düzenli olarak kontrol edilmeli
- 🚨 **KRİTİK** - Production deployment için mutlaka gerekli

### Kontrol Seviyeleri
1. **Pre-Development** - Geliştirme öncesi
2. **Development** - Geliştirme sırasında
3. **Pre-Integration** - Entegrasyon öncesi
4. **Integration** - Entegrasyon sırasında
5. **Pre-Deployment** - Deployment öncesi
6. **Post-Deployment** - Deployment sonrası

---

## 1. FRONTEND LAYER KONTROL LİSTELERİ

### 1.1 API Gateway ile Entegrasyon Kontrolleri

#### ✅ Pre-Development
- [ ] OpenAPI schema export edilmiş mi? (`backend/openapi.json`)
- [ ] TypeScript types generate edilmiş mi? (`frontend/src/types/api.generated.ts`)
- [ ] API base URL environment variable'da tanımlı mı? (`.env`)
- [ ] API versioning stratejisi belirlenmiş mi? (örn: `/api/v1/`)

**Komutlar:**
```bash
# Type generation
cd backend && py export_openapi_schema.py
bash scripts/generate-types.sh

# Verify
ls -lh frontend/src/types/api.generated.ts
```

#### ✅ Development
- [ ] `apiClient.ts` doğru base URL kullanıyor mu?
- [ ] Request interceptor JWT token ekliyor mu?
- [ ] Response interceptor error handling yapıyor mu?
- [ ] Timeout ayarları uygun mu? (default 30s)
- [ ] Retry logic var mı? (failed requests için)

**Kontrol:**
```typescript
// frontend/src/services/apiClient.ts

// ✅ Base URL check
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
});

// ✅ Auth interceptor check
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ✅ Error interceptor check
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      await refreshToken();
      return apiClient.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

#### ✅ Integration
- [ ] CORS ayarları backend'de doğru mu?
- [ ] Preflight requests (OPTIONS) çalışıyor mu?
- [ ] Response Content-Type header'ları doğru mu? (`application/json`)
- [ ] Error response formatı standart mı?

**Test:**
```bash
# CORS test
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Authorization" \
     -X OPTIONS \
     http://localhost:8000/api/auth/login

# Response format test
curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"wrong"}' \
     | jq .
```

#### 🚨 Pre-Deployment
- [ ] Production API URL doğru mu? (environment variable)
- [ ] API rate limiting frontend'de handle ediliyor mu?
- [ ] Network error retry logic çalışıyor mu?
- [ ] Offline mode fallback var mı?

---

### 1.2 State Management Kontrolleri

#### ✅ Development
- [ ] Zustand store'lar doğru yapılandırılmış mı?
- [ ] State persistence stratejisi belirlenmiş mi? (localStorage)
- [ ] Sensitive data localStorage'a kaydedilmiyor mu? (password, etc.)
- [ ] State hydration çalışıyor mu? (page reload)

**Kontrol:**
```typescript
// frontend/src/store/authStore.ts

// ✅ Store structure check
interface AuthState {
  user: User | null;
  token: string | null;  // ⚠️ JWT token - OK to store
  isAuthenticated: boolean;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
}

// ✅ Persistence check
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // ... state
    }),
    {
      name: 'auth-storage',
      // ⚠️ Don't persist sensitive data
      partialize: (state) => ({
        token: state.token,
        user: {
          id: state.user?.id,
          email: state.user?.email,
          // ❌ Don't persist: password, credit_card, etc.
        }
      })
    }
  )
);
```

#### 🔄 Periodic
- [ ] localStorage temizleniyor mu? (logout, expired token)
- [ ] State size reasonable mu? (<5MB)
- [ ] Memory leaks var mı? (React DevTools Profiler)

---

### 1.3 Component Architecture Kontrolleri

#### ✅ Development
- [ ] Component hierarchy düzgün mü? (Container → Presentational)
- [ ] Props drilling aşırı mı? (Context ya da Zustand kullan)
- [ ] Reusable components extracted mı?
- [ ] Component naming convention tutarlı mı?

**Best Practice:**
```
components/
├── Common/           # Shared components
│   ├── Button.tsx
│   ├── Input.tsx
│   └── Card.tsx
├── Exam/             # Feature-specific
│   ├── ExamList.tsx        (Container)
│   ├── ExamCard.tsx        (Presentational)
│   └── ExamTimer.tsx       (Presentational)
└── Layout/
    ├── Header.tsx
    └── Sidebar.tsx
```

#### ⚠️ Performance
- [ ] Large lists virtualized mı? (react-window)
- [ ] Images lazy loaded mı?
- [ ] Code splitting yapılmış mı? (React.lazy)
- [ ] Memoization kullanılıyor mu? (useMemo, useCallback, React.memo)

**Check:**
```typescript
// ✅ Virtualization for large lists
import { FixedSizeList } from 'react-window';

const QuestionList = ({ questions }: { questions: Question[] }) => (
  <FixedSizeList
    height={600}
    itemCount={questions.length}
    itemSize={100}
    width="100%"
  >
    {({ index, style }) => (
      <div style={style}>
        <QuestionCard question={questions[index]} />
      </div>
    )}
  </FixedSizeList>
);

// ✅ Code splitting
const ExamComponent = React.lazy(() => import('./components/Exam/ExamInterface'));

// ✅ Memoization
const ExpensiveComponent = React.memo(({ data }: { data: Data }) => {
  const processed = useMemo(() => processData(data), [data]);
  return <div>{processed}</div>;
});
```

---

### 1.4 Accessibility (a11y) Kontrolleri

#### ✅ Development
- [ ] Semantic HTML kullanılıyor mu? (`<button>`, `<nav>`, `<main>`)
- [ ] ARIA attributes doğru mu? (`aria-label`, `aria-describedby`)
- [ ] Keyboard navigation çalışıyor mu? (Tab, Enter, Escape)
- [ ] Focus management doğru mu? (modal açıldığında, kapatıldığında)
- [ ] Color contrast yeterli mi? (WCAG AA: 4.5:1)

**Test:**
```bash
# Automated a11y testing
npm run test:a11y

# Manual test
# 1. Tab tuşuyla tüm elementi dolaşabilir misiniz?
# 2. Screen reader (NVDA, JAWS) ile kullanılabilir mi?
# 3. Keyboard-only navigation çalışıyor mu?
```

**Code Example:**
```typescript
// ✅ Accessible button
<button
  aria-label="Sınavı başlat"
  aria-describedby="exam-description"
  onClick={startExam}
  disabled={isLoading}
>
  {isLoading ? <Spinner aria-hidden="true" /> : null}
  Başlat
</button>

// ✅ Accessible form
<form onSubmit={handleSubmit} aria-labelledby="login-form-title">
  <h2 id="login-form-title">Giriş Yap</h2>
  <Input
    id="email"
    type="email"
    label="E-posta"
    error={errors.email}
    aria-invalid={!!errors.email}
    aria-describedby={errors.email ? "email-error" : undefined}
  />
  {errors.email && <span id="email-error" role="alert">{errors.email}</span>}
</form>
```

#### ✅ Integration
- [ ] WCAG validator testi geçiyor mu? (jest-axe)
- [ ] Dyslexia support çalışıyor mu? (Bionic reading)
- [ ] ADHD support çalışıyor mu? (Focus mode)
- [ ] Screen reader test yapıldı mı?

---

### 1.5 Error Handling Kontrolleri

#### ✅ Development
- [ ] Global error boundary var mı?
- [ ] API error handling uniform mu?
- [ ] User-friendly error messages gösteriliyor mu?
- [ ] Error logging yapılıyor mu? (Sentry)

**Code Example:**
```typescript
// ✅ Error boundary
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to Sentry
    Sentry.captureException(error, { extra: errorInfo });

    // Show fallback UI
    this.setState({ hasError: true });
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}

// ✅ API error handling
const handleApiError = (error: AxiosError) => {
  if (error.response) {
    // Server responded with error
    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 400:
        toast.error(data.message || 'Geçersiz istek');
        break;
      case 401:
        toast.error('Oturum süreniz doldu');
        // Redirect to login
        router.push('/login');
        break;
      case 403:
        toast.error('Bu işlem için yetkiniz yok');
        break;
      case 404:
        toast.error('Aradığınız kaynak bulunamadı');
        break;
      case 500:
        toast.error('Sunucu hatası. Lütfen daha sonra tekrar deneyin');
        Sentry.captureException(error);
        break;
      default:
        toast.error('Bir hata oluştu');
    }
  } else if (error.request) {
    // Request made but no response
    toast.error('Sunucuya ulaşılamıyor. İnternet bağlantınızı kontrol edin');
  } else {
    // Something else happened
    toast.error('Beklenmeyen bir hata oluştu');
    Sentry.captureException(error);
  }
};
```

---

### 1.6 Testing Kontrolleri

#### ✅ Development
- [ ] Unit tests yazıldı mı? (components, hooks, utilities)
- [ ] Integration tests yazıldı mı? (user flows)
- [ ] E2E tests yazıldı mı? (critical paths)
- [ ] Test coverage yeterli mi? (>80% critical code)

**Test Structure:**
```
tests/
├── unit/
│   ├── components/
│   │   ├── ExamCard.test.tsx
│   │   └── QuestionDisplay.test.tsx
│   ├── hooks/
│   │   ├── useAuth.test.ts
│   │   └── useExamTimer.test.ts
│   └── utils/
│       └── apiHelpers.test.ts
├── integration/
│   ├── auth-flow.test.tsx
│   ├── exam-flow.test.tsx
│   └── learning-path-flow.test.tsx
└── e2e/
    ├── login.spec.ts
    ├── take-exam.spec.ts
    └── view-results.spec.ts
```

**Test Commands:**
```bash
# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests (Playwright)
npm run test:e2e

# Coverage
npm run test:coverage

# Accessibility tests
npm run test:a11y
```

---

## 2. API GATEWAY LAYER KONTROL LİSTELERİ

### 2.1 Authentication & Authorization Kontrolleri

#### ✅ Pre-Development
- [ ] JWT secret key güvenli mi? (256-bit, random)
- [ ] Token expiration süresi uygun mu? (15 min access, 7 day refresh)
- [ ] Password hashing algorithm güvenli mi? (bcrypt, 12 rounds)
- [ ] 2FA implementation doğru mu? (TOTP, Sprint 4)

**Kontrol:**
```python
# backend/core/config.py

# ✅ JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Must be from env
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ⚠️ Check JWT secret strength
assert len(JWT_SECRET_KEY) >= 32, "JWT secret too short"

# ✅ Password hashing
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# bcrypt rounds: 12 (default, good balance)
```

#### ✅ Development
- [ ] Token validation middleware çalışıyor mu?
- [ ] Token refresh endpoint güvenli mi?
- [ ] RBAC (Role-Based Access Control) çalışıyor mu?
- [ ] Permission checks her endpoint'te yapılıyor mu?

**Test:**
```bash
# Test token validation
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r .access_token)

# Use token
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/sinav/list

# Test expired token (should return 401)
curl -H "Authorization: Bearer expired_token" \
     http://localhost:8000/api/sinav/list

# Test wrong role (student trying to access admin endpoint)
curl -H "Authorization: Bearer $STUDENT_TOKEN" \
     http://localhost:8000/api/admin/users
# Expected: 403 Forbidden
```

#### ⚠️ Security
- [ ] Brute force protection aktif mi? (rate limiting on login)
- [ ] Account lockout çalışıyor mu? (5 failed attempts)
- [ ] Password reset secure mı? (token-based, time-limited)
- [ ] Session invalidation çalışıyor mu? (logout, password change)

**Kontrol:**
```python
# backend/core/auth_rate_limiting.py

# ✅ Brute force protection
@router.post("/login")
@limiter.limit("5/minute")  # Max 5 attempts per minute
async def login(credentials: LoginRequest):
    # ...
    pass

# ✅ Account lockout
async def check_lockout(email: str):
    attempts = await redis.get(f"login_attempts:{email}")
    if attempts and int(attempts) >= 5:
        raise HTTPException(
            status_code=429,
            detail="Hesabınız geçici olarak kilitlendi. 15 dakika sonra tekrar deneyin"
        )
```

---

### 2.2 Input Validation Kontrolleri

#### ✅ Development
- [ ] Pydantic models tüm endpoint'lerde kullanılıyor mu?
- [ ] Validation rules yeterli mi? (email format, string length, etc.)
- [ ] Custom validators tanımlanmış mı? (Turkish phone, TC kimlik no)
- [ ] Error messages user-friendly mı?

**Kontrol:**
```python
# backend/api/auth.py

from pydantic import BaseModel, EmailStr, constr, validator

# ✅ Input validation with Pydantic
class UserRegistration(BaseModel):
    email: EmailStr  # Automatic email validation
    ad_soyad: constr(min_length=2, max_length=100)  # Length constraint
    sifre: constr(min_length=8, max_length=128)  # Password length
    rol: UserRole  # Enum validation

    @validator('sifre')
    def validate_password_strength(cls, v):
        """Password must contain uppercase, lowercase, digit"""
        if not any(c.isupper() for c in v):
            raise ValueError('Şifre en az bir büyük harf içermelidir')
        if not any(c.islower() for c in v):
            raise ValueError('Şifre en az bir küçük harf içermelidir')
        if not any(c.isdigit() for c in v):
            raise ValueError('Şifre en az bir rakam içermelidir')
        return v

    @validator('ad_soyad')
    def validate_turkish_characters(cls, v):
        """Allow Turkish characters"""
        allowed = set('abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ ')
        if not all(c in allowed for c in v):
            raise ValueError('Geçersiz karakter')
        return v

# ✅ Usage in endpoint
@router.post("/register")
async def register(user_data: UserRegistration):
    # Pydantic automatically validates input
    # If validation fails, returns 422 Unprocessable Entity
    pass
```

#### 🚨 Security Validation
- [ ] SQL injection koruması var mı? (ORM kullanımı)
- [ ] XSS koruması var mı? (input sanitization)
- [ ] File upload validation var mı? (type, size, content)
- [ ] Max request size sınırı var mı? (10MB)

**Kontrol:**
```python
# backend/core/security_middleware.py

from fastapi import UploadFile
import bleach

# ✅ XSS protection
def sanitize_html(content: str) -> str:
    return bleach.clean(
        content,
        tags=['p', 'b', 'i', 'u', 'a', 'ul', 'ol', 'li'],
        attributes={'a': ['href', 'title']},
        strip=True
    )

# ✅ File upload validation
async def validate_file_upload(file: UploadFile):
    # Check size
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, "Dosya boyutu çok büyük (max 10MB)")

    # Check type
    allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Geçersiz dosya tipi: {file.content_type}")

    # Check magic bytes (actual file type)
    import magic
    actual_type = magic.from_buffer(contents, mime=True)
    if actual_type not in allowed_types:
        raise HTTPException(400, "Dosya içeriği geçersiz")

    return contents
```

---

### 2.3 Rate Limiting Kontrolleri

#### ✅ Development
- [ ] Global rate limiting aktif mi?
- [ ] Endpoint-specific rate limiting var mı?
- [ ] User-specific rate limiting çalışıyor mu?
- [ ] Rate limit exceeded response doğru mu? (429, Retry-After header)

**Kontrol:**
```python
# backend/core/advanced_rate_limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)

# ✅ Global rate limiting
app.state.limiter = limiter

# ✅ Endpoint-specific limits
@router.get("/questions")
@limiter.limit("100/minute")  # Standard endpoints
async def list_questions():
    pass

@router.post("/question-generation")
@limiter.limit("10/minute")  # Expensive operations
async def generate_question():
    pass

# ✅ User-specific limits (premium vs free)
@router.get("/api/exam/start")
async def start_exam(user: User = Depends(get_current_user)):
    if user.subscription == "free":
        # Max 10 exams per day for free users
        key = f"exam_count:{user.id}:{datetime.now().date()}"
        count = await redis.incr(key)
        await redis.expire(key, 86400)  # 24 hours
        if count > 10:
            raise HTTPException(429, "Günlük sınava ulaştınız. Premium'a geçin")
    # Premium users: unlimited
```

#### 🔄 Monitoring
- [ ] Rate limit metrics Prometheus'a gönderiliyor mu?
- [ ] Rate limit violations log'lanıyor mu?
- [ ] DDoS saldırıları tespit ediliyor mu?

**Test:**
```bash
# Test rate limiting
for i in {1..150}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/questions
done
# First 100: 200
# Next 50: 429 (Too Many Requests)

# Check response headers
curl -I http://localhost:8000/api/questions
# Should include:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 95
# X-RateLimit-Reset: 1635789600
```

---

### 2.4 Error Response Kontrolleri

#### ✅ Development
- [ ] Error response formatı standart mı?
- [ ] HTTP status codes doğru kullanılıyor mu?
- [ ] Error messages user-friendly mi? (Türkçe)
- [ ] Error details production'da gizleniyor mu? (stack trace)

**Standard Error Format:**
```python
# backend/core/exception_handlers.py

from fastapi import Request
from fastapi.responses import JSONResponse

class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str           # Error type (e.g., "VALIDATION_ERROR")
    message: str         # User-friendly message (Turkish)
    details: Optional[Dict] = None  # Field-level errors (dev only)
    request_id: str      # For tracking
    timestamp: datetime

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="Gönderilen veri geçersiz",
            details=exc.errors() if settings.ENVIRONMENT == "development" else None,
            request_id=request.state.request_id,
            timestamp=datetime.utcnow()
        ).dict()
    )

# ✅ HTTP status codes
# 200: Success
# 201: Created
# 204: No Content (successful delete)
# 400: Bad Request (client error)
# 401: Unauthorized (not authenticated)
# 403: Forbidden (not authorized)
# 404: Not Found
# 422: Unprocessable Entity (validation error)
# 429: Too Many Requests (rate limit)
# 500: Internal Server Error
# 503: Service Unavailable (maintenance)
```

---

### 2.5 CORS Kontrolleri

#### ✅ Pre-Deployment
- [ ] CORS origins environment-based mı?
- [ ] Production origins doğru mu?
- [ ] Credentials support gerekli mi? (allow_credentials=True)
- [ ] Preflight caching yapılıyor mu? (max_age)

**Kontrol:**
```python
# backend/main.py

from fastapi.middleware.cors import CORSMiddleware

# ✅ Environment-based CORS
CORS_ORIGINS = {
    "development": [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ],
    "staging": [
        "https://staging.kiro2.com",
    ],
    "production": [
        "https://kiro2.com",
        "https://www.kiro2.com",
    ]
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS[settings.ENVIRONMENT],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)
```

**Test:**
```bash
# Test CORS preflight
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Authorization, Content-Type" \
     -X OPTIONS \
     http://localhost:8000/api/auth/login

# Expected response headers:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: POST, GET, PUT, DELETE, PATCH
# Access-Control-Allow-Headers: Authorization, Content-Type
# Access-Control-Max-Age: 3600
```

---

### 2.6 API Documentation Kontrolleri

#### ✅ Development
- [ ] OpenAPI schema güncel mi?
- [ ] Endpoint descriptions yazılmış mı? (docstrings)
- [ ] Request/response examples var mı?
- [ ] Authentication requirements belirtilmiş mi?

**Kontrol:**
```python
# backend/api/sinav.py

@router.post(
    "/start",
    response_model=ExamResponse,
    status_code=201,
    summary="Sınav başlat",
    description="""
    Yeni bir sınav oturumu başlatır.

    **Gereksinimler:**
    - Kullanıcı kimlik doğrulaması (JWT token)
    - Aktif bir sınav oturumu olmamalı

    **İşlem adımları:**
    1. Kullanıcı profili al
    2. IRT-based soru seçimi yap
    3. Sınav oturumu oluştur
    4. Cache'e kaydet

    **Sınırlamalar:**
    - Ücretsiz kullanıcılar: 10 sınav/gün
    - Premium kullanıcılar: Sınırsız
    """,
    responses={
        201: {
            "description": "Sınav başarıyla oluşturuldu",
            "content": {
                "application/json": {
                    "example": {
                        "exam_id": "uuid",
                        "exam_type": "TYT",
                        "questions": [...],
                        "started_at": "2025-11-17T10:00:00Z",
                        "duration_minutes": 180
                    }
                }
            }
        },
        400: {"description": "Aktif sınav mevcut"},
        401: {"description": "Kimlik doğrulaması gerekli"},
        429: {"description": "Sınav limitine ulaşıldı"}
    }
)
async def start_exam(
    exam_data: ExamStartRequest,
    user: User = Depends(get_current_authenticated_user)
):
    """Sınav başlatma endpoint'i"""
    pass
```

**Access Documentation:**
```bash
# OpenAPI schema
curl http://localhost:8000/openapi.json | jq .

# Swagger UI
open http://localhost:8000/docs

# ReDoc
open http://localhost:8000/redoc
```

---

## 3. BUSINESS LOGIC LAYER KONTROL LİSTELERİ

### 3.1 Service Design Kontrolleri

#### ✅ Pre-Development
- [ ] Service responsibilities tanımlı mı? (Single Responsibility)
- [ ] Service interfaces belirlenmiş mi?
- [ ] Dependencies açık mı? (Dependency Injection)
- [ ] Transaction boundaries tanımlı mı?

**Service Pattern:**
```python
# backend/services/base_service.py

from typing import TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

T = TypeVar('T')

class BaseService(Generic[T]):
    """Base service with common functionality"""

    def __init__(self, db: AsyncSession, cache: Redis):
        self.db = db
        self.cache = cache
        self.logger = structlog.get_logger(self.__class__.__name__)

    async def _cache_get(self, key: str) -> Optional[T]:
        """Get from cache"""
        try:
            cached = await self.cache.get(key)
            if cached:
                self.logger.debug("cache_hit", key=key)
                return json.loads(cached)
            self.logger.debug("cache_miss", key=key)
            return None
        except Exception as e:
            self.logger.warning("cache_error", error=str(e))
            return None

    async def _cache_set(self, key: str, value: T, ttl: int = 3600):
        """Set to cache"""
        try:
            await self.cache.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
        except Exception as e:
            self.logger.warning("cache_set_error", error=str(e))

    async def _cache_delete(self, key: str):
        """Delete from cache"""
        try:
            await self.cache.delete(key)
        except Exception as e:
            self.logger.warning("cache_delete_error", error=str(e))
```

#### ✅ Development
- [ ] Service methods idempotent mi? (aynı işlem tekrar çalıştırılabilir)
- [ ] Error handling comprehensive mi?
- [ ] Logging yeterli mi? (info, warning, error levels)
- [ ] Metrics tracked mı? (operation count, duration)

**Example Service:**
```python
# backend/services/sinav_motoru_service.py

class SinavMotoruService(BaseService[Exam]):
    """Exam engine service"""

    def __init__(
        self,
        db: AsyncSession,
        cache: Redis,
        irt_service: IRTService,
        question_selector: QuestionSelector
    ):
        super().__init__(db, cache)
        self.irt_service = irt_service
        self.question_selector = question_selector

    async def create_exam_session(
        self,
        user_id: UUID,
        exam_type: ExamType
    ) -> ExamResponse:
        """
        Create a new exam session

        ✅ Idempotent: If user has active exam, return it
        ✅ Error handling: All exceptions caught and logged
        ✅ Logging: All steps logged
        ✅ Metrics: Tracked with Prometheus
        """
        # Metrics
        exam_creation_counter.labels(exam_type=exam_type).inc()

        with exam_creation_duration.labels(exam_type=exam_type).time():
            try:
                # Log start
                self.logger.info(
                    "creating_exam_session",
                    user_id=str(user_id),
                    exam_type=exam_type
                )

                # Check cache (idempotency)
                cache_key = f"active_exam:{user_id}"
                cached_exam = await self._cache_get(cache_key)
                if cached_exam:
                    self.logger.info("returning_cached_exam", user_id=str(user_id))
                    return ExamResponse(**cached_exam)

                # Check database for active exam
                active_exam = await self._get_active_exam(user_id)
                if active_exam:
                    self.logger.info("returning_active_exam", exam_id=str(active_exam.id))
                    result = ExamResponse.from_orm(active_exam)
                    await self._cache_set(cache_key, result.dict())
                    return result

                # Get user context
                user_context = await self._get_user_context(user_id)

                # Select questions (IRT-based)
                questions = await self.question_selector.select_questions(
                    exam_type=exam_type,
                    user_ability=user_context.estimated_ability,
                    count=40 if exam_type == ExamType.TYT else 30
                )

                # Create exam in database
                exam = await self._create_exam_record(
                    user_id=user_id,
                    exam_type=exam_type,
                    questions=questions
                )

                # Cache result
                result = ExamResponse.from_orm(exam)
                await self._cache_set(cache_key, result.dict(), ttl=14400)  # 4 hours

                # Log success
                self.logger.info(
                    "exam_session_created",
                    exam_id=str(exam.id),
                    question_count=len(questions)
                )

                return result

            except DatabaseError as e:
                self.logger.error("database_error", error=str(e))
                raise ServiceException("Veritabanı hatası") from e

            except QuestionSelectionError as e:
                self.logger.error("question_selection_error", error=str(e))
                raise ServiceException("Soru seçimi başarısız") from e

            except Exception as e:
                self.logger.error("unexpected_error", error=str(e), exc_info=True)
                Sentry.capture_exception(e)
                raise ServiceException("Beklenmeyen hata") from e
```

---

### 3.2 Transaction Management Kontrolleri

#### ✅ Development
- [ ] Transaction boundaries açık mı?
- [ ] Rollback stratejisi tanımlı mı?
- [ ] Nested transactions handle ediliyor mu?
- [ ] Long-running transactions optimize edilmiş mi?

**Transaction Pattern:**
```python
# backend/services/exam_service.py

async def submit_exam(self, exam_id: UUID) -> ExamResults:
    """
    Submit exam and calculate results

    ✅ Transaction boundary: All or nothing
    ✅ Rollback: Automatic on exception
    ✅ Isolation: REPEATABLE READ
    """
    async with self.db.begin():  # Start transaction
        try:
            # 1. Get exam (locks row)
            exam = await self.db.execute(
                select(Exam)
                .where(Exam.id == exam_id)
                .with_for_update()  # Row lock
            )
            exam = exam.scalar_one_or_none()

            if not exam:
                raise ExamNotFound()

            # 2. Get all answers
            answers = await self.db.execute(
                select(Answer).where(Answer.exam_id == exam_id)
            )
            answers = answers.scalars().all()

            # 3. Calculate scores
            scores = await self._calculate_scores(answers)

            # 4. Estimate ability (IRT)
            ability = await self.irt_service.estimate_ability(answers)

            # 5. Update exam record
            exam.finished_at = datetime.utcnow()
            exam.total_score = scores.total
            exam.net_score = scores.net
            exam.estimated_ability = ability

            # 6. Create performance record
            performance = ExamPerformance(
                exam_id=exam_id,
                scores=scores.dict(),
                weak_subjects=await self._identify_weak_subjects(answers),
                recommendations=await self._generate_recommendations(answers)
            )
            self.db.add(performance)

            # 7. Invalidate cache
            await self._cache_delete(f"active_exam:{exam.user_id}")

            # Commit happens automatically when exiting context

            return ExamResults.from_exam(exam, performance)

        except Exception as e:
            # Rollback happens automatically
            self.logger.error("exam_submission_failed", error=str(e))
            raise
```

#### ⚠️ Performance
- [ ] Batch operations kullanılıyor mu? (bulk insert/update)
- [ ] N+1 queries önleniyor mu? (eager loading)
- [ ] Index'ler kullanılıyor mu?
- [ ] Query optimization yapılmış mı?

**Optimization Example:**
```python
# ❌ BAD: N+1 query problem
async def get_exams_with_questions(user_id: UUID):
    exams = await db.execute(
        select(Exam).where(Exam.user_id == user_id)
    )
    exams = exams.scalars().all()

    for exam in exams:
        # This makes a separate query for each exam!
        questions = await db.execute(
            select(ExamQuestion).where(ExamQuestion.exam_id == exam.id)
        )
        exam.questions = questions.scalars().all()

    return exams

# ✅ GOOD: Eager loading
async def get_exams_with_questions(user_id: UUID):
    exams = await db.execute(
        select(Exam)
        .where(Exam.user_id == user_id)
        .options(joinedload(Exam.questions))  # Eager load
    )
    return exams.scalars().all()

# ✅ GOOD: Batch insert
async def save_answers(answers: List[Answer]):
    # Single query for all answers
    self.db.add_all(answers)
    await self.db.commit()
```

---

### 3.3 Caching Strategy Kontrolleri

#### ✅ Development
- [ ] Cache keys standardize mi? (namespace:entity:id)
- [ ] TTL values reasonable mi?
- [ ] Cache invalidation stratejisi var mı?
- [ ] Cache stampede koruması var mı?

**Caching Patterns:**
```python
# backend/services/learning_path_service.py

class LearningPathService(BaseService):

    async def get_learning_path(self, user_id: UUID) -> LearningPath:
        """
        Get learning path with multi-layer caching

        ✅ L1 Cache: In-memory LRU (100 entries, 5 min)
        ✅ L2 Cache: Redis (7 days)
        ✅ L3 Cache: Database
        """
        cache_key = f"learning_path:{user_id}"

        # L1: In-memory cache
        if cached := self._memory_cache.get(cache_key):
            return cached

        # L2: Redis cache
        if cached := await self._cache_get(cache_key):
            self._memory_cache.set(cache_key, cached, ttl=300)  # 5 min
            return cached

        # Cache miss: Generate new path (expensive operation)
        # Use distributed lock to prevent stampede
        async with self._distributed_lock(f"lock:{cache_key}"):
            # Double-check after acquiring lock
            if cached := await self._cache_get(cache_key):
                return cached

            # Generate learning path
            path = await self._generate_learning_path(user_id)

            # Cache in L1 and L2
            self._memory_cache.set(cache_key, path, ttl=300)
            await self._cache_set(cache_key, path, ttl=604800)  # 7 days

            return path

    async def _distributed_lock(self, lock_key: str):
        """Distributed lock using Redis"""
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def lock():
            # Acquire lock
            acquired = await self.cache.set(
                lock_key,
                "1",
                ex=30,  # Expire after 30s
                nx=True  # Only set if not exists
            )

            if not acquired:
                # Wait for lock to be released
                for _ in range(30):  # Max 3s wait
                    await asyncio.sleep(0.1)
                    if not await self.cache.exists(lock_key):
                        break
                else:
                    raise LockTimeoutError()

            try:
                yield
            finally:
                # Release lock
                await self.cache.delete(lock_key)

        return lock()

    # ✅ Cache invalidation
    async def update_learning_path(self, user_id: UUID, updates: dict):
        """Update learning path and invalidate cache"""
        # Update in database
        await self._update_learning_path_db(user_id, updates)

        # Invalidate all cache layers
        cache_key = f"learning_path:{user_id}"
        self._memory_cache.delete(cache_key)
        await self._cache_delete(cache_key)
```

---

## 4. CORE INFRASTRUCTURE LAYER KONTROL LİSTELERİ

### 4.1 Database Configuration Kontrolleri

#### 🚨 Pre-Deployment
- [ ] Connection pool size uygun mu? (50 pool, 100 max overflow)
- [ ] Connection timeout ayarları doğru mu?
- [ ] SSL/TLS kullanılıyor mu? (production)
- [ ] Database credentials güvenli mi? (environment variables)

**Kontrol:**
```python
# backend/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ✅ Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# ⚠️ SSL mode for production
if settings.ENVIRONMENT == "production":
    DATABASE_URL += "?sslmode=require"

# ✅ Connection pool configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,  # SQL logging
    pool_size=50,         # Base connections
    max_overflow=100,     # Additional connections
    pool_timeout=30,      # Wait 30s for connection
    pool_recycle=3600,    # Recycle connections after 1h
    pool_pre_ping=True,   # Check connection before use
)

# ✅ Session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

**Test:**
```bash
# Test database connection
python -c "
from backend.core.database import engine
import asyncio

async def test():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT version()')
        print(result.scalar())

asyncio.run(test())
"

# Monitor connections
psql -U kiro2_user -d kiro2_db -c "
SELECT
    count(*) as total_connections,
    state,
    wait_event_type
FROM pg_stat_activity
WHERE datname = 'kiro2_db'
GROUP BY state, wait_event_type;
"
```

---

### 4.2 Redis Configuration Kontrolleri

#### ✅ Development
- [ ] Redis persistence ayarları doğru mu? (AOF + RDB)
- [ ] Max memory policy tanımlı mı? (allkeys-lru)
- [ ] Connection pool yapılandırılmış mı?
- [ ] Reconnection logic var mı?

**Kontrol:**
```python
# backend/core/cache.py

from redis.asyncio import Redis, ConnectionPool

# ✅ Connection pool
pool = ConnectionPool.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    max_connections=50,
    socket_keepalive=True,
    socket_keepalive_options={
        socket.TCP_KEEPIDLE: 10,
        socket.TCP_KEEPINTVL: 10,
        socket.TCP_KEEPCNT: 3
    },
    retry_on_timeout=True,
    socket_connect_timeout=5,
    health_check_interval=30
)

redis_client = Redis(connection_pool=pool, decode_responses=True)

# ✅ Fallback mode
class CacheManager:
    def __init__(self):
        self.redis = redis_client
        self.fallback_mode = False

    async def get(self, key: str):
        if self.fallback_mode:
            return None

        try:
            return await self.redis.get(key)
        except RedisConnectionError:
            self.fallback_mode = True
            logger.warning("Redis unavailable, switching to fallback mode")
            return None

    async def health_check(self):
        """Periodic health check to restore from fallback"""
        if not self.fallback_mode:
            return

        try:
            await self.redis.ping()
            self.fallback_mode = False
            logger.info("Redis connection restored")
        except:
            pass  # Still in fallback mode
```

**Redis Configuration File:**
```conf
# redis.conf

# ✅ Persistence
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000

# ✅ Memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# ✅ Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300

# ✅ Security
requirepass ${REDIS_PASSWORD}
```

---

### 4.3 Security Middleware Kontrolleri

#### 🚨 Security
- [ ] JWT validation çalışıyor mu?
- [ ] Rate limiting aktif mi?
- [ ] Input sanitization yapılıyor mu?
- [ ] CSRF protection var mı?
- [ ] SQL injection koruması var mı?
- [ ] XSS koruması var mı?

**Security Checklist:**
```python
# backend/core/security_middleware.py

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""

    async def dispatch(self, request: Request, call_next):
        # ✅ 1. Request size limit
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large"}
            )

        # ✅ 2. Bot detection
        user_agent = request.headers.get('user-agent', '').lower()
        suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']
        if any(agent in user_agent for agent in suspicious_agents):
            if not self._is_whitelisted_bot(user_agent):
                return JSONResponse(
                    status_code=403,
                    content={"error": "Bot access not allowed"}
                )

        # ✅ 3. IP filtering
        client_ip = self._get_client_ip(request)
        if await self._is_blacklisted(client_ip):
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied"}
            )

        # ✅ 4. JWT validation (for protected routes)
        if request.url.path.startswith('/api/') and \
           request.url.path not in ['/api/auth/login', '/api/auth/register']:
            token = request.headers.get('authorization', '').replace('Bearer ', '')
            if not token:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required"}
                )

            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
                request.state.user_id = payload['sub']
            except JWTError:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid token"}
                )

        # ✅ 5. CSRF protection (for state-changing operations)
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            csrf_token = request.headers.get('X-CSRF-Token')
            session_csrf = request.cookies.get('csrf_token')
            if csrf_token != session_csrf:
                return JSONResponse(
                    status_code=403,
                    content={"error": "CSRF token invalid"}
                )

        # ✅ 6. Security headers
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"

        return response
```

---

### 4.4 Monitoring Configuration Kontrolleri

#### ✅ Development
- [ ] Prometheus metrics export ediliyor mu?
- [ ] Grafana dashboards yapılandırılmış mı?
- [ ] Alert rules tanımlı mı?
- [ ] Log aggregation çalışıyor mu?

**Prometheus Metrics:**
```python
# backend/core/application_metrics.py

from prometheus_client import Counter, Histogram, Gauge, Info

# ✅ HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# ✅ Business metrics
active_exams_gauge = Gauge(
    'active_exams_total',
    'Number of currently active exams'
)

question_generation_total = Counter(
    'question_generation_total',
    'Total question generation requests',
    ['subject', 'difficulty', 'status']
)

# ✅ Infrastructure metrics
db_connections_gauge = Gauge(
    'db_connections_total',
    'Number of database connections',
    ['state']  # 'idle', 'active', 'waiting'
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'status']  # operation: get/set/delete, status: hit/miss/error
)

# ✅ Application info
app_info = Info(
    'kiro2_app_info',
    'Application information'
)
app_info.info({
    'version': settings.VERSION,
    'environment': settings.ENVIRONMENT,
    'python_version': platform.python_version(),
})
```

**Prometheus Configuration:**
```yaml
# monitoring/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - "alerts/*.yml"

scrape_configs:
  # Backend
  - job_name: 'kiro2-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # System
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Containers
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

**Alert Rules:**
```yaml
# monitoring/prometheus/alerts/kiro2_alerts.yml

groups:
  - name: kiro2_backend
    interval: 30s
    rules:
      # ✅ High error rate
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # ✅ Slow response time
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile response time > 2s"

      # ✅ Database connection pool exhausted
      - alert: DatabaseConnectionPoolExhausted
        expr: |
          db_connections_gauge{state="waiting"} > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhausted"

      # ✅ Redis unavailable
      - alert: RedisDown
        expr: |
          up{job="redis"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"

      # ✅ High memory usage
      - alert: HighMemoryUsage
        expr: |
          (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage (>90%)"
```

---

## 5. AI/ML LAYER KONTROL LİSTELERİ

### 5.1 LLM Service Kontrolleri

#### ✅ Pre-Development
- [ ] OpenAI API key güvenli mi? (environment variable)
- [ ] Rate limiting stratejisi belirlenmiş mi? (60 req/min, 90k tokens/min)
- [ ] Cost tracking implementasyonu var mı?
- [ ] Fallback strategy tanımlı mı?

**Configuration:**
```python
# backend/core/llm_service.py

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ConfigurationError("OPENAI_API_KEY not set")

        self.client = AsyncOpenAI(api_key=self.api_key)

        # ✅ Rate limiter
        self.rate_limiter = RateLimiter(
            requests_per_minute=60,
            tokens_per_minute=90000
        )

        # ✅ Cost tracker
        self.cost_tracker = CostTracker()

        # ✅ Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60
        )

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text with LLM

        ✅ Rate limiting
        ✅ Cost tracking
        ✅ Circuit breaker
        ✅ Retry logic
        ✅ Timeout
        """
        # Rate limiting
        await self.rate_limiter.wait_if_needed()

        # Circuit breaker
        if self.circuit_breaker.is_open():
            raise ServiceUnavailableError("OpenAI API unavailable")

        try:
            # Token counting
            token_count = self.count_tokens(prompt)

            # Cost estimation
            estimated_cost = self.estimate_cost(
                model=model,
                prompt_tokens=token_count,
                completion_tokens=max_tokens
            )
            logger.info(
                "llm_request",
                model=model,
                prompt_tokens=token_count,
                estimated_cost=estimated_cost
            )

            # Generate with timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                ),
                timeout=30.0
            )

            # Track actual cost
            actual_cost = self.calculate_cost(
                model=model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
            await self.cost_tracker.record(actual_cost)

            # Track metrics
            llm_requests_total.labels(model=model, status="success").inc()
            llm_tokens_used.labels(model=model).inc(response.usage.total_tokens)
            llm_cost_usd.labels(model=model).inc(actual_cost)

            # Circuit breaker success
            self.circuit_breaker.record_success()

            return response.choices[0].message.content

        except OpenAIError as e:
            # Circuit breaker failure
            self.circuit_breaker.record_failure()

            # Track error
            llm_requests_total.labels(model=model, status="error").inc()
            logger.error("llm_error", error=str(e))

            # Retry or fallback
            if isinstance(e, RateLimitError):
                # Wait and retry
                await asyncio.sleep(60)
                return await self.generate(prompt, model, max_tokens, temperature)
            elif isinstance(e, APIConnectionError):
                # Fallback to template-based generation
                return await self.fallback_generator.generate(prompt)
            else:
                raise
```

#### 🔄 Monitoring
- [ ] LLM usage metrics tracked mı? (requests, tokens, cost)
- [ ] Error rates monitored mı?
- [ ] Response times logged mı?
- [ ] Cost alerts configured mı? (budget exceeded)

**Metrics Dashboard:**
```python
# Prometheus queries for Grafana dashboard

# ✅ Requests per minute
rate(llm_requests_total[1m])

# ✅ Error rate
rate(llm_requests_total{status="error"}[5m]) / rate(llm_requests_total[5m])

# ✅ Average response time
rate(llm_request_duration_seconds_sum[5m]) / rate(llm_request_duration_seconds_count[5m])

# ✅ Tokens used per minute
rate(llm_tokens_used[1m])

# ✅ Cost per hour
rate(llm_cost_usd[1h]) * 3600

# ✅ Circuit breaker status
llm_circuit_breaker_state  # 0=closed, 1=open, 2=half-open
```

---

### 5.2 BERTurk Model Kontrolleri

#### ✅ Pre-Development
- [ ] Model dosyaları downloaded mı?
- [ ] GPU kullanımı configured mı? (CUDA available)
- [ ] Model quantization yapılmış mı? (memory optimization)
- [ ] Batch inference configured mı?

**Model Loading:**
```python
# backend/core/berturk_service.py

import torch
from transformers import AutoTokenizer, AutoModel

class BERTurkService:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")

        # ✅ Load model (lazy loading for faster startup)
        self.model_name = "dbmdz/bert-base-turkish-128k-cased"
        self._model = None
        self._tokenizer = None

    @property
    def model(self):
        if self._model is None:
            logger.info("Loading BERTurk model...")
            self._model = AutoModel.from_pretrained(
                self.model_name,
                cache_dir="/models/cache"
            ).to(self.device)

            # ✅ Quantization for memory optimization
            if self.device.type == 'cpu':
                self._model = torch.quantization.quantize_dynamic(
                    self._model,
                    {torch.nn.Linear},
                    dtype=torch.qint8
                )
            logger.info("BERTurk model loaded")
        return self._model

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir="/models/cache"
            )
        return self._tokenizer

    async def get_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Get embeddings for texts

        ✅ Batch processing
        ✅ Memory efficient
        ✅ GPU acceleration
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]

            # Tokenize
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Mean pooling
            batch_embeddings = outputs.last_hidden_state.mean(dim=1)

            # Move to CPU
            embeddings.append(batch_embeddings.cpu().numpy())

        return np.vstack(embeddings)
```

#### ⚠️ Performance
- [ ] Model inference cached mı? (same input)
- [ ] Batch size optimize edilmiş mi?
- [ ] Memory leaks yok mu?
- [ ] GPU memory monitored mı?

**Caching Strategy:**
```python
# backend/services/berturk_service.py

class BERTurkService:
    def __init__(self):
        # ...
        self.embedding_cache = LRUCache(maxsize=10000)

    async def get_embeddings_cached(self, text: str) -> np.ndarray:
        """Get embeddings with caching"""
        # Cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()

        # Check cache
        if cached := self.embedding_cache.get(cache_key):
            berturk_cache_hits.inc()
            return cached

        # Generate
        berturk_cache_misses.inc()
        embeddings = await self.get_embeddings([text])

        # Cache
        self.embedding_cache.set(cache_key, embeddings[0])

        return embeddings[0]
```

---

### 5.3 Multi-Agent System Kontrolleri

#### ✅ Development
- [ ] Agent responsibilities açık mı?
- [ ] Blackboard architecture implemented mı?
- [ ] Conflict resolution stratejisi var mı?
- [ ] Agent coordination test edilmiş mi?

**Agent Architecture:**
```python
# backend/agents/blackboard_coordinator.py

class BlackboardCoordinator:
    """
    Multi-agent coordination using blackboard pattern

    ✅ Agents register themselves
    ✅ Task distribution
    ✅ Result aggregation
    ✅ Conflict resolution
    """

    def __init__(self):
        self.blackboard = {}  # Shared memory
        self.agents = []      # Registered agents
        self.lock = asyncio.Lock()

    def register_agent(self, agent: BaseAgent):
        """Register an agent"""
        self.agents.append(agent)
        logger.info(f"Agent registered: {agent.name}")

    async def coordinate(self, task: Dict) -> Dict:
        """
        Coordinate agents for a task

        1. Post task to blackboard
        2. Notify all agents
        3. Collect results
        4. Resolve conflicts
        5. Return aggregated result
        """
        async with self.lock:
            # 1. Post task
            task_id = str(uuid.uuid4())
            self.blackboard[task_id] = {
                'task': task,
                'results': [],
                'status': 'pending'
            }

        # 2. Notify agents (parallel)
        agent_results = await asyncio.gather(*[
            agent.process(task) for agent in self.agents
            if agent.can_handle(task)
        ])

        # 3. Collect results
        async with self.lock:
            self.blackboard[task_id]['results'] = [
                r for r in agent_results if r is not None
            ]
            self.blackboard[task_id]['status'] = 'processed'

        # 4. Resolve conflicts
        resolved = await self._resolve_conflicts(
            self.blackboard[task_id]['results']
        )

        # 5. Clean up
        async with self.lock:
            del self.blackboard[task_id]

        return resolved

    async def _resolve_conflicts(self, results: List[Dict]) -> Dict:
        """
        Resolve conflicts between agent results

        Strategy:
        - If all agents agree: Return consensus
        - If disagreement: Weighted voting based on confidence
        """
        if not results:
            return {}

        # Check for consensus
        if len(set(str(r) for r in results)) == 1:
            # All agents agree
            return results[0]

        # Weighted voting
        weighted_results = defaultdict(float)
        for result in results:
            confidence = result.get('confidence', 0.5)
            key = str(result.get('recommendation'))
            weighted_results[key] += confidence

        # Return highest weighted result
        best_key = max(weighted_results, key=weighted_results.get)
        return next(r for r in results if str(r.get('recommendation')) == best_key)
```

**Agent Example:**
```python
# backend/agents/learning_path_agent.py

class LearningPathAgent(BaseAgent):
    """
    Agent specialized in learning path generation

    ✅ Analyzes student performance
    ✅ Recommends learning resources
    ✅ Schedules study sessions
    """

    name = "learning_path_agent"

    def can_handle(self, task: Dict) -> bool:
        """Can this agent handle the task?"""
        return task.get('type') == 'learning_path_generation'

    async def process(self, task: Dict) -> Optional[Dict]:
        """Process the task"""
        try:
            student_id = task['student_id']

            # 1. Get student profile
            profile = await self.get_student_profile(student_id)

            # 2. Analyze weak areas
            weak_areas = await self.analyze_weak_areas(profile)

            # 3. Recommend resources
            resources = await self.recommend_resources(weak_areas)

            # 4. Create schedule
            schedule = await self.create_schedule(
                resources,
                profile['available_hours_per_week']
            )

            return {
                'agent': self.name,
                'confidence': 0.9,
                'weak_areas': weak_areas,
                'resources': resources,
                'schedule': schedule
            }

        except Exception as e:
            logger.error(f"Agent error: {e}")
            return None
```

---

## 6. ALGORITHM LAYER KONTROL LİSTELERİ

### 6.1 Turkish NLP Kontrolleri

#### ✅ Development
- [ ] Zemberek-NLP integration çalışıyor mu?
- [ ] Turkish character handling doğru mu? (İ/I, Ğ/G, Ş/S, etc.)
- [ ] Morphological analysis accurate mi?
- [ ] Text normalization configured mı?

**Turkish Text Processing:**
```python
# backend/algorithms/turkish_morphology_aware_irt.py

class TurkishMorphologyAwareIRT:
    """
    IRT + Turkish morphology

    ✅ Zemberek integration
    ✅ Turkish character support
    ✅ Morphological analysis
    ✅ Difficulty estimation
    """

    def __init__(self):
        from zemberek import TurkishMorphology
        self.morphology = TurkishMorphology.builder().use_default_lexicon().build()

    def calculate_linguistic_difficulty(self, text: str) -> float:
        """
        Calculate text difficulty based on Turkish morphology

        Factors:
        - Root word complexity (frequency)
        - Affix count
        - Morphological features
        - Sentence structure
        """
        # Normalize Turkish text
        text = self._normalize_turkish(text)

        # Morphological analysis
        analysis_results = self.morphology.analyze_sentence(text)

        scores = []
        for word_analysis in analysis_results:
            best_analysis = word_analysis.get_best()

            # Root complexity (use word frequency)
            root = best_analysis.get_root()
            root_score = self._get_word_frequency_score(root)

            # Affix complexity
            affixes = best_analysis.get_affixes()
            affix_score = len(affixes) * 0.1

            # Morphological features
            features = best_analysis.get_morphemes()
            feature_score = self._calculate_feature_complexity(features)

            word_score = root_score + affix_score + feature_score
            scores.append(word_score)

        # Average difficulty
        return np.mean(scores) if scores else 3.0

    def _normalize_turkish(self, text: str) -> str:
        """Normalize Turkish text"""
        # Lowercase (Turkish-aware)
        text = text.replace('I', 'ı').replace('İ', 'i')
        text = text.lower()

        # Remove punctuation
        text = re.sub(r'[^\wşğüöçıİĞÜÖÇŞ\s]', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def _get_word_frequency_score(self, word: str) -> float:
        """
        Get word frequency score

        Common words: Low score (easy)
        Rare words: High score (difficult)
        """
        # Turkish word frequency list (top 5000)
        freq = self.turkish_word_frequencies.get(word, 5000)

        # Normalize to 0-5 scale
        return min(5.0, (freq / 1000))

    def _calculate_feature_complexity(self, features) -> float:
        """
        Calculate complexity based on morphological features

        Complex features increase difficulty:
        - Case (nominative < accusative < dative < locative < ablative)
        - Tense (present < past < future < perfect)
        - Person (3rd < 1st < 2nd)
        """
        complexity = 0.0

        for feature in features:
            if 'Case' in feature:
                case_complexity = {
                    'Nom': 0.0, 'Acc': 0.5, 'Dat': 1.0,
                    'Loc': 1.5, 'Abl': 2.0
                }
                complexity += case_complexity.get(feature, 0.5)

            if 'Tense' in feature:
                tense_complexity = {
                    'Pres': 0.0, 'Past': 0.5, 'Fut': 1.0, 'Perf': 1.5
                }
                complexity += tense_complexity.get(feature, 0.5)

        return complexity
```

---

### 6.2 Adaptive Learning Algorithm Kontrolleri

#### ✅ Development
- [ ] ZPD calculation accurate mi?
- [ ] Difficulty adjustment smooth mi?
- [ ] Performance tracking working mi?
- [ ] Cultural factors considered mi?

**ZPD Implementation:**
```python
# backend/algorithms/turkish_zpd_maarif_system.py

class TurkishZPDMaarifSystem:
    """
    Zone of Proximal Development + Turkish Education System

    ✅ Vygotsky's ZPD theory
    ✅ MEB curriculum alignment
    ✅ OSYM standards
    ✅ Cultural adaptation
    """

    def calculate_zpd(self, student: StudentProfile) -> ZPDRange:
        """
        Calculate student's Zone of Proximal Development

        Current level: What student can do independently
        Potential level: What student can do with help
        ZPD: Gap between current and potential
        """
        # 1. Current ability (from exam history)
        current_ability = self._estimate_current_ability(student)

        # 2. Potential ability (based on various factors)
        potential_ability = self._estimate_potential_ability(student)

        # 3. ZPD range
        zpd_range = ZPDRange(
            lower_bound=current_ability,
            upper_bound=potential_ability,
            optimal_difficulty=(current_ability + potential_ability) / 2
        )

        # 4. Cultural adaptation
        zpd_range = self._apply_cultural_factors(zpd_range, student)

        # 5. MEB curriculum alignment
        zpd_range.meb_grade_level = self._map_to_meb_curriculum(
            zpd_range.optimal_difficulty
        )

        return zpd_range

    def _estimate_current_ability(self, student: StudentProfile) -> float:
        """
        Estimate current ability (theta in IRT)

        Based on:
        - Recent exam scores
        - Question difficulty
        - Time taken
        """
        recent_exams = student.get_recent_exams(limit=5)

        if not recent_exams:
            # Default: Middle difficulty
            return 3.0

        # IRT-based ability estimation
        abilities = []
        for exam in recent_exams:
            theta = self._irt_ability_estimation(
                exam.answers,
                exam.questions
            )
            abilities.append(theta)

        # Weighted average (more recent = more weight)
        weights = [0.4, 0.3, 0.2, 0.05, 0.05][:len(abilities)]
        current_ability = np.average(abilities, weights=weights)

        return current_ability

    def _estimate_potential_ability(self, student: StudentProfile) -> float:
        """
        Estimate potential ability

        Factors:
        - Current ability
        - Learning rate (from progress tracking)
        - Motivation level
        - Study time availability
        - Learning style match
        """
        current = student.current_ability

        # Learning rate (how fast student improves)
        learning_rate = self._calculate_learning_rate(student)

        # Motivation boost
        motivation_factor = 1.0 + (student.motivation_level / 10)

        # Study time factor
        study_time_factor = min(1.5, student.weekly_study_hours / 20)

        # Learning style match factor
        style_match_factor = 1.0 + (student.learning_style_match / 10)

        # Calculate potential
        potential = current * learning_rate * motivation_factor * study_time_factor * style_match_factor

        # Cap at maximum (5.0)
        potential = min(5.0, potential)

        # Minimum gap (at least 0.5 points)
        potential = max(current + 0.5, potential)

        return potential

    def _apply_cultural_factors(
        self,
        zpd_range: ZPDRange,
        student: StudentProfile
    ) -> ZPDRange:
        """
        Apply Turkish cultural factors

        Factors:
        - Exam anxiety (common in Turkey)
        - Family pressure
        - Peer competition
        - University entrance stress
        """
        # High exam anxiety: Lower optimal difficulty
        if student.exam_anxiety > 0.7:
            zpd_range.optimal_difficulty *= 0.9
            logger.info(
                "zpd_adjusted_for_anxiety",
                student_id=str(student.id),
                adjustment=-0.1
            )

        # High family pressure: More gradual progression
        if student.family_pressure > 0.7:
            zpd_range.optimal_difficulty *= 0.95
            logger.info(
                "zpd_adjusted_for_pressure",
                student_id=str(student.id),
                adjustment=-0.05
            )

        # High peer competition: Can handle slightly higher difficulty
        if student.peer_competition > 0.7:
            zpd_range.optimal_difficulty *= 1.05
            logger.info(
                "zpd_adjusted_for_competition",
                student_id=str(student.id),
                adjustment=+0.05
            )

        return zpd_range

    def _map_to_meb_curriculum(self, difficulty: float) -> str:
        """
        Map difficulty to MEB grade level

        Difficulty scale (1-5) → Grade level (9-12)
        """
        mapping = {
            (0.0, 2.0): "9. Sınıf",  # Easy
            (2.0, 3.0): "10. Sınıf", # Medium
            (3.0, 4.0): "11. Sınıf", # Hard
            (4.0, 5.0): "12. Sınıf"  # Very Hard
        }

        for (low, high), grade in mapping.items():
            if low <= difficulty < high:
                return grade

        return "12. Sınıf"  # Default
```

---

## 7. DATABASE LAYER KONTROL LİSTELERİ

### 7.1 Schema Design Kontrolleri

#### ✅ Pre-Development
- [ ] Entity-Relationship diagram hazırlanmış mı?
- [ ] Normalization yapılmış mı? (3NF)
- [ ] Foreign key constraints tanımlı mı?
- [ ] Indexes planlanmış mı?

**Schema Validation:**
```sql
-- Check foreign key constraints
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    confrelid::regclass AS referenced_table,
    conkey AS constrained_columns,
    confkey AS referenced_columns
FROM pg_constraint
WHERE contype = 'f'
ORDER BY table_name;

-- Check indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check for missing indexes (tables without indexes on foreign keys)
SELECT
    t.relname AS table_name,
    a.attname AS column_name,
    'Missing index on foreign key' AS issue
FROM pg_attribute a
JOIN pg_class t ON a.attrelid = t.oid
JOIN pg_constraint c ON c.conrelid = t.oid AND a.attnum = ANY(c.conkey)
WHERE c.contype = 'f'
  AND NOT EXISTS (
    SELECT 1
    FROM pg_index i
    WHERE i.indrelid = t.oid
      AND a.attnum = ANY(i.indkey)
  );
```

---

### 7.2 Migration Kontrolleri

#### ✅ Development
- [ ] Alembic migrations version controlled mı?
- [ ] Migration scripts test edilmiş mi? (up & down)
- [ ] Data migration strategy belirlenmiş mi?
- [ ] Rollback plan hazır mı?

**Migration Checklist:**
```bash
# 1. Create migration
alembic revision --autogenerate -m "Add performance indexes"

# 2. Review migration file
cat backend/alembic/versions/002_add_performance_indexes.py

# 3. Test migration (up)
alembic upgrade head

# 4. Test rollback (down)
alembic downgrade -1

# 5. Test re-apply
alembic upgrade head

# 6. Check database state
psql -U kiro2_user -d kiro2_db -c "\d+ questions"
```

**Migration Best Practices:**
```python
# backend/alembic/versions/002_add_performance_indexes.py

"""Add performance indexes

Revision ID: 002
Revises: 001
Create Date: 2025-11-17
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    """
    ✅ Add indexes
    ✅ CONCURRENTLY to avoid locks
    ✅ IF NOT EXISTS for safety
    """
    # Create indexes concurrently (no table lock)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
        ix_questions_subject_difficulty_quality
        ON questions(subject, difficulty, quality_score DESC)
        WHERE is_active = true;
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
        ix_exams_user_started
        ON exams(user_id, started_at DESC)
        WHERE is_active = true;
    """)

def downgrade():
    """
    ✅ Remove indexes
    ✅ IF EXISTS for safety
    """
    op.execute("DROP INDEX IF EXISTS ix_questions_subject_difficulty_quality;")
    op.execute("DROP INDEX IF EXISTS ix_exams_user_started;")
```

---

### 7.3 Query Performance Kontrolleri

#### 🔄 Periodic
- [ ] Slow queries identified mı? (>100ms)
- [ ] EXPLAIN ANALYZE yapılmış mı?
- [ ] N+1 queries eliminated mı?
- [ ] Query cache stratejisi uygulanmış mı?

**Slow Query Monitoring:**
```sql
-- Enable slow query logging
ALTER DATABASE kiro2_db SET log_min_duration_statement = 100;  -- Log queries > 100ms

-- View slow queries
SELECT
    calls,
    total_exec_time / 1000 AS total_time_seconds,
    mean_exec_time / 1000 AS mean_time_seconds,
    max_exec_time / 1000 AS max_time_seconds,
    query
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- Queries with avg > 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Most frequently called queries
SELECT
    calls,
    mean_exec_time / 1000 AS avg_ms,
    query
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 20;

-- Queries with highest total time
SELECT
    calls,
    total_exec_time / 1000 AS total_seconds,
    mean_exec_time / 1000 AS avg_ms,
    query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

**Query Optimization Example:**
```python
# ❌ BAD: N+1 query
async def get_exams_with_details(user_id: UUID):
    # Query 1: Get exams
    exams = await db.execute(
        select(Exam).where(Exam.user_id == user_id)
    )
    exams = exams.scalars().all()

    for exam in exams:
        # Query 2-N: Get questions for each exam
        questions = await db.execute(
            select(ExamQuestion).where(ExamQuestion.exam_id == exam.id)
        )
        exam.questions = questions.scalars().all()

        # Query N+1-2N: Get answers for each exam
        answers = await db.execute(
            select(Answer).where(Answer.exam_id == exam.id)
        )
        exam.answers = answers.scalars().all()

    return exams  # Total queries: 1 + 2*N

# ✅ GOOD: Single query with joins
async def get_exams_with_details(user_id: UUID):
    exams = await db.execute(
        select(Exam)
        .where(Exam.user_id == user_id)
        .options(
            joinedload(Exam.questions),  # Eager load questions
            joinedload(Exam.answers)     # Eager load answers
        )
    )
    return exams.scalars().all()  # Total queries: 1

# ✅ BETTER: With subqueryload for large collections
async def get_exams_with_details(user_id: UUID):
    exams = await db.execute(
        select(Exam)
        .where(Exam.user_id == user_id)
        .options(
            subqueryload(Exam.questions),  # Separate query but optimized
            subqueryload(Exam.answers)
        )
    )
    return exams.scalars().all()  # Total queries: 3 (1 + 2)
```

---

## 8. EXTERNAL SERVICES LAYER KONTROL LİSTELERİ

### 8.1 API Integration Kontrolleri

#### ✅ Pre-Development
- [ ] API keys güvenli mi? (environment variables)
- [ ] Rate limits documented mı?
- [ ] Error handling comprehensive mi?
- [ ] Timeout values appropriate mi?

**OpenAI Integration:**
```python
# backend/services/llm_service.py

class LLMService:
    """
    OpenAI API integration

    ✅ API key from environment
    ✅ Rate limiting (60 req/min, 90k tokens/min)
    ✅ Error handling
    ✅ Timeout (30s)
    ✅ Retry logic
    ✅ Cost tracking
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key or self.api_key == "your-openai-api-key-here":
            raise ConfigurationError("OPENAI_API_KEY not properly configured")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=30.0,
            max_retries=3
        )

        # Rate limiter
        self.rate_limiter = RateLimiter(
            requests_per_minute=60,
            tokens_per_minute=90000
        )

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate with error handling and retries"""
        await self.rate_limiter.wait_if_needed()

        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", "gpt-4"),
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.choices[0].message.content

        except RateLimitError:
            # Wait 60s and retry
            logger.warning("OpenAI rate limit hit, waiting 60s")
            await asyncio.sleep(60)
            return await self.generate(prompt, **kwargs)

        except APIConnectionError as e:
            # Network error, retry after short delay
            logger.error(f"OpenAI connection error: {e}")
            await asyncio.sleep(5)
            return await self.generate(prompt, **kwargs)

        except AuthenticationError as e:
            # Invalid API key, don't retry
            logger.error(f"OpenAI authentication error: {e}")
            raise ConfigurationError("Invalid OpenAI API key")

        except Exception as e:
            logger.error(f"OpenAI unexpected error: {e}")
            Sentry.capture_exception(e)
            raise
```

**YouTube Integration:**
```python
# backend/services/real_youtube_api.py

class YouTubeService:
    """
    YouTube Data API v3 integration

    ✅ API key from environment
    ✅ Quota management (10,000 units/day)
    ✅ Rate limiting (100 QPS)
    ✅ Caching (1 hour)
    """

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ConfigurationError("YOUTUBE_API_KEY not set")

        # Rate limiter
        self.rate_limiter = RateLimiter(queries_per_second=100)

        # Quota tracker
        self.quota_tracker = QuotaTracker(daily_limit=10000)

        # Cache
        self.cache = Redis()

    async def search_videos(
        self,
        query: str,
        max_results: int = 10
    ) -> List[VideoInfo]:
        """
        Search videos with caching

        Cost: 100 quota units per request
        """
        # Check cache
        cache_key = f"youtube:search:{query}:{max_results}"
        if cached := await self.cache.get(cache_key):
            return json.loads(cached)

        # Check quota
        if not self.quota_tracker.can_make_request(cost=100):
            raise QuotaExceededError("YouTube API quota exceeded")

        # Rate limiting
        await self.rate_limiter.wait_if_needed()

        try:
            # Make request
            response = await self.youtube.search().list(
                q=query,
                part="snippet",
                maxResults=max_results,
                relevanceLanguage="tr",
                type="video",
                videoCaption="closedCaption"
            ).execute()

            # Parse results
            videos = self._parse_search_results(response)

            # Cache for 1 hour
            await self.cache.setex(
                cache_key,
                3600,
                json.dumps([v.dict() for v in videos])
            )

            # Track quota
            self.quota_tracker.record_request(cost=100)

            return videos

        except HttpError as e:
            if e.resp.status == 403:
                # Quota exceeded
                raise QuotaExceededError("YouTube API quota exceeded")
            elif e.resp.status == 400:
                # Bad request
                raise ValidationError(f"Invalid query: {query}")
            else:
                logger.error(f"YouTube API error: {e}")
                raise
```

---

## 9. MONITORING LAYER KONTROL LİSTELERİ

### 9.1 Prometheus Metrics Kontrolleri

#### ✅ Development
- [ ] Metrics exported mı? (`/metrics` endpoint)
- [ ] Business metrics tracked mı? (exams, questions, users)
- [ ] Infrastructure metrics tracked mı? (CPU, memory, disk)
- [ ] SLI/SLO defined mı?

**Metrics Export:**
```python
# backend/main.py

from prometheus_client import make_asgi_app

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**SLI/SLO Definitions:**
```yaml
# Service Level Indicators (SLI) & Objectives (SLO)

# ✅ Availability SLO: 99.9% uptime
- name: availability
  sli: up{job="kiro2-backend"} == 1
  slo: 99.9%
  window: 30d

# ✅ Latency SLO: 95% of requests < 500ms
- name: latency_p95
  sli: histogram_quantile(0.95, http_request_duration_seconds_bucket) < 0.5
  slo: 95%
  window: 7d

# ✅ Error rate SLO: < 1% errors
- name: error_rate
  sli: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) < 0.01
  slo: 99%
  window: 7d
```

---

## 10. INFRASTRUCTURE LAYER KONTROL LİSTELERİ

### 10.1 Docker Configuration Kontrolleri

#### 🚨 Pre-Deployment
- [ ] Docker images optimized mı? (multi-stage build)
- [ ] Health checks configured mı?
- [ ] Resource limits set mı? (CPU, memory)
- [ ] Secrets managed properly mi? (not in image)

**Dockerfile Best Practices:**
```dockerfile
# backend/Dockerfile

# ✅ Multi-stage build (smaller final image)
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ✅ Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# ✅ Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# ✅ Non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# ✅ Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml Best Practices:**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}  # ✅ From .env file
    # ✅ Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    # ✅ Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    # ✅ Restart policy
    restart: unless-stopped
    # ✅ Logging
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 11. BİLEŞENLER ARASI ENTEGRASYON MATRİSİ

### Entegrasyon Test Senaryoları

#### Frontend ↔ API Gateway
```typescript
// Test: Authentication flow
test('Full authentication flow', async () => {
  // 1. Register
  const registerResponse = await authService.register({
    email: 'test@example.com',
    password: 'SecurePass123!',
    ad_soyad: 'Test User',
    rol: 'ogrenci'
  });
  expect(registerResponse.status).toBe(201);

  // 2. Login
  const loginResponse = await authService.login({
    email: 'test@example.com',
    password: 'SecurePass123!'
  });
  expect(loginResponse.access_token).toBeDefined();
  expect(loginResponse.token_type).toBe('bearer');

  // 3. Access protected endpoint
  const profileResponse = await userService.getProfile();
  expect(profileResponse.email).toBe('test@example.com');

  // 4. Logout
  await authService.logout();
  const tokenRemoved = !localStorage.getItem('token');
  expect(tokenRemoved).toBe(true);
});
```

#### API Gateway ↔ Business Logic ↔ Database
```python
# Test: Exam creation flow
@pytest.mark.asyncio
async def test_exam_creation_flow(async_client, authenticated_student):
    # 1. Start exam
    response = await async_client.post(
        "/api/sinav/start",
        json={"exam_type": "TYT"},
        headers={"Authorization": f"Bearer {authenticated_student.token}"}
    )
    assert response.status_code == 201
    data = response.json()
    exam_id = data["exam_id"]

    # 2. Verify in database
    exam = await db.execute(
        select(Exam).where(Exam.id == exam_id)
    )
    exam = exam.scalar_one()
    assert exam.user_id == authenticated_student.id
    assert exam.exam_type == ExamType.TYT
    assert len(exam.questions) == 40

    # 3. Verify in cache
    cached = await redis.get(f"active_exam:{authenticated_student.id}")
    assert cached is not None
    cached_data = json.loads(cached)
    assert cached_data["exam_id"] == str(exam_id)
```

---

## 12. KRİTİK SENARYO KONTROLLERI

### 12.1 Yüksek Trafik Senaryosu

**Test: 1000 concurrent exam sessions**
```bash
# Load test with k6
k6 run --vus 1000 --duration 5m tests/load/exam_start.js
```

**Kontrol Listesi:**
- [ ] Database connection pool yeterli mi?
- [ ] Redis connections yeterli mi?
- [ ] Memory kullanımı safe mi?
- [ ] Response times acceptable mı? (<2s)
- [ ] Error rate kabul edilebilir mi? (<1%)

---

### 12.2 Database Failure Senaryosu

**Test: Database unavailability**
```bash
# Stop PostgreSQL
docker-compose stop postgres

# Test application behavior
curl http://localhost:8000/health
# Expected: 503 Service Unavailable

# Check logs
docker-compose logs backend | grep -i "database"
# Expected: Connection error logs

# Restart PostgreSQL
docker-compose start postgres

# Wait for health check
sleep 30

# Test recovery
curl http://localhost:8000/health
# Expected: 200 OK
```

**Kontrol Listesi:**
- [ ] Circuit breaker opens mı?
- [ ] Cached data served mı?
- [ ] Graceful degradation var mı?
- [ ] Users notified mı?
- [ ] Auto-recovery works mı?

---

### 12.3 Redis Failure Senaryosu

**Test: Redis unavailability**
```bash
# Stop Redis
docker-compose stop redis

# Test application behavior
curl http://localhost:8000/api/questions
# Expected: 200 OK (but slower, no cache)

# Check logs
docker-compose logs backend | grep -i "redis"
# Expected: "Switching to fallback mode"

# Verify fallback mode
curl http://localhost:8000/metrics | grep cache_fallback_mode
# Expected: cache_fallback_mode 1
```

**Kontrol Listesi:**
- [ ] Fallback mode activates mı?
- [ ] Application continues working mı?
- [ ] Database load increases mı? (expected)
- [ ] Auto-recovery after Redis restart mı?

---

## SONUÇ

Bu kapsamlı kontrol listeleri, KIRO2 platformunun tüm bileşenlerinin tam uyumlu çalışması için gereken tüm kontrolleri içermektedir.

**Kullanım:**
1. Her bileşen geliştirmesinde ilgili bölümü kontrol edin
2. Entegrasyon öncesi ilgili kontrol listelerini uygulayın
3. Production deployment öncesi tüm 🚨 KRİTİK işaretli kontrolleri yapın
4. Periyodik olarak 🔄 PERİYODİK işaretli kontrolleri tekrarlayın

**Teknofest 2025 - Eğitim Eylemcisi Kategorisi**
**KIRO2 Platform - Türkiye Üniversite Sınavları Hazırlık Platformu**
