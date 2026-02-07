# KIRO2 Project Instructions

## 🎯 Project Overview

KIRO2 is a Turkish EdTech platform for YKS/TYT/AYT university entrance exam preparation.

**Mission:** Deliver personalized, AI-powered exam preparation using Turkish NLP and adaptive learning.

**Project Root:** `C:\Users\husey\kiro2`

## 📊 Current Status (February 2026)

### Database & Content ✅
- ✅ **PostgreSQL 15** (port 5434) - Production ready
  - **PgBouncer:** Not yet configured (planned for 100K+ concurrent users)
- ✅ **Redis 7** (port 6379) - Session & cache layer
- ✅ **36,967 YKS questions loaded** (Target: 50K by March 2026)
  - 📊 **Success Story:** Matching rate improved from 0.11% → 48.8% (36,967/75,745)
  - High confidence: 24.2% (8,949 questions)
  - Medium confidence: 23.2% (8,570 questions)
  - Low confidence: 52.6% (19,448 questions) ← **PRIORITY: Quality improvement**
- ✅ **308 source books** processed from 426 total
- ✅ **eslesmis_sorucevap.jsonl** format in production

### 🎯 Next Priorities
1. **Low-confidence question refinement pipeline** (19,448 questions)
2. **Quality improvement**: 52.6% → 90%+ high-confidence target
3. **Remaining 118 books**: Process for additional 13K+ questions
4. **Manual validation**: Sample-based QA on medium-confidence matches

### Orchestrator Architecture ✅
- ✅ **orchestrator/** v2.5.0 (LangGraph 1.0.5) - **ACTIVE**
  - 24 modules (graph.py, routing.py, policy_engine.py, etc.)
  - 45 policies
  - 20 active agents
- ❌ **kiro2-orchestrator/** - **DEPRECATED** (safe to delete, legacy code)
- ✅ **YKS Module**: `.claude/plugins/installed/kiro2-yks/`

### d-dataset Pipeline Status
- ✅ **Phase 1-3 COMPLETED**
  - OCR processing: 75,745 questions extracted
  - Answer key extraction: 88,711 answers identified
  - Matching pipeline: 36,967 successful pairs (48.8% match rate)
- 🎯 **Phase 4 (Current)**: Quality enhancement
  - Target: Improve low-confidence matches (19K questions)
  - Method: Advanced Turkish NLP + semantic matching
  - Expected uplift: +15-20% high-confidence rate
  - **Output location**: `d-dataset/processed/` (versioned files)
  - **Production update**: `eslesmis_sorucevap.jsonl` updated only in release step (manual verification required)

**Release Workflow (Phase 4 → Production):**
```bash
# Step 1: Phase 4 generates versioned output
# Output: d-dataset/processed/eslesmis_sorucevap_v2.0.jsonl

# Step 2: Manual QA - sample validation (100-200 random questions)
python scripts/validate_sample.py d-dataset/processed/eslesmis_sorucevap_v2.0.jsonl

# Step 3: If QA passes (>95% accuracy), promote to production
cp d-dataset/processed/eslesmis_sorucevap_v2.0.jsonl d-dataset/eslesmis_sorucevap.jsonl

# Step 4: Backup old version (safety)
mv d-dataset/eslesmis_sorucevap.jsonl d-dataset/backups/eslesmis_sorucevap_v1.0_backup.jsonl

# ⚠️ NEVER skip manual QA step before production update
```

## 🛠️ Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | FastAPI (Python 3.11+), Uvicorn | Latest |
| Frontend | React 18 + TypeScript (Vite) | 18.x |
| Database | PostgreSQL 15 | 15.x |
| Cache | Redis 7 | 7.x |
| AI/NLP | Qwen3-8B (fine-tuned for Turkish) | Custom |
| Search | pgvector for semantic search | Latest |
| Auth | JWT + OAuth2 | - |
| Real-time | SSE (Server-Sent Events) | Default |

## 📁 Project Structure

```
kiro2/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers (41 endpoints)
│   │   ├── core/          # Config, security, deps
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── nlp/           # Turkish NLP modules
│   ├── tests/
│   └── alembic/           # DB migrations
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Route pages
│   │   ├── hooks/         # Custom hooks
│   │   ├── services/      # API clients
│   │   └── store/         # State management
│   └── tests/
├── orchestrator/          # ✅ ACTIVE - v2.5.0 (LangGraph)
├── kiro2-orchestrator/    # ❌ DEPRECATED - safe to delete
├── d-dataset/             # C:\Users\husey\kiro2\d-dataset
│   ├── ocr_output/        # 75,745 extracted questions (READ-ONLY)
│   ├── answer_keys/       # 88,711 answer entries (READ-ONLY)
│   ├── eslesmis_sorucevap.jsonl  # Final matched pairs (READ-ONLY)
│   └── processed/         # ✅ WRITABLE - pipeline outputs
├── docker/
└── docs/
```

## 🔒 File Access Rules

### ✅ ALLOWED TO MODIFY (Writable)
- `backend/app/**/*.py` - Application code
- `frontend/src/**/*` - Frontend code
- `orchestrator/**/*.py` - Orchestrator code
- `d-dataset/processed/**` - Pipeline outputs
- `backend/tests/**/*.py` - Test files
- `frontend/tests/**/*` - Frontend tests
- `docs/**/*.md` - Documentation

### ❌ NEVER MODIFY (Read-only)
- `d-dataset/ocr_output/**` - Raw OCR data
- `d-dataset/answer_keys/**` - Answer key data
- `d-dataset/eslesmis_sorucevap.jsonl` - Production matched data
- `backend/alembic/versions/*.py` - Migration history
- `backend/app/core/config.py` - Core configuration (sensitive)
  - **⚠️ EVEN IF USER REQUESTS:** Config changes must go through `.env` or override mechanism, NEVER modify `core/config.py` directly
- `.env*` - Environment files (secrets)
- `node_modules/**` - Dependencies
- `venv/**` - Virtual environment
- `.git/**` - Git internals
- `kiro2-orchestrator/**` - Deprecated code

**CRITICAL: Secrets & Environment**
- ❌ NEVER commit `.env*` files
- ❌ NEVER log secrets or API keys
- ❌ NEVER output secrets in responses
- ❌ Config changes: Use `.env` or environment variables, NOT `core/config.py`

## ⚠️ CRITICAL WARNINGS

### 1. Ripgrep Root Search Prevention
**NEVER run ripgrep on project root - causes 30min timeout!**

```bash
# ❌ WRONG: Searches entire 15GB+ project (timeout)
rg "pattern" C:\Users\husey\kiro2

# ✅ CORRECT: Target specific subdirectories
rg "pattern" C:\Users\husey\kiro2\backend\app
rg "pattern" C:\Users\husey\kiro2\orchestrator

# For multiple directories
rg "pattern" C:\Users\husey\kiro2\backend C:\Users\husey\kiro2\frontend
```

### 2. Directory Navigation
- Always use **orchestrator/** (active v2.5.0)
- Avoid **kiro2-orchestrator/** (deprecated legacy)

### 3. Turkish Text Encoding
**All Turkish text MUST be UTF-8 + NFC normalized (non-negotiable)**

### 4. Quality Gates (CI/CD)
All code changes must pass before commit:
```bash
# Backend quality gates (run from backend/ directory)
cd backend
ruff check . --fix                           # Linting
ruff format .                                # Formatting
mypy app/ --strict                           # Type checking (strict mode)
pytest -v --cov=app --cov-report=term-missing  # Tests + coverage with missing lines

# Frontend quality gates
cd frontend
npm run lint:fix          # ESLint with auto-fix
npm run format            # Prettier
npm run typecheck         # TypeScript
npm test -- --coverage    # Tests + coverage

# ❌ FAIL = DO NOT COMMIT
```

## 🔀 Agent Routing Rules

### Use Claude Code (this agent) for:

```yaml
ALWAYS_CLAUDE:
  - Turkish NLP tasks (sentiment, question generation, embeddings)
  - Qwen3-8B integration and fine-tuning
  - Complex multi-file refactoring
  - Security audits and vulnerability scanning
  - Database schema design and migrations
  - Performance optimization and profiling
  - Architectural decisions
  - Deep debugging requiring context preservation
  - d-dataset pipeline improvements
  - Orchestrator development
  - Turkish text normalization (NFC + casefold)
```

### Delegate to Codex CLI for:

```yaml
PREFER_CODEX:
  - New React component creation (simple, single-file)
  - FastAPI endpoint boilerplate (CRUD only)
  - Unit test generation (straightforward cases)
  - Documentation generation (OpenAPI, README)
  - Docker/CI-CD configuration (standard patterns)
  - Simple bug fixes (single-line, obvious)
  - CSS/Tailwind styling (non-complex)
```

### Routing Decision Logic

```
IF task contains [türkçe|turkish|nlp|qwen|sentiment] → Claude
IF task contains [security|auth|vulnerability|audit] → Claude
IF task contains [refactor|restructure|architecture] → Claude
IF task contains [d-dataset|ocr|matching|pipeline] → Claude
IF task contains [react|component|ui|frontend|css] AND simple → Codex
IF task contains [test|jest|pytest] AND straightforward → Codex
IF task contains [create|generate|add|new] AND clearly simple → Codex
IF task contains [debug|fix|optimize] AND complex → Claude
ELSE → Claude (default; repo is complex). Use Codex only for clearly simple tasks.
```

## 📋 Code Standards

### General
- All Turkish text MUST use **UTF-8 + NFC normalization**
- API response time target: <2s (realistic for complex queries)
- Test coverage minimum: 80%
- Follow existing patterns in codebase
- Use type hints everywhere (Python) / TypeScript (Frontend)

### Python/Backend
```python
# Use type hints everywhere
def create_question(content: str, topic_id: int) -> Question:
    ...

# Async by default for I/O operations
async def fetch_student_progress(student_id: int) -> Progress:
    ...

# Pydantic for validation
class QuestionCreate(BaseModel):
    content: str = Field(..., min_length=10, max_length=2000)
    topic_id: int = Field(..., gt=0)
```

### React/Frontend
```typescript
// Functional components with TypeScript
interface QuestionCardProps {
  question: Question;
  onAnswer: (answer: string) => void;
}

const QuestionCard: React.FC<QuestionCardProps> = ({ question, onAnswer }) => {
  // Use hooks for state
  const [selected, setSelected] = useState<string | null>(null);
  ...
};
```

### Database
```sql
-- Always add indexes for foreign keys
CREATE INDEX idx_questions_topic_id ON questions(topic_id);

-- Use JSONB for flexible data
ALTER TABLE questions ADD COLUMN metadata JSONB DEFAULT '{}';
```

## 🇹🇷 Turkish NLP Guidelines

### ⚠️ CRITICAL: Turkish Text Normalization

**ALWAYS use NFC Unicode normalization + Turkish lowercase mapping**

```python
import unicodedata

def normalize_tr(text: str) -> str:
    """
    Normalize Turkish text for matching/comparison.
    
    CRITICAL RULES:
    1. NFC normalization FIRST (prevents İ decomposition)
    2. Turkish mapping: İ→i, I→ı (NOT İ→I!)
    3. Standard lowercase LAST
    
    ❌ WRONG: text.replace('İ', 'I')  # Breaks Turkish!
    ✅ CORRECT: See below
    """
    if not text:
        return text
    
    # Step 1: Unicode NFC normalization (prevents decomposition issues)
    text = unicodedata.normalize("NFC", text)
    
    # Step 2: Turkish-specific lowercase mapping
    text = text.replace("İ", "i").replace("I", "ı")
    
    # Step 3: Standard lowercase
    return text.lower()

def tr_casefold(text: str) -> str:
    """Case-insensitive comparison key for Turkish.
    
    Use this for:
    - Search queries
    - String comparison
    - Deduplication
    """
    return normalize_tr(text)

# Example usage
book_name = "ACİL Matematik İSTANBUL"
normalized = normalize_tr(book_name)  # "acil matematik istanbul"
```

### Zemberek Integration
```python
# Use zemberek for morphological analysis
from zemberek import TurkishMorphology

morphology = TurkishMorphology.create_with_defaults()

def analyze_turkish_word(word: str) -> list:
    """Morphological analysis for Turkish words."""
    return morphology.analyze(normalize_tr(word))
```

### Question Generation
```python
# Template for YKS-style questions
QUESTION_TEMPLATE = """
Aşağıdaki {konu} ile ilgili soruyu cevaplayınız:

{soru_metni}

A) {secenek_a}
B) {secenek_b}
C) {secenek_c}
D) {secenek_d}
E) {secenek_e}
"""
```

### Embeddings
- Use Qwen3-8B for Turkish text embeddings
- Vector dimension: 4096
- Similarity: cosine
- Store in pgvector

## 🔒 Security Requirements

### Authentication
- JWT tokens with 24h expiry
- Refresh tokens with 7d expiry
- Rate limiting: 100 req/min per user
  - **SSE endpoints exempt** from rate limiting (long-lived connections)
  - Alternative: Separate rate limit profile for SSE (1 connection per user)

### API Security
- Input validation on all endpoints
- SQL injection prevention (use ORM)
- XSS prevention (escape HTML)
- CORS configuration for frontend only

### Data Privacy
- Student data encrypted at rest
- PII anonymization in logs
- KVKK compliance (Turkish GDPR)

## 📈 Quality Metrics

### Current Status (as of Feb 2026)
- Backend test coverage: **[MEASURE NEEDED]** (target: >80%)
  - Run: `cd backend && pytest --cov=app --cov-report=html`
- Orchestrator test coverage: **[MEASURE NEEDED]**
  - Run: `cd orchestrator && pytest tests/test_complete_system.py -v`
- Frontend test coverage: **[MEASURE NEEDED]**
  - Run: `cd frontend && npm test -- --coverage`

### Success Criteria
- ✅ All linting passes (ruff, mypy for Python)
- ✅ No type errors
- 🎯 API response time <2s (complex queries)
- 🎯 Test coverage >80% across all modules
- 🎯 High-confidence match rate >90%

### Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| API Response Time | <2s | ~2-3s | 🟡 Needs optimization |
| Vector Search | <100ms | ~300ms | 🟡 Needs optimization |
| DB Queries | <50ms | ~150ms | 🟡 Needs optimization |
| Frontend Load | <2s | ~3s | 🟡 Needs optimization |
| **Total Matched Questions** | **50K by March** | **36,967** | 🟢 On track (74%) |
| **High Confidence Rate** | **>90%** | **24.2%** | 🔴 Priority (Phase 4) |

## 🚀 Common Tasks

### Adding a New API Endpoint
```bash
# 1. Create schema in backend/app/schemas/
# 2. Add route in backend/app/api/
# 3. Implement service in backend/app/services/
# 4. Add tests in backend/tests/
# 5. Update OpenAPI docs
```

### Database Migration
```bash
# Generate migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running Tests
```bash
# Backend with coverage
cd backend && pytest -v --cov=app --cov-report=html

# Frontend with coverage
cd frontend && npm test -- --coverage

# Orchestrator tests
cd orchestrator && pytest -v
```

### Measure Test Coverage
```bash
# Backend
cd C:\Users\husey\kiro2\backend
pytest --cov=app --cov-report=term-missing --cov-report=html

# View HTML report
# Open: backend/htmlcov/index.html

# Frontend
cd C:\Users\husey\kiro2\frontend
npm test -- --coverage

# View HTML report
# Open: frontend/coverage/lcov-report/index.html
```

## 🔧 Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost:5434/kiro2  # Port 5434!
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key
QWEN_MODEL_PATH=/models/qwen3-8b-turkish

# Frontend (.env) - Vite standard
VITE_API_URL=http://localhost:8000
```

## 🌐 Real-time Communication

**Default:** Server-Sent Events (SSE)
- Unidirectional: Server → Client
- Use cases: Progress updates, notifications, leaderboard updates
- Endpoint pattern: `/api/v1/stream/*`

**Legacy:** WebSockets (deprecated, migration in progress)
- Bidirectional: Server ↔ Client
- Only for chat features (will migrate to SSE + polling)

## 📝 Commit Convention

```
feat: Add new feature
fix: Bug fix
refactor: Code refactoring
docs: Documentation
test: Tests
chore: Maintenance
perf: Performance improvement
style: Code style (formatting, etc.)
```

## ⚠️ Known Issues

### Current Challenges
1. **API Response Time**: Currently ~2-3s for complex queries
   - **Root cause**: Vector search on 36K+ questions
   - **Solution**: Implement query caching + index optimization
   
2. **Vector Search Performance**: pgvector queries ~300ms
   - **Root cause**: Large embedding dataset without proper indexing
   - **Solution**: Add HNSW indexes, batch query optimization
   
3. **Turkish Tokenization Edge Cases**
   - **Issue**: Some compound words not handled correctly
   - **Solution**: Enhance Zemberek integration, add custom rules

4. **Low Confidence Matches (52.6%)**
   - **Root cause**: OCR errors, answer key format variations
   - **Solution**: Phase 4 pipeline (advanced NLP + manual validation)

### Technical Debt
- [ ] Migrate from kiro2-orchestrator/ to orchestrator/ (cleanup)
- [ ] Implement comprehensive test coverage (>80%)
- [ ] Add performance monitoring dashboards
- [ ] Document all API endpoints in OpenAPI spec
- [ ] Migrate remaining WebSocket features to SSE

## 📞 Contact & Resources

- **Project Lead:** Hüseyin
- **Tech Stack:** FastAPI + React (Vite) + PostgreSQL (port 5434) + Redis + Qwen3-8B
- **Documentation:**
  - Main docs: `/docs`
  - API docs: http://localhost:8000/docs (when running)
  - Project guides: See uploaded documents

## 🎯 Q1 2026 Roadmap

### February
- [x] Complete Phase 1-3 of d-dataset pipeline (36,967 matches)
- [ ] Measure and document test coverage
- [ ] Implement Phase 4: Low-confidence improvement pipeline
- [ ] Clean up deprecated kiro2-orchestrator/ directory

### March
- [ ] Target: **50,000+ total questions matched**
- [ ] Achieve **90%+ high-confidence match rate**
- [ ] Performance optimization: <2s API response time
- [ ] Launch MVP for beta testing

## 📚 Lessons Learned (Agent Knowledge Base)

### Dogrulanmis Dersler (Verified, February 2026)

| # | Ders | Kategori | Uygulama |
|---|------|----------|----------|
| 1 | **Hibrit Yaklasim** | DRY/Refactoring | Merkezi fonksiyon + lokal fixture kombinasyonu en guvenli |
| 2 | **Adim Adim Ilerleme** | Process | 1 degisiklik -> 1 test -> basarili? devam : geri al |
| 3 | **Scope Analizi** | Test | Buyuk degisiklik oncesi bagimlilik ve context'i anla |
| 4 | **Geri Alma Stratejisi** | Safety | Her adimda recovery noktasi olustur |
| 5 | **Test Sonrasi Dogrulama** | Verification | Her kod degisikliginden sonra `pytest -x` ZORUNLU |

### Anti-Pattern'ler (Yapma!)

| Pattern | Neden Yanlis | Dogru Yaklasim |
|---------|--------------|----------------|
| Fixture'i tamamen kaldirmak | Context kaybi, test fail | Hibrit: import + lokal fixture |
| Buyuk degisiklik tek seferde | Geri almasi zor | Kucuk adimlar, her biri test edilebilir |
| Test calismadan commit | Hatalar prod'a gider | Her degisiklik sonrasi pytest |
| Scope anlamadan refactor | Beklenmeyen hatalar | Once analiz, sonra degisiklik |

### Agent'lara Entegre Edildi

- `.claude/rules/testing.md` - Ogrenilen dersler bolumu
- `.claude/rules/verification.md` - Adim adim ilerleme kurali
- `.claude/agents/verification-agent.md` - Dogrulanmis dersler tablosu
- `.claude/agents/kfc/spec-impl.md` - Anti-pattern'ler ve dersler

### Kaynak

Bu dersler JWT DRY Refactoring (Subat 2026) deneyiminden cikarilmistir:
- 9 dosyada kod tekrari tespit edildi
- Ilk yaklasim (tamamen merkezi) 32 test fail'e neden oldu
- Hibrit yaklasim ile 55 test pass elde edildi
- Boris Cherny verification feedback loop uygulandi

---

**Last Updated:** February 5, 2026
**Document Version:** 3.1
**Critical Fixes Applied:** Turkish normalization, Vite env, routing default, metric clarity, Lessons Learned section