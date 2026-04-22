---
name: kiro2-specific
description: KIRO2 platform özel gereksinimleri. Auth store, DB port, API endpoint'ler, performans hedefleri, güvenlik kuralları.
---

# KIRO2 Platform-Specific Rules

KIRO2'ye özgü kritik kurallar. `.cursor/rules/00-core.mdc`'deki temel
kurallara ek — bu skill derin platform bilgisi gerektiğinde yüklenir.

## Stack Özeti

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy 2.0+ + PostgreSQL + Redis
- **Frontend**: React 18 + TypeScript + Zustand + Next.js
- **AI/ML**: IRT, FSRS, BKT, ZPD, Zemberek, BERTurk, Qwen3-8B

## KRİTİK Port ve Path Kuralları

| Servis | Port | Not |
|---|---|---|
| Backend | 8000 | - |
| Frontend | 3000 / 3001 | dev'de |
| PostgreSQL | **5434** | Standart 5432 DEĞIL! |
| Redis | 6379 | - |

## Auth Store (P0 — ihlali ciddi)

```typescript
// ✅ DOĞRU
import { useAuthStore } from '@/store/authStore';

// ❌ YASAK — useAuth.ts KULLANMA
import { useAuth } from '@/hooks/useAuth';

// ❌ YASAK — stores/ (çoğul) DEĞIL, store/ (tekil)
import { useAuthStore } from '@/stores/authStore';
```

## Dual Table Trap (Session 78 — P0)

`Question` için iki model var. Production'da olan:

```python
# ✅ DOĞRU — 77,336 soruluk tablo
from models.question_bank import QuestionBankItem as Question
result = db.query(Question).filter(Question.is_active == True).all()

# ❌ YANLIŞ — bos legacy tablo (0 kayıt)
from models.database import Question
```

Her yeni query'de `is_active == True` filtresi ZORUNLU.

## Async Session Pattern (Session 78)

```python
# FastAPI endpoint (Depends kullanımı)
async def endpoint(db: AsyncSession = Depends(get_db)):
    await db.execute(...)

# Manuel kullanım (context manager)
async with get_db_session_context() as session:
    await session.execute(...)

# YASAK — generator'ı context manager gibi kullanma
async with get_async_session() as session:  # TypeError!
    ...
```

## Middleware HTTPException (Session 148)

`BaseHTTPMiddleware.dispatch()` içinde `raise HTTPException` YASAKTIR —
500 olarak çıkar. Yerine:

```python
from starlette.responses import JSONResponse

class MyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not valid:
            return JSONResponse(status_code=403, content={"detail": "..."})
        return await call_next(request)
```

## Enum Convention (Session 78)

KIRO2 enum'ları Türkçe:
```python
SubjectType.MATEMATIK     # MATHEMATICS değil
DifficultyLevel.COK_KOLAY # VERY_EASY değil
```

DB casing uyumsuzluğu:
- `question_bank.exam_type` → UPPERCASE ("TYT")
- `ExamType` enum → lowercase ("tyt")
- Query: `exam_config.exam_type.value.upper()`

## Rate Limiting

| Endpoint | Limit | Neden |
|---|---|---|
| `/auth/login` | 5/dk | Brute force |
| Genel API | 100/dk | Normal kullanım |
| AI işlemleri | 10/dk | Maliyet |

## Performans Hedefleri

| Metrik | Hedef | Kritik |
|---|---|---|
| p50 response | < 100ms | < 200ms |
| p95 response | < 300ms | < 500ms |
| p99 response | < 500ms | < 1000ms |
| Error rate | < 0.1% | < 1% |

## Docker Staleness (Session 121)

Container'da 404/ImportError → KOD DEĞIŞTIRMEDEN önce image rebuild:
```bash
docker exec kiro2-backend grep -c 'PATTERN' /app/FILE
# Local ile karşılaştır
docker compose build --no-cache backend && docker compose up -d
```

## Windows Path Replace (Session 48)

`str(Path(...))` Windows'ta backslash, prompt replace sessizce fail olur:
```python
# Her iki formatı normalize et
old_fwd = str(screenshot).replace("\\", "/")
new_fwd = str(enhanced).replace("\\", "/")
prompt = prompt.replace(str(screenshot), str(enhanced))
prompt = prompt.replace(old_fwd, new_fwd)
```

## Detaylı Rehber

- `.claude/skills/kiro2-specific/SKILL.md` — bu skill'in tam içeriği
- `.claude/rules/security.md` — güvenlik detayı (KVKK, YKS soru güvenliği)
- `CLAUDE.md` — session management, pre-flight checks
